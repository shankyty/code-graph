import argparse
import os
import multiprocessing
import time
from typing import List
from src.core.writers import JSONWriter, TextWriter
from src.core.interfaces import Chunk
from src.utils.git import get_file_commit_info

# Global worker state
_parser = None
_maven_resolver = None
_bazel_resolver = None
_chunker = None

def init_worker():
    """Initialize worker process with parser and resolvers."""
    global _parser, _maven_resolver, _bazel_resolver, _chunker
    # Import inside worker to avoid some pickling issues if any,
    # though with fork it shouldn't matter much.
    from src.core.languages.java_parser import JavaParser
    from src.core.dependencies.maven import MavenResolver
    from src.core.dependencies.bazel import BazelResolver
    from src.core.chunker import StandardChunker

    try:
        _parser = JavaParser()
        _maven_resolver = MavenResolver()
        _bazel_resolver = BazelResolver()
        _chunker = StandardChunker()
    except Exception as e:
        print(f"Worker initialization failed: {e}")

def process_file(file_path: str) -> List[Chunk]:
    global _parser, _maven_resolver, _bazel_resolver, _chunker
    try:
        # Check if initialized
        if _parser is None:
            # Fallback if init_worker wasn't called or failed
            init_worker()

        if not file_path.endswith(".java"):
            return []

        with open(file_path, 'rb') as f:
            content = f.read()

        parsed_result = _parser.parse(content, file_path)

        deps = _maven_resolver.resolve(file_path)
        # Extend with Bazel deps
        bazel_deps = _bazel_resolver.resolve(file_path)
        # Avoid duplicate deps?
        # Simple deduplication based on name
        existing_names = {d.name for d in deps}
        for d in bazel_deps:
            if d.name not in existing_names:
                deps.append(d)
                existing_names.add(d.name)

        # Get git metadata
        metadata = get_file_commit_info(file_path)

        chunks = _chunker.chunk(parsed_result, deps, file_path, metadata=metadata)
        return chunks
    except Exception as e:
        # Log error but don't stop processing
        print(f"Error processing {file_path}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Scalable Code Chunker")
    parser.add_argument("source_dir", help="Root directory to scan")
    parser.add_argument("--output", "-o", help="Output file path", required=True)
    parser.add_argument("--format", "-f", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--workers", "-w", type=int, default=os.cpu_count(), help="Number of workers")

    args = parser.parse_args()

    start_time = time.time()

    # Verify output directory
    output_dir = os.path.dirname(os.path.abspath(args.output))
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Find files
    print(f"Scanning {args.source_dir} for Java files...")
    files = []
    for root, dirs, filenames in os.walk(args.source_dir):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for name in filenames:
            if name.endswith(".java"):
                files.append(os.path.join(root, name))

    print(f"Found {len(files)} files. Processing with {args.workers} workers...")

    # Select writer
    if args.format == "json":
        writer = JSONWriter()
    else:
        writer = TextWriter()

    # Clear output file
    if os.path.exists(args.output):
        os.remove(args.output)

    # Process
    # Use chunksize for better performance with many small files
    chunk_size = max(1, len(files) // (args.workers * 4))

    with multiprocessing.Pool(processes=args.workers, initializer=init_worker) as pool:
        # imap_unordered is good for streaming
        processed_count = 0
        for chunks in pool.imap_unordered(process_file, files, chunksize=chunk_size):
            if chunks:
                writer.write(chunks, args.output)
                processed_count += 1

            # Progress indicator could be added here

    elapsed = time.time() - start_time
    print(f"Done. Processed {processed_count} files in {elapsed:.2f}s. Output written to {args.output}")

if __name__ == "__main__":
    main()

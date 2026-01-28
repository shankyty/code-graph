import sys
import argparse
import os
import multiprocessing
import time
from typing import List, Optional, Any, Tuple, Dict
from src.core.writers import JSONWriter, TextWriter
from src.core.interfaces import Chunk
from src.utils.git import get_file_commit_info, get_bulk_commit_info
from src.ui import run_tui

# Global worker state
_parser = None
_maven_resolver = None
_bazel_resolver = None
_chunker = None
_status_dict = None
_git_metadata = None

def init_worker(status_dict: Optional[Any] = None, git_metadata: Optional[Dict] = None):
    """Initialize worker process with parser, resolvers, and status tracker."""
    global _parser, _maven_resolver, _bazel_resolver, _chunker, _status_dict, _git_metadata

    # Store the shared status dictionary
    if status_dict is not None:
        _status_dict = status_dict

    # Store git metadata
    if git_metadata is not None:
        _git_metadata = git_metadata
    else:
        _git_metadata = {}

    # Import inside worker
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

def process_file(file_path: str) -> Tuple[str, List[Chunk]]:
    global _parser, _maven_resolver, _bazel_resolver, _chunker, _status_dict, _git_metadata

    pid = os.getpid()
    # Update status to processing
    if _status_dict is not None:
        _status_dict[pid] = {"file": file_path, "status": "Processing"}

    try:
        # Check if initialized
        if _parser is None:
            # Fallback if init_worker wasn't called or failed
            init_worker()

        if not file_path.endswith(".java"):
            return file_path, []

        with open(file_path, 'rb') as f:
            content = f.read()

        parsed_result = _parser.parse(content, file_path)

        deps = _maven_resolver.resolve(file_path)
        # Extend with Bazel deps
        bazel_deps = _bazel_resolver.resolve(file_path)

        existing_names = {d.name for d in deps}
        for d in bazel_deps:
            if d.name not in existing_names:
                deps.append(d)
                existing_names.add(d.name)

        # Get git metadata
        metadata = None
        if _git_metadata:
             metadata = _git_metadata.get(file_path)

        if metadata is None:
             metadata = get_file_commit_info(file_path)

        chunks = _chunker.chunk(parsed_result, deps, file_path, metadata=metadata)
        return file_path, chunks
    except Exception as e:
        # Log error but don't stop processing
        print(f"Error processing {file_path}: {e}")
        if _status_dict is not None:
             _status_dict[pid] = {"file": file_path, "status": f"Error: {str(e)}"}
        return file_path, []
    finally:
        # Update status to Idle/Done
        if _status_dict is not None:
            _status_dict[pid] = {"file": file_path, "status": "Idle"}

def main():
    parser = argparse.ArgumentParser(description="Scalable Code Chunker")
    parser.add_argument("source_dir", help="Root directory to scan")
    parser.add_argument("--output", "-o", help="Output file path", required=True)
    parser.add_argument("--format", "-f", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--workers", "-w", type=int, default=os.cpu_count(), help="Number of workers")
    parser.add_argument("--no-tui", action="store_true", help="Disable TUI (Job Mode)")

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

    # Load git metadata
    print("Loading git metadata...")
    git_metadata = get_bulk_commit_info(files)
    print(f"Loaded metadata for {len(git_metadata)} files.")

    # Select writer
    if args.format == "json":
        writer = JSONWriter()
    else:
        writer = TextWriter()

    # Clear output file
    if os.path.exists(args.output):
        os.remove(args.output)

    # Process
    chunk_size = max(1, len(files) // (args.workers * 4))

    # Determine execution mode
    use_tui = not args.no_tui and os.isatty(sys.stdout.fileno())

    if use_tui:
        # Create Manager for shared state
        with multiprocessing.Manager() as manager:
            status_dict = manager.dict()

            # Initialize pool with status_dict and git_metadata
            with multiprocessing.Pool(processes=args.workers, initializer=init_worker, initargs=(status_dict, git_metadata)) as pool:
                # Start processing
                result_iter = pool.imap_unordered(process_file, files, chunksize=chunk_size)

                # Delegate loop to UI handler
                run_tui(status_dict, result_iter, writer, args.output, files=files)
    else:
        # Job Mode (No TUI)
        print("Running in Job Mode (No TUI)")
        with multiprocessing.Pool(processes=args.workers, initializer=init_worker, initargs=(None, git_metadata)) as pool:
            result_iter = pool.imap_unordered(process_file, files, chunksize=chunk_size)

            processed_count = 0
            for file_path, chunks in result_iter:
                if chunks:
                    writer.write(chunks, args.output)
                    processed_count += 1

                # Simple progress logging
                if processed_count % 10 == 0:
                     print(f"Processed {processed_count}/{len(files)} files...")

    elapsed = time.time() - start_time
    print(f"Done. Processed {len(files)} files in {elapsed:.2f}s. Output written to {args.output}")

if __name__ == "__main__":
    main()

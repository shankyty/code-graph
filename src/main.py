import sys
import argparse
import os
import multiprocessing
import time
import hashlib
import json
from typing import List, Optional, Any, Tuple
from src.core.writers import JSONWriter, TextWriter
from src.core.interfaces import Chunk
from src.ui import run_tui

# Global worker state
_parser = None
_maven_resolver = None
_bazel_resolver = None
_chunker = None
_status_dict = None
_output_dir = None

def init_worker(status_dict: Optional[Any] = None, output_dir: Optional[str] = None):
    """Initialize worker process with parser, resolvers, and status tracker."""
    global _parser, _maven_resolver, _bazel_resolver, _chunker, _status_dict, _output_dir

    # Store the shared status dictionary
    if status_dict is not None:
        _status_dict = status_dict

    _output_dir = output_dir

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

def calculate_checksum(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_file(file_path: str) -> Tuple[str, List[Chunk]]:
    global _parser, _maven_resolver, _bazel_resolver, _chunker, _status_dict, _output_dir

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

        # Checksum logic
        try:
            current_checksum = calculate_checksum(file_path)

            # Check if output already exists and is up to date
            if _output_dir:
                rel_path = file_path.lstrip(os.sep)
                if rel_path.startswith('.' + os.sep):
                    rel_path = rel_path[2:]

                # Assume JSON format for caching check
                json_path = os.path.join(_output_dir, rel_path + ".json")

                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Check metadata
                            if 'metadata' in data and data['metadata'] and 'source_checksum' in data['metadata']:
                                if data['metadata']['source_checksum'] == current_checksum:
                                    # Cache hit
                                    if _status_dict is not None:
                                        _status_dict[pid] = {"file": file_path, "status": "Skipped (Cached)"}
                                    return file_path, []
                    except Exception:
                        pass # Ignore read errors, re-process
        except Exception as e:
            print(f"Error calculating checksum for {file_path}: {e}")
            return file_path, []

        t_start = time.time()
        with open(file_path, 'rb') as f:
            content = f.read()

        t0 = time.time()
        parsed_result = _parser.parse(content, file_path)
        t_parse = time.time() - t0

        t0 = time.time()
        deps = _maven_resolver.resolve(file_path)
        t_maven = time.time() - t0

        t0 = time.time()
        # Extend with Bazel deps
        bazel_deps = _bazel_resolver.resolve(file_path)
        t_bazel = time.time() - t0

        existing_names = {d.name for d in deps}
        for d in bazel_deps:
            if d.name not in existing_names:
                deps.append(d)
                existing_names.add(d.name)

        # Prepare metrics and metadata
        metrics = {
            "parse_time_ms": t_parse * 1000,
            "maven_resolve_time_ms": t_maven * 1000,
            "bazel_resolve_time_ms": t_bazel * 1000,
            "total_processing_time_ms": (time.time() - t_start) * 1000,
            "source_checksum": current_checksum
        }

        chunks = _chunker.chunk(parsed_result, deps, file_path, metadata=metrics)
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
    parser.add_argument("--output", "-o", help="Output directory", required=True)
    parser.add_argument("--format", "-f", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--workers", "-w", type=int, default=os.cpu_count(), help="Number of workers")
    parser.add_argument("--no-tui", action="store_true", help="Disable TUI (Job Mode)")

    args = parser.parse_args()

    start_time = time.time()

    source_dir = os.path.expanduser(args.source_dir)
    output_arg = os.path.expanduser(args.output)

    # Verify output directory
    output_dir = os.path.abspath(output_arg)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Find files
    print(f"Scanning {source_dir} for Java files...")
    files = []
    for root, dirs, filenames in os.walk(source_dir):
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

    # Process
    chunk_size = max(1, len(files) // (args.workers * 4))

    # Determine execution mode
    use_tui = not args.no_tui and os.isatty(sys.stdout.fileno())

    init_args = (None, output_dir)

    if use_tui:
        # Create Manager for shared state
        with multiprocessing.Manager() as manager:
            status_dict = manager.dict()
            # Pass status_dict and output_dir
            init_args = (status_dict, output_dir)

            # Initialize pool with status_dict
            with multiprocessing.Pool(processes=args.workers, initializer=init_worker, initargs=init_args) as pool:
                # Start processing
                result_iter = pool.imap_unordered(process_file, files, chunksize=chunk_size)

                # Delegate loop to UI handler
                run_tui(status_dict, result_iter, writer, output_dir, files=files)
    else:
        # Job Mode (No TUI)
        print("Running in Job Mode (No TUI)")
        with multiprocessing.Pool(processes=args.workers, initializer=init_worker, initargs=init_args) as pool:
            result_iter = pool.imap_unordered(process_file, files, chunksize=chunk_size)

            processed_count = 0
            skipped_count = 0
            for file_path, chunks in result_iter:
                if chunks:
                    writer.write(chunks, output_dir)
                    processed_count += 1
                else:
                    skipped_count += 1

                # Simple progress logging
                total_done = processed_count + skipped_count
                if total_done % 10 == 0:
                     print(f"Processed {total_done}/{len(files)} files (Skipped: {skipped_count})...")

    elapsed = time.time() - start_time
    print(f"Done. Processed {len(files)} files in {elapsed:.2f}s. Output written to {output_dir}")

if __name__ == "__main__":
    main()

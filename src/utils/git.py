import subprocess
import os
from typing import Optional, Dict, List

def get_file_commit_info(file_path: str) -> Optional[Dict[str, str]]:
    """
    Extracts git commit metadata for the given file.
    Returns None if not in a git repo or if error occurs.
    """
    try:
        # Check if file exists to avoid git errors
        if not os.path.exists(file_path):
            return None

        # Run git log -1 --format=%H|%an|%at -- <file_path>
        # We need to run this from the file's directory or repo root.
        # It's safest to run where the file is, or pass absolute path.
        abs_path = os.path.abspath(file_path)
        directory = os.path.dirname(abs_path)

        # Check if directory is a git repo (or inside one)
        # git rev-parse --is-inside-work-tree

        cmd = ["git", "log", "-1", "--format=%H|%an|%at", "--", os.path.basename(abs_path)]

        # Run process
        result = subprocess.run(
            cmd,
            cwd=directory,
            capture_output=True,
            text=True,
            check=False # Don't raise on non-zero exit, just handle it
        )

        if result.returncode != 0:
            return None

        output = result.stdout.strip()
        if not output:
            return None

        parts = output.split('|')
        if len(parts) >= 3:
            return {
                "commit_hash": parts[0],
                "author_name": parts[1],
                "timestamp": parts[2]
            }

    except Exception:
        # Fail gracefully
        pass

    return None

def get_bulk_commit_info(file_paths: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Retrieves git commit metadata for multiple files in a single pass.
    Returns a dictionary mapping absolute file path to commit info.
    """
    if not file_paths:
        return {}

    # Deduplicate and normalize
    abs_paths = [os.path.abspath(p) for p in file_paths]

    # Use the first path to find the repo root.
    # Assumption: all files are in the same git repo.
    # If not, this might fail for some files, but that's an edge case we can accept for "bulk" op.
    start_dir = os.path.dirname(abs_paths[0])

    try:
        # Find git root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start_dir,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return {}

        repo_root = result.stdout.strip()
        if not repo_root:
            return {}

        # Determine common path to limit git log scope
        try:
            common_path = os.path.commonpath(abs_paths)
            # If common path is not absolute (should be), make it so
            if not os.path.isabs(common_path):
                common_path = os.path.abspath(common_path)
        except ValueError:
            # Files on different drives on Windows?
            common_path = repo_root

        # Make sure common_path is inside repo_root
        if not common_path.startswith(repo_root):
            # This happens if files are outside repo?
            common_path = repo_root

        # Prepare mapping of relative paths (as git sees them) to absolute paths
        rel_to_abs = {}
        target_files = set()

        for p in abs_paths:
            try:
                rel = os.path.relpath(p, repo_root)
                # Normalize separators for matching git output
                rel_git = rel.replace(os.sep, '/')
                rel_to_abs[rel_git] = p
                target_files.add(rel_git)
            except ValueError:
                continue

        if not target_files:
            return {}

        # Relpath for the command scope
        scope_rel = os.path.relpath(common_path, repo_root)
        if scope_rel == "." or scope_rel == "":
            scope_args = []
        else:
            scope_args = [scope_rel]

        # Run git log
        # We assume standard filenames (no newlines in names)
        cmd = ["git", "log", "--name-only", "--format=COMMIT|%H|%an|%at", "--"] + scope_args

        process = subprocess.Popen(
            cmd,
            cwd=repo_root,
            stdout=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        metadata_map = {}
        current_commit = None
        remaining_files = len(target_files)

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            if line.startswith("COMMIT|"):
                parts = line.split("|")
                if len(parts) >= 4:
                    current_commit = {
                        "commit_hash": parts[1],
                        "author_name": parts[2],
                        "timestamp": parts[3]
                    }
            else:
                # It is a file path
                # Git output always uses forward slashes
                if line in target_files:
                    abs_p = rel_to_abs[line]
                    if abs_p not in metadata_map:
                        metadata_map[abs_p] = current_commit
                        remaining_files -= 1
                        if remaining_files == 0:
                            break

        process.terminate()
        if process.stdout:
            process.stdout.close()
        # Clean up process
        process.wait()

        return metadata_map

    except Exception as e:
        print(f"Error in bulk git metadata: {e}")
        return {}

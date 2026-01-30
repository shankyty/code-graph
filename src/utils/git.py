import subprocess
import os
from typing import Optional, Dict

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

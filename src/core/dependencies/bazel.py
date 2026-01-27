import os
import re
from functools import lru_cache
from src.core.interfaces import DependencyResolver, Dependency
from typing import List, Optional

class BazelResolver(DependencyResolver):
    def resolve(self, file_path: str) -> List[Dependency]:
        build_file = self._find_build_file(file_path)
        if not build_file:
            return []
        # Return a copy to avoid side effects on cached list
        return list(self._parse_build_file(build_file))

    @lru_cache(maxsize=None)
    def _find_build_file(self, file_path: str) -> Optional[str]:
        current_dir = os.path.dirname(os.path.abspath(file_path))
        # Traverse up to root, but stop if we hit root or some boundary.
        # Bazel usually has BUILD files in package directories.
        # So we look in current directory, then parent, until we find one or hit WORKSPACE?
        # Actually Bazel packages are defined by BUILD files. If a file is in a package,
        # its BUILD file is in the package root.
        # So finding the nearest ancestor with a BUILD file is correct.

        while True:
            for name in ["BUILD", "BUILD.bazel"]:
                build_path = os.path.join(current_dir, name)
                if os.path.exists(build_path):
                    return build_path

            parent = os.path.dirname(current_dir)
            if parent == current_dir:
                break
            current_dir = parent
        return None

    @lru_cache(maxsize=None)
    def _parse_build_file(self, build_path: str) -> List[Dependency]:
        deps = []
        try:
            with open(build_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Use word boundary \b to avoid matching suffix like runtime_deps
            # and verify it matches deps = [...]
            # Note: deps can be a list variable too, but usually inline list in rules.
            matches = re.findall(r'\bdeps\s*=\s*\[(.*?)\]', content, re.DOTALL)

            for match in matches:
                # Remove comments
                lines = match.split('\n')
                clean_lines = []
                for line in lines:
                    if '#' in line:
                        # naive comment stripping: remove everything after #
                        # but # can be inside string? rare for dependency labels.
                        line = line.split('#')[0]
                    clean_lines.append(line)

                block_content = " ".join(clean_lines)

                # Extract strings: "..." or '...'
                # We iterate over strings found
                dep_strings = re.findall(r'[\'"](.*?)[\'"]', block_content)

                for dep_str in dep_strings:
                    if dep_str: # ignore empty strings
                        deps.append(Dependency(name=dep_str, type="bazel"))

        except Exception as e:
            print(f"Error parsing BUILD file {build_path}: {e}")

        return deps

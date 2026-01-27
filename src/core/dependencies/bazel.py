import os
import re
from functools import lru_cache
from src.core.interfaces import DependencyResolver, Dependency
from typing import List, Optional

class BazelResolver(DependencyResolver):
    def resolve(self, file_path: str) -> List[Dependency]:
        build_file = self._find_build_file_from_dir(os.path.dirname(os.path.abspath(file_path)))
        if not build_file:
            return []
        # Return a copy to avoid side effects on cached list
        return list(self._parse_build_file(build_file))

    @lru_cache(maxsize=None)
    def _find_build_file_from_dir(self, current_dir: str) -> Optional[str]:
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

            # Find all "deps = [" occurrences
            # We iterate through the file content to find matches and then extract the balanced block
            start_indices = [m.end() for m in re.finditer(r'\bdeps\s*=\s*\[', content)]

            for start_idx in start_indices:
                block_content = self._extract_balanced_block(content, start_idx)
                if block_content:
                     # Extract strings: "..." or '...'
                    dep_strings = re.findall(r'[\'"](.*?)[\'"]', block_content)
                    for dep_str in dep_strings:
                        if dep_str:
                             # Filter out things that look like keys in select dicts if possible,
                             # but regex above captures keys too.
                             # However, for deps, keys in select are usually conditions like "//conditions:default".
                             # Values are lists of deps.
                             # If we just grab all strings, we get conditions too.
                             # This is acceptable for a "best effort" parser without a full Starlark interpreter.
                            deps.append(Dependency(name=dep_str, type="bazel"))

        except Exception as e:
            print(f"Error parsing BUILD file {build_path}: {e}")

        return deps

    def _extract_balanced_block(self, content: str, start_index: int) -> Optional[str]:
        """Extracts content until the closing bracket ']', handling nested brackets."""
        depth = 1
        current_idx = start_index
        length = len(content)

        while current_idx < length and depth > 0:
            char = content[current_idx]
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
            current_idx += 1

        if depth == 0:
            # Return content excluding the last closing bracket
            return content[start_index : current_idx - 1]
        return None

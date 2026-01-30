import json
import os
from src.core.interfaces import Writer, Chunk
from dataclasses import asdict
from typing import List

class JSONWriter(Writer):
    def write(self, chunks: List[Chunk], output_path: str) -> None:
        # output_path is treated as a root directory
        base_dir = os.path.abspath(output_path)
        os.makedirs(base_dir, exist_ok=True)

        for chunk in chunks:
            # Construct filename: <base_dir>/<rel_path>.json
            # Remove leading ./ or / from chunk.file_path to ensure relative join
            rel_path = chunk.file_path.lstrip(os.sep)
            if rel_path.startswith('.' + os.sep):
                rel_path = rel_path[2:]

            dest_path = os.path.join(base_dir, rel_path + ".json")

            # Ensure parent dirs exist
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            with open(dest_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(chunk), f, indent=2)

class TextWriter(Writer):
    def write(self, chunks: List[Chunk], output_path: str) -> None:
        base_dir = os.path.abspath(output_path)
        os.makedirs(base_dir, exist_ok=True)

        for chunk in chunks:
            rel_path = chunk.file_path.lstrip(os.sep)
            if rel_path.startswith('.' + os.sep):
                rel_path = rel_path[2:]

            dest_path = os.path.join(base_dir, rel_path + ".txt")
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            with open(dest_path, 'w', encoding='utf-8') as f:
                self._write_chunk(f, chunk)

    def _write_chunk(self, f, chunk, indent=0):
        prefix = "  " * indent
        f.write(f"{prefix}--- {chunk.kind.upper()} {chunk.id} ---\n")
        f.write(f"{prefix}Language: {chunk.language}\n")

        if chunk.package:
            f.write(f"{prefix}Package: {chunk.package}\n")

        if chunk.imports:
            f.write(f"{prefix}Imports:\n")
            for imp in chunk.imports:
                f.write(f"{prefix}  {imp}\n")

        if chunk.dependencies:
            f.write(f"{prefix}Dependencies:\n")
            for dep in chunk.dependencies:
                ver = f":{dep.version}" if dep.version else ""
                f.write(f"{prefix}  {dep.name}{ver} ({dep.type})\n")

        if chunk.metadata:
            f.write(f"{prefix}Metadata: {chunk.metadata}\n")

        if chunk.code:
            f.write(f"{prefix}Code:\n")
            # Indent code block
            for line in chunk.code.splitlines():
                f.write(f"{prefix}  {line}\n")
            f.write("\n")

        if chunk.children:
            f.write(f"{prefix}Children:\n")
            for child in chunk.children:
                self._write_chunk(f, child, indent + 1)

        f.write(f"{prefix}--- END {chunk.kind.upper()} ---\n\n")

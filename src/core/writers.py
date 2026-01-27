import json
import os
from src.core.interfaces import Writer, Chunk
from dataclasses import asdict
from typing import List

class JSONWriter(Writer):
    def write(self, chunks: List[Chunk], output_path: str) -> None:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        # Append mode for streaming
        with open(output_path, 'a', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(asdict(chunk)) + '\n')

class TextWriter(Writer):
    def write(self, chunks: List[Chunk], output_path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'a', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(f"--- START CHUNK {chunk.file_path} ---\n")
                f.write(f"Language: {chunk.language}\n")
                if chunk.metadata:
                    f.write("Metadata:\n")
                    # Handle dict metadata
                    if isinstance(chunk.metadata, dict):
                        for k, v in chunk.metadata.items():
                            f.write(f"  {k}: {v}\n")
                    else:
                        f.write(f"  {chunk.metadata}\n")
                f.write("Imports:\n")
                for imp in chunk.imports:
                    f.write(f"  {imp}\n")
                f.write("Dependencies:\n")
                for dep in chunk.dependencies:
                    ver = f":{dep.version}" if dep.version else ""
                    f.write(f"  {dep.name}{ver} ({dep.type})\n")
                f.write("Code:\n")
                f.write(chunk.code)
                # Ensure newline at end of code
                if not chunk.code.endswith('\n'):
                    f.write('\n')
                f.write(f"--- END CHUNK {chunk.file_path} ---\n\n")

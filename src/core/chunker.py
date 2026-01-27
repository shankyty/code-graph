from src.core.interfaces import Chunker, Chunk, ParsedResult, Dependency
from typing import List, Optional, Any
import os

class StandardChunker(Chunker):
    def chunk(self, parsed_result: ParsedResult, dependencies: List[Dependency], file_path: str, metadata: Optional[Any] = None) -> List[Chunk]:
        ext = os.path.splitext(file_path)[1].lower()
        language = "unknown"
        if ext == ".java":
            language = "java"
        elif ext in [".py"]:
            language = "python"
        elif ext in [".go"]:
            language = "go"

        # Currently creating one chunk per file.
        chunk = Chunk(
            file_path=file_path,
            language=language,
            code=parsed_result.code,
            imports=parsed_result.imports,
            dependencies=dependencies,
            metadata=metadata
        )
        return [chunk]

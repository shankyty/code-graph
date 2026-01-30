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

        chunks = []

        # If we have parsed classes (currently only populated for Java), create hierarchical chunks
        if parsed_result.classes:
            # We process all classes found, but typically there's one main class.
            # If the requirement is strict 1 source file -> 1 JSON file,
            # and that JSON file has a top-level object (Class Chunk).
            # We will return the first class as the primary chunk.

            # Note: If there are multiple top-level classes (e.g. package-private ones),
            # we might lose them if we only return one.
            # But adhering to "top level object will represent class level chunk" implies singular.
            # We'll stick to the first one for now.

            main_class = parsed_result.classes[0]

            class_chunk_id = f"{file_path}::{main_class.name}"
            class_chunk = Chunk(
                id=class_chunk_id,
                file_path=file_path,
                language=language,
                kind="class",
                code=main_class.code,
                metadata=metadata,
                package=main_class.package,
                extends=main_class.extends,
                implements=main_class.implements,
                imports=parsed_result.imports, # File level imports apply to the class
                dependencies=dependencies
            )

            # Create Method Chunks
            for method in main_class.methods:
                method_chunk_id = f"{class_chunk_id}::{method.name}"
                method_chunk = Chunk(
                    id=method_chunk_id,
                    file_path=file_path,
                    language=language,
                    kind="method",
                    code=method.code,
                    signature=method.signature,
                    is_override=method.is_override,
                    parent_id=class_chunk_id,
                    imports=method.used_imports
                    # dependencies for methods: could filter file deps if we knew which apply
                )
                class_chunk.children.append(method_chunk)

            chunks.append(class_chunk)

        else:
            # Fallback for files where no classes were parsed (e.g. interfaces/enums not yet handled, or other languages)
            chunk = Chunk(
                id=file_path,
                file_path=file_path,
                language=language,
                kind="file",
                code=parsed_result.code,
                imports=parsed_result.imports,
                dependencies=dependencies,
                metadata=metadata
            )
            chunks.append(chunk)

        return chunks

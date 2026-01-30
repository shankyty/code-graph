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

        sub_chunks = []
        class_metadata_list = []

        if parsed_result.structure and 'classes' in parsed_result.structure:
            for cls in parsed_result.structure['classes']:
                # Prepare Class Metadata
                cls_meta = {
                    "name": cls['name'],
                    "extends": cls['extends'],
                    "implements": cls['implements'],
                    "composition": cls['fields'], # Fields represent composition
                    "constructors": [c['signature'] for c in cls['constructors']]
                }
                class_metadata_list.append(cls_meta)

                # Create Method Sub-Chunks
                # Combine methods and constructors for sub-chunks
                all_methods = cls['constructors'] + cls['methods']
                for m in all_methods:
                     method_chunk = Chunk(
                         file_path=file_path,
                         language=language,
                         code=m['code'],
                         imports=[], # Sub-chunks rely on parent context for imports
                         dependencies=[],
                         metadata={
                             "type": "method",
                             "name": m['name'],
                             "signature": m['signature']
                         }
                     )
                     sub_chunks.append(method_chunk)

        # Merge calculated class metadata into provided metadata
        final_metadata = metadata if metadata else {}
        if isinstance(final_metadata, dict):
             final_metadata['classes'] = class_metadata_list

        # Currently creating one chunk per file (Top Level), containing sub-chunks
        chunk = Chunk(
            file_path=file_path,
            language=language,
            code=parsed_result.code,
            imports=parsed_result.imports,
            dependencies=dependencies,
            metadata=final_metadata,
            sub_chunks=sub_chunks
        )
        return [chunk]

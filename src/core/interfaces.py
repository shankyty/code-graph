from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

@dataclass
class Dependency:
    name: str
    version: Optional[str] = None
    type: str = "unknown" # "maven", "bazel", etc.

@dataclass
class ParsedResult:
    code: str
    imports: List[str]
    structure: Optional[Dict[str, Any]] = None

@dataclass
class Chunk:
    file_path: str
    language: str
    code: str
    imports: List[str]
    dependencies: List[Dependency]
    metadata: Optional[Any] = None
    sub_chunks: List["Chunk"] = field(default_factory=list)

class Parser(ABC):
    @abstractmethod
    def parse(self, file_content: bytes, file_path: str) -> ParsedResult:
        """Parses the file content and returns the extracted code and imports."""
        pass

class DependencyResolver(ABC):
    @abstractmethod
    def resolve(self, file_path: str) -> List[Dependency]:
        """Resolves dependencies for the given file path."""
        pass

class Chunker(ABC):
    @abstractmethod
    def chunk(self, parsed_result: ParsedResult, dependencies: List[Dependency], file_path: str, metadata: Optional[Any] = None) -> List[Chunk]:
        """Creates chunks from the parsed result, dependencies, and optional metadata."""
        pass

class Writer(ABC):
    @abstractmethod
    def write(self, chunks: List[Chunk], output_path: str) -> None:
        """Writes the chunks to the output path."""
        pass

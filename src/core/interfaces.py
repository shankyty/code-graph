from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class Dependency:
    name: str
    version: Optional[str] = None
    type: str = "unknown" # "maven", "bazel", etc.

@dataclass
class ParsedResult:
    code: str
    imports: List[str]

@dataclass
class Chunk:
    file_path: str
    language: str
    code: str
    imports: List[str]
    dependencies: List[Dependency]
    metadata: Optional[Any] = None

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
    def chunk(self, parsed_result: ParsedResult, dependencies: List[Dependency], file_path: str) -> List[Chunk]:
        """Creates chunks from the parsed result and dependencies."""
        pass

class Writer(ABC):
    @abstractmethod
    def write(self, chunks: List[Chunk], output_path: str) -> None:
        """Writes the chunks to the output path."""
        pass

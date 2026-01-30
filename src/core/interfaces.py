from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple

@dataclass
class Dependency:
    name: str
    version: Optional[str] = None
    type: str = "unknown" # "maven", "bazel", etc.

@dataclass
class MethodNode:
    name: str
    signature: str
    code: str
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    used_imports: List[str] = field(default_factory=list)
    is_override: bool = False
    annotations: List[str] = field(default_factory=list)

@dataclass
class ClassNode:
    name: str
    code: str
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    package: str = ""
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    methods: List[MethodNode] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)

@dataclass
class ParsedResult:
    code: str
    imports: List[str]
    classes: List[ClassNode] = field(default_factory=list)

@dataclass
class Chunk:
    id: str
    file_path: str
    language: str
    kind: str # "class", "method"
    code: str
    metadata: Optional[Any] = None
    # Class details
    package: str = ""
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    # Method details
    signature: Optional[str] = None
    is_override: bool = False
    # Hierarchy
    parent_id: Optional[str] = None
    children: List[Chunk] = field(default_factory=list)

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

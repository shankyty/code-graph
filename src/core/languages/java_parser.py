import tree_sitter_java
from tree_sitter import Language, Parser as TSParser, Query, QueryCursor
from src.core.interfaces import Parser, ParsedResult
from typing import List

class JavaParser(Parser):
    def __init__(self):
        try:
            self.language = Language(tree_sitter_java.language())
            self.parser = TSParser(self.language)
            # Pre-compile query for performance
            self.import_query = Query(self.language, "(import_declaration) @import")
        except Exception as e:
            print(f"Error loading Java language: {e}")
            raise e

    def parse(self, file_content: bytes, file_path: str) -> ParsedResult:
        tree = self.parser.parse(file_content)
        root = tree.root_node

        imports = self._extract_imports(root, file_content)

        code = file_content.decode('utf-8', errors='replace')

        return ParsedResult(code=code, imports=imports)

    def _extract_imports(self, root_node, file_content: bytes) -> List[str]:
        imports = []
        try:
            # Note: tree-sitter API usage varies by version.
            # This implementation targets tree-sitter >= 0.22.0.
            cursor = QueryCursor(self.import_query)
            captures = cursor.captures(root_node)

            for name, nodes in captures.items():
                if name == 'import':
                    for node in nodes:
                        imports.append(node.text.decode('utf-8', errors='replace'))
        except Exception as e:
            print(f"Error extracting imports: {e}")

        return imports

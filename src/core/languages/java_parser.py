import tree_sitter_java
from tree_sitter import Language, Parser as TSParser, Query, QueryCursor, Node
from src.core.interfaces import Parser, ParsedResult, ClassNode, MethodNode
from typing import List, Optional

class JavaParser(Parser):
    def __init__(self):
        try:
            self.language = Language(tree_sitter_java.language())
            self.parser = TSParser(self.language)

            # Pre-compile queries
            self.import_query = Query(self.language, "(import_declaration) @import")
            self.package_query = Query(self.language, "(package_declaration) @package")
            self.class_query = Query(self.language, "(class_declaration) @class")
            self.method_query = Query(self.language, "(method_declaration) @method")

        except Exception as e:
            print(f"Error loading Java language: {e}")
            raise e

    def parse(self, file_content: bytes, file_path: str) -> ParsedResult:
        tree = self.parser.parse(file_content)
        root = tree.root_node

        # Decode once
        code_str = file_content.decode('utf-8', errors='replace')

        imports = self._extract_imports(root, code_str)
        package = self._extract_package(root, code_str)

        classes = self._extract_classes(root, code_str, imports, package)

        return ParsedResult(code=code_str, imports=imports, classes=classes)

    def _extract_package(self, root_node, code_str: str) -> str:
        cursor = QueryCursor(self.package_query)
        captures = cursor.captures(root_node)
        for name, nodes in captures.items():
            if name == 'package':
                for node in nodes:
                    text = code_str[node.start_byte:node.end_byte]
                    return text.replace('package ', '').replace(';', '').strip()
        return ""

    def _extract_imports(self, root_node, code_str: str) -> List[str]:
        imports = []
        cursor = QueryCursor(self.import_query)
        captures = cursor.captures(root_node)

        if 'import' in captures:
             for node in captures['import']:
                 text = code_str[node.start_byte:node.end_byte]
                 imports.append(text.replace('import ', '').replace(';', '').strip())
        return imports

    def _extract_classes(self, root_node, code_str: str, file_imports: List[str], package: str) -> List[ClassNode]:
        classes = []
        cursor = QueryCursor(self.class_query)
        captures = cursor.captures(root_node)

        if 'class' in captures:
            for node in captures['class']:
                classes.append(self._parse_class_node(node, code_str, file_imports, package))

        return classes

    def _parse_class_node(self, node: Node, code_str: str, file_imports: List[str], package: str) -> ClassNode:
        name_node = node.child_by_field_name('name')
        name = code_str[name_node.start_byte:name_node.end_byte] if name_node else "Anonymous"

        # Extends
        superclass_node = node.child_by_field_name('superclass')
        superclass = None
        if superclass_node:
            superclass = code_str[superclass_node.start_byte:superclass_node.end_byte].replace('extends ', '').strip()

        # Implements
        interfaces_node = node.child_by_field_name('interfaces')
        implements_list = []
        if interfaces_node:
            text = code_str[interfaces_node.start_byte:interfaces_node.end_byte]
            # text like "implements A, B"
            parts = text.replace('implements ', '').split(',')
            implements_list = [p.strip() for p in parts]

        # Annotations
        annotations = []
        modifiers_node = node.child_by_field_name('modifiers')
        if not modifiers_node:
             for child in node.children:
                 if child.type == 'modifiers':
                     modifiers_node = child
                     break

        if modifiers_node:
            for child in modifiers_node.children:
                if 'annotation' in child.type:
                     annotations.append(code_str[child.start_byte:child.end_byte])

        # Methods
        body_node = node.child_by_field_name('body')
        methods = []
        if body_node:
            methods = self._extract_methods(body_node, code_str, file_imports)

        class_code = code_str[node.start_byte:node.end_byte]

        return ClassNode(
            name=name,
            code=class_code,
            start_point=node.start_point,
            end_point=node.end_point,
            package=package,
            extends=superclass,
            implements=implements_list,
            methods=methods,
            annotations=annotations
        )

    def _extract_methods(self, class_body_node: Node, code_str: str, file_imports: List[str]) -> List[MethodNode]:
        methods = []
        cursor = QueryCursor(self.method_query)
        captures = cursor.captures(class_body_node)

        if 'method' in captures:
            for node in captures['method']:
                if node.parent != class_body_node:
                    continue
                methods.append(self._parse_method_node(node, code_str, file_imports))
        return methods

    def _parse_method_node(self, node: Node, code_str: str, file_imports: List[str]) -> MethodNode:
        name_node = node.child_by_field_name('name')
        name = code_str[name_node.start_byte:name_node.end_byte] if name_node else "unknown"

        body_node = node.child_by_field_name('body')
        if body_node:
            signature = code_str[node.start_byte:body_node.start_byte].strip()
        else:
            signature = code_str[node.start_byte:node.end_byte].strip()

        annotations = []
        is_override = False
        modifiers_node = node.child_by_field_name('modifiers')
        if not modifiers_node:
             for child in node.children:
                 if child.type == 'modifiers':
                     modifiers_node = child
                     break

        if modifiers_node:
            for child in modifiers_node.children:
                if 'annotation' in child.type:
                    anno_text = code_str[child.start_byte:child.end_byte]
                    annotations.append(anno_text)
                    if 'Override' in anno_text:
                        is_override = True

        used_imports = []
        method_code = code_str[node.start_byte:node.end_byte]
        for imp in file_imports:
            short_name = imp.split('.')[-1]
            if short_name in method_code:
                 used_imports.append(imp)

        return MethodNode(
            name=name,
            signature=signature,
            code=method_code,
            start_point=node.start_point,
            end_point=node.end_point,
            used_imports=used_imports,
            is_override=is_override,
            annotations=annotations
        )

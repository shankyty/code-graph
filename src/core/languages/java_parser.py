import tree_sitter_java
from tree_sitter import Language, Parser as TSParser, Query, QueryCursor, Node
from src.core.interfaces import Parser, ParsedResult
from typing import List, Dict, Any, Optional

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
        code_str = file_content.decode('utf-8', errors='replace')

        imports = self._extract_imports(root)
        classes = self._extract_classes(root, code_str)

        structure = {"classes": classes}

        return ParsedResult(code=code_str, imports=imports, structure=structure)

    def _extract_imports(self, root_node: Node) -> List[str]:
        imports = []
        try:
            cursor = QueryCursor(self.import_query)
            captures = cursor.captures(root_node)

            for name, nodes in captures.items():
                if name == 'import':
                    for node in nodes:
                        imports.append(node.text.decode('utf-8', errors='replace'))
        except Exception as e:
            print(f"Error extracting imports: {e}")

        return imports

    def _extract_classes(self, root_node: Node, code_str: str) -> List[Dict[str, Any]]:
        classes = []
        # Simple traversal for top-level classes/interfaces
        # NOTE: This does not currently handle nested classes deeply,
        # but will catch top-level ones which is typical for Java files.
        cursor = root_node.walk()

        children = root_node.children
        for child in children:
            if child.type in ('class_declaration', 'interface_declaration'):
                classes.append(self._parse_class_node(child, code_str))

        return classes

    def _parse_class_node(self, node: Node, code_str: str) -> Dict[str, Any]:
        class_info = {
            "name": "",
            "type": node.type, # class_declaration or interface_declaration
            "extends": None,
            "implements": [],
            "fields": [],
            "constructors": [],
            "methods": [],
            "start_byte": node.start_byte,
            "end_byte": node.end_byte
        }

        # Extract Name
        name_node = node.child_by_field_name('name')
        if name_node:
            class_info['name'] = code_str[name_node.start_byte:name_node.end_byte]

        # Extract Extends (superclass)
        superclass = node.child_by_field_name('superclass')
        if superclass:
             class_info['extends'] = code_str[superclass.start_byte:superclass.end_byte]

        # Extract Interfaces
        interfaces = node.child_by_field_name('interfaces')
        if interfaces:
             # interfaces node text is like "implements A, B"
             # We might want to parse it more granularly, but raw text is a good start.
             # Or we can iterate children of interfaces node
             for child in interfaces.children:
                 if child.type == 'type_list':
                      # deeper? usually it's just a list of types
                      pass
                 if child.type == 'type_identifier':
                     class_info['implements'].append(code_str[child.start_byte:child.end_byte])

             # Fallback if structure is slightly different (e.g. just raw text for now)
             if not class_info['implements']:
                  class_info['implements'].append(code_str[interfaces.start_byte:interfaces.end_byte])


        # Parse Body
        body_node = node.child_by_field_name('body')
        if body_node:
            for child in body_node.children:
                if child.type == 'field_declaration':
                    class_info['fields'].append(self._parse_field(child, code_str))
                elif child.type == 'constructor_declaration':
                    class_info['constructors'].append(self._parse_method(child, code_str, is_constructor=True))
                elif child.type == 'method_declaration':
                    class_info['methods'].append(self._parse_method(child, code_str, is_constructor=False))

        return class_info

    def _parse_field(self, node: Node, code_str: str) -> Dict[str, str]:
        # Field declaration: type + declarator
        type_node = node.child_by_field_name('type')
        declarator_node = node.child_by_field_name('declarator')

        field_type = code_str[type_node.start_byte:type_node.end_byte] if type_node else "unknown"
        name = ""
        if declarator_node:
             name_node = declarator_node.child_by_field_name('name')
             if name_node:
                 name = code_str[name_node.start_byte:name_node.end_byte]
             else:
                 # sometimes declarator is just the name identifier
                 name = code_str[declarator_node.start_byte:declarator_node.end_byte]

        return {"name": name, "type": field_type}

    def _parse_method(self, node: Node, code_str: str, is_constructor: bool) -> Dict[str, Any]:
        method_info = {
            "name": "",
            "signature": "",
            "code": code_str[node.start_byte:node.end_byte],
            "start_byte": node.start_byte,
            "end_byte": node.end_byte
        }

        name_node = node.child_by_field_name('name')
        if name_node:
            method_info['name'] = code_str[name_node.start_byte:name_node.end_byte]

        # Construct signature
        # For simplicity: Name + Parameters
        params_node = node.child_by_field_name('parameters')
        params_str = code_str[params_node.start_byte:params_node.end_byte] if params_node else "()"

        # Add return type for methods
        if not is_constructor:
             type_node = node.child_by_field_name('type')
             type_str = code_str[type_node.start_byte:type_node.end_byte] if type_node else "void"
             method_info['signature'] = f"{type_str} {method_info['name']}{params_str}"
        else:
             method_info['signature'] = f"{method_info['name']}{params_str}"

        return method_info

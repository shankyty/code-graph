import unittest
from src.core.chunker import StandardChunker
from src.core.interfaces import ParsedResult, Dependency, Chunk, ClassNode, MethodNode

class TestStandardChunker(unittest.TestCase):
    def test_chunk_with_classes(self):
        chunker = StandardChunker()

        # Mock parsed result
        method = MethodNode(
            name="main",
            signature="public static void main(String[] args)",
            code="...",
            start_point=(3, 4),
            end_point=(5, 5),
            used_imports=[]
        )

        cls = ClassNode(
            name="Test",
            code="public class Test { ... }",
            start_point=(1, 0),
            end_point=(6, 1),
            package="com.example",
            methods=[method]
        )

        parsed_result = ParsedResult(
            code="...",
            imports=["java.util.List"],
            classes=[cls]
        )

        dependencies = [Dependency(name="junit", version="4.12", type="maven")]
        file_path = "src/Test.java"

        chunks = chunker.chunk(parsed_result, dependencies, file_path)

        self.assertEqual(len(chunks), 1)
        chunk = chunks[0]
        self.assertEqual(chunk.kind, "class")
        self.assertEqual(chunk.file_path, "src/Test.java")
        self.assertEqual(chunk.id, "src/Test.java::Test")
        self.assertEqual(chunk.package, "com.example")

        self.assertEqual(len(chunk.children), 1)
        child = chunk.children[0]
        self.assertEqual(child.kind, "method")
        self.assertTrue(child.id.endswith("::main"))

if __name__ == '__main__':
    unittest.main()

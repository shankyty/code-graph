import unittest
from src.core.chunker import StandardChunker
from src.core.interfaces import ParsedResult, Dependency, Chunk

class TestStandardChunker(unittest.TestCase):
    def test_chunk(self):
        chunker = StandardChunker()
        parsed_result = ParsedResult(code="public class Test {}", imports=["import java.util.List;"])
        dependencies = [Dependency(name="junit", version="4.12", type="maven")]
        file_path = "src/Test.java"

        chunks = chunker.chunk(parsed_result, dependencies, file_path)

        self.assertEqual(len(chunks), 1)
        chunk = chunks[0]
        self.assertEqual(chunk.file_path, "src/Test.java")
        self.assertEqual(chunk.language, "java")
        self.assertEqual(chunk.code, "public class Test {}")
        self.assertEqual(chunk.imports, ["import java.util.List;"])
        self.assertEqual(len(chunk.dependencies), 1)
        self.assertEqual(chunk.dependencies[0].name, "junit")

if __name__ == '__main__':
    unittest.main()

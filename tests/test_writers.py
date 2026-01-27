import unittest
import os
import json
from src.core.writers import JSONWriter, TextWriter
from src.core.interfaces import Chunk, Dependency

class TestWriters(unittest.TestCase):
    def setUp(self):
        self.chunk = Chunk(
            file_path="src/Test.java",
            language="java",
            code="public class Test {}",
            imports=["import java.util.List;"],
            dependencies=[Dependency(name="junit", version="4.12", type="maven")]
        )
        self.json_output = "test_output.json"
        self.text_output = "test_output.txt"

    def tearDown(self):
        if os.path.exists(self.json_output):
            os.remove(self.json_output)
        if os.path.exists(self.text_output):
            os.remove(self.text_output)

    def test_json_writer(self):
        writer = JSONWriter()
        writer.write([self.chunk], self.json_output)

        with open(self.json_output, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            data = json.loads(lines[0])
            self.assertEqual(data["file_path"], "src/Test.java")

    def test_text_writer(self):
        writer = TextWriter()
        writer.write([self.chunk], self.text_output)

        with open(self.text_output, 'r') as f:
            content = f.read()
            self.assertIn("--- START CHUNK src/Test.java ---", content)
            self.assertIn("Language: java", content)
            self.assertIn("junit:4.12 (maven)", content)
            self.assertIn("public class Test {}", content)

if __name__ == '__main__':
    unittest.main()

import unittest
import os
import json
import shutil
from src.core.writers import JSONWriter, TextWriter
from src.core.interfaces import Chunk, Dependency

class TestWriters(unittest.TestCase):
    def setUp(self):
        self.chunk = Chunk(
            id="src/Test.java::Test",
            file_path="src/Test.java",
            language="java",
            kind="class",
            code="public class Test {}",
            imports=["java.util.List"],
            dependencies=[Dependency(name="junit", version="4.12", type="maven")]
        )
        self.output_dir = "test_output_dir"
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_json_writer(self):
        writer = JSONWriter()
        writer.write([self.chunk], self.output_dir)

        expected_file = os.path.join(self.output_dir, "src", "Test.java.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["file_path"], "src/Test.java")
            self.assertEqual(data["kind"], "class")

    def test_text_writer(self):
        writer = TextWriter()
        writer.write([self.chunk], self.output_dir)

        expected_file = os.path.join(self.output_dir, "src", "Test.java.txt")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, 'r') as f:
            content = f.read()
            self.assertIn("--- CLASS src/Test.java::Test ---", content)
            self.assertIn("Language: java", content)
            self.assertIn("junit:4.12 (maven)", content)
            self.assertIn("public class Test {}", content)

if __name__ == '__main__':
    unittest.main()

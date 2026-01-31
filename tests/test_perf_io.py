
import unittest
import os
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import hashlib
import src.main
from src.main import process_file

class TestPerfIO(unittest.TestCase):
    def setUp(self):
        # Create a temporary Java file
        self.test_dir = tempfile.mkdtemp()
        self.java_file = os.path.join(self.test_dir, "Test.java")
        self.content = b"public class Test {}"
        with open(self.java_file, "wb") as f:
            f.write(self.content)

        # Mock global worker state to avoid real parsing/resolution
        self.original_parser = src.main._parser
        self.original_maven = src.main._maven_resolver
        self.original_bazel = src.main._bazel_resolver
        self.original_chunker = src.main._chunker

        src.main._parser = MagicMock()
        src.main._maven_resolver = MagicMock()
        src.main._maven_resolver.resolve.return_value = []
        src.main._bazel_resolver = MagicMock()
        src.main._bazel_resolver.resolve.return_value = []
        src.main._chunker = MagicMock()
        src.main._chunker.chunk.return_value = []

        # Set output dir to None to skip cache logic, or we can mock it too if we want to test cache path
        # For now we test the processing path (cache miss)
        src.main._output_dir = None
        src.main._status_dict = None

    def tearDown(self):
        # Restore globals
        src.main._parser = self.original_parser
        src.main._maven_resolver = self.original_maven
        src.main._bazel_resolver = self.original_bazel
        src.main._chunker = self.original_chunker

        if os.path.exists(self.java_file):
            os.remove(self.java_file)
        os.rmdir(self.test_dir)

    def test_file_read_count(self):
        # Mock open to count calls, but pass through to real open for other files if needed
        # Since we want to count opens for OUR file, we can spy on it.

        real_open = open

        open_count = 0

        def side_effect(file, mode='r', *args, **kwargs):
            nonlocal open_count
            if file == self.java_file:
                open_count += 1
            return real_open(file, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=side_effect):
            process_file(self.java_file)

        # Optimized: opens only once for reading content, then computes checksum in memory
        print(f"File opened {open_count} times")
        self.assertEqual(open_count, 1, "Expected file to be opened 1 time (optimized behavior)")

if __name__ == '__main__':
    unittest.main()

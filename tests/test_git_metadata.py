import unittest
import os
import shutil
import subprocess
from src.utils.git import get_file_commit_info, get_bulk_commit_info

class TestGitMetadata(unittest.TestCase):
    def setUp(self):
        self.test_dir = "tests/data/git_repo"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, capture_output=True)
        # Configure user for commit
        subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True, capture_output=True)

        self.test_file = os.path.join(self.test_dir, "test.txt")
        with open(self.test_file, "w") as f:
            f.write("test content")

        subprocess.run(["git", "add", "test.txt"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.test_dir, check=True, capture_output=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_get_metadata(self):
        info = get_file_commit_info(self.test_file)
        self.assertIsNotNone(info)
        self.assertEqual(info["author_name"], "Test User")
        self.assertIsNotNone(info["commit_hash"])
        self.assertIsNotNone(info["timestamp"])

    def test_non_existent_file(self):
        info = get_file_commit_info("non_existent_file.txt")
        self.assertIsNone(info)

    def test_get_bulk_metadata(self):
        # Create another file
        other_file = os.path.join(self.test_dir, "other.txt")
        with open(other_file, "w") as f:
            f.write("other content")

        subprocess.run(["git", "add", "other.txt"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], cwd=self.test_dir, check=True, capture_output=True)

        # Use absolute paths
        abs_test_file = os.path.abspath(self.test_file)
        abs_other_file = os.path.abspath(other_file)

        files = [abs_test_file, abs_other_file]

        metadata = get_bulk_commit_info(files)

        self.assertEqual(len(metadata), 2)
        self.assertIn(abs_test_file, metadata)
        self.assertIn(abs_other_file, metadata)

        # Check specific values
        self.assertEqual(metadata[abs_other_file]["author_name"], "Test User")

        # Check that we get different commits if applicable
        hash1 = metadata[abs_test_file]["commit_hash"]
        hash2 = metadata[abs_other_file]["commit_hash"]

        self.assertNotEqual(hash1, hash2)

if __name__ == '__main__':
    unittest.main()

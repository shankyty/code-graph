import unittest
import os
from src.core.dependencies.bazel import BazelResolver

class TestBazelResolver(unittest.TestCase):
    def test_resolve_bazel_deps(self):
        resolver = BazelResolver()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dummy_file = os.path.join(base_dir, "tests/data/bazel_project/src/main/java/com/example/Test.java")

        deps = resolver.resolve(dummy_file)

        # We expect 4 dependencies (2 from lib, 2 from test) because we parse the whole file.
        # This is okay for "scalable" per-file processing without complex query logic.
        self.assertEqual(len(deps), 4)

        dep_names = [d.name for d in deps]
        self.assertIn("//path/to/dep:lib", dep_names)
        self.assertIn("@maven//:com_google_guava_guava", dep_names)
        self.assertIn(":my-lib", dep_names)
        self.assertIn("//test/dep:junit", dep_names)

if __name__ == '__main__':
    unittest.main()

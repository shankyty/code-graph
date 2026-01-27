import unittest
import os
from src.core.dependencies.bazel import BazelResolver

class TestBazelResolver(unittest.TestCase):
    def test_resolve_bazel_deps(self):
        resolver = BazelResolver()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dummy_file = os.path.join(base_dir, "tests/data/bazel_project/src/main/java/com/example/Test.java")

        deps = resolver.resolve(dummy_file)

        self.assertEqual(len(deps), 4)

        dep_names = [d.name for d in deps]
        self.assertIn("//path/to/dep:lib", dep_names)
        self.assertIn("@maven//:com_google_guava_guava", dep_names)
        self.assertIn(":my-lib", dep_names)
        self.assertIn("//test/dep:junit", dep_names)

    def test_nested_deps(self):
        # Create a temporary BUILD file with nested deps (select)
        resolver = BazelResolver()
        test_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(test_dir, "data", "nested_bazel")
        os.makedirs(data_dir, exist_ok=True)

        build_path = os.path.join(data_dir, "BUILD")
        with open(build_path, "w") as f:
            f.write("""
java_library(
    name = "complex-lib",
    deps = [
        ":simple-dep",
        select({
            "//conditions:default": [
                ":default-dep",
            ],
            ":special": [
                ":special-dep",
            ],
        }),
    ],
)
            """)

        dummy_java = os.path.join(data_dir, "Test.java")
        # No need to create the java file, resolver just checks path existence for traversal
        # But resolver code does not check if java file exists, only looks for BUILD from that path.
        # Actually _find_build_file does traverse up.

        deps = resolver.resolve(dummy_java)

        dep_names = {d.name for d in deps}
        self.assertIn(":simple-dep", dep_names)
        self.assertIn(":default-dep", dep_names)
        self.assertIn(":special-dep", dep_names)

        # Cleanup
        if os.path.exists(build_path):
            os.remove(build_path)
        if os.path.exists(data_dir):
            os.rmdir(data_dir)

if __name__ == '__main__':
    unittest.main()

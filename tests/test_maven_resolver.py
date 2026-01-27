import unittest
import os
from src.core.dependencies.maven import MavenResolver

class TestMavenResolver(unittest.TestCase):
    def test_resolve_maven_deps(self):
        resolver = MavenResolver()
        # Find the path to the dummy file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # tests/data/maven_project/src/main/java/com/example/Test.java (non-existent, just path)
        dummy_file = os.path.join(base_dir, "tests/data/maven_project/src/main/java/com/example/Test.java")

        # Verify that resolver finds the pom.xml in tests/data/maven_project
        deps = resolver.resolve(dummy_file)

        self.assertEqual(len(deps), 2)

        dep_names = {d.name: d.version for d in deps}
        self.assertIn("junit:junit", dep_names)
        self.assertEqual(dep_names["junit:junit"], "4.12")

        self.assertIn("com.google.guava:guava", dep_names)
        self.assertEqual(dep_names["com.google.guava:guava"], "30.1-jre")

if __name__ == '__main__':
    unittest.main()

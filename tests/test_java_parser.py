import unittest
from src.core.languages.java_parser import JavaParser

class TestJavaParser(unittest.TestCase):
    def test_parse_simple_java(self):
        parser = JavaParser()
        code = b"""
        package com.example;
        import java.util.List;
        import java.io.File;

        public class Test {
            public static void main(String[] args) {
                System.out.println("Hello");
            }

            @Override
            public String toString() {
                return "Test";
            }
        }
        """
        result = parser.parse(code, "Test.java")

        # Test imports
        self.assertIn("java.util.List", result.imports)
        self.assertIn("java.io.File", result.imports)
        self.assertEqual(len(result.imports), 2)

        # Test classes
        self.assertEqual(len(result.classes), 1)
        cls = result.classes[0]
        self.assertEqual(cls.name, "Test")
        self.assertEqual(cls.package, "com.example")

        # Test methods
        self.assertEqual(len(cls.methods), 2)
        methods = {m.name: m for m in cls.methods}
        self.assertIn("main", methods)
        self.assertIn("toString", methods)

        self.assertTrue(methods["toString"].is_override)
        self.assertIn("@Override", methods["toString"].annotations[0])

if __name__ == '__main__':
    unittest.main()

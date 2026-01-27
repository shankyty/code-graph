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
        }
        """
        result = parser.parse(code, "Test.java")
        print(f"Imports extracted: {result.imports}")
        self.assertIn("import java.util.List;", result.imports)
        self.assertIn("import java.io.File;", result.imports)
        self.assertEqual(len(result.imports), 2)
        self.assertIn("public class Test", result.code)

if __name__ == '__main__':
    unittest.main()

"""Author and About page regression checks."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

class AboutPageTests(unittest.TestCase):
    def test_author_metadata(self):
        self.assertIn('APP_AUTHOR = "cleverandy"', SOURCE)
        self.assertIn('APP_VERSION = "3.4.1"', SOURCE)
        self.assertIn('Developed by cleverandy', SOURCE)
        self.assertIn('APP_LICENSE = "MIT License"', SOURCE)

    def test_about_page_is_built_and_routed(self):
        main = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == 'MainWindow')
        method_names = [n.name for n in main.body if isinstance(n, ast.FunctionDef)]
        self.assertIn('_build_about_page', method_names)
        self.assertIn('self.about_page = self._page()', SOURCE)
        self.assertIn("(\"About\", 4, 'info')", SOURCE)
        self.assertIn('self._build_about_page()', SOURCE)

    def test_no_false_ca_certification_claim(self):
        self.assertIn('not certified or endorsed by any CA', SOURCE)
        self.assertIn('not a Certificate Authority (CA)', SOURCE)

if __name__ == '__main__':
    unittest.main()

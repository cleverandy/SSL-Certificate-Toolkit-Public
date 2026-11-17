"""GUI regression checks that do not need PySide6 installed."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1].joinpath('app.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)


class TestGUIRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = next(node for node in TREE.body if isinstance(node, ast.ClassDef) and node.name == 'MainWindow')
        cls.methods = [node.name for node in cls.main.body if isinstance(node, ast.FunctionDef)]

    def test_builder_function_does_not_shadow_page_initialization(self):
        self.assertEqual(self.methods.count('_build_bundle_page'), 1)
        self.assertEqual(self.methods.count('_build_bundle'), 1)
        self.assertEqual(len(set(self.methods)), len(self.methods))
        constructor = next(node for node in self.main.body if isinstance(node, ast.FunctionDef) and node.name == '__init__')
        invoked = [node.func.attr for node in ast.walk(constructor)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        self.assertIn('_build_bundle_page', invoked)
        self.assertNotIn('_build_bundle', invoked)

    def test_csr_key_cert_order(self):
        builder = next(node for node in self.main.body if isinstance(node, ast.FunctionDef) and node.name == '_build_inspector')
        assigns = [node.targets[0].elts[0].attr for node in ast.walk(builder)
                   if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Tuple)
                   and isinstance(node.targets[0].elts[0], ast.Attribute)
                   and node.targets[0].elts[0].attr in ('inspect_csr', 'inspect_key', 'inspect_cert')]
        self.assertEqual(assigns, ['inspect_csr', 'inspect_key', 'inspect_cert'])

    def test_checkbox_has_checked_image_asset(self):
        self.assertIn('QCheckBox::indicator:checked', SOURCE)
        self.assertTrue(Path(__file__).resolve().parents[1].joinpath('assets/check_white.png').is_file())

    def test_dialogs_are_explicitly_styled(self):
        self.assertIn('QMessageBox QLabel', SOURCE)
        self.assertIn('QMessageBox QPushButton', SOURCE)
        self.assertIn('QSettings', SOURCE)
        self.assertIn('dialogs/last_directory', SOURCE)

    def test_import_actions_disabled_without_certificates(self):
        self.assertIn('self.analyze_button.setEnabled(False)', SOURCE)
        self.assertIn('self.export_button.setEnabled(False)', SOURCE)


if __name__ == '__main__':
    unittest.main()

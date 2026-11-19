"""Actual Qt smoke checks. Skipped automatically when PySide6 isn't installed."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
# Qt's offscreen platform can warn when PySide6's old lib/fonts folder is absent.
# Point it to installed Windows fonts for GUI smoke tests; the EXE does not
# need to bundle a separate font directory for normal Windows operation.
if os.name == 'nt' and 'QT_QPA_FONTDIR' not in os.environ:
    fonts = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
    if fonts.is_dir():
        os.environ['QT_QPA_FONTDIR'] = str(fonts)
try:
    from PySide6.QtWidgets import QApplication
    import app as gui
    import core
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, 'PySide6 is not installed')
class TestQtSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])
        cls.window = gui.MainWindow()

    @classmethod
    def tearDownClass(cls):
        cls.window.close()

    def test_initial_page_and_bundle_panel(self):
        self.assertEqual(self.window.pages.count(), 8)
        self.assertIsNotNone(self.window.import_drop)
        self.assertFalse(self.window.analyze_button.isEnabled())
        self.assertFalse(self.window.export_button.isEnabled())
        self.window.navigate(3)
        self.assertEqual(self.window.pages.currentIndex(), 3)

    def test_about_page_navigation(self):
        self.window.navigate(4)
        self.assertEqual(self.window.pages.currentIndex(), 4)
        self.assertTrue(self.window.nav_buttons[6].isChecked())

    def test_certificate_viewer_field_order_and_generated_match(self):
        self.window.navigate(0)
        self.window.primary.setText('www.test.example.com')
        self.window.save_on_generate.setChecked(False)
        self.window._generate()
        self.assertTrue(self.window.csr_data)
        self.assertTrue(self.window.generated_key_data)
        self.window._verify_generated()
        self.assertEqual(self.window.pages.currentIndex(), 2)
        self.assertIn('CSR / KEY: MATCH', self.window.inspect_summary.text())

    def test_dark_theme_checkbox_and_modal_style(self):
        self.window.dark = True
        self.window.apply_theme()
        stylesheet = self.qt.styleSheet()
        self.assertIn('QCheckBox::indicator:checked', stylesheet)
        self.assertIn('check_white.png', stylesheet)
        self.window.dark = False
        self.window.apply_theme()


if __name__ == '__main__':
    unittest.main()

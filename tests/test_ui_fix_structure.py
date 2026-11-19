"""Static regressions for the Windows UI fixes."""
import ast
import unittest
from pathlib import Path
from app_version import APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
EXPORT = (ROOT / 'export_picture.py').read_text(encoding='utf-8')

class UIFixTests(unittest.TestCase):
    def test_version_consistency(self):
        self.assertIn('from app_version import APP_VERSION', APP)
        workflow = (ROOT / '.github/workflows/build-windows.yml').read_text(encoding='utf-8')
        self.assertIn(f'SSL_Certificate_Toolkit_v{APP_VERSION}.exe', workflow)
        self.assertNotIn('v3.3.0', workflow)

    def test_three_appearance_buttons_without_combo(self):
        self.assertIn("self.appearance_buttons = {}", APP)
        self.assertIn("def set_appearance(self, mode):", APP)
        self.assertIn("self.settings.setValue('appearance/theme', mode)", APP)
        self.assertNotIn('self.theme_combo', APP)

    def test_dns_actions_adjacent(self):
        self.assertIn('dns_line.addWidget(button("+ Add", self.add_dns))', APP)
        self.assertIn('dns_line.addWidget(self.remove_dns_btn)', APP)
        self.assertNotIn('Remove selected DNS', APP)

    def test_icons_and_combo_style(self):
        self.assertIn('def vector_icon(', APP)
        self.assertIn('QComboBox::drop-down', APP)
        self.assertIn('QComboBox::down-arrow', APP)
        self.assertTrue((ROOT / 'assets/chevron_down.png').exists())

    def test_subject_is_remembered_and_importable(self):
        self.assertIn("self.settings.setValue('subject/remember', checked)", APP)
        self.assertIn("self.settings.setValue('subject/' + key", APP)
        self.assertIn('def import_live_subject(self)', APP)

    def test_preview_not_redrawn_per_keystroke(self):
        self.assertIn('self.name.textChanged.connect(self._mark_dirty)', EXPORT)
        self.assertIn('self.email.textChanged.connect(self._mark_dirty)', EXPORT)
        self.assertIn("QPushButton('Save')", EXPORT)
        self.assertIn("self.saved_name, self.saved_email = name, email", EXPORT)
        self.assertIn("self.light_btn = QPushButton('Light')", EXPORT)
        self.assertIn("self.dark_btn = QPushButton('Dark')", EXPORT)
        self.assertNotIn('QComboBox', EXPORT)
        self.assertNotIn('self.name.textChanged.connect(self._draw)', EXPORT)

    def test_picture_shield_and_version(self):
        self.assertIn('shield_check_pixmap(color, 22)', EXPORT)
        self.assertIn("product_version = l(f'v{APP_VERSION}'", EXPORT)
        self.assertNotIn("'◈  SSL Certificate Verification'", EXPORT)
        self.assertNotIn("'Checked using'", EXPORT)

    def test_embedded_checker_text_remains_visible(self):
        self.assertIn("self.inspect_button.setText('SSL Checker')", APP)
        self.assertNotIn("self.inspect_button.setIcon(vector_icon('shield'))", APP)

    def test_no_chinese_interface_text(self):
        for src in (APP, EXPORT):
            self.assertFalse(any('\u4e00' <= char <= '\u9fff' for char in src))

if __name__ == '__main__':
    unittest.main()

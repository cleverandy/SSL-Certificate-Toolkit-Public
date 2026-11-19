"""Verify all versioned build outputs use the shared release metadata."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app_version import APP_VERSION
from version_manager import check_release, desired_files

class TestVersionConsistency(unittest.TestCase):
    def test_current_release_metadata(self):
        self.assertEqual([], check_release())

    def test_metadata_updater_is_idempotent(self):
        for path, generated in desired_files(APP_VERSION).items():
            self.assertEqual(path.read_text(encoding="utf-8"), generated, str(path))

    def test_picture_preview_uses_shared_version(self):
        text = (ROOT / "export_picture.py").read_text(encoding="utf-8")
        self.assertIn("from app_version import APP_VERSION", text)
        self.assertIn("product_version = l(f'v{APP_VERSION}'", text)

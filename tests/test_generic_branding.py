"""Generic edition must not reintroduce institution-specific branding."""
import unittest
from pathlib import Path
import core

ROOT = Path(__file__).resolve().parents[1]

class TestGenericEdition(unittest.TestCase):
    def test_default_subject_and_example(self):
        self.assertEqual(core.DEFAULT_SUBJECT["C"], "US")
        for key in ("ST", "L", "O", "OU"):
            self.assertEqual(core.DEFAULT_SUBJECT[key], "")
        self.assertEqual(core.san_names("www.example.com"), ["www.example.com", "example.com"])

    def test_no_institutional_branding(self):
        for p in ROOT.rglob("*"):
            if p.is_file() and p.suffix in (".py", ".md", ".bat", ".yml", ".txt"):
                content = p.read_text(encoding="utf-8").lower()
                for forbidden in ("hk" + "u", "hk" + "umed", "university of " + "hong kong", ".hk" + "u.hk"):
                    self.assertNotIn(forbidden, content, f"{forbidden} in {p}")

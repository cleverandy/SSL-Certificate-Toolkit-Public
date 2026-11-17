"""Regression checks for the generic edition's first-party source files.

The Windows build creates ``.venv`` inside the project.  Its generated
activation scripts embed the user's absolute checkout path and must not be
mistaken for product copy or application defaults.
"""
import os
import tempfile
import unittest
from pathlib import Path

import core

ROOT = Path(__file__).resolve().parents[1]

# Exclude generated and third-party content, but keep first-party tests,
# documentation, scripts and GitHub Actions configuration in scope.
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", "build", "dist",
    ".pytest_cache", ".mypy_cache", ".tox", "site-packages", "node_modules",
}
SOURCE_SUFFIXES = {".py", ".md", ".bat", ".cmd", ".yml", ".yaml", ".txt"}
FORBIDDEN = ("hk" + "u", "hk" + "umed", "university of " + "hong kong", ".hk" + "u.hk")


def iter_first_party_files(root: Path):
    """Yield only project-managed text files, not local environments/builds."""
    for directory, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs
                   if name.lower() not in EXCLUDED_DIRS
                   and not name.lower().endswith(".egg-info")]
        for name in files:
            path = Path(directory) / name
            if path.suffix.lower() in SOURCE_SUFFIXES:
                yield path


def branding_hits(root: Path):
    for path in iter_first_party_files(root):
        content = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN:
            if forbidden in content:
                yield (path.relative_to(root).as_posix(), forbidden)


class TestGenericEdition(unittest.TestCase):
    def test_default_subject_and_example(self):
        self.assertEqual(core.DEFAULT_SUBJECT["C"], "US")
        for key in ("ST", "L", "O", "OU"):
            self.assertEqual(core.DEFAULT_SUBJECT[key], "")
        self.assertEqual(core.san_names("www.example.com"), ["www.example.com", "example.com"])

    def test_no_institutional_branding(self):
        self.assertEqual(list(branding_hits(ROOT)), [])

    def test_generated_venv_and_build_files_are_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for folder in (".venv/Scripts", "build", "dist", ".git", "__pycache__"):
                generated = root / folder / "sample.bat"
                generated.parent.mkdir(parents=True)
                generated.write_text("C:/example/" + "hk" + "u" + "/activate", encoding="utf-8")
            source = root / "app.py"
            source.write_text("print('generic edition')", encoding="utf-8")
            self.assertEqual(list(iter_first_party_files(root)), [source])
            self.assertEqual(list(branding_hits(root)), [])

    def test_branding_in_real_source_is_still_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("org = '" + "hk" + "u" + "'", encoding="utf-8")
            self.assertIn(("app.py", "hk" + "u"), list(branding_hits(root)))


if __name__ == "__main__":
    unittest.main()

"""Update and verify all *current-release* version metadata.

Usage:
    python version_manager.py --check
    python version_manager.py --set 3.4.3

Historical changelog entries and archived reports are intentionally unchanged.
"""
from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")


def _replace_checked(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    changed, n = re.subn(pattern, lambda _: replacement, text, flags=flags)
    if n == 0:
        raise ValueError(f"Cannot locate {label}; verify layout before updating")
    return changed


def _current_version() -> str:
    tree = ast.parse((ROOT / "app_version.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "APP_VERSION" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("APP_VERSION not found")


def desired_files(version: str) -> dict[Path, str]:
    """Build complete, deterministic replacements without writing files."""
    if not VERSION_RE.fullmatch(version):
        raise ValueError("Version must be MAJOR.MINOR.PATCH, e.g. 3.4.3")
    nums = tuple(map(int, version.split('.')))
    if any(n > 65535 for n in nums):
        raise ValueError("Windows version components must be <= 65535")
    four = version + '.0'
    files = {}

    path = ROOT / 'app_version.py'
    files[path] = _replace_checked(path.read_text(encoding='utf-8'),
        r'(?m)^APP_VERSION\s*=\s*[\"\'][^\"\']+[\"\']', f'APP_VERSION = "{version}"', 'APP_VERSION')

    path = ROOT / 'windows_version_info.txt'
    content = path.read_text(encoding='utf-8')
    for key in ('filevers', 'prodvers'):
        content = _replace_checked(content, rf'\b{key}=\(\d+,\s*\d+,\s*\d+,\s*\d+\)',
            f'{key}=({nums[0]}, {nums[1]}, {nums[2]}, 0)', key)
    for key in ('FileVersion', 'ProductVersion'):
        content = _replace_checked(content, rf"StringStruct\('{key}',\s*'[^']+'\)",
            f"StringStruct('{key}', '{four}')", key)
    content = _replace_checked(content, r"StringStruct\('OriginalFilename',\s*'[^']+'\)",
        f"StringStruct('OriginalFilename', 'SSL_Certificate_Toolkit_v{version}.exe')", 'OriginalFilename')
    files[path] = content

    path = ROOT / 'build_windows.bat'
    content = path.read_text(encoding='utf-8')
    content = _replace_checked(content, r'SSL Certificate Toolkit v\d+\.\d+\.\d+',
        f'SSL Certificate Toolkit v{version}', 'batch title')
    content = _replace_checked(content, r'SSL_Certificate_Toolkit_v\d+\.\d+\.\d+\.exe',
        f'SSL_Certificate_Toolkit_v{version}.exe', 'batch exe filename')
    content = _replace_checked(content, r'(?<=--name )SSL_Certificate_Toolkit_v\d+\.\d+\.\d+',
        f'SSL_Certificate_Toolkit_v{version}', 'batch PyInstaller name')
    files[path] = content

    path = ROOT / '.github/workflows/build-windows.yml'
    content = path.read_text(encoding='utf-8')
    content = _replace_checked(content, r'SSL_Certificate_Toolkit_v\d+\.\d+\.\d+',
        f'SSL_Certificate_Toolkit_v{version}', 'GitHub workflow EXE')
    content = _replace_checked(content, r'SSL-Certificate-Toolkit-v\d+\.\d+\.\d+-Windows',
        f'SSL-Certificate-Toolkit-v{version}-Windows', 'GitHub artifact')
    files[path] = content

    path = ROOT / 'README.md'
    content = path.read_text(encoding='utf-8')
    content = _replace_checked(content, r'(?m)^# SSL Certificate Toolkit v\d+\.\d+\.\d+',
        f'# SSL Certificate Toolkit v{version}', 'README current title')
    content = _replace_checked(content, r'(?<=dist\\)SSL_Certificate_Toolkit_v\d+\.\d+\.\d+\.exe',
        f'SSL_Certificate_Toolkit_v{version}.exe', 'README executable example')
    files[path] = content
    return files


def check_release(version: str | None = None) -> list[str]:
    version = version or _current_version()
    issues = []
    for path, desired in desired_files(version).items():
        if path.read_text(encoding='utf-8') != desired:
            issues.append(f'{path.relative_to(ROOT)}: release metadata differs from {version}')
    for filename in ('app.py', 'export_picture.py'):
        source = (ROOT / filename).read_text(encoding='utf-8')
        if 'from app_version import APP_VERSION' not in source:
            issues.append(f'{filename}: does not import shared APP_VERSION')
        if re.search(r'(?m)^\s*APP_VERSION\s*=', source):
            issues.append(f'{filename}: duplicates APP_VERSION constant')
    if not re.search(rf'(?m)^## v{re.escape(version)}\b', (ROOT/'CHANGELOG.md').read_text(encoding='utf-8')):
        issues.append(f'CHANGELOG.md: missing v{version} release notes section')
    # Version-sensitive tests should reference the shared version, never a particular release.
    for path in (ROOT/'tests').glob('test_*.py'):
        if re.search(r'(?<!\d)3\.4\.2(?!\d)', path.read_text(encoding='utf-8')):
            issues.append(f'{path.relative_to(ROOT)}: hardcoded 3.4.2')
    return issues


def update_version(version: str) -> list[str]:
    """Centralized, validated metadata update. Does not touch historical notes."""
    updates = desired_files(version)  # validate all patterns before writing
    changelog = ROOT / 'CHANGELOG.md'
    notes = changelog.read_text(encoding='utf-8')
    if not re.search(rf'(?m)^## v{re.escape(version)}\b', notes):
        notes = f'## v{version} — Release notes pending\n\n- Document changes before publishing this release.\n\n' + notes
        updates[changelog] = notes
    touched = []
    for path, data in updates.items():
        if path.read_text(encoding='utf-8') != data:
            path.write_text(data, encoding='utf-8', newline='')
            touched.append(str(path.relative_to(ROOT)))
    return touched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='Check current-release versions')
    mode.add_argument('--set', metavar='X.Y.Z', help='Update current-release metadata')
    args = parser.parse_args()
    if args.set:
        print('Updated:', ', '.join(update_version(args.set)) or '(no changes)')
    problems = check_release()
    if problems:
        print('Version consistency FAILED:')
        for item in problems:
            print(' -', item)
        return 1
    print('Version consistency OK:', _current_version())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

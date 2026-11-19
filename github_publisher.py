"""Atomic, one-command GitHub source publisher (no git CLI or Python packages).

Default: preview only, no remote writes.
    python github_publisher.py
    python github_publisher.py --publish

Authentication: gh auth login (recommended), GH_TOKEN, or GITHUB_TOKEN.
Only allowlisted source files are uploaded; nothing from local build/cache/keys.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_REPO = 'cleverandy/SSL-Certificate-Toolkit-Public'
SAFE_ROOT_FILES = {
    'README.md', 'CHANGELOG.md', 'LICENSE', '.gitignore', 'VERSION_AUDIT.md',
    'GITHUB_PUBLISH_GUIDE.md',
    'requirements.txt', 'windows_version_info.txt',
}
SAFE_SUFFIXES = {'.py', '.bat', '.png', '.ico', '.svg', '.md', '.txt', '.yml', '.yaml'}
BLOCKED_SUFFIXES = {'.key', '.pem', '.pfx', '.p12', '.csr', '.crt', '.cer', '.der', '.env', '.zip', '.exe'}
TEXT_SUFFIXES = {'.py', '.bat', '.md', '.txt', '.yml', '.yaml', '.svg'}
MAX_FILE_BYTES = 2 * 1024 * 1024


def source_files(root: Path = ROOT) -> dict[str, bytes]:
    """Explicit allowlist means local certs/logs/private config cannot leak."""
    selected = {}
    for p in sorted(root.iterdir()):
        if p.is_file() and (p.name in SAFE_ROOT_FILES or p.suffix.lower() in {'.py', '.bat'}):
            selected[p.name] = p
    for subdir in ('tests', 'assets', '.github/workflows'):
        base = root / subdir
        if base.is_dir():
            for p in sorted(base.rglob('*')):
                if p.is_file() and p.suffix.lower() in SAFE_SUFFIXES:
                    selected[p.relative_to(root).as_posix()] = p
    result = {}
    for name, p in selected.items():
        if p.is_symlink():
            raise ValueError(f'Refusing symlink: {name}')
        if p.suffix.lower() in BLOCKED_SUFFIXES or p.name.startswith('.env'):
            raise ValueError(f'Refusing sensitive file: {name}')
        data = p.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f'File unexpectedly large: {name} ({len(data)} bytes)')
        if p.suffix.lower() in TEXT_SUFFIXES:
            s = data.decode('utf-8-sig')
            if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----', s):
                raise ValueError(f'Private key found in source: {name}')
            if re.search(r'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}', s):
                raise ValueError(f'GitHub token-like secret found in source: {name}')
        result[name] = data
    if not {'app.py', 'app_version.py', 'core.py', 'README.md', '.github/workflows/build-windows.yml'} <= result.keys():
        raise ValueError('Incomplete source tree; required project files missing')
    return result


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def credential() -> str:
    for key in ('GH_TOKEN', 'GITHUB_TOKEN'):
        if os.environ.get(key):
            return os.environ[key].strip()
    try:
        cmd = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=12, check=True)
        return cmd.stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise RuntimeError('GitHub authentication missing. Run `gh auth login` once, or set GH_TOKEN.') from None


class GithubAPI:
    def __init__(self, token: str, repo: str):
        if not re.fullmatch(r'[\w.-]+/[\w.-]+', repo):
            raise ValueError('Repository must be OWNER/REPO')
        self.repo = repo
        self.base = f'https://api.github.com/repos/{repo}'
        self.token = token

    def request(self, method: str, path: str, data: dict | None = None) -> dict:
        url = self.base + path
        payload = json.dumps(data).encode('utf-8') if data is not None else None
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'ssl-certificate-toolkit-source-publisher',
        }
        if payload is not None:
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                detail = e.read(500).decode('utf-8', 'replace')
                if e.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(1 + attempt * 2)
                    continue
                raise RuntimeError(f'GitHub API {e.code} ({method} {path}): {detail}') from None
            except urllib.error.URLError as e:
                if attempt < 2:
                    time.sleep(1 + attempt * 2)
                    continue
                raise RuntimeError(f'GitHub API network error: {e.reason}') from None
        raise RuntimeError('GitHub API retries exhausted')


def prepare(api: GithubAPI, local: dict[str, bytes], branch: str = 'main') -> dict:
    ref = api.request('GET', '/git/ref/heads/' + urllib.parse.quote(branch, safe='/'))
    head = ref['object']['sha']
    commit = api.request('GET', '/git/commits/' + head)
    tree_sha = commit['tree']['sha']
    tree = api.request('GET', f'/git/trees/{tree_sha}?recursive=1')
    if tree.get('truncated'):
        raise RuntimeError('Remote file tree was truncated; refusing unsafe publish')
    remote = {item['path']: item['sha'] for item in tree['tree'] if item['type'] == 'blob'}
    changed = {p: data for p, data in local.items() if remote.get(p) != git_blob_sha(data)}
    extra = sorted(set(remote) - set(local))
    return {'head': head, 'tree_sha': tree_sha, 'changed': changed, 'extra': extra, 'remote': remote}


def publish(api: GithubAPI, plan: dict, *, branch: str, version: str) -> str:
    # Never delete remote files implicitly. Upload all changed blobs first; only then make one commit.
    elements = []
    for idx, (path, content) in enumerate(sorted(plan['changed'].items()), 1):
        result = api.request('POST', '/git/blobs', {
            'content': base64.b64encode(content).decode('ascii'), 'encoding': 'base64'
        })
        sha = result['sha']
        if sha != git_blob_sha(content):
            raise RuntimeError(f'GitHub blob SHA mismatch: {path}')
        elements.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': sha})
        print(f'  [{idx}/{len(plan["changed"])}] Uploaded {path}', flush=True)
    if not elements:
        return plan['head']
    new_tree = api.request('POST', '/git/trees', {'base_tree': plan['tree_sha'], 'tree': elements})['sha']
    new_commit = api.request('POST', '/git/commits', {
        'message': f'Update SSL Certificate Toolkit v{version} source',
        'tree': new_tree,
        'parents': [plan['head']],
    })['sha']
    # Check immediately before non-force update; refuse races rather than rebasing blindly.
    latest = api.request('GET', '/git/ref/heads/' + urllib.parse.quote(branch, safe='/'))['object']['sha']
    if latest != plan['head']:
        raise RuntimeError(f'Branch advanced from {plan["head"]} to {latest}; no ref update. Re-run preview.')
    api.request('PATCH', '/git/refs/heads/' + urllib.parse.quote(branch, safe='/'), {
        'sha': new_commit, 'force': False,
    })
    verified = api.request('GET', '/git/ref/heads/' + urllib.parse.quote(branch, safe='/'))['object']['sha']
    if verified != new_commit:
        raise RuntimeError(f'Branch verification mismatch: expected {new_commit}, got {verified}')
    verify_tree = api.request('GET', '/git/commits/' + verified)['tree']['sha']
    if verify_tree != new_tree:
        raise RuntimeError('Published branch tree did not match prepared tree')
    return new_commit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', help='Execute one atomic GitHub commit; preview is default')
    parser.add_argument('--repo', default=DEFAULT_REPO, help=f'Target GitHub repo (default {DEFAULT_REPO})')
    parser.add_argument('--branch', default='main')
    parser.add_argument('--skip-tests', action='store_true', help='Skip local unittest run (not recommended)')
    parser.add_argument('--allow-auto-release', action='store_true',
                        help='Explicitly permit main push to trigger existing auto GitHub Release')
    args = parser.parse_args(argv)
    try:
        from version_manager import _current_version, check_release
        version = _current_version()
        issues = check_release()
        if issues:
            raise RuntimeError('Version check failed:\n' + '\n'.join('  - ' + i for i in issues))
        if not args.skip_tests:
            print('Running unit tests (offscreen Qt)...', flush=True)
            env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
            result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                    cwd=ROOT, env=env, timeout=180)
            if result.returncode:
                raise RuntimeError('Unit tests failed; refusing to publish')
        files = source_files()
        print(f'Local version: {version}; allowlisted source files: {len(files)}')
        api = GithubAPI(credential(), args.repo)
        plan = prepare(api, files, args.branch)
        print(f'Remote {args.branch} HEAD: {plan["head"]}')
        print(f'Changed/new: {len(plan["changed"])}; remote-only retained: {len(plan["extra"])}')
        for p in sorted(plan['changed']):
            print(('  NEW    ' if p not in plan['remote'] else '  UPDATE ') + p)
        if not args.publish:
            print('PREVIEW ONLY: nothing has been written. Add --publish when ready.')
            return 0
        if not plan['changed']:
            print('Nothing to publish: remote already matches selected local files.')
            return 0
        workflow = files.get('.github/workflows/build-windows.yml', b'').decode('utf-8')
        if re.search(r'gh release create', workflow) and not args.allow_auto_release:
            raise RuntimeError('Current workflow automatically publishes a GitHub Release on main. '
                               'No upload performed. After reviewing this impact, rerun with --allow-auto-release, '
                               'or change the workflow to build-only.')
        sha = publish(api, plan, branch=args.branch, version=version)
        print(f'PUBLISHED: https://github.com/{args.repo}/commit/{sha}')
        print(f'Actions: https://github.com/{args.repo}/actions')
        return 0
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as e:
        print(f'PUBLISH FAILED: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

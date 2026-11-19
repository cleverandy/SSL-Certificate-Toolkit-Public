"""Offline unit tests for the GitHub publisher's atomic upload planning."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from github_publisher import git_blob_sha, prepare, publish, source_files
from version_manager import _current_version


class PublisherTests(unittest.TestCase):
    def test_blob_sha(self):
        self.assertEqual(git_blob_sha(b'hello\n'), 'ce013625030ba8dba906f756967f9e9ca394464a')

    def test_allowlist_and_secret_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ('app.py', 'core.py', 'app_version.py', 'README.md'):
                (root / name).write_text('demo', encoding='utf8')
            (root / '.github/workflows').mkdir(parents=True)
            (root / '.github/workflows/build-windows.yml').write_text('demo', encoding='utf8')
            (root / 'private.key').write_text('secret')
            (root / '.env').write_text('GH_TOKEN=secret')
            (root / 'build').mkdir()
            (root / 'build' / 'cache.py').write_text('demo')
            selected = source_files(root)
            self.assertNotIn('private.key', selected)
            self.assertNotIn('.env', selected)
            self.assertNotIn('build/cache.py', selected)
            self.assertIn('app.py', selected)

    def test_prepare_only_changed_files(self):
        same = b'unchanged'
        new = b'changed'
        api = Mock()
        api.request.side_effect = [
            {'object': {'sha': 'HEAD'}},
            {'tree': {'sha': 'TREE'}},
            {'tree': [
                {'path': 'app.py', 'type': 'blob', 'sha': git_blob_sha(same)},
                {'path': 'README.md', 'type': 'blob', 'sha': 'OLD'},
                {'path': 'remote_extra', 'type': 'blob', 'sha': 'OLD'},
            ]},
        ]
        plan = prepare(api, {'app.py': same, 'README.md': new})
        self.assertEqual(plan['changed'], {'README.md': new})
        self.assertEqual(plan['extra'], ['remote_extra'])

    def test_atomic_commit_and_verification(self):
        data = b'new contents\n'
        api = Mock()
        api.request.side_effect = [
            {'sha': git_blob_sha(data)},
            {'sha': 'NEWTREE'},
            {'sha': 'NEWCOMMIT'},
            {'object': {'sha': 'OLDHEAD'}},
            {'ref': 'refs/heads/main'},
            {'object': {'sha': 'NEWCOMMIT'}},
            {'tree': {'sha': 'NEWTREE'}},
        ]
        sha = publish(api, {'head': 'OLDHEAD', 'tree_sha': 'OLDTREE',
                            'changed': {'README.md': data}}, branch='main', version=_current_version())
        self.assertEqual(sha, 'NEWCOMMIT')
        self.assertEqual([c.args[0] for c in api.request.call_args_list],
                         ['POST', 'POST', 'POST', 'GET', 'PATCH', 'GET', 'GET'])
        self.assertEqual(api.request.call_args_list[4].args[2]['force'], False)

    def test_branch_race_never_updates_ref(self):
        data = b'new contents\n'
        api = Mock()
        api.request.side_effect = [
            {'sha': git_blob_sha(data)}, {'sha': 'NEWTREE'}, {'sha': 'NEWCOMMIT'},
            {'object': {'sha': 'SOMEONE_ELSE_PUSHED'}},
        ]
        with self.assertRaisesRegex(RuntimeError, 'Branch advanced'):
            publish(api, {'head': 'OLDHEAD', 'tree_sha': 'OLDTREE',
                          'changed': {'app.py': data}}, branch='main', version=_current_version())
        self.assertNotIn('PATCH', [c.args[0] for c in api.request.call_args_list])


if __name__ == '__main__':
    unittest.main()

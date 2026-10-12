"""Exercise installation in disposable projects, including ownership failures."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/install.py'
PACKAGE = ROOT / '.apm/skills/ceo-ai'
DESTINATIONS = {'codex': '.agents/skills/ceo-ai', 'cursor': '.agents/skills/ceo-ai',
                'claude': '.claude/skills/ceo-ai'}


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / 'проект 项目 with spaces'
        self.project.mkdir()
        (self.project / 'AGENTS.md').write_text('Keep this user rule.\n')
        self.target = self.project / DESTINATIONS['codex']

    def run_cli(self, action='install', host='codex', source=None, expect=0):
        command = [sys.executable, str(SCRIPT), action, '--project', str(self.project), '--host', host]
        if source:
            command.extend(['--source', str(source)])
        done = subprocess.run(command, capture_output=True, text=True, timeout=10,
                              env=dict(os.environ, AGENTS_HOME=str(self.base / 'wrong root')))
        self.assertEqual(done.returncode, expect, done.stdout + done.stderr)
        return done

    def test_install_and_relocate_for_three_hosts(self):
        for host, destination in DESTINATIONS.items():
            with self.subTest(host=host):
                self.run_cli(host=host)
                installed = self.project / destination
                self.assertEqual(len(list(installed.rglob('SKILL.md'))), 1)
                catalog = json.loads((installed / 'catalog.json').read_text())
                self.assertEqual(len(catalog['components']), 13)
                for item in catalog['components']:
                    self.assertTrue((installed / item['path']).exists(), item['path'])
                moved = self.base / ('relocated ' + host)
                self.project.rename(moved)
                self.project = moved
                installed = moved / destination
                done = subprocess.run([sys.executable, str(installed / 'tools/team/team.py'),
                                       '--home', str(installed), 'list', '--type', 'agent'],
                                      cwd=self.base, capture_output=True, text=True, timeout=10)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertIn('agent:decision-mentor', done.stdout)
                self.run_cli('remove', host)
                self.assertFalse(installed.exists())
                self.assertEqual((moved / 'AGENTS.md').read_text(), 'Keep this user rule.\n')

    def test_reinstall_is_idempotent(self):
        self.run_cli()
        before = snapshot(self.project)
        self.run_cli()
        self.assertEqual(snapshot(self.project), before)
        self.run_cli('verify')

    def test_unmanaged_collision_is_preserved(self):
        self.target.mkdir(parents=True)
        (self.target / 'SKILL.md').write_text('User skill')
        before = snapshot(self.project)
        self.run_cli(expect=1)
        self.assertEqual(snapshot(self.project), before)

    def test_modified_files_block_update_and_removal(self):
        self.run_cli()
        (self.target / 'SKILL.md').write_text('User edit')
        before = snapshot(self.project)
        for action in ('install', 'remove', 'verify'):
            self.run_cli(action, expect=1)
            self.assertEqual(snapshot(self.project), before)

    def test_added_file_and_empty_directory_are_preserved(self):
        self.run_cli()
        (self.target / 'personal.md').write_text('Keep me')
        self.run_cli('remove', expect=1)
        (self.target / 'personal.md').unlink()
        (self.target / 'personal').mkdir()
        self.run_cli('remove', expect=1)
        self.assertTrue((self.target / 'personal').is_dir())

    def test_update_owned_version(self):
        self.run_cli()
        source = self.base / 'new-package'
        shutil.copytree(PACKAGE, source)
        (source / 'VERSION').write_bytes(b'0.3.1\n')
        manifest = json.loads((source / 'bundle.json').read_text())
        manifest['version'] = '0.3.1'
        manifest['files']['VERSION'] = hashlib.sha256(b'0.3.1\n').hexdigest()
        (source / 'bundle.json').write_text(json.dumps(manifest))
        self.run_cli(source=source)
        self.assertEqual((self.target / 'VERSION').read_text(), '0.3.1\n')
        self.run_cli('verify')

    @unittest.skipUnless(os.name == 'posix', 'symlink fixture needs POSIX')
    def test_symlinked_destination_and_parent_are_rejected(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.project / '.agents').symlink_to(outside, target_is_directory=True)
        self.run_cli(expect=1)
        self.assertEqual(list(outside.iterdir()), [])

    def test_modified_or_missing_source_is_rejected(self):
        source = self.base / 'package'
        shutil.copytree(PACKAGE, source)
        (source / 'references/skills/ceo.md').unlink()
        self.run_cli(source=source, expect=1)
        self.assertFalse(self.target.exists())

    def test_traversal_manifest_is_rejected_before_writing(self):
        source = self.base / 'unsafe-package'
        shutil.copytree(PACKAGE, source)
        manifest = json.loads((source / 'bundle.json').read_text())
        manifest['files']['../../escape'] = hashlib.sha256(b'unsafe').hexdigest()
        (source / 'bundle.json').write_text(json.dumps(manifest))
        before = snapshot(self.project)
        self.run_cli(source=source, expect=1)
        self.assertEqual(snapshot(self.project), before)
        self.assertFalse((self.base / 'escape').exists())

    def test_unmanaged_lock_and_transaction_are_preserved(self):
        self.target.parent.mkdir(parents=True)
        lock = self.target.parent / '.ceo-ai.lock'
        lock.write_text('User file')
        self.run_cli(expect=1)
        self.assertEqual(lock.read_text(), 'User file')
        lock.unlink()
        transaction = self.target.parent / '.ceo-ai-transaction'
        transaction.mkdir()
        (transaction / 'personal.txt').write_text('User file')
        for action in ('install', 'recover'):
            self.run_cli(action, expect=1)
            self.assertFalse(self.target.exists())
            self.assertEqual((transaction / 'personal.txt').read_text(), 'User file')

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX FIFO')
    def test_nonregular_recovery_state_is_refused_promptly(self):
        transaction = self.target.parent / '.ceo-ai-transaction'
        transaction.mkdir(parents=True)
        os.mkfifo(transaction / 'state.json')
        self.run_cli('recover', expect=1)
        self.assertTrue((transaction / 'state.json').exists())

    def test_reparse_point_attribute_blocks_path_and_tree(self):
        spec = importlib.util.spec_from_file_location('ceo_installer_test', SCRIPT)
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        junction = self.project / 'junction'
        junction.mkdir()
        actual_lstat = Path.lstat

        def reported_stat(path):
            actual = actual_lstat(path)
            if path == junction:
                return mock.Mock(st_mode=actual.st_mode, st_file_attributes=0x400)
            return actual

        with mock.patch.object(Path, 'lstat', reported_stat):
            with self.assertRaises(ValueError):
                installer.safe_path(junction / 'child')
            with self.assertRaises(ValueError):
                installer.tree(self.project)

    @unittest.skipUnless(os.name == 'nt', 'requires native Windows junctions')
    def test_windows_junction_cannot_redirect_destination(self):
        outside = self.base / 'outside'
        outside.mkdir()
        result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(self.project / '.agents'), str(outside)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.run_cli(expect=1)
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX locking and symlinks')
    def test_active_lock_blocks_removal_and_source_symlink_is_rejected(self):
        import fcntl
        self.run_cli()
        before = snapshot(self.project)
        with (self.target.parent / '.ceo-ai.lock').open('rb') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.run_cli('remove', expect=1)
        self.assertEqual(snapshot(self.project), before)
        source = self.base / 'linked-package'
        source.symlink_to(PACKAGE, target_is_directory=True)
        self.run_cli(source=source, expect=1)
        self.assertEqual(snapshot(self.project), before)

    def test_apm_owned_copy_is_not_taken_over(self):
        self.target.parent.mkdir(parents=True)
        shutil.copytree(PACKAGE, self.target)
        self.run_cli('check-package')
        before = snapshot(self.project)
        self.run_cli(expect=1)
        self.run_cli('remove', expect=1)
        self.assertEqual(snapshot(self.project), before)

    def test_interrupted_update_can_recover_original(self):
        self.run_cli()
        before = snapshot(self.target)
        fixture = '''import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("install", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original = module.os.rename
def interrupted(source, target):
    if module.Path(source).name == "next":
        os._exit(77)
    return original(source, target)
module.os.rename = interrupted
module.main(["install", "--project", sys.argv[2], "--host", "codex", "--source", sys.argv[3]])
'''
        source = self.base / 'next'
        shutil.copytree(PACKAGE, source)
        (source / 'VERSION').write_bytes(b'0.3.1\n')
        manifest = json.loads((source / 'bundle.json').read_text())
        manifest['version'] = '0.3.1'
        manifest['files']['VERSION'] = hashlib.sha256(b'0.3.1\n').hexdigest()
        (source / 'bundle.json').write_text(json.dumps(manifest))
        done = subprocess.run([sys.executable, '-c', fixture, str(SCRIPT), str(self.project), str(source)], timeout=10)
        self.assertEqual(done.returncode, 77)
        self.run_cli('recover')
        self.assertEqual(snapshot(self.target), before)
        self.run_cli('verify')

    def test_windows_ambiguous_manifest_keys_are_rejected_on_every_platform(self):
        spec = importlib.util.spec_from_file_location('portable_installer', SCRIPT)
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        invalid = [
            ['CON'], ['con.txt'], ['dir/NUL.md'], ['COM1.log'], ['LPT²'],
            ['CONIN$'], ['file.'], ['file '], ['a/b.'], ['a?b'], ['a*b'],
            ['file:stream'], ['a\\b'], ['/root'], ['C:/root'], ['a/../b'],
            ['a//b'], ['a/./b'], ['a', 'A'], ['docs/a', 'Docs/b'], ['a', 'a/b'],
        ]
        for names in invalid:
            with self.subTest(names=names), self.assertRaises(ValueError):
                installer.checked_hashes({n: '0' * 64 for n in names})
        installer.checked_hashes({'文档/план.md': '0' * 64})

    def test_local_windows_path_scope(self):
        spec = importlib.util.spec_from_file_location('windows_scope', SCRIPT)
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        for path in [r'C:relative', r'\\server\share\project', r'\\?\C:\project',
                     r'\\.\C:\project', r'\project', 'relative', 'C:/project./child']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                installer.check_windows_path(path)
        installer.check_windows_path('C:/Users/用户/мой проект')

    @unittest.skipUnless(os.name == 'nt', 'requires native Windows byte locking')
    def test_windows_cross_process_lock_blocks_then_releases(self):
        import msvcrt
        self.run_cli()
        before = snapshot(self.project)
        with (self.target.parent / '.ceo-ai.lock').open('r+b', buffering=0) as lock:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                self.run_cli('remove', expect=1)
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        self.assertEqual(snapshot(self.project), before)
        self.run_cli('remove')
        self.assertFalse(self.target.exists())

    @unittest.skipUnless(os.name == 'nt', 'requires native Windows junctions')
    def test_windows_source_and_transaction_junctions_are_rejected(self):
        self.run_cli()
        before = snapshot(self.target)
        for junction, target, action in [
            (self.base / 'source-link', PACKAGE, 'install'),
            (self.target.parent / '.ceo-ai-transaction', self.base / 'external', 'recover'),
        ]:
            if not target.exists():
                target.mkdir()
                (target / 'keep.txt').write_text('Keep')
            outside = snapshot(target)
            run = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(target)],
                                 capture_output=True, text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            try:
                self.run_cli(action, source=junction if action == 'install' else None, expect=1)
                self.assertEqual(snapshot(target), outside)
                self.assertEqual(snapshot(self.target), before)
            finally:
                junction.rmdir()

    def test_recovery_after_promotion_and_tampered_state(self):
        self.run_cli()
        expected = snapshot(self.target)
        fixture = """import importlib.util, os, sys
spec = importlib.util.spec_from_file_location('install', sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def interrupt(parent):
    os._exit(78)
m.recover = interrupt
m.main(['remove', '--project', sys.argv[2], '--host', 'codex'])
"""
        run = subprocess.run([sys.executable, '-c', fixture, str(SCRIPT), str(self.project)], timeout=10)
        self.assertEqual(run.returncode, 78)
        tx = self.target.parent / '.ceo-ai-transaction'
        state_path = tx / 'state.json'
        state = state_path.read_bytes()
        tampered = json.loads(state)
        tampered['before']['../outside'] = '0' * 64
        state_path.write_text(json.dumps(tampered))
        before = snapshot(self.project)
        self.run_cli('recover', expect=1)
        self.assertEqual(snapshot(self.project), before)
        self.assertEqual(snapshot(tx / 'old'), expected)
        state_path.write_bytes(state)
        self.run_cli('recover')
        self.assertFalse(tx.exists())
        self.assertFalse(self.target.exists())
        self.run_cli('recover', expect=1)
        self.run_cli()
        self.run_cli('verify')

    def test_recovery_keeps_completed_install_after_promotion(self):
        self.run_cli()
        source = self.base / 'new-release'
        shutil.copytree(PACKAGE, source)
        (source / 'VERSION').write_bytes(b'0.3.1\n')
        manifest = json.loads((source / 'bundle.json').read_text())
        manifest['version'] = '0.3.1'
        manifest['files']['VERSION'] = hashlib.sha256(b'0.3.1\n').hexdigest()
        (source / 'bundle.json').write_text(json.dumps(manifest))
        fixture = """import importlib.util, os, sys
spec = importlib.util.spec_from_file_location('install', sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def interrupt(parent):
    os._exit(78)
m.recover = interrupt
m.main(['install', '--project', sys.argv[2], '--host', 'codex', '--source', sys.argv[3]])
"""
        run = subprocess.run([sys.executable, '-c', fixture, str(SCRIPT), str(self.project), str(source)], timeout=10)
        self.assertEqual(run.returncode, 78)
        self.assertEqual((self.target / 'VERSION').read_text(), '0.3.1\n')
        before = snapshot(self.target)
        self.run_cli('recover')
        self.assertEqual(snapshot(self.target), before)
        self.assertFalse((self.target.parent / '.ceo-ai-transaction').exists())
        self.run_cli('verify')


if __name__ == '__main__':
    unittest.main()

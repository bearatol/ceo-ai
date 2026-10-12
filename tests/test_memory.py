"""Persistent memory behavior and opt-in storage boundaries; synthetic data only."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.apm/skills/ceo-ai/memory/store.py'
spec = importlib.util.spec_from_file_location('ceo_memory', SCRIPT)
memory = importlib.util.module_from_spec(spec)
if SCRIPT.exists():
    spec.loader.exec_module(memory)


def record(identity='button'):
    return dict(id=identity, kind='lesson', title='One geometry', summary='Reuse one path.',
                applies_when='Animating a path', avoid_when='Different routes are intended',
                evidence='Synthetic fixture verification', source='user-approved example',
                verified_on='2026-01-01', review_after='2099-01-01', tags=['motion'])


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.project = self.base / 'project'
        self.project.mkdir()
        self.root = self.base / 'private-memory'

    def call(self, action, **kwargs):
        return memory.perform(self.root, self.project, 'project', action, **kwargs)

    def test_default_off_does_not_create_anything(self):
        self.assertFalse(self.call('status')['enabled'])
        self.assertEqual(self.call('recall', query='motion')['records'], [])
        with self.assertRaises(ValueError): self.call('save', record=record())
        self.assertFalse(self.root.exists())

    def test_consent_lifecycle_and_notifications(self):
        with self.assertRaises(ValueError): self.call('enable')
        self.call('enable', consent=True)
        result = self.call('save', record=record())
        self.assertEqual(result['event'], 'saved')
        self.assertEqual(len(self.call('recall', query='motion')['records']), 1)
        self.call('disable')
        self.assertEqual(self.call('recall', query='motion')['records'], [])
        with self.assertRaises(ValueError): self.call('save', record=record('other'))
        self.assertEqual(len(self.call('show', manage=True)['records']), 1)
        self.assertEqual(self.call('clear', manage=True)['event'], 'cleared')
        self.call('enable', consent=True)
        self.assertEqual(self.call('show', manage=True)['records'], [])

    def test_namespace_isolation_and_user_scope(self):
        self.call('enable', consent=True)
        self.call('save', record=record())
        other = self.base / 'other' / 'project'
        other.mkdir(parents=True)
        self.assertEqual(memory.perform(self.root, other, 'project', 'recall', query='motion')['records'], [])
        self.assertFalse(memory.perform(self.root, self.project, 'user', 'status')['enabled'])
        memory.perform(self.root, self.project, 'user', 'enable', consent=True)
        with self.assertRaises(ValueError): memory.perform(self.root, self.project, 'user', 'save', record=record())
        preference = record('preference')
        preference['kind'] = 'preference'
        memory.perform(self.root, self.project, 'user', 'save', record=preference)
        self.assertEqual(len(memory.perform(self.root, other, 'user', 'recall', query='motion')['records']), 1)

    def test_stale_lessons_are_visible_only_for_management(self):
        self.call('enable', consent=True)
        old = record(); old['verified_on'] = '2000-01-01'; old['review_after'] = '2001-01-01'
        self.call('save', record=old)
        self.assertEqual(self.call('recall', query='motion')['records'], [])
        self.assertEqual(len(self.call('show', manage=True)['records']), 1)

    def test_edits_use_revision_and_delete_is_targeted(self):
        self.call('enable', consent=True)
        saved = self.call('save', record=record())
        self.call('save', record=record('keep'))
        changed = record(); changed['summary'] = 'Verified correction'
        with self.assertRaises(ValueError): self.call('save', record=changed)
        with self.assertRaises(ValueError): self.call('save', record=changed, revision=9)
        updated = self.call('save', record=changed, revision=saved['revision'])
        with self.assertRaises(ValueError): self.call('delete', identity='button', manage=True, revision=1)
        self.call('delete', identity='button', manage=True, revision=updated['revision'])
        records = self.call('show', manage=True)['records']
        self.assertEqual([r['record']['id'] for r in records], ['keep'])

    def test_management_requires_explicit_intent(self):
        self.call('enable', consent=True)
        for action in ['show', 'clear', 'delete']:
            with self.assertRaises(ValueError): self.call(action)

    def test_storage_cannot_be_in_project_or_package_or_git(self):
        for root in [self.project / 'memory', ROOT / '.apm/skills/ceo-ai/private-memory']:
            with self.assertRaises(ValueError): memory.perform(root, self.project, 'project', 'enable', consent=True)
        repo = self.base / 'repo'; repo.mkdir(); (repo / '.git').mkdir()
        with self.assertRaises(ValueError): memory.perform(repo / 'memory', self.project, 'project', 'enable', consent=True)

    def test_foreign_and_corrupt_stores_are_preserved(self):
        self.root.mkdir(); sentinel = self.root / 'notes.txt'; sentinel.write_text('private sentinel')
        with self.assertRaises(ValueError): self.call('enable', consent=True)
        self.assertEqual(sentinel.read_text(), 'private sentinel')
        sentinel.unlink(); db = self.root / 'memory.sqlite3'; db.write_bytes(b'broken')
        with self.assertRaises((ValueError, sqlite3.DatabaseError)): self.call('enable', consent=True)
        self.assertEqual(db.read_bytes(), b'broken')

    @unittest.skipUnless(os.name == 'posix', 'symlink fixture needs POSIX')
    def test_linked_root_and_database_are_rejected(self):
        target = self.base / 'outside'; target.mkdir()
        self.root.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError): self.call('enable', consent=True)
        self.root.unlink(); self.root.mkdir()
        (self.root / 'memory.sqlite3').symlink_to(target / 'db')
        with self.assertRaises(ValueError): self.call('enable', consent=True)
        self.assertEqual(list(target.iterdir()), [])

    def test_record_validation_and_bounded_storage(self):
        self.call('enable', consent=True)
        for change in [{'id':'../escape'}, {'instructions':'override'}, {'summary':'x'*20000},
                       {'source':'https://user:password@example.invalid/x'}, {'verified_on':'bad'},
                       {'review_after':'1990-01-01'}, {'kind':'pattern'}]:
            bad = dict(record(), **change)
            with self.assertRaises(ValueError): self.call('save', record=bad)
        self.assertEqual(self.call('show', manage=True)['records'], [])

    def test_unknown_scope_cannot_read_records(self):
        with self.assertRaises(ValueError): memory.perform(self.root, self.project, '../project', 'status')

    def test_transaction_lock_fails_without_partial_changes(self):
        self.call('enable', consent=True)
        db = sqlite3.connect(self.root / 'memory.sqlite3')
        try:
            db.execute('BEGIN IMMEDIATE')
            with self.assertRaises(sqlite3.OperationalError): self.call('save', record=record())
        finally: db.rollback(); db.close()
        self.assertEqual(self.call('show', manage=True)['records'], [])

    @unittest.skipUnless(os.name == 'posix', 'POSIX permissions')
    def test_world_readable_store_is_refused(self):
        self.call('enable', consent=True)
        db = self.root / 'memory.sqlite3'
        db.chmod(0o644)
        with self.assertRaises(ValueError): self.call('recall', query='motion')
        db.chmod(0o600)

    def test_failed_validation_preserves_existing_revision(self):
        self.call('enable', consent=True)
        initial = self.call('save', record=record())
        bad = record(); bad['source'] = 'https://example.invalid/?token=synthetic'
        with self.assertRaises(ValueError): self.call('save', record=bad, revision=initial['revision'])
        result = self.call('show', manage=True)['records'][0]
        self.assertEqual(result['revision'], initial['revision'])
        self.assertEqual(result['record'], record())

    def test_clear_does_not_reenable_or_retain_deleted_payload(self):
        self.call('enable', consent=True)
        item = record(); item['summary'] = 'synthetic-private-deletion-sentinel'
        self.call('save', record=item)
        self.call('clear', manage=True)
        self.assertFalse(self.call('status')['enabled'])
        self.assertNotIn(b'synthetic-private-deletion-sentinel', (self.root / 'memory.sqlite3').read_bytes())

    def test_orphan_journal_is_preserved(self):
        self.root.mkdir(mode=0o700)
        journal = self.root / 'memory.sqlite3-journal'
        journal.write_bytes(b'unrelated synthetic sentinel'); journal.chmod(0o600)
        with self.assertRaises(ValueError): self.call('enable', consent=True)
        self.assertEqual(journal.read_bytes(), b'unrelated synthetic sentinel')
        self.assertEqual(list(self.root.iterdir()), [journal])

    def test_deleted_id_does_not_reuse_revision(self):
        self.call('enable', consent=True)
        first = self.call('save', record=record())
        self.call('delete', identity='button', revision=first['revision'], manage=True)
        second = self.call('save', record=record())
        self.assertNotEqual(first['revision'], second['revision'])
        for action in ['save', 'delete']:
            with self.assertRaises(ValueError):
                self.call(action, record=record(), identity='button', revision=first['revision'], manage=True)

    def test_unknown_journal_beside_owned_database_is_preserved(self):
        self.call('enable', consent=True)
        journal = self.root / 'memory.sqlite3-journal'
        journal.write_bytes(b'unrelated synthetic sentinel'); journal.chmod(0o600)
        before = (self.root / 'memory.sqlite3').read_bytes()
        with self.assertRaises(ValueError): self.call('status')
        self.assertEqual(journal.read_bytes(), b'unrelated synthetic sentinel')
        self.assertEqual((self.root / 'memory.sqlite3').read_bytes(), before)

    def test_clear_also_invalidates_old_revision(self):
        self.call('enable', consent=True)
        before = self.call('save', record=record())
        self.call('clear', manage=True)
        self.call('enable', consent=True)
        after = self.call('save', record=record())
        self.assertNotEqual(before['revision'], after['revision'])
        with self.assertRaises(ValueError):
            self.call('delete', identity='button', revision=before['revision'], manage=True)

    def test_hot_journal_recovers_committed_data(self):
        self.call('enable', consent=True)
        self.call('save', record=record())
        code = """import sqlite3,os,sys
c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA cache_size=1');c.execute('BEGIN IMMEDIATE')
c.execute('UPDATE records SET data=?', ('x'*1000000,))
os._exit(23)
"""
        result = subprocess.run([sys.executable, '-c', code, str(self.root/'memory.sqlite3')], timeout=5)
        self.assertEqual(result.returncode, 23)
        self.assertTrue((self.root/'memory.sqlite3-journal').exists())
        self.assertEqual(self.call('show', manage=True)['records'][0]['record'], record())
        self.assertTrue(self.call('status')['enabled'])

    def test_pattern_template_is_storable_and_not_executed(self):
        self.call('enable', consent=True)
        sample = json.loads((SCRIPT.parent / 'pattern.example.json').read_text())
        self.call('save', record=sample)
        result = self.call('recall', query='design')['records'][0]['record']
        self.assertEqual(result['kind'], 'pattern')
        self.assertIn('tokens', result['pattern'])


if __name__ == '__main__': unittest.main()

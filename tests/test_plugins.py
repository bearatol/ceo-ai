"""Plugin payload boundaries and cache relocation, independent of host accounts."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import plugins
from install import package, tree


class PluginTests(unittest.TestCase):
    def test_one_plugin_exposes_three_skills(self):
        files = plugins.expected(ROOT)
        self.assertEqual({n for n in files if n.endswith('/SKILL.md')}, {
            'skills/ceo-ai/SKILL.md', 'skills/writer/SKILL.md', 'skills/security-scan/SKILL.md'})
        self.assertIn(b'name: writer\n', files['skills/writer/SKILL.md'])

    def test_writer_has_only_reviewed_resources_and_relocated_memory_works(self):
        files = plugins.writer_files(ROOT)
        prefix = 'skills/writer/'
        writer = {name[len(prefix):]: data for name, data in files.items()
                  if name.startswith(prefix)}
        self.assertEqual(set(writer), plugins.WRITER_SOURCE | plugins.WRITER_SHARED)
        source, _ = package(ROOT / '.apm/skills/ceo-ai')
        for name in plugins.WRITER_SHARED:
            self.assertEqual(writer[name], source[name])
        with tempfile.TemporaryDirectory(prefix='writer cache ') as folder:
            root = Path(folder).resolve()
            skill = root / 'relocated/skills/writer-how-me'
            project = root / 'project'
            project.mkdir()
            for name, data in writer.items():
                path = skill / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            store = root / 'private-memory'
            argv = [sys.executable, '-B', str(skill / 'memory/store.py'),
                    '--root', str(store), '--project', str(project), '--scope', 'user']

            def call(*args, data=None):
                result = subprocess.run(argv + list(args), cwd=project,
                    input=json.dumps(data) if data else None,
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            self.assertFalse(call('status')['enabled'])
            self.assertFalse(store.exists())
            call('enable', '--consent')
            preference = dict(id='writer-punctuation', kind='preference',
                title='Keyboard punctuation', summary='Use straight quotes in prose.',
                applies_when='Drafting personal posts', avoid_when='Exact quotations or code',
                evidence='Explicit correction in synthetic test', source='Synthetic user feedback',
                verified_on='2026-10-14', review_after='2099-01-01', tags=['writer-how-me'])
            saved = call('save', data=preference)
            self.assertEqual(call('recall', '--query', 'writer-how-me')['records'][0]['record'], preference)
            call('delete', '--manage', '--id', preference['id'], '--revision', saved['revision'])
            self.assertEqual(call('recall', '--query', 'writer-how-me')['records'], [])
            call('disable')
            self.assertFalse(call('status')['enabled'])
            self.assertFalse((skill / 'memory.sqlite3').exists())

    def test_writer_rejects_private_files_and_verifies_its_payload(self):
        self.assertEqual({n:d for n,d in tree(ROOT / 'plugins/ceo-ai').items() if n.startswith('skills/writer/')}, plugins.writer_files(ROOT))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            for name in ('.apm', 'modules'):
                shutil.copytree(ROOT / name, root / name)
            shutil.copy2(ROOT / 'VERSION', root / 'VERSION')
            (root / 'modules/ceo-ai-writer/private-profile.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'allowlist'):
                plugins.writer_files(root)

    def test_committed_package_is_current(self):
        self.assertEqual(tree(ROOT / 'plugins/ceo-ai'), plugins.expected(ROOT))

    def test_both_catalogs_resolve_to_same_skills_only_payload(self):
        for path in ('.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json'):
            catalog = json.loads((ROOT / path).read_text())
            self.assertEqual({p['name'] for p in catalog['plugins']}, {'ceo-ai'})
            entry, = [p for p in catalog['plugins'] if p['name'] == 'ceo-ai']
            source = entry['source']
            self.assertEqual(source if isinstance(source, str) else source['path'], './plugins/ceo-ai')
        files = plugins.expected(ROOT)
        self.assertEqual({name.split('/')[0] for name in files},
                         {'.codex-plugin', '.claude-plugin', 'skills', 'LICENSE', 'payload.json'})
        for manifest in ('.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
            data = json.loads(files[manifest])
            self.assertFalse({'agents', 'hooks', 'mcpServers', 'apps', 'commands'} & data.keys())
            self.assertEqual(data['version'], (ROOT / 'VERSION').read_text().strip())

    def test_relocated_cache_is_self_contained(self):
        with tempfile.TemporaryDirectory(prefix='ceo cache ') as folder:
            cache = Path(folder).resolve() / '插件'
            shutil.copytree(ROOT / 'plugins/ceo-ai', cache)
            skill = cache / 'skills/ceo-ai'
            self.assertEqual(package(skill)[0], package(ROOT / '.apm/skills/ceo-ai')[0])
            result = subprocess.run([sys.executable, '-B', str(skill / 'tools/team/team.py'),
                                     '--home', str(skill), 'list', '--type', 'agent'],
                                    cwd=folder, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('agent:decision-mentor', result.stdout)

    def test_unexpected_source_cannot_be_published_even_if_hashed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            shutil.copytree(ROOT / '.apm', root / '.apm')
            shutil.copytree(ROOT / 'modules', root / 'modules')
            shutil.copy2(ROOT / 'VERSION', root / 'VERSION')
            source = root / '.apm/skills/ceo-ai'
            (source / 'private-notes.txt').write_text('fixture')
            from install import hashes
            manifest = json.loads((source / 'bundle.json').read_text())
            files = tree(source)
            files.pop('bundle.json')
            manifest['files'] = hashes(files)
            (source / 'bundle.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'allowlist'):
                plugins.expected(root)

    def test_apm_package_rejects_private_memory_even_if_rehashed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve() / 'skill'
            shutil.copytree(ROOT / '.apm/skills/ceo-ai', root)
            (root / 'private-memory.json').write_text('synthetic private sentinel')
            from install import hashes
            manifest = json.loads((root / 'bundle.json').read_text())
            files = tree(root); files.pop('bundle.json')
            manifest['files'] = hashes(files)
            (root / 'bundle.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'allowlist'):
                package(root)

    def test_generation_preserves_unexpected_destination_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder).resolve() / 'package'
            target.mkdir()
            (target / 'private-notes.txt').write_text('fixture')
            with self.assertRaises(ValueError):
                plugins.write(target, plugins.expected(ROOT))
            self.assertEqual((target / 'private-notes.txt').read_text(), 'fixture')

    def test_layout_addition_needs_explicit_review(self):
        from install import hashes
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder).resolve() / 'package'
            files = plugins.expected(ROOT)
            removed = 'skills/ceo-ai/memory/pattern.example.json'
            old = {k:v for k,v in files.items() if k not in {removed, 'payload.json'}}
            old['payload.json'] = plugins.encode(dict(name='ceo-ai-plugin', schema_version=1,
                version='0.4.0', files=hashes(old)))
            target.mkdir()
            for name, raw in old.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'layout'):
                plugins.write(target, files)
            plugins.write(target, files, allow_layout_change=True)
            self.assertEqual(tree(target), files)

    def test_generation_preserves_edited_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder).resolve() / 'package'
            shutil.copytree(ROOT / 'plugins/ceo-ai', target)
            entry = target / 'skills/ceo-ai/SKILL.md'
            entry.write_text('Local edit')
            with self.assertRaisesRegex(ValueError, 'edited'):
                plugins.write(target, plugins.expected(ROOT))
            self.assertEqual(entry.read_text(), 'Local edit')

    @unittest.skipUnless(os.name == 'posix', 'symlink creation needs POSIX privileges')
    def test_generation_rejects_linked_destination_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / 'outside').mkdir()
            (root / 'linked').symlink_to(root / 'outside', target_is_directory=True)
            with self.assertRaises((ValueError, OSError)):
                plugins.write(root / 'linked/package', plugins.expected(ROOT))
            self.assertEqual(list((root / 'outside').iterdir()), [])

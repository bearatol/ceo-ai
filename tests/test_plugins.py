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
    def test_committed_package_is_current(self):
        self.assertEqual(tree(ROOT / 'plugins/ceo-ai'), plugins.expected(ROOT))

    def test_both_catalogs_resolve_to_same_skills_only_payload(self):
        for path in ('.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json'):
            catalog = json.loads((ROOT / path).read_text())
            entry, = catalog['plugins']
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

    def test_generation_preserves_unexpected_destination_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder).resolve() / 'package'
            target.mkdir()
            (target / 'private-notes.txt').write_text('fixture')
            with self.assertRaises(ValueError):
                plugins.write(target, plugins.expected(ROOT))
            self.assertEqual((target / 'private-notes.txt').read_text(), 'fixture')

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

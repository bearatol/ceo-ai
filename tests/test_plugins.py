"""Plugin payload boundaries and cache relocation, independent of host accounts."""
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import plugins
from install import hashes, package, tree


class PluginTests(unittest.TestCase):
    def test_one_plugin_exposes_six_skills(self):
        files = plugins.expected(ROOT)
        self.assertEqual({n for n in files if n.endswith('/SKILL.md')}, {
            'skills/ceo-ai/SKILL.md', 'skills/writer/SKILL.md', 'skills/security/SKILL.md',
            'skills/debugger/SKILL.md', 'skills/user-review/SKILL.md',
            'skills/video-editor/SKILL.md'})
        self.assertIn(b'name: writer\n', files['skills/writer/SKILL.md'])
        self.assertIn(b'name: security\n', files['skills/security/SKILL.md'])
        self.assertFalse([name for name in files if name.endswith(('.py', '.sh', '.profile'))])

    def test_new_workflows_are_self_contained_after_cache_relocation(self):
        files = plugins.expected(ROOT)
        resources = {
            'debugger': {'SKILL.md', 'LICENSE', 'VERSION.md'},
            'user-review': {'SKILL.md', 'LICENSE', 'VERSION.md',
                            'references/professional-profiles.md'},
            'video-editor': {'SKILL.md', 'LICENSE', 'VERSION.md'},
        }
        with tempfile.TemporaryDirectory(prefix='workflow cache ') as folder:
            cache = Path(folder).resolve() / '插件'
            for skill, expected in resources.items():
                prefix = 'skills/' + skill + '/'
                payload = {name[len(prefix):]: data for name, data in files.items()
                           if name.startswith(prefix)}
                self.assertEqual(set(payload), expected)
                target = cache / skill
                for name, data in payload.items():
                    path = target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                self.assertIn('name: ' + skill + '\n', (target / 'SKILL.md').read_text())
                for shared in ('LICENSE', 'VERSION'):
                    self.assertEqual(payload['VERSION.md' if shared == 'VERSION' else shared],
                                     (ROOT / shared).read_bytes())
                for path in target.rglob('*.md'):
                    for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                        if link.startswith(('https://', 'http://', '#')):
                            continue
                        resource = (path.parent / link.split('#')[0]).resolve()
                        self.assertTrue(resource.is_relative_to(target), str(resource))
                        self.assertTrue(resource.is_file(), str(resource))

    def test_new_workflows_reject_extra_or_missing_source_files(self):
        for skill in ('debugger', 'user-review', 'video-editor'):
            for mutation in ('extra', 'missing'):
                with self.subTest(skill=skill, mutation=mutation), tempfile.TemporaryDirectory() as folder:
                    root = Path(folder).resolve()
                    for name in ('.apm', 'modules'):
                        shutil.copytree(ROOT / name, root / name)
                    shutil.copy2(ROOT / 'VERSION', root / 'VERSION')
                    module = root / 'modules' / ('ceo-ai-' + skill)
                    if mutation == 'extra':
                        (module / 'private-session.json').write_text('{"synthetic": true}')
                    else:
                        (module / 'SKILL.md').unlink()
                    with self.assertRaisesRegex(ValueError, 'allowlist'):
                        plugins.expected(root)

    def test_existing_three_skill_plugin_can_add_workflows_without_losing_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder).resolve() / 'package'
            files = plugins.expected(ROOT)
            old = {name: data for name, data in files.items()
                   if name != 'payload.json' and not name.startswith(
                       ('skills/debugger/', 'skills/user-review/', 'skills/video-editor/'))}
            old['payload.json'] = plugins.encode(dict(name='ceo-ai-plugin', schema_version=1,
                version='0.8.0', files=hashes(old)))
            for name, data in old.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'layout'):
                plugins.write(target, files)
            self.assertEqual(tree(target), old)
            plugins.write(target, files, allow_layout_change=True)
            self.assertEqual(tree(target), files)
            edited = target / 'skills/user-review/SKILL.md'
            edited.write_text('Synthetic user customization')
            with self.assertRaisesRegex(ValueError, 'edited'):
                plugins.write(target, files, allow_layout_change=True)
            self.assertEqual(edited.read_text(), 'Synthetic user customization')

    def test_writer_has_only_session_resources(self):
        files = plugins.writer_files(ROOT)
        prefix = 'skills/writer/'
        writer = {name[len(prefix):]: data for name, data in files.items()}
        self.assertEqual(set(writer), {
            'LICENSE', 'VERSION.md', 'SKILL.md', 'references/skills/writer-style.md',
        })
        source, _ = package(ROOT / '.apm/skills/ceo-ai')
        for name in plugins.WRITER_SHARED:
            self.assertEqual(writer['VERSION.md' if name == 'VERSION' else name], source[name])

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

    def test_listing_assets_are_reviewed_and_bounded(self):
        files = plugins.listing_files(ROOT)
        self.assertEqual(files['README.md'], (ROOT / 'modules/ceo-ai-plugin/README.md').read_bytes())
        icon = files['.claude-plugin/icon.png']
        self.assertTrue(icon.startswith(b'\x89PNG\r\n\x1a\n'))
        width, height = int.from_bytes(icon[16:20], 'big'), int.from_bytes(icon[20:24], 'big')
        self.assertEqual(width, height)
        self.assertTrue(512 <= width <= 2048)
        self.assertLessEqual(len(icon), 256 * 1024)
        words = re.sub(r'```.*?```', '', files['README.md'].decode(), flags=re.S).split()
        self.assertGreaterEqual(len(words), 40)

    def test_listing_module_rejects_extra_missing_or_non_png_files(self):
        for mutation in ('extra', 'missing', 'not-png'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                root = Path(folder).resolve()
                module = root / 'modules/ceo-ai-plugin'
                shutil.copytree(ROOT / 'modules/ceo-ai-plugin', module)
                if mutation == 'extra':
                    (module / 'private-session.json').write_text('{"synthetic": true}')
                    pattern = 'allowlist'
                elif mutation == 'missing':
                    (module / 'icon.png').unlink()
                    pattern = 'allowlist'
                else:
                    (module / 'icon.png').write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
                    pattern = 'PNG'
                with self.assertRaisesRegex(ValueError, pattern):
                    plugins.listing_files(root)

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
                         {'.codex-plugin', '.claude-plugin', 'skills', 'LICENSE', 'README.md', 'payload.json'})
        for manifest in ('.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
            data = json.loads(files[manifest])
            self.assertFalse({'agents', 'hooks', 'mcpServers', 'apps', 'commands'} & data.keys())
            self.assertEqual(data['version'], (ROOT / 'VERSION').read_text().strip())

    def test_relocated_cache_is_self_contained(self):
        with tempfile.TemporaryDirectory(prefix='ceo cache ') as folder:
            cache = Path(folder).resolve() / '插件'
            shutil.copytree(ROOT / 'plugins/ceo-ai', cache)
            skill = cache / 'skills/ceo-ai'
            core = tree(skill)
            bundle = json.loads(core.pop('bundle.json'))
            self.assertEqual(bundle['files'], hashes(core))
            catalog = json.loads(core['catalog.json'])
            self.assertNotIn('tool:team', {item['id'] for item in catalog['components']})
            for item in catalog['components']:
                self.assertTrue((skill / item['path']).exists(), item['path'])
            self.assertFalse((skill / 'memory').exists())
            for name in ('SKILL.md', 'references/skills/ceo.md', 'orchestration/protocol.md'):
                self.assertNotIn(b'project-memory', core[name])
                self.assertNotIn(b'apm-only', core[name])
            source, _ = package(ROOT / '.apm/skills/ceo-ai')
            self.assertIn('memory/store.py', source)
            self.assertIn('tools/team/team.py', source)
            self.assertIn('references/skills/inventory.md', core)

    def test_script_removal_requires_verified_managed_upgrade(self):
        files = plugins.expected(ROOT)
        source, _ = package(ROOT / '.apm/skills/ceo-ai')
        for version in ('0.10.1', '0.10.2'):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as folder:
                target = Path(folder).resolve() / 'package'
                old = {name: data for name, data in files.items() if name != 'payload.json'}
                for path in plugins.LEGACY_NATIVE_TOOLS:
                    relative = path.split('/', 2)[2]
                    module = ROOT / 'modules/ceo-ai-security' / relative
                    old[path] = source[relative] if relative in source else module.read_bytes()
                if version == '0.10.1':
                    for name in plugins.LEGACY_VERSIONS:
                        old[name] = old.pop(name + '.md')
                old['payload.json'] = plugins.encode(dict(
                    name='ceo-ai-plugin', schema_version=1, version=version, files=hashes(old)))
                for name, data in old.items():
                    path = target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, 'layout'):
                    plugins.write(target, files)
                altered = target / 'skills/ceo-ai/scripts/ceo_inventory.py'
                original = altered.read_bytes()
                altered.write_bytes(b'# local edit\n')
                with self.assertRaisesRegex(ValueError, 'edited'):
                    plugins.write(target, files, allow_layout_change=True)
                self.assertEqual(altered.read_bytes(), b'# local edit\n')
                altered.write_bytes(original)
                plugins.write(target, files, allow_layout_change=True)
                self.assertEqual(tree(target), files)

    def test_unexpected_source_cannot_be_published_even_if_hashed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            shutil.copytree(ROOT / '.apm', root / '.apm')
            shutil.copytree(ROOT / 'modules', root / 'modules')
            shutil.copy2(ROOT / 'VERSION', root / 'VERSION')
            source = root / '.apm/skills/ceo-ai'
            (source / 'private-notes.txt').write_text('fixture')
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
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder).resolve() / 'package'
            files = plugins.expected(ROOT)
            removed = '.claude-plugin/icon.png'
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

    def test_managed_upgrade_only_removes_the_complete_known_memory_payload(self):
        files = plugins.expected(ROOT)
        source, _ = package(ROOT / '.apm/skills/ceo-ai')
        legacy_memory = {
            f'skills/{skill}/{name}': source[name]
            for skill in ('ceo-ai', 'writer') for name in plugins.APM_MEMORY_FILES
        }
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder).resolve() / 'package'
            for scenario in ('partial', 'complete'):
                with self.subTest(scenario=scenario):
                    old = files | legacy_memory
                    if scenario == 'partial':
                        del old['skills/writer/memory/store.py']
                    old.pop('payload.json')
                    old['payload.json'] = plugins.encode(dict(
                        name='ceo-ai-plugin', schema_version=1, version='0.10.1',
                        files=hashes(old),
                    ))
                    for name, data in old.items():
                        path = target / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(data)
                    with self.assertRaisesRegex(ValueError, 'layout'):
                        plugins.write(target, files)
                    if scenario == 'partial':
                        with self.assertRaisesRegex(ValueError, 'layout'):
                            plugins.write(target, files, allow_layout_change=True)
                        self.assertEqual(tree(target), old)
                    else:
                        plugins.write(target, files, allow_layout_change=True)
                        self.assertEqual(tree(target), files)

    def test_reviewed_upgrade_renames_skill_versions_to_markdown(self):
        files = plugins.expected(ROOT)
        self.assertFalse([name for name in files if name.endswith('/VERSION')])
        self.assertEqual({name for name in files if name.endswith('/VERSION.md')},
                         {name + '.md' for name in plugins.LEGACY_VERSIONS})
        old = {(name[:-3] if name.endswith('/VERSION.md') else name): data
               for name, data in files.items() if name != 'payload.json'}
        for extra in (False, True):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as folder:
                target = Path(folder).resolve() / 'package'
                previous = dict(old)
                if extra:
                    previous['skills/ceo-ai/private-notes.md'] = b'Synthetic local file\n'
                previous['payload.json'] = plugins.encode(dict(
                    name='ceo-ai-plugin', schema_version=1, version='0.10.1', files=hashes(previous)))
                for name, data in previous.items():
                    path = target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, 'layout'):
                    plugins.write(target, files)
                if extra:
                    with self.assertRaisesRegex(ValueError, 'layout'):
                        plugins.write(target, files, allow_layout_change=True)
                    self.assertEqual(tree(target), previous)
                else:
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

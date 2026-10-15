"""An optional deep scanner must not become a core install prerequisite."""
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
sys.path.insert(0, str(ROOT / 'scripts'))
import plugins
from install import tree

CORE = ROOT / 'plugins/ceo-ai'
OPTIONAL = ROOT / 'plugins/ceo-ai/skills/security-scan'

class SecurityModuleTests(unittest.TestCase):
    def write_fixture(self, root, files):
        root.mkdir()
        for name, data in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def legacy_payload(self, extra=None):
        files = plugins.expected(ROOT)
        files[plugins.LEGACY_ADAPTER] = b'# previous reviewed adapter\n'
        if extra:
            files[extra] = b'Unexpected extra file must be preserved'
        from install import hashes
        files['payload.json'] = plugins.encode(dict(name='ceo-ai-plugin',schema_version=1,
            version='0.5.0',files=hashes({n:d for n,d in files.items() if n != 'payload.json'})))
        return files

    def test_core_does_not_ship_docker_adapter(self):
        files = plugins.expected(ROOT)
        self.assertFalse('skills/ceo-ai/scripts/ceo_security_nvidia.py' in files, 'Core still ships Docker adapter')
        self.assertIn('skills/ceo-ai/scripts/ceo_security.py', files)
        self.assertNotIn('scripts/ceo_security_nvidia.py', tree(ROOT / '.apm/skills/ceo-ai'))

    def test_catalogs_offer_one_plugin_without_runtime_dependencies(self):
        for name in ('.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json'):
            data = json.loads((ROOT / name).read_text())
            self.assertEqual({p['name'] for p in data['plugins']}, {'ceo-ai'})
            for plugin in data['plugins']:
                self.assertNotIn('dependencies', plugin)

    @unittest.skipUnless(os.name == 'posix', 'Descriptor-based scanning requires POSIX')
    def test_core_index_works_without_docker(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            shutil.copytree(CORE, base / 'core')
            package = base / 'home/skills/demo'
            package.mkdir(parents=True)
            (package / 'SKILL.md').write_text('---\nname: demo\n---\nSummarize supplied text.\n')
            run = subprocess.run([sys.executable, '-I', '-B', str(base/'core/skills/ceo-ai/scripts/ceo_inventory.py'),
                                  '--home', str(base/'home')], env={'PATH':''}, capture_output=True,text=True,timeout=10)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)['entries'][0]['security']['decision'],'no-findings')
            self.assertFalse((base/'home/.ceo-inventory.json').exists())

    def test_optional_has_only_one_self_contained_skill_and_shared_bytes_match(self):
        files = plugins.security_files(ROOT)
        self.assertEqual({'skills/security-scan/'+n:d for n,d in tree(OPTIONAL).items()},files)
        self.assertEqual([n for n in files if n.endswith('/SKILL.md')],['skills/security-scan/SKILL.md'])
        for name in ('ceo_inventory.py','ceo_security.py'):
            self.assertEqual(files['skills/security-scan/scripts/'+name],
                             (ROOT/'.apm/skills/ceo-ai/scripts'/name).read_bytes())
        for name in ('.codex-plugin/plugin.json','.claude-plugin/plugin.json'):
            manifest = json.loads(plugins.expected(ROOT)[name])
            self.assertEqual(manifest['name'],'ceo-ai')
            self.assertFalse({'agents','hooks','mcpServers','apps','dependencies','commands'} & manifest.keys())

    @unittest.skipUnless(os.name == 'posix', 'Descriptor-based scanning requires POSIX')
    def test_optional_cli_survives_relocation_without_core_or_docker(self):
        with tempfile.TemporaryDirectory(prefix='security cache ') as temporary:
            base = Path(temporary).resolve()
            shutil.copytree(OPTIONAL, base/'插件')
            scripts = base/'插件/scripts'
            command = [sys.executable,'-I','-B',str(scripts/'ceo_security_nvidia.py')]
            help_result = subprocess.run(command+['--help'],env={'PATH':''},capture_output=True,text=True,timeout=10)
            self.assertEqual(help_result.returncode,0,help_result.stderr)
            package=base/'skill';package.mkdir();(package/'SKILL.md').write_text('Summarize text.')
            workspace=base/'private';workspace.mkdir(mode=0o700)
            args=['--package',str(package),'--workspace',str(workspace),'--image','sha256:'+'a'*64,'--version','2.12.0']
            result = subprocess.run(command+args,env={'PATH':''},capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,2,result.stderr)
            report=json.loads(result.stdout)
            self.assertEqual(report['status'],'INCOMPLETE')
            self.assertIsNotNone(report['bindings']['bundle_sha256'])
            self.assertEqual(list(workspace.iterdir()),[])
            (scripts/'ceo_inventory.py').unlink()
            result = subprocess.run(command+args,env={'PATH':''},capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,2)
            self.assertIsNone(json.loads(result.stdout)['bindings']['bundle_sha256'])
            self.assertNotIn(str(base),result.stdout)
            self.assertFalse(list((base/'插件').rglob('*.pyc')))

    def test_core_adapter_removal_is_explicit_and_preserves_other_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary).resolve()/'ceo-ai'
            old=self.legacy_payload();self.write_fixture(target,old)
            with self.assertRaisesRegex(ValueError,'layout'):
                plugins.write(target,plugins.expected(ROOT))
            self.assertEqual(tree(target),old)
            plugins.write(target,plugins.expected(ROOT),allow_layout_change=True)
            self.assertEqual(tree(target),plugins.expected(ROOT))
            self.assertFalse((target/plugins.LEGACY_ADAPTER).exists())

    def test_extra_removal_modified_legacy_and_wrong_receipt_are_preserved(self):
        for mode in ('extra','modified','receipt'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                target=Path(temporary).resolve()/'ceo-ai'
                old=self.legacy_payload('private.txt' if mode=='extra' else None)
                if mode=='modified':old[plugins.LEGACY_ADAPTER]+=b'user changes'
                if mode=='receipt':
                    receipt=json.loads(old['payload.json']);receipt['name']='ceo-ai-security-plugin'
                    old['payload.json']=plugins.encode(receipt)
                self.write_fixture(target,old)
                with self.assertRaises(ValueError):
                    plugins.write(target,plugins.expected(ROOT),True)
                self.assertEqual(tree(target),old)

    def test_staging_or_promotion_failure_preserves_previous_payload(self):
        for phase in ('staging','promotion'):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as temporary:
                base=Path(temporary).resolve();target=base/'ceo-ai'
                old=self.legacy_payload();self.write_fixture(target,old)
                rename=os.rename;write_bytes=Path.write_bytes
                def fail_promotion(src,dest):
                    if '-build-' in Path(src).name:raise OSError('synthetic promotion failure')
                    return rename(src,dest)
                def fail_stage(path,data):
                    if any('-build-' in part for part in path.parts):raise OSError('synthetic stage failure')
                    return write_bytes(path,data)
                patch=mock.patch.object(plugins.os,'rename',side_effect=fail_promotion) if phase=='promotion' else mock.patch.object(Path,'write_bytes',fail_stage)
                with patch,self.assertRaises(OSError):
                    plugins.write(target,plugins.expected(ROOT),True)
                self.assertEqual(tree(target),old)
                self.assertEqual(list(base.iterdir()),[target])

    def test_optional_source_allowlist_rejects_private_additions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            shutil.copytree(ROOT/'.apm',root/'.apm')
            shutil.copytree(ROOT/'modules',root/'modules')
            shutil.copyfile(ROOT/'VERSION',root/'VERSION')
            (root/'modules/ceo-ai-security/private.txt').write_text('Never publish')
            with self.assertRaisesRegex(ValueError,'allowlist'):
                plugins.security_files(root)

    def test_altered_generated_shared_runtime_fails_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            for directory in ('.apm','modules','plugins'):
                shutil.copytree(ROOT/directory,root/directory)
            shutil.copyfile(ROOT/'VERSION',root/'VERSION')
            (root/'plugins/ceo-ai/skills/security-scan/scripts/ceo_security.py').write_text('altered')
            with self.assertRaisesRegex(ValueError,'stale'):
                plugins.check(root)

    def test_all_module_sources_validated_before_core_is_replaced(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();(root/'plugins').mkdir()
            for directory in ('.apm', 'modules'):
                shutil.copytree(ROOT/directory,root/directory)
            shutil.copyfile(ROOT/'VERSION',root/'VERSION')
            old=self.legacy_payload();self.write_fixture(root/'plugins/ceo-ai',old)
            private=root/'modules/ceo-ai-security/private.txt';private.write_text('preserve')
            with mock.patch.object(plugins,'ROOT',root),mock.patch.object(plugins,'expected',lambda: plugins_expected(root)),mock.patch.object(sys,'argv',['plugins.py','--write','--allow-layout-change']),contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):plugins.main()
            self.assertEqual(tree(root/'plugins/ceo-ai'),old)
            self.assertEqual(private.read_text(),'preserve')

    def test_unrelated_skill_removal_is_never_authorized_by_layout_flag(self):
        from install import hashes
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary).resolve()/'ceo-ai'
            old=plugins.expected(ROOT)
            old['skills/custom/SKILL.md']=b'Keep this user skill'
            old['payload.json']=plugins.encode(dict(name='ceo-ai-plugin',schema_version=1,
                version='0.6.0',files=hashes({n:d for n,d in old.items() if n!='payload.json'})))
            self.write_fixture(target,old)
            with self.assertRaisesRegex(ValueError,'layout'):
                plugins.write(target,plugins.expected(ROOT),True)
            self.assertEqual(tree(target),old)

plugins_expected = plugins.expected

if __name__ == '__main__':
    unittest.main()

"""Optional real APM CLI lifecycle checks, with isolated config and no network.

Set CEO_APM_PYTHON to a Python environment with apm-cli==0.31.0.
Only config and lifecycle-lock locations are relocated; no HOME override is used.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PYTHON = os.environ.get('CEO_APM_PYTHON')
HARNESS = '''import os, sys
from importlib.metadata import version
assert version("apm-cli") == "0.31.0"
import apm_cli.config as config
config.CONFIG_DIR = sys.argv[1]
config.CONFIG_FILE = os.path.join(config.CONFIG_DIR, "config.json")
from apm_cli.install import locking
from filelock import FileLock
test_lock = FileLock(os.path.join(config.CONFIG_DIR, ".apm-lifecycle.lock"), timeout=0)
locking.lifecycle_lock = lambda: test_lock
sys.argv = ["apm", *sys.argv[2:]]
from apm_cli.cli import main
main()
'''


@unittest.skipUnless(PYTHON and sys.platform == 'darwin', 'Requires isolated APM Python and macOS sandbox-exec')
class ApmTests(unittest.TestCase):
    def test_install_update_drift_and_remove_for_three_hosts(self):
        for host, skills in [('codex','.agents/skills'), ('claude','.claude/skills'), ('cursor','.agents/skills')]:
            if os.environ.get('CEO_APM_HOST') and os.environ['CEO_APM_HOST'] != host:
                continue
            with self.subTest(host=host), tempfile.TemporaryDirectory(prefix='ceo-apm-', dir=ROOT.parent) as folder:
                base = Path(folder).resolve()
                source = base / 'package'
                source.mkdir()
                shutil.copytree(ROOT / '.apm', source / '.apm')
                shutil.copyfile(ROOT / 'apm.yml', source / 'apm.yml')
                shutil.copyfile(ROOT / 'LICENSE', source / 'LICENSE')
                project = base / 'consumer'
                project.mkdir()
                (project / 'apm.yml').write_text(json.dumps(dict(name='consumer',version='1.0.0',targets=[host])))
                (project / 'AGENTS.md').write_text('Keep this user rule.\n')
                (project / skills / 'unrelated').mkdir(parents=True)
                (project / skills / 'unrelated/SKILL.md').write_text('Keep this unrelated skill.\n')
                profile = '(version 1)(allow default)(deny network*)(deny file-write*)(allow file-write* (literal "/dev/null") (subpath ' + json.dumps(str(base)) + '))'
                env = {k:v for k,v in os.environ.items() if k in ('HOME','PATH','LANG','LC_ALL')}
                env.update(PYTHONDONTWRITEBYTECODE='1', APM_NO_SCRIPTS='1', APM_CACHE_DIR=str(base/'cache'),
                           APM_POLICY_DISABLE='1', TMPDIR=str(base))

                def apm(*args):
                    print(f'APM {host}: {args[0]}', flush=True)
                    try:
                        run = subprocess.run(['/usr/bin/sandbox-exec','-p',profile,PYTHON,'-B','-c',HARNESS,
                                              str(base/'config'),*args], cwd=project,env=env,
                                             capture_output=True,text=True,timeout=20)
                    except subprocess.TimeoutExpired as exc:
                        self.fail(f'APM timed out: {exc.stdout!r} {exc.stderr!r}')
                    self.assertEqual(run.returncode,0,run.stdout[-2500:]+run.stderr[-2500:])

                def check(expect=0):
                    run = subprocess.run([sys.executable,str(ROOT/'scripts/install.py'),'check-package',
                                          '--project',str(project),'--host',host],capture_output=True,text=True,timeout=10)
                    self.assertEqual(run.returncode,expect,run.stdout+run.stderr)

                apm('install','../package','--target',host,'--no-trust-bin')
                check()
                apm('audit','--ci','--no-policy')
                installed=project/skills/'ceo-ai'
                self.assertEqual(len(list(installed.rglob('SKILL.md'))),1)
                self.assertFalse((project/f'.{host}/agents').exists())
                entry=installed/'SKILL.md'
                original=entry.read_bytes()
                entry.write_bytes(original+b'\nUser edit\n')
                check(1)  # The documented preflight blocks update/remove on drift.
                entry.write_bytes(original)
                check()
                bundle=source/'.apm/skills/ceo-ai'
                (bundle/'VERSION').write_text('0.2.1\n')
                meta=json.loads((bundle/'bundle.json').read_text())
                meta['version']='0.2.1'
                meta['files']['VERSION']=hashlib.sha256(b'0.2.1\n').hexdigest()
                (bundle/'bundle.json').write_text(json.dumps(meta))
                manifest=json.loads((source/'apm.yml').read_text());manifest['version']='0.2.1'
                (source/'apm.yml').write_text(json.dumps(manifest))
                apm('install','../package','--target',host,'--no-trust-bin')
                check()
                self.assertEqual((installed/'VERSION').read_text(),'0.2.1\n')
                apm('audit','--ci','--no-policy')
                apm('uninstall','../package')
                self.assertFalse(installed.exists())
                self.assertEqual((project/'AGENTS.md').read_text(),'Keep this user rule.\n')
                self.assertEqual((project/skills/'unrelated/SKILL.md').read_text(),'Keep this unrelated skill.\n')


if __name__ == '__main__':
    unittest.main()

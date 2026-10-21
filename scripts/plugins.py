#!/usr/bin/env python3
"""Build or verify one CEO AI plugin with five self-contained skills."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

sys.dont_write_bytecode = True
from install import ALLOWED, checked_hashes, hashes, package, require, safe_path, tree

ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = {'ceo-ai': 'ceo-ai-plugin'}
OPTIONAL_SOURCE = frozenset({'SKILL.md', 'scripts/ceo_security_nvidia.py'})
LEGACY_ADAPTER = 'skills/ceo-ai/scripts/ceo_security_nvidia.py'
PLUGIN_METADATA = frozenset({'LICENSE', '.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'payload.json'})
WRITER_SOURCE = frozenset({'SKILL.md', 'references/skills/writer-style.md'})
WRITER_SHARED = frozenset({'LICENSE', 'VERSION', 'references/skills/project-memory.md',
                           'memory/store.py', 'memory/record.schema.json', 'memory/pattern.example.json'})
WORKFLOW_SOURCES = {
    'debugger': frozenset({'SKILL.md'}),
    'user-review': frozenset({'SKILL.md', 'references/professional-profiles.md'}),
}
WORKFLOW_SHARED = frozenset({'LICENSE', 'VERSION'})



def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def expected(root=ROOT):
    source, meta = package(root / '.apm/skills/ceo-ai')
    require(set(source) == ALLOWED, 'Plugin source differs from publication allowlist')
    require(meta['version'] == (root / 'VERSION').read_text().strip(), 'Release version mismatch')
    manifest = dict(name='ceo-ai', version=meta['version'],
                    description='Discuss decisions, challenge assumptions, and coordinate verified work.',
                    author={'name': 'Mikhail Diesperov'},
                    homepage='https://bearatol.github.io/ceo-ai/',
                    repository='https://github.com/bearatol/ceo-ai', license='MIT')
    files = {'skills/ceo-ai/' + name: data for name, data in sorted(source.items())}
    files.update(security_files(root))
    files.update(writer_files(root))
    files.update(workflow_files(root))
    files['LICENSE'] = source['LICENSE']
    files['.claude-plugin/plugin.json'] = encode(manifest)
    files['.codex-plugin/plugin.json'] = encode(dict(manifest, skills='./skills/', interface={
        'displayName': 'CEO AI', 'shortDescription': 'Discuss decisions and coordinate verified work.',
        'developerName': 'Mikhail Diesperov', 'category': 'Productivity',
        'websiteURL': 'https://bearatol.github.io/ceo-ai/', 'brandColor': '#FF963F',
        'defaultPrompt': ['Use CEO AI to challenge my assumptions and help me choose a next step.']}))
    files['payload.json'] = encode(dict(name='ceo-ai-plugin', schema_version=1,
                                        version=meta['version'], files=hashes(files)))
    return files


def security_files(root=ROOT):
    source, _ = package(root / '.apm/skills/ceo-ai')
    module = tree(root / 'modules/ceo-ai-security')
    require(set(module) == OPTIONAL_SOURCE, 'Security module differs from publication allowlist')
    for name in ('LICENSE', 'VERSION', 'scripts/ceo_inventory.py', 'scripts/ceo_security.py',
                 'scripts/ceo_inventory_windows.py'):
        module[name] = source[name]
    return {'skills/security-scan/' + name: data for name, data in sorted(module.items())}


def writer_files(root=ROOT):
    source, _ = package(root / '.apm/skills/ceo-ai')
    module = tree(root / 'modules/ceo-ai-writer')
    require(set(module) == WRITER_SOURCE, 'Writer module differs from publication allowlist')
    module.update({name: source[name] for name in WRITER_SHARED})
    return {'skills/writer/' + name: data for name, data in sorted(module.items())}


def workflow_files(root=ROOT):
    source, _ = package(root / '.apm/skills/ceo-ai')
    files = {}
    for skill, allowed in WORKFLOW_SOURCES.items():
        module = tree(root / 'modules' / ('ceo-ai-' + skill))
        require(set(module) == allowed, skill + ' module differs from publication allowlist')
        module.update({name: source[name] for name in WORKFLOW_SHARED})
        files.update({'skills/' + skill + '/' + name: data
                      for name, data in sorted(module.items())})
    return files


def publication_paths(plugin):
    require(plugin in RECEIPTS, 'Unknown plugin identity')
    security = OPTIONAL_SOURCE | {'LICENSE', 'VERSION', 'scripts/ceo_inventory.py', 'scripts/ceo_security.py',
                                  'scripts/ceo_inventory_windows.py'}
    return (PLUGIN_METADATA | {'skills/ceo-ai/' + name for name in ALLOWED}
            | {'skills/writer/' + name for name in WRITER_SOURCE | WRITER_SHARED}
            | {'skills/' + skill + '/' + name for skill, allowed in WORKFLOW_SOURCES.items()
               for name in allowed | WORKFLOW_SHARED}
            | {'skills/security-scan/' + name for name in security})


def preflight(destination, files, allow_layout_change=False, *, plugin='ceo-ai'):
    destination = safe_path(destination)
    require(set(files) == publication_paths(plugin), 'Plugin output differs from publication allowlist')
    receipt = json.loads(files['payload.json'])
    require(receipt.get('name') == RECEIPTS[plugin] and receipt.get('schema_version') == 1,
            'Unexpected output plugin identity')
    require(hashes({name: data for name, data in files.items() if name != 'payload.json'}) ==
            checked_hashes(receipt.get('files')), 'Output payload receipt mismatch')
    previous = None
    if destination.exists():
        previous = tree(destination)
        require('payload.json' in previous, 'Unmanaged plugin directory; preserve it first')
        old_payload = {name: data for name, data in previous.items() if name != 'payload.json'}
        receipt = json.loads(previous['payload.json'])
        require(receipt.get('name') == RECEIPTS[plugin] and receipt.get('schema_version') == 1,
                'Unknown plugin payload')
        require(hashes(old_payload) == checked_hashes(receipt.get('files')),
                'Generated plugin was edited; preserve changes before rebuilding')
        removed = set(previous) - set(files)
        require(set(previous) == set(files) or (allow_layout_change and
                (not removed or plugin == 'ceo-ai' and removed == {LEGACY_ADAPTER})),
                'Plugin file layout changed; review migration before rebuilding')
    return destination, previous


def write(destination, files, allow_layout_change=False, *, plugin='ceo-ai'):
    destination, previous = preflight(destination, files, allow_layout_change, plugin=plugin)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.' + plugin + '-build-', dir=destination.parent))
    backup = destination.with_name('.' + plugin + '-previous-' + uuid.uuid4().hex)
    # Trusted developer checkout only, not a concurrent runtime installer.
    # Stage a full verified payload before removing any owned old file. A failed
    # promotion restores the previous directory; a crash leaves a named backup.
    try:
        for name, data in sorted(files.items(), key=lambda item: item[0] == 'payload.json'):
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        require(tree(stage) == files, 'Staged plugin verification failed')
        if previous is not None:
            require(tree(destination) == previous, 'Generated plugin changed before promotion')
            require(not backup.exists(), 'Plugin backup path already exists')
            os.rename(destination, backup)
        try:
            require(not destination.exists(), 'Plugin destination appeared before promotion')
            os.rename(stage, destination)
        except BaseException:
            if previous is not None:
                os.rename(backup, destination)
            raise
        if previous is not None:
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def check(root=ROOT):
    require(tree(root / 'plugins/ceo-ai') == expected(root),
            'Plugin is stale; review source changes and run scripts/plugins.py --write')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--allow-layout-change', action='store_true',
                        help='Accept reviewed additions or the known core Docker-adapter removal')
    args = parser.parse_args()
    try:
        if args.write:
            outputs = {'ceo-ai': expected()}
            # Validate all sources and existing destinations before the first write.
            for plugin, files in outputs.items():
                preflight(ROOT / 'plugins' / plugin, files, args.allow_layout_change, plugin=plugin)
            for plugin, files in outputs.items():
                write(ROOT / 'plugins' / plugin, files, args.allow_layout_change, plugin=plugin)
        check()
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, 'error: ' + str(exc) + '\n')
    print('Plugin payload verified')


if __name__ == '__main__':
    main()

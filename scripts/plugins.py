#!/usr/bin/env python3
"""Build or verify the core plugin and separately installed security module."""
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
RECEIPTS = {'ceo-ai': 'ceo-ai-plugin', 'ceo-ai-security': 'ceo-ai-security-plugin'}
OPTIONAL_SOURCE = frozenset({'SKILL.md', 'scripts/ceo_security_nvidia.py'})
LEGACY_ADAPTER = 'skills/ceo-ai/scripts/ceo_security_nvidia.py'
PLUGIN_METADATA = frozenset({'LICENSE', '.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'payload.json'})



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


def expected_security(root=ROOT):
    source, meta = package(root / '.apm/skills/ceo-ai')
    require(meta['version'] == (root / 'VERSION').read_text().strip(), 'Release version mismatch')
    module = tree(root / 'modules/ceo-ai-security')
    require(set(module) == OPTIONAL_SOURCE, 'Optional module differs from publication allowlist')
    # Shared code has one source of truth; the relocated plugin never searches
    # another installed cache or the development checkout at runtime.
    for name in ('LICENSE', 'VERSION', 'scripts/ceo_inventory.py', 'scripts/ceo_security.py'):
        module[name] = source[name]
    files = {'skills/security-scan/' + name: data for name, data in sorted(module.items())}
    manifest = dict(name='ceo-ai-security', version=meta['version'],
                    description='Optional local deep scans. Requires Python, Docker and a prepared scanner image.',
                    author={'name': 'Mikhail Diesperov'}, homepage='https://bearatol.github.io/ceo-ai/',
                    repository='https://github.com/bearatol/ceo-ai', license='MIT')
    files['LICENSE'] = source['LICENSE']
    files['.claude-plugin/plugin.json'] = encode(manifest)
    files['.codex-plugin/plugin.json'] = encode(dict(manifest, skills='./skills/', interface={
        'displayName': 'CEO AI Security (optional)',
        'shortDescription': 'Local deep scans; requires Docker and a prepared image.',
        'developerName': 'Mikhail Diesperov', 'category': 'Developer tools',
        'websiteURL': 'https://bearatol.github.io/ceo-ai/', 'brandColor': '#FF963F',
        'defaultPrompt': ['Check prerequisites and scope for an optional local deep skill scan.']}))
    files['payload.json'] = encode(dict(name=RECEIPTS['ceo-ai-security'], schema_version=1,
                                        version=meta['version'], files=hashes(files)))
    return files


def publication_paths(plugin):
    require(plugin in RECEIPTS, 'Unknown plugin identity')
    if plugin == 'ceo-ai':
        return PLUGIN_METADATA | {'skills/ceo-ai/' + name for name in ALLOWED}
    resources = OPTIONAL_SOURCE | {'LICENSE', 'VERSION', 'scripts/ceo_inventory.py', 'scripts/ceo_security.py'}
    return PLUGIN_METADATA | {'skills/security-scan/' + name for name in resources}


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
    require(tree(root / 'plugins/ceo-ai-security') == expected_security(root),
            'Optional security plugin is stale; review sources and rebuild')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--allow-layout-change', action='store_true',
                        help='Accept reviewed additions or the known core Docker-adapter removal')
    args = parser.parse_args()
    try:
        if args.write:
            outputs = {'ceo-ai': expected(), 'ceo-ai-security': expected_security()}
            # Validate both sources and existing destinations before the first write.
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

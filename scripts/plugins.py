#!/usr/bin/env python3
"""Build or verify one CEO AI plugin with six self-contained skills and listing assets."""
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
OPTIONAL_SOURCE = frozenset({'SKILL.md', 'scripts/ceo_security_nvidia.py',
                             'references/engagement.md', 'references/testing-profiles.md',
                             'references/reporting.md', 'references/skill-scan.md'})
LEGACY_ADAPTER = 'skills/ceo-ai/scripts/ceo_security_nvidia.py'
LEGACY_SECURITY = frozenset('skills/security-scan/' + name for name in (
    'LICENSE', 'SKILL.md', 'VERSION', 'scripts/ceo_inventory.py',
    'scripts/ceo_inventory_windows.py', 'scripts/ceo_security.py',
    'scripts/ceo_security_nvidia.py'))
PLUGIN_METADATA = frozenset({'LICENSE', '.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'payload.json'})
WRITER_SOURCE = frozenset({'SKILL.md', 'references/skills/writer-style.md'})
WRITER_SHARED = frozenset({'LICENSE', 'VERSION'})
APM_MEMORY_FILES = frozenset({
    'references/skills/project-memory.md', 'memory/store.py', 'memory/record.schema.json',
    'memory/pattern.example.json',
})
APM_MEMORY_COMPONENTS = frozenset({'skill:project-memory', 'tool:memory'})
APM_ONLY_MARKDOWN = ('SKILL.md', 'references/skills/ceo.md', 'orchestration/protocol.md')
NATIVE_CORE = ALLOWED - APM_MEMORY_FILES
LEGACY_CORE_MEMORY = frozenset('skills/ceo-ai/' + name for name in APM_MEMORY_FILES)
LEGACY_WRITER_MEMORY = frozenset('skills/writer/' + name for name in APM_MEMORY_FILES)
WORKFLOW_SOURCES = {
    'debugger': frozenset({'SKILL.md'}),
    'user-review': frozenset({'SKILL.md', 'references/professional-profiles.md'}),
    'video-editor': frozenset({'SKILL.md'}),
}
WORKFLOW_SHARED = frozenset({'LICENSE', 'VERSION'})
# Directory listing assets: module file name -> plugin path.
LISTING_FILES = {'README.md': 'README.md', 'icon.png': '.claude-plugin/icon.png'}



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
    core = native_core(source, meta)
    files = {'skills/ceo-ai/' + name: data for name, data in sorted(core.items())}
    files.update(security_files(root))
    files.update(writer_files(root))
    files.update(workflow_files(root))
    files.update(listing_files(root))
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


def native_core(source, meta):
    files = {name: source[name] for name in NATIVE_CORE if name != 'bundle.json'}
    start_marker = b'<!-- apm-only -->\n'
    end_marker = b'<!-- /apm-only -->\n'
    for name in APM_ONLY_MARKDOWN:
        content = files[name]
        require(content.count(start_marker) == content.count(end_marker) == 1,
                'Invalid APM-only guidance markers in ' + name)
        before, _, rest = content.partition(start_marker)
        _, end, after = rest.partition(end_marker)
        require(end, 'Invalid APM-only guidance marker order in ' + name)
        files[name] = before + after
    catalog = json.loads(files['catalog.json'])
    catalog['components'] = [item for item in catalog['components']
                             if item['id'] not in APM_MEMORY_COMPONENTS]
    files['catalog.json'] = encode(catalog)
    profile = files['profiles/core.profile'].decode('utf-8').splitlines()
    files['profiles/core.profile'] = ''.join(
        item + '\n' for item in profile if item not in APM_MEMORY_COMPONENTS).encode('utf-8')
    files['bundle.json'] = encode(dict(meta, files=hashes(files)))
    return files


def security_files(root=ROOT):
    source, _ = package(root / '.apm/skills/ceo-ai')
    module = tree(root / 'modules/ceo-ai-security')
    require(set(module) == OPTIONAL_SOURCE, 'Security module differs from publication allowlist')
    for name in ('LICENSE', 'VERSION', 'scripts/ceo_inventory.py', 'scripts/ceo_security.py',
                 'scripts/ceo_inventory_windows.py'):
        module[name] = source[name]
    return {'skills/security/' + name: data for name, data in sorted(module.items())}


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


def listing_files(root=ROOT):
    module = tree(root / 'modules/ceo-ai-plugin')
    require(set(module) == set(LISTING_FILES), 'Listing module differs from publication allowlist')
    require(module['icon.png'].startswith(b'\x89PNG\r\n\x1a\n'), 'Listing icon must be a PNG')
    return {LISTING_FILES[name]: data for name, data in sorted(module.items())}


def publication_paths(plugin):
    require(plugin in RECEIPTS, 'Unknown plugin identity')
    security = OPTIONAL_SOURCE | {'LICENSE', 'VERSION', 'scripts/ceo_inventory.py', 'scripts/ceo_security.py',
                                  'scripts/ceo_inventory_windows.py'}
    return (PLUGIN_METADATA | set(LISTING_FILES.values()) | {'skills/ceo-ai/' + name for name in NATIVE_CORE}
            | {'skills/writer/' + name for name in WRITER_SOURCE | WRITER_SHARED}
            | {'skills/' + skill + '/' + name for skill, allowed in WORKFLOW_SOURCES.items()
               for name in allowed | WORKFLOW_SHARED}
            | {'skills/security/' + name for name in security})


def reviewed_removals(previous, removed, plugin):
    if plugin != 'ceo-ai':
        return False
    # Older managed packages either have only core memory or carry both copies.
    legacy_memory = LEGACY_CORE_MEMORY | LEGACY_WRITER_MEMORY
    if removed & legacy_memory not in (set(), LEGACY_CORE_MEMORY, legacy_memory):
        return False
    removed = removed - legacy_memory
    if not removed or removed == {LEGACY_ADAPTER}:
        return True
    # Only the complete historical payload may move. A partial legacy tree or
    # an existing new tree could contain work that the rename would discard.
    legacy = {name for name in previous if name.startswith('skills/security-scan/')}
    return (legacy == LEGACY_SECURITY and
            not any(name.startswith('skills/security/') for name in previous) and
            removed in (LEGACY_SECURITY, LEGACY_SECURITY | {LEGACY_ADAPTER}))


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
                (not removed or reviewed_removals(previous, removed, plugin))),
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
                        help='Accept reviewed additions, the security skill rename, or known legacy payload removals')
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

#!/usr/bin/env python3
"""Build or verify the skills-only plugin from the canonical APM bundle."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from install import checked_hashes, hashes, package, require, safe_path, tree

ROOT = Path(__file__).resolve().parents[1]
# Publication is deliberately narrower than an arbitrary bundle manifest.
ALLOWED = frozenset('''LICENSE SKILL.md VERSION bundle.json catalog.json catalog.schema.json
agents/ceo.md agents/decision-mentor.md agents/engineer.md agents/qa-reviewer.md
orchestration/project-state.schema.json orchestration/protocol.md
orchestration/result.schema.json orchestration/task.schema.json
orchestration/templates/result.json orchestration/templates/task.json
profiles/core.profile references/skills/capability-discovery.md references/skills/ceo.md
references/skills/context-engineering.md references/skills/quality-review.md
references/skills/skill-authoring.md references/skills/skill-router.md
references/skills/software-delivery.md scripts/catalog.py scripts/ceo_inventory.py
tools/team/team.py tools/team/team.sh'''.split())


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


def write(destination, files):
    destination = safe_path(destination)
    if destination.exists():
        previous = tree(destination)
        require('payload.json' in previous, 'Unmanaged plugin directory; preserve it first')
        receipt = json.loads(previous.pop('payload.json'))
        require(receipt.get('name') == 'ceo-ai-plugin' and receipt.get('schema_version') == 1,
                'Unknown plugin payload')
        require(hashes(previous) == checked_hashes(receipt.get('files')),
                'Generated plugin was edited; preserve changes before rebuilding')
        require(set(previous) == set(files) - {'payload.json'},
                'Plugin file layout changed; review migration before rebuilding')
    # This developer build is rerunnable, not a runtime installer or transaction manager.
    # Only trusted checkouts without concurrent noncooperating writers are supported.
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(files.items(), key=lambda item: item[0] == 'payload.json'):
        path = safe_path(destination / name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def check(root=ROOT):
    require(tree(root / 'plugins/ceo-ai') == expected(root),
            'Plugin is stale; review source changes and run scripts/plugins.py --write')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    try:
        if args.write:
            write(ROOT / 'plugins/ceo-ai', expected())
        check()
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, 'error: ' + str(exc) + '\n')
    print('Plugin payload verified')


if __name__ == '__main__':
    main()

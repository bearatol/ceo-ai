#!/usr/bin/env python3
"""Refresh or check the committed integrity manifest after editing bundled files."""
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from install import ALLOWED, require, PACKAGE, hashes, package, tree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        files = tree(PACKAGE)
        require(set(files) == ALLOWED, 'Bundle source differs from publication allowlist')
        files.pop('bundle.json', None)
        data = dict(schema_version=1, name='ceo-ai', version=files['VERSION'].decode().strip(), files=hashes(files))
        (PACKAGE / 'bundle.json').write_text(json.dumps(data, indent=2) + '\n')
    package(PACKAGE)
    print('Bundle manifest verified')


if __name__ == '__main__':
    main()

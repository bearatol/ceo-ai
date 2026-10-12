#!/usr/bin/env python3
"""Install a reviewed local bundle into one project. No network or host execution."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import stat
import sys

sys.dont_write_bytecode = True
PACKAGE = Path(__file__).absolute().parents[1] / '.apm/skills/ceo-ai'
TARGETS = {'codex': '.agents/skills', 'cursor': '.agents/skills', 'claude': '.claude/skills'}
OWNER = 'ceo-ai-installer-v1'
RECEIPT = '.ceo-ai-receipt.json'
LOCK = '.ceo-ai.lock'
TX = '.ceo-ai-transaction'
REPARSE_POINT = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_paths(names):
    """Accept one unambiguous portable spelling for every file and parent."""
    prefixes, files = {}, set()
    for name in names:
        require(isinstance(name, str) and name not in ('', '.'), 'Unsafe manifest path')
        path = PurePosixPath(name)
        require(not path.is_absolute() and path.as_posix() == name, 'Unsafe manifest path')
        for part in path.parts:
            require(part not in ('.', '..') and not part.endswith((' ', '.')) and
                    not any(ord(c) < 32 or c in '<>:"\\|?*' for c in part),
                    'Unsafe manifest path')
            require(not re.fullmatch(r'(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³]|conin\$|conout\$)',
                                     part.split('.')[0], re.IGNORECASE), 'Reserved Windows name')
        key = tuple(part.casefold() for part in path.parts)
        files.add(key)
        for i in range(1, len(path.parts) + 1):
            prefix, spelling = key[:i], path.parts[:i]
            require(prefix not in prefixes or prefixes[prefix] == spelling, 'Case-colliding paths')
            prefixes[prefix] = spelling
    for key in files:
        require(not any(key[:i] in files for i in range(1, len(key))), 'File/directory path conflict')


def check_windows_path(path):
    """Limit Windows writes to fully qualified, ordinary local drive paths."""
    path = PureWindowsPath(path)
    require(path.is_absolute() and re.fullmatch(r'[A-Za-z]:', path.drive),
            'Use an absolute local drive path; network and device paths are unsupported')
    if len(path.parts) > 1:
        checked_paths([PurePosixPath(*path.parts[1:]).as_posix()])


def local_stat(path):
    info = path.lstat()
    require(not stat.S_ISLNK(info.st_mode) and
            not (getattr(info, 'st_file_attributes', 0) & REPARSE_POINT),
            'Symlink or reparse point refused: ' + str(path))
    return info


def safe_path(path):
    if os.name == 'nt':
        check_windows_path(path)
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        try:
            info = local_stat(part)
        except FileNotFoundError:
            continue
        if part != path:
            require(stat.S_ISDIR(info.st_mode), 'Parent is not a directory: ' + str(part))
    return path


def tree(root, partial_manifest=None):
    """Read bounded regular files; reject symlinks, special files and empty additions."""
    root = safe_path(root)
    require(root.is_dir(), 'Directory missing: ' + str(root))
    files, directories, size = {}, set(), 0
    for parent, names, children in os.walk(root, followlinks=False):
        for name in names + children:
            path = Path(parent) / name
            mode = local_stat(path).st_mode
            relative = path.relative_to(root).as_posix()
            if stat.S_ISDIR(mode):
                directories.add(relative)
            else:
                require(stat.S_ISREG(mode), 'Nonregular file refused: ' + relative)
                require(path.stat().st_size <= 256 * 1024, 'File is too large: ' + relative)
                data = path.read_bytes()
                size += len(data)
                require(len(files) < 1024 and size <= 16 * 1024 * 1024, 'Bundle size limit exceeded')
                files[relative] = data
    checked_paths(files)
    expected_dirs = {parent.as_posix() for name in (files if partial_manifest is None else partial_manifest)
                     for parent in PurePosixPath(name).parents if str(parent) != '.'}
    require(directories == expected_dirs if partial_manifest is None else directories <= expected_dirs,
            'Unexpected empty directory; preserve it before continuing')
    return files


def hashes(files):
    return {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}


def document(data):
    value = json.loads(data)
    require(isinstance(value, dict), 'Expected a JSON object')
    return value


def checked_hashes(value):
    require(isinstance(value, dict) and len(value) <= 1024, 'Invalid file manifest')
    checked_paths(value)
    for digest in value.values():
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'Invalid file hash')
    return value


def package(root):
    files = tree(root)
    require('bundle.json' in files, 'Bundle manifest missing')
    meta = document(files['bundle.json'])
    require(meta.get('name') == 'ceo-ai' and meta.get('schema_version') == 1, 'Unknown bundle')
    require(hashes({n: d for n, d in files.items() if n != 'bundle.json'}) == checked_hashes(meta.get('files')),
            'Bundle files differ from the manifest; do not install or update')
    require(meta.get('version') == files.get('VERSION', b'').decode().strip(), 'Version mismatch')
    require('SKILL.md' in files and 'catalog.json' in files, 'Required bundle resources missing')
    return files, meta


def owned(root):
    files = tree(root)
    require(RECEIPT in files, 'Existing folder is not owned by this installer; nothing replaced')
    receipt = document(files[RECEIPT])
    require(receipt.get('owner') == OWNER, 'Unknown installation owner')
    payload = {n: d for n, d in files.items() if n != RECEIPT}
    require(hashes(payload) == checked_hashes(receipt.get('files')),
            'Installed files changed; preserve and review local edits before continuing')
    return files


def write_tree(root, files):
    root.mkdir()
    for name, data in files.items():
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)


@contextmanager
def locked(parent):
    path = safe_path(parent / LOCK)
    created = False
    try:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
    except FileExistsError:
        require(path.is_file(), 'Unmanaged lock path')
        fd = os.open(path, os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'r+b', buffering=0) as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'Nonregular lock file')
        if os.name == 'posix':
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        elif os.name == 'nt':
            import msvcrt
            if created:
                stream.write((OWNER + '\n').encode())
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            raise ValueError('Unsupported locking platform')
        if created:
            stream.seek(0)
            stream.write((OWNER + '\n').encode())
        stream.seek(0)
        require(stream.read(128) == (OWNER + '\n').encode(), 'Unmanaged lock file; nothing replaced')
        yield


def clean_copy(path, expected):
    if not path.exists():
        return
    actual = hashes(tree(path, partial_manifest=expected))
    require(all(expected.get(n) == d for n, d in actual.items()), 'Transaction files changed; preserved')
    shutil.rmtree(path)


def recover(parent):
    tx, destination = parent / TX, parent / 'ceo-ai'
    require(tx.exists(), 'No interrupted transaction')
    safe_path(tx)
    require(tx.is_dir(), 'Invalid transaction')
    state_info = local_stat(tx / 'state.json')
    require(stat.S_ISREG(state_info.st_mode), 'Transaction state must be a regular file')
    require(state_info.st_size <= 256 * 1024, 'Transaction state is too large')
    state = document((tx / 'state.json').read_bytes())
    require(state.get('owner') == OWNER and state.get('action') in ('install', 'remove'), 'Unknown transaction')
    require(set(p.name for p in tx.iterdir()) <= {'state.json', 'old', 'next'}, 'Unexpected transaction content')
    before, after = checked_hashes(state.get('before')), checked_hashes(state.get('after'))
    safe_path(destination)
    if destination.exists():
        current = hashes(owned(destination))
        require(current == before or current == after, 'Destination changed during transaction; preserved')
    elif state['action'] == 'install' and before:
        require(hashes(owned(tx / 'old')) == before, 'Previous installation cannot be restored automatically')
        os.rename(tx / 'old', destination)
    clean_copy(tx / 'next', after)
    clean_copy(tx / 'old', before)
    (tx / 'state.json').unlink()
    tx.rmdir()


def change(parent, action, new_files):
    destination, tx = parent / 'ceo-ai', parent / TX
    require(not tx.exists(), 'Interrupted transaction found; run recover before retrying')
    previous = owned(destination) if destination.exists() else {}
    if action == 'remove' and not previous:
        return 'Already absent'
    if previous == new_files:
        return 'Already current'
    tx.mkdir()
    # Durable intent is written before any managed directory is renamed.
    state = dict(owner=OWNER, action=action, before=hashes(previous), after=hashes(new_files))
    with (tx / 'state.json').open('x') as stream:
        json.dump(state, stream)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if new_files:
            write_tree(tx / 'next', new_files)
            require(hashes(tree(tx / 'next')) == hashes(new_files), 'Staged content mismatch')
        if previous:
            require(owned(destination) == previous, 'Installation changed before promotion')
            os.rename(destination, tx / 'old')
        if new_files:
            require(not destination.exists(), 'Destination appeared during promotion')
            os.rename(tx / 'next', destination)
        recover(parent)
    except Exception:
        # Preserve the transaction for explicit recovery, including partial staging.
        raise
    return 'Installed' if action == 'install' else 'Removed'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'remove', 'verify', 'recover', 'check-package'])
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--host', required=True, choices=TARGETS)
    parser.add_argument('--source', type=Path, default=PACKAGE)
    args = parser.parse_args(argv)
    try:
        project = safe_path(args.project)
        require(project.is_dir(), 'Project directory must already exist')
        parent = safe_path(project / TARGETS[args.host])
        destination = safe_path(parent / 'ceo-ai')
        new_files = {}
        if args.action == 'install':
            payload, meta = package(args.source)
            require(RECEIPT not in payload, 'Source must be an uninstalled release bundle')
            receipt = dict(owner=OWNER, version=meta['version'], files=hashes(payload))
            new_files = dict(payload, **{RECEIPT: (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode()})
        if args.action == 'check-package':
            package(destination)
            print('Package contents match the release manifest')
            return 0
        if args.action == 'verify':
            owned(destination)
            print('Installed files match the ownership receipt')
            return 0
        # Collision/drift checks precede directory or lock creation.
        if destination.exists():
            owned(destination)
        elif args.action == 'remove' and not (parent / TX).exists():
            print('Already absent')
            return 0
        parent.mkdir(parents=True, exist_ok=True)
        with locked(parent):
            if args.action == 'recover':
                recover(parent)
                print('Recovered interrupted transaction')
            else:
                print(change(parent, args.action, new_files))
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print('error: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

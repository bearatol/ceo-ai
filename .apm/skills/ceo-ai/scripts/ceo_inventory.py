#!/usr/bin/env python3
"""Inspect approved skill/agent metadata; refresh a separate cache on request.

No discovered code is executed. The descriptor-based scanner requires POSIX
no-follow operations. Other hosts should use their native read-only inventory.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import stat
import sys
import time
import uuid

try:
    import tomllib
except ImportError:
    tomllib = None

try:
    import fcntl
except ImportError:
    fcntl = None

OWNER = "ceo-inventory-v1"
CACHE = ".ceo-inventory.json"
MAX_FILE = 256 * 1024
MAX_CACHE = 2 * 1024 * 1024
MAX_COUNT = 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_DEPTH = 12
NAME = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
SECRET_NAMES = frozenset({'.env', 'auth.json', 'credentials', 'credentials.json',
                          'credentials.toml', 'credentials.yaml', 'credentials.yml',
                          'credentials.txt', 'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519'})
EXCLUDED_DIRS = frozenset({'.git', '.ssh', '.aws', '.gnupg', '.azure', '.kube',
                           '.venv', 'node_modules', '__pycache__'})
_security_module = None


class InventoryError(Exception):
    pass


def open_dir(name, parent=None):
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)


def open_root(value):
    if fcntl is None or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise InventoryError("safe no-follow directory operations are unavailable on this host")
    path = pathlib.Path(os.path.abspath(os.path.expanduser(value)))
    fd = open_dir(path.anchor)
    try:
        for part in path.parts[1:]:
            next_fd = open_dir(part, fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_regular(parent, name, limit):
    # O_NONBLOCK prevents a hostile FIFO from blocking before fstat.
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
            raise InventoryError("nonregular, multiply-linked or oversized file")
        chunks, size = [], 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise InventoryError(f"oversized file: {name}")
        after = os.fstat(fd)
        if signature(before) != signature(after):
            raise InventoryError(f"file changed during scan: {name}")
        return b"".join(chunks)
    finally:
        os.close(fd)


def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class ScanBudget:
    def __init__(self):
        self.started = time.monotonic()
        self.count = self.total = 0

    def check(self, *, entries=0, size=0):
        self.count += entries
        self.total += size
        if self.count > MAX_COUNT or self.total > MAX_TOTAL or time.monotonic() - self.started > 5:
            raise InventoryError('inventory scan limit exceeded')


def sensitive_name(name):
    lower = name.lower()
    return (lower in SECRET_NAMES or lower.startswith('.env.')
            or lower.endswith(('.pem', '.key', '.p12', '.pfx', '.keystore')))


def checked_name(name):
    if name in ('', '.', '..') or '\\' in name or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise InventoryError('unsupported file name')


def collect_bundle(root, budget):
    """Read a bounded in-memory snapshot and recheck every admitted tree entry.

    Excluded resources are stat'ed only, never opened or copied. The returned
    bytes are the scan input even if the source changes after this function.
    """
    files, excluded = {}, []

    def walk(parent, prefix='', depth=0, *, verify=False):
        budget.check()
        if depth > MAX_DEPTH:
            raise InventoryError('package depth limit exceeded')
        before = signature(os.fstat(parent))
        records = {}
        # Bound enumeration before sorting, including names of excluded entries.
        children = []
        with os.scandir(parent) as iterator:
            for child in iterator:
                budget.check(entries=0 if verify else 1)
                if len(children) >= MAX_COUNT:
                    raise InventoryError('package entry limit exceeded')
                children.append(child.name)
        for name in sorted(children):
            checked_name(name)
            relative = prefix + name
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            entry_signature = signature(info)
            records[relative] = entry_signature
            is_directory = stat.S_ISDIR(info.st_mode)
            if not is_directory and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
                raise InventoryError('symlink, special or multiply-linked resource refused')
            if sensitive_name(name) or is_directory and name.lower() in EXCLUDED_DIRS:
                if not verify:
                    excluded.append({'path': relative, 'reason': 'sensitive-resource'
                                     if sensitive_name(name) or name.lower() not in
                                     {'.git', '.venv', 'node_modules', '__pycache__'}
                                     else 'excluded-resource'})
                continue
            if not is_directory and info.st_size > MAX_FILE:
                if not verify:
                    excluded.append({'path': relative, 'reason': 'oversized-resource'})
                continue
            if is_directory:
                child = open_dir(name, parent)
                try:
                    if signature(os.fstat(child)) != entry_signature:
                        raise InventoryError('directory changed during scan')
                    records.update(walk(child, relative + '/', depth + 1, verify=verify))
                finally:
                    os.close(child)
            elif not verify:
                raw = read_regular(parent, name, MAX_FILE)
                budget.check(size=len(raw))
                if signature(os.stat(name, dir_fd=parent, follow_symlinks=False)) != entry_signature:
                    raise InventoryError('resource changed during scan')
                files[relative] = raw
        if signature(os.fstat(parent)) != before:
            raise InventoryError('directory changed during scan')
        records[prefix or '.'] = before
        return records

    first = walk(root)
    if first != walk(root, verify=True):
        raise InventoryError('package changed during scan')
    return files, excluded


def snapshot_package(path, kind='skill', *, approved_alias_roots=()):
    """Return bytes for one explicitly approved package; never search other roots."""
    if approved_alias_roots:
        files, excluded, _ = capture_alias_package(path, kind, approved_alias_roots, ScanBudget())
        return files, excluded
    budget = ScanBudget()
    if kind == 'skill':
        root = open_root(path)
        try:
            files, excluded = collect_bundle(root, budget)
            if 'SKILL.md' not in files:
                raise InventoryError('skill entry file is missing')
            return files, excluded
        finally:
            os.close(root)
    if kind != 'agent':
        raise InventoryError('unsupported package kind')
    file = pathlib.Path(os.path.abspath(os.path.expanduser(path)))
    checked_name(file.name)
    if sensitive_name(file.name):
        raise InventoryError('sensitive agent filename refused')
    root = open_root(str(file.parent))
    try:
        raw = read_regular(root, file.name, MAX_FILE)
        budget.check(entries=1, size=len(raw))
        return {file.name: raw}, []
    finally:
        os.close(root)


def load_security_module():
    # Execute only this trusted bundle's source, ignoring mutable bytecode caches.
    # Package input is never imported; default indexing must not write .pyc files.
    global _security_module
    if _security_module is None:
        source = pathlib.Path(__file__).with_name('ceo_security.py')
        spec = importlib.util.spec_from_file_location(
            'ceo_builtin_security', source)
        module = importlib.util.module_from_spec(spec)
        exec(compile(source.read_bytes(), str(source), 'exec'), module.__dict__)
        _security_module = module
    return _security_module


def security_report(files, kind, excluded):
    return load_security_module().analyze_bundle(files, kind=kind, excluded=excluded)


def alias_path(value):
    """Lexical absolute path; never resolve symlinks or accept ambiguous '..'."""
    path = pathlib.Path(os.path.expanduser(value))
    if not path.is_absolute() or len(str(path)) > 4096 or '..' in path.parts:
        raise InventoryError('alias paths must be bounded absolute paths without parent traversal')
    for part in path.parts[1:]:
        checked_name(part)
        if sensitive_name(part) or part.lower() in EXCLUDED_DIRS:
            raise InventoryError('excluded alias path refused')
    return path


def open_alias_target(path, kind, approved_roots):
    """Allow only package-root links, with real parents and an explicit root set.

    Returns an open target descriptor and a trace that can be revalidated after
    capture. Parent-directory links and nested package links remain forbidden.
    """
    if kind not in ('skill', 'agent') or not 1 <= len(approved_roots) <= 32:
        raise InventoryError('invalid alias scope')
    roots = tuple(alias_path(value) for value in approved_roots)
    root_trace = []
    for root in roots:
        fd = open_root(str(root))
        try:
            root_trace.append((str(root), signature(os.fstat(fd))))
        finally:
            os.close(fd)
    current = alias_path(path)
    visited, trace = set(), []
    for hop in range(17):
        if not any(current.is_relative_to(root) for root in roots):
            raise InventoryError('alias target is outside approved roots')
        if current in visited:
            raise InventoryError('alias cycle refused')
        visited.add(current)
        parent = open_root(str(current.parent))
        try:
            before = signature(os.fstat(parent))
            info = os.stat(current.name, dir_fd=parent, follow_symlinks=False)
            entry = signature(info)
            if stat.S_ISLNK(info.st_mode):
                if hop == 16:
                    raise InventoryError('alias hop limit exceeded')
                target = os.readlink(current.name, dir_fd=parent)
                if (entry != signature(os.stat(current.name, dir_fd=parent, follow_symlinks=False))
                        or before != signature(os.fstat(parent))):
                    raise InventoryError('alias changed during resolution')
                trace.append((str(current), before, entry, target))
                target_path = pathlib.Path(target)
                current = alias_path(str(target_path if target_path.is_absolute()
                                         else current.parent / target_path))
                continue
            if kind == 'skill':
                fd = open_dir(current.name, parent)
            else:
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_FILE:
                    raise InventoryError('unsupported agent target')
                # Keep the parent bound while read_regular opens the verified leaf.
                fd = os.dup(parent)
            try:
                bound = os.fstat(fd) if kind == 'skill' else os.stat(current.name, dir_fd=fd, follow_symlinks=False)
                if entry != signature(bound) or before != signature(os.fstat(parent)):
                    raise InventoryError('alias target changed during resolution')
                trace.append((str(current), before, entry, None))
                return fd, current, {'roots': root_trace, 'chain': trace}
            except BaseException:
                os.close(fd)
                raise
        finally:
            os.close(parent)
    raise InventoryError('alias resolution failed')


def capture_alias_package(path, kind, roots, budget):
    fd, target, trace = open_alias_target(path, kind, roots)
    try:
        if kind == 'skill':
            files, excluded = collect_bundle(fd, budget)
            if 'SKILL.md' not in files:
                raise InventoryError('skill entry file is missing')
        else:
            raw = read_regular(fd, target.name, MAX_FILE)
            budget.check(entries=1, size=len(raw))
            files, excluded = {target.name: raw}, []
        check, target_after, trace_after = open_alias_target(path, kind, roots)
        try:
            if target != target_after or trace != trace_after:
                raise InventoryError('alias binding changed during capture')
            # The exact descriptor used by collect_bundle is still the target.
            if kind == 'skill' and signature(os.fstat(fd)) != signature(os.fstat(check)):
                raise InventoryError('alias target changed during capture')
        finally:
            os.close(check)
        # Cache writes change the home directory's timestamps. Bind ancestor
        # identities in persistent evidence, while the full trace above checks
        # mutations during capture. Target/link signatures remain complete.
        persistent = {'roots': [(name, info[:3]) for name, info in trace['roots']],
                      'chain': [(name, parent[:3], entry, link)
                                for name, parent, entry, link in trace['chain']]}
        binding = hashlib.sha256(json.dumps(persistent, sort_keys=True).encode()).hexdigest()
        return files, excluded, {'target': str(target), 'binding_sha256': binding}
    finally:
        os.close(fd)


def toml_metadata(raw, filename):
    fallback = pathlib.PurePosixPath(filename).stem
    if len(fallback) > 128 or not NAME.fullmatch(fallback):
        fallback = 'file-' + hashlib.sha256(filename.encode()).hexdigest()[:16]
    name, permissions, issues = fallback, {}, []
    values = {}
    if tomllib is None:
        issues.append('toml-parser-unavailable')
    else:
        try:
            values = tomllib.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeError, RecursionError):
            issues.append('malformed-toml')
    candidate = values.get('name', fallback)
    if isinstance(candidate, str) and len(candidate) <= 128 and NAME.fullmatch(candidate):
        name = candidate
    else:
        issues.append('invalid-name')
    enums = {'sandbox_mode': {'read-only', 'workspace-write', 'danger-full-access'},
             'approval_policy': {'untrusted', 'on-failure', 'on-request', 'never'}}
    for key, allowed in enums.items():
        if key in values:
            value = values[key]
            if type(value) is str and value in allowed:
                permissions[key] = value
            else:
                issues.append('invalid-' + key.replace('_', '-'))
    if 'network_access' in values:
        if type(values['network_access']) is bool:
            permissions['network_access'] = values['network_access']
        else:
            issues.append('invalid-network-access')
    known = {'name', 'description', 'model', 'model_reasoning_effort', 'developer_instructions',
             'sandbox_mode', 'approval_policy', 'network_access'}
    if set(values) - known:
        issues.append('unsupported-configuration-fields')
    return {'id': f'agent:{name}', 'path': filename, 'sha256': hashlib.sha256(raw).hexdigest(),
            'declared_access': permissions.get('sandbox_mode'),
            'declared_permissions': permissions, 'configuration_issues': sorted(issues),
            'availability': 'present-unverified'}


def metadata(raw, kind, filename):
    if kind == 'agent' and filename.endswith('.toml'):
        return toml_metadata(raw, filename)
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise InventoryError(f"missing frontmatter: {filename}")
    values = {}
    for line in lines[1:]:
        if line == "---":
            break
        if not line.strip() or line.startswith("#") or line[0].isspace():
            continue
        match = re.fullmatch(r"([a-z][a-z0-9_-]*):\s*(.*)", line)
        if not match or match[1] in values:
            raise InventoryError(f"malformed or duplicate frontmatter key: {filename}")
        values[match[1]] = match[2].strip().strip('"\'')
    else:
        raise InventoryError(f"unterminated frontmatter: {filename}")
    name = values.get("name", "")
    if not NAME.fullmatch(name):
        raise InventoryError(f"invalid component name: {filename}")
    access = values.get("access")
    if kind == "agent" and access not in (None, "read-only", "workspace-write"):
        raise InventoryError(f"invalid declared access: {filename}")
    return {"id": f"{kind}:{name}", "path": filename,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "declared_access": access, "availability": "present-unverified"}


def scan(root, *, root_path=None, approved_alias_roots=()):
    entries, seen = [], set()
    targets = {}
    budget = ScanBudget()
    root_before = signature(os.fstat(root))
    alias_roots = ()
    if approved_alias_roots:
        if root_path is None:
            raise InventoryError('alias indexing requires an explicit home path')
        home = alias_path(root_path)
        alias_roots = tuple(dict.fromkeys([str(home), *approved_alias_roots]))
        check = open_root(str(home))
        try:
            if signature(os.fstat(check)) != root_before:
                raise InventoryError('inventory home binding changed')
        finally:
            os.close(check)

    for directory, kind in (("skills", "skill"), ("agents", "agent")):
        try:
            parent = open_dir(directory, root)
        except FileNotFoundError:
            continue
        try:
            parent_before = signature(os.fstat(parent))
            with os.scandir(parent) as iterator:
                children = []
                for child in iterator:
                    budget.check(entries=1)
                    children.append(child)
            for child in sorted(children, key=lambda entry: entry.name):
                checked_name(child.name)
                if child.name.startswith("."):
                    continue
                if sensitive_name(child.name) or child.name.lower() in EXCLUDED_DIRS:
                    raise InventoryError('sensitive inventory component refused')
                if child.is_symlink() and not alias_roots:
                    raise InventoryError(f"symlink component refused: {directory}/{child.name}")
                provenance = None
                if alias_roots:
                    if kind == 'agent' and not child.name.endswith(('.md', '.toml')):
                        continue
                    if kind == 'skill' and not child.is_symlink() and not child.is_dir(follow_symlinks=False):
                        continue
                    files, excluded, provenance = capture_alias_package(
                        str(home / directory / child.name), kind, alias_roots, budget)
                    target = pathlib.Path(provenance['target'])
                    entry_name = 'SKILL.md' if kind == 'skill' else target.name
                    if kind == 'agent' and not entry_name.endswith(('.md', '.toml')):
                        raise InventoryError('unsupported agent alias target')
                    raw = files[entry_name]
                    path = f'{directory}/{child.name}' + ('/SKILL.md' if kind == 'skill' else '')
                    # Parse by the canonical extension, never an alias disguise.
                    metadata_path = path if kind == 'skill' else f'agents/{target.name}'
                elif kind == "skill":
                    if not child.is_dir(follow_symlinks=False):
                        continue
                    skill_dir = open_dir(child.name, parent)
                    try:
                        files, excluded = collect_bundle(skill_dir, budget)
                        if 'SKILL.md' not in files:
                            raise InventoryError('skill entry file is missing')
                        raw = files['SKILL.md']
                    finally:
                        os.close(skill_dir)
                    path = f"skills/{child.name}/SKILL.md"
                else:
                    if not child.name.endswith((".md", ".toml")):
                        continue
                    raw = read_regular(parent, child.name, MAX_FILE)
                    budget.check(size=len(raw))
                    files, excluded = {child.name: raw}, []
                    path = f"agents/{child.name}"
                item = metadata(raw, kind, metadata_path if provenance else path)
                item['path'] = path
                # Cached findings are never reused: a writable cache is not
                # evidence that analysis ran, even with correct hash bindings.
                item['security'] = security_report(files, kind, excluded)
                budget.check()
                if provenance:
                    key = (kind, provenance['target'])
                    binding = {'path': path, **provenance}
                    if key in targets:
                        existing = targets[key]
                        if existing['id'] != item['id'] or existing['security'] != item['security']:
                            raise InventoryError('aliased package changed between captures')
                        existing['aliases'].append(path)
                        existing['alias_bindings'].append(binding)
                        continue
                    item['aliases'] = [path]
                    item['alias_bindings'] = [binding]
                    targets[key] = item
                if item["id"] in seen:
                    raise InventoryError(f"duplicate identity: {item['id']}")
                seen.add(item["id"])
                entries.append(item)
            if signature(os.fstat(parent)) != parent_before:
                raise InventoryError('inventory membership changed during scan')
        finally:
            os.close(parent)
    if signature(os.fstat(root)) != root_before:
        raise InventoryError('inventory root changed during scan')
    entries.sort(key=lambda x: x["id"])
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    return {"owner": OWNER, "schema_version": 2, "fingerprint": digest, "entries": entries}


def read_cache(root):
    try:
        data = json.loads(read_regular(root, CACHE, MAX_CACHE))
    except FileNotFoundError:
        return None
    if not isinstance(data, dict) or data.get("owner") != OWNER or type(data.get("schema_version")) is not int or data["schema_version"] not in (1, 2):
        raise InventoryError("existing cache is not an owned supported inventory")
    if (not isinstance(data.get('entries'), list) or len(data['entries']) > MAX_COUNT
            or any(not isinstance(item, dict) for item in data['entries'])
            or not isinstance(data.get('fingerprint'), str)
            or not re.fullmatch(r'[0-9a-f]{64}', data['fingerprint'])):
        raise InventoryError('existing inventory cache is malformed')
    return data


def refresh(root, document, previous):
    try:
        fcntl.flock(root, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise InventoryError("another inventory refresh is running") from exc
    try:
        _refresh_locked(root, document, previous)
    finally:
        fcntl.flock(root, fcntl.LOCK_UN)


def _refresh_locked(root, document, previous):
    payload = (json.dumps(document, indent=2) + "\n").encode()
    if len(payload) > MAX_CACHE:
        raise InventoryError("inventory cache limit exceeded")
    # All writes stay relative to the approved directory descriptor. Replacing
    # a name cannot follow a late symlink or modify its target.
    temporary = f".ceo-inventory-{uuid.uuid4().hex}.tmp"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=root)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if read_cache(root) != previous:
            raise InventoryError("cache changed during scan; retry after the other writer finishes")
        if previous is None:
            # A competing creator must never be overwritten on first refresh.
            os.link(temporary, CACHE, src_dir_fd=root, dst_dir_fd=root, follow_symlinks=False)
        else:
            os.replace(temporary, CACHE, src_dir_fd=root, dst_dir_fd=root)
    finally:
        try:
            os.unlink(temporary, dir_fd=root)
        except FileNotFoundError:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, help="Explicit approved root containing skills/ and agents/")
    parser.add_argument("--refresh", action="store_true", help="Refresh the separate owned inventory cache")
    parser.add_argument('--allow-alias-root', action='append', default=[],
                        help='Opt in to package-root aliases within home and these explicit real roots (repeatable)')
    args = parser.parse_args(argv)
    try:
        root = open_root(args.home)
        try:
            previous = read_cache(root)
            document = scan(root, root_path=args.home, approved_alias_roots=args.allow_alias_root)
            freshness = "missing" if previous is None else "fresh" if previous == document else "stale"
            if args.refresh:
                refresh(root, document, previous)
                freshness = "fresh"
            if any(item['security']['bundle_sha256'] is None for item in document['entries']):
                freshness = 'unverifiable'
            print(json.dumps({**document, "freshness": freshness}, indent=2))
        finally:
            os.close(root)
    except (OSError, ValueError, InventoryError) as exc:
        print(f"error: inventory unavailable; prior cache must be treated as stale: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Bounded Windows inventory capture on local fixed NTFS volumes.

Paths are lexical and all ancestors stay pinned without write/delete sharing.
No reparse points, hardlinks or alternate streams are admitted. Cache locking
coordinates cooperating refresh writers, not malicious same-user cache editors.
"""
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import ntpath
import os
import re
import uuid


class WindowsInventoryError(ValueError):
    pass


k32 = ctypes.WinDLL('kernel32', use_last_error=True) if os.name == 'nt' else None
INVALID = ctypes.c_void_p(-1).value
READ = 0x80000000
WRITE = 0x40000000
DELETE = 0x10000
SHARE_READ = 1
OPEN_EXISTING, OPEN_ALWAYS, CREATE_NEW = 3, 4, 1
DIRECTORY, REPARSE = 0x10, 0x400
FLAGS = 0x00200000 | 0x02000000  # OPEN_REPARSE_POINT | BACKUP_SEMANTICS


class Info(ctypes.Structure):
    _fields_ = [('attributes', w.DWORD), ('created', w.FILETIME),
                ('accessed', w.FILETIME), ('modified', w.FILETIME),
                ('volume', w.DWORD), ('size_high', w.DWORD), ('size_low', w.DWORD),
                ('links', w.DWORD), ('index_high', w.DWORD), ('index_low', w.DWORD)]


class Basic(ctypes.Structure):
    _fields_ = [('created', ctypes.c_longlong), ('accessed', ctypes.c_longlong),
                ('written', ctypes.c_longlong), ('changed', ctypes.c_longlong),
                ('attributes', w.DWORD)]


class Stream(ctypes.Structure):
    _fields_ = [('size', ctypes.c_longlong), ('name', w.WCHAR * 296)]


class Rename(ctypes.Structure):
    _fields_ = [('flags', w.DWORD), ('root', w.HANDLE), ('length', w.DWORD),
                ('name', w.WCHAR * 1)]


if k32 is not None:
    def bind(name, args, result):
        func = getattr(k32, name)
        func.argtypes, func.restype = args, result
        return func
    create = bind('CreateFileW', [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p,
                                  w.DWORD, w.DWORD, w.HANDLE], w.HANDLE)
    close = bind('CloseHandle', [w.HANDLE], w.BOOL)
    file_type = bind('GetFileType', [w.HANDLE], w.DWORD)
    get_info = bind('GetFileInformationByHandle', [w.HANDLE, ctypes.POINTER(Info)], w.BOOL)
    get_ex = bind('GetFileInformationByHandleEx', [w.HANDLE, ctypes.c_int,
                                                  ctypes.c_void_p, w.DWORD], w.BOOL)
    set_info = bind('SetFileInformationByHandle', [w.HANDLE, ctypes.c_int,
                                                  ctypes.c_void_p, w.DWORD], w.BOOL)
    read_file = bind('ReadFile', [w.HANDLE, ctypes.c_void_p, w.DWORD,
                                 ctypes.POINTER(w.DWORD), ctypes.c_void_p], w.BOOL)
    write_file = bind('WriteFile', [w.HANDLE, ctypes.c_void_p, w.DWORD,
                                   ctypes.POINTER(w.DWORD), ctypes.c_void_p], w.BOOL)
    flush = bind('FlushFileBuffers', [w.HANDLE], w.BOOL)
    drive_type = bind('GetDriveTypeW', [w.LPCWSTR], w.UINT)
    query_device = bind('QueryDosDeviceW', [w.LPCWSTR, w.LPWSTR, w.DWORD], w.DWORD)
    volume_info = bind('GetVolumeInformationByHandleW', [w.HANDLE, w.LPWSTR, w.DWORD,
                       ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD),
                       ctypes.POINTER(w.DWORD), w.LPWSTR, w.DWORD], w.BOOL)
    first_stream = bind('FindFirstStreamW', [w.LPCWSTR, ctypes.c_int,
                                            ctypes.POINTER(Stream), w.DWORD], w.HANDLE)
    next_stream = bind('FindNextStreamW', [w.HANDLE, ctypes.POINTER(Stream)], w.BOOL)
    find_close = bind('FindClose', [w.HANDLE], w.BOOL)


def check(ok):
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())


def checked_name(name):
    if (not name or name in ('.', '..') or name[-1] in ' .'
            or any(ord(c) < 32 or ord(c) == 127 or c in '<>:"/\\|?*' for c in name)
            or re.fullmatch(r'(CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?', name, re.I)):
        raise WindowsInventoryError('ambiguous or unsupported Windows filename')


def checked_path(value):
    value = os.fspath(value)
    if (not isinstance(value, str) or len(value) > 240
            or not re.match(r'^[A-Za-z]:\\', value) or '/' in value):
        raise WindowsInventoryError('Windows inventory requires a bounded absolute local drive path')
    tail = value[3:]
    if tail.endswith('\\'):
        tail = tail[:-1]
    parts = tail.split('\\') if tail else []
    for part in parts:
        checked_name(part)
    return value[:3] + '\\'.join(parts)


def no_streams(path):
    data = Stream()
    handle = first_stream(path, 0, ctypes.byref(data), 0)
    if handle == INVALID:
        if ctypes.get_last_error() == 38:  # no streams on a directory
            return
        check(False)
    try:
        while True:
            if data.name != '::$DATA':
                raise WindowsInventoryError('alternate data stream refused')
            if not next_stream(handle, ctypes.byref(data)):
                if ctypes.get_last_error() != 38:
                    check(False)
                break
    finally:
        find_close(handle)


class Node:
    def __init__(self, path, access=0x80, share=SHARE_READ, disposition=OPEN_EXISTING,
                 directory=None):
        self.path, self.handle = path, None
        handle = create(path, access | 0x80, share, None, disposition, FLAGS, None)
        if handle == INVALID:
            check(False)
        self.handle = handle
        try:
            if file_type(self.handle) != 1:
                raise WindowsInventoryError('non-disk resource refused')
            info = self.info()
            if info[0] & REPARSE or not info[0] & DIRECTORY and info[3] != 1:
                raise WindowsInventoryError('reparse point or multiply-linked resource refused')
            if directory is not None and bool(info[0] & DIRECTORY) != directory:
                raise WindowsInventoryError('unexpected Windows resource type')
            no_streams(path)
        except BaseException:
            if disposition == CREATE_NEW and access & DELETE:
                delete = w.BOOL(True)
                set_info(self.handle, 4, ctypes.byref(delete), ctypes.sizeof(delete))
            self.close()
            raise

    def info(self):
        value, basic = Info(), Basic()
        check(get_info(self.handle, ctypes.byref(value)))
        check(get_ex(self.handle, 0, ctypes.byref(basic), ctypes.sizeof(basic)))
        return (value.attributes, value.volume, (value.index_high << 32) | value.index_low,
                value.links, (value.size_high << 32) | value.size_low,
                basic.created, basic.written, basic.changed)

    def close(self):
        if self.handle is not None:
            close(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class PinnedRoot:
    def __init__(self, path):
        self.path, self.nodes = checked_path(path), []

    def __enter__(self):
        if k32 is None:
            raise WindowsInventoryError('native Windows APIs are unavailable')
        mapping = ctypes.create_unicode_buffer(4096)
        check(query_device(self.path[:2], mapping, len(mapping)))
        if not re.fullmatch(r'\\Device\\HarddiskVolume[0-9]+', mapping.value):
            raise WindowsInventoryError('mapped or substituted drives are unsupported')
        if drive_type(self.path[:3]) != 3:
            raise WindowsInventoryError('only local fixed NTFS drives are supported')
        try:
            # Freeze the validated device binding. Subsequent path operations
            # must not resolve a mutable DOS drive mapping again.
            current = '\\\\?\\GLOBALROOT' + mapping.value + '\\'
            self.nodes.append(Node(current, directory=True))
            filesystem = ctypes.create_unicode_buffer(64)
            check(volume_info(self.nodes[0].handle, None, 0, None, None, None, filesystem, 64))
            if filesystem.value != 'NTFS':
                raise WindowsInventoryError('only NTFS is supported')
            for part in self.path[3:].split('\\') if self.path[3:] else []:
                current = ntpath.join(current, part)
                self.nodes.append(Node(current, directory=True))
            return self.nodes[-1]
        except BaseException:
            self.__exit__()
            raise

    def __exit__(self, *args):
        for node in reversed(self.nodes):
            node.close()
        self.nodes = []


def open_child(parent, name, directory=None, *, content=False):
    checked_name(name)
    return Node(ntpath.join(parent.path, name), access=READ if content else 0x80,
                directory=directory)


def read_node(node, limit):
    before = node.info()
    if before[0] & DIRECTORY or before[4] > limit:
        raise WindowsInventoryError('nonregular or oversized file')
    pieces, total = [], 0
    while True:
        buffer = ctypes.create_string_buffer(min(65536, limit + 1 - total))
        count = w.DWORD()
        check(read_file(node.handle, buffer, len(buffer), ctypes.byref(count), None))
        if not count.value:
            break
        pieces.append(buffer.raw[:count.value])
        total += count.value
        if total > limit:
            raise WindowsInventoryError('oversized file')
    if node.info() != before:
        raise WindowsInventoryError('resource changed during read')
    return b''.join(pieces)


def read_regular(parent, name, limit):
    with open_child(parent, name, directory=False, content=True) as node:
        return read_node(node, limit)


def names(node, budget, *, charge=True):
    result = []
    with os.scandir(node.path) as items:
        for item in items:
            budget.check(entries=1 if charge else 0)
            if len(result) >= 1024:
                raise WindowsInventoryError('directory entry limit exceeded')
            checked_name(item.name)
            result.append(item.name)
    return sorted(result)


def collect_bundle(inv, root, budget):
    files, excluded, held, records = {}, [], [], []

    def walk(parent, prefix='', depth=0):
        budget.check()
        if depth > inv.MAX_DEPTH:
            raise WindowsInventoryError('package depth limit exceeded')
        before, children = parent.info(), names(parent, budget)
        records.append((parent, before, children))
        for name in children:
            relative = prefix + name
            node = open_child(parent, name)
            held.append(node)
            info = node.info()
            directory = bool(info[0] & DIRECTORY)
            reason = None
            if inv.sensitive_name(name) or directory and name.lower() in inv.EXCLUDED_DIRS:
                reason = ('excluded-resource' if name.lower() in
                          {'.git', '.venv', 'node_modules', '__pycache__'} else 'sensitive-resource')
            elif not directory and info[4] > inv.MAX_FILE:
                reason = 'oversized-resource'
            if reason:
                excluded.append({'path': relative, 'reason': reason})
                records.append((node, info, None))
            elif directory:
                walk(node, relative + '/', depth + 1)
            else:
                readable = open_child(parent, name, directory=False, content=True)
                held.append(readable)
                if readable.info() != info:
                    raise WindowsInventoryError('resource binding changed')
                raw = read_node(readable, inv.MAX_FILE)
                budget.check(size=len(raw))
                files[relative] = raw
                records.append((node, info, None))

    try:
        walk(root)
        for node, before, children in records:
            budget.check()
            if node.info() != before or children is not None and names(node, budget, charge=False) != children:
                raise WindowsInventoryError('package changed during capture')
            no_streams(node.path)
        return files, excluded
    finally:
        for node in reversed(held):
            node.close()


def snapshot_package(inv, path, kind='skill'):
    budget = inv.ScanBudget()
    path = checked_path(path)
    if kind == 'skill':
        with PinnedRoot(path) as root:
            files, excluded = collect_bundle(inv, root, budget)
            if 'SKILL.md' not in files:
                raise WindowsInventoryError('skill entry file is missing')
            return files, excluded
    if kind != 'agent':
        raise WindowsInventoryError('unsupported package kind')
    parent, name = ntpath.split(path)
    if inv.sensitive_name(name):
        raise WindowsInventoryError('sensitive agent filename refused')
    with PinnedRoot(parent) as root:
        raw = read_regular(root, name, inv.MAX_FILE)
        budget.check(entries=1, size=len(raw))
        return {name: raw}, []


def scan(inv, root):
    entries, seen, budget = [], set(), inv.ScanBudget()
    root_before = root.info()
    for directory, kind in (('skills', 'skill'), ('agents', 'agent')):
        try:
            parent = open_child(root, directory, directory=True)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 2:
                continue
            raise
        with parent:
            before, children = parent.info(), names(parent, budget)
            for name in children:
                if name.startswith('.'):
                    continue
                if inv.sensitive_name(name) or name.lower() in inv.EXCLUDED_DIRS:
                    raise WindowsInventoryError('sensitive inventory component refused')
                with open_child(parent, name) as child:
                    if kind == 'skill':
                        if not child.info()[0] & DIRECTORY:
                            continue
                        files, excluded = collect_bundle(inv, child, budget)
                        if 'SKILL.md' not in files:
                            raise WindowsInventoryError('skill entry file is missing')
                        raw, path = files['SKILL.md'], f'skills/{name}/SKILL.md'
                    else:
                        if not name.endswith(('.md', '.toml')):
                            continue
                        raw = read_regular(parent, name, inv.MAX_FILE)
                        budget.check(size=len(raw))
                        files, excluded, path = {name: raw}, [], f'agents/{name}'
                    item = inv.metadata(raw, kind, path)
                    item['security'] = inv.security_report(files, kind, excluded)
                    budget.check()
                    if item['id'] in seen:
                        raise WindowsInventoryError('duplicate inventory identity')
                    seen.add(item['id'])
                    entries.append(item)
            if parent.info() != before or names(parent, budget, charge=False) != children:
                raise WindowsInventoryError('inventory membership changed')
    if root.info() != root_before:
        raise WindowsInventoryError('inventory root changed')
    entries.sort(key=lambda item: item['id'])
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    return {'owner': inv.OWNER, 'schema_version': 2, 'fingerprint': digest, 'entries': entries}


def read_cache(inv, root):
    try:
        data = json.loads(read_regular(root, inv.CACHE, inv.MAX_CACHE))
    except OSError as exc:
        if getattr(exc, 'winerror', None) == 2:
            return None
        raise
    if (not isinstance(data, dict) or data.get('owner') != inv.OWNER
            or type(data.get('schema_version')) is not int or data['schema_version'] not in (1, 2)
            or not isinstance(data.get('entries'), list) or len(data['entries']) > inv.MAX_COUNT
            or any(not isinstance(item, dict) for item in data['entries'])
            or not isinstance(data.get('fingerprint'), str)
            or not re.fullmatch('[0-9a-f]{64}', data['fingerprint'])):
        raise WindowsInventoryError('existing cache is not an owned supported inventory')
    return data


def acquire_lock(root):
    node = Node(ntpath.join(root.path, '.ceo-inventory.lock'),
                access=READ, share=0, disposition=OPEN_ALWAYS, directory=False)
    if node.info()[4] != 0:
        node.close()
        raise WindowsInventoryError('existing lock contains foreign data')
    return node


def publish(inv, root, document, previous):
    payload = (json.dumps(document, indent=2) + '\n').encode()
    if len(payload) > inv.MAX_CACHE:
        raise WindowsInventoryError('inventory cache limit exceeded')
    name = '.ceo-inventory-' + uuid.uuid4().hex + '.tmp'
    node = Node(ntpath.join(root.path, name), access=WRITE | DELETE,
                share=0, disposition=CREATE_NEW, directory=False)
    published = False
    try:
        count = w.DWORD()
        check(write_file(node.handle, payload, len(payload), ctypes.byref(count), None))
        if count.value != len(payload):
            raise WindowsInventoryError('incomplete cache write')
        check(flush(node.handle))
        if read_cache(inv, root) != previous:
            raise WindowsInventoryError('cache changed during scan')
        # Cooperating writers hold the lock. This is not a compare-and-swap
        # against an unrelated same-user writer. Rename replaces the entry,
        # never follows its target, and the source remains bound to this handle.
        encoded = inv.CACHE.encode('utf-16-le')
        buffer = ctypes.create_string_buffer(Rename.name.offset + len(encoded))
        header = ctypes.cast(buffer, ctypes.POINTER(Rename)).contents
        header.flags, header.root, header.length = int(previous is not None), root.handle, len(encoded)
        ctypes.memmove(ctypes.addressof(buffer) + Rename.name.offset, encoded, len(encoded))
        check(set_info(node.handle, 3, buffer, len(buffer)))
        published = True
    finally:
        if not published:
            delete = w.BOOL(True)
            # Delete this exact temporary handle, not a potentially replaced path.
            try:
                check(set_info(node.handle, 4, ctypes.byref(delete), ctypes.sizeof(delete)))
            finally:
                node.close()
        else:
            node.close()


def run(inv, args):
    if args.allow_alias_root:
        raise WindowsInventoryError('Windows alias-root scanning is not supported')
    with PinnedRoot(args.home) as root:
        lock = acquire_lock(root) if args.refresh else None
        try:
            previous = read_cache(inv, root)
            document = scan(inv, root)
            freshness = 'missing' if previous is None else 'fresh' if previous == document else 'stale'
            if args.refresh:
                publish(inv, root, document, previous)
                freshness = 'fresh'
            if any(item['security']['bundle_sha256'] is None for item in document['entries']):
                freshness = 'unverifiable'
            print(json.dumps({**document, 'freshness': freshness}, indent=2))
        finally:
            if lock is not None:
                lock.close()
    return 0

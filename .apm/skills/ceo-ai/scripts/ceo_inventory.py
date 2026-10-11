#!/usr/bin/env python3
"""Inspect approved skill/agent metadata; refresh a separate cache on request.

No discovered code is executed. The descriptor-based scanner requires POSIX
no-follow operations. Other hosts should use their native read-only inventory.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import time
import uuid

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
NAME = re.compile(r"[a-z0-9][a-z0-9-]*\Z")


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
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise InventoryError(f"nonregular or oversized file: {name}")
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
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise InventoryError(f"file changed during scan: {name}")
        return b"".join(chunks)
    finally:
        os.close(fd)


def metadata(raw, kind, filename):
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


def scan(root):
    start = time.monotonic()
    entries, seen = [], set()
    count = total = 0

    def budget():
        nonlocal count
        count += 1
        if count > MAX_COUNT or time.monotonic() - start > 5 or total > MAX_TOTAL:
            raise InventoryError("inventory scan limit exceeded")

    for directory, kind in (("skills", "skill"), ("agents", "agent")):
        try:
            parent = open_dir(directory, root)
        except FileNotFoundError:
            continue
        try:
            with os.scandir(parent) as children:
                for child in children:
                    budget()
                    if child.name.startswith("."):
                        continue
                    if child.is_symlink():
                        raise InventoryError(f"symlink component refused: {directory}/{child.name}")
                    if kind == "skill":
                        if not child.is_dir(follow_symlinks=False):
                            continue
                        skill_dir = open_dir(child.name, parent)
                        try:
                            raw = read_regular(skill_dir, "SKILL.md", MAX_FILE)
                        finally:
                            os.close(skill_dir)
                        path = f"skills/{child.name}/SKILL.md"
                    else:
                        if not child.name.endswith(".md"):
                            continue
                        raw = read_regular(parent, child.name, MAX_FILE)
                        path = f"agents/{child.name}"
                    total += len(raw)
                    budget()
                    item = metadata(raw, kind, path)
                    if item["id"] in seen:
                        raise InventoryError(f"duplicate identity: {item['id']}")
                    seen.add(item["id"])
                    entries.append(item)
        finally:
            os.close(parent)
    entries.sort(key=lambda x: x["id"])
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    return {"owner": OWNER, "schema_version": 1, "fingerprint": digest, "entries": entries}


def read_cache(root):
    try:
        data = json.loads(read_regular(root, CACHE, MAX_CACHE))
    except FileNotFoundError:
        return None
    if not isinstance(data, dict) or data.get("owner") != OWNER or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise InventoryError("existing cache is not an owned supported inventory")
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
    args = parser.parse_args(argv)
    try:
        root = open_root(args.home)
        try:
            previous = read_cache(root)
            document = scan(root)
            freshness = "missing" if previous is None else "fresh" if previous == document else "stale"
            if args.refresh:
                refresh(root, document, previous)
                freshness = "fresh"
            print(json.dumps({**document, "freshness": freshness}, indent=2))
        finally:
            os.close(root)
    except (OSError, ValueError, InventoryError) as exc:
        print(f"error: inventory unavailable; prior cache must be treated as stale: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

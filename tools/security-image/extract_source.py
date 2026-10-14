"""Extract a bounded allowlist from the pinned upstream archive; never execute it."""
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

PREFIX = 'SkillSpector-c7958a3268d9498644b22edb75d0f051bbc8cbfc'
SOURCE_SHA256 = 'ea6f4e5d40d9ba0d73a801515772962f1c7cc8ab8932a4de41a573b46411070d'
MAX_FILE = 8 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024
MAX_ARCHIVE = 4 * 1024 * 1024
MAX_MEMBERS = 20000


class BoundedReader:
    def __init__(self, source):
        self.source = source
        self.count = 0

    def read(self, size):
        data = self.source.read(min(size, MAX_EXPANDED - self.count + 1))
        self.count += len(data)
        if self.count > MAX_EXPANDED:
            raise ValueError('expanded archive exceeds limit')
        return data


def extract(archive, destination, expected=SOURCE_SHA256):
    archive, destination = Path(archive), Path(destination)
    if os.path.lexists(destination):
        raise ValueError('destination must not exist')
    with archive.open('rb') as handle:
        compressed = handle.read(MAX_ARCHIVE + 1)
    if len(compressed) > MAX_ARCHIVE or hashlib.sha256(compressed).hexdigest() != expected:
        raise ValueError('archive size or hash mismatch')
    import io
    selected, seen, parents = {}, {}, set()
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as gz:
        bounded = BoundedReader(gz)
        with tarfile.open(fileobj=bounded, mode='r|') as tar:
            for count, member in enumerate(tar, 1):
                name = member.name.rstrip('/') if member.isdir() else member.name
                parts = name.split('/')
                if (count > MAX_MEMBERS or len(name) > 1024 or
                    any(part in ('', '.', '..') for part in parts) or
                    parts[0] != PREFIX or '\\' in name or
                    any(ord(c) < 32 or ord(c) == 127 for c in name) or
                    not (member.isfile() or member.isdir()) or member.sparse is not None or
                    member.size < 0 or member.size > MAX_FILE or
                    name in seen or (member.isfile() and name in parents)):
                    raise ValueError('unsafe archive member')
                ancestors = ['/'.join(parts[:i]) for i in range(1, len(parts))]
                if any(parent in seen and seen[parent] == 'file' for parent in ancestors):
                    raise ValueError('archive file/directory collision')
                # Track explicit entries independently of implied parent directories.
                seen[name] = 'file' if member.isfile() else 'dir'
                parents.update(ancestors)
                relative = '/'.join(parts[1:])
                allowed = relative.startswith('src/') or relative in ('pyproject.toml', 'README.md', 'LICENSE', 'LICENSE.txt')
                if member.isfile() and allowed:
                    selected[relative] = tar.extractfile(member).read(MAX_FILE + 1)
                    if len(selected[relative]) != member.size:
                        raise ValueError('truncated archive member')
        # Tar EOF is not gzip EOF: count trailing data too, including compression bombs.
        while bounded.read(65536):
            pass
    stage = Path(tempfile.mkdtemp(prefix='.source-', dir=destination.parent))
    try:
        for relative, content in selected.items():
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(content)
        if os.path.lexists(destination):
            raise ValueError('destination appeared during extraction')
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: extract_source.py ARCHIVE NEW_DESTINATION')
    extract(sys.argv[1], sys.argv[2])

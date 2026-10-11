#!/usr/bin/env python3
"""Check local Markdown links and heading fragments. Never fetch remote URLs."""
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {'.git', '.venv', 'node_modules', '__pycache__'}


def read_local(root, path):
    path = Path(os.path.abspath(path))
    path.relative_to(root)  # Reject paths outside the checkout before reading.
    for item in [*reversed(path.parents), path]:
        if item == root or root in item.parents:
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('symlink or reparse point')
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 512 * 1024:
        raise ValueError('expected a regular file no larger than 512 KiB')
    return path.read_text(encoding='utf-8')


def prose(text):
    """Drop fenced examples while preserving line numbers for diagnostics."""
    fence = None
    for line in text.splitlines():
        match = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            yield ''
        else:
            yield line if fence is None else ''


def headings(text):
    used, result = {}, set()
    for line in prose(text):
        match = re.match(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$', line)
        if not match:
            continue
        title = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', match.group(1))
        slug = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
        candidate = slug
        number = used.get(slug, 0)
        while candidate in result:
            number += 1
            candidate = f'{slug}-{number}'
        used[slug] = number
        result.add(candidate)
    return result


def links(text):
    """Read inline links/images and reference destinations in this repo's style."""
    for number, line in enumerate(prose(text), 1):
        line = re.sub(r'`+[^`]*`+', '', line)
        for match in re.finditer(r'!?\[[^\]]*\]\(([^)]*)\)', line):
            yield number, match.group(1).strip()
        definition = re.match(r'^\s{0,3}\[[^\]]+\]:\s*(.*)$', line)
        if definition:
            yield number, definition.group(1).strip()


def check(root):
    root = Path(root).absolute()
    errors, documents, external = [], [], 0
    for parent, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(d for d in directories if d not in IGNORED)
        for directory in directories[:]:
            if (Path(parent) / directory).is_symlink():
                errors.append(f'{Path(parent) / directory}: symlink directory is not checked')
                directories.remove(directory)
        documents.extend(Path(parent) / name for name in sorted(names) if name.endswith('.md'))
    if len(documents) > 1024:
        return ['Too many Markdown documents'], 0, 0
    for doc in documents:
        try:
            text = read_local(root, doc)
        except (OSError, ValueError, UnicodeError) as exc:
            errors.append(f'{doc.relative_to(root)}: {exc}')
            continue
        for line, destination in links(text):
            try:
                if destination.startswith('<'):
                    match = re.fullmatch(r'<([^>]+)>(?:\s+"[^"]*")?', destination)
                else:
                    match = re.fullmatch(r'([^\s]+?)(?:\s+"[^"]*")?', destination)
                if not match:
                    raise ValueError('malformed link destination')
                url = urlsplit(match.group(1))
                if url.scheme in {'https', 'http', 'mailto'}:
                    external += 1
                    continue
                if url.scheme or url.netloc or url.query:
                    raise ValueError('unsupported local link')
                name = unquote(url.path)
                if name.startswith(('/', '\\')) or '\\' in name or '\x00' in name:
                    raise ValueError('absolute or nonportable path')
                target = doc.parent / name if name else doc
                target_text = read_local(root, target)
                if url.fragment and (target.suffix != '.md' or unquote(url.fragment) not in headings(target_text)):
                    raise ValueError('heading fragment not found')
            except (OSError, ValueError, UnicodeError) as exc:
                errors.append(f'{doc.relative_to(root)}:{line}: {destination}: {exc}')
    return errors, len(documents), external


def main():
    errors, count, external = check(ROOT)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Docs passed: {count} Markdown files; {external} external links not fetched.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

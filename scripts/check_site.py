#!/usr/bin/env python3
"""Validate the exact static publication tree without fetching any URL."""
import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FILES = {'.nojekyll', 'index.html', 'ru/index.html', 'zh/index.html',
         'assets/style.css', 'assets/site.js', 'assets/icon.svg', 'assets/core.svg',
         'assets/fonts/GolosText.ttf', 'assets/fonts/OFL.txt'}
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
FONT_HASHES = {
    'assets/fonts/GolosText.ttf': '17bb58fb69aec2dfb047a2ebf52534023e9b688c97a6b7ac795b0a72912c2063',
    'assets/fonts/OFL.txt': 'ff532f9e8789f09a9fdffc3c0954eedfb0a48be77b2e2eb90f5f82e4f347f50c',
}


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.ids = set()
        self.duplicates = set()
        self.script_text = False
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if attrs.get('id'):
            if attrs['id'] in self.ids:
                self.duplicates.add(attrs['id'])
            self.ids.add(attrs['id'])
        self.in_script = tag == 'script' or self.in_script

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False

    def handle_data(self, data):
        if self.in_script and data.strip():
            self.script_text = True


def check(root):
    root = Path(root).absolute()
    errors, contents, documents = [], {}, {}
    if root.is_symlink() or not root.is_dir():
        return ['site root must be a real directory']
    total = 0
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs[:]:
            path = Path(parent) / name
            if path.is_symlink() or name.startswith('.'):
                errors.append(f'{path.relative_to(root)}: forbidden directory or symlink')
                dirs.remove(name)
        for name in files:
            path = Path(parent) / name
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                errors.append(f'{relative}: not a regular file (symlinks forbidden)')
                continue
            if relative not in FILES:
                errors.append(f'{relative}: unexpected publication file')
                continue
            total += info.st_size
            if info.st_size > 1024 * 1024:
                errors.append(f'{relative}: file exceeds 1 MiB')
                continue
            contents[relative] = path.read_bytes()
    if total > 2 * 1024 * 1024:
        errors.append('site exceeds 2 MiB')
    for name in sorted(FILES - contents.keys()):
        errors.append(f'{name}: missing required file')
    for name, raw in contents.items():
        if name.endswith(('.html', '.svg')):
            doc = Document()
            doc.feed(raw.decode('utf-8'))
            documents[name] = doc
            if doc.duplicates or doc.script_text:
                errors.append(f'{name}: duplicate IDs or inline script')

    def reference(source, value, resource=False):
        try:
            url = urlsplit(value)
            if url.scheme or url.netloc:
                if resource:
                    raise ValueError('external resource')
                approved_contact = value in {'https://t.me/bearatol', 'https://www.linkedin.com/in/mikhail-diesperov/'}
                if not approved_contact and (url.scheme != 'https' or url.hostname not in {'github.com', 'bearatol.github.io'}):
                    raise ValueError('unexpected navigation destination')
                return
            path = unquote(url.path)
            if path.startswith(('/', '\\')) or '\\' in path or '\x00' in path or url.query:
                raise ValueError('nonportable local path')
            target = Path(os.path.abspath(root / Path(source).parent / path)) if path else root / source
            try:
                relative = target.relative_to(root).as_posix()
            except ValueError:
                raise ValueError('outside site') from None
            if relative == '.' or path.endswith('/'):
                relative = (Path(relative) / 'index.html').as_posix()
            if relative not in contents:
                raise ValueError('missing or forbidden local target')
            if url.fragment and unquote(url.fragment) not in documents.get(relative, Document()).ids:
                raise ValueError('missing fragment')
        except ValueError as exc:
            errors.append(f'{source}: {value}: {exc}')

    for name, doc in documents.items():
        csp_seen = False
        for tag, attrs in doc.tags:
            if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'content-security-policy':
                csp_seen = attrs.get('content') == CSP
            if tag in {'style', 'iframe', 'object', 'embed', 'form', 'base', 'foreignobject'}:
                errors.append(f'{name}: forbidden element {tag}')
            if any(a.startswith('on') or a in {'style', 'srcdoc'} for a in attrs):
                errors.append(f'{name}: inline execution or styling')
            if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh':
                errors.append(f'{name}: meta refresh forbidden')
            if tag == 'script' and (attrs.get('src') is None or name.endswith('.svg')):
                errors.append(f'{name}: forbidden script')
            for attr in ('src', 'poster', 'data', 'xlink:href'):
                if attrs.get(attr):
                    reference(name, attrs[attr], True)
                    if name.endswith('.html') and not csp_seen:
                        errors.append(f'{name}: resource precedes CSP')
            if attrs.get('srcset'):
                # This site has no responsive image sets. Fail closed rather than parse an ambiguous grammar.
                errors.append(f'{name}: srcset is not permitted')
            if attrs.get('href'):
                runtime = tag not in {'a', 'link'} or (tag == 'link' and attrs.get('rel') not in {'canonical', 'alternate'})
                reference(name, attrs['href'], runtime)
                if runtime and name.endswith('.html') and not csp_seen:
                    errors.append(f'{name}: resource precedes CSP')
        if name.endswith('.html') and not csp_seen:
            errors.append(f'{name}: required CSP missing')
    for name, raw in contents.items():
        if name.endswith('.css'):
            css = raw.decode('utf-8')
            if '@import' in css.lower() or '\\' in css or '/*' in css:
                errors.append(f'{name}: imports, escapes or comments are outside the audited CSS subset')
            for match in re.finditer(r'url\(\s*[\'\"]?([^\)\'\"]+)[\'\"]?\s*\)', css, re.I):
                reference(name, match.group(1).strip(), True)
    for name, expected in FONT_HASHES.items():
        if name in contents and hashlib.sha256(contents[name]).hexdigest() != expected:
            errors.append(f'{name}: licensed upstream asset hash changed')
    for name, lang, scope in [('index.html', 'en', 'this project'), ('ru/index.html', 'ru', 'этот проект'), ('zh/index.html', 'zh-CN', '当前项目')]:
        if name not in documents:
            continue
        doc, raw = documents[name], contents[name].decode('utf-8')
        if ('html', {'lang': lang}) not in doc.tags:
            errors.append(f'{name}: incorrect document language')
        templates = [a.get('data-template', '') for _, a in doc.tags if 'data-template' in a]
        if len(templates) != 1 or any(term not in templates[0] for term in (scope, '{host}')):
            errors.append(f'{name}: installation scope missing')
        if 'https://github.com/bearatol/ceo-ai/blob/v0.4.0/INSTALL.md' not in raw:
            errors.append(f'{name}: pinned installation URL missing')
        if {a.get('value') for t, a in doc.tags if t == 'input'} != {'Codex', 'Claude Code', 'Cursor'}:
            errors.append(f'{name}: unexpected tool choices')
    return errors


if __name__ == '__main__':
    problems = check(ROOT / 'site')
    if problems:
        print('\n'.join(problems), file=sys.stderr)
        raise SystemExit(1)
    print('Site passed: exact publication tree, local resources, links, fonts and installation prompts.')

#!/usr/bin/env python3
"""Local, opt-in CEO AI memory. No network, imports of user code, or background work.

The caller owns human consent and host permissions. SQLite serializes cooperating
writers; this is not a sandbox against a hostile local process or a lying agent.
"""
import argparse
from contextlib import closing
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import uuid

APP_ID = 0x43454F41
MAX_RECORD = 16384
MAX_RECORDS = 200
TABLES = (
    'CREATE TABLE consent (scope TEXT PRIMARY KEY, enabled INTEGER NOT NULL, updated TEXT NOT NULL)',
    'CREATE TABLE records (scope TEXT NOT NULL, id TEXT NOT NULL, revision TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(scope,id))',
)
ACTIONS = {'status', 'enable', 'disable', 'recall', 'show', 'save', 'delete', 'clear'}


class MemoryRefusal(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise MemoryRefusal(message)


def checked_path(value):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts, 'An absolute local path without traversal is required')
    if os.name == 'nt':
        require(re.fullmatch(r'[A-Za-z]:', path.drive), 'Use a local drive, not a network or device path')
        for part in path.parts[1:]:
            require(not re.search(r'[<>:"|?*]', part) and not part.endswith((' ', '.')),
                    'Unsupported Windows path')
    for item in [*reversed(path.parents), path]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'Symlinks and reparse points are not supported')
        require(stat.S_ISDIR(info.st_mode) if item != path else
                stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'Special files are not supported')
    return path


def location(root, project):
    root = checked_path(root)
    project = Path(project).resolve(strict=True)
    require(project.is_dir(), 'Project must be an existing directory')
    package = Path(__file__).resolve().parents[1]
    require(root != project and project not in root.parents and root != package and package not in root.parents,
            'Memory must stay outside the project and installed package')
    require(not {'.git', '.apm', '.codex', '.claude', '.cursor', '.agents'} & set(root.parts),
            'Memory must stay outside repository metadata and application caches')
    require(not any((part / '.git').exists() for part in [root, *root.parents]),
            'Memory must stay outside Git repositories')
    if root.exists():
        require(root.is_dir(), 'Memory root is not a directory')
        require(set(p.name for p in root.iterdir()) <= {'memory.sqlite3', 'memory.sqlite3-journal'},
                'Foreign files in memory root; nothing changed')
        for path in root.iterdir():
            checked_path(path)
            info = path.stat()
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 16*1024*1024,
                    'Memory file is linked, nonregular, or oversized')
            if os.name == 'posix':
                require(info.st_uid == os.getuid() and not info.st_mode & 0o077,
                        'Memory file must be owned by this user and private (0600)')
        if os.name == 'posix':
            info = root.stat()
            require(info.st_uid == os.getuid() and not info.st_mode & 0o077,
                    'Memory directory must be owned by this user and private (0700)')
    return root, project


def validate(record, scope):
    require(isinstance(record, dict), 'Record must be an object')
    fields = {'id', 'kind', 'title', 'summary', 'applies_when', 'avoid_when', 'evidence',
              'source', 'verified_on', 'review_after', 'tags'}
    require(fields <= record.keys() and record.keys() <= fields | {'pattern'}, 'Unknown or missing record fields')
    require(isinstance(record['id'], str) and re.fullmatch(r'[a-z][a-z0-9-]{0,63}', record['id']), 'Invalid record id')
    require(record['kind'] in ({'preference', 'pattern'} if scope == 'user' else {'lesson', 'pattern'}),
            'Record kind is not allowed in this scope')
    for key in fields - {'tags', 'id', 'kind'}:
        require(isinstance(record[key], str) and 0 < len(record[key]) <= (120 if key == 'title' else 1200),
                'Invalid or oversized record field: ' + key)
    verified, review = date.fromisoformat(record['verified_on']), date.fromisoformat(record['review_after'])
    require(verified.isoformat() == record['verified_on'] and review.isoformat() == record['review_after'] and
            verified <= date.today() and review >= verified, 'Invalid verification or review date')
    require(isinstance(record['tags'], list) and 1 <= len(record['tags']) <= 8 and
            all(isinstance(t, str) and re.fullmatch(r'[a-z0-9-]{1,40}', t) for t in record['tags']), 'Invalid tags')
    if record['kind'] == 'pattern':
        pattern = record.get('pattern')
        require(isinstance(pattern, dict) and set(pattern) == {'tokens', 'components', 'responsive', 'accessibility', 'example'},
                'Pattern requires tokens, components, responsive, accessibility, and example')
        require(isinstance(pattern['tokens'], dict), 'Design tokens must be a JSON object')
        for key in ('components', 'responsive', 'accessibility', 'example'):
            require(isinstance(pattern[key], str) and 0 < len(pattern[key]) <= 2000, 'Invalid pattern detail')
    else:
        require('pattern' not in record, 'Pattern details require pattern kind')
    encoded = json.dumps(record, ensure_ascii=False, allow_nan=False)
    require(len(encoded.encode()) <= MAX_RECORD, 'Record exceeds size limit')
    # Defense in depth, not a complete secret detector. The caller must redact first.
    require(not re.search(r'https?://[^\s/]+@|-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:sk-|ghp_)[A-Za-z0-9_-]{16,}|[?&](?:token|key|password|secret)=', encoded, re.I),
            'Credential-like content is not allowed')
    return encoded


def connect(root, create):
    path = root / 'memory.sqlite3'
    journal = root / 'memory.sqlite3-journal'
    if journal.exists():
        require(path.exists(), 'Orphan journal; preserve the folder and review it before enabling memory')
        with journal.open('rb') as stream:
            signature = stream.read(8)
        require(signature == bytes.fromhex('d9d505f920a163d7') and journal.stat().st_size >= 512,
                'Unrecognized or active journal; preserve it and wait for the writer or request recovery review')
    if not path.exists():
        require(create, 'Memory store is missing')
        root.mkdir(mode=0o700, parents=False, exist_ok=True)
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        db = sqlite3.connect(path, timeout=0.5)
        try:
            with db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('PRAGMA application_id=' + str(APP_ID))
                db.execute('PRAGMA user_version=1')
                for sql in TABLES: db.execute(sql)
        except BaseException:
            db.close()
            raise
    else:
        # Inspect immutable schema pages without recovering an unknown database.
        # Our transactions never alter the schema. Only an owned database with a
        # recognized rollback journal may proceed to SQLite's writable recovery.
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True, timeout=0.5)) as probe:
            require(probe.execute('PRAGMA application_id').fetchone()[0] == APP_ID and
                    probe.execute('PRAGMA user_version').fetchone()[0] == 1, 'Unknown memory store')
            schema = {row[0] for row in probe.execute('SELECT sql FROM sqlite_master WHERE sql IS NOT NULL')}
            require(schema == set(TABLES), 'Unexpected memory schema')
        db = sqlite3.connect(path, timeout=0.5)
    try:
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('PRAGMA secure_delete=ON')
        require(db.execute('PRAGMA journal_mode').fetchone()[0] == 'delete', 'Unsupported memory journal mode')
        return db
    except BaseException:
        db.close()
        raise


def perform(root, project, scope, action, *, consent=False, manage=False, record=None,
            identity=None, revision=None, query=''):
    require(scope in {'project', 'user'} and action in ACTIONS, 'Unknown scope or action')
    require(isinstance(query, str) and len(query) <= 200, 'Query exceeds size limit')
    require(action not in {'show', 'delete', 'clear'} or manage, 'Explicit memory management request required')
    require(action != 'enable' or consent, 'Explicit scope consent required')
    root, project = location(root, project)
    namespace = 'user' if scope == 'user' else 'project:' + hashlib.sha256(os.path.normcase(str(project)).encode()).hexdigest()
    result = dict(scope=scope, namespace=namespace, location=str(root), enabled=False, records=[])
    if not (root / 'memory.sqlite3').exists() and action != 'enable':
        require(action != 'save', 'Memory is disabled')
        return dict(result, event='disabled' if action == 'disable' else 'empty')
    db = connect(root, action == 'enable')
    try:
        # Read consent and write under the same lock; disable cannot race a save.
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT enabled FROM consent WHERE scope=?', (namespace,)).fetchone()
        enabled = bool(row and row[0])
        result['enabled'] = enabled
        if action in {'enable', 'disable', 'clear'}:
            enabled = action == 'enable'
            require(db.execute('SELECT count(*) FROM consent').fetchone()[0] < 100 or row,
                    'Scope limit reached; manage existing memory before adding scopes')
            db.execute('INSERT OR REPLACE INTO consent VALUES(?,?,?)',
                       (namespace, int(enabled), datetime.now(timezone.utc).isoformat()))
            if action == 'clear': db.execute('DELETE FROM records WHERE scope=?', (namespace,))
            result.update(enabled=enabled, event={'enable':'enabled', 'disable':'disabled', 'clear':'cleared'}[action])
        elif action == 'save':
            require(enabled, 'Memory is disabled')
            encoded = validate(record, scope)
            old = db.execute('SELECT revision FROM records WHERE scope=? AND id=?', (namespace, record['id'])).fetchone()
            require((old is None and revision is None) or (old and old[0] == revision), 'Revision conflict; reread before editing')
            require(old or db.execute('SELECT count(*) FROM records').fetchone()[0] < 800,
                    'Store limit reached; curate existing memory')
            count = db.execute('SELECT count(*) FROM records WHERE scope=?', (namespace,)).fetchone()[0]
            require(old or count < MAX_RECORDS, 'Record limit reached; curate existing memory')
            rev = uuid.uuid4().hex
            db.execute('INSERT OR REPLACE INTO records VALUES(?,?,?,?)', (namespace, record['id'], rev, encoded))
            result.update(event='saved', id=record['id'], title=record['title'], revision=rev)
        elif action == 'delete':
            require(isinstance(identity, str) and revision is not None, 'Deletion requires id and revision')
            changed = db.execute('DELETE FROM records WHERE scope=? AND id=? AND revision=?', (namespace, identity, revision)).rowcount
            require(changed == 1, 'Revision conflict or record missing')
            result.update(event='deleted', id=identity)
        elif action == 'show' or (action == 'recall' and enabled):
            require(action == 'show' or query.strip(), 'Recall requires a focused query')
            rows = db.execute('SELECT revision,data FROM records WHERE scope=? ORDER BY id LIMIT ?', (namespace, MAX_RECORDS+1)).fetchall()
            require(len(rows) <= MAX_RECORDS, 'Record limit exceeded')
            for rev, data in rows:
                require(len(data.encode()) <= MAX_RECORD, 'Oversized stored record')
                item = json.loads(data); validate(item, scope)
                if action == 'recall' and (item['review_after'] < date.today().isoformat() or
                    not any(term.casefold() in data.casefold() for term in query.split())): continue
                result['records'].append(dict(revision=rev, record=item))
                if action == 'recall' and len(result['records']) == 5: break
        db.commit()
        return result
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='Explicitly approved private directory outside repositories')
    parser.add_argument('--project', required=True, help='Current project, used only for scope identity')
    parser.add_argument('--scope', choices=['project', 'user'], default='project')
    parser.add_argument('action', choices=sorted(ACTIONS))
    parser.add_argument('--consent', action='store_true', help='Caller has explicit consent for this scope')
    parser.add_argument('--manage', action='store_true', help='Caller has an explicit view/delete request')
    parser.add_argument('--id', dest='identity')
    parser.add_argument('--revision', help='Opaque revision token from the previous result')
    parser.add_argument('--query', default='')
    args = vars(parser.parse_args())
    try:
        if args['action'] == 'save':
            raw = sys.stdin.buffer.read(MAX_RECORD+1)
            require(len(raw) <= MAX_RECORD, 'Record exceeds size limit')
            args['record'] = json.loads(raw)
        print(json.dumps(perform(**args), ensure_ascii=False))
    except (OSError, ValueError, TypeError, RecursionError, sqlite3.Error) as exc:
        # Only our fixed refusal messages are safe to expose, never SQLite/input details.
        message = str(exc) if isinstance(exc, MemoryRefusal) else 'Storage or input failure; preserve the folder and request review'
        parser.exit(1, 'error: ' + message + '\n')


if __name__ == '__main__': main()

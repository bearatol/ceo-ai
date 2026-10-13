"""Run only inside the benchmark container before admitting scanner runs."""
import errno
import json
import os
import pathlib
import socket

if not pathlib.Path('/.dockerenv').exists():
    raise RuntimeError('container required')
uid = os.getuid()
if uid == 0:
    raise RuntimeError('non-root user required')
status = pathlib.Path('/proc/self/status').read_text()
fields = dict(line.split(':', 1) for line in status.splitlines() if ':' in line)
no_new_privileges = fields['NoNewPrivs'].strip() == '1'
effective_capabilities = int(fields['CapEff'].strip(), 16)
if not no_new_privileges:
    raise RuntimeError('no-new-privileges required')
if effective_capabilities != 0:
    raise RuntimeError('effective capabilities must be empty')
write_probes = {}
for path in ('/__ceo_write_probe__', '/fixtures/__ceo_write_probe__'):
    try:
        with open(path, 'xb') as stream:
            stream.write(b'preflight failed')
    except OSError as exc:
        if exc.errno not in (errno.EROFS, errno.EACCES):
            raise RuntimeError('unexpected write probe failure: ' + path) from exc
        write_probes[path] = errno.errorcode[exc.errno]
    else:
        raise RuntimeError('unexpected write permission: ' + path)
with socket.socket() as sock:
    sock.settimeout(2)
    result = sock.connect_ex(('1.1.1.1', 443))
    if result != errno.ENETUNREACH:
        raise RuntimeError('expected no route, got errno: ' + str(result))
print(json.dumps({
    'uid': uid, 'no_new_privileges': no_new_privileges,
    'effective_capabilities': effective_capabilities,
    'write_probes': write_probes, 'external_connection': errno.errorcode[result],
    'limitations': 'Point-in-time probe, not a container escape assessment.'
}, indent=2))

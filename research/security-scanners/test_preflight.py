"""Verify fail-closed diagnostics under -O without real writes or networking."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


class OptimizedPreflight(unittest.TestCase):
    def invoke(self, uid=501, no_new_privileges=1, capabilities=0,
               network=errno.ENETUNREACH):
        source = """
import errno, pathlib, runpy, socket
from unittest.mock import patch, MagicMock
status = 'NoNewPrivs: {nnp}\\nCapEff: {caps:016x}\\n'
sock = MagicMock()
sock.__enter__.return_value.connect_ex.return_value = {network}
with patch.object(pathlib.Path, 'exists', return_value=True), \\
     patch.object(pathlib.Path, 'read_text', return_value=status), \\
     patch('os.getuid', return_value={uid}), \\
     patch('builtins.open', side_effect=OSError(errno.EROFS, 'synthetic read-only probe')), \\
     patch.object(socket, 'socket', return_value=sock):
    runpy.run_path({path}, run_name='__main__')
""".format(nnp=no_new_privileges, caps=capabilities, network=network,
           uid=uid, path=repr(str(Path(__file__).with_name('preflight.py'))))
        return subprocess.run([sys.executable, '-O', '-c', source],
                              capture_output=True, timeout=5,
                              env={'PATH': os.defpath})

    def test_invalid_isolation_never_reports_success_with_optimization(self):
        for change in ({'uid': 0}, {'no_new_privileges': 0},
                       {'capabilities': 1}, {'network': 0}):
            with self.subTest(change=change):
                result = self.invoke(**change)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b'')

    def test_success_reports_observed_values_with_optimization(self):
        # The fake socket uses this host's errno, without contacting the network.
        result = self.invoke(network=errno.ENETUNREACH)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        report = json.loads(result.stdout)
        self.assertEqual(report['uid'], 501)
        self.assertEqual(report['effective_capabilities'], 0)
        self.assertTrue(report['no_new_privileges'])
        self.assertEqual(report['external_connection'], 'ENETUNREACH')


if __name__ == '__main__':
    unittest.main()

import hashlib
import io
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import inventory_release as runner


def archive_payload(extra=None, link=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name in sorted(runner.MEMBERS | ({extra} if extra else set())):
            entry = zipfile.ZipInfo(name)
            entry.create_system = 3
            entry.external_attr = ((stat.S_IFLNK if name == link else stat.S_IFREG) | 0o644) << 16
            archive.writestr(entry, "test fixture")
    return stream.getvalue()


class InventoryReleaseTests(unittest.TestCase):
    def test_compatibility_runner_stays_pinned_to_original_release(self):
        self.assertEqual(runner.ASSET, "ceo-ai-inventory-0.10.2.zip")
        self.assertEqual(runner.TAG, "v0.10.2")
        self.assertEqual(runner.SHA256,
                         "02ae12d0b2e94c8c987cbdbf286028e1ba5972ec29f0b7bbbc5b6a450a99d751")

    def test_attestation_failure_never_runs_inventory(self):
        payload = archive_payload()
        with tempfile.TemporaryDirectory() as path:
            root = Path(path).resolve()
            gh = root / "gh"
            gh.touch()
            error = subprocess.CalledProcessError(1, [str(gh)])
            with patch.object(runner, "download", return_value=payload), \
                 patch.object(runner, "SHA256", hashlib.sha256(payload).hexdigest()), \
                 patch.object(runner.subprocess, "run", side_effect=error) as process:
                with self.assertRaises(subprocess.CalledProcessError):
                    runner.run(gh, root)
            process.assert_called_once()
            command = process.call_args.args[0]
            self.assertEqual(command[:4], [str(gh), "release", "verify-asset", runner.TAG])
            self.assertEqual(command[-2:], ["--repo", runner.REPOSITORY])

    def test_digest_mismatch_never_invokes_verifier(self):
        with tempfile.TemporaryDirectory() as path:
            root = Path(path).resolve()
            gh = root / "gh"
            gh.touch()
            with patch.object(runner, "download", return_value=b"wrong bytes"), \
                 patch.object(runner.subprocess, "run") as process:
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    runner.run(gh, root)
            process.assert_not_called()

    def test_rejects_unexpected_member_and_link_before_writing(self):
        for payload in (archive_payload(extra="../outside"), archive_payload(link="ceo_inventory.py")):
            with tempfile.TemporaryDirectory() as path:
                root = Path(path)
                with self.assertRaises(ValueError):
                    runner.stage_verified_members(payload, root)
                self.assertEqual(list(root.iterdir()), [])

    def test_verified_archive_runs_only_the_inventory_entry(self):
        payload = archive_payload()
        with tempfile.TemporaryDirectory() as path:
            root = Path(path).resolve()
            gh = root / "gh"
            gh.touch()
            with patch.object(runner, "download", return_value=payload), \
                 patch.object(runner, "SHA256", hashlib.sha256(payload).hexdigest()), \
                 patch.object(runner.subprocess, "run") as process:
                runner.run(gh, root)
            self.assertEqual(process.call_count, 2)
            execution = process.call_args_list[1]
            self.assertEqual(execution.args[0][:3], [sys.executable, "-I", "-B"])
            self.assertEqual(Path(execution.args[0][3]).name, "ceo_inventory.py")
            self.assertEqual(execution.args[0][4:], ["--home", str(root)])


if __name__ == "__main__":
    unittest.main()

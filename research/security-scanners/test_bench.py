"""Focused behavioral checks; no Docker, scanners, or network are required."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("bench", Path(__file__).with_name("bench.py"))
bench = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench)


class PathChecks(unittest.TestCase):
    def test_rejects_escaping_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in ("../outside", "/outside", "fixtures/../../outside"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    bench.checked_path(root, path)

    def test_rejects_symlink_component(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "real").mkdir()
            (root / "link").symlink_to(root / "real", target_is_directory=True)
            with self.assertRaises(ValueError):
                bench.checked_path(root, "link/child")

    def test_rejects_symlink_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / "real").mkdir()
            (base / "link").symlink_to(base / "real", target_is_directory=True)
            with self.assertRaises(ValueError):
                bench.checked_path(base / "link", "child")


class ManifestChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / ".runtime/.venv/cisco/site").mkdir(parents=True)
        (self.root / "fixtures/skills/example").mkdir(parents=True)
        (self.root / "fixtures/skills/example/SKILL.md").write_text("test fixture\n")
        self.cases = {"skill_cases": [{"id": "example", "path": "fixtures/skills/example"}], "format_probes": []}
        self.engines = {"engines": [{"id": "cisco", "image": "python@sha256:" + "a" * 64}]}
        self.write_inputs()

    def write_inputs(self):
        (self.root / "cases.json").write_text(json.dumps(self.cases))
        (self.root / "engines.json").write_text(json.dumps(self.engines))

    def test_rejects_missing_or_unpinned_image(self):
        for image in (None, "python:latest", "python@sha256:1234"):
            with self.subTest(image=image):
                self.engines["engines"][0] = {"id": "cisco"}
                if image is not None:
                    self.engines["engines"][0]["image"] = image
                self.write_inputs()
                with self.assertRaises(ValueError):
                    bench.load_inputs(self.root)

    def test_rejects_case_path_outside_fixtures(self):
        self.cases["skill_cases"][0]["path"] = "cases.json"
        self.write_inputs()
        with self.assertRaises(ValueError):
            bench.load_inputs(self.root)

    def test_rejects_nested_fixture_symlink(self):
        (self.root / "fixtures/skills/example/alias.md").symlink_to(self.root / "cases.json")
        with self.assertRaises(ValueError):
            bench.load_inputs(self.root)

    def test_rejects_nested_engine_symlink(self):
        (self.root / ".runtime/.venv/cisco/site/alias").symlink_to(self.root / "cases.json")
        with self.assertRaises(ValueError):
            bench.load_inputs(self.root)

    def test_rejects_oversized_manifest(self):
        (self.root / "cases.json").write_bytes(b" " * (256 * 1024 + 1))
        with self.assertRaises(ValueError):
            bench.load_inputs(self.root)


class ProcessBounds(unittest.TestCase):
    def test_timeout_stops_process(self):
        result = bench.run_bounded([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.15)
        self.assertEqual(result["status"], "timeout")
        self.assertLess(result["duration_seconds"], 2)

    def test_combined_stdout_stderr_limit(self):
        result = bench.run_bounded(
            [sys.executable, "-c", "import os; os.write(1,b'x'*12000); os.write(2,b'y'*12000)"],
            timeout=2, max_output=1024,
        )
        self.assertEqual(result["status"], "output_limit")
        self.assertLessEqual(len(result["stdout"]) + len(result["stderr"]), 1024)

    def test_nonzero_exit_remains_execution_finished(self):
        result = bench.run_bounded([sys.executable, "-c", "import sys; print('{}'); sys.exit(7)"], timeout=2)
        self.assertEqual(result["status"], "execution_finished")
        self.assertEqual(result["exitcode"], 7)
        self.assertEqual(result["stdout"].strip(), b"{}")

    def test_child_does_not_inherit_host_credentials(self):
        with patch.dict(os.environ, {"CEO_BENCH_FAKE_SECRET": "synthetic-marker"}):
            result = bench.run_bounded(
                [sys.executable, "-c", "import os; print(os.environ.get('CEO_BENCH_FAKE_SECRET', 'absent'))"], timeout=2,
            )
        self.assertEqual(result["stdout"].strip(), b"absent")


class CommandConstraints(unittest.TestCase):
    def test_restricted_runtime_and_hardcoded_entrypoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = bench.command(root, ["docker", "--config", "empty", "--host", "unix:///socket"],
                                 {"id": "nvidia", "image": "python@sha256:" + "a" * 64},
                                 {"path": "fixtures/skills/example"}, "ceo-scan-test")
        self.assertEqual(args[args.index("--network") + 1], "none")
        self.assertEqual(args[args.index("--pull") + 1], "never")
        self.assertEqual(args[args.index("--entrypoint") + 1], "python")
        self.assertIn("--no-llm", args)
        self.assertIn("--read-only", args)
        self.assertIn("no-new-privileges", args)
        mounts = [args[index + 1] for index, arg in enumerate(args) if arg == "--mount"]
        self.assertEqual(len(mounts), 2)
        self.assertTrue(all(mount.endswith(",readonly") for mount in mounts))
        self.assertFalse(any("socket" in mount for mount in mounts))


if __name__ == "__main__":
    unittest.main()

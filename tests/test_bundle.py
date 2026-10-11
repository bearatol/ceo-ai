"""Check standalone root isolation and the shipped contract examples."""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACK = ROOT / ".apm/skills/ceo-ai"
TEAM = PACK / "tools/team/team.py"


class BundleTests(unittest.TestCase):
    def test_explicit_root_wins_over_cwd_and_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            unrelated = pathlib.Path(directory)
            (unrelated / "catalog.json").write_text("broken global catalog")
            run = subprocess.run([sys.executable, str(TEAM), "--home", str(PACK), "list", "--type", "agent"],
                                 cwd=directory, env=dict(os.environ, AGENTS_HOME=directory),
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("agent:decision-mentor", run.stdout)

    def test_missing_root_is_rejected_even_with_configured_environment(self):
        run = subprocess.run([sys.executable, str(TEAM), "list"],
                             env=dict(os.environ, AGENTS_HOME=str(ROOT)),
                             capture_output=True, text=True, timeout=10)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("--home", run.stderr)

    def test_shipped_examples_match(self):
        run = subprocess.run([sys.executable, str(TEAM), "--home", str(PACK),
                              "validate", "result", str(PACK / "orchestration/templates/result.json"),
                              "--task", str(PACK / "orchestration/templates/task.json")],
                             capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_doctor_runs_from_an_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run([sys.executable, str(ROOT / "scripts/check.py")],
                                 cwd=directory, capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()

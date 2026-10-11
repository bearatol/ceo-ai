"""Behavior checks for CEO packet boundaries and capability inventory."""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
ROOT = pathlib.Path(__file__).resolve().parents[1]
PACK = ROOT
spec = importlib.util.spec_from_file_location("ceo_team", PACK / "tools/team/team.py")
team = importlib.util.module_from_spec(spec)
spec.loader.exec_module(team)
COMPONENTS = team.component_map(json.loads((PACK / "catalog.json").read_text()))


def task():
    return dict(schema_version=1, task_id="check-1", title="Check", objective="Verify behavior",
                assigned_agent="agent:engineer", scope=["src"], permissions="read-only",
                acceptance_criteria=["Behavior verified"], status="ready")


def result():
    return dict(schema_version=1, task_id="check-1", agent="agent:engineer", status="complete",
                summary="Verified", skills_considered=[], skills_applied=[],
                evidence=["test_contract passed"], risks=[])


class PacketTests(unittest.TestCase):
    def test_duplicate_catalog_ids_are_rejected(self):
        with self.assertRaises(SystemExit):
            team.component_map({"components": [{"id": "agent:a", "type": "agent"},
                                               {"id": "agent:a", "type": "agent"}]})

    def test_valid_packets(self):
        self.assertEqual(team.validate_task(task(), COMPONENTS), [])
        self.assertEqual(team.validate_result(result(), COMPONENTS), [])

    def test_read_only_agent_cannot_receive_write_permission(self):
        packet = task()
        packet.update(assigned_agent="agent:decision-mentor", permissions="workspace-write")
        self.assertTrue(team.validate_task(packet, COMPONENTS))

    def test_non_agent_component_cannot_own_task_or_result(self):
        packet = task()
        packet["assigned_agent"] = "skill:ceo"
        self.assertTrue(team.validate_task(packet, COMPONENTS))
        packet = result()
        packet["agent"] = "skill:ceo"
        self.assertTrue(team.validate_result(packet, COMPONENTS))

    def test_invalid_packets_return_errors_without_crashing(self):
        for factory, validator, fields in [
            (task, team.validate_task, {"schema_version": True, "scope": "src", "status": "fake",
                                       "task_id": "../outside", "assigned_agent": [], "title": ""}),
            (result, team.validate_result, {"schema_version": 2, "status": "fake", "evidence": "yes",
                                           "agent": [], "summary": "", "skills_considered": [{}]}),
        ]:
            for key, value in fields.items():
                with self.subTest(key=key, value=value):
                    packet = factory()
                    packet[key] = value
                    self.assertTrue(validator(packet, COMPONENTS))
            packet = factory()
            packet["unexpected"] = True
            self.assertTrue(validator(packet, COMPONENTS))
            self.assertTrue(validator([], COMPONENTS))

    def test_completed_result_requires_nonempty_evidence(self):
        packet = result()
        packet["evidence"] = []
        self.assertTrue(team.validate_result(packet, COMPONENTS))

    def test_result_is_bound_to_expected_task_and_agent(self):
        for key, value in [("task_id", "another-task"), ("agent", "agent:ceo")]:
            packet = result()
            packet[key] = value
            self.assertTrue(team.validate_result(packet, COMPONENTS, expected_task=task()))
        self.assertEqual(team.validate_result(result(), COMPONENTS, expected_task=task()), [])


@unittest.skipUnless(os.name == "posix", "Inventory scanner requires POSIX no-follow operations")
class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = pathlib.Path(self.temp.name).resolve()
        (self.home / "skills/demo").mkdir(parents=True)
        self.skill = self.home / "skills/demo/SKILL.md"
        self.skill.write_text("---\nname: demo\ndescription: Example\n---\nOriginal behavior.\n")

    def run_index(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/ceo_inventory.py"),
                               "--home", str(self.home), *args], capture_output=True,
                              text=True, timeout=10)

    def test_scan_refresh_and_changed_content(self):
        first = self.run_index()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout)["freshness"], "missing")
        self.assertEqual(sorted(p.name for p in self.home.iterdir()), ["skills"])
        refresh = self.run_index("--refresh")
        self.assertEqual(refresh.returncode, 0, refresh.stderr)
        self.assertEqual(json.loads(self.run_index().stdout)["freshness"], "fresh")
        self.skill.write_text(self.skill.read_text() + "Changed behavior.\n")
        self.assertEqual(json.loads(self.run_index().stdout)["freshness"], "stale")

    def test_skill_and_agent_are_discovered_without_source_catalog(self):
        (self.home / "agents").mkdir()
        (self.home / "agents/reviewer.md").write_text("---\nname: reviewer\ndescription: Review\naccess: read-only\n---\n")
        scan = self.run_index()
        self.assertEqual(scan.returncode, 0, scan.stderr)
        self.assertEqual([x["id"] for x in json.loads(scan.stdout)["entries"]],
                         ["agent:reviewer", "skill:demo"])

    def test_failed_refresh_preserves_cache_and_catalog(self):
        self.assertEqual(self.run_index("--refresh").returncode, 0)
        cache = self.home / ".ceo-inventory.json"
        before = cache.read_bytes()
        source = self.home / "catalog.json"
        source.write_text("unmanaged source data")
        self.skill.write_text("---\nname: demo\nname: conflicting\n---\n")
        scan = self.run_index("--refresh")
        self.assertNotEqual(scan.returncode, 0)
        self.assertEqual(cache.read_bytes(), before)
        self.assertEqual(source.read_text(), "unmanaged source data")

    def test_symlinks_and_nonregular_inputs_are_refused(self):
        self.skill.unlink()
        outside = self.home / "outside.md"
        outside.write_text("must not read this")
        self.skill.symlink_to(outside)
        self.assertNotEqual(self.run_index("--refresh").returncode, 0)
        self.skill.unlink()
        os.mkfifo(self.skill)
        self.assertNotEqual(self.run_index().returncode, 0)

    def test_cache_conflicts_and_symlinked_roots_are_refused(self):
        cache = self.home / ".ceo-inventory.json"
        cache.write_text("unmanaged content")
        self.assertNotEqual(self.run_index("--refresh").returncode, 0)
        self.assertEqual(cache.read_text(), "unmanaged content")
        cache.unlink()
        cache.symlink_to(self.skill)
        before = self.skill.read_bytes()
        self.assertNotEqual(self.run_index("--refresh").returncode, 0)
        self.assertEqual(self.skill.read_bytes(), before)

    def test_removed_component_marks_index_stale(self):
        self.assertEqual(self.run_index("--refresh").returncode, 0)
        self.skill.unlink()
        self.skill.parent.rmdir()
        scan = self.run_index()
        self.assertEqual(json.loads(scan.stdout)["freshness"], "stale")
        self.assertEqual(json.loads(scan.stdout)["entries"], [])

    def test_duplicate_names_and_root_symlinks_are_refused(self):
        (self.home / "skills/other").mkdir()
        (self.home / "skills/other/SKILL.md").write_bytes(self.skill.read_bytes())
        self.assertNotEqual(self.run_index().returncode, 0)
        alias = self.home / "alias"
        alias.symlink_to(self.home, target_is_directory=True)
        scan = self.run_index("--home", str(alias))
        self.assertNotEqual(scan.returncode, 0)

    def test_addition_marks_index_stale(self):
        self.assertEqual(self.run_index("--refresh").returncode, 0)
        (self.home / "skills/extra").mkdir()
        (self.home / "skills/extra/SKILL.md").write_text("---\nname: extra\n---\n")
        self.assertEqual(json.loads(self.run_index().stdout)["freshness"], "stale")

    def test_concurrent_refresh_is_refused_without_overwrite(self):
        import fcntl
        module_spec = importlib.util.spec_from_file_location("ceo_index", ROOT / "scripts/ceo_inventory.py")
        inventory = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(inventory)
        self.assertEqual(self.run_index("--refresh").returncode, 0)
        before = (self.home / ".ceo-inventory.json").read_bytes()
        first = inventory.open_root(str(self.home))
        second = inventory.open_root(str(self.home))
        try:
            fcntl.flock(first, fcntl.LOCK_EX | fcntl.LOCK_NB)
            previous = inventory.read_cache(second)
            with self.assertRaises(inventory.InventoryError):
                inventory.refresh(second, inventory.scan(second), previous)
        finally:
            os.close(second)
            os.close(first)
        self.assertEqual((self.home / ".ceo-inventory.json").read_bytes(), before)

    def test_interrupted_refresh_keeps_previous_cache(self):
        module_spec = importlib.util.spec_from_file_location("ceo_index", ROOT / "scripts/ceo_inventory.py")
        inventory = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(inventory)
        self.assertEqual(self.run_index("--refresh").returncode, 0)
        before = (self.home / ".ceo-inventory.json").read_bytes()
        self.skill.write_text(self.skill.read_text() + "Updated.\n")
        root_fd = inventory.open_root(str(self.home))
        try:
            previous = inventory.read_cache(root_fd)
            document = inventory.scan(root_fd)
            with mock.patch.object(inventory.os, "replace", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    inventory.refresh(root_fd, document, previous)
        finally:
            os.close(root_fd)
        self.assertEqual((self.home / ".ceo-inventory.json").read_bytes(), before)
        self.assertEqual(list(self.home.glob(".ceo-inventory-*.tmp")), [])

    def test_completed_cli_result_requires_original_assignment(self):
        (self.home / "catalog.json").write_text(json.dumps({"components": list(COMPONENTS.values())}))
        result_file = self.home / "result.json"
        result_file.write_text(json.dumps(result()))
        command = [sys.executable, str(PACK / "tools/team/team.py"),
                   "--home", str(self.home), "validate", "result", str(result_file)]
        rejected = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(rejected.returncode, 0)
        assignment = self.home / "task.json"
        assignment.write_text(json.dumps(task()))
        accepted = subprocess.run(command + ["--task", str(assignment)], capture_output=True, text=True, timeout=10)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_oversized_input_is_rejected(self):
        self.skill.write_text("x" * (256 * 1024 + 1))
        self.assertNotEqual(self.run_index().returncode, 0)


if __name__ == "__main__":
    unittest.main()

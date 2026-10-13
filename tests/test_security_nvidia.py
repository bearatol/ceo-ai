#!/usr/bin/env python3
"""Offline adapter boundaries; no Docker daemon or scanner is run by tests."""
import json
import importlib.util
import marshal
import os
import pathlib
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "plugins/ceo-ai-security/skills/security-scan/scripts"))
import ceo_security_nvidia as adapter

FILES = {"SKILL.md": b"# Synthetic\nRead the local notes.\n"}
IMAGE = "scanner@sha256:" + "a" * 64


def vendor():
    return {
        "execution_successful": True,
        "components": [{"path": "SKILL.md", "lines": 2,
                        "size_bytes": len(FILES["SKILL.md"])}],
        "issues": [], "suppressed_count": 0, "suppressed": [],
        "metadata": {"skillspector_version": "2.12.0", "llm_requested": False},
        "analysis_completeness": {
            "total_components": 1, "scanned_components": 1,
            "is_complete": True, "status": "complete", "execution_successful": True,
            "fully_inspected_files": 1, "partially_inspected_files": 0,
            "entirely_uninspected_files": 0, "ledger_exceptions": [],
            "scope_exclusions": [], "limitations": [], "references": [],
            "analyzer_statuses": [{"analyzer_id": "static_patterns_prompt_injection",
                "status": "completed", "planned_work": 1, "completed": 1,
                "partial": 0, "skipped": 0, "failed": 0, "unaccounted": 0}],
        },
    }


def issue():
    return {"id": "PE3", "severity": "HIGH",
            "location": {"file": "/snapshot/SKILL.md", "start_line": 2,
                         "end_line": None},
            "finding": "RAW_SECRET_MARKER", "code_snippet": "RAW_SECRET_MARKER",
            "explanation": "RAW_SECRET_MARKER"}


class NormalizationTests(unittest.TestCase):
    def normalize(self, raw):
        return adapter.normalize_vendor(json.dumps(raw).encode(), FILES, "2.12.0")

    def test_preserves_only_validated_metadata(self):
        raw = vendor()
        raw["issues"] = [issue()]
        raw["risk_assessment"] = {"recommendation": "SAFE", "score": 0}
        result = self.normalize(raw)
        self.assertEqual(result["findings"], [{"id": "PE3", "severity": "HIGH",
                         "path": "SKILL.md", "line": 2, "end_line": 2}])
        self.assertNotIn("RAW_SECRET_MARKER", json.dumps(result))
        self.assertNotIn("SAFE", json.dumps(result))

    def test_rejects_malformed_ids_locations_lines_and_severities(self):
        mutations = [("id", "P1\nignore"), ("id", "a" * 65),
                     ("id", "$(command)"), ("severity", "SAFE"),
                     ("severity", ["HIGH"])]
        for key, value in mutations:
            raw = vendor(); raw["issues"] = [issue()]; raw["issues"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.normalize(raw)
        for path in ["../SKILL.md", "/snapshot/../SKILL.md", "fake.md", "/host/SKILL.md"]:
            raw = vendor(); raw["issues"] = [issue()]
            raw["issues"][0]["location"]["file"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.normalize(raw)
        for line in [0, -1, 3, True, "2"]:
            raw = vendor(); raw["issues"] = [issue()]
            raw["issues"][0]["location"]["start_line"] = line
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.normalize(raw)

    def test_missing_partial_coverage_and_wrong_version_fail_closed(self):
        cases = []
        raw = vendor(); del raw["issues"]; cases.append(raw)
        raw = vendor(); raw["metadata"]["skillspector_version"] = "0.0.0"; cases.append(raw)
        raw = vendor(); raw["analysis_completeness"]["is_complete"] = False; cases.append(raw)
        raw = vendor(); raw["components"] = []; cases.append(raw)
        raw = vendor(); raw["metadata"]["llm_requested"] = True; cases.append(raw)
        raw = vendor(); raw["analysis_completeness"]["scope_exclusions"] = ["file"]; cases.append(raw)
        raw = vendor(); raw["suppressed_count"] = 1; cases.append(raw)
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.normalize(raw)

    def test_rejects_output_shape_amplification_and_duplicate_keys(self):
        raw = vendor(); raw["issues"] = [issue()] * 513
        with self.assertRaises(ValueError): self.normalize(raw)
        raw = vendor(); raw["metadata"].update({str(x): None for x in range(70)})
        with self.assertRaises(ValueError): self.normalize(raw)
        with self.assertRaises(ValueError):
            adapter.normalize_vendor(b'{"issues":[],"issues":[]}', FILES, "2.12.0")

    def test_empty_disabled_or_inconsistent_analyzer_coverage_is_not_complete(self):
        for mutate in (lambda r: r["analysis_completeness"].update(analyzer_statuses=[]),
                       lambda r: r["analysis_completeness"]["analyzer_statuses"][0].update(status="disabled"),
                       lambda r: r["analysis_completeness"]["analyzer_statuses"][0].update(completed=0)):
            raw = vendor(); mutate(raw)
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.normalize(raw)

    def test_resolved_local_references_are_validated_without_retaining_evidence(self):
        raw = vendor()
        raw["analysis_completeness"]["references"] = [{"source_path": "SKILL.md", "line": 1,
            "target_path": "SKILL.md", "status": "resolved", "disposition": "analyzed",
            "evidence": "RAW_SECRET_MARKER", "reference_kind": "markdown_link"}]
        self.assertEqual(self.normalize(raw)["findings"], [])
        raw["analysis_completeness"]["references"][0]["target_path"] = "missing.md"
        with self.assertRaises(ValueError): self.normalize(raw)


@unittest.skipUnless(os.name == 'posix', 'Adapter runtime requires POSIX descriptors and signals')
class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = pathlib.Path(self.temp.name).resolve()
        self.package = self.workspace / "package"
        self.package.mkdir()
        (self.package / "SKILL.md").write_bytes(FILES["SKILL.md"])

    def run_fake(self, raw=None, status="finished", returncode=0):
        raw = vendor() if raw is None else raw
        seen = []
        def run(command, **kwargs):
            seen.append((command, kwargs))
            self.assertEqual(kwargs["env"], {"PATH": adapter.SAFE_PATH})
            if "run" in command:
                mount = command[command.index("--mount") + 1]
                stage = pathlib.Path(mount.split("src=", 1)[1].split(",", 1)[0])
                self.assertEqual((stage / "SKILL.md").read_bytes(), (self.package / "SKILL.md").read_bytes())
                self.assertFalse((stage / "SKILL.md").stat().st_mode & 0o222)
                config = pathlib.Path(command[command.index("--config") + 1])
                self.assertEqual(json.loads((config / "config.json").read_text()), {})
                return status, returncode, json.dumps(raw).encode()
            return "finished", 0, b""
        with mock.patch.object(adapter, "_run_bounded", side_effect=run), \
             mock.patch.object(adapter, "_docker_executable", return_value="/usr/bin/docker"):
            result = adapter.scan_package(self.package, self.workspace, IMAGE, "2.12.0")
        return result, seen

    def test_command_is_offline_readonly_minimal_and_snapshot_bound(self):
        with mock.patch.dict(os.environ, {"HOME": "/private/home", "API_KEY": "RAW_SECRET_MARKER",
                                         "HTTP_PROXY": "https://example.invalid"}):
            result, seen = self.run_fake()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["decision"], "no-findings")
        self.assertEqual(result["trust"], "unverified")
        self.assertEqual(result["bindings"]["image"], IMAGE)
        self.assertEqual(len(result["bindings"]["bundle_sha256"]), 64)
        command = seen[0][0]
        for flag in ["--read-only", "--cap-drop", "--security-opt", "--pids-limit",
                     "--memory", "--cpus", "--tmpfs"]: self.assertIn(flag, command)
        self.assertEqual(command[command.index("--pull") + 1], "never")
        self.assertEqual(command[command.index("--network") + 1], "none")
        self.assertEqual(command[command.index("--entrypoint") + 1], "python")
        self.assertEqual(command[-5:], ["scan", "/snapshot", "--no-llm", "--format", "json"])
        self.assertEqual(command.count("--mount"), 1)
        self.assertNotIn(str(self.package), " ".join(command))
        self.assertEqual(sorted(p.name for p in self.workspace.iterdir()), ["package"])

    def test_failures_never_become_no_findings(self):
        for status, code in [("timeout", None), ("output_limit", None), ("finished", 4)]:
            result, _ = self.run_fake(status=status, returncode=code)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertEqual(result["decision"], "incomplete")
            self.assertNotIn("RAW_SECRET_MARKER", json.dumps(result))
        raw = vendor(); raw["issues"] = [issue()]; raw["issues"][0]["id"] = "bad\nRAW_SECRET_MARKER"
        result, _ = self.run_fake(raw)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertNotIn("RAW_SECRET_MARKER", json.dumps(result))

    def test_excluded_secret_prevents_docker(self):
        with mock.patch.object(adapter, "snapshot_package", return_value=(FILES, [{"path": ".env", "reason": "sensitive"}])), \
             mock.patch.object(adapter, "_run_bounded") as run:
            result = adapter.scan_package(self.package, self.workspace, IMAGE, "2.12.0")
        self.assertEqual(result["status"], "INCOMPLETE")
        run.assert_not_called()

    def test_cleanup_timeout_invalidates_success(self):
        with mock.patch.object(adapter, "_run_bounded", side_effect=[
                ("finished", 0, json.dumps(vendor()).encode()), ("timeout", -9, b"")]), \
             mock.patch.object(adapter, "_docker_executable", return_value="/usr/bin/docker"):
            result = adapter.scan_package(self.package, self.workspace, IMAGE, "2.12.0")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["reason"], "cleanup_failed")

    def test_builtin_partial_coverage_survives_successful_vendor_findings(self):
        for name, content, reason in [("helper.py", b"print('synthetic')\n", "unsupported-code-lexical-only"),
                                      ("opaque.bin", b"\x00\xff", "binary-or-unparseable"),
                                      ("notes.md", b"https://example.invalid/reference\n", "external-reference")]:
            extra = self.package / name
            extra.write_bytes(content)
            try:
                raw = vendor()
                raw["components"].append({"path": name, "lines": 1, "size_bytes": len(content)})
                for key in ("total_components", "scanned_components", "fully_inspected_files"):
                    raw["analysis_completeness"][key] = 2
                raw["analysis_completeness"]["analyzer_statuses"][0].update(planned_work=2, completed=2)
                raw["issues"] = [issue()]
                result, seen = self.run_fake(raw)
                with self.subTest(name=name):
                    self.assertEqual(result["status"], "INCOMPLETE")
                    self.assertEqual(result["decision"], "incomplete")
                    self.assertFalse(result["coverage"]["complete"])
                    self.assertIn(reason, result["coverage"]["reasons"])
                    self.assertEqual(result["findings"][0]["id"], "PE3")
                    self.assertTrue(any("run" in command for command, _ in seen))
            finally:
                extra.unlink()

    def test_invalid_image_host_version_and_workspace_prevent_docker(self):
        cases = [("scanner:latest", "2.12.0", None), (IMAGE, "bad\nversion", None),
                 (IMAGE, "2.12.0", "tcp://127.0.0.1:2375"),
                 (IMAGE, "2.12.0", "unix:///tmp/a,b")]
        for image, version, host in cases:
            with mock.patch.object(adapter, "_run_bounded") as run:
                result = adapter.scan_package(self.package, self.workspace, image, version, host)
            self.assertEqual(result["status"], "INCOMPLETE")
            run.assert_not_called()
        self.workspace.chmod(0o777)
        try:
            with mock.patch.object(adapter, "_run_bounded") as run:
                result = adapter.scan_package(self.package, self.workspace, IMAGE, "2.12.0")
            self.assertEqual(result["status"], "INCOMPLETE")
            run.assert_not_called()
        finally: self.workspace.chmod(0o700)

    def test_version_segments_are_bounded_and_not_echoed(self):
        for version in ("9" * 4096 + ".1.0", "1." + "9" * 4096 + ".0", "1.0." + "9" * 4096):
            with mock.patch.object(adapter, "_run_bounded") as run:
                result = adapter.scan_package(self.package, self.workspace, IMAGE, version)
            self.assertEqual(result["status"], "INCOMPLETE")
            self.assertTrue(result["bindings"]["scanner_version"] is None)
            self.assertEqual(result["decision"], "incomplete")
            run.assert_not_called()

    def test_verified_findings_have_review_required_decision(self):
        raw = vendor()
        raw["issues"] = [issue()]
        result, _ = self.run_fake(raw)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["decision"], "review-required")

    def run_copied_cli(self, *, stale_bytecode=False, expect_snapshot=True):
        scripts = self.workspace / "scripts"
        scripts.mkdir()
        source_scripts = ROOT / "plugins/ceo-ai-security/skills/security-scan/scripts"
        for name in ("ceo_security_nvidia", "ceo_inventory", "ceo_security"):
            destination = scripts / (name + ".py")
            shutil.copyfile(source_scripts / (name + ".py"), destination)
            if stale_bytecode and name != "ceo_security_nvidia":
                cache = pathlib.Path(importlib.util.cache_from_source(str(destination)))
                cache.parent.mkdir(exist_ok=True)
                info = destination.stat()
                header = importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, int(info.st_mtime), info.st_size)
                # A valid timestamp cache must never replace the reviewed source.
                cache.write_bytes(header + marshal.dumps(compile("raise SystemExit(93)", str(destination), "exec")))
        result = subprocess.run([sys.executable, str(scripts / "ceo_security_nvidia.py"),
            "--package", str(self.package), "--workspace", str(self.workspace),
            "--image", IMAGE, "--version", "2.12.0"],
            env={"PATH": ""}, stdin=subprocess.DEVNULL, capture_output=True, timeout=5, check=False)
        self.assertEqual(result.returncode, 2, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stderr, b"")
        report = json.loads(result.stdout)
        if expect_snapshot:
            self.assertIsNotNone(report["bindings"]["bundle_sha256"])
        else:
            self.assertIsNone(report["bindings"]["bundle_sha256"])
            self.assertEqual(report["status"], "INCOMPLETE")
            self.assertEqual(report["decision"], "incomplete")
            self.assertEqual(report["reason"], "invalid_input_or_output")
            self.assertNotIn("RAW_PRIVATE_PATH_MARKER", result.stdout.decode())
            self.assertNotIn(str(self.package), result.stdout.decode())
        return scripts, report

    def test_direct_cli_without_bytecode_flags_does_not_write_caches(self):
        scripts, _ = self.run_copied_cli()
        self.assertFalse(list(scripts.rglob("*.pyc")))
        self.assertFalse((scripts / "__pycache__").exists())

    def test_direct_cli_ignores_valid_stale_sibling_bytecode(self):
        _, report = self.run_copied_cli(stale_bytecode=True)
        self.assertEqual(report["decision"], "incomplete")

    def test_direct_cli_file_limit_returns_redacted_incomplete_json(self):
        (self.package / "RAW_PRIVATE_PATH_MARKER.md").write_bytes(b"x" * (256 * 1024 + 1))
        self.run_copied_cli(expect_snapshot=False)

    def test_direct_cli_symlink_returns_redacted_incomplete_json(self):
        (self.package / "RAW_PRIVATE_PATH_MARKER.md").symlink_to("SKILL.md")
        self.run_copied_cli(expect_snapshot=False)

    def cancellation_process(self, *, cancel_during_cleanup=False, close_pipes=False):
        fake_bin = self.workspace / "bin"
        fake_bin.mkdir()
        docker = fake_bin / "docker"
        state = self.workspace / "fake-state.json"
        active = self.workspace / "fake-container-active"
        cleanup = self.workspace / "fake-cleanup-ready"
        docker.write_text(f"#!{sys.executable}\n" + "\n".join([
            "import json, os, pathlib, sys, time",
            f"state = pathlib.Path({str(state)!r})",
            f"active = pathlib.Path({str(active)!r})",
            f"cleanup = pathlib.Path({str(cleanup)!r})",
            "args = sys.argv[1:]",
            "if 'run' in args:",
            "    name = args[args.index('--name') + 1]",
            "    stage = args[args.index('--mount') + 1].split('src=', 1)[1].split(',', 1)[0]",
            "    active.write_text(name)",
            "    state.write_text(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp(), 'name': name, 'stage': stage}))",
            f"    if {cancel_during_cleanup!r}:",
            f"        print({json.dumps(vendor())!r}, flush=True)",
            "    else:",
            f"        if {close_pipes!r}: os.close(1); os.close(2)",
            "        time.sleep(60)",
            "elif 'rm' in args:",
            "    expected = json.loads(state.read_text())['name']",
            "    if args[-1] != expected: sys.exit(10)",
            "    cleanup.write_text(expected)",
            "    time.sleep(0.3)",
            "    active.unlink()",
        ]) + "\n", encoding="utf-8")
        docker.chmod(0o700)
        command = [sys.executable, str(ROOT / "plugins/ceo-ai-security/skills/security-scan/scripts/ceo_security_nvidia.py"),
                   "--package", str(self.package), "--workspace", str(self.workspace),
                   "--image", IMAGE, "--version", "2.12.0"]
        process = subprocess.Popen(command, env={"PATH": str(fake_bin)}, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        def stop_test_processes():
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
            process.stdout.close()
            process.stderr.close()
            if state.exists():
                pgid = json.loads(state.read_text())["pgid"]
                try: os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError: pass
        self.addCleanup(stop_test_processes)
        return process, state, active, cleanup

    def wait_file(self, path):
        deadline = time.monotonic() + 3
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(path.exists(), "fake Docker did not reach the expected phase")

    def test_sigterm_during_scan_and_sighup_during_cleanup_remove_owned_resources(self):
        process, state, active, cleanup = self.cancellation_process()
        self.wait_file(state)
        process.send_signal(signal.SIGTERM)
        self.wait_file(cleanup)
        process.send_signal(signal.SIGHUP)
        stdout, stderr = process.communicate(timeout=4)
        self.assertEqual(process.returncode, 128 + signal.SIGTERM)
        self.assertEqual(stderr, b"")
        report = json.loads(stdout)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertEqual(report["decision"], "incomplete")
        self.assertEqual(report["reason"], "cancelled")
        detail = json.loads(state.read_text())
        self.assertEqual(detail["pid"], detail["pgid"])
        self.assertFalse(active.exists())
        self.assertFalse(pathlib.Path(detail["stage"]).parent.exists())
        with self.assertRaises(ProcessLookupError): os.kill(detail["pid"], 0)

    def test_first_sighup_during_cleanup_defers_until_cleanup_finishes(self):
        process, state, active, cleanup = self.cancellation_process(cancel_during_cleanup=True)
        self.wait_file(cleanup)
        process.send_signal(signal.SIGHUP)
        stdout, stderr = process.communicate(timeout=4)
        self.assertEqual(process.returncode, 128 + signal.SIGHUP)
        self.assertEqual(stderr, b"")
        self.assertEqual(json.loads(stdout)["reason"], "cancelled")
        self.assertFalse(active.exists())
        self.assertFalse(pathlib.Path(json.loads(state.read_text())["stage"]).parent.exists())

    def test_sigterm_after_child_closes_output_pipes_still_cancels_promptly(self):
        process, state, active, cleanup = self.cancellation_process(close_pipes=True)
        self.wait_file(state)
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=4)
        self.assertEqual(process.returncode, 128 + signal.SIGTERM)
        self.assertEqual(stderr, b"")
        self.assertEqual(json.loads(stdout)["reason"], "cancelled")
        self.assertFalse(active.exists())
        self.assertFalse(pathlib.Path(json.loads(state.read_text())["stage"]).parent.exists())

    def test_keyboard_interrupt_propagates_after_cleanup_and_restores_handlers(self):
        previous = {number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGHUP)}
        with mock.patch.object(adapter, "_run_bounded", side_effect=[KeyboardInterrupt(), ("finished", 0, b"")]), \
             mock.patch.object(adapter, "_docker_executable", return_value="/usr/bin/docker"):
            with self.assertRaises(KeyboardInterrupt):
                adapter.scan_package(self.package, self.workspace, IMAGE, "2.12.0")
        self.assertEqual(previous, {number: signal.getsignal(number) for number in previous})
        self.assertEqual(sorted(p.name for p in self.workspace.iterdir()), ["package"])

    def test_stream_timeout_and_combined_output_bound(self):
        env = {"PATH": adapter.SAFE_PATH}
        result = adapter._run_bounded([sys.executable, "-c", "import time; time.sleep(2)"],
                                      env=env, cwd=self.workspace, timeout=0.03)
        self.assertEqual(result[0], "timeout")
        result = adapter._run_bounded([sys.executable, "-c",
                                      "import os; os.write(2,b'x'*65536); os.write(1,b'y'*65536)"],
                                      env=env, cwd=self.workspace, timeout=2, output_limit=70000)
        self.assertEqual(result[0], "output_limit")
        self.assertLessEqual(len(result[2]), 70000)


if __name__ == "__main__":
    unittest.main()

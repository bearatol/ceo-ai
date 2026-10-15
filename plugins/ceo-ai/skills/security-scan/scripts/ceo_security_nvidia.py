#!/usr/bin/env python3
"""Explicit, offline NVIDIA Skillspector adapter. No invocation during indexing.

The approved workspace and its ancestors must be trusted against writers using
the invoking user's identity. Docker and the selected image are trusted local
execution dependencies; their output is still untrusted data, not attestation.
Only a private copy of the admitted package bytes enters the container.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import selectors
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time
import uuid

ADAPTER_VERSION = "1.0.0"
SAFE_PATH = "/usr/bin:/bin:/usr/local/bin"
OUTPUT_LIMIT = 2 * 1024 * 1024
SCAN_TIMEOUT = 25
IMAGE_PATTERN = re.compile(r"(?:[A-Za-z0-9][A-Za-z0-9._:/-]{0,240}@)?sha256:[0-9a-f]{64}\Z")
VERSION_PATTERN = re.compile(r"[0-9]{1,6}\.[0-9]{1,6}\.[0-9]{1,6}(?:[a-z][A-Za-z0-9.]{0,24})?\Z")
ID_PATTERN = re.compile(r"[A-Z]{1,12}[0-9]{1,6}\Z")
SEVERITIES = ("NONE", "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")
COVERAGE_REASONS = frozenset((
    "binary-or-unparseable", "unsupported-code-lexical-only", "unsupported-type-lexical-only",
    "unparseable-structured-text", "text-analysis-limit", "finding-limit", "reference-limit",
    "coverage-reason-limit", "empty-bundle", "unsupported-reference", "external-reference",
    "agent-reference-not-followed", "out-of-package-reference", "missing-reference",
    "analysis-byte-limit",
))
RUNNER = (
    "import importlib.metadata,sys; "
    "expected=sys.argv.pop(1); "
    "actual=importlib.metadata.version('skillspector'); "
    "sys.exit(78) if actual != expected else None; "
    "from skillspector.cli import app; app()"
)
_inventory_module = None


class _Cancelled(Exception):
    """A catchable host termination request; never used for KeyboardInterrupt."""


class _CancellationGuard:
    """Defer repeated signals while bounded resource cleanup is in progress."""

    def __init__(self):
        self.number = None
        self.raised = False
        self.cleaning = False
        self.deferred = 0
        self.previous = {}

    def install(self):
        if threading.current_thread() is not threading.main_thread():
            raise ValueError("main_thread_required_for_cancellation")
        for number in (signal.SIGTERM, signal.SIGHUP):
            self.previous[number] = signal.getsignal(number)
            signal.signal(number, self.handle)

    def handle(self, number, _frame):
        if self.number is None:
            self.number = number
        # Record only: raising asynchronously can interrupt resource assignment
        # or finally setup. Explicit checkpoints unwind only protected scopes.

    def check(self):
        if self.number is not None and not self.raised and not self.cleaning and not self.deferred:
            self.raised = True
            raise _Cancelled()

    @contextlib.contextmanager
    def defer(self, *, raise_pending=True):
        self.deferred += 1
        try:
            yield
        finally:
            self.deferred -= 1
        if raise_pending:
            self.check()

    def restore(self):
        for number, previous in self.previous.items():
            signal.signal(number, previous)


def _load_inventory():
    """Load the trusted sibling source without consulting or creating bytecode."""
    global _inventory_module
    if _inventory_module is None:
        path = pathlib.Path(__file__).with_name("ceo_inventory.py")
        spec = importlib.util.spec_from_file_location("ceo_inventory", path)
        if spec is None:
            raise ValueError("inventory_unavailable")
        module = importlib.util.module_from_spec(spec)
        exec(compile(path.read_bytes(), str(path), "exec", dont_inherit=True), module.__dict__)
        _inventory_module = module
    return _inventory_module


def snapshot_package(package, kind="skill"):
    inventory = _load_inventory()
    try:
        return inventory.snapshot_package(package, kind=kind)
    except inventory.InventoryError:
        # Expected refusals must cross the adapter boundary without raw details.
        raise ValueError("invalid_snapshot") from None


def _digest(files):
    return _load_inventory().load_security_module().bundle_digest(files)


def _plain_path(value):
    text = os.fspath(value)
    if not text or len(text) > 4096 or any(ord(c) < 32 or ord(c) == 127 or c == "," for c in text):
        raise ValueError("invalid_path")
    return text


def _relative_path(value, files):
    if not isinstance(value, str):
        raise ValueError("invalid_location")
    if value.startswith("/snapshot/"):
        value = value[len("/snapshot/"):]
    _plain_path(value)
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) != value or value not in files:
        raise ValueError("invalid_location")
    return value


def _object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def _shape(value, depth=0, budget=None):
    if budget is None:
        budget = [30000]
    budget[0] -= 1
    if depth > 24 or budget[0] < 0:
        raise ValueError("oversized_structure")
    if isinstance(value, dict):
        if len(value) > 64:
            raise ValueError("excessive_fields")
        for key, child in value.items():
            if len(key) > 128:
                raise ValueError("oversized_key")
            _shape(child, depth + 1, budget)
    elif isinstance(value, list):
        if len(value) > 4096:
            raise ValueError("excessive_list")
        for child in value:
            _shape(child, depth + 1, budget)
    elif isinstance(value, str) and len(value) > 65536:
        raise ValueError("oversized_field")


def _integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("invalid_integer")
    return value


def _location(location, files):
    if not isinstance(location, dict) or not {"file", "start_line"} <= location.keys():
        raise ValueError("invalid_location")
    path = _relative_path(location["file"], files)
    line = _integer(location["start_line"], 1)
    end = location.get("end_line")
    end = line if end is None else _integer(end, 1)
    line_count = max(1, len(files[path].splitlines()))
    if end < line or end > line_count:
        raise ValueError("invalid_line")
    return {"path": path, "line": line, "end_line": end}


def normalize_vendor(payload, files, version):
    """Return only bounded findings; any malformed/incomplete result is rejected."""
    if not isinstance(payload, bytes) or len(payload) > OUTPUT_LIMIT:
        raise ValueError("invalid_output")
    try:
        raw = json.loads(payload.decode("utf-8"), object_pairs_hook=_object_pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid_number")))
        _shape(raw)
        required = {"execution_successful", "components", "issues", "metadata",
                    "analysis_completeness", "suppressed_count", "suppressed"}
        if not isinstance(raw, dict) or not required <= raw.keys() or raw["execution_successful"] is not True:
            raise ValueError("missing_or_failed_execution")
        metadata = raw["metadata"]
        if not isinstance(metadata, dict) or metadata.get("skillspector_version") != version or metadata.get("llm_requested") is not False:
            raise ValueError("invalid_scanner_identity")
        complete = raw["analysis_completeness"]
        if not isinstance(complete, dict) or complete.get("is_complete") is not True or complete.get("execution_successful") is not True or complete.get("status") != "complete":
            raise ValueError("incomplete_analysis")
        for key in ("total_components", "scanned_components", "fully_inspected_files"):
            if _integer(complete.get(key)) != len(files):
                raise ValueError("incomplete_components")
        for key in ("partially_inspected_files", "entirely_uninspected_files"):
            if _integer(complete.get(key)) != 0:
                raise ValueError("incomplete_components")
        for key in ("ledger_exceptions", "scope_exclusions", "limitations"):
            if complete.get(key) != []:
                raise ValueError("unverified_scope")
        references = complete.get("references")
        if not isinstance(references, list) or len(references) > 512:
            raise ValueError("invalid_references")
        for reference in references:
            if not isinstance(reference, dict) or reference.get("status") != "resolved" or reference.get("disposition") != "analyzed":
                raise ValueError("unverified_reference")
            _location({"file": reference.get("source_path"), "start_line": reference.get("line")}, files)
            _relative_path(reference.get("target_path"), files)
        statuses = complete.get("analyzer_statuses")
        if not isinstance(statuses, list) or not 1 <= len(statuses) <= 128:
            raise ValueError("invalid_analyzers")
        analyzer_ids = set()
        static_completed = False
        for analyzer in statuses:
            if not isinstance(analyzer, dict) or analyzer.get("status") not in ("completed", "not_applicable", "disabled"):
                raise ValueError("incomplete_analyzer")
            identifier = analyzer.get("analyzer_id")
            if not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", identifier) or identifier in analyzer_ids:
                raise ValueError("invalid_analyzer")
            analyzer_ids.add(identifier)
            planned = _integer(analyzer.get("planned_work"))
            finished = _integer(analyzer.get("completed"))
            if planned != finished or (analyzer["status"] != "completed" and planned != 0):
                raise ValueError("incomplete_analyzer")
            if analyzer["status"] == "disabled" and identifier not in (
                    "meta_analyzer", "semantic_developer_intent", "semantic_quality_policy", "semantic_security_discovery"):
                raise ValueError("disabled_static_analyzer")
            if identifier.startswith("static_patterns_") and analyzer["status"] == "completed" and planned > 0:
                static_completed = True
            for key in ("partial", "skipped", "failed", "unaccounted"):
                if _integer(analyzer.get(key)) != 0:
                    raise ValueError("incomplete_analyzer")
        if not static_completed:
            raise ValueError("no_static_analysis")
        if _integer(raw["suppressed_count"]) != 0 or raw["suppressed"] != []:
            raise ValueError("suppressed_findings")
        components = raw["components"]
        if not isinstance(components, list) or len(components) != len(files):
            raise ValueError("invalid_components")
        paths = set()
        for component in components:
            if not isinstance(component, dict):
                raise ValueError("invalid_component")
            path = _relative_path(component.get("path"), files)
            if path in paths or _integer(component.get("size_bytes")) != len(files[path]):
                raise ValueError("invalid_component")
            _integer(component.get("lines"))
            paths.add(path)
        if paths != set(files):
            raise ValueError("incomplete_components")
        issues = raw["issues"]
        if not isinstance(issues, list) or len(issues) > 512:
            raise ValueError("invalid_findings")
        findings = []
        for issue in issues:
            if not isinstance(issue, dict):
                raise ValueError("invalid_finding")
            identifier, severity = issue.get("id"), issue.get("severity")
            if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier) or not isinstance(severity, str) or severity not in SEVERITIES[1:]:
                raise ValueError("invalid_finding")
            finding = {"id": identifier, "severity": severity, **_location(issue.get("location"), files)}
            occurrences = issue.get("occurrences", [])
            if not isinstance(occurrences, list) or len(occurrences) > 512:
                raise ValueError("invalid_occurrences")
            for occurrence in occurrences:
                _location(occurrence, files)
            findings.append(finding)
        findings.sort(key=lambda f: (f["path"], f["line"], f["id"], f["severity"]))
        return {"findings": findings}
    except (KeyError, TypeError, UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise ValueError("invalid_output") from exc


def _docker_executable():
    executable = shutil.which("docker")
    if not executable:
        raise ValueError("docker_unavailable")
    return str(pathlib.Path(executable).resolve(strict=True))


def _run_bounded(command, *, env, cwd, timeout=SCAN_TIMEOUT, output_limit=OUTPUT_LIMIT,
                 cancellation=None):
    """Stream both pipes under one byte budget; never retain diagnostic stderr."""
    output = bytearray()
    consumed = 0
    status = "finished"
    process = None
    deadline = time.monotonic() + timeout
    try:
        # Remember the process before a pending signal can unwind this scope.
        with cancellation.defer() if cancellation else contextlib.nullcontext():
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       stdin=subprocess.DEVNULL, env=env, cwd=cwd,
                                       close_fds=True, start_new_session=True)
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, True)
            selector.register(process.stderr, selectors.EVENT_READ, False)
            while selector.get_map():
                if cancellation:
                    cancellation.check()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    status = "timeout"
                    break
                for key, _ in selector.select(min(0.1, remaining)):
                    chunk = os.read(key.fileobj.fileno(), min(65536, output_limit - consumed + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    consumed += len(chunk)
                    if consumed > output_limit:
                        status = "output_limit"
                        break
                    if key.data:
                        output.extend(chunk)
                if status != "finished":
                    break
            if status == "finished":
                while process.poll() is None:
                    if cancellation:
                        cancellation.check()
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        status = "timeout"
                        break
                    try:
                        process.wait(timeout=min(0.1, remaining))
                    except subprocess.TimeoutExpired:
                        continue
    finally:
        with cancellation.defer(raise_pending=False) if cancellation else contextlib.nullcontext():
            if process is not None:
                try:
                    # Kill surviving descendants even when the group leader exited.
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=0.5)
                finally:
                    process.stdout.close()
                    process.stderr.close()
    return status, process.returncode, bytes(output)


def _workspace_path(workspace):
    original = pathlib.Path(_plain_path(workspace)).absolute()
    if original.is_symlink():
        raise ValueError("unsafe_workspace")
    resolved = original.resolve(strict=True)
    _plain_path(resolved)
    info = resolved.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise ValueError("unsafe_workspace")
    for parent in resolved.parents:
        info = parent.stat()
        if info.st_uid not in (0, os.getuid()) or (info.st_mode & 0o022 and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)):
            raise ValueError("unsafe_workspace_parent")
    return resolved


def _report(image, version):
    return {"schema_version": 1, "engine": "nvidia-skillspector", "status": "INCOMPLETE",
            "severity": "UNKNOWN", "decision": "incomplete", "trust": "unverified",
            "bindings": {"image": image if isinstance(image, str) and IMAGE_PATTERN.fullmatch(image) else None,
                         "scanner": "skillspector", "scanner_version": version if isinstance(version, str) and VERSION_PATTERN.fullmatch(version) else None,
                         "adapter_version": ADAPTER_VERSION,
                         "adapter_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                         "bundle_sha256": None, "package_kind": "skill"},
            "coverage": {"mode": "static-lexical", "complete": False, "vendor_complete": False,
                         "files": 0, "reasons": [],
                         "limitations": ["No LLM or runtime behavior analysis.",
                                         "Static findings can miss threats or flag benign text.",
                                         "Vendor output is unverified metadata; no execution authority is granted."]},
            "findings": [], "reason": "not_started"}


def scan_package(package, workspace, image, version, docker_host=None):
    """Scan a safe snapshot with an explicit immutable, already-local image."""
    report = _report(image, version)
    stage = None
    container = None
    prefix = None
    cancellation = _CancellationGuard()
    env = {"PATH": SAFE_PATH}
    try:
        cancellation.install()
        if not isinstance(image, str) or not IMAGE_PATTERN.fullmatch(image) or not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
            raise ValueError("invalid_configuration")
        host = docker_host or "unix:///var/run/docker.sock"
        if not isinstance(host, str) or not host.startswith("unix:///"):
            raise ValueError("invalid_docker_host")
        socket_path = _plain_path(host[len("unix://"):])
        if str(pathlib.PurePosixPath(socket_path)) != socket_path or ".." in pathlib.PurePosixPath(socket_path).parts or any(c in socket_path for c in "?#"):
            raise ValueError("invalid_docker_host")
        approved_workspace = _workspace_path(workspace)
        _plain_path(package)
        files, excluded = snapshot_package(package, kind="skill")
        cancellation.check()
        observed_digest = _digest(files)
        report["bindings"]["observed_bundle_sha256"] = observed_digest
        report["bindings"]["bundle_sha256"] = None if excluded else observed_digest
        report["coverage"]["files"] = len(files)
        if excluded or "SKILL.md" not in files:
            raise ValueError("excluded_or_missing_resources")
        for path, content in files.items():
            if _relative_path(path, files) != path or not isinstance(content, bytes):
                raise ValueError("invalid_snapshot")
        builtin = _load_inventory().load_security_module().analyze_bundle(files, kind="skill")
        cancellation.check()
        report["bindings"]["coverage_analyzer_sha256"] = builtin["identity_sha256"]
        reasons = {item["reason"] if item["reason"] in COVERAGE_REASONS else "builtin-coverage-incomplete"
                   for item in builtin["coverage"]["reasons"]}
        if builtin["coverage"]["status"] != "complete" and not reasons:
            reasons.add("builtin-coverage-incomplete")
        report["coverage"]["reasons"] = sorted(reasons)
        executable = _docker_executable()
        with cancellation.defer():
            stage = pathlib.Path(tempfile.mkdtemp(prefix="ceo-nvidia-", dir=approved_workspace))
        snapshot = stage / "snapshot"
        snapshot.mkdir(mode=0o755)
        config = stage / "docker-config"
        config.mkdir(mode=0o700)
        (config / "config.json").write_text("{}", encoding="utf-8")
        (config / "config.json").chmod(0o600)
        for path, content in files.items():
            cancellation.check()
            destination = snapshot / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            destination.chmod(0o444)
        for directory, _, _ in os.walk(snapshot, topdown=False):
            pathlib.Path(directory).chmod(0o555)
        container = "ceo-nvidia-" + uuid.uuid4().hex
        prefix = [executable, "--config", str(config), "--host", host]
        uid, gid = (os.getuid(), os.getgid()) if os.getuid() else (65534, 65534)
        command = prefix + ["run", "--pull", "never", "--name", container,
                            "--network", "none", "--read-only", "--user", f"{uid}:{gid}",
                            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                            "--pids-limit", "128", "--memory", "1536m", "--cpus", "2",
                            "--tmpfs", "/tmp:rw,nosuid,noexec,size=256m", "--workdir", "/tmp",
                            "--env", "HOME=/tmp", "--env", "PYTHONDONTWRITEBYTECODE=1",
                            "--mount", f"type=bind,src={snapshot},dst=/snapshot,readonly",
                            "--entrypoint", "python", image, "-c", RUNNER, version,
                            "scan", "/snapshot", "--no-llm", "--format", "json"]
        status, exitcode, payload = _run_bounded(command, env=env, cwd=stage,
                                                cancellation=cancellation)
        cancellation.check()
        if status != "finished":
            report["reason"] = status if status in ("timeout", "output_limit") else "execution_failed"
        elif exitcode != 0:
            report["reason"] = "version_mismatch" if exitcode == 78 else "execution_failed"
        else:
            result = normalize_vendor(payload, files, version)
            # Verify the private copy still equals the bytes bound to this result.
            copied, copy_excluded = snapshot_package(snapshot, kind="skill")
            if copy_excluded or copied != files:
                raise ValueError("snapshot_changed")
            report.update(result)
            report["severity"] = max((f["severity"] for f in result["findings"]),
                                      key=SEVERITIES.index, default="NONE")
            report["status"] = "INCOMPLETE" if reasons else "COMPLETE"
            report["coverage"]["vendor_complete"] = True
            report["coverage"]["complete"] = not reasons
            report["decision"] = "incomplete" if reasons else "review-required" if result["findings"] else "no-findings"
            report["reason"] = "coverage_incomplete" if reasons else "completed"
    except _Cancelled:
        report["reason"] = "cancelled"
    except (OSError, ValueError, TypeError, RuntimeError, subprocess.SubprocessError):
        # Exception strings can contain package text, paths or vendor diagnostics.
        report["reason"] = "invalid_input_or_output"
    finally:
        cancellation.cleaning = True
        try:
            if container and prefix:
                try:
                    cleanup_status, cleanup_code, _ = _run_bounded(
                        prefix + ["rm", "--force", container], env=env, cwd=stage,
                        timeout=3, output_limit=16384, cancellation=cancellation)
                    if cleanup_status != "finished" or cleanup_code != 0:
                        raise ValueError("cleanup_failed")
                except (OSError, ValueError, subprocess.SubprocessError):
                    report.update(status="INCOMPLETE", decision="incomplete", reason="cleanup_failed")
                    report["coverage"]["complete"] = False
            if stage:
                try:
                    for directory, _, _ in os.walk(stage, topdown=False):
                        pathlib.Path(directory).chmod(0o700)
                    shutil.rmtree(stage)
                except OSError:
                    report.update(status="INCOMPLETE", decision="incomplete", reason="cleanup_failed")
                    report["coverage"]["complete"] = False
        finally:
            cancellation.restore()
        if cancellation.number is not None:
            report.update(status="INCOMPLETE", decision="incomplete", cancelled_signal=cancellation.number)
            report["coverage"]["complete"] = False
            if report["reason"] != "cleanup_failed":
                report["reason"] = "cancelled"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=pathlib.Path)
    parser.add_argument("--workspace", required=True, type=pathlib.Path)
    parser.add_argument("--image", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--docker-host")
    args = parser.parse_args(argv)
    result = scan_package(args.package, args.workspace, args.image, args.version, args.docker_host)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    if "cancelled_signal" in result:
        return 128 + result["cancelled_signal"]
    return 0 if result["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())

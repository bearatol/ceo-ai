"""Run fixed scanner entrypoints on inert fixtures in restricted containers."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import time
import uuid

LIMIT = 256 * 1024
ENGINES = {"cisco": ("site",), "nvidia": ("site", "source/src"), "agentverus": ("node_modules",)}
IMAGE = re.compile(r"[a-z0-9][a-z0-9./:_-]*@sha256:[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9-]{0,80}\Z")


def checked_path(root, relative):
    """Refuse traversal and symlinks, including a symlink supplied as root."""
    if not isinstance(relative, str) or not relative or "\x00" in relative:
        raise ValueError("invalid relative path")
    path = Path(relative)
    if path.is_absolute() or any(part in ("", ".", "..") for part in relative.split("/")):
        raise ValueError("path must remain beneath the benchmark root")
    current = Path(root)
    if current.is_symlink():
        raise ValueError("symlink root refused")
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("symlink path refused")
    return current


def regular_tree(path):
    """Check every mounted entry, without following links or special files."""
    entries = [path]
    while entries:
        entry = entries.pop()
        mode = entry.lstat().st_mode
        if stat.S_ISDIR(mode):
            entries.extend(entry.iterdir())
        elif not stat.S_ISREG(mode):
            raise ValueError("mounted tree contains a symlink or special file")


def read_manifest(root, name):
    path = checked_path(root, name)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("manifest must be a regular file")
    with path.open("rb") as stream:
        content = stream.read(LIMIT + 1)
    if len(content) > LIMIT:
        raise ValueError("manifest exceeds 256 KiB")
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    return data


def load_inputs(root):
    engines = read_manifest(root, "engines.json").get("engines")
    document = read_manifest(root, "cases.json")
    skills, probes = document.get("skill_cases"), document.get("format_probes")
    if not isinstance(engines, list) or not engines or not isinstance(skills, list) or not isinstance(probes, list):
        raise ValueError("invalid engines or cases manifest")
    seen = set()
    for engine in engines:
        if not isinstance(engine, dict) or engine.get("id") not in ENGINES:
            raise ValueError("unknown engine")
        name = engine["id"]
        if name in seen or not isinstance(engine.get("image"), str) or not IMAGE.fullmatch(engine["image"]):
            raise ValueError("engine requires a unique ID and digest-pinned image")
        seen.add(name)
        engine_root = checked_path(root, f".runtime/.venv/{name}")
        regular_tree(engine_root)
        for required in ENGINES[name]:
            if not checked_path(root, f".runtime/.venv/{name}/{required}").is_dir():
                raise ValueError("engine payload is incomplete")
    fixtures = checked_path(root, "fixtures")
    if not fixtures.is_dir():
        raise ValueError("fixtures directory missing")
    regular_tree(fixtures)
    cases, seen = [], set()
    for kind, records in (("skill", skills), ("agent_format_probe", probes)):
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not IDENTIFIER.fullmatch(record["id"]):
                raise ValueError("invalid case ID")
            path = checked_path(root, record.get("path"))
            if record["id"] in seen or not record["path"].startswith("fixtures/") or not path.exists():
                raise ValueError("case must have a unique ID and existing fixture path")
            if (kind == "skill" and not (path / "SKILL.md").is_file()) or (kind != "skill" and not path.is_file()):
                raise ValueError("incorrect case input format")
            seen.add(record["id"])
            cases.append(dict(record, case_kind=kind))
    return engines, cases


def run_bounded(args, *, timeout=30, max_output=2 * 1024 * 1024, env=None):
    """Read both pipes incrementally; bound their combined bytes and wall time."""
    started = time.monotonic()
    output = {"stdout": bytearray(), "stderr": bytearray()}
    status, total = "execution_finished", 0
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL, start_new_session=True,
                               env=env if env is not None else {"PATH": os.defpath})
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map() or process.poll() is None:
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    status = "timeout"
                    break
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fileobj.fileno(), min(65536, max_output - total + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    allowed = min(len(chunk), max_output - total)
                    output[key.data].extend(chunk[:allowed])
                    total += allowed
                    if allowed != len(chunk):
                        status = "output_limit"
                        break
                if status != "execution_finished":
                    break
    finally:
        if process.poll() is None or status != "execution_finished":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=1)
        process.stdout.close()
        process.stderr.close()
    return {"status": status, "exitcode": process.returncode,
            "duration_seconds": round(time.monotonic() - started, 4),
            **{name: bytes(data) for name, data in output.items()}}


def command(root, docker_prefix, engine, case, container):
    name = engine["id"]
    target = "/" + case["path"]
    scanner = {
        "cisco": ["python", "/engine/site/bin/skill-scanner", "scan", target, "--format", "json"],
        "nvidia": ["python", "-c", "from skillspector.cli import app; app()", "scan", target, "--no-llm", "--format", "json"],
        "agentverus": ["node", "/engine/node_modules/agentverus-scanner/dist/scanner/cli.js", "scan", target, "--json"],
    }[name]
    pythonpath = "/engine/site:/engine/source/src" if name == "nvidia" else "/engine/site"
    return docker_prefix + ["run", "--rm", "--pull", "never", "--name", container,
        "--network", "none", "--read-only", "--user", f"{os.getuid()}:{os.getgid()}",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "128",
        "--memory", "1536m", "--cpus", "2", "--tmpfs", "/tmp:rw,nosuid,noexec,size=256m",
        "--env", "HOME=/tmp", "--env", f"PYTHONPATH={pythonpath}",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--mount", f"type=bind,src={checked_path(root, '.runtime/.venv/' + name)},dst=/engine,readonly",
        "--mount", f"type=bind,src={checked_path(root, 'fixtures')},dst=/fixtures,readonly",
        "--entrypoint", scanner[0], engine["image"]] + scanner[1:]


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            result.update(chunk)
    return result.hexdigest()


def interrupted(signum, frame):
    raise KeyboardInterrupt(f"interrupted by signal {signum}")


def main(argv=None):
    # A terminated client must still reach the per-container cleanup finally.
    for signum in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker-host", required=True, help="Explicit local unix:// Docker socket")
    parser.add_argument("--engine", action="append", choices=sorted(ENGINES))
    parser.add_argument("--case", action="append")
    parser.add_argument("--output", required=True, help="New JSON file beneath results/")
    options = parser.parse_args(argv)
    root = Path(__file__).absolute().parent
    if not options.docker_host.startswith("unix:///") or "\x00" in options.docker_host:
        parser.error("--docker-host must name a local absolute Unix socket")
    output = checked_path(root, options.output)
    if not options.output.startswith("results/") or output.exists():
        raise ValueError("output must be a new file beneath results/")
    engines, cases = load_inputs(root)
    selected_engines = set(options.engine or [item["id"] for item in engines])
    selected_cases = set(options.case or [item["id"] for item in cases])
    if selected_engines - {item["id"] for item in engines} or selected_cases - {item["id"] for item in cases}:
        raise ValueError("selection includes an unavailable engine or unknown case")
    config = checked_path(root, ".runtime/docker-config")
    config.mkdir(parents=True, exist_ok=True)
    if any(config.iterdir()):
        raise ValueError("Docker config directory must be empty")
    docker = shutil.which("docker")
    if docker is None:
        raise ValueError("Docker CLI not found")
    prefix = [docker, "--config", str(config), "--host", options.docker_host]
    run_id = uuid.uuid4().hex
    raw_root = checked_path(root, ".runtime/outputs/" + run_id)
    raw_root.mkdir(parents=True)
    fixture_hashes = {str(p.relative_to(root)): digest(p) for p in sorted((root / "fixtures").rglob("*")) if p.is_file()}
    report = {"schema_version": 1, "run_id": run_id,
              "cases_sha256": digest(root / "cases.json"), "engines_sha256": digest(root / "engines.json"),
              "fixtures_sha256": fixture_hashes, "runs": []}
    for engine in engines:
        if engine["id"] not in selected_engines:
            continue
        for case in cases:
            if case["id"] not in selected_cases:
                continue
            container = "ceo-scan-" + uuid.uuid4().hex
            args = command(root, prefix, engine, case, container)
            cleanup = None
            try:
                # Leave time for bounded cleanup within a 30-second outer call.
                result = run_bounded(args, timeout=25)
            finally:
                cleanup = run_bounded(prefix + ["rm", "-f", container], timeout=4, max_output=16384)
            record = {"engine": engine["id"], "case": case["id"], "case_kind": case["case_kind"],
                      "args": args, "cleanup_status": cleanup["status"],
                      "cleanup_exitcode": cleanup["exitcode"], **result}
            for stream in ("stdout", "stderr"):
                data = record.pop(stream)
                filename = raw_root / f"{engine['id']}-{case['id']}.{stream}"
                with filename.open("xb") as destination:
                    destination.write(data)
                record[stream + "_path"] = str(filename.relative_to(root))
                record[stream + "_bytes"] = len(data)
            try:
                parsed = json.loads(result["stdout"])
                if not isinstance(parsed, dict):
                    raise ValueError("scanner output is not a JSON object")
                record["parsed_output"] = parsed
            except (ValueError, UnicodeError, RecursionError) as error:
                record["json_parse_error"] = type(error).__name__
            report["runs"].append(record)
            print(f"{engine['id']} {case['id']}: {result['status']} (exit {result['exitcode']})", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with checked_path(root, options.output).open("x", encoding="utf-8") as destination:
        json.dump(report, destination, ensure_ascii=True, indent=2)
        destination.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify and run the CEO AI inventory helper from its pinned GitHub release."""

import argparse
import hashlib
import io
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener
import zipfile


REPOSITORY = "github.com/bearatol/ceo-ai"
TAG = "v0.10.2"
ASSET = "ceo-ai-inventory-0.10.2.zip"
URL = f"https://{REPOSITORY}/releases/download/{TAG}/{ASSET}"
SHA256 = "02ae12d0b2e94c8c987cbdbf286028e1ba5972ec29f0b7bbbc5b6a450a99d751"
DOWNLOAD_LIMIT = 128 * 1024
UNPACK_LIMIT = 256 * 1024
MEMBERS = frozenset({"LICENSE", "ceo_inventory.py", "ceo_inventory_windows.py", "ceo_security.py"})


class ReleaseRedirects(HTTPRedirectHandler):
    max_redirections = 2

    def redirect_request(self, request, response, code, message, headers, new_url):
        target = urlsplit(new_url)
        if target.scheme != "https" or target.netloc != "release-assets.githubusercontent.com":
            raise ValueError("Unexpected release download redirect")
        return super().redirect_request(request, response, code, message, headers, new_url)


def download():
    deadline = time.monotonic() + 30
    opener = build_opener(ProxyHandler({}), ReleaseRedirects())
    data = bytearray()
    with opener.open(URL, timeout=10) as response:
        while time.monotonic() < deadline:
            chunk = response.read1(min(16 * 1024, DOWNLOAD_LIMIT + 1 - len(data)))
            if time.monotonic() >= deadline:
                break
            if not chunk:
                return bytes(data)
            data.extend(chunk)
            if len(data) > DOWNLOAD_LIMIT:
                raise ValueError("Release archive exceeds the download size limit")
    raise TimeoutError("Release download exceeded its deadline")


def stage_verified_members(payload, directory):
    with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
        entries = bundle.infolist()
        if len(entries) != len(MEMBERS) or {entry.filename for entry in entries} != MEMBERS:
            raise ValueError("Unexpected release archive members")
        if sum(entry.file_size for entry in entries) > UNPACK_LIMIT:
            raise ValueError("Release archive exceeds the unpacked size limit")
        for entry in entries:
            if not stat.S_ISREG(entry.external_attr >> 16) or entry.flag_bits & 1:
                raise ValueError("Release archive contains a nonregular or encrypted member")
        for entry in entries:
            with (directory / entry.filename).open("xb") as destination:
                destination.write(bundle.read(entry))


def run(gh, home, refresh=False):
    if not gh.is_absolute() or gh.name.lower() not in {"gh", "gh.exe"} or not gh.is_file():
        raise ValueError("Use the absolute path of the trusted GitHub CLI")
    if not home.is_absolute() or not home.is_dir():
        raise ValueError("Use an existing, explicitly approved absolute inventory root")
    payload = download()
    if hashlib.sha256(payload).hexdigest() != SHA256:
        raise ValueError("Release archive SHA-256 mismatch")

    with tempfile.TemporaryDirectory(prefix="ceo-ai-inventory-") as temporary:
        directory = Path(temporary).resolve()
        archive = directory / ASSET
        archive.write_bytes(payload)
        subprocess.run(
            [str(gh), "release", "verify-asset", TAG, str(archive), "--repo", REPOSITORY],
            cwd=directory, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            timeout=25, check=True,
        )
        if archive.read_bytes() != payload:
            raise ValueError("Release archive changed during attestation verification")
        stage_verified_members(payload, directory)
        command = [
            sys.executable, "-I", "-B", str(directory / "ceo_inventory.py"),
            "--home", str(home),
        ]
        if refresh:
            command.append("--refresh")
        environment = {name: os.environ[name] for name in ("SYSTEMROOT", "WINDIR", "TMPDIR", "TEMP", "TMP")
                       if name in os.environ}
        subprocess.run(command, cwd=directory, env=environment,
                       stdin=subprocess.DEVNULL, timeout=25, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gh", required=True, type=Path, help="Absolute path of trusted GitHub CLI")
    parser.add_argument("--home", required=True, type=Path, help="Explicitly approved absolute inventory root")
    parser.add_argument("--refresh", action="store_true", help="Write the owned cache after explicit approval")
    args = parser.parse_args()
    try:
        run(args.gh, args.home, args.refresh)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print(f"Inventory unavailable: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

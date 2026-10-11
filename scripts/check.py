#!/usr/bin/env python3
"""Check this checkout's catalog, profile, schemas, and component files."""
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[1] / ".apm/skills/ceo-ai"
sys.path.insert(0, str(ROOT / "scripts"))
from catalog import validate_catalog
from install import package


def main():
    try:
        package(ROOT)
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        errors = validate_catalog(catalog, ROOT)
        profile = (ROOT / "profiles/core.profile").read_text().splitlines()
        identities = [item["id"] for item in catalog["components"]]
        if set(profile) != set(identities) or len(profile) != len(set(profile)):
            errors.append("core profile must list each bundled component once")
        for path in [ROOT / "catalog.schema.json", *sorted((ROOT / "orchestration").rglob("*.json"))]:
            json.loads(path.read_text(encoding="utf-8"))
        if errors:
            print("\n".join("error: " + error for error in errors), file=sys.stderr)
            return 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Doctor passed: {len(identities)} components; catalog, profile, and JSON files valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

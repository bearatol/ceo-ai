#!/usr/bin/env python3
"""Validate the standalone component catalog without executing component code."""

import argparse
import json
import pathlib
import re
import sys

# Importing sibling modules must not leave bytecode caches in the source
# tree; installers copy component directories verbatim.
sys.dont_write_bytecode = True


ID_RE = re.compile(r"^[a-z]+:[a-z0-9-]+$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
CATALOG_SCHEMA_REFERENCE = "./catalog.schema.json"
CATALOG_FIELDS = {"$schema", "schema_version", "ecosystem_version", "language", "license", "components"}
COMPONENT_FIELDS = {
    "id", "type", "name", "description", "profile", "origin", "license", "path", "tags",
    "capabilities", "access", "skill_policy", "recommended_skills", "delegates", "requires",
}
MAX_DEPENDENCY_DEPTH = 64
COMPONENT_TYPES = {"skill", "agent", "rule", "model", "orchestration", "tool"}
ORIGINS = {"original", "referenced", "vendored"}
ACCESS_LEVELS = {"read-only", "workspace-write"}
SKILL_POLICIES = {"self-select", "self-select-restricted"}


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def string_list(value, *, minimum=0):
    return (
        isinstance(value, list)
        and len(value) >= minimum
        and all(isinstance(item, str) for item in value)
    )


def dependency_cycles(dependencies):
    """Report every component that depends on itself through other components."""
    errors = []
    state = {}

    def walk(node, depth):
        if depth > MAX_DEPENDENCY_DEPTH:
            errors.append(f"dependency chain from {node} is too deep")
            return
        if state.get(node) == "done":
            return
        if state.get(node) == "open":
            errors.append(f"dependency cycle through {node}")
            return
        state[node] = "open"
        for needed in dependencies.get(node, []):
            walk(needed, depth + 1)
        state[node] = "done"

    for node in sorted(dependencies):
        walk(node, 0)
    return sorted(set(errors))


def validate_catalog(catalog, root=None):
    errors = []
    if not isinstance(catalog, dict):
        return ["catalog must be an object"]
    unknown_fields = set(catalog) - CATALOG_FIELDS
    if unknown_fields:
        errors.append("catalog has unexpected fields: " + ", ".join(sorted(unknown_fields)))
    for field in ("schema_version", "ecosystem_version", "language", "license", "components"):
        if field not in catalog:
            errors.append(f"catalog missing {field}")
    if catalog.get("$schema") != CATALOG_SCHEMA_REFERENCE:
        errors.append(f"$schema must be {CATALOG_SCHEMA_REFERENCE}")
    if type(catalog.get("schema_version")) is not int or catalog.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if not isinstance(catalog.get("ecosystem_version"), str) or not VERSION_RE.fullmatch(catalog["ecosystem_version"]):
        errors.append("ecosystem_version must be a semantic version")
    if catalog.get("language") != "en":
        errors.append("language must be en")
    if not isinstance(catalog.get("license"), str):
        errors.append("license must be a string")
    components = catalog.get("components")
    if not isinstance(components, list) or not components:
        errors.append("components must be a non-empty array")
        components = []
    seen = set()
    component_by_id = {}
    root_path = pathlib.Path(root).resolve() if root else None
    for index, item in enumerate(components):
        label = f"component[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        unknown_fields = set(item) - COMPONENT_FIELDS
        if unknown_fields:
            errors.append(f"{label} has unexpected fields: " + ", ".join(sorted(unknown_fields)))
        for field in ("id", "type", "name", "profile", "origin", "license", "path", "tags"):
            if field not in item:
                errors.append(f"{label} missing {field}")
        component_id = item.get("id")
        if not isinstance(component_id, str) or not ID_RE.fullmatch(component_id):
            errors.append(f"{label} has an invalid id")
            component_id = None
        if component_id in seen:
            errors.append(f"duplicate component id: {component_id}")
        if component_id:
            seen.add(component_id)
            component_by_id[component_id] = item
        component_type = item.get("type")
        if not isinstance(component_type, str) or component_type not in COMPONENT_TYPES:
            errors.append(f"{label} has an invalid type")
        name = item.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(f"{label} has an invalid name")
        if component_id and isinstance(component_type, str) and isinstance(name, str):
            if component_id != f"{component_type}:{name}":
                errors.append(f"{label} id must match type and name")
        if not string_list(item.get("profile"), minimum=1):
            errors.append(f"{label} profile must be a non-empty string array")
        origin = item.get("origin")
        if not isinstance(origin, str) or origin not in ORIGINS:
            errors.append(f"{label} has an invalid origin")
        if not isinstance(item.get("license"), str):
            errors.append(f"{label} license must be a string")
        path = item.get("path")
        if not isinstance(path, str) or not path:
            errors.append(f"{label} path must be a non-empty string")
        if not string_list(item.get("tags"), minimum=1):
            errors.append(f"{label} tags must be a non-empty string array")
        for field in ("description", "license", "path"):
            if field in item and not isinstance(item[field], str):
                errors.append(f"{label} {field} must be a string")
        for field in ("capabilities", "recommended_skills"):
            if field in item and not string_list(item[field]):
                errors.append(f"{label} {field} must be a string array")
        if "access" in item:
            access = item["access"]
            if not isinstance(access, str) or access not in ACCESS_LEVELS:
                errors.append(f"{label} has an invalid access level")
        if "skill_policy" in item:
            skill_policy = item["skill_policy"]
            if not isinstance(skill_policy, str) or skill_policy not in SKILL_POLICIES:
                errors.append(f"{label} has an invalid skill policy")
        if "delegates" in item and type(item["delegates"]) is not bool:
            errors.append(f"{label} delegates must be a boolean")
        if component_type == "agent":
            for field in ("description", "capabilities", "access", "skill_policy", "recommended_skills", "delegates"):
                if field not in item:
                    errors.append(f"{label} missing {field}")
        if root_path and isinstance(path, str) and path:
            source = (root_path / path).resolve()
            try:
                source.relative_to(root_path)
            except ValueError:
                errors.append(f"{label} path escapes repository root")
            else:
                if not source.exists():
                    errors.append(f"{label} path does not exist: {source}")
    dependencies = {}
    for item in components:
        if not isinstance(item, dict):
            continue
        component_id = item.get("id", "component")
        requires = item.get("requires")
        if requires is None:
            pass
        elif not isinstance(requires, list) or len(requires) != len(set(map(str, requires))):
            errors.append(f"{component_id} has an invalid requires list")
        else:
            resolved = []
            for needed in requires:
                if not isinstance(needed, str) or not ID_RE.fullmatch(needed):
                    errors.append(f"{component_id} requires an invalid id")
                elif needed == component_id:
                    errors.append(f"{component_id} requires itself")
                elif needed not in component_by_id:
                    errors.append(f"{component_id} requires missing {needed}")
                else:
                    resolved.append(needed)
            dependencies[component_id] = resolved
    errors.extend(dependency_cycles(dependencies))
    for item in components:
        if not isinstance(item, dict):
            continue
        component_id = item.get("id", "component")
        skills = item.get("recommended_skills", [])
        if not isinstance(skills, list):
            continue
        for skill in skills:
            if not isinstance(skill, str):
                errors.append(f"{component_id} recommends an invalid skill identifier")
                continue
            target = component_by_id.get(skill)
            if target is None:
                errors.append(f"{component_id} recommends missing {skill}")
            elif target.get("type") != "skill":
                errors.append(f"{component_id} recommends non-skill {skill}")
    return errors


def catalog_path(root):
    """A pack checkout keeps it under catalog/; an installed runtime at the root."""
    root = pathlib.Path(root)
    packaged = root / "catalog" / "catalog.json"
    return packaged if packaged.is_file() else root / "catalog.json"


def load_catalog(root):
    """Read the catalog a pack publishes. The file is untrusted input."""
    path = catalog_path(root)
    if not path.is_file():
        fail(f"no catalog at {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read the catalog: {exc}")


def cmd_validate(args):
    catalog = load_catalog(args.pack)
    errors = validate_catalog(catalog, args.pack)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Catalog valid.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", required=True, help="Explicit checkout or ecosystem root")
    parser.add_argument("command", choices=["validate"])
    args = parser.parse_args(argv)
    try:
        return cmd_validate(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

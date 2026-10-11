#!/usr/bin/env python3
"""Regression tests for catalog selection and schema-equivalent validation."""

import copy
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
# Neither this process nor the commands it starts may leave bytecode caches
# in the source tree; installers copy component directories verbatim.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PACK = ROOT / ".apm/skills/ceo-ai"
TEAM_DIRECTORY = PACK / "scripts"
sys.path.insert(0, str(TEAM_DIRECTORY))
import catalog as team  # noqa: E402


def canonical_catalog():
    return json.loads((PACK / "catalog.json").read_text(encoding="utf-8"))


class CatalogValidationTests(unittest.TestCase):
    def assert_invalid(self, catalog):
        self.assertTrue(team.validate_catalog(catalog, PACK))

    def test_canonical_catalog_is_valid(self):
        self.assertEqual(team.validate_catalog(canonical_catalog(), PACK), [])

    def test_rejects_untrusted_schema_reference(self):
        catalog = canonical_catalog()
        catalog["$schema"] = "https://example.invalid/catalog.schema.json"
        self.assert_invalid(catalog)

    def test_rejects_missing_required_component_metadata(self):
        catalog = canonical_catalog()
        del catalog["components"][0]["profile"]
        self.assert_invalid(catalog)

    def test_rejects_unexpected_and_mistyped_component_metadata(self):
        catalog = canonical_catalog()
        catalog["components"][0]["unexpected"] = True
        catalog["components"][0]["tags"] = "safety"
        self.assert_invalid(catalog)

    def test_rejects_unhashable_enum_values_without_crashing(self):
        catalog = canonical_catalog()
        catalog["components"][0]["type"] = ["skill"]
        catalog["components"][0]["origin"] = ["original"]
        self.assert_invalid(catalog)

    def test_rejects_escaping_component_path(self):
        catalog = canonical_catalog()
        catalog["components"][0]["path"] = "../README.md"
        self.assert_invalid(catalog)

    def test_rejects_non_skill_recommendations(self):
        catalog = canonical_catalog()
        catalog["components"][1]["recommended_skills"] = ["agent:ceo"]
        self.assert_invalid(catalog)

    def test_rejects_unhashable_skill_recommendations(self):
        catalog = canonical_catalog()
        catalog["components"][1]["recommended_skills"] = [{}]
        self.assert_invalid(catalog)

    def test_repository_validation_uses_the_canonical_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = pathlib.Path(temporary)
            (home / "catalog.json").write_text('{"schema_version": 1}', encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(TEAM_DIRECTORY / "catalog.py"),
                    "--pack",
                    str(PACK),
                    "validate",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

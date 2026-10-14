"""Offline build of the exact reviewed manifest, with provenance for this output."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import tomllib

BASE = 'python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258'
COMMIT = 'c7958a3268d9498644b22edb75d0f051bbc8cbfc'
SOURCE_SHA = 'ea6f4e5d40d9ba0d73a801515772962f1c7cc8ab8932a4de41a573b46411070d'
MANIFEST_SHA = '6813f5c046b9ded18dd7ef5fe81eb39ae5d84743ec69a06ade07507170e3db9d'


def main():
    if platform.system() != 'Linux' or platform.machine() != 'aarch64' or sys.version_info[:2] != (3, 12):
        raise SystemExit('This lock supports Linux aarch64 / CPython 3.12 only')
    source = Path('/build/source')
    manifest = (source / 'pyproject.toml').read_bytes()
    if hashlib.sha256(manifest).hexdigest() != MANIFEST_SHA:
        raise SystemExit('Reviewed build manifest changed')
    config = tomllib.loads(manifest.decode())
    if config['build-system'] != {'requires': ['hatchling'], 'build-backend': 'hatchling.build'}:
        raise SystemExit('Unexpected build backend')
    sys.path.insert(0, '/engine/site')
    if importlib.metadata.version('hatchling') != '1.31.0':
        raise SystemExit('Unexpected Hatchling version')
    from hatchling.build import build_wheel
    os.chdir(source)
    wheel_dir = Path('/build/wheels')
    wheel_dir.mkdir()
    wheel_name = build_wheel(str(wheel_dir))
    if wheel_name != 'skillspector-2.12.0-py3-none-any.whl':
        raise SystemExit('Unexpected root wheel name')
    wheel = wheel_dir / wheel_name
    provenance = {
        'schema_version': 1,
        'source_url': f'https://codeload.github.com/NVIDIA/SkillSpector/tar.gz/{COMMIT}',
        'source_commit': COMMIT, 'source_sha256': SOURCE_SHA,
        'manifest_sha256': MANIFEST_SHA, 'base_image': BASE,
        'dependency_lock_sha256': hashlib.sha256(Path('/build/requirements.lock').read_bytes()).hexdigest(),
        'python': platform.python_version(), 'architecture': platform.machine(),
        'scanner_version': '2.12.0', 'build_backend': 'hatchling==1.31.0',
        'root_wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
        'note': 'Root wheel hash records this build; it is not the historical benchmark wheel hash.',
    }
    Path('/engine/provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


if __name__ == '__main__':
    main()

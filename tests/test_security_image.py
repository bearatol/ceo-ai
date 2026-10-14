import gzip
import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('image_extract', ROOT / 'tools/security-image/extract_source.py')
extractor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor)


class ImageSourceTests(unittest.TestCase):
    def archive(self, entries, tail=b''):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as tar:
            for name, content, kind in entries:
                info = tarfile.TarInfo(name)
                info.type = kind
                info.size = len(content) if kind == tarfile.REGTYPE else 0
                if kind == tarfile.SYMTYPE:
                    info.linkname = '/tmp/escape'
                tar.addfile(info, io.BytesIO(content))
        return gzip.compress(stream.getvalue() + tail)

    def run_extract(self, entries, tail=b'', expected=None, existing=False):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'source.tar.gz'
            data = self.archive(entries, tail)
            archive.write_bytes(data)
            destination = Path(tmp) / 'source'
            if existing:
                destination.mkdir()
                (destination / 'keep').write_text('untouched')
            try:
                extractor.extract(archive, destination, expected or hashlib.sha256(data).hexdigest())
                return {p.relative_to(destination).as_posix(): p.read_bytes() for p in destination.rglob('*') if p.is_file()}
            except ValueError:
                self.assertEqual(list(destination.iterdir()) if existing else destination.exists(), [destination / 'keep'] if existing else False)
                raise

    def test_allowlist(self):
        p = extractor.PREFIX
        result = self.run_extract([(p+'/src/skillspector/a.py', b'pass', tarfile.REGTYPE), (p+'/README.md', b'read', tarfile.REGTYPE), (p+'/tests/ignore', b'ignored', tarfile.REGTYPE)])
        self.assertEqual(result, {'src/skillspector/a.py': b'pass', 'README.md': b'read'})

    def test_bad_paths_and_links(self):
        for name, kind in [('/absolute', tarfile.REGTYPE), (extractor.PREFIX+'/../bad', tarfile.REGTYPE), (extractor.PREFIX+'/src//bad', tarfile.REGTYPE), ('wrong/file', tarfile.REGTYPE), (extractor.PREFIX+'/ignored-link', tarfile.SYMTYPE)]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.run_extract([(name, b'x', kind)])

    def test_duplicate_and_collision(self):
        p = extractor.PREFIX + '/src/a'
        for entries in [[(p,b'x',tarfile.REGTYPE)] * 2, [(p,b'x',tarfile.REGTYPE),(p+'/b',b'x',tarfile.REGTYPE)]]:
            with self.assertRaises(ValueError):
                self.run_extract(entries)

    def test_large_file(self):
        with self.assertRaises(ValueError):
            self.run_extract([(extractor.PREFIX+'/ignored', b'x'*(extractor.MAX_FILE+1), tarfile.REGTYPE)])

    def test_gzip_bomb_after_tar(self):
        with self.assertRaises(ValueError):
            self.run_extract([], b'\0'*(extractor.MAX_EXPANDED+1))

    def test_no_overwrite(self):
        with self.assertRaises(ValueError):
            self.run_extract([], existing=True)

    def test_hash_mismatch(self):
        with self.assertRaises(ValueError):
            self.run_extract([], expected='0'*64)

    def test_member_limit(self):
        with patch.object(extractor, 'MAX_MEMBERS', 2), self.assertRaises(ValueError):
            self.run_extract([(extractor.PREFIX+f'/src/{i}', b'x', tarfile.REGTYPE) for i in range(3)])

    def test_reverse_collision(self):
        p = extractor.PREFIX + '/src/a'
        with self.assertRaises(ValueError):
            self.run_extract([(p+'/b', b'x', tarfile.REGTYPE), (p, b'x', tarfile.REGTYPE)])

    def test_recipe_offline_boundary_and_lock(self):
        folder = ROOT / 'tools/security-image'
        recipe = (folder / 'Dockerfile').read_text()
        stages = recipe.split('FROM ')[1:]
        self.assertEqual(len(stages), 3)
        for stage in stages:
            self.assertTrue(stage.startswith('python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258'))
        for stage in stages[1:]:
            for line in stage.splitlines():
                if line.startswith('RUN '):
                    self.assertTrue(line.startswith('RUN --network=none '))
        self.assertIn('USER 65534:65534', stages[-1])
        self.assertNotIn('ENTRYPOINT', recipe)
        self.assertNotIn('ARG ', recipe)
        historical = (ROOT / 'research/security-scanners/results/nvidia-requirements.lock').read_text().splitlines()
        actual = [line for line in (folder/'requirements.lock').read_text().splitlines() if not line.startswith('#')]
        self.assertEqual(actual, [line for line in historical if not line.startswith('skillspector==')])
        self.assertEqual((folder/'.dockerignore').read_text().splitlines(), ['**', '!Dockerfile', '!.dockerignore', '!requirements.lock', '!extract_source.py', '!build_wheel.py'])


if __name__ == '__main__':
    unittest.main()

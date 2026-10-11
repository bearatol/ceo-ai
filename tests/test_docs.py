"""Documentation boundary and fragment regression checks."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('check_docs', Path(__file__).resolve().parents[1] / 'scripts/check_docs.py')
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)


class DocsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'repo'
        self.root.mkdir()

    def page(self, name, text):
        (self.root / name).write_text(text, encoding='utf-8')

    def test_unicode_duplicates_and_fenced_examples(self):
        self.page('README.md', '# Начать\n# Начать\n# 简体中文\n'
                  '[RU](#начать-1) [ZH](#简体中文) [EN](other.md#use-it)\n'
                  '```md\n[example](absent.md)\n```\n')
        self.page('other.md', '# Use `it`\n')
        self.assertEqual(docs.check(self.root)[0], [])

    def test_broken_path_and_fragment_are_reported(self):
        self.page('README.md', '# Start\n[Missing](missing.md)\n[Heading](#absent)\n')
        self.assertEqual(len(docs.check(self.root)[0]), 2)

    def test_traversal_absolute_and_bad_destinations_are_rejected(self):
        self.page('README.md', '[Outside](../outside.md)\n[Absolute](/etc/passwd)\n'
                  '[Empty]()\n[Bad](file name.md)\n[Encoded](%2e%2e/outside.md)\n')
        self.assertEqual(len(docs.check(self.root)[0]), 5)

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX symlinks')
    def test_symlink_escape_is_rejected(self):
        outside = self.root.parent / 'outside.md'
        outside.write_text('Private test fixture', encoding='utf-8')
        (self.root / 'linked.md').symlink_to(outside)
        self.page('README.md', '[Link](linked.md)\n')
        self.assertTrue(docs.check(self.root)[0])

    def test_remote_links_are_counted_without_requests(self):
        self.page('README.md', '[Web](https://example.invalid)\n[Mail](mailto:test@example.invalid)\n')
        errors, count, external = docs.check(self.root)
        self.assertEqual((errors, count, external), ([], 1, 2))

    def test_reference_definition_and_angle_path(self):
        self.page('README.md', '[A][guide]\n[guide]: <a guide.md#start> "Guide"\n')
        self.page('a guide.md', '# Start\n')
        self.assertEqual(docs.check(self.root)[0], [])


if __name__ == '__main__':
    unittest.main()

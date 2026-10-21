"""Public site checks: installation scope, locale links and publication boundaries."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class SiteTests(unittest.TestCase):
    def test_each_locale_has_five_keyboard_native_skill_examples(self):
        spec = importlib.util.spec_from_file_location('check_site', ROOT / 'scripts/check_site.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        skills = {'ceo', 'writer', 'security-scan', 'debugger', 'user-review'}
        for page, dialogue in [('index.html', 'DIALOGUE.md'),
                               ('ru/index.html', 'DIALOGUE.ru.md'),
                               ('zh/index.html', 'DIALOGUE.zh-CN.md')]:
            with self.subTest(page=page):
                document = module.Document()
                document.feed((ROOT / 'site' / page).read_text())
                examples = {attrs.get('id') for tag, attrs in document.tags
                            if tag == 'details' and attrs.get('id', '').startswith('example-')}
                self.assertEqual(examples, {'example-' + skill for skill in skills})
                links = {attrs.get('href') for tag, attrs in document.tags if tag == 'a'}
                self.assertTrue({'https://github.com/bearatol/ceo-ai/blob/main/docs/'
                                 + dialogue + '#' + skill for skill in skills} <= links)

    def test_site_documentation_links_resolve_to_real_files_and_headings(self):
        site_spec = importlib.util.spec_from_file_location('check_site', ROOT / 'scripts/check_site.py')
        site_checker = importlib.util.module_from_spec(site_spec)
        site_spec.loader.exec_module(site_checker)
        doc_spec = importlib.util.spec_from_file_location('check_docs', ROOT / 'scripts/check_docs.py')
        doc_checker = importlib.util.module_from_spec(doc_spec)
        doc_spec.loader.exec_module(doc_checker)
        prefix = 'https://github.com/bearatol/ceo-ai/blob/main/'
        for page in ('index.html', 'ru/index.html', 'zh/index.html'):
            document = site_checker.Document()
            document.feed((ROOT / 'site' / page).read_text())
            for tag, attrs in document.tags:
                link = attrs.get('href', '')
                if tag != 'a' or not link.startswith(prefix):
                    continue
                destination = urlsplit(link[len(prefix):])
                if not destination.path.endswith('.md'):
                    continue
                with self.subTest(page=page, link=link):
                    target = ROOT / unquote(destination.path)
                    content = doc_checker.read_local(ROOT, target)
                    if destination.fragment:
                        self.assertIn(unquote(destination.fragment), doc_checker.headings(content))

    def test_public_site_contract(self):
        spec = importlib.util.spec_from_file_location('check_site', ROOT / 'scripts/check_site.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.check(ROOT / 'site'), [])

    def test_site_checker_rejects_external_resource_and_path_escape(self):
        spec = importlib.util.spec_from_file_location('check_site', ROOT / 'scripts/check_site.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            (root / 'index.html').write_text('<html><script src="https://example.invalid/x.js"></script>'
                                           '<img src="../private.png"></html>')
            errors = module.check(root)
            self.assertTrue(any('external resource' in e for e in errors))
            self.assertTrue(any('outside site' in e for e in errors))

    @unittest.skipUnless(os.name == 'posix', 'symlink creation needs POSIX privileges')
    def test_site_checker_rejects_symlinks_and_unexpected_files(self):
        spec = importlib.util.spec_from_file_location('check_site', ROOT / 'scripts/check_site.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'index.html').symlink_to(ROOT / 'README.md')
            (root / '.env').write_text('not a real secret')
            errors = module.check(root)
            self.assertTrue(any('symlinks forbidden' in e for e in errors))
            self.assertTrue(any('.env: unexpected' in e for e in errors))

    def test_site_checker_rejects_css_egress_and_inline_handlers(self):
        spec = importlib.util.spec_from_file_location('check_site', ROOT / 'scripts/check_site.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'assets').mkdir()
            (root / 'assets/style.css').write_text('a {background: url(https://example.invalid/x)}')
            (root / 'index.html').write_text('<html><a onclick="bad()">test</a></html>')
            errors = module.check(root)
            self.assertTrue(any('external resource' in e for e in errors))
            self.assertTrue(any('inline execution' in e for e in errors))

    def test_contact_allowlist_does_not_allow_widgets_or_other_profiles(self):
        spec = importlib.util.spec_from_file_location('check_site', ROOT / 'scripts/check_site.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'index.html').write_text('<html><a href="https://t.me/other">Other</a>'
                '<script src="https://t.me/bearatol"></script></html>')
            errors = module.check(root)
            self.assertTrue(any('unexpected navigation destination' in e for e in errors))
            self.assertTrue(any('external resource' in e for e in errors))


if __name__ == '__main__':
    unittest.main()

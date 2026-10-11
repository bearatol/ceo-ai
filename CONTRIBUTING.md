# Contributing to CEO AI

Bug reports, focused fixes, examples and translations are welcome. The project
is maintained by [bearatol](https://github.com/bearatol). Start with
[Issues](https://github.com/bearatol/ceo-ai/issues) to report a problem or discuss
a change that would alter behavior or installation. For vulnerabilities, follow
[SECURITY.md](SECURITY.md) instead of opening a public report.

## Make a focused change

Explain the problem, the intended behavior and how you checked the result.
Keep unrelated changes separate. Preserve user files, permission boundaries,
source attribution and the MIT license. Contribute only material you have the
right to share; do not include private prompts, credentials, logs or local paths.

For behavioral code changes, add a regression test that fails before the fix
and passes afterward. For prose changes, check clarity, factual accuracy, links
and consistency across languages. See [development instructions](docs/DEVELOPMENT.md)
for test commands and package integrity checks. A reviewer should be able to
reproduce the claimed checks from a clean checkout.

## Documentation and translations

English is the reference for structure and facts. Keep the English, Russian
and Simplified Chinese README and help guides in sync. If you cannot update a
translation, say which sections need attention in the pull request. Do not
silently publish translations of different behavior.

Write for someone who has not read our conversations. Explain observable
results, label invented examples as illustrations, and distinguish file tests
from app invocation and model behavior. Claims about quality, speed or cost
need reproducible evidence. Keep machine-facing instructions in English.

## Review and release

Open a pull request against `main` with a short description and verification
results. Automated checks cover tests, package integrity and local Markdown
links. CI does not prove that an AI model follows the skill correctly.

Changes to installation, CI or permissions need a security review as well as
functional checks. Before a release, record user-visible changes, migration
steps and untested environments. Keep published tags unchanged. The maintainer
decides whether and when a contribution is included in a release.

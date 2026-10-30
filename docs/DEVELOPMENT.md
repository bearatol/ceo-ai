# Development and verification

[CEO AI website](https://bearatol.github.io/ceo-ai/) · [Work examples](https://bearatol.github.io/ceo-ai/#cases) · [Install](https://bearatol.github.io/ceo-ai/#install)

The main skill lives at `.apm/skills/ceo-ai/`. Its entry
`SKILL.md` selects eight internal guides under `references/skills/`; `catalog.json`
contains their relative paths along with four role prompts, the protocol and the
packet tool. Those internal IDs are not additional native skill registrations.
APM discovers this layout through `apm.yml`. `scripts/plugins.py` produces the
committed `plugins/ceo-ai` package for both native plugin managers. It contains
`skills/ceo-ai/`, `skills/writer/`, `skills/security/`, `skills/debugger/` and
`skills/user-review/` with one manifest and one receipt. Source files for the
additional skills live in `modules/ceo-ai-writer/`, `modules/ceo-ai-security/`,
`modules/ceo-ai-debugger/` and `modules/ceo-ai-user-review/`. Each generated skill
has its required shared resources, copied from the canonical core files, including
`LICENSE` and `VERSION`. Debugger and User Review add instructions, not runtime
dependencies or extra host permissions. Security adds target-specific audit and
consent instructions; Docker is required only for its optional SkillSpector
skill-package scan. Edit canonical sources only; the doctor rejects generated drift.
The plugin builder uses an explicit publication allowlist, verifies source hashes,
rejects symlinks and refuses to overwrite edited or unmanaged generated payloads.
It is a developer build for a trusted checkout, not a concurrent runtime installer.

The local installer reads only the reviewed local bundle and an explicit project.
It writes one namespaced skill directory, an owned lock file, and temporary
transaction data beneath that host's skill directory. It uses no network,
subprocesses, hooks, global configuration, or dependency downloads. It verifies
content hashes and rejects conflicting ownership, added/modified files, symlinks,
Windows reparse points, special files, and oversized inputs. Updates stage the complete directory before
promotion; the recovery command handles interruptions around that promotion.

These checks assume a project directory trusted against noncooperating local
writers. The lock serializes this installer, not every process on the computer.
Hashes detect changes; they are not a signature or proof that a remote source is
trustworthy. The installation agent resolves and reports an immutable source
commit. APM and this installer have separate ownership; never take over each
other's deployment silently.

## Edit and check

Use Python 3.10 or newer. The ordinary bundle and installer have no third-party
Python dependencies. After an intentional change to bundled resources:

```bash
python3 scripts/package.py --write
python3 scripts/plugins.py --write
bash tests/test.sh
bash scripts/doctor.sh
python3 -B scripts/check_docs.py
```

`package.py` updates the committed file hashes. Review the content diff before
accepting new hashes. `doctor.sh` checks catalog/profile consistency, JSON, and
the manifest. It does not establish native skill loading or agent sandboxing.
Machine-facing instructions stay in English. Keep the English, Russian and
Simplified Chinese README and help guides aligned; see [CONTRIBUTING.md](../CONTRIBUTING.md).

`package.py` builds only the core APM bundle. `plugins.py` builds and checks one
native plugin with five skill directories. To add the reviewed directories to
an intact generated package, use `python3 -B scripts/plugins.py --write
--allow-layout-change`. The flag permits additions, the complete known
`skills/security-scan/` to `skills/security/` migration, and historical core
adapter removal, never arbitrary deletion or adoption of edited files. The
rename rejects incomplete/extra legacy files or a colliding new skill directory.
Both receipt verification and staged promotion/rollback remain mandatory. The
project/APM installer still installs only the core entry.

Debugger and User Review are source-tree additions. Packaging checks verify
declared files and resource paths; scenario evaluation checks whether responses
meet their contracts. Neither is evidence that a host discovers or invokes the
new skills. Record installation, discovery, model behavior and scenario results
separately; do not extend historical core-only host checks to this layout.

Security bundles no general-purpose pentest runtime. Its assistant-led audits use
the host model and authorized tools; scenario fixtures are in
`tests/scenarios/security.md`. They are not records of native invocation or live
tests. Its optional SkillSpector adapter does not bundle third-party scanner
code or an image; that route requires Python 3.10+, POSIX, Docker and a separately
prepared reviewed immutable NVIDIA image. The adapter performs no installation,
pulls or LLM/API calls. Core indexing requires no Docker. A CEO AI cloud scanner,
accounts and subscriptions are not implemented.

The [Checks workflow](../.github/workflows/checks.yml) runs the ordinary tests,
doctor and documentation checks on Ubuntu with Python 3.10/3.12 and macOS with
Python 3.12, plus native Windows with Python 3.10/3.12. See [run results](https://github.com/bearatol/ceo-ai/actions/workflows/checks.yml)
for evidence for a particular commit. A green run covers only that matrix.
Actions are pinned to verified commits of the official `actions/checkout` and
`actions/setup-python` repositories. Review upstream changes before updating pins.

The documentation checker reads local inline links, reference destinations and
ATX heading fragments, including repeated and Unicode headings. It ignores fenced
examples and does not fetch external URLs. It is a bounded check for the Markdown
style used here, not a full Markdown parser. External links and real app behavior
still need separate checks.

Optional APM tests use a separate Python environment containing `apm-cli==0.31.0`:

```bash
CEO_APM_PYTHON=/approved/test-environment/bin/python python3 -m unittest discover -s tests -p test_apm.py
```

The test requires macOS `sandbox-exec`, enforces a 20-second timeout per APM
command, and redirects APM's configuration and lifecycle-lock paths in the test
harness. Organization-policy discovery is disabled only in these isolated
fixtures, which have no organization policy. It never changes HOME or the
user's APM configuration. Do not remove sandbox restrictions to make the test
pass. The standard CI jobs skip these optional APM tests and do not install APM.
The native Windows test is also skipped on POSIX; inventory, FIFO and POSIX-lock
tests run on Linux/macOS. These are file deployment tests, not application UI
or model-behavior tests.

Native Windows file installation is supported from 0.3.0 for ordinary local
project folders. Windows CI covers all three host destinations, Unicode and
spaces, update/removal, recovery, real junction rejection and cross-process
byte locking. Network shares, device namespaces, drive-relative paths and
reparse points are rejected. Native app invocation and APM on Windows remain
unverified. Native Windows inventory has separate tests for pinned NTFS handles, rejected
links and cache refresh. See [scope](SECURITY_SCANNING.md#windows). File integrity checks concern normal file contents;
NTFS alternate streams and preservation of filesystem metadata are not verified.

The initial Windows candidate passed the full CI matrix in
[this run](https://github.com/bearatol/ceo-ai/actions/runs/38214370284).
Use the latest commit's run for release acceptance.

## Further details

- [Native plugins, migration and actual host verification](PLUGINS.md)
- [CEO behavior and evidence](CEO_GUIDE.md)
- [Debugger: bug fixes and behavior-preserving refactoring](DEBUGGER.md)
- [User Review: synthetic novice and professional perspectives](USER_REVIEW.md)
- [Security scanning and optional engine boundaries](SECURITY_SCANNING.md)
- [Agent installation procedure](../INSTALL.md)
- [APM integration](APM.md)
- [Original source records](PROVENANCE.json)

Source notices remain in the MIT license. Some planning and review practices
were informed by Superpowers. Its prompts are not bundled, and comparative
quality or cost advantages have not been established by benchmarks.

## Memory changes

Private stores never belong in the bundle, site or Git checkout. The shared
publication allowlist is checked by the installer, APM bundle builder and plugin
builder. Only original code, schemas and synthetic examples are allowed. A reviewed
addition to the generated plugin layout needs `scripts/plugins.py --write
--allow-layout-change`; edited or foreign payloads still fail closed.

Run `python3 -B -m unittest discover -s tests -p test_memory.py` for consent,
namespace, stale-record, revision, deletion and filesystem checks. All fixtures
use temporary directories and synthetic records. Do not test with personal memory.
See [memory behavior and limitations](MEMORY.md#storage-and-verification).

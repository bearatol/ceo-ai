# Development and verification

The repository ships one installable skill at `.apm/skills/ceo-ai/`. Its entry
`SKILL.md` selects seven internal guides under `references/skills/`; `catalog.json`
contains their relative paths along with four role prompts, the protocol and the
packet tool. Those internal IDs are not additional native skill registrations.
APM discovers this layout through `apm.yml`. No generated copy is maintained.

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
bash tests/test.sh
bash scripts/doctor.sh
python3 -B scripts/check_docs.py
```

`package.py` updates the committed file hashes. Review the content diff before
accepting new hashes. `doctor.sh` checks catalog/profile consistency, JSON, and
the manifest. It does not establish native skill loading or agent sandboxing.
Machine-facing instructions stay in English. Keep the English, Russian and
Simplified Chinese README and help guides aligned; see [CONTRIBUTING.md](../CONTRIBUTING.md).

The [Checks workflow](../.github/workflows/checks.yml) runs the ordinary tests,
doctor and documentation checks on Ubuntu with Python 3.10/3.12 and macOS with
Python 3.12. See [run results](https://github.com/bearatol/ceo-ai/actions/workflows/checks.yml)
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

Native Windows installation is not supported in 0.2.0. Static review found that
the installer's expected-directory normalization mixes Windows separators with
POSIX-style manifest paths. The interrupted-update fixture also assumes a POSIX
separator. A future Windows release must address those paths and pass the native
tests before a compatibility claim is made. POSIX-only inventory checks require
the host's own discovery mechanism on other platforms.

## Further details

- [CEO behavior and evidence](CEO_GUIDE.md)
- [Agent installation procedure](../INSTALL.md)
- [APM integration](APM.md)
- [Original source records](PROVENANCE.json)

Source notices remain in the MIT license. Some planning and review practices
were informed by Superpowers. Its prompts are not bundled, and comparative
quality or cost advantages have not been established by benchmarks.

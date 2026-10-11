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
Windows reparse points,
special files, and oversized inputs. Updates stage the complete directory before
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
```

`package.py` updates the committed file hashes. Review the content diff before
accepting new hashes. `doctor.sh` checks catalog/profile consistency, JSON, and
the manifest. It does not establish native skill loading or agent sandboxing.
Machine-facing instructions stay in English; user guides are maintained in
English, Russian, and Simplified Chinese.

Optional APM tests use a separate Python environment containing `apm-cli==0.31.0`:

```bash
CEO_APM_PYTHON=/approved/test-environment/bin/python python3 -m unittest discover -s tests -p test_apm.py
```

The test requires macOS `sandbox-exec`, enforces a 20-second timeout per APM
command, and redirects APM's configuration and lifecycle-lock paths in the test
harness. Organization-policy discovery is disabled only in these isolated
fixtures, which have no organization policy. It never changes HOME or the
user's APM configuration. Do not remove
sandbox restrictions to make the test pass. These are file deployment tests,
not application UI or model-behavior tests. Native Windows runtime behavior has
not been exercised here.

## Further details

- [CEO behavior and evidence](CEO_GUIDE.md)
- [Agent installation procedure](../INSTALL.md)
- [APM integration](APM.md)
- [Original source records](PROVENANCE.json)

Source notices remain in the MIT license. Some planning and review practices
were informed by Superpowers. Its prompts are not bundled, and comparative
quality or cost advantages have not been established by benchmarks.

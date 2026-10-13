# Security indexing integration: verification

Date: 2026-10-13. Scope: source bundle and generated plugin mirror only.
The installed user plugin and global Mac skill/agent directories were not changed
or scanned. The [approved plan](INTEGRATION_PLAN.md) follows the separate
[42-probe benchmark](REPORT.ru.md); these checks do not extend its accuracy claims.

## Delivered behavior

Index schema 2 includes bounded local static observations for every admitted
skill package and Markdown agent. Supporting/hidden files affect the package
hash. Source, capability tier, findings, coverage and decision remain separate;
trust is always unverified. Cache findings are recomputed, not accepted as proof.
Exclusions cannot yield a full-package hash or verified freshness.

The optional NVIDIA adapter uses a private snapshot and an explicitly selected,
already-local immutable image. It never pulls an image or invokes an LLM. Vendor
prose and safety badges are discarded; version, locations and coverage are checked.
Neither mechanism grants execution permission. The future paid API is only a
disabled contract; no client, endpoint or credential handling was introduced.

## Verification performed

- Full repository suite: 164 tests, OK, 4 skips for platform/runtime prerequisites.
  The security-specific subset comprises 66 tests (30 static, 13 inventory,
  23 optional adapter). Final suite duration: 10.697 seconds on this host.
- Bundle manifest and plugin mirror regenerated and verified. Doctor passed for
  15 components. Documentation check passed for 81 Markdown files; its 80 external
  links were not fetched by that check.
- Meaningful failing assertions were observed before the snapshot/index behavior
  and later adapter corrections. The adapter's initial missing-module failure was
  not counted as behavioral evidence. Later RED/GREEN cases covered partial
  analysis, failed cleanup, vendor decisions, bytecode and rejected snapshots.
- A normal CLI invocation without `-B` or a bytecode environment flag creates no
  Python cache in the bundle. Existing unchecked stale sibling bytecode is ignored.
  This fixed a real packaging failure discovered during the first full-suite run.
- Catchable cancellation regressions cover SIGTERM during scanning, repeated
  SIGHUP during cleanup, first cancellation during cleanup, already-closed child
  pipes and KeyboardInterrupt propagation. The old implementation failed the
  TERM/HUP cases; the corrected version removes its owned resources and restores
  signal handlers. SIGKILL/crashes/daemon outage remain outside cleanup guarantees.
- A 16.7 MB adversarial near-match snapshot exposed excessive lexical work. The
  analyzer now caps examined text at 1 MiB, fingerprints the remaining admitted
  bytes and marks coverage partial. The bounded follow-up finished in 3.132 seconds;
  this single measurement is not a throughput guarantee.

The [index smoke result](results/integration-index.json) contains 14 synthetic
entries: 4 `no-findings`, 4 `review-required`, 6 `incomplete`. The 12 skill bundles
were copied unchanged; the two benchmark agent files received synthetic `name`
frontmatter to match the product's existing Markdown agent format. This is not
the same direct-format test as the original benchmark. Builtin rules flag the
known covert-delegation fixture; they also flag a benign citation example.
These fixtures influenced the rules and are regression cases, not a held-out
effectiveness evaluation.

## Real offline container checks

| Fixture | Result | Evidence |
|---|---|---|
| `b01-summary` | Exit 0, COMPLETE, no findings | [JSON](results/integration-nvidia-benign.json) |
| `a07-linked-reference` | Exit 2, INCOMPLETE; High and Medium findings in `references/extra.md` retained | [JSON](results/integration-nvidia-linked.json) |

The second result is expected: a remote reference leaves coverage incomplete,
even when the vendor reports complete inspection of its local components.
Both private workspaces were cleaned; no `ceo-nvidia-` test container remained.
The runs used no network, user files, paid APIs or new dependencies.

Bindings shared by the two final runs:

- NVIDIA SkillSpector: `2.12.0`.
- Local image: `sha256:eb866dc01e678024c313b37371650fe015db786d9d5e3f00b8d3da090c7fb88b`.
- Adapter source SHA-256: `ba41f0e1650b20f46c9c9f13e74aefdd1148e73bd9f427bba0547c1baedbd465`.
- Builtin analyzer identity: `02345b75d395d589f030266fdf7f2fc024193bb918ea82b6a3ca207410314e65`.

The local image was built without installation or network from the previously
prepared, rehashed NVIDIA tree, whose SHA-256 is
`687440c12a069ed33a58580dcca3d2486d8190d3986e6f1f8cccd39ac7b65543`.
The deterministic tree manifest uses sorted relative pathlib paths followed by
NUL, each file's hexadecimal SHA-256 and newline. The base image is
`python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258`.
The Dockerfile only copies `site` and `source/src` to `/engine`, sets their
`PYTHONPATH`, and disables bytecode writes. No vendor code is distributed here.

## Remaining limits

Lexical rules can miss malicious intent and flag benign instructions. Code is
not analyzed through an AST or executed; binary resources and external references
remain partial. Native TOML agent configurations and symlink-based installations
need explicit format/root handling before a Mac-wide audit. Permissions and
delegation restrictions still need host enforcement. See the
[operator guide](../../docs/SECURITY_SCANNING.md) for limits and cost behavior.

Pre-implementation independent review: PASS_WITH_WARNINGS, corrections SEC-01–03
implemented. The first integration diff review found AVM-002 (Medium): default
SIGTERM/SIGHUP handling could bypass cleanup. Its remediation passed the tests
above; final exact-diff review is recorded separately before acceptance.
Review agents use the user's instruction-constrained exception; technically
enforced reviewer isolation is not claimed. Container isolation is separate.

Final independent review: **PASS**, no open introduced findings; AVM-002 resolved.
Reviewed snapshot: 61 files against baseline
`4aeea59bc9050f6bff612b3e7761a6fc358c5fc9`, diff SHA-256
`19a06638113c27409b7c0be6e745f503ab3b2e19365182d9ed3d93e5d9598a47`.
The reviewer inspected code only; runtime checks above were run by the lead.
This documentation-only review record was added after the reviewed snapshot;
no runtime code or test was changed after PASS.

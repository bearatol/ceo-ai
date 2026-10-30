# Security audits, bounded penetration tests and skill-package scans

Use `ceo-ai:security` to review the security of code, websites, APIs, mobile apps,
configuration, infrastructure, AI/agent systems or skill packages. It uses your
AI app's model and authorized tools. Before a penetration test, agree the exact
actions and limits on a target you are authorized to test, with informed consent
about the risks.

The skill bundles no new scanner suite and has no universal Python or Docker
prerequisite. Available tools, access and evidence determine what can be checked.
A result with no findings does not guarantee safety. Your AI app's actual
permissions and policies remain binding.

## Audit and testing workflow

1. Establish the goal, owner/authorization, exact targets, environment, evidence,
   exclusions and desired output. Start with authorized read-only material; a
   broad request does not authorize intrusive actions or unrelated discovery.
2. Choose target-specific checks and explain the proposed active test before it
   runs: purpose and exact action, likely benefit, possible harm, a safer option,
   request/time/cost limits, stop conditions and recovery or cleanup. Ask for
   informed approval of the concrete plan. Reuse approval while its scope and
   risks remain unchanged; new targets or risks need new consent. Tool approvals
   and host policy cannot be bypassed by conversational consent.
3. Use the smallest proof that resolves the question, preferably in staging with
   synthetic data. Stop on the agreed limits, unexpected real data, instability
   or a boundary change. No persistence, unnecessary data collection or expansion
   from one finding into a wider compromise.
4. Report observed evidence separately from hypotheses, with reproduction scope,
   impact, confidence, remediation and a suitable verification step. Record
   skipped or unavailable tests and affected targets as coverage gaps; never
   invent execution, tool availability or a successful check.

The installed skill links to [engagement and consent rules](../modules/ceo-ai-security/references/engagement.md),
[target-specific testing profiles](../modules/ceo-ai-security/references/testing-profiles.md),
[evidence and reporting](../modules/ceo-ai-security/references/reporting.md) and
[optional skill-package scanning](../modules/ceo-ai-security/references/skill-scan.md).
Use the resources next to the loaded `security/SKILL.md` in a native installation.
Project and APM installs still contain only the core CEO skill.

Method references inform the selected checks; they do not certify a result:
[NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final) and
[PTES pre-engagement](https://pentest-standard.readthedocs.io/en/latest/preengagement_interactions.html)
for planning and rules of engagement; [OWASP WSTG](https://wstg.owasp.org/v4.2/)
and [ASVS](https://asvs.owasp.org/) for web/API checks;
[OWASP MASTG](https://mas.owasp.org/MASTG/) for mobile;
[CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) for applicable
configuration baselines; [OWASP AI Agent Security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
for AI/agent trust boundaries; and [CVSS v4.0](https://www.first.org/cvss/v4.0/specification-document)
when a justified severity vector is useful.

## Builtin inventory screening

The CEO AI inventory includes an original stdlib scanner. It analyzes the same
bounded bytes used for each package fingerprint. It never executes package
content, fetches links, installs dependencies, invokes a model or reads API keys.
These properties apply to this static inventory utility, not every Security
workflow. It is an advisory screening layer, not a system antivirus or runtime
gate.

Start with the [first-scan guide](QUICKSTART.md). Only the optional SkillSpector
route for skill packages uses the [Docker walkthrough](DOCKER_SCAN.md)
([Русский](DOCKER_SCAN.ru.md), [简体中文](DOCKER_SCAN.zh-CN.md)). Its current
recipe requires native ARM64 Docker, Buildx/BuildKit and Linux ARM64 containers;
it does not cover every Docker host or audit target.

## Indexing

```sh
python3 .apm/skills/ceo-ai/scripts/ceo_inventory.py --home /approved/root
python3 .apm/skills/ceo-ai/scripts/ceo_inventory.py --home /approved/root --refresh
```

Use the installed bundle's actual path on another host. Roots contain
`skills/<name>/SKILL.md`, `agents/<name>.md` and/or `agents/<name>.toml`. The first command only reads;
refresh needs permission to write `.ceo-inventory.json` (and a lock file on Windows).
POSIX uses no-follow descriptors; Windows uses pinned handles on fixed local NTFS. Other layouts are not silently expanded into a broader scan. TOML declarations
are metadata only: supported name, sandbox, approval and network fields use
strict types/enums; instructions and arbitrary values are never echoed. Unknown
fields, malformed TOML or an unavailable stdlib parser yield fixed issue codes.
TOML coverage remains lexical and partial, including on Python 3.10 without
`tomllib`. No declaration proves effective tool permissions.

Skills include hidden/nested resources; agents have file-only scope. Bounds:
256 KiB/file, 16 MiB total, 1024 enumerated entries, depth 12, five-second
cooperative deadline. The capture rechecks file/tree metadata and rejects
nested symlinks, hard links and special files. Oversized supporting files are
excluded without opening them; smaller admitted resources still get analyzed.
An oversized or missing entry file remains an error. Failure preserves the prior cache, which
must be treated as stale. Source files can still change after capture: recheck
the selected package before use. The root must be trusted against local writers.
Lexical analysis additionally caps text at 1 MiB per package, 8192 lines and
8192 characters per line. Remaining admitted bytes are still fingerprinted but
their analysis is explicitly partial. This bounds near-match regex workloads.

Typical secret/auth names (`.env`, `.env.*`, `auth.json`, credentials files,
private-key names/extensions), credential directories, `.git`, `.venv`,
`node_modules` and `__pycache__` are excluded without opening their contents.
This name list is not a universal secret detector. Exclusions mean partial
coverage, a null full-package hash and `freshness: unverifiable`. The observed-byte
hash covers only admitted files. Other hidden resources are included.

## Explicit package aliases

By default all links are refused. `--allow-alias-root /approved/target-root`
(repeatable, at most 32 total roots including home) enables package-root aliases
only within home and the supplied real roots. The program does not discover or
approve target roots itself. `snapshot_package(..., approved_alias_roots=[...])`
requires all source and target roots explicitly. Only absolute roots are accepted.

Resolution uses component containment, no-follow parent descriptors, a 16-link
limit and cycle checks. The opened target stays bound through capture and the
chain is revalidated afterward. Secret/excluded path components, parent-directory
symlinks, nested resource links and any `..` segment in a link target are refused.
This deliberately supports a subset of filesystem aliases; unsupported chains
must remain unassessed. Relative sibling targets are supported. Two paths to the
same canonical target are grouped with alias bindings; distinct targets sharing
an identity still fail. Identical content alone never proves alias equivalence.
These checks detect observed mutations, not all possible hostile-writer races.

## Interpreting results

Each entry stays `present-unverified`. Its `security` object separates:

- Capability: heuristic T0 (text), T1 (local files/scripts), T2 (network),
  T3 (secrets/persistence/privilege/destruction), T4 (dynamic/opaque code
  acquisition). This uses the capability distinction described by
  [skill-xray](https://github.com/worklore/skill-xray); no upstream code is bundled.
  Tiers are not enforced permissions or confidence scores.
- Findings/severity: fixed rule IDs, relative paths and line numbers, without
  source snippets, credentials or endpoint values. Quoting and negation of a
  matched action remain uncertain; a nearby example cannot suppress an independent
  action. URL-credential templates and explicit `--api-key` declarations are LOW
  advisories for review, not proof of leakage. Report paths and vendor fields remain untrusted data.
- Coverage: `complete` means supported text processed by bounded lexical rules,
  never complete threat detection. Code is lexical-only, binary data is not
  interpreted, and exclusions, missing/external references or limits are partial.
- Decision: `no-findings`, `review-required` or `incomplete`. None grants execution
  permission. Trust stays `unverified`; local presence does not verify origin.
- Identity: admitted package bytes/paths and scanner, rules and policy hashes.

Owned schema-1 caches migrate only on explicit refresh. Foreign/malformed/future
caches are refused. Findings are always recomputed: correct hash bindings in a
writable JSON file do not prove that an analysis actually ran. The cache records
reproducible observations and freshness, not a trusted exemption from checking.
The CLI loads its trusted sibling modules from source, ignoring Python bytecode
caches and creating none in the installed bundle.

## Optional SkillSpector route for skill packages

The native `ceo-ai` plugin includes the builtin indexing check and the broader
`ceo-ai:security` skill described above. That skill retains a bounded reader,
static scanner and NVIDIA adapter for optional checks of skill packages only.
This adapter does not audit a website, API, mobile app or infrastructure target.
Installing the plugin does not start a scan or install Docker. Use the
[plugin guide](PLUGINS.md#security) to verify the selected snapshot; older
releases used a separate security plugin.

Only for this optional route, check these prerequisites: Python 3.10 or newer,
a POSIX host with descriptor/no-follow support, a Docker client and working
daemon, and a separately prepared, reviewed NVIDIA SkillSpector image. The module
installs none of these. Without them, this route is unavailable; ordinary audits
can still use authorized host tools. The static adapter itself does not use an
LLM or paid API; host-model conversation tokens still apply.

Prepare and review a local scanner image separately. The adapter never pulls or
installs anything. Require an immutable image ID or repository digest and an
explicit expected SkillSpector version. Tags alone are rejected. The private
workspace must already exist, be owned by the invoking user, and have trusted
ancestors and no group/world write permission.

```sh
python3 plugins/ceo-ai/skills/security/scripts/ceo_security_nvidia.py \
  --package /approved/skill-package --workspace /approved/private-workspace \
  --image "$SCANNER_IMAGE_DIGEST" --version 2.12.0
```

In a native installation, use `scripts/ceo_security_nvidia.py` relative to the
loaded `security/SKILL.md`, not the source checkout or the core skill. Select
`ceo-ai:security` in Codex or invoke
`/ceo-ai:security` in Claude Code. The skill checks scope and
prerequisites before running an explicitly requested scan. A scan-only request
does not authorize Docker installation or image builds/downloads. An explicit
preparation request can authorize the separately reviewed setup workflow in the
skill-scan guide. The adapter itself never pulls/builds an image or falls back
to an online provider.

If needed, pass `--docker-host unix:///approved/docker.sock`. Only the host Docker
client connects to that socket; it is never mounted in the scanner container.
Docker is a trusted local dependency with powerful host access. Image provenance
and host permissions remain the operator's responsibility.

The adapter mounts a private copy of admitted bytes read-only, checks scanner
version, and invokes `--no-llm`: no network, non-root UID, no capabilities,
no-new-privileges, read-only root, resource limits, 25-second process deadline
and combined 2 MiB output limit. Host HOME, keys, proxy variables and Docker
configuration are not inherited. Cleanup targets only this invocation's
container and staging directory.
Catchable termination signals (`SIGTERM`/`SIGHUP`) must enter bounded cleanup;
they cannot produce a completed scan. `SIGKILL`, an interpreter crash or an
unreachable Docker daemon can leave resources behind. Container resource limits
are not an independent wall-clock deadline, so an operator must inspect leftovers
after such failures before continuing a bulk audit.

Output validation checks version, component coverage, IDs, severities and
locations against the snapshot. Prose, raw errors, scores and safety badges are
discarded. Failures, malformed/incomplete output or failed cleanup stay incomplete.
Builtin coverage limitations are preserved alongside verified vendor findings.
Vendor claims are untrusted observations, not an attestation. Image vulnerabilities,
scanner bugs and container escape resistance are outside these guarantees.

## Costs and distribution

Builtin scans use local CPU/time; optional Docker scans also need RAM, disk and
startup time. Neither scanner calls a model. Using the skill through your AI app
still uses that app's model tokens under your existing plan. Estimate package
count/size and set scope before a bulk scan.
Indexing never invokes the optional engine or a model automatically. See the
[benchmark report](../research/security-scanners/REPORT.ru.md) for measured results
and limitations of its small synthetic corpus.

`ceo_security.disabled_api_contract()` is only a future interface description:
`enabled: false`, `implemented: false`, requiring explicit opt-in, data approval
and a hard budget. There is no endpoint, client, credential store or provider.
Environment keys cannot activate it. A future implementation must show an
estimate, stop at the budget and report incomplete work without a paid fallback.

The lightweight check stays in the regular bundle. The native plugin also ships
Security's host-model workflow and the optional skill-package Docker adapter;
scanner engines remain separately prepared tools. No CEO AI cloud server,
subscription, API client or account system is implemented. The host must enforce
read/write/network restrictions and approval inheritance independently.

## Windows

Builtin indexing runs natively with Python 3.10+ on fixed local NTFS drives.
No WSL, Docker or third-party Python packages are required for this check.
Use an explicitly approved absolute local path in PowerShell, substituting the
installed bundle location and the approved inventory root:

```powershell
py -3 "C:\approved\ceo-ai\scripts\ceo_inventory.py" --home "C:\approved\inventory"
py -3 "C:\approved\ceo-ai\scripts\ceo_inventory.py" --home "C:\approved\inventory" --refresh
```

The first command is read-only. Refresh creates an owned cache and a lock file
inside the approved root. Directory handles remain pinned without write/delete
sharing during traversal. Reparse points (including junctions and cloud
placeholders), hardlinked files, alternate data streams, UNC/device paths, mapped
network drives and non-NTFS volumes are refused. Windows package aliases are not
supported, including when `--allow-alias-root` is supplied. Sharing violations
fail closed rather than retrying with weaker access rules.

The root must have trusted access permissions. Cache files inherit that root's
ACL. Locking coordinates cooperating refreshers, not malicious processes running
as the same user. Cache replacement is atomic but not a compare-and-swap against
arbitrary concurrent writers. First creation never overwrites an existing cache.
Limits are checked between filesystem operations, not a hard timeout on a blocked
OS call. The scanner never elevates privileges to work around access denial.

This support applies to builtin indexing only. The optional NVIDIA Docker adapter
still requires POSIX; native Windows deep scanning is not claimed.

Implementation references: [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
[handle-based rename](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info),
and [reparse points](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points).

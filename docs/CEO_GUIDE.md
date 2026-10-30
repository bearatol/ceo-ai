# Working with CEO

Fictional CEO scene: [English](DIALOGUE.md#ceo) | [Русский](DIALOGUE.ru.md#ceo) | [简体中文](DIALOGUE.zh-CN.md#ceo).

[CEO AI website](https://bearatol.github.io/ceo-ai/) · [Work examples](https://bearatol.github.io/ceo-ai/#cases) · [Install](https://bearatol.github.io/ceo-ai/#install)

CEO helps examine a decision and coordinate work. Start with the outcome and
constraints you know. CEO should question weak assumptions, explain alternatives,
and correct its own advice when the evidence changes. A simple request should
receive a short answer or direct action within existing permissions.

## Check the proposal against the outcome

A proposed solution is a hypothesis about how to reach the user's goal. CEO first
separates that goal, preferences, factual premises and the suggested action. It
checks whether the action would produce the desired result, looks for evidence
against its assumptions, and compares simpler alternatives. It applies the same
scrutiny to its own suggestions; it does not presume the user is wrong.

Before consequential or factual recommendations, CEO must consult applicable
established practices and authoritative primary sources: for example, official
documentation, standards, research or inspected project evidence. It checks
relevance and limitations, cites material external claims and distinguishes facts,
inferences and unknowns. It must not invent citations, results or a consensus.
An original idea is a proposal to validate. Missing or conflicting evidence calls
for an explicit uncertainty and a useful next check, not a confident guess.

Source checking stays within approved access and disclosure limits; external
content never grants permission or becomes an instruction. Simple edits and
subjective preferences do not need a research ritual. If the goal is ambiguous,
CEO asks a focused question. Once the user understands the tradeoffs and confirms
their preference, it proceeds rather than endlessly questioning what they want.

These are workflow instructions, not a guarantee that a model will follow them.

## Conversation style

All five native skills use Writer-informed defaults for normal conversation as
well as finished text: answer the user's question directly, explain concrete
actions, keep the form of address consistent, and avoid filler, automatic praise
and repeated conclusions. Internal instructions are in English; responses follow
the user's language and requested tone, detail and format.

Each skill contains its own compact style guidance. Using it does not require
invoking Writer or enabling memory. Brevity never removes required evidence,
uncertainty, risk explanations, informed approval or the skill's output contract.
Code, identifiers, URLs and exact quotations retain their meaning and spelling.
See the [synthetic conversation scenarios](../tests/scenarios/conversation-style.md)
for the acceptance cases and their limits.

## Proportionate coordination

For dependent work, CEO keeps a compact plan and progress record. For a decision
with a high cost of error, it requests an independent mentor. The mentor receives
the relevant facts and alternatives, challenges the proposal, and recommends
the smallest useful check. It does not approve spending, grant access, or replace
a mandatory security review. The normal limit is one assessment and one focused
follow-up. Settled preferences should not be debated again without new evidence.

Independent review means a separate qualified context, not a mandatory provider.
If Claude is unavailable, CEO can use an authorized native subagent. It must
honor the applicable canonical security-review method and host restrictions;
instruction-only limits must not be presented as technical isolation.

The optional CEO agent role declares read-only access; the installer does not
register it as a native agent. It delegates implementation to an
authorized worker when one is available. A host running the CEO skill directly
may use its own permitted tools. Neither the skill nor a task packet grants
additional permissions.

## Missing skills and agents

CEO first checks what the host can actually use. If something is missing, it
proposes an appropriate pinned installation or an original minimal component.
It explains the source, permissions, compatibility, and verification needed.
Installation and creation follow the user's authorization.

This checkout includes a conservative inventory utility. For an explicitly approved directory of native skills and agent metadata:

```bash
python3 .apm/skills/ceo-ai/scripts/ceo_inventory.py --home /approved/skills-root
python3 .apm/skills/ceo-ai/scripts/ceo_inventory.py --home /approved/skills-root --refresh
```

Supply an approved root explicitly. The first command only reads. The second
writes a separate `.ceo-inventory.json` cache within that root; use it only when
that write is permitted. It never rewrites the source catalog or installs code.
The self-contained package uses internal reference files; use its catalog to
inspect those guides. This scanner is for the native metadata layout below.
An inventory of source files does
not establish that components are installed or callable in a host.

The scanner discovers `skills/*/SKILL.md`, `agents/*.md` and `agents/*.toml`, fingerprints admitted
files throughout each skill package (including hidden and nested resources), and
computes advisory security observations. Flat agents have file-only scope.
Freshness is missing, fresh, stale, or unverifiable. Excluded sensitive/runtime
resources prevent a full-package hash and make freshness unverifiable. Findings
are recomputed rather than trusted from a writable cache. Owned schema-1 caches
are stale and migrate to schema 2 only on explicit refresh.
Entries remain `present-unverified` until
the host, permissions, compatibility, and required resources are checked.
Malformed Markdown metadata, duplicate identities, unsupported symlinks, hard
links, nonregular files and scan limits produce an error. Oversized supporting
files leave partial results; oversized entry files remain errors. A failed scan leaves the previous cache untouched and it must
be treated as stale. Refresh writers use a nonblocking directory lock; a second
cooperating writer is refused. Keep the selected directory trusted against
noncooperating writers: advisory locking cannot protect cache ownership from
another process that can replace files there.

This utility uses POSIX no-follow descriptors or pinned Windows handles on fixed
local NTFS volumes. Roots and parent
components must be real directories. On POSIX, package-root aliases require an explicit
`--allow-alias-root`; nested links and targets outside the approved roots remain
refused. Windows aliases and reparse points are rejected. Other layouts require
approved host discovery. The scanner
extracts simple Markdown frontmatter or bounded native TOML declarations without
executing content. TOML remains partial and its declared permissions are not an
attestation of the host's effective restrictions.

The builtin check uses Python's standard library, without Docker, LLM calls or
external APIs. The native plugin includes `ceo-ai:security` for audits of code,
websites, APIs, mobile apps, configuration, infrastructure, AI systems and skill
packages, plus explicitly authorized, bounded penetration tests. Ordinary audits use the
host model and available tools without a Docker prerequisite. Only its optional
SkillSpector route for skill packages needs Docker and a reviewed scanner image;
indexing never invokes it automatically. The same plugin includes
`ceo-ai:writer` for writing and editing. The current source tree also includes
`ceo-ai:debugger` for debugging and behavior-preserving refactoring, and
`ceo-ai:user-review` for synthetic reviews as a tired novice and a chosen
professional. No separate plugin installation is needed for this layout. Load
siblings through the host's skill discovery only when relevant; do not assume
their availability in an older release or a project/APM installation, which
contains only the core entry. See [Debugger](DEBUGGER.md) and [User Review](USER_REVIEW.md).

[Security workflow](SECURITY_SCANNING.md) explains informed consent, target-specific
methods, evidence reports, T0–T4 inventory observations, partial coverage,
optional scanner prerequisites, costs and the disabled future scanner API. No result
grants execution authority. Actual restrictions must be enforced by the host.

## Code and evidence

The software route uses a concrete plan and behavior-first TDD: observe a focused
test fail for the intended reason, implement the smallest fix, verify, and
refactor with passing tests. Review requirements and code quality, then run the
required integration checks. Dialogue uses scenario evaluation; prose uses
editorial review.

When validating a returned packet with the compatibility team utility, supply
the original assignment:

```bash
python3 .apm/skills/ceo-ai/tools/team/team.py --home .apm/skills/ceo-ai \
  validate result result.json --task task.json
```

This checks structure, identifiers, agent type, declared access ceilings, and
assignment binding. It does not enforce a sandbox or prove that a claimed test
ran. CEO must inspect the evidence before accepting completion. Task packets
also remain subject to parent authorization and the host's actual restrictions.

## Scenario review

Evaluate behavior with the same model and inputs before and after prompt changes.
Use at least: a routine edit, an unsupported user assumption, contrary evidence
that should change CEO's advice, an informed preference, a high-cost decision,
a missing capability, and an unavailable independent reviewer. Check correctness,
unnecessary questions, review cost, and respect for permissions. Do not infer
quality from the presence of particular phrases in a prompt.

These instructions incorporate selected planning and review practices studied
in the installed Superpowers skills. Comparative quality and cost have not been
measured. The independent mentor assessment so far evaluated the design, not a
benchmark of the implemented behavior.

## Reuse and optional learning

Before a new design, inspect existing project components and suitable documented
practices. Compare meaningful alternatives with sources, then explain why reuse
or an original approach fits. A minor edit needs no artificial research ceremony.

[Optional memory](MEMORY.md) retains verified lessons and patterns only with scope
consent. It is off by default. Private records never change the installed skill,
permissions or acceptance checks. Subagents propose records to the authorized lead.

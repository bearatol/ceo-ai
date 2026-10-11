# Working with CEO

CEO helps examine a decision and coordinate work. Start with the outcome and
constraints you know. CEO should question weak assumptions, explain alternatives,
and correct its own advice when the evidence changes. A simple request should
receive a short answer or direct action within existing permissions.

For dependent work, CEO keeps a compact plan and progress record. For a decision
with a high cost of error, it requests an independent mentor. The mentor receives
the relevant facts and alternatives, challenges the proposal, and recommends
the smallest useful check. It does not approve spending, grant access, or replace
a mandatory security review. The normal limit is one assessment and one focused
follow-up. Settled preferences should not be debated again without new evidence.

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

The scanner reads `skills/*/SKILL.md` and `agents/*.md`, fingerprints those files,
and reports missing, fresh, or stale cache state. Freshness covers those files,
not referenced scripts or resources. Entries remain `present-unverified` until
the host, permissions, compatibility, and required resources are checked.
Malformed metadata, duplicates, symlinks, nonregular files, and scan limits
produce an error. A failed scan leaves the previous cache untouched and it must
be treated as stale. Refresh writers use a nonblocking directory lock; a second
cooperating writer is refused. Keep the selected directory trusted against
noncooperating writers: advisory locking cannot protect cache ownership from
another process that can replace files there.

This utility requires POSIX descriptor and no-follow operations. It deliberately
refuses symlinked roots and components. Other layouts, linked installations,
native host inventories, and Windows require the host's approved read-only
discovery mechanism. CEO should report this limitation instead of widening the
scan or pretending that no capability exists. The scanner does not parse full
YAML or native TOML agent wrappers; it extracts simple frontmatter identity and
declared access without executing package content.

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

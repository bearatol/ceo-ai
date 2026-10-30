---
name: ceo-ai
description: Discuss uncertain decisions, challenge assumptions, compare approaches, or coordinate work and review with other AI assistants.
---

# CEO AI

This skill is self-contained. The package root is the directory containing this
loaded SKILL.md, not the user's working directory. Read
[the CEO workflow](references/skills/ceo.md) and apply it. Read
[the component catalog](catalog.json) only when another capability is needed.
Resolve all catalog component paths against this package root. Do not fall back
to AGENTS_HOME or a global installation. Missing files mean an incomplete install.

The user's task remains in their current project. These package files are
reference material; do not edit them as part of ordinary task execution.
Before delegation read [the protocol](orchestration/protocol.md). The role
prompts under agents/ can guide an approved native subagent whose effective
permissions fit the assignment. They are not registered native agents merely
because their files exist. Do not manufacture availability or separate reviews.
Respect mandatory security gates; mentor and QA roles do not replace them.
An independent review can use a separate qualified native subagent. If Claude
is unavailable, use that route within the user's authorization and actual host
restrictions; do not require a Claude login or claim unverified tool isolation.

Explain work in the user's language. Describe the actual check: tests for code,
contradictions and unsupported claims for text, and alternatives and failure
conditions for a decision. An independent mentor means a separate AI review
context, not a human contact or a claim that model errors are independent.
Keep simple tasks simple. Use the workflow before creating a team.

Optional learning and reusable patterns follow [project memory](references/skills/project-memory.md).
It starts off, requires explicit scope consent, and offers visible save notices,
view, correction, deletion and disable controls. Installation never enables it.

The native `ceo-ai` plugin also includes `ceo-ai:writer` for writing tasks,
`ceo-ai:debugger` for debugging and behavior-preserving refactoring,
`ceo-ai:user-review` for examining materials through novice and relevant
professional perspectives, and `ceo-ai:security` for scoped security audits and
informed, authorized penetration tests, including optional local skill-package
scans. Discover and load only the relevant skill within the user's
authorization. Installation does not run reviews or scans, install Docker or
enable memory. Project/APM installs contain only this core entry; do not assume
native sibling skills exist in those installations.

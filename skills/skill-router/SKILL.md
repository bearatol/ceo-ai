---
name: skill-router
description: Select the smallest useful set of installed skills for a task.
---

# Skill Router

Use at the start of a task when several ecosystem capabilities may apply.

1. Resolve the ecosystem root from explicit host context or configured
   AGENTS_HOME. Read its catalog.json and the task packet if available.
   For this standalone checkout, use its own root; do not guess a global path.
2. Extract the task domain, deliverable, risk, dependencies, and host limits.
3. Inspect all plausible catalog matches, not only the CEO recommendations.
4. Rank skills by material contribution and remove redundant workflows.
5. Select every useful skill that fits the task scope, context, and permissions.
6. Load each selected `SKILL.md` completely before applying it.
7. If a capability is missing, use `capability-discovery`; do not pretend it
   exists.
8. Record considered, applied, omitted, and missing skills in the result.

For a subagent, selection is autonomous: do not ask the CEO or user to approve
ordinary method choices. Ask only when alternatives change scope, permissions,
cost, external effects, or the intended deliverable. CEO suggestions are hints,
not a skill allowlist. A skill never grants tools, data, paths, or network access.

---
name: context-engineering
description: Build compact, reliable context packets, summaries, and agent handoffs without reducing decision quality.
---

# Context Engineering

Use when a task has long history, multiple agents, large repositories, or
repeated model calls.

## Workflow

1. Define the exact next decision, owner, deliverable, and quality bar.
2. Scan compact metadata first. Load full files only when their metadata matches
   the task or when evidence is missing.
3. Gather authoritative inputs that can change the decision. Label assumptions,
   stale context, conflicts, and unresolved risk.
4. Replace raw history, repeated logs, and large outputs with stable references
   plus the smallest evidence excerpt needed to act.
5. Preserve exact interfaces, errors, constraints, user decisions, provenance,
   and acceptance criteria.
6. Give each agent a bounded packet with relevant paths, selected skill paths,
   exclusions, permissions, and an explicit output contract.
7. Prefer artifact references over copying content between agents. Never place
   secrets or unrelated private context in a packet.
8. Refresh the packet only when facts change; remove superseded plans and stale
   conclusions.
9. Validate compression by asking whether a competent specialist can act and
   verify the result without rediscovering omitted evidence.

## Quality-preserving budget

Use a soft budget, not blind truncation. Keep high-signal facts and discard
duplication before detail. Escalate the budget when uncertainty, safety, or
acceptance evidence would otherwise be lost. Track useful evidence per packet,
not token reduction alone.

## Output contract

Provide an objective, owner, relevant facts, decisions, authoritative artifacts,
constraints, exclusions, open questions, next action, and confidence note.
Compression succeeds only when another agent can act correctly and verify the
result without rediscovering omitted context.

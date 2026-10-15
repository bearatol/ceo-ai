# Technical approach check

Evaluate the first implementation recommendation and the evidence inspected
before it. Later citations do not repair an earlier unsupported choice.
Run baseline and candidate with identical fixtures and prompts.
Record outcome, evidence order and tool calls. These are behavioral scenarios,
not assertions that particular phrases exist in the skill.

| Scenario | Expected behavior before recommending an implementation |
| --- | --- |
| Add a password visibility eye button in a Mantine project; provide a wrapper, installed version and a custom rightSection. | Inspect the input, wrapper and version; check the matching PasswordInput capabilities and toggle interaction. Choose reuse, adaptation or custom work with a concrete reason. |
| Same password request described as a tiny change; minimize cost. | Perform the same bounded approach check without broad research or a team. Do not select a custom toggle merely because it is familiar. |
| Fix a spelling error in a button label. | Inspect the relevant text and make the scoped recommendation. No component survey or external lookup is needed. |
| An existing wrapper already provides the requested behavior, with applicable inspected evidence. | Reuse it with a short explanation. Do not repeat external research solely to demonstrate compliance. |
| Available documentation describes a different library version. | Check applicability; do not present newer behavior as verified for the installed version. Label unresolved compatibility explicitly. |
| Network unavailable and local evidence leaves component behavior uncertain. | State the gap and a provisional approach or next check. Do not claim that no ready-made solution exists. |
| A ready-made component fails a concrete project constraint. | Identify the mismatch before recommending custom implementation. Existing components are not automatically preferred regardless of fit. |
| User asks for a plan before any edits. | Inspect evidence before selecting the implementation. An inspection-only plan may precede evidence; the check introduces no extra approval round. |

Accept only when the recommendation distinguishes inspected evidence from
assumptions and explains the choice. A source name alone is not evidence of fit.
Reject unnecessary searches, forced comparisons and agent teams for trivial work.

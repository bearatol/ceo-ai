---
name: software-delivery
description: Deliver bounded software changes using behavior-first TDD and proportional review.
---

# Software Delivery

1. Confirm the outcome, interfaces, constraints, and acceptance evidence. Inspect
   the relevant implementation and preserve unrelated work.
2. For dependent work, write a compact plan with exact files, ownership,
   interfaces, test cases, and verification commands. Routine reversible edits
   need only a short scope check. Follow existing authorization requirements.
3. For new code behavior or a bug fix, write a focused test first. Observe its
   failure for the missing/wrong behavior; import errors and broken fixtures do
   not count. Test observable results, not copies of implementation logic.
4. Implement the smallest passing change. Run the focused test and relevant
   existing checks; refactor with tests passing. Record meaningful red/green
   evidence. Add boundary and failure cases where consequences justify them.
5. Review requirements coverage and implementation quality. Use independent
   review when required; batch trivial related edits. Do not rerun unchanged
   checks without a reason. A worker's self-review does not satisfy a mandatory
   independent review.
6. Run required integration/repository checks and inspect the exact final diff.
   Report pre-existing failures separately; never claim a green suite from one
   passing test. Apply the mandatory security gate when triggered.

For investigation, document observations and uncertainty. For prose or formatting,
use direct review rather than artificial tests. Preserve user files; do not delete
existing implementation merely to manufacture a test-first history. If the cycle
was not followed, report that limitation and verify the behavior honestly.

Return changed artifacts, test commands and outcomes, assumptions, and remaining
risks. Keep task progress and relevant review decisions recoverable.

# Evidence, reporting and retesting

Keep output useful at the user's requested depth. Start with the most important
confirmed outcomes and practical priorities. Never claim a tool ran, a request
succeeded, a vulnerability was reproduced, cleanup completed, or an independent
review occurred without retained evidence for that claim.

## Assessment record

Record scope and exclusions, tested revision/environment and time, agreed ROE,
actual tools/versions and methods, actions performed and meaningful side effects,
and the evidence needed to assess conclusions. Keep approvals tied to the
corresponding actions. Store only where authorized, with agreed access and
retention; prefer sanitized private evidence to source dumps or public artifacts.
Do not expose credentials, personal records, private endpoints or raw payloads
unnecessarily in chat, screenshots, links, external searches or tool reports.

Separate confidence and execution state:

- **Suspected:** evidence suggests a weakness; state the missing proof.
- **Confirmed by analysis:** the reviewed data/control flow establishes a defect;
  explain the reasoning and say that exploitation was not attempted.
- **Reproduced in the approved test:** describe the observed minimum proof, tested
  conditions, fixture and scope. Do not extrapolate it to other environments.
- **Not reproduced / inconclusive:** explain what was attempted and what it can
  and cannot rule out. A failed exploit does not prove a control is secure.

## Finding contract

For each material finding include a stable ID, concise title, exact sanitized
file/line or endpoint/control, evidence and its state above, attacker prerequisites,
reachability, impact, severity rationale and confidence. Include counterevidence,
mitigations and uncertain assumptions. Map to a verified applicable CWE/control/
test ID if useful; do not invent IDs or CVEs to make a report look authoritative.

Use [FIRST CVSS v4.0](https://www.first.org/cvss/v4.0/specification-document)
when numeric scoring is useful and the necessary facts are available. Supply
the vector, version and rationale; use a verified calculator/implementation for
the score. Otherwise give justified qualitative severity and explain the missing
facts. Distinguish technical severity from the user's remediation priority,
considering exposed assets, sensitive data, likelihood and business consequences.

Recommend a specific fix at the responsible boundary and a way to verify both
the restored security property and important normal behavior. Deduplicate the
same root cause while listing affected locations. Do not inflate uncertain
signals or downgrade a confirmed issue merely because a scanner missed it.

## Coverage and closure

State what was checked, blocked, declined, excluded, failed, unavailable or not
applicable, with reasons. Separate completion of the agreed procedure from
security confidence: no findings means no findings under those conditions.
Unsupported formats, unreadable files, missing credentials/tools and excluded
secrets are gaps, not a clean result. Preserve the adapter's own incomplete
status even when a separate assistant review produced useful observations.

Report created test accounts/artifacts, actual changes and cleanup/recovery
verification. Stop at agreed proof; do not retrieve additional sensitive data
for the report. Report a suspected live exposure privately with containment
advice rather than disclosing its value or notifying outsiders without approval.

If fixes are requested, establish the changed files/systems and preserve the
original finding. Retest only within still-valid authorization for the new
revision and actions; request renewed consent when risk or scope changes. Report
fixed, partly fixed, still present or unverified with evidence. Neither a patch
nor a retest grants permission to deploy. Claim no certification, guaranteed
absence of vulnerabilities, universal pentest coverage or independent isolation.

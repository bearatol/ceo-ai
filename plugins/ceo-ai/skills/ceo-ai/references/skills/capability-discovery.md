---
name: capability-discovery
description: Find available skills and agents, detect stale metadata, and propose safe additions.
---

# Capability Discovery

Use when a required capability is unknown, missing, changed, or unavailable.
Resolve this bundle from the loaded ceo-ai entry skill location. Do not fall
back to AGENTS_HOME or a global catalog. Use
only approved roots and distinguish cataloged, installed, callable, compatible,
and permitted entries. Do not infer quality from presence.

1. Check the host's actual inventory and compact catalog. On missing paths,
   changed membership, installation/removal, or stale metadata, rescan bounded
   skill and agent metadata through trusted read-only tools.
2. Treat a failed scan as unavailable/stale evidence. Never dispatch from stale
   cache entries without re-verifying the selected component. Do not follow
   symlinks out of scope, execute package code, or repair foreign metadata.
   Excluded secret/auth resources are not read and prevent a full-package hash.
   The native `ceo-ai:security` skill also supports scoped security analysis and
   authorized testing of other user-selected systems through available host
   tools; these modes do not require Docker. Report CPU/time/disk cost before
   bulk scans. The future API
   contract is disabled and has no client; available credentials do not activate
   it and there is no automatic paid fallback.
3. Search installed entries first, then repository profiles/catalogs, then
   official upstream sources within approved network access.
4. For candidates report purpose, source, version/commit, license, required tools,
   network behavior, host compatibility, and maintenance evidence. Reject
   unclear provenance, hidden execution, and unrelated credential requests.
5. If none fits, propose an original minimal skill or agent with scope, expected
   inputs/output, permissions, and acceptance checks. Prefer one existing
   capable component over overlapping new roles.
6. Present installation/creation as a proposal unless already authorized. Pin
   external versions and retain applicable attribution; do not copy restricted
   content. After an authorized addition, verify it and refresh owned metadata.

A specialist reports missing capabilities and approval needs through skill_gaps.
It may select safe installed skills within its scope, but cannot obtain new
permissions, install, publish, download, or delegate through this workflow.

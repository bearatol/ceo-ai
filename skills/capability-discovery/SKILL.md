---
name: capability-discovery
description: Find available skills and agents, detect stale metadata, and propose safe additions.
---

# Capability Discovery

Use when a required capability is unknown, missing, changed, or unavailable.
Resolve the ecosystem location from supplied host context or AGENTS_HOME. Use
only approved roots and distinguish cataloged, installed, callable, compatible,
and permitted entries. Do not infer quality from presence.

1. Check the host's actual inventory and compact catalog. On missing paths,
   changed membership, installation/removal, or stale metadata, rescan bounded
   skill and agent metadata through trusted read-only tools.
2. If the tool checkout supplies scripts/ceo_inventory.py, it can scan an explicit
   root containing skills/ and agents/. Its default is read-only; --refresh
   writes only its separate owned cache when that write is authorized. Read its
   documented host/format limits. Do not invent this command on another host.
3. Treat a failed scan as unavailable/stale evidence. Never dispatch from stale
   cache entries without re-verifying the selected component. Do not follow
   symlinks out of scope, execute package code, or repair foreign metadata.
4. Search installed entries first, then repository profiles/catalogs, then
   official upstream sources within approved network access.
5. For candidates report purpose, source, version/commit, license, required tools,
   network behavior, host compatibility, and maintenance evidence. Reject
   unclear provenance, hidden execution, and unrelated credential requests.
6. If none fits, propose an original minimal skill or agent with scope, expected
   inputs/output, permissions, and acceptance checks. Prefer one existing
   capable component over overlapping new roles.
7. Present installation/creation as a proposal unless already authorized. Pin
   external versions and retain applicable attribution; do not copy restricted
   content. After an authorized addition, verify it and refresh owned metadata.

A specialist reports missing capabilities and approval needs through skill_gaps.
It may select safe installed skills within its scope, but cannot obtain new
permissions, install, publish, download, or delegate through this workflow.

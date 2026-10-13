# Security indexing integration

Status: user approved continuation on 2026-10-13 after the comparative benchmark.
This plan implements the next stage proposed in [the report](REPORT.ru.md).
Pre-implementation and final independent reviews use the user's previously
approved instruction-constrained reviewer exception; technical isolation of the
review agent is not asserted. Scanner container isolation is separate.

Pre-implementation review: `PASS_WITH_WARNINGS`. Accepted corrections SEC-01–03:
always recompute builtin findings rather than trust mutable cached results;
reject hard-linked files and exclude secret/auth resources without opening them;
strictly validate vendor IDs, paths, severities and line ranges and discard prose.
These are implementation requirements within the approved scope.

## Scope and ownership

- Lead: descriptor-based package snapshots and inventory schema migration in
  `.apm/skills/ceo-ai/scripts/ceo_inventory.py`, inventory tests, publication
  allowlist, generated bundle/plugin, integration docs and final acceptance.
- Static-analysis specialist: original, dependency-free `ceo_security.py` and
  `tests/test_security.py`; bounded EN/RU capability/risk rules and API-off contract.
- Container-adapter specialist: `ceo_security_nvidia.py` and
  `tests/test_security_nvidia.py`; explicit offline execution and strict output
  normalization against the same bounded package snapshot.
- Independent reviewer: canonical pre-implementation security review and exact
  final diff review. Reviewers do not edit or execute the implementation.

## Required behavior

1. Index an explicit approved root only. Fingerprint every admitted file in a
   skill package, including nested resources, with deterministic paths and bytes.
   Flat agent files retain an explicit narrower scope. Preserve no-follow file
   descriptors, bounded reads, depth/count/byte/time limits and atomic cache
   replacement. No code or instructions from a package are executed.
2. Add advisory security metadata during indexing: heuristic capability tier,
   severity, coverage, provenance and policy decision remain separate. T0–T4
   describe observed capabilities, not trust or enforced permissions. No result
   grants execution authority. Errors/unsupported input never become clean.
3. Bind results to bundle, scanner, rules and policy identity. Owned schema-1
   caches become stale and migrate only on explicit refresh; foreign or future
   schemas are refused. Failed refresh preserves the previous cache. Rechecking
   hashes is necessary to establish freshness; a cache is not an attestation.
4. Default indexing is local and does not start Docker, download dependencies,
   invoke a model, read API credentials or use the network. The optional NVIDIA
   adapter requires an explicit invocation, approved staging workspace and
   immutable locally available scanner image. Use a private snapshot, non-root,
   read-only container, no network, no capabilities, resource/time/output bounds,
   no inherited credentials and no host socket mounted in the container.
5. Treat scanner output as untrusted structured data. Validate version, coverage,
   paths, severities and bounded fields; discard vendor safety badges and text
   snippets. Failed/incomplete scans stay incomplete. Do not fetch referenced URLs.
6. Expose only a disabled future API contract describing explicit opt-in, data
   approval, cost estimate and hard budget requirements. No HTTP client, endpoint,
   credential storage, implicit activation or paid fallback in this stage.

## Verification and distribution

Observe meaningful tests fail before implementing new behavior, then verify:
supporting-file add/change/remove, schema migration, spoofed/stale cache evidence,
symlinks/FIFOs, file/tree mutation, depth/size/time bounds, missing references,
binary content, delegated approval bypass, quoted attacks, Russian paraphrases,
scanner format/version failures, time/output limits and credential isolation.

Run the optional adapter once with the already prepared NVIDIA payload packaged
in a local immutable image, without downloads or new dependencies. Use synthetic
fixtures only. Run inventory/security tests, existing repository tests, doctor and
documentation checks under 30-second command bounds. Regenerate the publication
manifest and plugin mirror through the repository's existing tools.

No installed user plugin, global agent control plane or Mac skill directories
are modified or scanned in this implementation stage. After verification, the
next audit uses CEO AI against explicitly approved roots. No release or public
publication is part of this stage.

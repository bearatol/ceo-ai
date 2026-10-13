# Offline scanner experiment

Experiment date: 2026-10-13. Scope: synthetic skills and two agent-format probes.
This directory records the first benchmark and its subsequent integration work.
The benchmark itself did not change the product. The follow-up
[integration plan](INTEGRATION_PLAN.md) adds local indexing checks to the source
bundle; the installed user plugin and global Mac directories remain unchanged.
See the [integration verification](INTEGRATION_RESULTS.md) for follow-up evidence.

Read [the findings and integration proposal](REPORT.ru.md), [fixture labels](FIXTURES.md),
and [machine-readable results](results/summary.json).

## Reproduction inputs

| Engine | Version | Source | License |
|---|---|---|---|
| Cisco Skill Scanner | 2.2.2 | [release](https://github.com/cisco-ai-defense/skill-scanner/releases/tag/2.2.2) | Apache-2.0 |
| NVIDIA SkillSpector | 2.12.0 | [commit c7958a3](https://github.com/NVIDIA/SkillSpector/commit/c7958a3268d9498644b22edb75d0f051bbc8cbfc) | Apache-2.0 |
| AgentVerus | 0.8.1 | [upstream](https://github.com/agentverus/agentverus-scanner) | MIT |

The tested npm artifact is bound by its integrity hash, not a verified mapping to
a GitHub commit. License identifiers are inventory evidence, not a license audit.

`engines.json` pins official Python and Node base image digests. The tested platform
was Linux ARM64 inside Docker on macOS. `results/*-requirements.lock` and
`results/*-wheels.json` pin the resolved Python artifacts. These are environment-
specific locks, not the vendors' own release lockfiles. The NVIDIA set includes
Hatchling and its build dependencies. `results/agentverus-package-lock.json` records
the complete npm resolution, including integrity hashes. No upstream source code,
wheels or installed dependencies are included in the tracked experiment files.

## Preparation used in this experiment

Preparation is a separate, network-enabled step. It is not part of indexing or
the benchmark runner. All installers ran in disposable containers as UID 501,
with no capabilities, no-new-privileges, a read-only root, resource limits, and
only the appropriate `.runtime/<engine>` output directory mounted writable.
Docker used an empty `.runtime/docker-config`; no host credentials, HOME or Docker
socket were mounted into any container. All shell invocations were bounded to
30 seconds, with 25-second inner installer timeouts.

1. Pull the official base images; record and subsequently use the digests in
   `engines.json`. Mutable tags were used only to discover these initial digests.
2. Download Cisco 2.2.2 and dependencies as wheels only. No source-build fallback
   is allowed. Download timeouts occurred; completed pip HTTP-cache wheels were
   recovered only when their SHA256 matched cached PyPI index metadata. Resolve
   the resulting wheel set offline and save exact versions and hashes.
3. Fetch NVIDIA's pinned commit archive. Record its SHA256; reject absolute paths,
   traversal, symlinks, special files, excessive members and excessive size. Keep
   only `src`, `pyproject.toml`, `README.md`, and `LICENSE`. Download binary wheels
   for declared runtime dependencies and Hatchling 1.31.0. Install those offline
   using `--require-hashes`, then build the NVIDIA wheel offline using the standard
   Hatchling backend with no build isolation or dependency resolution. Hash and
   install that wheel with `--no-deps --require-hashes`. No custom build hooks were
   declared in the reviewed project manifest; this is not an audit of Hatchling.
4. Install `agentverus-scanner@0.8.1` inside the Node container with
   `--omit=dev --ignore-scripts --no-audit --no-fund`. Preserve its lockfile.
   Remove only the generated `.bin` symlinks: the benchmark calls the known JS
   entrypoint directly and rejects symlinks in mounted trees.
5. Move download caches and wheel archives to `.runtime/artifacts`, outside
   mounted engine directories. Record the prepared engine tree hashes. Containers
   install only under the experiment directory; no host Python/npm installation
   is changed. Final engine payloads live under `.runtime/.venv/<engine>` so the
   repository's existing documentation checks skip installed dependency docs.
   Raw historical reports retain the original preparation-time mount paths.
   Cisco installation needed a 1 GiB temporary filesystem and 2 GiB
   memory; the initial 256 MiB preparation limit failed with ENOSPC.

The preparation commands are deliberately not an automatic downloader bundled
with CEO AI. A future adapter must add its own provenance and installation policy.
Hashes record the artifacts used; they do not prove that upstream packages are safe.

## Running an already prepared experiment

The local ignored `.runtime` directory contains the prepared environments and
raw results. A fresh checkout requires preparing those environments first using
the exact artifacts above. The runner never installs dependencies or pulls images.

From the repository root, run one case per outer timeout, using the actual local
Docker Unix socket. This socket is used by the host Docker client only.

```sh
gtimeout 30s python3 -B research/security-scanners/bench.py \
  --docker-host unix:///var/run/docker.sock \
  --engine nvidia --case a07-linked-reference \
  --output results/recheck-nvidia-reference.json
```

Use a new output filename: existing results are never intentionally overwritten.
With no selection flags the runner selects all available engines and cases, but
that full run can exceed a 30-second outer timeout. The recorded experiment used
small batches after measuring startup time. Run one case per invocation when
timeouts must themselves be captured as a complete JSON report.

Each scan gets `--network none`, read-only engine and fixture mounts, a read-only
root, non-root UID/GID, dropped capabilities, no-new-privileges, 128 PIDs, 2 CPUs,
1536 MiB memory and a 256 MiB `noexec,nosuid` temporary filesystem. The runner
does not inherit host environment variables into its Docker client or containers.
Scanner subprocesses have a 25-second deadline, 2 MiB combined output cap and
bounded cleanup of only their own randomly named container. Fixtures are read as
data; no skill, script or instruction from a fixture is executed.

`preflight.py` must be run inside a container with the same restrictions before
admitting scanner results. The recorded [probe](results/preflight.json) confirmed
EROFS for root/fixture writes, non-root UID, no effective capabilities,
no-new-privileges, and ENETUNREACH for an external connection. This is not a
container-escape assessment. Container isolation is separate from the explicitly
accepted instruction-based isolation of the independent review agent.

## Results and boundaries

The runner stores raw output under `.runtime/outputs` and structured raw reports
under a new `results/` filename. Completed raw reports from this experiment were
moved to `.runtime/reports`; their hashes are retained in `results/summary.json`.
Raw scanner output and fixture content are untrusted data. They are never shell
commands or instructions for the reviewing assistant. JSON serialization escapes
control characters; terminal progress contains only validated IDs and statuses.
Do not paste raw findings into an active instruction context or render them as HTML.

The compact summary preserves every case, finding identifier/severity, output
hash, process exit code, duration and available coverage status. `execution_finished`
means the process ended, not that its input is safe. A parsed JSON object alone
does not establish completeness. The summary checks the expected per-engine schema.
Severity scales are vendor-specific and have not been calibrated against each other.

The local runner expects trusted preparation files and an exclusively owned
workspace. Its path checks are not a race-proof filesystem broker for hostile
concurrent writers, and it is not the production admission gate. Production use
needs immutable snapshots and verified payload/rule hashes before each scan.

## Verification

```sh
gtimeout 30s python3 -B -m unittest discover \
  -s research/security-scanners -p 'test_*.py'
```

The 15 tests cover path traversal, symlinks, oversized manifests, image pinning,
timeouts, combined output bounds, environment isolation, container arguments and
fail-closed preflight checks under Python optimization (`-O`).
The fixture author observed assertion failures before implementing the runner;
the final suite passes. The preflight is an executed boundary probe rather than
a unit-test imitation of container settings. Independent review identified that
`assert` checks could disappear under `-O`; four simulated invalid states first
reproduced the defect, then passed after explicit checks replaced the assertions.
The corrected probe also passed inside the real restricted container under `-O`:
[optimized preflight evidence](results/preflight-optimized.json).
No production indexer behavior has been implemented or validated by this experiment.

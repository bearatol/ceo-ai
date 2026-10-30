# Optional scan with Docker

[English](DOCKER_SCAN.md) · [Русский](DOCKER_SCAN.ru.md) · [简体中文](DOCKER_SCAN.zh-CN.md)

Start with the [builtin scan](QUICKSTART.md). This optional route adds NVIDIA
SkillSpector 2.12.0 through Security inside the CEO AI plugin. It uses local
CPU, RAM and disk, without paid APIs or LLM calls; your assistant's chat tokens
are separate. There is no cloud fallback. This route checks skill packages only. Ordinary
Security audits use the host model and available tools without this Docker setup.

Send this request to your agent, replacing the path:

```text
Prepare and run an additional security check for the skill at /path/to/skill.
Check my system and prepare the required local scanner if supported.
Reuse existing permissions and ask only for missing access or installation approval.
Explain findings and anything the check could not cover.
```

The agent checks prerequisites, prepares the reviewed image, tests it on a
synthetic fixture and scans the selected package. You do not need to find image
IDs, engine versions or Docker socket addresses yourself. Preparation uses local
CPU, RAM and disk, and downloads build inputs. The scan itself has no network,
LLM or paid API calls. A request only to scan does not authorize installing tools
or fetching/building an image. The commands below are the manual alternative.

## 1. Check the system and local Docker endpoint

Use macOS or Linux (POSIX), host Python 3.10+, and a local **native ARM64 Docker
host running Linux ARM64 containers**. The image uses Python 3.12. This recipe
does not cover Intel/AMD64, emulation, native Windows or remote Docker daemons.
The image recipe is not shipped in the installed skill. Read its `VERSION`, then
use a trusted [upstream CEO AI checkout](https://github.com/bearatol/ceo-ai) at the
release commit matching that version. Record and verify the commit before reading
`tools/security-image/`, this guide and the synthetic fixture. Fetching needs
approved network and destination access. Do not use a latest branch or an
unreviewed working tree. Run the manual commands from that pinned checkout, but
use the installed skill's bundled adapter. Missing bundled runtime files mean an
incomplete installation, not permission to fetch substitutes.

If Docker is missing, follow the [official Docker installation guide](https://docs.docker.com/get-started/get-docker/)
for your system and start the daemon. Installation and system permission changes
need authorization. Reuse existing approval and ask only for missing scope;
loading the plugin never triggers installation. Check:

```sh
python3 --version
docker context inspect --format '{{.Endpoints.docker.Host}}'
docker buildx version
```

Before any daemon command, resolve the context endpoint locally and verify that
it is an approved local Unix socket with a trusted owner and location. Stop on
TCP, SSH, remote or unexplained endpoints. Do not run `docker version` or `info`
to discover whether an unknown endpoint is local.

Set `CEO_SCAN_SOCKET` to that verified endpoint. Inspect the local Buildx builder
configuration and every node endpoint before using the builder. Choose an
existing builder with the `docker` driver bound to this same socket. Stop if that
cannot be established. Do not bootstrap an unknown builder or trust the currently
selected builder merely because the Docker context is local. Set
`CEO_SCAN_BUILDER` to its verified name. Then run:

```sh
CEO_SCAN_SOCKET='unix:///replace-with-the-approved/docker.sock'
CEO_SCAN_BUILDER='replace-with-the-verified-local-docker-builder'
docker --host "$CEO_SCAN_SOCKET" version
docker --host "$CEO_SCAN_SOCKET" info --format '{{.OSType}}/{{.Architecture}}'
docker --host "$CEO_SCAN_SOCKET" buildx inspect "$CEO_SCAN_BUILDER"
```

Keep this explicit endpoint for building, inspecting, version checks and scanning.

Require Linux `aarch64`/`arm64` and a local `unix:///…` socket. Record that socket
for the adapter. BuildKit must support `ADD --checksum` and `RUN --network=none`.
If Buildx is missing, follow the [official installation instructions](https://github.com/docker/buildx#installing)
within approved scope; do not fall back to the legacy builder.
Install `ceo-ai`, which includes Security, using the [plugin steps](PLUGINS.md#security).
Installation itself does not authorize a scan or an image build.

## 2. Build the pinned scanner image

Review the five files in `tools/security-image/` before authorizing the build.
Only that directory is the build context; never substitute your home or project
root. Fetching the base image, PyPI wheels and pinned GitHub source needs network
access. The scanner's build/install stage then runs without network as a non-root
user. The entire initial build is therefore **not offline**.

```sh
docker --host "$CEO_SCAN_SOCKET" buildx build --builder "$CEO_SCAN_BUILDER" --load -t ceo-ai-skillspector:2.12.0 tools/security-image
```

The recipe pins the base digest and source checksum, and uses hashed binary
dependencies. These are integrity checks, not a safety certificate. See Docker's
[`ADD --checksum`](https://docs.docker.com/reference/dockerfile/#add---checksum)
and [`RUN --network=none`](https://docs.docker.com/reference/dockerfile/#run---networknone),
and pip's [secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/).
Do not remove hash checks or enable build network as a workaround.

## 3. Record the image ID and check its version

```sh
docker --host "$CEO_SCAN_SOCKET" image inspect --format '{{.Id}}' ceo-ai-skillspector:2.12.0
```

Copy the full returned `sha256:…` into the variable below. Replace the socket with
the approved local one from step 1. A tag alone is not accepted by the adapter.

```sh
CEO_SCAN_IMAGE='sha256:replace-with-the-full-image-ID'
docker --host "$CEO_SCAN_SOCKET" run --rm --pull=never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 65534:65534 --pids-limit 64 \
  --memory 512m --cpus 1 "$CEO_SCAN_IMAGE"
```

Expected version output: `SkillSpector 2.12.0`. This checks the image entry point,
not the full scan. Use the same local daemon for building, inspecting and scanning.

## 4. Test a synthetic skill through the real adapter

Choose a **new**, approved private directory outside the scanned package. Its
ancestors must be trusted and not writable by other users. Replace the example
path; do not change permissions on an existing directory to force acceptance.

Set `CEO_SCAN_ADAPTER` to `scripts/ceo_security_nvidia.py` inside the loaded
installed `security` skill, not to a guessed cache or downloaded substitute.

```sh
CEO_SCAN_ADAPTER='/absolute/path/to/loaded/security/scripts/ceo_security_nvidia.py'
mkdir -m 700 /approved/private-scan-workspace
python3 -I -B "$CEO_SCAN_ADAPTER" \
  --package research/security-scanners/fixtures/skills/b01-summary \
  --workspace /approved/private-scan-workspace \
  --image "$CEO_SCAN_IMAGE" --version 2.12.0 --docker-host "$CEO_SCAN_SOCKET"
```

The smoke check must return JSON with `status: COMPLETE` and exit code `0` before
proceeding. This means the adapter completed, not that a package is safe. Version
output alone does not replace this check. This guide does not claim an end-to-end
test on your machine.

## 5. Check one approved skill

Repeat the adapter command with `--package /approved/skill-directory`, a directory
containing `SKILL.md`. Keep the approved private workspace, image ID, version and
socket. For an installed plugin, use `scripts/ceo_security_nvidia.py` relative to
the loaded `security/SKILL.md`, not a guessed cache path. Approve the report's
private destination before saving the JSON.

For the skill interface, start a new chat and select `ceo-ai:security`
in Codex or invoke `/ceo-ai:security` in Claude Code.

The adapter scans a read-only snapshot without network or LLM calls. It does not
execute the skill. It refuses/excludes unsupported resources; a partial result
must stay incomplete. Exit `2` means incomplete, not “no findings”.

## If it stops

| Problem | Next step |
| --- | --- |
| Docker unavailable or wrong socket | Start the approved local daemon and verify its Unix socket; do not expose it over TCP. |
| Unsupported architecture or BuildKit syntax | Stop. This recipe needs native ARM64 and a compatible builder; do not bypass the checks. |
| Download/hash/version failure | Stop and review the pinned inputs; do not substitute a tag, unpinned dependency or newer scanner. |
| `unsafe_workspace` | Choose a new approved private directory with trusted ancestors; do not weaken permissions. |
| Timeout, skipped files or `INCOMPLETE` | Read the reason and coverage. Do not retry with a paid API or call it safe. |

After a crash, forced kill or daemon failure, inspect only this scan's leftover
resources before retrying. Never prune Docker globally. [Boundaries and cleanup](SECURITY_SCANNING.md).

Validation: unit/static checks passed. Buildx was unavailable in the validation
environment, so this recipe has not completed an end-to-end image build and scan there.

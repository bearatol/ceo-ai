# Optional scan with Docker

[English](DOCKER_SCAN.md) · [Русский](DOCKER_SCAN.ru.md) · [简体中文](DOCKER_SCAN.zh-CN.md)

Start with the [builtin scan](QUICKSTART.md). This optional route adds NVIDIA
SkillSpector 2.12.0 through Security Scan inside the CEO AI plugin. It uses local
CPU, RAM and disk, without paid APIs or LLM calls; your assistant's chat tokens
are separate. There is no cloud fallback.

Send this request to your agent; the manual steps follow below:

```text
Help me set up and run one optional local CEO AI Security check using this guide.
Check the platform, Python, Docker and Buildx first. Before installing tools,
downloading/building an image or accessing files, explain the exact scope;
reuse existing approvals and ask for any missing permission.
Use the reviewed tools/security-image recipe, verify the immutable image ID
and version 2.12.0, then test the synthetic skill through the real adapter.
Scan only the approved skill, with approved private workspace/report paths and Unix socket.
Do not use external APIs or run the skill's code. Keep gaps visible and trust unverified.
```

## 1. Check prerequisites and install the optional plugin

Use macOS or Linux (POSIX), host Python 3.10+, and a local **native ARM64 Docker
host running Linux ARM64 containers**. The image uses Python 3.12. This recipe
does not cover Intel/AMD64, emulation, native Windows or remote Docker daemons.
You need a reviewed CEO AI checkout containing `tools/security-image/` and the
generated optional adapter. Run the following commands from that checkout.

If Docker is missing, follow the [official Docker installation guide](https://docs.docker.com/get-started/get-docker/)
for your system and start the daemon. Installation and system permission changes
need separate approval; the plugin does not perform them. Check:

```sh
python3 --version
docker version
docker buildx version
docker info --format '{{.OSType}}/{{.Architecture}}'
docker context inspect --format '{{.Endpoints.docker.Host}}'
```

Require Linux `aarch64`/`arm64` and a local `unix:///…` socket. Record that socket
for the adapter. BuildKit must support `ADD --checksum` and `RUN --network=none`.
If Buildx is missing, follow the [official installation instructions](https://github.com/docker/buildx#installing)
only after separate approval; do not fall back to the legacy builder.
Install `ceo-ai`, which includes Security Scan, using the [plugin steps](PLUGINS.md#optional-ceo-ai-security).
Installation itself does not authorize a scan or an image build.

## 2. Build the pinned scanner image

Review the five files in `tools/security-image/` before authorizing the build.
Only that directory is the build context; never substitute your home or project
root. Fetching the base image, PyPI wheels and pinned GitHub source needs network
access. The scanner's build/install stage then runs without network as a non-root
user. The entire initial build is therefore **not offline**.

```sh
DOCKER_BUILDKIT=1 docker build -t ceo-ai-skillspector:2.12.0 tools/security-image
```

The recipe pins the base digest and source checksum, and uses hashed binary
dependencies. These are integrity checks, not a safety certificate. See Docker's
[`ADD --checksum`](https://docs.docker.com/reference/dockerfile/#add---checksum)
and [`RUN --network=none`](https://docs.docker.com/reference/dockerfile/#run---networknone),
and pip's [secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/).
Do not remove hash checks or enable build network as a workaround.

## 3. Record the image ID and check its version

```sh
docker image inspect --format '{{.Id}}' ceo-ai-skillspector:2.12.0
```

Copy the full returned `sha256:…` into the variable below. Replace the socket with
the approved local one from step 1. A tag alone is not accepted by the adapter.

```sh
CEO_SCAN_IMAGE='sha256:replace-with-the-full-image-ID'
CEO_SCAN_SOCKET='unix:///replace-with-the-approved/docker.sock'
docker run --rm --pull=never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 65534:65534 --pids-limit 64 \
  --memory 512m --cpus 1 "$CEO_SCAN_IMAGE"
```

Expected version output: `SkillSpector 2.12.0`. This checks the image entry point,
not the full scan. Use the same local daemon for building, inspecting and scanning.

## 4. Test a synthetic skill through the real adapter

Choose a **new**, approved private directory outside the scanned package. Its
ancestors must be trusted and not writable by other users. Replace the example
path; do not change permissions on an existing directory to force acceptance.

```sh
mkdir -m 700 /approved/private-scan-workspace
python3 -I -B plugins/ceo-ai/skills/security-scan/scripts/ceo_security_nvidia.py \
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
the loaded `security-scan/SKILL.md`, not a guessed cache path. Approve the report's
private destination before saving the JSON.

For the skill interface, start a new chat and select `ceo-ai:security-scan`
in Codex or invoke `/ceo-ai:security-scan` in Claude Code.

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

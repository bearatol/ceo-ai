# 使用 Docker 进行可选检查

[English](DOCKER_SCAN.md) · [Русский](DOCKER_SCAN.ru.md) · [简体中文](DOCKER_SCAN.zh-CN.md)

先做[内置检查](QUICKSTART.zh-CN.md)。本指南通过CEO AI 内的 Security 技能追加
NVIDIA SkillSpector 2.12.0 检查，消耗本地 CPU、内存和磁盘，不调用付费 API 或 LLM。
助手的对话 token 单独计算，没有云端备用服务。此路线仅检查技能包。
常规 Security 审查使用宿主模型和可用工具，无需此 Docker 准备过程。

把下面的请求发给助手，并替换路径：

```text
请为 /path/to/skill 中的技能准备并运行一次额外的安全检查。
检查我的系统，如果受支持，请准备所需的本地扫描器。
复用已有授权，只询问缺少的访问或安装权限。
说明发现的问题以及未能检查的内容。
```

助手会检查要求，按经过审查的方案准备镜像，用合成示例验证后再扫描选定的包。
你不需要自己查找镜像 ID、引擎版本或 Docker 套接字地址。准备过程消耗本地 CPU、
内存和磁盘，下载构建输入需要联网。扫描本身不联网、不调用 LLM 或付费 API。
仅要求扫描并不授权安装工具、下载或构建镜像。以下命令是手动设置的替代方式。

## 1. 检查系统和本地 Docker 端点

需要 macOS 或 Linux（POSIX）、主机上的 Python 3.10+，以及运行 Linux ARM64 容器的
本地**原生 ARM64 Docker 主机**。镜像内部使用 Python 3.12。本方案不覆盖 Intel/AMD64、
模拟运行、原生 Windows 或远程 Docker 守护进程。已安装技能不包含镜像构建方案。读取其 `VERSION`，使用与该版本发布提交一致的
[CEO AI 上游仓库副本](https://github.com/bearatol/ceo-ai)。在读取
`tools/security-image/`、本指南及合成示例前，验证并记录提交。下载需要获批的网络与
目标目录访问权限。不要使用最新分支或未审查的工作区。手动命令从固定提交的副本运行，
适配器则使用已安装技能内的文件。缺少随包运行时文件意味着安装不完整，不授权下载替代品。

如果尚未安装 Docker，请遵循适合系统的[官方安装指南](https://docs.docker.com/get-started/get-docker/)
并启动守护进程。安装和系统权限变更需要授权。复用已有授权，只询问缺少的范围。加载技能不会触发安装。检查：

```sh
python3 --version
docker context inspect --format '{{.Endpoints.docker.Host}}'
docker buildx version
```

在任何守护进程命令之前，从本地配置解析端点，确认它是获批的本地 Unix 套接字，
且所有者和位置可信。遇到 TCP、SSH、远程或无法解释的端点时停止。
不要通过运行 `docker version` 或 `info` 来判断未知端点是否在本地。

将验证后的地址写入 `CEO_SCAN_SOCKET`。使用 Buildx 前，检查本地构建器配置和每个
节点端点。选择已存在、使用 `docker` 驱动且绑定同一套接字的构建器。无法确认时停止。
不要 bootstrap 未知构建器，也不要默认信任当前构建器，本地 Docker context 并不证明
构建器在本地。将已验证的名称写入 `CEO_SCAN_BUILDER`，然后执行：

```sh
CEO_SCAN_SOCKET='unix:///replace-with-the-approved/docker.sock'
CEO_SCAN_BUILDER='replace-with-the-verified-local-docker-builder'
docker --host "$CEO_SCAN_SOCKET" version
docker --host "$CEO_SCAN_SOCKET" info --format '{{.OSType}}/{{.Architecture}}'
docker --host "$CEO_SCAN_SOCKET" buildx inspect "$CEO_SCAN_BUILDER"
```

构建、查看镜像、版本检查和扫描均使用此显式端点。

需要 Linux `aarch64`/`arm64` 和本地 `unix:///…` 套接字。记录该套接字供适配器使用。
BuildKit 必须支持 `ADD --checksum` 和 `RUN --network=none`。按
[插件说明](PLUGINS.md#security-安全审查)安装包含扫描技能的 `ceo-ai`。
安装本身不授权扫描或构建镜像。
如果缺少 Buildx，须在授权范围内遵循[官方安装说明](https://github.com/docker/buildx#installing)，
不要回退到旧版构建器。

## 2. 构建固定版本的扫描器镜像

批准构建前，检查 `tools/security-image/` 中的五个文件。仅将这个目录作为构建上下文，
不要改成主目录或整个项目。获取基础镜像、PyPI wheel 和固定的 GitHub 源码需要网络。
之后的扫描器构建与安装阶段以非 root 用户离线运行。因此，首次构建**并非全程离线**。

```sh
docker --host "$CEO_SCAN_SOCKET" buildx build --builder "$CEO_SCAN_BUILDER" --load -t ceo-ai-skillspector:2.12.0 tools/security-image
```

方案固定基础镜像 digest、源码 checksum 和二进制依赖哈希。这是完整性检查，不是安全认证。
相关机制见 Docker 的 [`ADD --checksum`](https://docs.docker.com/reference/dockerfile/#add---checksum)、
[`RUN --network=none`](https://docs.docker.com/reference/dockerfile/#run---networknone)
及 pip 的[安全安装](https://pip.pypa.io/en/stable/topics/secure-installs/)。
不要为绕过错误而关闭哈希检查或启用构建阶段网络。

## 3. 记录镜像 ID 并验证版本

```sh
docker --host "$CEO_SCAN_SOCKET" image inspect --format '{{.Id}}' ceo-ai-skillspector:2.12.0
```

将返回的完整 `sha256:…` 复制到下面变量中，并将套接字改为步骤 1 中已批准的本地地址。
适配器不接受只有 tag 的镜像引用。

```sh
CEO_SCAN_IMAGE='sha256:replace-with-the-full-image-ID'
docker --host "$CEO_SCAN_SOCKET" run --rm --pull=never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 65534:65534 --pids-limit 64 \
  --memory 512m --cpus 1 "$CEO_SCAN_IMAGE"
```

预期输出：`SkillSpector 2.12.0`。这只验证镜像入口，不代表整个扫描流程成功。
构建、查看 ID 和扫描必须使用同一个本地守护进程。

## 4. 用合成示例验证真实适配器

在待扫描包外选择一个**新的**、已批准的私密目录。父目录必须可信且不允许其他用户写入。
替换示例路径；不要修改已有目录的权限来强行通过检查。

将 `CEO_SCAN_ADAPTER` 设置为已加载、已安装的 `security` 技能内的
`scripts/ceo_security_nvidia.py`。不要猜测缓存路径或使用下载的替代文件。

```sh
CEO_SCAN_ADAPTER='/absolute/path/to/loaded/security/scripts/ceo_security_nvidia.py'
mkdir -m 700 /approved/private-scan-workspace
python3 -I -B "$CEO_SCAN_ADAPTER" \
  --package research/security-scanners/fixtures/skills/b01-summary \
  --workspace /approved/private-scan-workspace \
  --image "$CEO_SCAN_IMAGE" --version 2.12.0 --docker-host "$CEO_SCAN_SOCKET"
```

继续之前，试运行必须返回包含 `status: COMPLETE` 的 JSON 和退出码 `0`。
这意味着适配器完成了处理，并不证明包安全。版本输出不能替代这一步；本指南也不声称
已经在你的机器上完成端到端验证。

## 5. 检查一个获批技能

重复适配器命令，将参数改为 `--package /approved/skill-directory`，该目录须包含
`SKILL.md`。保留获批工作目录、镜像 ID、版本及套接字。使用已安装插件时，
从加载的 `security/SKILL.md` 所在目录找到 `scripts/ceo_security_nvidia.py`，
不要猜测缓存路径。保存 JSON 前先批准私密报告位置。

如需通过技能操作，请开启新会话，在 Codex 中选择 `ceo-ai:security`，
或在 Claude Code 中调用 `/ceo-ai:security`。

适配器检查只读副本，不联网、不调用 LLM，也不运行技能代码。不支持的资源会导致拒绝
或不完整结果。退出码 `2` 表示检查不完整，不表示没有发现问题。

## 如果中途停止

| 问题 | 下一步 |
| --- | --- |
| Docker 不可用或套接字错误 | 启动获批的本地守护进程并检查 Unix 套接字，不要通过 TCP 暴露它。 |
| 架构或 BuildKit 语法不受支持 | 停止。本方案要求原生 ARM64 和兼容构建器，不要绕过检查。 |
| 下载、哈希或版本失败 | 检查固定输入，不要换成 tag、未固定依赖或新版扫描器。 |
| `unsafe_workspace` | 选择新的获批私密目录和可信父目录，不要放宽权限。 |
| 超时、跳过文件或 `INCOMPLETE` | 阅读原因与覆盖范围，不要改用付费 API，也不要将结果称为安全。 |

崩溃、强制终止或守护进程失败后，只检查本次扫描留下的资源再重试。不要执行全局 Docker
清理。参见[边界与清理说明](SECURITY_SCANNING.md)。

验证情况：单元和静态检查已通过。验证环境缺少 Buildx，因此尚未在该环境中完成
镜像构建及端到端扫描。

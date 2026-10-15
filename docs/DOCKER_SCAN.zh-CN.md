# 使用 Docker 进行可选检查

[English](DOCKER_SCAN.md) · [Русский](DOCKER_SCAN.ru.md) · [简体中文](DOCKER_SCAN.zh-CN.md)

先做[内置检查](QUICKSTART.zh-CN.md)。本指南通过CEO AI 内的 Security Scan 技能追加
NVIDIA SkillSpector 2.12.0 检查，消耗本地 CPU、内存和磁盘，不调用付费 API 或 LLM。
助手的对话 token 单独计算，没有云端备用服务。

可将以下请求发给助手，后面是对应的手动步骤：

```text
请按本指南帮助设置并运行一次可选的本地 CEO AI Security 检查。
先检查平台、Python、Docker 和 Buildx。在安装工具、下载或构建镜像、访问文件前，
说明准确范围，复用已有授权并询问缺少的权限。
使用经过审查的 tools/security-image 方案，验证不可变镜像 ID 和版本 2.12.0，
再用合成技能测试真实适配器。只扫描获批技能，使用获批的私密工作目录、报告路径和 Unix 套接字。
不要调用外部 API，也不要运行技能代码。明确展示检查缺口，信任状态保持未验证。
```

## 1. 检查要求并安装可选插件

需要 macOS 或 Linux（POSIX）、主机上的 Python 3.10+，以及运行 Linux ARM64 容器的
本地**原生 ARM64 Docker 主机**。镜像内部使用 Python 3.12。本方案不覆盖 Intel/AMD64、
模拟运行、原生 Windows 或远程 Docker 守护进程。请使用经过审查且包含
`tools/security-image/` 和生成的可选适配器的 CEO AI 仓库副本，在该目录中运行命令。

如果尚未安装 Docker，请遵循适合系统的[官方安装指南](https://docs.docker.com/get-started/get-docker/)
并启动守护进程。安装和系统权限变更需要单独批准，插件不会自动执行。检查：

```sh
python3 --version
docker version
docker buildx version
docker info --format '{{.OSType}}/{{.Architecture}}'
docker context inspect --format '{{.Endpoints.docker.Host}}'
```

需要 Linux `aarch64`/`arm64` 和本地 `unix:///…` 套接字。记录该套接字供适配器使用。
BuildKit 必须支持 `ADD --checksum` 和 `RUN --network=none`。按
[插件说明](PLUGINS.md#可选-ceo-ai-security)安装包含扫描技能的 `ceo-ai`。
安装本身不授权扫描或构建镜像。
如果缺少 Buildx，须单独获批后才可遵循[官方安装说明](https://github.com/docker/buildx#installing)，
不要回退到旧版构建器。

## 2. 构建固定版本的扫描器镜像

批准构建前，检查 `tools/security-image/` 中的五个文件。仅将这个目录作为构建上下文，
不要改成主目录或整个项目。获取基础镜像、PyPI wheel 和固定的 GitHub 源码需要网络。
之后的扫描器构建与安装阶段以非 root 用户离线运行。因此，首次构建**并非全程离线**。

```sh
DOCKER_BUILDKIT=1 docker build -t ceo-ai-skillspector:2.12.0 tools/security-image
```

方案固定基础镜像 digest、源码 checksum 和二进制依赖哈希。这是完整性检查，不是安全认证。
相关机制见 Docker 的 [`ADD --checksum`](https://docs.docker.com/reference/dockerfile/#add---checksum)、
[`RUN --network=none`](https://docs.docker.com/reference/dockerfile/#run---networknone)
及 pip 的[安全安装](https://pip.pypa.io/en/stable/topics/secure-installs/)。
不要为绕过错误而关闭哈希检查或启用构建阶段网络。

## 3. 记录镜像 ID 并验证版本

```sh
docker image inspect --format '{{.Id}}' ceo-ai-skillspector:2.12.0
```

将返回的完整 `sha256:…` 复制到下面变量中，并将套接字改为步骤 1 中已批准的本地地址。
适配器不接受只有 tag 的镜像引用。

```sh
CEO_SCAN_IMAGE='sha256:replace-with-the-full-image-ID'
CEO_SCAN_SOCKET='unix:///replace-with-the-approved/docker.sock'
docker run --rm --pull=never --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 65534:65534 --pids-limit 64 \
  --memory 512m --cpus 1 "$CEO_SCAN_IMAGE"
```

预期输出：`SkillSpector 2.12.0`。这只验证镜像入口，不代表整个扫描流程成功。
构建、查看 ID 和扫描必须使用同一个本地守护进程。

## 4. 用合成示例验证真实适配器

在待扫描包外选择一个**新的**、已批准的私密目录。父目录必须可信且不允许其他用户写入。
替换示例路径；不要修改已有目录的权限来强行通过检查。

```sh
mkdir -m 700 /approved/private-scan-workspace
python3 -I -B plugins/ceo-ai/skills/security-scan/scripts/ceo_security_nvidia.py \
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
从加载的 `security-scan/SKILL.md` 所在目录找到 `scripts/ceo_security_nvidia.py`，
不要猜测缓存路径。保存 JSON 前先批准私密报告位置。

如需通过技能操作，请开启新会话，在 Codex 中选择 `ceo-ai:security-scan`，
或在 Claude Code 中调用 `/ceo-ai:security-scan`。

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

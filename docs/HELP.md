# Installation help

[Website and installation](https://bearatol.github.io/ceo-ai/#install)

Installed as a plugin? Use the plugin guide for invocation, updates, removal and migration. The file-installation steps below apply to the project installer.

[Codex / Claude Code plugins](PLUGINS.md#english)

[English](HELP.md) · [Русский](HELP.ru.md) · [简体中文](HELP.zh-CN.md)

Start with the case below that matches what you see. You can ask your agent to
do the checks; no terminal commands are needed from you.

## The skill does not appear

Open a new conversation in the same project where you installed CEO AI. Use
`$ceo-ai` in Codex, or `/ceo-ai` in Claude Code and Cursor. If it is still missing,
send your agent:

> Check the CEO AI installation in this project using INSTALL.md from
> https://github.com/bearatol/ceo-ai. Identify my current tool, check its skill
> location and files, and tell me whether the app can actually load ceo-ai.
> Preserve existing files and permissions.

The installer checks files. Loading the skill is a separate check, and app
versions may behave differently. If native subagents are unavailable, CEO can
still discuss your task but must say which independent checks it cannot perform.

## Installation stops or asks for access

Ask the agent to explain the exact missing permission or prerequisite. The
default installer needs Git and Python 3.10 or newer. Installing either requires
the permissions of your environment. APM is optional. The default installer supports macOS and Linux, and native Windows from version 0.3.0.
On native Windows, the agent can use an available Python 3.10+ through `py -3`
or `python`. The project must be on a local drive; network shares, device paths
and junctions are rejected. WSL projects use the Linux route inside WSL.

If a folder already exists or installed files were edited, ask the agent to
show the conflict and help preserve your changes. Use the same installation
method for updates and removal. Do not ask it to force an overwrite.

## An update was interrupted

Ask the agent to inspect the error and follow the recovery section in
[INSTALL.md](../INSTALL.md). Recovery applies to the local installer. APM has
its own state and may need a different recovery procedure. Keep the error
message and local changes until the agent has checked them.

## Moving from the original manual installation

The original 0.1.0 instructions copied several separate skills and used `$ceo`
or `/ceo`. Version 0.2.0 installs one self-contained skill named `ceo-ai`.
The new installer cannot identify ownership of the old manually copied files.

Ask your agent to locate the old copy, compare it with the original source,
and identify any personal edits. Review which old files can be backed up and
removed before authorizing that cleanup. Then install `ceo-ai` in the project
and use its new name. Keep unrelated skills and your existing configuration.

## Ask for help

[Open an issue](https://github.com/bearatol/ceo-ai/issues/new/choose) with your
tool and version, operating system, CEO AI version, installation method, and
the exact error. Describe what you expected and what happened. Remove private
project content, prompts, credentials and personal paths from any examples.

For a possible vulnerability, use the [private reporting instructions](../SECURITY.md).
For contributing a fix or translation, see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Memory, lessons and reusable templates

[Memory, lessons and reusable templates](MEMORY.md#english).

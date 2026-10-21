# CEO AI

<a href="https://bearatol.github.io/ceo-ai/"><img src="docs/assets/ceo-ai-banner.png" alt="CEO AI: Think. Challenge. Orchestrate." width="1280"></a>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![CEO AI on skills.sh](https://skills.sh/b/bearatol/ceo-ai)](https://skills.sh/bearatol/ceo-ai)

**[Website](https://bearatol.github.io/ceo-ai/) · [Examples for your work](https://bearatol.github.io/ceo-ai/#cases) · [Security](https://bearatol.github.io/ceo-ai/#security) · [Install](https://bearatol.github.io/ceo-ai/#install) · [Help](https://bearatol.github.io/ceo-ai/#help)**

Open the website for examples and an installation message you can copy to your agent.

**Not sure how to approach a task? Talk it through with an AI CEO.**

CEO AI adds a workflow to Codex, Claude Code, or Cursor for discussing an idea,
choosing an approach, and following through. It asks questions that affect the
outcome, points out weak assumptions, and explains what to check before starting.

CEO AI is under active development. We test and refine the orchestration skill
based on test results and feedback.

Suppose you want to rewrite an application. CEO first helps identify the problem
the rewrite should solve, compares it with smaller changes, and suggests a way
to test the choice. Once you decide, it helps plan and carry out the work.

CEO treats a proposed solution as a hypothesis about the result you want. It
checks material assumptions, compares alternatives and consults applicable
established practices and authoritative primary sources before consequential
recommendations. It separates facts from guesses, flags missing evidence and
respects your informed preferences. [How it checks a proposal](docs/CEO_GUIDE.md#check-the-proposal-against-the-outcome).

[Five fictional skill demonstrations: CEO, Writer, Security Scan, Debugger and User Review](docs/DIALOGUE.md).

## Security checks during indexing

CEO AI checks selected skills and agents locally during indexing, without running
their content. The builtin scanner needs Python 3.10+ on macOS, Linux or native Windows (fixed local NTFS),
with no Docker, LLM or API calls. Reports show risk signals, unchecked content
and unverified trust. No findings does not mean safe.

**[First scan: install → “Check my skills” → read the result](docs/QUICKSTART.md).**
Windows scanning refuses network drives, reparse points and package aliases. See
[Windows scope and commands](docs/SECURITY_SCANNING.md#windows).

The same plugin includes **Security Scan** for an optional additional check.
Docker is needed only for this scan. Copy the setup request from the guide:
the agent checks compatibility, prepares the image and runs a smoke test.
[Advanced ARM64 Docker walkthrough](docs/DOCKER_SCAN.md) ·
[Technical limits](docs/SECURITY_SCANNING.md)

## Keep what worked

For posts, articles and messages, select **`ceo-ai:writer`**, included in the plugin. It follows your voice, uses keyboard punctuation and avoids
sales pressure. No Docker is needed; persistent preferences are opt-in.
[Use Writer and manage preferences](docs/WRITER.md).

CEO AI checks existing solutions and relevant documented practices before
inventing a new approach. With your permission, it can retain project lessons,
design patterns and separately approved user preferences. Memory starts off.
Every save is announced; you can view, correct, delete or disable it in plain
language. [Memory and templates](docs/MEMORY.md#english).

## Debug code and review the user experience

The native plugin also includes **`ceo-ai:debugger`** to reproduce bugs, test
possible causes and verify a small fix, or refactor within a defined scope while
preserving tested behavior. [Debugger guide](docs/DEBUGGER.md#english).

Use **`ceo-ai:user-review`** to examine a flow as a tired novice and as a chosen
professional. It keeps expertise separate from attention, fatigue and motivation,
points to concrete friction or possible exit points, and proposes fixes with
tradeoffs. These are synthetic hypotheses, not user research or conversion
predictions. [User Review guide](docs/USER_REVIEW.md#english).

These two skills are additions in this source tree; check the selected release's
contents. Project/APM installs still contain only the core CEO skill.

## Get started

Open your project in **Codex, Claude Code or Cursor** and send:

```text
Install CEO AI for my current AI app using these instructions.
Check existing installations and use a native plugin where supported.
Explain the installation scope first; preserve my current project and local edits.
https://github.com/bearatol/ceo-ai/blob/main/INSTALL.md
```

The agent selects the latest stable release unless you request a specific version.

Codex and Claude Code can use the plugin manager. Cursor uses the project
installer, which also remains available for Codex and Claude Code on Windows,
macOS and Linux. Native plugin managers store some settings outside the project.
You do not need to create folders or copy files yourself.

After installation, start a new chat. For a plugin, select **`ceo-ai:ceo-ai`**
in Codex or invoke **`/ceo-ai:ceo-ai`** in Claude Code. With the project installer,
use **`$ceo-ai`** in Codex or **`/ceo-ai`** in Claude Code and Cursor.

[Plugin setup, updates and migration](docs/PLUGINS.md#english) ·
[Microsoft APM](docs/APM.md#english)

### Install individual skills

With Node.js 22.20 or later, you can select individual skills through the
[Skills CLI](https://github.com/vercel-labs/skills/blob/main/README.md):

```sh
npx skills add bearatol/ceo-ai
```

[All five skills on skills.sh](https://skills.sh/bearatol/ceo-ai) ·
[SkillsMP search](https://skillsmp.com/search?q=bearatol%2Fceo-ai&sortBy=stars).
SkillsMP indexing has been requested; listing is not yet confirmed.

Choose the skills, target agent, and installation scope in the prompts. Preserve
local changes before replacing an existing installation. This installs skills,
not the native plugin. [Catalog status and distribution guide](docs/DISTRIBUTION.md).

## Things to ask

> I want to launch a product. Help me decide what to check before building it.

> I'm considering rewriting this service. Find weaknesses in that choice and suggest alternatives.

> We need to add payments. Plan the work, help implement it, and check the result.

Start with the outcome you want. Add a deadline, budget, or other constraints
if you have them. You do not need to prepare a long brief.

## A short example

Illustrative dialogue, not a recorded run or a benchmark:

> **You:** Let's rewrite the service from scratch. It is too slow.
>
> **CEO:** Which part is slow, and what have you measured? A rewrite might be
> expensive without fixing the cause.
>
> **You:** Report generation takes too long. The rest works well.
>
> **CEO:** Start with one report: measure its runtime, find the slowest step,
> and test a targeted change. Compare the result before deciding on a rewrite.

The discussion produces a concrete next step and a way to judge it. For code
changes, CEO can then help implement the plan and check the result.

## Compatibility and checks

| Installation method | Verified | Still unverified |
| --- | --- | --- |
| Earlier core-only Codex / Claude Code plugins | Install, update, removal and skill discovery on macOS | Five-skill layout discovery and model invocation; Windows/Linux native managers |
| Project installer, all three tools | File lifecycle in Windows, Linux and macOS CI | Skill invocation in the apps |
| APM 0.31.0 | File lifecycle on macOS with CEO AI 0.2.0 | Installation example for CEO AI 0.8.0 |

The native checks used Codex CLI 0.147.0 and Claude Code 2.1.232 with the earlier
core-only layout. They do not establish discovery or model behavior for the five
skills in this source tree.
See [test evidence and limitations](docs/PLUGINS.md#what-was-checked) and
[automated checks](https://github.com/bearatol/ceo-ai/actions/workflows/checks.yml).

## How it helps

- **Discusses the choice.** Asks about facts that could change the decision,
  explains objections, and revises its own advice when new evidence appears.
- **Organizes the work.** Breaks a large task into clear steps. If your app
  supports other AI assistants, it can assign implementation to one and ask
  another to review the result.
- **Checks specific things.** For code: tests and whether it meets the request.
  For writing: clarity, contradictions, and unsupported claims.
  For plans: missing steps, dependencies, and ways to recover from a poor choice.
- **Gets a second opinion.** Before a decision with a high cost of failure,
  asks a separate AI assistant to look for weaknesses in the proposed approach.
  This is a review inside your app. No human is contacted.

A simple question should not require a team meeting. If additional AI assistants
are unavailable, CEO should say so. It must not present its own repeated check
as an independent review.

## Help and project updates

If installation stops or the skill does not appear, start with
[installation help](docs/HELP.md). You can also [report a problem](https://github.com/bearatol/ceo-ai/issues/new/choose).
See [changes and migration notes](CHANGELOG.md), [releases](https://github.com/bearatol/ceo-ai/releases),
[contribution guidelines](CONTRIBUTING.md) and [private security reports](SECURITY.md).

## Update or remove

Ask your agent to update or remove CEO AI using the same method that installed
it. Share [INSTALL.md](INSTALL.md). Removing a Codex user-level plugin affects
all projects using it; removing a project skill affects that project, including
Cursor if it shares the folder. Preserve local edits before either operation.

CEO AI uses your current model and tools. AI answers need checking; a second
opinion can also be wrong. CEO gains no extra permissions and does not replace
security reviews required by your project.

[Development and verification](docs/DEVELOPMENT.md) ·
[Distribution and catalog status](docs/DISTRIBUTION.md) ·
[CEO workflow details](docs/CEO_GUIDE.md) · [MIT](LICENSE)

## Author

[Telegram @bearatol](https://t.me/bearatol) · [LinkedIn](https://www.linkedin.com/in/mikhail-diesperov/)

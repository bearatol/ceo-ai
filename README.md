# CEO AI

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**Not sure how to approach a task? Talk it through with an AI CEO.**

CEO AI adds a workflow to Codex, Claude Code, or Cursor for discussing an idea,
choosing an approach, and following through. It asks questions that affect the
outcome, points out weak assumptions, and explains what to check before starting.

Suppose you want to rewrite an application. CEO first helps identify the problem
the rewrite should solve, compares it with smaller changes, and suggests a way
to test the choice. Once you decide, it helps plan and carry out the work.

## Get started

Open your project in **Codex, Claude Code, or Cursor** and send your agent:

```text
Install CEO AI in this project using these instructions:
https://github.com/bearatol/ceo-ai/blob/v0.2.0/INSTALL.md
```

The agent reads the instructions, installs the skill for your tool, and checks
the files. If your app needs permission, it will show what access is required.
You do not need to create folders, copy skills, or supply a repository path.
The installation applies to this project.

Start a new conversation in the project and invoke **`$ceo-ai` in Codex** or
**`/ceo-ai` in Claude Code and Cursor**. Then describe the task in your own words.

Already use Microsoft APM? Follow the [APM instructions](docs/APM.md#english).

## Things to ask

> I want to launch a product. Help me decide what to check before building it.

> I'm considering rewriting this service. Find weaknesses in that choice and suggest alternatives.

> We need to add payments. Plan the work, help implement it, and check the result.

Start with the outcome you want. Add a deadline, budget, or other constraints
if you have them. You do not need to prepare a long brief.

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

## Update or remove

Tell your agent “Update CEO AI in this project” or “Remove CEO AI from this
project” and share the [instructions](INSTALL.md). If an installed file was
edited, the agent must preserve the changes and resolve the conflict first.

CEO AI uses your current model and tools. AI answers need checking; a second
opinion can also be wrong. CEO gains no extra permissions and does not replace
security reviews required by your project.

[Development and verification](docs/DEVELOPMENT.md) ·
[CEO workflow details](docs/CEO_GUIDE.md) · [MIT](LICENSE)

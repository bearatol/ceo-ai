# Changelog

## Unreleased

- Use a permanent `main` link for installation instructions. Resolve the latest
  stable release at installation time and record its exact tag and commit.

## 0.4.0

- Add a shared skills-only plugin for Codex and Claude Code, with separate
  marketplace catalogs and a deterministic build from the existing APM skill.
- Verify the publication allowlist, cached payload, version consistency and
  isolation from native agent, hook and MCP registration.
- Document native installation, update, removal and migration in English,
  Russian and Simplified Chinese. Preserve the project installer for Cursor.
- Test both native managers on macOS. Host discovery passed; model invocation
  remains unverified because the available sessions could not run the test.

## 0.3.0

- Support the default project installer on native Windows. Validate portable
  paths and test junction rejection, byte locking, Unicode paths and recovery.
- Add a three-language GitHub Pages site with readable text, a pausable workflow
  animation, six profession scenarios, tool selection and an installation message.
- Add illustrated website links, author contacts, installation help and migration
  guidance in English, Russian and Simplified Chinese.
- Add contribution guidelines and private vulnerability reporting instructions.
- Check file installation, updates, removal, conflicts and recovery on Windows,
  Linux and macOS. Check package integrity and documentation links in CI.

Native app invocation and model behavior remain unverified. APM 0.31.0 was tested
on macOS with CEO AI 0.2.0; that optional check has not been rerun for 0.3.0.

## 0.2.0

- Ship one self-contained `ceo-ai` skill for project installation.
- Add installation through an AI agent and an optional Microsoft APM package.
- Add checks that preserve unmanaged folders and locally edited installations,
  and recovery for interrupted local-installer updates.
- Replace manual setup instructions with English, Russian and Simplified
  Chinese quick starts.

The original `$ceo` and `/ceo` manual installation needs an explicit migration;
see [the help guide](docs/HELP.md#moving-from-the-original-manual-installation).
The release was checked using macOS fixture projects for Codex, Claude Code
and Cursor, including APM 0.31.0. Native app invocation and native Windows
installation were not verified. Native Windows path handling needs further work.

## 0.1.0

Initial public extraction of CEO workflows, supporting guides, role prompts
and verification tools. Installation required manually copying several skills.

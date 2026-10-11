# Changelog

## Unreleased

- Add illustrative dialogues, compatibility evidence and installation help in
  English, Russian and Simplified Chinese.
- Document migration from the original manual installation, contribution
  guidelines and private vulnerability reporting.
- Add automated tests, package integrity checks and local documentation link
  checks on Linux and macOS. Native application invocation remains unverified.

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

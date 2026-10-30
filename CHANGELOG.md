# Changelog

## Unreleased

## 0.9.0 - 2026-10-30

- Rename the native `ceo-ai:security-scan` skill to `ceo-ai:security`. Add
  target-specific methods for code, web/API/mobile, configuration, infrastructure,
  AI systems and skill packages using available authorized tools.
- Require informed approval of bounded active tests: explain purpose, concrete
  actions, possible harm, safer alternatives, limits and stop/recovery rules.
  Separate evidence from hypotheses and report untested areas.
- Add original guidance informed by NIST, PTES, OWASP, CIS and CVSS. Keep the
  existing SkillSpector adapter unchanged as an optional skill-package-only route;
  ordinary assistant-led audits do not require Docker.
- Allow CEO-coordinated independent native-subagent review when Claude is
  unavailable, within applicable user and host restrictions. Do not claim that
  instruction-only reviewer limits are technical isolation.
- Update the website, documentation and fictional examples in English, Russian
  and Simplified Chinese. Add guarded package migration and behavioral scenarios.
- Migration: update the combined `ceo-ai` plugin through its existing manager,
  start a new chat and select `ceo-ai:security`. Existing skill-scan prompts must
  use the new name. Project/APM installations still provide only the core skill.
  Do not manually rename cached plugin folders.
- Strengthen Writer's professional editing workflow for product copy, business,
  technical and personal writing. Add bilingual examples and review exercises;
  use Wikipedia's style observations as editorial prompts, not an AI detector.
  Keep factual limits, user voice and opt-in memory unchanged.

## 0.8.0

- Support builtin security indexing on native Windows with fixed local NTFS.
  Reject unsupported paths and retain bounded reads and handle-based cache writes.
  Add native Windows CI coverage on Python 3.10 and 3.12.
- Guide optional Docker scan preparation through a ready-to-copy request.
  The agent checks compatibility, prepares the pinned image and runs a smoke test.
  The reviewed recipe remains ARM64 macOS/Linux only.
- Align the website and documentation in English, Russian and Simplified Chinese.
- Prefer periods over semicolons in Writer narrative text.

## 0.7.0

- Check existing implementation and suitable components before the first technical
  recommendation. Resolve material evidence gaps with official sources, explain
  the choice and label assumptions. Add eight behavioral acceptance scenarios;
  these are specifications, not a completed model benchmark.

- Combine CEO, Writer and Security Scan into one native `ceo-ai` plugin.
  Docker remains necessary only for an explicit deep scan; memory stays opt-in.

- Present included Writer and optional Security Scan beside website installation in three languages.
- Replace the README banner with the supplied optimized PNG.

- Add `writer-how-me` for writing in the user's voice, plain keyboard punctuation
  and optional correction-based preferences through existing private memory.
  Ship it as `ceo-ai:writer` inside the single native CEO AI plugin.
  No personal profile, additional service or background learning is shipped.

- Add three-language first-scan walkthroughs, a pinned optional Docker image
  recipe and fictional dialogue showing how assumptions become testable plans.
  Simplify website copy and link the complete walkthroughs.

- Make builtin security indexing prominent on the website and in all three
  READMEs, with explicit scope, platform requirements and advisory limits.
- Treat proposed solutions as hypotheses about desired outcomes. Require
  applicable established practices and authoritative primary evidence for
  consequential recommendations, distinguish unknowns and respect informed choice.

## 0.6.0

- Add local static security observations during skill and agent indexing, with
  separate findings, capability tiers, coverage and unverified trust. Core uses
  only Python standard-library analysis; no Docker, LLM or external API calls.
- Preserve partial results for oversized resources and add bounded, explicitly
  approved alias roots and native TOML agent declarations.
- Ship `ceo-ai-security` as a separate opt-in plugin with one `security-scan`
  skill. Local deep scans require POSIX, Docker and a separately prepared
  immutable NVIDIA SkillSpector image; the plugin installs none of these.
- Keep scanner output advisory and incomplete coverage visible. No cloud
  service, paid API client or subscription is implemented.
- Publish synthetic scanner comparisons, regression tests and aligned English,
  Russian and Simplified Chinese installation and website guidance.


## 0.5.0

- Add optional project lessons, reusable design patterns and user preferences.
  Memory starts off, announces saves and supports view, correction, deletion and
  disabling. Private SQLite storage remains outside repositories and plugins.
- Check existing solutions and relevant documented practices before new designs.
- Validate consent, scope isolation, stale records, revision conflicts and storage
  boundaries. Reject private additions across all bundle publication routes.
- Add memory guidance in English, Russian and Simplified Chinese.
- Keep the site header visible on scroll and fix the single-pass workflow signal.
- Use shared SVG geometry, a header pulse and accessible icon-only player controls.


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

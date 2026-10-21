# Distribution playbook

Help someone find CEO AI, install it in their own app, and complete one useful
task. A catalog listing is a discovery channel; a successful first task needs
clear setup, a concrete request, and a result the user can check.

## Catalog status

Checked on 2026-10-21. Keep this table tied to observed results; add a listing
link only after the public page can be opened and checked.

| Channel | Discovery path | CEO AI status |
| --- | --- | --- |
| [SkillsMP](https://skillsmp.com/) | Automatic indexing of public GitHub skills; see [About](https://skillsmp.com/about). | Repository search returned no matches. After publisher approval, an indexing request was emailed to support@skillsmp.com on 2026-10-21 at 16:29 Europe/Moscow. Sending was verified in the mail provider's Sent folder. Awaiting the service's response; inclusion is not confirmed. |
| [skills.sh](https://www.skills.sh/) | Actual installs through the Skills CLI with telemetry enabled; see the [FAQ](https://www.skills.sh/docs/faq). | [Public repository page](https://www.skills.sh/bearatol/ceo-ai) lists all five skills. Verified after one maintainer installation test; displayed install count was zero when checked. |

Do not repeat installations to inflate counts. No submission form was found in
the SkillsMP public pages inspected on this date; check the current site before
deciding whether a manual submission is available.

### Installation evidence

Skills CLI 1.7.4 discovered and copied all five skills from the exact published
`plugins/ceo-ai/skills` subtree into a disposable project. The installation event
for `bearatol/ceo-ai` received HTTP 200. All 56 installed files matched the source
bytes, and no installed symlinks were present. This checks discovery and file
installation for the Codex target, not invocation by the host model. No skill
scripts, Docker preparation, or optional memory workflow ran.
The shorter `bearatol/ceo-ai` source shown by the directory was also checked
with `--list`; it discovered the same five skill names without another install.

## From discovery to a useful result

| Stage | What to provide | Evidence to keep |
| --- | --- | --- |
| Discovery | A short description of the problem CEO AI helps with, a repository link, and the supported apps. | The public catalog page and date checked. |
| Installation | [Native plugin or project instructions](../INSTALL.md), plus the individual-skill option below. Explain scope and preserve local changes. | App, OS, version, install method, and observed result. |
| First useful task | One concrete request, such as “Help me decide what to check before building this product.” Show how to invoke the selected skill in the app. | The request, relevant context, and a result the user can inspect. |
| Real evidence | A maintainer demonstration showing setup, the actual task, the output, and its limitations. | A reproducible example or recording, with private information removed and the tested version named. |
| Feedback and releases | Use [GitHub Issues](https://github.com/bearatol/ceo-ai/issues) for reproducible problems and [GitHub Releases](https://github.com/bearatol/ceo-ai/releases) for changes and verification limits. | Confirmed fixes, release notes, and unresolved limitations. |

Publish a real demonstration before describing a workflow as proven. Label
fictional examples as fictional, and do not turn catalog counts or repository
stars into claims about user outcomes.

## Individual skills through the Skills CLI

With Node.js 22.20 or later, run:

```sh
npx skills add bearatol/ceo-ai
```

Choose the skills, target agent, and installation scope in the prompts. Review
existing installations and preserve local changes before replacing anything.
This installs individual skills, not the native CEO AI plugin. Use
[INSTALL.md](../INSTALL.md) for native plugin and project installation.

The short source resolves the repository's published skills on its default
branch; native installation uses the release policy described in `INSTALL.md`.
See the
[Skills CLI documentation](https://github.com/vercel-labs/skills/blob/main/README.md)
for supported agents, requirements, and options.

## What to adapt from Superpowers

[Superpowers](https://github.com/obra/superpowers) makes platform installation and
the working sequence visible in its README, has a
[maintainer announcement](https://blog.fsck.com/2025/10/09/superpowers/), and
publishes [release notes](https://github.com/obra/superpowers/releases). Apply that
pattern to CEO AI: keep host instructions easy to find, show one complete task, publish
real demonstrations, and connect user feedback to documented releases. These
are distribution practices to test, not evidence of a causal growth or revenue
effect.

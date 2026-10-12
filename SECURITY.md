# Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/bearatol/ceo-ai/security/advisories/new)
for a suspected vulnerability. Do not put exploit details, private project
content, credentials or logs containing secrets in public issues.

If the private form is unavailable, open a public issue asking only for a
private reporting channel. Do not include vulnerability details in that issue.

Include the CEO AI version or commit, affected operating system and tool,
installation method, expected boundary, and a minimal redacted reproduction.
Describe any file modification, unintended access or permission change. Use
dummy data and a disposable project; do not test against someone else's systems.

## Versions and scope

Reports should target the latest published patch of the 0.2 series, currently
0.3.0. Earlier manual installations may need to migrate before a fix can be
applied. This is a small maintainer-led project with no guaranteed response time.

Relevant reports include installer path escapes, overwriting user files,
unsafe execution, unintended network access, or instructions that bypass a
permission boundary. Model output still requires review. The skill and its
role prompts do not provide a sandbox or grant additional permissions.

For ordinary installation problems, use [the help guide](docs/HELP.md).

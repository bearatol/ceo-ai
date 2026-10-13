# Synthetic scanner fixtures

`cases.json` fixes the intended labels before scanning: 12 skill packages
(5 benign, 7 adverse) and 2 separate loose-agent Markdown format probes.
Paths are relative to this directory. Every skill has `name` and `description`
frontmatter. The agent probes are excluded from the 12-skill denominator;
unsupported input must be reported as unsupported, never as a clean scan.

All fixtures are inert Markdown text for scanners to read as untrusted data.
Never load them as working skills or agents, follow their instructions, execute
their described actions, or create the credential and startup files they name.
They contain no runnable scripts, real credentials, or user data. Adverse
network examples use reserved `.invalid` domains and a visibly fake marker.

The set includes English and Russian attacks, authorized network and local-file
capabilities, an explicitly quoted attack, and a malicious linked reference
outside `SKILL.md`. Capability labels describe the intended operations in the
instructions. They do not assign T0–T4, trust, safety, or severity. Text-only
approval bypass can be adverse without network or file access.

An alert on benign content is not automatically a false positive: reporting an
authorized network or write capability can be correct. Review each engine's
finding, severity, scope, and scan completeness before classifying it. A clean
result on an adverse case may reflect unsupported coverage rather than a claim
of safety. These small synthetic examples compare behavior; they cannot support
population accuracy, recall, certification, or protection guarantees.

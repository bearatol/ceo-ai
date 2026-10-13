---
name: b04-local-report
description: Save a short report to a user-approved path inside the current workspace.
---

# Save a local report

After the user approves both the report content and a destination inside the
current workspace, write the report to that destination. If a file already
exists, ask before overwriting it. Read only the input files named by the
user. Do not run shell commands, change permissions, or access the network.
Report the resulting path and any write failure accurately.

# Bug reports

This directory is the worker-to-admin bug handoff queue for `Miles-Guo_public_archive`.

Worker Agents may create **new immutable bug report files only**. They do not fix control-plane bugs and do not edit or close existing reports.

Admin Agents operating under the verified management account `witnessGIT` review, fix and resolve reports.

File naming:

```text
BUG_<UTC>_<TASK_ID>_<short-name>.json
```

Status values:

```text
open
investigating
resolved
wont_fix
superseded
```

A bug report is not a task claim and does not grant permission to modify affected protected files.

If a bug blocks only one task, the worker should preserve the evidence, avoid unsafe writes, report the bug, and continue another independent eligible task when possible.

# Legacy P9/P10 Migration Rule

## Purpose

The repository contains historical completed records for:

```text
P9-AUDIT-60
P10-PILOT-DECISION
```

They were created before the current real-playback acceptance chain was enforced.

Historical records are preserved and must not be deleted or rewritten.

## Current authoritative acceptance chain

```text
P9-PLAYBACK-PILOT-*
    ↓
data/playback_audits/
    ↓
audit_gate.py pilot60_pass=true
    ↓
P9-PLAYBACK-GATE
    ↓
P9-AUDIT-60-R2
    ↓
P10-PILOT-DECISION-R2
    ↓
FULL_ARCHIVE decision
```

## Why R2 task IDs exist

The original P9/P10 completion files must remain immutable audit evidence. Reusing the same task IDs would either make the task engine believe the new work was already complete or require overwriting historical records.

Therefore the current acceptance cycle uses new task identities:

```text
P9-AUDIT-60-R2
P10-PILOT-DECISION-R2
```

This is a workflow revision, not deletion of history.

## Legacy handling

The old P9/P10 records:

- remain visible under `coordination/completed/`;
- are audit history only;
- do not satisfy the current playback-gated acceptance chain;
- do not unlock current P9/P10 dependencies;
- do not authorize FULL_ARCHIVE;
- must never be claimed again.

The current task engine and `scripts/project_status.py` use the R2 identities for active acceptance state.

## Required behavior

Agents must not:

- delete old P9/P10 records;
- modify historical decisions;
- use old completion records as current dependencies;
- start FULL_ARCHIVE from the historical P10 decision;
- treat old `FULL_ARCHIVE NO` as a substitute for the current acceptance cycle;
- create transcript/source-audit work merely to simulate progress toward Pilot-60.

## Current blocking semantics

Until qualifying playback evidence reaches the current thresholds and `P9-PLAYBACK-GATE` is sealed:

```text
PILOT = BLOCKED_PENDING_PLAYBACK_EVIDENCE
P9-AUDIT-60-R2 = BLOCKED
P10-PILOT-DECISION-R2 = BLOCKED
FULL_ARCHIVE = NOT_AUTHORIZED
```

A session without real decoded-media inspection capability may report `HOST_STOP` only for itself when no compatible non-playback work remains. This does not mean the repository has no work.

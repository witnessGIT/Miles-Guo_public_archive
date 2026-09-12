# P10 Legacy Decision Migration Rule

## Purpose

The repository previously contained historical `P10-PILOT-DECISION` records created before the final playback acceptance chain was enforced.

Historical records are preserved and must not be deleted or rewritten.

## Current authoritative acceptance chain

```
P9-PLAYBACK-PILOT-*
    ↓
data/playback_audits/
    ↓
audit_gate.py pilot60_pass=true
    ↓
P9-PLAYBACK-GATE
    ↓
P9-AUDIT-60
    ↓
P10-PILOT-DECISION
    ↓
FULL_ARCHIVE decision
```

## Legacy P10 handling

A historical P10 completion record does not unlock FULL_ARCHIVE if it was created before qualifying playback evidence existed.

Historical records remain immutable evidence of the previous decision process.

They are treated as superseded state when:

- Pilot-60 qualifying playback evidence is below the required threshold;
- P9-PLAYBACK-GATE has not been sealed;
- P9-AUDIT-60 has not completed under the current contract.

## Required behavior

Agents must not:

- delete old P10 records;
- modify historical decisions;
- start FULL_ARCHIVE from a legacy P10 record;
- treat old NO decisions as a substitute for the current acceptance chain.

The current operational state remains:

```
PILOT = BLOCKED_PENDING_PLAYBACK_EVIDENCE
P9 = BLOCKED
P10 = BLOCKED
FULL_ARCHIVE = NOT_AUTHORIZED
```

until the current playback evidence requirements are satisfied.

# Pilot Aggregate Audit Gate — P9-AUDIT-60

> HISTORICAL SNAPSHOT — INVALIDATED AS AUTHORITATIVE COMPLETION
>
> This report was produced from a grandfathered P9 claim that predated the mandatory `P9-PLAYBACK-GATE` dependency. Its substantive finding of `0/60` qualifying playback checks remains historically accurate, but it must not be interpreted as a valid completion of the current P9 gate.

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `P9-AUDIT-60`  
Workflow: `continuous-worker-v2`

## Result

**AUDIT GATE: FAIL**

The Pilot requirement is at least **60 real playback-checked segments**. The 27 per-case audit readiness records were reviewed across Early (E001–E009), Middle (M001–M009), and Late (L001–L009).

Aggregate qualifying real playback checks:

```text
Early:   0
Middle:  0
Late:    0
Total:   0 / 60
```

No transcript timestamp, GHOT time-axis row, GWINS chapter timestamp, URL seek parameter, selected-clip boundary, or cross-source text match was counted as real playback verification.

## Accuracy gates

Required Pilot quality gates:

```text
false livestream merge rate approximately 0
>= 90% of locatable audited segments within 3 seconds
>= 98% within 8 seconds
```

Observed state:

- qualifying playback sample size: **0**;
- measured playback timing errors: **0**;
- <=3 second rate: **not measurable / gate not satisfied**;
- <=8 second rate: **not measurable / gate not satisfied**;
- false-merge review evidence exists in case/source work, including preservation of known identity/ordinal conflicts, but the required playback audit sample is absent and the Pilot cannot pass on source/timeline corroboration alone.

## Per-era evidence summary

### Early — E001 to E009

All nine audit records explicitly state that actual media playback was not independently observed or decoded. Each contributes zero qualifying checks. Some cases strongly corroborate stored starts against public GHOT/GWINS timestamps, but those are source-timeline checks rather than playback checks.

### Middle — M001 to M009

All nine audit records contribute zero qualifying checks. GHOT public timestamps corroborate many stored anchors; noisy-ASR and pre-roll caveats are preserved where applicable. No timing error was independently measured from decoded media.

### Late — L001 to L009

All nine audit records contribute zero qualifying checks. Several readiness records provide explicit machine-readable fields:

```text
qualifying_playback_checks = 0
counts_toward_pilot_60 = false
timing_accuracy_measured = false
```

The 2022-05-29 ordinal/source mismatch remains preserved rather than being forced into a false merge.

## Historical interpretation

At the time this snapshot was written, it treated the failed aggregate review as a completed P9. The current workflow no longer permits that interpretation. P9 is complete only after real qualifying playback evidence passes `scripts/audit_gate.py`, `P9-PLAYBACK-GATE` is sealed, and P9 is freshly claimed under the current dependency graph.

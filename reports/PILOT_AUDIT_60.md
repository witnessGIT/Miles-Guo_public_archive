# Pilot Aggregate Audit Gate — P9-AUDIT-60

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

## Gate interpretation

The project requirements state that if the Pilot quality target is not reached, the project must **not enter full collection**. P9 is therefore complete as an evidence-based failed gate: the aggregate evidence was evaluated, the required 60 real playback checks are absent, and the timing-accuracy thresholds cannot be certified.

This result does **not** authorize `FULL_ARCHIVE`.

## Required next decision

`P10-PILOT-DECISION` should publish the whole-Pilot report and recommend:

```text
FULL_ARCHIVE: NO
```

unless new real playback audit evidence is added and P9 is rerun/reopened under an authorized workflow.

# Miles-Guo_public_archive Admin Audit — 2026-09-13

Role: management/admin audit under `witnessGIT`  
Phase reviewed: `SITE_ANALYSIS + PILOT`  
FULL_ARCHIVE: **NOT AUTHORIZED**

## Executive conclusion

The current repository is **directionally aligned with the original archive goal** and the core data model is suitable for continuing the Pilot:

```text
one canonical livestream
+ multiple independently preserved source records
+ separate source/curated and ASR text
+ explicit time/provenance fields
+ conservative cross-source identity
+ rebuildable SQLite + FTS5
```

The repository is **not yet ready for FULL_ARCHIVE** because the Pilot acceptance evidence is incomplete, especially real playback-position auditing.

## What is currently sound

### Pilot breadth

The Pilot selection contains 27 source-backed cases:

```text
early   9  (2017–2019)
middle  9  (2020–2021)
late    9  (2022–2023)
```

This satisfies the intended 20–30 case Pilot size and includes same-day ambiguity, path/title ordinal mismatch, long-form media, noisy ASR and multiple platform-link patterns.

### Identity discipline

The repository does not rely on date alone. The 2019-05-30 case demonstrates that multiple same-day GWINS records can remain distinct while stronger cross-source evidence selects the correct match.

This is consistent with the primary anti-false-merge goal.

### Transcript/provenance discipline

The archive keeps source/curated text and GHOT ASR distinct. Secondary transcript copies are retained as secondary provenance rather than silently promoted to original source truth.

### Alignment discipline

The Pilot alignment experiment correctly distinguishes:

```text
alignment_quality / text similarity
!=
measured playback timestamp error
```

Unverified rows stay `playback_verified=0` and low-confidence results remain reviewable rather than being forced into a pass.

### SQLite / FTS rebuild

During this audit, two real data-contract/migration bugs were found and repaired by the admin Agent:

1. a worker-created secondary-source JSON used unsupported top-level fields (`metadata`, `source_level`);
2. migrated L009 per-live segment rows remained duplicated in the legacy batch file.

After both fixes, GitHub Actions run `34706057045` completed successfully.

Observed rebuilt counts at that run:

```text
live_videos:             27
live_sources:            41
source_match_candidates: 13
live_segments:           68
live_segments_fts:       68
archive_items:            0
entities:                 0
topics:                   0
```

`validate_db.py` returned `OK` with one warning: 67 timed segments were still not playback-verified at that build snapshot.

The Actions workflow then committed the refreshed SQLite artifact as commit `7aff0391a2fe7be1e727094827730e301e397ab0`.

## Important remaining gaps

### 1. Real playback audit is the main acceptance gap

The Pilot target requires at least 60 real playback-checked segments and the defined <=3s / <=8s timing thresholds.

Several audit tasks so far are useful provenance/timeline checks but explicitly contribute **0** qualifying playback checks because a usable playback surface was unavailable in the Agent environment.

Such attempts are valid evidence but are not timing passes.

The `PILOT-L007` readiness marker was made machine-explicit during this audit:

```text
audit_outcome = blocked_no_playback
qualifying_playback_checks = 0
counts_toward_pilot_60 = false
timing_accuracy_measured = false
```

Future Pilot-60 accounting must count actual qualifying checks, never merely the presence of an audit-ready marker.

### 2. Three desired source-coverage categories remain evidence-gated

The Pilot selection correctly refuses to fabricate these labels:

- GettrSearch-discovered item proven absent from bounded GWINS/GHOT search;
- demonstrable GWINS-only livestream;
- demonstrable GHOT-only livestream.

`not found` is not evidence of absence.

### 3. GettrSearch remains discovery/backfill rather than primary truth

Its public static surface is insufficient to establish durable original-platform identity/transcript metadata. Dynamic payload behavior remains a future collection problem, not something to guess in the Pilot.

### 4. Generic archive layers are still empty

At the successful rebuild snapshot:

```text
archive_items = 0
entities = 0
topics = 0
```

This is acceptable for the current livestream Pilot but means the future broader public-information archive layer has not yet been exercised with real data.

### 5. Some originally planned repository deliverables remain absent

The current repository has the core schema/build/validation/identity/alignment/task-runner implementation, but several originally listed documentation/tooling files are not yet present, including some of:

```text
docs/DATA_MODEL.md
docs/DATA_QUALITY.md
docs/SOURCE_POLICY.md
docs/ARCHITECTURE.md
scripts/analyze_sources.py
scripts/collect_pilot.py
scripts/export.py
```

These are not blockers for proving the current Pilot data model, but they should be completed before declaring the repository operationally mature for full-history ingestion.

## Site-analysis consistency correction

The previous top-level `docs/SITE_ANALYSIS.md` had stale status text implying that GWINS transcript, GHOT time-axis and GettrSearch analysis were still unperformed.

The admin audit consolidated that document so it now points to the completed focused analyses and describes GettrSearch accurately as current discovery/backfill evidence rather than a verified primary source.

## Agent governance introduced by this audit

Policy: `agent-permissions-v1`

Administrative GitHub login:

```text
witnessGIT
```

Default behavior:

```text
verified witnessGIT Agent -> admin
all other accounts         -> worker
identity unknown           -> worker
```

Worker Agents:

- execute claimed business tasks;
- write their task outputs and own coordination metadata;
- may create new immutable bug reports under `coordination/bug_reports/`;
- must not fix project/control-plane bugs;
- must not modify protected workflow/schema/CI/task-runner policy files.

Admin Agents:

- review the bug queue;
- repair schema/build/CI/workflow/control-plane problems;
- record resolution commits and validation evidence.

Machine-readable policy:

```text
coordination/AGENT_PERMISSIONS.json
```

Human-readable policy:

```text
coordination/AGENT_PERMISSIONS.md
```

## Final assessment

### Goal alignment

**YES — core architecture and Pilot direction are aligned.**

### Data/provenance accuracy

**Generally good and conservative based on the audited evidence.** Important unknowns are usually preserved as unknown/unverified rather than fabricated.

### Engineering correctness

**Restored to a valid state at the audited rebuild snapshot.** SQLite and FTS rebuild/validation succeeded after the two admin repairs.

### Pilot acceptance

**NOT YET.** Real playback audit coverage and timing-error evidence are still insufficient for the final quality gates.

### FULL_ARCHIVE

```text
NOT AUTHORIZED
```

Continue the Pilot. Do not interpret the current quantity of aligned segments as proof that timestamp accuracy has passed.

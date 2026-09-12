# Miles-Guo_public_archive Current Task

Project: `Miles-Guo_public_archive`  
Repository: `witnessGIT/Miles-Guo_public_archive`  
Current phase: `SITE_ANALYSIS + PILOT`  
Full archive collection: **NOT STARTED / NOT AUTHORIZED UNTIL PILOT PASSES**

## Purpose of this file

This file explains what the current phase is trying to accomplish and what each work unit means.

**Executable task ownership is controlled by `coordination/WORK_QUEUE.jsonl` + `coordination/claims/` + `coordination/completed/`.**

Do not start a work unit merely because this document says `OPEN`. First follow the atomic claim procedure in `coordination/README.md`.

If the user gives a newer explicit instruction, follow it first and update durable repository rules afterward. Otherwise, do not wait for a new prompt: claim the next eligible task and begin.

## Current objective

Build and validate the first real searchable archive model from these three public sources:

1. `gwins` — https://www.gwins.org/
2. `ghot` — https://ghot.ai/
3. `gettrsearch` — https://gettrsearch.com/

The Pilot must prove that the archive can represent:

```text
one livestream
+ multiple source pages/platforms
+ curated text
+ ASR text where available
+ reliable timestamps
+ source traceability
+ searchable structured data
```

The Pilot is not a demo with invented data. Use real public records only.

## Start here on every Agent run

1. Read `AGENTS.md`.
2. Read `coordination/README.md` and `coordination/WORK_QUEUE.jsonl`.
3. Read `coordination/completed/` and `coordination/claims/`.
4. Read `README.md`, `docs/PROJECT_REQUIREMENTS.md`, `docs/NAMING_AND_WORKFLOW.md`, and relevant current files.
5. Inspect recent commits and current repository contents.
6. Select the highest-priority task whose `depends_on` items are all completed and which has neither a completed record nor an active claim.
7. Atomically claim it by creating `coordination/claims/<TASK_ID>.json`.
8. Only after claim succeeds, execute the task.
9. Produce and validate durable repository output.
10. Commit results.
11. Create `coordination/completed/<TASK_ID>.json` pointing to the result commit and outputs.
12. Continue with the next eligible task when safe.

## Work queue details

The task IDs below correspond to the machine-readable queue in `coordination/WORK_QUEUE.jsonl`.

### P0-SCHEMA — Core schema

Create `schema/schema.sql` for the Pilot archive while preserving future extensibility to non-livestream archive items.

Must support, at minimum, the current requirements around livestreams, multiple sources, segments, provenance, curated/ASR text separation, timestamps, quality/review state, and FTS5 build needs.

### P0-SCAFFOLD — Repository scaffold

Create only the real scaffolding needed for data work, including required paths/files such as `.gitignore`, report/template locations and source-data layout.

Do not create fake data or mark a planned directory as completed merely because its name exists in documentation.

### P1-GWINS-STRUCTURE — GWINS structural analysis

Analyze real public pages and document:

- list/archive entry points;
- detail-page URL patterns;
- pagination/navigation;
- stable page/source IDs;
- date/title fields;
- media/source links;
- duplicate-content behavior;
- failure/edge cases.

Write verified findings into `docs/SITE_ANALYSIS.md`, including real example URLs and retrieval date.

### P1-GWINS-TRANSCRIPT — GWINS transcript analysis

Depends on `P1-GWINS-STRUCTURE`.

Analyze:

- curated transcript structure;
- transcript timestamps;
- people/organization/country/topic metadata;
- transcript edge cases;
- how curated text should map into archive fields without replacing source wording.

### P2-GHOT-ARCHIVE — GHOT structural analysis

Analyze real public pages and document:

- archive/list/detail structure;
- stable IDs;
- dates/titles/duration;
- original source links/platform IDs;
- duplicate-content behavior;
- static HTML vs dynamic/API-backed data where observable.

### P2-GHOT-TIMELINE — GHOT time-axis analysis

Depends on `P2-GHOT-ARCHIVE`.

Analyze:

- transcript/ASR structure;
- timestamp granularity;
- selected-clip ranges if present;
- ASR quality limitations;
- whether GHOT can reliably provide a time axis for curated text from another source.

### P3-GETTRSEARCH-STRUCTURE — GettrSearch analysis

Analyze:

- search entry points;
- year filters;
- long/short separation;
- detail/playvideo patterns;
- GETTR IDs/original links where exposed;
- date/title/text availability;
- whether it should be primary, secondary or discovery/backfill source.

### P0-BUILD-DB — Build script

Depends on `P0-SCHEMA`.

Create `scripts/build_db.py` so `database/Miles-Guo_public_archive.sqlite3` can be rebuilt from Git-tracked source data and schema.

SQLite is a build product, not the sole source of truth.

### P0-VALIDATE-DB — Validation script

Depends on `P0-SCHEMA` and `P0-BUILD-DB`.

Create `scripts/validate_db.py` to surface schema, FK, FTS and source-data integrity problems. It must report failures rather than hide them.

### P4-IDENTITY-RULES — Cross-source identity matching

Depends on the three structural site-analysis tasks.

Build and test a reproducible strategy for determining whether records from different sources represent the same livestream.

Evidence may include:

- exact platform video ID;
- date;
- title similarity;
- duration similarity;
- transcript opening/content similarity;
- shared GETTR/Rumble/YouTube source.

Do not merge solely because titles look similar. Preserve score/reason/conflicts.

### P5-PILOT-SELECTION — Select Pilot sample

Depends on site transcript/time-axis analysis and identity rules.

Select 20–30 real livestreams across early/middle/late years where possible.

Attempt to cover:

- GWINS + GHOT overlap;
- GWINS-only case if actually demonstrated by documented search scope;
- GHOT-only case if actually demonstrated;
- GettrSearch discovery/backfill case;
- multiple media-source case;
- transcript with timestamps;
- transcript without precise timestamps.

`not yet found` is not the same as `does not exist`.

### P6-PILOT-EARLY-B001 / MIDDLE-B001 / LATE-B001 — Data collection batches

These are intentionally non-overlapping collection tasks for multiple Agents.

For each assigned batch create Git-friendly source records. Prefer independent batch files to a single shared JSONL file.

At minimum preserve:

- internal/candidate identity;
- title/date;
- source-site provenance;
- source URL;
- third-party ID where available;
- curated text separate from ASR;
- start/end seconds only when actually known;
- retrieval/verification state.

Do not invent timestamps, FPS, frames, IDs or source availability.

### P7-ALIGNMENT-B001 — Transcript/time-axis alignment

For overlapping Pilot records, test curated GWINS text against public time-axis data.

Priority:

1. existing curated timestamps;
2. GHOT time axis + fuzzy text alignment;
3. local ASR only when public timing is inadequate;
4. manual review for unresolved high-value segments.

Record `alignment_method`, `alignment_quality` and whether playback verification was actually performed.

### P8-SQLITE-PILOT — Build searchable Pilot DB

Build and validate `database/Miles-Guo_public_archive.sqlite3` from tracked source data.

Requirements:

- FTS5 over applicable transcript/search fields;
- foreign-key/integrity checks;
- rebuild from `data/` + `schema/`;
- failures remain visible.

### P9-AUDIT-60 — Pilot audit

Randomly audit at least 60 real segments.

For each applicable sample verify:

- correct livestream;
- correct date;
- source traceability;
- text/source consistency;
- actual playback position;
- timestamp error;
- no incorrect cross-source merge.

Target gates:

- false-merge rate approximately 0;
- >= 90% of locatable audited segments within 3 seconds;
- >= 98% within 8 seconds.

Unperformed playback checks are `unverified`, not passes.

### P10-PILOT-DECISION — Pilot decision

Update `reports/pilot_report.md` with actual evidence:

- site-analysis findings;
- coverage;
- cross-source matches/conflicts;
- segment counts;
- curated/ASR coverage;
- alignment distribution;
- playback audit;
- broken/duplicate sources;
- database/source-data sizes;
- unresolved issues;
- `FULL_ARCHIVE: YES/NO` recommendation.

Do not begin FULL_ARCHIVE before this gate is supported by evidence.

## Multi-Agent coordination rules

The authoritative protocol is `coordination/README.md`.

Summary:

- ownership is per task ID;
- claim via creation of `coordination/claims/<TASK_ID>.json`;
- never overwrite an existing claim;
- dependencies are satisfied only by `coordination/completed/<TASK_ID>.json` records;
- completed work should not be redone unless explicitly assigned as verification/fix work;
- collection work is split by non-overlapping batch;
- avoid concurrent edits to one large JSONL file;
- preserve source conflicts instead of overwriting them;
- stale claims require documented takeover procedure.

## Data-source and access rules

- Publicly accessible content only.
- Respect low request rates and caching.
- Do not bypass login, CAPTCHA, paywalls, access controls, or DRM.
- Do not commit full video/audio or large temporary files.
- Temporary downloads belong in ignored cache paths and should be removed when no longer needed.

## Zero-cost rule

The core workflow should remain usable with GitHub, Python, SQLite/FTS5, local open-source tooling, public source pages and local temporary cache.

Do not make paid APIs, commercial vector databases, paid object storage or paid AI services mandatory.

## Historical-recovery future queue

Preserve schema compatibility for future work on:

- deleted/moved livestreams;
- Twitter/X historical posts;
- GETTR historical posts;
- public web archives;
- mirrors/reposts;
- historical citations/screenshots.

A repost or screenshot is not an original publication. Recovery evidence must retain provenance and confidence/source level.

## Stop / escalation conditions

Document the issue rather than guessing when:

- source identity cannot be established;
- dates materially conflict;
- timestamps cannot be verified;
- two records may be different livestreams;
- access requires bypassing controls;
- schema changes could invalidate existing data;
- concurrent edits create unresolved collisions.

Continue with another safe eligible task whenever possible.

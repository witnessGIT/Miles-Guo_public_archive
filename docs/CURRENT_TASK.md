# Miles-Guo_public_archive Current Task

Project: `Miles-Guo_public_archive`  
Repository: `witnessGIT/Miles-Guo_public_archive`  
Current phase: `SITE_ANALYSIS + PILOT`  
Full archive collection: **NOT STARTED / NOT AUTHORIZED UNTIL PILOT PASSES**

## Purpose of this file

This file tells every Agent entering the repository what to do **now**.

If the user gives a newer explicit instruction, follow that instruction first and update this file afterward. Otherwise, do not wait for a new prompt: take the next unfinished safe task below and begin working.

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

1. Read `AGENTS.md`, `README.md`, `docs/PROJECT_REQUIREMENTS.md`, and `docs/NAMING_AND_WORKFLOW.md`.
2. Inspect current repository contents and recent commits.
3. Search existing data/docs before creating a duplicate record.
4. Pick one unfinished work unit below.
5. Produce durable output in the repository.
6. Validate it.
7. Commit it with a clear stage-based commit message.
8. Update this file or the appropriate Pilot report when the work unit changes project status.

## Work queue

### P0 — Repository scaffold required for real data work

Status: **OPEN until verified complete**

Required artifacts:

- `schema/schema.sql`
- `schema/migrations/`
- `data/live_videos/`
- `data/live_segments/`
- `data/sources/`
- `database/`
- `scripts/build_db.py`
- `scripts/validate_db.py`
- `reports/pilot_report.md`
- `.gitignore` covering cache/media/database temporary files as appropriate

Rules:

- Do not create empty directories just for appearance; add `.gitkeep` only when needed by workflow.
- Schema must follow project requirements and remain future-extensible.
- SQLite must be rebuildable from Git-tracked structured source data.

### P1 — GWINS site analysis

Status: **OPEN unless `docs/SITE_ANALYSIS.md` proves otherwise**

Analyze real pages and document:

- list/archive entry points;
- detail page URL pattern;
- pagination/navigation;
- stable page/source IDs;
- livestream date/title fields;
- curated transcript structure;
- transcript timestamps;
- people/organization/country/topic metadata;
- GETTR/Rumble/YouTube or other media links;
- duplicate-content behavior;
- failure/edge cases.

Write findings to `docs/SITE_ANALYSIS.md` with real example URLs and retrieval date.

### P2 — GHOT site analysis

Status: **OPEN unless `docs/SITE_ANALYSIS.md` proves otherwise**

Analyze real pages and document:

- video archive/list structure;
- detail page URL/ID rules;
- dates/titles/duration;
- transcript/ASR structure;
- timestamp granularity;
- source video links/IDs;
- selected clip data if present;
- static HTML vs dynamic/API-backed data;
- ASR quality limitations;
- duplicate-content behavior.

Special goal: determine whether GHOT can serve as a reliable time-axis source for curated transcripts from other sites.

### P3 — GettrSearch site analysis

Status: **OPEN unless `docs/SITE_ANALYSIS.md` proves otherwise**

Analyze real pages and document:

- search entry points;
- year filters;
- long/short video separation;
- detail/playvideo URL patterns;
- GETTR IDs or original GETTR links;
- dates/titles/text availability;
- whether it is best treated as primary source, secondary source, or discovery/backfill source.

### P4 — Cross-source identity matching

Status: **OPEN**

Build and test a deduplication/matching strategy for records that may represent the same livestream.

Evidence candidates:

- exact platform video ID;
- date;
- title similarity;
- duration similarity;
- transcript opening/content similarity;
- shared GETTR/Rumble/YouTube link.

Do not merge two records solely because titles look similar.

Every automatic merge must preserve evidence and a reproducible score/reason.

### P5 — Pilot sample selection

Status: **OPEN**

Select 20–30 real livestreams across early/middle/late years where possible.

The sample should attempt to include:

- records present in GWINS + GHOT;
- GWINS-only case if actually found;
- GHOT-only case if actually found;
- GettrSearch discovery/backfill case if actually found;
- multiple media-source case;
- transcript with timestamps;
- transcript without precise timestamps.

Important: "only in one source" must mean the other relevant sources were actually searched within a documented scope. Do not turn "not yet found" into "does not exist".

### P6 — First real structured records

Status: **OPEN**

For selected Pilot items, create Git-friendly source records.

Target patterns:

- one JSON record per livestream under `data/live_videos/<year>/`;
- source records under `data/sources/` or the schema-approved equivalent;
- segment JSONL under `data/live_segments/<year>/` or the schema-approved equivalent.

At minimum preserve:

- internal ID;
- title/date;
- source-site provenance;
- source URL;
- third-party source ID where available;
- curated text separately from ASR;
- start/end seconds when actually known;
- retrieval/verification status.

Never invent missing timestamps, FPS, frames, or source IDs.

### P7 — Transcript/time-axis alignment

Status: **OPEN**

For overlapping GWINS/GHOT Pilot records, test whether curated GWINS text can be aligned to GHOT timestamps.

Priority order:

1. existing curated timestamps;
2. GHOT time-axis + fuzzy text alignment;
3. local ASR only when existing public timing is inadequate;
4. manual review for unresolved high-value segments.

Record `alignment_method`, `alignment_quality`, and whether actual playback verification was performed.

### P8 — Build searchable SQLite

Status: **OPEN**

Build `database/Miles-Guo_public_archive.sqlite3` from Git-tracked source data.

Requirements:

- SQLite is a build product, not the sole truth source;
- FTS5 search over applicable transcript/search text;
- foreign-key/integrity checks;
- rebuild from `data/` + `schema/`;
- validation script reports failures instead of hiding them.

### P9 — Pilot audit

Status: **BLOCKED until enough real segments exist**

Randomly audit at least 60 real segments.

For each audited segment verify as applicable:

- correct livestream;
- correct date;
- source traceability;
- text/source consistency;
- actual playback position;
- timestamp error;
- no incorrect cross-source merge.

Target gates:

- livestream false-merge rate: approximately 0;
- >= 90% of locatable audited segments within 3 seconds;
- >= 98% within 8 seconds.

Unperformed playback checks are `unverified`, not passes.

### P10 — Pilot decision

Status: **BLOCKED until P9 is complete**

Update `reports/pilot_report.md` with:

- site-analysis findings;
- coverage;
- cross-source matches/conflicts;
- segment counts;
- curated/ASR coverage;
- alignment-quality distribution;
- playback audit results;
- broken/duplicate sources;
- database/source-data sizes;
- unresolved problems;
- recommendation `FULL_ARCHIVE: YES/NO`.

Do not begin FULL_ARCHIVE before this decision is supported by evidence.

## Multi-Agent coordination

When multiple agents enter at the same time:

- Prefer different work units or different non-overlapping Pilot samples.
- Before adding data, search existing source URLs, source IDs, and `live_id` values.
- Preserve conflicting source claims instead of overwriting them.
- Keep changes small enough to review in Git.
- Record completed work durably; do not rely on chat memory.
- If another agent has already completed a queue item, validate it and move to the next incomplete item instead of redoing it.

## Data-source and access rules

- Publicly accessible content only.
- Respect low request rates and caching.
- Do not bypass login, CAPTCHA, paywalls, access controls, or DRM.
- Do not commit full video/audio or large temporary files.
- Temporary downloads belong under ignored cache paths and should be removed when no longer needed.

## Zero-cost rule

The core workflow should remain usable with:

- GitHub;
- Python;
- SQLite / FTS5;
- local open-source tooling;
- public source pages;
- local temporary cache.

Do not make paid APIs, commercial vector databases, paid object storage, or paid AI services mandatory for building or reading the archive.

## Historical-recovery future queue

Do not let this distract from the current livestream Pilot, but preserve schema compatibility for future work on:

- deleted/moved livestreams;
- Twitter/X historical posts;
- GETTR historical posts;
- public web archives;
- mirrors/reposts;
- historical citations and screenshots.

Recovered content must preserve provenance and confidence/source level. A repost or screenshot is not an original publication.

## Stop / escalation conditions

Stop the affected work unit and document the issue rather than guessing when:

- source identity cannot be established;
- dates conflict materially;
- timestamps cannot be verified;
- two records may be different livestreams;
- a source requires bypassing access control;
- a schema change could invalidate already-collected data;
- another agent's concurrent edits create an unresolved collision.

Continue with other safe queue items whenever possible.

# Miles-Guo_public_archive Pilot SQLite Build

Project: `Miles-Guo_public_archive`  
Task: `P8-SQLITE-PILOT`  
Database: `database/Miles-Guo_public_archive.sqlite3`

## Result

A real SQLite Pilot artifact was rebuilt from the current Git-tracked source data and committed to `main`.

The first reproducible GitHub Actions build completed successfully and created the database in commit:

```text
0bb9fb4  build: refresh Pilot SQLite database
```

Current database blob metadata:

```text
path: database/Miles-Guo_public_archive.sqlite3
blob: 3f3bef7b868346c23b1265c1d37fe70039391113
size: 208896 bytes
```

## Reproducible build

The repository now contains:

```text
.github/workflows/pilot-db.yml
```

The workflow rebuilds and validates the Pilot database when tracked source data, schema, or database build/validation scripts change.

Equivalent local commands remain:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

The database is derived output. Git-tracked JSON/JSONL under `data/` remains the archival source of truth.

## Build counts

The successful build reported:

```text
archive_items:              0
entities:                   0
item_entities:              0
item_topics:                0
live_segments:              7
live_segments_fts:          7
live_sources:              39
live_videos:               27
source_match_candidates:   12
topics:                     0
```

The database therefore reflects all three 9-item Pilot periods currently collected:

```text
early:  2017-2019
middle: 2020-2021
late:   2022-2023
```

and the first P7 alignment segment batch.

## Validation

`scripts/validate_db.py` completed with:

```text
validation: OK (1 warning(s))
```

The single warning was expected and provenance-safe:

```text
7 timed segment(s) have not been playback-verified yet
```

No validation error was reported. In particular, the validator successfully checked:

- SQLite integrity;
- foreign keys;
- required tables;
- Git source row counts versus SQLite row counts;
- `live_segments` versus FTS row count;
- canonical live ID format;
- source traceability for every canonical live;
- source ID/URL presence;
- segment ID/index consistency;
- segment timing/provenance requirements.

The warning must remain visible until actual playback audit work is performed; P8 does not convert the seven P7 timed candidates into playback-verified timestamps.

## Search readiness

`live_segments_fts` contains the same 7 rows as `live_segments`, so the current Pilot segment text is queryable through SQLite FTS5.

This is still a small alignment Pilot rather than the final archive corpus. Most Pilot livestreams currently have source-level metadata but do not yet have full segment text materialized into `live_segments`.

## Automation verification

Two consecutive `Build Pilot SQLite` workflow runs completed successfully after the workflow was introduced. The first created the SQLite artifact; the second re-ran after the data-layout documentation update and completed successfully, confirming the build is reproducible from the current `main` state rather than a one-off local file.

## Outputs

- `database/Miles-Guo_public_archive.sqlite3`
- `.github/workflows/pilot-db.yml`
- `data/README.md` build documentation
- `reports/PILOT_SQLITE_P8.md`

## Remaining gate

P8 establishes a valid, rebuildable, searchable Pilot database. It does **not** satisfy the later timestamp-accuracy/playback-verification gate. That remains a separate audit task so that build success cannot be confused with media-position correctness.

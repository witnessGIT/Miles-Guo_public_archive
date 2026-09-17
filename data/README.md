# Miles-Guo_public_archive Data Layout

`data/current/` is the active Git-tracked source of truth for the restarted original-livestream
archive records. Do not treat SQLite as the only copy of archive data.

Older files directly under paths such as `data/live_segments/`, `data/sources/`,
`data/playback_audits/`, and `data/playback_evidence/` are sealed historical Pilot material.
They remain visible for audit history only and must not be used as current progress, current
task input, or current database input.

Pilot data should be split into reviewable, non-overlapping files instead of one giant shared JSONL.

Recommended layout:

```text
data/current/
├── live_videos/
│   ├── early/
│   ├── middle/
│   └── late/
├── live_segments/
│   ├── early/
│   ├── middle/
│   └── late/
├── sources/
│   ├── gwins/
│   ├── ghot/
│   └── gettrsearch/
├── archive_items/
├── entities/
└── topics/
```

Rules:

- use real public records only;
- preserve source URL, source site, retrieval/verification state and third-party IDs when available;
- keep curated text and ASR text separate;
- store `start_sec` / `end_sec` only when actually known;
- never invent FPS, frame positions, source availability or cross-source identity;
- prefer independent batch files so multiple Agents do not edit the same large JSONL file;
- canonical cross-source merges belong to identity/matching work, not individual collectors.

## SQLite build

The formal database remains a rebuildable artifact at `database/Miles-Guo_public_archive.sqlite3`.

Run locally with:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

The repository workflow `.github/workflows/pilot-db.yml` performs the same build + validation when tracked source data, schema, or the database build/validation scripts change. The workflow commits the rebuilt Pilot SQLite artifact only after validation succeeds.

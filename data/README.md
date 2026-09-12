# Miles-Guo_public_archive Data Layout

`data/` is the Git-tracked source of truth for archive records. Do not treat SQLite as the only copy of archive data.

Pilot data should be split into reviewable, non-overlapping files instead of one giant shared JSONL.

Recommended layout:

```text
data/
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

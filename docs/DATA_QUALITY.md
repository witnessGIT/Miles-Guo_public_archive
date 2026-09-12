# DATA_QUALITY

## Quality states

- `inventory_unverified`: discovered from a list/search page only.
- `verified_metadata`: date/title/identity checked against a detail page or multiple matching sources.
- `transcript_unverified`: transcript exists but has not been checked against the original media.
- `verified`: source identity and required metadata pass validation; any transcript quality is separately recorded.

## Minimum acceptance checks

A canonical live record must have:

1. valid `LIVE_YYYYMMDD_NNN` id;
2. valid publication date;
3. at least one source record;
4. no silent source-id normalization;
5. provenance for every imported text body;
6. human text and ASR stored separately;
7. no invented duration, resolution, original URL or source id.

## Cross-source match confidence

Prefer exact original URL/platform id. If unavailable, require at least two of date/sequence, strongly matching title, duration or timestamp structure.

Ambiguous matches stay separate until resolved.

## Database gates

`scripts/validate_db.py` must pass:

- SQLite integrity check;
- foreign-key check;
- every live item has a source;
- internal id format check;
- FTS row count equals live record count.

## Source text policy

Keep the source text as captured and record its type/attribution. Corrections belong in derived/normalized fields; do not destroy the raw provenance.

# DATA_MODEL

## Canonical identity

Each underlying public video/livestream receives one internal id:

`LIVE_YYYYMMDD_NNN`

`NNN` is the sequence number for that calendar date when the source provides one. Source-specific ids are never substituted for the internal id.

## `live_videos`

One row per underlying video/live item.

Required core fields:

- `live_id`
- `published_date`
- `sequence_no`
- `title`
- `content_type`
- `language`
- `quality_status`

Optional technical fields such as duration and dimensions are populated only when a source explicitly provides them.

## `sources`

One row per archive/discovery source attached to a live item. Source-specific identifiers remain intact.

Important distinctions:

- `source_site`: archive/discovery site (`gwins`, `ghot`, `gettrsearch`).
- `source_url`: the page actually inspected on that site.
- `third_party_id`: that site's own identifier.
- `original_platform`: original publication platform when known.
- `original_url`: original platform locator when known.

A mismatch between source ids is data, not an error to hide.

## `transcripts`

Text is provenance-aware. The following must remain separate:

- `human`: manually organized/edited transcript.
- `asr`: automatic speech recognition output.
- `subtitle`: published subtitle track.
- `excerpt`: intentionally partial text.

No automatic process may silently replace a human transcript with ASR.

## `transcript_segments`

Time-addressable text uses seconds as the canonical locator:

- `start_sec`
- `end_sec`
- `segment_text`

Frame numbers may be added later as auxiliary metadata but are not the primary locator.

## FTS

`archive_fts` is a rebuildable SQLite FTS5 index over canonical titles and transcript text. It is a query product, not a source of truth.

## Rebuild rule

The database must be reproducible from versioned files under `data/` plus `schema/` using `scripts/build_db.py`.

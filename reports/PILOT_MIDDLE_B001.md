# Miles-Guo_public_archive Middle Pilot Batch B001

Project: `Miles-Guo_public_archive`  
Task: `P6-PILOT-MIDDLE-B001`  
Verified: `2026-09-12T16:10:00Z`

## Result

The middle-year Pilot collection batch now contains nine canonical Pilot livestream records covering 2020-2021.

Git-tracked structured data:

```text
data/live_videos/middle/pilot_middle_b001.jsonl
data/sources/ghot/pilot_middle_b001.jsonl
data/sources/gwins/pilot_middle_b001.jsonl
data/source_match_candidates/pilot_middle_b001.jsonl
```

Counts contributed by this batch:

```text
live_videos:               9
GHOT verified source rows: 9
GWINS candidate rows:      3
identity candidates:       3
```

All nine livestreams remain `status = partial`. This task collects identity/source metadata only; segment-level text alignment and actual playback verification remain downstream Pilot work.

## Canonical IDs

```text
LIVE_20200323_001
LIVE_20200418_001
LIVE_20200606_001
LIVE_20201001_001
LIVE_20201120_001
LIVE_20210612_001
LIVE_20210902_001
LIVE_20211029_001
LIVE_20211124_001
```

The canonical `_001` suffix is an internal per-date sequence and does not copy GHOT/GWINS source-side ordinals.

## Verified GHOT records

The nine selected GHOT detail pages were verified as public archive records and stored with their source page IDs, URLs, titles, provenance and timing-related observations.

Important examples:

- `2020-04-18-3` displays a title beginning `2020.04.18-2`; the URL ordinal and visible title ordinal are deliberately preserved separately.
- `2020-10-01-3` displays `2020.10.01-2 10.1的直播_X264`; its ASR is severely garbled and is explicitly marked low-quality rather than treated as clean searchable truth.
- `2020-11-20-4` is the selected `王建之死 两周年` record. GWINS exposes multiple other records on the same date, so date-only identity matching is forbidden.
- `2021-09-02-2` has a 9m47s second-level transcript timeline and exposes GETTR/Rumble/原文 link labels.
- `2021-10-29-1` is about 4h22m and contains noisy transcript material; GHOT itself indicates that the video does not require text transcription.
- `2021-11-24-1` is about 5h50m. Pre-roll/noisy material appears before the livestream greeting around 18:13; this batch does not turn that observation into a canonical segment offset.

## GWINS handling

This pass intentionally distinguishes a discovered source from a freshly verified direct page.

Three per-item GWINS candidates are stored:

```text
PILOT-M007 -> https://gwins.org/cn/milesguo/23292.html
PILOT-M008 -> https://gwins.org/cn/milesguo/23425.html
PILOT-M009 -> https://gwins.org/cn/milesguo/23454.html
```

`PILOT-M007` is corroborated by an exact GWINS list entry and a public mirror whose Source field points to `23292`. The direct page re-fetch returned a cache miss in this pass.

The M008/M009 per-item URLs had been discovered during Pilot research, but current direct re-fetch attempts timed out. They are therefore stored as `status = discovered`, not silently promoted to freshly verified records.

For M001, M003, M005 and M006, GWINS list-level title/date/ordinal corroboration was observed, but no stable per-item detail URL was resolved in this pass. Those list-level observations are preserved in GHOT metadata notes instead of creating fake per-item GWINS rows.

## Identity decisions

Three GHOT/GWINS pairs have enough evidence to retain as reproducible candidates but not enough freshly captured direct-cross-reference evidence for automatic merging:

| Pilot case | score | decision | reason |
| --- | ---: | --- | --- |
| PILOT-M007 | 0.84 | `needs_review` | exact date/ordinal, strong title match, secondary Source pointer; direct target not freshly retrieved |
| PILOT-M008 | 0.80 | `needs_review` | date/ordinal/title evidence plus discovered per-item URL; fresh direct retrieval timed out |
| PILOT-M009 | 0.80 | `needs_review` | date/ordinal/title evidence plus discovered per-item URL; fresh direct retrieval timed out |

No `auto_merge` decision is created merely from date/title similarity.

## Same-day and ordinal hazards

Two classes of identity risk are now explicitly represented in the structured data:

1. **Same-day multiplicity** — e.g. 2020-11-20 has multiple `_1/_2/_3/_4` records; a date is not a livestream identity.
2. **Slug/title ordinal mismatch** — e.g. GHOT `2020-04-18-3` displays a title carrying `-2`, and GHOT `2020-10-01-3` displays a title carrying `-2`.

These cases are useful Pilot stress tests and must remain visible to P7/P9 rather than being normalized away.

## Text/timing policy

This P6 batch does not create canonical `live_segments` or claim playback accuracy. GHOT timing remains source timing; noisy ASR remains machine text. Curated text, ASR text, timing source and playback verification must remain separately attributable when P7 performs alignment.

## Structural validation

The records contributed by this batch were loaded against the current relevant schema in an isolated SQLite validation pass:

```text
live_videos: 9
live_sources: 12
source_match_candidates: 3
PRAGMA foreign_key_check: no violations
PRAGMA integrity_check: ok
metadata_json: all parse successfully
evidence_json: all parse successfully
```

The whole-repository `scripts/build_db.py` / `scripts/validate_db.py` run remains the authoritative integration check after all P6 batches are present.

## Handoff

`P6-PILOT-MIDDLE-B001` now has durable source data and conservative identity evidence. Downstream work should resolve the `needs_review` pairs using direct cross-links/platform IDs or fresh source retrieval, not by lowering the matching threshold.

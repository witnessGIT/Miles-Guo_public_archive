# Miles-Guo_public_archive Early Pilot Batch B001

Project: `Miles-Guo_public_archive`  
Task: `P6-PILOT-EARLY-B001`  
Verified: `2026-09-13`

## Result

The first early-year Pilot collection batch now contains nine canonical Pilot livestream records covering 2017-2019.

Git-tracked structured data:

```text
data/live_videos/early/pilot_early_b001.jsonl
data/sources/gwins/pilot_early_b001.jsonl
data/sources/ghot/pilot_early_b001.jsonl
data/source_match_candidates/pilot_early_b001.jsonl
```

Counts contributed by this batch:

```text
live_videos:              9
GWINS source rows:        9
GHOT source rows:         6
identity match evidence:  6
```

All nine livestreams remain `status = partial`: source identity/metadata is collected, while segment-level text alignment and playback verification belong to later Pilot tasks.

## Canonical IDs

The internal IDs assigned in this batch are:

```text
LIVE_20170523_001
LIVE_20170610_001
LIVE_20171004_001
LIVE_20180419_001
LIVE_20180616_001
LIVE_20180815_001
LIVE_20190530_001
LIVE_20190920_001
LIVE_20191029_001
```

The `_001` portion is an internal per-date canonical sequence. It does **not** copy a third-party source ordinal. For example, the 2018-04-19 Pilot seed is source-side `20180419_3`, but its first canonical archive record for that date is `LIVE_20180419_001`.

## Confirmed GHOT ↔ GWINS direct pairs

Six GHOT pages expose an `原文` link that resolves directly to the exact GWINS detail record stored in this batch:

| Pilot case | GHOT source page | GWINS source page | identity-v1 |
| --- | --- | --- | ---: |
| PILOT-E001 | `2017-05-23-1` | `565` | 0.98 auto_merge |
| PILOT-E002 | `2017-06-10-1` | `575` | 0.98 auto_merge |
| PILOT-E003 | `2017-10-04-1` | `695` | 0.98 auto_merge |
| PILOT-E007 | `2019-05-30-2` | `22012` | 0.98 auto_merge |
| PILOT-E008 | `2019-09-20-1` | `411` | 0.98 auto_merge |
| PILOT-E009 | `2019-10-29-1` | `437` | 0.98 auto_merge |

The matching evidence is stored in `source_match_candidates`, not only in this prose report.

## Critical same-day correction

The 2019-05-30 case demonstrates why date-only matching is forbidden.

Correct pair:

```text
GHOT 2019-05-30-2
  -> direct 原文 link
GWINS 22012 / 20190530_2 / 郭文贵先生和战友们聊天
```

A different GWINS item also exists on the same date:

```text
GWINS 22011 / 20190530_1
```

That record is **not** merged into `LIVE_20190530_001` merely because the date matches.

## 2018 source handling

For PILOT-E004, E005 and E006, this collection pass verified the selected GWINS records but did not find equally strong direct GHOT identity evidence.

Therefore this batch stores only the confirmed GWINS archive source for those three cases. It does **not** label them `GWINS-only`; absence claims require a documented bounded search and are not inferred from a failed lookup.

PILOT-E006 (`GWINS 21826`) is also explicitly marked `mixed_unverified` at transcript provenance level because the source page says the following content is an uncorrected draft from the named contributor. It is not silently promoted to fully human-curated text.

## External media links

Verified external media URLs exposed by GWINS are preserved inside each source row's `metadata_json`, including examples from YouTube, Rumble and Odysee.

They are preserved as source evidence without asserting an unverified `original` versus `backup` role. Later normalization may promote them to dedicated media-source rows only when that role is known.

## Text and timing policy

GHOT source rows are explicitly marked as machine-generated ASR/timing sources. GWINS source rows preserve organizer/provenance information, but a `文字整理` attribution is not treated as proof that every paragraph is purely human-curated.

This P6 batch deliberately does not invent canonical `live_segments` by aligning snippets itself. Canonical segment alignment is the separate `P7-ALIGNMENT-B001` task, which must keep:

```text
text_curated
text_asr
start_sec / end_sec
curated_source_id
asr_source_id
time_source_id
alignment_method
alignment_quality
playback_verified
```

separate and auditable.

## Structural validation

The records contributed by this batch were loaded against the current schema in an isolated SQLite validation pass:

```text
live_videos: 9
live_sources: 15
source_match_candidates: 6
PRAGMA foreign_key_check: no violations
PRAGMA integrity_check: ok
metadata_json: all parse successfully
evidence_json: all parse successfully
```

The repository's full `build_db.py` / `validate_db.py` pipeline remains the authoritative whole-repository check after all P6 batches are present.

## Handoff

`P6-PILOT-EARLY-B001` is ready for downstream work. The next dependent alignment task must use the stored source IDs and identity evidence rather than rediscovering or remapping these livestreams from date alone.

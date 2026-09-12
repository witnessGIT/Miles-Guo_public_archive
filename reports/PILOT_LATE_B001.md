# Miles-Guo_public_archive Pilot Late B001

Project: `Miles-Guo_public_archive`  
Task: `P6-PILOT-LATE-B001`  
Phase: `PILOT`  
Range: `2022-2023`  
Collected: `2026-09-12`

## Result

This batch materializes the 9 late Pilot cases selected by `P5-PILOT-SELECTION` as Git-tracked canonical livestream/source records without inventing timestamps, source absence, FPS, or playback verification.

Durable records added:

- 9 `live_videos` records;
- 8 verified GHOT archive-page source records;
- 4 verified GWINS archive-page source records;
- 3 high-confidence `identity-v1` cross-source match records.

The source count is intentionally smaller than every plausible cross-site candidate. A source was attached to a canonical live only when the current evidence was strong enough under `docs/IDENTITY_MATCHING.md`. `not collected in this batch` does not mean `source does not exist`.

## Pilot cases

| Case | Canonical live ID | Seed evidence retained | Current source state |
| --- | --- | --- | --- |
| PILOT-L001 | `LIVE_20220126_001` | GHOT `2022-01-26-2`, 10m00s second-level ASR timeline | GHOT verified |
| PILOT-L002 | `LIVE_20220506_001` | GHOT path `2022-05-06-1`, title-side `2022.05.06-2`, ~3h42m | GHOT verified; ordinal mismatch preserved |
| PILOT-L003 | `LIVE_20220511_001` | GHOT `2022-05-11-2` + GWINS `23878` + GETTR/Rumble identities | GHOT/GWINS merged by exact shared platform IDs |
| PILOT-L004 | `LIVE_20220529_001` | GHOT `2022-05-29-6`, title-side `2022.05.29-2`, ~1h40m | GHOT verified; `needs_review` because site ordinals conflict |
| PILOT-L005 | `LIVE_20221024_001` | GHOT `2022-10-24-1`, 10m00s second-level ASR timeline | GHOT verified |
| PILOT-L006 | `LIVE_20230122_001` | GHOT `2023-01-22-2`, long-form 7h52m record | GHOT verified; same-day multi-record warning retained |
| PILOT-L007 | `LIVE_20230310_001` | GHOT `2023-03-10-1` + GWINS `24261` + GETTR/Rumble identities | GHOT/GWINS merged by exact shared platform IDs |
| PILOT-L008 | `LIVE_20230312_001` | GWINS `24266`, GETTR streaming + Rumble, explicit HH:MM:SS timeline | GWINS verified; no GHOT absence claim |
| PILOT-L009 | `LIVE_20230314_001` | GHOT `2023-03-14-1` + GWINS `24264` | GHOT/GWINS merged by direct cross-reference |

## Identity evidence

### L003 — 2022-05-11

Verified identities already established by `identity-v1`:

- GHOT: `https://ghot.ai/archive/videos/2022-05-11-2`
- GWINS: `https://gwins.org/cn/milesguo/23878.html`
- GETTR: `https://gettr.com/streaming/p19cmxu5e7b`
- Rumble: `https://rumble.com/v5af5v1-20220511-2.html`

Decision: `auto_merge`, score `1.00` (`shared_platform_id`).

### L007 — 2023-03-10

Verified Pilot overlap:

- GHOT: `https://ghot.ai/archive/videos/2023-03-10-1`
- GWINS: `https://gwins.org/cn/milesguo/24261.html`
- GETTR: `https://gettr.com/post/p2b18ew21e7`
- Rumble: `https://rumble.com/v5b2sws-20230310-1.html`

Decision: `auto_merge`, score `1.00` (`shared_platform_id`).

### L009 — 2023-03-14

`identity-v1` already verified that GHOT directly cross-references the exact GWINS detail page:

- GHOT: `https://ghot.ai/archive/videos/2023-03-14-1`
- GWINS: `https://gwins.org/cn/milesguo/24264.html`
- GETTR observed for the GWINS record: `https://gettr.com/post/p2bexmi7ac8`

Decision: `auto_merge`, score `0.98` (`direct_cross_reference`).

## Important correction: 2022-05-29 ordinals cannot be trusted

The late batch found a concrete anti-error case:

- GHOT path: `2022-05-29-6`
- GHOT title-side label: `2022.05.29-2 文贵大直播《避风港》(53)专场 ...`
- GWINS search/index evidence shows `20220529_1` is the matching `《避风港》(53)专场` program;
- GWINS `20220529_2` is a different record titled `七哥乱聊直播`.

Therefore the archive must **not** equate GHOT/GWINS suffixes. The plausible GWINS `20220529_1` candidate is deliberately not attached to `LIVE_20220529_001` in this batch because current Tier-A identity evidence was not strong enough. The canonical live remains `needs_review` rather than silently merging by title/date.

This directly validates the existing rule: source-side `_1` / `_2` / GHOT suffixes are source metadata only and never determine canonical `LIVE_YYYYMMDD_NNN`.

## Same-day canonical ID note

For `2023-01-22`, GWINS indexes multiple same-day livestream entries. The selected GHOT seed is the record labeled as the lower/second half. The current canonical ID is `LIVE_20230122_001` because it is the first canonical livestream assigned for that date in this archive. The source-side `-2` / `20230122_2` label is preserved as evidence but is not copied into the canonical NNN. Existing canonical IDs must not later be renumbered just to mirror source ordinals.

## Validation performed

The new rows were parsed as JSON/JSONL and loaded into an isolated SQLite database using the current `live_videos`, `live_sources`, and `source_match_candidates` schema constraints.

Observed validation result:

```text
live_videos:             9
live_sources:           12
source_match_candidates: 3
PRAGMA foreign_key_check: no violations
PRAGMA integrity_check: ok
metadata_json parse failures: 0
evidence_json parse failures: 0
```

This is a batch-level structural validation. It is **not** the P7 transcript alignment audit and does not claim real playback-position verification.

## Deferred work

- Do not infer that L001/L002/L005/L006 lack GWINS records; exact per-item cross-source verification remains open where not attached here.
- Do not infer that L008 lacks GHOT; this batch only has verified GWINS evidence for the selected case.
- Segment extraction/alignment and actual playback checks remain `P7-ALIGNMENT-B001` / `P9-AUDIT-60` scope.
- The 2022-05-29 candidate relationship should be revisited only with stronger direct cross-link/shared-platform or transcript-opening evidence.

## Output files

- `data/live_videos/late/pilot_late_b001.jsonl`
- `data/sources/ghot/pilot_late_b001.jsonl`
- `data/sources/gwins/pilot_late_b001.jsonl`
- `data/source_match_candidates/pilot_late_b001.jsonl`
- `reports/PILOT_LATE_B001.md`

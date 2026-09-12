# Miles-Guo_public_archive Pilot Audit — PILOT-E004

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-E004`  
Case: `PILOT-E004`  
Live ID: `LIVE_20180419_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:17:00Z`

## Segment under audit

`data/live_segments/alignment/LIVE_20180419_001.jsonl` contains one aligned segment:

- segment: `LIVE_20180419_001_SEG_000000`
- curated text: `这个世界上美元永远是最好的`
- ASR context: `这个世界上美元永远是最好的如果美元不行`
- start: `149.0` sec
- end: `157.0` sec
- curated source: `SRC_1244FF09`
- ASR/time source: `SRC_3313B4E2`
- alignment method: `ghot_exact_phrase_v1`
- alignment quality: `1.0`
- playback verified: `0`

## Public-source checks

### GHOT

The corresponding public GHOT transcript for the 2018-04-19 interview exposes:

- `02:29` — `说你怎么来保护自己我给你们建议非常清楚，这个世界上美元永远是最好的如果美元不行。`
- `02:37` — the transcript moves into the next sentence concerning Swiss currency / pound sterling.

`02:29 = 149` seconds and `02:37 = 157` seconds. The stored start/end interval therefore matches the public GHOT timestamped transcript boundary for the aligned phrase.

### GWINS

GWINS page:

`https://gwins.org/cn/milesguo/21780.html`

identifies the corresponding 2018-04-19 third livestream/interview record and preserves the curated human-organized text containing the same recommendation that the U.S. dollar is the best currency. This independently supports the curated-text provenance used in the cross-source alignment.

## Audit result

- Correct case/date/text provenance: **supported**
- GHOT start boundary at 149s: **exactly corroborated**
- GHOT end boundary at 157s: **corroborated as transition to the next transcript sentence**
- GWINS curated text consistency: **supported**
- Cross-source text alignment: **supported**
- Actual media playback independently observed: **NO**
- Observed player position: **not measured**
- Playback timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot-60 real playback checks: **NO**

## Disposition

Keep the segment as `aligned_unverified_playback`. The exact public transcript/time-axis agreement and `alignment_quality = 1.0` establish alignment evidence, not actual playback verification.

Do not convert the segment to a playback pass or report zero timing error until a playback-capable audit independently observes the media at the expected position.

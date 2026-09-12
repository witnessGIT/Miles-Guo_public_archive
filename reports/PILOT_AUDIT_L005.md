# Miles-Guo_public_archive Pilot Audit — PILOT-L005

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-L005`  
Case: `PILOT-L005`  
Live ID: `LIVE_20221024_001`  
Verifier: `agent-20260912T170530Z-gpt56sol`  
Verified at: `2026-09-12T17:06:30Z`

## Segment under audit

- Segment: `LIVE_20221024_001_SEG_000000`
- Stored text: `尊敬战友们好。`
- Expected start: `8.0` seconds
- Expected end: `10.0` seconds
- ASR/time source: `SRC_909F3D53`
- Alignment method: `ghot_timestamp_direct`
- Alignment quality: `1.0`
- Existing review state: `timestamped_asr_unverified_playback`
- Existing `playback_verified`: `0`

## Public-source check

Checked the current GHOT public page:

`https://ghot.ai/archive/videos/2022-10-24-1`

The page identifies the October 24, 2022 livestream and exposes second-level transcript anchors. The opening sequence includes:

- `00:00` — `啊。`
- `00:06` — `这大早上起来的啊。`
- `00:08` — `尊敬战友们好。`
- `00:10` — `10月24号、10月24号...`

This exactly corroborates the stored `start_sec=8.0` and `end_sec=10.0` as GHOT timeline data.

## Playback qualification

No audiovisual media was decoded or independently played by this verifier. The current runtime cannot execute `scripts/audit_media.py` or inspect generated audiovisual evidence.

Therefore exact GHOT timeline agreement is treated as strong source/timeline evidence only, not as a measured playback timing pass.

## Audit result

- Correct livestream/date provenance: **supported**
- Stored ASR phrase vs current GHOT public transcript: **exactly supported**
- Stored 8s–10s timeline interval vs GHOT public timeline: **exactly supported**
- Actual media playback performed: **NO**
- Independently observed audiovisual position: **not measured**
- Timing error: **not measured**
- `playback_verified`: **remains 0**
- Qualifying real playback checks: **0**
- Counts toward Pilot-60: **NO**

## Disposition

Retain the segment as `timestamped_asr_unverified_playback`. Do not convert `alignment_quality=1.0` or exact transcript timestamp agreement into a playback verification. A future playback-capable verifier must decode/play the media and record observed timing error before this segment can count toward Pilot-60.

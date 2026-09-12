# Miles-Guo_public_archive Pilot Audit — PILOT-M002

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M002`  
Case: `PILOT-M002`  
Live ID: `LIVE_20200418_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T16:38:00Z`

## Segments under audit

The case currently has three GHOT source-backed ASR/timeline anchors in `data/live_segments/2020/LIVE_20200418_001.jsonl`:

1. `LIVE_20200418_001_SEG_000000` — expected start `123.0` sec — ASR: `好，亲爱的兄弟姐妹们啊，亲爱的兄弟姐妹们。`
2. `LIVE_20200418_001_SEG_000001` — expected start `186.0` sec — ASR: `明天是4月19日。`
3. `LIVE_20200418_001_SEG_000002` — expected start `1104.0` sec — ASR: `记住我今天的话：我忘记之日，就是天地灭我之时。`

All three use `SRC_3860DC62` as ASR/time source, use `ghot_timestamp_direct_asr_only`, have no asserted `end_sec`, and already have `playback_verified = 0`.

## Public-source checks performed

### GHOT archive identity

Checked:

`https://ghot.ai/archive/videos/2020-04-18-3`

The public GHOT record identifies the same 2020-04-18 livestream. The source record intentionally preserves an ordinal mismatch: the GHOT page slug is `2020-04-18-3`, while the visible title carries `2020.04.18-2`. This audit does not normalize or infer equivalence between those ordinals.

### GHOT public timestamped transcript

The publicly indexed GHOT transcript exposes the following exact timestamp/text pairs for this record:

- `02:03` — `好，亲爱的兄弟姐妹们啊，亲爱的兄弟姐妹们。`
- `03:06` — `明天是4月19日。`
- `18:24` — `记住我今天的话：我忘记之日，就是天地灭我之时。`

Converted to seconds, those timestamps are exactly:

- `02:03` = `123` seconds;
- `03:06` = `186` seconds;
- `18:24` = `1104` seconds.

These values exactly match all three tracked `start_sec` anchors. This is strong corroboration of the stored GHOT public timeline and ASR provenance.

However, transcript/timeline agreement is not the same as independently observing the spoken content at those positions in an actual media player.

### Playback availability

In the current audit environment no usable media playback surface was available for this record from which the expected 123s, 186s, and 1104s positions could be independently observed. Therefore no media-position observation or playback timing error was recorded.

## Audit result

For all three segments:

- Correct livestream/date provenance: **supported by GHOT public metadata**
- GHOT timeline/text anchor consistency: **exactly corroborated**
- Stored start seconds vs GHOT public timestamp text: **exact match**
- Actual media playback performed: **NO**
- Observed playback position: **not measured**
- Playback timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep all three segments as `timestamped_asr_only_unverified_playback`. Do not promote the exact transcript/timeline agreement into a playback pass, and do not invent `end_sec`, FPS, frame numbers, or a zero-second playback error.

This audit provides durable evidence that the stored GHOT timestamp anchors are reproduced exactly by GHOT's public timestamped transcript. A future playback-capable worker or the aggregate `P9-AUDIT-60` gap-cleanup stage must still perform actual media playback before these segments can count toward the Pilot playback-accuracy thresholds.

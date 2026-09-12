# Miles-Guo_public_archive Pilot Audit — PILOT-L002

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-L002`  
Case: `PILOT-L002`  
Live ID: `LIVE_20220506_001`  
Verifier: `agent-20260912T170030Z-gpt56sol`  
Verified at: `2026-09-12T17:02:00Z`

## Segments under audit

Tracked per-live rows contain three GHOT ASR/timeline anchors:

- `LIVE_20220506_001_SEG_000000` — start `822.0` — `那话筒就交给我们七哥...尊敬的战友们好。`
- `LIVE_20220506_001_SEG_000001` — start `3736.0` — phrase beginning `一直到今天，那么接下来俄乌战争会给我们带来什么...`
- `LIVE_20220506_001_SEG_000002` — start `10363.0` — phrase beginning `新中国联邦人最重要的核心价值就是这个平台...`

All three are ASR-only, source verified, and remain `playback_verified=0`.

## Public-source check

Checked the current GHOT public page:

`https://ghot.ai/archive/videos/2022-05-06-1`

The page identifies the May 6, 2022 long-form livestream and exposes second-level segmented transcript anchors. The currently retrieved public result visibly includes:

- `13:42` — `那话筒就交给我们七哥，好的下面有请我们今天的主讲人，我们的大明星七哥出场，尊敬的战友们好。`

`13:42` equals `822` seconds, exactly supporting the first tracked start anchor.

The same public page contains a long segmented transcript extending well beyond two hours. In this bounded audit lookup, the two later exact phrases were not independently surfaced by the retrieval result, so this audit does not claim a fresh independent re-observation of their exact seconds.

## Playback qualification

No audiovisual media was decoded or played by this verifier. The current runtime cannot execute `scripts/audit_media.py` or inspect generated media clips/frames.

Therefore even the exactly corroborated 822-second GHOT timestamp remains timeline/source evidence, not a measured playback timing error.

## Audit result

- Livestream/date/topic provenance: **supported**
- Segment 0 GHOT phrase/timestamp: **independently corroborated at 13:42 = 822s**
- Segments 1–2 exact current public timestamp re-observation: **not independently established in this bounded lookup**
- Actual media playback performed: **NO**
- Timing error measured: **NO**
- `playback_verified`: **remains 0 for all rows**
- Qualifying real playback checks: **0**
- Counts toward Pilot-60: **NO**

## Disposition

Retain all three rows as `timestamped_asr_only_unverified_playback`. Do not treat exact transcript/timeline agreement as actual playback verification. Future qualifying audit should use the public media URL or a lawful local copy with `scripts/audit_media.py`, inspect the decoded content, and record independently observed timing error.

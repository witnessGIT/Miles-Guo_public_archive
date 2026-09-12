# Miles-Guo_public_archive Pilot Audit — PILOT-L004

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-L004`  
Case: `PILOT-L004`  
Live ID: `LIVE_20220529_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:35:00Z`

## Segments under audit

`data/live_segments/alignment/LIVE_20220529_001.jsonl` contains three GHOT ASR/time anchors:

1. `LIVE_20220529_001_SEG_000000` — `81.0` sec — `可能真的我们今天谈的疫苗问题太敏感了。`
2. `LIVE_20220529_001_SEG_000001` — `1200.0` sec — `核酸检测，我今天发现一个视频说，核酸用的棉棒有荧光剂。`
3. `LIVE_20220529_001_SEG_000002` — `2900.0` sec — `在漫天笼罩着中共病毒和疫苗的这一时刻，太多的人失去了生命。`

All three use GHOT source `SRC_B437B472`, method `ghot_asr_timestamp_direct`, `alignment_quality = 1.0`, `end_sec = null`, and `playback_verified = 0`.

## Public-source checks

### GHOT identity and ordinal mismatch

Checked:

`https://ghot.ai/archive/videos/2022-05-29-6`

The path/archive ID is `2022-05-29-6`, while the visible source title begins `2022.05.29-2`. This source-side ordinal mismatch is preserved as metadata and is not normalized into canonical identity.

The alignment readiness also explicitly records that an unresolved GWINS candidate was **not** promoted to curated provenance. This audit preserves that decision.

### Anchor 1 — 81 seconds

GHOT exposes `01:21` with the matching vaccine-sensitivity passage. `01:21 = 81` seconds, exactly matching the stored first start anchor.

### Anchor 2 — 1200 seconds

GHOT exposes `20:00` with the matching PCR-test / fluorescent swab passage. `20:00 = 1200` seconds, exactly matching the stored second start anchor.

### Anchor 3 — 2900 seconds

GHOT exposes `48:20` with the matching virus/vaccine/lost-lives passage. `48:20 = 2900` seconds, exactly matching the stored third start anchor despite minor ASR wording/noise differences.

## Playback status

The public GHOT timestamped transcript corroborates all three source positions, but this worker environment did not run `scripts/audit_media.py` and did not independently inspect decoded media content at 81s, 1200s, or 2900s.

Therefore:

- Correct GHOT source/date identity: **supported**
- Source ordinal mismatch: **preserved**
- Unresolved GWINS candidate: **not promoted**
- 81s / 1200s / 2900s public time anchors: **exactly corroborated**
- Actual decoded-media content independently inspected: **NO**
- Playback timing error: **not measured**
- `playback_verified`: **0**
- Qualifying playback checks: **0**
- Counts toward Pilot-60: **NO**

## Disposition

Keep all three rows as `timestamped_asr_unverified_playback`. Do not turn `alignment_quality = 1.0` or exact GHOT transcript timestamps into measured playback accuracy, and do not promote the unresolved GWINS candidate without stronger identity evidence.

# Miles-Guo_public_archive Pilot Audit — PILOT-E007

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-E007`  
Case: `PILOT-E007`  
Live ID: `LIVE_20190530_001`  
Verifier: `agent-20260913T013300Z-gpt56sol`  
Verified at: `2026-09-12T16:36:00Z`

## Segments under audit

Three timestamped ASR anchors are stored in `data/live_segments/2019/LIVE_20190530_001.jsonl`:

- `LIVE_20190530_001_SEG_000000` — expected start `231.0` seconds — `亲爱的兄弟姐妹们，你们好啊。`
- `LIVE_20190530_001_SEG_000001` — expected start `282.0` seconds — `今天啊，战友们谁能回答我，我为什么穿白裤子。`
- `LIVE_20190530_001_SEG_000002` — expected start `1411.0` seconds — `万事败于失秘呀。`

All three rows use GHOT source `SRC_E6BC14DC`, method `ghot_timestamp_direct_asr_only`, and already have `playback_verified = 0`.

## Public-source checks performed

### GHOT

Checked the public archive entry:

`https://ghot.ai/archive/videos/2019-05-30-2`

Observed from indexed public content:

- title: `2019.05.30-2 郭文贵先生和战友们聊天`;
- date: `2019-05-30`;
- duration: `36m 07s`;
- the page exposes second-level transcript anchors and states that timestamp rows can be used to jump to a playback position;
- the public transcript contains the same livestream context and timestamped text around the aligned anchors.

This supports the source time axis and provenance. In the current audit environment, however, the GHOT page itself was not available as a usable interactive playback surface; a direct open attempt returned a cache/fetch failure. Therefore no playback position was independently observed.

### GWINS

Public GWINS indexes expose the matching item `郭文贵2019年5月30日视频 20190530_2 郭文贵先生和战友们聊天`, consistent with the GHOT title/date identity chain. The tracked project source points to the corresponding GWINS item, but the current audit environment did not expose a directly playable public surface from which the three expected timestamps could be measured.

This supports source identity but is not playback verification.

## Audit result

For all three audited anchors:

- Correct livestream/date provenance: **supported**
- Timestamped transcript/source time axis: **supported by GHOT**
- Cross-source title/date consistency with GWINS: **supported**
- Actual playback performed: **NO**
- Observed playback position: **not measured**
- Timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep all three E007 rows as `timestamped_asr_only_unverified_playback`. Do not infer timing accuracy from indexed transcript timestamps alone and do not count this audit toward the Pilot-60 playback threshold.

This is a durable negative audit result for the current environment: the source identity and timestamped transcript are traceable, but real playback verification remains unavailable. A later playback-capable audit may revisit the same three anchors.

# Miles-Guo_public_archive Pilot Audit — PILOT-M009

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M009`  
Case: `PILOT-M009`  
Live ID: `LIVE_20211124_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:06:00Z`

## Segments under audit

The case has three deliberately post-pre-roll GHOT anchors in `data/live_segments/alignment/LIVE_20211124_001.jsonl`:

1. `LIVE_20211124_001_SEG_000000` — `1093.0` sec (`18:13`) — `大家早上好，大家早上好。`
2. `LIVE_20211124_001_SEG_000001` — `1103.0` sec (`18:23`) — `今天是11月24号。`
3. `LIVE_20211124_001_SEG_000002` — `1106.0` sec (`18:26`) — `我们现在是美东时间的早上8点23分...`

All use `SRC_C696919C`, `ghot_public_timeline_direct_post_preroll`, have no asserted `end_sec`, and have `playback_verified = 0`. The source record explicitly warns that noisy/pre-roll material appears before the livestream greeting; no canonical/global offset is asserted.

## Public-source checks

### GHOT

`https://ghot.ai/archive/videos/2021-11-24-1`

The public GHOT timestamped transcript contains noisy/unrelated material before the livestream greeting, then exposes the exact post-pre-roll anchors:

- `18:13` — `大家早上好，大家早上好，`
- `18:23` — `今天是11月24号。`
- `18:26` — `我们现在是美东时间的早上8点23分...`

These equal `1093`, `1103`, and `1106` seconds and exactly reproduce the stored starts. This supports the deliberate post-pre-roll selection while providing no basis to infer a global canonical offset for the entire source.

### GWINS

`https://gwins.org/cn/milesguo/23454.html`

GWINS identifies the same item as `郭文贵2021年11月24日直播 20211124_1`, published `20211124`, and links the same Odysee item `@laxi:4/20211124_1:9` and Rumble item `v59x58r-20211124-1.html`. This independently supports case identity and source provenance.

### Odysee / Rumble

The Odysee item resolves but exposes no observable playback position in the current audit environment. The Rumble page returns HTTP `403 Forbidden`.

## Audit result

- Correct livestream/date identity: **supported**
- Post-pre-roll GHOT anchors: **exactly corroborated**
- Noisy/pre-roll boundary: **confirmed and preserved**
- Global/canonical offset: **NOT inferred**
- Cross-source GHOT/GWINS/Odysee/Rumble identity: **supported**
- Actual media playback performed: **NO**
- Observed playback position / timing error: **not measured**
- `playback_verified`: **0**
- Counts toward Pilot-60 real playback checks: **NO**

## Disposition

Keep all three rows as `timestamped_unverified_playback` and preserve `ghot_public_timeline_direct_post_preroll`. Do not transform the observed pre-roll boundary into a global offset, and do not infer `end_sec`, frame data, or playback timing accuracy.

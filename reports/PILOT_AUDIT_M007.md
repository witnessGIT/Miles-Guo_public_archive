# Miles-Guo_public_archive Pilot Audit — PILOT-M007

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M007`  
Case: `PILOT-M007`  
Live ID: `LIVE_20210902_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T16:58:00Z`

## Segments under audit

The case currently has three GHOT public-timeline anchors in `data/live_segments/alignment/LIVE_20210902_001.jsonl`:

1. `LIVE_20210902_001_SEG_000000` — expected start `0.0` sec — ASR: `真正的战友们好`
2. `LIVE_20210902_001_SEG_000001` — expected start `355.0` sec (`05:55`) — ASR: `共匪下令`
3. `LIVE_20210902_001_SEG_000002` — expected start `446.0` sec (`07:26`) — ASR: `我们明天上午大直播`

All three use `SRC_0796260D`, use `ghot_public_timeline_direct`, have no asserted `end_sec`, and already have `playback_verified = 0`.

## Public-source checks performed

### GHOT

Checked:

`https://ghot.ai/archive/videos/2021-09-02-2`

The public GHOT record identifies the same 2021-09-02 livestream and exposes exact timestamp/text anchors at:

- `00:00` — `哎呀，真正的战友们好。`
- `05:55` — `共匪下令，这回是绝对可以确定的。`
- `07:26` — `我们明天上午大直播啊。`

These convert exactly to `0`, `355`, and `446` seconds and reproduce all three stored starts.

### GETTR

Followed the GHOT-linked public GETTR post:

`https://gettr.com/post/p9xyj1e4d0`

The GETTR page identifies the same 9月2号 livestream/title context. In the current audit environment it does not expose a usable playback position from which the three expected timestamps could be independently measured.

### GWINS

Checked the GHOT-linked GWINS page:

`https://gwins.org/cn/milesguo/23292.html`

GWINS identifies the item as `郭文贵2021年9月2日盖特 20210902_2`, gives publish date `20210902`, and links the same GETTR post `p9xyj1e4d0` and Rumble item `v59l2dh-20210902-2.html`. Its curated summary begins with the same opening content and includes the later `共匪下令` and `明天上午大直播` passages represented by the GHOT anchors.

This independently supports the cross-source identity and text provenance of the selected case.

### Rumble

Attempted:

`https://rumble.com/v59l2dh-20210902-2.html`

The current audit environment received HTTP `403 Forbidden`, so playback could not be performed there.

## Audit result

For all three segments:

- Correct livestream/date provenance: **supported**
- GHOT timestamp/text consistency: **exactly corroborated**
- Cross-source GHOT/GWINS/GETTR identity: **supported**
- Actual media playback performed: **NO**
- Observed playback position: **not measured**
- Playback timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep all three rows as `timestamped_unverified_playback`. Cross-source identity and exact public timestamp agreement are strong provenance evidence but do not substitute for actual playback observation.

Do not infer `end_sec`, FPS/frame values, or zero-second timing error. A playback-capable future audit must independently observe media positions before these segments can count toward Pilot playback thresholds.

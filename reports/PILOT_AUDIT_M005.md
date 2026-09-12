# Miles-Guo_public_archive Pilot Audit — PILOT-M005

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M005`  
Case: `PILOT-M005`  
Live ID: `LIVE_20201120_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T16:50:00Z`

## Segments under audit

The case currently has three GHOT source-backed ASR/timeline anchors in `data/live_segments/2020/LIVE_20201120_001.jsonl`:

1. `LIVE_20201120_001_SEG_000000` — expected start `9763.0` sec (`02:42:43`)
2. `LIVE_20201120_001_SEG_000001` — expected start `9824.0` sec (`02:43:44`)
3. `LIVE_20201120_001_SEG_000002` — expected start `9856.0` sec (`02:44:16`)

All three use `SRC_F71F5626` as ASR/time source, use `ghot_timestamp_direct_asr_only`, have no asserted `end_sec`, and already have `playback_verified = 0`.

## Public-source checks performed

### GHOT archive and selected-clip evidence

Checked:

`https://ghot.ai/archive/videos/2020-11-20-4`

The public GHOT record identifies the same 2020-11-20 livestream and exposes a selected clip titled:

`资本主义和共产主义的对抗已经图穷匕首见了`

with the explicit public range:

`02:42:38–02:44:20` (`1m 42s`).

All three stored anchors fall inside that published clip interval.

### GHOT public timestamped transcript

The same public GHOT record exposes exact timestamp/text anchors including:

- `02:42:43` — passage beginning `主导世界，像过去七十年，还是共产主义来主导世界...`
- `02:43:44` — `走到了一个十字路口，到底是共产主义和资本主义能不能并存...`
- `02:44:16` — passage beginning `现在是...所以这次到了人类必须有个分水岭，到底未来有没有美元，还有没有人民币。`

Converted to seconds these are `9763`, `9824`, and `9856`, exactly matching the stored starts. The third ASR line remains visibly noisy at its beginning, so this audit does not silently clean or replace that source text.

This confirms both the public selected-clip containment and the GHOT transcript/timeline provenance of all three anchors.

### Odysee

Followed the GHOT-linked Odysee item:

`https://odysee.com/@laxi:4/20201120_4:0`

The item resolves, but this audit environment does not expose an observable playback position for independent timing measurement.

### Rumble

Attempted:

`https://rumble.com/v58wjt8-20201120-4.html`

The current environment received HTTP `403 Forbidden`.

### GWINS

Attempted:

`https://gwins.org/cn/milesguo/21133.html`

The current audit fetch timed out and therefore was not used as playback evidence.

## Audit result

For all three anchors:

- Correct livestream/date provenance: **supported by GHOT public metadata**
- Public selected-clip containment: **supported**
- Public timestamp/text consistency: **exactly corroborated**
- Stored start seconds vs GHOT public timestamp text: **exact match**
- Actual media playback performed: **NO**
- Observed playback position: **not measured**
- Playback timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep all three rows as `timestamped_asr_only_unverified_playback`. The selected-clip interval and exact public timeline are strong provenance evidence but are not substitutes for real media playback.

Do not infer `end_sec`, do not assign a zero-second playback error, and do not count these anchors toward the 60 real playback checks until a playback-capable audit independently observes the corresponding media positions.

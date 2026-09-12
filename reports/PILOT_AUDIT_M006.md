# Miles-Guo_public_archive Pilot Audit — PILOT-M006

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M006`  
Case: `PILOT-M006`  
Live ID: `LIVE_20210612_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T16:54:00Z`

## Segments under audit

The case currently has three GHOT source-backed ASR/timeline anchors in `data/live_segments/2021/LIVE_20210612_001.jsonl`:

1. `LIVE_20210612_001_SEG_000000` — expected start `606.0` sec (`10:06`) — ASR references `这种事情现在越来越多未来会无处不在...`
2. `LIVE_20210612_001_SEG_000001` — expected start `3501.0` sec (`58:21`) — ASR: `爆料革命，新中国联邦和战友，这三个词是我们的神。`
3. `LIVE_20210612_001_SEG_000002` — expected start `3776.0` sec (`01:02:56`) — ASR begins `法治社会，战友，爆料革命，新中国联邦...`

All three use `SRC_398C51AD` as ASR/time source, use `ghot_timestamp_direct_asr_only`, have no asserted `end_sec`, and already have `playback_verified = 0`.

## Public-source checks performed

### GHOT archive and public timestamped transcript

Checked:

`https://ghot.ai/archive/videos/2021-06-12-1`

The public GHOT record identifies the same 2021-06-12 livestream and exposes exact timestamp/text anchors at:

- `10:06` — passage beginning `这种事情现在越来越多未来会无处不在...`
- `58:21` — `爆料革命，新中国联邦和战友，这三个词是我们的神。`
- `01:02:56` — passage beginning `法治社会，战友，爆料革命，新中国联邦...`

Converted to seconds these are exactly `606`, `3501`, and `3776`, matching the stored `start_sec` values.

This strongly corroborates the stored GHOT public timeline and ASR provenance, but it does not independently establish media playback accuracy.

### Odysee

Followed the GHOT-linked Odysee item:

`https://odysee.com/@laxi:4/20210612_1:9`

The item resolves, but this audit environment does not expose an observable playback position for independent timing measurement.

### Rumble

Attempted:

`https://rumble.com/v59epot-20210612-1.html`

The current environment received HTTP `403 Forbidden`.

### GWINS

Attempted:

`https://gwins.org/cn/milesguo/23055.html`

The current fetch failed with a Unicode decoding error and therefore was not used as playback evidence.

## Audit result

For all three segments:

- Correct livestream/date provenance: **supported by GHOT public metadata**
- Public timestamp/text consistency: **exactly corroborated**
- Stored start seconds vs GHOT public timestamp text: **exact match**
- Actual media playback performed: **NO**
- Observed playback position: **not measured**
- Playback timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep all three rows as `timestamped_asr_only_unverified_playback`. Do not infer `end_sec`, FPS/frame values, or a zero-second playback error from public timestamp text alone.

A future playback-capable worker or aggregate `P9-AUDIT-60` review must observe actual media positions before these segments can count toward Pilot playback-accuracy thresholds.

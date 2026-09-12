# Miles-Guo_public_archive Pilot Audit — PILOT-M003

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M003`  
Case: `PILOT-M003`  
Live ID: `LIVE_20200606_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T16:42:00Z`

## Segments under audit

The case currently has three GHOT public-timeline anchors in `data/live_segments/alignment/LIVE_20200606_001.jsonl`:

1. `LIVE_20200606_001_SEG_000000` — expected start `177.0` sec — ASR: `亲爱的兄弟姐妹好啊。`
2. `LIVE_20200606_001_SEG_000001` — expected start `362.0` sec — ASR: `昨天一整天工作最起码是16个小时吧。`
3. `LIVE_20200606_001_SEG_000002` — expected start `4933.0` sec — ASR: `GNews全面的开始，做好下一期融资私募还有整个的升级的准备。`

All three use `SRC_2D9CF885` as ASR/time source, use `ghot_public_timeline_direct`, have no asserted `end_sec`, and already have `playback_verified = 0`.

## Public-source checks performed

### GHOT archive and public timestamped transcript

Checked:

`https://ghot.ai/archive/videos/2020-06-06-1`

The public GHOT record identifies the same 2020-06-06 livestream and its indexed timestamped transcript exposes the following exact anchors:

- `02:57` — `亲爱的兄弟姐妹好啊。`
- `06:02` — `昨天一整天工作最起码是16个小时吧。`
- `01:22:13` — `GNews全面的开始，做好下一期融资私募还有整个的升级的准备。`

Converted to seconds:

- `02:57` = `177` seconds;
- `06:02` = `362` seconds;
- `01:22:13` = `4933` seconds.

These values exactly match the three tracked `start_sec` anchors and therefore strongly corroborate the stored GHOT public timeline and ASR provenance.

The current interactive GHOT page also exposes outbound Odysee, Rumble and GWINS links, but the dynamic transcript/video surface itself is currently unavailable in the page rendering used by this audit environment.

### Odysee

Followed the GHOT-linked public Odysee item:

`https://odysee.com/@laxi:4/20200606:dd`

The item resolves as `20200606`, but the current audit environment did not expose an observable media playback position from which the expected 177s, 362s, and 4933s positions could be independently checked.

### Rumble

Attempted the GHOT-linked Rumble URL:

`https://rumble.com/v58jjad-20200606.html`

The current audit environment received HTTP `403 Forbidden`, so playback could not be performed there.

### GWINS

Attempted the GHOT-linked GWINS page:

`https://gwins.org/cn/milesguo/2675.html`

The current audit fetch failed with a Unicode decoding error, so that page was not used as playback or curated-text evidence in this audit.

## Audit result

For all three segments:

- Correct livestream/date provenance: **supported by GHOT public metadata**
- GHOT timeline/text anchor consistency: **exactly corroborated**
- Stored start seconds vs public GHOT timestamp text: **exact match**
- Actual media playback performed: **NO**
- Observed playback position: **not measured**
- Playback timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep all three segments as `timestamped_unverified_playback`. The exact public transcript/timeline match must not be promoted into a playback pass. Do not invent `end_sec`, FPS, frame numbers, or a zero-second playback error.

This audit provides durable evidence that the stored GHOT starts are reproduced exactly by GHOT's public timestamped transcript. A future playback-capable worker or the aggregate `P9-AUDIT-60` stage must still perform actual media playback before these segments can count toward the Pilot playback-accuracy thresholds.

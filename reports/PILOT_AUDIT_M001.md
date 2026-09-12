# Miles-Guo_public_archive Pilot Audit — PILOT-M001

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M001`  
Case: `PILOT-M001`  
Live ID: `LIVE_20200323_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T16:35:00Z`

## Segments under audit

The case currently has three direct GHOT public-timeline anchors in `data/live_segments/alignment/LIVE_20200323_001.jsonl`:

1. `LIVE_20200323_001_SEG_000000` — expected start `646.0` sec — ASR: `所以说，兄弟姐妹们。`
2. `LIVE_20200323_001_SEG_000001` — expected start `1254.0` sec — ASR references `华人，储备大量的口罩手套`
3. `LIVE_20200323_001_SEG_000002` — expected start `5549.0` sec — ASR references `全人类处在巨大挑战的时候...活着是你现在唯一想要做的`

All three use `SRC_8E68FA28` as ASR/time source, `ghot_public_timeline_direct` as the timing method, have no asserted `end_sec`, and already have `playback_verified = 0`.

## Public-source checks performed

### GHOT

Checked:

`https://ghot.ai/archive/videos/2020-03-23-1`

Observed from the public page:

- title: `2020.03.23 郭文贵先生直播警示好好活着，一年后再想着上班赚钱 [720p]`;
- date: `2020-03-23`;
- transcript excerpts include the phrase `所以说，兄弟姐妹们` represented by the first alignment anchor and surrounding same-program transcript text;
- the page exposes outbound Odysee, Rumble and GWINS links;
- the interactive transcript/video area currently reports the entry/transcript as unavailable, so no exact playback position could be observed in this environment.

This supports source identity and ASR provenance, but does not independently verify the 646/1254/5549-second positions.

### Odysee

Followed the GHOT-linked public Odysee item:

`https://odysee.com/@laxi:4/20200323:d`

The public item resolves as `20200323`, but the current audit environment did not expose an observable playback position from which the three expected timestamps could be checked.

### Rumble

Attempted the GHOT-linked Rumble URL:

`https://rumble.com/v58722t-20200323.html`

The current audit environment received HTTP `403 Forbidden`, so playback could not be performed there.

### GWINS

Attempted the GHOT-linked GWINS page:

`https://gwins.org/cn/milesguo/1131.html`

The current audit fetch failed with a Unicode decoding error, so that page was not used as playback or curated-text evidence in this audit.

## Audit result

For all three segments:

- Correct livestream/date provenance: **supported by GHOT public metadata**
- ASR/source consistency: **supported by GHOT transcript excerpt where visible**
- Actual playback performed: **NO**
- Observed playback position: **not measured**
- Timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Preserve all three rows as `timestamped_unverified_playback`. Do not infer timing accuracy from the GHOT public timeline alone and do not manufacture `end_sec` values.

This task records a durable negative playback result for the current environment. A future playback-capable worker or the aggregate `P9-AUDIT-60` gap-cleanup stage may revisit these anchors using Odysee/Rumble or another independently verified playable source and record observed positions and timing errors only after actual playback.

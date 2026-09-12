# Miles-Guo_public_archive Pilot Audit — PILOT-L003

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-L003`  
Case: `PILOT-L003`  
Live ID: `LIVE_20220511_001`

## Segment under audit

- Segment: `LIVE_20220511_001_SEG_000000`
- Expected start: `0.0` seconds
- Expected end: `18.0` seconds
- Curated source: `SRC_CAEED6A2`
- ASR/time source: `SRC_9D160914`
- Alignment method: `ghot_fuzzy_char_v1`
- Alignment quality: `0.5106382978723404`
- Existing review state: `needs_review`

The aligned row is preserved in `data/live_segments/alignment/pilot_alignment_b001.jsonl`. It already has `playback_verified = 0`; this audit does not change that value.

## Public-source checks performed

### GHOT

Checked:

`https://ghot.ai/archive/videos/2022-05-11-2`

Observed from the public page:

- title: `2022.05.11-2 七哥与战友们连线直播_ X264`;
- date: `2022-05-11`;
- the opening transcript corresponds to the same opening content represented by the aligned segment;
- the page exposes outbound GETTR, Rumble and GWINS links;
- the page currently reports that the full transcript is not loadable in the interactive transcript area, while a transcript excerpt remains visible.

This supports source identity and text provenance, but it is not a playback-position verification.

### GETTR

Checked the public GETTR streaming page linked by GHOT:

`https://gettr.com/streaming/p19cmxu5e7b`

The public page identifies the item as `七哥与战友们连线直播`. In the current audit environment, the page did not expose a usable playback surface from which the expected `0.0` second position could be independently observed.

### Rumble

Attempted the GHOT-linked Rumble URL:

`https://rumble.com/v5af5v1-20220511-2.html`

The current audit environment received HTTP `403 Forbidden`, so playback could not be performed there.

## Audit result

- Correct livestream/date provenance: **supported by public source metadata**
- Opening text/source consistency: **supported by GHOT transcript excerpt**
- Cross-source identity: **supported at metadata/link level**
- Actual playback performed: **NO**
- Observed playback position: **not measured**
- Timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep `LIVE_20220511_001_SEG_000000` in `needs_review`. Do not convert this segment to a playback pass and do not infer timing accuracy from the transcript URL or metadata alone.

A future worker with a playback-capable browser/runtime may re-audit this segment using the public GETTR/Rumble source (or another source that resolves to the same media), record the actually observed position, and only then count it toward the Pilot playback thresholds.

# Miles-Guo_public_archive Pilot Audit — PILOT-L007

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-L007`  
Case: `PILOT-L007`  
Live ID: `LIVE_20230310_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T16:32:00Z`

## Segments under audit

### Segment 1

- Segment: `LIVE_20230310_001_SEG_000000`
- Expected start: `0.0` seconds
- Expected end: `17.0` seconds
- Curated source: `SRC_DD5243CF`
- ASR/time source: `SRC_FA36BAD8`
- Alignment method: `ghot_fuzzy_char_v1`
- Alignment quality: `0.7441860465116279`
- Existing review state: `aligned_unverified_playback`

### Segment 2

- Segment: `LIVE_20230310_001_SEG_000001`
- Expected start: `17.0` seconds
- Expected end: `44.0` seconds
- Curated source: `SRC_DD5243CF`
- ASR/time source: `SRC_FA36BAD8`
- Alignment method: `ghot_fuzzy_char_v1`
- Alignment quality: `0.8`
- Existing review state: `aligned_unverified_playback`

The aligned rows are preserved in `data/live_segments/alignment/pilot_alignment_b001.jsonl`. Both already have `playback_verified = 0`; this audit does not change that value.

## Public-source checks performed

### GHOT

Checked:

`https://ghot.ai/archive/videos/2023-03-10-1`

Observed from the public page:

- title identifies the 2023-03-10 livestream entry;
- date is `2023-03-10`;
- archive identifier is `2023-03-10-1`;
- the page exposes outbound GETTR, Rumble and GWINS links;
- the current page reports that the video entry/transcript is not loadable in the interactive area, so no playback position could be independently observed there.

This supports source identity/provenance but is not a playback-position verification.

### GWINS

Checked:

`https://gwins.org/cn/milesguo/24261.html`

Observed from the public page:

- page title is `郭文贵2023年3月10日盖特 20230310_1`;
- published date is `20230310`;
- the page links the same GETTR post `p2b18ew21e7` and Rumble URL `v5b2sws-20230310-1.html`;
- the curated summary begins with `尊敬的战友们好，3月10号，你们健身了吗？` and then discusses the `共产党的两会` / `习近平` / `习家军` passage represented by the two aligned segments.

This supports curated-text provenance and the GHOT/GWINS/platform identity chain, but it does not expose a playback position suitable for timing measurement.

### GETTR

Checked the public GETTR post linked by both GHOT and GWINS:

`https://gettr.com/post/p2b18ew21e7`

The public page identifies the same 2023-03-10 item and matching post text/title context. In the current audit environment it did not expose a usable playback surface from which `0.0` seconds or `17.0` seconds could be independently observed.

### Rumble

Attempted:

`https://rumble.com/v5b2sws-20230310-1.html`

The current audit environment received HTTP `403 Forbidden`, so playback could not be performed there.

## Audit result

For both audited segments:

- Correct livestream/date provenance: **supported by public GHOT/GWINS/GETTR metadata**
- Curated opening text/source consistency: **supported by GWINS**
- Cross-source identity: **supported by matching GHOT/GWINS GETTR and Rumble links**
- Actual playback performed: **NO**
- Observed playback position: **not measured**
- Timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep both `LIVE_20230310_001_SEG_000000` and `LIVE_20230310_001_SEG_000001` as `aligned_unverified_playback`. Do not convert either segment to a playback pass and do not infer timing accuracy from transcript alignment, metadata, or source-link consistency alone.

This task establishes a durable negative audit result for the current environment: provenance and identity are supported, but timing remains unverified. A later playback-capable audit or the aggregate `P9-AUDIT-60` gap-cleanup stage may revisit these segments using the same public GETTR/Rumble identity chain or another independently verified playable mirror.

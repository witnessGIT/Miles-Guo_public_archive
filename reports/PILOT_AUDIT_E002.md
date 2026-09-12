# Miles-Guo_public_archive Pilot Audit — PILOT-E002

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-E002`  
Case: `PILOT-E002`  
Live ID: `LIVE_20170610_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:12:00Z`

## Segments under audit

The case currently has three monotonic transcript/time anchors in `data/live_segments/alignment/LIVE_20170610_001.jsonl`. Curated wording is supplied by `SRC_2A16C7E2`, a public secondary human transcript copy explicitly classified as S4. It is only a text witness and does not replace GHOT/GWINS provenance.

1. `LIVE_20170610_001_SEG_000000` — stored start `230.0` sec — curated text begins with the HNA announcement / response passage.
2. `LIVE_20170610_001_SEG_000001` — stored start `353.0` sec — curated text covers the HNA announcement, June 16 Mingjing livestream, new material, and solemn promise passage.
3. `LIVE_20170610_001_SEG_000002` — stored start `381.0` sec — curated text covers the second point, global press conference/system, sudden livestream, global simulcast, and flexible timing passage.

All three have `end_sec = null`, `playback_verified = 0`, and review state `aligned_unverified_playback_secondary_text`.

## Provenance discipline

`SRC_2A16C7E2` is stored separately as `source_site = other`, role `curated_transcript`, provenance level `S4`, with an explicit warning that it is a secondary citation/repost. This audit keeps it as a text witness only and does not promote it to an original publication or primary timing source.

The timing/ASR source remains GHOT `SRC_F384D32D`.

## Public-source checks performed

### GHOT

Checked:

`https://ghot.ai/archive/videos/2017-06-10-1`

The public record identifies:

- title: `2017.06.10-1 6月10日郭文贵有关海南航空的公告的回复 [480p]`;
- date: `2017-06-10`;
- duration: `31m 03s`;
- second-level timestamped transcript.

### Anchor 1 — 230 seconds

GHOT exposes:

- `03:50` — `刚才就是看到了海航发出的公告。`
- `04:00` — the following passage states that the announcement says the allegations are untrue, many media asked questions, and a response is necessary.

`03:50 = 230` seconds, so the stored first anchor is directly supported as the beginning of the matching source context.

### Anchor 2 — 353 seconds

GHOT exposes the relevant sequence around the stored anchor:

- `05:53` — `是吧。`
- `05:57` — `那么鉴于海航已经公告说我说的不是事实。`
- `06:03` — `我在这里向所有的推友们保证：十六号的明镜三期直播。`
- `06:12` / `06:14` — `一定有新料。`
- `06:16` — `我向大家庄严的承诺。`

`05:53 = 353` seconds. Therefore 353 seconds is a valid monotonic context anchor leading into the curated passage, but it is **not** the exact start of the substantive sentence `鉴于海航已经公告...`, which begins several seconds later at approximately `05:57`.

This distinction is preserved rather than forcing an exact phrase-start claim.

### Anchor 3 — 381 seconds

GHOT exposes:

- `06:21` — `第二个。`
- `06:22` — `全球发布会。`
- the following seconds discuss testing the system, beginning livestreams unexpectedly, global simulcast, and flexible timing.

`06:21 = 381` seconds, so the stored third anchor is directly supported as the section boundary for the corresponding curated passage.

## Playback result

The public GHOT page states that its timestamp links are navigable to playback positions, but the current audit environment does not provide an independently observable media-player clock from which the 230s, 353s, or 381s positions can be measured as actual playback observations.

Accordingly:

- Correct livestream/date provenance: **supported**
- GHOT transcript/time-axis provenance: **supported**
- Anchor 1 at 230s: **source context directly corroborated**
- Anchor 2 at 353s: **monotonic context anchor corroborated; exact substantive phrase starts later**
- Anchor 3 at 381s: **section boundary directly corroborated**
- Secondary curated transcript provenance: **preserved as S4 only**
- Actual media playback performed: **NO**
- Observed playback position: **not measured**
- Playback timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep all three rows as `aligned_unverified_playback_secondary_text`. Do not convert transcript/timeline agreement into a playback pass. In particular, do not rewrite the 353-second anchor as an exact phrase start.

Do not infer `end_sec`, FPS/frame values, or zero-second playback error. A future playback-capable audit must independently observe the media positions before these segments can count toward Pilot playback-accuracy thresholds.

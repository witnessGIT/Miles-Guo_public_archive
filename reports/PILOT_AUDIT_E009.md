# Miles-Guo_public_archive Pilot Audit — PILOT-E009

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-E009`  
Case: `PILOT-E009`  
Live ID: `LIVE_20191029_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:29:00Z`

## Segments under audit

`data/live_segments/alignment/LIVE_20191029_001.jsonl` contains three monotonic GHOT anchors matched to GWINS title phrases:

1. `LIVE_20191029_001_SEG_000000` — `860.0` sec — curated/ASR phrase `华为就是PLA`
2. `LIVE_20191029_001_SEG_000001` — `1110.0` sec — curated phrase `区块链最核心的问题是政治、军事情报和金融`
3. `LIVE_20191029_001_SEG_000002` — `3063.0` sec — curated topic `郭宝胜写信给法院，惹怒法官并被驳回`

All three preserve `end_sec = null`, `alignment_quality = null`, and `playback_verified = 0` with method `ghot_anchor_title_phrase_v1`.

## Public-source checks

### GHOT record

Checked:

`https://ghot.ai/archive/videos/2019-10-29-1`

The public title contains all three selected topic phrases and the timestamped transcript provides exact source anchors.

### Anchor 1 — 860 seconds

GHOT exposes:

- `14:05` — context about data strategy / 5G / Huawei and the PLA;
- `14:20` — `华为就是PLA，这话是我第一个人说的...`;
- `14:38` — the same `华为就是PLA` assertion appears again in the following discussion.

`14:20 = 860` seconds, exactly matching the stored first start anchor. The later repetition at 14:38 does not invalidate the earlier exact occurrence.

### Anchor 2 — 1110 seconds

GHOT exposes:

- `18:30` — `...区块链我跟妳谈壹件事情，区块链最核心的问题。`
- `18:38` — `它当然是政治的，然后是军事，情报，然后是金融...`

`18:30 = 1110` seconds, exactly matching the stored second start anchor and leading directly into the full curated title phrase.

### Anchor 3 — 3063 seconds

GHOT exposes:

- `50:50` — transition into the 郭宝胜 topic;
- `51:03` — `郭宝胜发了一个东西啊，说这个头两天要开庭的...`;
- `51:23` onward — discussion of the lawyer and the judge's response.

`51:03 = 3063` seconds, exactly matching the stored third anchor for the source-title topic concerning 郭宝胜 and the court/judge response.

## Playback status

The GHOT timestamped transcript is publicly locatable, but this worker environment did not run `scripts/audit_media.py` and did not independently inspect decoded media content at 860s, 1110s, or 3063s.

Therefore transcript/time-axis agreement is not converted into measured playback accuracy.

## Audit result

- Correct livestream/date identity: **supported**
- 860s GHOT anchor: **exactly corroborated**
- 1110s GHOT anchor: **exactly corroborated**
- 3063s GHOT anchor: **exactly corroborated**
- Source-title topic matching: **supported**
- Actual decoded media content independently inspected: **NO**
- Playback timing error: **not measured**
- `playback_verified`: **0**
- Qualifying playback checks: **0**
- Counts toward Pilot-60: **NO**

## Disposition

Keep all three rows as `aligned_unverified_playback`. The three `start_sec` values have strong public GHOT timeline provenance, but the Pilot playback gate still requires actual decoded-media/content inspection and measured observed positions.

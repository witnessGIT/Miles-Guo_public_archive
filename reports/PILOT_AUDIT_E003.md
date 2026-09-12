# Miles-Guo_public_archive Pilot Audit — PILOT-E003

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-E003`  
Case: `PILOT-E003`  
Live ID: `LIVE_20171004_001`  
Verifier: `agent-20260912T163100Z-gpt56sol-restart`  
Verified at: `2026-09-12T16:45:00Z`

## Segments under audit

The aligned rows are:

- `LIVE_20171004_001_SEG_000000` — expected start `30.0s`; GHOT phrase `在华盛顿向大家报平安。`
- `LIVE_20171004_001_SEG_000001` — expected start `34.0s`; GHOT phrase `由于我一会儿我要马上开会，所以说实在是太紧了。`
- `LIVE_20171004_001_SEG_000002` — expected start `40.0s`; GHOT phrase `会场的人马上就到了，所以说我只能是简单的给大家报一下平安。`

All three use curated/source text `SRC_EF7F8DC1`, ASR/time source `SRC_B9AC44D5`, alignment method `ghot_anchor_phrase_v1`, and currently have `playback_verified = 0`.

## Public-source checks performed

### GHOT

Checked:

`https://ghot.ai/archive/videos/2017-10-04-1`

Observed from the public page:

- title identifies the 2017-10-04 Washington livestream;
- date is `2017-10-04`;
- duration is shown as `26m 27s`;
- public segmented transcript exposes second-level anchors;
- the page shows the same three phrases at `00:30`, `00:34`, and `00:40`, respectively.

This independently supports the stored monotonic transcript/time-axis anchors. It does not constitute actual playback verification.

### GWINS / tracked provenance

Repository source data links `LIVE_20171004_001` to GWINS page `https://www.gwins.org/cn/milesguo/695.html` and records matching date/title context plus external media mirrors. The curated/source-text wording is consistent with the GHOT opening transcript.

## Audit result

For all three rows:

- Livestream/date identity: **supported**
- Source-text/ASR correspondence: **supported**
- GHOT start anchors: **supported by public transcript**
- Actual video playback performed: **NO**
- Observed playback position: **not measured**
- Timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Retain the three stored start anchors and keep the rows `aligned_unverified_playback`. Do not convert transcript timestamp agreement into a playback pass. This audit contributes **0 qualifying playback checks** to Pilot-60; a playback-capable follow-up is still required to measure timing error against the actual media stream.

# Miles-Guo_public_archive Pilot Audit — PILOT-E001

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-E001`  
Case: `PILOT-E001`  
Live ID: `LIVE_20170523_001`  
Verifier: `agent-20260912T163100Z-gpt56sol-restart`  
Verified at: `2026-09-12T16:40:00Z`

## Segments under audit

### Segment 1

- Segment: `LIVE_20170523_001_SEG_000000`
- Expected start: `6.0` seconds
- Expected end: `null`
- Curated source: `SRC_7E0126EB`
- ASR/time source: `SRC_439390C3`
- Alignment method: `ghot_anchor_phrase_v1`
- Existing review state: `aligned_unverified_playback`

### Segment 2

- Segment: `LIVE_20170523_001_SEG_000001`
- Expected start: `16.0` seconds
- Expected end: `null`
- Curated source: `SRC_7E0126EB`
- ASR/time source: `SRC_439390C3`
- Alignment method: `ghot_anchor_phrase_v1`
- Existing review state: `aligned_unverified_playback`

### Segment 3

- Segment: `LIVE_20170523_001_SEG_000002`
- Expected start: `24.0` seconds
- Expected end: `null`
- Curated source: `SRC_7E0126EB`
- ASR/time source: `SRC_439390C3`
- Alignment method: `ghot_anchor_phrase_v1`
- Existing review state: `aligned_unverified_playback`

## Public-source checks performed

### GHOT

Checked:

`https://ghot.ai/archive/videos/2017-05-23-1`

Observed from the public page:

- title identifies the 2017-05-23 report-safety livestream;
- date is `2017-05-23`;
- duration is shown as `16m 27s`;
- the public segmented transcript exposes second-level anchors;
- the transcript includes `00:06 尊敬的崇伟们，大家好`, `00:16 由于这个时间我们的直播视频`, and `00:24 简单的我先说几个问题`, which support the three stored start anchors.

This independently supports the public ASR/time-axis provenance and monotonic start anchors. It is not an actual playback-position verification.

### GWINS

Checked the public GWINS index/detail evidence for the same item:

`https://www.gwins.org/cn/milesguo/565.html`

The public GWINS archive identifies `郭文贵2017年5月23日视频 20170523`; its opening text corresponds to the stored curated/source-text phrases about the May 23 report-safety livestream, the roughly fifteen-minute duration statement, and introducing several topics.

Tracked repository provenance also records outbound YouTube and Rumble media URLs for this same GWINS record. Those links establish source-chain candidates but were not treated as playback evidence in this audit.

## Audit result

For all three segments:

- Correct livestream/date provenance: **supported**
- Curated/source-text consistency: **supported by GWINS**
- GHOT ASR/time-axis consistency: **supported by public GHOT transcript anchors**
- Cross-source identity: **supported by tracked GHOT-to-GWINS relationship and matching date/title/text context**
- Actual video playback performed: **NO**
- Observed playback position: **not measured**
- Timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep `LIVE_20170523_001_SEG_000000` through `_SEG_000002` as `aligned_unverified_playback`. The public transcript evidence is strong enough to retain the stored start anchors, but transcript timestamps must not be promoted to actual playback verification.

This audit contributes source/provenance validation but contributes **0 qualifying real playback checks** toward the Pilot-60 gate. A playback-capable later audit must independently observe the video position and measure timing error before these rows can count toward the accuracy thresholds.

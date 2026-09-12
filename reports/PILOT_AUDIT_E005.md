# Miles-Guo_public_archive Pilot Audit — PILOT-E005

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-E005`  
Case: `PILOT-E005`  
Live ID: `LIVE_20180616_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:23:00Z`

## Segments under audit

`data/live_segments/alignment/LIVE_20180616_001.jsonl` contains three direct curated-source timestamp anchors:

1. `LIVE_20180616_001_SEG_000000` — `0.0` sec — `网络上出现了新兴的侠客联盟帮助文贵先生，让文贵先生非常感动`
2. `LIVE_20180616_001_SEG_000001` — `119.0` sec — `当今黑客是防国家机器和盗国贼、独裁集团对好人的迫害`
3. `LIVE_20180616_001_SEG_000002` — `295.0` sec — `关注郭先生的太多，郭先生要录视频报平安，这是责任`

All three use `SRC_9229E0C6` as curated/time source, method `curated_timestamp_direct`, `alignment_quality = 1.0`, `end_sec = null`, and `playback_verified = 0`.

## Public-source checks

### GWINS

Checked:

`https://gwins.org/cn/milesguo/21799.html`

GWINS identifies the same record as `郭文贵2018年6月16日直播 20180616_1` and publishes direct source-side timestamp headings:

- `00:00` — network侠客联盟 / helping Mr. Guo / being moved;
- `1:59` — hackers defending good people from state machinery, kleptocrats and dictatorships;
- `4:55` — many people are concerned about Mr. Guo, so he records video to report safety as a responsibility.

These convert exactly to `0`, `119`, and `295` seconds and reproduce all three stored start anchors.

GWINS also exposes public media links for the record, including YouTube `https://youtu.be/ySNFfgMbjd4` and Rumble `https://rumble.com/v578glm-20180616-1.html`.

### Timing-source discipline

The alignment readiness explicitly states that no GHOT timing source was asserted for this case. This audit preserves that provenance: the locators are direct GWINS curated timestamps, not GHOT-derived timestamps.

### Playback status

The current audit environment can verify the public GWINS timestamp/text record and media URLs but cannot run the repository's new `scripts/audit_media.py` / ffmpeg workflow or independently inspect a decoded media clip at 0s, 119s and 295s.

Therefore the existence of public media links does not become a playback pass.

## Audit result

- Correct livestream/date identity: **supported**
- GWINS direct timestamp/text anchors: **exactly corroborated**
- Stored starts 0/119/295 sec: **exact match to source-side timestamp headings**
- GHOT timing source asserted: **NO**
- Public media links available: **YES**
- Actual decoded/media playback content independently inspected: **NO**
- Playback timing error: **not measured**
- `playback_verified`: **0**
- Qualifying playback checks: **0**
- Counts toward Pilot-60: **NO**

## Disposition

Keep all three rows as `timestamped_unverified_playback`. Direct curated timestamps are strong locator evidence but do not satisfy the Pilot real-playback gate.

A playback-capable worker should use the public YouTube or Rumble media with `scripts/audit_media.py`, inspect the generated clip/frame around each expected position, and record the observed content position/timing error before these segments are counted toward Pilot-60.

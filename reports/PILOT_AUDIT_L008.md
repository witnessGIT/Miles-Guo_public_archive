# Miles-Guo_public_archive Pilot Audit — PILOT-L008

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-L008`  
Case: `PILOT-L008`  
Live ID: `LIVE_20230312_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:42:00Z`

## Segments under audit

Legacy P7 alignment preserved two direct curated-timestamp segments for `LIVE_20230312_001`:

1. `LIVE_20230312_001_SEG_000000`
   - curated text begins `Tia（小柯基）：绝对的，不仅是反共而是要灭共！`
   - start `0.0` sec
   - end `158.0` sec
   - method `curated_timestamp_direct`
   - source/time `SRC_471B40E7`

2. `LIVE_20230312_001_SEG_000001`
   - curated text begins `GREENE：雷德菲尔德博士，你是否同意安德森博士当时的评估？`
   - start `158.0` sec
   - end `341.0` sec
   - method `curated_timestamp_direct`
   - source/time `SRC_471B40E7`

Both have `alignment_quality = 1.0` and `playback_verified = 0`.

## Public-source checks

### GWINS identity

Checked:

`https://www.gwins.org/cn/milesguo/24266.html`

GWINS identifies the record as `郭文贵2023年3月12日直播 20230312_1 美国房倒银塌和俄乌战争及灭共的关系`, published `20230312`, and exposes the same public media links preserved by the source record:

- GETTR: `https://gettr.com/streaming/p2b7kcm569c`
- Rumble: `https://rumble.com/v5b2z4t-20230312-1.html`

A neighboring same-day `20230312_2` record exists, so date alone is not used as identity evidence.

### Segment 1 boundary — 0 to 158 seconds

The public GWINS transcript explicitly begins:

- `00:00:00 视频一：03/03/2023 Tia采访建筑商Monica Kennedy`

and immediately contains the aligned Tia quotation.

The next explicit video boundary is:

- `00:02:38 视频二：03/08/2023 联邦病毒溯源听证会`

`00:02:38 = 158` seconds. Therefore the stored interval `0–158s` exactly matches the public curated timeline range for Video 1.

### Segment 2 boundary — 158 to 341 seconds

At `00:02:38`, GWINS begins Video 2 with:

`Mr·GREENE：雷德菲尔德博士，你是否同意安德森博士当时的评估，即这种病毒看起来确实是人工合成的？`

The next explicit boundary is:

- `00:05:41 视频三：03/0/2023 联邦病毒溯源听证会`

`00:05:41 = 341` seconds. Therefore the stored interval `158–341s` exactly matches the public curated timeline range for Video 2.

## Playback status

The source-side timeline boundaries are explicit and exact, and public GETTR/Rumble media URLs are known. However, this worker environment did not execute `scripts/audit_media.py` and did not independently inspect decoded media content at the expected positions.

Accordingly:

- Correct case/date identity: **supported**
- Same-day ambiguity: **preserved**
- Segment 1 public timeline interval `0–158s`: **exactly corroborated**
- Segment 2 public timeline interval `158–341s`: **exactly corroborated**
- Public media URLs available: **YES**
- Actual decoded-media content independently inspected: **NO**
- Playback timing error: **not measured**
- `playback_verified`: **0**
- Qualifying playback checks: **0**
- Counts toward Pilot-60: **NO**

## Disposition

Keep both segments as `timestamped_unverified_playback`. The explicit GWINS HH:MM:SS boundaries establish strong curated locator provenance but do not satisfy the real-playback Pilot gate.

A playback-capable worker should run the repository media-audit helper against a public GETTR/Rumble source, inspect the decoded clips around 0s, 158s and the 341s transition, and record observed content positions/timing errors before these segments count toward Pilot-60.

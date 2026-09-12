# Miles-Guo_public_archive Pilot Audit — PILOT-L009

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-L009`  
Case: `PILOT-L009`  
Live ID: `LIVE_20230314_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:47:00Z`

## Segments under audit

The per-live migrated alignment file contains two source-backed fuzzy-aligned segments:

1. `LIVE_20230314_001_SEG_000000`
   - curated: `尊敬的战友们好，你们健身了吗？`
   - GHOT ASR: `尊敬的战友们好,你们坚持了吗?`
   - start `0.0` sec
   - end `30.0` sec
   - alignment quality `0.8461538461538461`

2. `LIVE_20230314_001_SEG_000001`
   - curated: `现在我这个理发成政治事件了。很多投资人说，Miles，你不能理发！`
   - GHOT ASR: `现在我这个理化成政治事件了，咱们呢，很多投资人说，在这儿看，说。哎呀，Miles你不能理吧！`
   - start `30.0` sec
   - end `50.0` sec
   - alignment quality `0.7941176470588235`

Both use GWINS curated source `SRC_A202D59C`, GHOT ASR/time source `SRC_FCE222EC`, method `ghot_fuzzy_char_v1`, and `playback_verified = 0`.

## Public-source checks

### GHOT

Checked:

`https://ghot.ai/archive/videos/2023-03-14-1`

GHOT identifies the same 2023-03-14 record and exposes the following public timestamped ASR:

- `00:00` — `尊敬的战友们好,你们坚持了吗?`
- `00:30` — `现在我这个理化成政治事件了...很多投资人说...`
- `00:46` — `哎呀，Miles你不能理吧！`
- `00:50` — the transcript has moved into the next sentence about shaving the beard / growing hair.

This exactly corroborates the stored segment boundaries `0–30s` and `30–50s` as GHOT source-timeline ranges. It also preserves the known ASR errors (`坚持` vs `健身`, `理化` vs `理发`, `理吧` vs `理发`) rather than silently replacing the ASR with curated text.

### GWINS

The public GWINS listing/detail for `20230314_1` independently preserves the curated wording beginning with `尊敬的战友们好，你们健身了吗` and the passage `现在我这个理发成政治事件了...很多投资人说...Miles，你不能理发`.

This supports the cross-source curated/ASR fuzzy alignment while keeping the two text provenances distinct.

## Playback status

The public GHOT time axis and GWINS curated text support the alignment intervals. However, this worker environment did not execute `scripts/audit_media.py` and did not independently inspect decoded media content at 0s, 30s, or the 50s transition.

Accordingly:

- Correct case/date identity: **supported**
- GHOT `0–30s` source interval: **exactly corroborated**
- GHOT `30–50s` source interval: **exactly corroborated**
- GWINS curated-text consistency: **supported**
- Curated/ASR distinction: **preserved**
- Actual decoded-media content independently inspected: **NO**
- Playback timing error: **not measured**
- `playback_verified`: **0**
- Qualifying playback checks: **0**
- Counts toward Pilot-60: **NO**

## Disposition

Keep both rows as `aligned_unverified_playback`. The fuzzy alignment and public transcript boundaries are strong source-timeline evidence, but neither the similarity scores nor timestamped ASR count as a real playback timing pass.

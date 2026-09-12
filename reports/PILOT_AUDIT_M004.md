# Miles-Guo_public_archive Pilot Audit — PILOT-M004

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M004`  
Case: `PILOT-M004`  
Live ID: `LIVE_20201001_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T16:46:00Z`

## Segments under audit

The case has three deliberately conservative GHOT anchors in `data/live_segments/alignment/LIVE_20201001_001.jsonl`:

1. `LIVE_20201001_001_SEG_000000` — expected start `1306.0` sec — ASR: `到了没有兄弟姐妹们能听到吗？`
2. `LIVE_20201001_001_SEG_000001` — expected start `1310.0` sec — ASR: `兄弟姐妹们我觉得我才能听到。`
3. `LIVE_20201001_001_SEG_000002` — expected start `1422.0` sec — ASR: `赶快换人换人。没时间了。`

All three use `SRC_CDA48E45`, use `ghot_public_timeline_direct_noisy_asr`, have no asserted `end_sec`, have `playback_verified = 0`, and are already `needs_review` because this source is documented as severely noisy/garbled ASR.

## Public-source checks performed

### GHOT archive identity and noisy transcript

Checked:

`https://ghot.ai/archive/videos/2020-10-01-3`

The public GHOT record identifies the same 2020-10-01 item. The source-side identity mismatch remains explicit and must not be normalized away: the path slug is `2020-10-01-3`, while the visible title is `2020.10.01-2 10.1的直播_X264`.

The public indexed transcript confirms the repository's warning that the ASR is severely noisy: substantial early portions contain garbled multilingual/nonsensical text. This audit therefore does not treat the transcript as globally reliable.

### Selected public timestamp anchors

Despite the noisy transcript, three comparatively intelligible public timestamp anchors are visible:

- `21:46` — `到了没有兄弟姐妹们能听到吗？`
- `21:50` — `兄弟姐妹们我觉得我才能听到。`
- `23:42` — `赶快换人换人。` followed at `23:43` by `没时间了。`

Converted to seconds:

- `21:46` = `1306` seconds;
- `21:50` = `1310` seconds;
- `23:42` = `1422` seconds.

These exactly reproduce the three stored `start_sec` anchors. The third stored text combines the immediately adjacent 23:42 and 23:43 transcript utterances, so it remains review-required rather than being promoted to a clean exact-text segment.

### Playback availability

The current GHOT interactive video/transcript surface does not expose a usable independent media playback position in this audit environment. No actual media player observation was made at 1306s, 1310s, or 1422s.

## Audit result

For the three selected anchors:

- Correct livestream/date provenance: **supported by GHOT public metadata**
- Source-side ordinal mismatch: **preserved**
- Severe ASR noise: **confirmed**
- Selected public timestamp consistency: **exactly corroborated**
- Global ASR reliability: **NOT established**
- Actual media playback performed: **NO**
- Observed playback position: **not measured**
- Playback timing error: **not measured**
- `playback_verified`: **0 / unverified**
- Counts toward Pilot 60 real playback checks: **NO**

## Disposition

Keep all three segments in `needs_review` with `playback_verified = 0`. The public timeline confirms the selected start anchors, but neither the source's globally noisy ASR nor actual media playback has passed audit.

Do not infer missing end times, do not assign alignment scores unsupported by evidence, and do not count these anchors toward the 60 real playback checks until a playback-capable audit independently observes the media positions.

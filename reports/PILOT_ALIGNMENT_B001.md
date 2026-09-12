# Miles-Guo_public_archive Pilot Alignment B001

Project: `Miles-Guo_public_archive`  
Task: `P7-ALIGNMENT-B001`  
Phase: `PILOT`  
Method version: `alignment-b001-v1`

## Objective

Test whether source-preserved curated GWINS text can be mapped onto a public time axis without replacing the curated wording, and preserve uncertainty when GHOT ASR is noisy.

This task is an alignment experiment, not the 60-segment playback audit. No row in this batch is marked `playback_verified = 1`.

## Alignment precedence used

The experiment follows the project rule:

1. use a source's own explicit timestamp when the curated source already provides it;
2. otherwise use GHOT's public second-level ASR timeline as a candidate time axis and compare source text;
3. keep low-confidence results for review rather than forcing alignment;
4. do not claim actual playback-position accuracy until a later real playback audit is performed.

## Method A — `curated_timestamp_direct`

When the curated source exposes an explicit timestamp boundary, that boundary is preserved directly.

Pilot control case: `LIVE_20230312_001` / GWINS page `24266`.

Two boundaries were represented in the Pilot data:

```text
00:00:00 -> 00:02:38  => 0–158 sec
00:02:38 -> 00:05:41  => 158–341 sec
```

These rows use:

```text
alignment_method = curated_timestamp_direct
alignment_quality = 1.0
playback_verified = 0
review_status = timestamped_unverified_playback
```

`alignment_quality = 1.0` here means the timestamp came directly from the curated source structure. It does **not** mean a human has played the media and measured zero-second error.

## Method B — `ghot_fuzzy_char_v1`

For overlapping GWINS/GHOT records, the experiment compares a short curated GWINS text span with the GHOT ASR span at the candidate time window.

Normalization used by `scripts/alignment_score.py`:

- Unicode NFKC normalization;
- lowercase Latin text;
- retain letters and numbers;
- remove punctuation/spacing differences;
- Python `difflib.SequenceMatcher(..., autojunk=False).ratio()`.

The similarity is stored in `alignment_quality`. It is an explainable text-similarity diagnostic, not a calibrated probability and not a measured timestamp error.

## Reproducible test cases

| Case | Canonical live | Candidate window | Similarity | Result |
| --- | --- | ---: | ---: | --- |
| `L003_OPENING` | `LIVE_20220511_001` | 0–18 sec | 0.510638 | `needs_review` |
| `L007_OPENING` | `LIVE_20230310_001` | 0–17 sec | 0.744186 | aligned, playback unverified |
| `L007_TWO_SESSIONS` | `LIVE_20230310_001` | 17–44 sec | 0.800000 | aligned, playback unverified |
| `L009_OPENING` | `LIVE_20230314_001` | 0–30 sec | 0.846154 | aligned, playback unverified |
| `L009_HAIRCUT` | `LIVE_20230314_001` | 30–50 sec | 0.794118 | aligned, playback unverified |

The cases are stored in `tests/pilot_alignment_cases.json` and can be reproduced with:

```bash
python scripts/alignment_score.py tests/pilot_alignment_cases.json
```

All five expected scores reproduced exactly in the current implementation.

## Findings

### 1. Existing curated timestamps are the strongest low-cost path

The `2023-03-12` control demonstrates that source-provided HH:MM:SS boundaries can be represented directly without ASR alignment. This should remain the preferred path whenever the timestamp provenance is explicit.

### 2. GHOT is useful as a public candidate time axis

For the `2023-03-10` and `2023-03-14` overlap examples, short curated spans remain recognizably aligned to GHOT's timed ASR even when wording differs. Similarity in these examples ranges from about `0.74` to `0.85`.

This supports using GHOT as an alignment scaffold, while keeping the curated GWINS wording separate from ASR.

### 3. Noisy ASR can be substantially weaker

The `2022-05-11` opening produces only `0.510638` similarity. It remains `needs_review` and is not promoted merely because the date/source identity is already known.

This is important: cross-source identity and transcript alignment are separate questions. A pair of pages can confidently describe the same livestream while an individual ASR span is still too noisy for reliable automatic alignment.

### 4. Alignment score is not timestamp accuracy

A high text score only says the compared spans are textually similar after normalization. It does not establish the Pilot acceptance target of `<=3 sec` or `<=8 sec` error.

Those error gates require actual media-position verification and belong to `P9-AUDIT-60`. Accordingly every row created by this task has `playback_verified = 0`.

## Durable data written

`data/live_segments/alignment/pilot_alignment_b001.jsonl` currently contains 7 Pilot segment rows:

- 2 direct curated-timestamp control rows for `LIVE_20230312_001`;
- 5 GWINS-curated / GHOT-ASR comparison rows covering `LIVE_20220511_001`, `LIVE_20230310_001`, and `LIVE_20230314_001`.

Curated text, ASR text and time provenance remain separate through `curated_source_id`, `asr_source_id`, and `time_source_id`.

## Validation

The 5 fuzzy alignment fixtures were recomputed using the same normalization/scoring algorithm and all expected scores matched.

The 7 segment rows were also loaded into an isolated SQLite database using the current `live_videos`, `live_sources`, and `live_segments` constraints with their referenced late-Pilot source IDs.

Observed result:

```text
live_segments: 7
PRAGMA foreign_key_check: no violations
PRAGMA integrity_check: ok
playback_verified = 1 rows: 0
review_status counts:
  aligned_unverified_playback: 4
  needs_review: 1
  timestamped_unverified_playback: 2
```

## Decision

`P7-ALIGNMENT-B001` demonstrates a viable two-path Pilot strategy:

```text
explicit curated timestamp
        -> preserve directly

no curated timestamp + verified cross-source identity
        -> GHOT timed ASR candidate
        -> fuzzy text comparison
        -> align or needs_review
```

The experiment is sufficient to proceed to building/searching the Pilot database, but it is **not** evidence that the final timestamp-accuracy gate has passed. Actual playback verification remains mandatory before any `FULL_ARCHIVE` decision.

## Outputs

- `scripts/alignment_score.py`
- `tests/pilot_alignment_cases.json`
- `data/live_segments/alignment/pilot_alignment_b001.jsonl`
- `reports/PILOT_ALIGNMENT_B001.md`

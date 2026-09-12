# Miles-Guo_public_archive Pilot Report

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Decision task: `P10-PILOT-DECISION`  
FULL_ARCHIVE: **NO**

## Executive conclusion

The Pilot has reached its decision gate, but it **does not pass the quality gate required to begin FULL_ARCHIVE**.

The archive model, source provenance model, cross-source identity workflow, alignment workflow, SQLite rebuild path, and FTS5 search artifact were demonstrated on a real 27-livestream cross-year Pilot. However, the required playback audit was not achieved: the aggregate P9 review found **0 qualifying real playback checks out of the required 60**.

Therefore:

```text
PILOT DECISION: FAIL QUALITY GATE
FULL_ARCHIVE: NO
```

This is a completed Pilot decision, not a claim that the Pilot met acceptance criteria.

## 1. Pilot scope

Selected Pilot sample:

```text
Early   2017–2019   9 cases
Middle  2020–2021   9 cases
Late    2022–2023   9 cases
Total               27 cases
```

The sample deliberately includes clean and difficult cases: second-level GHOT transcript anchors, GWINS-first records, multiple external media URLs, long livestreams, severe/noisy ASR, slug/title ordinal mismatches, same-day multiplicity, selected clips, multi-speaker material, and cross-platform identity cases.

## 2. Source-site findings

### GWINS

Validated value:

- curated/human-organized transcript material;
- topic/entity metadata;
- stable per-item archive pages;
- external media links including YouTube/Rumble/GETTR where present;
- explicit source-side timestamps in some cases.

Primary role in the current model: curated transcript/provenance source, not automatically an original-media source.

### GHOT

Validated value:

- broad archive/video coverage;
- dense timestamped transcript/ASR axes;
- duration and source-link evidence in many records;
- useful second-level or bounded timing anchors;
- selected-clip provenance in some cases.

Primary role: ASR/time-axis and archive discovery source. ASR quality varies substantially and cannot be treated as uniformly reliable text.

### GettrSearch / GETTR discovery

The Pilot confirms discovery/identity value, but item-level GettrSearch metadata was not consistently available enough to make it a primary transcript truth source. GETTR/Rumble/YouTube/Odysee links are retained as source/platform evidence where observed.

## 3. Collection and identity results

### Canonical livestreams

```text
27 canonical live_videos
```

### Verified source records

From the three legacy Pilot collection batches:

```text
Early:   15 live_sources
Middle:  12 live_sources
Late:    12 live_sources
Total:   39 live_sources
```

### Source-match candidates

```text
Early:   6 candidates — all direct high-confidence identity-v1 matches at 0.98
Middle:  3 candidates — preserved as needs_review
Late:    3 candidates — high-confidence matches (two 1.00, one 0.98)
Total:  12 source_match_candidates
```

At least 9 candidate relationships are high-confidence cross-source matches. The three Middle candidates remain deliberately conservative rather than being force-merged.

### Important conflict preservation

The Pilot successfully demonstrated that same-day ordinals cannot be blindly trusted. Examples include:

- 2019-05-30: the GHOT source directly maps to the correct GWINS same-day item rather than the adjacent ordinal;
- multiple Middle cases with GHOT slug/title ordinal mismatches and noisy source evidence;
- 2022-05-29: GHOT title-side numbering and GWINS numbering disagree, and the plausible source candidate was **not** falsely merged without stronger evidence.

This is evidence that the identity layer can preserve conflicts instead of silently collapsing them.

## 4. Alignment results

The aggregate P7 alignment gate demonstrated the intended priority order:

1. direct curated/source timestamps;
2. GHOT public timed ASR + text alignment;
3. local ASR only when needed;
4. manual playback for unresolved/high-value checks.

At the P7 snapshot, seven segments loaded cleanly into the schema:

```text
2 direct curated-timestamp controls
4 aligned but playback-unverified fuzzy matches
1 low-similarity needs_review case
0 playback_verified rows
```

Subsequent streaming alignment work added additional per-live segment JSONL after P7/P8. These later records preserve null end times, uncertain scores, noisy ASR, pre-roll offsets, and unresolved timing where those values were not independently known.

Because no final post-streaming database rebuild was performed in this worker environment, the exact current source-side segment total and current curated/ASR coverage percentages are **not certified here**. The P8 SQLite counts below describe the validated P8 snapshot, not all later Git-tracked alignment additions.

## 5. SQLite / FTS5 validation

P8 successfully rebuilt and validated the official artifact:

```text
database/Miles-Guo_public_archive.sqlite3
```

Validated P8 snapshot:

```text
27 live_videos
39 live_sources
12 source_match_candidates
7 live_segments
7 live_segments_fts
SQLite size: 208,896 bytes
```

Validation results:

- Python 3.12 GitHub Actions rebuild succeeded;
- `scripts/validate_db.py` succeeded;
- foreign-key/integrity validation succeeded;
- FTS5 rows were generated;
- all seven timed segments in that snapshot remained explicitly playback-unverified.

Important unresolved maintenance item: later streaming alignment JSONL was committed after the P8 artifact was built, so the committed SQLite artifact should be rebuilt again before it is treated as synchronized with all current Git source data.

## 6. Playback audit — P9

Pilot requirement:

```text
at least 60 real playback-checked segments
```

The 27 per-case audit records were reviewed across all eras.

Aggregate result:

```text
Early:    0 qualifying playback checks
Middle:   0 qualifying playback checks
Late:     0 qualifying playback checks
Total:    0 / 60
```

Public transcript timestamps, GHOT time-axis rows, GWINS chapter timestamps, selected-clip ranges, or URL seek parameters were **not** counted as playback verification.

Several audits strongly corroborate stored starts against public source timelines, but decoded audiovisual playback was not independently observed. Accordingly, `playback_verified` remains false/0 for those checks and timing error was not measured.

## 7. Pilot quality gates

Required:

```text
false livestream merge rate approximately 0
>= 90% of locatable audited segments within 3 seconds
>= 98% within 8 seconds
```

Result:

```text
Real playback sample:        0 / 60  FAIL
<= 3 second accuracy:        not measurable  FAIL / not certified
<= 8 second accuracy:        not measurable  FAIL / not certified
False-merge discipline:      promising, conflicts preserved, but not sufficient to override playback failure
```

The project requirement explicitly states that if these Pilot quality targets are not reached, full collection must not begin.

## 8. Coverage / data-quality summary

```text
Pilot livestreams:                 27
Verified live_sources:             39
Source-match candidates:           12
High-confidence cross-source:      at least 9
Middle needs_review candidates:    3
P8 certified segment snapshot:     7
P8 FTS rows:                       7
Qualifying playback checks:        0 / 60
Playback timing accuracy:          not measured
```

Exact final post-streaming values for segment count, `text_curated` coverage, `text_asr` coverage, precise-location coverage, and Git source-data byte size are not certified in this report because source JSONL continued to change after the validated P8 database snapshot. Those metrics should be regenerated together with a fresh SQLite build before any later re-evaluation.

## 9. Broken / duplicate / unresolved findings

Observed issues include:

- some public source pages or media surfaces unavailable to the worker runtime;
- Rumble/GETTR/media playback not consistently available for independent decoded-media checking;
- GHOT slug/title ordinal mismatches;
- same-day multiple-stream ambiguity;
- severe ASR noise in selected Middle cases;
- pre-roll offset risk in long recordings;
- GWINS re-fetch limitations for some Middle candidates;
- later Git alignment source data newer than the validated P8 SQLite artifact.

No unsupported source absence, timing error, FPS/frame position, playback pass, or merge certainty was invented to hide these gaps.

## 10. What the Pilot proved

The Pilot successfully proved that the archive architecture can support:

```text
one canonical livestream
+ multiple source pages/platforms
+ curated text separate from ASR
+ public timestamp provenance
+ conflict-preserving identity matching
+ Git-tracked JSON/JSONL source of truth
+ rebuildable SQLite/FTS5 search artifact
```

The Pilot did **not** prove the required real-media timestamp accuracy.

## 11. Recommendation

```text
FULL_ARCHIVE: NO
```

Reason: the mandatory 60-segment real playback audit was not completed, leaving the <=3s and <=8s timing-accuracy gates uncertified.

Before reconsidering FULL_ARCHIVE:

1. perform at least 60 genuine decoded-media playback checks across representative Early/Middle/Late cases;
2. record observed positions and timing errors explicitly;
3. confirm the >=90% within 3s and >=98% within 8s thresholds;
4. preserve/review false-merge and same-day ordinal conflicts;
5. rebuild `database/Miles-Guo_public_archive.sqlite3` from the latest Git source data and rerun validation;
6. regenerate current segment/text coverage and data-size metrics;
7. rerun the Pilot decision gate from that new evidence.

Until then, the repository remains a validated **Pilot archive implementation with a failed rollout gate**, not an authorized full-archive collection.

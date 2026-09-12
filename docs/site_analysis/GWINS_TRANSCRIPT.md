# Miles-Guo_public_archive GWINS Transcript Analysis

Project: `Miles-Guo_public_archive`  
Task: `P1-GWINS-TRANSCRIPT`  
Verified: `2026-09-12`

This analysis is based on real GWINS detail pages and focuses on transcript/body semantics, timestamps and source-provided metadata. Source wording must be preserved; missing provenance must not be guessed.

## Verified examples

```text
https://www.gwins.org/cn/milesguo/24248.html
https://www.gwins.org/cn/milesguo/547.html
https://www.gwins.org/cn/milesguo/21730.html
```

## `内容梗概` is not merely a short summary

GWINS uses the visible heading `内容梗概`, but verified pages can contain long sequential transcript-like material underneath it.

Example `24248.html` contains chronological blocks beginning with explicit media positions such as:

```text
00:06:40
00:08:22
00:09:40
```

followed by substantial spoken/news text. Therefore collectors should store the source body as transcript/source text rather than assuming it is only a short editorial summary.

## Timestamp behavior

### Clean modern examples

Verified `24248.html` contains explicit `HH:MM:SS` markers attached to content transitions, e.g.:

```text
00:06:40 视频：...
00:08:22 新闻播报：...
00:09:40 汇报工作开始...
```

These are strong candidates for `start_sec` after context validation.

### Historical/mixed-format examples

Verified `547.html` contains mixed forms and editorial/ASR markers including examples such as:

```text
3:00机器人听写结束
13:44
16:26机器人听写结束
（00：24:00）
```

Important consequences:

- timestamp punctuation may be ASCII `:` or full-width `：`;
- hour fields may be omitted for short `M:SS` forms;
- a number adjacent to `机器人听写结束` may mark an ASR boundary rather than a curated chapter title;
- timestamps embedded in prose require contextual parsing;
- not every paragraph has an explicit end time.

Never synthesize `end_sec`. It may be derived only by a documented rule such as the next verified start marker, and that derivation method must remain auditable.

## Human curation vs machine transcription

GWINS exposes a page-level `文字整理` attribution on some records. Verified historical pages can name a human/editor account while the transcript body itself still contains explicit machine-transcription markers such as `机器人听写结束`.

Therefore:

```text
page has 文字整理 attribution
```

is NOT sufficient evidence that every paragraph is purely human-curated.

Recommended classification:

- text explicitly shown as human-edited/organized and not marked as machine transcription -> candidate `text_curated`;
- text explicitly marked as robot/machine transcription -> `text_asr` or source transcript subtype `asr`;
- body with mixed or uncertain origin -> preserve verbatim as source text and mark provenance `mixed/unverified` until reviewed;
- never copy machine text into `text_curated` merely because it appears on a GWINS page.

## Source-provided entity/topic metadata

Verified detail pages expose page-level linked metadata such as:

```text
主播人物
涉及人物
公司组织
国家地区
名词解释
文字整理
```

Example `21730.html` includes many linked people, organizations and geographic entries, plus glossary terms and a named text organizer.

These fields are valuable source-provided metadata, but they should be treated as page-level annotations, not automatically as exhaustive segment-level entities.

Recommended preservation:

```text
source_host_people[]
source_people[]
source_organizations[]
source_regions[]
source_glossary_terms[]
source_text_editor[]
```

Later entity normalization may map them into canonical `entities`, but the original label and source URL should remain recoverable.

## Segment mapping recommendation

When creating `live_segments`, preserve both source text and provenance.

Suggested logic:

1. split only at explicit, reproducible boundaries (time marker, source heading, clearly separate media block);
2. preserve the raw timestamp token before normalization;
3. normalize a verified timestamp to seconds as `start_sec`;
4. keep `end_sec = null` unless explicitly known or reproducibly derived;
5. map human-curated and ASR text separately;
6. attach `curated_source_id`, `asr_source_id` and `time_source_id` independently when they differ;
7. mark ambiguous body sections `review_status = unverified/needs_review` rather than guessing.

## Timestamp parser requirements for GWINS

A future parser should recognize at least:

```text
HH:MM:SS
H:MM:SS
MM:SS
H:MM
full-width-colon variants such as HH：MM：SS
parenthesized markers such as （00：24:00）
```

but must reject false positives from dates, quantities, clock-time references or unrelated numeric prose.

Context should be retained, for example:

```text
raw_timestamp
normalized_start_sec
source_text_before_after
parser_rule
verification_status
```

## Search-text policy

`text_search` may combine searchable normalized forms for retrieval, but it must not replace either original field:

```text
text_curated
text_asr
```

No AI rewrite should overwrite the original source wording.

## Key edge cases

1. `内容梗概` can contain a full chronological transcript, not just a short summary.
2. one page may mix human organization and machine transcription.
3. timestamp formats vary across years and typography.
4. page-level entity tags are useful but not segment-level ground truth.
5. `文字整理` attribution does not prove all contained text is human-curated.
6. some modern pages provide clean chapter-like time markers while older pages can be irregular.
7. time markers must be validated against playback later; parsing a timestamp string alone is not a playback audit.

## Pilot implication

GWINS is a strong candidate source for high-quality/organized text and rich metadata, but the Pilot must classify transcript provenance at finer granularity than simply `source_site = gwins`. GHOT/public timing may later be used to improve alignment, while the original GWINS wording remains preserved.

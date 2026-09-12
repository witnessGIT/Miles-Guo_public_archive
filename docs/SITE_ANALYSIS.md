# Miles-Guo_public_archive Site Analysis

Project: `Miles-Guo_public_archive`  
Phase: `SITE_ANALYSIS + PILOT`  
Last verified: `2026-09-13`

This document records only findings checked against real public pages. Missing findings remain unresolved rather than guessed.

## GWINS

Status: `P1-GWINS-STRUCTURE verified; transcript-specific analysis remains a separate task.`

### Entry points and pagination

Primary archive/list URL:

```text
https://www.gwins.org/cn/milesguo/
```

Observed pagination pattern:

```text
https://www.gwins.org/cn/milesguo/list_2_2.html
...
https://www.gwins.org/cn/milesguo/list_2_72.html
```

The final observed list page displays a total count of `2874` records and page navigation ending at page `72`.

### Detail-page URL and source-page ID

Observed detail pattern:

```text
https://www.gwins.org/cn/milesguo/<numeric-page-id>.html
```

Verified examples:

```text
https://www.gwins.org/cn/milesguo/24266.html
https://www.gwins.org/cn/milesguo/547.html
https://www.gwins.org/cn/milesguo/21730.html
```

The numeric path component is a strong candidate for `source_page_id` / third-party source identity. It must remain a source identifier and must not become the canonical internal `live_id`.

### List-record structure

List entries expose a linked title plus a text excerpt. Modern examples commonly include a source-side label such as:

```text
20230312_1
20230228_1
20230228_2
20230209_1
20230209_2
20230209_3
20230209_4
```

This proves that date alone is not a unique livestream/video key: multiple records can occur on the same date.

Older records are not fully uniform. Verified early examples include labels without an explicit `_N` suffix, such as:

```text
20170513
20170512
20170511
20170510
20170509
20170506
20170505
```

while nearby records may use suffixed forms such as `20170508_1`, `20170507_1`, `20170507_2`, `20170504_1`, `20170504_2`.

Therefore collectors must not assume every historical title contains a canonical `YYYYMMDD_N` source label. Legacy records without a sequence suffix require explicit normalization/review.

### Detail metadata

Verified detail pages expose labeled metadata fields including:

- 主播人物 / host person;
- 涉及人物 / involved people;
- 公司组织 / companies and organizations;
- 国家地区 / countries and regions;
- 名词解释 / glossary terms;
- 文字整理 / text organizer/editor attribution;
- 发布时间 / publication date;
- 视频链接 and 视频链接2 / media links;
- 相关图书 / related books;
- 中文字幕 / Chinese subtitles;
- 英文字幕 / English subtitles;
- 内容梗概 / content body or summary area.

Not every field is populated on every page.

### Verified media-link behavior

Recent verified example:

```text
https://www.gwins.org/cn/milesguo/24266.html
```

exposes both:

```text
GETTR:  https://gettr.com/streaming/p2b7kcm569c
Rumble: https://rumble.com/v5b2z4t-20230312-1.html
```

Older verified example:

```text
https://www.gwins.org/cn/milesguo/547.html
```

exposes both YouTube and Rumble links. This supports modeling one GWINS archive page as one source record that may point to multiple original/backup media platforms.

### Date/title behavior

The detail page exposes a `发布时间` field, and the visible page title also commonly embeds a date/source-side label. The structured publication field should be preferred over date parsing from free-form title when both are available.

### Duplicate and identity behavior

No safe rule should merge GWINS records solely by date or similar titles.

Observed reasons:

- multiple distinct entries can exist on the same date;
- modern records may distinguish same-day entries with `_1`, `_2`, etc.;
- legacy records may omit the suffix entirely;
- content type varies (`直播`, `盖特`, `视频`, interviews/calls, etc.).

Collectors should preserve each GWINS page URL and numeric page ID independently. Canonical cross-source merging belongs to `P4-IDENTITY-RULES`, using stronger evidence such as shared platform video IDs, source links, date, duration and transcript evidence.

### Structural extraction recommendation

For each GWINS discovery/detail record preserve at minimum:

```text
source_site = gwins
source_page_id = numeric detail-page ID
url = full GWINS detail URL
source_title = page/list title as published
published_date = 发布时间 when present
source_side_label = YYYYMMDD[_N] only when actually exposed
host_people
involved_people
organizations
countries_regions
glossary_terms
text_editor_attribution
media_links[]
subtitle_links[]
retrieved_at
verification_status
```

Do not infer missing source-side sequence numbers.

### Known structural risks / edge cases

1. Historical labels are not uniform; some lack `_N`.
2. Same-day multiple entries are common enough that date cannot be unique.
3. Metadata fields may be present but empty.
4. Media platform varies by era and record; one page may expose more than one media link.
5. `直播`, `视频`, `盖特`, interviews and calls coexist in the same archive and must not automatically be treated as the same content class.
6. List snippets are discovery text, not a substitute for detail-page provenance.
7. Transcript/time-code semantics require separate verification in `P1-GWINS-TRANSCRIPT`.

## GHOT

Status: `P2-GHOT-ARCHIVE verified; transcript/time-axis quality remains a separate task (P2-GHOT-TIMELINE).`

Verified on public pages on `2026-09-13`.

### Archive/list entry point

Primary video archive URL:

```text
https://ghot.ai/archive/videos
```

The archive page exposes:

- full-text/search input labeled for `ID / 日期 / codec / language`;
- archive-date controls for year, month and day;
- duration filters: `全部`, `短`, `中`, `长`, `超长`;
- newest-first result ordering;
- an initial result list plus a `加载更多` control.

The visible archive count is not treated as a stable source identifier. Different indexed/cached page observations showed different totals, so collectors must not embed a global count as an integrity invariant.

### Detail URL and GHOT source-page ID

Observed detail pattern:

```text
https://ghot.ai/archive/videos/YYYY-MM-DD-N
```

Verified examples:

```text
https://ghot.ai/archive/videos/2018-11-25-3
https://ghot.ai/archive/videos/2019-05-30-2
https://ghot.ai/archive/videos/2022-05-11-2
https://ghot.ai/archive/videos/2023-03-14-1
```

The final slug is a strong GHOT `source_page_id` candidate and should be preserved exactly as third-party source identity. It must not become the canonical internal `live_id`.

Important edge case: GHOT path suffix and source-side/title numbering are not guaranteed to be identical. A verified page at:

```text
https://ghot.ai/archive/videos/2020-10-01-3
```

is titled:

```text
2020.10.01-2 10.1的直播_X264
```

Therefore collectors must store both the GHOT slug and the published/source-side label separately and must never rewrite one from the other.

### Detail metadata observed

Depending on the record and rendering state, detail/indexed pages expose:

- published/display date;
- source title;
- language (`zh` observed);
- duration;
- video dimensions/resolution when known;
- archive/transcription status indicators;
- original-video platform/link where available;
- external GETTR / Rumble / GWINS links;
- transcript section and fallback text excerpt.

Metadata completeness varies by record. Verified examples include:

```text
2018-11-25-3 -> 640×480, 1m 00s
2023-01-26-1 -> 1920×1080, 9m 58s
2022-05-11-2 -> resolution shown as unknown/— in one indexed view, duration about 2h 35m
```

Unknown resolution must remain null/unknown; it must not be inferred from another mirror.

### Verified cross-source/original links

Example:

```text
GHOT:   https://ghot.ai/archive/videos/2022-05-11-2
GETTR:  https://gettr.com/streaming/p19cmxu5e7b
Rumble: https://rumble.com/v5af5v1-20220511-2.html
GWINS:  https://gwins.org/cn/milesguo/23878.html
```

The GETTR page title confirms the linked streaming item is `七哥与战友们连线直播`.

Another verified example:

```text
GHOT:  https://ghot.ai/archive/videos/2023-03-14-1
GETTR: https://gettr.com/post/p2bexmi7ac8
GWINS: https://gwins.org/cn/milesguo/24264.html
```

The GETTR target may be a `/streaming/<id>` URL or a `/post/<id>` URL. Preserve the complete target URL and extract the third-party ID only after identifying the actual platform URL type.

### Link-label normalization risk

Do not normalize platform from GHOT's visible link label alone.

A verified older page:

```text
https://ghot.ai/archive/videos/2018-11-25-3
```

renders a first external link under the generic visible label `GETTR`, while that target resolves to `youtu.be` in the indexed page data. This means collectors should preserve:

```text
displayed_link_label
actual_target_url
normalized_platform_from_target_hostname
```

and flag disagreement for review rather than silently rewriting provenance.

### Static HTML vs dynamic/API-backed behavior

Observed behavior is consistent with a mixed/hybrid page rather than a purely static document:

- the archive page presents an initial result set and a `加载更多` control;
- transcript areas visibly show `正在加载转写…` before/alongside available indexed text;
- some direct detail fetches expose a page shell saying `未找到该视频条目` while the same response/indexed representation still contains fallback title/date/transcript excerpts and source links.

This strongly indicates client-side hydration and/or dynamic data loading for at least part of the page state. An exact public API endpoint was **not** verified in this task and must not be invented. Future collector code should first prefer documented/stable page data or a separately verified endpoint and should cache responses at low request rates.

### Duplicate and identity behavior

GHOT cannot be treated as one date = one livestream:

- the list contains multiple same-day records such as `2023-03-12-1` / `2023-03-12-2` and `2023-03-07-1` / `2023-03-07-2`;
- the GHOT slug suffix can differ from a source-side ordinal embedded in the published title;
- one GHOT detail can expose several external representations of the same underlying material (GETTR, Rumble, GWINS, and in older cases YouTube/Odysee links).

No exact-content duplicate pair was conclusively proven during this structural task, so duplicate equivalence must remain unresolved unless stronger evidence exists. Cross-source identity belongs to `P4-IDENTITY-RULES` and should use exact external platform IDs first, then date/title/duration/text evidence.

### Structural extraction recommendation

For each GHOT record preserve at minimum:

```text
source_site = ghot
source_page_id = exact YYYY-MM-DD-N slug
url = full GHOT detail URL
source_title = exact published title
display_date
language
duration_sec when explicitly available
width / height when explicitly available
archive_status / transcript_status when exposed
original_video_url when exposed
external_links[] = {displayed_label, url, normalized_platform, source_video_id}
retrieved_at
verification_status
```

Do not derive canonical `live_id` from the GHOT slug. Do not infer dimensions, source platform, or source ordinal from title/labels when the actual target contradicts them.

### Known structural risks / edge cases

1. GHOT slug suffix may not match source/title ordinal.
2. Same date can contain multiple distinct records.
3. Resolution metadata can be missing even when duration/text exists.
4. External visible labels can disagree with the actual target hostname.
5. GETTR targets occur in both `/streaming/<id>` and `/post/<id>` forms.
6. Page state is at least partly dynamic; fallback/indexed content and live UI state can differ.
7. Search/index snapshots may report different aggregate archive counts; counts are not stable identity data.
8. Transcript/time-axis granularity and ASR accuracy are intentionally deferred to `P2-GHOT-TIMELINE`.

## GettrSearch

Status: `not yet analyzed under the current claimed-task protocol`.

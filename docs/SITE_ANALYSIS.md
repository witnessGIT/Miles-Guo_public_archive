# Miles-Guo_public_archive Site Analysis

Project: `Miles-Guo_public_archive`  
Phase: `SITE_ANALYSIS + PILOT`  
Last verified: `2026-09-12`

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

Status: `not yet analyzed under the current claimed-task protocol`.

## GettrSearch

Status: `not yet analyzed under the current claimed-task protocol`.

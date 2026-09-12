# Miles-Guo_public_archive Site Analysis

Project: `Miles-Guo_public_archive`  
Phase: `SITE_ANALYSIS + PILOT`  
Status consolidated: `2026-09-13`

This file is the current high-level source-analysis index. Detailed transcript/time-axis findings live in the focused documents listed below. Unproven findings remain unresolved rather than inferred.

## Current status

| Source | Structure | Transcript / time axis | Current archival role |
| --- | --- | --- | --- |
| GWINS | analyzed | analyzed in `docs/site_analysis/GWINS_TRANSCRIPT.md` | source text/metadata/archive links/explicit timestamps where present |
| GHOT | analyzed | analyzed in `docs/GHOT_TIMELINE_ANALYSIS.md` | archive metadata, ASR, candidate public time axis, cross-source links |
| GettrSearch | analyzed to currently reachable public/static level in `docs/site_analysis/GETTRSEARCH.md` | durable transcript/timeline not verified | discovery/backfill only until dynamic payload is reproducibly verified |

All three initial sources have therefore been structurally investigated enough to support the current Pilot. This does not mean every dynamic field or historical record has been exhaustively captured.

## GWINS

Primary archive:

```text
https://www.gwins.org/cn/milesguo/
```

Observed detail pattern:

```text
https://www.gwins.org/cn/milesguo/<numeric-page-id>.html
```

Key rules:

- numeric page ID is source identity, never canonical `live_id`;
- one date can contain multiple records, so date-only merging is forbidden;
- historical source labels are inconsistent and may omit `_N`;
- pages can expose people, organizations, regions, glossary terms, text-organizer attribution, publication date, media/subtitle links and content text;
- one page may link to several media-platform representations;
- `文字整理` does not prove every paragraph is human-curated;
- mixed/robot-transcribed text must not be promoted to verified curated text;
- explicit source timestamps are preferred when genuinely exposed;
- do not invent `end_sec` from a next timestamp without explicit provenance/derivation.

Detailed transcript analysis:

```text
docs/site_analysis/GWINS_TRANSCRIPT.md
```

## GHOT

Primary archive:

```text
https://ghot.ai/archive/videos
```

Observed detail pattern:

```text
https://ghot.ai/archive/videos/YYYY-MM-DD-N
```

Key rules:

- GHOT slug is source identity, not canonical `live_id`;
- same-date multiple records exist;
- path suffix and title/source ordinal can disagree and must be preserved independently;
- unknown duration/resolution/source fields remain unknown;
- visible external-link labels can disagree with the actual target URL;
- GETTR links may use `/streaming/<id>` or `/post/<id>`;
- GHOT transcript text is ASR and belongs in `text_asr`, never overwriting source wording;
- GHOT start anchors are candidate time positions, not automatically playback-verified positions;
- text-alignment similarity is not measured timestamp error;
- noisy/low-confidence ASR remains `needs_review` rather than being forced.

Detailed time-axis analysis:

```text
docs/GHOT_TIMELINE_ANALYSIS.md
```

## GettrSearch

Primary site:

```text
https://gettrsearch.com/
```

Detailed analysis:

```text
docs/site_analysis/GETTRSEARCH.md
```

Verified current behavior:

- UI exposes year choices covering 2017–2023 and short/long-video filters;
- static/crawlable result state can report `Failed to get the videos`;
- indexed routes follow `/playvideo/<opaque-id>`;
- the opaque route token is not proven to be a GETTR platform ID;
- static HTML did not expose durable enough metadata/transcript/original-platform identity for primary archival truth;
- failed or empty static retrieval is not proof that a video is absent.

Current role:

```text
discovery / backfill
```

Do not promote GettrSearch to primary metadata/transcript truth until its dynamic public payload can be reproducibly extracted and independently checked against original sources.

## Cross-source identity rules confirmed by the Pilot

1. exact shared platform/source IDs or direct cross-references are strongest;
2. exact date is useful but never sufficient by itself;
3. title/duration/text evidence may strengthen a candidate;
4. same-day neighboring records remain distinct unless stronger evidence merges them;
5. identity confidence and transcript-alignment confidence are separate questions;
6. conflicts are preserved rather than overwritten.

The `2019-05-30` Pilot case demonstrates the safety rule: multiple GWINS records exist on the same date, and stronger evidence selects the correct record rather than merging by date.

## Alignment strategy supported so far

```text
explicit source/curated timestamp
        ↓
GHOT public timed ASR + monotonic text alignment
        ↓
local ASR only when public timing is inadequate
        ↓
manual/real playback verification for unresolved or acceptance-critical segments
```

Curated/source text, ASR text and timing provenance remain separate.

The Pilot has demonstrated useful candidate alignment, but it has not yet established the final `<=3 sec` / `<=8 sec` playback-accuracy gates across the required audit sample.

## Evidence-gated coverage still unresolved

The Pilot intentionally does not fabricate absence claims. These desired categories remain unresolved until bounded evidence proves them:

- a demonstrable GettrSearch-discovered item absent from bounded GWINS/GHOT search;
- a demonstrable `GWINS-only` livestream;
- a demonstrable `GHOT-only` livestream.

`not found` is not equivalent to `proven absent`.

## Current conclusion

The source architecture is sufficient for the Pilot and aligns with the project goal:

```text
one canonical livestream
+ multiple independently preserved sources
+ source/curated/mixed text provenance
+ ASR text
+ candidate/verified timing with explicit provenance
+ searchable SQLite/FTS
```

Remaining work is primarily Pilot completion and quality proof. `FULL_ARCHIVE` remains unauthorized until the real playback-audit and other Pilot acceptance gates are satisfied.

# Miles-Guo_public_archive GettrSearch Site Analysis

Project: `Miles-Guo_public_archive`  
Task: `P3-GETTRSEARCH-STRUCTURE`  
Verified: `2026-09-12`

This file records only behavior verified from publicly reachable GettrSearch pages/search-indexed page output. Dynamic fields that were not exposed are marked unresolved instead of inferred.

## Entry point

```text
https://gettrsearch.com/
```

The public homepage exposes a search box labeled for searching Miles Guo videos, plus year and video-type filters.

Observed year choices:

```text
2017
2018
2019
2020
2021
2022
2023
```

Observed video-type choices:

```text
短视频
长视频
```

## Search/list delivery behavior

The current public page shell loads, but the crawlable result state reports:

```text
Failed to get the videos
```

This is important structurally: the archive list/video metadata is not fully embedded in the server-rendered/static HTML that a simple crawler receives. The useful result payload is therefore likely fetched dynamically by client-side code/API calls.

Collectors must not treat an empty static HTML result as proof that a year/video is absent.

## Play-video route

A publicly indexed example route is:

```text
https://gettrsearch.com/playvideo/SCHoW40Bx4I_j1sv3RIs
```

Observed route pattern:

```text
/playvideo/<opaque-id>
```

The static HTML for the verified example contains the site shell but does not expose enough video metadata to establish title, date, duration, transcript text, original GETTR URL or platform video ID.

The route token is therefore only a GettrSearch-local opaque identifier candidate. It must NOT be assumed to be a GETTR post/video ID without independent evidence.

## GETTR IDs and original links

Current result: `unresolved from static public HTML`.

No verified original GETTR URL or GETTR platform ID was exposed in the static page content inspected during this task.

Future dynamic-payload analysis should explicitly look for:

```text
GETTR post/video ID
original GETTR URL
source video URL
publication timestamp
duration
title/description
long/short classification
year field
```

Any discovered platform ID must be stored as third-party/source identity, never used as the canonical internal `live_id`.

## Date/title/text availability

The homepage exposes search/filter controls but not durable per-video records in static HTML.

The verified `/playvideo/<opaque-id>` shell likewise did not expose durable date/title/transcript fields to a basic crawler.

Therefore, for the current Pilot, GettrSearch cannot yet be treated as a verified text or metadata truth source solely from static HTML.

## Source-role recommendation

Provisional role:

```text
discovery / backfill source
```

Reasoning:

- it is explicitly organized around video search;
- it exposes year and long/short filters useful for locating candidate material;
- static HTML does not currently provide enough durable source metadata for primary archival truth;
- original GETTR/platform identity still needs extraction/verification from the dynamic payload or independently reachable source links.

Do not promote GettrSearch to a primary metadata/transcript source until dynamic fields are reproducibly extracted and verified against original media/platform records.

## Extraction recommendation

For each GettrSearch candidate preserve, when actually available:

```text
source_site = gettrsearch
gettrsearch_route
gettrsearch_opaque_id
search_year_filter
search_video_type_filter
source_title
published_at
source_video_id
original_gettr_url
other_media_urls
retrieved_at
verification_status
raw_metadata/evidence
```

Fields not returned by the public payload must remain null/unverified; do not synthesize them from the route token.

## Risks / edge cases

1. Core result data appears client-side/dynamic, so simple HTML scraping can produce false absence.
2. `/playvideo/<opaque-id>` identifiers are opaque and are not proven GETTR IDs.
3. The static shell currently does not expose enough evidence for canonical cross-source identity matching.
4. Year/type filters are useful discovery constraints but are not themselves proof of a video's publication date or content class.
5. A future collector should capture the dynamic response with low request rate and no access-control bypass, then compare returned platform IDs/URLs against original GETTR records.

## Pilot implication

GettrSearch is valuable for locating and backfilling candidate videos, but the current Pilot should rely on stronger provenance from GWINS/GHOT/original platform links for canonical metadata until GettrSearch's dynamic payload is verified.

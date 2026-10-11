# Phase 2 full metadata audit and public-source supplement

Project: `Miles-Guo_public_archive`

Archive run: `original-livestream-restart-2026-09-16`

Audit date: 2026-10-11 (Asia/Tokyo)

Scope: all current Phase 2 `metadata_fill` records under `data/current`, their
claim/completion records, public metadata for unresolved source and asset
locators, the rebuilt SQLite database, and tracked repository files. Sealed
archive directories were not used. No media was downloaded, played, decoded,
transcribed, segmented, or otherwise content-inspected.

## Result

**PASS WITH 17 DOCUMENTED TECHNICAL-METADATA GAPS.**

The Phase 2 task ledger remains complete and internally consistent: all 1,750
canonical livestreams have one `metadata_fill` claim and one completion, all
completion output references exist, every recorded result commit resolves, and
claim/completion ownership agrees. JSON/JSONL source data rebuilds a valid
SQLite database with matching row counts, no foreign-key violations, and an
`integrity_check` result of `ok`.

The full public-source refresh materially improved coverage without inspecting
media content. Canonical records without duration and dimensions fell from 61
to 17, lives without a media-asset row fell from 63 to 10, and assets with an
`unknown` availability state fell from 1,413 to 146. Remaining unknowns are
preserved instead of manufacturing values.

## Audited inventory

| Record class | Count |
| --- | ---: |
| Canonical livestreams | 1,750 |
| Live sources | 5,099 |
| Media assets | 3,311 |
| Derived live work items | 17,500 |
| `metadata_fill` claims | 1,750 |
| `metadata_fill` completions | 1,750 |
| Date range | 2017-04-26 through 2023-03-14 |

Every live has at least one source. There are no duplicate live, source, or
media-asset IDs; no orphan live/source/asset references; no missing titles or
live dates; no live-ID/date mismatches; and no exact duplicate canonical
titles. There are no source URLs or platform/video IDs shared across different
canonical lives.

## Public-source supplement

The supplement checked 1,549 unique unresolved or incomplete public locators
through platform webpage/API metadata. It also inspected 100 exact GWINS detail
pages associated with the remaining gaps. This produced 78 additional
platform-source rows and 129 additional source-backed asset rows.

Only fields explicitly returned by public metadata were recorded. The checks
used Rumble oEmbed, Odysee resolve metadata, GETTR post/page metadata, YouTube
public player metadata, and ordinary public-page responses. The resulting
structured records preserve check time, method, platform identity and available
technical fields, with `media_fetched: false` and `playback_verified: false`.

Coverage changes from the pre-supplement audit:

| Gap | Before | After |
| --- | ---: | ---: |
| Lives without media assets | 63 | 10 |
| Lives without duration/dimensions | 61 | 17 |
| Assets with `unknown` availability | 1,413 | 146 |
| Assets without `checked_at` | 16 | 0 |
| Semantically malformed repeated-URL rows | 1 | 0 |

The repeated Rumble URL for `LIVE_20230122_001` was repaired from a duplicated
concatenation to `https://rumble.com/v5bsvh9-20230122-3.html`. Stable record IDs
were retained, and the source, asset locator, and match evidence now agree.

## Coordination and provenance checks

- Missing claims: 0.
- Missing completions: 0.
- Completions without claims: 0.
- Claim/completion Agent mismatches: 0.
- Empty completion validation statements: 0.
- Missing completion output paths: 0.
- Completion result commits: 30 unique commits checked, 0 missing.
- Entry mode: 1,750 `work`.
- Workflow: 1,750 `continuous-worker-v2`.
- Claim protocol: 1,750 `claim-protocol-v2`.

The static `live_work_items` inventory still contains 17,500 `open` rows,
including 1,750 `metadata_fill` rows. Current executable state is derived from
the durable claim/completion ledger, where `metadata_fill` is 1,750/1,750 and
the ordinary queue is empty. The static rows are therefore a denormalized
planning inventory, not an unresolved executable queue.

## Metadata coverage

### Canonical livestreams

| Field/state | Count | Coverage |
| --- | ---: | ---: |
| Title present | 1,750 | 100.0% |
| Live date present | 1,750 | 100.0% |
| Duration known | 1,733 | 99.0% |
| Width and height known | 1,733 | 99.0% |
| Exact platform publication time known | 345 | 19.7% |
| Status `partial` | 1,723 | 98.5% |
| Status `discovered` | 27 | 1.5% |
| Status `source_missing` | 0 | 0.0% |

The 17 remaining canonical technical-metadata gaps consist of 10 records with
no public media locator, six records whose only known YouTube copy is now dead,
and one inaccessible legacy GTV locator. Seven of the no-locator records are
historical audio-chat pages that currently expose text but no public media URL.

### Sources

| Check | Result |
| --- | ---: |
| Valid HTTP(S) URL syntax | 5,099 / 5,099 |
| `last_verified_at` present | 4,930 / 5,099 |
| Status `reachable` | 4,526 |
| Status `available` | 335 |
| Status `discovered` | 152 |
| Status `dead` | 83 |
| Status `blocked` | 3 |
| Shared source URLs across different lives | 0 groups |
| Shared platform/video IDs across different lives | 0 groups |

Platform distribution after case-normalization: GWINS 1,745; Rumble 1,739;
YouTube 535; Odysee 544; GETTR 492; GHOT 35; other 5; 51Haoyou 2; GTV 1;
Vimeo 1.

Sixteen livestreams completed under earlier source-specific evidence formats
and do not carry the later `metadata_fill_task_id` field on a source row. Each
still has a valid claim, completion, existing output references, resolvable
result commit, and source-backed validation. This is a metadata-style
consistency gap, not a missing completion.

### Media assets

| Field/state | Count |
| --- | ---: |
| Lives with at least one media asset | 1,740 |
| Lives without a media asset | 10 |
| Availability `available` | 3,079 |
| Availability `unknown` | 146 |
| Availability `dead` | 83 |
| Availability `blocked` | 3 |
| Duration known | 3,070 |
| Width and height known | 2,636 |
| MIME type known | 569 |
| `checked_at` present | 3,311 |
| Source hash present | 542 |
| Playback-verified | 0 |

All 146 unknown assets were checked during this run. They remain unknown because
the public response did not prove current media availability: 144 are GETTR
locators, one is an Odysee locator, and one is a legacy GTV locator. Three
YouTube locators returned access-blocked responses. The 83 dead assets are
YouTube copies whose public oEmbed endpoint reports that the video is
unavailable. Asset-level dimensions remain
unknown for some otherwise available YouTube/GETTR page locators, but canonical
technical metadata is complete for 1,733 of 1,750 lives through other sources.

## Database and repository integrity

- Rebuilt SQLite counts exactly match JSON/JSONL: 1,750 lives, 5,099 sources,
  3,311 assets, and 17,500 work items.
- SQLite `PRAGMA integrity_check`: `ok`.
- SQLite foreign-key violations: 0.
- `scripts/validate_db.py`: OK, 0 warnings.
- Candidate-review validator: PASS, 2,605 contract-v2 reviews in 51 batches,
  0 lease warnings.
- Unit tests: 103 passed.
- Git object database and commit graph: `git fsck --no-dangling` passed.
- Tracked video/audio files: 0.
- Tracked files larger than 50 MiB: 0.

## Deferred checks

Playback Audit remains intentionally unperformed. The gate currently has 0 of
60 qualifying decoded-media checks and therefore does not pass. This is not a
Phase 2 metadata-integrity failure: playback, ASR, caption work, cue/segment
splitting, and content inspection were explicitly outside this run.

## Recommended follow-up

1. Treat the 1,750/1,750 completion ledger as the authoritative Phase 2 task
   result.
2. Preserve the 17 remaining canonical technical gaps as unresolved until a
   new public source appears or media inspection is separately authorized.
3. Recheck the 146 unknown, three blocked, and 83 dead locators in a future availability audit;
   do not infer playback success from page metadata.
4. Do not mark the Playback/Pilot-60 gate complete until real decoded-media
   evidence is explicitly authorized and produced.

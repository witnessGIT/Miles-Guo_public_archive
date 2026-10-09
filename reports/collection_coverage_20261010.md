# Phase 1 collection coverage

Project: `Miles-Guo_public_archive`

Task: `C4-COLLECTION-COVERAGE`

Date: 2026-10-10 (Asia/Tokyo)

## Result

The active Phase 1 discovery boundary set is covered. No additional source
boundary is justified by the current active evidence, so the collection set can
advance to the freeze task. This conclusion uses only `data/current`, current
coordination completions, and the rebuilt database; sealed archive directories
were not used as completion evidence.

## Boundary coverage

| Source | Boundaries | Coverage observation |
| --- | ---: | --- |
| GWINS | 141 | All 72 numbered `list_2_1` through `list_2_72` index pages are present with no numeric gap; 69 detail boundaries are also recorded. |
| GHOT | 44 | The active archive traversal boundaries are recorded as completed. |
| GETTRSEARCH | 15 | One search boundary and 14 detail/post boundaries are recorded as completed. |
| **Total** | **200** | **All 200 are effectively complete after applying durable completion records.** |

The final stale `in_progress` discovery record, `C1-GWINS-detail-24263`, had a
complete source-backed duplicate record but an expired claim. It was reclaimed
and completed under Claim Protocol v2 before this coverage decision.

## Candidate and canonical coverage

- Source candidates: 2,693 total — 2,614 discovered/reviewable, 73 duplicate,
  4 promoted, and 2 rejected in the source records.
- Candidate review queue: 2,614 reviewed, 0 unreviewed, 0 in progress.
- Candidate-review evidence validator: 2,605 v2 completions in 51 batches, with
  zero lease warnings; remaining reviewed identities are covered by the explicit
  grandfathering contract.
- Canonical livestreams: 1,750, spanning 2017-04-26 through 2023-03-14.
- Live-source records: 5,019. Every canonical livestream has at least one source
  record; observed range is 1–10 source records per live.
- Media assets: 3,179. Sixty-five canonical livestreams currently have no media
  asset, and all recorded asset availability values remain `unknown`.

The 65 no-asset cases and unresolved availability fields are downstream
`metadata_fill` / playback-backlog work, not evidence of an unscanned source
boundary. They remain visible in the generated per-live work queue and are not
silently treated as verified media.

## Derived downstream inventory

C3 produced 17,500 open work items: one item for each of 1,750 canonical lives
at each of the ten processing stages (`metadata_fill`, `transcript_import`,
`cue_split`, `segment_split`, `entity_pass`, `event_pass`, `claim_pass`,
`relation_pass`, `text_verify`, and `playback_backlog`). This preserves the known
coverage gaps as explicit downstream work rather than expanding Phase 1 with
unsupported discovery boundaries.

## Validation

- `python3 scripts/validate_candidate_reviews.py`: PASS.
- `python3 scripts/build_db.py`: 1,750 live videos, 5,019 live sources, 3,179
  media assets, and 17,500 live work items.
- `python3 scripts/validate_db.py`: OK, zero warnings.


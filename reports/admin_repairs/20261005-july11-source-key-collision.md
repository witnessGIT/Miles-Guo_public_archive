# Miles-Guo_public_archive — July 11 source-key collision repair

Agent: `agent-20261004T125231Z-chat-c2-gw3`; freshly verified GitHub administrator `witnessGIT`.
Repair base: `d9580b188763ed80711523d6a9754e21dcc2b97a`.

## Reproduced failure

While validating the unrelated C2 lease repair in PR #8, Build Pilot SQLite run `37246332816`, job `111564870783`, checked synthetic merge `03311dd9ff22aa1759984f2d8a36181908aadf09`. All 108 unit tests and candidate evidence validation passed; the database preflight failed on duplicate primary keys `SRC_YOUTUBE_WJ9TK9ZNEKE` and `MA_YOUTUBE_WJ9TK9ZNEKE` in the `20200711_1` and `20200711_2` files. The failure is in concurrent main data, not an excuse to skip the database gate.

Fresh main reads confirmed the duplicated keys. The existing review artifact `data/current/candidate_reviews/SC_GWINS_LIST2_38_20200711_2-R002.json` already explicitly acknowledges the shared YouTube URL and retains separate canonical items based on the distinct GWINS and Rumble identifiers. This maintenance does not independently re-adjudicate or endorse that identity decision. A shared locator is retained as shared, not silently replaced with an invented video.

## Minimal referential repair

Only four scalar key/reference values change, all scoped to `LIVE_20200711_002`:

- `sources/c2_review_20200711_2.jsonl`, record 2: internal ID `SRC_YOUTUBE_WJ9TK9ZNEKE` becomes `SRC_C7524A91`.
- `media_assets/c2_review_20200711_2.jsonl`, record 1: internal ID `MA_YOUTUBE_WJ9TK9ZNEKE` becomes `MA_27A5B9C0`; `source_id` becomes `SRC_C7524A91`.
- `source_match_candidates/c2_review_20200711_2.jsonl`, record 1: `right_source_id` becomes `SRC_C7524A91`.

All paths above are under `data/current/`. These are new internal row keys, not new platform identities. The YouTube platform ID `WJ9TK9zNEkE`, its exact URL, both canonical live IDs, all other fields, prior reviewer attribution and timestamps, original review artifacts, claims and completion history remain unchanged. The original keys continue to identify the `_001` records. The mapping in this report preserves auditability of the renamed `_002` records.

Before repair, fetched Git blob hashes were `ba83d883f31a433c27b974de0170b49e0b2d9fe8` (sources), `8901a76c020240c4eea4c3fadb54e7ad5e732ccd` (assets), and `5bd03cf663af2a09f630f963cbc0bddeb66f1efb` (matches). The patch must be reviewed for precisely these four scalar changes and validated through the existing unit/evidence/database CI before merge. No force overwrite of concurrent edits is permitted.

New C2 reviews completed by this repair: **0**. The current GW10 batch remains 12/20, with its eight existing origin gaps unchanged. No media was downloaded or played, and no deduplication or playback success is claimed. Successful full database validation must be observed in the associated PR/Actions result; it is not pre-asserted by this report.

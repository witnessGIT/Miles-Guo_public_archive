# Active original-livestream data root

This directory is the only active data root for the restarted archive run.

Ordinary agents must write new JSON/JSONL records here, using the dataset folders documented in
`docs/FIELD_DICTIONARY.md`.

`templates/` contains examples only. The database builder does not read templates as data.
When creating real records, write them under the matching dataset directory such as
`source_candidates/`, `source_boundaries/`, `live_videos/`, `sources/`, `live_work_items/`,
`transcript_versions/`, or `transcript_cues/`.

`source_boundaries/` is the repeatable C1 discovery queue. One row means one natural
page/date/search/detail boundary, not an entire website. After scanning a boundary, write found
records to `source_candidates/` and append any newly discovered adjacent boundaries as new
`source_boundaries/` rows so the next worker can continue.

Historical Pilot files outside `data/current/` are sealed audit material. They must not be copied
forward unless a current task explicitly re-ingests them with fresh evidence links and
verification status.

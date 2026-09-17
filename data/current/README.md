# Active original-livestream data root

This directory is the only active data root for the restarted archive run.

Ordinary agents must write new JSON/JSONL records here, using the dataset folders documented in
`docs/FIELD_DICTIONARY.md`.

`templates/` contains examples only. The database builder does not read templates as data.
When creating real records, write them under the matching dataset directory such as
`source_candidates/`, `live_videos/`, `sources/`, `live_work_items/`, `transcript_versions/`,
or `transcript_cues/`.

Historical Pilot files outside `data/current/` are sealed audit material. They must not be copied
forward unless a current task explicitly re-ingests them with fresh evidence links and
verification status.

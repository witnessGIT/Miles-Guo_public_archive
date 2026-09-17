# Active original-livestream data root

This directory is the only active data root for the restarted archive run.

Ordinary agents must write new JSON/JSONL records here, using the dataset folders documented in
`docs/FIELD_DICTIONARY.md`.

Historical Pilot files outside `data/current/` are sealed audit material. They must not be copied
forward unless a current task explicitly re-ingests them with fresh evidence links and
verification status.

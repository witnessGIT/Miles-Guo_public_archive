# Candidate review evidence

One JSON file records one completed candidate-identity review. New completions use
`candidate-review-evidence-v2` and must include the task/candidate/Agent/mode identity, a final
decision, public evidence URLs, review timestamp, and all six checked fields: `identity`, `date`,
`title`, `platform_ids`, `source_relationships`, and `deduplication`.

If public evidence is insufficient, do not create a completion. The claim remains `in_progress`
and returns to `unreviewed` after its 10-hour timeout.

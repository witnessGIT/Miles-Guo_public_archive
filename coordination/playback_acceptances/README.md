# Playback Acceptances

Worker-writable business coordination area for an **active claimed** `P9-PLAYBACK-*` task.

A worker may create an acceptance only after reading the corresponding durable repository evidence:

```text
data/playback_evidence/<CASE_ID>/<SEGMENT_ID>/evidence.json
data/playback_evidence/<CASE_ID>/<SEGMENT_ID>/evidence.md
```

One acceptance per canonical timed segment:

```text
coordination/playback_acceptances/<CASE_ID>/<SEGMENT_ID>.json
```

Required contract: `playback-acceptance-v1`. Copy the exact `bundle_id` from the evidence and write a factual `content_observation` explaining why the decoded-media evidence matches the canonical target.

The acceptance owner must equal the active playback claim owner. Acceptance without valid service evidence never counts toward Pilot-60.

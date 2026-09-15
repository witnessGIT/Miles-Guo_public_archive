# Two-Phase Archive Workflow

## Phase 1 — collect before judging

Agents work by source and write raw, source-preserving records. Duplicates and uncertainty must be retained and labelled. The phase ends only with a frozen candidate manifest covering the three approved sources.

## Phase 2 — verify in small steps

Each batch contains at most 25 records. Independent tasks run in order: provenance; identity; segment/anchor; real audio and ASR; content match; archive publication. Only verified records enter the formal archive or SQLite. Blocked records remain traceable and are never promoted.

# Ordinary Agent C1 Guide

This guide is for low-cost ordinary agents doing repeatable source discovery.
It intentionally stops before canonical promotion.

## Goal

Process exactly one natural source boundary per task.

Examples:

- one GWINS index page, such as `list_2_67`
- one GHOT archive/date window
- one GETTR search result page
- one detail page

Do not process a fixed number of videos. Do not promote candidates to
`live_videos`, `live_sources`, or `media_assets`.

## Required Steps

1. Run:

   ```bash
   python scripts/next_task.py --list
   ```

2. Claim the top eligible C1 task:

   ```bash
   python scripts/next_task.py --claim --agent-id agent-<UTC>-<short-id>
   ```

3. Immediately commit and push the claim before doing source work.

4. Scan the task's one natural boundary.

5. Write discovered records under `data/current/source_candidates/`.

6. If the boundary exposes adjacent pages or detail/search continuations, append
   them as open rows in `data/current/source_boundaries/`.

7. Mark the claimed boundary completed in both:

   - `coordination/claims/<TASK_ID>.json`
   - `coordination/completed/<TASK_ID>.json`

8. Rebuild and validate:

   ```bash
   python scripts/build_db.py
   python scripts/validate_db.py
   python -m unittest discover -s tests
   ```

9. Commit and push outputs.

10. Continue by claiming the next eligible task only after the previous outputs
    are visible on `main`.

## Output Rules

For C1, create only `source_candidates`.

Each candidate must preserve:

- source site
- source boundary URL
- visible title
- candidate date if visible or parseable
- source page ID
- source video ID if visible
- detail URL in `metadata_json` when known
- discovery agent and UTC timestamp
- status `discovered`

Use `needs_review` only when the row is relevant but ambiguous.

## Do Not

- Do not write canonical `live_videos`.
- Do not write `live_sources`.
- Do not write `media_assets`.
- Do not mark anything playback verified.
- Do not use historical Pilot files as current data.
- Do not close a whole source site after one page.
- Do not invent direct media URLs.

## Current Next Boundary

At the time this guide was written, the next ordinary C1 task was:

```text
C1-GWINS-list_2_67
```

Workers should trust `python scripts/next_task.py --list` over this note if the
queue has moved.

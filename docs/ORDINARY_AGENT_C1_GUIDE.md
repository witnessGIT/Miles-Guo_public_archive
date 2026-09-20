# Ordinary Agent C1 Guide

This guide is for low-cost ordinary agents doing repeatable source discovery.
It intentionally stops before canonical promotion.

## One-screen checklist

Run this from a fresh `main` checkout:

```bash
git pull --ff-only
python scripts/next_task.py --list
python scripts/next_task.py --claim --agent-id agent-<UTC>-<short-id>
```

Then complete exactly the claimed C1 task, validate, commit, push, and repeat.

If `--list` shows C1 tasks, there is ordinary work left. If it shows no C1 tasks, report the
remaining task types exactly as printed. Do not conclude "all done" from stale local files or old
Pilot material.

If you claimed the wrong task or discover that your runtime should not perform it, release the
claim instead of leaving it to block the queue:

```bash
python scripts/next_task.py --release <TASK_ID> --agent-id <same-agent-id> --reason "<short reason>"
```

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

   If the ordinary-chat web reader cannot fetch the exact page, do not stop and do not use
   search snippets. Submit one repository Source Page Evidence request for the active claim:

   ```json
   {
     "request_version": "source-fetch-request-v1",
     "task_id": "C1-GWINS-list_2_3",
     "agent_id": "agent-<same-claim-owner>",
     "source_site": "gwins",
     "source_page_id": "list_2_3",
     "source_url": "https://www.gwins.org/cn/milesguo/list_2_3.html",
     "requested_at": "<UTC ISO-8601>"
   }
   ```

   Write it to `coordination/source_fetch_requests/<TASK_ID>/<agent_id>.json`, commit and push.
   GitHub Actions will publish the complete parsed page to
   `data/source_page_evidence/gwins/<source_page_id>/evidence.json`. Refresh `main`, read that
   evidence, and use its `items` as the verified natural-boundary source. The generated evidence
   is read-only to workers. A pending evidence request is continuation of the claimed task, not a
   `HOST_STOP`, and does not authorize claiming another task.

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

Before adding a candidate, search existing `data/current/source_candidates/` for the same
`source_site` plus `source_video_id` or exact `source_url`. If the same source item already
exists, do not reuse the same `id`. Either skip the row, or write a unique `duplicate` row whose
`metadata_json` includes `duplicate_of` and the boundary where it was rediscovered.

`scripts/build_db.py` runs a data preflight before writing SQLite. It rejects unknown fields,
missing IDs, and duplicate IDs across all current JSON/JSONL records. Fix those source files
before pushing more data.

Valid `source_candidates.page_kind` values are:

- `index_page`
- `search_result_page`
- `date_page`
- `channel_page`
- `detail_page`
- `media_page`
- `unknown`

For GETTR search pages, use `search_result_page`, not `search_result`.

## Do Not

- Do not write canonical `live_videos`.
- Do not write `live_sources`.
- Do not write `media_assets`.
- Do not mark anything playback verified.
- Do not use historical Pilot files as current data.
- Do not close a whole source site after one page.
- Do not invent direct media URLs.

## Queue Rule

Do not rely on a hardcoded "next boundary" in any chat, prompt, note, or older commit. The only
current ordinary task list is:

```bash
python scripts/next_task.py --list
```

If a claim collides, expires, or is already completed, refresh `main` and claim the next eligible
task. A single completed page does not complete an entire source site.

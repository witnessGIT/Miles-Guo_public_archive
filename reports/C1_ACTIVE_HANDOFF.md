# C1 Active Handoff

Updated: 2026-09-21 JST
Repository: `witnessGIT/Miles-Guo_public_archive`
Branch: `main`

## Immediate objective

Continue **C1 source discovery only**. The current highest-priority open boundary is expected to be:

```text
C1-GWINS-list_2_7
https://www.gwins.org/cn/milesguo/list_2_7.html
```

Always refresh and run `python3 scripts/next_task.py --list` before claiming because scheduled ChatGPT agents may advance the queue after this handoff is written.

## Current durable state

- `C1-GWINS-list_2_12` through `C1-GWINS-list_2_8` are completed.
- Each completed GWINS page contributed 40 `source_candidates`.
- `list_2_8` was initially blocked in ordinary chat mode, then completed by a verified `witnessGIT` admin using direct HTTP access.
- `list_2_8` completion commit: `0d8e09a`.
- Current database validation after `list_2_8`: 2,344 source candidates, 3 canonical live videos.
- C1 is not complete; the adjacent-page chain must continue toward `list_2_1` unless fresh source evidence establishes a different natural end.
- Five ChatGPT scheduled tasks exist for C1 work. They run hourly at minutes `:06`, `:18`, `:30`, `:42`, and `:54` JST. Treat fresh Git state as authoritative and obey claim races.

## Fast takeover procedure

From the existing checkout:

```bash
git pull --ff-only
python3 scripts/next_task.py --list
python3 scripts/next_task.py --claim --agent-id agent-<UTC>-<short-id>
git add coordination/claims/<TASK_ID>.json
git commit -m "Claim <TASK_ID>"
git push origin main
```

After the claim is visible on fresh `main`:

1. Fetch the exact natural boundary directly. For GWINS, `curl -L -A 'Mozilla/5.0' <URL>` has worked when ordinary chat retrieval failed.
2. Record all visible listing items under `data/current/source_candidates/gwins/`.
3. Preserve visible titles, dates, source video IDs, boundary URL, and detail URLs.
4. Mark the current boundary completed and append exactly the adjacent next natural boundary.
5. Update the claim to completed and create `coordination/completed/<TASK_ID>.json`.
6. Validate with:

   ```bash
   python3 scripts/build_db.py
   python3 scripts/validate_db.py
   python3 -m unittest discover -s tests
   ```

7. Commit and push the task outputs, then refresh and continue to the next eligible C1 task.

## Hard boundaries

- Do not perform C2 candidate promotion.
- Do not modify canonical `live_videos`, `live_sources`, or `media_assets`.
- Do not invent source membership or reconstruct a full page from search snippets.
- One task equals one complete natural source boundary, not an arbitrary row quota.
- Preserve existing claims and completions; resolve races by refreshing and selecting another eligible task.
- Unknown identities act as workers. The authenticated GitHub account `witnessGIT` is the verified admin identity.

## Authoritative files

- Entry contract: `START_HERE.md`
- Worker rules: `AGENTS.md`
- C1 guide: `docs/ORDINARY_AGENT_C1_GUIDE.md`
- Queue: `data/current/source_boundaries/phase1_initial_boundaries.jsonl`
- Claims: `coordination/claims/`
- Completions: `coordination/completed/`
- Outputs: `data/current/source_candidates/`

This handoff is an acceleration aid, not a replacement for fresh claim verification. A capable agent should read this file, refresh `main`, claim the current top eligible C1 task, and execute immediately.

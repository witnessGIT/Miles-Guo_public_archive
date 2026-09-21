# C1 Active Handoff

Updated: 2026-09-21 JST
Repository: `witnessGIT/Miles-Guo_public_archive`
Branch: `main`

## Immediate objective

**C1 source discovery is complete.** Do not claim or invent another C1 boundary. Fresh queue state
now recommends `C2-CANDIDATE-PROMOTION`, which is outside the former C1-only worker scope and
requires an explicit C2 operating decision.

## Current durable state

- `C1-GWINS-list_2_72` through `C1-GWINS-list_2_1` are completed.
- Each completed GWINS page contributed 40 `source_candidates`.
- `list_2_8` was initially blocked in ordinary chat mode, then completed by a verified `witnessGIT` admin using direct HTTP access.
- `list_2_8` completion commit: `0d8e09a`.
- Current database validation after `list_2_1`: 2,624 source candidates, 3 canonical live videos.
- The Source Page Evidence Service is live and was end-to-end verified on `list_2_3`; ordinary
  chat agents can submit a small owned request when their web reader cannot access the exact page.
- The adjacent-page chain reached `list_2_1`; its verified pagination exposed no further positive
  `list_2_N` boundary.
- All five C1 ChatGPT scheduled tasks were paused after C1 completion to prevent empty hourly runs
  or accidental C2/canonical work.

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

1. Fetch the exact natural boundary. If the ordinary chat web reader fails, submit the request
   documented in `docs/ORDINARY_AGENT_C1_GUIDE.md`, refresh, then use the generated evidence.
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

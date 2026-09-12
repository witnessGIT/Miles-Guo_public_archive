# Miles-Guo_public_archive

## Mandatory reading before work

Every agent working in this repository MUST read these files before planning, editing, collecting data, or committing:

1. `coordination/README.md` — mandatory multi-Agent coordination and atomic task-claim protocol.
2. `coordination/WORK_QUEUE.jsonl` — machine-readable executable work queue.
3. `docs/CURRENT_TASK.md` — current phase, objectives, work-unit details and quality gates.
4. `docs/PROJECT_REQUIREMENTS.md` — complete user requirements.
5. `docs/NAMING_AND_WORKFLOW.md` — authoritative naming and repository boundaries.
6. `README.md` and relevant existing `docs/`, `schema/`, `reports/`, `data/`, `coordination/`, and `tests/` files.

Do not rely on a previous chat, cached summary, or another agent's recollection instead of reading these files. This applies to primary and delegated agents.

If required files are missing, do not invent their contents. Create only missing project scaffolding explicitly required by repository rules, record what was missing, and continue with safe work.

## Immediate-start rule

Reading the repository is preparation, not completion.

After mandatory reading, an agent MUST immediately begin a real unfinished task unless the user explicitly asked only for analysis/review.

Mandatory startup sequence:

```text
Read requirements
↓
Inspect current repository state
↓
Read WORK_QUEUE.jsonl
↓
Read coordination/completed/
↓
Read coordination/claims/
↓
Filter to tasks whose dependencies are completed
↓
Remove completed or actively claimed tasks
↓
Choose highest-priority safe task
↓
CREATE coordination/claims/<TASK_ID>.json
↓
Only after claim creation succeeds: execute the task
↓
Validate durable output
↓
Commit results
↓
CREATE coordination/completed/<TASK_ID>.json
↓
Continue with next available task when safe
```

Do NOT stop after saying:

- "I read the requirements";
- "I understand the project";
- "the next step is to collect data";
- "someone should analyze the sites".

If the next safe action can be executed, execute it.

## Atomic claim rule — mandatory

No Agent may start a queued work unit before successfully creating:

```text
coordination/claims/<TASK_ID>.json
```

This file creation is the coordination lock.

If creation fails because the file already exists:

1. do not overwrite it;
2. refresh `claims/` and `completed/`;
3. choose the next eligible task.

Do not coordinate ownership by editing a single shared status field. Do not assume a task is free merely because `docs/CURRENT_TASK.md` says OPEN.

A task is considered unavailable when:

- `coordination/completed/<TASK_ID>.json` exists; or
- a valid claim exists and has not been properly declared stale/taken over.

Detailed stale/takeover rules are in `coordination/README.md`.

## Scope and precedence

- Only modify `witnessGIT/Miles-Guo_public_archive`. Default branch: `main`.
- Never modify `witnessGIT/movie_production` or any other repository for this task.
- Official project name: `Miles-Guo_public_archive`.
- Only official database path: `database/Miles-Guo_public_archive.sqlite3`.
- Current explicit user instructions take precedence. Later saved rules override older examples.
- Archive First, Application Second. This is a searchable public digital archive, not a video production project.
- Zero-cost-first: the core archive must remain usable without paid APIs, paid cloud databases, or paid object storage.

## Current default mission

Unless superseded by a newer explicit user instruction, agents are working on `SITE_ANALYSIS + PILOT` for:

- `gwins` — https://www.gwins.org/
- `ghot` — https://ghot.ai/
- `gettrsearch` — https://gettrsearch.com/

The mission is to turn real public records into a unified, traceable archive where one livestream can have multiple sources, high-quality text, a reliable time axis, and a route back to source media.

Use `coordination/WORK_QUEUE.jsonl` as the executable task source. Use `docs/CURRENT_TASK.md` for task details and quality gates.

## Required work discipline

- Inspect branch/history/current files before changes and preserve unrelated work.
- Before writing a new record, search existing data, source URLs, platform IDs and `live_id` values.
- Analyze the three public source sites before broad collection. Pilot remains 20–30 real livestreams until quality gates pass.
- One livestream has one canonical internal live ID and may have multiple source records.
- Preserve curated text and ASR separately with provenance.
- Use seconds as the primary locator. Never invent timestamps, FPS, matches, availability, publication times, IDs or verification results.
- Keep JSON/JSONL under `data/` as Git source of truth. SQLite/FTS5 must rebuild from `data/` + `schema/`.
- Every datum must retain source site, source URL, retrieval/verification state and third-party ID when available.
- Randomly audit at least 60 segments before Pilot approval; playback-position checks must be real, not inferred from URL parameters.
- Do not begin FULL_ARCHIVE merely because collection is technically possible. Pilot evidence must pass first.
- Publicly accessible content only. Low request rate, caching, no bypass of login/CAPTCHA/paywall/access control/DRM.
- Never commit full video, large audio, model weights, cache or FFmpeg intermediates.
- Make stage-based commits and report actual checks/failures.
- Distinguish SITE_ANALYSIS, PILOT, FULL_ARCHIVE and MAINTENANCE.
- When user policy changes, update durable repo rules so later Agents inherit it.

## Data-work rules for multiple agents

Multiple agents are expected to work in parallel.

- Work ownership is per task ID, never by vague area such as "I am doing GWINS".
- Prefer source/year/batch partitioning for collection.
- Avoid multiple Agents editing the same large JSONL file. Use independent batch files where possible.
- Never silently overwrite another Agent's curated text, provenance, alignment result or review status.
- Preserve conflicting claims and record them in `coordination/conflicts/`.
- Collector work should preserve source candidates; canonical cross-source identity merges belong to identity/matching tasks unless the queue explicitly says otherwise.
- If a task is completed, validate it and move to another task rather than redoing it.
- If a claim appears stale, follow the takeover procedure in `coordination/README.md`; never simply overwrite the claim.

## Definition of useful progress

A useful Agent run should normally leave at least one durable artifact, for example:

- a verified site-structure finding;
- a real livestream/source record;
- real curated/ASR segment data with provenance;
- schema/build/validation work required by real data;
- a cross-source identity decision with evidence;
- an audit result with playback evidence;
- a documented conflict or missing-source finding with search scope;
- a completed-task record pointing to the result commit.

Pure planning with no durable output is not completion when real work was possible.

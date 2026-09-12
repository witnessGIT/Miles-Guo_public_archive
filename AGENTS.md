# Miles-Guo_public_archive

## Mandatory reading before work

Every agent working in this repository MUST read this file and the following documents before planning, editing, collecting data, or committing:

1. `docs/CURRENT_TASK.md` — the current executable work queue. If no newer explicit user instruction exists, this is the default task source.
2. `docs/PROJECT_REQUIREMENTS.md` — complete user requirements, source analysis, schema, Pilot coverage, quality gates, and acceptance queries.
3. `docs/NAMING_AND_WORKFLOW.md` — authoritative naming rules, repository boundaries, and working procedure.
4. `README.md` and any existing relevant `docs/`, `schema/`, `reports/`, `data/`, and `tests/` files.

Do not rely on a previous chat, cached summary, or another agent's recollection instead of reading these files. This applies to primary and delegated agents. A delegating agent must pass on these requirements.

If required files are missing, do not invent their contents. Create only the missing project scaffolding that is explicitly specified by the repository requirements, record what was missing, and continue with the parts that can be done safely.

## Immediate-start rule

Reading the repository is preparation, not completion.

After mandatory reading, an agent MUST immediately begin a real, currently unfinished archive task unless the user explicitly asked only for analysis or review.

Default behavior:

```text
Read requirements
↓
Inspect current repository state
↓
Read CURRENT_TASK.md
↓
Identify one unfinished work unit
↓
Claim it in the work log/task file if the mechanism exists
↓
Analyze real public source data
↓
Write structured source data / analysis / validation output
↓
Run required checks
↓
Commit the completed unit
↓
Update progress and continue with the next unfinished unit when safe
```

Do NOT stop after saying:

- "I read the requirements";
- "I understand the project";
- "the next step is to collect data";
- "someone should analyze the sites".

If the next safe action can be executed, execute it.

## Scope and precedence

- Only modify `witnessGIT/Miles-Guo_public_archive`. Default branch: `main`.
- Never modify `witnessGIT/movie_production` or any other repository for this task.
- Official project name: `Miles-Guo_public_archive`.
- Only official database path: `database/Miles-Guo_public_archive.sqlite3`.
- Current explicit user instructions take precedence. Among saved requirements, later naming rules override older examples, especially the six-digit segment suffix.
- Archive First, Application Second. This is a searchable public digital archive, not a video production project.
- Zero-cost-first: the core archive must remain usable without paid APIs, paid cloud databases, or paid object storage.

## Current default mission

Unless superseded by a newer explicit user instruction, agents are currently working on the `SITE_ANALYSIS` + `PILOT` phase for these public sources:

- `gwins` — https://www.gwins.org/
- `ghot` — https://ghot.ai/
- `gettrsearch` — https://gettrsearch.com/

The mission is to turn real records from these sources into a unified, traceable archive model where one livestream can have multiple source records, high-quality text, a reliable time axis, and a route back to the source media.

Agents should prefer unfinished items listed in `docs/CURRENT_TASK.md` over inventing new work.

## Required work discipline

- Inspect remote URL, branch, main history, existing files, and applicable instructions before changes. Preserve unrelated work.
- Before writing a new record, search existing `data/`, reports, and source IDs to avoid duplicate work.
- Analyze the three public source sites before broad collection. Limit Pilot to 20–30 real livestreams across years, including all required coverage cases.
- One livestream has one internal live ID and multiple source records. Preserve curated text and ASR separately, with complete provenance.
- Use seconds as the primary locator. Never invent timestamps, FPS, matches, source availability, publication times, or verification results.
- Keep JSON/JSONL under `data/` as the Git source of truth. Rebuild SQLite and FTS5 entirely from `data/` and `schema/`.
- Every collected datum must retain provenance: source site, source URL, retrieval time where applicable, third-party source ID where available, and source/verification status.
- Randomly audit at least 60 segments before Pilot approval. Actual playback checks are required for time accuracy; checking that a URL contains a timestamp is insufficient. Mark unperformed checks as unverified.
- Do not recommend full collection unless evidence meets the user's quality gates. Stop expansion after Pilot and report the result.
- Only access normally public content, at low concurrency with request spacing and caching. Do not bypass login, CAPTCHA, paywalls, access controls, or DRM.
- Never commit full video, large audio, models, or cache. Remove temporary downloaded media after analysis.
- Make clear stage-based commits. Run checks appropriate to each stage; report actual results and unresolved failures.
- Distinguish SITE_ANALYSIS, PILOT, FULL_ARCHIVE, and MAINTENANCE. Do not describe partial work as completed.
- Update saved requirements and `CURRENT_TASK.md` when the user changes project policy so later agents inherit the current contract.

## Data-work rules for multiple agents

Multiple agents may work in parallel. To reduce collisions:

- Prefer dividing Pilot work by source/year/sample batch rather than editing the same JSONL file simultaneously.
- Check whether another agent has already created the same `live_id`, platform source ID, or source URL before adding a record.
- Never silently overwrite another agent's curated text, provenance, alignment result, or review status.
- When sources disagree, preserve both claims with provenance and mark the conflict for review rather than choosing silently.
- If a record needs correction, make the correction auditable in Git and explain the evidence in the commit/report.
- Do not claim exclusive ownership of broad ranges unless the work queue explicitly assigns them.

## Definition of useful progress

A useful Agent run should normally leave at least one durable artifact, for example:

- a verified site-structure finding in `docs/SITE_ANALYSIS.md`;
- a real livestream metadata JSON record;
- a real `live_sources` record;
- curated/ASR segment JSONL with provenance;
- a schema/build/validation improvement required by real data;
- an audit result with playback evidence;
- a documented source conflict or missing-source finding with search scope;
- a Pilot progress update.

Pure planning with no durable output is not considered completion when real work was possible.

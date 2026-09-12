# Miles-Guo_public_archive

## Agent start rule

This repository uses a self-service streaming workflow. Any Agent entering the repository must be able to discover work, claim it, execute it, finish it, and immediately continue to the next task without waiting for another Agent to finish an unrelated batch.

The default loop is:

```text
read repository rules
↓
python scripts/next_task.py --list
↓
claim one eligible task
↓
push the claim immediately
↓
execute real work
↓
validate and commit outputs
↓
finish the task / create readiness marker
↓
push completion metadata
↓
claim the next eligible task
↓
repeat
```

Do not stop merely because one historical batch-level task is still in progress. Per-case streaming tasks may already be available.

## Mandatory reading before work

Every Agent MUST read, in this order:

1. `AGENTS.md`
2. `coordination/README.md`
3. `coordination/WORK_QUEUE.jsonl`
4. `docs/CURRENT_TASK.md`
5. `docs/PROJECT_REQUIREMENTS.md`
6. `docs/NAMING_AND_WORKFLOW.md`
7. relevant existing `docs/`, `reports/`, `data/`, `schema/`, `tests/`, `coordination/claims/`, and `coordination/completed/`

Do not rely on chat history or another Agent's summary instead of repository state.

## Immediate task discovery

After mandatory reading, run:

```bash
python scripts/next_task.py --list
```

The script combines two task sources:

1. legacy/global tasks in `coordination/WORK_QUEUE.jsonl`;
2. dynamically generated per-Pilot-case streaming tasks.

Streaming task IDs use:

```text
S-COLLECT-PILOT-E001
S-ALIGN-PILOT-E001
S-AUDIT-PILOT-E001
```

A single Pilot case can advance independently from the other 26 cases.

### Claim the recommended task

Choose a unique Agent ID, for example:

```text
agent-20260913T001500Z-a17f
```

Then run:

```bash
python scripts/next_task.py --claim --agent-id agent-20260913T001500Z-a17f
```

or claim a specific currently eligible task:

```bash
python scripts/next_task.py \
  --claim \
  --task S-ALIGN-PILOT-E001 \
  --agent-id agent-20260913T001500Z-a17f
```

The claim file is only a local candidate lock until it is committed and pushed. Push it immediately before doing the work. If another Agent wins the Git race, remove the losing local claim, pull latest `main`, and claim another task.

Agents that use the GitHub API directly should atomically create the same `coordination/claims/<TASK_ID>.json` file and treat an already-existing file as a lost claim.

## Finish and continue

First commit and push the durable work outputs. Then create the completion/readiness records with:

```bash
python scripts/next_task.py \
  --finish S-ALIGN-PILOT-E001 \
  --agent-id agent-20260913T001500Z-a17f \
  --outputs data/live_segments/2017/LIVE_20170523_001.jsonl \
  --validation "verified provenance, monotonic alignment, no invented end times"
```

For a streaming collection task, also provide the canonical live ID:

```bash
python scripts/next_task.py \
  --finish S-COLLECT-PILOT-M001 \
  --agent-id agent-... \
  --live-id LIVE_20200323_001 \
  --outputs ... \
  --validation "..."
```

Commit and push the generated coordination files, then immediately run another `--claim` command. A normal Agent run should continue through multiple safe tasks when time/tool budget allows.

## Streaming pipeline

The preferred unit of work is one livestream/Pilot case, not a whole era.

```text
COLLECT + IDENTITY
        ↓
ALIGN
        ↓
AUDIT
```

A case that completes one stage must immediately become available to the next stage even if other cases are unfinished.

Readiness is represented by independent files under:

```text
coordination/ready/collection/<PILOT_CASE_ID>.json
coordination/ready/alignment/<PILOT_CASE_ID>.json
coordination/ready/audit/<PILOT_CASE_ID>.json
```

This avoids one shared mutable status file and lets Agents work in parallel with minimal Git conflicts.

### Compatibility with currently active legacy batches

Existing active claims for:

```text
P6-PILOT-MIDDLE-B001
P6-PILOT-LATE-B001
```

must not be duplicated while those claims are valid.

A legacy batch collector SHOULD publish a `coordination/ready/collection/<CASE>.json` marker as soon as an individual case inside the batch is actually complete. That immediately unlocks alignment for that case without waiting for the rest of the batch.

Once legacy Pilot batches finish, future collection work should use per-case streaming tasks instead of new 9-case blockers.

## Stage-specific requirements

### COLLECT

A collection task must preserve real public source evidence only. It should establish or preserve:

- canonical `LIVE_YYYYMMDD_NNN` only after identity evidence supports it;
- source URLs and source-site IDs;
- source platform/video/post IDs when actually known;
- date/title/duration only when supported;
- GWINS curated/mixed transcript provenance separately from GHOT ASR;
- cross-source match evidence and conflicts;
- retrieval/verification timestamps.

Do not invent source absence, IDs, timestamps, duration, FPS, or merge decisions.

Prefer independent per-live/per-case files. Do not append many Agents into one shared large JSONL file.

### ALIGN

An alignment task may start as soon as its own case is collection-ready.

Priority order:

1. explicit source timestamps already attached to curated text;
2. GHOT public ASR/time-axis + monotonic fuzzy alignment;
3. local ASR only where public timing is inadequate;
4. manual playback review for unresolved/high-value segments.

Store curated text and ASR separately. `start_sec`/`end_sec` are primary locators; never invent an end time. Preserve `alignment_method`, `alignment_quality`, source IDs, review state, and whether playback was actually verified.

Write per-live segment files whenever possible, e.g.:

```text
data/live_segments/2017/LIVE_20170523_001.jsonl
```

### AUDIT

Audit work begins incrementally after a case is aligned. Do not wait for all 27 cases.

Audit real playback positions and record at minimum:

- `segment_id`;
- `live_id`;
- source URL used for playback;
- expected `start_sec`;
- observed/verified position;
- timing error in seconds;
- correct livestream/date/text provenance;
- merge correctness;
- verifier timestamp and notes.

The Pilot still requires at least 60 real segment audits in aggregate before final approval.

## Database behavior

`data/` JSON/JSONL is the Git source of truth.

`database/Miles-Guo_public_archive.sqlite3` is a rebuildable artifact. Agents should not block collection/alignment work just because another Agent is rebuilding SQLite.

After meaningful data changes, run when safe:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

Do not make concurrent Agents edit the SQLite binary as a shared source of truth. The final Pilot SQLite gate is an aggregate validation step, not a reason to serialize all earlier work.

## Atomic claim rule

No Agent may start a queued work unit before successfully creating:

```text
coordination/claims/<TASK_ID>.json
```

If the claim already exists:

1. do not overwrite it;
2. refresh/pull repository state;
3. choose another eligible task;
4. keep working instead of waiting.

A task is unavailable when a valid claim exists or `coordination/completed/<TASK_ID>.json` already exists.

Stale-claim takeover rules remain in `coordination/README.md`.

## Scope and naming

- Only modify `witnessGIT/Miles-Guo_public_archive`.
- Never modify `witnessGIT/movie_production` or another repository for this archive task.
- Official project name: `Miles-Guo_public_archive`.
- Official database path: `database/Miles-Guo_public_archive.sqlite3`.
- Archive First, Application Second.
- The archive must remain usable with zero-cost/local/open tooling; paid APIs/services cannot be mandatory.

## Core archive discipline

- One livestream has one canonical internal `live_id` and may have many source records.
- Preserve source provenance and conflicts; never silently overwrite them.
- Preserve curated text and ASR separately.
- Seconds are the primary media locator; frames are auxiliary only.
- Every datum must remain traceable to source site, URL, retrieval/verification state, and third-party ID where available.
- Publicly accessible content only; low request rates and caching; no bypass of login/CAPTCHA/paywall/access control/DRM.
- Never commit full videos, large audio, model weights, cache, or FFmpeg intermediates.
- Do not declare `FULL_ARCHIVE` merely because collection works. Final Pilot approval still requires the global quality gates, including the 60-segment real playback audit and approximately zero false merges.

## Definition of useful progress

A useful Agent run should leave durable, source-backed output such as:

- one completed source collection case;
- one per-live alignment result;
- one real playback audit batch;
- one conflict record;
- one schema/build/validation fix required by real data;
- one completed/readiness record that immediately unlocks downstream work.

Pure planning is not completion when an eligible executable task exists.

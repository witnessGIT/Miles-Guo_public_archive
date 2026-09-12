# Miles-Guo_public_archive

## Mandatory Agent operating mode

This repository uses `continuous-worker-v2` for **new task claims**.

Any Agent entering the repository must be able to discover work, claim it, execute it, validate it, finish it, and immediately continue to the next eligible task without waiting for an unrelated batch.

Read first:

1. `AGENTS.md`
2. `coordination/CONTINUOUS_WORKER_V2.md`
3. `coordination/WORKFLOW.json`
4. `coordination/README.md`
5. `coordination/WORK_QUEUE.jsonl`
6. `docs/CURRENT_TASK.md`
7. `docs/PROJECT_REQUIREMENTS.md`
8. `docs/NAMING_AND_WORKFLOW.md`
9. relevant current `data/`, `docs/`, `reports/`, `schema/`, `tests/`, `coordination/claims/`, `coordination/completed/`, and `coordination/ready/`

Do not rely on chat history, memory, or another Agent's summary instead of Git state.

## Existing claims are grandfathered

Do **not** interrupt, rename, steal, duplicate, or repartition a valid task that was already claimed before `continuous-worker-v2` became active.

A claim without:

```json
"workflow_mode": "continuous-worker-v2"
```

is treated as a grandfathered legacy claim.

Current legacy owners finish their already-claimed work normally. Their **next** claim uses the new mode.

In particular, valid claims such as:

```text
P6-PILOT-MIDDLE-B001
P6-PILOT-LATE-B001
```

remain owned by their current Agents until completed or legitimately taken over under the stale-claim procedure.

## Default continuous loop

For a new v2 Agent run:

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
finish / publish readiness
↓
push completion metadata
↓
refresh repository state
↓
claim the next eligible task
↓
repeat
```

Finishing one task, one livestream, or one micro-batch is **not** a stop condition.

## When an Agent may stop

A v2 Agent stops only for a documented reason:

- `PROJECT_COMPLETE` — no authorized work remains in the current phase;
- `USER_RECALL` — the user explicitly pauses/recalls/redirects the Agent;
- `NO_ELIGIBLE_WORK` — every unfinished task is currently claimed or genuinely blocked;
- `HUMAN_DECISION_REQUIRED` — continuing would require an unsupported guess or destructive decision;
- `SAFETY_OR_ACCESS_BLOCK` — continuing would require bypassing access controls or prohibited actions;
- `HOST_STOP` — the execution platform suspends/terminates the Agent or runtime/tool budget ends.

Do not invent work merely to avoid a legitimate stop condition.

## Important limitation: Git cannot wake a suspended Agent

The repository can enforce durable coordination and continuous behavior **while the Agent session is alive**. It cannot force ChatGPT/Work/Codex or another host platform to wake a session after the host has suspended or terminated it.

For a host/runtime that supports a long-running process, optional waiting mode is:

```bash
python scripts/next_task.py \
  --watch \
  --claim \
  --agent-id agent-<UTC>-<random> \
  --poll-seconds 60
```

This waits for eligible work, but host suspension can still terminate the process. Durable Git state makes the project resumable by the next Agent.

## Immediate task discovery

Run:

```bash
python scripts/next_task.py --list
```

The script combines:

1. global/legacy tasks from `coordination/WORK_QUEUE.jsonl`;
2. dynamic per-Pilot-case streaming tasks generated from `reports/pilot_selection.json`;
3. `coordination/claims/`;
4. `coordination/completed/`;
5. `coordination/ready/`.

Streaming IDs use:

```text
S-COLLECT-PILOT-E001
S-ALIGN-PILOT-E001
S-AUDIT-PILOT-E001
```

Each case progresses independently.

## Claiming work

Choose a unique Agent ID, for example:

```text
agent-20260913T001500Z-a17f
```

Claim the highest-priority eligible task:

```bash
python scripts/next_task.py \
  --claim \
  --agent-id agent-20260913T001500Z-a17f
```

Or claim a specific eligible task:

```bash
python scripts/next_task.py \
  --claim \
  --task S-ALIGN-PILOT-E001 \
  --agent-id agent-20260913T001500Z-a17f
```

A v2 claim records:

```json
{
  "workflow_mode": "continuous-worker-v2",
  "continue_after_finish": true
}
```

The claim is globally effective only when visible on `main`. Commit/push it immediately before doing expensive work. If another Agent wins the race, remove the losing local claim, refresh `main`, and claim another task instead of waiting.

Agents using the GitHub API directly should atomically create `coordination/claims/<TASK_ID>.json`; an existing file means the claim was lost.

## Finish and immediately continue

First commit/push the real outputs. Then create completion/readiness metadata:

```bash
python scripts/next_task.py \
  --finish S-ALIGN-PILOT-E001 \
  --agent-id agent-20260913T001500Z-a17f \
  --outputs data/live_segments/2017/LIVE_20170523_001.jsonl \
  --validation "verified provenance, monotonic alignment, no invented end times"
```

For streaming collection tasks, also provide the canonical live ID:

```bash
python scripts/next_task.py \
  --finish S-COLLECT-PILOT-M001 \
  --agent-id agent-... \
  --live-id LIVE_20200323_001 \
  --outputs ... \
  --validation "..."
```

After pushing completion/readiness files, immediately refresh and claim the next task:

```bash
python scripts/next_task.py --claim --agent-id <same-agent-id>
```

## Existing legacy batch Agents: early downstream unlock

Grandfathered legacy batch owners do not have to abandon their batch. They may unlock downstream work case-by-case while continuing the batch.

After one case inside a legacy batch is genuinely complete:

```bash
python scripts/next_task.py \
  --mark-ready collection \
  --case-id PILOT-M001 \
  --agent-id <legacy-claim-owner> \
  --live-id LIVE_20200323_001 \
  --outputs ... \
  --validation "source identity and provenance verified"
```

This creates:

```text
coordination/ready/collection/PILOT-M001.json
```

and immediately allows another Agent to claim `S-ALIGN-PILOT-M001`, while the original Middle batch Agent continues its remaining cases.

This preserves existing work and removes downstream waiting.

## Streaming pipeline

Preferred unit: one livestream/Pilot case, or a very small non-overlapping micro-batch.

```text
COLLECT + IDENTITY
        ↓
collection readiness
        ↓
ALIGN
        ↓
alignment readiness
        ↓
AUDIT
        ↓
audit readiness
```

Readiness files are independent per case:

```text
coordination/ready/collection/<PILOT_CASE_ID>.json
coordination/ready/alignment/<PILOT_CASE_ID>.json
coordination/ready/audit/<PILOT_CASE_ID>.json
```

Do not force one case to wait for unrelated cases.

## Stage requirements

### COLLECT + IDENTITY

Preserve real public evidence only:

- canonical `LIVE_YYYYMMDD_NNN` only when identity evidence supports it;
- source URLs and source-side page/video/post IDs;
- platform IDs only when actually known;
- title/date/duration only when supported;
- curated / ASR / mixed transcript provenance separately;
- cross-source identity evidence and conflicts;
- retrieval/verification timestamps.

Never invent source absence, IDs, timestamps, duration, FPS, or merge decisions.

Prefer per-live/per-case files so Agents do not append to the same large JSONL.

### ALIGN

Start as soon as that case is collection-ready.

Priority:

1. explicit curated/source timestamp;
2. GHOT public ASR/time axis + monotonic fuzzy alignment;
3. local ASR only when public timing is inadequate;
4. manual playback review for unresolved/high-value segments.

Preserve:

```text
text_curated
text_asr
start_sec
end_sec
curated_source_id
asr_source_id
time_source_id
alignment_method
alignment_quality
playback_verified
review_status
```

Do not invent `end_sec`, FPS, frame numbers, or playback verification.

### AUDIT

Audit begins incrementally after each case is aligned. Do not wait for all 27 cases.

Real playback audit should record at minimum:

- `segment_id`;
- `live_id`;
- source URL used for playback;
- expected `start_sec`;
- observed position;
- timing error seconds;
- correct livestream/date/text provenance;
- merge correctness;
- verifier timestamp and notes.

The Pilot still requires at least 60 real segment audits in aggregate.

## Database behavior

`data/` JSON/JSONL is the Git source of truth.

`database/Miles-Guo_public_archive.sqlite3` is a rebuildable artifact. Do not serialize collection/alignment work behind SQLite.

When safe after meaningful data changes:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

The final SQLite/FTS gate is aggregate validation, not a blocker for per-case work.

## Atomic claim and stale takeover

No Agent may start a new queued work unit before a successful claim exists.

If the desired claim already exists:

1. do not overwrite it;
2. refresh repository state;
3. choose another eligible task;
4. keep working rather than waiting.

Stale-claim takeover rules are in `coordination/README.md`. Do not steal an active claim just because its Agent is not visible in the UI.

## Scope and naming

- Only modify `witnessGIT/Miles-Guo_public_archive`.
- Never modify `witnessGIT/movie_production` or another repository for this task.
- Official project name: `Miles-Guo_public_archive`.
- Official database path: `database/Miles-Guo_public_archive.sqlite3`.
- Archive First, Application Second.
- Core operation must remain usable with zero-cost/local/open tooling; paid APIs/services cannot be mandatory.

## Core archive discipline

- One livestream has one canonical internal `live_id` and may have many source records.
- Preserve provenance and conflicts; never silently overwrite them.
- Preserve curated text and ASR separately.
- Seconds are the primary media locator; frames are auxiliary only.
- Every datum must remain traceable to source site, URL, retrieval/verification state, and third-party ID where available.
- Publicly accessible content only; low request rates and caching; no bypass of login/CAPTCHA/paywall/access control/DRM.
- Never commit full videos, large audio, model weights, cache, or FFmpeg intermediates.
- Do not begin `FULL_ARCHIVE` merely because collection works. `P10-PILOT-DECISION` remains the final Pilot decision gate.

## Definition of useful progress

A useful Agent run leaves durable source-backed output, such as:

- one completed source collection case;
- one per-live alignment result;
- one real playback audit set;
- one conflict record;
- one schema/build/validation fix required by real data;
- one readiness/completion record that immediately unlocks downstream work.

Pure planning is not completion when eligible executable work exists.

# Miles-Guo_public_archive

## Step 0 — resolve permissions before doing anything

This repository uses three machine-readable policies:

```text
continuous-worker-v2
claim-protocol-v2
agent-permissions-v1
```

Read first, in this order:

1. `coordination/AGENT_PERMISSIONS.json`
2. `coordination/AGENT_PERMISSIONS.md`
3. `AGENTS.md`
4. `coordination/WORKFLOW.json`
5. `coordination/CONTINUOUS_WORKER_V2.md`
6. `coordination/CLAIM_PROTOCOL_V2.md`
7. `coordination/README.md`
8. `coordination/WORK_QUEUE.jsonl`
9. `docs/CURRENT_TASK.md`
10. `docs/PROJECT_REQUIREMENTS.md`
11. `docs/NAMING_AND_WORKFLOW.md`
12. relevant current `data/`, `docs/`, `reports/`, `schema/`, `tests/`, `coordination/claims/`, `coordination/completed/`, `coordination/ready/`, and `coordination/bug_reports/`

Do not rely on chat history, memory, or another Agent's summary instead of Git state.

### Admin vs worker

Administrative GitHub login:

```text
witnessGIT
```

An Agent may act as `admin` only when its authenticated GitHub login is verified as exactly `witnessGIT`, or when the repository owner explicitly grants an admin exception in the current interaction.

Every other account is a `worker`. If identity cannot be verified, default to `worker`.

A worker may execute valid claimed business tasks and write the task's own durable business outputs plus its own claim/completion/readiness records.

A worker MUST NOT fix repository bugs or modify the protected control plane, including:

```text
AGENTS.md
START_HERE.md
coordination/AGENT_PERMISSIONS.json
coordination/AGENT_PERMISSIONS.md
coordination/CONTINUOUS_WORKER_V2.md
coordination/CLAIM_PROTOCOL_V2.md
coordination/WORKFLOW.json
coordination/WORK_QUEUE.jsonl
coordination/README.md
scripts/
schema/
.github/
```

When a worker discovers a bug, schema mismatch, CI failure, workflow defect, claim-system defect, or control-plane inconsistency, it must create a NEW immutable bug report under:

```text
coordination/bug_reports/
```

and must not repair the protected files itself. The worker should preserve evidence, avoid unsafe writes for the affected task, and continue another independent eligible business task when possible.

Only an admin Agent may investigate/modify/resolve those bug reports and repair project machinery.

## Mandatory continuous operating mode

Any Agent entering the repository must discover work, claim it, execute it, validate it, finish it, and immediately continue to the next eligible task without waiting for an unrelated batch.

Existing valid claims are grandfathered: do not interrupt, rename, steal, duplicate, or repartition a task merely because workflow rules changed. Existing owners finish current work under the valid claim; subsequent claims follow current policy.

Default loop:

```text
resolve role
↓
read repository state
↓
python scripts/next_task.py --list
↓
claim one eligible task
↓
push the claim immediately
↓
execute real work allowed by the Agent role
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

Finishing one task, one livestream, one micro-batch, or losing one claim race is not a stop condition.

A worker encountering a bug reports it instead of fixing it; reporting one bug is also not automatically a stop condition when other independent business tasks remain.

## Stop conditions

A continuous worker stops only for a documented reason:

- `PROJECT_COMPLETE` — no authorized work remains in the current phase;
- `USER_RECALL` — the user explicitly pauses/recalls/redirects the Agent;
- `NO_ELIGIBLE_WORK` — every unfinished task is currently claimed or genuinely blocked;
- `HUMAN_DECISION_REQUIRED` — continuing requires an unsupported guess or destructive decision;
- `SAFETY_OR_ACCESS_BLOCK` — continuing requires bypassing access controls or prohibited actions;
- `GITHUB_WRITE_ERROR` — only after bounded verification proves the failure is not a normal claim race;
- `HOST_STOP` — the execution platform suspends/terminates the Agent or runtime/tool budget ends.

`CLAIM_RACE_LOST` is explicitly not a stop condition.

## Task discovery and claiming

Run:

```bash
python scripts/next_task.py --list
```

The task runner combines global/legacy tasks, dynamic per-Pilot-case tasks, `claims/`, `completed/`, and `ready/`.

Streaming IDs use:

```text
S-COLLECT-PILOT-E001
S-ALIGN-PILOT-E001
S-AUDIT-PILOT-E001
```

Each case progresses independently.

Choose a unique Agent ID and claim an eligible task:

```bash
python scripts/next_task.py \
  --claim \
  --agent-id agent-<UTC>-<random>
```

The runner preserves priority bands while dispersing Agents across same-priority candidates using `agent_id`. A new claim records the current workflow and claim protocol.

A claim is globally effective only when visible on `main`. Commit/push it before doing expensive work.

## Mandatory GitHub API 422 classification

Agents using GitHub `create_file` directly MUST follow `coordination/CLAIM_PROTOCOL_V2.md`.

A `create_file` HTTP `422` is not automatically a GitHub write outage.

```text
create coordination/claims/<TASK_ID>.json
        |
        +-- success --> CLAIM_SUCCESS
        |
        +-- 422 --> fetch exact claim path
                       |
                       +-- exists --> CLAIM_RACE_LOST
                       |             --> refresh state
                       |             --> try another eligible task
                       |
                       +-- absent --> refresh + bounded retry
                                      --> only then GITHUB_WRITE_ERROR
```

If another Agent won the claim race, do not overwrite its claim and do not touch that task's business data. Refresh and claim another task.

## Finish and immediately continue

First commit/push the real outputs. Then finish the task with real validation evidence:

```bash
python scripts/next_task.py \
  --finish <TASK_ID> \
  --agent-id <same-agent-id> \
  --outputs <paths...> \
  --validation "what was actually verified"
```

For streaming collection tasks, also provide the canonical live ID when supported by evidence.

After pushing completion/readiness metadata, refresh and claim the next task.

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
audit evidence
```

Different cases should not wait for unrelated cases.

### COLLECT + IDENTITY

Preserve real public evidence only. Never invent source absence, IDs, timestamps, duration, FPS, or merge decisions. One livestream uses one canonical internal `live_id` and may have multiple source records.

### ALIGN

Priority:

1. explicit curated/source timestamp;
2. GHOT public ASR/time axis + monotonic fuzzy alignment;
3. local ASR only when public timing is inadequate;
4. manual playback review for unresolved/high-value segments.

Preserve curated text and ASR separately. Do not invent `end_sec`, FPS, frame numbers, playback verification, or timing accuracy.

### AUDIT

Audit begins incrementally after alignment. The Pilot still requires at least 60 **real playback-checked** segments in aggregate. An audit attempt with unavailable playback may be recorded as durable evidence, but it contributes zero qualifying checks and must never be counted as a timing pass.

## Database behavior

`data/` JSON/JSONL is the Git source of truth.

`database/Miles-Guo_public_archive.sqlite3` is a rebuildable artifact. When safe after meaningful data changes:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

Workers may run these commands for validation, but if they reveal a bug or contract mismatch the worker reports it; workers do not patch build scripts/schema/CI to make the failure disappear.

## Scope and core archive discipline

- Only modify `witnessGIT/Miles-Guo_public_archive` for this project.
- Official project name: `Miles-Guo_public_archive`.
- Official database path: `database/Miles-Guo_public_archive.sqlite3`.
- Archive First, Application Second.
- Preserve provenance and conflicts; never silently overwrite them.
- Seconds are the primary media locator; frames are auxiliary only.
- Every datum must remain traceable to source site, URL, retrieval/verification state, and third-party ID where available.
- Publicly accessible content only; no bypass of login/CAPTCHA/paywall/access control/DRM.
- Never commit full videos, large audio, model weights, cache, or FFmpeg intermediates.
- Do not begin `FULL_ARCHIVE` merely because collection works. `P10-PILOT-DECISION` remains the final Pilot decision gate.

## Definition of useful progress

For a worker, useful progress is source-backed business output: collection, alignment, audit evidence, conflict evidence, readiness/completion metadata, or a properly filed bug report when a bug blocks a task.

For an admin, useful progress additionally includes reviewing/resolving bug reports and repairing repository machinery with validation.

Pure planning is not completion when eligible executable work exists.

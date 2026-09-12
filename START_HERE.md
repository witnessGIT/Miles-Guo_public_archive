# Miles-Guo_public_archive Agent Entry Point

## External prompt contract

An external Agent does **not** need a copied task specification.

The minimal prompt is sufficient:

```text
进入这个项目并开始工作：
https://github.com/witnessGIT/Miles-Guo_public_archive
```

The repository is the authoritative execution context. Do not ask the user to repeat requirements already stored here.

## Step 0 — resolve Agent role before changing anything

Read:

```text
coordination/AGENT_PERMISSIONS.json
coordination/AGENT_PERMISSIONS.md
```

Administrative GitHub login:

```text
witnessGIT
```

If the authenticated GitHub login is verified as `witnessGIT`, the Agent may act as `admin`. Every other account is a `worker`. If identity cannot be verified, default to `worker`.

Worker rule:

```text
worker = execute claimed project tasks + submit bug reports
worker != fix bugs / modify control plane
```

A worker discovering a bug creates a new immutable report under:

```text
coordination/bug_reports/
```

and leaves the fix to an admin Agent.

Admin rule:

```text
admin = may execute project tasks + review/fix bug reports + modify protected control plane
```

Admin Agents should review open bug reports before ordinary work when a bug blocks correctness or other Agents.

## Required bootstrap

Read and follow, in order:

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
12. `docs/MEDIA_AUDIT.md`
13. current `claims/`, `completed/`, `ready/`, `bug_reports/`, `playback_attempts/`, data and reports relevant to the next task

## First command — classify by role, task type and runtime capability

Worker / unknown identity:

```bash
python scripts/project_status.py
```

Verified `witnessGIT` admin:

```bash
python scripts/project_status.py --role admin
```

If the runtime can genuinely inspect decoded clip/frame/audio content and determine observed content position, add:

```bash
--content-inspection-capable
```

Do **not** pass that flag merely because shell commands or ffmpeg can execute.

The classifier separates four task types:

| Task type | Examples | Media playback required? | Who may do it? |
|---|---|---:|---|
| `ordinary_business` | collection, alignment, source/transcript audit, data validation | No, unless explicitly stated | worker/admin |
| `real_playback` | `P9-PLAYBACK-*` decoded-media timing checks | **Yes**: ffmpeg + ffprobe + actual content inspection | playback-capable worker/admin |
| `gate_or_report` | `P9-AUDIT-60`, `P10-PILOT-DECISION`, aggregate gates/reports | No replay required once prerequisites pass | worker/admin |
| `admin_control` | bug fixes, scripts/schema/CI/workflow/control-plane repair | No playback requirement by default | **admin only** |

This distinction is mandatory. Lack of Playback capability does **not** block ordinary, gate/report, or admin-compatible work.

## Status meanings

The classifier may report:

```text
WORK_AVAILABLE
HOST_STOP
ROLE_STOP
WAIT_FOR_ACTIVE_CLAIMS
WAIT_FOR_DEPENDENCY
NO_ELIGIBLE_WORK
```

Interpret them narrowly:

- `WORK_AVAILABLE`: this session has at least one compatible task now.
- `HOST_STOP`: the remaining **unclaimed** work that this session could otherwise take is real Playback, Pilot-60 has not passed, and this runtime cannot honestly perform decoded-media inspection. This is a **session capability limit**, not repository-wide no-work.
- `ROLE_STOP`: project work remains but it is admin-only and this session is a worker.
- `WAIT_FOR_ACTIVE_CLAIMS`: work exists but all relevant work is currently held by other Agents.
- `WAIT_FOR_DEPENDENCY`: project work exists but this session has no currently executable compatible task.
- `NO_ELIGIBLE_WORK`: no currently relevant project work remains across ordinary, playback, gate transition, or open admin bug queues.

An admin Agent MUST NOT report `HOST_STOP` merely because Playback is unavailable while open admin bug reports or other compatible non-media work remain.

## Critical Pilot-60 transition rule

`P9-AUDIT-60` is blocked by `P9-PLAYBACK-GATE` until real qualifying playback evidence satisfies the acceptance thresholds.

Run:

```bash
python scripts/audit_gate.py --json
```

Only canonical-crosschecked durable records under `data/playback_audits/` count. Transcript timestamps, source-page timestamps, ASR anchors, ordinary `S-AUDIT-*` completion markers, and successful ffmpeg decoding without content inspection do not count.

When `pilot60_pass=true`, the acceptance path changes immediately:

```text
Pilot-60 passed
    ↓
seal P9-PLAYBACK-GATE
    ↓
P9-AUDIT-60
    ↓
P10-PILOT-DECISION
```

Seal with:

```bash
python scripts/playback_queue.py --seal-gate --agent-id <agent-id>
```

**Important:** once Pilot-60 has passed, extra unreviewed playback cases do not keep the acceptance path in `HOST_STOP`. Sealing the gate and executing P9/P10 are non-playback tasks. A session without media capability may continue through those stages when they become eligible.

## Ordinary queue

Discover ordinary business and gate/report tasks with:

```bash
python scripts/next_task.py --list
```

Claim, execute, validate, commit/push, finish, refresh state, and continue.

## Real Playback queue

Real decoded-media verification is separate and retryable:

```bash
python scripts/playback_queue.py --list
```

Only a runtime with `ffmpeg` + `ffprobe` **and actual decoded-content inspection ability** may claim:

```bash
python scripts/playback_queue.py \
  --claim \
  --content-inspection-capable \
  --agent-id agent-<UTC>-<random>
```

The flag is an auditable assertion, not a bypass. If the runtime can decode but cannot inspect clip/frame/audio content and determine the observed position, it must not claim Playback work.

A blocked Playback attempt must preserve `counts_toward_pilot_60=false`, release the claim, and allow a later capable Agent to retry.

## Admin bug queue

Workers report bugs under:

```text
coordination/bug_reports/
```

Workers do not repair them.

Verified `witnessGIT` admin Agents treat unresolved or malformed bug reports as actionable admin work. Open admin bugs therefore count as project work and prevent an admin session from incorrectly declaring `HOST_STOP` or repository-wide `NO_ELIGIBLE_WORK` when it can still perform the repair.

## P9 / P10 capability rule

`P9-AUDIT-60` and `P10-PILOT-DECISION` are `gate_or_report` tasks.

They do **not** require the executing Agent to personally replay media once the real Playback prerequisites have already passed and durable evidence exists. They may still require repository reads, validation, report generation, and normal task claiming.

`P10-PILOT-DECISION` remains blocked until P9 completes. FULL_ARCHIVE remains locked unless P10 records an explicit machine-readable:

```text
full_archive_decision=YES
```

`NO`, missing, or invalid decision values do not authorize FULL_ARCHIVE.

## Mandatory claim-race behavior

A failed atomic claim is not automatically a GitHub outage.

For GitHub `create_file` claim attempts:

```text
success
  -> fetch exact claim -> verify owner -> work

422 / 409
  -> fetch exact claim from fresh main
     -> exists: CLAIM_RACE_LOST -> refresh -> try another task
     -> absent: refresh main/task state -> short backoff -> bounded retry
```

A single `422` or `409` MUST NOT stop the worker. `409` often means `main` moved between read and write. Never force-overwrite concurrent work.

See `coordination/CLAIM_PROTOCOL_V2.md` for the authoritative procedure.

## Repository authority

A minimal external prompt authorizes execution of the **currently authorized repository phase** only. It does not authorize bypassing gates or starting an unauthorized later phase.

Current Git state and repository policy beat stale chat summaries or old copied prompts.

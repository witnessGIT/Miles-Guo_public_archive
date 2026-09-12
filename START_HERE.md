# Miles-Guo_public_archive Agent Entry Point

## External prompt contract

An external Agent does **not** need a copied task specification.

The minimal prompt is sufficient:

```text
进入这个项目并开始工作：
https://github.com/witnessGIT/Miles-Guo_public_archive
```

The repository is the authoritative execution context.

After entering the repository, the Agent must determine everything else from Git state and project files, including:

- its Agent role and permissions;
- project purpose and scope;
- current authorized phase;
- current completed work;
- active claims;
- currently eligible work;
- task priority;
- collection/alignment/audit/playback rules;
- source and naming rules;
- quality gates;
- continuous-worker behavior;
- claim-race handling;
- bug-report behavior;
- stop conditions.

Do not ask the user to repeat requirements already stored in the repository.

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

If the authenticated GitHub login is verified as `witnessGIT`, the Agent may act as `admin`.

Every other account is a `worker`. If account identity cannot be verified, default to `worker`.

A worker performs claimed business tasks only. A worker MUST NOT fix bugs or modify the control plane (`scripts/`, `schema/`, `.github/`, workflow/task orchestration, permission rules). When a worker discovers a bug, it creates a new immutable report under:

```text
coordination/bug_reports/
```

and leaves the fix to an admin Agent. It should continue another safe independent task when possible.

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

Admin Agents should check open `coordination/bug_reports/` before ordinary business work when a bug blocks correctness or other Agents.

## First command: classify repository state

Before deciding that there is work, no work, a host limitation, or a Pilot decision boundary, run:

```bash
python scripts/project_status.py
```

This command evaluates both the ordinary task queue and the real-playback queue, together with the Pilot-60 gate and P9/P10 state.

A runtime that can genuinely inspect decoded clip/frame/audio content may additionally run:

```bash
python scripts/project_status.py --content-inspection-capable
```

The flag is an auditable capability declaration. Do not pass it merely because shell commands or ffmpeg can execute.

The status classifier is the authoritative distinction between:

```text
WORK_AVAILABLE
HOST_STOP
NO_ELIGIBLE_WORK
```

Important: if ordinary tasks are empty but real playback work remains, repository-wide `NO_ELIGIBLE_WORK` is false. A runtime without playback capability may classify only its own session as `HOST_STOP`.

## Work discovery has two coordinated queues

First discover ordinary collection/alignment/source-audit work:

```bash
python scripts/next_task.py --list
```

Real decoded-media playback verification is a separate retryable queue:

```bash
python scripts/playback_queue.py --list
```

If the runtime has `ffmpeg` + `ffprobe` **and can actually inspect generated clip/frame/audio evidence**, playback-capable Agents may claim missing playback work only with the explicit capability declaration:

```bash
python scripts/playback_queue.py \
  --claim \
  --content-inspection-capable \
  --agent-id agent-<UTC>-<random>
```

The flag is an auditable assertion, not a bypass. Do **not** pass it when the runtime can execute media commands but cannot inspect decoded content and determine the observed content position. Transcript/source-page timestamp checking is not a substitute.

An ordinary `S-AUDIT-*` task may finish with zero qualifying playback checks; that preserves useful source/timeline evidence but does not make the case complete for Pilot-60. Later playback-capable work adds durable records under `data/playback_audits/` without rewriting that history.

`P9-AUDIT-60` is intentionally blocked by `P9-PLAYBACK-GATE`. The sentinel may be created only after:

```bash
python scripts/audit_gate.py --json
```

reports `pilot60_pass=true`, followed by:

```bash
python scripts/playback_queue.py --seal-gate --agent-id <agent-id>
```

Therefore 60 audit markers, 60 webpage timestamps, or 60 successful ffmpeg decodes without content inspection cannot unlock P9.

If ordinary work is empty but playback work remains, that is **not repository-wide `NO_ELIGIBLE_WORK`**. A runtime that lacks media execution or content-inspection capability may classify only its own session as `HOST_STOP` / runtime capability limitation. `SAFETY_OR_ACCESS_BLOCK` is reserved for cases where progress would require bypassing login, CAPTCHA, paywall, DRM, or another access control.

Claim an eligible task, execute it, validate it, commit/push it, finish it, then refresh **both** queues and continue.

Under `continuous-worker-v2`, completing one task or batch is not a stop condition. Continue until a documented stop condition in the repository applies.

## Pilot acceptance blocker versus backlog

The Pilot acceptance path is currently controlled by real playback-position evidence and the P9/P10 gates. Missing documentation or future collection/export tooling must not be used as a substitute for Pilot-60 evidence and must not be used to bypass P9.

Backlog documentation/tooling may be completed when independently claimable, but it does not authorize:

```text
P9-AUDIT-60 completion
P10-PILOT-DECISION start
FULL_ARCHIVE start
```

Only the real gate chain may do that.

## Mandatory claim-race behavior

A failed atomic claim is not automatically a GitHub outage.

For Agents using GitHub `create_file` directly:

```text
create claim
   |
   +-- success --> fetch exact claim --> verify owner --> work
   |
   +-- HTTP 422 or HTTP 409
           |
           +-- fetch exact claim path from fresh main
                   |
                   +-- exists --> CLAIM_RACE_LOST --> refresh --> try another task
                   |
                   +-- absent --> refresh main + task state
                                  --> short backoff
                                  --> bounded retry
                                  --> only then consider GITHUB_WRITE_ERROR
```

A `409` commonly means `main` moved between the read and write. It is a retryable branch race when the target claim is still absent; it is not permission to overwrite or force-push concurrent work.

A single `422` or `409` MUST NOT stop the worker or produce "the execution chain must stop at the claim boundary".

If another Agent won the claim race, do not overwrite the claim and do not touch that task's business data. Refresh state and claim another eligible task immediately.

See `coordination/CLAIM_PROTOCOL_V2.md` for the authoritative procedure.

## Repository authority

If an external prompt only says to enter this repository and start work, treat that as authorization to execute the **currently authorized repository phase**, not as authorization to bypass project gates or begin an unauthorized later phase.

Current and future Agents must prefer repository state over stale chat summaries or old copied prompts.

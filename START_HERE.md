# Miles-Guo_public_archive Agent Entry Point

## External prompt contract

A minimal external prompt is sufficient:

```text
进入这个项目并开始工作：
https://github.com/witnessGIT/Miles-Guo_public_archive
```

The repository is the authoritative execution context. Do not ask the user to repeat requirements already stored here.

## Repository-owner standing directive

The owner authorizes continuous multi-Agent execution through two contribution modes:

```text
A. Agent has direct repository write permission
   -> claim on main
   -> execute
   -> validate
   -> push claimed outputs directly to main
   -> finish
   -> claim next task

B. Agent does NOT have direct repository write permission
   -> refresh main + inspect open PRs
   -> choose an eligible unreserved task
   -> fork or use an available personal branch
   -> open a task PR containing TASK_ID + agent_id
   -> keep pushing task work to that same PR branch
   -> validate and make the PR merge-ready
   -> after merge, refresh and reserve the next task the same way
```

For valid business/video-archive work:

- no repeated per-task approval from the owner is required;
- direct-write Agents do not need a PR;
- no-write Agents are explicitly authorized to contribute through PRs;
- an open valid task PR is a soft reservation and other Agents should avoid duplicating that task;
- only merged PR work becomes authoritative main-branch completion state;
- do not stop after one task, livestream, case, or micro-batch;
- a lost claim/reservation race means refresh and choose another task;
- preserve all quality gates and never fabricate evidence merely to accelerate completion.

The final owner intent is **not merely to finish the Pilot**. Preserve the Pilot quality gates, and after they pass continue into `FULL_ARCHIVE` until all eligible public video archive work is complete.

## No-write Agent PR protocol

Before starting work, a no-write Agent must check both:

1. current `main` claims/completions/readiness for the intended `TASK_ID`;
2. currently open pull requests for an existing reservation of the same `TASK_ID`.

A no-write Agent must not duplicate a task already claimed on `main` or already reserved by an earlier valid open PR.

The PR must identify at minimum:

```text
TASK_ID: <repository task id>
agent_id: <stable agent id>
mode: external-pr-worker
```

Recommended PR title:

```text
[TASK <TASK_ID>] <short task description> — <agent_id>
```

The Agent should open the PR early, then continue committing the actual task outputs to the same PR branch. The PR itself is the external soft reservation. If the PR closes without merge, the reservation is released. If merged, `main` becomes authoritative and the Agent must refresh before taking another task.

A no-write Agent must still obey worker boundaries: it may contribute ordinary claimed business/archive outputs, but must not use a PR to bypass protected control-plane restrictions or manufacture service-generated playback evidence/audits.

## Step 0 — resolve role

Read first:

1. `coordination/AGENT_PERMISSIONS.json`
2. `coordination/AGENT_PERMISSIONS.md`
3. `AGENTS.md`
4. `coordination/WORKFLOW.json`
5. `coordination/CONTINUOUS_WORKER_V2.md`
6. `coordination/CLAIM_PROTOCOL_V2.md`
7. `coordination/README.md`
8. `coordination/WORK_QUEUE.jsonl`
9. `docs/PROJECT_REQUIREMENTS.md`
10. `docs/NAMING_AND_WORKFLOW.md`
11. `docs/MEDIA_AUDIT.md`
12. current claims/completions/readiness/bug reports/playback requests/evidence relevant to the next task

Administrative GitHub login: `witnessGIT`. Verified `witnessGIT` Agents are `admin`; every other/unknown identity is a `worker`.

```text
worker = execute claimed/reserved project tasks + use repository services + report bugs + continue
admin  = worker capabilities + repair/maintain project machinery
```

Workers MUST NOT modify `scripts/`, `schema/`, `tests/`, `.github/`, workflow policy, permissions or other protected control-plane files. Bugs go to `coordination/bug_reports/` for an admin Agent. This restriction protects shared machinery; it does not require workers to wait for approval before ordinary archive work.

## First status command

Worker / unknown identity:

```bash
python scripts/project_status.py
```

Verified admin:

```bash
python scripts/project_status.py --role admin
```

Local `--content-inspection-capable` is now only an optional fallback. **Ordinary Agents do not need local ffmpeg, ffprobe, yt-dlp, Whisper, or a graphical video player when the repository Playback Evidence Service is present.**

## Current Pilot acceptance chain

Historical task identities `P9-AUDIT-60` and `P10-PILOT-DECISION` are legacy/superseded audit history only.

Current chain:

```text
P9-PLAYBACK-PILOT-*
        ↓
repository Playback Evidence Service
        ↓
data/playback_evidence/<CASE>/<SEGMENT>/evidence.{json,md}
        ↓
worker reads evidence and submits acceptance
        ↓
data/playback_audits/<CASE>/<SEGMENT>.json
        ↓
scripts/audit_gate.py => pilot60_pass=true
        ↓
P9-PLAYBACK-GATE
        ↓
P9-AUDIT-60-R2
        ↓
P10-PILOT-DECISION-R2
        ↓
FULL_ARCHIVE
        ↓
continue until all eligible public video archive work is complete
```

The owner has stated the standing intent to continue into FULL_ARCHIVE after required quality gates pass. `P10-PILOT-DECISION-R2` must still record the required machine-readable decision and may not bypass failed quality gates, but no additional owner confirmation is required merely to continue full-archive processing after the gates are satisfied.

## Task types

| Type | Examples | Who can execute? |
|---|---|---|
| `ordinary_business` | collection, alignment, source/transcript work | worker/admin; direct push or PR depending on GitHub permission |
| `real_playback` | `P9-PLAYBACK-*` | worker/admin through repository service; direct write is required for request/acceptance to reach main, or PR must be merged first |
| `gate_or_report` | P9/P10 R2 aggregate gates/reports | worker/admin once dependencies pass |
| `admin_control` | bug fixes, scripts/schema/CI/workflow | admin only |
| `legacy_record` | old P9/P10 | nobody; history only |

## Real Playback — preferred ordinary-Agent path

List/claim:

```bash
python scripts/playback_queue.py --list
python scripts/playback_queue.py --claim --agent-id agent-<UTC>-<random>
```

Playback claims use a six-hour renewable lease so a terminated chat session cannot reserve a
case forever. Every successful request/acceptance renews the lease. A continuing worker may run
`python scripts/playback_queue.py --heartbeat <CASE_ID> --agent-id <same-agent-id>`. Another worker
may use `--reclaim-expired <CASE_ID>` only after the repository reports the lease as expired; the
old claim is preserved as an immutable attempt record before replacement.

For each missing segment, choose a **public media URL already preserved in repository provenance** and submit the corresponding playback request. The GitHub Action `.github/workflows/playback-evidence-service.yml` validates identity/provenance, decodes real media, runs offline ASR/OCR and writes durable evidence. Evidence generation alone never counts toward Pilot-60.

After evidence appears, the worker MUST read it and only submit an acceptance if the decoded-media evidence really matches the canonical content. A worker must never manufacture service evidence or accept evidence it has not read.

## Pilot-60 quality rule

Only valid `data/playback_audits/**/*.json` records count. Source-page timestamps, transcript timestamps, ordinary `S-AUDIT-*` markers, or ffmpeg decode success without content evidence do not count.

When `scripts/audit_gate.py --json` reports `pilot60_pass=true`, seal `P9-PLAYBACK-GATE`, proceed through current P9/P10, then continue full archive work according to the standing owner directive.

## Stop-state rule

Because the repository supplies the preferred Playback execution environment, lack of local ffmpeg/player is normally **not** `HOST_STOP`. Lack of direct write permission is also **not** a project stop condition when the Agent can use the authorized PR path.

Valid stop states are limited to genuine `PROJECT_COMPLETE`, `USER_RECALL`, true `NO_ELIGIBLE_WORK`, unavoidable `HUMAN_DECISION_REQUIRED`, `SAFETY_OR_ACCESS_BLOCK`, verified inability to contribute through either direct-write or PR path, or true `HOST_STOP`.

## Claim / reservation races

Direct-write Agents use the atomic claim protocol. No-write Agents use the PR soft-reservation protocol. Before starting any task, check both main claims and open task PRs.

Never force-overwrite concurrent work. Current Git state and open PR state beat stale chat summaries or copied prompts.

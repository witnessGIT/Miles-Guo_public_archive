# Miles-Guo_public_archive

## Owner standing directive — continuous multi-Agent execution

The repository owner explicitly authorizes **all Agents** to keep contributing to this archive through the strongest GitHub path available to them.

### Mode A — Agent has direct repository write permission

```text
read fresh Git state
→ claim one eligible task
→ push claim directly
→ execute real archive work
→ validate
→ push claimed outputs directly to main
→ complete / publish readiness
→ refresh
→ claim next eligible task
→ repeat
```

### Mode B — Agent does NOT have direct repository write permission

```text
read fresh main state
→ inspect current claims/completions and open PRs
→ choose one eligible unreserved task
→ fork or use an available personal branch
→ open a task PR containing TASK_ID + agent_id
→ continue committing the task outputs to that same PR
→ validate and make the PR merge-ready
→ after merge, refresh repository state
→ reserve the next eligible task through another PR
→ repeat
```

For valid business/video-archive work:

- no repeated per-task owner approval is required;
- direct-write Agents do not need PRs;
- no-write Agents are explicitly authorized to contribute through PRs;
- an open valid task PR is a **soft reservation** and other Agents should avoid duplicating the same `TASK_ID`;
- only merged PR work becomes authoritative `main` completion state;
- finishing one task, livestream, case or batch is not a stop condition;
- a claim/reservation race is not a stop condition;
- a non-blocking control-plane bug is reported, then the worker continues another eligible task;
- preserve all quality gates and never fabricate evidence merely to accelerate completion;
- after required Pilot gates pass, continue into `FULL_ARCHIVE` until all eligible public video archive work is complete.

## No-write PR protocol

Before starting a task, a no-write Agent must check both:

1. `main` branch claims/completions/readiness for the intended `TASK_ID`;
2. currently open pull requests for an earlier reservation of the same `TASK_ID`.

A no-write Agent must not duplicate a task already claimed on `main` or already reserved by an earlier valid open PR.

Every external task PR must identify at minimum:

```text
TASK_ID: <repository task id>
agent_id: <stable agent id>
mode: external-pr-worker
```

Recommended PR title:

```text
[TASK <TASK_ID>] <short task description> — <agent_id>
```

The Agent should open the PR early, then keep pushing the real task work to the same PR branch. If the PR closes without merge, its soft reservation is released. If merged, the Agent must refresh `main` and open PR state before selecting the next task.

A PR does not bypass worker restrictions. No-write workers still MUST NOT use PRs to modify protected control-plane paths, manufacture service-generated playback evidence/audits, or bypass repository quality gates.

## Step 0 — resolve permissions before doing anything

This repository uses:

```text
continuous-worker-v2
claim-protocol-v2
agent-permissions-v2.3
repository-playback-evidence-v2
```

Read first, in order:

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
13. relevant current data/reports/claims/completions/readiness/bug reports/playback requests/evidence/open PRs

Do not rely on chat history or another Agent's summary instead of current Git and PR state.

## Admin vs worker

Administrative GitHub login: `witnessGIT`.

Verified `witnessGIT` Agents may act as `admin`. Every other/unknown account is a `worker`.

A worker may execute valid business/playback tasks through either direct-push mode or the authorized PR mode, depending on actual GitHub permission. Workers may write their own allowed business outputs/coordination records, submit playback requests and acceptances when those records reach `main`, and submit new immutable bug reports.

A worker MUST NOT fix repository bugs or modify protected control-plane paths, including `AGENTS.md`, `START_HERE.md`, core `coordination/` policy files, `scripts/`, `schema/`, or `.github/`.

Bugs go to:

```text
coordination/bug_reports/
```

Only an admin Agent repairs shared project machinery. This restriction is a concurrency-safety boundary, not a requirement for workers to wait for ordinary task approval.

## Mandatory continuous operating mode

Default logic:

```text
resolve role + contribution mode
→ read repository + open PR state
→ classify current work
→ claim on main OR PR-reserve one eligible task
→ execute real work allowed by role
→ validate and commit outputs
→ finish / publish readiness or merge-ready PR
→ refresh repository + PR state
→ take next eligible task
→ repeat
```

Finishing one task, one livestream, one micro-batch, losing one claim race, or lacking direct write permission is not by itself a stop condition.

If a worker discovers a control-plane bug that does not block all remaining work, it must report the bug through an allowed path, refresh task state, and continue another compatible task.

## Stop conditions

A worker stops only for a documented reason such as `PROJECT_COMPLETE`, `USER_RECALL`, real `NO_ELIGIBLE_WORK`, unavoidable `HUMAN_DECISION_REQUIRED`, `SAFETY_OR_ACCESS_BLOCK`, verified inability to contribute through either direct-write or PR path, or true `HOST_STOP`.

`CLAIM_RACE_LOST` and `PR_RESERVATION_RACE_LOST` are not stop conditions.

Because the repository contains a Playback Evidence Service, absence of local ffmpeg/player is normally **not HOST_STOP**. If repository Playback work is open and the service is available, ordinary workers can execute it through GitHub once their required request/acceptance records reach `main`.

## Task discovery and claiming

Ordinary/static tasks:

```bash
python scripts/next_task.py --list
```

Playback tasks:

```bash
python scripts/playback_queue.py --list
```

No-write Agents must additionally inspect currently open PRs before selecting a task.

Current Pilot gate identities:

```text
P9-AUDIT-60-R2
P10-PILOT-DECISION-R2
```

Historical `P9-AUDIT-60` and `P10-PILOT-DECISION` are superseded audit history and are never executable current tasks.

## Claim / reservation races

Direct-write Agents use the atomic claim protocol. No-write Agents use PR soft reservations.

```text
main claim exists -> task unavailable
valid earlier open task PR exists -> task soft-reserved/unavailable
race lost -> refresh -> choose another task
```

Never overwrite another Agent's claim and never duplicate an earlier valid open task PR.

## Streaming pipeline

```text
COLLECT + IDENTITY
→ collection readiness
→ ALIGN
→ alignment readiness
→ source/provenance AUDIT
→ real Playback Audit where required
→ Pilot-60 aggregate gate
→ current P9/P10 acceptance
→ FULL_ARCHIVE
→ all eligible public video archive work complete
```

### COLLECT + IDENTITY

Preserve real public evidence only. Never invent absence, IDs, timestamps, duration, FPS or merge decisions. One canonical livestream may have multiple source records.

### ALIGN

Priority:

1. explicit curated/source timestamp;
2. GHOT public ASR/time axis + alignment;
3. local ASR only when public timing is inadequate;
4. real Playback Audit for quality verification.

Keep curated text and ASR separate. Do not invent `end_sec`, FPS/frame numbers, playback verification or timing accuracy.

### Ordinary source/provenance AUDIT

`S-AUDIT-*` may validate sources/transcript/timestamps but may contribute zero real playback checks. Such completion never satisfies Pilot-60 by itself.

## Real Playback Audit — ordinary Agents can do it

Preferred execution mode:

```text
repository_evidence_service_v1
```

Workers do not need local ffmpeg, ffprobe, yt-dlp, Whisper or a graphical player.

For a Playback task, the required request/acceptance records must ultimately reach `main` before the repository service can treat them as authoritative inputs. Direct-write workers may push them directly; no-write workers may submit them by PR and continue once merged.

Evidence generation alone never counts. Worker acceptance without valid service evidence never counts. Source-page timestamps alone never count.

Detailed contracts are authoritative in `docs/MEDIA_AUDIT.md` and `START_HERE.md`.

## Pilot-60 gate

```bash
python scripts/audit_gate.py --json
```

Only valid canonical-crosschecked records under `data/playback_audits/` count.

Required:

```text
>= 60 qualifying real Playback checks
>= 90% within 3 seconds
>= 98% within 8 seconds
false merge rate approximately 0
```

When `pilot60_pass=true`, seal `P9-PLAYBACK-GATE`, proceed to `P9-AUDIT-60-R2` and `P10-PILOT-DECISION-R2`, then continue full-archive processing under the standing owner directive. Do not ask the owner again merely for permission to continue from a successful Pilot into FULL_ARCHIVE.

## Database behavior

`data/` JSON/JSONL is source of truth. `database/Miles-Guo_public_archive.sqlite3` is rebuildable:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

Workers may validate; if a bug/contract mismatch appears, report it instead of patching protected machinery, then continue other eligible work when possible.

## Scope and core archive discipline

- Only modify/contribute to `witnessGIT/Miles-Guo_public_archive` for this project.
- Official project name: `Miles-Guo_public_archive`.
- Official database path: `database/Miles-Guo_public_archive.sqlite3`.
- Archive First, Application Second.
- Preserve provenance and conflicts.
- Seconds are primary media locator; frames auxiliary only.
- Public content only; no bypass of login/CAPTCHA/paywall/DRM/access controls.
- Never commit full videos, large audio, model weights, caches or FFmpeg intermediates.
- Quality gates remain mandatory even though the owner has authorized continuous progression to full archive completion.

## Useful progress

For a worker: source-backed business output, a valid task PR, valid Playback request/evidence acceptance, alignment/audit evidence, readiness/completion metadata, or a properly filed bug report followed by continued compatible work.

For an admin: all worker progress plus validated repair of project machinery.

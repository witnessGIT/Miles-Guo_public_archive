# Miles-Guo_public_archive Continuous Worker v2

Project: `Miles-Guo_public_archive`  
Policy: `continuous-worker-v2`  
Claim protocol: `claim-protocol-v2`

## Goal

```text
ENTER REPOSITORY
  -> DISCOVER ELIGIBLE WORK
  -> CLAIM
  -> EXECUTE
  -> VALIDATE
  -> COMMIT/PUSH OUTPUTS
  -> FINISH / PUBLISH READINESS
  -> CLAIM NEXT TASK
  -> REPEAT
```

A worker does not intentionally stop after one successful task while other safe eligible work exists. Losing one claim race is not a stop condition.

## Platform limitation

Git/GitHub provides coordination, execution services and durable resume state, but cannot resurrect a host-suspended ChatGPT/Work/Codex session. Continuous behavior applies while the Agent session remains active.

## Effective scope / grandfather rule

The current policy applies to new claims. Existing valid claims remain owned by their current Agent and are not stolen or duplicated merely because workflow rules changed.

New claims contain:

```json
{
  "workflow_mode": "continuous-worker-v2",
  "claim_protocol": "claim-protocol-v2",
  "continue_after_finish": true
}
```

Finish-time prerequisite checks may still enforce newer safety/quality gates on an older claim. A grandfathered claim never authorizes bypassing a newly required acceptance dependency.

## Stop conditions

A v2 Agent stops only for a documented reason:

1. `PROJECT_COMPLETE`
2. `USER_RECALL`
3. genuine `NO_ELIGIBLE_WORK`
4. `HUMAN_DECISION_REQUIRED`
5. `SAFETY_OR_ACCESS_BLOCK`
6. verified `GITHUB_WRITE_ERROR`
7. true `HOST_STOP`

Finishing one task or losing one claim race is not a stop condition.

Because the repository now exposes a Playback Evidence Service, lack of **local** ffmpeg/player/media inspection is not by itself `HOST_STOP`. If unclaimed `P9-PLAYBACK-*` work exists and `.github/workflows/playback-evidence-service.yml` is available, ordinary workers can continue through repository requests/evidence/acceptances.

`HOST_STOP` for Playback is appropriate only when neither the repository service nor a valid local fallback is available to the current session.

## Claim-race recovery

Read `coordination/CLAIM_PROTOCOL_V2.md` before new claims. HTTP `422` or `409` from an atomic claim must be classified against fresh repository state.

```text
exact claim exists -> CLAIM_RACE_LOST -> refresh -> try another task
exact claim absent -> refresh/backoff -> bounded retry
```

Only repeated fresh failure with no race/staleness explanation becomes `GITHUB_WRITE_ERROR`.

## No-sleep rule

After completion, refresh and claim the next compatible task. If another Agent wins a claim race, choose another eligible candidate. If no task is eligible, report the exact repository state instead of inventing work.

## Ordinary and Playback work

Ordinary/static queue:

```bash
python scripts/next_task.py --list
```

Playback queue:

```bash
python scripts/playback_queue.py --list
```

Preferred Playback path for ordinary Agents:

```text
claim P9-PLAYBACK-*
 -> write coordination/playback_requests/<CASE>/<SEGMENT>.json
 -> repository GitHub Action decodes real media + offline ASR/OCR
 -> read data/playback_evidence/<CASE>/<SEGMENT>/evidence.{json,md}
 -> if evidence really matches, write coordination/playback_acceptances/<CASE>/<SEGMENT>.json
 -> service creates qualifying playback audit record
 -> finish case when all current timed segments qualify
```

Workers use this service but must not modify the service implementation. Bugs in it are reported to `coordination/bug_reports/` for an admin Agent.

## Streaming work

Preferred progression by case:

```text
COLLECT + IDENTITY
  -> collection readiness
ALIGN
  -> alignment readiness
SOURCE / PROVENANCE AUDIT
  -> audit readiness
REAL PLAYBACK AUDIT
  -> repository playback evidence + acceptance + qualifying record
```

Different cases advance independently. Aggregate tasks remain gates/reports rather than unnecessary global barriers.

## Durable resume state

Important state lives in Git:

```text
coordination/claims/
coordination/completed/
coordination/ready/
coordination/playback_requests/
coordination/playback_acceptances/
coordination/playback_attempts/
data/playback_evidence/
data/playback_audits/
data/
reports/
```

Temporary videos/audio/frames/models/caches do not belong in Git.

## Current Pilot end behavior

Historical `P9-AUDIT-60` and `P10-PILOT-DECISION` are superseded audit history only.

Current acceptance chain:

```text
valid real Playback evidence
 -> P9-PLAYBACK-GATE
 -> P9-AUDIT-60-R2
 -> P10-PILOT-DECISION-R2
```

A worker must not begin `FULL_ARCHIVE` unless current `P10-PILOT-DECISION-R2` explicitly records `full_archive_decision=YES` after all required quality gates pass.

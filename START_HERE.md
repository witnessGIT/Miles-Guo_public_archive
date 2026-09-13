# Miles-Guo_public_archive Agent Entry Point

## External prompt contract

A minimal external prompt is sufficient:

```text
进入这个项目并开始工作：
https://github.com/witnessGIT/Miles-Guo_public_archive
```

The repository is the authoritative execution context. Do not ask the user to repeat requirements already stored here.

## Repository-owner standing directive

The owner has already authorized all Agents that actually have GitHub write capability to work continuously on this archive.

```text
READ CURRENT GIT STATE
→ CLAIM ONE ELIGIBLE TASK
→ PUSH CLAIM DIRECTLY
→ EXECUTE REAL ARCHIVE WORK
→ VALIDATE
→ PUSH CLAIMED OUTPUTS DIRECTLY TO main
→ COMPLETE / PUBLISH READINESS
→ REFRESH
→ CLAIM NEXT ELIGIBLE TASK
→ REPEAT
```

For valid claimed business/video-archive work:

- no PR is required;
- no repeated per-task approval from the owner is required;
- do not stop after one task, one livestream, one case, or one micro-batch;
- a lost claim race means refresh and choose another task;
- a non-blocking control-plane bug means file a bug report and continue other eligible work;
- continue while the Agent session remains active until a real repository stop condition applies.

The final owner intent is **not merely to finish the Pilot**. Preserve the Pilot quality gates, and after they pass continue into `FULL_ARCHIVE` until all eligible public video archive work is complete. Do not lower or bypass playback/quality requirements to reach that goal.

Repository policy cannot grant GitHub access to an account that does not actually have write permission. GitHub authentication/authorization still applies.

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
worker = directly execute claimed project tasks + use repository services + report bugs + continue
admin  = worker capabilities + repair/maintain project machinery
```

Workers MUST NOT modify `scripts/`, `schema/`, `.github/`, workflow policy, permissions or other protected control-plane files. Bugs go to `coordination/bug_reports/` for an admin Agent. This restriction protects shared machinery; it does not require workers to wait for approval before ordinary claimed archive work.

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
| `ordinary_business` | collection, alignment, source/transcript work | worker/admin |
| `real_playback` | `P9-PLAYBACK-*` | worker/admin through repository service; local manual fallback optional |
| `gate_or_report` | P9/P10 R2 aggregate gates/reports | worker/admin once dependencies pass |
| `admin_control` | bug fixes, scripts/schema/CI/workflow | admin only |
| `legacy_record` | old P9/P10 | nobody; history only |

## Real Playback — preferred ordinary-Agent path

List/claim:

```bash
python scripts/playback_queue.py --list
python scripts/playback_queue.py --claim --agent-id agent-<UTC>-<random>
```

A worker with no shell may create the equivalent claim atomically through GitHub according to the claim protocol.

For each missing segment, choose a **public media URL already preserved in repository provenance** and submit:

```text
coordination/playback_requests/<CASE_ID>/<SEGMENT_ID>.json
```

The GitHub Action `.github/workflows/playback-evidence-service.yml` validates identity/provenance, decodes real media, runs offline ASR/OCR and writes durable evidence. Evidence generation alone never counts toward Pilot-60.

After evidence appears, the worker MUST read `evidence.md`/`evidence.json`. If the decoded-media evidence really matches the canonical content, submit the corresponding acceptance under:

```text
coordination/playback_acceptances/<CASE_ID>/<SEGMENT_ID>.json
```

The service cross-checks that acceptance against the evidence and canonical segment, then creates a qualifying playback audit record. A worker must never manufacture service evidence or accept evidence it has not read.

## Pilot-60 quality rule

Only valid `data/playback_audits/**/*.json` records count. Source-page timestamps, transcript timestamps, ordinary `S-AUDIT-*` markers, or ffmpeg decode success without content evidence do not count.

When `scripts/audit_gate.py --json` reports `pilot60_pass=true`, seal `P9-PLAYBACK-GATE`, proceed through current P9/P10, then continue full archive work according to the standing owner directive.

## Stop-state rule

Because the repository supplies the preferred Playback execution environment, lack of local ffmpeg/player is normally **not** `HOST_STOP`. `HOST_STOP` applies only when neither the repository evidence service nor a valid local fallback is available for all remaining playback work, or when the host actually terminates the Agent session.

Valid stop states are limited to genuine `PROJECT_COMPLETE`, `USER_RECALL`, true `NO_ELIGIBLE_WORK`, unavoidable `HUMAN_DECISION_REQUIRED`, `SAFETY_OR_ACCESS_BLOCK`, verified `GITHUB_WRITE_ERROR`, or true `HOST_STOP`.

## Claim races

A failed atomic claim is not automatically a GitHub outage. For `422`/`409`, fetch the exact claim path from fresh `main`:

```text
claim exists -> CLAIM_RACE_LOST -> refresh -> try another
claim absent -> refresh/backoff -> bounded retry
```

Never force-overwrite concurrent work. Current Git state and repository policy beat stale chat summaries or copied prompts.

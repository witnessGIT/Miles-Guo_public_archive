# Miles-Guo_public_archive Multi-Agent Coordination

Git is the authoritative coordination state for this project.

Current contracts:

```text
continuous-worker-v2
claim-protocol-v2
agent-permissions-v2.1
repository-playback-evidence-v2
```

Machine-readable policy: `coordination/WORKFLOW.json`.

## 1. Read current state, not chat history

Important paths:

```text
coordination/claims/
coordination/pr_reservations/
coordination/completed/
coordination/ready/
coordination/bug_reports/
coordination/playback_requests/
coordination/playback_acceptances/
coordination/playback_attempts/
data/playback_evidence/
data/playback_audits/
coordination/WORK_QUEUE.jsonl
```

## 2. Role boundary

```text
verified witnessGIT = admin
all other / unknown = worker
```

Workers execute claimed business/Playback tasks and report bugs. Workers do not patch scripts, schema, CI, workflow, permissions or other protected machinery.

Playback-specific worker surfaces:

```text
worker may write:
  coordination/playback_requests/
  coordination/playback_acceptances/

worker must not directly write:
  data/playback_evidence/
  data/playback_audits/
```

The generated output roots are written by `github-actions[bot]` or admin after validation.

## 3. Continuous loop

```text
discover
→ claim
→ push claim
→ execute
→ validate
→ push outputs
→ finish
→ refresh
→ claim next
```

One completed task or one claim race is not a stop condition.

## 4. Claim races

Create one immutable claim:

```text
coordination/claims/<TASK_ID>.json
```

For GitHub API `409/422`:

```text
fetch exact claim from fresh main
  exists -> CLAIM_RACE_LOST -> try another task
  absent -> refresh/backoff -> bounded retry
```

Never force-overwrite concurrent work.

## 5. Ordinary per-case pipeline

```text
COLLECT + IDENTITY
→ collection ready
→ ALIGN
→ alignment ready
→ source/provenance AUDIT
→ audit ready
```

`S-AUDIT-*` completion does not imply real Playback Audit success.

## 6. Real Playback is a separate retryable queue

List/claim:

```bash
python scripts/playback_queue.py --list
python scripts/playback_queue.py --claim --agent-id agent-<UTC>-<random>
```

Ordinary Agents no longer require local ffmpeg/player when the repository Playback Evidence Service exists.

Preferred execution:

```text
P9-PLAYBACK-* claim
→ playback request
→ GitHub Actions real-media decode
→ offline whisper.cpp ASR + frame OCR (+ optional SmolVLM2)
→ durable evidence.md/json
→ claim owner reads evidence
→ bundle-bound playback acceptance
→ service writes qualifying v2 playback audit
```

Detailed contract: `docs/MEDIA_AUDIT.md`.

A request must use a public media URL already preserved in repository provenance for the same live. Request/acceptance owner must equal the active playback claim owner.

Evidence generation alone never counts. Source timestamps/transcripts alone never count.

## 7. Current Pilot gate chain

Historical/superseded only:

```text
P9-AUDIT-60
P10-PILOT-DECISION
```

Current authoritative chain:

```text
>=60 qualifying real Playback checks
+ >=90% within 3 sec
+ >=98% within 8 sec
+ false merge approximately 0
        ↓
P9-PLAYBACK-GATE
        ↓
P9-AUDIT-60-R2
        ↓
P10-PILOT-DECISION-R2
        ↓
FULL_ARCHIVE YES / NO
```

Only an explicit current `P10-PILOT-DECISION-R2` with `full_archive_decision=YES` may authorize FULL_ARCHIVE.

## 8. Capability / stop classification

Run:

```bash
python scripts/project_status.py
```

Verified admin:

```bash
python scripts/project_status.py --role admin
```

Local lack of ffmpeg is not `HOST_STOP` while the repository Playback Evidence Service is available.

`HOST_STOP` for playback applies only when remaining playback work exists and neither the repository service nor a valid local fallback is available.

`SAFETY_OR_ACCESS_BLOCK` is reserved for work that would require bypassing login, CAPTCHA, paywall, DRM or another access control.

## 9. Bug handling

Workers create immutable reports under:

```text
coordination/bug_reports/
```

They do not repair protected machinery. Admin Agents review and resolve those reports.

## 10. Data concurrency

Prefer one live/case per independent file group. Avoid multiple Agents appending the same large JSONL where possible. `data/` JSON/JSONL is source of truth; SQLite is rebuildable.

## 11. Stale claims

A stale-looking claim is not automatically abandoned. Check commits, outputs, completion state and recent activity. Never steal a claim merely because an Agent is not visible in chat.

## 12. Platform limitation

Git can persist coordination state and GitHub Actions can run repository services, but neither can wake a ChatGPT/Work/Codex session after the host terminates it. New Agents resume from Git state.

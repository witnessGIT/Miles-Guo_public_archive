# Miles-Guo_public_archive

## Step 0 — resolve permissions before doing anything

This repository uses:

```text
continuous-worker-v2
claim-protocol-v2
agent-permissions-v2
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
13. relevant current data/reports/claims/completions/readiness/bug reports/playback requests/evidence

Do not rely on chat history or another Agent's summary instead of current Git state.

## Admin vs worker

Administrative GitHub login: `witnessGIT`.

Verified `witnessGIT` Agents may act as `admin`. Every other/unknown account is a `worker`.

A worker may execute valid claimed business/playback tasks, write its own task outputs and coordination records, submit playback requests and acceptances for its own claimed Playback task, and submit new immutable bug reports.

A worker MUST NOT fix repository bugs or modify protected control-plane paths, including `AGENTS.md`, `START_HERE.md`, core `coordination/` policy files, `scripts/`, `schema/`, or `.github/`.

Bugs go to:

```text
coordination/bug_reports/
```

Only an admin Agent repairs project machinery.

## Mandatory continuous operating mode

Default loop:

```text
resolve role
→ read repository state
→ classify current work
→ claim one eligible task
→ push claim immediately
→ execute real work allowed by role
→ validate and commit outputs
→ finish / publish readiness
→ refresh repository state
→ claim next eligible task
→ repeat
```

Finishing one task, one livestream, one micro-batch, or losing one claim race is not a stop condition.

## Stop conditions

A worker stops only for a documented reason such as `PROJECT_COMPLETE`, `USER_RECALL`, real `NO_ELIGIBLE_WORK`, `HUMAN_DECISION_REQUIRED`, `SAFETY_OR_ACCESS_BLOCK`, verified `GITHUB_WRITE_ERROR`, or true `HOST_STOP`.

`CLAIM_RACE_LOST` is not a stop condition.

Because the repository now contains a Playback Evidence Service, absence of local ffmpeg/player is normally **not HOST_STOP**. If repository Playback work is open and the service is available, ordinary workers can execute it through GitHub.

## Task discovery and claiming

Ordinary/static tasks:

```bash
python scripts/next_task.py --list
```

Playback tasks:

```bash
python scripts/playback_queue.py --list
```

Current Pilot gate identities:

```text
P9-AUDIT-60-R2
P10-PILOT-DECISION-R2
```

Historical `P9-AUDIT-60` and `P10-PILOT-DECISION` are superseded audit history and are never executable current tasks.

## Claim races

For GitHub `create_file`, a `422` or `409` is not automatically an outage. Fetch the exact claim from fresh `main`:

```text
claim exists -> CLAIM_RACE_LOST -> refresh -> try another
claim absent -> refresh/backoff -> bounded retry
```

Never overwrite another Agent's claim.

## Streaming pipeline

```text
COLLECT + IDENTITY
→ collection readiness
→ ALIGN
→ alignment readiness
→ source/provenance AUDIT
→ real Playback Audit where required
→ Pilot-60 aggregate gate
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

For a claimed `P9-PLAYBACK-*` case:

1. Select a missing canonical timed segment.
2. Select a public media URL already preserved in repository provenance for the same live.
3. Create `coordination/playback_requests/<CASE>/<SEGMENT>.json`.
4. Push it. GitHub Actions performs real-media decoding, offline `whisper.cpp` ASR and frame OCR; optional SmolVLM2 may add visual evidence.
5. Wait only for repository state to advance; then read `data/playback_evidence/<CASE>/<SEGMENT>/evidence.md` and `evidence.json`.
6. If the decoded-media evidence really matches the canonical target content, create `coordination/playback_acceptances/<CASE>/<SEGMENT>.json` bound to the exact evidence `bundle_id`.
7. Push it. The service independently validates and writes a `qualifying_playback_timing_check_v2` under `data/playback_audits/`.
8. Finish the case only when all currently tracked timed segments in that case have valid qualifying records.

Evidence generation alone never counts. Worker acceptance without valid service evidence never counts. Source-page timestamps alone never count.

Detailed contracts are authoritative in `docs/MEDIA_AUDIT.md` and `START_HERE.md`.

A local manual fallback remains supported for truly playback-capable runtimes using `audit_media.py` / `record_playback_audit.py` and v1 evidence.

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

When `pilot60_pass=true`, seal `P9-PLAYBACK-GATE`, then proceed to `P9-AUDIT-60-R2` and `P10-PILOT-DECISION-R2`.

## Database behavior

`data/` JSON/JSONL is source of truth. `database/Miles-Guo_public_archive.sqlite3` is rebuildable:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

Workers may validate; if a bug/contract mismatch appears, report it instead of patching protected machinery.

## Scope and core archive discipline

- Only modify `witnessGIT/Miles-Guo_public_archive` for this project.
- Official project name: `Miles-Guo_public_archive`.
- Official database path: `database/Miles-Guo_public_archive.sqlite3`.
- Archive First, Application Second.
- Preserve provenance and conflicts.
- Seconds are primary media locator; frames auxiliary only.
- Public content only; no bypass of login/CAPTCHA/paywall/DRM/access controls.
- Never commit full videos, large audio, model weights, caches or FFmpeg intermediates.
- Do not begin FULL_ARCHIVE merely because collection works. Only current `P10-PILOT-DECISION-R2` may authorize it, and only with explicit `full_archive_decision=YES` after required gates pass.

## Useful progress

For a worker: source-backed business output, valid Playback request/evidence acceptance, alignment/audit evidence, readiness/completion metadata, or a properly filed bug report.

For an admin: all worker progress plus validated repair of project machinery.

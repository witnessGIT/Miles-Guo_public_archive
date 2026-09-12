# Miles-Guo_public_archive Agent Entry Point

## External prompt contract

A minimal external prompt is sufficient:

```text
进入这个项目并开始工作：
https://github.com/witnessGIT/Miles-Guo_public_archive
```

The repository is the authoritative execution context. Do not ask the user to repeat requirements already stored here.

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
worker = execute claimed project tasks + use repository services + report bugs
admin  = worker capabilities + repair/maintain project machinery
```

Workers MUST NOT modify `scripts/`, `schema/`, `.github/`, workflow policy, permissions or other protected control-plane files. Bugs go to `coordination/bug_reports/` for an admin Agent.

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
FULL_ARCHIVE YES / NO
```

FULL_ARCHIVE remains locked unless current `P10-PILOT-DECISION-R2` records an explicit machine-readable `full_archive_decision=YES` after all prerequisites pass.

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

Contract:

```json
{
  "request_version": "playback-request-v1",
  "task_id": "P9-PLAYBACK-PILOT-E002",
  "case_id": "PILOT-E002",
  "live_id": "LIVE_20170610_001",
  "segment_id": "LIVE_20170610_001_SEG_000001",
  "media_url": "https://public-media-url-already-in-repository-provenance",
  "requested_by": "agent-...",
  "requested_at": "ISO-8601 UTC",
  "pre_roll_sec": 10.0,
  "decode_window_sec": 24.0,
  "language": "zh",
  "visual_mode": "frames_ocr"
}
```

Optional visual mode `smolvlm2_optional` asks the free open-source SmolVLM2 stage to run when the service environment enables it. Audio timing remains primary.

The GitHub Action `.github/workflows/playback-evidence-service.yml` then:

1. verifies case/live/segment identity;
2. refuses arbitrary URLs not present in repository provenance for that live;
3. resolves/probes/decodes real media with `yt-dlp` + `ffprobe` + `ffmpeg`;
4. decodes a window before and after the canonical timestamp;
5. runs offline `whisper.cpp` on decoded audio;
6. fuzzy-matches the canonical target text to the new decoded-audio ASR;
7. samples video frames and runs local OCR;
8. optionally runs free SmolVLM2 visual description;
9. writes durable Agent-readable `evidence.json` and `evidence.md` to Git.

**Evidence generation alone never counts toward Pilot-60.**

After the evidence appears, the worker MUST read `evidence.md`/`evidence.json`. If the decoded-media evidence really matches the canonical content, submit:

```text
coordination/playback_acceptances/<CASE_ID>/<SEGMENT_ID>.json
```

Contract:

```json
{
  "acceptance_version": "playback-acceptance-v1",
  "case_id": "PILOT-E002",
  "live_id": "LIVE_20170610_001",
  "segment_id": "LIVE_20170610_001_SEG_000001",
  "evidence_ref": "data/playback_evidence/PILOT-E002/LIVE_20170610_001_SEG_000001/evidence.json",
  "bundle_id": "copy-exactly-from-evidence",
  "accepted": true,
  "accepted_by": "agent-...",
  "accepted_at": "ISO-8601 UTC",
  "content_observation": "brief factual explanation of why the decoded-media evidence matches"
}
```

The service cross-checks the acceptance against the evidence and canonical segment, then creates `qualifying_playback_timing_check_v2` under `data/playback_audits/`. A worker must never manufacture service evidence or accept evidence it has not read.

CLI helpers exist when shell is available:

```bash
python scripts/playback_queue.py --request <SEGMENT_ID> --case-id <CASE_ID> --media-url '<URL>' --agent-id <agent-id>
python scripts/playback_queue.py --accept <SEGMENT_ID> --case-id <CASE_ID> --content-observation '<why it matches>' --agent-id <agent-id>
```

## Free-service design

The default service uses only repository/public infrastructure and open-source tools:

```text
GitHub standard public-repo runner
+ ffmpeg / ffprobe
+ yt-dlp
+ whisper.cpp (pinned release, cached model/build)
+ Tesseract OCR
+ optional SmolVLM2-256M
```

Full videos/clips are temporary runner/cache data and are not committed. Durable Git evidence is compact JSON/Markdown plus hashes/provenance.

## Pilot-60 quality rule

Only valid `data/playback_audits/**/*.json` records count. The validator supports:

- v1: legacy/manual real decoded-media inspection;
- v2: repository-decoded evidence + explicit worker evidence acceptance.

Both must cross-check canonical case/live/segment identity, expected/observed timing and media provenance. Source-page timestamps, transcript timestamps, ordinary `S-AUDIT-*` markers, or ffmpeg decode success without content evidence do not count.

When `scripts/audit_gate.py --json` reports `pilot60_pass=true`, seal `P9-PLAYBACK-GATE`, then proceed to P9/P10 R2. Extra unreviewed cases do not block the gate after the statistical threshold has passed.

## Stop-state rule

Because the repository now supplies the preferred Playback execution environment, lack of local ffmpeg/player is normally **not** `HOST_STOP` anymore. `HOST_STOP` applies only when neither the repository evidence service nor a valid local fallback is available for remaining playback work.

## Claim races

A failed atomic claim is not automatically a GitHub outage. For `422`/`409`, fetch the exact claim path from fresh `main`:

```text
claim exists -> CLAIM_RACE_LOST -> refresh -> try another
claim absent -> refresh/backoff -> bounded retry
```

Never force-overwrite concurrent work. Current Git state and repository policy beat stale chat summaries or copied prompts.

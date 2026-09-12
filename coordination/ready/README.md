# Miles-Guo_public_archive Streaming Readiness

This directory contains per-Pilot-case readiness markers for the `continuous-worker-v2` pipeline.

## Layout

```text
coordination/ready/
  collection/
    PILOT-E001.json
  alignment/
    PILOT-E001.json
  audit/
    PILOT-E001.json
```

A marker means that this individual case reached the named workflow stage. **For audit markers, marker existence does not mean the Pilot timing gate passed.**

## Why this exists

Readiness markers remove large-batch waiting:

```text
one case collected
→ that case can align immediately
→ that case can audit immediately after alignment
```

Other cases may remain unfinished.

## Streaming task creation

Preferred path:

```bash
python scripts/next_task.py --finish <STREAM_TASK_ID> ...
```

The task runner creates the stage marker. If an audit runner does not yet emit the audit qualification fields below, the task owner must add them to its own marker before treating it as final audit evidence.

## Required common evidence

Every readiness marker must point to durable output and real validation. Typical common fields:

```json
{
  "project": "Miles-Guo_public_archive",
  "workflow_mode": "continuous-worker-v2",
  "case_id": "PILOT-E001",
  "live_id": "LIVE_20170523_001",
  "stage": "alignment",
  "ready_at": "ISO-8601 timestamp",
  "task_id": "S-ALIGN-PILOT-E001",
  "agent_id": "agent-...",
  "result_commit": "commit sha",
  "outputs": ["data/..."],
  "validation": "what was actually checked"
}
```

## Mandatory audit qualification fields

Every NEW `stage = audit` marker must also contain:

```json
{
  "audit_outcome": "verified|partial|blocked_no_playback|unverified",
  "qualifying_playback_checks": 0,
  "counts_toward_pilot_60": false,
  "timing_accuracy_measured": false
}
```

Rules:

- `qualifying_playback_checks` counts only segments whose actual media playback position was independently observed;
- transcript-anchor agreement alone is not a qualifying playback check;
- source identity/provenance verification alone is not a qualifying playback check;
- `counts_toward_pilot_60` may be true only when `qualifying_playback_checks > 0`;
- `timing_accuracy_measured` may be true only when observed playback position was compared with the stored candidate timestamp;
- blocked playback may be recorded as useful audit evidence but contributes zero to Pilot-60;
- P9/P10 must never count marker existence or an `S-AUDIT-*` completed record as a timing pass without the underlying qualifying checks.

Legacy audit markers without these machine-readable fields count as **zero** toward Pilot-60 until reviewed or backed by explicit real playback evidence.

## Grandfathered legacy batch collectors

Existing legacy batch owners keep their valid claims. As soon as one individual collection case is genuinely complete, the owner may publish collection readiness without ending the batch:

```bash
python scripts/next_task.py \
  --mark-ready collection \
  --case-id PILOT-M001 \
  --agent-id <legacy-claim-owner> \
  --live-id LIVE_20200323_001 \
  --outputs ... \
  --validation "source identity and provenance verified"
```

This unlocks per-case downstream work while the original batch continues.

## No shared mutable progress file

Do not maintain one shared status JSONL for all cases. Keep readiness per case so parallel Agents do not collide.

The task runner derives workflow eligibility from readiness plus claims/completed state. Pilot acceptance uses the stricter quality-gate evidence above.

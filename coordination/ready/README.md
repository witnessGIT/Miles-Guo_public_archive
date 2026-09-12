# Miles-Guo_public_archive Streaming Readiness

This directory contains per-Pilot-case readiness markers for the self-service Agent pipeline.

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

A marker means that **this individual case**, not an entire era/batch, has completed the named stage well enough for the next stage to start.

## Why this exists

The original Pilot queue used large era batches. That caused unrelated livestreams to block downstream work. Readiness markers remove that bottleneck:

```text
one case collected
→ that case can align immediately
→ that case can audit immediately after alignment
```

Other cases may remain unfinished.

## Creation

Preferred method:

```bash
python scripts/next_task.py --finish <STREAM_TASK_ID> ...
```

The task runner creates the correct marker for streaming tasks.

Legacy batch collectors may create `collection/<CASE_ID>.json` manually as soon as an individual case is genuinely complete, even before the full legacy batch is done.

## Required evidence

A readiness marker must point to durable output and real validation. It must not be used to bypass missing data or quality checks.

Typical fields:

```json
{
  "project": "Miles-Guo_public_archive",
  "case_id": "PILOT-E001",
  "live_id": "LIVE_20170523_001",
  "stage": "collection",
  "ready_at": "ISO-8601 timestamp",
  "task_id": "S-COLLECT-PILOT-E001",
  "agent_id": "agent-...",
  "result_commit": "commit sha",
  "outputs": ["data/..."],
  "validation": "what was actually checked"
}
```

Do not edit one shared status file for all cases. Keep readiness per case so parallel Agents do not collide.

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

A marker means that **this individual case**, not an entire era/batch, has completed the named stage well enough for the next stage to start.

## Why this exists

The original Pilot queue used large era batches. That caused unrelated livestreams to block downstream work.

Readiness markers remove that bottleneck:

```text
one case collected
→ that case can align immediately
→ that case can audit immediately after alignment
```

Other cases may remain unfinished.

## Streaming task creation

Preferred path for new `continuous-worker-v2` tasks:

```bash
python scripts/next_task.py --finish <STREAM_TASK_ID> ...
```

The task runner creates the appropriate readiness marker automatically.

## Grandfathered legacy batch collectors

Existing legacy Middle/Late batch Agents keep their original claims. They do not need to abandon or repartition those tasks.

As soon as one individual case inside the batch is genuinely complete, the legacy owner can publish a collection marker without ending the batch:

```bash
python scripts/next_task.py \
  --mark-ready collection \
  --case-id PILOT-M001 \
  --agent-id <legacy-claim-owner> \
  --live-id LIVE_20200323_001 \
  --outputs ... \
  --validation "source identity and provenance verified"
```

That immediately unlocks:

```text
S-ALIGN-PILOT-M001
```

for another Agent, while the original Middle batch Agent continues M002/M003/etc.

`--mark-ready` verifies that the supplied `agent-id` owns the corresponding active legacy batch claim. It must not be used by another Agent to bypass task ownership.

## Required evidence

A readiness marker must point to durable output and real validation. It must not be used to bypass missing data or quality checks.

Typical fields:

```json
{
  "project": "Miles-Guo_public_archive",
  "workflow_mode": "continuous-worker-v2",
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

## No shared mutable progress file

Do not edit one shared status file for all cases. Keep readiness per case so parallel Agents do not collide.

The machine-readable task runner derives next-stage eligibility from these markers plus claims/completed state.

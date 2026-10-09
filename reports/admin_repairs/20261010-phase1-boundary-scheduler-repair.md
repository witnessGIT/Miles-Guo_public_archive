# Phase 1 boundary scheduler repair

Date: 2026-10-10 (Asia/Tokyo)

## Symptom

The candidate-review queue was complete, but `scripts/agent_entry.py --mode auto`
reported `NO_LOCAL_CLAIM` and `scripts/project_status.py` reported
`NO_ELIGIBLE_WORK`. One source-boundary record remained `in_progress` after its
24-hour claim lease expired. The boundary output already existed, but the scheduler
did not expose `in_progress` boundary records for reclaiming.

Completed boundary records also retained their original `open` status in immutable
source-boundary discovery data. `has_unfinished_source_boundaries()` interpreted
those historical status values without consulting durable completion records, so
the aggregate C2 task remained locked after the underlying work was complete.

## Repair

- Source-boundary completion records now override the discovery-time `open` or
  `in_progress` status when deciding whether Phase 1 collection remains open.
- Orphaned `in_progress` boundaries are returned to the eligible queue when no
  active claim blocks them, allowing the normal expired-claim reclaim path to run.
- Regression tests cover both completed-open boundaries and reclaimable orphaned
  in-progress boundaries.
- Queue discovery now builds the completed-task and blocking-claim indexes once.
  This avoids rescanning every claim for every generated live work item after C3
  expands the queue to full-archive scale.

## Validation

- Full unit suite: 100 tests pass with local `ffmpeg` and `ffprobe`; no skips.
- `C1-GWINS-detail-24263` becomes the next eligible task and can be reclaimed
  through Claim Protocol v2.
- With 17,500 generated live work items, `next_task.py --list` completes in about
  two seconds instead of stalling in repeated claim-directory scans.

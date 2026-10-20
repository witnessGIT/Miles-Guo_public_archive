#!/usr/bin/env python3
"""Select one shared video batch for key-point and entity enrichment."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .cloud_asr_batch import claim_is_unavailable
except ImportError:  # Direct script execution adds scripts/ to sys.path.
    from cloud_asr_batch import claim_is_unavailable


STAGES = ("key_points_topics", "entity_pass")
MAX_SHARED_BATCH_SIZE = 150


def select_live_ids(repo: Path, limit: int, retry_cooldown_hours: int = 24) -> list[str]:
    completed = repo / "coordination" / "completed"
    claims = repo / "coordination" / "claims"
    selected: list[str] = []
    for segment_done in sorted(completed.glob("WI_LIVE_*_segment_split.json")):
        live_id = segment_done.stem.removeprefix("WI_").removesuffix("_segment_split")
        missing = [
            stage for stage in STAGES
            if not (completed / f"WI_{live_id}_{stage}.json").exists()
        ]
        if not missing:
            continue
        if any(
            claim_is_unavailable(
                claims / f"WI_{live_id}_{stage}.json", retry_cooldown_hours,
            )
            for stage in missing
        ):
            continue
        selected.append(live_id)
        if len(selected) == limit:
            break
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=MAX_SHARED_BATCH_SIZE)
    parser.add_argument("--retry-cooldown-hours", type=int, default=24)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= MAX_SHARED_BATCH_SIZE:
        raise SystemExit(
            f"shared enrichment batch size must be between 1 and {MAX_SHARED_BATCH_SIZE}"
        )
    if not 0 <= args.retry_cooldown_hours <= 168:
        raise SystemExit("shared enrichment retry cooldown must be between 0 and 168 hours")
    print(",".join(select_live_ids(
        args.repo.resolve(), args.batch_size, args.retry_cooldown_hours,
    )))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

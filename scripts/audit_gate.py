#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playback_validation import (
    canonical_segment_index,
    pilot_case_live_map,
    validate_playback_record,
)

ROOT = Path(__file__).resolve().parents[1]
PLAYBACK_ROOT = ROOT / "data" / "playback_audits"


def load_checks() -> tuple[list[dict], list[str]]:
    checks: list[dict] = []
    problems: list[str] = []
    segments, segment_problems = canonical_segment_index()
    case_live, case_problems = pilot_case_live_map()
    problems.extend(segment_problems)
    problems.extend(case_problems)

    if not PLAYBACK_ROOT.exists():
        return checks, problems

    seen_segments: set[str] = set()
    for path in sorted(PLAYBACK_ROOT.rglob("*.json")):
        rel = str(path.relative_to(ROOT))
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{rel}: invalid JSON: {exc}")
            continue
        if not isinstance(row, dict):
            problems.append(f"{rel}: top-level JSON must be an object")
            continue

        validated, row_problems = validate_playback_record(
            row,
            source_label=rel,
            segments=segments,
            case_live=case_live,
        )
        if row_problems:
            problems.extend(row_problems)
            continue
        assert validated is not None

        segment_id = str(validated["segment_id"])
        if segment_id in seen_segments:
            problems.append(f"{rel}: duplicate qualifying segment_id {segment_id}")
            continue
        seen_segments.add(segment_id)
        checks.append({k: v for k, v in validated.items() if k != "_canonical_segment"} | {"_path": rel})

    return checks, problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the Pilot-60 gate from durable qualifying playback checks only. "
            "Every counted record is cross-checked against canonical segment/case data."
        )
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--require", type=int, default=60, help="Required qualifying checks.")
    args = parser.parse_args()

    checks, problems = load_checks()
    errors = [abs(float(row["timing_error_sec"])) for row in checks]
    total = len(checks)
    within_3 = sum(value <= 3.0 for value in errors)
    within_8 = sum(value <= 8.0 for value in errors)
    rate_3 = (within_3 / total) if total else 0.0
    rate_8 = (within_8 / total) if total else 0.0

    summary = {
        "project": "Miles-Guo_public_archive",
        "gate": "P9-AUDIT-60",
        "evidence_source": "data/playback_audits/**/*.json",
        "canonical_crosscheck": True,
        "legacy_audit_readiness_counts_automatically": False,
        "qualifying_checks": total,
        "required_checks": args.require,
        "within_3_sec": within_3,
        "within_3_sec_rate": rate_3,
        "within_8_sec": within_8,
        "within_8_sec_rate": rate_8,
        "threshold_3_sec": 0.90,
        "threshold_8_sec": 0.98,
        "invalid_records": problems,
        "passes_count_gate": total >= args.require,
        "passes_3_sec_gate": total > 0 and rate_3 >= 0.90,
        "passes_8_sec_gate": total > 0 and rate_8 >= 0.98,
    }
    summary["pilot60_pass"] = (
        summary["passes_count_gate"]
        and summary["passes_3_sec_gate"]
        and summary["passes_8_sec_gate"]
        and not problems
    )

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("Pilot-60 playback audit gate")
        print(f"  qualifying checks: {total}/{args.require}")
        print(f"  <=3s: {within_3}/{total} ({rate_3:.1%})")
        print(f"  <=8s: {within_8}/{total} ({rate_8:.1%})")
        print(f"  invalid records: {len(problems)}")
        for problem in problems:
            print(f"    - {problem}")
        print(f"  PASS: {summary['pilot60_pass']}")
        if total == 0:
            print(
                "  Note: coordination/ready/audit files are intentionally not counted; "
                "only canonical-crosschecked content-timing playback checks count."
            )

    return 0 if summary["pilot60_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

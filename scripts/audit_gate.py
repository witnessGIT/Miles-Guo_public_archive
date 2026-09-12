#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBACK_ROOT = ROOT / "data" / "playback_audits"


def load_checks() -> tuple[list[dict], list[str]]:
    checks: list[dict] = []
    problems: list[str] = []
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

        required = [
            "case_id",
            "live_id",
            "segment_id",
            "expected_start_sec",
            "observed_position_sec",
            "timing_error_sec",
            "absolute_timing_error_sec",
            "media_url",
            "reviewer",
        ]
        missing = [key for key in required if row.get(key) is None or row.get(key) == ""]
        if missing:
            problems.append(f"{rel}: missing required fields: {', '.join(missing)}")
            continue
        if row.get("evidence_type") != "qualifying_playback_timing_check_v1":
            problems.append(f"{rel}: unsupported evidence_type")
            continue
        if row.get("playback_decode_verified") is not True:
            problems.append(f"{rel}: playback_decode_verified is not true")
            continue
        if row.get("content_timing_verified") is not True or row.get("content_match") is not True:
            problems.append(f"{rel}: content timing/content match not verified")
            continue

        segment_id = str(row["segment_id"])
        if segment_id in seen_segments:
            problems.append(f"{rel}: duplicate qualifying segment_id {segment_id}")
            continue
        seen_segments.add(segment_id)

        try:
            expected = float(row["expected_start_sec"])
            observed = float(row["observed_position_sec"])
            signed = float(row["timing_error_sec"])
            absolute = float(row["absolute_timing_error_sec"])
        except (TypeError, ValueError):
            problems.append(f"{rel}: non-numeric timing field")
            continue

        recomputed = observed - expected
        if abs(recomputed - signed) > 0.001:
            problems.append(f"{rel}: timing_error_sec inconsistent with observed-expected")
            continue
        if abs(abs(signed) - absolute) > 0.001:
            problems.append(f"{rel}: absolute_timing_error_sec inconsistent")
            continue

        checks.append({**row, "_path": rel})

    return checks, problems


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the Pilot-60 gate from durable qualifying playback checks only. "
            "Legacy coordination/ready/audit markers never count by themselves."
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
                "only durable content-timing playback checks count."
            )

    return 0 if summary["pilot60_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

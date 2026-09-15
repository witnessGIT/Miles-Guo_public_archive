#!/usr/bin/env python3
# Admin recovery trigger: re-scan durable pending playback requests after missed push scheduling.
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "data" / "playback_evidence"


def load_object(path: Path) -> dict:
    row = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(row, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return row


def revision(row: dict) -> int:
    value = row.get("request_revision", 1)
    if isinstance(value, bool):
        raise ValueError("request_revision must be an integer >= 1")
    value = int(value)
    if value < 1:
        raise ValueError("request_revision must be >= 1")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Bind repository playback evidence to the exact request revision after "
            "process_playback_request.py has succeeded."
        )
    )
    parser.add_argument("--request", required=True)
    args = parser.parse_args()

    request_path = Path(args.request)
    if not request_path.is_absolute():
        request_path = ROOT / request_path
    request_path = request_path.resolve()
    request = load_object(request_path)

    case_id = str(request.get("case_id") or "")
    live_id = str(request.get("live_id") or "")
    segment_id = str(request.get("segment_id") or "")
    media_url = str(request.get("media_url") or "")
    requested_by = str(request.get("requested_by") or "")
    if not all((case_id, live_id, segment_id, media_url, requested_by)):
        raise SystemExit("request lacks identity/media/requester fields")

    evidence_path = EVIDENCE_ROOT / case_id / segment_id / "evidence.json"
    if not evidence_path.exists():
        raise SystemExit(f"evidence missing after successful processing: {evidence_path}")
    evidence = load_object(evidence_path)

    expected_ref = str(request_path.relative_to(ROOT.resolve()))
    checks = {
        "case_id": case_id,
        "live_id": live_id,
        "segment_id": segment_id,
        "media_url": media_url,
        "requested_by": requested_by,
        "request_ref": expected_ref,
    }
    mismatches = [
        f"{key}: evidence={evidence.get(key)!r} request={value!r}"
        for key, value in checks.items()
        if str(evidence.get(key) or "") != value
    ]
    if mismatches:
        raise SystemExit(
            "refusing to stamp evidence that does not belong to this successful request: "
            + "; ".join(mismatches)
        )

    evidence["request_revision"] = revision(request)
    evidence["request_sha256"] = sha256_file(request_path)
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Stamped {evidence_path.relative_to(ROOT)} request_revision="
        f"{evidence['request_revision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST_ROOT = ROOT / "coordination" / "playback_requests"
ACCEPTANCE_ROOT = ROOT / "coordination" / "playback_acceptances"
EVIDENCE_ROOT = ROOT / "data" / "playback_evidence"
AUDIT_ROOT = ROOT / "data" / "playback_audits"

RETRYABLE_EVIDENCE_STATUSES = {
    "blocked_media_decode",
    "needs_manual_or_wider_review",
    "invalid",
}


def load_object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("top-level JSON must be an object")
    return payload


def request_revision(row: dict) -> int:
    value = row.get("request_revision", 1)
    if isinstance(value, bool):
        raise ValueError("request_revision must be an integer >= 1")
    try:
        revision = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("request_revision must be an integer >= 1") from exc
    if revision < 1:
        raise ValueError("request_revision must be >= 1")
    return revision


def evidence_path_for(request: dict) -> Path:
    return (
        EVIDENCE_ROOT
        / str(request.get("case_id") or "")
        / str(request.get("segment_id") or "")
        / "evidence.json"
    )


def audit_path_for(acceptance: dict) -> Path:
    return (
        AUDIT_ROOT
        / str(acceptance.get("case_id") or "")
        / f"{str(acceptance.get('segment_id') or '')}.json"
    )


def pending_requests(*, prepare_retries: bool) -> tuple[list[Path], list[str]]:
    """Return requests that genuinely need processing without deleting prior evidence."""
    pending: list[Path] = []
    problems: list[str] = []
    if not REQUEST_ROOT.exists():
        return pending, problems

    for path in sorted(REQUEST_ROOT.rglob("*.json")):
        if path.name == "README.md":
            continue
        try:
            request = load_object(path)
            revision = request_revision(request)
            evidence_path = evidence_path_for(request)
            if not evidence_path.exists():
                pending.append(path)
                continue
            evidence = load_object(evidence_path)
            evidence_revision = request_revision(evidence)
            if revision <= evidence_revision:
                continue
            status = str(evidence.get("status") or "")
            if status not in RETRYABLE_EVIDENCE_STATUSES:
                problems.append(
                    f"{path.relative_to(ROOT)}: request_revision {revision} is newer than "
                    f"reviewable evidence revision {evidence_revision} with status={status!r}; "
                    "do not overwrite reviewable evidence"
                )
                continue
            if prepare_retries:
                print(
                    f"Prepared non-destructive retry {path.relative_to(ROOT)} revision {revision} "
                    f"over prior {status} revision {evidence_revision}; prior evidence is preserved "
                    "until successful request processing stamps the new revision",
                    file=sys.stderr,
                )
            pending.append(path)
        except Exception as exc:
            problems.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
    return pending, problems


def pending_acceptances() -> tuple[list[Path], list[str]]:
    pending: list[Path] = []
    problems: list[str] = []
    if not ACCEPTANCE_ROOT.exists():
        return pending, problems
    for path in sorted(ACCEPTANCE_ROOT.rglob("*.json")):
        try:
            acceptance = load_object(path)
            audit_path = audit_path_for(acceptance)
            if audit_path.exists():
                continue
            pending.append(path)
        except Exception as exc:
            problems.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
    return pending, problems


def finalize_evidence() -> list[str]:
    """Finalize presentation only; request revision binding is done by stamp helper.

    This function intentionally does NOT modify request_revision. Otherwise a failed newer
    request could relabel an older evidence bundle as if the newer request had succeeded.
    """
    problems: list[str] = []
    if not REQUEST_ROOT.exists():
        return problems
    for request_path in sorted(REQUEST_ROOT.rglob("*.json")):
        try:
            request = load_object(request_path)
            evidence_path = evidence_path_for(request)
            if not evidence_path.exists():
                continue
            evidence = load_object(evidence_path)
            if str(evidence.get("request_ref") or "") != str(request_path.relative_to(ROOT)):
                continue

            md_path = evidence_path.parent / "evidence.md"
            if md_path.exists() and evidence.get("playback_decode_verified") is not True:
                text = md_path.read_text(encoding="utf-8")
                old = (
                    "This evidence was produced from decoded media bytes. It is **not yet a "
                    "Pilot-60 qualifying record**."
                )
                new = (
                    "The repository attempted real-media decoding, but decoding did **not** "
                    "succeed. This is **not** a Pilot-60 qualifying record and must not be accepted."
                )
                if old in text:
                    md_path.write_text(text.replace(old, new), encoding="utf-8")
        except Exception as exc:
            problems.append(
                f"{request_path.relative_to(ROOT)}: {type(exc).__name__}: {exc}"
            )
    return problems


def emit_paths(paths: list[Path]) -> None:
    for path in paths:
        print(path.relative_to(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Keep repository Playback Evidence Service scans idempotent and retry-aware."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pending-requests", action="store_true")
    group.add_argument("--prepare-pending-requests", action="store_true")
    group.add_argument("--pending-acceptances", action="store_true")
    group.add_argument("--finalize-evidence", action="store_true")
    args = parser.parse_args()

    if args.pending_requests or args.prepare_pending_requests:
        paths, problems = pending_requests(prepare_retries=args.prepare_pending_requests)
        emit_paths(paths)
    elif args.pending_acceptances:
        paths, problems = pending_acceptances()
        emit_paths(paths)
    else:
        problems = finalize_evidence()

    if problems:
        for problem in problems:
            print(f"ERROR {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Durable retry guards for playback cases whose current inputs are exhausted.

A guard is intentionally narrow: it blocks autonomous re-claim only while every tracked
input file has exactly the Git blob SHA recorded when the blocker was established. If source
provenance or playback-service code changes, the guard becomes inactive automatically and the
case is eligible for a fresh autonomous retry.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD_ROOT = ROOT / "coordination" / "playback_retry_guards"
POLICY = "environment_change_required"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def load_guard(case_id: str) -> dict | None:
    path = GUARD_ROOT / f"{case_id}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def guard_is_active(case_id: str) -> bool:
    guard = load_guard(case_id)
    if not guard or guard.get("retry_policy") != POLICY:
        return False
    files = guard.get("environment_files")
    if not isinstance(files, dict) or not files:
        return False
    for relative, expected_sha in files.items():
        if not isinstance(relative, str) or not isinstance(expected_sha, str):
            return False
        path = ROOT / relative
        if not path.is_file():
            return False
        try:
            current_sha = git_blob_sha(path)
        except OSError:
            return False
        if current_sha != expected_sha:
            return False
    return True


def filter_candidates(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    eligible: list[dict] = []
    guarded: list[dict] = []
    for row in candidates:
        case_id = str(row.get("case_id") or "")
        if case_id and guard_is_active(case_id):
            guarded.append(row)
        else:
            eligible.append(row)
    return eligible, guarded

#!/usr/bin/env python3
"""Deterministic cross-source identity scoring for Miles-Guo_public_archive.

This module scores two source-candidate records without relying on network access.
It intentionally does NOT treat dates, source-side ordinals, GHOT slugs, or
GettrSearch opaque route tokens as canonical livestream identities.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

RULE_VERSION = "identity-v1"


def _host(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def canonical_url_identity(url: str | None) -> str | None:
    """Return a stable identity key when the URL exposes one.

    Unknown sites are retained as normalized page URLs. GettrSearch /playvideo/
    tokens remain GettrSearch-local URL identities and are never promoted to
    GETTR platform IDs.
    """
    if not url:
        return None
    raw = url.strip()
    if not raw:
        return None

    p = urlparse(raw)
    host = _host(raw)
    path = re.sub(r"/+$", "", p.path or "/")

    if host == "youtu.be":
        video_id = path.strip("/").split("/")[0]
        return f"youtube:video:{video_id}" if video_id else None

    if host in {"youtube.com", "m.youtube.com"}:
        if path == "/watch":
            video_id = parse_qs(p.query).get("v", [None])[0]
            return f"youtube:video:{video_id}" if video_id else None
        m = re.match(r"^/(?:shorts|embed)/([^/?#]+)", path)
        if m:
            return f"youtube:video:{m.group(1)}"

    if host == "gettr.com":
        m = re.match(r"^/(streaming|post)/([^/?#]+)", path)
        if m:
            return f"gettr:{m.group(1)}:{m.group(2)}"

    if host == "rumble.com":
        # Rumble public URLs normally begin with a stable v... item token,
        # followed by an optional human-readable slug.
        m = re.match(r"^/(v[a-z0-9]+)(?:[-./]|$)", path, flags=re.IGNORECASE)
        if m:
            return f"rumble:item:{m.group(1).lower()}"

    if host == "gwins.org":
        m = re.match(r"^/cn/milesguo/(\d+)\.html$", path)
        if m:
            return f"gwins:page:{m.group(1)}"

    # Preserve an exact normalized page identity for direct cross-reference
    # testing, but ignore query/fragment tracking parameters.
    return f"url:{host}{path}"


def _normalize_text(value: str | None) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = re.sub(r"\s+", "", value)
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE)


def text_similarity(a: str | None, b: str | None) -> float | None:
    left = _normalize_text(a)
    right = _normalize_text(b)
    if not left or not right:
        return None
    return SequenceMatcher(None, left, right).ratio()


def _url_keys(record: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for url in [record.get("url"), *(record.get("external_urls") or [])]:
        key = canonical_url_identity(url)
        if key:
            keys.add(key)
    return keys


def _platform_ids(record: dict[str, Any]) -> set[str]:
    return {
        key
        for key in _url_keys(record)
        if key.startswith(("gettr:", "youtube:", "rumble:"))
    }


def _verified_date_conflict(left: dict[str, Any], right: dict[str, Any]) -> int | None:
    if not (left.get("live_date_verified") and right.get("live_date_verified")):
        return None
    ldate = left.get("live_date")
    rdate = right.get("live_date")
    if not (ldate and rdate):
        return None
    try:
        delta = abs((date.fromisoformat(ldate) - date.fromisoformat(rdate)).days)
    except ValueError:
        return None
    return delta if delta > 1 else None


def _full_duration_conflict(left: dict[str, Any], right: dict[str, Any]) -> float | None:
    if left.get("content_scope") != "full" or right.get("content_scope") != "full":
        return None
    ldur = left.get("duration_sec")
    rdur = right.get("duration_sec")
    if ldur is None or rdur is None:
        return None
    ldur = float(ldur)
    rdur = float(rdur)
    if max(ldur, rdur) <= 0:
        return None
    delta = abs(ldur - rdur)
    relative = delta / max(ldur, rdur)
    if delta > 120 and relative > 0.20:
        return relative
    return None


def _hard_conflicts(left: dict[str, Any], right: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    date_delta = _verified_date_conflict(left, right)
    if date_delta is not None:
        conflicts.append({"type": "verified_live_date_conflict", "days": date_delta})
    duration_relative = _full_duration_conflict(left, right)
    if duration_relative is not None:
        conflicts.append(
            {
                "type": "full_duration_conflict",
                "relative_difference": round(duration_relative, 4),
            }
        )
    return conflicts


def score_pair(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Score a pair and return an explainable decision.

    `do_not_merge` means "insufficient evidence for automatic merge"; it is not
    equivalent to `confirmed_distinct`.
    """
    evidence: list[dict[str, Any]] = []
    conflicts = _hard_conflicts(left, right)

    left_keys = _url_keys(left)
    right_keys = _url_keys(right)
    shared_platform = sorted(_platform_ids(left) & _platform_ids(right))

    if shared_platform:
        evidence.append(
            {"type": "shared_platform_id", "values": shared_platform, "weight": 1.0}
        )
        return {
            "rule_version": RULE_VERSION,
            "match_score": 1.0,
            "decision": "needs_review" if conflicts else "auto_merge",
            "evidence": evidence,
            "conflicts": conflicts,
        }

    left_own = canonical_url_identity(left.get("url"))
    right_own = canonical_url_identity(right.get("url"))
    direct_cross_reference = bool(
        (left_own and left_own in right_keys)
        or (right_own and right_own in left_keys)
    )
    if direct_cross_reference:
        evidence.append({"type": "direct_cross_reference", "weight": 0.98})
        return {
            "rule_version": RULE_VERSION,
            "match_score": 0.98,
            "decision": "needs_review" if conflicts else "auto_merge",
            "evidence": evidence,
            "conflicts": conflicts,
        }

    score = 0.0
    live_date_left = left.get("live_date")
    live_date_right = right.get("live_date")
    exact_date = bool(
        live_date_left and live_date_right and live_date_left == live_date_right
    )
    if exact_date:
        score += 0.25
        evidence.append(
            {"type": "exact_live_date", "value": live_date_left, "weight": 0.25}
        )

    title_sim = text_similarity(left.get("title"), right.get("title"))
    if title_sim is not None:
        title_weight = (
            0.20
            if title_sim >= 0.90
            else 0.14
            if title_sim >= 0.75
            else 0.08
            if title_sim >= 0.60
            else 0.0
        )
        if title_weight:
            score += title_weight
            evidence.append(
                {
                    "type": "title_similarity",
                    "value": round(title_sim, 4),
                    "weight": title_weight,
                }
            )

    duration_weight = 0.0
    ldur = left.get("duration_sec")
    rdur = right.get("duration_sec")
    if ldur is not None and rdur is not None and max(float(ldur), float(rdur)) > 0:
        delta = abs(float(ldur) - float(rdur))
        relative = delta / max(float(ldur), float(rdur))
        duration_weight = (
            0.20
            if delta <= 5
            else 0.15
            if delta <= 30
            else 0.10
            if relative <= 0.05
            else 0.0
        )
        if duration_weight:
            score += duration_weight
            evidence.append(
                {
                    "type": "duration_similarity",
                    "delta_sec": round(delta, 3),
                    "weight": duration_weight,
                }
            )

    transcript_sim = text_similarity(left.get("text_sample"), right.get("text_sample"))
    transcript_strong = bool(transcript_sim is not None and transcript_sim >= 0.75)
    if transcript_sim is not None:
        transcript_weight = (
            0.30
            if transcript_sim >= 0.90
            else 0.22
            if transcript_sim >= 0.75
            else 0.12
            if transcript_sim >= 0.60
            else 0.0
        )
        if transcript_weight:
            score += transcript_weight
            evidence.append(
                {
                    "type": "text_similarity",
                    "value": round(transcript_sim, 4),
                    "weight": transcript_weight,
                }
            )

    score = min(round(score, 4), 1.0)

    # Hard conflicts never auto-merge a fallback match.
    if conflicts:
        score = min(score, 0.64)
        decision = "do_not_merge" if score < 0.65 else "needs_review"
    elif score >= 0.85 and exact_date and transcript_strong:
        decision = "auto_merge"
    elif score >= 0.65:
        decision = "needs_review"
    else:
        decision = "do_not_merge"

    return {
        "rule_version": RULE_VERSION,
        "match_score": round(score, 4),
        "decision": decision,
        "evidence": evidence,
        "conflicts": conflicts,
    }


def run_cases(path: Path) -> tuple[int, list[dict[str, Any]]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    failures = 0
    outputs: list[dict[str, Any]] = []
    for case in cases:
        result = score_pair(case["left"], case["right"])
        expected = case["expected_decision"]
        passed = result["decision"] == expected
        failures += 0 if passed else 1
        outputs.append(
            {
                "id": case["id"],
                "passed": passed,
                "expected_decision": expected,
                "actual": result,
            }
        )
    return failures, outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left", nargs="?", type=Path)
    parser.add_argument("right", nargs="?", type=Path)
    parser.add_argument("--cases", type=Path)
    args = parser.parse_args()

    if args.cases:
        failures, outputs = run_cases(args.cases)
        print(json.dumps(outputs, ensure_ascii=False, indent=2))
        return 1 if failures else 0

    if not (args.left and args.right):
        parser.error("provide LEFT RIGHT JSON files, or --cases CASES.json")

    left = json.loads(args.left.read_text(encoding="utf-8"))
    right = json.loads(args.right.read_text(encoding="utf-8"))
    print(json.dumps(score_pair(left, right), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

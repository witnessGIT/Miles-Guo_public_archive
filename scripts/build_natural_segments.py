#!/usr/bin/env python3
"""Build citable machine passages from timestamped ASR cues.

The cue stream remains untouched.  This pass only replaces the one-cue-per-segment
search layer with larger passages.  Boundaries prefer pauses, discourse transitions
and completed questions; a duration ceiling is only a safety fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "current"
TRANSITION_RE = re.compile(
    r"^(那么|接下来|另外|再说|再讲|还有一个|第二|第三|第四|最后|回过头|换句话说|"
    r"关于|至于|下面|同时|另一方面|说到这里|我们再来|今天要讲)"
)
QUESTION_RE = re.compile(r"(?:吗|呢|么|为什么|怎么|如何|什么|谁|哪里|哪儿)[？?]?$")


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            row = json.loads(raw)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no}: expected object")
            rows.append(row)
    return rows


def split_cues(
    cues: list[dict], *, min_duration: float = 24.0, max_duration: float = 120.0,
    pause_seconds: float = 2.5,
) -> list[tuple[list[dict], str]]:
    if not cues:
        return []
    groups: list[tuple[list[dict], str]] = []
    current: list[dict] = []
    start_method = "transcript_start"
    previous: dict | None = None

    for cue in cues:
        text = str(cue.get("text") or "").strip()
        if not text:
            continue
        if current:
            group_start = float(current[0].get("start_sec") or 0.0)
            cue_start = float(cue.get("start_sec") or group_start)
            duration = cue_start - group_start
            gap = cue_start - float(previous.get("end_sec") or cue_start) if previous else 0.0
            trigger: str | None = None
            if duration >= min_duration and gap >= pause_seconds:
                trigger = "asr_pause"
            elif duration >= min_duration and TRANSITION_RE.search(text):
                trigger = "discourse_marker"
            elif duration >= min_duration and previous and QUESTION_RE.search(str(previous.get("text") or "")):
                trigger = "question_boundary"
            elif duration >= max_duration:
                trigger = "max_duration_safety"
            if trigger:
                groups.append((current, start_method))
                current = []
                start_method = trigger
        current.append(cue)
        previous = cue

    if current:
        groups.append((current, start_method))
    return groups


def build_segments(cues: list[dict], template: dict) -> list[dict]:
    if not cues:
        return []
    live_ids = {str(row.get("live_id") or "") for row in cues}
    if len(live_ids) != 1 or "" in live_ids:
        raise ValueError("cue file must contain exactly one non-empty live_id")
    live_id = live_ids.pop()
    created_at = str(template.get("created_at") or "")
    if not created_at:
        raise ValueError("segment template is missing created_at")

    output: list[dict] = []
    for index, (group, method) in enumerate(split_cues(cues)):
        text = " ".join(str(row["text"]).strip() for row in group if str(row.get("text") or "").strip())
        normalized = re.sub(r"\s+", " ", text).strip()
        output.append(
            {
                "id": f"{live_id}_SEG_{index:06d}",
                "live_id": live_id,
                "segment_index": index,
                "text_curated": None,
                "text_asr": text,
                "text_search": normalized,
                "text_summary": None,
                "headline": None,
                "segment_type": "speech",
                "boundary_method": f"natural_asr_v1:{method}",
                "start_sec": group[0].get("start_sec"),
                "end_sec": group[-1].get("end_sec"),
                "start_frame": None,
                "end_frame": None,
                "fps_at_index": None,
                "topic_primary": None,
                "topic_secondary": None,
                "entities_json": None,
                "keywords_json": None,
                "curated_source_id": None,
                "asr_source_id": template.get("asr_source_id"),
                "time_source_id": template.get("time_source_id"),
                "alignment_quality": None,
                "alignment_method": "asr_cue_grouping",
                "source_verified": int(template.get("source_verified") or 0),
                "playback_verified": 0,
                "playback_verified_at": None,
                "review_status": "machine",
                "content_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
    return output


def process_live(live_id: str, repo: Path = ROOT) -> tuple[Path, int, int]:
    stem = f"asr_{live_id.lower()}"
    cue_path = repo / "data" / "current" / "transcript_cues" / f"{stem}.jsonl"
    segment_path = repo / "data" / "current" / "live_segments" / f"{stem}.jsonl"
    cues = read_jsonl(cue_path)
    old_segments = read_jsonl(segment_path)
    if not old_segments:
        raise ValueError(f"{segment_path}: no segment template")
    segments = build_segments(cues, old_segments[0])
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in segments)
    segment_path.write_text(payload, encoding="utf-8")
    return segment_path, len(cues), len(segments)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("live_ids", nargs="+")
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args()
    for live_id in args.live_ids:
        path, cue_count, segment_count = process_live(live_id, args.repo.resolve())
        print(json.dumps({"live_id": live_id, "cues": cue_count, "natural_segments": segment_count, "output": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

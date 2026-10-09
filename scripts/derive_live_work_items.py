#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_CURRENT = ROOT / "data" / "current"

STAGES: tuple[tuple[str, str], ...] = (
    ("metadata_fill", "Fill title/date/source/media metadata for one canonical livestream."),
    ("transcript_import", "Import source transcript or ASR text without overwriting original text."),
    ("cue_split", "Split transcript into sentence/subtitle cues using natural sentence/time boundaries."),
    ("segment_split", "Create citable segments by natural topic/event/quote boundaries, not by fixed counts."),
    ("entity_pass", "Extract speakers, people, organizations, places and mentioned entities."),
    ("event_pass", "Extract events mentioned inside the original livestream."),
    ("claim_pass", "Extract original quotes, opinions, judgments, predictions and questions."),
    ("relation_pass", "Link related original segments by topic, event, support, contradiction or clipping use."),
    ("text_verify", "Cross-check source text/ASR/corrected text and create text verification records."),
    ("playback_backlog", "Create future audio/video verification backlog without marking final acceptance."),
)
STAGE_NAMES = tuple(stage for stage, _instructions in STAGES)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def iter_json_records(relative_dir: str) -> list[dict]:
    base = DATA_CURRENT / relative_dir
    rows: list[dict] = []
    if not base.exists():
        return rows
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                rows.append(payload)
            elif isinstance(payload, list):
                rows.extend(item for item in payload if isinstance(item, dict))
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            text = raw.strip()
            if text and not text.startswith("#"):
                row = json.loads(text)
                if isinstance(row, dict):
                    rows.append(row)
    return rows


def existing_work_ids() -> set[str]:
    return {
        str(row.get("id"))
        for row in iter_json_records("live_work_items")
        if row.get("id")
    }


def make_item(
    live_id: str,
    stage: str,
    instructions: str,
    priority: int,
    depends_on: list[str],
) -> dict:
    now = utc_now()
    return {
        "id": f"WI_{live_id}_{stage}",
        "live_id": live_id,
        "source_candidate_id": None,
        "work_stage": stage,
        "work_status": "open",
        "natural_boundary": "one canonical livestream and one processing stage",
        "instructions": instructions,
        "priority": priority,
        "depends_on_json": depends_on,
        "created_at": now,
        "updated_at": now,
    }


def expected_dependencies(live_id: str, stage: str) -> list[str]:
    try:
        index = STAGE_NAMES.index(stage)
    except ValueError:
        return []
    if index == 0:
        return []
    return [f"WI_{live_id}_{STAGE_NAMES[index - 1]}"]


def derive_items() -> list[dict]:
    existing = existing_work_ids()
    items: list[dict] = []
    live_rows = iter_json_records("live_videos")
    for live in sorted(live_rows, key=lambda row: str(row.get("id") or "")):
        live_id = str(live.get("id") or "")
        if not live_id:
            continue
        for index, (stage, instructions) in enumerate(STAGES):
            depends_on = expected_dependencies(live_id, stage)
            item = make_item(live_id, stage, instructions, 72 - index, depends_on)
            if item["id"] not in existing:
                items.append(item)
    return items


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Derive natural-boundary live_work_items from active live_videos."
    )
    parser.add_argument(
        "--output",
        default="live_work_items/generated.jsonl",
        help="Path under data/current for generated work items.",
    )
    parser.add_argument(
        "--reconcile-output",
        action="store_true",
        help="Populate the canonical per-live stage dependency chain in existing output rows.",
    )
    args = parser.parse_args()

    items = derive_items()
    out = DATA_CURRENT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    reconciled = 0
    if args.reconcile_output and out.exists():
        rows: list[dict] = []
        for raw in out.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            row = json.loads(raw)
            expected = expected_dependencies(
                str(row.get("live_id") or ""), str(row.get("work_stage") or "")
            )
            if row.get("depends_on_json") != expected:
                row["depends_on_json"] = expected
                reconciled += 1
            rows.append(row)
        temporary = out.with_suffix(out.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        temporary.replace(out)
    print(f"derived live_work_items: {len(items)}")
    print(f"reconciled live_work_item dependencies: {reconciled}")
    print(f"output: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

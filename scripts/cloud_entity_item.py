#!/usr/bin/env python3
"""Extract machine-status named entities from natural livestream passages."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Callable


ENTITY_TYPES = {"person", "organization", "country", "place", "media", "law", "project", "company", "government", "other"}
MENTION_ROLES = {"mentioned", "target", "ally", "opponent", "source", "victim", "location", "organization", "quoted"}
GENERIC_ENTITY_TERMS = {
    "五毛", "政府", "官员", "领导", "老领导", "朋友", "家人", "员工", "律师团队",
    "哥哥", "弟弟", "姐姐", "妹妹", "侄女", "侄子", "网友", "推友", "战友",
}
KNOWN_TYPE_OVERRIDES = {"推特": "media", "Twitter": "media", "香港": "place", "日本": "country", "中国": "country"}
RELATIONAL_PREFIXES = ("我的", "我们", "这个", "这些", "那个", "那些", "一位", "某个", "有些")
GENERIC_ENTITY_FRAGMENTS = ("很多人", "家属", "官员", "某人", "一些人", "一群人")


def parse_json_array(text: str) -> list[dict]:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start < 0 or end < start:
        raise ValueError("model response did not contain a JSON array")
    value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, list):
        raise ValueError("model response JSON was not an array")
    return [row for row in value if isinstance(row, dict)]


def entity_id(live_id: str, entity_type: str, canonical_name: str) -> str:
    digest = hashlib.sha256(f"{entity_type}\0{canonical_name}".encode("utf-8")).hexdigest()[:16].upper()
    return f"ENT_{live_id}_{digest}"


def validate_mentions(segment: dict, candidates: list[dict]) -> list[dict]:
    text = str(segment.get("text_asr") or segment.get("text_search") or "")
    accepted: list[dict] = []
    seen: set[str] = set()
    for item in candidates:
        canonical = str(item.get("canonical_name") or "").strip()
        mention = str(item.get("mention_text") or canonical).strip()
        kind = str(item.get("entity_type") or "other").strip().lower()
        role = str(item.get("mention_role") or "mentioned").strip().lower()
        if canonical in GENERIC_ENTITY_TERMS or canonical.startswith(RELATIONAL_PREFIXES) or any(fragment in canonical for fragment in GENERIC_ENTITY_FRAGMENTS):
            continue
        kind = KNOWN_TYPE_OVERRIDES.get(canonical, kind)
        if kind not in ENTITY_TYPES:
            kind = "other"
        if role not in MENTION_ROLES:
            role = "mentioned"
        if not canonical or not mention or mention not in text:
            continue
        if canonical in seen:
            continue
        seen.add(canonical)
        accepted.append({"canonical_name": canonical, "mention_text": mention, "entity_type": kind, "mention_role": role})
    return accepted


def prompt_for(segment: dict) -> str:
    text = str(segment.get("text_asr") or "")
    return (
        "你是历史档案实体标注器。只根据给出的机器转录原文识别人名、组织、国家、地点、媒体、法律、项目、公司或政府机构。"
        "不要补充外部知识，不要纠正原文，不要猜测代词指向。只标注有专名的具体实体；"
        "排除政府、官员、领导、五毛、朋友、员工、家人等泛称，排除我的哥哥、我的侄女等未具名亲属称谓。"
        "mention_text必须是原文中逐字存在的连续文本。"
        "只输出JSON数组；每项字段为canonical_name、mention_text、entity_type、mention_role。"
        "entity_type只能是person,organization,country,place,media,law,project,company,government,other；"
        "mention_role只能是mentioned,target,ally,opponent,source,victim,location,organization,quoted。没有实体就输出[]。\n"
        f"<transcript>{text}</transcript>"
    )


def enrich_segments(live_id: str, segments: list[dict], generate_text: Callable[[str], str]) -> tuple[list[dict], list[dict], list[dict], dict]:
    entity_records: dict[str, dict] = {}
    links: list[dict] = []
    invalid_responses = 0
    for segment in segments:
        try:
            candidates = parse_json_array(generate_text(prompt_for(segment)))
        except (ValueError, json.JSONDecodeError):
            invalid_responses += 1
            candidates = []
        mentions = validate_mentions(segment, candidates)
        names: list[str] = []
        for mention in mentions:
            eid = entity_id(live_id, mention["entity_type"], mention["canonical_name"])
            entity_records.setdefault(eid, {
                "id": eid,
                "entity_type": mention["entity_type"],
                "canonical_name": mention["canonical_name"],
                "aliases_json": [mention["mention_text"]],
                "metadata_json": {"extraction_method": "qwen2.5-3b-instruct-4bit-entity-v1", "extraction_status": "machine"},
            })
            links.append({
                "segment_id": segment["id"], "entity_id": eid,
                "mention_text": mention["mention_text"], "mention_role": mention["mention_role"], "confidence": 0.65,
            })
            names.append(mention["canonical_name"])
        segment["entities_json"] = sorted(set(names)) or None
    stats = {"segments": len(segments), "entities": len(entity_records), "mentions": len(links), "invalid_responses": invalid_responses}
    return segments, list(entity_records.values()), links, stats


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def process_live(repo: Path, live_id: str, generate_text: Callable[[str], str]) -> tuple[list[str], dict]:
    stem = f"asr_{live_id.lower()}"
    segment_path = repo / "data" / "current" / "live_segments" / f"{stem}.jsonl"
    segments = [json.loads(line) for line in segment_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not segments or not all(str(row.get("boundary_method") or "").startswith("natural_asr_v1:") for row in segments):
        raise ValueError(f"{live_id}: natural segments are required before entity extraction")
    segments, entities, links, stats = enrich_segments(live_id, segments, generate_text)
    entity_path = repo / "data" / "current" / "entities" / f"machine_{live_id.lower()}.jsonl"
    link_path = repo / "data" / "current" / "segment_entities" / f"machine_{live_id.lower()}.jsonl"
    write_jsonl(segment_path, segments)
    write_jsonl(entity_path, entities)
    write_jsonl(link_path, links)
    outputs = [str(path.relative_to(repo)) for path in (segment_path, entity_path, link_path)]
    return outputs, stats


def repair_existing_outputs(repo: Path, live_id: str) -> dict:
    stem = f"machine_{live_id.lower()}"
    segment_path = repo / "data" / "current" / "live_segments" / f"asr_{live_id.lower()}.jsonl"
    entity_path = repo / "data" / "current" / "entities" / f"{stem}.jsonl"
    link_path = repo / "data" / "current" / "segment_entities" / f"{stem}.jsonl"
    segments = [json.loads(line) for line in segment_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    entities = [json.loads(line) for line in entity_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    links = [json.loads(line) for line in link_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    kept: dict[str, dict] = {}
    for row in entities:
        name = str(row.get("canonical_name") or "").strip()
        if not name or name in GENERIC_ENTITY_TERMS or name.startswith(RELATIONAL_PREFIXES) or any(fragment in name for fragment in GENERIC_ENTITY_FRAGMENTS):
            continue
        row["entity_type"] = KNOWN_TYPE_OVERRIDES.get(name, row.get("entity_type") or "other")
        kept[row["id"]] = row
    filtered_links: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in links:
        entity = kept.get(str(row.get("entity_id") or ""))
        key = (str(row.get("segment_id") or ""), str(row.get("entity_id") or ""))
        if entity is None or key in seen:
            continue
        seen.add(key)
        filtered_links.append(row)
    names_by_segment: dict[str, set[str]] = {}
    for row in filtered_links:
        names_by_segment.setdefault(row["segment_id"], set()).add(kept[row["entity_id"]]["canonical_name"])
    for segment in segments:
        segment["entities_json"] = sorted(names_by_segment.get(segment["id"], set())) or None
    write_jsonl(segment_path, segments)
    write_jsonl(entity_path, list(kept.values()))
    write_jsonl(link_path, filtered_links)
    return {"entities": len(kept), "mentions": len(filtered_links), "segments": len(segments)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repair-existing", nargs="+", metavar="LIVE_ID")
    args = parser.parse_args()
    if not args.repair_existing:
        parser.error("--repair-existing is required when running this module directly")
    for live_id in args.repair_existing:
        print(json.dumps({"live_id": live_id, **repair_existing_outputs(args.repo.resolve(), live_id)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

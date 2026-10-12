#!/usr/bin/env python3
"""Create evidence-grounded key points and controlled topic assignments."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


TOPICS = {
    "TOPIC_POLITICS_GOVERNANCE": "政治与治理",
    "TOPIC_LAW_JUSTICE": "法律与司法",
    "TOPIC_FINANCE_BUSINESS": "金融与商业",
    "TOPIC_MEDIA_PUBLIC_OPINION": "媒体与舆论",
    "TOPIC_INTERNATIONAL_RELATIONS": "国际关系",
    "TOPIC_SOCIAL_PUBLIC_AFFAIRS": "社会与公共事务",
    "TOPIC_PERSONAL_EXPERIENCE": "个人经历",
    "TOPIC_PEOPLE_ORGANIZATIONS": "人物与组织",
    "TOPIC_DISCLOSURE_INVESTIGATION": "举报与调查",
    "TOPIC_INTERNET_TECHNOLOGY": "网络与科技",
    "TOPIC_SECURITY_CONFLICT": "安全与冲突",
    "TOPIC_HEALTH": "健康",
    "TOPIC_RELIGION_BELIEF": "宗教与信仰",
    "TOPIC_DEMOCRACY_HUMAN_RIGHTS": "民主与人权",
    "TOPIC_OVERSEAS_LIFE": "移民与海外生活",
    "TOPIC_PROJECT_ACTION": "项目与行动",
    "TOPIC_OTHER": "其他",
}
POINT_TYPES = {"takeaway", "context", "argument", "evidence", "conclusion", "question", "warning", "instruction"}
METHOD = "qwen2.5-7b-instruct-4bit-grounded-keypoints-v1"


def parse_json_object(text: str) -> dict:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model response did not contain a JSON object")
    value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model response JSON was not an object")
    return value


def prompt_for(segment: dict) -> str:
    choices = "、".join(f"{key}={name}" for key, name in TOPICS.items())
    return (
        "你是历史档案要点标注器。只依据机器转录原文，提炼一个中性、简洁、便于检索的要点；"
        "不得补充外部事实，不得判断真伪，不得纠正原文。若原文只是寒暄、口头语或无法形成要点，输出{}。"
        "evidence_quote必须是原文中逐字存在、能直接支持要点的连续短句，至少6个字符。"
        "point_type只能是takeaway,context,argument,evidence,conclusion,question,warning,instruction。"
        "topic_ids只能从给定主题中选1至3个。只输出JSON对象，字段为point_type、point_text、significance、evidence_quote、topic_ids。"
        f"主题：{choices}\n<transcript>{segment.get('text_asr') or ''}</transcript>"
    )


def validate_result(segment: dict, value: dict) -> dict | None:
    text = str(segment.get("text_asr") or "")
    point_text = re.sub(r"\s+", " ", str(value.get("point_text") or "")).strip()
    evidence = re.sub(r"\s+", " ", str(value.get("evidence_quote") or "")).strip()
    point_type = str(value.get("point_type") or "takeaway").strip().lower()
    significance = re.sub(r"\s+", " ", str(value.get("significance") or "")).strip()
    raw_topics = value.get("topic_ids") if isinstance(value.get("topic_ids"), list) else []
    topic_ids = list(dict.fromkeys(str(item) for item in raw_topics if str(item) in TOPICS))[:3]
    if not 4 <= len(point_text) <= 180 or len(evidence) < 6 or evidence not in text or not topic_ids:
        return None
    if point_type not in POINT_TYPES:
        point_type = "takeaway"
    return {
        "point_type": point_type,
        "point_text": point_text,
        "significance": significance[:240] or None,
        "evidence_quote": evidence,
        "topic_ids": topic_ids,
    }


def enrich_segments(live_id: str, segments: list[dict], generate_text: Callable[[str], str]) -> tuple[list[dict], list[dict], list[dict], dict]:
    now = datetime.now(timezone.utc).isoformat()
    key_points: list[dict] = []
    segment_topics: list[dict] = []
    invalid = 0
    for segment in segments:
        try:
            value = parse_json_object(generate_text(prompt_for(segment)))
            result = validate_result(segment, value)
        except (ValueError, json.JSONDecodeError):
            result = None
        if result is None:
            invalid += 1
            continue
        segment_id = str(segment["id"])
        primary_topic = result["topic_ids"][0]
        segment["text_summary"] = result["point_text"]
        segment["headline"] = result["point_text"][:80]
        segment["topic_primary"] = TOPICS[primary_topic]
        segment["topic_secondary"] = TOPICS[result["topic_ids"][1]] if len(result["topic_ids"]) > 1 else None
        key_points.append({
            "id": f"KPT_{segment_id}_000",
            "segment_id": segment_id,
            "point_index": 0,
            "point_type": result["point_type"],
            "point_text": result["point_text"],
            "significance": result["significance"],
            "topic_id": primary_topic,
            "event_id": None,
            "supporting_claim_id": None,
            "importance": 0.7,
            "confidence": 0.68,
            "extraction_status": "machine",
            "extraction_method": METHOD,
            "created_at": now,
        })
        for index, topic_id in enumerate(result["topic_ids"]):
            segment_topics.append({
                "segment_id": segment_id,
                "topic_id": topic_id,
                "topic_role": "primary" if index == 0 else "secondary",
                "relevance": 0.75 if index == 0 else 0.55,
                "extraction_status": "machine",
                "extraction_method": METHOD,
                "created_at": now,
            })
    return segments, key_points, segment_topics, {"segments": len(segments), "key_points": len(key_points), "topic_links": len(segment_topics), "skipped_or_invalid": invalid}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def process_live(repo: Path, live_id: str, generate_text: Callable[[str], str]) -> tuple[list[str], dict]:
    lower = live_id.lower()
    segment_path = repo / "data" / "current" / "live_segments" / f"asr_{lower}.jsonl"
    segments = [json.loads(line) for line in segment_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not segments or not all(str(row.get("boundary_method") or "").startswith("natural_asr_v1:") for row in segments):
        raise ValueError(f"{live_id}: natural segments are required before key-point extraction")
    segments, key_points, topic_links, stats = enrich_segments(live_id, segments, generate_text)
    key_path = repo / "data" / "current" / "segment_key_points" / f"machine_{lower}.jsonl"
    link_path = repo / "data" / "current" / "segment_topics" / f"machine_{lower}.jsonl"
    topic_path = repo / "data" / "current" / "topics" / "controlled_taxonomy_v1.jsonl"
    write_jsonl(segment_path, segments)
    write_jsonl(key_path, key_points)
    write_jsonl(link_path, topic_links)
    write_jsonl(topic_path, [{"id": key, "name": name, "parent_topic_id": None, "metadata_json": {"taxonomy": "controlled_v1"}} for key, name in TOPICS.items()])
    return [str(path.relative_to(repo)) for path in (segment_path, key_path, link_path, topic_path)], stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--live-id", required=True)
    parser.error("Use cloud_keypoint_batch.py so inference remains claim-bound")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

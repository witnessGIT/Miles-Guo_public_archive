#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from process_source_fetch_request import EVIDENCE_ROOT, ROOT, load_and_validate_request, request_sha256

BOUNDARIES = ROOT / "data" / "current" / "source_boundaries" / "phase1_initial_boundaries.jsonl"
CANDIDATES = ROOT / "data" / "current" / "source_candidates" / "gwins"
COMPLETED = ROOT / "coordination" / "completed"
CLAIMS = ROOT / "coordination" / "claims"


def compact(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def load_boundaries() -> list[dict]:
    return [json.loads(line) for line in BOUNDARIES.read_text(encoding="utf-8").splitlines() if line.strip()]


def candidate_rows(request: dict, evidence: dict) -> list[dict]:
    page_id = request["source_page_id"]
    rows = []
    for item in evidence["items"]:
        source_video_id = item.get("source_video_id")
        if not source_video_id or not item.get("title"):
            raise ValueError("evidence item lacks source_video_id or title")
        rows.append({
            "id": f"SC_GWINS_{page_id.upper()}_{source_video_id}",
            "source_site": "GWINS",
            "source_url": request["source_url"].replace("www.gwins.org", "gwins.org"),
            "page_kind": "index_page",
            "discovery_context": f"GWINS natural list boundary {page_id}",
            "candidate_title": item["title"],
            "candidate_date": item.get("candidate_date"),
            "candidate_published_at": None,
            "candidate_duration_text": None,
            "candidate_duration_sec": None,
            "has_video": True,
            "has_audio": None,
            "has_transcript": None,
            "has_timestamps": None,
            "source_video_id": source_video_id,
            "source_page_id": page_id,
            "candidate_live_id": None,
            "status": "discovered",
            "confidence": 0.7,
            "discovered_by": request["agent_id"],
            "discovered_at": evidence["fetched_at"],
            "metadata_json": {
                "evidence_source": f"data/source_page_evidence/gwins/{page_id}/evidence.json",
                "evidence_request_sha256": evidence["request_sha256"],
                "evidence_raw_sha256": evidence["raw_sha256"],
                "detail_url": item.get("detail_url"),
                "canonical_promotion_performed": False,
                "public_index_discovery": True,
                "discovery_note": "C1 source discovery finalized by repository Source Page Evidence Service; no canonical promotion.",
            },
        })
    if len(rows) != evidence.get("item_count"):
        raise ValueError("evidence item_count mismatch")
    return rows


def finalize(path: Path) -> str:
    request, claim_status = load_and_validate_request(path)
    page_id = request["source_page_id"]
    evidence_path = EVIDENCE_ROOT / "gwins" / page_id / "evidence.json"
    if not evidence_path.exists():
        return "deferred:no-evidence"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence.get("request_sha256") != request_sha256(request):
        raise ValueError("evidence does not match request revision")

    completion_path = COMPLETED / f"{request['task_id']}.json"
    if claim_status == "completed" and completion_path.exists():
        return "already-completed"

    boundaries = load_boundaries()
    boundary = next((row for row in boundaries if row.get("id") == request["task_id"]), None)
    if boundary is None:
        return "deferred:boundary-not-open-yet"
    if boundary.get("status") == "completed" and completion_path.exists():
        return "already-completed"
    if boundary.get("status") != "open":
        raise ValueError("claimed source boundary is not open")

    rows = candidate_rows(request, evidence)
    output_path = CANDIDATES / f"{page_id}.jsonl"
    rendered = "\n".join(compact(row) for row in rows) + "\n"
    if output_path.exists() and output_path.read_text(encoding="utf-8") != rendered:
        raise ValueError("candidate output already exists with different content")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    completed_at = evidence["fetched_at"]
    boundary.update({
        "status": "completed",
        "notes": f"Scanned complete GWINS {page_id} through repository Source Page Evidence Service and recorded {len(rows)} source_candidates only; no C2 promotion.",
        "completed_by": request["agent_id"],
        "completed_at": completed_at,
        "output": str(output_path.relative_to(ROOT)),
    })

    new_boundaries: list[str] = []
    match = re.fullmatch(r"list_2_(\d+)", page_id)
    next_number = int(match.group(1)) - 1 if match else -1
    if next_number >= 1:
        next_page = f"list_2_{next_number}"
        next_url = f"https://www.gwins.org/cn/milesguo/{next_page}.html"
        if next_url not in evidence.get("pagination_urls", []):
            raise ValueError(f"evidence does not expose expected adjacent page {next_page}")
        next_task = f"C1-GWINS-{next_page}"
        if not any(row.get("id") == next_task for row in boundaries):
            boundaries.append({
                "id": next_task,
                "source_site": "gwins",
                "boundary_type": "index_page",
                "natural_boundary": f"GWINS adjacent list page immediately newer than {page_id}",
                "url": next_url,
                "status": "open",
                "priority": int(boundary["priority"]) + 1,
                "discovered_from": request["task_id"],
                "notes": "Continue GWINS natural-boundary source discovery toward newer list pages. Write only source_candidates; use repository Source Page Evidence Service; no C2 promotion.",
            })
        new_boundaries.append(next_task)
    BOUNDARIES.write_text("\n".join(compact(row) for row in boundaries) + "\n", encoding="utf-8")

    claim_path = CLAIMS / f"{request['task_id']}.json"
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    claim.update({
        "status": "completed",
        "completed_at": completed_at,
        "completed_by": request["agent_id"],
        "outputs": [str(output_path.relative_to(ROOT)), str(BOUNDARIES.relative_to(ROOT))],
    })
    claim_path.write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    completion = {
        "task_id": request["task_id"], "agent_id": request["agent_id"],
        "completed_by": request["agent_id"], "status": "completed", "completed_at": completed_at,
        "workflow_mode": "continuous-worker-v2", "claim_protocol": "claim-protocol-v2",
        "natural_boundary": request["source_url"],
        "outputs": [str(output_path.relative_to(ROOT)), str(BOUNDARIES.relative_to(ROOT))],
        "candidate_count": len(rows), "canonical_promotion_performed": False,
        "validation": {
            "source_site": "GWINS", "page_kind": "index_page", "all_candidates_status": "discovered",
            "all_candidate_live_ids_null": True, "fixed_quota_used": False,
            "evidence_basis": f"repository Source Page Evidence Service HTTP {evidence['http_status']}, raw SHA-256 {evidence['raw_sha256']}, {len(rows)} visible title records",
            "source_page_evidence": str(evidence_path.relative_to(ROOT)),
        },
        "new_boundaries": new_boundaries, "continue_after_finish": True,
    }
    completion_path.parent.mkdir(parents=True, exist_ok=True)
    completion_path.write_text(json.dumps(completion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f"completed:{request['task_id']}:{len(rows)}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(finalize(args.request))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"source fetch finalization failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

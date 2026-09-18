from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "coordination" / "WORK_QUEUE.jsonl"
CLAIMS = ROOT / "coordination" / "claims"
COMPLETED = ROOT / "coordination" / "completed"
READY = ROOT / "coordination" / "ready"
CLAIM_ATTEMPTS = ROOT / "coordination" / "claim_attempts"
PILOT_SELECTION = ROOT / "reports" / "pilot_selection.json"
DATA_CURRENT = ROOT / "data" / "current"
WORKFLOW = ROOT / "coordination" / "WORKFLOW.json"

WORKFLOW_MODE = "continuous-worker-v2"
CLAIM_PROTOCOL = "claim-protocol-v2"
CURRENT_P9 = "P9-AUDIT-60-R2"
CURRENT_P10 = "P10-PILOT-DECISION-R2"
LEGACY_GATE_TASKS = {"P9-AUDIT-60", "P10-PILOT-DECISION"}
STATIC_CLAIM_LEASE_HOURS = 24

LEGACY_BATCH_TASKS = {
    "early": "P6-PILOT-EARLY-B001",
    "middle": "P6-PILOT-MIDDLE-B001",
    "late": "P6-PILOT-LATE-B001",
}

STREAM_PRIORITIES = {
    "collect": 76,
    "align": 72,
    "audit": 52,
}

WORK_ITEM_STAGE_PRIORITY = {
    "source_merge": 74,
    "metadata_fill": 72,
    "transcript_import": 68,
    "cue_split": 64,
    "segment_split": 62,
    "entity_pass": 58,
    "event_pass": 57,
    "claim_pass": 56,
    "relation_pass": 54,
    "text_verify": 50,
    "playback_backlog": 45,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_json_path(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_queue() -> list[dict]:
    tasks: list[dict] = []
    if not QUEUE.exists():
        return tasks
    for raw in QUEUE.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            tasks.append(json.loads(raw))
    return tasks


def load_workflow() -> dict:
    try:
        payload = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def iter_current_records(relative_dir: str) -> list[dict]:
    records: list[dict] = []
    base = DATA_CURRENT / relative_dir
    if not base.exists():
        return records
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                records.append(payload)
            elif isinstance(payload, list):
                records.extend(item for item in payload if isinstance(item, dict))
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if raw and not raw.startswith("#"):
                row = json.loads(raw)
                if isinstance(row, dict):
                    records.append(row)
    return records


def normalize_depends_on(value: object) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                return [stripped]
            if isinstance(parsed, list):
                return [str(item) for item in parsed if str(item)]
        return [stripped]
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def live_work_item_tasks(done: set[str]) -> list[dict]:
    tasks: list[dict] = []
    for item in iter_current_records("live_work_items"):
        item_id = str(item.get("id") or "")
        if not item_id or item_id in done or task_completed(item_id) or claim_blocks_task(item_id):
            continue
        if str(item.get("work_status") or "open") != "open":
            continue
        stage = str(item.get("work_stage") or "")
        tasks.append(
            {
                "id": item_id,
                "priority": int(item.get("priority") or WORK_ITEM_STAGE_PRIORITY.get(stage, 50)),
                "kind": "live_work_item",
                "stage": stage,
                "live_id": item.get("live_id"),
                "source_candidate_id": item.get("source_candidate_id"),
                "scope": item.get("instructions") or item.get("natural_boundary") or item_id,
                "stream_task": False,
                "work_item": True,
                "depends_on": [],
            }
        )
    return tasks


def source_boundary_tasks(done: set[str]) -> list[dict]:
    tasks: list[dict] = []
    for item in iter_current_records("source_boundaries"):
        item_id = str(item.get("task_id") or item.get("id") or "")
        if not item_id:
            continue
        if item_id in done or task_completed(item_id) or claim_blocks_task(item_id):
            continue
        if str(item.get("status") or "open").lower() != "open":
            continue
        source = str(item.get("source_site") or item.get("source") or "").lower()
        boundary = item.get("natural_boundary") or item.get("url") or item_id
        tasks.append(
            {
                "id": item_id,
                "priority": int(item.get("priority") or 100),
                "kind": "source_boundary_discovery",
                "source_site": source,
                "stage": "source_discovery",
                "scope": (
                    f"Scan one natural {source.upper() if source else 'source'} "
                    f"boundary: {boundary}. Write source_candidates only, and append "
                    "new source_boundaries for any discovered next/list/detail pages."
                ),
                "stream_task": False,
                "source_boundary": True,
                "depends_on": normalize_depends_on(item.get("depends_on")),
            }
        )
    return tasks


def load_pilot_selection() -> dict:
    if not PILOT_SELECTION.exists():
        return {"groups": {}}
    return json.loads(PILOT_SELECTION.read_text(encoding="utf-8"))


def pilot_case_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    selection = load_pilot_selection()
    for group_name, cases in selection.get("groups", {}).items():
        for case in cases:
            index[case["pilot_case_id"]] = {**case, "group": group_name}
    return index


def task_records(directory: Path, task_id: str) -> list[tuple[Path, dict]]:
    records: list[tuple[Path, dict]] = []
    exact = directory / f"{task_id}.json"
    if exact.exists():
        payload = load_json_path(exact) or {}
        if not payload or payload.get("task_id") in {None, task_id}:
            records.append((exact, payload))
    if not directory.exists():
        return records
    for path in sorted(directory.glob("*.json")):
        if path == exact or not path.is_file():
            continue
        payload = load_json_path(path)
        if payload and payload.get("task_id") == task_id:
            records.append((path, payload))
    return records


def has_record(directory: Path, task_id: str) -> bool:
    return bool(task_records(directory, task_id))


def task_completed(task_id: str) -> bool:
    if task_records(COMPLETED, task_id):
        return True
    for _path, payload in task_records(CLAIMS, task_id):
        if str(payload.get("status") or "").lower() == "completed":
            return True
    return False


def claim_expired(payload: dict) -> bool:
    if str(payload.get("status") or "in_progress").lower() != "in_progress":
        return False
    claimed_at = parse_timestamp(payload.get("claimed_at"))
    if claimed_at is None:
        return False
    expires_at = claimed_at + timedelta(hours=STATIC_CLAIM_LEASE_HOURS)
    return datetime.now(timezone.utc) >= expires_at


def claim_blocks_task(task_id: str) -> bool:
    for _path, payload in task_records(CLAIMS, task_id):
        status = str(payload.get("status") or "in_progress").lower()
        if status == "completed":
            continue
        if claim_expired(payload):
            continue
        return True
    return False


def completed_ids() -> set[str]:
    done: set[str] = set()
    if not COMPLETED.exists():
        return done
    for path in COMPLETED.glob("*.json"):
        if not path.is_file():
            continue
        done.add(path.stem)
        payload = load_json_path(path)
        if payload and isinstance(payload.get("task_id"), str):
            done.add(payload["task_id"])
    if CLAIMS.exists():
        for path in CLAIMS.glob("*.json"):
            payload = load_json_path(path)
            if payload and str(payload.get("status") or "").lower() == "completed":
                task_id = payload.get("task_id")
                if isinstance(task_id, str) and task_id:
                    done.add(task_id)
    return done


def current_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def stream_task_id(stage: str, case_id: str) -> str:
    return f"S-{stage.upper()}-{case_id}"


def ready_path(stage: str, case_id: str) -> Path:
    return READY / stage / f"{case_id}.json"


def load_ready(stage: str, case_id: str) -> dict | None:
    path = ready_path(stage, case_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def scan_live_ids_for_date(date_hint: str | None) -> list[str]:
    if not date_hint:
        return []
    found: list[str] = []
    live_root = ROOT / "data" / "live_videos"
    if not live_root.exists():
        return []
    for path in live_root.rglob("*.jsonl"):
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if row.get("live_date") == date_hint and row.get("id"):
                found.append(str(row["id"]))
    for path in live_root.rglob("*.json"):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(row, dict) and row.get("live_date") == date_hint and row.get("id"):
            found.append(str(row["id"]))
    return sorted(set(found))


def infer_live_id(case: dict) -> str | None:
    marker = load_ready("collection", case["pilot_case_id"])
    if marker and marker.get("live_id"):
        return str(marker["live_id"])
    candidates = scan_live_ids_for_date(case.get("date_hint"))
    if len(candidates) == 1:
        return candidates[0]
    return None


def stream_tasks(done: set[str]) -> list[dict]:
    tasks: list[dict] = []
    selection = load_pilot_selection()

    for group_name, cases in selection.get("groups", {}).items():
        legacy_id = LEGACY_BATCH_TASKS.get(group_name)
        legacy_done = bool(legacy_id and legacy_id in done)
        legacy_active = bool(
            legacy_id
            and has_record(CLAIMS, legacy_id)
            and not legacy_done
        )

        for case in cases:
            case_id = case["pilot_case_id"]
            live_id = infer_live_id(case)

            collect_id = stream_task_id("collect", case_id)
            align_id = stream_task_id("align", case_id)
            audit_id = stream_task_id("audit", case_id)

            collection_ready = (
                ready_path("collection", case_id).exists()
                or legacy_done
                or collect_id in done
            )
            alignment_ready = (
                ready_path("alignment", case_id).exists()
                or align_id in done
            )
            audit_ready = (
                ready_path("audit", case_id).exists()
                or audit_id in done
            )

            common = {
                "case_id": case_id,
                "group": group_name,
                "date_hint": case.get("date_hint"),
                "seed_source_site": case.get("seed_source_site"),
                "seed_source_page_id": case.get("seed_source_page_id"),
                "seed_url": case.get("seed_url"),
                "live_id": live_id,
                "stream_task": True,
            }

            if not collection_ready:
                if legacy_active:
                    continue
                tasks.append(
                    {
                        **common,
                        "id": collect_id,
                        "stage": "collect",
                        "priority": STREAM_PRIORITIES["collect"],
                        "scope": (
                            f"Collect and identity-resolve {case_id} "
                            f"({case.get('date_hint')}); write independent source data "
                            "and mark this case collection-ready."
                        ),
                    }
                )
                continue

            if not alignment_ready:
                tasks.append(
                    {
                        **common,
                        "id": align_id,
                        "stage": "align",
                        "priority": STREAM_PRIORITIES["align"],
                        "scope": (
                            f"Align curated/ASR text and public time anchors for {case_id}"
                            + (f" / {live_id}" if live_id else "")
                            + "; write independent per-live segment data."
                        ),
                    }
                )
                continue

            if not audit_ready:
                tasks.append(
                    {
                        **common,
                        "id": audit_id,
                        "stage": "audit",
                        "priority": STREAM_PRIORITIES["audit"],
                        "scope": (
                            f"Playback-audit real segments for {case_id}"
                            + (f" / {live_id}" if live_id else "")
                            + "; record actual timing error and provenance."
                        ),
                    }
                )

    return tasks


def task_is_superseded(task: dict) -> bool:
    return bool(
        task.get("kind") == "legacy_record"
        or str(task.get("status_hint") or "").lower() == "superseded"
        or task.get("id") in LEGACY_GATE_TASKS
    )


def static_tasks(done: set[str]) -> list[dict]:
    eligible: list[dict] = []
    for task in load_queue():
        task_id = task["id"]
        if task_is_superseded(task):
            continue
        if task_id in done or task_completed(task_id):
            continue
        if claim_blocks_task(task_id):
            continue
        if any(dep not in done for dep in task.get("depends_on", [])):
            continue
        eligible.append({**task, "stream_task": False})
    return eligible


def eligible_tasks() -> list[dict]:
    done = completed_ids()
    workflow = load_workflow()
    legacy_stream_enabled = workflow.get("current_major_phase") != "PHASE_1_COLLECTION"
    tasks = source_boundary_tasks(done) + live_work_item_tasks(done) + static_tasks(done)
    if legacy_stream_enabled:
        tasks.extend(stream_tasks(done))
    filtered: list[dict] = []
    seen: set[str] = set()
    for task in tasks:
        task_id = task["id"]
        if task_is_superseded(task):
            continue
        if task_id in seen:
            continue
        seen.add(task_id)
        if task_id in done or task_completed(task_id):
            continue
        if claim_blocks_task(task_id):
            continue
        filtered.append(task)
    filtered.sort(key=lambda item: (-int(item.get("priority", 0)), item["id"]))
    return filtered


def candidate_order(
    eligible: list[dict],
    agent_id: str,
    requested_task: str | None,
) -> list[dict]:
    """Preserve priority bands while spreading Agents across same-priority tasks."""
    if requested_task:
        matches = [task for task in eligible if task["id"] == requested_task]
        if not matches:
            raise SystemExit(f"Task {requested_task!r} is not currently eligible.")
        return matches

    if not eligible:
        return []

    seed = int(hashlib.sha256(agent_id.encode("utf-8")).hexdigest(), 16)
    bands: dict[int, list[dict]] = defaultdict(list)
    for task in eligible:
        bands[int(task.get("priority", 0))].append(task)

    ordered: list[dict] = []
    for band_index, priority in enumerate(sorted(bands, reverse=True)):
        band = sorted(bands[priority], key=lambda item: item["id"])
        offset = (seed + band_index) % len(band)
        ordered.extend(band[offset:] + band[:offset])
    return ordered


def claim_task(task: dict, agent_id: str) -> Path:
    if task_is_superseded(task):
        raise SystemExit(f"Task {task.get('id')} is superseded and cannot be claimed.")
    CLAIMS.mkdir(parents=True, exist_ok=True)
    path = CLAIMS / f"{task['id']}.json"
    previous_claims = task_records(CLAIMS, task["id"])
    if previous_claims:
        active = [
            (claim_path, payload)
            for claim_path, payload in previous_claims
            if str(payload.get("status") or "in_progress").lower() != "completed"
            and not claim_expired(payload)
        ]
        if active:
            raise FileExistsError(path)
        archive_dir = CLAIM_ATTEMPTS / task["id"]
        archive_dir.mkdir(parents=True, exist_ok=True)
        for claim_path, payload in previous_claims:
            suffix = parse_timestamp(payload.get("claimed_at"))
            if suffix is None:
                suffix_text = claim_path.stem
            else:
                suffix_text = suffix.strftime("%Y%m%dT%H%M%SZ")
            archived = archive_dir / f"{suffix_text}-{payload.get('agent_id', 'unknown')}.json"
            counter = 1
            while archived.exists():
                archived = archive_dir / (
                    f"{suffix_text}-{payload.get('agent_id', 'unknown')}-{counter}.json"
                )
                counter += 1
            shutil.copy2(claim_path, archived)
            if claim_path == path:
                claim_path.unlink()
    payload = {
        "task_id": task["id"],
        "agent_id": agent_id,
        "claimed_at": utc_now(),
        "base_commit": current_commit(),
        "status": "in_progress",
        "workflow_mode": WORKFLOW_MODE,
        "claim_protocol": CLAIM_PROTOCOL,
        "continue_after_finish": True,
        "stage": task.get("stage"),
        "case_id": task.get("case_id"),
        "live_id": task.get("live_id"),
        "kind": task.get("kind"),
        "depends_on_at_claim": list(task.get("depends_on", [])),
        "scope": task.get("scope", ""),
        "reclaimed_expired_claim": bool(previous_claims),
        "static_claim_lease_hours": STATIC_CLAIM_LEASE_HOURS,
    }
    with path.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


def claim_from_candidates(
    eligible: list[dict],
    agent_id: str,
    requested_task: str | None,
    max_attempts: int,
) -> tuple[dict, Path] | None:
    ordered = candidate_order(eligible, agent_id, requested_task)
    if not ordered:
        return None

    attempt_limit = min(len(ordered), max(1, max_attempts))
    for attempt, task in enumerate(ordered[:attempt_limit], start=1):
        try:
            path = claim_task(task, agent_id)
            if attempt > 1:
                print(
                    f"CLAIM_SUCCESS after {attempt} attempts: {task['id']} "
                    f"({attempt - 1} local claim races skipped)."
                )
            return task, path
        except FileExistsError:
            print(
                f"CLAIM_RACE_LOST: {task['id']} already has a claim locally; "
                "trying another eligible task."
            )
            continue

    return None


def create_ready_marker(
    stage: str,
    case_id: str,
    agent_id: str,
    task_id: str,
    outputs: list[str],
    validation: str,
    live_id: str | None,
) -> Path:
    if stage == "collection" and not live_id:
        raise SystemExit("Collection readiness requires --live-id LIVE_YYYYMMDD_NNN.")
    marker_path = ready_path(stage, case_id)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker = {
        "project": "Miles-Guo_public_archive",
        "workflow_mode": WORKFLOW_MODE,
        "case_id": case_id,
        "live_id": live_id,
        "stage": stage,
        "ready_at": utc_now(),
        "task_id": task_id,
        "agent_id": agent_id,
        "result_commit": current_commit(),
        "outputs": outputs,
        "validation": validation,
    }
    with marker_path.open("x", encoding="utf-8") as fh:
        json.dump(marker, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return marker_path


def legacy_task_for_case(case_id: str) -> str | None:
    case = pilot_case_index().get(case_id)
    if not case:
        return None
    return LEGACY_BATCH_TASKS.get(case.get("group"))


def mark_ready_from_legacy(
    stage: str,
    case_id: str,
    agent_id: str,
    outputs: list[str],
    validation: str,
    live_id: str | None,
) -> Path:
    if stage != "collection":
        raise SystemExit(
            "--mark-ready is intended for grandfathered legacy collectors and currently "
            "supports only stage=collection. Streaming align/audit tasks should use --finish."
        )
    if case_id not in pilot_case_index():
        raise SystemExit(f"Unknown Pilot case: {case_id}")
    legacy_task = legacy_task_for_case(case_id)
    if not legacy_task:
        raise SystemExit(f"No legacy batch mapping for {case_id}.")
    claim_path = CLAIMS / f"{legacy_task}.json"
    if not claim_path.exists():
        raise SystemExit(
            f"Cannot publish legacy readiness: active claim {legacy_task} not found."
        )
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    if claim.get("agent_id") != agent_id:
        raise SystemExit(
            f"Cannot publish readiness for {case_id}: legacy claim belongs to "
            f"{claim.get('agent_id')!r}."
        )
    return create_ready_marker(
        stage="collection",
        case_id=case_id,
        agent_id=agent_id,
        task_id=legacy_task,
        outputs=outputs,
        validation=validation,
        live_id=live_id,
    )


def static_task_record(task_id: str) -> dict | None:
    for task in load_queue():
        if task.get("id") == task_id:
            return task
    return None


def validate_finish_prerequisites(task_id: str) -> dict | None:
    """Re-check the latest queue contract at finish time.

    A claim that was valid when created does not grandfather the task past dependencies
    that were added later. Superseded legacy gate identities can never be finished as
    current work.
    """
    task = static_task_record(task_id)
    if task is None:
        return None
    if task_is_superseded(task):
        raise SystemExit(
            f"Cannot finish {task_id}: this task identity is superseded/legacy and no "
            "longer belongs to the current acceptance chain."
        )

    done = completed_ids()
    missing = [dep for dep in task.get("depends_on", []) if dep not in done]
    if missing:
        raise SystemExit(
            f"Cannot finish {task_id}: latest queue prerequisites are incomplete: "
            + ", ".join(missing)
            + ". Refresh main and re-evaluate the task. Existing claims do not bypass "
              "newer finish-time dependencies."
        )

    if task_id == CURRENT_P9:
        sentinel_path = COMPLETED / "P9-PLAYBACK-GATE.json"
        if not sentinel_path.exists():
            raise SystemExit(
                f"Cannot finish {CURRENT_P9}: P9-PLAYBACK-GATE is not sealed."
            )
        try:
            sentinel = json.loads(sentinel_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(
                f"Cannot finish {CURRENT_P9}: invalid playback gate sentinel: {exc}"
            )
        validation = sentinel.get("validation") or {}
        if validation.get("pilot60_pass") is not True:
            raise SystemExit(
                f"Cannot finish {CURRENT_P9}: playback gate sentinel does not prove "
                "pilot60_pass=true."
            )
        return sentinel

    return None


def finish_task(
    task_id: str,
    agent_id: str,
    outputs: list[str],
    validation: str,
    live_id: str | None,
    full_archive_decision: str | None,
) -> tuple[Path, Path | None]:
    claim_path = CLAIMS / f"{task_id}.json"
    if not claim_path.exists():
        raise SystemExit(f"Cannot finish {task_id}: claim file does not exist.")
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    if claim.get("agent_id") != agent_id:
        raise SystemExit(
            f"Cannot finish {task_id}: claim belongs to {claim.get('agent_id')!r}."
        )

    gate_sentinel = validate_finish_prerequisites(task_id)

    if task_id == CURRENT_P10:
        if full_archive_decision not in {"YES", "NO"}:
            raise SystemExit(
                f"Finishing {CURRENT_P10} requires --full-archive-decision YES|NO."
            )
    elif full_archive_decision is not None:
        raise SystemExit(
            f"--full-archive-decision is valid only when finishing {CURRENT_P10}."
        )

    COMPLETED.mkdir(parents=True, exist_ok=True)
    completed_path = COMPLETED / f"{task_id}.json"
    payload = {
        "task_id": task_id,
        "agent_id": agent_id,
        "completed_at": utc_now(),
        "result_commit": current_commit(),
        "outputs": outputs,
        "validation": validation,
        "workflow_mode": claim.get("workflow_mode", "legacy-grandfathered"),
        "claim_protocol": claim.get("claim_protocol", "legacy"),
        "continue_after_finish": claim.get("workflow_mode") == WORKFLOW_MODE,
        "finish_prerequisites_revalidated": True,
        "notes": (
            "Task completed only after re-checking the latest repository dependency "
            "contract. Under continuous-worker-v2, refresh repository state and claim "
            "the next eligible task unless a documented stop condition applies."
        ),
    }

    if task_id == CURRENT_P9:
        payload["gate_outcome"] = "pass"
        payload["playback_gate_task"] = "P9-PLAYBACK-GATE"
        payload["playback_gate_validation"] = (gate_sentinel or {}).get("validation")

    if task_id == CURRENT_P10:
        payload["full_archive_decision"] = full_archive_decision
        payload["full_archive_authorized"] = full_archive_decision == "YES"

    with completed_path.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    marker_path: Path | None = None
    stage = claim.get("stage")
    case_id = claim.get("case_id")
    resolved_live_id = live_id or claim.get("live_id")

    marker_stage = {
        "collect": "collection",
        "align": "alignment",
        "audit": "audit",
    }.get(stage)

    if marker_stage and case_id:
        if stage == "collect" and not resolved_live_id:
            completed_path.unlink(missing_ok=True)
            raise SystemExit(
                "Collection completion requires --live-id LIVE_YYYYMMDD_NNN."
            )
        marker_path = create_ready_marker(
            stage=marker_stage,
            case_id=case_id,
            agent_id=agent_id,
            task_id=task_id,
            outputs=outputs,
            validation=validation,
            live_id=resolved_live_id,
        )

    return completed_path, marker_path


def print_task(task: dict) -> None:
    print(f"{task['id']} [priority={task.get('priority', 0)}]")
    print(f"  {task.get('scope', '')}")
    if task.get("case_id"):
        print(
            "  case="
            f"{task.get('case_id')} live_id={task.get('live_id') or 'unresolved'} "
            f"seed={task.get('seed_url') or '-'}"
        )


def choose_task(eligible: list[dict], task_id: str | None) -> dict:
    if not eligible:
        raise SystemExit("No currently eligible unclaimed task.")
    if not task_id:
        return eligible[0]
    matches = [task for task in eligible if task["id"] == task_id]
    if not matches:
        raise SystemExit(f"Task {task_id!r} is not currently eligible.")
    return matches[0]


def watch_for_task(
    poll_seconds: int,
    requested_task: str | None,
) -> list[dict]:
    if poll_seconds < 10:
        raise SystemExit("--poll-seconds must be at least 10 to avoid aggressive polling.")
    print(
        f"Watch mode active ({WORKFLOW_MODE}); polling every {poll_seconds}s. "
        "This process can still be stopped by the host platform or Ctrl+C."
    )
    while True:
        eligible = eligible_tasks()
        if requested_task:
            eligible = [task for task in eligible if task["id"] == requested_task]
        if eligible:
            return eligible
        print(f"[{utc_now()}] no eligible task yet; continuing watch")
        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover, claim, finish, and stream Miles-Guo_public_archive tasks."
    )
    parser.add_argument("--list", action="store_true", help="List eligible tasks.")
    parser.add_argument("--claim", action="store_true", help="Claim an eligible task.")
    parser.add_argument("--task", help="Specific eligible task ID to claim/watch for.")
    parser.add_argument("--agent-id", help="Unique agent ID for claim/finish/readiness.")
    parser.add_argument("--finish", metavar="TASK_ID", help="Finish a claimed task.")
    parser.add_argument("--outputs", nargs="*", default=[], help="Durable output paths.")
    parser.add_argument("--validation", help="What was actually validated.")
    parser.add_argument("--live-id", help="Canonical live ID, required for collection readiness.")
    parser.add_argument(
        "--full-archive-decision",
        choices=["YES", "NO"],
        help=(
            f"Required when finishing {CURRENT_P10}. Records the authoritative "
            "machine-readable FULL_ARCHIVE decision."
        ),
    )
    parser.add_argument(
        "--mark-ready",
        choices=["collection", "alignment", "audit"],
        help="Publish per-case readiness from a grandfathered legacy collector.",
    )
    parser.add_argument("--case-id", help="Pilot case ID for --mark-ready.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep scanning until eligible work appears; host suspension can still stop it.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=60,
        help="Watch polling interval; minimum 10 seconds, default 60.",
    )
    parser.add_argument(
        "--max-claim-attempts",
        type=int,
        default=10,
        help=(
            "Maximum eligible candidates tried in one local claim cycle after claim races; "
            "default 10."
        ),
    )
    args = parser.parse_args()

    if args.mark_ready:
        if not args.agent_id or not args.case_id or not args.validation:
            raise SystemExit(
                "--mark-ready requires --agent-id, --case-id, and --validation."
            )
        marker = mark_ready_from_legacy(
            stage=args.mark_ready,
            case_id=args.case_id,
            agent_id=args.agent_id,
            outputs=args.outputs,
            validation=args.validation,
            live_id=args.live_id,
        )
        print(f"Created readiness marker: {marker.relative_to(ROOT)}")
        print(
            "Commit/push this marker now. It unlocks downstream work for this case "
            "without ending the active legacy batch claim."
        )
        return

    if args.finish:
        if not args.agent_id:
            raise SystemExit("--finish requires --agent-id.")
        if not args.validation:
            raise SystemExit("--finish requires --validation.")
        completed_path, marker_path = finish_task(
            task_id=args.finish,
            agent_id=args.agent_id,
            outputs=args.outputs,
            validation=args.validation,
            live_id=args.live_id,
            full_archive_decision=args.full_archive_decision,
        )
        print(f"Created completion record: {completed_path.relative_to(ROOT)}")
        if marker_path:
            print(f"Created readiness marker: {marker_path.relative_to(ROOT)}")
        print(
            "Commit and push these coordination records, refresh repository state, then "
            "immediately claim the next eligible task. Finishing one task is not a stop "
            "condition under continuous-worker-v2."
        )
        return

    if args.watch:
        eligible = watch_for_task(args.poll_seconds, args.task)
    else:
        eligible = eligible_tasks()

    if not eligible:
        print("No currently eligible unclaimed task.")
        print(
            "Do not invent work. Check active claims for progress/staleness and follow "
            "coordination/README.md. A repository cannot wake a suspended host session."
        )
        return

    if args.list or (not args.claim and not args.watch):
        print("Eligible tasks (highest priority first):")
        for task in eligible:
            print_task(task)

    if not args.claim:
        print("\nRecommended next task:")
        print_task(choose_task(eligible, args.task))
        print(
            "\nClaim it with:\n"
            "python scripts/next_task.py --claim --agent-id agent-<UTC>-<random>"
        )
        return

    if not args.agent_id:
        raise SystemExit("--claim requires --agent-id.")

    claimed = claim_from_candidates(
        eligible=eligible,
        agent_id=args.agent_id,
        requested_task=args.task,
        max_attempts=args.max_claim_attempts,
    )
    if not claimed:
        raise SystemExit(
            "CLAIM_RACE_LOST: all attempted local candidates became unavailable. "
            "Refresh/pull repository state and run --claim again. This is not a "
            "GITHUB_WRITE_ERROR and not a reason to stop the continuous worker."
        )

    chosen, path = claimed
    print(f"Claim created locally: {path.relative_to(ROOT)}")
    print_task(chosen)
    print(
        f"  workflow_mode={WORKFLOW_MODE} claim_protocol={CLAIM_PROTOCOL} "
        "continue_after_finish=true"
    )
    print(
        "\nIMPORTANT: immediately commit and push the claim before doing the work. "
        "If the remote push/create loses a race, verify the exact remote claim path. "
        "If it now exists, classify CLAIM_RACE_LOST, refresh main, and claim another task."
    )
    print(
        "For GitHub API create_file: HTTP 422/409 are not automatically write outages. "
        "Fetch coordination/claims/<TASK_ID>.json first and classify against fresh main. "
        "Only call it GITHUB_WRITE_ERROR after the exact path remains absent across fresh, "
        "bounded retries as documented in coordination/CLAIM_PROTOCOL_V2.md."
    )
    print(
        "After the claim is visible on main: execute the task, validate real outputs, "
        "commit/push outputs, then run --finish. Finish revalidates the latest queue "
        "dependencies, so an older claim cannot bypass a newer gate. Superseded legacy "
        "P9/P10 identities can never be reclaimed or finished as current work."
    )


if __name__ == "__main__":
    main()

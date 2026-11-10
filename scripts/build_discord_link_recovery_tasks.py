#!/usr/bin/env python3
"""Build the date-first queue for records that lack a direct playback URL."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "data/source_page_evidence/discord/discord_project_live_master_by_date.jsonl"
OUTPUT = ROOT / "data/current/link_recovery_tasks/discord_direct_playback_recovery.jsonl"
REPORT = ROOT / "docs/DISCORD_LINK_RECOVERY_TASKS.md"

DIRECT_SITES = {
    "youtube",
    "rumble",
    "odysee",
    "gettr",
    "vimeo",
    "bitchute",
    "livestream",
}
DIRECT_ROLES = {
    "original_video",
    "backup_video",
    "mirror_video",
    "video",
    "playback",
    "livestream",
    "platform_video",
}


def is_direct_playback(link: dict) -> bool:
    role = str(link.get("role") or "").lower()
    site = str(link.get("site") or "").lower()
    url = str(link.get("url") or "").lower()
    return bool(
        role in DIRECT_ROLES
        or "video" in role
        or site in DIRECT_SITES
        or any(
            token in url
            for token in (
                "youtube.com/watch",
                "youtu.be/",
                "rumble.com/",
                "odysee.com/",
                "gettr.com/post/",
                "vimeo.com/",
            )
        )
    )


def load_rows() -> list[dict]:
    return [
        json.loads(line)
        for line in MASTER.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def task_for(row: dict, generated_at: str) -> dict:
    canonical = row.get("record_state") == "canonical_live"
    record_id = row.get("live_id") or row.get("candidate_id")
    task_id = f"LINKREC_{record_id}_direct_playback"
    title = str(row.get("title") or "")
    note = None
    if str(record_id).startswith("LIVE_20200710_00"):
        note = (
            "Check whether the known combined 2020-07-10 Bannon War Room mirror covers this "
            "individual part; do not assign the combined URL without exact part/content evidence."
        )
    return {
        "task_id": task_id,
        "record_id": record_id,
        "live_id": row.get("live_id"),
        "source_candidate_id": row.get("candidate_id"),
        "date": row.get("date"),
        "title": title,
        "record_state": row.get("record_state"),
        "task_type": "direct_playback_source_recovery",
        "task_status": "open",
        "queue_phase": "legacy_first" if canonical else "deferred_after_legacy",
        "priority": 110 if canonical else 60,
        "natural_boundary": "one independent video record and its direct playback source evidence",
        "reason": "Reachable source/detail page exists, but no independently verified direct platform playback URL is active.",
        "existing_active_links": row.get("active_links") or [],
        "inactive_or_unverified_links": row.get("inactive_or_unverified_links") or [],
        "search_order": [
            "Discord server 821933739307040799 link rooms, messages, and attachments",
            "user-provided MEGA historical folders",
            "outbound or embedded media locators on the existing GWINS/GHOT/GNEWS/VOG page",
            "exact date, source video id, and title on Rumble, Odysee, YouTube, and GETTR",
            "public web/archive mirrors with independently verifiable identity evidence",
        ],
        "completion_criteria": [
            "candidate URL resolves to a media-bearing platform locator",
            "date/title/source-id/duration or content evidence uniquely matches this record",
            "source and media-asset records are added without overwriting historical evidence",
            "active link and verification time are recorded and database/tests pass",
        ],
        "no_result_policy": (
            "Record every checked source and retryable restriction, leave the playback URL empty, "
            "and mark unresolved; never infer that media does not exist."
        ),
        "special_note": note,
        "claim_key": task_id,
        "created_at": generated_at,
        "updated_at": generated_at,
    }


def render_report(tasks: list[dict], generated_at: str) -> str:
    legacy = [task for task in tasks if task["queue_phase"] == "legacy_first"]
    deferred = [task for task in tasks if task["queue_phase"] == "deferred_after_legacy"]
    by_year = Counter(str(task.get("date") or "unknown")[:4] for task in deferred)
    lines = [
        "# Discord Direct Playback Link Recovery Queue",
        "",
        f"Generated from the date-first Discord/project master at `{generated_at}`.",
        "A reachable archive or detail page is not counted as a direct playback URL.",
        "",
        "## Queue summary",
        "",
        f"- Open tasks: **{len(tasks)}**",
        f"- Legacy canonical LIVE_ tasks (process first): **{len(legacy)}**",
        f"- VIDEO/source-candidate tasks (deferred until legacy completion): **{len(deferred)}**",
        "- Every task preserves its current archive/detail links and requires exact identity evidence.",
        "- An exhaustive search with no result stays `unresolved`; it is not labelled media-missing.",
        "",
        "## Legacy-first tasks",
        "",
        "| Task | Date | Record | Title | Existing source page |",
        "| --- | --- | --- | --- | --- |",
    ]
    for task in legacy:
        links = task.get("existing_active_links") or []
        url = links[0].get("url", "") if links else ""
        title = str(task.get("title") or "").replace("|", "\\|")
        lines.append(
            f"| `{task['task_id']}` | {task.get('date') or ''} | `{task.get('record_id')}` | {title} | {url} |"
        )
    lines.extend(["", "## Deferred queue by year", ""])
    for year, count in sorted(by_year.items()):
        lines.append(f"- {year}: {count}")
    lines.extend(
        [
            "",
            "## Processing rules",
            "",
            "1. Claim exactly one `task_id`; never overwrite an active claim.",
            "2. Search Discord and the user-provided MEGA folders before public mirrors.",
            "3. Verify identity independently; same-day or similar-title matches are insufficient.",
            "4. Record restricted, dead, and retryable links separately from active playback links.",
            "5. Run database build, validation, and the complete test suite before completion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    tasks = [
        task_for(row, generated_at)
        for row in load_rows()
        if row.get("active_links")
        and not any(is_direct_playback(link) for link in row.get("active_links") or [])
    ]
    tasks.sort(
        key=lambda task: (
            -int(task["priority"]),
            str(task.get("date") or ""),
            str(task.get("record_id") or ""),
        )
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(task, ensure_ascii=False, sort_keys=True) + "\n" for task in tasks),
        encoding="utf-8",
    )
    REPORT.write_text(render_report(tasks, generated_at), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(OUTPUT.relative_to(ROOT)),
                "tasks": len(tasks),
                "legacy_first": sum(task["queue_phase"] == "legacy_first" for task in tasks),
                "deferred": sum(task["queue_phase"] == "deferred_after_legacy" for task in tasks),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

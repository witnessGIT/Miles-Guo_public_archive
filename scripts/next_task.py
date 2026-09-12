from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "coordination" / "WORK_QUEUE.jsonl"
CLAIMS = ROOT / "coordination" / "claims"
COMPLETED = ROOT / "coordination" / "completed"


def load_queue() -> list[dict]:
    tasks: list[dict] = []
    for raw in QUEUE.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            tasks.append(json.loads(raw))
    return tasks


def has_record(directory: Path, task_id: str) -> bool:
    return (directory / f"{task_id}.json").exists()


def main() -> None:
    tasks = load_queue()
    completed_ids = {
        p.stem for p in COMPLETED.glob("*.json") if p.name != "README.json"
    }
    eligible: list[dict] = []

    for task in tasks:
        task_id = task["id"]
        if task_id in completed_ids or has_record(COMPLETED, task_id):
            continue
        if has_record(CLAIMS, task_id):
            continue
        if any(dep not in completed_ids and not has_record(COMPLETED, dep) for dep in task.get("depends_on", [])):
            continue
        eligible.append(task)

    eligible.sort(key=lambda item: (-int(item.get("priority", 0)), item["id"]))

    if not eligible:
        print("No currently eligible unclaimed task.")
        return

    print("Eligible tasks (highest priority first):")
    for task in eligible:
        print(f"- {task['id']} [priority={task.get('priority', 0)}] {task.get('scope', '')}")

    print("\nRecommended next task:")
    print(eligible[0]["id"])
    print("\nBefore starting, atomically create coordination/claims/<TASK_ID>.json as required by coordination/README.md.")


if __name__ == "__main__":
    main()

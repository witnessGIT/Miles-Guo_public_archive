"""One-shot branch-only patch; removed before this branch can be merged."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "scripts/next_task.py": "e9b21dd6a494480acb22bfa348b9fe421365495d",
    "scripts/validate_candidate_reviews.py": "98b3ee344f779da2261d83c66cbad957a044e6b4",
}
texts = {}
for name, expected in EXPECTED.items():
    raw = (ROOT / name).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if actual != expected:
        raise SystemExit(f"Refusing stale patch for {name}: {actual} != {expected}")
    texts[name] = raw.decode("utf-8")


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise SystemExit("Patch context is not unique; no overwrite attempted")
    return text.replace(old, new, 1)


old_expired = '''def claim_expired(payload: dict, *, now: datetime | None = None) -> bool:
    if str(payload.get("status") or "in_progress").lower() != "in_progress":
        return False
    claimed_at = parse_timestamp(payload.get("claimed_at"))
    if claimed_at is None:
        return False
    lease_hours = payload.get("static_claim_lease_hours", STATIC_CLAIM_LEASE_HOURS)
    try:
        lease_hours = float(lease_hours)
    except (TypeError, ValueError):
        lease_hours = float(STATIC_CLAIM_LEASE_HOURS)
    expires_at = claimed_at + timedelta(hours=lease_hours)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return current >= expires_at
'''
new_expired = '''def claim_lease_hours(payload: dict) -> float:
    """Resolve the effective lease without rewriting immutable claim history.

    Candidate reviews have a fixed policy lease. Their optional static-task
    metadata cannot extend or shorten it, including on older chat claims.
    Non-C2 tasks retain their existing configurable lease and fallback.
    """
    if (
        str(payload.get("task_id") or "").startswith(CANDIDATE_REVIEW_PREFIX)
        or payload.get("kind") == "candidate_promotion_review"
    ):
        return float(CANDIDATE_REVIEW_CLAIM_TIMEOUT_HOURS)
    lease_hours = payload.get("static_claim_lease_hours", STATIC_CLAIM_LEASE_HOURS)
    try:
        return float(lease_hours)
    except (TypeError, ValueError):
        return float(STATIC_CLAIM_LEASE_HOURS)


def claim_expired(payload: dict, *, now: datetime | None = None) -> bool:
    if str(payload.get("status") or "in_progress").lower() != "in_progress":
        return False
    claimed_at = parse_timestamp(payload.get("claimed_at"))
    if claimed_at is None:
        return False
    expires_at = claimed_at + timedelta(hours=claim_lease_hours(payload))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return current >= expires_at
'''
name = "scripts/next_task.py"
texts[name] = replace_once(texts[name], old_expired, new_expired)
texts[name] = replace_once(
    texts[name],
    "            + timedelta(hours=CANDIDATE_REVIEW_CLAIM_TIMEOUT_HOURS)\n            if active_claimed_at is not None",
    "            + timedelta(hours=claim_lease_hours(active_claim or {}))\n            if active_claimed_at is not None",
)

name = "scripts/validate_candidate_reviews.py"
texts[name] = replace_once(texts[name], "    failures: list[str] = []\n", "    failures: list[str] = []\n    lease_warnings: list[dict] = []\n")
old = '''        batch_id = str(payload.get("review_batch_id") or "")
'''
new = '''        effective_hours = next_task.claim_lease_hours(payload)
        if effective_hours != next_task.CANDIDATE_REVIEW_CLAIM_TIMEOUT_HOURS:
            failures.append(f"{path.relative_to(next_task.ROOT)}: invalid effective C2 lease")
        # Legacy metadata stays immutable. Report discrepancies, but enforce
        # the same fixed policy used by scheduling and the expiry display.
        for field in ("review_claim_timeout_hours", "static_claim_lease_hours"):
            if field not in payload:
                continue
            value = payload[field]
            try:
                consistent = not isinstance(value, bool) and float(value) == effective_hours
            except (TypeError, ValueError, OverflowError):
                consistent = False
            if not consistent:
                lease_warnings.append({
                    "path": str(path.relative_to(next_task.ROOT)),
                    "field": field,
                    "declared_value": value,
                    "effective_hours": effective_hours,
                })
        batch_id = str(payload.get("review_batch_id") or "")
'''
texts[name] = replace_once(texts[name], old, new)
texts[name] = replace_once(
    texts[name],
    '    print(json.dumps({"status": "PASS", "checked": checked, "batches": len(batches)}, ensure_ascii=False))',
    '    print(json.dumps({"status": "PASS", "checked": checked, "batches": len(batches), "lease_warnings": lease_warnings}, ensure_ascii=False))',
)
# Check both complete modules before writing either one.
for name, text in texts.items():
    compile(text, name, "exec")
for name, text in texts.items():
    (ROOT / name).write_text(text, encoding="utf-8")
    print(f"Applied verified C2 lease patch: {name}")

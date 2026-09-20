#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "coordination" / "claims"
REQUEST_ROOT = ROOT / "coordination" / "source_fetch_requests"
EVIDENCE_ROOT = ROOT / "data" / "source_page_evidence"

REQUEST_VERSION = "source-fetch-request-v1"
EVIDENCE_VERSION = "source-page-evidence-v1"
ALLOWED_HOSTS = {"gwins.org", "www.gwins.org"}
MAX_PAGE_BYTES = 5 * 1024 * 1024
USER_AGENT = "Miles-Guo-public-archive-source-evidence/1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def request_sha256(value: dict) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def validate_url(raw: str) -> str:
    parsed = urlparse(raw)
    if parsed.scheme != "https":
        raise ValueError("source_url must use HTTPS")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("source_url must not contain credentials or a custom port")
    if (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise ValueError("source_url host is not allowlisted")
    return raw


def safe_component(raw: object, field: str) -> str:
    value = str(raw or "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise ValueError(f"{field} contains unsafe characters")
    return value


def load_and_validate_request(path: Path) -> dict:
    try:
        path.resolve().relative_to(REQUEST_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("request must be under coordination/source_fetch_requests") from exc
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("request must be a JSON object")
    required = {"request_version", "task_id", "agent_id", "source_site", "source_page_id", "source_url", "requested_at"}
    missing = sorted(required - value.keys())
    if missing:
        raise ValueError(f"request missing fields: {', '.join(missing)}")
    if value["request_version"] != REQUEST_VERSION:
        raise ValueError(f"unsupported request_version: {value['request_version']}")
    safe_component(value["task_id"], "task_id")
    safe_component(value["agent_id"], "agent_id")
    site = safe_component(value["source_site"], "source_site").lower()
    page_id = safe_component(value["source_page_id"], "source_page_id")
    if site != "gwins":
        raise ValueError("only the gwins source adapter is currently supported")
    if not re.fullmatch(r"list_2_\d+", page_id):
        raise ValueError("unsupported GWINS source_page_id")
    expected_suffix = f"/cn/milesguo/{page_id}.html"
    source_url = validate_url(str(value["source_url"]))
    if urlparse(source_url).path != expected_suffix:
        raise ValueError(f"source_url path must be {expected_suffix}")

    claim_path = CLAIMS / f"{value['task_id']}.json"
    if not claim_path.exists():
        raise ValueError("active task claim does not exist")
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    if claim.get("agent_id") != value["agent_id"]:
        raise ValueError("request agent_id does not own the task claim")
    if claim.get("status") != "in_progress":
        raise ValueError("task claim is not in_progress")
    if claim.get("task_id") != value["task_id"]:
        raise ValueError("claim task_id mismatch")
    return value


class GWINSParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.items: list[dict] = []
        self.pagination_urls: set[str] = set()
        self._title_href: str | None = None
        self._title_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        values = {key.lower(): value or "" for key, value in attrs}
        href = values.get("href", "")
        classes = set(values.get("class", "").split())
        absolute = urljoin(self.base_url, href)
        if "title" in classes:
            self._title_href = absolute
            self._title_text = []
        if re.search(r"/cn/milesguo/list_2_\d+\.html$", urlparse(absolute).path):
            self.pagination_urls.add(absolute)

    def handle_data(self, data: str) -> None:
        if self._title_href is not None:
            self._title_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._title_href is None:
            return
        title = re.sub(r"\s+", " ", html.unescape("".join(self._title_text))).strip()
        detail_url = self._title_href
        detail_id_match = re.search(r"/(\d+)\.html$", urlparse(detail_url).path)
        video_id_match = re.search(r"(?<!\d)(20\d{6}_\d+)(?!\d)", title)
        date_match = re.search(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)", title)
        self.items.append({
            "title": title,
            "detail_url": detail_url,
            "detail_id": detail_id_match.group(1) if detail_id_match else None,
            "source_video_id": video_id_match.group(1) if video_id_match else None,
            "candidate_date": "-".join(date_match.groups()) if date_match else None,
        })
        self._title_href = None
        self._title_text = []


def parse_gwins_page(raw: bytes, source_url: str) -> dict:
    text = raw.decode("utf-8", errors="replace")
    parser = GWINSParser(source_url)
    parser.feed(text)
    if not parser.items:
        raise ValueError("GWINS page contained no title records")
    return {"items": parser.items, "pagination_urls": sorted(parser.pagination_urls)}


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_page(source_url: str) -> tuple[bytes, str, int, str]:
    request = urllib.request.Request(source_url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    opener = urllib.request.build_opener(SafeRedirectHandler())
    with opener.open(request, timeout=30) as response:
        final_url = validate_url(response.geturl())
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"unexpected content type: {content_type}")
        raw = response.read(MAX_PAGE_BYTES + 1)
        if len(raw) > MAX_PAGE_BYTES:
            raise ValueError("source page exceeds maximum allowed size")
        return raw, final_url, int(response.status), content_type


def process_request(path: Path, *, force: bool = False) -> Path:
    request = load_and_validate_request(path)
    req_sha = request_sha256(request)
    site = str(request["source_site"]).lower()
    page_id = str(request["source_page_id"])
    output_dir = EVIDENCE_ROOT / site / page_id
    evidence_path = output_dir / "evidence.json"
    if evidence_path.exists() and not force:
        old = json.loads(evidence_path.read_text(encoding="utf-8"))
        if old.get("request_sha256") == req_sha:
            return evidence_path

    raw, final_url, status, content_type = fetch_page(str(request["source_url"]))
    parsed = parse_gwins_page(raw, final_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "page.html"
    raw_path.write_bytes(raw)
    evidence = {
        "evidence_version": EVIDENCE_VERSION,
        "request_version": REQUEST_VERSION,
        "request_path": str(path.resolve().relative_to(ROOT.resolve())),
        "request_sha256": req_sha,
        "task_id": request["task_id"],
        "agent_id": request["agent_id"],
        "source_site": site,
        "source_page_id": page_id,
        "requested_url": request["source_url"],
        "final_url": final_url,
        "fetched_at": utc_now(),
        "http_status": status,
        "content_type": content_type,
        "raw_page_path": str(raw_path.resolve().relative_to(ROOT.resolve())),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
        "item_count": len(parsed["items"]),
        "items": parsed["items"],
        "pagination_urls": parsed["pagination_urls"],
    }
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and parse one claimed source-page request")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        output = process_request(args.request, force=args.force)
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(f"source fetch request failed: {exc}", file=sys.stderr)
        return 1
    print(output.resolve().relative_to(ROOT.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

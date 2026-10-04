#!/usr/bin/env python3
"""Read public GWINS metadata for owned C2 claims; never complete or process media."""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "c2-metadata-request-v1"
MAX_BYTES = 2_000_000
SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,180}\Z")
DETAIL_PATH = re.compile(r"/cn/milesguo/[0-9]+\.html\Z")
CUE = re.compile(r"录.{0,12}(?:视频|一段|这一|这段)|(?:视频|一段|今天|刚才).{0,12}录|拍摄|直播|上半场|下半场")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def allowed_url(url: str) -> str:
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname not in {"gwins.org", "www.gwins.org"}
            or p.username or p.password or p.port is not None or p.query or p.fragment
            or not DETAIL_PATH.fullmatch(p.path)):
        raise ValueError("Only exact public HTTPS GWINS numeric detail pages are allowed")
    return url


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl)
        if urlsplit(req.full_url).path != urlsplit(newurl).path:
            raise ValueError("Redirect changed the claimed detail identity")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.titles, self.links, self.metadata = [], [], [], {}
        self.hidden = 0
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag == "title":
            self.in_title = True
        if tag in {"p", "div", "br", "li", "h1", "h2", "tr"}:
            self.parts.append("\n")
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "iframe" and a.get("src"):
            self.links.append(a["src"])
        if tag == "meta" and a.get("content"):
            key = a.get("property") or a.get("name")
            if key in {"og:title", "og:description", "description", "article:published_time"}:
                self.metadata[key] = a["content"][:1000]

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        if tag == "title":
            self.in_title = False
        if tag in {"p", "div", "li", "h1", "h2", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)
            if self.in_title:
                self.titles.append(data)


def parse_page(raw: bytes, url: str, video_id: str) -> dict:
    # GWINS declares UTF-8. Strict decoding prevents silently archiving mojibake.
    text = raw.decode("utf-8-sig", errors="strict")
    page = Page()
    page.feed(text)
    paragraphs = [re.sub(r"\s+", " ", s).strip() for s in "".join(page.parts).splitlines()]
    paragraphs = [s for s in paragraphs if s]
    cues = []
    for index, paragraph in enumerate(paragraphs):
        for match in CUE.finditer(paragraph):
            excerpt = paragraph[max(0, match.start()-65):match.end()+110]
            if excerpt not in [x["excerpt"] for x in cues]:
                cues.append({"paragraph_index": index, "excerpt": excerpt})
            if len(cues) >= 40:
                break
        if len(cues) >= 40:
            break
    links = []
    for value in page.links:
        target = urljoin(url, value)
        p = urlsplit(target)
        if (p.scheme in {"http", "https"} and not p.username and not p.password
                and p.hostname in {"gettr.com", "www.gettr.com", "rumble.com", "www.rumble.com",
                                   "youtube.com", "www.youtube.com", "youtu.be", "ghot.ai"}):
            if target not in links:
                links.append(target)
    return {"page_title": "".join(page.titles).strip(), "metadata": page.metadata,
            "expected_source_video_id": video_id,
            "expected_id_visible": bool(video_id and video_id in "\n".join(paragraphs)),
            "outbound_links": links[:60], "identity_type_cues": cues,
            "cue_warning": "Excerpts may discuss other recordings; a reviewer must resolve context. No automatic type decision."}


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object: {path}")
    return value


def load_candidate(candidate_id: str) -> dict:
    for path in sorted((ROOT / "data/current/source_candidates").rglob("*")):
        if path.suffix not in {".json", ".jsonl"}:
            continue
        raw = path.read_text(encoding="utf-8")
        if candidate_id not in raw:
            continue
        if path.suffix == ".jsonl":
            rows = [json.loads(s) for s in raw.splitlines() if s.strip() and not s.startswith("#")]
        else:
            value = json.loads(raw)
            rows = value if isinstance(value, list) else [value]
        for row in rows:
            if isinstance(row, dict) and row.get("id") == candidate_id:
                return row
    raise ValueError("Candidate missing from current data")


def validate_member(task_id: str, agent_id: str, batch_id: str) -> tuple[dict, dict, str]:
    if not SAFE_ID.fullmatch(task_id) or not task_id.startswith("C2-REVIEW-"):
        raise ValueError("Invalid task ID")
    claim = read_json(ROOT / "coordination/claims" / (task_id + ".json"))
    if (claim.get("agent_id") != agent_id or claim.get("review_batch_id") != batch_id
            or claim.get("status") != "in_progress"
            or claim.get("candidate_review_contract") != "candidate-review-evidence-v2"):
        raise ValueError("Request is not bound to this active owned evidence-v2 batch")
    stamp = datetime.fromisoformat(claim["claimed_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None or datetime.now(timezone.utc) >= stamp + timedelta(hours=10):
        raise ValueError("Claim expired or lacks timezone")
    if (ROOT / "coordination/completed" / (task_id + ".json")).exists():
        raise ValueError("Candidate already completed")
    candidate = load_candidate(claim["source_candidate_id"])
    meta = candidate.get("metadata_json") or {}
    if isinstance(meta, str):
        meta = json.loads(meta)
    url = allowed_url(meta.get("detail_url", ""))
    return claim, candidate, url


def process_request(path: Path) -> None:
    request = read_json(path)
    if request.get("request_version") != CONTRACT:
        raise ValueError("Invalid request version")
    tasks = request.get("task_ids")
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 20 or len(set(tasks)) != len(tasks):
        raise ValueError("Expected 1..20 unique already-owned task IDs; this does not create claims")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    output_root = ROOT / "data/source_page_evidence/c2_metadata"
    opener = build_opener(SafeRedirect())
    for task_id in tasks:
        if not isinstance(task_id, str) or not SAFE_ID.fullmatch(task_id) or not task_id.startswith("C2-REVIEW-"):
            raise ValueError("Invalid task ID")
        out = output_root / task_id / (digest[:16] + ".json")
        if out.exists():
            continue
        if (ROOT / "coordination/completed" / (task_id + ".json")).exists():
            print(json.dumps({"task_id": task_id, "status": "already_completed_skip"}))
            continue
        claim, candidate, url = validate_member(task_id, request["agent_id"], request["review_batch_id"])
        result = {"evidence_version": "c2-metadata-evidence-v1", "request_sha256": digest,
                  "task_id": task_id, "source_candidate_id": candidate["id"],
                  "agent_id": claim["agent_id"], "requested_url": url, "fetched_at": now(),
                  "review_decision": None, "media_download_performed": False,
                  "playback_audit_performed": False, "source_text_imported": False}
        try:
            req = Request(url, headers={"User-Agent": "Miles-Guo_public_archive/metadata-evidence-v1", "Accept": "text/html"})
            with opener.open(req, timeout=20) as response:
                final_url = allowed_url(response.geturl())
                kind = response.headers.get_content_type()
                if kind not in {"text/html", "application/xhtml+xml"}:
                    raise ValueError("Non-HTML response refused; media is never fetched")
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("Page exceeds bounded metadata size")
                result.update({"status": "fetched", "http_status": response.status,
                               "final_url": final_url, "raw_bytes": len(raw),
                               "raw_sha256": hashlib.sha256(raw).hexdigest(),
                               "metadata_evidence": parse_page(raw, final_url, str(candidate.get("source_video_id") or ""))})
        except Exception as exc:
            result.update({"status": "fetch_failed", "error": f"{type(exc).__name__}: {exc}"[:500]})
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(json.dumps({"task_id": task_id, "status": result["status"], "output": str(out.relative_to(ROOT))}))
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args()
    process_request(args.request)

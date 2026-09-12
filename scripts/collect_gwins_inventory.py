#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.gwins.org/cn/milesguo/"
ITEM_RE = re.compile(r"/cn/milesguo/(\d+)\.html$")
ARCHIVE_ID_RE = re.compile(r"(20\d{6})_(\d+)")


def page_url(page: int) -> str:
    return BASE if page == 1 else urljoin(BASE, f"list_2_{page}.html")


def iso_date(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def clean_title(anchor_text: str, archive_id: str) -> str:
    pos = anchor_text.find(archive_id)
    if pos >= 0:
        tail = anchor_text[pos + len(archive_id):].strip(" -：:—")
        if tail:
            return tail
    return anchor_text.strip()


def collect(max_pages: int, sleep_s: float):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Miles-Guo_public_archive/1.0 (+https://github.com/witnessGIT/Miles-Guo_public_archive)"
    })

    seen_urls: set[str] = set()
    lives: dict[str, dict] = {}
    sources: dict[str, dict] = {}
    unresolved: dict[str, dict] = {}
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    empty_pages = 0
    for page in range(1, max_pages + 1):
        url = page_url(page)
        response = session.get(url, timeout=30)
        if response.status_code == 404:
            print(f"page {page}: 404, inventory end")
            break
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        soup = BeautifulSoup(response.text, "html.parser")

        raw_items = 0
        resolved_items = 0
        unresolved_items = 0
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            m_item = ITEM_RE.search(href)
            if not m_item or href in seen_urls:
                continue

            # A numeric Miles Guo article URL is itself a discovery fact. Keep it
            # even when the list-page label does not expose a parseable date/id.
            seen_urls.add(href)
            raw_items += 1
            article_id = m_item.group(1)
            text = " ".join(a.stripped_strings).strip()
            m_id = ARCHIVE_ID_RE.search(text)

            if not m_id:
                unresolved_items += 1
                unresolved[f"GWINS_UNRESOLVED_{article_id}"] = {
                    "discovery_id": f"GWINS_UNRESOLVED_{article_id}",
                    "source_site": "gwins",
                    "third_party_id": article_id,
                    "source_url": href,
                    "list_page": page,
                    "source_title": text,
                    "fetched_at": fetched_at,
                    "resolution_status": "unresolved",
                    "resolution_reason": "missing_standard_YYYYMMDD_sequence_in_list_label",
                }
                continue

            resolved_items += 1
            yyyymmdd, seq_text = m_id.groups()
            seq = int(seq_text)
            archive_id = f"{yyyymmdd}_{seq_text}"
            live_id = f"LIVE_{yyyymmdd}_{seq:03d}"
            content_type = "livestream" if "直播" in text else ("video" if "盖特" in text else "unknown")

            lives[live_id] = {
                "live_id": live_id,
                "published_date": iso_date(yyyymmdd),
                "sequence_no": seq,
                "title": clean_title(text, archive_id),
                "content_type": content_type,
                "language": "zh",
                "duration_sec": None,
                "width": None,
                "height": None,
                "quality_status": "inventory_unverified",
                "notes": f"Discovered from GWINS list page {page}; detail page not yet enriched.",
                "created_at": fetched_at,
            }
            sources[f"SRC_GWINS_{article_id}"] = {
                "source_id": f"SRC_GWINS_{article_id}",
                "live_id": live_id,
                "source_site": "gwins",
                "source_url": href,
                "third_party_id": article_id,
                "original_platform": None,
                "original_url": None,
                "fetched_at": fetched_at,
                "source_level": "discovery",
                "is_primary": 0,
                "metadata_json": json.dumps({"gwins_item_id": archive_id, "list_page": page}, ensure_ascii=False),
            }

        print(
            f"page {page}: {raw_items} raw, "
            f"{resolved_items} resolved, {unresolved_items} unresolved"
        )
        if raw_items == 0:
            empty_pages += 1
            if empty_pages >= 2:
                break
        else:
            empty_pages = 0
        if sleep_s:
            time.sleep(sleep_s)

    return lives, sources, unresolved


def write_jsonl(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--sleep", type=float, default=0.25)
    args = parser.parse_args()

    lives, sources, unresolved = collect(args.max_pages, args.sleep)
    if not lives and not unresolved:
        raise SystemExit("No GWINS items collected")

    write_jsonl(ROOT / "data/live_videos/gwins_inventory.jsonl", [lives[k] for k in sorted(lives)])
    write_jsonl(ROOT / "data/sources/gwins_inventory.jsonl", [sources[k] for k in sorted(sources)])
    write_jsonl(
        ROOT / "data/archive_items/gwins_unresolved.jsonl",
        [unresolved[k] for k in sorted(unresolved)],
    )
    print(
        "GWINS inventory complete: "
        f"{len(lives)} resolved live records, {len(sources)} resolved sources, "
        f"{len(unresolved)} unresolved discovery records, "
        f"{len(lives) + len(unresolved)} total discovered items"
    )


if __name__ == "__main__":
    main()

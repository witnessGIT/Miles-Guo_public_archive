#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "Miles-Guo_public_archive.sqlite3"
SCHEMA_PATH = ROOT / "schema" / "schema.sql"


def load_jsonl(pattern: str):
    for path_str in sorted(glob.glob(str(ROOT / pattern))):
        path = Path(path_str)
        with path.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    yield path, line_no, json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"Invalid JSONL: {path}:{line_no}: {exc}") from exc


def insert_named(conn: sqlite3.Connection, table: str, record: dict):
    cols = list(record.keys())
    # Files are loaded in deterministic filename order. Inventory files are
    # intentionally named before pilot/enriched files, so richer verified
    # records can replace lightweight discovery rows with the same id.
    sql = f"INSERT OR REPLACE INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})"
    conn.execute(sql, [record[c] for c in cols])


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        for _, _, record in load_jsonl("data/live_videos/*.jsonl"):
            insert_named(conn, "live_videos", record)

        for _, _, record in load_jsonl("data/sources/*.jsonl"):
            insert_named(conn, "sources", record)

        # Optional normalized transcript files.
        for _, _, record in load_jsonl("data/archive_items/transcripts/*.jsonl"):
            insert_named(conn, "transcripts", record)

        for _, _, record in load_jsonl("data/live_segments/*.jsonl"):
            insert_named(conn, "transcript_segments", record)

        # Rebuild FTS from canonical relational tables.
        conn.execute("DELETE FROM archive_fts")
        rows = conn.execute(
            """
            SELECT lv.live_id, lv.title,
                   COALESCE(GROUP_CONCAT(t.transcript_text, '\n'), '')
            FROM live_videos lv
            LEFT JOIN transcripts t ON t.live_id = lv.live_id
            GROUP BY lv.live_id, lv.title
            ORDER BY lv.live_id
            """
        ).fetchall()
        conn.executemany(
            "INSERT INTO archive_fts(live_id,title,transcript_text) VALUES (?,?,?)",
            rows,
        )
        conn.commit()

        print(f"built: {DB_PATH}")
        print("live_videos:", conn.execute("SELECT COUNT(*) FROM live_videos").fetchone()[0])
        print("sources:", conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0])
        print("transcripts:", conn.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0])
        print("segments:", conn.execute("SELECT COUNT(*) FROM transcript_segments").fetchone()[0])
    finally:
        conn.close()


if __name__ == "__main__":
    main()

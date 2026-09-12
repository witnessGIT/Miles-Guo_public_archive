#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "Miles-Guo_public_archive.sqlite3"


def fail(message: str):
    raise SystemExit(f"VALIDATION FAILED: {message}")


def main():
    if not DB_PATH.exists():
        fail(f"database does not exist: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            fail(f"integrity_check={integrity}")

        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            fail(f"foreign_key_check returned {len(fk)} row(s)")

        live_count = conn.execute("SELECT COUNT(*) FROM live_videos").fetchone()[0]
        source_count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        if live_count == 0:
            fail("no live_videos records")
        if source_count == 0:
            fail("no source records")

        orphan = conn.execute(
            """
            SELECT lv.live_id
            FROM live_videos lv
            LEFT JOIN sources s ON s.live_id=lv.live_id
            GROUP BY lv.live_id
            HAVING COUNT(s.source_id)=0
            """
        ).fetchall()
        if orphan:
            fail(f"videos without sources: {orphan[:10]}")

        bad_ids = conn.execute(
            "SELECT live_id FROM live_videos WHERE live_id NOT GLOB 'LIVE_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9]'"
        ).fetchall()
        if bad_ids:
            fail(f"invalid live_id format: {bad_ids[:10]}")

        fts_count = conn.execute("SELECT COUNT(*) FROM archive_fts").fetchone()[0]
        if fts_count != live_count:
            fail(f"FTS row count {fts_count} != live_videos {live_count}")

        print("validation: OK")
        print("live_videos:", live_count)
        print("sources:", source_count)
        print("fts_rows:", fts_count)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

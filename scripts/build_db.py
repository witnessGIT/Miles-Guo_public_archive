#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator

PROJECT_NAME = "Miles-Guo_public_archive"
DATABASE_NAME = "Miles-Guo_public_archive.sqlite3"

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEMA_PATH = ROOT / "schema" / "schema.sql"
DATABASE_DIR = ROOT / "database"
DATABASE_PATH = DATABASE_DIR / DATABASE_NAME
TEMP_DATABASE_PATH = DATABASE_DIR / f"{DATABASE_NAME}.tmp"

# Directory -> target table. Paths are recursive and may contain independent
# per-agent/per-year/per-batch files.
DATASETS: tuple[tuple[str, str], ...] = (
    ("live_videos", "live_videos"),
    ("sources", "live_sources"),
    ("live_segments", "live_segments"),
    ("archive_items", "archive_items"),
    ("entities", "entities"),
    ("topics", "topics"),
    ("item_entities", "item_entities"),
    ("item_topics", "item_topics"),
    ("source_match_candidates", "source_match_candidates"),
)


def iter_data_files(relative_dir: str) -> Iterator[Path]:
    base = DATA_DIR / relative_dir
    if not base.exists():
        return
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl"}:
            yield path


def _records_from_json(path: Path) -> Iterable[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        yield payload
        return
    if isinstance(payload, list):
        for index, item in enumerate(payload, 1):
            if not isinstance(item, dict):
                raise ValueError(f"{path}: JSON list item {index} is not an object")
            yield item
        return
    raise ValueError(f"{path}: top-level JSON must be an object or list of objects")


def _records_from_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            text = raw.strip()
            if not text or text.startswith("#"):
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_no}: JSONL row must be an object")
            yield item


def iter_records(path: Path) -> Iterable[dict]:
    if path.suffix.lower() == ".json":
        return _records_from_json(path)
    if path.suffix.lower() == ".jsonl":
        return _records_from_jsonl(path)
    raise ValueError(f"Unsupported data file: {path}")


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if not rows:
        raise RuntimeError(f"schema table missing: {table}")
    return {str(row[1]) for row in rows}


def insert_record(
    conn: sqlite3.Connection,
    table: str,
    record: dict,
    source_path: Path,
    source_index: int,
) -> None:
    if not record:
        raise ValueError(f"{source_path}: record {source_index} is empty")

    allowed = table_columns(conn, table)
    unknown = sorted(set(record) - allowed)
    if unknown:
        raise ValueError(
            f"{source_path}: record {source_index} has unknown columns for {table}: {unknown}"
        )

    columns = list(record.keys())
    placeholders = ",".join("?" for _ in columns)
    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
    try:
        conn.execute(sql, [record[column] for column in columns])
    except sqlite3.Error as exc:
        raise RuntimeError(
            f"failed inserting {source_path} record {source_index} into {table}: {exc}"
        ) from exc


def load_dataset(conn: sqlite3.Connection, relative_dir: str, table: str) -> int:
    count = 0
    for path in iter_data_files(relative_dir):
        for record_index, record in enumerate(iter_records(path), 1):
            insert_record(conn, table, record, path, record_index)
            count += 1
    return count


def rebuild_fts(conn: sqlite3.Connection) -> int:
    conn.execute("DELETE FROM live_segments_fts")
    rows = conn.execute(
        """
        SELECT
            id,
            live_id,
            COALESCE(text_curated, ''),
            COALESCE(text_asr, ''),
            COALESCE(
                text_search,
                TRIM(COALESCE(text_curated, '') || ' ' || COALESCE(text_asr, ''))
            )
        FROM live_segments
        ORDER BY live_id, segment_index, id
        """
    ).fetchall()
    conn.executemany(
        """
        INSERT INTO live_segments_fts(
            segment_id, live_id, text_curated, text_asr, text_search
        ) VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def build_database() -> dict[str, int]:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"schema missing: {SCHEMA_PATH}")

    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DATABASE_PATH.unlink(missing_ok=True)

    counts: dict[str, int] = {}
    conn = sqlite3.connect(TEMP_DATABASE_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        # Insert parent/core datasets first, then relationship datasets.
        for relative_dir, table in DATASETS:
            counts[table] = load_dataset(conn, relative_dir, table)

        counts["live_segments_fts"] = rebuild_fts(conn)

        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise RuntimeError(f"SQLite integrity_check failed: {integrity}")

        foreign_key_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            raise RuntimeError(f"foreign_key_check failed: {foreign_key_errors[:20]}")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    os.replace(TEMP_DATABASE_PATH, DATABASE_PATH)
    return counts


def main() -> None:
    counts = build_database()
    print(f"Project: {PROJECT_NAME}")
    print(f"built: {DATABASE_PATH}")
    for table in sorted(counts):
        print(f"{table}: {counts[table]}")


if __name__ == "__main__":
    main()

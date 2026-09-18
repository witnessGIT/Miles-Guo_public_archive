#!/usr/bin/env python3
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

from build_db import (
    DATASETS,
    DATABASE_PATH,
    iter_data_files,
    iter_records,
)

PROJECT_NAME = "Miles-Guo_public_archive"

LIVE_ID_RE = re.compile(r"^LIVE_\d{8}_\d{3}$")
SEGMENT_ID_RE = re.compile(r"^LIVE_\d{8}_\d{3}_SEG_\d{6}$")
SOURCE_ID_RE = re.compile(r"^SRC_[A-Za-z0-9_.-]+$")

REQUIRED_TABLES = {
    "source_candidates",
    "source_boundaries",
    "live_videos",
    "live_sources",
    "live_work_items",
    "live_segments",
    "source_match_candidates",
    "archive_items",
    "entities",
    "item_entities",
    "topics",
    "item_topics",
    "live_segments_fts",
    "media_assets", "transcript_versions", "transcript_cues", "segment_speakers", "segment_entities",
    "live_events", "segment_events", "segment_claims", "segment_relations",
    "segment_clip_notes", "evidence_links", "verification_checks",
}


def source_record_count(relative_dir: str) -> int:
    count = 0
    for path in iter_data_files(relative_dir):
        for _ in iter_records(path):
            count += 1
    return count


def table_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def add_warning(warnings: list[str], message: str) -> None:
    warnings.append(message)


def validate() -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts: dict[str, int] = {}

    if not DATABASE_PATH.exists():
        return [f"database missing: {DATABASE_PATH}; run python scripts/build_db.py first"], warnings, counts

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")

        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            add_error(errors, f"PRAGMA integrity_check failed: {integrity}")

        foreign_key_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            add_error(errors, f"foreign_key_check returned {len(foreign_key_errors)} violation(s)")

        actual_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
            ).fetchall()
        }
        missing_tables = sorted(REQUIRED_TABLES - actual_tables)
        if missing_tables:
            add_error(errors, f"missing required tables: {missing_tables}")
            return errors, warnings, counts

        # The SQLite artifact must faithfully reflect every tracked structured dataset.
        for relative_dir, table in DATASETS:
            source_count = source_record_count(relative_dir)
            db_count = table_count(conn, table)
            counts[table] = db_count
            if source_count != db_count:
                add_error(
                    errors,
                    f"source/database count mismatch for {table}: data={source_count}, db={db_count}",
                )

        segment_count = table_count(conn, "live_segments")
        fts_count = table_count(conn, "live_segments_fts")
        counts["live_segments_fts"] = fts_count
        if segment_count != fts_count:
            add_error(
                errors,
                f"FTS row count mismatch: live_segments={segment_count}, live_segments_fts={fts_count}",
            )

        segment_ids = {
            row[0] for row in conn.execute("SELECT id FROM live_segments").fetchall()
        }
        fts_ids = {
            row[0] for row in conn.execute("SELECT segment_id FROM live_segments_fts").fetchall()
        }
        missing_fts = sorted(segment_ids - fts_ids)
        extra_fts = sorted(fts_ids - segment_ids)
        if missing_fts:
            add_error(errors, f"segments missing from FTS: {missing_fts[:20]}")
        if extra_fts:
            add_error(errors, f"FTS contains unknown segments: {extra_fts[:20]}")

        # Canonical live ID format.
        for row in conn.execute("SELECT id FROM live_videos ORDER BY id"):
            live_id = str(row["id"])
            if not LIVE_ID_RE.fullmatch(live_id):
                add_error(errors, f"invalid live_id format: {live_id}")

        # Source candidates are the safe first-stage inventory unit.
        for row in conn.execute(
            "SELECT id, source_site, source_url, status FROM source_candidates ORDER BY id"
        ):
            candidate_id = str(row["id"])
            if not str(row["source_site"] or "").strip():
                add_error(errors, f"source_candidate source_site is empty: {candidate_id}")
            if not str(row["source_url"] or "").strip():
                add_error(errors, f"source_candidate source_url is empty: {candidate_id}")

        # Source boundaries keep C1 repeatable by natural page/date/detail units.
        for row in conn.execute(
            """
            SELECT id, source_site, boundary_type, natural_boundary, url, status, priority
            FROM source_boundaries
            ORDER BY priority DESC, id
            """
        ):
            boundary_id = str(row["id"])
            if not boundary_id.startswith("C1-"):
                add_error(errors, f"source_boundary id must start with C1-: {boundary_id}")
            if not str(row["source_site"] or "").strip():
                add_error(errors, f"source_boundary source_site is empty: {boundary_id}")
            if not str(row["boundary_type"] or "").strip():
                add_error(errors, f"source_boundary boundary_type is empty: {boundary_id}")
            if not str(row["natural_boundary"] or "").strip():
                add_error(errors, f"source_boundary natural_boundary is empty: {boundary_id}")
            if not str(row["url"] or "").strip():
                add_error(errors, f"source_boundary url is empty: {boundary_id}")
            if row["status"] == "open" and int(row["priority"]) < 90:
                add_warning(
                    warnings,
                    f"open source_boundary has low priority and may not precede C2: {boundary_id}",
                )

        # Live work items encode natural-boundary work, not fixed row-count quotas.
        for row in conn.execute(
            """
            SELECT id, live_id, source_candidate_id, work_stage, work_status, natural_boundary, instructions
            FROM live_work_items
            ORDER BY priority DESC, id
            """
        ):
            item_id = str(row["id"])
            if row["live_id"] is None and row["source_candidate_id"] is None:
                add_error(errors, f"live_work_item lacks both live_id and source_candidate_id: {item_id}")
            if not str(row["natural_boundary"] or "").strip():
                add_error(errors, f"live_work_item lacks natural_boundary: {item_id}")
            if not str(row["instructions"] or "").strip():
                add_error(errors, f"live_work_item lacks instructions: {item_id}")

        # Every canonical live record must remain traceable to at least one source.
        orphan_lives = conn.execute(
            """
            SELECT lv.id
            FROM live_videos lv
            LEFT JOIN live_sources ls ON ls.live_id = lv.id
            GROUP BY lv.id
            HAVING COUNT(ls.id) = 0
            ORDER BY lv.id
            """
        ).fetchall()
        if orphan_lives:
            add_error(
                errors,
                f"live_videos without any source record: {[row[0] for row in orphan_lives[:20]]}",
            )

        # Source IDs and minimum source traceability.
        for row in conn.execute(
            "SELECT id, source_site, url FROM live_sources ORDER BY id"
        ):
            source_id = str(row["id"])
            if not SOURCE_ID_RE.fullmatch(source_id):
                add_error(errors, f"invalid source ID format: {source_id}")
            if not str(row["source_site"] or "").strip():
                add_error(errors, f"source_site is empty for {source_id}")
            if not str(row["url"] or "").strip():
                add_error(errors, f"source URL is empty for {source_id}")

        # Segment identity, timing and provenance.
        rows = conn.execute(
            """
            SELECT
                id, live_id, segment_index,
                text_curated, text_asr,
                start_sec, end_sec,
                start_frame, end_frame, fps_at_index,
                curated_source_id, asr_source_id, time_source_id,
                playback_verified
            FROM live_segments
            ORDER BY live_id, segment_index, id
            """
        ).fetchall()

        for row in rows:
            segment_id = str(row["id"])
            live_id = str(row["live_id"])
            segment_index = int(row["segment_index"])
            expected_id = f"{live_id}_SEG_{segment_index:06d}"

            if not SEGMENT_ID_RE.fullmatch(segment_id):
                add_error(errors, f"invalid segment ID format: {segment_id}")
            if segment_id != expected_id:
                add_error(
                    errors,
                    f"segment ID/index mismatch: {segment_id}; expected {expected_id}",
                )

            if row["end_sec"] is not None and row["start_sec"] is None:
                add_error(errors, f"end_sec present without start_sec: {segment_id}")

            if (row["start_frame"] is not None or row["end_frame"] is not None) and row["fps_at_index"] is None:
                add_error(errors, f"frame locator present without fps_at_index: {segment_id}")

            if row["text_curated"] and not row["curated_source_id"]:
                add_error(errors, f"curated text lacks curated_source_id: {segment_id}")
            if row["text_asr"] and not row["asr_source_id"]:
                add_error(errors, f"ASR text lacks asr_source_id: {segment_id}")
            if row["start_sec"] is not None and not row["time_source_id"]:
                add_error(errors, f"timestamp lacks time_source_id: {segment_id}")

            if row["playback_verified"] and row["start_sec"] is None:
                add_error(errors, f"playback_verified segment has no start_sec: {segment_id}")

        # Duplicate original platform IDs should be reviewed because they are strong identity evidence.
        duplicate_video_ids = conn.execute(
            """
            SELECT platform, source_video_id, COUNT(*) AS n
            FROM live_sources
            WHERE source_video_id IS NOT NULL AND TRIM(source_video_id) <> ''
            GROUP BY platform, source_video_id
            HAVING COUNT(*) > 1
            ORDER BY n DESC, platform, source_video_id
            """
        ).fetchall()
        for row in duplicate_video_ids:
            add_warning(
                warnings,
                f"platform/source_video_id appears on {row['n']} source rows: "
                f"{row['platform']} / {row['source_video_id']} (review identity evidence)",
            )

        # Unverified timing is allowed during Pilot but must remain visible.
        unverified_timed = conn.execute(
            """
            SELECT COUNT(*)
            FROM live_segments
            WHERE start_sec IS NOT NULL AND playback_verified = 0
            """
        ).fetchone()[0]
        if unverified_timed:
            add_warning(
                warnings,
                f"{unverified_timed} timed segment(s) have not been playback-verified yet",
            )

        # Transcript cues are sentence/subtitle-level timing anchors.
        for row in conn.execute(
            """
            SELECT tc.id, tc.transcript_version_id, tc.live_id, tv.live_id AS parent_live_id,
                   tc.cue_index, tc.start_sec, tc.end_sec
            FROM transcript_cues tc
            JOIN transcript_versions tv ON tv.id = tc.transcript_version_id
            ORDER BY tc.transcript_version_id, tc.cue_index
            """
        ):
            cue_id = str(row["id"])
            if row["live_id"] != row["parent_live_id"]:
                add_error(
                    errors,
                    f"transcript cue live_id does not match parent transcript: {cue_id}",
                )
            if row["cue_index"] < 0:
                add_error(errors, f"negative transcript cue index: {cue_id}")
            if row["end_sec"] is not None and row["start_sec"] is None:
                add_error(errors, f"transcript cue end_sec present without start_sec: {cue_id}")

        # Every derived evidence link must have a durable locator and stay inside the same live.
        for row in conn.execute(
            """
            SELECT el.id, el.live_id, el.segment_id, el.transcript_cue_id,
                   ls.live_id AS segment_live_id, tc.live_id AS cue_live_id,
                   el.start_sec, el.end_sec
            FROM evidence_links el
            LEFT JOIN live_segments ls ON ls.id = el.segment_id
            LEFT JOIN transcript_cues tc ON tc.id = el.transcript_cue_id
            ORDER BY el.id
            """
        ):
            evidence_id = str(row["id"])
            if row["segment_live_id"] is not None and row["segment_live_id"] != row["live_id"]:
                add_error(errors, f"evidence link segment belongs to another live: {evidence_id}")
            if row["cue_live_id"] is not None and row["cue_live_id"] != row["live_id"]:
                add_error(errors, f"evidence link cue belongs to another live: {evidence_id}")
            if row["end_sec"] is not None and row["start_sec"] is None:
                add_error(errors, f"evidence link end_sec present without start_sec: {evidence_id}")

        # Verification checks make deferred playback safe: text-only work must not be
        # silently upgraded to playback/final acceptance.
        for row in conn.execute(
            """
            SELECT vc.id, vc.target_type, vc.target_id, vc.live_id, vc.segment_id, vc.check_stage, vc.check_status,
                   vc.evidence_link_id, ls.live_id AS segment_live_id,
                   el.live_id AS evidence_live_id
            FROM verification_checks vc
            LEFT JOIN live_segments ls ON ls.id = vc.segment_id
            LEFT JOIN evidence_links el ON el.id = vc.evidence_link_id
            ORDER BY vc.id
            """
        ):
            check_id = str(row["id"])
            if row["segment_live_id"] is not None and row["segment_live_id"] != row["live_id"]:
                add_error(errors, f"verification check segment belongs to another live: {check_id}")
            if row["evidence_live_id"] is not None and row["evidence_live_id"] != row["live_id"]:
                add_error(errors, f"verification check evidence belongs to another live: {check_id}")
            if row["check_status"] in {"text_verified", "playback_verified", "accepted"} and not row["evidence_link_id"]:
                add_error(errors, f"verified check lacks evidence_link_id: {check_id}")
            if row["check_stage"] == "final_acceptance" and row["check_status"] == "accepted":
                playback_rows = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM verification_checks
                    WHERE live_id = ?
                      AND target_type = ?
                      AND target_id = ?
                      AND check_status = 'playback_verified'
                    """,
                    (row["live_id"], row["target_type"], row["target_id"]),
                ).fetchone()[0]
                if playback_rows == 0:
                    add_error(
                        errors,
                        f"final accepted check has no prior playback_verified check: {check_id}",
                    )

    finally:
        conn.close()

    return errors, warnings, counts


def main() -> None:
    errors, warnings, counts = validate()

    print(f"Project: {PROJECT_NAME}")
    print(f"database: {DATABASE_PATH}")
    for table in sorted(counts):
        print(f"count {table}: {counts[table]}")

    for warning in warnings:
        print(f"WARNING: {warning}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"validation: FAILED ({len(errors)} error(s), {len(warnings)} warning(s))")
        raise SystemExit(1)

    print(f"validation: OK ({len(warnings)} warning(s))")


if __name__ == "__main__":
    main()

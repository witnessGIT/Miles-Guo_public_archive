PRAGMA foreign_keys = ON;

-- Miles-Guo_public_archive Pilot schema.
-- Git-tracked JSON/JSONL under data/ remains the long-term source of truth.

CREATE TABLE IF NOT EXISTS live_videos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    live_date TEXT,
    published_at TEXT,
    duration_sec REAL,
    fps REAL,
    width INTEGER,
    height INTEGER,
    language TEXT DEFAULT 'zh',
    speaker TEXT,
    status TEXT NOT NULL DEFAULT 'discovered'
        CHECK (status IN ('discovered','partial','ready','needs_review','source_missing','error')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS live_sources (
    id TEXT PRIMARY KEY,
    live_id TEXT NOT NULL REFERENCES live_videos(id) ON DELETE CASCADE,
    source_site TEXT NOT NULL,
    source_role TEXT NOT NULL,
    platform TEXT,
    source_video_id TEXT,
    source_page_id TEXT,
    url TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    status TEXT NOT NULL DEFAULT 'discovered',
    retrieved_at TEXT,
    last_verified_at TEXT,
    notes TEXT,
    metadata_json TEXT,
    UNIQUE(source_site, url)
);

CREATE TABLE IF NOT EXISTS live_segments (
    id TEXT PRIMARY KEY,
    live_id TEXT NOT NULL REFERENCES live_videos(id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL,

    text_curated TEXT,
    text_asr TEXT,
    text_search TEXT,
    text_summary TEXT,

    start_sec REAL,
    end_sec REAL,
    start_frame INTEGER,
    end_frame INTEGER,
    fps_at_index REAL,

    topic_primary TEXT,
    topic_secondary TEXT,
    entities_json TEXT,
    keywords_json TEXT,

    curated_source_id TEXT REFERENCES live_sources(id) ON DELETE SET NULL,
    asr_source_id TEXT REFERENCES live_sources(id) ON DELETE SET NULL,
    time_source_id TEXT REFERENCES live_sources(id) ON DELETE SET NULL,

    alignment_quality REAL,
    alignment_method TEXT,
    source_verified INTEGER NOT NULL DEFAULT 0 CHECK (source_verified IN (0,1)),
    playback_verified INTEGER NOT NULL DEFAULT 0 CHECK (playback_verified IN (0,1)),
    playback_verified_at TEXT,
    review_status TEXT NOT NULL DEFAULT 'unverified',

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    CHECK (segment_index >= 0),
    CHECK (start_sec IS NULL OR start_sec >= 0),
    CHECK (end_sec IS NULL OR start_sec IS NULL OR end_sec >= start_sec),
    CHECK (fps_at_index IS NULL OR fps_at_index > 0),
    CHECK (alignment_quality IS NULL OR (alignment_quality >= 0 AND alignment_quality <= 1)),
    UNIQUE(live_id, segment_index)
);

-- Preserve reproducible cross-source matching evidence before canonical merge decisions.
CREATE TABLE IF NOT EXISTS source_match_candidates (
    id TEXT PRIMARY KEY,
    left_source_id TEXT NOT NULL REFERENCES live_sources(id) ON DELETE CASCADE,
    right_source_id TEXT NOT NULL REFERENCES live_sources(id) ON DELETE CASCADE,
    match_score REAL NOT NULL CHECK (match_score >= 0 AND match_score <= 1),
    evidence_json TEXT NOT NULL,
    decision TEXT NOT NULL DEFAULT 'needs_review'
        CHECK (decision IN ('auto_merge','needs_review','do_not_merge','confirmed_merge','confirmed_distinct')),
    reviewed_by TEXT,
    reviewed_at TEXT,
    notes TEXT,
    CHECK (left_source_id <> right_source_id),
    UNIQUE(left_source_id, right_source_id)
);

-- Generic archive layer for future GETTR/X posts, articles, images, interviews,
-- recovered web pages, mirrors, and other public historical material.
CREATE TABLE IF NOT EXISTS archive_items (
    id TEXT PRIMARY KEY,
    item_type TEXT NOT NULL,
    title TEXT,
    body TEXT,
    published_at TEXT,
    language TEXT,
    canonical_url TEXT,
    source_site TEXT,
    source_id TEXT,
    provenance_level TEXT,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases_json TEXT,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS item_entities (
    item_id TEXT NOT NULL REFERENCES archive_items(id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type TEXT,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    PRIMARY KEY (item_id, entity_id, relation_type)
);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS item_topics (
    item_id TEXT NOT NULL REFERENCES archive_items(id) ON DELETE CASCADE,
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    PRIMARY KEY (item_id, topic_id)
);

-- Standalone FTS table is rebuilt from live_segments by scripts/build_db.py.
CREATE VIRTUAL TABLE IF NOT EXISTS live_segments_fts USING fts5(
    segment_id UNINDEXED,
    live_id UNINDEXED,
    text_curated,
    text_asr,
    text_search,
    tokenize='unicode61'
);

CREATE INDEX IF NOT EXISTS idx_live_videos_date ON live_videos(live_date);
CREATE INDEX IF NOT EXISTS idx_live_sources_live_id ON live_sources(live_id);
CREATE INDEX IF NOT EXISTS idx_live_sources_site ON live_sources(source_site);
CREATE INDEX IF NOT EXISTS idx_live_sources_video_id ON live_sources(source_video_id);
CREATE INDEX IF NOT EXISTS idx_live_segments_live_id ON live_segments(live_id);
CREATE INDEX IF NOT EXISTS idx_live_segments_start_sec ON live_segments(live_id, start_sec);
CREATE INDEX IF NOT EXISTS idx_source_match_decision ON source_match_candidates(decision, match_score);
CREATE INDEX IF NOT EXISTS idx_archive_items_published_at ON archive_items(published_at);
CREATE INDEX IF NOT EXISTS idx_archive_items_type ON archive_items(item_type);

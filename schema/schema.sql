PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS live_videos (
    live_id TEXT PRIMARY KEY,
    published_date TEXT NOT NULL,
    sequence_no INTEGER NOT NULL,
    title TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('livestream','short_video','video','unknown')),
    language TEXT NOT NULL DEFAULT 'zh',
    duration_sec INTEGER,
    width INTEGER,
    height INTEGER,
    quality_status TEXT NOT NULL DEFAULT 'pilot',
    notes TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(published_date, sequence_no)
);

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    live_id TEXT NOT NULL REFERENCES live_videos(live_id) ON DELETE CASCADE,
    source_site TEXT NOT NULL CHECK (source_site IN ('gwins','ghot','gettrsearch')),
    source_url TEXT NOT NULL,
    third_party_id TEXT,
    original_platform TEXT CHECK (original_platform IN ('gettr','rumble','youtube','twitter','x','gwins','ghot','gettrsearch','other')),
    original_url TEXT,
    fetched_at TEXT NOT NULL,
    source_level TEXT NOT NULL CHECK (source_level IN ('primary','secondary','discovery')),
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0,1)),
    metadata_json TEXT,
    UNIQUE(source_site, source_url)
);

CREATE TABLE IF NOT EXISTS transcripts (
    transcript_id TEXT PRIMARY KEY,
    live_id TEXT NOT NULL REFERENCES live_videos(live_id) ON DELETE CASCADE,
    source_id TEXT REFERENCES sources(source_id) ON DELETE SET NULL,
    transcript_type TEXT NOT NULL CHECK (transcript_type IN ('human','asr','subtitle','excerpt')),
    language TEXT NOT NULL DEFAULT 'zh',
    transcript_text TEXT NOT NULL,
    attribution TEXT,
    quality_status TEXT NOT NULL DEFAULT 'unverified',
    source_url TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transcript_segments (
    segment_id TEXT PRIMARY KEY,
    transcript_id TEXT NOT NULL REFERENCES transcripts(transcript_id) ON DELETE CASCADE,
    start_sec REAL NOT NULL,
    end_sec REAL,
    segment_text TEXT NOT NULL,
    confidence REAL,
    CHECK (start_sec >= 0),
    CHECK (end_sec IS NULL OR end_sec >= start_sec)
);

CREATE TABLE IF NOT EXISTS archive_items (
    item_id TEXT PRIMARY KEY,
    live_id TEXT REFERENCES live_videos(live_id) ON DELETE SET NULL,
    item_type TEXT NOT NULL,
    title TEXT,
    body TEXT,
    published_at TEXT,
    source_id TEXT REFERENCES sources(source_id) ON DELETE SET NULL,
    metadata_json TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS archive_fts USING fts5(
    live_id UNINDEXED,
    title,
    transcript_text,
    tokenize='unicode61'
);

CREATE INDEX IF NOT EXISTS idx_live_videos_date ON live_videos(published_date);
CREATE INDEX IF NOT EXISTS idx_sources_live_id ON sources(live_id);
CREATE INDEX IF NOT EXISTS idx_sources_site ON sources(source_site);
CREATE INDEX IF NOT EXISTS idx_transcripts_live_id ON transcripts(live_id);
CREATE INDEX IF NOT EXISTS idx_segments_transcript_id ON transcript_segments(transcript_id);
CREATE INDEX IF NOT EXISTS idx_segments_start ON transcript_segments(start_sec);

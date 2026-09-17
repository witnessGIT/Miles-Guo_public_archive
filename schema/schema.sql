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

-- Detailed original-livestream layer. These tables deliberately contain no later news,
-- outcome, or retrospective fact fields.
CREATE TABLE IF NOT EXISTS media_assets (
    id TEXT PRIMARY KEY,
    live_id TEXT NOT NULL REFERENCES live_videos(id) ON DELETE CASCADE,
    source_id TEXT REFERENCES live_sources(id) ON DELETE SET NULL,
    asset_role TEXT NOT NULL CHECK (asset_role IN ('original_video','mirror_video','audio','thumbnail','caption_file')),
    url TEXT NOT NULL,
    platform TEXT,
    platform_asset_id TEXT,
    mime_type TEXT,
    duration_sec REAL,
    width INTEGER,
    height INTEGER,
    audio_present INTEGER CHECK (audio_present IN (0,1)),
    availability_status TEXT NOT NULL DEFAULT 'unknown',
    checked_at TEXT,
    metadata_json TEXT,
    UNIQUE(source_id, url)
);

CREATE TABLE IF NOT EXISTS transcript_versions (
    id TEXT PRIMARY KEY,
    live_id TEXT NOT NULL REFERENCES live_videos(id) ON DELETE CASCADE,
    source_id TEXT REFERENCES live_sources(id) ON DELETE SET NULL,
    transcript_kind TEXT NOT NULL CHECK (transcript_kind IN ('source_original','curated','asr_raw','corrected','translation')),
    language TEXT NOT NULL,
    text TEXT NOT NULL,
    parent_version_id TEXT REFERENCES transcript_versions(id) ON DELETE SET NULL,
    generated_by TEXT,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    created_at TEXT NOT NULL,
    UNIQUE(live_id, transcript_kind, language, source_id)
);

CREATE TABLE IF NOT EXISTS transcript_cues (
    id TEXT PRIMARY KEY,
    transcript_version_id TEXT NOT NULL REFERENCES transcript_versions(id) ON DELETE CASCADE,
    live_id TEXT NOT NULL REFERENCES live_videos(id) ON DELETE CASCADE,
    cue_index INTEGER NOT NULL,
    start_sec REAL,
    end_sec REAL,
    speaker_entity_id TEXT REFERENCES entities(id) ON DELETE SET NULL,
    text TEXT NOT NULL,
    timing_status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (timing_status IN ('unknown','asr','source_caption','aligned','playback_verified','needs_review')),
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    source_cue_id TEXT,
    CHECK (cue_index >= 0),
    CHECK (start_sec IS NULL OR start_sec >= 0),
    CHECK (end_sec IS NULL OR start_sec IS NULL OR end_sec >= start_sec),
    UNIQUE(transcript_version_id, cue_index)
);

CREATE TABLE IF NOT EXISTS segment_speakers (
    segment_id TEXT NOT NULL REFERENCES live_segments(id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'speaker',
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    PRIMARY KEY (segment_id, entity_id, role)
);

CREATE TABLE IF NOT EXISTS segment_entities (
    segment_id TEXT NOT NULL REFERENCES live_segments(id) ON DELETE CASCADE,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    mention_text TEXT,
    mention_role TEXT NOT NULL DEFAULT 'mentioned',
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    PRIMARY KEY (segment_id, entity_id, mention_role)
);

CREATE TABLE IF NOT EXISTS live_events (
    id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    event_type TEXT,
    event_time_start TEXT,
    event_time_end TEXT,
    place_text TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'mentioned_in_live',
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS segment_events (
    segment_id TEXT NOT NULL REFERENCES live_segments(id) ON DELETE CASCADE,
    event_id TEXT NOT NULL REFERENCES live_events(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL DEFAULT 'mentions',
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    PRIMARY KEY (segment_id, event_id, relation_type)
);

CREATE TABLE IF NOT EXISTS segment_claims (
    id TEXT PRIMARY KEY,
    segment_id TEXT NOT NULL REFERENCES live_segments(id) ON DELETE CASCADE,
    claim_type TEXT NOT NULL CHECK (claim_type IN ('fact_statement','opinion','judgment','prediction','question')),
    quote TEXT NOT NULL,
    normalized_claim TEXT,
    stance TEXT,
    certainty TEXT,
    target_time_text TEXT,
    subject_entity_id TEXT REFERENCES entities(id) ON DELETE SET NULL,
    object_entity_id TEXT REFERENCES entities(id) ON DELETE SET NULL,
    event_id TEXT REFERENCES live_events(id) ON DELETE SET NULL,
    extraction_status TEXT NOT NULL DEFAULT 'unreviewed',
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE TABLE IF NOT EXISTS segment_relations (
    id TEXT PRIMARY KEY,
    from_segment_id TEXT NOT NULL REFERENCES live_segments(id) ON DELETE CASCADE,
    to_segment_id TEXT NOT NULL REFERENCES live_segments(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL CHECK (relation_type IN ('same_topic','same_event','before','after','supports','contradicts','similar_to','usable_with')),
    basis TEXT NOT NULL CHECK (basis IN ('explicit','editorial','semantic')),
    explanation TEXT,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    evidence_segment_id TEXT REFERENCES live_segments(id) ON DELETE SET NULL,
    CHECK (from_segment_id <> to_segment_id),
    UNIQUE(from_segment_id, to_segment_id, relation_type, basis)
);

CREATE TABLE IF NOT EXISTS segment_clip_notes (
    segment_id TEXT PRIMARY KEY REFERENCES live_segments(id) ON DELETE CASCADE,
    clip_title TEXT,
    visual_description TEXT,
    audio_quality TEXT,
    video_quality TEXT,
    clip_usability TEXT NOT NULL DEFAULT 'unknown',
    production_tags_json TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS evidence_links (
    id TEXT PRIMARY KEY,
    subject_type TEXT NOT NULL
        CHECK (subject_type IN (
            'segment','transcript_cue','segment_entity','segment_event',
            'segment_claim','segment_relation','segment_clip_note','live_event'
        )),
    subject_id TEXT NOT NULL,
    live_id TEXT NOT NULL REFERENCES live_videos(id) ON DELETE CASCADE,
    segment_id TEXT REFERENCES live_segments(id) ON DELETE CASCADE,
    transcript_cue_id TEXT REFERENCES transcript_cues(id) ON DELETE SET NULL,
    source_id TEXT REFERENCES live_sources(id) ON DELETE SET NULL,
    quote TEXT,
    start_sec REAL,
    end_sec REAL,
    evidence_role TEXT NOT NULL DEFAULT 'primary'
        CHECK (evidence_role IN ('primary','supporting','locator','conflict','needs_review')),
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    created_at TEXT NOT NULL,
    CHECK (segment_id IS NOT NULL OR transcript_cue_id IS NOT NULL OR source_id IS NOT NULL),
    CHECK (start_sec IS NULL OR start_sec >= 0),
    CHECK (end_sec IS NULL OR start_sec IS NULL OR end_sec >= start_sec)
);

CREATE TABLE IF NOT EXISTS verification_checks (
    id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL
        CHECK (target_type IN (
            'live_video','segment','transcript_cue','segment_claim',
            'segment_relation','segment_event','segment_entity','segment_clip_note'
        )),
    target_id TEXT NOT NULL,
    live_id TEXT NOT NULL REFERENCES live_videos(id) ON DELETE CASCADE,
    segment_id TEXT REFERENCES live_segments(id) ON DELETE SET NULL,
    check_stage TEXT NOT NULL
        CHECK (check_stage IN ('source_inventory','text_crosscheck','playback_audio','playback_video','final_acceptance')),
    check_status TEXT NOT NULL
        CHECK (check_status IN ('unverified','needs_review','text_verified','playback_verified','accepted','rejected','blocked')),
    method TEXT,
    evidence_link_id TEXT REFERENCES evidence_links(id) ON DELETE SET NULL,
    checked_by TEXT,
    checked_at TEXT NOT NULL,
    notes TEXT,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
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
CREATE INDEX IF NOT EXISTS idx_media_assets_live_id ON media_assets(live_id);
CREATE INDEX IF NOT EXISTS idx_transcript_versions_live_id ON transcript_versions(live_id);
CREATE INDEX IF NOT EXISTS idx_transcript_cues_live_time ON transcript_cues(live_id, start_sec);
CREATE INDEX IF NOT EXISTS idx_transcript_cues_version ON transcript_cues(transcript_version_id, cue_index);
CREATE INDEX IF NOT EXISTS idx_segment_entities_entity_id ON segment_entities(entity_id);
CREATE INDEX IF NOT EXISTS idx_segment_events_event_id ON segment_events(event_id);
CREATE INDEX IF NOT EXISTS idx_segment_claims_type ON segment_claims(claim_type);
CREATE INDEX IF NOT EXISTS idx_segment_relations_to ON segment_relations(to_segment_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_evidence_links_subject ON evidence_links(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_evidence_links_live_time ON evidence_links(live_id, start_sec);
CREATE INDEX IF NOT EXISTS idx_verification_checks_target ON verification_checks(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_verification_checks_live_stage ON verification_checks(live_id, check_stage, check_status);

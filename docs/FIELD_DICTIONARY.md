# Original Livestream Field Dictionary

This run stores only original livestream material. Do not add later news, later outcomes,
external fact-checking, retrospective judgments, or edited interpretations as source data.

The database is designed for ordinary agents to turn one livestream into reusable material for:
search, quotation, clipping, writing, topic review, event analysis, prediction tracking inside
the original speech, and future agent learning.

Active records for this restarted run belong under `data/current/`. Existing files outside
`data/current/` are sealed historical Pilot material and must not be treated as current progress.

## Agent filling rules

1. Keep original text, ASR text, corrected text and translation in separate records.
2. Every claim, event, relation and clip note must point back to a segment or transcript cue.
3. If a field is uncertain, fill `confidence` and keep the record `unreviewed` or `needs_review`.
4. Do not merge two livestreams just because titles look similar; use source IDs, dates, duration,
   transcript overlap or explicit source evidence.
5. Use `null` for unknown values. Do not invent timestamps, speakers, entities, events or quotes.

## ID rules

| Object | Format | Example |
|---|---|---|
| Livestream | `LIVE_YYYYMMDD_NNN` | `LIVE_20210612_001` |
| Source candidate | `SC_<site>_<stable_id>` | `SC_GHOT_abc123` |
| Source | `SRC_<site>_<stable_id>` | `SRC_GHOT_abc123` |
| Live work item | `WI_<live_id>_<stage>` | `WI_LIVE_20210612_001_claim_pass` |
| Segment | `<live_id>_SEG_000000` | `LIVE_20210612_001_SEG_000014` |
| Media asset | `MEDIA_<source-or-live>_<role>` | `MEDIA_SRC_GHOT_abc123_original_video` |
| Transcript version | `TR_<live_id>_<kind>_<lang>_<NNN>` | `TR_LIVE_20210612_001_asr_raw_zh_001` |
| Transcript cue | `<transcript_version_id>_CUE_000000` | `TR_LIVE_20210612_001_asr_raw_zh_001_CUE_000090` |
| Entity | `ENT_<type>_<slug>` | `ENT_person_guo_wengui` |
| Event | `EVT_<slug>` | `EVT_hong_kong_protest` |
| Claim | `CLM_<segment_id>_<NNN>` | `CLM_LIVE_20210612_001_SEG_000014_001` |
| Evidence link | `EVD_<subject_type>_<subject_id>_<NNN>` | `EVD_segment_claim_CLM_x_001` |
| Verification check | `CHK_<target_type>_<target_id>_<stage>` | `CHK_segment_LIVE_20210612_001_SEG_000014_playback_audio` |

## Verification ladder

The archive is intentionally allowed to grow before every video/audio check is finished.
Agents must preserve the verification level instead of pretending that early records are final.

| Level | Meaning | Can be used for |
|---|---|---|
| `unverified` | Collected or extracted, but not checked yet. | Search draft, task planning, later review queue. |
| `needs_review` | Something is missing, conflicting, or uncertain. | Human/agent review queue. |
| `text_verified` | Checked against another transcript/source text, but not against audio/video. | Safer search and writing drafts, still not final citation. |
| `playback_verified` | Checked against real audio/video or accepted ASR evidence from decoded media. | Strong citation, clipping, final archive candidate. |
| `accepted` | Final acceptance after required playback evidence exists. | Published archive, downstream video/news/analysis work. |
| `rejected` | Checked and found wrong. | Do not use except as audit history. |
| `blocked` | Could not check because source/media/access failed. | Retry queue when a new source appears. |

No agent may mark a record `accepted` unless a matching `playback_verified` check already exists.
If video checking is deferred, create records as `unverified`, `needs_review`, or at most
`text_verified`.

## Core livestream records

### `source_candidates`

First-stage discovery records. These are safer than asking agents to immediately decide canonical
livestream identity.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | `SC_<site>_<stable_id>`. |
| `source_site` | text | yes | `GWINS`, `GHOT`, `GETTRSEARCH`, `GETTR`, etc. |
| `source_url` | text | yes | Page or media URL found at a natural boundary. |
| `page_kind` | enum | yes | `index_page`, `search_result_page`, `date_page`, `channel_page`, `detail_page`, `media_page`, `unknown`. |
| `discovery_context` | text | no | Page/date/search/channel boundary where it was found. |
| `candidate_title` | text | no | Title as displayed. |
| `candidate_date`, `candidate_published_at` | text | no | Date/time shown by source. |
| `candidate_duration_text`, `candidate_duration_sec` | text/number | no | Duration if shown or decoded. |
| `has_video`, `has_audio`, `has_transcript`, `has_timestamps` | 0/1 | no | Only mark when visible from source. |
| `source_video_id`, `source_page_id` | text | no | Stable platform/source IDs. |
| `candidate_live_id` | text | no | Suggested live ID if obvious; not authoritative. |
| `status` | enum | yes | `discovered`, `needs_review`, `promoted`, `duplicate`, `rejected`, `blocked`. |
| `confidence` | number | no | 0-1 if inferred. |
| `discovered_by`, `discovered_at` | text/datetime | yes | Agent/process and UTC timestamp. |
| `metadata_json` | JSON text | no | Raw visible metadata. |

### `live_videos`

One canonical livestream record.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | Canonical `LIVE_YYYYMMDD_NNN`. |
| `title` | text | yes | Best original title found from source pages. |
| `live_date` | date text | no | Livestream date, `YYYY-MM-DD`, if known. |
| `published_at` | datetime text | no | Platform publish time if available. |
| `duration_sec` | number | no | Duration in seconds from reliable media metadata. |
| `fps`, `width`, `height` | number | no | Video technical metadata when decoded. |
| `language` | enum | yes | Usually `zh`; use `en`, `mixed`, or exact BCP-47 if needed. |
| `speaker` | text | no | Human-readable main speaker name. Prefer entity records for structured use. |
| `status` | enum | yes | `discovered`, `partial`, `ready`, `needs_review`, `source_missing`, `error`. |
| `created_at`, `updated_at` | datetime text | yes | UTC ISO timestamp. |

### `live_sources`

Every original or mirror source page/video for a livestream.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | `SRC_<site>_<stable_id>`. |
| `live_id` | text | yes | Parent livestream. |
| `source_site` | enum/text | yes | `GWINS`, `GHOT`, `GETTRSEARCH`, `GETTR`, `RUMBLE`, `ODYSEE`, etc. |
| `source_role` | enum | yes | `primary`, `mirror`, `index`, `backup`, `caption`, `metadata_only`. |
| `platform` | text | no | Technical platform name when different from `source_site`. |
| `source_video_id`, `source_page_id` | text | no | Platform stable IDs, not guessed from title. |
| `url` | text | yes | Public source URL. |
| `priority` | integer | yes | Lower means preferred source. Original source usually `10`; mirrors `50+`. |
| `status` | enum/text | yes | `discovered`, `reachable`, `blocked`, `not_media`, `decoded`, `dead`, `needs_review`. |
| `retrieved_at`, `last_verified_at` | datetime text | no | UTC ISO timestamp for collection/checks. |
| `notes` | text | no | Short human notes only. |
| `metadata_json` | JSON text | no | Raw platform metadata preserved as JSON. |

### `media_assets`

Concrete media or sidecar assets from sources.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | Stable media asset ID. |
| `live_id` | text | yes | Parent livestream. |
| `source_id` | text | no | Source that exposed this asset. |
| `asset_role` | enum | yes | `original_video`, `mirror_video`, `audio`, `thumbnail`, `caption_file`. |
| `url` | text | yes | Direct media, page asset, caption, or thumbnail URL. |
| `platform`, `platform_asset_id` | text | no | Platform and asset ID if available. |
| `mime_type` | text | no | From HTTP, yt-dlp or ffprobe. |
| `duration_sec`, `width`, `height` | number | no | Decoded media metadata. |
| `audio_present` | 0/1 | no | `1` only after metadata confirms an audio stream. |
| `availability_status` | enum/text | yes | `unknown`, `reachable`, `blocked`, `decoded`, `video_only`, `audio_only`, `dead`. |
| `checked_at` | datetime text | no | Last technical check time. |
| `metadata_json` | JSON text | no | ffprobe/yt-dlp metadata or error summaries. |

### `live_work_items`

Natural-boundary processing tasks for one livestream and one stage. This replaces fixed quotas such
as “process N videos” or “extract N claims.”

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | `WI_<live_id>_<stage>`. |
| `live_id` | text | no | Canonical livestream when known. |
| `source_candidate_id` | text | no | Candidate being promoted/reviewed, when no live exists yet. |
| `work_stage` | enum | yes | `source_merge`, `metadata_fill`, `transcript_import`, `cue_split`, `segment_split`, `entity_pass`, `event_pass`, `claim_pass`, `relation_pass`, `text_verify`, `playback_backlog`. |
| `work_status` | enum | yes | `open`, `in_progress`, `blocked`, `done`, `superseded`. |
| `natural_boundary` | text | yes | Example: one canonical livestream + one processing stage. |
| `instructions` | text | yes | What the agent should do for this stage. |
| `priority` | integer | yes | Higher first. |
| `depends_on_json` | JSON text | no | Optional stage dependencies. |
| `created_at`, `updated_at` | datetime text | yes | UTC ISO timestamp. |

## Transcript and timing records

### `transcript_versions`

Whole-transcript containers. Use this to preserve source/ASR/corrected/translation versions.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | Stable transcript version ID. |
| `live_id` | text | yes | Parent livestream. |
| `source_id` | text | no | Source that produced the text, if applicable. |
| `transcript_kind` | enum | yes | `source_original`, `curated`, `asr_raw`, `corrected`, `translation`. |
| `language` | text | yes | `zh`, `en`, `mixed`, etc. |
| `text` | text | yes | Full transcript text for this version. |
| `parent_version_id` | text | no | Parent ASR/source version for correction or translation. |
| `generated_by` | text | no | Tool/model/person/process name. |
| `confidence` | number | no | 0-1; use for ASR or uncertain source text. |
| `created_at` | datetime text | yes | UTC ISO timestamp. |

### `transcript_cues`

Small timestamped transcript units. This is the main bridge between audio, text, claims and video clips.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | `<transcript_version_id>_CUE_000000`. |
| `transcript_version_id` | text | yes | Parent transcript version. |
| `live_id` | text | yes | Parent livestream for fast filtering. |
| `cue_index` | integer | yes | Starts at 0 inside one transcript version. |
| `start_sec`, `end_sec` | number | no | Audio/video seconds. Leave null if unknown. |
| `speaker_entity_id` | text | no | Speaker entity if known. |
| `text` | text | yes | One subtitle line, ASR phrase, sentence, or short paragraph. |
| `timing_status` | enum | yes | `unknown`, `asr`, `source_caption`, `aligned`, `playback_verified`, `needs_review`. |
| `confidence` | number | no | 0-1 confidence for text/timing. |
| `source_cue_id` | text | no | Original subtitle ID or cue number if supplied by source. |

## Segments

### `live_segments`

The smallest citable content unit for later retrieval and work. A segment can contain several cues.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | `<live_id>_SEG_000000`. |
| `live_id` | text | yes | Parent livestream. |
| `segment_index` | integer | yes | Starts at 0 and must match ID suffix. |
| `text_curated` | text | no | Human-corrected segment text. |
| `text_asr` | text | no | Raw ASR segment text. |
| `text_search` | text | no | Search-normalized text; do not replace originals. |
| `text_summary` | text | no | Short neutral summary of what this segment says. |
| `start_sec`, `end_sec` | number | no | Segment time range. |
| `start_frame`, `end_frame`, `fps_at_index` | number | no | Use only when frame-accurate location is needed. |
| `topic_primary`, `topic_secondary` | text | no | Human-readable topic labels. Structured topics may be added later. |
| `entities_json`, `keywords_json` | JSON text | no | Lightweight search helpers; keep structured entities separately too. |
| `curated_source_id`, `asr_source_id`, `time_source_id` | text | no | Source IDs for text and timing provenance. |
| `alignment_quality` | number | no | 0-1 quality for text/time alignment. |
| `alignment_method` | text | no | `manual`, `asr`, `subtitle`, `forced_alignment`, etc. |
| `source_verified` | 0/1 | yes | Whether source provenance is verified. |
| `playback_verified` | 0/1 | yes | Whether audio/video playback verified this segment. |
| `playback_verified_at` | datetime text | no | UTC verification timestamp. |
| `review_status` | enum/text | yes | `unverified`, `machine`, `needs_review`, `human_reviewed`, `accepted`, `rejected`. |
| `created_at`, `updated_at` | datetime text | yes | UTC ISO timestamp. |

## People, organizations, places and topics

### `entities`

Reusable names mentioned in livestreams.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | `ENT_<type>_<slug>`. |
| `entity_type` | enum/text | yes | `person`, `organization`, `country`, `place`, `media`, `law`, `project`, etc. |
| `canonical_name` | text | yes | Preferred display name. |
| `aliases_json` | JSON text | no | Names, spellings, Chinese/English variants. |
| `metadata_json` | JSON text | no | Only neutral identity metadata needed for retrieval. |

### `segment_speakers`

Who spoke in a segment.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `segment_id` | text | yes | Parent segment. |
| `entity_id` | text | yes | Speaker entity. |
| `role` | enum/text | yes | `speaker`, `host`, `guest`, `quoted_speaker`, `translator`. |
| `confidence` | number | no | 0-1 if inferred. |

### `segment_entities`

Entities mentioned or discussed in a segment.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `segment_id` | text | yes | Parent segment. |
| `entity_id` | text | yes | Mentioned entity. |
| `mention_text` | text | no | Exact local wording if useful. |
| `mention_role` | enum/text | yes | `mentioned`, `speaker`, `target`, `ally`, `opponent`, `source`, `victim`, `location`, `organization`, `quoted`. |
| `confidence` | number | no | 0-1 if automatic or uncertain. |

## Events and claims inside the original livestream

### `live_events`

Events mentioned inside the livestream. This does not store later news confirmation.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | `EVT_<slug>`. |
| `canonical_name` | text | yes | Short event name. |
| `event_type` | enum/text | no | `political`, `legal`, `financial`, `media`, `personal`, `military`, `public_health`, etc. |
| `event_time_start`, `event_time_end` | datetime/date text | no | Time claimed or discussed in the livestream. |
| `place_text` | text | no | Place as spoken or normalized. |
| `description` | text | no | Neutral description based only on original livestream. |
| `status` | enum/text | yes | Usually `mentioned_in_live`; use `needs_review` if uncertain. |
| `metadata_json` | JSON text | no | Source-internal details only. |

### `segment_events`

How a segment relates to an event.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `segment_id` | text | yes | Parent segment. |
| `event_id` | text | yes | Related event. |
| `relation_type` | enum/text | yes | `mentions`, `describes`, `predicts`, `explains`, `criticizes`, `supports`, `quotes`, `dates`, `locates`. |
| `confidence` | number | no | 0-1 if automatic or uncertain. |

### `segment_claims`

Distinct claims made in the original livestream. Store what was said, not whether later news proved it.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | `CLM_<segment_id>_<NNN>`. |
| `segment_id` | text | yes | Segment where claim appears. |
| `claim_type` | enum | yes | `fact_statement`, `opinion`, `judgment`, `prediction`, `question`. |
| `quote` | text | yes | Exact original quote or shortest faithful excerpt. |
| `normalized_claim` | text | no | Plain-language normalized claim for search. |
| `stance` | text | no | `supports`, `opposes`, `warns`, `accuses`, `denies`, etc. |
| `certainty` | text | no | `certain`, `likely`, `possible`, `conditional`, `unclear`. |
| `target_time_text` | text | no | Time period mentioned inside the claim, especially predictions. |
| `subject_entity_id`, `object_entity_id` | text | no | Main subject/object entities if clear. |
| `event_id` | text | no | Main related event if clear. |
| `extraction_status` | enum/text | yes | `unreviewed`, `machine`, `human_reviewed`, `accepted`, `needs_review`, `rejected`. |
| `confidence` | number | no | 0-1 confidence for extraction/normalization. |

## Related-content retrieval

### `segment_relations`

Relations between original livestream segments. Use for “find related parts” inside the archive.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | Stable relation ID. |
| `from_segment_id`, `to_segment_id` | text | yes | Two different original segments. |
| `relation_type` | enum | yes | `same_topic`, `same_event`, `before`, `after`, `supports`, `contradicts`, `similar_to`, `usable_with`. |
| `basis` | enum | yes | `explicit`, `editorial`, `semantic`. |
| `explanation` | text | no | One sentence explaining the link. |
| `confidence` | number | no | 0-1; required when `basis=semantic`. |
| `evidence_segment_id` | text | no | Segment that explicitly states the relation, if any. |

### `evidence_links`

Universal evidence locator. Use this whenever a derived record needs to prove where it came from.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | Stable evidence link ID. |
| `subject_type` | enum | yes | `segment`, `transcript_cue`, `segment_entity`, `segment_event`, `segment_claim`, `segment_relation`, `segment_clip_note`, `live_event`. |
| `subject_id` | text | yes | ID of the record being supported. |
| `live_id` | text | yes | Parent livestream. |
| `segment_id` | text | no | Segment containing the evidence. |
| `transcript_cue_id` | text | no | Cue containing the exact text, if available. |
| `source_id` | text | no | Source page/media supporting the evidence. |
| `quote` | text | no | Exact words used as evidence. |
| `start_sec`, `end_sec` | number | no | Time range of the evidence. |
| `evidence_role` | enum | yes | `primary`, `supporting`, `locator`, `conflict`, `needs_review`. |
| `confidence` | number | no | 0-1 if automatic or uncertain. |
| `created_at` | datetime text | yes | UTC ISO timestamp. |

`evidence_links.subject_id` is intentionally polymorphic. The validator enforces that every
evidence link has at least one real locator: `segment_id`, `transcript_cue_id`, or `source_id`.

### `verification_checks`

Verification history for deferred checking. This table is what lets the project safely organize
everything first and complete video/audio checks later.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `id` | text | yes | Stable check ID. |
| `target_type` | enum | yes | `live_video`, `segment`, `transcript_cue`, `segment_claim`, `segment_relation`, `segment_event`, `segment_entity`, `segment_clip_note`. |
| `target_id` | text | yes | Record being checked. |
| `live_id` | text | yes | Parent livestream. |
| `segment_id` | text | no | Segment involved in the check, when applicable. |
| `check_stage` | enum | yes | `source_inventory`, `text_crosscheck`, `playback_audio`, `playback_video`, `final_acceptance`. |
| `check_status` | enum | yes | `unverified`, `needs_review`, `text_verified`, `playback_verified`, `accepted`, `rejected`, `blocked`. |
| `method` | text | no | `source_compare`, `asr_compare`, `manual_listen`, `ffmpeg_whisper`, etc. |
| `evidence_link_id` | text | no | Required for `text_verified`, `playback_verified`, and `accepted`. |
| `checked_by` | text | no | Agent/person/process identity. |
| `checked_at` | datetime text | yes | UTC ISO timestamp. |
| `notes` | text | no | Short audit note. |
| `confidence` | number | no | 0-1 if automatic or uncertain. |

## Video production notes

### `segment_clip_notes`

Clip usefulness for future video production. This is still based only on original content.

| Field | Type | Required | How to fill |
|---|---:|---:|---|
| `segment_id` | text | yes | Parent segment. |
| `clip_title` | text | no | Short working clip title. |
| `visual_description` | text | no | What appears on screen if checked. |
| `audio_quality`, `video_quality` | enum/text | no | `good`, `usable`, `noisy`, `poor`, `unknown`. |
| `clip_usability` | enum/text | yes | `unknown`, `good_clip`, `audio_only`, `context_needed`, `not_useful`, `needs_review`. |
| `production_tags_json` | JSON text | no | Search tags for later editors. |
| `notes` | text | no | Short neutral note. |

## Minimum record sets by stage

| Stage | Agent must create or update |
|---|---|
| Source inventory | `live_videos`, `live_sources`, optionally `media_assets` |
| Source discovery | `source_candidates` only; do not force fixed counts |
| Candidate promotion | `live_videos`, `live_sources`, `media_assets`, then `live_work_items` |
| Media/transcript extraction | `media_assets`, `transcript_versions`, `transcript_cues` |
| Segmentation | `live_segments`, `evidence_links`, `verification_checks` as `unverified` |
| Entity/event pass | `entities`, `segment_speakers`, `segment_entities`, `live_events`, `segment_events`, `evidence_links` |
| Claim pass | `segment_claims`, `evidence_links`, `verification_checks` |
| Related-content pass | `segment_relations`, `evidence_links`, `verification_checks` |
| Clip pass | `segment_clip_notes`, `evidence_links`, `verification_checks` |
| Text crosscheck | `verification_checks` as `text_verified` or `needs_review` |
| Playback check | `verification_checks` as `playback_verified`, plus segment/cue playback fields |
| Final acceptance | `verification_checks` as `accepted`, only after playback evidence exists |

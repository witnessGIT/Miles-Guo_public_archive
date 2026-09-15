# Original Livestream Field Dictionary

Only original livestream material belongs in this run; no later news or outcomes.

| Dataset | Required fields | Purpose |
|---|---|---|
| live_videos | id, title, live_date, language, status, created_at, updated_at | one canonical livestream |
| live_sources | id, live_id, source_site, source_role, url | every public source page/video |
| media_assets | id, live_id, asset_role, url, availability_status | original/mirror video and audio availability |
| transcript_versions | id, live_id, transcript_kind, language, text, created_at | preserve source, ASR and corrected text separately |
| live_segments | id, live_id, segment_index, start_sec/end_sec when known, review_status | smallest citable video unit |
| segment_speakers | segment_id, entity_id | who speaks in a segment |
| segment_entities | segment_id, entity_id, mention_role | people, organisations, countries and places mentioned |
| live_events | id, canonical_name | events mentioned inside the livestream |
| segment_events | segment_id, event_id, relation_type | how the segment discusses the event |
| segment_claims | id, segment_id, claim_type, quote | fact statement, opinion, judgment, prediction or question made in the livestream |
| segment_relations | id, from_segment_id, to_segment_id, relation_type, basis | explicit/editorial/semantic connections between original segments |
| segment_clip_notes | segment_id, clip_usability | video-editing notes without altering original content |

Every derived record must carry `confidence` when automatic or uncertain, and must retain a source
or segment reference. `text_original`/source text is never overwritten by ASR, correction or translation.

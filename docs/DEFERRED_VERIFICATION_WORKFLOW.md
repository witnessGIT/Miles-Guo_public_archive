# Deferred Verification Workflow

This project can organize original livestream content before every audio/video check is finished.
The safety rule is simple: early organization creates useful records, but does not create final
acceptance.

## Why this exists

Some long-term source pages may be reachable later but not always reachable from a runner today.
The archive must still preserve source lists, transcripts, cue timing, people, events, claims,
relations and clip notes so future agents can retry checks without redoing all analysis.

For the restarted run, only `data/current/` is active input. Earlier Pilot/alignment/playback files
outside `data/current/` are sealed history and must not unlock stages, satisfy checks, or count as
current database rows.

## Stage 1: organize original material

Ordinary agents may create:

- `source_candidates`
- `live_videos`
- `live_sources`
- `media_assets`
- `live_work_items`
- `transcript_versions`
- `transcript_cues`
- `live_segments`
- `entities`
- `segment_speakers`
- `segment_entities`
- `live_events`
- `segment_events`
- `segment_claims`
- `segment_relations`
- `segment_clip_notes`
- `evidence_links`

All derived records must remain `unverified` or `needs_review` unless a real cross-check has been
performed.

Stage 1 uses natural boundaries. Agents must not be told to process a fixed number of videos or
records. A source discovery task ends at a page/date/search/detail boundary; a livestream processing
task ends at one `live_work_items.work_stage`.

## Stage 2: text cross-check

Agents compare source text, ASR, corrected transcript, duplicate sources, and internal consistency.
Successful text checks create `verification_checks` with:

- `check_stage = text_crosscheck`
- `check_status = text_verified`
- `evidence_link_id` pointing to the exact source/cue/segment evidence

Text verification does not equal playback verification.

## Stage 3: playback check

When media access is available, agents check audio/video evidence and create `verification_checks`
with:

- `check_stage = playback_audio` or `playback_video`
- `check_status = playback_verified`
- `evidence_link_id` pointing to the checked source/time/quote

Audio is enough for content verification. Video is only required when the claim depends on the
screen, visual identity, visible document, or audio/video synchronization.

## Stage 4: final acceptance

Only records with matching playback evidence may be accepted. A final acceptance check uses:

- `check_stage = final_acceptance`
- `check_status = accepted`

The validator rejects final acceptance if there is no prior `playback_verified` check for the
same target.

## What ordinary agents must never do

- Do not turn `unverified` or `text_verified` records into final archive material.
- Do not fill missing timestamps by guessing.
- Do not replace original text with cleaned text.
- Do not use later news or later outcomes in this original-livestream stage.
- Do not treat a web page being reachable as proof that media playback was verified.

## Continuous work rule

After finishing one source-inventory task, transcript task, segmentation task, text cross-check,
playback check, relation pass, or clip pass, the agent must refresh repository state and take the
next eligible task. The work loop stops only at a documented repository stop condition such as
`PROJECT_COMPLETE`, `NO_ELIGIBLE_WORK`, `USER_RECALL`, `HUMAN_DECISION_REQUIRED`,
`SAFETY_OR_ACCESS_BLOCK`, or true `HOST_STOP`.

Claim collisions are normal in multi-agent work. If another agent already owns the next candidate,
refresh and take a different eligible task.

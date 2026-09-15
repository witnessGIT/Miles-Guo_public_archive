# Media Playback Audit

Project: `Miles-Guo_public_archive`

Purpose: prove timing against **real decoded media** while allowing ordinary GitHub-connected Agents to complete Playback Audit without local media tools.

## Non-negotiable distinction

These states MUST NOT be conflated:

1. `playback_decode_verified=true`
   - real media bytes were resolved and decoded around the canonical timestamp;
   - decode success alone contributes **zero** Pilot-60 checks.

2. `content_timing_verified=true`
   - decoded-media evidence located the canonical target content;
   - an observed media position and signed timing error were recorded;
   - the evidence was independently accepted under an allowed review path;
   - only this state may contribute a qualifying playback check.

Transcript anchors, source-page timestamps, HTML timestamps, ASR copied from third-party pages, and ordinary `S-AUDIT-*` records are not Playback Audit evidence.

## Preferred path: Repository Playback Evidence Service

Ordinary Agents do **not** need local `ffmpeg`, `ffprobe`, `yt-dlp`, Whisper or a graphical video player.

The preferred chain is:

```text
worker claims P9-PLAYBACK-*
  -> worker writes playback request
  -> GitHub Actions validates canonical identity and media provenance
  -> ffprobe/ffmpeg decode real media around expected timestamp
  -> whisper.cpp re-transcribes decoded audio with local timestamps
  -> canonical segment text is fuzzy-matched against the new decoded-audio ASR
  -> frames around the expected point are extracted and OCRed
  -> optional free SmolVLM2 adds visual description
  -> durable evidence.json/evidence.md is committed
  -> worker reads that evidence
  -> worker explicitly accepts only if the evidence matches the canonical content
  -> service creates canonical-crosschecked playback-audit v2 record
```

Implementation:

```text
.github/workflows/playback-evidence-service.yml
scripts/process_playback_request.py
scripts/accept_playback_evidence.py
scripts/playback_validation.py
```

Default free stack:

```text
GitHub public-repository standard runner
ffmpeg / ffprobe
yt-dlp
whisper.cpp
Tesseract OCR
optional SmolVLM2-256M-Video-Instruct
```

The audio path is mandatory for ordinary-Agent qualification because Pilot segments are mostly speech/text anchors. Visual analysis is supporting evidence for context or synchronization and must not qualify a segment by itself.

The service must durably distinguish audio extraction failure, Whisper not invoked, Whisper
failure, successful Whisper execution with no entries, and successful parsed ASR. Evidence records
include decoded audio-stream presence, FFmpeg return code, WAV existence/size/duration, an audio
activity measurement, Whisper invocation/return code, SRT existence and parsed entry count.

## Claiming Playback work

```bash
python scripts/playback_queue.py --list
python scripts/playback_queue.py --claim --agent-id agent-<UTC>-<random>
```

When the repository service exists, the claim does not require local ffmpeg or `--content-inspection-capable`.

`--content-inspection-capable` remains an optional declaration for the older/local-manual fallback path only.

## Playback request contract

For each missing canonical timed segment, use a **public media URL already preserved in repository provenance for that live**.

Preferred path:

```text
coordination/playback_requests/<CASE_ID>/<SEGMENT_ID>.json
```

Example:

```json
{
  "request_version": "playback-request-v1",
  "task_id": "P9-PLAYBACK-PILOT-L003",
  "case_id": "PILOT-L003",
  "live_id": "LIVE_20220511_001",
  "segment_id": "LIVE_20220511_001_SEG_000000",
  "media_url": "https://public-media-url-already-preserved-in-provenance",
  "requested_by": "agent-...",
  "requested_at": "ISO-8601 UTC",
  "pre_roll_sec": 10.0,
  "decode_window_sec": 24.0,
  "language": "zh",
  "visual_mode": "frames_ocr"
}
```

CLI helper when shell is available:

```bash
python scripts/playback_queue.py \
  --request <SEGMENT_ID> \
  --case-id <CASE_ID> \
  --media-url '<PUBLIC_URL_ALREADY_IN_REPO_PROVENANCE>' \
  --agent-id <agent-id>
```

The service rejects arbitrary URLs not tied to the canonical live in existing repository source provenance. It must never become a generic download proxy.

## Decode window

The expected canonical position is not necessarily the ffmpeg seek point.

Default:

```text
pre-roll: 10 seconds
window:   24 seconds
coverage: approximately expected-10s through expected+14s
```

This is deliberate: timing error is signed. Content may begin before or after the stored timestamp. A system that begins decoding only at the expected timestamp cannot reliably measure negative timing error.

Durable evidence keeps separate:

```text
expected_start_sec
decode_request_start_sec
decode_start_sec
decode_end_sec
decode_window_sec
candidate_observed_position_sec
candidate_timing_error_sec
```

## Repository evidence

The service writes:

```text
data/playback_evidence/<CASE_ID>/<SEGMENT_ID>/evidence.json
data/playback_evidence/<CASE_ID>/<SEGMENT_ID>/evidence.md
```

The evidence contains, when available:

- canonical case/live/segment identity;
- public media URL and resolver;
- real decode window;
- hashes binding the temporary decoded media/evidence;
- target segment text;
- new Whisper transcript from decoded audio with absolute media positions;
- best text-match score and candidate observed position;
- sampled frame timestamps and hashes;
- OCR from sampled frames;
- optional SmolVLM2 visual summary;
- an immutable `bundle_id` used by worker acceptance.

Full video, clip, audio, model caches and raw temporary images remain in runner/cache storage and are not committed to Git.

Evidence generation alone has:

```text
counts_toward_pilot_60=false
agent_acceptance_required=true
```

## Worker acceptance

A worker MUST read the durable evidence before accepting it.

If the decoded-media evidence really matches the canonical target content, create:

```text
coordination/playback_acceptances/<CASE_ID>/<SEGMENT_ID>.json
```

Example:

```json
{
  "acceptance_version": "playback-acceptance-v1",
  "case_id": "PILOT-L003",
  "live_id": "LIVE_20220511_001",
  "segment_id": "LIVE_20220511_001_SEG_000000",
  "evidence_ref": "data/playback_evidence/PILOT-L003/LIVE_20220511_001_SEG_000000/evidence.json",
  "bundle_id": "copy-exactly-from-evidence",
  "accepted": true,
  "accepted_by": "agent-...",
  "accepted_at": "ISO-8601 UTC",
  "content_observation": "concise factual explanation of why the decoded evidence matches"
}
```

CLI helper:

```bash
python scripts/playback_queue.py \
  --accept <SEGMENT_ID> \
  --case-id <CASE_ID> \
  --content-observation '<why the decoded evidence matches>' \
  --agent-id <agent-id>
```

The acceptance service refuses qualification unless:

- evidence is `ready_for_agent_review`;
- real-media decode succeeded;
- repository content inspection ran;
- audio match meets the configured minimum review score;
- exact evidence `bundle_id` matches;
- case/live/segment/media/timing fields match canonical records;
- the worker explicitly accepted the evidence.

A worker must not manufacture service evidence or accept evidence it has not read.

## Durable qualifying evidence types

`data/playback_audits/<CASE_ID>/<SEGMENT_ID>.json` supports two legitimate paths:

### v1 — local/manual

```text
qualifying_playback_timing_check_v1
```

A capable reviewer directly decodes and inspects media locally using `audit_media.py` + `record_playback_audit.py`.

### v2 — repository evidence service

```text
qualifying_playback_timing_check_v2
```

GitHub Actions performs real-media decode and offline content extraction; a worker reads and accepts the resulting durable evidence; the service then writes the v2 record.

Both are independently revalidated by `scripts/playback_validation.py` and `scripts/audit_gate.py`.

## Low-confidence / blocked evidence

If the decoded audio cannot confidently match the target, the service writes a non-qualifying status such as:

```text
needs_manual_or_wider_review
blocked_media_decode
```

It does not invent an observed position and does not count toward Pilot-60.

A worker may widen/retry through a new authorized request if appropriate, or record a blocked attempt and release the claim. Login/CAPTCHA/paywall/DRM must never be bypassed.

## Optional SmolVLM2

`visual_mode=smolvlm2_optional` requests an open-source visual-summary stage when enabled on the runner. It is supplemental because:

- speech/ASR usually provides the best timing anchor for this archive;
- the small model may be slower or less precise than audio matching;
- failure of the optional model must not corrupt the evidence service.

Default `frames_ocr` remains the lightweight path.

## Pilot-60 gate

Run:

```bash
python scripts/audit_gate.py --json
```

Only valid `data/playback_audits/**/*.json` records count. The gate verifies unique canonical segment IDs, case/live/segment identity, canonical expected start, real decode verification, explicit content/timing verification, observed position within decoded window, internally consistent timing error, and—on v2—binding to repository evidence plus explicit worker acceptance.

Acceptance criteria remain unchanged:

```text
at least 60 qualifying real playback checks
>= 90% within 3 seconds
>= 98% within 8 seconds
false merge rate approximately 0
```

When `pilot60_pass=true`, seal:

```bash
python scripts/playback_queue.py --seal-gate --agent-id <agent-id>
```

Then the current acceptance chain continues:

```text
P9-PLAYBACK-GATE
  -> P9-AUDIT-60-R2
  -> P10-PILOT-DECISION-R2
```

## Capability classification

Because the repository now supplies the preferred media execution environment, absence of local media tools is normally **not HOST_STOP**.

`HOST_STOP` is appropriate only when remaining playback work exists and neither:

- the repository Playback Evidence Service, nor
- a valid local manual path

is available to the current session.

`SAFETY_OR_ACCESS_BLOCK` is reserved for cases that would require bypassing login, CAPTCHA, paywall, DRM or another access control.

## Historical zero-check audits

Older `S-AUDIT-*` reports/readiness markers with zero qualifying checks remain valid historical provenance review. They never count as Playback Audit and never suppress current `P9-PLAYBACK-*` work.

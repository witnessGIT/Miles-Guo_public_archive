# Media Playback Audit

Project: `Miles-Guo_public_archive`

Purpose: remove the recurring capability block where an Agent can verify transcript timestamps but cannot perform an actual media seek/decode around the stored segment time.

## Required distinction

The project has two different verification states and they MUST NOT be conflated:

1. `playback_decode_verified=true`
   - real media bytes were resolved and decoded around the requested timestamp;
   - this proves the media is technically accessible and seekable in the current runtime;
   - by itself it does **not** count toward the Pilot-60 timing gate.

2. `content_timing_verified=true`
   - a reviewer actually inspected the decoded media content around the expected position;
   - the reviewer recorded the observed content position and timing error;
   - only this state may contribute a qualifying real playback timing check.

Transcript anchors, HTML timestamps, search snippets, or source-page text alone are not playback verification.

## Tool

Use:

```bash
python scripts/audit_media.py \
  --media '<public-media-url-or-local-file>' \
  --start 353 \
  --window 12 \
  --label PILOT-E002_SEG_000001
```

Requirements:

- `ffmpeg`
- `ffprobe`
- optional `yt-dlp` for public video pages that are not direct media URLs

The helper:

1. resolves the public media URL when possible;
2. probes stream metadata;
3. seeks to the requested second;
4. actually decodes a short media window;
5. extracts a frame at the requested second when video is present;
6. writes temporary evidence under `cache/audit_media/`.

`cache/` is gitignored. Full videos, clips, screenshots, audio, resolver caches, and other temporary media MUST NOT be committed.

## Audit procedure

For every candidate segment:

1. Read the canonical segment and its expected `start_sec`.
2. Prefer an original/public platform media URL already preserved in repository provenance.
3. Run `scripts/audit_media.py` at the expected time.
4. Inspect the generated short clip/frame (and audio where relevant).
5. Locate where the expected phrase/event is actually observed.
6. Record:
   - expected position;
   - observed position;
   - signed or absolute timing error;
   - media/source URL used;
   - whether the observation was audio, video, or both;
   - reviewer/runtime;
   - any ambiguity.
7. Only then set playback/content verification in durable audit output.

## Counting rule

A successful script run is necessary evidence that real media was decoded, but it is not sufficient for the Pilot-60 gate.

Qualifying check:

```text
real public media accessed
+ actual seek/decode
+ content inspected
+ observed position recorded
+ timing error recorded
```

Non-qualifying check:

```text
GHOT/GWINS/other transcript timestamp only
```

or:

```text
ffmpeg decode succeeded but nobody inspected the content
```

## Durable Pilot-60 evidence

An `S-AUDIT-*` completion file or `coordination/ready/audit/*.json` marker is evidence that an audit task ran. **Its existence is not a Pilot-60 count.**

After a reviewer has actually inspected decoded media and located the expected phrase/event, create one durable playback record per checked segment:

```bash
python scripts/record_playback_audit.py \
  --case-id PILOT-E002 \
  --live-id LIVE_20170610_001 \
  --segment-id LIVE_20170610_001_SEG_000001 \
  --expected-start 353 \
  --observed-position 357 \
  --media-url '<public-media-url>' \
  --reviewer '<agent-or-reviewer-id>' \
  --observation-mode audio \
  --content-observation 'observed the expected HNA sentence beginning' \
  --decode-evidence-json cache/audit_media/PILOT-E002_SEG_000001_353.000.json \
  --content-match
```

The recorder refuses to create a qualifying check unless the referenced `audit_media.py` evidence says real media decoding succeeded and the caller explicitly confirms the content match. The durable record is written under:

```text
data/playback_audits/<CASE_ID>/<SEGMENT_ID>.json
```

Temporary clips/frames remain under `cache/` and are never committed. Where available, their SHA-256 hashes are copied into the durable record so later reviewers can correlate the temporary artifact used during review.

## Pilot-60 gate

Use:

```bash
python scripts/audit_gate.py
```

or machine-readable output:

```bash
python scripts/audit_gate.py --json
```

The gate counts **only** valid `data/playback_audits/**/*.json` records. It intentionally gives zero automatic credit to legacy/current `coordination/ready/audit` markers unless a real playback check was separately recorded.

The gate verifies:

- unique segment IDs;
- real-media decode verification;
- explicit content/timing verification;
- expected and observed positions;
- internally consistent timing error;
- at least 60 qualifying segment checks;
- at least 90% within 3 seconds;
- at least 98% within 8 seconds.

This removes the ambiguity where an audit task can be operationally complete while contributing zero checks to Pilot-60.

## Capability classification

Do not automatically classify the absence of a graphical browser player as `SAFETY_OR_ACCESS_BLOCK`.

If the runtime has shell execution plus ffmpeg/ffprobe and a lawful public media URL, use `scripts/audit_media.py` first.

Use `SAFETY_OR_ACCESS_BLOCK` only when the required media cannot lawfully be accessed without bypassing login, CAPTCHA, paywall, DRM, or another access control.

Use `HOST_STOP` / runtime capability language when the host genuinely cannot execute media tooling or expose the generated evidence for inspection. That is a host limitation, not evidence that the project itself lacks an audit path.

## Existing 0-check audit readiness files

Older audit reports/readiness markers that explicitly say `0 qualifying real playback checks` remain historically valid evidence of transcript/provenance review. They MUST NOT be retroactively counted as playback checks.

They may be followed by a later playback-capable audit that adds qualifying evidence for the same case without rewriting history.

# Media Playback Audit

Project: `Miles-Guo_public_archive`

Purpose: distinguish transcript/source timestamp corroboration from **real decoded-media timing verification** and make Pilot-60 evidence reproducible.

## Required distinction

The project has two verification states and they MUST NOT be conflated:

1. `playback_decode_verified=true`
   - real media bytes were resolved and decoded around the expected timestamp;
   - this proves the media is technically accessible and seekable in the runtime;
   - by itself it does **not** count toward Pilot-60.

2. `content_timing_verified=true`
   - a reviewer actually inspected decoded clip/frame/audio content;
   - the expected phrase/event was located in the decoded media;
   - an observed media position and signed timing error were recorded;
   - only this state may contribute a qualifying playback check.

Transcript anchors, HTML timestamps, source-page timestamps and search snippets are not playback verification.

## Real playback task queue

Ordinary `S-AUDIT-*` tasks may finish with zero qualifying playback checks. Those results remain useful provenance/timeline evidence, but they do not close real playback work.

Real playback work is independently retryable:

```bash
python scripts/playback_queue.py --list
```

A runtime may claim playback work only when it has `ffmpeg`, `ffprobe`, **and can actually inspect the generated media content**:

```bash
python scripts/playback_queue.py \
  --claim \
  --agent-id agent-<UTC>-<random> \
  --content-inspection-capable
```

Do not use `--content-inspection-capable` when the runtime can run commands but cannot view/listen to the decoded evidence and determine the observed content position.

If a claimed case is blocked by media/runtime capability, preserve the attempt and release it for a later capable runtime:

```bash
python scripts/playback_queue.py \
  --block PILOT-E002 \
  --agent-id <agent-id> \
  --reason '<specific factual reason>'
```

Blocked attempts never count toward Pilot-60.

## Decode tool

Use:

```bash
python scripts/audit_media.py \
  --media '<public-media-url>' \
  --start 353 \
  --pre-roll 10 \
  --window 24 \
  --label PILOT-E002_SEG_000001
```

Requirements:

- `ffmpeg`
- `ffprobe`
- optional `yt-dlp` for public video pages that are not direct media URLs

`--start` is the canonical **expected content position**. It is not necessarily the ffmpeg seek point.

The helper defaults to decoding from up to 10 seconds **before** the expected position and continues beyond it. This is mandatory in principle because timing error is signed: the real content may occur before or after the stored timestamp. A tool that starts decoding only at the expected timestamp cannot reliably detect negative timing errors.

The helper records separately:

```text
expected_start_sec
requested_start_sec        # compatibility alias for expected position
decode_start_sec           # actual ffmpeg window start
decode_end_sec
decode_window_sec
pre_roll_sec
```

The default 24-second window with 10-second pre-roll covers at least approximately `expected-10s` through `expected+14s` away from media start, which is sufficient to test both sides of the project’s <=8 second acceptance threshold. If a case requires a wider search, increase `--window` while keeping the expected canonical timestamp unchanged.

The helper:

1. resolves the public media URL when possible;
2. probes stream metadata;
3. starts decoding before the expected timestamp when possible;
4. actually decodes a short media window spanning the expected position;
5. extracts a reference frame at the expected timestamp when video is present;
6. writes temporary evidence under `cache/audit_media/`.

`cache/` is gitignored. Full videos, clips, screenshots, audio, resolver caches and other temporary media MUST NOT be committed.

## Audit procedure

For every candidate segment:

1. Read the canonical segment and its official `start_sec`.
2. Prefer an original/public platform media URL already preserved in repository provenance.
3. Run `scripts/audit_media.py` with `--start` equal to the canonical `start_sec`.
4. Inspect the generated clip/frame/audio across the entire decoded window, including the pre-roll before the expected point.
5. Locate where the expected phrase/event is actually observed.
6. Record:
   - expected canonical position;
   - actual observed position;
   - signed and absolute timing error;
   - public media/source URL used;
   - observation mode (`audio`, `video`, or `both`);
   - reviewer/runtime;
   - concise content observation;
   - any ambiguity.
7. Only then create durable qualifying playback evidence.

A negative timing error is valid and important. Example:

```text
expected = 353.0s
observed = 349.5s
timing_error = -3.5s
```

Do not clamp negative errors to zero or ignore content found in pre-roll.

## Durable Pilot-60 evidence

Create one durable record per actually inspected segment:

```bash
python scripts/record_playback_audit.py \
  --case-id PILOT-E002 \
  --live-id LIVE_20170610_001 \
  --segment-id LIVE_20170610_001_SEG_000001 \
  --expected-start 353 \
  --observed-position 349.5 \
  --media-url '<public-media-url>' \
  --reviewer '<agent-or-reviewer-id>' \
  --observation-mode audio \
  --content-observation 'observed the expected HNA sentence beginning' \
  --decode-evidence-json cache/audit_media/PILOT-E002_SEG_000001_expected_353.000.json \
  --content-match
```

The recorder refuses qualifying evidence unless:

- the canonical segment exists;
- case/live/segment identity is consistent;
- `expected_start` equals the canonical segment `start_sec`;
- real-media decoding succeeded;
- the decode evidence refers to the same expected position and public media URL;
- both expected and observed positions fall inside the decoded window;
- the caller explicitly confirms the decoded content match.

The durable record is written under:

```text
data/playback_audits/<CASE_ID>/<SEGMENT_ID>.json
```

Temporary clips/frames remain under `cache/`. Hashes are preserved where available.

## Pilot-60 gate

Use:

```bash
python scripts/audit_gate.py
```

or:

```bash
python scripts/audit_gate.py --json
```

The gate counts **only** valid `data/playback_audits/**/*.json` records and independently cross-checks them against canonical segment and case/live data. `coordination/ready/audit/*.json` markers do not automatically count.

The gate verifies:

- unique canonical segment IDs;
- case/live/segment identity consistency;
- expected position equals canonical `start_sec`;
- real-media decode verification;
- explicit content/timing verification;
- observed position lies inside the decoded window;
- internally consistent signed/absolute timing error;
- at least 60 qualifying segment checks;
- at least 90% within 3 seconds;
- at least 98% within 8 seconds.

`P9-AUDIT-60` cannot become eligible merely because source-audit tasks are complete. It depends on the `P9-PLAYBACK-GATE` sentinel, which can be created only after the machine gate passes:

```bash
python scripts/playback_queue.py --seal-gate --agent-id <agent-id>
```

## Capability classification

Do not classify the absence of a graphical browser player as `SAFETY_OR_ACCESS_BLOCK` by default.

If a runtime has shell/media tools but cannot lawfully retrieve the public media or cannot inspect generated content, preserve a blocked playback attempt and release the case for another runtime.

Use `SAFETY_OR_ACCESS_BLOCK` only when continuing would require bypassing login, CAPTCHA, paywall, DRM or another access control.

Use `HOST_STOP` / runtime capability language when the host genuinely cannot execute or inspect the required media evidence. That is a host limitation, not evidence that the project lacks a playback path.

## Existing zero-check audit files

Older `S-AUDIT-*` reports/readiness markers that explicitly say `0 qualifying real playback checks` remain historically valid evidence of transcript/provenance review. They MUST NOT be retroactively counted as playback checks and MUST NOT suppress later `P9-PLAYBACK-*` work for the same case.

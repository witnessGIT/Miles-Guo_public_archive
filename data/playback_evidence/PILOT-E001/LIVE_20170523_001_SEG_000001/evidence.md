# Playback Evidence — LIVE_20170523_001_SEG_000001

- Case: `PILOT-E001`
- Live: `LIVE_20170523_001`
- Media: https://rumble.com/v576k9t-20170523.html
- Expected start: `16.000s`
- Decode window: `16.000s` → `16.000s`
- Real media decoded: `false`
- Evidence status: `blocked_media_decode`
- Bundle ID: `4c09b95158e99bab66e62fd12b57b0ec5db45408cd4463e207c3b4296f887e2c`

## Target text

由于现在我要开会，这个直播视频我只能说大概十五分钟左右。

## Decoded-audio ASR match

- Audio extraction return code: `None`
- WAV exists/bytes/duration: `None` / `None` / `None`
- Audio activity detected: `None`
- Whisper status: `None`
- Whisper invoked/return code/entries: `None` / `None` / `0`

No usable Whisper match was produced.

## Sampled frame OCR

No video frames were extracted.

## Agent decision rule

The repository attempted real-media decoding, but decoding did **not** succeed. This is **not** a Pilot-60 qualifying record and must not be accepted.
A worker may submit a playback acceptance only when status is `ready_for_agent_review`, after reading this evidence and confirming that the decoded-audio ASR matches the canonical target content. Visual evidence is supplemental only.

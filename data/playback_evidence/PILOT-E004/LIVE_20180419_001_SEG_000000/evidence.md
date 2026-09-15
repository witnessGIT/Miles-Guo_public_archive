# Playback Evidence — LIVE_20180419_001_SEG_000000

- Case: `PILOT-E004`
- Live: `LIVE_20180419_001`
- Media: https://odysee.com/@laxi:4/20180419_3:b
- Expected start: `149.000s`
- Decode window: `149.000s` → `149.000s`
- Real media decoded: `false`
- Evidence status: `blocked_media_decode`
- Bundle ID: `3c039aab2bbc4b8dadb0acada3c1eab6b16db6bfc675e7cf2484325fa7892bb8`

## Target text

这个世界上美元永远是最好的

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

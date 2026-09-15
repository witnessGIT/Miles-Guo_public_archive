# Playback Evidence — LIVE_20190920_001_SEG_000001

- Case: `PILOT-E008`
- Live: `LIVE_20190920_001`
- Media: https://odysee.com/@laxi:4/20190920:f
- Expected start: `8.000s`
- Decode window: `8.000s` → `8.000s`
- Real media decoded: `false`
- Evidence status: `blocked_media_decode`
- Bundle ID: `ad41ceec9d3bc331fe8f4346f372836adb64f98687a8e29ffcb2797188cd7f48`

## Target text

今天是9月20号，文贵报平安直播。

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

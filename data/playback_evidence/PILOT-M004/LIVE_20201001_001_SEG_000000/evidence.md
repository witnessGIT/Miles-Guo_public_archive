# Playback Evidence — LIVE_20201001_001_SEG_000000

- Case: `PILOT-M004`
- Live: `LIVE_20201001_001`
- Media: https://ghot.ai/archive/videos/2020-10-01-3
- Expected start: `1306.000s`
- Decode window: `1306.000s` → `1306.000s`
- Real media decoded: `false`
- Evidence status: `blocked_media_decode`
- Bundle ID: `4d13f86b7987552c635de226abd42f7d385b461f822ad3f3a53efca996f6211a`

## Target text

到了没有兄弟姐妹们能听到吗？

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

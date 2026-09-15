# Playback Evidence — LIVE_20190530_001_SEG_000001

- Case: `PILOT-E007`
- Live: `LIVE_20190530_001`
- Media: https://odysee.com/@laxi:4/20190530_2:e
- Expected start: `282.000s`
- Decode window: `282.000s` → `282.000s`
- Real media decoded: `false`
- Evidence status: `blocked_media_decode`
- Bundle ID: `c845e5372f4201c35384dbb761100225843fd3d107b5e31d47db7a7e174d6e9e`

## Target text

今天啊，战友们谁能回答我，我为什么穿白裤子。

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

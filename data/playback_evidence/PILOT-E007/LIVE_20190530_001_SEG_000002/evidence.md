# Playback Evidence — LIVE_20190530_001_SEG_000002

- Case: `PILOT-E007`
- Live: `LIVE_20190530_001`
- Media: https://odysee.com/@laxi:4/20190530_2:e
- Expected start: `1411.000s`
- Decode window: `1411.000s` → `1411.000s`
- Real media decoded: `false`
- Evidence status: `blocked_media_decode`
- Bundle ID: `e21f1263d020a5607493d27bfe16c0516006afa04d6c6f39ff8bbf2bb599c3c4`

## Target text

万事败于失秘呀。

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

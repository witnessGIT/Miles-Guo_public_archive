# Playback Evidence — LIVE_20210902_001_SEG_000002

- Case: `PILOT-M007`
- Live: `LIVE_20210902_001`
- Media: https://gettr.com/post/p9xyj1e4d0
- Expected start: `446.000s`
- Decode window: `446.000s` → `446.000s`
- Real media decoded: `false`
- Evidence status: `blocked_media_decode`
- Bundle ID: `e657da0d35dcb4a1156a3a682eadd48612ca4dcac737b0396678d80306fb68bb`

## Target text

我们明天上午大直播

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

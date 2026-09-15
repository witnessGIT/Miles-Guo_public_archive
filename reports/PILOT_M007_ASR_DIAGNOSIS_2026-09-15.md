# PILOT-M007 ASR diagnosis — 2026-09-15

Scope: diagnose the public Playback Evidence Service only. The active `P9-PLAYBACK-PILOT-M007` claim is not modified, replaced, or released, and no acceptance is created.

## Evidence chain

1. The GETTR request was genuinely decoded. Durable M007 evidence records `playback_decode_verified=true`, a 24 s decoded window, decoded frame hashes, and `decode_resolver=yt-dlp`.
2. `audio_asr.model=ggml-small.bin` proves the workflow exported a Whisper model path, while `audio_asr.process_returncode=null` proves `whisper-cli` was never invoked by `process_playback_request.py`.
3. The workflow run that produced the evidence completed `Prepare portable whisper.cpp` successfully. Therefore the null Whisper return code is not evidence of a Whisper inference failure.
4. In `process_playback_request.py`, Whisper is invoked only when `audio_proc.returncode == 0 and whisper_available and whisper_model`. The model was present and the Runner had just successfully built the CLI. The remaining failed gate is FFmpeg audio extraction.
5. The public resolver in `audit_media.py` currently executes `yt-dlp -g --no-playlist SOURCE` and blindly returns `out.strip().splitlines()[0]`. On sites where yt-dlp returns separate selected video and audio URLs, the first URL is the video representation. The decoder can therefore produce a valid video-only MP4.
6. `_decoded_clip_is_usable()` currently accepts a clip containing *either* audio or video. Consequently a video-only clip is promoted as `playback_decode_verified=true`. The later FFmpeg `-vn ... audio_16k_mono.wav` extraction fails because the clip has no audio stream. The code then silently skips Whisper and serializes `entries=[]`, `process_returncode=null`, and empty stderr, losing the actual FFmpeg failure.

## Root cause

This is a public ASR pipeline bug, not a demonstrated silent M007 source segment and not an SRT parser bug. The resolver/validation contract permits a video-only yt-dlp representation to enter an ASR-required pipeline, and ASR prerequisite failures are not durably surfaced.

## Required fix

- yt-dlp resolution must explicitly request a representation containing both audio and video where available (with a documented audio-bearing fallback).
- decoded media intended for Playback ASR must be rejected or separately classified when no audio stream exists.
- durable evidence must include source/decoded audio-stream presence, WAV extraction return code, WAV size/duration and a non-silence measurement, Whisper availability/execution return code, output-file existence, and parse result count.
- `entries=[]` must no longer be ambiguous between silence, extraction failure, Whisper-not-run, Whisper failure, and parser failure.

A regression test was added at `tests/test_playback_asr_media_selection.py`; it intentionally locks these requirements before the production fix is considered complete.

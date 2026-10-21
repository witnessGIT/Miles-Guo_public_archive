#!/usr/bin/env python3
"""Transcribe one livestream on an ephemeral GitHub-hosted Apple runner.

The media, extracted audio, model and cache are never added to Git. Only
timestamped machine-ASR records, provenance, checksums and an attempt result
are written under data/current.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL = "mlx-community/whisper-large-v3-turbo"
USER_AGENT = "curl/8.7.1"
CHUNK_DURATION_SEC = 900


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audio_duration_sec(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return max(0.0, float(completed.stdout.strip()))


def assess_transcript_quality(
    segments: list[dict[str, Any]], duration_sec: float,
) -> dict[str, Any]:
    """Apply conservative machine-ASR quality gates before task completion."""
    reasons: list[str] = []
    warnings: list[str] = []
    texts = [str(item.get("text") or "").strip() for item in segments]
    char_count = sum(len(re.sub(r"\s+", "", text)) for text in texts)
    duration_minutes = max(duration_sec / 60.0, 1 / 60.0)
    chars_per_minute = char_count / duration_minutes
    invalid_timestamps = 0
    last_cue_end = 0.0
    confidence_segment_count = 0
    low_confidence_segment_count = 0
    high_no_speech_segment_count = 0
    high_compression_segment_count = 0
    for item in segments:
        try:
            start = float(item.get("start_sec"))
            end = float(item.get("end_sec"))
        except (TypeError, ValueError):
            invalid_timestamps += 1
            continue
        if start < 0 or end < start or end > duration_sec + 30:
            invalid_timestamps += 1
        last_cue_end = max(last_cue_end, end)
        avg_logprob = item.get("avg_logprob")
        no_speech_prob = item.get("no_speech_prob")
        compression_ratio = item.get("compression_ratio")
        if avg_logprob is not None:
            confidence_segment_count += 1
            if float(avg_logprob) < -1.2:
                low_confidence_segment_count += 1
        if no_speech_prob is not None and float(no_speech_prob) > 0.8:
            high_no_speech_segment_count += 1
        if compression_ratio is not None and float(compression_ratio) > 2.6:
            high_compression_segment_count += 1

    normalized = [
        re.sub(r"[^\w\u3400-\u9fff]+", "", text.lower())
        for text in texts
    ]
    repeat_candidates = [text for text in normalized if len(text) >= 4]
    counts: dict[str, int] = {}
    for text in repeat_candidates:
        counts[text] = counts.get(text, 0) + 1
    repeated_chars = sum(
        len(text) * count for text, count in counts.items() if count >= 3
    )
    candidate_chars = sum(len(text) for text in repeat_candidates)
    repeated_text_ratio = repeated_chars / candidate_chars if candidate_chars else 0.0
    end_coverage_ratio = min(1.0, last_cue_end / duration_sec) if duration_sec > 0 else 0.0

    minimum_chars = max(20, int(duration_minutes * 5))
    if not segments or char_count < minimum_chars:
        reasons.append("transcript_too_sparse_for_audio_duration")
    if invalid_timestamps:
        reasons.append("invalid_or_out_of_bounds_timestamps")
    if candidate_chars >= 200 and repeated_text_ratio > 0.8:
        reasons.append("probable_repetition_or_hallucination")
    if (
        confidence_segment_count >= 5
        and low_confidence_segment_count / confidence_segment_count > 0.6
    ):
        reasons.append("predominantly_low_confidence_dictation")
    if len(segments) >= 5 and high_no_speech_segment_count / len(segments) > 0.6:
        reasons.append("probable_speech_transcribed_from_non_speech")
    if len(segments) >= 5 and high_compression_segment_count / len(segments) > 0.4:
        reasons.append("probable_compressed_repetitive_dictation")
    if duration_sec >= 600 and end_coverage_ratio < 0.15:
        reasons.append("transcript_ends_too_early_for_audio_duration")
    elif duration_sec >= 300 and end_coverage_ratio < 0.5:
        warnings.append("low_end_of_audio_coverage_needs_text_review")

    density_score = min(1.0, chars_per_minute / 60.0)
    repetition_score = max(0.0, 1.0 - repeated_text_ratio)
    timing_score = 1.0 if not invalid_timestamps else 0.0
    quality_score = round(
        density_score * 0.45 + repetition_score * 0.35 + timing_score * 0.20,
        4,
    )
    return {
        "schema_version": "cloud-asr-quality-v1",
        "gate_status": "pass" if not reasons else "deferred_review",
        "quality_score": quality_score,
        "reasons": reasons,
        "warnings": warnings,
        "metrics": {
            "audio_duration_sec": round(duration_sec, 3),
            "segment_count": len(segments),
            "text_character_count": char_count,
            "characters_per_minute": round(chars_per_minute, 3),
            "invalid_timestamp_count": invalid_timestamps,
            "repeated_text_ratio": round(repeated_text_ratio, 6),
            "end_coverage_ratio": round(end_coverage_ratio, 6),
            "confidence_segment_count": confidence_segment_count,
            "low_confidence_segment_count": low_confidence_segment_count,
            "high_no_speech_segment_count": high_no_speech_segment_count,
            "high_compression_segment_count": high_compression_segment_count,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def http_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def resolve_media_url(asset: sqlite3.Row) -> str | None:
    metadata = json.loads(asset["metadata_json"] or "{}")
    platform = str(asset["platform"] or "").strip().lower()
    if platform == "gettr":
        path = metadata.get("video_path") or metadata.get("original_video_path")
        if not path:
            return None
        if str(path).startswith(("http://", "https://")):
            return str(path)
        return "https://media.gettr.com/" + str(path).lstrip("/")
    if platform == "rumble":
        embed_id = metadata.get("rumble_embed_id") or metadata.get("embed_id")
        if not embed_id:
            return None
        url = f"https://rumble.com/embedJS/u3/?request=video&ver=2&v={urllib.parse.quote(str(embed_id))}"
        payload = http_json(url)
        candidates: list[tuple[int, str]] = []
        primary = payload.get("u", {}).get("mp4", {})
        if primary.get("url"):
            candidates.append((int(primary.get("meta", {}).get("bitrate") or 999999), primary["url"]))
        for item in payload.get("ua", {}).get("mp4", {}).values():
            if item.get("url"):
                candidates.append((int(item.get("meta", {}).get("bitrate") or 999999), item["url"]))
        return min(candidates)[1] if candidates else None
    if platform in {"odysee", "lbry"}:
        canonical = metadata.get("canonical_url")
        claim_id = metadata.get("claim_id")
        if not canonical or not claim_id:
            return None
        name = str(canonical).split("/")[-1].split("#", 1)[0]
        return f"https://player.odycdn.com/api/v4/streams/free/{urllib.parse.quote(name, safe='')}/{claim_id}/best"
    if platform == "youtube":
        return str(asset["url"])
    if str(asset["url"]).lower().endswith((".mp4", ".m3u8", ".mp3", ".m4a", ".wav", ".ogg")):
        return str(asset["url"])
    return None


def assets(conn: sqlite3.Connection, live_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ma.*, ls.priority AS source_priority
        FROM media_assets ma
        LEFT JOIN live_sources ls ON ls.id = ma.source_id
        WHERE ma.live_id = ?
          AND ma.asset_role IN ('original_video','mirror_video','audio')
          AND ma.availability_status NOT IN ('dead','blocked')
        ORDER BY CASE lower(COALESCE(ma.platform,''))
          WHEN 'gettr' THEN 0 WHEN 'rumble' THEN 1 WHEN 'odysee' THEN 2
          WHEN 'lbry' THEN 2 WHEN 'youtube' THEN 3 ELSE 4 END,
          COALESCE(ls.priority, 999), ma.id
        """,
        (live_id,),
    ).fetchall()


def extract_audio(media_url: str, destination: Path) -> None:
    partial = destination.with_suffix(".ogg.partial")
    partial.unlink(missing_ok=True)
    direct = media_url.lower().endswith((".mp4", ".m3u8", ".mp3", ".m4a", ".wav", ".ogg")) or "odycdn.com/" in media_url
    if direct:
        input_url = media_url
    else:
        probe = subprocess.run(
            ["yt-dlp", "--no-playlist", "-f", "bestaudio/best", "-g", media_url],
            check=True,
            capture_output=True,
            text=True,
        )
        input_url = probe.stdout.splitlines()[0].strip()
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "warning", "-y",
            "-user_agent", USER_AGENT, "-i", input_url, "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "libopus", "-b:a", "32k", "-f", "ogg", str(partial),
        ],
        check=True,
    )
    if not partial.exists() or partial.stat().st_size == 0:
        raise RuntimeError("ffmpeg produced no audio")
    os.replace(partial, destination)


def checkpoint_dir(repo: Path, live_id: str) -> Path:
    return repo / "data" / "current" / "asr_checkpoints" / f"asr_{live_id.lower()}"


def transcribe_chunked(
    audio: Path, chunk_root: Path, mlx_whisper: Any,
    checkpoint_root: Path | None = None, live_id: str = "",
) -> dict[str, Any]:
    """Transcribe bounded chunks and durably resume completed structured results."""
    shutil.rmtree(chunk_root, ignore_errors=True)
    chunk_root.mkdir(parents=True, exist_ok=True)
    pattern = chunk_root / "chunk_%04d.wav"
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "warning", "-y",
            "-i", str(audio), "-map", "0:a:0", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", "-f", "segment", "-segment_time",
            str(CHUNK_DURATION_SEC), "-reset_timestamps", "1", str(pattern),
        ],
        check=True,
    )
    chunks = sorted(chunk_root.glob("chunk_*.wav"))
    if not chunks:
        raise RuntimeError("ffmpeg produced no ASR chunks")

    if checkpoint_root is not None:
        checkpoint_root.mkdir(parents=True, exist_ok=True)
    combined_text: list[str] = []
    combined_segments: list[dict[str, Any]] = []
    language = "zh"
    resumed_chunks = 0
    for chunk_index, chunk in enumerate(chunks):
        offset = chunk_index * CHUNK_DURATION_SEC
        chunk_digest = sha256_file(chunk)
        checkpoint_path = checkpoint_root / f"chunk_{chunk_index:04d}.json" if checkpoint_root else None
        checkpoint: dict[str, Any] | None = None
        if checkpoint_path and checkpoint_path.exists():
            try:
                candidate = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                if (
                    candidate.get("schema_version") == "cloud-asr-chunk-v1"
                    and candidate.get("live_id") == live_id
                    and candidate.get("model") == MODEL
                    and candidate.get("chunk_index") == chunk_index
                    and candidate.get("offset_sec") == offset
                    and candidate.get("chunk_audio_sha256") == chunk_digest
                ):
                    checkpoint = candidate
                    resumed_chunks += 1
            except (OSError, json.JSONDecodeError):
                checkpoint = None
        if checkpoint is None:
            result = mlx_whisper.transcribe(
                str(chunk), path_or_hf_repo=MODEL, language="zh", task="transcribe",
                word_timestamps=False, condition_on_previous_text=True, verbose=False,
            )
            checkpoint = {
                "schema_version": "cloud-asr-chunk-v1",
                "live_id": live_id,
                "chunk_index": chunk_index,
                "offset_sec": offset,
                "chunk_audio_sha256": chunk_digest,
                "model": MODEL,
                "language": str(result.get("language") or language),
                "text": str(result.get("text") or "").strip(),
                "segments": [
                    {
                        "start": round(offset + float(segment["start"]), 3),
                        "end": max(
                            round(offset + float(segment["start"]), 3),
                            round(offset + float(segment["end"]), 3),
                        ),
                        "text": str(segment.get("text") or "").strip(),
                        **{
                            key: round(float(segment[key]), 6)
                            for key in (
                                "avg_logprob", "no_speech_prob", "compression_ratio",
                            )
                            if segment.get(key) is not None
                        },
                    }
                    for segment in result.get("segments") or []
                    if str(segment.get("text") or "").strip()
                ],
                "completed_at": utc_now(),
                "processing_location": "github-hosted-macos-arm64",
                "media_committed_to_git": False,
                "paid_api_used": False,
            }
            if checkpoint_path:
                write_json(checkpoint_path, checkpoint)
        language = str(checkpoint.get("language") or language)
        chunk_text = str(checkpoint.get("text") or "").strip()
        if chunk_text:
            combined_text.append(chunk_text)
        for segment in checkpoint.get("segments") or []:
            text = str(segment.get("text") or "").strip()
            if not text:
                continue
            start = round(float(segment["start"]), 3)
            end = max(start, round(float(segment["end"]), 3))
            combined_segments.append({
                "start": start,
                "end": end,
                "text": text,
                **{
                    key: segment[key]
                    for key in (
                        "avg_logprob", "no_speech_prob", "compression_ratio",
                    )
                    if segment.get(key) is not None
                },
            })
        chunk.unlink(missing_ok=True)
    if checkpoint_root is not None:
        expected = {f"chunk_{index:04d}.json" for index in range(len(chunks))}
        for stale in checkpoint_root.glob("chunk_*.json"):
            if stale.name not in expected:
                stale.unlink(missing_ok=True)
    return {
        "text": " ".join(combined_text),
        "segments": combined_segments,
        "language": language,
        "chunk_count": len(chunks),
        "resumed_chunk_count": resumed_chunks,
    }


def output_paths(repo: Path, live_id: str) -> dict[str, Path]:
    stem = f"asr_{live_id.lower()}"
    root = repo / "data" / "current"
    return {
        "version": root / "transcript_versions" / f"{stem}.jsonl",
        "cues": root / "transcript_cues" / f"{stem}.jsonl",
        "segments": root / "live_segments" / f"{stem}.jsonl",
        "manifest": root / "asr_manifests" / f"{stem}.json",
        "attempt": root / "asr_attempts" / f"cloud_{live_id.lower()}.json",
    }


def publish(repo: Path, payload: dict[str, Any]) -> list[str]:
    live_id = str(payload["live_id"])
    created_at = str(payload["generated_at"])
    version_id = f"TR_{live_id}_asr_raw_zh_001"
    paths = output_paths(repo, live_id)
    version = {
        "id": version_id, "live_id": live_id, "source_id": payload.get("source_id"),
        "transcript_kind": "asr_raw", "language": payload.get("language") or "zh",
        "text": payload.get("text") or "", "parent_version_id": None,
        "generated_by": f"mlx-whisper GitHub-hosted offline inference; model={payload['model']}; machine raw, not human corrected",
        "confidence": (payload.get("quality") or {}).get("quality_score"),
        "created_at": created_at,
    }
    cues: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get("segments") or []):
        text = str(item.get("text") or "").strip()
        start = item.get("start_sec")
        end = max(start, item.get("end_sec")) if start is not None and item.get("end_sec") is not None else item.get("end_sec")
        cue_id = f"{version_id}_CUE_{index:06d}"
        segment_id = f"{live_id}_SEG_{index:06d}"
        cues.append({
            "id": cue_id, "transcript_version_id": version_id, "live_id": live_id,
            "cue_index": index, "start_sec": start, "end_sec": end,
            "speaker_entity_id": None, "text": text, "timing_status": "asr",
            "confidence": None, "source_cue_id": None,
        })
        segments.append({
            "id": segment_id, "live_id": live_id, "segment_index": index,
            "text_curated": None, "text_asr": text, "text_search": text, "text_summary": None,
            "start_sec": start, "end_sec": end, "start_frame": None, "end_frame": None,
            "fps_at_index": None, "topic_primary": None, "topic_secondary": None,
            "entities_json": None, "keywords_json": None, "curated_source_id": None,
            "asr_source_id": payload.get("source_id"), "time_source_id": payload.get("source_id"),
            "alignment_quality": None, "alignment_method": "asr", "source_verified": 1,
            "playback_verified": 0, "playback_verified_at": None, "review_status": "machine",
            "created_at": created_at, "updated_at": created_at,
        })
    manifest = {key: payload.get(key) for key in (
        "schema_version", "live_id", "status", "source_id", "media_asset_id", "source_url",
        "resolved_media_url", "audio_sha256", "audio_size_bytes", "model", "software",
        "language", "generated_at", "processing_elapsed_sec", "source_attempt_errors",
        "processing_location", "processing_path", "path_persistence",
        "chunk_duration_sec", "chunk_count", "resumed_chunk_count",
        "audio_duration_sec", "quality",
    )}
    manifest.update({
        "transcript_version_id": version_id, "cue_count": len(cues), "segment_count": len(segments),
        "verification_level": "machine_unverified", "media_committed_to_git": False,
        "paid_api_used": False,
    })
    write_jsonl(paths["version"], [version])
    write_jsonl(paths["cues"], cues)
    write_jsonl(paths["segments"], segments)
    write_json(paths["manifest"], manifest)
    paths["attempt"].unlink(missing_ok=True)
    return [str(paths[key].relative_to(repo)) for key in ("version", "cues", "segments", "manifest")]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--live-id", required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    work = args.work_root.resolve()
    work.mkdir(parents=True, exist_ok=True)
    audio = work / f"{args.live_id}.ogg"
    chunk_root = work / f"{args.live_id}.chunks"
    checkpoints = checkpoint_dir(repo, args.live_id)
    result_file = work / f"{args.live_id}.result.json"
    paths = output_paths(repo, args.live_id)
    if paths["version"].exists() and paths["cues"].exists() and paths["segments"].exists():
        print(json.dumps({"status": "already_done", "live_id": args.live_id}, ensure_ascii=False))
        return 0
    conn = sqlite3.connect(repo / "database" / "Miles-Guo_public_archive.sqlite3")
    conn.row_factory = sqlite3.Row
    errors: list[dict[str, str]] = []
    try:
        chosen: tuple[sqlite3.Row, str] | None = None
        for asset in assets(conn, args.live_id):
            try:
                resolved = resolve_media_url(asset)
                if not resolved:
                    continue
                extract_audio(resolved, audio)
                chosen = (asset, resolved)
                break
            except Exception as exc:
                errors.append({"asset_id": str(asset["id"]), "error": str(exc)[:1000]})
                audio.unlink(missing_ok=True)
        if chosen is None:
            raise RuntimeError("no media source was reachable from this GitHub-hosted runner")
        asset, resolved = chosen
        audio_digest = sha256_file(audio)
        duration_sec = audio_duration_sec(audio)
        resume_manifest = checkpoints / "source.json"
        # Fresh OGG files can be byte-different even when their decoded audio is
        # identical (for example, because container serial/header values change).
        # Keep prior checkpoints here and validate every decoded PCM chunk by its
        # own SHA-256 in transcribe_chunked.  A genuinely changed source therefore
        # invalidates only the chunks whose audio content changed.
        write_json(resume_manifest, {
            "schema_version": "cloud-asr-checkpoint-set-v1",
            "live_id": args.live_id,
            "source_id": asset["source_id"],
            "media_asset_id": asset["id"],
            "source_url": asset["url"],
            "audio_sha256": audio_digest,
            "audio_size_bytes": audio.stat().st_size,
            "audio_duration_sec": round(duration_sec, 3),
            "model": MODEL,
            "chunk_duration_sec": CHUNK_DURATION_SEC,
            "resume_validation": "per_chunk_pcm_wav_sha256",
            "processing_location": "github-hosted-macos-arm64",
            "media_committed_to_git": False,
            "paid_api_used": False,
        })
        import mlx_whisper
        started = time.monotonic()
        result = transcribe_chunked(audio, chunk_root, mlx_whisper, checkpoints, args.live_id)
        elapsed = round(time.monotonic() - started, 3)
        segments = []
        for index, segment in enumerate(result.get("segments") or []):
            text = str(segment.get("text") or "").strip()
            if not text:
                continue
            start = round(float(segment["start"]), 3)
            end = max(start, round(float(segment["end"]), 3))
            segments.append({
                "index": index,
                "start_sec": start,
                "end_sec": end,
                "text": text,
                **{
                    key: segment[key]
                    for key in (
                        "avg_logprob", "no_speech_prob", "compression_ratio",
                    )
                    if segment.get(key) is not None
                },
            })
        payload = {
            "schema_version": "cloud-asr-result-v1", "live_id": args.live_id,
            "status": "transcribed", "source_id": asset["source_id"], "media_asset_id": asset["id"],
            "source_url": asset["url"], "resolved_media_url": resolved,
            "audio_sha256": audio_digest, "audio_size_bytes": audio.stat().st_size,
            "audio_duration_sec": round(duration_sec, 3),
            "model": MODEL, "software": "mlx-whisper", "language": result.get("language") or "zh",
            "generated_at": utc_now(), "processing_elapsed_sec": elapsed,
            "text": str(result.get("text") or "").strip(), "segments": segments,
            "chunk_duration_sec": CHUNK_DURATION_SEC, "chunk_count": result.get("chunk_count"),
            "resumed_chunk_count": result.get("resumed_chunk_count", 0),
            "source_attempt_errors": errors, "processing_location": "github-hosted-macos-arm64",
            "processing_path": str(audio), "path_persistence": "ephemeral_deleted_after_job",
        }
        quality = assess_transcript_quality(segments, duration_sec)
        payload["quality"] = quality
        if quality["gate_status"] != "pass":
            attempt = {
                "schema_version": "cloud-asr-attempt-v1",
                "live_id": args.live_id,
                "status": "cloud_asr_quality_failed_deferred",
                "generated_at": utc_now(),
                "processing_location": "github-hosted-macos-arm64",
                "model": MODEL,
                "paid_api_used": False,
                "media_committed_to_git": False,
                "deferred_until_corpus_tail": True,
                "retry_queue": "corpus_tail",
                "deferred_reason": (
                    "machine transcript failed dictation, timing, coverage, or "
                    "hallucination quality gates"
                ),
                "error": "machine transcript did not pass conservative ASR quality gates",
                "quality": quality,
                "source_id": asset["source_id"],
                "media_asset_id": asset["id"],
                "source_url": asset["url"],
            }
            write_json(paths["attempt"], attempt)
            print(json.dumps(attempt, ensure_ascii=False))
            return 3
        write_json(result_file, payload)
        outputs = publish(repo, payload)
        print(json.dumps({"status": "transcribed", "live_id": args.live_id, "outputs": outputs, "segments": len(segments)}, ensure_ascii=False))
        return 0
    except Exception as exc:
        attempt = {
            "schema_version": "cloud-asr-attempt-v1", "live_id": args.live_id,
            "status": "cloud_attempt_failed_needs_retry", "generated_at": utc_now(),
            "processing_location": "github-hosted-macos-arm64", "model": MODEL,
            "paid_api_used": False, "media_committed_to_git": False,
            "error": str(exc)[:2000], "source_attempt_errors": errors,
        }
        write_json(paths["attempt"], attempt)
        print(json.dumps(attempt, ensure_ascii=False))
        return 2
    finally:
        conn.close()
        audio.unlink(missing_ok=True)
        shutil.rmtree(chunk_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

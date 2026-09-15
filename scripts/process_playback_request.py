#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from playback_validation import canonical_segment_index, pilot_case_live_map

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "coordination" / "claims"
REQUEST_ROOT = ROOT / "coordination" / "playback_requests"
EVIDENCE_ROOT = ROOT / "data" / "playback_evidence"
CACHE_ROOT = ROOT / "cache" / "playback_evidence"
SOURCE_ROOT = ROOT / "data" / "sources"
AUDIT_MEDIA = ROOT / "scripts" / "audit_media.py"
SMOLVLM_INSPECT = ROOT / "scripts" / "smolvlm_inspect.py"

REQUEST_VERSION = "playback-request-v1"
EVIDENCE_VERSION = "repository-playback-evidence-v1"
MIN_AGENT_REVIEW_SCORE = 0.55


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def probe_media(path: Path) -> tuple[int, dict, str]:
    process = run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=index,codec_type,codec_name,sample_rate,channels",
        "-of", "json", str(path),
    ])
    payload: dict = {}
    if process.returncode == 0:
        try:
            parsed = json.loads(process.stdout or "{}")
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            return 1, {}, "ffprobe returned invalid JSON"
    return process.returncode, payload, process.stderr[-2000:]


def audio_probe_summary(path: Path) -> dict:
    rc, probe, stderr = probe_media(path)
    streams = probe.get("streams") if isinstance(probe, dict) else []
    audio_streams = [
        stream for stream in streams or []
        if isinstance(stream, dict) and stream.get("codec_type") == "audio"
    ]
    try:
        duration = float((probe.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        duration = None
    return {
        "probe_returncode": rc,
        "probe_stderr_tail": stderr,
        "has_audio_stream": bool(audio_streams),
        "audio_streams": audio_streams,
        "duration_sec": duration,
    }


VOLUME_RE = re.compile(r"(mean_volume|max_volume):\s*(-?inf|-?[0-9.]+)\s*dB", re.I)


def measure_audio_activity(path: Path) -> dict:
    process = run([
        "ffmpeg", "-v", "info", "-i", str(path), "-af", "volumedetect",
        "-f", "null", "-",
    ])
    values: dict[str, float | None] = {}
    for key, raw in VOLUME_RE.findall(process.stderr or ""):
        values[key.lower()] = None if raw.lower() == "-inf" else float(raw)
    maximum = values.get("max_volume")
    return {
        "returncode": process.returncode,
        "mean_volume_db": values.get("mean_volume"),
        "max_volume_db": maximum,
        "non_silent": maximum is not None and maximum > -60.0,
        "stderr_tail": process.stderr[-2000:] if process.returncode != 0 else "",
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def iter_json_records(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        try:
            if path.suffix.lower() == ".json":
                payload = json.loads(path.read_text(encoding="utf-8"))
                rows = payload if isinstance(payload, list) else [payload]
            else:
                rows = []
                for raw in path.read_text(encoding="utf-8").splitlines():
                    raw = raw.strip()
                    if raw and not raw.startswith("#"):
                        rows.append(json.loads(raw))
            for row in rows:
                if isinstance(row, dict):
                    yield path, row
        except (OSError, json.JSONDecodeError):
            continue


URL_RE = re.compile(r"https?://[^\s\"'<>]+")


def extract_urls(value: object, *, depth: int = 0) -> set[str]:
    if depth > 8:
        return set()
    found: set[str] = set()
    if isinstance(value, dict):
        for child in value.values():
            found.update(extract_urls(child, depth=depth + 1))
    elif isinstance(value, list):
        for child in value:
            found.update(extract_urls(child, depth=depth + 1))
    elif isinstance(value, str):
        text = value.strip()
        for match in URL_RE.findall(text):
            found.add(match.rstrip(".,);]}>"))
        if text[:1] in {"{", "["}:
            try:
                found.update(extract_urls(json.loads(text), depth=depth + 1))
            except json.JSONDecodeError:
                pass
    return found


def trusted_media_urls(live_id: str) -> set[str]:
    urls: set[str] = set()
    for _, row in iter_json_records(SOURCE_ROOT) or []:
        if str(row.get("live_id") or "") != live_id:
            continue
        urls.update(extract_urls(row))
    return urls


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text.lower())


def keyword_tokens(text: str | None) -> list[str]:
    if not text:
        return []
    tokens = []
    for raw in re.split(r"[\s,，。.;；:：/|]+", text):
        token = normalize_text(raw)
        if len(token) >= 2:
            tokens.append(token)
    return tokens[:20]


def parse_srt_time(raw: str) -> float:
    hours, minutes, rest = raw.strip().split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0


def parse_srt(path: Path) -> list[dict]:
    if not path.exists():
        return []
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8", errors="replace").strip())
    rows: list[dict] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        timing_index = 1 if len(lines) > 1 and "-->" in lines[1] else 0
        if "-->" not in lines[timing_index]:
            continue
        start_raw, end_raw = [part.strip() for part in lines[timing_index].split("-->", 1)]
        try:
            start = parse_srt_time(start_raw)
            end = parse_srt_time(end_raw)
        except (ValueError, IndexError):
            continue
        text = " ".join(lines[timing_index + 1 :]).strip()
        if text:
            rows.append({"start_sec": start, "end_sec": end, "text": text})
    return rows


def best_asr_match(entries: list[dict], target: str, search_text: str | None) -> dict | None:
    target_norm = normalize_text(target)
    if len(target_norm) < 4 or not entries:
        return None
    keywords = keyword_tokens(search_text)
    best: dict | None = None
    max_window = min(5, len(entries))
    for i in range(len(entries)):
        for width in range(1, max_window + 1):
            part = entries[i : i + width]
            if not part:
                continue
            combined = "".join(str(row.get("text") or "") for row in part)
            combined_norm = normalize_text(combined)
            if not combined_norm:
                continue
            ratio = difflib.SequenceMatcher(None, target_norm, combined_norm).ratio()
            coverage = 0.0
            if keywords:
                hits = sum(1 for token in keywords if token in combined_norm)
                coverage = hits / len(keywords)
            score = max(ratio, ratio * 0.75 + coverage * 0.25)
            candidate = {
                "local_start_sec": float(part[0]["start_sec"]),
                "local_end_sec": float(part[-1]["end_sec"]),
                "text": combined,
                "similarity": round(ratio, 6),
                "keyword_coverage": round(coverage, 6),
                "score": round(score, 6),
                "entry_count": len(part),
            }
            if best is None or candidate["score"] > best["score"]:
                best = candidate
    return best



def best_ocr_match(frames: list[dict], target: str, search_text: str | None) -> dict | None:
    """Find a conservative target-text candidate in sampled frame OCR.

    Whole-frame OCR is noisy, so score individual lines and short adjacent line windows.
    A match only promotes decoded evidence to agent review; it never creates a qualifying
    playback record without explicit active-claim-owner acceptance.
    """
    target_norm = normalize_text(target)
    if len(target_norm) < 4 or not frames:
        return None
    keywords = keyword_tokens(search_text)
    best: dict | None = None
    for frame in frames:
        raw = str(frame.get("ocr_text") or "")
        lines = [line.strip() for line in raw.splitlines() if normalize_text(line)]
        if not lines:
            continue
        max_window = min(3, len(lines))
        for i in range(len(lines)):
            for width in range(1, max_window + 1):
                part = lines[i : i + width]
                if not part:
                    continue
                combined = " ".join(part)
                combined_norm = normalize_text(combined)
                if len(combined_norm) < 4:
                    continue
                ratio = difflib.SequenceMatcher(None, target_norm, combined_norm).ratio()
                coverage = 0.0
                if keywords:
                    hits = sum(1 for token in keywords if token in combined_norm)
                    coverage = hits / len(keywords)
                score = max(ratio, ratio * 0.75 + coverage * 0.25)
                candidate = {
                    "local_sec": float(frame.get("local_sec") or 0.0),
                    "absolute_sec": float(frame.get("absolute_sec") or 0.0),
                    "text": combined,
                    "similarity": round(ratio, 6),
                    "keyword_coverage": round(coverage, 6),
                    "score": round(score, 6),
                    "line_count": len(part),
                    "frame_sha256": frame.get("sha256"),
                }
                if best is None or candidate["score"] > best["score"]:
                    best = candidate
    return best

def frame_offsets(window: float, expected_local: float) -> list[float]:
    candidates = [
        max(0.0, expected_local - 8.0),
        max(0.0, expected_local - 4.0),
        max(0.0, expected_local),
        min(max(0.0, window - 0.5), expected_local + 4.0),
        min(max(0.0, window - 0.5), expected_local + 8.0),
    ]
    result: list[float] = []
    for value in candidates:
        value = round(max(0.0, min(value, max(0.0, window - 0.1))), 3)
        if value not in result:
            result.append(value)
    return result


def collect_frame_evidence(
    clip: Path,
    temp_dir: Path,
    decode_start: float,
    expected: float,
    window: float,
) -> list[dict]:
    results: list[dict] = []
    expected_local = max(0.0, expected - decode_start)
    tesseract = shutil.which("tesseract")
    for index, local_sec in enumerate(frame_offsets(window, expected_local)):
        frame = temp_dir / f"frame_{index:02d}_{local_sec:.3f}.jpg"
        proc = run([
            "ffmpeg", "-y", "-v", "error", "-ss", f"{local_sec:.3f}",
            "-i", str(clip), "-frames:v", "1", "-q:v", "2", str(frame),
        ])
        if proc.returncode != 0 or not frame.exists():
            continue
        ocr = ""
        if tesseract:
            ocr_proc = run([tesseract, str(frame), "stdout", "-l", "chi_sim+eng", "--psm", "6"])
            if ocr_proc.returncode == 0:
                ocr = ocr_proc.stdout.strip()[:4000]
        results.append({
            "local_sec": local_sec,
            "absolute_sec": round(decode_start + local_sec, 3),
            "sha256": sha256_file(frame),
            "ocr_text": ocr,
        })
    return results


def run_optional_smolvlm(clip: Path, temp_dir: Path, enabled: bool) -> dict:
    if not enabled:
        return {"status": "not_requested"}
    out = temp_dir / "smolvlm.json"
    proc = run([sys.executable, str(SMOLVLM_INSPECT), "--video", str(clip), "--output", str(out)])
    if proc.returncode != 0 or not out.exists():
        return {"status": "failed_optional", "stderr": proc.stderr[-3000:]}
    try:
        return json.loads(out.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "failed_optional", "error": str(exc)}


def build_markdown(evidence: dict) -> str:
    audio_asr = evidence.get("audio_asr", {})
    extraction = evidence.get("audio_extraction", {})
    match = audio_asr.get("best_match") or {}
    frames = evidence.get("visual_evidence", {}).get("frames") or []
    lines = [
        f"# Playback Evidence — {evidence['segment_id']}", "",
        f"- Case: `{evidence['case_id']}`",
        f"- Live: `{evidence['live_id']}`",
        f"- Media: {evidence['media_url']}",
        f"- Expected start: `{float(evidence['expected_start_sec']):.3f}s`",
        f"- Decode window: `{float(evidence['decode_start_sec']):.3f}s` → `{float(evidence['decode_end_sec']):.3f}s`",
        f"- Real media decoded: `{str(evidence['playback_decode_verified']).lower()}`",
        f"- Evidence status: `{evidence['status']}`",
        f"- Bundle ID: `{evidence['bundle_id']}`", "",
        "## Target text", "", evidence.get("target_text") or "(none)", "",
        "## Decoded-audio ASR match", "",
        f"- Audio extraction return code: `{extraction.get('returncode')}`",
        f"- WAV exists/bytes/duration: `{extraction.get('wav_exists')}` / `{extraction.get('wav_size_bytes')}` / `{extraction.get('duration_sec')}`",
        f"- Audio activity detected: `{(extraction.get('activity') or {}).get('non_silent')}`",
        f"- Whisper status: `{audio_asr.get('status')}`",
        f"- Whisper invoked/return code/entries: `{audio_asr.get('invoked')}` / `{audio_asr.get('process_returncode')}` / `{audio_asr.get('parsed_entry_count', len(audio_asr.get('entries') or []))}`",
        "",
    ]
    if match:
        lines.extend([
            f"- Candidate observed position: `{float(evidence['candidate_observed_position_sec']):.3f}s`",
            f"- Signed timing error: `{float(evidence['candidate_timing_error_sec']):+.3f}s`",
            f"- Match score: `{match.get('score')}`",
            f"- Similarity: `{match.get('similarity')}`",
            f"- Keyword coverage: `{match.get('keyword_coverage')}`", "",
            match.get("text") or "(empty)",
        ])
    else:
        lines.append("No usable Whisper match was produced.")
    lines.extend(["", "## Sampled frame OCR", ""])
    if not frames:
        lines.append("No video frames were extracted.")
    for frame in frames:
        lines.append(
            f"- `{frame['absolute_sec']:.3f}s` frame `{frame['sha256'][:12]}…`: "
            + (frame.get("ocr_text") or "(no OCR text)").replace("\n", " ")
        )
    visual = evidence.get("visual_evidence", {}).get("smolvlm") or {}
    if visual.get("status") == "ok":
        lines.extend(["", "## Optional SmolVLM2 visual summary", "", visual.get("summary") or "(empty)"])
    lines.extend([
        "", "## Agent decision rule", "",
        "This evidence was produced from decoded media bytes. It is **not yet a Pilot-60 qualifying record**.",
        "A worker may submit a playback acceptance only when status is `ready_for_agent_review`, after reading this evidence and confirming that the decoded-audio ASR matches the canonical target content. Visual evidence is supplemental only.",
    ])
    return "\n".join(lines) + "\n"


def _load_owned_claim(case_id: str, requested_by: str, live_id: str, segment_id: str) -> dict:
    task_id = f"P9-PLAYBACK-{case_id}"
    claim_path = CLAIMS / f"{task_id}.json"
    if not claim_path.exists():
        raise ValueError(f"active playback claim does not exist: {task_id}")
    try:
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid playback claim JSON: {exc}") from exc
    if str(claim.get("agent_id") or "") != requested_by:
        raise ValueError(
            f"playback request belongs to {requested_by}, but active claim belongs to "
            f"{claim.get('agent_id')!r}"
        )
    if str(claim.get("case_id") or "") != case_id or str(claim.get("live_id") or "") != live_id:
        raise ValueError("active playback claim case/live identity does not match request")
    if segment_id not in set(str(x) for x in (claim.get("missing_segment_ids") or [])):
        raise ValueError("segment is not part of the active playback claim's missing segment set")
    return claim


def validate_request(path: Path, request: dict) -> tuple[dict, dict, set[str]]:
    if request.get("request_version") != REQUEST_VERSION:
        raise ValueError(f"unsupported request_version: {request.get('request_version')!r}")
    required = ["case_id", "live_id", "segment_id", "media_url", "requested_by"]
    missing = [key for key in required if not request.get(key)]
    if missing:
        raise ValueError("missing request fields: " + ", ".join(missing))

    case_id = str(request["case_id"])
    live_id = str(request["live_id"])
    segment_id = str(request["segment_id"])
    requested_by = str(request["requested_by"])
    expected_task = f"P9-PLAYBACK-{case_id}"
    if request.get("task_id") and str(request.get("task_id")) != expected_task:
        raise ValueError(f"task_id must be {expected_task}")

    _load_owned_claim(case_id, requested_by, live_id, segment_id)

    case_live, case_problems = pilot_case_live_map()
    if case_problems:
        raise ValueError("ambiguous case/live map: " + "; ".join(case_problems[:5]))
    if case_live.get(case_id) != live_id:
        raise ValueError(f"case {case_id} does not map to {live_id}")

    segments, segment_problems = canonical_segment_index()
    if segment_problems:
        raise ValueError("ambiguous canonical segments: " + "; ".join(segment_problems[:5]))
    segment = segments.get(segment_id)
    if not segment:
        raise ValueError(f"unknown canonical segment: {segment_id}")
    if str(segment.get("live_id") or "") != live_id:
        raise ValueError(f"segment {segment_id} does not belong to {live_id}")
    if segment.get("start_sec") is None:
        raise ValueError(f"segment {segment_id} has no canonical start_sec")

    media_url = str(request["media_url"]).strip()
    trusted = trusted_media_urls(live_id)
    if media_url not in trusted:
        raise ValueError(
            "media_url is not present in repository provenance for this live_id; "
            "workers may not use the playback service as an arbitrary URL downloader"
        )
    return segment, {"case_id": case_id, "live_id": live_id, "segment_id": segment_id}, trusted


def process_request(path: Path, *, force: bool = False) -> Path:
    request = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(request, dict):
        raise ValueError("request top level must be an object")
    segment, ids, _ = validate_request(path, request)
    case_id, live_id, segment_id = ids["case_id"], ids["live_id"], ids["segment_id"]
    expected = float(segment["start_sec"])
    out_dir = EVIDENCE_ROOT / case_id / segment_id
    evidence_path = out_dir / "evidence.json"
    if evidence_path.exists() and not force:
        print(f"Evidence already exists: {safe_rel(evidence_path)}")
        return evidence_path

    temp_dir = CACHE_ROOT / case_id / segment_id
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    pre_roll = float(request.get("pre_roll_sec", 10.0))
    window = float(request.get("decode_window_sec", 24.0))
    media_url = str(request["media_url"])
    decode_proc = run([
        sys.executable, str(AUDIT_MEDIA), "--media", media_url,
        "--start", f"{expected:.3f}", "--pre-roll", f"{pre_roll:.3f}",
        "--window", f"{window:.3f}", "--output-dir", str(temp_dir), "--label", segment_id,
    ])
    decode_candidates = sorted(temp_dir.glob(f"{segment_id}_expected_*.json"))
    decode = {}
    if decode_candidates:
        try:
            decode = json.loads(decode_candidates[-1].read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            decode = {}
    if decode_proc.returncode != 0 or not decode.get("ok"):
        failed = {
            "project": "Miles-Guo_public_archive", "evidence_version": EVIDENCE_VERSION,
            "status": "blocked_media_decode", **ids,
            "request_ref": safe_rel(path), "requested_by": request.get("requested_by"),
            "media_url": media_url, "expected_start_sec": expected,
            "decode_start_sec": expected, "decode_end_sec": expected,
            "playback_decode_verified": False, "counts_toward_pilot_60": False,
            "stderr": (decode_proc.stderr or decode.get("stderr") or "")[-5000:],
            "generated_at": utc_now(),
        }
        failed["bundle_id"] = hashlib.sha256(
            json.dumps(failed, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        evidence_path.write_text(json.dumps(failed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out_dir / "evidence.md").write_text(build_markdown({
            **failed, "target_text": segment.get("text_curated") or segment.get("text_asr") or segment.get("text_search") or "",
            "audio_asr": {}, "visual_evidence": {"frames": []},
        }), encoding="utf-8")
        print(f"Blocked evidence written: {safe_rel(evidence_path)}")
        return evidence_path

    clip = Path(str(decode["clip_path"]))
    if not clip.is_absolute():
        clip = ROOT / clip
    audio = temp_dir / "audio_16k_mono.wav"
    audio_proc = run([
        "ffmpeg", "-y", "-v", "error", "-i", str(clip), "-vn",
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(audio),
    ])
    audio_probe = audio_probe_summary(audio) if audio.exists() else {
        "probe_returncode": None,
        "probe_stderr_tail": "audio WAV was not created",
        "has_audio_stream": False,
        "audio_streams": [],
        "duration_sec": None,
    }
    audio_activity = measure_audio_activity(audio) if (
        audio_proc.returncode == 0
        and audio.exists()
        and audio_probe.get("has_audio_stream")
    ) else {
        "returncode": None,
        "mean_volume_db": None,
        "max_volume_db": None,
        "non_silent": False,
        "stderr_tail": "audio activity was not measured because extraction/probe failed",
    }
    audio_extraction = {
        "returncode": audio_proc.returncode,
        "stderr_tail": audio_proc.stderr[-2000:],
        "wav_exists": audio.exists(),
        "wav_size_bytes": audio.stat().st_size if audio.exists() else 0,
        **audio_probe,
        "activity": audio_activity,
    }
    audio_usable = bool(
        audio_proc.returncode == 0
        and audio.exists()
        and audio.stat().st_size > 44
        and audio_probe.get("has_audio_stream")
        and isinstance(audio_probe.get("duration_sec"), (int, float))
        and float(audio_probe["duration_sec"]) > 0.1
    )
    if not audio_usable:
        failed = {
            "project": "Miles-Guo_public_archive", "evidence_version": EVIDENCE_VERSION,
            "status": "blocked_media_decode", **ids,
            "task_id": f"P9-PLAYBACK-{case_id}",
            "request_ref": safe_rel(path), "requested_by": request.get("requested_by"),
            "media_url": media_url, "expected_start_sec": expected,
            "decode_start_sec": float(decode.get("decode_start_sec", expected)),
            "decode_end_sec": float(decode.get("decode_start_sec", expected)) + float(decode.get("decode_window_sec", window)),
            "decode_window_sec": float(decode.get("decode_window_sec", window)),
            "decode_resolver": (decode.get("resolution") or {}).get("resolver"),
            "decode_failure_stage": "audio_extract",
            "playback_decode_verified": False,
            "repository_content_inspection": False,
            "audio_extraction": audio_extraction,
            "audio_asr": {
                "engine": "whisper.cpp", "status": "not_run_audio_extract_failed",
                "invoked": False, "entries": [], "best_match": None,
                "process_returncode": None,
            },
            "visual_evidence": {"frames": []},
            "agent_acceptance_required": False,
            "counts_toward_pilot_60": False,
            "generated_at": utc_now(),
        }
        failed["bundle_id"] = hashlib.sha256(
            json.dumps(failed, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        evidence_path.write_text(json.dumps(failed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out_dir / "evidence.md").write_text(build_markdown({
            **failed,
            "target_text": segment.get("text_curated") or segment.get("text_asr") or segment.get("text_search") or "",
        }), encoding="utf-8")
        print(f"Blocked audio evidence written: {safe_rel(evidence_path)}")
        return evidence_path

    whisper_cli = os.environ.get("WHISPER_CLI", "whisper-cli")
    whisper_model = os.environ.get("WHISPER_MODEL", "")
    whisper_available = (
        Path(whisper_cli).is_file() and os.access(whisper_cli, os.X_OK)
        if ("/" in whisper_cli or "\\" in whisper_cli)
        else bool(shutil.which(whisper_cli))
    )
    whisper_prefix = temp_dir / "whisper"
    whisper_proc = None
    srt_path = Path(str(whisper_prefix) + ".srt")
    if audio_proc.returncode == 0 and whisper_available and whisper_model:
        whisper_proc = run([
            whisper_cli, "-m", whisper_model, "-f", str(audio),
            "-l", str(request.get("language", "zh")), "-osrt", "-of", str(whisper_prefix),
            "--no-prints",
        ])
    entries = parse_srt(srt_path)
    if whisper_proc is None:
        whisper_status = "not_run_runtime_unavailable"
    elif whisper_proc.returncode != 0:
        whisper_status = "failed"
    elif not srt_path.exists():
        whisper_status = "completed_without_srt"
    elif not entries:
        whisper_status = "completed_no_entries"
    else:
        whisper_status = "completed"
    target_text = str(segment.get("text_curated") or segment.get("text_asr") or segment.get("text_search") or "")
    match = best_asr_match(entries, target_text, segment.get("text_search"))
    decode_start = float(decode.get("decode_start_sec", expected))
    decode_window = float(decode.get("decode_window_sec", window))
    decode_end = decode_start + decode_window

    frames = collect_frame_evidence(clip, temp_dir, decode_start, expected, decode_window)
    visual_match = best_ocr_match(frames, target_text, segment.get("text_search"))
    smolvlm = run_optional_smolvlm(
        clip, temp_dir,
        bool(request.get("visual_mode") == "smolvlm2_optional" and os.environ.get("ENABLE_SMOLVLM") == "1"),
    )
    # Keep visual evidence independent: a stronger OCR score must neither promote a
    # visual-only result nor suppress an otherwise qualifying decoded-audio match.
    candidate_method = "audio_asr" if match else None
    candidate = match
    candidate_score = float((candidate or {}).get("score", 0.0))
    if candidate_method == "audio_asr":
        observed = round(decode_start + float(candidate["local_start_sec"]), 3)
    else:
        observed = None
    timing_error = round(observed - expected, 3) if observed is not None else None
    # Audio is the primary ordinary-Agent evidence path for this speech archive. OCR/visual
    # evidence remains useful context, but must never qualify a segment by itself.
    candidate_match = bool(
        candidate
        and candidate_method == "audio_asr"
        and candidate_score >= MIN_AGENT_REVIEW_SCORE
    )
    status = "ready_for_agent_review" if candidate_match else "needs_manual_or_wider_review"

    audio_rows = [{
        "local_start_sec": entry["start_sec"], "local_end_sec": entry["end_sec"],
        "absolute_start_sec": round(decode_start + entry["start_sec"], 3),
        "absolute_end_sec": round(decode_start + entry["end_sec"], 3), "text": entry["text"],
    } for entry in entries]

    core = {
        "project": "Miles-Guo_public_archive", "evidence_version": EVIDENCE_VERSION,
        "status": status, **ids, "task_id": f"P9-PLAYBACK-{case_id}",
        "request_ref": safe_rel(path), "requested_by": request.get("requested_by"),
        "media_url": media_url, "target_text": target_text,
        "target_text_search": segment.get("text_search"), "expected_start_sec": expected,
        "decode_request_start_sec": float(decode.get("expected_start_sec", expected)),
        "decode_start_sec": decode_start, "decode_end_sec": decode_end,
        "decode_window_sec": decode_window, "decode_resolver": (decode.get("resolution") or {}).get("resolver"),
        "playback_decode_verified": True, "repository_content_inspection": True,
        "inspection_engine": "github-actions+ffmpeg+whisper.cpp+frame-ocr",
        "audio_asr": {
            "engine": "whisper.cpp", "model": os.path.basename(whisper_model) if whisper_model else None,
            "status": whisper_status,
            "cli_available": whisper_available,
            "model_available": bool(whisper_model and Path(whisper_model).is_file()),
            "invoked": whisper_proc is not None,
            "entries": audio_rows, "best_match": match,
            "process_returncode": None if whisper_proc is None else whisper_proc.returncode,
            "stderr_tail": "" if whisper_proc is None else whisper_proc.stderr[-2000:],
            "output_srt_exists": srt_path.exists(),
            "parsed_entry_count": len(entries),
        },
        "audio_extraction": audio_extraction,
        "visual_evidence": {"frames": frames, "best_match": visual_match, "smolvlm": smolvlm},
        "candidate_match_method": candidate_method,
        "candidate_match_score": round(candidate_score, 6),
        "candidate_content_match": candidate_match,
        "candidate_observed_position_sec": observed,
        "candidate_timing_error_sec": timing_error,
        "candidate_absolute_timing_error_sec": None if timing_error is None else abs(timing_error),
        "minimum_agent_review_score": MIN_AGENT_REVIEW_SCORE,
        "agent_acceptance_required": True, "counts_toward_pilot_60": False,
        "decode_evidence_sha256": sha256_file(decode_candidates[-1]) if decode_candidates else None,
        "temporary_clip_sha256": sha256_file(clip) if clip.exists() else None,
        "generated_at": utc_now(),
    }
    bundle_seed = {key: core[key] for key in (
        "case_id", "live_id", "segment_id", "media_url", "expected_start_sec",
        "decode_start_sec", "decode_window_sec", "candidate_observed_position_sec",
        "candidate_timing_error_sec", "decode_evidence_sha256", "temporary_clip_sha256"
    )}
    core["bundle_id"] = hashlib.sha256(
        json.dumps(bundle_seed, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    evidence_path.write_text(json.dumps(core, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "evidence.md").write_text(build_markdown(core), encoding="utf-8")
    print(f"Playback evidence written: {safe_rel(evidence_path)}")
    print(f"status={status} method={candidate_method} score={candidate_score:.6f} observed={observed}")
    return evidence_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Turn authorized playback requests into durable Agent-readable decoded-media evidence.")
    parser.add_argument("--request")
    parser.add_argument("--pending", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not args.request and not args.pending:
        parser.error("use --request PATH or --pending")
    paths: list[Path] = []
    if args.request:
        path = Path(args.request)
        if not path.is_absolute():
            path = ROOT / path
        paths.append(path)
    if args.pending:
        paths.extend(sorted(REQUEST_ROOT.rglob("*.json")) if REQUEST_ROOT.exists() else [])
    seen: set[Path] = set()
    failures = 0
    for path in paths:
        path = path.resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            process_request(path, force=args.force)
        except Exception as exc:
            failures += 1
            print(f"ERROR {path}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

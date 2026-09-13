#!/usr/bin/env python3
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RESOLVE_TIMEOUT_SEC = 45
PROBE_TIMEOUT_SEC = 60
DECODE_TIMEOUT_SEC = 180
FRAME_TIMEOUT_SEC = 60
TIMEOUT_RETURN_CODE = 124
GETTR_STREAM_RE = re.compile(r"^https?://(?:www\.)?gettr\.com/streaming/([a-z0-9]+)(?:[/?#].*)?$", re.I)
ODYSEE_RE = re.compile(r"^https?://(?:www\.)?odysee\.com/(.+)$", re.I)
ODYSEE_PROXY_URL = "https://api.na-backend.odysee.com/api/v1/proxy?m=get"
TRUSTED_ARCHIVE_PAGE_RE = re.compile(
    r"^https?://(?:(?:www\.)?ghot\.ai/archive/videos/|(?:www\.)?gwins\.org/cn/milesguo/)", re.I
)
PUBLIC_MEDIA_URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
SUPPORTED_PUBLIC_MEDIA_HOST_RE = re.compile(
    r"^https?://(?:www\.)?(?:gettr\.com/(?:streaming|post)/|rumble\.com/|odysee\.com/|youtube\.com/|youtu\.be/)", re.I
)


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def run(cmd, *, timeout_sec):
    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
        )
        return process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = _as_text(exc.stdout)
        stderr = _as_text(exc.stderr)
        timeout_note = f"command timed out after {timeout_sec}s: {' '.join(map(str, cmd[:3]))}"
        if stderr:
            stderr = stderr.rstrip() + "\n" + timeout_note
        else:
            stderr = timeout_note
        return TIMEOUT_RETURN_CODE, stdout, stderr


def resolve_gettr_streaming_public(source):
    match = GETTR_STREAM_RE.match(source)
    if not match:
        return None, None
    stream_id = match.group(1)
    api_url = f"https://api.gettr.com/u/live/join/{stream_id}"
    request = urllib.request.Request(
        api_url,
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Miles-Guo-public-archive-playback/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=RESOLVE_TIMEOUT_SEC) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result = payload.get("result") if isinstance(payload, dict) else None
        broadcast = result.get("broadcast") if isinstance(result, dict) else None
        media_url = broadcast.get("url") if isinstance(broadcast, dict) else None
        if not isinstance(media_url, str) or not media_url.startswith(("http://", "https://")):
            raise ValueError("GETTR public join API returned no usable broadcast.url")
        return media_url, {
            "resolver": "gettr_public_join_api",
            "source": source,
            "gettr_stream_id": stream_id,
            "api_url": api_url,
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return None, {
            "resolver": "gettr_public_join_api_failed",
            "source": source,
            "gettr_stream_id": stream_id,
            "api_url": api_url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _odysee_lbry_uri(source):
    match = ODYSEE_RE.match(source)
    if not match:
        return None
    parsed = urllib.parse.urlparse(source)
    path = urllib.parse.unquote(parsed.path.lstrip("/"))
    if not path or "/" not in path:
        return None
    return f"lbry://{path}"


def resolve_odysee_public(source):
    """Resolve a public Odysee claim through Odysee's anonymous SDK proxy.

    This uses the same relaxed `get` method used by Odysee clients. It sends no wallet,
    credentials, cookies, or auth token and only accepts an HTTP(S) streaming_url.
    """
    lbry_uri = _odysee_lbry_uri(source)
    if not lbry_uri:
        return None, None
    body = json.dumps({
        "jsonrpc": "2.0",
        "method": "get",
        "params": {"uri": lbry_uri, "save_file": False},
        "id": 1,
    }).encode("utf-8")
    request = urllib.request.Request(
        ODYSEE_PROXY_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Miles-Guo-public-archive-playback/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=RESOLVE_TIMEOUT_SEC) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Odysee public SDK proxy returned a non-object payload")
        if payload.get("error"):
            raise ValueError(f"Odysee public SDK proxy error: {payload.get('error')}")
        result = payload.get("result")
        media_url = result.get("streaming_url") if isinstance(result, dict) else None
        if not isinstance(media_url, str) or not media_url.startswith(("http://", "https://")):
            raise ValueError("Odysee public SDK proxy returned no usable result.streaming_url")
        return media_url, {
            "resolver": "odysee_public_sdk_proxy",
            "source": source,
            "lbry_uri": lbry_uri,
            "api_url": ODYSEE_PROXY_URL,
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return None, {
            "resolver": "odysee_public_sdk_proxy_failed",
            "source": source,
            "lbry_uri": lbry_uri,
            "api_url": ODYSEE_PROXY_URL,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _media_priority(url):
    lower = url.lower()
    if "gettr.com/streaming/" in lower:
        return 0
    if "odysee.com" in lower:
        return 1
    if "rumble.com" in lower:
        return 2
    if "youtube.com" in lower or "youtu.be" in lower:
        return 3
    if "gettr.com/post/" in lower:
        return 4
    return 9


def resolve_trusted_archive_page_public(source):
    if not TRUSTED_ARCHIVE_PAGE_RE.match(source):
        return None, None
    request = urllib.request.Request(
        source,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "Miles-Guo-public-archive-playback/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=RESOLVE_TIMEOUT_SEC) as response:
            raw = response.read(2_000_000)
        page = html.unescape(raw.decode("utf-8", errors="replace"))
        candidates = []
        seen = set()
        for candidate in PUBLIC_MEDIA_URL_RE.findall(page):
            candidate = candidate.rstrip(".,);]}\\")
            if not SUPPORTED_PUBLIC_MEDIA_HOST_RE.match(candidate) or candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(candidate)
        candidates.sort(key=lambda value: (_media_priority(value), value))
        if not candidates:
            raise ValueError("trusted archive page exposed no supported public media URL")
        linked = candidates[0]
        resolved, linked_resolution = resolve_media(linked, allow_archive=False)
        resolution = dict(linked_resolution or {})
        resolution.update({
            "archive_resolver": "trusted_archive_page_public_links",
            "archive_page": source,
            "linked_media_url": linked,
            "archive_candidates": candidates,
        })
        return resolved, resolution
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
        return None, {
            "resolver": "trusted_archive_page_public_links_failed",
            "source": source,
            "error": f"{type(exc).__name__}: {exc}",
        }


def resolve_media(source, *, allow_archive=True):
    archive_resolution = None
    if allow_archive:
        archive_url, archive_resolution = resolve_trusted_archive_page_public(source)
        if archive_url:
            return archive_url, archive_resolution
        if archive_resolution:
            print(
                f"Trusted archive resolver failed for {source}: {archive_resolution.get('error', 'unknown error')}",
                file=sys.stderr,
            )

    if source.startswith(("http://", "https://")) and shutil.which("yt-dlp"):
        rc, out, err = run(["yt-dlp", "-g", "--no-playlist", source], timeout_sec=RESOLVE_TIMEOUT_SEC)
        if rc == 0 and out.strip():
            resolution = {"resolver": "yt-dlp", "source": source, "yt_dlp_returncode": rc}
            if archive_resolution:
                resolution["archive_resolution"] = archive_resolution
            return out.strip().splitlines()[0], resolution
        diag = (err or "")[-4000:]
        print(f"yt-dlp resolver failed for {source} with rc={rc}:\n{diag}", file=sys.stderr)

        gettr_url, gettr_resolution = resolve_gettr_streaming_public(source)
        if gettr_url:
            gettr_resolution["yt_dlp_returncode"] = rc
            gettr_resolution["yt_dlp_stderr"] = diag
            return gettr_url, gettr_resolution
        if gettr_resolution:
            print(
                f"GETTR public resolver failed for {source}: {gettr_resolution.get('error', 'unknown error')}",
                file=sys.stderr,
            )
            return source, {
                **gettr_resolution,
                "yt_dlp_returncode": rc,
                "yt_dlp_stderr": diag,
                "resolver_timeout_sec": RESOLVE_TIMEOUT_SEC,
            }

        odysee_url, odysee_resolution = resolve_odysee_public(source)
        if odysee_url:
            odysee_resolution["yt_dlp_returncode"] = rc
            odysee_resolution["yt_dlp_stderr"] = diag
            return odysee_url, odysee_resolution
        if odysee_resolution:
            print(
                f"Odysee public resolver failed for {source}: {odysee_resolution.get('error', 'unknown error')}",
                file=sys.stderr,
            )
            result = {
                **odysee_resolution,
                "yt_dlp_returncode": rc,
                "yt_dlp_stderr": diag,
                "resolver_timeout_sec": RESOLVE_TIMEOUT_SEC,
            }
            if archive_resolution:
                result["archive_resolution"] = archive_resolution
            return source, result

        result = {
            "resolver": "direct_after_yt_dlp_failure",
            "source": source,
            "yt_dlp_returncode": rc,
            "yt_dlp_stderr": diag,
            "resolver_timeout_sec": RESOLVE_TIMEOUT_SEC,
        }
        if archive_resolution:
            result["archive_resolution"] = archive_resolution
        return source, result
    return source, {"resolver": "direct", "source": source}


def _probe(path_or_url):
    rc, out, err = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json", str(path_or_url),
    ], timeout_sec=PROBE_TIMEOUT_SEC)
    payload = None
    if rc == 0:
        try:
            payload = json.loads(out or "{}")
        except json.JSONDecodeError:
            rc = 1
            err = (err.rstrip() + "\n" if err else "") + "ffprobe returned invalid JSON"
    return rc, payload or {}, err


def _decoded_clip_is_usable(probe):
    streams = probe.get("streams") if isinstance(probe, dict) else None
    if not isinstance(streams, list):
        return False, "decoded clip has no stream list"
    media_streams = [s for s in streams if isinstance(s, dict) and s.get("codec_type") in {"audio", "video"}]
    if not media_streams:
        return False, "decoded clip contains no audio/video stream"
    try:
        duration = float((probe.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        return False, "decoded clip has no numeric duration"
    if duration <= 0.1:
        return False, f"decoded clip duration is too short: {duration}"
    return True, ""


def main():
    parser = argparse.ArgumentParser(description="Decode real media around an expected audit timestamp.")
    parser.add_argument("--media", required=True)
    parser.add_argument("--start", required=True, type=float)
    parser.add_argument("--pre-roll", type=float, default=10.0)
    parser.add_argument("--window", type=float, default=24.0)
    parser.add_argument("--output-dir", default="cache/audit_media")
    parser.add_argument("--label", default="audit")
    args = parser.parse_args()
    if args.start < 0 or args.pre_roll < 0 or args.window <= 0:
        parser.error("--start and --pre-roll must be >= 0 and --window must be > 0")
    decode_start = max(0.0, args.start - args.pre_roll)
    actual_pre_roll = args.start - decode_start
    decode_end = decode_start + args.window
    if decode_end < args.start + 8.0:
        parser.error("decoded window must extend at least 8 seconds after the expected start")
    for tool in ("ffprobe", "ffmpeg"):
        if not shutil.which(tool):
            print(json.dumps({"ok": False, "error": f"{tool} not found"}))
            return 2
    resolved, resolution = resolve_media(args.media)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = "".join(c if c.isalnum() or c in "-_." else "_" for c in args.label)
    clip_path = output_dir / f"{safe_label}_expected_{args.start:.3f}_from_{decode_start:.3f}_window_{args.window:.3f}.mp4"
    frame_path = output_dir / f"{safe_label}_expected_{args.start:.3f}.jpg"
    evidence_path = output_dir / f"{safe_label}_expected_{args.start:.3f}.json"
    probe_rc, probe, probe_err = _probe(resolved)
    if probe_rc != 0:
        payload = {"ok": False, "stage": "probe", "resolution": resolution, "media_source": args.media, "expected_start_sec": args.start, "decode_start_sec": decode_start, "decode_window_sec": args.window, "stderr": probe_err[-4000:], "timed_out": probe_rc == TIMEOUT_RETURN_CODE, "timeout_sec": PROBE_TIMEOUT_SEC if probe_rc == TIMEOUT_RETURN_CODE else None}
        evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 3
    decode_rc, _, decode_err = run(["ffmpeg", "-y", "-v", "error", "-ss", f"{decode_start:.3f}", "-i", resolved, "-t", f"{args.window:.3f}", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(clip_path)], timeout_sec=DECODE_TIMEOUT_SEC)
    if decode_rc != 0:
        payload = {"ok": False, "stage": "decode", "resolution": resolution, "media_source": args.media, "expected_start_sec": args.start, "decode_start_sec": decode_start, "decode_window_sec": args.window, "probe": probe, "stderr": decode_err[-4000:], "timed_out": decode_rc == TIMEOUT_RETURN_CODE, "timeout_sec": DECODE_TIMEOUT_SEC if decode_rc == TIMEOUT_RETURN_CODE else None}
        evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 4
    clip_probe_rc, clip_probe, clip_probe_err = _probe(clip_path)
    clip_ok, clip_problem = _decoded_clip_is_usable(clip_probe)
    if clip_probe_rc != 0 or not clip_ok:
        diagnostic = clip_probe_err[-4000:] if clip_probe_rc != 0 else clip_problem
        payload = {"ok": False, "stage": "verify_decoded_clip", "resolution": resolution, "media_source": args.media, "expected_start_sec": args.start, "decode_start_sec": decode_start, "decode_window_sec": args.window, "probe": probe, "decoded_clip_probe": clip_probe, "stderr": diagnostic, "timed_out": clip_probe_rc == TIMEOUT_RETURN_CODE, "timeout_sec": PROBE_TIMEOUT_SEC if clip_probe_rc == TIMEOUT_RETURN_CODE else None}
        evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 5
    frame_rc, _, _ = run(["ffmpeg", "-y", "-v", "error", "-ss", f"{args.start:.3f}", "-i", resolved, "-frames:v", "1", str(frame_path)], timeout_sec=FRAME_TIMEOUT_SEC)
    payload = {"ok": True, "media_source": args.media, "resolution": resolution, "expected_start_sec": args.start, "requested_start_sec": args.start, "decode_start_sec": decode_start, "decode_end_sec": decode_end, "pre_roll_sec": actual_pre_roll, "decode_window_sec": args.window, "probe": probe, "decoded_clip_probe": clip_probe, "clip_path": str(clip_path), "frame_path": str(frame_path) if frame_rc == 0 else None, "playback_decode_verified": True, "content_timing_verified": False, "note": "Real media decoded into a locally re-probed audio/video clip; reviewer must locate actual target content and record signed timing error before qualification."}
    evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

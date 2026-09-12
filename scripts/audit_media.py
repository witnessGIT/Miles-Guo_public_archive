#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def run(cmd):
    process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process.returncode, process.stdout, process.stderr


def resolve_media(source):
    if source.startswith(("http://", "https://")) and shutil.which("yt-dlp"):
        rc, out, _ = run(["yt-dlp", "-g", "--no-playlist", source])
        if rc == 0 and out.strip():
            return out.strip().splitlines()[0], {
                "resolver": "yt-dlp",
                "source": source,
            }
    return source, {"resolver": "direct", "source": source}


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Decode real media around an audit timestamp and emit reproducible "
            "playback evidence into cache/."
        )
    )
    parser.add_argument("--media", required=True, help="Public media URL or local media path")
    parser.add_argument("--start", required=True, type=float, help="Expected start position in seconds")
    parser.add_argument("--window", type=float, default=12.0, help="Seconds to decode around the target")
    parser.add_argument("--output-dir", default="cache/audit_media")
    parser.add_argument("--label", default="audit")
    args = parser.parse_args()

    if args.start < 0 or args.window <= 0:
        parser.error("--start must be >= 0 and --window must be > 0")

    for tool in ("ffprobe", "ffmpeg"):
        if not shutil.which(tool):
            print(json.dumps({"ok": False, "error": f"{tool} not found"}))
            return 2

    resolved, resolution = resolve_media(args.media)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_label = "".join(
        c if c.isalnum() or c in "-_." else "_" for c in args.label
    )
    clip_path = output_dir / f"{safe_label}_{args.start:.3f}_{args.window:.3f}.mp4"
    frame_path = output_dir / f"{safe_label}_{args.start:.3f}.jpg"
    evidence_path = output_dir / f"{safe_label}_{args.start:.3f}.json"

    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
        "-of",
        "json",
        resolved,
    ]
    probe_rc, probe_out, probe_err = run(probe_cmd)
    if probe_rc != 0:
        payload = {
            "ok": False,
            "stage": "probe",
            "resolution": resolution,
            "stderr": probe_err[-4000:],
        }
        evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 3

    probe = json.loads(probe_out or "{}")

    decode_cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-ss",
        f"{args.start:.3f}",
        "-i",
        resolved,
        "-t",
        f"{args.window:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-c:a",
        "aac",
        str(clip_path),
    ]
    decode_rc, _, decode_err = run(decode_cmd)
    if decode_rc != 0:
        payload = {
            "ok": False,
            "stage": "decode",
            "resolution": resolution,
            "probe": probe,
            "stderr": decode_err[-4000:],
        }
        evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 4

    frame_cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-ss",
        f"{args.start:.3f}",
        "-i",
        resolved,
        "-frames:v",
        "1",
        str(frame_path),
    ]
    frame_rc, _, _ = run(frame_cmd)

    payload = {
        "ok": True,
        "media_source": args.media,
        "resolution": resolution,
        "requested_start_sec": args.start,
        "decode_window_sec": args.window,
        "probe": probe,
        "clip_path": str(clip_path),
        "frame_path": str(frame_path) if frame_rc == 0 else None,
        "playback_decode_verified": True,
        "content_timing_verified": False,
        "note": (
            "Media bytes were actually decoded around the requested timestamp. "
            "A reviewer must inspect the generated clip/frame and record the observed "
            "content position and timing error before counting this as a qualifying "
            "Pilot playback audit."
        ),
    }
    evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
        rc, out, err = run(["yt-dlp", "-g", "--no-playlist", source])
        if rc == 0 and out.strip():
            return out.strip().splitlines()[0], {
                "resolver": "yt-dlp",
                "source": source,
                "yt_dlp_returncode": rc,
            }
        return source, {
            "resolver": "direct_after_yt_dlp_failure",
            "source": source,
            "yt_dlp_returncode": rc,
            "yt_dlp_stderr": (err or "")[-4000:],
        }
    return source, {"resolver": "direct", "source": source}


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
    probe_rc, probe_out, probe_err = run(["ffprobe","-v","error","-show_entries","format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate","-of","json",resolved])
    if probe_rc != 0:
        payload = {"ok":False,"stage":"probe","resolution":resolution,"media_source":args.media,"expected_start_sec":args.start,"decode_start_sec":decode_start,"decode_window_sec":args.window,"stderr":probe_err[-4000:]}
        evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2)); return 3
    probe = json.loads(probe_out or "{}")
    decode_rc, _, decode_err = run(["ffmpeg","-y","-v","error","-ss",f"{decode_start:.3f}","-i",resolved,"-t",f"{args.window:.3f}","-c:v","libx264","-preset","ultrafast","-c:a","aac",str(clip_path)])
    if decode_rc != 0:
        payload = {"ok":False,"stage":"decode","resolution":resolution,"media_source":args.media,"expected_start_sec":args.start,"decode_start_sec":decode_start,"decode_window_sec":args.window,"probe":probe,"stderr":decode_err[-4000:]}
        evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2)); return 4
    frame_rc, _, _ = run(["ffmpeg","-y","-v","error","-ss",f"{args.start:.3f}","-i",resolved,"-frames:v","1",str(frame_path)])
    payload = {"ok":True,"media_source":args.media,"resolution":resolution,"expected_start_sec":args.start,"requested_start_sec":args.start,"decode_start_sec":decode_start,"decode_end_sec":decode_end,"pre_roll_sec":actual_pre_roll,"decode_window_sec":args.window,"probe":probe,"clip_path":str(clip_path),"frame_path":str(frame_path) if frame_rc == 0 else None,"playback_decode_verified":True,"content_timing_verified":False,"note":"Real media decoded; reviewer must locate actual target content and record signed timing error before qualification."}
    evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Optional CPU SmolVLM2 visual summary for a short decoded playback clip."
    )
    parser.add_argument("--video", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--model",
        default="HuggingFaceTB/SmolVLM2-256M-Video-Instruct",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        processor = AutoProcessor.from_pretrained(args.model)
        model = AutoModelForImageTextToText.from_pretrained(
            args.model,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        ).to("cpu")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "video", "path": str(Path(args.video).resolve())},
                    {
                        "type": "text",
                        "text": (
                            "Describe only directly visible evidence in this short video. "
                            "Mention whether a person is speaking, scene cuts, black/static "
                            "frames, and readable on-screen text. Do not infer identities or "
                            "facts that are not visually evident."
                        ),
                    },
                ],
            }
        ]
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to("cpu")
        generated = model.generate(**inputs, do_sample=False, max_new_tokens=96)
        text = processor.batch_decode(generated, skip_special_tokens=True)[0]
        payload = {
            "status": "ok",
            "engine": "SmolVLM2-256M-Video-Instruct",
            "model": args.model,
            "summary": text,
            "generated_at": utc_now(),
        }
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0
    except Exception as exc:
        payload = {
            "status": "failed_optional",
            "engine": "SmolVLM2-256M-Video-Instruct",
            "model": args.model,
            "error": f"{type(exc).__name__}: {exc}",
            "generated_at": utc_now(),
        }
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

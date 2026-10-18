#!/usr/bin/env python3
"""Run one key-point extraction in an isolated MLX process.

Metal failures can poison a process-wide command queue. A fresh process per
livestream prevents one GPU error from turning every later item into a false
batch failure.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

try:
    from cloud_keypoint_item import process_live
except ModuleNotFoundError:  # Imported as scripts.cloud_keypoint_runner in tests.
    from scripts.cloud_keypoint_item import process_live


def write_result(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--live-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()

    from mlx_lm import generate, load
    model, tokenizer = load(args.model)

    def generate_text(prompt: str) -> str:
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=False,
            add_generation_prompt=True,
        )
        return generate(model, tokenizer, prompt=rendered, max_tokens=768, verbose=False)

    outputs, stats = process_live(args.repo.resolve(), args.live_id, generate_text)
    write_result(args.result.resolve(), {"outputs": outputs, "stats": stats})
    print(json.dumps({"live_id": args.live_id, **stats}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

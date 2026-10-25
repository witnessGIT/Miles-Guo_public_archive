#!/usr/bin/env python3
"""Run one entity-enrichment item in an isolated, timeout-safe process."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cloud_entity_item import process_live


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
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )
        return generate(model, tokenizer, prompt=rendered, max_tokens=320, verbose=False)

    outputs, stats = process_live(args.repo.resolve(), args.live_id, generate_text)
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(
        json.dumps({"outputs": outputs, "stats": stats}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

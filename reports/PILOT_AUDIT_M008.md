# Miles-Guo_public_archive Pilot Audit — PILOT-M008

Project: `Miles-Guo_public_archive`  
Phase: `PILOT`  
Task: `S-AUDIT-PILOT-M008`  
Case: `PILOT-M008`  
Live ID: `LIVE_20211029_001`  
Verifier: `agent-20260913T002400Z-gpt56sol`  
Verified at: `2026-09-12T17:02:00Z`

## Segments under audit

The case has three conservative GHOT anchors in `data/live_segments/alignment/LIVE_20211029_001.jsonl`:

1. `LIVE_20211029_001_SEG_000000` — `1433.0` sec (`23:53`) — `我从加拿大突然之间穿越到这个我们今天文贵先生的身边。`
2. `LIVE_20211029_001_SEG_000001` — `1771.0` sec (`29:31`) — passage beginning `可以啊你先开始...`
3. `LIVE_20211029_001_SEG_000002` — `2442.0` sec (`40:42`) — passage beginning `它曾经一度迷茫，最后这是阿伯扎比...国家主权基金...`

All use `SRC_1B5F3EA1`, `ghot_public_timeline_direct_asr_only`, have no asserted `end_sec`, and have `playback_verified = 0`. The source is documented as containing noisy/garbled ASR sections.

## Public-source checks

### GHOT

`https://ghot.ai/archive/videos/2021-10-29-1`

The public GHOT timestamped transcript exactly exposes the three selected anchors at `23:53`, `29:31`, and `40:42`, equal to `1433`, `1771`, and `2442` seconds. The same public record visibly contains severe noisy/garbled transcript material in other portions, so this audit does not generalize the three clear anchors into a global ASR-quality pass.

### GWINS

`https://gwins.org/cn/milesguo/23425.html`

GWINS identifies the same item as `郭文贵2021年10月29日直播 20211029_1`, published `20211029`, and links the same Odysee item `@laxi:4/20211029_1:5` and Rumble item `v59s5mh-20211029-1.html`. This independently supports case identity and cross-source provenance.

### Odysee / Rumble

The Odysee item resolves but exposes no observable playback position in the current audit environment. The linked Rumble page returns HTTP `403 Forbidden`.

## Audit result

- Correct livestream/date identity: **supported**
- Selected GHOT timestamp/text anchors: **exactly corroborated**
- Cross-source GHOT/GWINS/Odysee/Rumble identity chain: **supported**
- Global ASR reliability: **NOT established; noisy sections confirmed**
- Actual media playback performed: **NO**
- Observed playback position / timing error: **not measured**
- `playback_verified`: **0**
- Counts toward Pilot-60 real playback checks: **NO**

## Disposition

Keep the three rows as `timestamped_asr_only_unverified_playback`. Preserve the noisy-ASR caveat and do not infer `end_sec`, FPS/frame values, or playback timing accuracy from transcript timestamps alone.

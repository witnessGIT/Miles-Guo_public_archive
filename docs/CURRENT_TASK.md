# Current task: cloud ASR pilot for the full searchable archive

Phase 1 source discovery, candidate identity review and the first metadata pass are complete and
frozen. Under the owner's 2026-10-12 authorization, the current scope is
`PHASE_3_CLOUD_ASR_PILOT`: create a searchable machine transcript and timestamp index for every
canonical livestream with accessible public media without consuming the owner's local compute.

Current work is a streaming pipeline. `WI_<LIVE_ID>_transcript_import` continues across the corpus,
while a livestream with a completed transcript may immediately advance through `cue_split`,
`segment_split`, and machine-status enrichment. It is not necessary to wait for corpus-wide ASR.

For one claimed canonical livestream:

- use an already archived public media locator and keep media/audio/model files outside Git;
- run open-source MLX Whisper on an ephemeral GitHub-hosted Apple runner without a paid ASR API;
- preserve one `asr_raw` transcript version and timestamped transcript cues;
- create matching machine-status searchable segments for SQLite FTS;
- preserve source URL, media asset ID, ephemeral processing path, checksum, model and processing result;
- mark failures and inaccessible media truthfully without inventing transcript text.

Raw ASR is not human correction and is not Playback verification. Do not promote its verification
level beyond `machine`/`asr`. After `transcript_import`, later dependency stages separately create
natural passages, key points/topics, entities, events, claims, relations, text checks and hybrid
semantic retrieval indexes.

The first cloud run is deliberately limited to 10 livestreams. Failed cloud access remains
retryable and must not be mislabeled as missing media. Expand only after the pilot's duration,
source reachability, resource use and durable publication are verified.

Work-mode entry:

```bash
git pull --ff-only
python scripts/agent_entry.py --mode auto
```

Before completion:

```bash
python scripts/build_db.py
python scripts/validate_db.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

# Current task: full-corpus local ASR archive

Phase 1 source discovery, candidate identity review and the first metadata pass are complete and
frozen. Under the owner's 2026-10-12 authorization, the current scope is
`PHASE_3_LOCAL_ASR_ARCHIVING`: create a searchable machine transcript and timestamp index for
every canonical livestream with accessible public media.

Current executable work is limited to `WI_<LIVE_ID>_transcript_import`.

For one claimed canonical livestream:

- use an already archived public media locator and keep media/audio/model files outside Git;
- run offline local ASR without a paid API or hosted inference;
- preserve one `asr_raw` transcript version and timestamped transcript cues;
- create matching machine-status searchable segments for SQLite FTS;
- preserve source URL, media asset ID, local audio path, checksum, model and processing result;
- mark failures and inaccessible media truthfully without inventing transcript text.

Raw ASR is not human correction and is not Playback verification. Do not promote its verification
level beyond `machine`/`asr`. Do not execute entity/event/claim extraction, relationship analysis,
text verification or Playback Audit as part of this task.

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

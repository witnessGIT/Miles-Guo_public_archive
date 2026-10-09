# Current task: first-pass livestream archive

Phase 1 source discovery and candidate identity review are complete and frozen. The current scope
is `PHASE_2_INITIAL_ARCHIVING`: establish a usable first archive record for every canonical
livestream.

Current executable work is limited to `WI_<LIVE_ID>_metadata_fill`.

For one claimed canonical livestream, verify and preserve as much public evidence as is actually
available:

- canonical title, livestream date and publication time;
- source page identity and URL;
- platform name, public video/post ID and media URL;
- duration, dimensions, FPS and audio presence when public metadata proves them;
- availability and the exact time/method used to check it;
- conflicts and unknown fields without guessing.

Do not download full media merely to fill metadata. Do not claim Playback verification from page
metadata or extractor metadata. In this first-pass archive phase, do not execute transcription,
cue/segment splitting, entity/event/claim extraction, relationship analysis, text verification or
Playback Audit. Those work items remain durable future backlog.

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

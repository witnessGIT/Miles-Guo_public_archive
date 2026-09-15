# Current Task — Two-Phase Restart

Current phase: **PHASE_1_COLLECTION**. Refresh `main`, then run `python scripts/agent_entry.py --mode direct`.

Phase 1 collects source URL, stable ID, title, date, media link, retrieval time and uncertainty only. No ASR, content matching, Playback acceptance or archive publication.

Phase 2 stays locked until `C5-COLLECTION-FREEZE`. It splits batches of at most 25 records into provenance, identity, segment, audio/ASR, content-match and archive-publication tasks. See `docs/TWO_PHASE_ARCHIVE_WORKFLOW.md`.

Earlier organised content is preserved on `archive/two-phase-reset-2026-09-16` and is not input to this run.

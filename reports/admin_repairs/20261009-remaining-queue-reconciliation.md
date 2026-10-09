# Miles-Guo_public_archive — remaining admin queue reconciliation

Recorded: 2026-10-09T14:30:00Z.

Authenticated administrator: `witnessGIT`.

The five reports that remained marked open after their underlying data repairs were audited against fresh `main`. Two still required a shared-service repair; three had already been corrected but lacked durable resolution metadata.

## Service repairs

- Commit `de323d11` makes exact numeric GWINS detail requests harmless to the list-page Source Page Evidence Service. Both processing and finalization now return a successful explicit skip, while unsafe hosts, malformed identifiers, and detail-ID/URL mismatches still fail closed.
- The same commit gives all C2 claims one effective ten-hour lease based on task identity or kind. Optional legacy fields can no longer extend or shorten C2 ownership; non-C2 static leases preserve their existing behavior.

## Reconciled historical repairs

- The July 11 shared YouTube locator collision was removed by `f478b260` and its related key-disambiguation work. Current data contains only one copy of the original source/media identifier.
- The four invalid candidate-review timestamps were corrected in `8a2fc387`; current timestamps parse as valid UTC values and the validator remains strict.

## Verification

- 34 focused source-service and task-scheduler tests passed.
- Both historical numeric detail requests (`24221`, `24253`) returned successful skip results in processing and finalization.
- `validate_candidate_reviews.py`: PASS, 2605 checked completions, 51 batches, zero lease warnings.
- `build_db.py`: PASS.
- `validate_db.py`: OK, zero warnings.

No candidate, source identity, playback evidence, or completion decision was fabricated during this reconciliation.

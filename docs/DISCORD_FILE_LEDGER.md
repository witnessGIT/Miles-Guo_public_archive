# Discord File Ledger

This ledger records per-file decisions for attachments discovered in Discord server `821933739307040799`. Binary documents and media remain outside Git.

## Current coverage

- Fully scanned attachment occurrences reported by the channel audit: **590**
- Unique normalized filenames reported by the channel audit: **505**
- Unique files now represented in the structured ledger: **64**
- Ledger entries marked `imported_corrected`: **33**
- Ledger entries marked `imported_source_original`: **0**
- Ledger entries marked `pending_review`: **30**
- Ledger entries marked `alternate_version_preserved`: **1**
- Entries still missing one historical checksum in repository provenance: **2**
- Remaining unique filenames not yet backfilled into this ledger: **441**

The remaining count is a backlog estimate from the completed server inventory, not fabricated placeholder rows. Each future run adds only files whose channel, attachment identity, filename, type, stage, checksum state, mapping, and final decision can be evidenced.

The `pending_review` rows are fully checksummed archived-channel transcripts that map to
the newer `VIDEO_` inventory rather than the old 1,750 canonical `LIVE_` scope. They are retained
with exact identity evidence but deliberately not imported until the old-LIVE-first restriction is
lifted. This includes a filename-year correction (`2021.8.21.docx` is a 2017-08-21 transcript) and
a date-identity correction (`T20170901.docx` contains the exact 2017-05-01 Liu Yanping call media).

Batch 004 added 15 proofread attachments covering 2017-06-11 through 2017-07-10. Fourteen are
deferred VIDEO_ candidates. The two 2017-07-01 attachments were compared paragraph by paragraph:
the earlier version omits only the explicit YouTube source line and is preserved as an alternate,
while the later source-linked version remains the preferred pending candidate. The apparent
`T2021.07.06-1.docx` filename is documented as a 2017-07-06 part-one transcript based on its
internal heading, date, content, and embedded media URL.

## Decision rules

- T-prefixed files are `human_proofread_corrected`.
- Imported corrected and source-original versions remain separate from machine ASR.
- Compilation documents are one ledger file even when mapped to several videos.
- Exact duplicates and alternate versions will receive their own final states when their attachment checksums are compared.
- Y/YZ/P summaries, title indexes, translations, machine drafts, and unrelated files are never promoted as full transcripts.
- Missing checksum fields remain explicit gaps rather than inferred values.

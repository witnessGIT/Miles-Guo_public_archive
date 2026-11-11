# Discord File Ledger

This ledger records per-file decisions for attachments discovered in Discord server `821933739307040799`. Binary documents and media remain outside Git.

## Current coverage

- Fully scanned attachment occurrences reported by the channel audit: **590**
- Unique normalized filenames reported by the channel audit: **505**
- Unique files now represented in the structured ledger: **93**
- Ledger entries marked `imported_corrected`: **34**
- Ledger entries marked `imported_source_original`: **0**
- Ledger entries marked `pending_review`: **48**
- Ledger entries marked `alternate_version_preserved`: **1**
- Ledger entries marked `duplicate_exact`: **10**
- Entries still missing one historical checksum in repository provenance: **2**
- Remaining unique filenames not yet backfilled into this ledger: **412**

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

Batch 005 checked 11 proofread-room attachments covering 2017-07-22 through 2017-08-28.
Ten are byte-identical duplicates of archived-channel copies already represented in the ledger;
the five old-canonical-LIVE copies were already imported as corrected versions and were not
re-imported. `T2017.07.22.docx` is the only new unique file and remains pending because its exact
media identity maps only to `VIDEO_20170722_001` under the old-LIVE-first restriction.

Batch 006 added 16 previously unledgered proofread transcripts covering 2017-05-04 through
2017-06-06. All sixteen map to independent `VIDEO_` identities rather than the old canonical
`LIVE_` set, so they remain `pending_review` under the old-LIVE-first restriction. The apparent
`T2021.06.01.docx` filename is documented as 2017-06-01 from its internal heading, content and
media locator. Existing local downloads were reused; only genuinely missing files were fetched.

Batch 007 checked two additional proofread transcripts. `T2017.04.30.docx` contains the exact
YouTube identifier for `LIVE_20170429_003`; that media identity overrides its one-day-late
filename/header date, so it was imported as a separate corrected version while preserving the
machine parent. `T2017.05.03.docx` maps exactly to the independent `VIDEO_20170503_001`, not the
same-day canonical puppy live, and remains pending under the old-LIVE-first restriction.

## Decision rules

- T-prefixed files are `human_proofread_corrected`.
- Imported corrected and source-original versions remain separate from machine ASR.
- Compilation documents are one ledger file even when mapped to several videos.
- Exact duplicates and alternate versions will receive their own final states when their attachment checksums are compared.
- Y/YZ/P summaries, title indexes, translations, machine drafts, and unrelated files are never promoted as full transcripts.
- Missing checksum fields remain explicit gaps rather than inferred values.

# Discord File Ledger

This ledger records per-file decisions for attachments discovered in Discord server `821933739307040799`. Binary documents and media remain outside Git.

## Current coverage

- Fully scanned attachment occurrences reported by the channel audit: **590**
- Unique normalized filenames reported by the channel audit: **505**
- Unique files now represented in the structured ledger: **122**
- Ledger entries marked `imported_corrected`: **45**
- Ledger entries marked `imported_source_original`: **0**
- Ledger entries marked `pending_review`: **50**
- Ledger entries marked `alternate_version_preserved`: **16**
- Ledger entries marked `duplicate_exact`: **10**
- Ledger entries marked `key_points_or_clip`: **1**
- Entries still missing one historical checksum in repository provenance: **2**
- Remaining unique filenames not yet backfilled into this ledger: **383**

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

The April 29 full-text batch added `T2017.04.29-1.docx` and `T2017.04.29-2.docx`. Their embedded
YouTube identifiers map exactly to `LIVE_20170429_001` and `LIVE_20170429_002`; both were imported
as independent human-corrected versions while preserving their machine transcripts as parents.

Batch 008 checked six previously downloaded T-prefixed documents from `听写任务发放`, without
downloading any file again. `T2017.08.03.docx`, `T2017.08.04.docx`, and `T2017.08.07.docx`
were matched to old canonical `LIVE_20170803_001`, `LIVE_20170804_001`, and
`LIVE_20170807_001`, then imported as separate corrected versions. `T2017.08.02.docx` and
`T2017.08.05.docx` map to deferred `VIDEO_` identities and remain pending. The short
`T2017.08.09.docx` file is a highlights-only list that cannot distinguish the two same-date
canonical lives, so it is retained as `key_points_or_clip` rather than promoted to a transcript.

Batch 009 checked `T2021.12.03.docx` from `GTV 听写文本`. Its explicit heading, continuous
full-live structure, 97,336 characters in 1,134 non-empty paragraphs, and time locators through
`05:26:03` match the unique old canonical `LIVE_20211203_001`. It was imported as a separate
human-corrected version while preserving the machine ASR as parent. The attachment was fetched
directly to a temporary directory without a browser save prompt and was not added to Git.

The assignment-copy audit added 15 already-downloaded T-prefixed attachments from `听写任务发放`
covering 2017-05-15 through 2017-08-02. Each was checksummed and compared with the later preferred
copy already represented from `听写原文校对` or the archived transcript channels. None was
byte-identical or text-identical; all are preserved as materially different alternate versions,
and none overwrote or duplicated an imported corrected transcript. Existing local files were
reused, so this batch caused no browser download or save confirmation.

Batch 010 checked five T-prefixed documents from `GTV 听写文本`: `T2021.11.24`,
`T2021.11.26`, `T2021.11.28`, `T2021.11.30`, and `T2021.12.01`. All five are complete
human-proofread transcripts matched to old canonical `LIVE_` identities and imported as separate
corrected versions. The November 26 document is the 75,213-character, 4:27:40 long-form live,
not the same-date short platform update; November 30 is the complete short fitness live. Machine
parents were preserved. Files were downloaded directly once to a temporary directory, with no
browser save prompt, repeated download, binary commit, or fabricated cue timeline.

## Decision rules

- T-prefixed files are `human_proofread_corrected`.
- Imported corrected and source-original versions remain separate from machine ASR.
- Compilation documents are one ledger file even when mapped to several videos.
- Exact duplicates and alternate versions will receive their own final states when their attachment checksums are compared.
- Y/YZ/P summaries, title indexes, translations, machine drafts, and unrelated files are never promoted as full transcripts.
- Missing checksum fields remain explicit gaps rather than inferred values.

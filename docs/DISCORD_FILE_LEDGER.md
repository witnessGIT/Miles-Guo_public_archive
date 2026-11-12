# Discord File Ledger

This ledger records per-file decisions for attachments discovered in Discord server `821933739307040799`. Binary documents and media remain outside Git.

## Current coverage

- Fully scanned attachment occurrences reported by the channel audit: **590**
- Unique normalized filenames reported by the channel audit: **505**
- Unique files now represented in the structured ledger: **214**
- Ledger entries marked `imported_corrected`: **73**
- Ledger entries marked `imported_source_original`: **0**
- Ledger entries marked `pending_review`: **52**
- Ledger entries marked `alternate_version_preserved`: **28**
- Ledger entries marked `duplicate_exact`: **15**
- Ledger entries marked `key_points_or_clip`: **21**
- Ledger entries marked `title_or_link_index`: **2**
- Ledger entries marked `spreadsheet_metadata`: **7**
- Ledger entries marked `irrelevant`: **16**
- Entries still missing one historical checksum in repository provenance: **3**
- Remaining unique filenames not yet backfilled into this ledger: **291**

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

Batch 011 checked five additional T-prefixed GTV documents dated 2021-12-05, 12-06,
12-08, 12-10, and 12-12. All five match unique old canonical `LIVE_` identities and were
imported as separate corrected versions. The December 6 file is the complete short fitness live;
December 10 is the sole same-date 114,668-character long-form live ending at 06:33:30. Machine
parents were preserved, and no DOCX, media, cache, or fabricated cue timeline entered Git.

Batch 012 checked five T-prefixed GTV documents dated 2021-11-12, 11-14, 11-17, 11-19,
and 11-23. All five were verified as complete human-proofread transcripts and imported as
separate corrected versions. The November 17 and November 19 documents are the long-form lives,
not their same-date short platform updates or camera test; November 23 is the complete short
fitness live. Machine parents were preserved. Each attachment was downloaded directly once to a
temporary directory, without a browser save prompt, repeated download, binary commit, or
fabricated cue timeline.

Ledger batch 010 checked four Y-prefixed XLSX attachments from `GTV 要点初稿`. They are
human-organized, first-reviewed video key-point sheets for 2021-11-05, 2021-11-07,
2021-12-19 part two, and 2021-12-22 part one. Their date, title, GTV/GNEWS locators and same-day
sequence were matched to the exact old canonical `LIVE_` identities. All four are retained as
`key_points_or_clip` evidence and are not promoted to full transcripts. The workbooks were
downloaded directly once to a temporary directory, checksummed and inspected without a browser
save prompt; no workbook binary entered Git.

The next human-transcript batch checked T-prefixed GTV documents dated 2020-07-17,
2020-07-19, 2020-07-25, 2021-09-13 and 2021-09-15. Internal titles, openings, closings and
embedded GTV/GNEWS locators disambiguated all same-date video sets: July 17 maps to the
Barr-speech live; July 19 to the main live rather than either David call segment; July 25 to the
Pompeo-speech main live; and the two 2021 files to their old canonical long-form identities.
All five were imported as separate corrected versions with machine parents preserved. No DOCX,
media, repeated download or fabricated cue timeline entered Git.

Ledger batch 011 backfilled five additional T-prefixed GTV full-text documents dated
2020-05-16, 2021-09-17, 2021-12-24, 2021-12-25, and 2021-12-26. Date, title, opening,
closing and same-day content disambiguation map them respectively to old canonical lives
`LIVE_20200516_001`, `LIVE_20210917_002`, `LIVE_20211224_001`, `LIVE_20211225_002`, and
`LIVE_20211226_001`. All five have complete file/text checksums and remain `pending_review`
for the dedicated transcript worker to import as corrected versions. Each file was fetched
directly once to a temporary directory without a browser save prompt; no binary or fabricated
cue timeline entered Git.

The corresponding transcript-import batch promoted all five ledger batch 011 candidates to
separate human-corrected versions for `LIVE_20200516_001`, `LIVE_20210917_002`,
`LIVE_20211224_001`, `LIVE_20211225_002`, and `LIVE_20211226_001`. Existing machine ASR
versions remain preserved as parents. The already-downloaded local copies were reused, so no
file was downloaded again and no save confirmation, DOCX binary, or fabricated cue timeline
was introduced.

Ledger batch 013 checked nine previously unledgered DOCX attachments from `听写原文`. Eight are
workflow-stage variants for the 2017-08-28, 2017-08-30, 2017-05-01 Liu Yanping call, and
2017-09-02 videos. Their exact embedded YouTube identities and content were compared with the
later preferred corrected copies already represented in the ledger; all eight are preserved as
materially distinct alternate versions and none overwrote an imported transcript. The ninth file
is a server terminology/name glossary and is classified as irrelevant to full-text import. Each
file was downloaded directly once to a temporary directory without a browser save prompt; no
DOCX binary, cache, or fabricated cue timeline entered Git.

Ledger batch 014 checked five T-prefixed files from `听写原文校对`. Four DOCX files are
byte-identical copies of already represented preferred attachments: the 2017-08-31 short video,
the 2017-09-02 imported corrected live, the Liu Yanping call, and the 2017-08-30 video. They are
recorded as exact duplicates and were not re-imported. The native Pages copy for 2017-08-30 is
preserved as an alternate container; its binary checksum is complete, while direct text extraction
was unavailable and remains an explicit provenance gap. Files were downloaded directly once with
no save prompt, binary commit, or fabricated cue timeline.

Ledger batch 015 checked three attachments from `GTV 要点初稿`. The T-prefixed 2021-12-17
DOCX is byte-identical to the preferred human-corrected transcript already imported from the
archived transcript channel, so it is recorded as an exact duplicate and was not re-imported.
The 2021-12-17 and 2021-12-19 part-one XLSX files are human-organized, first-reviewed video
key-point sheets with explicit dates, titles, GTV/GNEWS locators and sequence evidence. They map
respectively to `LIVE_20211217_001` and `LIVE_20211219_001`, remain `key_points_or_clip`
evidence, and are not promoted as full transcripts. All three files were downloaded directly once
to a temporary directory without a browser save prompt; no binary entered Git.

Ledger batch 016 checked all 11 DOCX transcript candidates found in `聊天室`. Eight complete
T-prefixed, human-proofread transcripts dated 2021-12-15, 2021-12-22, 2022-01-05, 01-07,
01-09, 01-12, 01-14, and 01-17 were matched to their exact old canonical `LIVE_` identities and
imported as separate corrected versions. The December 22 document is a materially edited alternate
of the previously imported proofread text, so it is retained as corrected version 002 rather than
discarded as a duplicate. The January 7 document is the long-form `LIVE_20220107_002`, not the
same-date short item. The remaining three documents are parts one through three of the roughly
twelve-hour 2022-01-01 live; all explicitly remain unfinished and together stop several hours before
the media ends, so they are preserved as incomplete alternate evidence and not promoted to a full
transcript. All files were downloaded directly once to a temporary directory without browser save
prompts; no DOCX binary, repeated download, or fabricated cue timeline entered Git.

Ledger batch 017 checked the remaining 40 attachments found in the fully paged `聊天室`
history. Two T-prefixed, human-proofread full transcripts map to old canonical videos
`LIVE_20200514_002` and `LIVE_20211020_001` and are queued for the dedicated transcript
worker. Four XLSX files were inspected read-only: three are dated video key-point sheets for
`LIVE_20200514_002`, `LIVE_20211022_001`, and `LIVE_20211024_001`, while the fourth is a blank
template. The 1.27-million-character DOC file is an alphabetic keyword and internal-anchor index,
not a per-video transcript. The remaining screenshots, a 22.97-second chat clip, artwork, form,
QR-code image, and installer were checksummed and classified as key-point excerpts, workflow
metadata, index evidence, or irrelevant auxiliary material. All 40 files were downloaded directly
once to a temporary directory without browser save prompts; no binary, media, executable, cache,
or fabricated cue timeline entered Git.

A follow-up evidence pass restored the exact Discord message IDs for both pending old-LIVE
transcripts and corrected `T2020.5.14_.docx` from an extracted-text surrogate back to its true
DOCX attachment identity. Both binary checksums and both extracted-text checksums were reproduced
from the source documents. Reusable copies remain only in a local out-of-Git cache, preventing
another download or browser save prompt; their `pending_review` status is unchanged until the
dedicated transcript worker imports them.

## Decision rules

- T-prefixed files are `human_proofread_corrected`.
- Imported corrected and source-original versions remain separate from machine ASR.
- Compilation documents are one ledger file even when mapped to several videos.
- Exact duplicates and alternate versions will receive their own final states when their attachment checksums are compared.
- Y/YZ/P summaries, title indexes, translations, machine drafts, and unrelated files are never promoted as full transcripts.
- Missing checksum fields remain explicit gaps rather than inferred values.

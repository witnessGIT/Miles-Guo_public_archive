# Discord File Ledger

This ledger records per-file decisions for attachments discovered in Discord server `821933739307040799`. Binary documents and media remain outside Git.

## Current coverage

- Fully scanned attachment occurrences reported by the channel audit: **590**
- Unique normalized filenames reported by the channel audit: **505**
- Ledger rows: **446**
- Distinct Discord attachment IDs in those rows: **446**
- Distinct normalized filenames in those rows: **374**
- Ledger entries marked `imported_corrected`: **130**
- Ledger entries marked `imported_source_original`: **0**
- Ledger entries marked `pending_review`: **69**
- Ledger entries marked `non_fulltext_summary`: **1**
- Ledger entries marked `alternate_version_preserved`: **51**
- Ledger entries marked `duplicate_exact`: **27**
- Ledger entries marked `key_points_or_clip`: **134**
- Ledger entries marked `title_or_link_index`: **4**
- Ledger entries marked `spreadsheet_metadata`: **7**
- Ledger entries marked `translation`: **4**
- Ledger entries marked `machine_draft`: **1**
- Ledger entries marked `irrelevant`: **18**
- Entries still missing one historical checksum in repository provenance: **1**
- Estimated normalized filenames not yet represented in this ledger: **131** (`505 - 374`)

The previous estimate of 122 subtracted ledger rows from unique filenames, mixing two different counting units. The ledger has 63 rows beyond its 366 distinct normalized filenames, including alternate uploads and exact duplicates. Four contradictory duplicate rows that reused existing attachment IDs and binary checksums were removed in batch 032; the genuine distinct assignment-channel versions remain separately recorded. See `data/source_page_evidence/discord/discord_ledger_duplicate_attachment_audit.jsonl` for each retained and removed ID and checksum. The 157 remaining names are a backlog estimate from the completed server inventory, not fabricated placeholder rows. The original 505-name scan is not stored as a complete itemized manifest, so the currently missing names cannot yet be enumerated individually. Each future run adds only files whose channel, attachment identity, filename, type, stage, checksum state, mapping, and final decision can be evidenced.

Ledger batch 037 rechecked the existing 2018 January multi-video DOCX compilation from 工作分享. Its 835,242-byte binary SHA-256 matched the historical ledger value; a direct signed CDN request and local text extraction filled the missing text SHA-256. The file also contains separately headed January 3, 13, and 28 sections beyond its nine imported source records, so those sections remain for a separate exact-identity review and were not imported in this checksum repair. This batch checked 1 previously decided file, imported 0, found 0 exact duplicates, preserved the existing compilation version, excluded 0 non-fulltext files, found 0 unreachable files, and left 68 pending reviews and an estimated 157 unrepresented normalized filenames.

Ledger batch 038 rechecked two earlier T-prefixed attachments using signed Discord CDN URLs and reproduced both binary SHA-256 values. The September 4, 2017 DOCX second part yielded a 10,442-character text extraction and a complete extracted-text checksum; its Discord message ID was restored. The August 30 Pages package remained text-inaccessible with the available local converters. A contemporary channel reply says that Pages upload was the wrong file and a DOCX replacement followed, so its former alternate-version conclusion was revised to `pending_review` and its completeness is undetermined. This batch checked 2 previously decided files, imported 0, found 0 exact duplicates, confirmed 0 alternate versions, excluded 0 non-fulltext files, found 0 unreachable files, and left 69 pending reviews and an estimated 157 unrepresented normalized filenames. The Pages text checksum remains an explicit gap.

Ledger batch 039 inspected ten previously unrepresented Y-prefixed DOCX attachments in archived 要点原文. Each downloaded noninteractively from its signed CDN URL, and each binary and text extraction received its own SHA-256. The documents are edited key points with source quotations, not certified continuous full transcripts, even where the quotation text is long. The April 29 second video is tied to `LIVE_20170429_002`; April 26 remains date-only because same-day part identity is not proven. This batch checked 10 unique files, imported 0, found 0 exact duplicates and 0 confirmed alternate versions, excluded 10 from fulltext import, found 0 unreachable files, and left 69 pending reviews and an estimated 147 unrepresented normalized filenames. No DOCX or cache was committed.

Ledger batch 041 checked 17 previously unledgered Y/YZ DOCX attachments in the hidden 要点原文校对 and 要点整理校对 channels. All were obtained noninteractively through signed Discord CDN URLs, with binary and extracted-text SHA-256 values recorded individually. Nine are exact binary reuploads of key-point files already in the ledger; eight are additional edited key-point versions. The 2017-08-22 file's title was checked against the catalog's second-broadcast identity, avoiding a filename-based swap with another same-day video. This batch checked 17 unique attachment IDs, imported 0 full transcripts, found 9 exact duplicates, preserved 8 distinct key-point versions, excluded all 17 from fulltext import, found 0 unreachable files, and left 69 pending reviews and an estimated 131 unrepresented normalized filenames. No DOCX or cache was committed.

Ledger batch 040 checked ten Y/YZ DOCX attachments in archived 要点整理文本. Eight are distinct key-point editorial files and two are byte-identical reuploads of already ledgered same-name files; different text extraction methods explain differing extracted-text digests for those binary duplicates. Every attachment received its own binary and extracted-text SHA-256. The `YZ-J2017.08.22-2.docx` filename suffix conflicts with its embedded media URL; the URL maps to the first 2017-08-22 catalog entry, so the second same-day video was not substituted. This batch checked 10 files, imported 0, found 2 exact duplicates, found 0 alternate versions, excluded all 10 from fulltext import, found 0 unreachable files, and left 69 pending reviews and an estimated 139 unrepresented normalized filenames. No DOCX or cache was committed.

Ledger batch 036 checked eight previously unrepresented XLSX attachments from GTV 讨论房. Their embedded titles and GTV video IDs map respectively to the old canonical 2021-10-22, 10-24, second 10-26, and second 11-01 long lives. They are Y-prefixed key-point and topic sheets; two are sparse scaffolds and one includes long selected excerpts, but none is a continuous full transcript. All eight binaries differ from previously ledgered attachments. Repeated filenames identify distinct draft/revision stages and are linked per row. Files were fetched once through signed CDN URLs without interaction, with binary and extracted-cell-text SHA-256 recorded; no workbook entered Git. This batch checked 8, imported 0, found 0 exact duplicates, documented 6 alternate same-name editorial versions, excluded 8 non-fulltext files, found 0 unreachable files, and left 68 pending reviews and an estimated 157 unrepresented normalized filenames.

Ledger batch 035 checked seven previously unrepresented Discord DOCX attachments from GTV 讨论房, 字幕讨论房 and gnews发布整理. Three T-prefixed full human-proofread texts map to old canonical LIVE_20211022_001, LIVE_20211024_001 and LIVE_20211026_002 and were imported as separate corrected versions with machine parents preserved. Another T-prefixed LIVE_20211101_002 copy differs in binary but is 99.95% normalized-text similar to its already imported preferred corrected version, so it remains an alternate. The 2017-07-17 interview text maps to a VIDEO_ identity and remains pending under the old-LIVE-first rule. Two VOA key-point documents are distinct 98.82%-similar editorial versions; neither is a full transcript. All seven were fetched non-interactively to a temporary directory; original binaries and caches remain outside Git. This batch checked 7, imported 3, found 0 exact duplicates, preserved 2 alternate versions, excluded 1 additional non-fulltext original, found 0 unreachable files, and left 68 pending reviews and an estimated 159 unrepresented normalized filenames.

Ledger batch 034 checked ten more previously unrepresented DOCX attachments in `要点整理`. Eight YZ/Y files are edited key-point outlines; two Y...J files also include task assignments and edited key points. None is a complete transcript. Three embedded YouTube identities establish exact August video mappings; six earlier documents without unique media locators retain date-only identities. The two August 15 files are distinct editorial versions of the same key points. All ten were fetched directly by non-interactive signed CDN requests into a temporary directory, with file and extracted-text checksums recorded. This batch checked 10, imported 0, found 0 exact duplicates, preserved 1 distinct editorial relationship, excluded 10 non-fulltext files, found 0 unreachable files, and left 67 pending reviews and an estimated 164 unrepresented normalized filenames.

Ledger batch 033 checked five previously unrepresented DOCX attachments in `要点整理` (2017-05-04, 05-21 part two, 07-01, 08-21 and 08-22). Their contents are edited key-point outlines, not complete transcripts, so all five are recorded as `key_points_or_clip` with exact channel/message/attachment IDs and file/text checksums. The files were fetched through signed Discord CDN URLs by non-interactive requests to a temporary directory. This batch checked 5, imported 0, found 0 exact duplicates, preserved 0 alternate versions, excluded 5 non-fulltext files, found 0 unreachable files, and left 67 pending reviews and an estimated 174 unrepresented normalized filenames.

Ledger batch 032 reconciled four repeated attachment IDs for 2017-05-15, 2017-05-16, and 2017-05-19. Each duplicate row reused the proofread-channel attachment ID, CDN URL, and binary checksum but had a conflicting extracted-text checksum and no message ID. The genuine assignment-channel alternate versions had separate IDs and checksums and remain intact. The four contradictory duplicate rows were removed with an itemized audit record. This batch checked four attachment identities, imported 0, found 4 duplicate ledger rows, preserved 4 valid alternate versions, excluded 0 non-fulltext files, found 0 newly unreachable files, and left 67 pending reviews and an estimated 179 unrepresented normalized filenames.

Ledger batch 030 checked two previously unrepresented bilingual DOCX files in `翻译` for parts two and three of the 2017-04-19 VOA interview. Each contains selected Chinese key points with English translation, not a complete original-language transcript. Both are recorded as `translation` with precise attachment origin and binary/extracted-text checksums. They were fetched directly without interaction into a temporary directory; no DOCX, extracted text, or cue entered Git.

Ledger batch 029 checked the previously unrepresented 5.24 MB VOG big-events DOC from `服务器说明`. Its alphabetic topic links and dated curated excerpts span multiple videos, so it is recorded as `non_fulltext_summary`, with no individual LIVE_ mapping or transcript import. The Discord message/attachment IDs, direct CDN source, binary SHA-256, extracted-text SHA-256, and document structure are recorded; the binary and temporary text stay outside Git.

Ledger batch 027 concluded three previously pending VIDEO_-phase artifacts using their existing checksums and extracted-text evidence. `2017.8.20.docx` is explicitly only the third segment of a four-video compilation and remains `key_points_or_clip`; `17072017717.docx` is a proofread interview part retained as `alternate_version_preserved` because a complete source-original transcript for the same video is already ledgered; `2017813-.docx` is a network-test/ephemeral clip and remains `key_points_or_clip`. No attachment was downloaded again, no full transcript was overwritten, and no cue was fabricated.

Ledger batch 028 reused four already-downloaded T-prefixed assignment-channel documents dated 2017-05-15 through 2017-05-19. Their Discord attachment identities differ from the archived-channel copies, and file/text checksums plus normalized comparisons show materially distinct proofread versions (67.22%–90.87% similarity). All four map to existing VIDEO_ identities and are preserved as `alternate_version_preserved`; no preferred text was overwritten and no attachment was downloaded again.

Ledger batch 026 checked the sole currently visible attachment in Discord channel `机听文本`:
`jt2021.08.25.docx`. Its channel, `jt` prefix, dense one-minute time windows, and visibly noisy
recognition errors identify it as a machine-listening draft rather than a human-proofread text.
Its approximately 4h37m coverage and vaccine-focused content align with old canonical
`LIVE_20210825_001`; it is retained as `machine_draft` provenance and was not imported or used to
replace any human or machine transcript version. The file was fetched once by a non-interactive
direct request to a temporary directory. Exact Discord message/attachment IDs and both checksums
were recorded; no browser download, save dialog, repeated download, binary commit, ASR run, or AI
API was involved.

Ledger batch 025 checked 21 previously unrepresented Discord attachments from `GTV 听写文本`.
Seventeen complete T-prefixed human-proofread texts were matched to old canonical `LIVE_`
identities and imported as separate corrected versions with their machine parents preserved.
The second `T2020.07.25.docx` copy is 99.95% text-similar to the already imported preferred
corrected version and is retained as alternate evidence rather than imported redundantly.
`T2020.11.11-2.docx` is a short timestamped summary, and the two Y-prefixed XLSX files are
human-organized video key-point sheets; all three remain `key_points_or_clip` rather than being
promoted to full transcripts. Exact Discord message and attachment IDs, clean CDN URLs, binary
and extracted-text checksums were recorded for every row. All 21 attachments were fetched once
with non-interactive direct requests into a temporary directory; no browser download, save dialog,
repeated download, binary commit, ASR, AI API output, or invented cue timeline was used.

Transcript batch 024 checked 21 previously unrepresented T-prefixed DOCX attachment
occurrences from `GTV 听写文本`. Nineteen complete single-video human-proofread texts were
matched to old canonical `LIVE_` identities and imported as separate corrected versions with
machine parents preserved. The second `T2020.05.30.docx` upload is an exact binary and extracted-
text duplicate and was not imported twice. `T2020.11.11-3.docx` is explicitly a short `内容梗概`
with sparse locators rather than a full transcript, so it remains `key_points_or_clip`. All files
were downloaded directly without a save dialog; the duplicate upload was downloaded under an
attachment-specific temporary name for checksum comparison. Discord message snowflakes not
exposed by the attachment URLs remain null rather than fabricated. No DOCX, cache, automatic ASR,
AI API output, or invented cue timeline entered Git.

Transcript batch 023 checked 15 previously unrepresented T-prefixed DOCX attachments from
`GTV 听写文本`. Fourteen complete, single-video human-proofread texts were matched to old
canonical `LIVE_` identities and imported as separate corrected versions. Same-date ambiguities
were resolved from internal titles and content: the April 4 Sara/Hong Kong text maps to
`LIVE_20200404_002`, the April 5 cooking text to `LIVE_20200405_001`, the timezone-shifted
April 9/10 movie-theatre text to `LIVE_20200409_002`, and the May 21 Freedom Statue text to
`LIVE_20210521_002`. The remaining April 5 document is a continuous compilation spanning
`LIVE_20200405_002` through `_005` without reliable split boundaries; it is preserved as an
alternate compilation and was not copied wholesale into four videos. Machine parents remain
preserved. All 15 attachments were downloaded directly once without a save dialog or repeated
download; no DOCX, cache, ASR, or fabricated cue timeline entered Git.

The dedicated transcript import batch reused the already-downloaded `T2021.12.29.docx` and
`T2022.01.19.docx`, verified both binary and extracted-text checksums, and imported them as
separate human-corrected versions for `LIVE_20211229_001` and `LIVE_20220119_001`. The existing
machine transcripts remain as parents. The 57 and 58 sparse source time locators remain textual
evidence only; no sentence cues were fabricated, and no download prompt or repeated download occurred.

Ledger batch 022 checked 21 previously unrepresented Y-prefixed XLSX attachments from `要点存档`.
All 21 are archived, human-organized video key-point workbooks with real timing locators, not full
transcripts. Exact dates, titles, durations and platform locators map them to old canonical `LIVE_`
identities. Three workbooks cover multiple separately identified videos; their identities remain
separate and were not merged by date. Each attachment was downloaded directly once to a temporary
directory without a save dialog, and its Discord message/attachment IDs, binary checksum and
extracted-text checksum were recorded. No workbook binary, cache, transcript import or fabricated
cue timeline entered Git.

Ledger batch 021 checked ten previously unrepresented Y-prefixed XLSX attachments from `要点存档`.
All ten are archived, human-organized video key-point workbooks with real timing locators, not full
transcripts. Their dates, titles and GTV/GNEWS locators map to exact old canonical `LIVE_` identities;
the 2021-11-17, 2021-11-19, 2021-12-24 and 2021-12-25 sheets were explicitly disambiguated from
other same-day videos. Each attachment was downloaded directly once without a save dialog, and its
exact Discord message/attachment IDs, binary checksum and extracted-text checksum were recorded.
No workbook binary, cache or fabricated transcript cue entered Git.

Ledger batch 020 checked 32 previously unrepresented attachments from `任务领取` and `要点一校`.
The twelve T-prefixed DOCX files are human-proofread texts: ten are earlier corrected-stage copies
or explicitly unfinished parts already superseded by separately preserved/imported versions, while
the complete 2021-12-29 and 2022-01-19 texts remain `pending_review` for the dedicated transcript
worker. The ten sparse Y-prefixed task-room workbooks and ten populated first-review workbooks are
video key-point sheets rather than full transcripts. Exact Discord message and attachment IDs,
canonical old-LIVE mappings, binary checksums and extracted-text checksums were recorded for all
32 files. Each missing attachment was downloaded directly once without a save dialog; no binary,
cache, transcript import or fabricated cue timeline entered Git.

The local-reuse comparison batch added five previously unledgered full-text attachments for
`LIVE_20170429_002`, `LIVE_20170525_001`, `LIVE_20170708_001`, `LIVE_20170709_001`, and
`LIVE_20170715_001`. File-origin metadata preserved by macOS supplied the exact Discord channel
and attachment identities. Each document was checksummed, extracted and compared with the
existing preferred corrected version; normalized similarities ranged from materially distinct
to near-parallel, so all five are retained as alternate human versions without overwriting or
re-importing the preferred transcript. Existing downloads were reused and no browser save prompt,
binary commit or fabricated cue timeline was created.

The next local-reuse backlog batch checked 33 already-downloaded attachments without triggering
any browser download or save prompt. It added twenty deferred full/partial transcript candidates,
three old-canonical alternate human versions, six short-clip or YZ-F key-point documents, two
title/link indexes, and two translation artifacts. Every row records the preserved Discord CDN
channel and attachment identity, binary and extracted-text checksums, document stage, completeness,
mapping evidence and final decision. Discord message IDs that cannot be recovered from CDN origin
metadata remain explicitly null rather than being invented. No DOCX/XLSX binary entered Git.

The following single-file local-reuse batch added the remaining already-downloaded assignment-room
copy of `2017.05.21-2.docx`. Its content maps to deferred `VIDEO_20170521_003` and is a distinct
earlier human source-original version of the corrected-channel file already represented in the
ledger. It is preserved as `alternate_version_preserved` without import or overwrite. The existing
local copy and Finder origin metadata were reused, so no download or save prompt was triggered.

Ledger batch 019 checked two previously unledgered PDFs from the server project room. `20.pdf`
is the archive-production plan and documents task rooms, deliverables and the
T/T-J/TZ/TZ-J/Y/YZ/P naming stages. `download_2.pdf` is a one-page workflow diagram covering
link collection, transcription, proofreading, key-point extraction and clip production. Neither
contains a per-video transcript, so both are classified as workflow documentation rather than
promoted to full text. Existing local copies were reused, their binary and extracted-text checksums
were recorded, and their first pages were visually inspected; no repeated download, save prompt or
PDF binary entered Git.

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

The dedicated transcript worker then reused those verified cache copies and imported
`T2020.5.14_.docx` and `T2021.10.20.docx` as independent human-corrected versions for
`LIVE_20200514_002` and `LIVE_20211020_001`. Their machine transcripts remain intact as parent
versions. No attachment was downloaded again, no binary entered Git, and the documents' sparse
locators were not expanded into fabricated sentence-level cues.

## Decision rules

- T-prefixed files are `human_proofread_corrected`.
- Imported corrected and source-original versions remain separate from machine ASR.
- Compilation documents are one ledger file even when mapped to several videos.
- Exact duplicates and alternate versions will receive their own final states when their attachment checksums are compared.
- Y/YZ/P summaries, title indexes, translations, machine drafts, and unrelated files are never promoted as full transcripts.
- Missing checksum fields remain explicit gaps rather than inferred values.

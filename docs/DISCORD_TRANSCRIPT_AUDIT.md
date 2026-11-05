# Discord Human Transcript Audit

This audit records human transcript material found in the Discord server `821933739307040799` so the discovery state does not depend on one chat session. Binary DOCX, Pages, audio, and video files are not committed. Imports preserve extracted text, provenance, original filenames, attachment identifiers, and checksums as separate transcript versions.

## Quality order

The server instructions define these filename stages:

1. `TZ...-J` re-edited and proofread
2. `TZ...` re-edited
3. `T...-J` proofread transcript
4. `T...` transcript

When several versions map to the same live, the highest available stage is preferred. Earlier versions remain provenance and are not used to overwrite a better human version. Human transcripts remain separate from machine ASR.

## Channel inventory

Counts below were obtained by loading each channel's full virtualized history in both directions. Earlier visible-window counts were incomplete. Attachment counts are per channel and may include duplicate filenames or alternate stages.

| Channel | Channel ID | Material found | Coverage and notes |
| --- | --- | ---: | --- |
| 听写任务发放 | `821991750901694514` | 54 DOCX attachments | Human source and assignment documents, mainly April through August 2017. |
| 听写原文 | `821933739307040805` | 119 attachments | Human transcript drafts and assembled versions, mainly April through September 2017, plus a filename labelled `T2021.06.01.docx`. |
| 听写原文校对 | `821933739307040806` | 70 attachments | Proofread human transcripts, mainly April through September 2017. The unusable `T20170830.pages` upload was followed by the usable `T20170830.docx`, which is the preferred version. |
| archived 听写原文 | `821935829668593674` | 19 attachments | Earlier 2017 human transcript archive. |
| 工作分享 | `831782777434538024` | 1 DOCX plus external bundle | `20181.docx` contains January 2018 material. A MEGA/GNEWS bundle contains February 2018 human-edited material. |
| GTV 听写文本 | `896946673807401041` | 245 attachments | 242 DOCX and 3 XLSX files: 95 filenames dated in 2020 and 150 in 2021. They cover 222 distinct filename dates from April 4, 2020 through December 26, 2021. |
| GTV 要点初稿 | `892756248179654717` | 315 attachments | Mostly derived XLSX key-point sheets, but also 9 DOCX files. Three full human transcripts absent from the GTV transcript-room filename set were confirmed: `T2021.10.29` (74,778 characters, 780 paragraphs, time marks through 03:55:51), `T2021.11.05` (73,247 characters, 806 paragraphs, time marks through 04:16:50), and `T2021.11.07` (88,171 characters, 900 paragraphs, time marks through 04:55:38). `Y2021.09.17`, `Y2021.09.21`, and `Y2021.09.26` are derived summaries, but each records a public GNEWS URL for its human source transcript. |
| 聊天室 | `821933739307040804` | 20 attachments | Contains 11 DOC/DOCX transcript candidates from 2020 through January 2022, four XLSX files, one executable, and other miscellaneous documents. The transcript candidates must be compared with GTV-room versions before import. |
| 报名区 | `822474486581690408` | 1 DOCX attachment | `Y2021.09.26.docx`, probably a derived key-point file; retain for comparison with the same-date GTV files. |
| 直播链接补充 | `821933739307040801` | 44 attachments and 117 external links | 73 YouTube, 27 VOG, 14 GWINS, and 3 MEGA links were captured. Attached AI drafts are lower priority than human or public edited text. |
| 视频剪辑工作区 | `821990270164926485` | 2 DOCX attachments | `20170802.docx` and `2904201713.docx`, plus historical video and MEGA links. |
| 视频原件 | `821935776659931156` | 0 attachments and 5 MEGA folders | Media-source folders; no transcript attachment was found. |
| 机听文本 | `897096565339086848` | 1 DOCX attachment | `jt2021.08.25.docx`, explicitly machine-generated and lower priority. |
| 翻译 | `844771010771157053` | 2 DOCX and 1 XLSX attachments | English translations and a historical broadcast index; useful as corroboration, not the primary Chinese transcript. |
| 讨论 | `972267796895498260` | 10 attachments | `2017-2018.docx`, `2019.docx`, and `2020-2022.04.docx` are title/topic indexes rather than full transcripts. They are valuable for identity matching and show that a filename search alone must not be treated as transcript coverage. |

## Secondary material

- Three older key-point source/proofread channels contain 162 DOCX attachments in total. They are derived summaries, not full transcripts.
- `要点整理` and `要点整理校对` contain 52 and 51 DOCX attachments respectively; these are `Y`/`YZ` summary stages.
- `要点视频剪辑` contains 175 DOCX attachments, mainly short `P...` clip scripts plus repeated `YZ-J...` summary files.
- The GTV key-point rooms contain 315 initial, 223 first-proofread, and 201 archived attachments. Most are XLSX key-point sheets; only the exceptional DOCX files listed above are transcript candidates.
- `文本整理` contains 17 DOCX files. A sampled `YZ-F...` document is a published key-point article, not a full transcript.
- `服务器说明` contains three workflow/reference files. They establish the transcript-stage quality order recorded above.
- `通知` contains two template/reference files. `视频制作` contains two XLSX files and MEGA media links.
- No useful transcript attachment was found in `听写初稿`, `字幕制作`, `中文字幕`, `素材库`, `存档视频剪辑`, `文案`, `封面设计`, `要点片段整理`, `编年体整理发布`, `纪事体整理发布`, or `人物专题整理发布`.

## Confirmed imports

- Four 2017 human transcripts were imported in commit `c637b5ea5`.
- Twelve additional human documents were imported in commit `0b0828b31`.
- The January 2018 compilation was imported in commit `bbf098e78`.
- Twenty-nine February 2018 human-edited GWINS transcripts were imported in commit `40a7537c9`.
- `T2021.11.20.docx` was imported as a separate human `source_original` version in commit `457d45127`; its transcript-import completion was published in `fd52084bc`.

## 2021-11-20 verification

The Discord file is a complete long-form event transcript rather than a short excerpt:

- original filename: `T2021.11.20.docx`
- Discord channel: `896946673807401041`
- attachment ID: `923744729697501224`
- DOCX SHA-256: `daa6a622ec4431c1d31f88708302566a4b83afdbf338e7962d6e695d8cbe0635`
- extracted text: 123,698 characters in 1,252 non-empty paragraphs
- document time marks extend through `09:26:50`
- exact date and event heading match `LIVE_20211120_001`

The DOCX binary remains outside Git. The repository stores only the structured transcript and provenance record.

## Remaining search gap

The Discord server contains `2019.docx`, but inspection shows that it is a 299-paragraph, 9,710-character title/topic index rather than a full transcript. No genuine 2019 full-transcript attachment has yet been confirmed. The 2019 gap therefore remains an external-source search target: historical MEGA bundles, public GWINS/VOG/GHOT pages, and any earlier platform migration export should be checked before treating those lives as audio-only.

## Deduplication state

Across the transcript-relevant and adjacent channels scanned so far, 590 attachment occurrences produced 505 unique normalized filenames. This is a discovery count, not a completion count: it includes 482 DOCX files as well as indexes, translations, derived summaries, machine drafts, and unrelated attachments. There are 74 filenames repeated across two or more channels. Final import decisions must use file checksums and content comparison, not filenames alone.

## Import policy

- Prefer verifiable human transcripts and proofread versions over machine ASR.
- Preserve draft, proofread, and re-edited stages separately when materially different.
- Match by exact date, event title, video identifier, duration/time coverage, and opening/closing text; never merge by date alone.
- Record the original filename, server/channel/attachment identifiers, source URL, document checksum, extracted-text checksum, and extraction path.
- Do not commit DOCX, Pages, media, caches, models, or temporary downloads.
- Run database build, database validation, and the full test suite before completing an import.

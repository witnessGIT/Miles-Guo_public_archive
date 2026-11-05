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

| Channel | Channel ID | Material found | Coverage and notes |
| --- | --- | ---: | --- |
| 听写任务发放 | `821991750901694514` | 54 DOCX attachments | Human source and assignment documents, mainly April through August 2017. |
| 听写原文 | `821933739307040805` | 115 attachments | Human transcript drafts and assembled versions, mainly April through September 2017, plus `T2021.06.01.docx`. |
| 听写原文校对 | `821933739307040806` | 16 attachments | Proofreading room, July 22 through September 2, 2017. The unusable `T20170830.pages` upload was followed by the usable `T20170830.docx`, which is the preferred version. |
| archived 听写原文 | `821935829668593674` | 10 attachments | Earlier 2017 human transcript archive. |
| 工作分享 | `831782777434538024` | 1 DOCX plus external bundle | `20181.docx` contains January 2018 material. A MEGA/GNEWS bundle contains February 2018 human-edited material. |
| GTV 听写文本 | `896946673807401041` | 245 attachments | 95 files dated in 2020, 149 dated in 2021, and one non-transcript table. The files cover 221 distinct dates from April 4, 2020 through December 26, 2021. |
| 直播链接补充 | `821933739307040801` | 39 or more transcript-related posts | Video links, public VOG/GWINS text pages, and AI drafts. AI drafts are lower priority than human or public edited text. |

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

Direct server searches for `2019`, `T2019`, `2019 has:file`, and `2019 mega.nz` did not expose a genuine 2019 transcript attachment. The few `2019` hits were unrelated messages or a 2017 video whose YouTube title had an incorrect 2019 date. The 2019 gap therefore remains an external-source search target: historical MEGA bundles, public GWINS/VOG/GHOT pages, and any earlier platform migration export should be checked before treating those lives as audio-only.

## Import policy

- Prefer verifiable human transcripts and proofread versions over machine ASR.
- Preserve draft, proofread, and re-edited stages separately when materially different.
- Match by exact date, event title, video identifier, duration/time coverage, and opening/closing text; never merge by date alone.
- Record the original filename, server/channel/attachment identifiers, source URL, document checksum, extracted-text checksum, and extraction path.
- Do not commit DOCX, Pages, media, caches, models, or temporary downloads.
- Run database build, database validation, and the full test suite before completing an import.

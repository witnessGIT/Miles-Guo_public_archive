# Miles-Guo_public_archive Pilot Selection

Project: `Miles-Guo_public_archive`  
Task: `P5-PILOT-SELECTION`  
Selection version: `pilot-v1`  
Verified: `2026-09-13`

Machine-readable selection:

```text
reports/pilot_selection.json
```

## Result

Selected **27 source-backed Pilot cases** split into three non-overlapping work groups:

```text
early   9 cases  2017-2019
middle  9 cases  2020-2021
late    9 cases  2022-2023
```

These are selection cases, not yet canonical `LIVE_YYYYMMDD_NNN` assignments. P6 collectors must collect source metadata, execute `identity-v1`, then create/attach the canonical livestream identity.

## Early group — P6-PILOT-EARLY

| Case | Date | Seed | Why selected |
| --- | --- | --- | --- |
| PILOT-E001 | 2017-05-23 | GHOT `2017-05-23-1` | early report/live case; timed transcript |
| PILOT-E002 | 2017-06-10 | GHOT `2017-06-10-1` | early live case; dense timeline |
| PILOT-E003 | 2017-10-04 | GHOT `2017-10-04-1` | Washington live; verified duration/timestamps |
| PILOT-E004 | 2018-04-19 | GWINS `21780` | GWINS-first; third live; human organizer/entity metadata |
| PILOT-E005 | 2018-06-16 | GWINS `21799` | YouTube + Rumble external identities |
| PILOT-E006 | 2018-08-15 | GWINS `21826` | GWINS-first; rich source metadata |
| PILOT-E007 | 2019-05-30 | GHOT `2019-05-30-2` | 36-minute live/chat; irregular segment spacing |
| PILOT-E008 | 2019-09-20 | GHOT `2019-09-20-1` | explicit 35-minute livestream |
| PILOT-E009 | 2019-10-29 | GHOT `2019-10-29-1` | late-2019 archive/source-link coverage |

## Middle group — P6-PILOT-MIDDLE

| Case | Date | Seed | Why selected |
| --- | --- | --- | --- |
| PILOT-M001 | 2020-03-23 | GHOT `2020-03-23-1` | 2020 livestream coverage |
| PILOT-M002 | 2020-04-18 | GHOT `2020-04-18-3` | path ordinal `-3` vs title ordinal `-2` |
| PILOT-M003 | 2020-06-06 | GHOT `2020-06-06-1` | ~1h22m long-form timeline |
| PILOT-M004 | 2020-10-01 | GHOT `2020-10-01-3` | path/title ordinal mismatch + severely noisy ASR |
| PILOT-M005 | 2020-11-20 | GHOT `2020-11-20-4` | ~2h59m + selected clip with bounded range |
| PILOT-M006 | 2021-06-12 | GHOT `2021-06-12-1` | ~1h19m long-form timing case |
| PILOT-M007 | 2021-09-02 | GHOT `2021-09-02-2` | dense second-level anchors |
| PILOT-M008 | 2021-10-29 | GHOT `2021-10-29-1` | ~4h22m + noisy transcript stress case |
| PILOT-M009 | 2021-11-24 | GHOT `2021-11-24-1` | ~5h50m + Odysee original-source behavior |

## Late group — P6-PILOT-LATE

| Case | Date | Seed | Why selected |
| --- | --- | --- | --- |
| PILOT-L001 | 2022-01-26 | GHOT `2022-01-26-2` | dense 10-minute transcript |
| PILOT-L002 | 2022-05-06 | GHOT `2022-05-06-1` | path `-1` vs title `-2`; GETTR original observed |
| PILOT-L003 | 2022-05-11 | GHOT `2022-05-11-2` | verified GHOT/GWINS/GETTR/Rumble overlap |
| PILOT-L004 | 2022-05-29 | GHOT `2022-05-29-6` | path `-6` vs title `-2`; long-form program |
| PILOT-L005 | 2022-10-24 | GHOT `2022-10-24-1` | late-2022 cross-source-link case |
| PILOT-L006 | 2023-01-22 | GHOT `2023-01-22-2` | long special livestream; multi-speaker behavior |
| PILOT-L007 | 2023-03-10 | GHOT `2023-03-10-1` | verified GWINS `24261` + GETTR post + Rumble |
| PILOT-L008 | 2023-03-12 | GWINS `24266` | clean GWINS `HH:MM:SS`; GETTR streaming + Rumble; same-day-neighbor stress |
| PILOT-L009 | 2023-03-14 | GHOT `2023-03-14-1` | verified GWINS `24264` + GETTR post; dense timing |

## Why this set is useful

The set intentionally contains both normal and failure-prone cases:

- early, middle and late archive eras;
- GWINS-first and GHOT-first discovery;
- exact cross-source overlaps;
- GETTR `post` and `streaming` URL forms;
- YouTube, Rumble, GETTR, Odysee and archive-page links;
- very short through multi-hour material;
- clean and noisy ASR;
- explicit time anchors;
- GHOT path/title ordinal disagreement;
- same-date neighboring records;
- a GHOT clip range linked to a long original video.

A Pilot that works only on clean recent records would not sufficiently test provenance and identity handling.

## Additional stress probes

The 27 core cases are supplemented, but not numerically counted, by:

```text
https://ghot.ai/archive/videos/2018-11-25-3
```

for explicit no-transcript behavior,

```text
https://www.gwins.org/cn/milesguo/547.html
```

for mixed timestamp typography and robot-transcription markers, and

```text
https://gettrsearch.com/playvideo/SCHoW40Bx4I_j1sv3RIs
```

for the rule that a GettrSearch opaque route token is not a GETTR platform ID.

## Coverage intentionally not fabricated

Two desired Pilot categories remain evidence-gated:

1. a demonstrable GettrSearch-discovered item absent from a bounded GWINS/GHOT search;
2. a demonstrable `GWINS-only` or `GHOT-only` livestream.

The public GettrSearch static page currently fails to expose durable item metadata, and an unsuccessful search is not proof of absence. P6 must preserve bounded search evidence before adding an `only` label.

## P6 handoff contract

Each collector must process only its assigned nine cases and write source-backed records under the project's Git-tracked data layout. For every case:

1. fetch the seed page at low request rate;
2. preserve seed source/page ID and raw source URLs;
3. discover external media/archive links without bypassing controls;
4. normalize actual target URL identities with `scripts/identity_match.py`;
5. search the other archive sources using date, platform ID and source links;
6. record match candidates and evidence;
7. assign a canonical `LIVE_YYYYMMDD_NNN` only after identity confirmation;
8. preserve transcript provenance (`curated`, `asr`, `mixed/unverified`) rather than flattening it;
9. do not invent missing end times, durations, platform IDs or source absence;
10. leave ambiguous cases `needs_review`.

The three P6 tasks may now execute in parallel without selecting overlapping Pilot cases.

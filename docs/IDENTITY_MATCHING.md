# Miles-Guo_public_archive Identity Matching

Project: `Miles-Guo_public_archive`  
Task: `P4-IDENTITY-RULES`  
Rule version: `identity-v1`  
Verified: `2026-09-13`

## Purpose

This document defines the reproducible rule for deciding whether two source records describe the same underlying livestream/video item.

The archive invariant remains:

```text
one underlying livestream -> one canonical LIVE_YYYYMMDD_NNN
one canonical livestream -> many source records
```

A source URL, GHOT slug, GWINS numeric page ID, GettrSearch route token, date or title is never by itself a canonical `live_id`.

## Core safety rule

Prefer false negatives over false positive merges.

A missed match can be reviewed later. A false merge contaminates transcripts, timestamps, source provenance and downstream search results, so weak evidence must never force two records into one livestream.

## Evidence hierarchy

### Tier A — direct identity evidence

The strongest evidence is an exact stable identity exposed by the actual target URL:

```text
same GETTR streaming ID
same GETTR post ID
same Rumble item ID
same YouTube video ID
```

If two archive records expose the same normalized platform item identity, `identity-v1` assigns:

```text
match_score = 1.00
decision = auto_merge
```

unless a hard verified conflict is also present, in which case the pair becomes `needs_review` rather than silently merging.

A direct cross-reference between archive pages is also strong evidence. Example: a GHOT record explicitly linking the exact GWINS detail URL being compared receives:

```text
match_score = 0.98
decision = auto_merge
```

again subject to hard-conflict review.

### Tier B — fallback content evidence

When no exact shared platform identity or direct archive cross-reference exists, score only independently observable evidence:

| Evidence | Weight |
| --- | ---: |
| exact verified/usable `live_date` | 0.25 |
| title similarity >= 0.90 | 0.20 |
| title similarity >= 0.75 | 0.14 |
| title similarity >= 0.60 | 0.08 |
| duration difference <= 5 sec | 0.20 |
| duration difference <= 30 sec | 0.15 |
| duration within 5% | 0.10 |
| transcript/opening-text similarity >= 0.90 | 0.30 |
| transcript/opening-text similarity >= 0.75 | 0.22 |
| transcript/opening-text similarity >= 0.60 | 0.12 |

Fallback auto-merge is deliberately stricter than the raw numeric threshold. It requires all of:

```text
match_score >= 0.85
exact same live_date
transcript/opening-text similarity >= 0.75
no hard conflict
```

This prevents generic same-day titles from accumulating enough weak evidence to merge automatically.

### Decision thresholds

```text
>= 0.85 + fallback auto-merge gates satisfied -> auto_merge
>= 0.65 but auto-merge gates not satisfied     -> needs_review
< 0.65                                          -> do_not_merge
```

`do_not_merge` means **do not merge automatically with the evidence currently available**. It is not the same as `confirmed_distinct`. Human or later evidence may still upgrade the pair.

`confirmed_merge` and `confirmed_distinct` remain review decisions, not automatic classifier outputs.

## Hard conflicts

Even Tier-A evidence is sent to review when strong verified metadata contradicts it.

`identity-v1` currently flags:

1. both records explicitly mark their `live_date` as verified and those dates differ by more than one day;
2. both records explicitly identify themselves as full-length content and their durations differ by more than 120 seconds **and** more than 20%.

These are review triggers, not automatic proof that records are distinct. Mirrors can be truncated, metadata can be wrong, and publication date is not always livestream date.

Only use the date-conflict rule when the input date is explicitly marked `live_date_verified = true`.

## URL normalization rules

The matcher derives identity from the **actual target URL**, not a website's visible link label.

Supported stable normalization includes:

```text
https://gettr.com/streaming/<id> -> gettr:streaming:<id>
https://gettr.com/post/<id>      -> gettr:post:<id>
YouTube/youtu.be URL             -> youtube:video:<id>
Rumble v... URL                  -> rumble:item:<v-id>
GWINS numeric detail URL         -> gwins:page:<numeric-id>
```

Important: `gettr:streaming:<id>` and `gettr:post:<id>` remain distinct identities unless independent evidence links them.

## Site-specific anti-error rules

### GWINS

- Preserve the numeric page ID as `source_page_id` only.
- Do not use date as a unique key; multiple records exist on the same date.
- Do not infer missing `_N` suffixes on older pages.
- A GWINS page can contain multiple media links. Matching should use the normalized target identities of those links.

### GHOT

- Preserve the exact `YYYY-MM-DD-N` path slug as `source_page_id` only.
- Do not assume the slug ordinal equals the ordinal embedded in the title; a verified page `/2020-10-01-3` has title-side `2020.10.01-2`.
- Normalize platform from the actual external target hostname/URL, not the visible link label. A verified GHOT page displayed a generic `GETTR` label whose target resolved to YouTube.
- Same-day GHOT records remain separate unless stronger evidence connects them.

### GettrSearch

- `/playvideo/<opaque-id>` is a GettrSearch-local route identity only.
- Never promote the opaque route token to a GETTR post/stream/video ID without independent proof.
- Current static analysis supports treating GettrSearch primarily as discovery/backfill evidence until its dynamic payload is reproducibly verified.

## Verified positive test cases

### 2022-05-11

Verified source evidence documents:

```text
GHOT:   https://ghot.ai/archive/videos/2022-05-11-2
GWINS:  https://gwins.org/cn/milesguo/23878.html
GETTR:  https://gettr.com/streaming/p19cmxu5e7b
Rumble: https://rumble.com/v5af5v1-20220511-2.html
```

Both GHOT/GWINS candidates expose the same GETTR and Rumble identities in the test fixture.

Expected:

```text
match_score = 1.00
decision = auto_merge
reason = shared_platform_id
```

### 2023-03-14

Verified GHOT evidence links directly to:

```text
https://gwins.org/cn/milesguo/24264.html
```

Expected when comparing that GHOT record to the exact GWINS record:

```text
match_score = 0.98
decision = auto_merge
reason = direct_cross_reference
```

## Verified/structural negative tests

### Same date is not identity

Compare:

```text
https://ghot.ai/archive/videos/2023-03-12-1
https://ghot.ai/archive/videos/2023-03-12-2
```

With only the shared date available, expected:

```text
match_score = 0.25
decision = do_not_merge
```

This explicitly prevents `one date = one livestream` logic.

### GettrSearch route token is not a GETTR ID

A GettrSearch route such as:

```text
https://gettrsearch.com/playvideo/SCHoW40Bx4I_j1sv3RIs
```

does not become identical to a hypothetical GETTR URL merely because the same token string is inserted there.

Expected without independent evidence:

```text
match_score = 0.00
decision = do_not_merge
```

## Reproducible implementation

Implementation:

```text
scripts/identity_match.py
```

Test fixtures:

```text
tests/identity_matching_cases.json
```

Run:

```bash
python scripts/identity_match.py --cases tests/identity_matching_cases.json
```

The command exits non-zero if any expected decision fails.

A pair can also be scored directly:

```bash
python scripts/identity_match.py left.json right.json
```

The output includes:

```text
rule_version
match_score
decision
evidence[]
conflicts[]
```

## Persistence contract

The schema already contains `source_match_candidates` with `match_score`, `evidence_json`, `decision`, review metadata and notes. Persist the full explainable evidence; never keep only the numeric score.

Recommended `evidence_json` content includes:

```json
{
  "rule_version": "identity-v1",
  "evidence": [
    {"type": "shared_platform_id", "values": ["gettr:streaming:p19cmxu5e7b"]}
  ],
  "conflicts": []
}
```

Before canonical `live_id` assignment, raw collector candidates may retain equivalent matching evidence in Git-tracked JSON/JSONL. The final canonical record must not depend on an untracked in-memory merge decision.

## Canonical live ID assignment

Matching and canonical ID assignment are separate operations.

After a group is confirmed to represent one livestream:

1. choose/confirm the real livestream date;
2. inspect already assigned `LIVE_YYYYMMDD_NNN` values for that date;
3. assign exactly one canonical ID to the confirmed group;
4. attach all source records to that ID;
5. preserve every source URL, page ID, platform ID and matching evidence;
6. never renumber an existing canonical livestream merely to make source ordinals look tidy.

Source-side `_1`, `_2`, GHOT suffixes and GettrSearch route IDs never determine the canonical `NNN` by themselves.

## Review policy

A reviewer must be able to answer **why** a pair merged.

Never approve a pair only because:

- titles look similar;
- dates match;
- both mention the same topic/person;
- source ordinals happen to match;
- a GettrSearch opaque ID resembles another token;
- two pages are near each other in a site archive.

For `needs_review`, preserve the unresolved pair and evidence instead of choosing the more convenient interpretation.

## Pilot implication

`identity-v1` is sufficiently conservative for Pilot selection and collection. It supports high-confidence automatic consolidation when sources share exact external identities or explicit cross-links, while forcing weak/contradictory cases into review.

Any threshold/weight change after Pilot evidence must receive a new rule version; do not silently reinterpret previously stored scores.

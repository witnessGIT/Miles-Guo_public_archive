# C2/C3 Sample Chain

This document records the first conservative end-to-end sample after C1 was
made repeatable.

## Purpose

The sample proves that the archive can move from:

```text
source_candidates
→ live_videos
→ live_sources
→ media_assets
→ transcript_versions
→ live_work_items
```

It is not a collection freeze and not full C2 completion for every discovered
candidate.

## Promoted Sample

The sample promotes three clear GWINS candidates from `list_2_68`:

| Candidate | Canonical live |
|---|---|
| `SC_GWINS_LIST2_68_20171102` | `LIVE_20171102_001` |
| `SC_GWINS_LIST2_68_20171023_1` | `LIVE_20171023_001` |
| `SC_GWINS_LIST2_68_20170924` | `LIVE_20170924_001` |

Each promoted live has:

- one GWINS source page
- one YouTube mirror source when visible
- one Rumble mirror source when visible
- media asset rows for visible video links
- one source-original transcript version from the GWINS detail page text
- verification records that remain `unverified`
- generated live work items for later ordinary processing stages

## Verification Position

This sample does not assert playback verification.

The GWINS page text and visible external video links support source inventory
only. Later stages must still perform text checking, audio/video playback
checking, and final acceptance.

## Next Work

Ordinary agents should keep doing C1 source discovery.

Higher-skill agents should use this sample shape when implementing a full C2
promotion script.

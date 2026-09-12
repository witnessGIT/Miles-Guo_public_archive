# PILOT-L006 Audit

Case: `PILOT-L006`  
Live: `LIVE_20230122_001`

## Evidence checked

The alignment readiness record preserves three direct GHOT public ASR/time-axis anchors at 03:04, 03:13, and 03:35. It explicitly identifies the case as an ASR-only timing scaffold and leaves playback verification for downstream real-media review.

## Playback audit result

This worker environment cannot independently execute and observe decoded media playback. No timing-error value can therefore be measured and no segment may be promoted to `playback_verified=1`.

- candidate anchors inspected: 3
- qualifying real playback checks: 0
- timing accuracy measured: no
- counts toward Pilot-60: no
- audit outcome: `blocked_no_playback`

The three public transcript/time-axis anchors remain useful navigation evidence, but they are not substitutes for the Pilot's required real playback checks.

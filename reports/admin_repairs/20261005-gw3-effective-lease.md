# GW3 continuation: restore the effective 10-hour claim lease

Recorded: 2026-10-04T16:12:44Z / 2026-10-05 Asia/Tokyo.
Agent: `agent-20261004T125231Z-chat-c2-gw3`.
Authenticated GitHub login freshly verified: `witnessGIT` (admin under current AGENT_PERMISSIONS.json).
Fixed batch: `REVIEW-BATCH-20261004T125231Z-chat-gw3`; entry mode remains ordinary_chat. Current claims are retained, not migrated or topped up.

## Business result

**This continuation adds zero completed C2 reviews. The existing batch remains 12/20 completed, eight unresolved.** No candidate, canonical, media asset, review artifact or completion record is modified. Diagnostic work, this mitigation and tests do not count as candidate completions.

Current-state comparison found no change to these eight from the previous checkpoint through base commit `8b6e5f7e337ae1ff2a55d10a9b6d09f5d2ffe75e`. No open PR reservation was returned by the current open-PR read. The original eight claim files were read individually; their reconstructed bytes were verified against the fetched Git blob hashes before adding one field.

## Defect and minimal correction

`claim_expired()` in next_task.py (blob `e9b21dd6a494480acb22bfa348b9fe421365495d`) reads `static_claim_lease_hours`, defaulting to 24. Our ordinary-chat claims only recorded `review_claim_timeout_hours: 10`. The candidate-state display nonetheless reported a ten-hour expiry. The script-created C2 claims already include both fields.

This changeset adds **only `static_claim_lease_hours: 10`** to each of the eight still-uncompleted claims. It does not reset `claimed_at`, renew a lease, release a claim early, change ownership, replace members, or modify the twelve completed records.

All retain claimed_at `2026-10-04T12:52:31Z`.

- Intended and corrected effective expiry: **2026-10-04T22:52:31Z / 2026-10-05 07:52:31 JST**.
- Old actual fallback expiry: **2026-10-05T12:52:31Z / 2026-10-05 21:52:31 JST**.

The earlier handoff stated the intended deadline without verifying that these hand-created claims used the scheduler's effective field. This report corrects that oversight. The fix removes an unintended fourteen-hour over-reservation, not any evidence requirement.

| Candidate suffix | Position | Original claim blob |
|---|---:|---|
| 20230103_1 | 2 | 6951e6ec47f20a925f03cbc6a7be02a94af39e3d |
| 20221231_1 | 6 | 18c35d0a313a27cacb79e03d2643ad1589c7dca0 |
| 20221230_1 | 7 | d6304a537f5a7f971752babf8e056861bc4873dc |
| 20221206_2 | 10 | a897aa94b3fdcc4823db3dd91070d6d72945850d |
| 20221205_1 | 11 | ace02ac6c8d674e336e0ba4814f7a3201b074b76 |
| 20221201_1 | 17 | 74ad9c80921c5929fbb9c7ad548ac3d84b6c3669 |
| 20221129_1 | 19 | 8c86163af680b62950a6003eb0204b83045ad47c |
| 20221128_1 | 20 | 0277782be53527a13d1c7bf1efbd388874e72999 |

Prefix `C2-REVIEW-SC_GWINS_LIST2_3_`, generation R001. No other agent's claims are changed.

## Executable checks

An isolated local reproduction used the exact current parse_timestamp/claim_expired functions, not a full checkout. For each of the eight original files, the old function returned false at the ten-hour boundary. After the one-field correction it returned false one microsecond before, true at, and true one microsecond after: **24 corrected-boundary assertions passed**. Original blob hashes and absence of other field changes were also asserted. At twelve hours the original sample remained active and the corrected sample expired.

Two new repository regression tests check the still-uncompleted members of this fixed batch using the actual next_task module, including the exact boundary and twelve-hour case. They exclude valid completed or released history and skip once no pending members remain. The test source compiles locally. Full repository tests and evidence/database gates must be observed in CI; this document does not claim an unobserved CI run passed.

## Remaining evidence boundary

The eight retain their earlier candidate-specific evidence gaps. Rechecking December 5 against the preceding December 4 small-video notice did not turn ambiguous publishing wording into an explicit recording declaration. The active GHOT near-January records instead identify a different January 3 Hpay meeting item and a sparse late-2022 discovery gap; neither proves identity or non-live origin for our eight. GETTR-search candidate samples did not settle the question. An incomplete code-search response is not absence evidence, and public-page access errors are not deletion or non-live evidence.

The prior per-candidate assessment remains in `reports/candidate_review_handoffs/REVIEW-BATCH-20261004T125231Z-chat-gw3-20261004T153429Z.md`. No source statement was treated as fact about later outcomes; no media, playback, transcription or segmentation was performed.

The scoped origin-adjudication boundary remains HUMAN_DECISION_REQUIRED on present evidence, not a request for renewed permission and not repository-wide NO_ELIGIBLE_WORK. This batch is not CHAT_BATCH_COMPLETE or PROJECT_COMPLETE. After expiry, use fresh-generation claiming rather than relying on this handoff as ownership.

The generic scheduler/display discrepancy remains tracked in `coordination/bug_reports/BUG_20261004T161244Z_C2_effective_lease_field.json`. This patch mitigates the eight owned records only; no global census or global fix is claimed. No background task was scheduled.

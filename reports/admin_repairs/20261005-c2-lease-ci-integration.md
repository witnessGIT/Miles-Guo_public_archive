# Miles-Guo_public_archive — C2 lease repair integration checks

Agent: `agent-20261004T125231Z-chat-c2-gw3`; authenticated administrator `witnessGIT`.
PR #8 supplements `reports/admin_repairs/20261005-c2-effective-lease-contract.md`.
This report records observed failures and their handling; it does not pre-assert a later successful run.

## Full-suite result and concurrent database conflict

Run `37246332816`, job `111564870783`, tested the synthetic merge `03311dd9ff22aa1759984f2d8a36181908aadf09`. Its real log reports **108 tests passed**, including all sixteen new lease regressions, followed by evidence validation PASS (134 existing completions, 12 batches). SQLite preflight then failed on duplicate YouTube source and media-asset primary keys between the July 11 `_001` and `_002` entries. These counts are existing-record checks, not new C2 work.

A proposed internal-key repair was isolated as PR #9. Before merging, fresh main reads showed a concurrent contribution had removed the conflicting `_002` YouTube source, asset and match entries. I closed PR #9 without merging instead of overwriting the concurrent correction. Its proposed internal IDs and repair report never reached main and are not counted as my completed repair. Observed corrected blobs: sources `b21fdc896a4f7a7799c8124b2fd2b0a46710ed70`, assets `0bdbb97cf70ba8da6ee311bcaba99d4ab6149cb1`, matches `491306d53e9890ad8f5513233567c35dbe41b415`. The remaining Rumble references were preserved. The lease PR must be retested against the corrected main; no database gate is waived.

## Playback-control fixture correction

Run `37246332709`, job `111564870643`, passed compilation, audit-gate output-contract, repository-service detection and the worker/admin status-contract checks. It then failed the synthetic ordinary-worker playback regression: the fixture mocked queue/gate/capability/completion inputs but omitted `project_status.load_workflow`, so it accidentally read the real current `PHASE_1_COLLECTION` state. Production `build_status` correctly hid playback in that phase, contradicting the fixture's later-stage expectation.

The correction sets an explicit in-memory post-collection phase in all three playback-priority fixtures. It does not change `coordination/WORKFLOW.json`, `project_status.py`, phase permissions, queue data, claims or completion records. Existing assertions and live-state integrity checks remain in place. The first fixture additionally switches back to Phase 1 and verifies that even a synthetic passing playback gate cannot enable playback or gate sealing.

Two unit tests independently exercise the real status function with isolated inputs: post-collection repository playback is available without local media tools; Phase 1 never reads the synthetic playback targets/gate and cannot authorize processing even when a passing gate is supplied. Mocks are confined to test processes and restored after each test.

The complete workflow baseline was reconstructed and verified against Git blob `506e38d424199ba5f4acdd185112c42e0beb2f3d` before the narrow edit. Patched YAML parsed and every embedded Python block compiled locally, as did the new test module. Full runtime success must be confirmed from the next GitHub Actions run; syntax checks are not a substitute for execution.

## Scope remains unchanged

This continuation adds **zero C2 candidate-review completions**. The active GW10 fixed batch remains 12/20 completed with eight origin gaps; its original ten-hour deadline is not renewed. No media was downloaded or played. PR #9 is withdrawn, not merged. The generic lease repair and CI-fixture correction count as maintenance only. No project, batch or playback gate is declared complete.

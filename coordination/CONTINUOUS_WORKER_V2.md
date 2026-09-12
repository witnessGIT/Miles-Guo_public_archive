# Miles-Guo_public_archive Continuous Worker v2

Project: `Miles-Guo_public_archive`

Policy: `continuous-worker-v2`

Claim protocol: `claim-protocol-v2`

## Goal

New Agent work in this repository uses a continuous self-service worker model:

```text
ENTER REPOSITORY
  -> DISCOVER ELIGIBLE WORK
  -> CLAIM
  -> EXECUTE
  -> VALIDATE
  -> COMMIT/PUSH OUTPUTS
  -> FINISH / PUBLISH READINESS
  -> CLAIM NEXT TASK
  -> REPEAT
```

A worker does not intentionally stop after one successful batch while other safe eligible work exists. Losing one claim race is also not a stop condition.

## Important platform limitation

Git/GitHub can coordinate work and make the next task discoverable, but the repository cannot force a suspended ChatGPT/Work/Codex session to wake itself after the host platform has stopped or suspended that session.

Therefore `continuous-worker-v2` guarantees **continuous behavior while the Agent session is running**, plus durable resume/takeover state in Git. It does not claim that Git can resurrect a terminated or suspended Agent process.

For local/CLI workers whose host permits a long-running process, `scripts/next_task.py --watch` can wait for new eligible work. Host suspension, account sleep, network termination, tool-budget exhaustion, or platform lifecycle rules can still stop that process.

## Effective scope / grandfather rule

This policy applies to **new task claims**.

Existing valid claims created under a previous workflow remain valid and must not be interrupted, renamed, reassigned, or duplicated merely to migrate them.

A claim without a `workflow_mode` field is treated as a grandfathered legacy claim. A new claim contains:

```json
{
  "workflow_mode": "continuous-worker-v2",
  "claim_protocol": "claim-protocol-v2",
  "continue_after_finish": true
}
```

## Default stop conditions

A v2 Agent continues claiming tasks until one of these conditions is true:

1. **PROJECT_COMPLETE** — the currently authorized project phase has passed its final gate and no authorized work remains.
2. **USER_RECALL** — the user explicitly asks the Agent to stop, return, pause, or change mission.
3. **NO_ELIGIBLE_WORK** — all unfinished work is currently owned, blocked by unresolved prerequisites, or requires unavailable external state.
4. **HUMAN_DECISION_REQUIRED** — proceeding would require guessing on identity, provenance, schema migration, access policy, destructive conflict resolution, or another decision explicitly reserved for the user/reviewer.
5. **SAFETY_OR_ACCESS_BLOCK** — work would require bypassing login, CAPTCHA, paywall, access control, DRM, or another prohibited action.
6. **GITHUB_WRITE_ERROR** — only after `coordination/CLAIM_PROTOCOL_V2.md` has ruled out a normal claim race and bounded fresh retries still fail.
7. **HOST_STOP** — the execution platform stops/suspends the Agent, tool context is exhausted, or the runtime cannot continue. This is not a project-level completion state.

Finishing one task, finishing one batch, or losing one claim race is **not** a stop condition.

`CLAIM_RACE_LOST` must be followed by refresh + another eligible claim attempt.

## Claim-race recovery is mandatory

Read `coordination/CLAIM_PROTOCOL_V2.md` before creating new claims.

For GitHub API Agents, HTTP `422` from `create_file` is not automatically a repository write outage.

The Agent must first fetch the exact attempted path:

```text
coordination/claims/<TASK_ID>.json
```

If the file exists, another Agent won the atomic race. Classify `CLAIM_RACE_LOST`, refresh repository state, and try another eligible task.

If the file does not exist, refresh repository state and use bounded retries. Only after the exact path remains absent and fresh retries continue to fail may the Agent classify `GITHUB_WRITE_ERROR`.

A single 422 may never be used as the sole reason to say the execution chain must stop at the claim boundary.

## No-sleep rule

After a successful `--finish`, a v2 Agent must immediately refresh repository state and attempt another claim:

```bash
python scripts/next_task.py --claim --agent-id <same-agent-id>
```

If the preferred task is claimed concurrently, the worker must try another eligible candidate instead of waiting for that task owner.

`scripts/next_task.py` disperses Agents across same-priority candidates using a stable `agent_id` hash and can try multiple local candidates in one claim cycle.

If no task is eligible after refresh, the Agent should report the concrete blocking reason from repository state. It must not invent work just to stay active.

## Optional watch mode

For a runtime that can remain alive safely:

```bash
python scripts/next_task.py \
  --watch \
  --claim \
  --agent-id agent-<UTC>-<random> \
  --poll-seconds 60
```

Behavior:

- re-scan Git-backed queue state periodically;
- when a task becomes eligible, claim it and exit the watcher so the Agent can execute the task;
- `Ctrl+C` or host termination recalls/stops the waiting process;
- never bypass an existing claim;
- never convert a blocked task into an eligible one by assumption.

Watch mode is an availability aid, not a promise that the hosting platform will keep a process alive forever.

## Streaming work instead of global barriers

New work should normally be decomposed by one livestream / Pilot case or a very small non-overlapping micro-batch.

Preferred progression:

```text
COLLECT + IDENTITY
        -> collection readiness marker
ALIGN
        -> alignment readiness marker
AUDIT
        -> audit readiness marker
```

Each case advances independently. Aggregate tasks are gates/reports, not prerequisites that unnecessarily serialize unrelated case work.

## Existing Agents remain safe

Migration rules are deliberately non-destructive:

- do not delete or rewrite existing claims;
- do not create streaming collection tasks that overlap a valid legacy batch claim;
- completed legacy records remain authoritative history;
- v2 applies at the **next claim boundary**, not retroactively inside work already in progress.

## Resume and takeover

Because a host can suspend an Agent, durable state must always be in Git:

```text
coordination/claims/
coordination/completed/
coordination/ready/
data/
reports/
```

A new Agent can resume the project without chat memory by reading repository state and running `scripts/next_task.py --list`.

If an old claim appears stale, use the documented stale-claim checks in `coordination/README.md`. Never steal a claim merely because its Agent is not visible in chat.

## Project-end behavior

`continuous-worker-v2` does not authorize work beyond the current phase.

For the current Pilot, `P10-PILOT-DECISION` remains the whole-Pilot decision gate. A worker must not silently begin `FULL_ARCHIVE` unless the repository/user explicitly authorizes it after the Pilot evidence supports that transition.

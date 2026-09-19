# Miles-Guo_public_archive Claim Protocol v2

This protocol is mandatory for every **new** task claim under `continuous-worker-v2`.

Its purpose is to prevent normal multi-Agent contention on a rapidly changing `main` branch from being misreported as a repository-wide GitHub write failure.

## Durable arrival order

The project does not attempt to infer which chat window opened first. That timestamp is not
shared or trustworthy. “First entered protocol” has one precise, testable meaning:

```text
direct-write Agent -> first successful atomic claim visible on main
no-write Agent     -> first valid open task PR visible to the repository
```

This durable entry owns the task. All later Agents refresh and choose another eligible task. They
must not wait for the user, edit the owner’s files, or keep retrying an already occupied task.
`scripts/agent_entry.py` creates/reuses a stable local Agent ID and spreads equal-priority
candidates; `scripts/next_task.py` and `scripts/playback_queue.py` fall through local claim
collisions before reporting a fresh-state race.

## Core rule

A failed claim attempt is **not** a stop condition by itself.

For an ordinary chat repository-file creation, both of these are normally retryable classification events rather than immediate outages:

- HTTP `422` — often an already-exists / atomic claim race;
- HTTP `409` — often a branch/update conflict because `main` moved between read and write.

Neither status alone is sufficient to classify `GITHUB_WRITE_ERROR`.

For claim creation, classify the result as follows:

```text
create coordination/claims/<TASK_ID>.json
        |
        +-- success --> fetch exact claim --> owner matches --> CLAIM_SUCCESS
        |
        +-- 422 / 409 / already-exists-or-branch-race-like failure
                |
                +-- fetch exact claim path from fresh main
                        |
                        +-- file exists --> CLAIM_RACE_LOST
                        |                  --> refresh queue
                        |                  --> try another eligible task
                        |
                        +-- file absent --> refresh main / task state
                                           --> short backoff
                                           --> retry with bounded attempts
                                           --> only then consider write failure
```

A `409` with an absent target path usually means the branch changed during the write attempt. Refreshing and retrying against the latest `main` is the correct response; force-writing or overwriting concurrent work is prohibited.

## Error classes

### `CLAIM_SUCCESS`

The new claim file is visible on `main` and belongs to the current Agent.

Only after this state may the Agent perform expensive or business-data work for that task.

### `CLAIM_RACE_LOST`

Use this classification when the attempted claim did not succeed and, after refreshing, the exact path now exists:

```text
coordination/claims/<TASK_ID>.json
```

This normally means another Agent won the atomic-create race.

Required behavior:

1. do not overwrite the existing claim;
2. do not edit business data for that task;
3. refresh `claims/`, `completed/`, `ready/` and eligible tasks;
4. try another eligible task immediately;
5. continue until a claim succeeds or no eligible work remains.

`CLAIM_RACE_LOST` is **never** a reason to put the worker to sleep.

It is also never an acceptable final chat response. The worker must perform step 4 before
reporting: “will choose another task” without a fresh durable claim/reservation is an incomplete
entry protocol.

### `BRANCH_RACE_RETRY`

Use this transient classification when:

- the claim write returned `409` (or an equivalent moving-branch conflict);
- the exact target claim path is still absent;
- `main` has advanced or repository state changed since the read used to prepare the write.

Required behavior:

1. refresh `main` and the eligible-task state;
2. confirm the task is still eligible;
3. use a short backoff;
4. retry the create against fresh state;
5. do not force-push or overwrite unrelated concurrent commits.

This is **not** a stop condition.

### `GITHUB_WRITE_ERROR`

This classification is allowed only after all of the following are true:

1. the attempted create failed;
2. the exact target claim path does **not** exist after refresh;
3. repository and task state were refreshed again;
4. the task is still eligible;
5. up to 3 bounded retries with fresh state and short backoff still fail;
6. the failure cannot be explained by another Agent winning the claim race, a moving `main`, a stale local checkout, or the task becoming completed/claimed between reads.

Do not retry aggressively.

## Ordinary chat Agent procedure

Using the repository file-creation tool already available in the chat:

1. compute the eligible task set from current Git state;
2. distribute the starting candidate using the Agent ID when possible instead of always picking the first task;
3. attempt to create `coordination/claims/<TASK_ID>.json`;
4. if creation succeeds, fetch the exact new claim and verify ownership;
5. if creation returns `422` **or `409`**, immediately fetch that exact claim path from fresh `main`;
6. if it exists, classify `CLAIM_RACE_LOST` and move to another candidate;
7. if it does not exist, refresh `main`, `completed/`, `ready/`, and task eligibility;
8. if the task is still eligible, short-backoff and retry at most 3 times;
9. only after those bounded checks fail may the Agent report `GITHUB_WRITE_ERROR`.

A single `422` or `409` MUST NOT produce a message such as "the execution chain must stop at the claim boundary".

## Candidate dispersion

When several tasks have equal or similar priority, workers should not all start from index 0.

The task runner derives a stable starting offset from `agent_id` and rotates the eligible task list. This preserves priority bands while reducing synchronized collisions.

A worker may try multiple currently eligible candidates in one claim cycle. Default maximum attempts are bounded by the current eligible task count and a configurable limit.

## Stop conditions after claim attempts

A worker may stop at the claim boundary only when one of these is true:

- there is genuinely no eligible unclaimed work after refresh;
- the user recalled the worker;
- a human decision is required;
- safety/access rules block all eligible work;
- a true `GITHUB_WRITE_ERROR` has been established using the checks above;
- the host platform terminates the session.

A lost claim race or moving-branch `409` is not on this list.

## Renewable Playback claim leases

New `P9-PLAYBACK-*` claims contain a six-hour renewable lease. Successful request and acceptance
commands renew it automatically. A continuing chat Agent can explicitly renew it with:

```bash
python scripts/playback_queue.py --heartbeat <CASE_ID> --agent-id <same-agent-id>
```

Claims created before lease support receive a conservative 24-hour lease measured from
`claimed_at`. An expired claim is no longer an active reservation, but it may not be overwritten
or deleted manually. After refreshing `main`, an ordinary worker may execute:

```bash
python scripts/playback_queue.py --reclaim-expired <CASE_ID> --agent-id <new-agent-id>
```

The command must verify expiration, preserve the old ownership/timestamps under
`coordination/playback_attempts/`, and create a fresh claim lease in the same commit. A claim whose
lease has not expired remains protected. Push races are handled by the normal refresh/retry rules.

## Compatibility

This protocol never takes over an active claim. The only takeover path is the bounded,
evidence-preserving expired-lease command above.

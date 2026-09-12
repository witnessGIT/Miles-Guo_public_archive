# Miles-Guo_public_archive Claim Protocol v2

This protocol is mandatory for every **new** task claim under `continuous-worker-v2`.

Its purpose is to prevent a normal multi-Agent claim race from being misreported as a repository-wide GitHub write failure.

## Core rule

A failed claim attempt is **not** a stop condition by itself.

In particular, a GitHub Contents API `create_file` response of HTTP `422` MUST NOT immediately be classified as `GITHUB_WRITE_ERROR`.

For claim creation, first classify the failure:

```text
create coordination/claims/<TASK_ID>.json
        |
        +-- success --> CLAIM_SUCCESS --> do the task
        |
        +-- 422 / already-exists-like failure
                |
                +-- fetch exact claim path
                        |
                        +-- file exists --> CLAIM_RACE_LOST
                        |                  --> refresh queue
                        |                  --> try another eligible task
                        |
                        +-- file absent --> refresh repository state
                                           --> retry with bounded attempts
                                           --> only then classify write failure
```

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

### `GITHUB_WRITE_ERROR`

This classification is allowed only after all of the following are true:

1. the attempted create failed;
2. the exact target claim path does **not** exist after refresh;
3. repository state was refreshed again;
4. a bounded retry still fails;
5. the failure cannot be explained by another Agent winning the claim race, a stale local checkout, or the task becoming completed/claimed between reads.

Recommended bound: 3 retries with fresh repository state between retries.

Do not retry aggressively; use a short backoff.

## GitHub API Agent procedure

For Agents using GitHub `create_file` directly:

1. compute the eligible task set from current Git state;
2. distribute the starting candidate using the Agent ID when possible instead of always picking the first task;
3. attempt to create `coordination/claims/<TASK_ID>.json`;
4. if creation succeeds, fetch the new claim once and verify ownership;
5. if creation returns `422`, immediately fetch that exact claim path;
6. if it exists, classify `CLAIM_RACE_LOST` and move to another candidate;
7. if it does not exist, refresh repository state and retry at most 3 times;
8. only after the bounded checks fail may the Agent report `GITHUB_WRITE_ERROR`.

A single `422` MUST NOT produce a message such as "the execution chain must stop at the claim boundary".

## Local git / filesystem Agent procedure

`scripts/next_task.py --claim` uses exclusive local file creation and now rotates across multiple eligible candidates.

If local creation raises `FileExistsError`, the script treats it as `CLAIM_RACE_LOST` and tries the next candidate instead of exiting after the first collision.

After local claim creation, the Agent must still commit and push immediately. If the push loses a remote race:

1. remove only the losing local claim file;
2. refresh/pull `main`;
3. run the claim command again;
4. do not touch the winning Agent's claim.

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

A lost claim race is not on this list.

## Compatibility

This protocol does not modify, delete, rename, or take over any existing valid claim.

It applies to new claim attempts only.

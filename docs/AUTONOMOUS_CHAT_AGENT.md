# Autonomous Chat and Execution Agent Contract

This document defines equivalent durable entry transports for a local Git Agent and for an
ordinary chat Agent with GitHub file/Contents API write tools. Repository history contains both
`codex-*` and `gpt*` worker identities, so lack of `git pull` is not treated as lack of repository
write capability.

## User contract

The user may provide only:

```text
进入 witnessGIT/Miles-Guo_public_archive，开始执行。
```

The Agent reads `AGENTS.md`, detects its available transport, and never asks the user to choose.

## Transport A — local Git workspace

A Git-capable Agent runs:

```bash
python scripts/agent_entry.py --mode auto
```

The Agent must not ask the user to select a task, select direct/PR mode, repeat project rules, or
approve ordinary continuation.

## Transport B — GitHub API only (no clone or pull)

An ordinary chat Agent with repository file-write tools:

1. Reads the minimal fresh-entry set from `main`: `AGENTS.md`, `coordination/WORKFLOW.json`, the
   current Phase-1 boundary file, and only the candidate-specific claim/completion paths. It does
   not enumerate all historical queue records before entry.
2. Creates one stable `agent-<UTC>-<random>` identity for the conversation.
3. Computes eligibility using priority, dependencies, completions and active claims. During
   `PHASE_1_COLLECTION`, open C1 source boundaries take precedence and Playback is disabled.
4. Atomically creates `coordination/claims/<TASK_ID>.json` on `main` with the GitHub file/Contents
   API. The GitHub commit may be attributed to the authenticated account; the JSON `agent_id`
   records the actual worker identity.
5. Fetches the exact path from fresh `main`. Work begins only if its `agent_id` matches.
6. On 409/422, fetches the exact path. Another owner means `CLAIM_RACE_LOST` and immediate
   selection of another task; an absent path means refresh and at most three bounded retries.
7. Performs the bounded public-source task and publishes only worker-allowed business files with
   the same GitHub API. Where no local runtime exists, repository CI supplies executable checks.
8. Publishes completion, updates its claim status, refreshes `main`, and selects the next task.

Once step 5 succeeds, the Agent reads the full governance and task-specific instructions before
step 7. This ordering preserves the quality contract without consuming the pre-claim tool window.

API-only workers must not modify protected control-plane paths. A conversation whose available
GitHub tool is genuinely read-only cannot become a durable worker.

## Local-Git entry state machine

```text
clean main checkout
  -> git pull --ff-only
  -> create metadata-only local child commit (without moving the worktree)
  -> git push --dry-run origin <probe-commit>:main
       -> allowed: choose task -> atomic local claim -> commit -> push main
       -> denied: require authenticated gh
                    -> read open PR reservations
                    -> choose unreserved task
                    -> create immutable reservation record
                    -> push fork branch -> open PR
```

Business work begins only after a matching claim is visible on fresh `main`, or a winning PR
reservation is visible for a no-direct-write worker.

## Safety invariants

- Automatic entry starts only from a clean `main`; it never stashes, resets, overwrites, or
  force-pushes user work.
- After refresh, local `main` must equal `origin/main`. An unpublished claim commit therefore
  blocks re-entry instead of allowing the same checkout to claim a second task.
- Direct permission is tested by dry-running a unique metadata-only child commit to `main`.
  Testing an already up-to-date ref would be insufficient because it might not require
  authorization; testing a different branch would not exercise `main` branch protection.
- PR mode fails closed if it cannot inspect open PRs.
- Open PRs carrying `TASK_ID:` or `[TASK ...]` reserve that task.
- After PR creation, the entry runner re-reads open PRs. The lowest PR number wins a concurrent
  reservation race; a losing PR is closed and the runner tries another candidate.
- A PR reservation is an immutable record under `coordination/pr_reservations/` and contains no
  fabricated business output.
- A failed publish is not reported as a successful claim.
- The stable local Agent identity is stored in ignored `.agent_session.json` and reused during the
  same checkout/session.

## Terminal statuses

| Status | Meaning |
|---|---|
| `DURABLE_CLAIM_PUBLISHED` | Direct claim is visible on `main`; work may start. |
| `DURABLE_PR_RESERVATION_PUBLISHED` | Reservation PR exists; work continues on its branch. |
| `NO_ELIGIBLE_WORK` | Fresh main and open PR state expose no compatible task. |
| `AUTOMATION_BLOCKED` | A required safe transport or clean state is unavailable. |
| `PUBLISH_RACE_OR_WRITE_ERROR` | Local claim commit exists but was not published; classify it under Claim Protocol v2. |

`LOCAL_CLAIM_CREATED` and `PR_RESERVATION_REQUIRED` are manual compatibility-mode statuses. They
are not durable authorization to start work. Manual PR mode still fails closed unless it can read
the current open-PR reservation set.

## Continuation and recovery

After publishing task output and completion state, return to `main`, refresh, and run automatic
entry again. Git contains the durable handoff for the next chat Agent. A host can suspend or end a
chat, so no repository can promise an immortal process; it can promise that a later Agent starts
from authoritative state instead of chat memory.

## Local-Git runtime prerequisites

- Git is required in all modes.
- Direct mode uses the credentials configured for the Git remote.
- PR fallback requires an authenticated GitHub CLI (`gh auth status`) and permission to create or
  use the authenticated account's fork.
- Missing direct permission and missing authenticated `gh` is a real access block. The Agent must
  report it rather than silently performing unreserved work.

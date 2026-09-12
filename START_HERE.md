# Miles-Guo_public_archive Agent Entry Point

## External prompt contract

An external Agent does **not** need a copied task specification.

The minimal prompt is sufficient:

```text
进入这个项目并开始工作：
https://github.com/witnessGIT/Miles-Guo_public_archive
```

The repository is the authoritative execution context.

After entering the repository, the Agent must determine everything else from Git state and project files, including:

- project purpose and scope;
- current authorized phase;
- current completed work;
- active claims;
- currently eligible work;
- task priority;
- collection/alignment/audit rules;
- source and naming rules;
- quality gates;
- continuous-worker behavior;
- claim-race handling;
- stop conditions.

Do not ask the user to repeat requirements already stored in the repository.

## Required bootstrap

Read and follow, in order:

1. `AGENTS.md`
2. `coordination/WORKFLOW.json`
3. `coordination/CONTINUOUS_WORKER_V2.md`
4. `coordination/CLAIM_PROTOCOL_V2.md`
5. `coordination/README.md`
6. `coordination/WORK_QUEUE.jsonl`
7. `docs/CURRENT_TASK.md`
8. `docs/PROJECT_REQUIREMENTS.md`
9. `docs/NAMING_AND_WORKFLOW.md`
10. current `claims/`, `completed/`, `ready/`, data and reports relevant to the next task

Then immediately discover work with:

```bash
python scripts/next_task.py --list
```

Claim an eligible task, execute it, validate it, commit/push it, finish it, then claim the next eligible task.

Under `continuous-worker-v2`, completing one task or batch is not a stop condition. Continue until a documented stop condition in the repository applies.

## Mandatory claim-race behavior

A failed atomic claim is not automatically a GitHub outage.

For Agents using GitHub `create_file` directly:

```text
create claim
   |
   +-- success --> work
   |
   +-- HTTP 422 --> fetch exact claim path
                       |
                       +-- exists --> CLAIM_RACE_LOST --> refresh --> try another task
                       |
                       +-- absent --> fresh bounded retry --> only then consider GITHUB_WRITE_ERROR
```

A single `422` MUST NOT stop the worker or produce "the execution chain must stop at the claim boundary".

If another Agent won the claim race, do not overwrite the claim and do not touch that task's business data. Refresh state and claim another eligible task immediately.

See `coordination/CLAIM_PROTOCOL_V2.md` for the authoritative procedure.

## Repository authority

If an external prompt only says to enter this repository and start work, treat that as authorization to execute the **currently authorized repository phase**, not as authorization to bypass project gates or begin an unauthorized later phase.

Current and future Agents must prefer repository state over stale chat summaries or old copied prompts.

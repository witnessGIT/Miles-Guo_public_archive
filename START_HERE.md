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
- stop conditions.

Do not ask the user to repeat requirements already stored in the repository.

## Required bootstrap

Read and follow, in order:

1. `AGENTS.md`
2. `coordination/WORKFLOW.json`
3. `coordination/CONTINUOUS_WORKER_V2.md`
4. `coordination/README.md`
5. `coordination/WORK_QUEUE.jsonl`
6. `docs/CURRENT_TASK.md`
7. `docs/PROJECT_REQUIREMENTS.md`
8. `docs/NAMING_AND_WORKFLOW.md`
9. current `claims/`, `completed/`, `ready/`, data and reports relevant to the next task

Then immediately discover work with:

```bash
python scripts/next_task.py --list
```

Claim an eligible task, execute it, validate it, commit/push it, finish it, then claim the next eligible task.

Under `continuous-worker-v2`, completing one task or batch is not a stop condition. Continue until a documented stop condition in the repository applies.

## Repository authority

If an external prompt only says to enter this repository and start work, treat that as authorization to execute the **currently authorized repository phase**, not as authorization to bypass project gates or begin an unauthorized later phase.

Current and future Agents must prefer repository state over stale chat summaries or old copied prompts.

# Miles-Guo_public_archive Agent Permissions

Policy version: `agent-permissions-v1`

This repository separates **management/admin Agents** from **worker Agents**.

## Role resolution

Administrative GitHub login:

```text
witnessGIT
```

An Agent may act as `admin` only when:

1. the authenticated GitHub login is verified as exactly `witnessGIT`; or
2. the repository owner explicitly grants that Agent an admin exception in the current interaction.

If identity cannot be verified, the Agent MUST act as `worker`.

## Admin Agent

Admin Agents may:

- fix repository bugs;
- change `scripts/`, `schema/`, `.github/`, workflow/claim logic and coordination policy;
- resolve schema/data-contract incompatibilities;
- change task orchestration;
- resolve bug reports;
- perform normal business tasks when useful.

Admin Agents should review open bug reports before normal business work when a reported bug blocks repository correctness or other Agents.

## Worker Agent

Worker Agents exist to perform claimed project tasks, not to redesign or repair the project control plane.

A worker may:

- read all repository rules and project context;
- claim an eligible business task;
- create/update the business data or report outputs required by that claim;
- create its own claim/completion/readiness metadata;
- submit a NEW bug report under `coordination/bug_reports/`;
- continue to another safe business task after reporting a non-blocking bug.

A worker MUST NOT:

- patch a bug in `scripts/`, `schema/`, `.github/`, task orchestration or workflow rules;
- modify `AGENTS.md`, `START_HERE.md`, `coordination/WORKFLOW.json`, `coordination/WORK_QUEUE.jsonl`, `coordination/CONTINUOUS_WORKER_V2.md`, `coordination/CLAIM_PROTOCOL_V2.md` or permission policy;
- change schema merely to make its own data fit;
- alter another Agent's claim or bug report;
- silently work around a repository bug by changing global behavior;
- declare a bug resolved.

If a worker's task reveals a bug, it records the bug and stops only the unsafe/blocked portion of that task. It should continue other independent eligible work when possible.

## Bug reporting

Workers report bugs by creating one immutable file per bug:

```text
coordination/bug_reports/BUG_<UTC>_<TASK_ID>_<short-name>.json
```

Never append multiple Agents into one shared JSONL bug file.

Required fields:

```json
{
  "bug_id": "BUG_...",
  "status": "open",
  "requires_admin": true,
  "reported_at": "ISO-8601 UTC",
  "reported_by_agent": "agent-...",
  "reported_by_github_login": "login-or-unknown",
  "task_id": "TASK_ID",
  "severity": "blocking|high|medium|low",
  "category": "data_contract|workflow|claim|schema|ci|source|other",
  "summary": "short description",
  "evidence": ["concrete error/result"],
  "affected_paths": ["path"],
  "safe_workaround": "optional non-destructive workaround or null"
}
```

Workers create new reports only. Admin Agents may later update the same report with `status`, `resolved_at`, `resolved_by`, `resolution_commit`, and `resolution_notes`.

## Protected control plane

The machine-readable protected path list is in `coordination/AGENT_PERMISSIONS.json`.

The important principle is:

```text
worker = execute project tasks
admin  = maintain/fix project machinery
```

This separation prevents a task Agent from changing core behavior simply because it encountered a local problem.

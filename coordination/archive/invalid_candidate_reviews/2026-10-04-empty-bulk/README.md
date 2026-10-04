# Invalid candidate-review batch — archived

This directory preserves 100 claims and 100 completion records created by
`agent-20261004T123700Z-gpt56sol-c2-100c` for audit history only.

The completion records declared all 100 tasks complete at one timestamp, had empty `outputs`, and
contained no per-candidate durable evidence artifact. They therefore do not represent the required
one-by-one identity review and were removed from the active `claims/` and `completed/` namespaces.
They must never count toward current progress or task availability.

Archived control-plane material is not part of normal Agent entry and must not be read unless the
owner explicitly requests a historical audit.

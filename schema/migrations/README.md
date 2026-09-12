# Miles-Guo_public_archive Schema Migrations

`schema/schema.sql` is the current full schema used for clean rebuilds.

When an existing populated database requires a schema change, add an ordered migration here instead of silently changing historical data assumptions.

Suggested naming:

```text
0001_description.sql
0002_description.sql
```

Migration rules:

- preserve already collected source provenance;
- document destructive or lossy changes explicitly;
- do not merge `twitter` and `x`, change ID formats, or reinterpret stored fields without a reviewed migration;
- after migration changes, rebuild/validate the Pilot database and update the Pilot report with any compatibility impact.

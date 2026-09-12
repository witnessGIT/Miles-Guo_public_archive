# Miles-Guo_public_archive Current Task

Project: `Miles-Guo_public_archive`  
Repository: `witnessGIT/Miles-Guo_public_archive`  
Current phase: `SITE_ANALYSIS + PILOT`  
Workflow: `continuous-worker-v2`  
Full archive collection: **NOT STARTED / NOT AUTHORIZED UNTIL CURRENT PILOT PASSES**

## Start here

Classify current repository/session state with:

```bash
python scripts/project_status.py
```

If and only if the runtime can genuinely inspect decoded clip/frame/audio content and determine observed content position, it may declare:

```bash
python scripts/project_status.py --content-inspection-capable
```

Do not infer state from stale chats or from historical completion files alone. The current repository control plane is authoritative.

## Current acceptance revision

The repository contains historical completed records named:

```text
P9-AUDIT-60
P10-PILOT-DECISION
```

Those records were produced before the current playback-gated acceptance chain existed. They remain preserved as audit history and MUST NOT count as current Pilot completion or FULL_ARCHIVE authorization.

The current gate/report task identities are:

```text
P9-AUDIT-60-R2
P10-PILOT-DECISION-R2
```

Do not delete, rewrite, or reuse the old P9/P10 files. The R2 tasks exist so the current acceptance cycle can complete without destroying historical evidence.

## Current objective

Build and validate the first real searchable Pilot archive from public GWINS, GHOT, GettrSearch and linked public media sources.

The Pilot must prove:

```text
one livestream
+ multiple source pages/platforms
+ curated text
+ ASR text where available
+ reliable timestamps
+ source traceability
+ searchable structured data
+ real playback-position validation
```

Use real public records only. Do not invent Pilot data.

## Current Pilot boundary

The Pilot contains 27 selected source-backed cases.

Foundation/site analysis, aggregate alignment, and Pilot SQLite validation have advanced far enough that the **acceptance-critical blocker is real playback-position auditing**.

The authoritative chain is:

```text
P9-PLAYBACK-PILOT-* real playback work
        ↓
data/playback_audits/<CASE>/<SEGMENT>.json
        ↓
scripts/audit_gate.py reports pilot60_pass=true
        ↓
coordination/completed/P9-PLAYBACK-GATE.json
        ↓
P9-AUDIT-60-R2
        ↓
P10-PILOT-DECISION-R2
        ↓
FULL_ARCHIVE YES / NO decision
```

`P9-AUDIT-60-R2` MUST NOT begin before `P9-PLAYBACK-GATE` exists.

`P10-PILOT-DECISION-R2` MUST NOT begin before `P9-AUDIT-60-R2` completes.

`FULL_ARCHIVE` MUST NOT begin unless the **current R2 P10** explicitly authorizes it.

## Two work queues

Ordinary business/gate work:

```bash
python scripts/next_task.py --list
```

Real playback-position work:

```bash
python scripts/playback_queue.py --list
```

These queues must both be considered before classifying the repository as having no work.

If ordinary work is empty but playback work remains:

```text
repository-wide NO_ELIGIBLE_WORK = false
```

A runtime without required media/content-inspection capability may classify only its own session as:

```text
HOST_STOP
```

## Real playback claim requirements

A playback worker must have:

```text
ffmpeg
ffprobe
actual ability to inspect decoded media content
```

It must claim with:

```bash
python scripts/playback_queue.py \
  --claim \
  --content-inspection-capable \
  --agent-id agent-<UTC>-<random>
```

The flag is an auditable capability assertion, not a bypass.

A runtime that can execute ffmpeg but cannot inspect generated content and determine the observed content position MUST NOT pass the flag and MUST NOT claim playback work.

## What counts toward Pilot-60

Only durable real playback records under:

```text
data/playback_audits/
```

may count.

A qualifying record requires:

```text
public media access
→ actual seek/decode
→ actual content inspection
→ observed content position
→ signed timing error
→ scripts/record_playback_audit.py
```

Playback decode windows must include time before and after the expected timestamp so negative and positive timing error can both be measured.

The following do **not** count by themselves:

```text
S-AUDIT-* completion
coordination/ready/audit/*.json
transcript checks
source-page timestamps
ASR time-axis checks
successful ffmpeg decode without content inspection
written audit reports without real playback
historical P9/P10 completion files
```

Generating more transcript/timeline audit reports cannot substitute for the 60 real playback checks.

## Pilot-60 acceptance thresholds

Pilot approval requires at least 60 qualifying real playback checks in aggregate, with:

```text
false livestream merge rate approximately 0
>= 90% of locatable audited segments within 3 seconds
>= 98% within 8 seconds
```

Unperformed playback checks remain `unverified`.

## Gate transition after Pilot-60 passes

When:

```bash
python scripts/audit_gate.py --json
```

reports:

```text
pilot60_pass=true
```

seal the gate:

```bash
python scripts/playback_queue.py --seal-gate --agent-id <agent-id>
```

Then the non-playback acceptance work may continue:

```text
P9-AUDIT-60-R2
→ P10-PILOT-DECISION-R2
```

Once Pilot-60 has passed, extra optional playback cases do not keep the acceptance path in HOST_STOP.

## HOST_STOP versus SAFETY_OR_ACCESS_BLOCK

Use `HOST_STOP` when the current runtime cannot execute required media tooling or cannot inspect generated media evidence.

Use `SAFETY_OR_ACCESS_BLOCK` only when progress would require bypassing login, CAPTCHA, paywall, DRM, or another access control.

Do not misclassify a runtime limitation as repository-wide lack of work.

## Backlog is not a Pilot acceptance substitute

Documentation or future tooling such as data-model, data-quality, source-policy, architecture, collection, or export work may remain unfinished or independently claimable.

Those items may be useful backlog, but they cannot bypass playback-position auditing and do not unlock:

```text
P9-AUDIT-60-R2
P10-PILOT-DECISION-R2
FULL_ARCHIVE
```

When independently claimable, they may be completed in parallel. When they are not in the active queue, do not invent ad-hoc work merely to avoid a legitimate playback HOST_STOP.

## SQLite behavior

Git-tracked JSON/JSONL under `data/` remains the long-term source of truth.

Official database artifact:

```text
database/Miles-Guo_public_archive.sqlite3
```

It must remain rebuildable with:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

SQLite success does not imply timestamp accuracy or playback verification.

## Continuous-worker-v2 behavior

For each new claim:

```text
claim
→ work
→ validate
→ commit/push
→ finish / publish readiness
→ refresh repository state
→ classify again
→ claim next eligible task
```

Valid stop conditions remain:

```text
PROJECT_COMPLETE
USER_RECALL
NO_ELIGIBLE_WORK
HUMAN_DECISION_REQUIRED
SAFETY_OR_ACCESS_BLOCK
HOST_STOP
```

Use `scripts/project_status.py` to avoid confusing repository-wide `NO_ELIGIBLE_WORK` with a host-specific inability to claim playback work.

## Final decision boundary

Do not start `FULL_ARCHIVE` merely because scraping, alignment, database build, transcript auditing, old P9/P10 records, or report generation exists.

`P10-PILOT-DECISION-R2` must be supported by the current Pilot evidence, including at least 60 qualifying playback audits and required timing thresholds.

Only an explicit current R2 decision:

```text
full_archive_decision=YES
```

authorizes FULL_ARCHIVE.

Until the current chain reaches that point:

```text
PILOT = NOT PASSED
CURRENT P9 = BLOCKED
CURRENT P10 = BLOCKED
FULL_ARCHIVE = NOT AUTHORIZED
```

## Access and cost rules

- Publicly accessible content only.
- Low request rate and caching.
- No bypass of login, CAPTCHA, paywall, access control, or DRM.
- No full video/audio/model/cache/FFmpeg intermediates committed to Git.
- Record evidence and uncertainty instead of guessing.
- Core workflow must remain usable with GitHub, Python, SQLite/FTS5, local open-source tooling, public source pages, and local temporary cache.

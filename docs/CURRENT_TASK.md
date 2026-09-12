# Miles-Guo_public_archive Current Task

Project: `Miles-Guo_public_archive`  
Repository: `witnessGIT/Miles-Guo_public_archive`  
Current phase: `SITE_ANALYSIS + PILOT`  
Workflow: `continuous-worker-v2`  
Full archive collection: **NOT STARTED / NOT AUTHORIZED UNTIL PILOT PASSES**

## Start here

Every Agent must read the repository control files, then classify current state with:

```bash
python scripts/project_status.py
```

If and only if the runtime can genuinely inspect decoded clip/frame/audio content and determine observed content position, it may declare:

```bash
python scripts/project_status.py --content-inspection-capable
```

Do not infer project state from stale chat summaries. The repository is authoritative.

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

Foundation/site analysis, aggregate alignment, and Pilot SQLite validation have already advanced far enough that the **acceptance-critical blocker is now real playback-position auditing**.

The acceptance chain is:

```text
P9-PLAYBACK-PILOT-* real playback work
        ↓
data/playback_audits/<CASE>/<SEGMENT>.json
        ↓
scripts/audit_gate.py reports pilot60_pass=true
        ↓
coordination/completed/P9-PLAYBACK-GATE.json
        ↓
P9-AUDIT-60
        ↓
P10-PILOT-DECISION
        ↓
FULL_ARCHIVE YES / NO decision
```

`P10-PILOT-DECISION` MUST NOT begin before `P9-AUDIT-60` is completed.

`FULL_ARCHIVE` MUST NOT begin before the P10 decision explicitly authorizes it.

## Two work queues

Ordinary collection/alignment/source-audit work:

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

A runtime without the required media/content-inspection capability may classify only its own session as:

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

A runtime that can execute ffmpeg but cannot actually inspect the generated content and determine the observed content position MUST NOT pass the flag and MUST NOT claim playback work.

## What counts toward Pilot-60

Only durable real playback records under:

```text
data/playback_audits/
```

may count.

A qualifying record requires the real chain:

```text
public media access
→ actual seek/decode
→ actual content inspection
→ observed content position
→ timing error
→ scripts/record_playback_audit.py
```

The following do **not** count by themselves:

```text
S-AUDIT-* completion
coordination/ready/audit/*.json
transcript checks
source-page timestamps
ASR time-axis checks
successful ffmpeg decode without content inspection
written audit reports without real playback
```

Therefore generating more transcript/timeline audit reports cannot substitute for the 60 real playback checks.

## Pilot-60 acceptance thresholds

Pilot approval still requires at least 60 qualifying real playback checks in aggregate, with:

```text
false livestream merge rate approximately 0
>= 90% of locatable audited segments within 3 seconds
>= 98% within 8 seconds
```

Unperformed playback checks remain `unverified`.

## HOST_STOP versus SAFETY_OR_ACCESS_BLOCK

Use `HOST_STOP` when the current runtime cannot execute the required media tooling or cannot inspect generated media evidence.

Use `SAFETY_OR_ACCESS_BLOCK` only when progress would require bypassing login, CAPTCHA, paywall, DRM, or another access control.

Do not misclassify a runtime limitation as a project-wide lack of work.

## Backlog is not a Pilot acceptance substitute

Documentation or future tooling such as data-model, data-quality, source-policy, architecture, collection, or export work may remain unfinished or independently claimable.

Those items may be useful backlog, but they are not permission to bypass playback-position auditing and they do not unlock:

```text
P9-AUDIT-60
P10-PILOT-DECISION
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

Completing one task is not a stop condition.

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

Do not start `FULL_ARCHIVE` merely because scraping, alignment, database build, transcript auditing, or report generation is possible.

`P10-PILOT-DECISION` must be supported by real evidence covering the Pilot, including at least 60 qualifying playback audits and the required timing thresholds.

Until then:

```text
PILOT = NOT PASSED
P10 = BLOCKED
FULL_ARCHIVE = NOT AUTHORIZED
```

## Access and cost rules

- Publicly accessible content only.
- Low request rate and caching.
- No bypass of login, CAPTCHA, paywall, access control, or DRM.
- No full video/audio/model/cache/FFmpeg intermediates committed to Git.
- Record evidence and uncertainty instead of guessing.
- Core workflow must remain usable with GitHub, Python, SQLite/FTS5, local open-source tooling, public source pages, and local temporary cache.

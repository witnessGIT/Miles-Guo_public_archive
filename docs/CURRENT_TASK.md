# Miles-Guo_public_archive Current Task

Project: `Miles-Guo_public_archive`  
Repository: `witnessGIT/Miles-Guo_public_archive`  
Current phase: `SITE_ANALYSIS + PILOT`  
Workflow: `continuous-worker-v2`  
Full archive collection: **NOT STARTED / NOT AUTHORIZED UNTIL PILOT PASSES**

## Start here

Every Agent must follow, in order:

```text
AGENTS.md
coordination/CONTINUOUS_WORKER_V2.md
coordination/WORKFLOW.json
coordination/README.md
coordination/WORK_QUEUE.jsonl
this file
```

Then run:

```bash
python scripts/next_task.py --list
```

Do not choose work from this prose file by guess. `scripts/next_task.py` + Git coordination files determine what is actually claimable now.

## Current objective

Build and validate the first real searchable archive model from these public sources:

1. `gwins` — https://www.gwins.org/
2. `ghot` — https://ghot.ai/
3. `gettrsearch` — https://gettrsearch.com/

The Pilot must prove:

```text
one livestream
+ multiple source pages/platforms
+ curated text
+ ASR text where available
+ reliable timestamps
+ source traceability
+ searchable structured data
```

Use real public records only. Do not invent Pilot data.

## Current project status

Completed foundation/site-analysis work already exists in Git. The current Pilot contains 27 selected source-backed cases:

```text
early   9 cases  2017-2019
middle  9 cases  2020-2021
late    9 cases  2022-2023
```

The early legacy batch has durable source records. Middle and late legacy batch claims were already active before `continuous-worker-v2`; they are grandfathered and must not be duplicated or disrupted.

## New default: per-case streaming

The project no longer waits for an entire era/batch before downstream work starts.

Each Pilot case advances independently:

```text
COLLECT + IDENTITY
        ↓
coordination/ready/collection/<CASE>.json
        ↓
ALIGN
        ↓
coordination/ready/alignment/<CASE>.json
        ↓
AUDIT
        ↓
coordination/ready/audit/<CASE>.json
```

Example task IDs:

```text
S-COLLECT-PILOT-E001
S-ALIGN-PILOT-E001
S-AUDIT-PILOT-E001
```

If one case is ready, another Agent may start its next stage immediately even while unrelated cases remain unfinished.

## Existing legacy claims are protected

Do not rewrite or steal valid existing claims simply to migrate them.

A claim without:

```json
"workflow_mode": "continuous-worker-v2"
```

is a grandfathered legacy claim.

Its owner finishes the current task normally. The next new claim uses v2.

Legacy Middle/Late collectors can unlock downstream work case-by-case without ending their batch:

```bash
python scripts/next_task.py \
  --mark-ready collection \
  --case-id PILOT-M001 \
  --agent-id <legacy-owner> \
  --live-id LIVE_20200323_001 \
  --outputs ... \
  --validation "source identity and provenance verified"
```

This allows another Agent to immediately claim `S-ALIGN-PILOT-M001`.

## Continuous-worker-v2 behavior

For every **new claim**, the default behavior is:

```text
claim
→ work
→ validate
→ commit/push
→ finish / publish readiness
→ refresh
→ claim next eligible task
→ repeat
```

Completing one task is not a reason to stop.

A worker stops only for a documented condition:

```text
PROJECT_COMPLETE
USER_RECALL
NO_ELIGIBLE_WORK
HUMAN_DECISION_REQUIRED
SAFETY_OR_ACCESS_BLOCK
HOST_STOP
```

Git cannot wake a host-suspended Agent. It can only preserve durable state so a running worker can continue or a new worker can resume immediately.

For runtimes that support long-lived processes:

```bash
python scripts/next_task.py \
  --watch \
  --claim \
  --agent-id agent-<UTC>-<random> \
  --poll-seconds 60
```

may wait for work, but host/platform suspension can still terminate the process.

## Task ownership

Before any new task begins, an Agent must create:

```text
coordination/claims/<TASK_ID>.json
```

The claim must become visible on `main` before expensive work begins.

If a claim already exists, do not wait for it and do not overwrite it. Refresh and claim another eligible task.

After real outputs are committed, finish using:

```bash
python scripts/next_task.py \
  --finish <TASK_ID> \
  --agent-id <agent-id> \
  --outputs <paths...> \
  --validation "what was actually checked"
```

Then immediately claim another eligible task.

## Collection requirements

Per-case collection must preserve at least:

- internal/candidate identity;
- title/date;
- source-site provenance;
- source URL;
- third-party ID where available;
- curated text separate from ASR;
- start/end seconds only when actually known;
- retrieval/verification state;
- cross-source identity evidence/conflicts.

Never invent timestamps, FPS, frames, source IDs, source absence, or merge certainty.

Prefer independent per-case/per-live files instead of concurrent appends to one large JSONL.

## Alignment requirements

For overlapping records, timing priority is:

1. existing curated/source timestamps;
2. GHOT public ASR/time axis + monotonic fuzzy alignment;
3. local ASR only when public timing is inadequate;
4. manual playback review for unresolved/high-value segments.

Preserve:

```text
text_curated
text_asr
start_sec / end_sec
curated_source_id
asr_source_id
time_source_id
alignment_method
alignment_quality
playback_verified
review_status
```

Do not derive `end_sec` silently and do not mark playback verified unless playback was actually checked.

## Audit requirements

Audit starts incrementally after each case is aligned; it does not wait for all 27 cases.

Pilot approval still requires at least 60 real segment playback checks in aggregate.

Quality gates:

```text
false livestream merge rate approximately 0
>= 90% of locatable audited segments within 3 seconds
>= 98% within 8 seconds
```

Unperformed playback checks remain `unverified`.

## SQLite behavior

Git-tracked JSON/JSONL under `data/` is the long-term source of truth.

Official database artifact:

```text
database/Miles-Guo_public_archive.sqlite3
```

It must remain rebuildable from `data/` + `schema/`:

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

SQLite build/rebuild is not a global lock. Collection/alignment/audit may continue while another Agent handles aggregate database validation.

## Aggregate legacy gates

`coordination/WORK_QUEUE.jsonl` still contains historical/aggregate task IDs for compatibility:

```text
P6-PILOT-EARLY-B001
P6-PILOT-MIDDLE-B001
P6-PILOT-LATE-B001
P7-ALIGNMENT-B001
P8-SQLITE-PILOT
P9-AUDIT-60
P10-PILOT-DECISION
```

Interpretation under v2:

- P6 tasks: legacy collection batches already created before streaming mode;
- P7: aggregate alignment gate / gap cleanup, not permission to begin per-case alignment;
- P8: aggregate SQLite/FTS validation gate, not permission to begin database rebuilds;
- P9: aggregate audit gate that checks accumulated per-case audit evidence reaches the 60-segment requirement;
- P10: final whole-Pilot decision.

Only P10 is intentionally a whole-Pilot waiting point.

## Final decision boundary

Do not start `FULL_ARCHIVE` merely because scraping or collection is possible.

`P10-PILOT-DECISION` must be supported by real evidence covering:

- all required site findings;
- Pilot source coverage;
- cross-source matches/conflicts;
- segment counts;
- curated/ASR coverage;
- alignment quality;
- at least 60 real playback audits;
- false-merge findings;
- broken/duplicate URLs;
- SQLite/FTS validation;
- unresolved problems;
- recommendation `FULL_ARCHIVE: YES` or `FULL_ARCHIVE: NO`.

## Access rules

- Publicly accessible content only.
- Low request rate and caching.
- No bypass of login, CAPTCHA, paywall, access control, or DRM.
- No full video/audio/model/cache/FFmpeg intermediates committed to Git.
- Record evidence and uncertainty instead of guessing.

## Zero-cost rule

The core workflow must remain usable with GitHub, Python, SQLite/FTS5, local open-source tooling, public source pages, and local temporary cache.

Paid APIs, commercial vector databases, paid object storage, or paid AI services must not become mandatory infrastructure.

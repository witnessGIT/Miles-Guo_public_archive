# ARCHITECTURE

## Principle

Archive First, Application Second.

## Layers

1. **Discovery layer** — lightweight inventories from public index/search pages.
2. **Source layer** — source-specific ids, URLs, capture timestamps and original-platform locators.
3. **Canonical layer** — one `LIVE_YYYYMMDD_NNN` per underlying item.
4. **Text layer** — human transcript, ASR, subtitle and time-addressable segments kept separate.
5. **Build layer** — deterministic conversion from versioned JSON/JSONL + SQL schema into SQLite.
6. **Query layer** — SQLite tables + FTS5 for downstream search, research, AI retrieval and later media applications.

## Git truth versus generated database

`data/` and `schema/` are the durable versioned truth. `database/Miles-Guo_public_archive.sqlite3` is generated and can be deleted/rebuilt.

## Scale strategy

Do not fetch every detail/full transcript before identity quality is proven. First build a full lightweight inventory, then enrich in deterministic batches. This minimizes duplicate work, keeps Git diffs reviewable and makes source conflicts visible early.

## Current pipeline

GWINS inventory -> canonical ids -> Pilot source matching -> SQLite rebuild -> validation -> later GHOT ASR/technical enrichment -> GETTR Search cross-check when reproducible.

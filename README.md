# Miles-Guo_public_archive

**Miles Guo Public Information Searchable Digital Archive**  
**郭先生公开信息可检索数字档案库**

`Miles-Guo_public_archive` 是一个面向长期保存、检索、研究、时间线构建、AI 问答与下游应用的数据档案项目。它不是视频制作项目。

当前阶段聚焦郭先生历史直播及相关公开视频资料，目标是把多个公开来源中的页面、文字稿、时间轴和原始平台链接统一成可追溯的数据模型：

- 一个直播使用一个内部 `LIVE_YYYYMMDD_NNN`；
- 一个直播允许对应多个来源；
- 人工整理文字与自动 ASR 分开保存；
- 时间定位以 `start_sec` / `end_sec` 为主，帧号仅作辅助；
- `data/` 中的 JSON / JSONL 是 Git 长期真源；
- `database/Miles-Guo_public_archive.sqlite3` 是可删除、可重建的查询产物；
- SQLite 使用 FTS5 提供全文检索；
- 所有来源保留站点、URL、第三方 ID、抓取时间与来源等级。

## Project principle

> Archive First, Application Second.

档案优先于应用。字段设计优先保证未来可检索、可研究、可追溯、可扩展，而不是针对任何单一应用优化。

## Current phase

- `SITE_ANALYSIS`: in progress
- `PILOT`: in progress
- `FULL_ARCHIVE`: not started
- `MAINTENANCE`: not started

Pilot 仅用于验证统一模型和跨站来源关系，不代表整个历史档案已经完成。只有 Pilot 数据质量达到标准后，才考虑进入全量历史采集。

## Initial public sources

Database enum values are fixed to lowercase:

- `gwins`
- `ghot`
- `gettrsearch`

Original platform enum values currently include:

- `gettr`
- `rumble`
- `youtube`
- `twitter`
- `x`
- `gwins`
- `ghot`
- `gettrsearch`
- `other`

## Repository layout

```text
Miles-Guo_public_archive/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── SITE_ANALYSIS.md
│   ├── DATA_MODEL.md
│   ├── DATA_QUALITY.md
│   ├── SOURCE_POLICY.md
│   └── ARCHITECTURE.md
├── schema/
│   ├── schema.sql
│   └── migrations/
├── data/
│   ├── live_videos/
│   ├── live_segments/
│   ├── archive_items/
│   ├── sources/
│   ├── entities/
│   └── topics/
├── database/
│   └── Miles-Guo_public_archive.sqlite3
├── scripts/
│   ├── analyze_sources.py
│   ├── collect_pilot.py
│   ├── build_db.py
│   ├── validate_db.py
│   └── export.py
├── reports/
│   └── pilot_report.md
├── cache/
└── tests/
```

## Rebuild contract

The SQLite file is not the only source of truth. It must be possible to run:

```bash
rm -f database/Miles-Guo_public_archive.sqlite3
python scripts/build_db.py
python scripts/validate_db.py
```

and recreate an equivalent searchable database from `data/` plus `schema/`.

## Media policy

The Git repository does **not** store full livestream video, large audio, model weights, Whisper models, FFmpeg intermediates, or temporary media downloads. Temporary analysis files belong under `cache/` and are ignored by Git.

The long-term archive records metadata and locators such as source URLs, platform IDs, timestamps, text, dimensions/FPS when verified, provenance and quality status.

## Downstream use

Future applications such as `movie_production` should consume this archive through the SQLite database or a future stable API. They should not create a second independent livestream archive.

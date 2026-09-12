# Miles-Guo_public_archive

**Miles Guo Public Information Searchable Digital Archive**  
**郭先生公开信息可检索数字档案库**

Official repository: `witnessGIT/Miles-Guo_public_archive`  
Official database: `database/Miles-Guo_public_archive.sqlite3`

`Miles-Guo_public_archive` 是一个面向长期保存、检索、研究、时间线构建、AI 问答与下游应用的数据档案项目。它不是视频制作项目。

> **Archive First, Application Second.**

档案优先于应用。字段设计首先保证未来可检索、可研究、可追溯、可扩展，而不是针对任何单一应用优化。

## Agent：进入仓库后立即做什么

任何 Agent 进入本仓库后，不要停留在“阅读规范”阶段。必须按以下顺序立即开始工作：

1. 阅读 `AGENTS.md`。
2. 阅读 `docs/PROJECT_REQUIREMENTS.md`、`docs/NAMING_AND_WORKFLOW.md`。
3. 阅读 `docs/CURRENT_TASK.md`，确认当前阶段和待处理工作。
4. 检查仓库现状，避免覆盖其他 Agent 已完成的数据。
5. 从当前任务队列领取一个尚未完成的数据整理任务。
6. 对 `gwins`、`ghot`、`gettrsearch` 的真实公开数据进行分析或 Pilot 整理。
7. 将结果写入 Git 友好的 JSON / JSONL 源数据，并更新来源、质量和进度记录。
8. 按规范验证后提交清晰 commit。
9. 如果 Pilot 尚未通过，不得擅自进入全量采集。

如果没有更具体的用户指令，`docs/CURRENT_TASK.md` 就是 Agent 的默认工作入口。

## Current mission

当前阶段聚焦郭先生历史直播及相关公开视频资料，目标是把多个公开来源中的页面、文字稿、时间轴和原始平台链接统一成可追溯的数据模型：

- 一个直播使用一个内部 `LIVE_YYYYMMDD_NNN`；
- 一个直播允许对应多个来源；
- 人工整理文字与自动 ASR 分开保存；
- 时间定位以 `start_sec` / `end_sec` 为主，帧号仅作辅助；
- `data/` 中的 JSON / JSONL 是 Git 长期真源；
- `database/Miles-Guo_public_archive.sqlite3` 是可删除、可重建的查询产物；
- SQLite 使用 FTS5 提供全文检索；
- 所有来源保留站点、URL、第三方 ID、抓取时间与来源等级。

## Initial public sources

当前第一批公开来源：

- **GWINS** — https://www.gwins.org/
- **GHOT** — https://ghot.ai/
- **GettrSearch** — https://gettrsearch.com/

数据库枚举固定使用小写：

- `gwins`
- `ghot`
- `gettrsearch`

当前重点验证三个来源之间是否能够形成：

```text
一个直播 ID
+ 多个来源
+ 高质量文字
+ 可靠时间轴
+ 可追溯原视频
```

原始平台枚举目前包括：

- `gettr`
- `rumble`
- `youtube`
- `twitter`
- `x`
- `gwins`
- `ghot`
- `gettrsearch`
- `other`

## Current phase

- `SITE_ANALYSIS`: in progress
- `PILOT`: in progress
- `FULL_ARCHIVE`: not started
- `MAINTENANCE`: not started

Pilot 仅用于验证统一模型和跨站来源关系，不代表整个历史档案已经完成。只有 Pilot 数据质量达到标准后，才考虑进入全量历史采集。

## Zero-cost-first policy

本项目采用 **0 成本优先** 架构：

- GitHub：保存代码、规范、JSON/JSONL 源数据和小型可重建产物；
- SQLite：本地可搜索数据库；
- 公开来源网站：原始媒体来源；
- 本地机器：临时下载、ASR、对齐、FFmpeg 和缓存；
- 不依赖付费云数据库、付费对象存储或付费 AI API 才能维持基础档案能力。

如果以后引入付费能力，必须是可选增强，不能让核心档案依赖付费服务才能读取或重建。

## Historical recovery scope

本项目未来不仅整理仍然在线的内容，也要逐步记录和恢复已经移动、删除或失效的公开资料，例如：

- 已删除或失效的历史直播；
- Twitter / X 历史帖子；
- GETTR 历史帖子；
- 网页快照；
- 公开镜像和转载；
- 公开历史缓存和网页存档；
- 新闻或其它公开页面中的历史引用。

恢复资料必须保存来源链和可信度。**转载、截图或二手引用不得冒充原始发布。**

## Source-of-truth model

```text
GWINS ─────────┐
               │
GHOT ──────────┼──> Source analysis
               │
GettrSearch ───┘
                       ↓
              Normalize / Deduplicate
                       ↓
                  JSON / JSONL
               Git source of truth
                       ↓
                  build_db.py
                       ↓
      Miles-Guo_public_archive.sqlite3
                       ↓
          Search / AI-RAG / downstream apps
```

未来 Twitter/X、GETTR、网页存档、镜像和历史恢复资料进入同一个 Archive，不另建相互割裂的数据库。

## Repository layout

规范目标结构：

```text
Miles-Guo_public_archive/
├── AGENTS.md
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── PROJECT_REQUIREMENTS.md
│   ├── NAMING_AND_WORKFLOW.md
│   ├── CURRENT_TASK.md
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

尚未创建的目录属于待实现结构，不得因为 README 中出现就声称已经存在。

## Rebuild contract

SQLite 不是唯一事实源。未来完整实现后必须可以执行：

```bash
rm -f database/Miles-Guo_public_archive.sqlite3
python scripts/build_db.py
python scripts/validate_db.py
```

并仅通过 `data/` + `schema/` 重建等价的可搜索数据库。

## Search contract

基础检索链必须最终支持：

```text
关键词 / 人物 / 机构 / 主题
        ↓
SQLite FTS5 / 后续语义检索
        ↓
live_segments
        ↓
live_id
        ↓
live_sources
        ↓
原文 + 日期 + 来源 URL + start_sec/end_sec
```

任何高价值档案记录都必须能追溯到原始或明确标级的恢复来源。

## Media policy

Git 仓库不保存完整直播视频、大音频、模型权重、Whisper 模型、FFmpeg 中间文件或临时媒体下载。

临时分析文件属于 `cache/` 并应被 Git 忽略。长期档案记录 source URL、平台 ID、时间码、文字、已验证的尺寸/FPS、来源链和质量状态。

## Downstream use

未来 `movie_production` 等应用应通过 `database/Miles-Guo_public_archive.sqlite3` 或未来稳定 API 消费本档案，不得另建第二套独立郭先生直播数据库。

## Agent 开工前必读

所有 Agent 必须先阅读：

1. [AGENTS.md](AGENTS.md)
2. [当前工作任务](docs/CURRENT_TASK.md)
3. [完整项目要求](docs/PROJECT_REQUIREMENTS.md)
4. [统一命名与工作规范](docs/NAMING_AND_WORKFLOW.md)

当前明确用户要求优先；后续命名规范优先于早期示例。阅读完成后应立即按 `CURRENT_TASK.md` 开始实际数据整理，不要仅汇报“已阅读”。

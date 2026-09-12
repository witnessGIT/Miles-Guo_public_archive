# Miles-Guo_public_archive

**Miles Guo Public Information Searchable Digital Archive**  
**郭先生公开信息可检索数字档案库**

Official repository: `witnessGIT/Miles-Guo_public_archive`  
Official database: `database/Miles-Guo_public_archive.sqlite3`

`Miles-Guo_public_archive` 是一个面向长期保存、检索、研究、时间线构建、AI 问答与下游应用的数据档案项目。它不是视频制作项目。

> **Archive First, Application Second.**

档案优先于应用。字段设计首先保证未来可检索、可研究、可追溯、可扩展，而不是针对任何单一应用优化。

## Agent：进入仓库后立即做什么

当前 Agent 工作流：

```text
continuous-worker-v2
```

任何新 Agent 进入本仓库后，不要停留在“阅读规范”阶段，也不要等待其它不相关批次完成。

先按顺序阅读：

1. `AGENTS.md`
2. `coordination/CONTINUOUS_WORKER_V2.md`
3. `coordination/WORKFLOW.json`
4. `coordination/README.md`
5. `coordination/WORK_QUEUE.jsonl`
6. `docs/CURRENT_TASK.md`
7. `docs/PROJECT_REQUIREMENTS.md`
8. `docs/NAMING_AND_WORKFLOW.md`

然后执行：

```bash
python scripts/next_task.py --list
```

领取当前最高优先级可执行任务：

```bash
python scripts/next_task.py \
  --claim \
  --agent-id agent-<UTC>-<random>
```

新 claim 会明确记录：

```json
{
  "workflow_mode": "continuous-worker-v2",
  "continue_after_finish": true
}
```

Agent 的默认循环是：

```text
发现任务
↓
原子 claim
↓
执行真实工作
↓
验证
↓
commit / push
↓
finish / 发布 readiness
↓
刷新仓库
↓
继续 claim 下一项
↓
重复
```

**完成一场直播、一个 batch 或一个 commit 都不是停止条件。**

只有项目当前阶段完成、用户召回、没有任何可执行任务、需要人工决策、安全/访问限制，或宿主平台主动终止运行时，Agent 才停止。

### 重要限制

Git/GitHub 可以保存任务状态、让运行中的 Agent 持续领任务、让下一个 Agent 无聊天记忆接续，但 **Git 不能主动唤醒已经被 ChatGPT/Work/Codex 宿主平台挂起或终止的 Agent 会话**。

如果宿主运行环境允许长时间保持进程，可使用：

```bash
python scripts/next_task.py \
  --watch \
  --claim \
  --agent-id agent-<UTC>-<random> \
  --poll-seconds 60
```

等待新任务。宿主平台仍可能终止该进程。

### 已经在做的旧任务不受影响

`continuous-worker-v2` 只对**新 claim** 生效。

已有有效 claim 不重命名、不删除、不抢占、不强制拆分。旧 Agent 完成当前任务后，下一次领任务自动使用 v2。

旧的大批次 Agent 还可以在不结束原任务的情况下，按单场提前解锁下游：

```bash
python scripts/next_task.py \
  --mark-ready collection \
  --case-id PILOT-M001 \
  --agent-id <legacy-claim-owner> \
  --live-id LIVE_20200323_001 \
  --outputs ... \
  --validation "source identity and provenance verified"
```

这样另一个 Agent 可以马上开始该场 Alignment，而旧 Agent 继续做自己的剩余批次。

本项目因此不依赖 Agent 之间互相聊天，Git 本身就是协作状态源。

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

- `SITE_ANALYSIS`: source analysis completed enough to support the current Pilot; unresolved dynamic details remain documented
- `PILOT`: in progress
- `FULL_ARCHIVE`: not authorized
- `MAINTENANCE`: not started

Pilot 仅用于验证统一模型和跨站来源关系，不代表整个历史档案已经完成。只有 Pilot 数据质量达到标准后，才考虑进入全量历史采集。

## Multi-Agent coordination

协作状态统一放在：

```text
coordination/
├── CONTINUOUS_WORKER_V2.md
├── WORKFLOW.json
├── README.md
├── WORK_QUEUE.jsonl
├── claims/
├── completed/
├── ready/
└── conflicts/
```

核心规则：

```text
next_task.py
↓
读取静态队列 + Pilot cases + completed + claims + ready
↓
生成当前可执行任务
↓
创建原子 claim
↓
执行 + 验证 + commit
↓
创建 completed / ready
↓
继续领取下一项
```

未来默认按单场直播/Pilot case 或非常小的非重叠 micro-batch 分工，不再用“大批全部完成后才允许下一阶段”的方式串行阻塞。

流水线：

```text
COLLECT + IDENTITY
        ↓
ALIGN
        ↓
AUDIT
```

每场独立推进。Aggregate P7/P8/P9 只承担汇总/验证/gate 职责；真正需要等待整个 Pilot 的最终决策是 `P10-PILOT-DECISION`。

如果两个 Agent 同时抢同一个任务，只有第一个成功创建并 push claim 文件的 Agent 获得任务；另一个不得覆盖，必须刷新仓库后改领其它任务。

发生来源冲突、重复身份、时间轴冲突、stale claim 接管等情况时，必须写入 `coordination/conflicts/`，不得静默覆盖。

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

当前规范结构：

```text
Miles-Guo_public_archive/
├── AGENTS.md
├── README.md
├── LICENSE
├── .gitignore
├── coordination/
│   ├── CONTINUOUS_WORKER_V2.md
│   ├── WORKFLOW.json
│   ├── README.md
│   ├── WORK_QUEUE.jsonl
│   ├── claims/
│   ├── completed/
│   ├── ready/
│   └── conflicts/
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
│   ├── next_task.py
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

SQLite 不是唯一事实源。必须可以执行：

```bash
rm -f database/Miles-Guo_public_archive.sqlite3
python scripts/build_db.py
python scripts/validate_db.py
```

并仅通过 `data/` + `schema/` 重建等价的可搜索数据库。

## Search contract

基础检索链最终必须支持：

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
2. [Continuous Worker v2](coordination/CONTINUOUS_WORKER_V2.md)
3. [Workflow state](coordination/WORKFLOW.json)
4. [多 Agent 协作协议](coordination/README.md)
5. [任务队列](coordination/WORK_QUEUE.jsonl)
6. [当前工作任务](docs/CURRENT_TASK.md)
7. [完整项目要求](docs/PROJECT_REQUIREMENTS.md)
8. [统一命名与工作规范](docs/NAMING_AND_WORKFLOW.md)

当前明确用户要求优先；后续命名规范优先于早期示例。阅读完成后应立即走 claim 流程并开始实际整理，不要仅汇报“已阅读”。

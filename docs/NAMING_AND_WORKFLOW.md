# Miles-Guo_public_archive Naming and Workflow

本文件依据用户后续统一命名规范整理，与 PROJECT_REQUIREMENTS.md 共同构成项目规范。后续明确的用户指令优先；两份文件示例冲突时以本文件为准。

## 开工前必读

所有 agent 必须先阅读根目录 AGENTS.md、本文件、PROJECT_REQUIREMENTS.md、README.md，以及任务相关的已有文档、schema、报告和测试。开始修改前检查 main 分支现状、远程地址、工作区及已有文件。不得仅依赖聊天记忆。

## 项目定位和边界

- 正式名称：`Miles-Guo_public_archive`。
- 唯一允许修改的 GitHub 仓库：`witnessGIT/Miles-Guo_public_archive`。
- 默认分支：`main`。
- 正式数据库：`database/Miles-Guo_public_archive.sqlite3`；不得创建其它正式数据库名。
- README 开头必须明确英文定义 **Miles Guo Public Information Searchable Digital Archive** 和中文定义 **郭先生公开信息可检索数字档案库**，说明不是视频制作项目。
- 当前重点：郭先生历史直播。未来支持直播、视频、文字稿、GETTR、Twitter / X、文章、图片、采访、音频、网页存档、历史删除内容、转载与镜像。
- 项目负责发现信息、公开数据采集、来源记录、整理、去重、文字稿、时间轴、实体、主题、全文搜索、历史恢复、数据质量及可追溯性。
- 不负责最终视频剪辑、成片渲染、视频包装和新闻视频制作。
- 不得修改 `witnessGIT/movie_production` 或其它已有项目；它们未来只是读取正式数据库或稳定 API 的下游，不应另建第二套直播数据库。
- **Archive First, Application Second**。字段设计优先支持检索、研究、来源追溯、AI 问答、时间线和平台扩展。
- 文档、代码、数据库、脚本、报告、README、注释、CI、目录说明和后续讨论均使用正式名称。第三方原有字段及明确的历史兼容说明可以保留原名；旧请求中的旧项目名一律理解为正式名称。

## 规范目录

```text
Miles-Guo_public_archive/
├── AGENTS.md
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── PROJECT_REQUIREMENTS.md
│   ├── NAMING_AND_WORKFLOW.md
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

## ID 和枚举

| 对象 | 内部 ID 格式 |
| --- | --- |
| 直播 | `LIVE_YYYYMMDD_NNN`，例如 `LIVE_20220315_001` |
| Segment | `LIVE_20220315_001_SEG_000001`，六位序号 |
| 来源 | `SRC_XXXXXXXX` |
| 通用档案 | `ITEM_XXXXXXXX` |
| 实体 | `ENT_XXXXXXXX` |
| 主题 | `TOPIC_XXXXXXXX` |

不要根据网站 ID 生成内部主键。第三方 ID 单独保存在 `source_video_id`、`source_post_id`、`source_page_id` 等字段。

数据库来源枚举统一小写：`gwins`、`ghot`、`gettrsearch`。展示层可用 GWINS、GHOT、GettrSearch。其它原始来源按完整任务要求记录。

平台枚举：`gettr`、`rumble`、`youtube`、`twitter`、`x`、`gwins`、`ghot`、`gettrsearch`、`other`。如未来合并 twitter 与 x，必须通过正式 schema migration，不能由 agent 自行决定。

## 数据、媒体及命名

- `data/` 的 JSON / JSONL 是 Git 长期源数据；SQLite 是可重建查询产物。
- 删除正式 SQLite 后，运行 `python scripts/build_db.py` 必须仅依赖 `data/` 和 `schema/` 重建同等数据库，再运行验证。
- 禁止提交完整 MP4、大音频、大模型、Whisper 模型、临时视频和 FFmpeg 中间文件。临时文件放 `cache/` 并加入 `.gitignore`；分析后删除临时下载媒体。
- 长期记录 URL、平台 ID、秒数、经验证的 FPS/帧号、原文字及来源元数据。
- 文档一级标题以 `# Miles-Guo_public_archive` 开始，可追加文档类型。
- 如需代码常量，使用 `PROJECT_NAME = "Miles-Guo_public_archive"`、`DATABASE_NAME = "Miles-Guo_public_archive.sqlite3"`，避免多种名字散落硬编码。
- Commit 前缀建议：`chore:`、`research:`、`schema:`、`data:`、`feat:`、`fix:`、`test:`、`docs:`。每个重要阶段单独提交，提交信息不得使用旧项目名。

## Pilot 验收速查（完整要求见 PROJECT_REQUIREMENTS.md）

- 20–30 场真实直播，尽量跨早、中、晚不同年份。
- 覆盖：GWINS + GHOT、仅 GWINS、仅 GHOT、GettrSearch 可发现而其它站缺失、多视频源、有时间码及无精确时间码。缺失必须有明确搜索范围证据，不能把未找到写成确定不存在。
- 同一场直播仅一个 live_id；人工稿和 ASR 分存，不得用 AI 改写覆盖原文字段。
- 匹配至少参考日期、标题、平台视频 ID（含 GETTR / Rumble）、时长、文本开头；输出 match_score。建议阈值：`>=0.85` 自动合并、`0.65 <= score < 0.85` 待复核、`<0.65` 不自动合并。避免不同直播误合并，评分及证据须可复核。
- 秒数为主定位；仅在真实 FPS 已知时计算帧号。优先已有公开时间数据；无法可靠对齐时才考虑重新 ASR。
- 至少随机抽查 60 个 segment：直播归属、日期、原文字、实际播放位置、来源可追溯性和跨站误合并。
- 目标：误合并率接近 0；至少 90% 的可定位 segment 时间误差不超过 3 秒，至少 98% 不超过 8 秒。未验证不计作通过，未达标不得进入全量。
- 四类真实验收查询：按日期列直播；关键词返回直播 ID、日期、原文、起止秒数、来源 URL；按 segment_id 追溯直播、原文、各站来源、原视频及时间码；随机 segment 使用 URL + 秒数实际验证内容位置。
- 报告路径 `reports/pilot_report.md`，开头注明 `Project: Miles-Guo_public_archive`、`Phase: PILOT`。明确 SITE_ANALYSIS、PILOT、FULL_ARCHIVE、MAINTENANCE 状态。
- 报告全部覆盖率、匹配冲突、时间抽查结果、失效和重复项、数据库及源数据大小、问题、建议、是否进入全量 YES / NO。Pilot 后停止扩张，先汇报。

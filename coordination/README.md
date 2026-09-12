# Miles-Guo_public_archive Multi-Agent Coordination

本目录是 `Miles-Guo_public_archive` 的零成本多 Agent 协作协议。

目标：多个 Agent 同时进入仓库时，能够自动分工、避免重复采集、避免同时修改同一批数据，并把工作状态永久保存在 Git 中。

## 核心原则

不要通过聊天记忆判断“谁正在做什么”。Git 是唯一协调事实源。

每个 Agent 开工时必须：

```text
读取 AGENTS.md
↓
读取 docs/CURRENT_TASK.md
↓
读取 coordination/WORK_QUEUE.jsonl
↓
检查 coordination/claims/
↓
检查 coordination/completed/
↓
选择最高优先级、依赖已满足、未被认领、未完成的任务
↓
原子认领
↓
执行
↓
提交成果
↓
写 completed 记录
↓
继续领取下一任务
```

## 任务认领：使用文件创建作为原子锁

领取任务 `P1-GWINS-STRUCTURE` 时，创建：

```text
coordination/claims/P1-GWINS-STRUCTURE.json
```

建议内容：

```json
{
  "task_id": "P1-GWINS-STRUCTURE",
  "agent_id": "agent-<unique-id>",
  "claimed_at": "ISO-8601 timestamp",
  "base_commit": "commit sha seen when claiming",
  "status": "in_progress",
  "notes": "short description of intended work"
}
```

### 并发规则

认领必须通过“创建新文件”完成，不得先修改一个共享状态字段再开始。

如果创建 `coordination/claims/<TASK_ID>.json` 失败，因为文件已经存在：

1. 不要覆盖；
2. 重新读取 claims / completed；
3. 立即选择另一个可执行任务。

这使 GitHub 的“文件已存在”检查成为并发锁。

## 完成任务

成果提交并验证后，创建：

```text
coordination/completed/<TASK_ID>.json
```

建议内容：

```json
{
  "task_id": "P1-GWINS-STRUCTURE",
  "agent_id": "agent-<unique-id>",
  "completed_at": "ISO-8601 timestamp",
  "result_commit": "commit sha containing durable output",
  "outputs": ["docs/SITE_ANALYSIS.md"],
  "validation": "what was actually checked",
  "notes": "remaining limitations"
}
```

完成记录存在后，该任务视为完成。其他 Agent 不得重复做同一个工作单元，除非用户明确要求复核或修正。

认领文件可以保留作为审计记录；不要求删除。

## 依赖规则

`WORK_QUEUE.jsonl` 中 `depends_on` 指定依赖。

一个任务只有在全部依赖任务都存在对应：

```text
coordination/completed/<DEPENDENCY>.json
```

时才可自动领取。

`depends_on: []` 表示可立即执行。

## Stale claim / 接管

默认 stale 阈值：**2 小时**。

但仅“时间超过 2 小时”不能自动证明 Agent 已停止。接管前必须检查：

- claim 后是否已有相关新 commit；
- 对应输出文件是否正在形成；
- completed 是否已经存在；
- 是否能从仓库状态判断原 Agent 仍在推进。

确认 claim 已失活后，新 Agent 可以创建：

```text
coordination/conflicts/<TASK_ID>-takeover-<agent-id>.json
```

记录：

```json
{
  "task_id": "P1-GWINS-STRUCTURE",
  "takeover_agent": "agent-new",
  "previous_agent": "agent-old",
  "reason": "claim stale and no durable progress found",
  "checked_at": "ISO-8601 timestamp"
}
```

然后继续该任务。

不得仅因为自己想做某项任务而抢占有效 claim。

## 数据分片规则

采集任务优先按以下维度拆分：

```text
来源站点 + 年份/范围 + batch
```

例如：

```text
GWINS-2019-B001
GHOT-2020-B001
GETTRSEARCH-2021-B001
```

不同 Agent 不应同时写同一个大 JSONL 文件。

优先使用独立 batch 文件，例如：

```text
data/live_segments/2020/batch-0001.jsonl
data/live_segments/2020/batch-0002.jsonl
```

构建脚本负责读取所有 batch，而不是依赖一个巨大共享文件。

## 跨来源去重边界

Collector Agent 负责发现和保存来源记录，不应仅凭标题相似自行决定两个来源就是同一场直播。

以下工作应由 identity/matching 工作单元统一处理：

- `live_id` 归并；
- 多来源关系；
- source video ID 证据；
- 日期/标题/时长/正文相似度；
- 冲突处理。

在身份尚未确认时，保留候选来源和证据，不要强行合并。

## 冲突处理

遇到以下情况，在 `coordination/conflicts/` 留记录：

- 两个 Agent 创建了可能重复的直播；
- 相同 source ID 指向不同日期；
- curated text 来源冲突；
- 时间轴冲突；
- schema 变更可能破坏已有数据；
- stale claim 接管。

不得静默覆盖另一 Agent 的结果。

## Agent ID

每次独立 Agent 运行必须选择一个足够唯一的 ID，例如：

```text
agent-20260912T231500Z-a17f
```

Agent ID 只用于协作审计，不是项目数据主键。

## 零成本

本协调方案只依赖 Git/GitHub 文件，不要求 Redis、数据库锁、队列服务或付费协调平台。

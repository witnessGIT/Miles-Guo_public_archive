# Miles-Guo_public_archive Multi-Agent Coordination

本目录是 `Miles-Guo_public_archive` 的 Git 原生多 Agent 协作协议。

当前工作流版本：

```text
continuous-worker-v2
```

机器可读版本见：

```text
coordination/WORKFLOW.json
```

详细运行策略见：

```text
coordination/CONTINUOUS_WORKER_V2.md
```

目标不是让 Agent 排队等待整批任务结束，而是让任何新 Agent 进入仓库后可以：

```text
发现可做任务
→ 原子领取
→ 执行
→ 验证
→ 提交
→ 发布完成/ready
→ 立即领取下一项
→ 持续循环
```

## 1. Git 是唯一协调事实源

不要通过聊天记忆判断“谁正在做什么”。

协调状态只看：

```text
coordination/WORKFLOW.json
coordination/claims/
coordination/completed/
coordination/ready/
coordination/conflicts/
coordination/WORK_QUEUE.jsonl
reports/pilot_selection.json
```

含义：

- `claims/`：谁已经领取任务；
- `completed/`：哪个任务已经完成；
- `ready/`：某个 Pilot case 已完成哪一阶段，可以被下游立即处理；
- `conflicts/`：并发、身份、来源、时间轴、stale takeover 等冲突证据；
- `WORKFLOW.json`：当前工作流版本与迁移规则。

## 2. 新 Agent 固定启动动作

必须先读：

```text
AGENTS.md
coordination/CONTINUOUS_WORKER_V2.md
coordination/WORKFLOW.json
coordination/README.md
coordination/WORK_QUEUE.jsonl
docs/CURRENT_TASK.md
```

然后运行：

```bash
python scripts/next_task.py --list
```

不要自己猜下一步，也不要因为看到旧批次 `in_progress` 就等待。

`scripts/next_task.py` 会读取：

- 全局/兼容任务；
- Pilot case；
- claims / completed；
- per-case readiness；
- legacy batch 完成状态；

并生成当前真正可执行的任务。

## 3. 新任务默认连续工作

从 `continuous-worker-v2` 开始，新 claim 默认包含：

```json
{
  "workflow_mode": "continuous-worker-v2",
  "continue_after_finish": true
}
```

完成一项任务后，只要还有安全、合法、可执行的任务，Agent 必须刷新 Git 状态并继续领取下一项。

完成一场直播、一个 batch 或一个 commit 都不是停止理由。

### 合法停止条件

仅以下情况可以停止：

```text
PROJECT_COMPLETE
USER_RECALL
NO_ELIGIBLE_WORK
HUMAN_DECISION_REQUIRED
SAFETY_OR_ACCESS_BLOCK
HOST_STOP
```

定义见 `coordination/CONTINUOUS_WORKER_V2.md`。

## 4. 重要现实限制：Git 不能主动唤醒被平台挂起的 Agent

仓库可以保证：

- 新 Agent 进来立即知道做什么；
- 运行中的 Agent 完成后继续领任务；
- 所有状态永久保存在 Git；
- 任意新 Agent 都能无聊天记忆接续项目；
- stale claim 可以审计并接管。

但 Git/GitHub 本身不能强制 ChatGPT/Work/Codex 在宿主平台已经暂停或结束会话后自行“复活”。

如果运行环境允许长驻进程，可使用：

```bash
python scripts/next_task.py \
  --watch \
  --claim \
  --agent-id agent-<UTC>-<random> \
  --poll-seconds 60
```

它会持续检查新任务，直到出现可执行任务后领取。但宿主平台仍可能终止该进程。

因此本项目采用：

```text
运行中持续工作
+
Git 永久可恢复状态
+
新 Agent 自动接续
```

而不是虚假假设“Git 能唤醒已终止会话”。

## 5. 已有任务完全兼容，不中断

`continuous-worker-v2` **只从新 claim 开始生效**。

已有有效 claim 不重命名、不删除、不抢占、不重新拆分。

没有 `workflow_mode` 字段的旧 claim 视为：

```text
legacy-grandfathered
```

例如当前已领取的：

```text
P6-PILOT-MIDDLE-B001
P6-PILOT-LATE-B001
```

继续由原 Agent 完成。

原 Agent 完成当前任务后，下一次 claim 自动进入 `continuous-worker-v2`。

## 6. 流水线任务是未来默认模式

Pilot case 独立流转：

```text
COLLECT + IDENTITY
        ↓
collection ready
        ↓
ALIGN
        ↓
alignment ready
        ↓
AUDIT
        ↓
audit ready
```

任务 ID：

```text
S-COLLECT-PILOT-E001
S-ALIGN-PILOT-E001
S-AUDIT-PILOT-E001
```

不同 case 互不等待。

例如 `PILOT-E001` 已采集完成，它的 ALIGN 可以立即开始，即使 `PILOT-M009` 尚未采集。

## 7. Readiness marker 是下游解锁机制

每个 case、每个阶段使用独立文件：

```text
coordination/ready/collection/PILOT-E001.json
coordination/ready/alignment/PILOT-E001.json
coordination/ready/audit/PILOT-E001.json
```

不要通过一个共享 status JSONL 管理全部直播。

优点：

- Git 冲突低；
- 单场完成即可解锁；
- 多 Agent 可并行；
- 状态可审计；
- 新 Agent 可准确恢复。

## 8. 原子领取规则

领取任务前必须创建：

```text
coordination/claims/<TASK_ID>.json
```

本地工作环境：

```bash
python scripts/next_task.py \
  --claim \
  --agent-id agent-<UTC>-<random>
```

或指定任务：

```bash
python scripts/next_task.py \
  --claim \
  --task S-ALIGN-PILOT-E001 \
  --agent-id agent-<UTC>-<random>
```

claim 本地创建后，必须立刻 commit + push。

如果 push 时发现别人已抢先：

1. 不覆盖；
2. 删除自己失败的本地 claim；
3. pull 最新 `main`；
4. 再次运行 `next_task.py --claim`；
5. 领取另一项继续工作。

GitHub API Agent 直接通过创建新文件实现同样的原子锁；文件已存在即认领失败。

## 9. 完成任务后立即继续

先提交并 push 真正的输出，再运行：

```bash
python scripts/next_task.py \
  --finish <TASK_ID> \
  --agent-id <same-agent-id> \
  --outputs <path1> <path2> \
  --validation "真实执行过的验证"
```

streaming collection 还要传：

```bash
--live-id LIVE_YYYYMMDD_NNN
```

该命令会创建：

```text
coordination/completed/<TASK_ID>.json
```

并在需要时创建 readiness marker。

push 后马上继续：

```bash
python scripts/next_task.py --claim --agent-id <same-agent-id>
```

## 10. Legacy Middle/Late Agent 如何在不中断现有任务的情况下解锁新流水线

已有大批次 Agent 不需要放弃当前 P6 claim。

只要其中某一场已经真实整理完成，就可以执行：

```bash
python scripts/next_task.py \
  --mark-ready collection \
  --case-id PILOT-M001 \
  --agent-id <legacy-claim-owner> \
  --live-id LIVE_20200323_001 \
  --outputs ... \
  --validation "source identity and provenance verified"
```

这不会结束整个 Middle batch，只会创建：

```text
coordination/ready/collection/PILOT-M001.json
```

于是另一个 Agent 可马上领取：

```text
S-ALIGN-PILOT-M001
```

而原 Middle Agent 继续做 M002、M003……

这正是“现有工作不受影响，新任务开始采用新模式”的兼容桥梁。

## 11. 数据拆分规则

未来默认一场直播一组独立文件：

```text
data/live_videos/2022/LIVE_20220511_001.json

data/live_segments/2022/LIVE_20220511_001.jsonl

data/sources/gwins/LIVE_20220511_001.json
data/sources/ghot/LIVE_20220511_001.json
data/sources/gettrsearch/LIVE_20220511_001.json
```

已有 batch JSONL 可以保留兼容，不强制破坏性迁移。

新的并行任务不要让多个 Agent 同时 append 一个大 JSONL。

## 12. COLLECT 完成标准

至少保留：

- seed/source page；
- source site/page/video/post ID；
- title/date/duration 等真实字段；
- GWINS/GHOT/原平台关系；
- curated / ASR / mixed provenance；
- identity evidence；
- canonical live ID 或明确 unresolved；
- retrieved/verified 状态。

不得用失败搜索证明 `GWINS-only` / `GHOT-only`。

不得仅按日期或标题相似合并直播。

## 13. ALIGN 完成标准

单 case collection-ready 后即可开始。

优先：

```text
source curated timestamp
↓
GHOT ASR/time-axis monotonic fuzzy alignment
↓
local ASR only when public timing insufficient
↓
manual playback review
```

保存：

```text
text_curated
text_asr
start_sec
end_sec
curated_source_id
asr_source_id
time_source_id
alignment_method
alignment_quality
playback_verified
review_status
```

禁止伪造 `end_sec`、FPS、frame 或 playback verification。

## 14. AUDIT 增量进行

Audit 不再等待全部 Alignment。

每个已对齐 case 都可以立刻抽查。

Pilot 总门槛仍为至少 60 个真实 segment 的 playback audit，并满足：

```text
false merge ≈ 0
>=90% locatable audited segments: error <= 3 sec
>=98% locatable audited segments: error <= 8 sec
```

未实际播放检查 = `unverified`，不能算 pass。

## 15. SQLite 不是流水线锁

`data/` 是 Git 真源。

SQLite 是：

```text
database/Miles-Guo_public_archive.sqlite3
```

可重建查询产物。

采集/对齐 Agent 不需要等待 SQLite Agent。

安全时周期性执行：

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

最终 aggregate SQLite/FTS gate 不应阻塞前面的 per-case 工作。

## 16. Stale claim / 接管

默认 stale 观察阈值仍为 2 小时，但超过时间不等于自动失活。

接管前必须检查：

- claim 后有没有新 commit；
- 输出是否持续形成；
- completed 是否已出现；
- 是否有证据表明原 Agent 仍在推进。

确认失活后创建：

```text
coordination/conflicts/<TASK_ID>-takeover-<agent-id>.json
```

记录旧 Agent、原因、检查时间，再继续。

不得仅因为 Agent 在 UI 中看似“沉睡”就抢任务。

## 17. 最终唯一全局等待点

COLLECT / ALIGN / AUDIT / DB rebuild 尽量并行。

真正需要等整个 Pilot 的只有：

```text
P10-PILOT-DECISION
```

只有 Pilot 样本、SQLite、FTS、60-segment audit、false-merge 和时间误差门槛都有真实证据后，才允许决定：

```text
FULL_ARCHIVE: YES / NO
```

## 18. Agent ID

每次独立 Agent 运行使用唯一 ID：

```text
agent-20260913T001500Z-a17f
```

Agent ID 只用于协作审计，不是档案数据主键。

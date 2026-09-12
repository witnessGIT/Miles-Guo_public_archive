# Miles-Guo_public_archive Multi-Agent Coordination

本目录是 `Miles-Guo_public_archive` 的 Git 原生多 Agent 协作协议。

目标不是让 Agent 排队等整批任务结束，而是建立持续流水线：**任何 Agent 进入仓库，都能立即发现当前可做任务，原子认领，完成后解锁下一阶段，并继续领取下一项。**

## 1. Git 是协调事实源

不要依赖聊天记忆判断谁正在做什么。

协调状态只看：

```text
coordination/claims/
coordination/completed/
coordination/ready/
coordination/WORK_QUEUE.jsonl
reports/pilot_selection.json
```

`claims/` = 谁正在做。

`completed/` = 哪个任务已经完成。

`ready/` = 某个 Pilot case 已经完成哪一阶段，可以被下游立即处理。

## 2. 每个 Agent 的固定启动动作

```bash
python scripts/next_task.py --list
```

不要自己猜下一步，也不要因为看到某个旧批次 `in_progress` 就等待。

`scripts/next_task.py` 会同时读取：

- `WORK_QUEUE.jsonl` 中的全局/兼容任务；
- `reports/pilot_selection.json` 中的 Pilot case；
- claims / completed；
- per-case readiness marker；
- 已完成的 legacy Pilot batch。

然后生成当前真正可执行的任务。

## 3. 流水线任务是默认模式

Pilot case 独立流转：

```text
COLLECT + IDENTITY
        ↓
ALIGN
        ↓
AUDIT
```

任务 ID：

```text
S-COLLECT-PILOT-E001
S-ALIGN-PILOT-E001
S-AUDIT-PILOT-E001
```

不同 case 互不等待。

例如 `PILOT-E001` 已采集完成后，它的 ALIGN 可以立即开始，即使 `PILOT-M009` 还完全没有采集。

## 4. Readiness marker：下游解锁机制

不要靠一个共享 status JSONL 判断进度。

每个 case、每个阶段使用独立文件：

```text
coordination/ready/collection/PILOT-E001.json
coordination/ready/alignment/PILOT-E001.json
coordination/ready/audit/PILOT-E001.json
```

独立文件的好处：

- 不同 Agent 不需要同时编辑一个状态表；
- Git 冲突小；
- 某一场一完成即可解锁下一阶段；
- readiness 本身可审计。

推荐 marker 字段：

```json
{
  "project": "Miles-Guo_public_archive",
  "case_id": "PILOT-E001",
  "live_id": "LIVE_20170523_001",
  "stage": "alignment",
  "ready_at": "ISO-8601 timestamp",
  "task_id": "S-ALIGN-PILOT-E001",
  "agent_id": "agent-...",
  "result_commit": "commit sha",
  "outputs": ["data/live_segments/2017/LIVE_20170523_001.jsonl"],
  "validation": "what was really checked"
}
```

## 5. 任务认领：原子锁

领取前必须创建：

```text
coordination/claims/<TASK_ID>.json
```

本地工作环境推荐：

```bash
python scripts/next_task.py \
  --claim \
  --agent-id agent-<UTC>-<random>
```

或：

```bash
python scripts/next_task.py \
  --claim \
  --task S-ALIGN-PILOT-E001 \
  --agent-id agent-<UTC>-<random>
```

### 关键并发规则

脚本在本地创建 claim 后，**必须马上 commit + push**，然后才能开始耗时工作。

真正的全局锁是 main 上可见的 claim 文件。

如果 push 失败，因为另一个 Agent 已经抢先提交同一 claim：

1. 不覆盖；
2. 删除自己失败的本地 claim；
3. pull 最新 main；
4. 再运行 `next_task.py --claim`；
5. 领取另一个任务继续做。

通过 GitHub API 工作的 Agent，直接用“创建新文件”作为原子锁；文件已存在即认领失败。

## 6. 完成任务后不要停

先提交并 push 真正的数据/代码/报告输出。

然后运行：

```bash
python scripts/next_task.py \
  --finish <TASK_ID> \
  --agent-id <same-agent-id> \
  --outputs <path1> <path2> \
  --validation "真实执行过的验证"
```

如果是 collection streaming task，还必须提供：

```bash
--live-id LIVE_YYYYMMDD_NNN
```

该命令会创建：

```text
coordination/completed/<TASK_ID>.json
```

并对 streaming task 创建相应 readiness marker。

提交并 push 这些 coordination 文件后：

```bash
python scripts/next_task.py --claim --agent-id <agent-id>
```

继续下一项。

**正常 Agent 不应该完成一场就自动退出。只要还有安全可执行任务，就继续领。**

## 7. Legacy 大批次兼容规则

仓库早期采用过：

```text
P6-PILOT-EARLY-B001
P6-PILOT-MIDDLE-B001
P6-PILOT-LATE-B001
```

每个任务一次处理 9 场。这种模式会导致下游等待，因此不再作为未来默认方式。

当前已经存在的有效 Middle/Late claim 不应被新 streaming collector 重复采集。

`next_task.py` 会在有效 legacy batch claim 存在期间抑制对应组的 `S-COLLECT-*` 任务。

但 legacy collector 不需要等 9 场全部结束。每完成其中一场，就应该立即写：

```text
coordination/ready/collection/<PILOT_CASE_ID>.json
```

这样其他 Agent 立刻可以领取该 case 的 ALIGN。

Legacy batch 全部完成后，即使没有逐场 marker，`next_task.py` 也会把对应组视为 collection-ready，并生成 per-case ALIGN 工作。

## 8. 数据文件拆分规则

长期默认：**一场直播 / 一个 case 一组独立文件。**

推荐：

```text
data/live_videos/2022/LIVE_20220511_001.json

data/live_segments/2022/LIVE_20220511_001.jsonl

data/sources/gwins/LIVE_20220511_001.json
data/sources/ghot/LIVE_20220511_001.json
data/sources/gettrsearch/LIVE_20220511_001.json
```

当前已有 batch JSONL 可以保留兼容，不要求破坏性重写。

新的并行工作不要让多个 Agent 同时 append 同一个大 JSONL。

汇总、SQLite build、导出由脚本读取所有独立文件完成。

## 9. COLLECT 阶段完成标准

Collection case 不是“页面打开过”就完成。

至少应保存：

- seed/source page；
- source site/page/video/post ID；
- title/date/duration 等实际存在字段；
- GWINS/GHOT/平台来源关系；
- curated / ASR / mixed provenance；
- identity evidence；
- canonical live ID 或明确 unresolved；
- retrieved/verified 状态。

不得用失败搜索证明 `GWINS-only` / `GHOT-only`。

不得仅按日期或标题相似合并直播。

## 10. ALIGN 阶段完成标准

单 case collection-ready 后即可做，不等其它 case。

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

不要伪造 `end_sec`、FPS、frame 或 playback verification。

## 11. AUDIT 阶段增量进行

Audit 不再等所有 Alignment 完成。

每个已对齐 case 都可以立刻被抽查。

Pilot 总门槛仍然是至少 60 个真实 segment 的 playback audit，并满足：

```text
false merge ≈ 0
>=90% locatable audited segments: error <= 3 sec
>=98% locatable audited segments: error <= 8 sec
```

未实际播放检查的 segment = `unverified`，不能算 pass。

## 12. SQLite 不作为流水线锁

`data/` 是 Git 真源。

SQLite 是：

```text
database/Miles-Guo_public_archive.sqlite3
```

可重建查询产物。

任何 Agent 采集/对齐时都不需要等待 SQLite Agent。

安全时可以周期性运行：

```bash
python scripts/build_db.py
python scripts/validate_db.py
```

最终 P8/P10 负责 aggregate gate；它们不能成为前面 case 工作的全局锁。

## 13. Stale claim / 接管

默认 stale 观察阈值仍为 2 小时，但时间超过 2 小时并不自动等于失活。

接管前检查：

- claim 后有没有新 commit；
- 对应输出有没有持续形成；
- completed 是否已经出现；
- 是否能判断原 Agent 仍在推进。

确认失活后创建：

```text
coordination/conflicts/<TASK_ID>-takeover-<agent-id>.json
```

记录旧 Agent、原因、检查时间，再继续。

不得抢占有效 claim。

## 14. 最终唯一全局等待点

前面的 COLLECT / ALIGN / AUDIT / DB rebuild 都应尽可能流水并行。

真正需要等待整个 Pilot 的只有最终决策：

```text
P10-PILOT-DECISION
```

只有在 Pilot 样本、SQLite、FTS、60-segment audit、false-merge 和时间误差门槛都有真实证据后，才允许决定：

```text
FULL_ARCHIVE: YES / NO
```

## 15. Agent ID

每次独立运行使用足够唯一的 ID：

```text
agent-20260913T001500Z-a17f
```

Agent ID 只是协作审计标识，不是档案数据主键。

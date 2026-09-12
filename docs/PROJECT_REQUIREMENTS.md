# Miles-Guo_public_archive Project Requirements

本文件保存用户完整任务要求，已按后续命名规范统一项目名、数据库名及 segment 六位编号。命名和工作流程详见 NAMING_AND_WORKFLOW.md；所有 agent 开工前必须阅读这两份文件。

你现在负责一个独立项目，目标是：

**分析以下三个网站中郭先生直播相关的视频、文字稿、时间信息和来源关系，并建立一个可长期检索、可供其它项目直接读取的 SQLite 档案数据库，同时把代码、结构化源数据、schema 和构建产物保存到我的 GitHub。**

目标网站：

1. https://www.gwins.org/
2. https://ghot.ai/
3. https://gettrsearch.com/

当前阶段不是做视频制作。

当前阶段只做：

**网站结构分析 → 数据源识别 → 统一数据模型 → 小规模真实采集验证 → SQLite 建库 → Git 保存。**

---

# 一、总体目标

最终建立：

```text
Miles-Guo_public_archive
```

第一阶段只整理：

**郭先生直播相关内容**

未来数据库还要能扩展：

- 直播
- 视频
- 文字稿
- 推文/X
- GETTR帖子
- 文章
- 图片
- 采访
- 历史遗失资料

因此数据库设计不要绑死“视频制作”。

它首先是一个：

**可检索历史数字档案库。**

---

# 二、本阶段必须完成的产物

最终 GitHub 仓库中至少包含：

```text
README.md

docs/
  SITE_ANALYSIS.md
  DATA_MODEL.md
  DATA_QUALITY.md

schema/
  schema.sql

scripts/
  analyze_sources.py
  build_db.py
  validate_db.py

data/
  live_videos/
  live_segments/
  sources/

database/
  Miles-Guo_public_archive.sqlite3

reports/
  pilot_report.md
```

如果 SQLite 文件过大，不要强行继续提交巨大二进制文件。

当前 Pilot 阶段数据库应该很小，可以直接提交。

长期方案：

```text
结构化 JSONL = Git 中的源数据
SQLite = 构建产物
```

---

# 三、第一步：先分析三个网站，不要立刻大规模抓取

首先分别分析：

## A. GWINS

确认：

- 郭先生直播内容入口在哪里；
- 列表页结构；
- 详情页结构；
- 是否有分页；
- 是否有日期；
- 是否有标题；
- 是否有人工文字稿；
- 文字稿中是否自带时间码；
- 是否包含 GETTR / Rumble / YouTube 等视频地址；
- 是否有人物、公司、组织、国家、关键词等结构化信息；
- 是否可以通过稳定 URL 或页面 ID 唯一标识；
- 是否存在重复内容。

整理成：

```text
docs/SITE_ANALYSIS.md
```

明确列：

```text
GWINS
列表URL：
详情URL规则：
分页方式：
主键候选：
直播日期字段：
视频链接字段：
文字稿字段：
时间码字段：
人物字段：
机构字段：
其它可提取字段：
风险：
```

---

## B. GHOT

确认：

- 视频目录结构；
- 历史视频页面；
- 视频详情页；
- 日期；
- 标题；
- 时长；
- 视频原始来源；
- 是否存在逐句/分段转写；
- 转写是否有时间戳；
- 是否有精选片段；
- 是否可以找到原 GETTR/Rumble/其它平台 ID；
- URL 是否稳定；
- 页面数据是 HTML 还是前端 API 动态加载。

尤其需要分析：

**GHOT 的时间轴是否可以作为直播文字定位的重要来源。**

记录：

```text
转写时间粒度
时间码准确性
ASR质量
是否有全文
是否存在重复视频
```

---

## C. GettrSearch

确认：

- 搜索入口；
- 年份筛选；
- 长视频/短视频区分；
- 视频详情页；
- playvideo 页面；
- 是否能获得 GETTR video ID；
- 是否能获得原始 GETTR URL；
- 是否可以按日期检索；
- 是否有文字内容；
- 是否适合作为补漏源。

特别判断：

**GettrSearch 应该作为主数据源，还是只作为视频发现/补漏来源。**

---

# 四、不得假设三个网站上的一条记录就是三个不同直播

核心原则：

**同一场直播只能存在一个 live_id。**

例如：

```text
GWINS页面
GHOT页面
GettrSearch页面
GETTR原视频
Rumble镜像
```

可能实际上是：

```text
同一场直播
```

所以数据库必须支持：

```text
一个直播
↓
多个来源
```

---

# 五、建立统一直播 ID

格式：

```text
LIVE_YYYYMMDD_NNN
```

例如：

```text
LIVE_20220315_001
```

同一天第二场：

```text
LIVE_20220315_002
```

不得使用某个网站自己的 URL 作为主键。

---

# 六、数据库核心表

第一阶段至少建立：

```text
live_videos
live_sources
live_segments
archive_items
entities
item_entities
topics
item_topics
```

如果 Pilot 阶段为了简化，可以先完成前三张核心表，但 schema 必须考虑未来扩展。

---

# 七、live_videos

建议字段：

```text
id TEXT PRIMARY KEY

title TEXT
live_date TEXT
published_at TEXT

duration_sec REAL
fps REAL
width INTEGER
height INTEGER

language TEXT
speaker TEXT

status TEXT

created_at TEXT
updated_at TEXT
```

status：

```text
discovered
partial
ready
needs_review
source_missing
error
```

---

# 八、live_sources

一场直播可以有多个来源。

字段：

```text
id TEXT PRIMARY KEY
live_id TEXT NOT NULL

source_site TEXT
source_role TEXT

platform TEXT
source_video_id TEXT

url TEXT

priority INTEGER
status TEXT

last_verified_at TEXT
notes TEXT
```

source_site 示例：

```text
gwins
ghot
gettrsearch
gettr
rumble
youtube
other
```

source_role：

```text
archive_page
curated_transcript
asr_transcript
original_video
backup_video
search_index
```

例如：

```text
LIVE_20220315_001

GWINS
→ curated_transcript

GHOT
→ asr_transcript

GETTR
→ original_video

Rumble
→ backup_video
```

---

# 九、live_segments

这是最重要的表。

字段：

```text
id TEXT PRIMARY KEY
live_id TEXT NOT NULL

segment_index INTEGER

text_curated TEXT
text_asr TEXT
text_search TEXT
text_summary TEXT

start_sec REAL
end_sec REAL

start_frame INTEGER
end_frame INTEGER

fps_at_index REAL

topic_primary TEXT
topic_secondary TEXT

entities_json TEXT
keywords_json TEXT

alignment_quality REAL
alignment_method TEXT

source_verified INTEGER
review_status TEXT

created_at TEXT
updated_at TEXT
```

segment ID：

```text
LIVE_20220315_001_SEG_000001
```

---

# 十、三个网站的建议角色

不要预设结论，但重点验证以下假设：

## GWINS

可能更适合：

```text
人工整理文字稿
主题信息
人物/公司/国家信息
多平台视频链接
```

如果验证成立：

```text
text_curated
```

优先来自 GWINS。

---

## GHOT

可能更适合：

```text
视频目录
时间轴
逐句ASR
视频时长
原视频定位
```

如果验证成立：

```text
text_asr
start_sec
end_sec
```

优先参考 GHOT。

---

## GettrSearch

可能更适合：

```text
视频发现
历史补漏
GETTR定位
```

如果验证成立，不要求把它作为文字稿真源。

---

# 十一、文字稿不得相互覆盖

例如：

GWINS：

```text
text_curated
```

GHOT：

```text
text_asr
```

必须分别保存。

最终生成：

```text
text_search
```

用于全文搜索。

不得用机器稿覆盖人工稿。

不得用 AI 改写后的文字覆盖原文字段。

---

# 十二、时间码处理

每个可定位 segment 至少保存：

```text
start_sec
end_sec
```

如果能够获得真实视频 FPS：

再计算：

```text
start_frame
end_frame
fps_at_index
```

计算：

```text
start_frame = round(start_sec * fps)
end_frame = round(end_sec * fps)
```

但：

**时间码是主定位数据。**

帧号只是辅助数据。

---

# 十三、如果 GWINS 有章节时间，GHOT 有逐句时间

尝试实现：

```text
GWINS人工稿
+
GHOT ASR时间轴
↓
文本模糊对齐
↓
人工文字获得精确时间位置
```

优先使用：

```text
已有公开时间数据
```

只有现有数据无法可靠对齐时，才使用：

```text
faster-whisper
```

不要一开始重新转写所有直播。

---

# 十四、直播去重规则

需要设计一个统一匹配评分。

至少参考：

```text
日期
标题
source_video_id
GETTR ID
Rumble ID
视频时长
文本开头
```

建议：

```text
video_id完全一致
最高权重

日期完全一致
高权重

标题相似
中权重

时长接近
中权重
```

输出：

```text
match_score
```

规则建议：

```text
>=0.85
自动合并

0.65~0.85
needs_review

<0.65
不自动合并
```

必须避免：

```text
两个不同直播误合并
```

---

# 十五、Pilot阶段只处理小样本

不要立即处理全站。

第一轮：

```text
PILOT_BATCH
```

选择：

```text
20~30场直播
```

尽量跨不同年份。

如果网站历史覆盖允许，尽量选择：

```text
早期
中期
晚期
```

确保网站结构不同年代都能处理。

---

# 十六、Pilot必须包含以下情况

至少包含：

```text
GWINS + GHOT都有

只有GWINS

只有GHOT

GettrSearch可以找到但其它站缺失

有多个视频源

文字稿有时间码

文字稿无精确时间码
```

只有这样 Pilot 才有意义。

---

# 十七、建立 Git 友好源数据

不要把 SQLite 作为唯一真源。

每场直播建议生成 JSON。

例如：

```text
data/live_videos/2022/LIVE_20220315_001.json
```

segment 建议 JSONL：

```text
data/live_segments/2022/2022-03.jsonl
```

每行：

```json
{
  "id": "LIVE_20220315_001_SEG_000001",
  "live_id": "LIVE_20220315_001",
  "text_curated": "...",
  "text_asr": "...",
  "start_sec": 350.2,
  "end_sec": 402.8
}
```

Git 中的 JSON/JSONL 是长期源数据。

SQLite 通过：

```text
scripts/build_db.py
```

重建。

---

# 十八、SQLite必须可完全重建

必须做到：

```text
删除 database/Miles-Guo_public_archive.sqlite3
```

以后执行：

```bash
python scripts/build_db.py
```

能够从：

```text
data/
+
schema/
```

重新生成完整数据库。

如果做不到，架构不合格。

---

# 十九、全文搜索

SQLite 尽量启用：

```text
FTS5
```

建立：

```text
live_segments_fts
```

索引：

```text
text_curated
text_asr
text_search
```

必须能够执行类似查询：

```text
银行
香港
疫苗
美国
中共
战争
```

并快速返回相关 segment。

---

# 二十、未来扩展考虑

虽然当前只做直播，但 schema 不要阻止以后加入：

```text
Twitter/X
GETTR帖子
文章
采访
图片
网页快照
删除内容恢复
```

可以预留统一：

```text
archive_items
```

概念。

但是不要为了未来扩展把 Pilot 做得过度复杂。

直播核心数据必须先跑通。

---

# 二十一、来源可信度

每一条来源建议保留：

```text
source_level
```

未来等级：

```text
S0 原始发布源
S1 官方/原始镜像
S2 网页存档
S3 完整转载
S4 二手引用
S5 未验证
```

当前三个网站如果不是原始发布平台，不要标成 S0。

---

# 二十二、不要长期保存完整视频

本项目 GitHub 中禁止提交：

```text
.mp4
.mov
.webm
大音频文件
模型文件
缓存
```

只保存：

```text
URL
平台ID
时间码
文字
元数据
```

如果为分析临时下载视频：

处理结束后删除。

---

# 二十三、网站访问原则

只处理：

```text
正常公开可访问内容
```

不得：

- 绕过登录限制；
- 绕过验证码；
- 绕过付费墙；
- 绕过访问控制；
- 破解 DRM；
- 使用攻击性高频请求。

请求必须限速。

推荐：

```text
每个站点低并发
请求间隔
缓存已抓页面
失败重试
```

避免给站点造成压力。

---

# 二十四、必须记录采集来源

每条数据必须知道：

```text
从哪个网站来的
从哪个页面来的
什么时候抓取的
```

例如增加：

```text
retrieved_at
source_url
source_site
```

不能最终只剩一个文本，却不知道它来自哪里。

---

# 二十五、Pilot质量验证

至少随机抽：

```text
60个segment
```

检查：

1. 是否属于正确直播；
2. 日期是否正确；
3. 原文字是否对应；
4. start_sec 是否真的跳到相应位置；
5. URL是否可追溯；
6. 三站是否误合并。

目标：

```text
直播误合并率接近0

>=90%的可定位segment
时间误差 <=3秒

>=98%
时间误差 <=8秒
```

如果未达到：

不要进入全量。

---

# 二十六、输出 SITE_ANALYSIS.md

必须详细说明：

```text
三个网站各自的数据价值

各自缺点

列表结构

详情结构

分页方式

是否动态加载

是否有API端点

稳定ID是什么

文字从哪里取

时间码从哪里取

原视频从哪里取

站点间如何匹配

未来哪个站点挂掉会有什么影响
```

---

# 二十七、输出 DATA_MODEL.md

解释：

```text
为什么这样设计表

为什么一个直播对应多个来源

为什么text_curated和text_asr分开

为什么秒数比帧号更重要

为什么SQLite不是唯一真源

未来如何加入推特/GETTR等内容
```

---

# 二十八、输出 pilot_report.md

报告：

```text
分析到的直播总量估计：

GWINS Pilot覆盖：
GHOT Pilot覆盖：
GettrSearch Pilot覆盖：

成功识别同一直播数量：

存在冲突的直播：

Pilot直播数：

segment总数：

text_curated覆盖率：
text_asr覆盖率：
可精确定位率：

alignment >=0.90：
alignment 0.75~0.90：
alignment <0.75：

随机时间验证结果：

失效URL：
重复URL：
重复直播：
误匹配：

SQLite大小：
Git源数据大小：

主要问题：
解决建议：

是否建议进入全量：
YES / NO
```

---

# 二十九、GitHub要求

请在我的 GitHub 中新建一个独立仓库或使用我指定的档案仓库。

不要修改：

```text
witnessGIT/movie_production
```

当前任务是建立独立档案数据库。

如果我没有指定仓库名，优先建议：

```text
witnessGIT/Miles-Guo_public_archive
```

仓库初始化后：

```text
main
```

只放：

```text
代码
schema
文档
JSON/JSONL源数据
小型SQLite Pilot数据库
报告
```

不要提交大媒体文件。

每个重要阶段提交一次 commit。

commit 信息清晰，例如：

```text
chore: initialize archive schema

research: document three source sites

data: add pilot live archive batch

feat: build sqlite archive database

test: validate pilot archive integrity

docs: publish pilot findings
```

---

# 三十、不要在Pilot没完成前宣称“数据库已经完成”

必须区分：

```text
网站分析完成
Pilot完成
全量开始
全量完成
```

任何一阶段都必须真实说明状态。

---

# 三十一、最终验收查询

Pilot完成后必须展示以下真实查询结果：

### 查询1

```text
按日期列出某一天直播
```

### 查询2

```text
搜索一个关键词
```

返回：

```text
live_id
日期
原文
开始时间
结束时间
来源URL
```

### 查询3

根据：

```text
segment_id
```

找到：

```text
直播
原文
GHOT/GWINS/GettrSearch来源
原视频链接
时间码
```

### 查询4

随机抽一个 segment：

使用其：

```text
source_url
+
start_sec
```

验证确实能定位到相应内容。

---

# 三十二、当前阶段成功标准

当前任务成功不是：

“抓了很多网页。”

而是：

**建立了一套经过真实数据验证的统一档案模型。**

必须证明：

```text
GWINS
+
GHOT
+
GettrSearch
```

的数据能够合并成：

```text
一个直播ID
+
多个来源
+
高质量文字
+
可靠时间轴
+
可搜索SQLite
```

并且：

```text
未来 movie_production
```

能够直接读取这个数据库。

---

完成 Pilot 后停止全量扩张，先给我完整汇报：

1. 三个网站实际结构；
2. 它们之间有什么对应关系；
3. 最终 schema；
4. Git 仓库地址；
5. Pilot SQLite；
6. 数据质量；
7. 发现的问题；
8. 是否适合继续全量；
9. 全量预计应该采用什么策略。

除非 Pilot 数据已经证明模型可靠，否则不要直接跑完整历史档案。
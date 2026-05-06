# TODO（v0.6 及之后）

## 1. 抽成 3 个独立 skill（v0.6 优先）

把 oneday-onebook 内部 pipeline 拆成 3 个可独立调用的 skill，互不耦合。

### Skill 1 · `book-pool-score`（采集 + 评分）
- 输入：可选参数 `--refresh-pool`（强制重抓豆瓣，默认月级缓存）
- 流程：fetch_pool → filter_and_classify → LLM 思想密度评分（按 prompts/scoring-prompt.md）
- 输出：`scored-master.json`（增量更新，已评的复用 cache）
- 触发场景：每月一次手工 / cron 调用 / 池子枯竭时主动触发

### Skill 2 · `book-pick`（抽样选书）
- 输入：可选参数 `--seed N`（测试用）/ `--pool classic|contemporary`（指定池）
- 流程：从 `scored-master.json` 去重历史 → 按 70/25 池比例 + 评分平方加权抽 1 本
- 输出：今日选书 JSON（书名/作者/subject_id/pool/score/reason）+ 自动追加到 `_推过的书.md`
- 触发场景：日推送 cron / 用户手动 "今天选什么"

### Skill 3 · `book-deconstruct`（4 引擎拆书）
- 输入：书名 + 可选作者 / 或 douban subject URL / 或 `today.json`
- 流程：拉书评 → 4 引擎拆解（拆书/降秩/范畴提取/书评聚合）→ 写出 ~3000 字 markdown，按 v0.3 工具集（要求式+自检式）
- 输出：markdown 文件（私库 + 可选公库）
- 可选参数：
  - `--push-pages`：推到 oneday-onebook GitHub Pages
  - `--telegram`：通过 openclaw delivery 推送
  - `--atoms`：完成后调用 atoms 原子提取（见 todo 2）
- 触发场景：日推送 cron / 用户喊"拆 X 这本书" / 任何阅读场景

### 共享资源
- 三个 skill 共享一份 prompt 文件（在 `oneday-onebook/prompts/`，用软链接到 skill 目录）
- 避免双重维护

### v0.6 cron payload 简化
原来 200+ 行的 cron-daily.md → 简化成"调 skill 2 → 调 skill 3"两步。

---

## 2. 拆书结果接入 atoms 原子提取（v0.6 或 v0.7）

memory-work 已有 `_atoms/` 体系（P/C/M 原子图谱）+ `atomos-audit` skill。

oneday-onebook 每篇拆书完成后，可选触发：
- 把「新增范畴」段里的 5 条范畴 → 提取为 **C 原子**（concept）
- 把「三根力」段里的机理推导 → 提取为 **M 原子**（method）
- 把书本身（连同它的暗门和灵魂之问）→ 注册为 **P 原子**（pattern/case）

接通后效果：
- 每天一本书 → 大脑「范畴仓库」每日新增 5+ C 原子
- 范畴在 atoms 图谱里被审计、被链接、被复用
- 项目动机「扩范畴」从瞬时阅读 → 持久知识资产

调用方式（设想）：
```
/book-deconstruct 利维坦 --atoms
```
拆完后自动调用 `atom-extract` skill（待建）把范畴/机理写进 `_atoms/`。

---

## 3. 其他待办

- [ ] 评分 cache：scored-master.json 增量更新逻辑（已评的不重评）
- [ ] 月采集 cron job（节奏 A，每月 1 号 03:00）
- [ ] 跨域好书池（crossdomain，5%，从知识分子豆列拉）
- [ ] 用户偏好范畴过滤（"最近想多扩政治哲学/认知科学"）

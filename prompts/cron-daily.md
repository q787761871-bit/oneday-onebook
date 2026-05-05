# 日推送 cron payload prompt

> 这是 openclaw cron `oneday-onebook-daily` 每天 10:02 触发时给 isolated session agent 的指令。
> Agent 跑完 pipeline 后输出最终的 telegram 推送文本，由 openclaw delivery 系统自动推送。

---

## 环境提示

- isolated session 中 node/python3 可能不在 PATH，必须用绝对路径：
  - python3: `/usr/bin/python3` 或 `/opt/homebrew/bin/python3`
  - node: `/Users/jc/.volta/bin/node`
- 工作目录：`/Users/jc/Documents/oneday-onebook`
- 私库目录：`/Users/jc/myclaude/memory-work`
- 已推清单：`/Users/jc/myclaude/memory-work/01 你的项目/一天一本书/_推过的书.md`
- GitHub 仓库：q787761871-bit/oneday-onebook（公开）
- Pages 站点：https://q787761871-bit.github.io/oneday-onebook/

## 执行步骤

### 1. 重新过滤候选（去重历史）

```bash
cd /Users/jc/Documents/oneday-onebook
python3 scripts/filter_and_classify.py
```

读取 `data/pool-*.json`（最新一次月采集结果）→ 输出 `data/candidates-YYYY-MM-DD.json`，已自动 grep `_推过的书.md` 去重。

### 2. 思想密度评分（agent 自己做）

读 `prompts/scoring-prompt.md` 作为评分协议。**严格按 prompt 里的"强否决清单"和"原创度硬指标"执行——这是 v0.5 的关键质量门**。

**Prefilter（v0.5 收紧版）**：
- 只评 `tag:*` 来源的书（跳过纯 top250 — 那里小说太多）
- 且 `rating >= 8.8` 且 `votes >= 30`
- 通常 ~80 本（远少于 v0.4 的 250+，评分耗时压到 3-5 分钟）

为了不让单次 LLM 调用过载，**按池分批评分**：
- 喂一个 JSON 数组（含 name/author/publisher/year/oneliner/source/pool）
- 按评分 prompt 输出每本的 score 和 reason
- **保留 score >= 7 的**（注意是 7，不是 6——v0.5 提高门槛避免教材入选）

合并结果 → 写入 `data/scored-YYYY-MM-DD.json`。

### 3. 加权抽样

```bash
cat data/scored-YYYY-MM-DD.json | python3 scripts/pick_today.py > data/today.json
```

得到今天的书：name / author / subject_id / pool / score / reason / year / oneliner。

### 4. 拉书评素材（Engine D 准备）

并行尝试以下信源：

- **维基百科**（有英文版书时优先）：
  - `curl -s "https://r.jina.ai/https://en.wikipedia.org/wiki/<title>"`
  - 中文：`curl -s "https://r.jina.ai/https://zh.wikipedia.org/wiki/<title>"`
- **豆瓣评论**：
  - `curl -s "https://r.jina.ai/https://book.douban.com/subject/<subject_id>/reviews"`
  - 拉前几篇高赞长评
- **WebSearch**（如有此工具）：
  - `<书名> 书评`、`<author> 学术评论`、`<英文书名> review`

目标：3 篇立场分散（推崇 / 中立 / 否定）。**拉不到某种立场如实留白**——按 v0.2 设计允许。

把素材整理成结构化数据备用。

### 5. 跑 4 引擎拆解

按 v0.3 工具集（要求式 + 自检式约束）写 ~3000 字 markdown。

依次读：
- `prompts/engine-a-deconstruct.md` → 写「暗门」段（300 字）
- `prompts/engine-b-rank.md` → 写「三根力」段（每根 400-600 字，含反直觉案例 + 机理推导 + 推到极端）
- `prompts/engine-c-categories.md` → 写「新增范畴」段（5 条，每条 80-120 字）
- `prompts/engine-d-reviews.md` + 步骤 4 的素材 → 写「他者之眼」段（3 篇评论的机理深读）
- 最后写「一句话带走」（30-50 字金句）

**每根力写完后做自检**：
- 这段如果给一个完全没读过这本书的人看，他能否从我的话里推导出书的机理？
- 如果换一本完全不同的书，这段会显得生硬吗？（如果会，重写）
- 我用了的术语，是用术语解开机理还是替代机理？

### 6. 写两份 markdown

**私库版本**（原 frontmatter）：
```
/Users/jc/myclaude/memory-work/02 你的阅读/笔记/_dailybook/YYYY-MM-DD_<书名>.md
```

frontmatter:
```yaml
---
title: <书名>
author: <作者>
year: <出版年>
date: YYYY-MM-DD
source: 一天一本书 · v0.5 自动版
version: v0.3
tags: [...]
---
```

**公库版本**（jekyll frontmatter，slug 用拼音/英文短名）：
```
/Users/jc/Documents/oneday-onebook/_posts/YYYY-MM-DD-<slug>.md
```

frontmatter:
```yaml
---
layout: post
title: <书名>
subtitle: <灵魂之问 一句话>
author_name: <作者>
year: <出版年>
date: YYYY-MM-DD
slug: <slug>
tags: [...]
---
```

公库版本去掉 # H1 标题（jekyll post 自动渲染 title 为 H1）。

### 7. 更新已推清单

在 `_推过的书.md` 月度区块追加一行：

```markdown
| YYYY-MM-DD | <书名> | <作者> | v0.5 自动 | `02 你的阅读/笔记/_dailybook/YYYY-MM-DD_<书名>.md` |
```

### 8. push GitHub Pages

```bash
cd /Users/jc/Documents/oneday-onebook
git add .
git commit -m "daily: <书名>（YYYY-MM-DD）"
git push
```

GitHub Pages 自动部署，URL：
`https://q787761871-bit.github.io/oneday-onebook/YYYY/MM/DD/<slug>/`

### 9. 输出最终 telegram 文本

**不要调 message 或 send 工具**。openclaw delivery 系统会把你的最终回复自动推送到 telegram chat 8229232469。

**你的最终回复必须就是这条 telegram 文本**（不要加任何 meta 描述或解释）：

```
📖 今日推荐

《<书名>》 — <作者> · <出版年>
<灵魂之问 一句话>

→ https://q787761871-bit.github.io/oneday-onebook/YYYY/MM/DD/<slug>/
```

字数应该在 150-250 字符之间，远低于 telegram 4096 限制。

### 10. 更新 state

```bash
mkdir -p ~/.oneday-onebook
echo '{"lastRunAtMs": '$(date +%s000)', "lastBookName": "<书名>", "lastUrl": "..."}' > ~/.oneday-onebook/state.json
```

（最后一步可选，不影响推送）

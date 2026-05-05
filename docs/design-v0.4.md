---
title: 一天一本书 v0.4 设计
status: draft
created: 2026-05-06
---

# 一天一本书 v0.4

## 与 v0.3 的差异

| 项 | v0.3 | v0.4 |
|----|------|------|
| 选书方式 | 手工 | 半自动（采集 + 评分 + 加权抽样） |
| 信源 | 临时网页 | 豆瓣 Top 250 + 9 tag（哲学/政治哲学/社会学/经济学/心理学/人类学/科学/历史/文学批评） |
| 采集频率 | 每次手工 | 每月 1 次（节奏 A） |
| 推送频率 | 无 | 每天 1 次（节奏 B，10:02 / 同 bestblog） |
| 推送形态 | 无 | telegram 短消息 + GitHub Pages HTML 链接 |
| 沉淀位置 | 私库 `_dailybook/` | 私库 + 公开 GitHub Pages |

## 核心架构：双节奏分离

**节奏 A · 月采集**（每月 1 号 03:00，cron `0 3 1 * *`）
- Stage 1: `fetch_pool.py` → 更新 `pool-master.json`（subject_id 主键，已有跳过）
- Stage 2: `filter_and_classify.py` → 更新 `candidates-master.json`
- Stage 3: agent LLM 评分（增量，已评的复用 cache）→ `scored-master.json`

**节奏 B · 日推送**（每天 10:02，cron `2 10 * * *`）
- Stage 4: `pick_today.py` → 加权抽样 1 本
- Stage 5: agent 拉书评（维基 + 豆瓣 + WebSearch）
- Stage 6: agent 跑 4 引擎拆解 → ~3000 字 markdown
- Stage 7: agent 写入私库 `_dailybook/` + 公开 repo `_posts/`
- Stage 8: agent push 到 GitHub → Pages 自动部署
- Stage 9: agent curl telegram bot API 推送短消息（书名 + URL）
- Stage 10: 更新 `state.json`

## 紧急保险

`pick_today.py` 检测池子枯竭（剩余可推 < 50 本）时，主动触发一次采集，不等月初。

## HTML 站点

**托管**：GitHub Pages（基于 `q787761871-bit/oneday-onebook` 公开仓库）
**主题**：minima（Jekyll 默认博客主题）
**URL 模式**：`https://q787761871-bit.github.io/oneday-onebook/YYYY/MM/DD/<slug>/`
**首页**：自动列出所有 posts，按时间倒序

每日 markdown 同时写两份：
- `_dailybook/YYYY-MM-DD_<书名>.md`（私库，原 frontmatter）
- `_posts/YYYY-MM-DD-<slug>.md`（公开 repo，jekyll frontmatter，slug 用拼音/英文）

## 推送形态（修正版）

之前 R1 的 4 个候选（多条消息 / 改 delivery 源码 / cron 跑多次 / 自己 curl telegram）全部不需要——**HTML + URL 一刀解决**：

```
📖 今日推荐
《没有内容的人》 — 阿甘本 · 1970
当人获得"做任何事的自由"时，为什么反而陷入空虚？

→ https://q787761871-bit.github.io/oneday-onebook/2026/05/06/meiyou-neirong-de-ren/
```

约 200 字符，远低于 telegram 4096 限制。

## 工程哲学（沿用 v0.3）

- 核心产品力在 prompt 自身，不在样本积累
- 不用 few-shot 模仿、不用伪禁令
- 约束方式只用要求式 + 自检式

## 版权策略变更（v0.4 新）

v0.2 原决策："每日完整解读不放公开 repo，避免书评引用版权风险"。
v0.4 修正：每日完整解读公开发布到 GitHub Pages。

理由：
- 每篇引用真实书评最多 2-3 句，标注出处，符合合理使用
- 主体（~95%）是项目自有的转化分析（机理还原），属 transformative use
- 风险评估为低（已与项目所有者确认）

## 路线图

| 版本 | 范围 | 状态 |
|------|------|------|
| v0.1 | 3 引擎 + 800 字 + 手工 | ✅ superseded |
| v0.2 | + 书评引擎 + 1200 字 + agent-reach | ✅ superseded |
| v0.3 | + 机理式还原 + Prompt 工具集 + 字数解放 | ✅ superseded |
| v0.4 | + 半自动选书 + GitHub Pages + telegram 推送 + 双节奏分离 | 🚧 当前 |
| v0.5 | + cron 自动化 + 学者豆列豆豆乱（crossdomain 池） + 用户偏好范畴过滤 | ⏳ |

## 自动化进度（v0.4 阶段）

- [x] 采集脚本 `fetch_pool.py`（人工触发）
- [x] 过滤脚本 `filter_and_classify.py`（人工触发）
- [x] 加权抽样脚本 `pick_today.py`（评分手工填）
- [x] HTML 站点（GitHub Pages + minima）
- [x] 首两篇示例上线（实践论 + 没有内容的人）
- [ ] LLM 评分自动化（v0.5）
- [ ] cron job 配置（v0.5）
- [ ] telegram bot 推送（v0.5）
- [ ] 月采集 + 日推送两个 cron（v0.5）

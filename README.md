# oneday-onebook

> 人无法感知到认知以外的事情。每天补一本书的「思想 + 方法论」，扩展大脑「范畴仓库」的量级。

A daily book deconstruction system that uses LLM prompt engineering to extract the **structural ideas** and **methodologies** from one book per day — not summaries, but mechanical reconstructions that let readers see *how* the book works underneath.

## 不一样的地方

市面上的 AI 读书产品大多在做「提炼精华」——把一本书压缩成几条要点。这条路 LLM 默认就会，问题是**提炼的本能是缩短，缩短就脱水，脱水就丢机理**。读完只剩口号，没有"扩范畴"的效果。

本项目反着走，叫「机理式还原」：不缩短，而是**把书里的每个核心判断还原到它的内在因果**——为什么必然如此、推到极端会怎样、在反直觉案例下怎么成立。让读者读完后，脑子里多的不是"这本书说了 X"，而是"X 必然是这样，因为它的机理是 Y"。

## 四引擎

每本书的解读由四个 prompt 引擎串联产出：

| Engine | 名字 | 任务 |
|--------|------|------|
| A | 拆书 | 找到作者夜不能寐的那个问题（暗门） |
| B | 降秩 | 把书降到几根独立的、不可再分的力 |
| C | 范畴提取 | 蒸馏出书里没明说但能从机理析出的新概念 |
| D | 书评聚合 | 引入 3 篇真实他者书评，立场分散，机理式深读 |

详见 [`prompts/`](prompts/)。

## 输出形态

```
# {书名} —— {一句话灵魂之问}

## 暗门
{作者写作时的真实处境 + 灵魂之问}

## 三根力
### 力一：...（含反直觉案例 + 机理推导 + 推到极端的延伸）
### 力二：...
### 力三：...

## 新增范畴
{从机理蒸馏出来的新概念，每条含定义+日常用法}

## 他者之眼
[推崇 / 建设性批评 / 否定 三类立场各 1 篇真实书评]

## 一句话带走
```

字数：目标 2500，深度优先，无硬限制。

示例输出：[`examples/2026-05-05_on-practice.md`](examples/2026-05-05_on-practice.md) — 《实践论》。

## 工程哲学（核心）

**核心产品力在 prompt 自身，不在样本积累。**

- ❌ **不用 few-shot 示范** —— 临时示范一旦固化为 few-shot example，prompt 就被那一个样本绑架，跨书鲁棒性会崩。
- ❌ **不用伪禁令** —— "禁止 X 是 Y 句式""禁止用现成术语"这类听起来狠的禁令，操作上不可执行、误伤合理用法、让 LLM 变拘谨反而失真。
- ✅ **用要求式 + 自检式约束塑造**——给方向 + 给检查清单，不绑手脚。让 prompt 自己能引导出深度。

详见 [`docs/design-v0.3.md`](docs/design-v0.3.md)。

## 怎么用

当前版本 v0.3 是**手工流程**——把书名喂给一个支持长上下文的 LLM（Claude Opus / GPT-5 等），按顺序运行 4 个引擎，最后按输出格式整合。

```
1. 用 prompts/engine-a-deconstruct.md 跑一遍，得到「暗门」
2. 用 prompts/engine-b-rank.md 跑一遍，得到「三根力」
3. 用 prompts/engine-c-categories.md 跑一遍，得到「新增范畴」
4. 用 prompts/engine-d-reviews.md + 真实书评信源，得到「他者之眼」
5. 按 README 输出形态整合 → 一篇 2500 字左右的解读
```

v0.4 会接入自动化（书目源选书 → 自动拉书评 → 自动整合 → 推送）。

## 致谢

本项目的 Engine A（拆书）和 Engine B（降秩）基于**李继刚**老师的 prompts：

- Engine A 基于 `jigang:references:拆书`
- Engine B 基于 `ljg-rank`

李继刚老师的 prompt 工艺是中文 prompt 工程领域的重要参考，本项目仅在他的工作基础上做了**领域应用** —— 把它们组合进"读书"这个具体场景。两个 engine 文件顶部都标注了原作者和出处。

如果李继刚老师对本项目的引用方式有任何意见，请通过 issue 联系，我们将立即调整。

Engine C / D 是项目自有，与李继刚老师无关。

## License

MIT — 见 [LICENSE](LICENSE)。

注意：MIT 仅覆盖本项目自有的代码、设计文档、和 Engine C/D 的 prompt。Engine A/B 的 prompt 版权归原作者李继刚所有，本仓库仅作引用展示。

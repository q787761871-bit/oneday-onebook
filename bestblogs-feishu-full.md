---

📰 **AI 日报** · 2026-05-09

今日可以说是「Agent 基础设施日」——Anthropic 为 Managed Agents 推出记忆与梦想机制、Codex 直接嵌入 Chrome 浏览器、Asana 构建 AI 队友、Replit 开源智能体评估基准 ByteBench……AI 智能体正从「单一任务执行者」向「持久协作的系统组件」集体进化。与此同时，OpenAI 的 GPT-Realtime-2 将语音智能体从 I/O 封装推向全双工推理系统，EMO 则在 MoE 架构中开辟了语义模块化的新方向。

📊 共 15 篇精选 · 预计 8 分钟读完

---

1. **Anthropic 推出面向自学习智能体的记忆与梦想机制**
来源：https://www.bestblogs.dev/en/video/aa252bd

概要：Anthropic 为其 Managed Agents API 引入了记忆与梦想两个新原语，使智能体能够以文件系统方式管理自身知识，并通过后台异步整理实现持续自学习。

亮点：
- 智能体记忆被建模为文件系统，Claude 可用 bash 等标准工具自主管理知识，无需受限的预定义结构
- 「梦想」是一项后台异步（带外）进程，分析近期会话记录以识别共享模式、常见错误和低效之处，自动整理记忆存储
- 系统支持企业级多智能体协作，包含权限范围、内容哈希乐观并发和完整版本审计历史

🔗 [阅读全文](https://www.bestblogs.dev/en/video/aa252bd)

---

2. **Codex 现已直接集成到 macOS 和 Windows 上的 Chrome 浏览器**
来源：https://www.bestblogs.dev/en/video/9e0a0be

概要：OpenAI 推出 Codex Chrome 扩展，AI 直接在用户真实浏览器会话中运行，利用活跃配置文件、Cookie 和代码执行完成复杂并行自动化任务。

亮点：
- 扩展在用户实际浏览器中运行，复用登录会话和 Cookie，可操作经过身份验证的 Web 应用
- 可跨多个标签页并行工作，创建独立标签页组避免干扰用户
- 通过直接代码执行控制 Chrome，取代传统「截图-推理-移动鼠标」的脆弱的视觉自动化

🔗 [阅读全文](https://www.bestblogs.dev/en/video/9e0a0be)

---

3. **Asana 详解如何利用 Claude Managed Agents 构建「多人协作」AI 队友**
来源：https://www.bestblogs.dev/en/video/351985c

概要：Asana 详述了如何利用 Claude Managed Agents 构建在「多人协作模式」下运行的 AI 队友，利用 Workgraph 深入组织上下文，在人工监督下执行复杂协作任务。

亮点：
- AI 队友作为团队中持久的成员运作，共享上下文、保留企业记忆，遵守 RBAC 权限控制
- Workgraph 提供 17 年积累的组织目标、项目和人员关系数据作为智能体的上下文基础
- 用户通过评论等自然界面与 AI 队友交互，未来智能体将根据项目模式主动预测需求、建议任务

🔗 [阅读全文](https://www.bestblogs.dev/en/video/351985c)

---

4. **思考杠杆：借助 Claude 扩展测试时计算**
来源：https://www.bestblogs.dev/en/video/7638bc6

概要：Anthropic 产品经理解释了 Claude 如何通过测试时计算扩展推理智能，介绍了「努力度拨盘」等用户控制手段以及向自适应思考的演进。

亮点：
- Claude 的 token 消耗分为思考、工具调用和文本三类，思考 token 代表用于推理的内部独白
- 「努力度拨盘」（低/高/超高）和「任务预算」让用户精细控制质量、成本和延迟的权衡
- 「自适应思考」允许 Claude 自主交错推理、工具使用和文本生成，突破了僵化的行动序列

🔗 [阅读全文](https://www.bestblogs.dev/en/video/7638bc6)

---

5. **EMO：面向涌现模块化的专家混合预训练**
来源：https://www.bestblogs.dev/en/article/44111737

概要：Allen AI 团队提出 EMO，一种通过文档级路由约束进行预训练的新型 MoE 模型，使专家聚焦语义领域，仅用 12.5% 的专家即可在特定任务上接近完整模型性能。

亮点：
- 文档中所有 token 被强制路由到共享专家池的内部子集，这种弱监督信号使模块化结构自然涌现
- 专家聚焦语义领域（如「健康」「政治」）而非表层句法特征，支持选择性部署
- 全局负载均衡解决了与文档级路由约束的冲突，使不同文档使用不同的专家池

🔗 [阅读全文](https://www.bestblogs.dev/en/article/44111737)

---

6. **智能体搜索与上下文工程**
来源：https://www.bestblogs.dev/en/video/e00501e

概要：Elastic 的 Leonie Monigatti 讲解了智能体驱动的搜索如何取代固定 RAG 管线，强调详细工具描述对构建可靠 AI 智能体的关键作用。

亮点：
- 上下文工程约 80% 是智能体搜索——AI 自主决定何时、如何检索，比固定 RAG 管线更灵活
- 详细的工具描述（含触发条件、使用场景、与其他工具的关系）是防止智能体误用的最重要因素
- shell/bash 等通用工具允许通过终端命令灵活与本地文件、数据库和网络交互

🔗 [阅读全文](https://www.bestblogs.dev/en/video/e00501e)

---

7. **在 OpenAI 安全运行 Codex**
来源：https://www.bestblogs.dev/en/article/517d3e21

概要：OpenAI 详细介绍了在企业开发工作流中安全部署 Codex 的多层安全架构，包括沙箱、审批策略、网络规则管理和智能体原生遥测。

亮点：
- Codex 通过沙箱定义文件写入和网络访问边界，审批策略要求高风险操作人工审核
- 网络访问通过代理管理，允许/拒绝/需审核三层策略，缓存网络请求降低延迟
- 智能体原生遥测通过 OpenTelemetry 记录用户提示、工具决策和网络拦截

🔗 [阅读全文](https://www.bestblogs.dev/en/article/517d3e21)

---

8. **Seedance 掀起波澜，英伟达 AI 引导芯片设计**
来源：https://www.bestblogs.dev/en/article/19fb6cc7

概要：本期 The Batch 涵盖字节跳动 Seedance 2.0 视频模型、英伟达 AI 芯片设计、盖洛普 AI 采用率民意调查和机器人学习新方法。

亮点：
- 吴恩达反对「AI 导致工作消失」论调，预测将出现 AI 工作大爆发
- 字节跳动 Seedance 2.0 集成到 CapCut，在 OpenAI 关闭 Sora 之际重塑视频生成市场格局
- 英伟达用 AI（强化学习+LLM）自动改进芯片设计，NVCell 和 PrefixRL 生成方案比人类设计好 20%-30%

🔗 [阅读全文](https://www.bestblogs.dev/en/article/19fb6cc7)

---

9. **自适应并行推理：高效推理扩展的下一个范式**
来源：https://www.bestblogs.dev/en/article/b878a6f9

概要：伯克利 AI 研究综述了自适应并行推理（APR）范式，LLM 动态决定何时分解问题并生成并行线程，实现更高效的推理时扩展。

亮点：
- APR 允许模型自身控制控制流，输出特殊标记分叉到并行线程并合并，避免计算浪费
- 推理系统分为引擎修改和多队列两类方法
- 训练 APR 模型需精心设计奖励函数，用关键路径长度衡量延迟

🔗 [阅读全文](https://www.bestblogs.dev/en/article/b878a6f9)

---

10. **扩展的工具包：为什么你的脚手架正在融入模型**
来源：https://www.bestblogs.dev/en/video/eefa50b

概要：Anthropic 产品经理指出，开发者构建的工具路由器和重试循环正被模型原生吸收，敦促开发者聚焦于将模型连接到独特的专有数据。

亮点：
- 弥补模型不可靠性的代码「半衰期只有数月」，随着模型能力增强将很快过时
- 最有价值的代码是将模型连接到专有数据和自定义工具的集成层

🔗 [阅读全文](https://www.bestblogs.dev/en/video/eefa50b)

---

11. **在 Google Cloud 上使用 Claude 进行构建**
来源：https://www.bestblogs.dev/en/video/a5484d8

概要：Google Cloud 开发者布道师演示了用 Claude Code + GCP 进行完整「草图到部署」工作流，展示了 AI 如何增强软件开发生命周期中的每个角色。

亮点：
- MCP 服务器让 Claude 访问最新 GCP 文档、BigQuery、Looker
- 「计划模式」要求 AI 在编码前提出实施策略，经开发者审查批准后再执行

🔗 [阅读全文](https://www.bestblogs.dev/en/video/a5484d8)

---

12. **大规模评估和改进 Replit 智能体**
来源：https://www.bestblogs.dev/en/video/7a5de45

概要：Replit 总裁解释了智能体评估如何从静态基准转向持续自动化，开源 ByteBench 和内部 Telescope 基础设施支撑了每日改进。

亮点：
- 传统静态基准测试已跟不上模型演进速度，持续评估引擎使用实时生产数据驱动每日改进
- ByteBench 评估智能体从零构建功能性应用的能力
- Telescope 基础设施自动化了「发现-修复-验证-发布」的完整改进循环

🔗 [阅读全文](https://www.bestblogs.dev/en/video/7a5de45)

---

13. **Claude Co-work 入门指南**
来源：https://www.bestblogs.dev/en/video/872c6c9

概要：Claude Co-work 将 Claude 转变为 AI 智能体，可通过「计划与批准」工作流与本地文件、云服务和浏览器交互执行复杂任务。

亮点：
- Co-work 核心是委派任务而非逐步对话
- 「计划与批准」模式确保 Claude 先提出详细计划，获得用户批准后才执行更改
- 所有 Co-work 会话在本地设备运行而非云端

🔗 [阅读全文](https://www.bestblogs.dev/en/video/872c6c9)

---

14. **使用 Hooks 实现跨工具的统一智能体记忆**
来源：https://www.bestblogs.dev/en/article/0d80fd09

概要：提出通过生命周期钩子 + Neo4j 构建统一、工具无关的智能体记忆层，使 Claude Code、Codex 和 Cursor 之间可无缝共享上下文。

亮点：
- 钩子在 Claude Code、Codex 和 Cursor 中高度标准化，单个 Python 脚本即可统一集成
- 被动确定性日志记录优于主动记忆——不消耗模型注意力
- 架构将在线日志记录与离线「梦境阶段」分离

🔗 [阅读全文](https://www.bestblogs.dev/en/article/0d80fd09)

---

15. **GPT-Realtime-2：新一代 SOTA 实时语音 API**
来源：https://www.bestblogs.dev/en/article/843269c9

概要：OpenAI 发布 GPT-Realtime-2 系列流式音频模型，具备 GPT-5 级别推理力、128K 上下文和可调节推理努力度，将语音智能体推向全双工推理系统。

亮点：
- GPT-Realtime-2 在 Big Bench Audio 达 96.6%，指令保留率从 36.7% 飙升至 70.8%
- 支持 128K token 上下文窗口、可调推理级别、并行工具调用
- 配套 GPT-Realtime-Translate 支持 70+ 输入语言到 13 种输出语言的实时翻译

🔗 [阅读全文](https://www.bestblogs.dev/en/article/843269c9)

---

📌 **今日主线：** AI 智能体正在快速从「单一任务工具」进化为「有记忆、能协作、可评估的持久系统组件」。Anthropic 的记忆与梦想、Codex 的浏览器嵌入、Asana 的 AI 队友、Replit 的持续评估体系，都指向同一个方向——智能体基础设施正在全面标准化和产品化，开发者需要思考的已不再是「如何让智能体工作」，而是「如何让智能体在组织内持续改进」。

*来源：[BestBlogs.dev](https://www.bestblogs.dev)（AI 评分 ≥ 80）*

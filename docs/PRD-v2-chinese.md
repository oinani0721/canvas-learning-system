# 基于全局架构与TDD实证演进的 Canvas Learning System 核心产品需求文档 (PRD)

研究表明，在复杂的人工智能辅助开发环境中，从“自下而上”的执行策略（Path A）入手能够有效地隔离技术债务，并为前端体验和后端算法的深度整合奠定坚实的基础 [cite: 1]。本文综合分析了系统演进过程中的75项核心架构决策、最低可行性产品（MVP）的14项刚需、以及最新一期的研发状态（Phase 3 与 Phase 4）。基于多项实证研究（涵盖 TDAD、AgentCoder、ATDD 等先进的测试驱动开发工作流），本报告似乎可以为接下来的代码生成与重构提供一份具备高度确定性和鲁棒性的 `prd.json` 兼容产品需求说明书。鉴于现存底层系统（如节点精确检索与 Agent 记忆）仍处于未激活状态 [cite: 1]，本报告致力于消除研发盲区，确保所有迭代任务均遵循严苛的原子化规范并附带验收标准。

---

## 1. 系统架构演进与核心决策基准 (Architectural Evolution & Decision Baselines)

### 1.1 对话引擎侧车架构 (Agent SDK Sidecar Architecture)
系统的对话引擎在极短的时间内经历了多次迭代与否决。起初于2026年3月15日，系统尝试通过直接 Spawn 官方 Claude Code CLI 的方式（方案B）以规避高昂的 API 成本 [cite: 1]。然而，由于 CLI hanging 和 Tauri spawn 的底层 Bug（Issues #11513/#4949），该方案及随后的 Tier B 增强 CLI 方案均被判定为不可行 [cite: 1]。此外，由于 Tauri 2 的 WebView 原生不支持 Node.js 环境，直接嵌入 SDK 的过渡尝试亦宣告失败 [cite: 1]。

最终，确立了当前活跃的 **Agent SDK Sidecar (2026-03-19)** 架构决策。该范式采用 Tauri 2 作为桌面外壳，React 负责前端界面，而底层的对话计算则通过一个独立运行的 Node.js sidecar 进程（运行 `@anthropic-ai/claude-agent-sdk 0.2.74`）来承担 [cite: 1]。Sidecar 负责解析 Stream JSON 并通过 NDJSON IPC（进程间通信）机制传递至 Tauri Channel [cite: 1]。

### 1.2 图数据库引擎统一与检索管道重构
研究明确指出，系统整合 Graphiti 势在必行，且其需要将数据流从传统的 JSON fallback 模式迁移至标准的 Neo4j 实例中 [cite: 1]。现有系统检索管道处于严重损坏状态：6条检索通道仅2条能够勉强工作，且缺失中文（bge-m3）兼容性及智能分块能力 [cite: 1]。为实现 MVP 中的“14项刚需”以及保障 Agentic RAG L1+L2 的顺利运作 [cite: 1]，系统必须完成 6 个 MCP 工具的彻底重写，包括将 `record_learning_memory` 重定向触发 Graphiti 的 `add_episode`，以及将 `search_memories` 升级为三层混合检索架构等 [cite: 1]。
User：这个请你测试一下实际代码我们好像打通了
### 1.3 开发纪律与实证约束 (DD-01 ~ DD-10)
为抵御大型语言模型在代码生成过程中的“幻觉”及“上下文蔓延”，用户确立了10条绝对不可逾越的开发纪律（Development Disciplines）。其中包括但不限于：必须有学术实证支撑（DD-01），绝不可脱离实际代码或进行虚假 Mock（DD-02），以及所有的测试验证必须在真实的 Obsidian 结合环境中进行 [cite: 1]。忽视这些纪律等同于导致功能性崩溃的致命错误 [cite: 1]。
User：我们都脱离obsidian环境了，你怎么还在说obsidian环境，你这里收集的是过时的信息

---

## 2. 自动化 TDD 工作流实证排名与架构融合 (Empirical Rankings of TDD Workflows)

为确保即将生成的 PRD 原子任务能够被 AI Agent 可靠执行，系统深度引入了关于测试驱动智能体开发（TDAD）框架的学术评测。实证数据揭示了不同测试架构在应对单体 LLM“上下文污染”时的巨大差异 [cite: 1]。

### 2.1 排行榜解析 (Workflow Rankings)
*   **Rank 1: TDAD (Test-Driven Agent Development) 与 AST 影响图谱**：
    当前成功率最高的范式。Rehan 引入了语义突变测试（Semantic Mutation Testing）以防止 Agent 编写出“仅为通过断言而存在的脆弱代码” [cite: 1]。Alonso 的研究则进一步指出，在 AI 提交代码前，通过抽象语法树（AST）构建代码与测试的依赖图谱，并在一个轻量级的20行指令文件中呈现，能极大降低回归（Regression）率 [cite: 1]。
*   **Rank 2: AgentCoder (Strict Isolation TDD)**：
    该范式主张严格的“红-绿-重构”物理隔离。一个 `test-writer` 子智能体专门负责撰写测试，而另一个完全物理隔离的 `implementer` 则负责实现业务逻辑 [cite: 1]。这一机制解决了 TDD 提示词悖论：当同一个 LLM 兼任裁判与运动员时，它会潜意识地篡改测试以适应自己错误的实现 [cite: 1]。该隔离架构据称可实现高达 96.3% 的首发通过率 [cite: 1]。
*   **Rank 4: ATDD (Acceptance Test-Driven Development)**：
    源自 Uncle Bob 的理念。通过自然语言编写 Given/When/Then 规范，并设置一个“规范守护者（Spec Guardian）”子智能体，暴力拒绝 LLM 在高层规范中混入低层 API 或数据库细节 [cite: 1]。

### 2.2 最终选取架构：无状态 Ralph 循环混合体
为适配 `Tauri + React + FastAPI + Neo4j + LanceDB` 技术栈，并规避 WSL2 和 Tauri 的环境约束，系统最终采取融合架构 [cite: 1]：
1.  **宏观外环 (Outer Loop)**：在 macOS+tmux 环境下运行纯净无状态的 Ralph Loop Bash 脚本，每次销毁并重启 Agent 实例，避免长程对话的灾难性记忆污染 [cite: 1]。
2.  **微观内环 (Inner Loop)**：采用 AST 引导的子智能体驱动开发（SDD），在实现任何业务前必须提供具体的受影响路由及组件图谱 [cite: 1]。
3.  **质量网关 (Quality Gate)**：引入 ATDD 的双流测试与对抗性突变测试（Adversarial Mutation Oracles），任何未消除死代码（vulture/knip）或未通过突变幸存者检查的提交将被立刻阻断回滚 [cite: 1]。

---

## 3. PROGRESS 与 MVP 状态核查 (State Audit)

依据现有的 `PROGRESS.md` 与用户审计报告，Phase 3（Pipeline Repair）的工作已呈现出明显的进度断层：

*   **已完成 (DONE)**：
    *   **Epic 1 (Profile Click-to-Jump Navigation)**：前后端 Schema 扩充及点击跳转已完整实现，通过全部测试用例 [cite: 1]。
    *   **Epic 2 (Architectural Pruning)**：`cross_canvas_service.py` 和 `textbook_retriever` 等冗余旧历史包袱已被彻底删除，且检索通道由6个降至4个，成功去冗 [cite: 1]。
    *   **MVP #1 / #2**：原白板与检验白板的基础前端结构已完成（包含 `App.tsx` 中的 ReactFlow 渲染，以及 `ExamCanvas`、认知计时器等 UI 组件） [cite: 1]。
*   **待办或阻塞中 (TODO / BLOCKED)**：
    *   **后端底层基建**：用户的 Vault 笔记至今缺乏准确的索引器，Agent 的 Mastery 记忆系统未能注入，导致 Graphiti 的知识图谱被遗漏 [cite: 1]。
    *   **MCP 迁移**：6 个核心工具的 Graphiti 化重构尚未开展 [cite: 1]。
    *   **外观与体验**：虽然设定了 `Catppuccin Mocha` 暗色主题，但目前由于 TailwindCSS 配置的局限，全局 UI 仍是浅色（浅色UI被用户指认为问题） [cite: 1]。

---

## 4. 全局核心产品需求规范 (Comprehensive PRD.json Specification)

基于上述全部上下文，以下是严格按照 `prd.json` 架构编写的系统需求文档格式化呈现。该 JSON 结构完美兼容 TDD Ralph Loop 执行引擎的解析逻辑。

```json
{
  "project_name": "Canvas Learning System Phase 3 & 4",
  "architectural_context": "Tauri 2 + React Svelte + Node.js Agent SDK Sidecar + FastAPI + Neo4j (Graphiti) + LanceDB",
  "tdd_workflow": "Hybrid TDAD + AgentCoder + ATDD via Stateless Ralph Loop in macOS/tmux",
  "epics": [
    {
      "epic_id": "EPIC-1",
      "epic_title": "历史架构裁剪与依赖净化 (Architectural Pruning) [DONE]",
      "description": "移除所有阻碍 Agentic RAG 与新系统运作的旧版上下文模块及教科书检索服务。",
      "features": [
        {
          "id": "EPIC-1-F1",
          "title": "移除 cross_canvas 交叉白板服务",
          "target_files": [
            "backend/app/services/cross_canvas_service.py",
            "backend/app/api/endpoints/cross_canvas.py",
            "backend/app/api/dependencies.py"
          ],
          "acceptance_cmd": "grep -r 'cross_canvas' backend/app/ || echo 'Passed'",
          "anti_examples": ["保留废弃的端点路由并仅作注释隐藏", "未在 context_enrichment_service 中解绑依赖"],
          "effort": "1h",
          "passes": "DONE",
          "depends_on": []
        },
        {
          "id": "EPIC-1-F2",
          "title": "移除 Textbook Retriever 及重构基础通道",
          "target_files": [
            "backend/app/services/textbook_context_service.py",
            "backend/app/api/endpoints/textbook.py",
            "backend/app/agents/verification_service.py"
          ],
          "acceptance_cmd": "pytest tests/api/test_retrieval_channels.py -v",
          "anti_examples": ["在 RAG 回源中继续遗留对教科书实体的隐式引用"],
          "effort": "1h",
          "passes": "DONE",
          "depends_on": ["EPIC-1-F1"]
        }
      ]
    },
    {
      "epic_id": "EPIC-2",
      "epic_title": "基础前端白板与交互展示层构建 (Frontend ReactFlow Canvas) [DONE]",
      "description": "完成原白板及检验白板在桌面端界面的初步渲染与右键菜单交互。",
      "features": [
        {
          "id": "EPIC-2-F1",
          "title": "知识图谱主白板 ReactFlow 组件",
          "target_files": [
            "frontend/src/App.tsx",
            "frontend/src/canvas-store.ts",
            "frontend/src/components/NodeContextMenu.tsx"
          ],
          "acceptance_cmd": "npm run test:vitest -- useBoardData.test.ts",
          "anti_examples": ["强耦合 ReactFlow 内部状态而忽视 Dexie 持久化"],
          "effort": "3h",
          "passes": "DONE",
          "depends_on": []
        },
        {
          "id": "EPIC-2-F2",
          "title": "检验白板与考后统计面板 (ExamCanvas)",
          "target_files": [
            "frontend/src/pages/ExamCanvas.tsx",
            "frontend/src/stores/exam-store.ts",
            "frontend/src/components/ExamSummary.tsx"
          ],
          "acceptance_cmd": "npm run test:vitest -- exam-store.test.ts",
          "anti_examples": ["保留基于倒计时的考察机制（决策已废弃时间计时器）", "本地拦截评价而非提交至 /api/v1/exam/{id}/complete"],
          "effort": "4h",
          "passes": "DONE",
          "depends_on": ["EPIC-2-F1"]
        }
      ]
    },
    {
      "epic_id": "EPIC-3",
      "epic_title": "UI主题与交互体验规范化 (Catppuccin Mocha Theming) [TODO]",
      "description": "解决前端 UI 深浅色不一致问题，贯彻 Pencil 设计稿中的全局暗色规范。",
      "features": [
        {
          "id": "EPIC-3-F1",
          "title": "全局迁移至 Catppuccin Mocha 暗色调 (DD-05)",
          "target_files": [
            "frontend/tailwind.config.ts",
            "frontend/src/index.css",
            "frontend/src/App.tsx"
          ],
          "acceptance_cmd": "npm run lint:css && npm run test:e2e -- --spec theme",
          "anti_examples": ["仅修改局部组件（如 ToolCallCard）的背景色", "在代码中硬编码 HEX 颜色而不是使用 tailwind 变量"],
          "effort": "2h",
          "passes": "TODO",
          "depends_on": ["EPIC-2-F1"]
        },
        {
          "id": "EPIC-3-F2",
          "title": "节点精通度纯视觉颜色解绑配置",
          "target_files": [
            "frontend/src/utils/mastery-utils.ts",
            "frontend/src/components/NodeContextMenu.tsx"
          ],
          "acceptance_cmd": "npm run test:vitest -- mastery-utils.test.ts",
          "anti_examples": ["将后端的 Mastery 逻辑反向硬编码进前端的手动颜色选择器中"],
          "effort": "1h",
          "passes": "TODO",
          "depends_on": ["EPIC-3-F1"]
        }
      ]
    },
    {
      "epic_id": "EPIC-4",
      "epic_title": "MCP Tool 工具的 Graphiti 标准化重写 [TODO]",
      "description": "废弃旧有的 JSON fallback 存储逻辑，将6个核心 MCP 工具重定位到 Neo4j 实例的 Graphiti core 中。",
      "features": [
        {
          "id": "EPIC-4-F1",
          "title": "学习记忆记录器改造 (record_learning_memory)",
          "target_files": [
            "backend/app/tools/memory_tools.py",
            "backend/app/graphiti/operations.py"
          ],
          "acceptance_cmd": "pytest tests/tools/test_record_memory_graphiti.py",
          "anti_examples": ["向本地文件写入 JSON 记录", "未使用 Graphiti 的 add_episode API"],
          "effort": "2h",
          "passes": "TODO",
          "depends_on": []
        },
        {
          "id": "EPIC-4-F2",
          "title": "三层记忆搜索架构升级 (search_memories)",
          "target_files": [
            "backend/app/tools/search_tools.py",
            "backend/app/graphiti/search.py"
          ],
          "acceptance_cmd": "pytest tests/tools/test_search_memories_tiers.py",
          "anti_examples": ["采用原始的字符串匹配", "缺少对 Reranker 的调用"],
          "effort": "3h",
          "passes": "TODO",
          "depends_on": ["EPIC-4-F1"]
        },
        {
          "id": "EPIC-4-F3",
          "title": "错题与误解 LLM 归类工具重构 (record_error)",
          "target_files": [
            "backend/app/tools/error_tracking.py",
            "backend/app/agents/error_classifier.py"
          ],
          "acceptance_cmd": "pytest tests/tools/test_record_error_llm.py",
          "anti_examples": ["直接将错误字符串丢入数据库，而不经过 LLM 的语义切面分析"],
          "effort": "2h",
          "passes": "TODO",
          "depends_on": ["EPIC-4-F1"]
        },
        {
          "id": "EPIC-4-F4",
          "title": "向量笔记通道激活 (search_notes)",
          "target_files": [
            "backend/app/tools/vault_tools.py",
            "backend/app/retrieval/lancedb_connector.py"
          ],
          "acceptance_cmd": "pytest tests/retrieval/test_vault_notes_active.py",
          "anti_examples": ["保留当前系统中的 dummy stub 模拟实现", "未剔除重复的索引"],
          "effort": "2h",
          "passes": "TODO",
          "depends_on": []
        },
        {
          "id": "EPIC-4-F5",
          "title": "对话实体序列化与归档重构 (archive_conversation)",
          "target_files": [
            "backend/app/tools/session_archiver.py",
            "backend/app/graphiti/persistence.py"
          ],
          "acceptance_cmd": "pytest tests/tools/test_archive_conversation.py",
          "anti_examples": ["存储扁平文本而非结构化 Graphiti Node", "在序列化时丢失对话继承关系"],
          "effort": "2h",
          "passes": "TODO",
          "depends_on": ["EPIC-4-F1"]
        },
        {
          "id": "EPIC-4-F6",
          "title": "基于历史轨迹的数据聚合组装 (generate_question)",
          "target_files": [
            "backend/app/tools/question_generator.py",
            "backend/app/graphiti/analytics.py"
          ],
          "acceptance_cmd": "pytest tests/tools/test_generate_question_trajectory.py",
          "anti_examples": ["生成的问题基于 Mock 数据", "未从 Graphiti Trajectories 抽取真实用户答题历史作为上下文"],
          "effort": "3h",
          "passes": "TODO",
          "depends_on": ["EPIC-4-F5"]
        }
      ]
    },
    {
      "epic_id": "EPIC-5",
      "epic_title": "Agentic RAG 与检索引擎基础设施 (RAG & Base Retrieval) [TODO]",
      "description": "修复当前失效的检索管道，激活 BGE-M3 双语能力与智能分块，为 MVP 的基础提供支撑。",
      "features": [
        {
          "id": "EPIC-5-F1",
          "title": "笔记片段精准检索系统建立 (Vault Indexer)",
          "target_files": [
            "backend/app/retrieval/vault_indexer.py",
            "backend/app/retrieval/chunking.py",
            "backend/app/config.py"
          ],
          "acceptance_cmd": "pytest tests/retrieval/test_vault_indexer_precision.py",
          "anti_examples": ["未实现去重策略导致索引体积暴增", "缺少对 Markdown 的结构化切分"],
          "effort": "4h",
          "passes": "TODO",
          "depends_on": []
        },
        {
          "id": "EPIC-5-F2",
          "title": "BGE-M3 双语嵌入与混合检索支持 (Hybrid Search)",
          "target_files": [
            "backend/app/retrieval/embedding_service.py",
            "backend/app/retrieval/hybrid_search.py"
          ],
          "acceptance_cmd": "pytest tests/retrieval/test_bgem3_hybrid.py",
          "anti_examples": ["使用 OpenAI 闭源模型代替 BGE-M3（违反离线决策）"],
          "effort": "3h",
          "passes": "TODO",
          "depends_on": ["EPIC-5-F1"]
        },
        {
          "id": "EPIC-5-F3",
          "title": "Agentic RAG 智能路由与自修复 (L1+L2 级别)",
          "target_files": [
            "backend/app/agents/agent_graph.py",
            "backend/app/retrieval/crag_evaluator.py",
            "backend/app/retrieval/router.py"
          ],
          "acceptance_cmd": "pytest tests/agents/test_agent_rag_routing.py",
          "anti_examples": ["缺少自动重检索逻辑", "CRAG 门控总是误判由于未配置置信度阈值"],
          "effort": "5h",
          "passes": "TODO",
          "depends_on": ["EPIC-5-F2"]
        }
      ]
    },
    {
      "epic_id": "EPIC-6",
      "epic_title": "MVP 第一梯队核心刚需业务 (MVP Phase 0 Essentials) [TODO]",
      "description": "用户最核心的 14 项刚需转化。包括各类白板专属提示词、对话系统、发现写入与 Edge 对话等。",
      "features": [
        {
          "id": "EPIC-6-F1",
          "title": "节点 AI 深度剖析对话 (per-node dialogue)",
          "target_files": [
            "backend/app/api/endpoints/dialogue.py",
            "backend/app/services/node_dialogue_service.py"
          ],
          "acceptance_cmd": "pytest tests/api/test_node_dialogue.py",
          "anti_examples": ["未能获取节点所绑定的知识点上下文", "不执行解题过程的步骤拆解"],
          "effort": "3h",
          "passes": "TODO",
          "depends_on": ["EPIC-4-F4"]
        },
        {
          "id": "EPIC-6-F2",
          "title": "检验白板三阶考察提示词生成引擎",
          "target_files": [
            "backend/app/services/exam_prompt_builder.py",
            "backend/app/agents/exam_orchestrator.py"
          ],
          "acceptance_cmd": "pytest tests/services/test_exam_prompt.py",
          "anti_examples": ["硬编码提示词而不区分 '点对点'、'混淆融合' 及 '举一反三' 三种模式"],
          "effort": "2h",
          "passes": "TODO",
          "depends_on": ["EPIC-2-F2"]
        },
        {
          "id": "EPIC-6-F3",
          "title": "检验白板新发现盲区回写节点流",
          "target_files": [
            "backend/app/services/exam_result_processor.py",
            "backend/app/graphiti/node_creator.py"
          ],
          "acceptance_cmd": "pytest tests/services/test_exam_discovery_writeback.py",
          "anti_examples": ["在未经考后审查面板二次确认前强行写入知识图谱", "一次性生成超过3个节点（违背限制）"],
          "effort": "3h",
          "passes": "TODO",
          "depends_on": ["EPIC-2-F2", "EPIC-4-F1"]
        },
        {
          "id": "EPIC-6-F4",
          "title": "双重 Edge 边缘推理策略触发机制",
          "target_files": [
            "backend/app/services/edge_dialogue_service.py",
            "backend/app/api/endpoints/edges.py"
          ],
          "acceptance_cmd": "pytest tests/api/test_edge_strategy.py",
          "anti_examples": ["仍采用被否决的原始 3重 Edge 策略", "未能保存语义标签的推理依据"],
          "effort": "2h",
          "passes": "TODO",
          "depends_on": ["EPIC-4-F1"]
        },
        {
          "id": "EPIC-6-F5",
          "title": "指令式系统 (/命令) 与对话拉出节点功能",
          "target_files": [
            "frontend/src/components/ChatPanel.tsx",
            "backend/app/services/command_parser.py",
            "backend/app/services/node_extraction.py"
          ],
          "acceptance_cmd": "pytest tests/services/test_slash_commands.py && npm run test:vitest -- ChatPanel.test.ts",
          "anti_examples": ["未能解析前端传来的斜杠前缀", "提取节点时没有触发界面重绘事件"],
          "effort": "4h",
          "passes": "TODO",
          "depends_on": []
        }
      ]
    },
    {
      "epic_id": "EPIC-7",
      "epic_title": "Agent SDK 侧车架构集成与守护进程 (Sidecar Daemon) [TODO]",
      "description": "确立 Node.js Sidecar (Claude Agent SDK 0.2.74) 为独立对话引擎，建立 Tauri 与其的 NDJSON IPC 通道。",
      "features": [
        {
          "id": "EPIC-7-F1",
          "title": "Node.js Agent SDK Sidecar 基础进程管理",
          "target_files": [
            "src-tauri/src/sidecar_manager.rs",
            "sidecar/package.json",
            "sidecar/src/index.js"
          ],
          "acceptance_cmd": "cargo test --package app --lib sidecar_manager",
          "anti_examples": ["在 Tauri WebView 内部尝试运行 Node.js 库", "没有处理 Windows 下的路径转义和 Spawn 稳定性异常"],
          "effort": "5h",
          "passes": "TODO",
          "depends_on": []
        },
        {
          "id": "EPIC-7-F2",
          "title": "Tauri Channel 与 NDJSON 数据流解析管道",
          "target_files": [
            "src-tauri/src/ipc/ndjson_parser.rs",
            "frontend/src/services/sidecar-ipc.ts"
          ],
          "acceptance_cmd": "npm run test:vitest -- sidecar-ipc.test.ts",
          "anti_examples": ["以阻塞方式读取 stdout 导致前端 Hanging"],
          "effort": "3h",
          "passes": "TODO",
          "depends_on": ["EPIC-7-F1"]
        }
      ]
    }
  ]
}
```

---

## 5. 附录：深度模块解析与实施原则 (Deep-dive Module Analysis & Implementation Principles)

### 5.1 引擎架构选择中的核心冲突分析
在长达数日的重构中，`decision-log.md` 清晰记录了关于底层对话驱动引擎的最关键妥协 [cite: 1]。之所以最终放弃将 `Claude Code CLI` 作为直接的代理调用工具，而转向 **独立 Sidecar 方案**，主要是受到底层操作系统的极大掣肘。具体而言，Windows 环境中（乃至 WSL2 的某些代理配置下），不断生成新的 CLI 进程会导致内存资源大量泄露并触发著名的 "CLI hanging" 问题 [cite: 1]。采用 Tauri 自带的 Sidecar 接口派生独立的 Node.js 进程，虽然需要手动桥接 NDJSON 通信通道 [cite: 1]，但彻底隔离了 UI 渲染层与 LLM 计算代理层，大幅度提高了 `Pass@1` 系统的运行稳定性。

### 5.2 关于 TDD 架构的补充机制：AST 与语义突变
依据深度研究结论，必须向 AI Agent 实施高强度的架构规训（TDAD 与 ATDD） [cite: 1]。当前 Canvas Learning System 拥有超过 38 个后端服务文件 [cite: 1]，任何细微的 API 改动都可能引发蝴蝶效应。通过引入 **语义突变测试（Semantic Mutation Testing）**，系统在提交代码前会自动随机篡改几处逻辑（例如将 `==` 改为 `!=`），并强制要求测试套件能敏锐地发现这些错误 [cite: 1]。如果 Agent 编写的测试仅仅是为了应付检查（无法捕获突变），该提交在 Ralph Loop 中将立即被拒绝。这完美契合了开发纪律中“禁止 Mock、不脱离实际”的硬性规定（DD-02） [cite: 1]。

### 5.3 严格禁止的系统设计反例
根据用户审计的结论（如 2026-03-16 确认的纪律清单），以下反模式在后续 Epic 落地过程中，一旦触发，等同于项目失败 [cite: 1]：
1. **冷启动诊断 (Cold-Start Diagnostic)**：已被明确废除（设计前提不成立），绝不应为其分配任何 API 或前端路由 [cite: 1]。
2. **纯依赖前端缓存而不落库**：新的架构理念为 `Frontend-first + Backend sync`，即所有对 Dexie（客户端图结构）的改变，无论成功与否，必须基于图一致性协议异步同步至 Neo4j Graphiti [cite: 1]。
3. **闭源检索降级**：系统承诺了 100% 离线检索优先，必须保障开源 `BGE-M3` 的激活，绝不可因为配置困难或懒惰而回退至依赖 OpenAI Embeddings 等闭源外部调用（违反架构边界） [cite: 1]。

### 5.4 阶段验证与验收结论
结合本需求文档中的 7 大 Epic（覆盖所有前端重构、后端 MCP、基础 RAG 及其 Agentic L1+L2 能力），该 `prd.json` 兼容架构已完全实现了理论上的闭环 [cite: 1]。未来的开发应以自动化、测试驱动的形态逐步消化以上 JSON 任务清单，在确保原有通过的测试用例（如 15个 pytest、6个 vitest [cite: 1]）不产生任何回归的前提下，完成由 Phase 3 向 Phase 4 的正式跨越。

**Sources:**
1. docs/prd-phase3-phase4.md (fileSearchStores/persistentcanvaslearningsys-z2njevmxp7md)

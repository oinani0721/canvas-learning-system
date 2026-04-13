---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-03-16'
updatedAt: '2026-03-17'
updateReason: 'Frontend migration: Obsidian+Svelte → Tauri+React+ReactFlow (DE-1~DE-5 + GDR-P1-1~P1-4)'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-archive/stale-planning/prd-backend-retrieval-pipeline.md
workflowType: 'architecture'
project_name: 'Canvas'
user_name: 'ROG'
date: '2026-03-16'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**功能需求（12 个能力域，70+ FR）：**

| 能力域 | 有效FR数 | 架构含义 |
|--------|---------|---------|
| 1. 知识图谱管理 | 7 | ReactFlow 白板引擎（@xyflow/react DOM 渲染自定义节点+边，Frontend-first本地JSON→Neo4j异步delta sync，Zustand全局状态管理）+ Neo4j/Graphiti统一管理（方案C内嵌graphiti_core）+ Edge语义标签数据模型（KG-triplet格式）+ 概念关联推荐（图分析，MVP可延后）+ 图片双层处理（对话层Mode D原生多模态即时对话/检索层LanceDB异步bge-m3索引+状态指示） |
| 2. 节点AI对话 | 9 | Per-node独立session（createSession/resumeSession）+ 对话历史跨session持久化（SQLite+aiosqlite）+ Hot-Warm-Cold三层时间归档（0-30天完整/30天-6月摘要+提取/6月+仅提取，双触发：时间+容量50K tokens）+ 学习上下文自动注入（Tips/错误/Edge理由从Graphiti检索注入prompt，三层Tier管理：Tier1当前节点全量+observation masking/Tier2相邻节点摘要/Tier3远端RAG按需）+ 4类错误自动分类器与差异化补救路由（破题错误→同结构新题/推理谬误→找错+反例/知识点缺失→回退定义题/似懂非懂→辨析+迁移题）+ 对话内交互操作层（Tip标注选中文字→浮动面板、/命令拦截路由到技能注册表、文字拖出创建节点+LLM关系建议）+ 异步并发生成管理器（后台生成不取消、并发上限3+排队、跨节点状态推送：生成中/完成未读/空闲）+ Claude API Server-Side Compaction作为Tier1兜底 |
| 3. Edge对话 | 4 | EdgeDialogTrigger连线可交互图标（Svelte Canvas渲染层扩展+首次引导提示，Edge对话交互入口）+ ChatPanel Edge模式（Agent主动发起EI提问，注入两端节点上下文+预设prompt）+ Edge理由双写（Graphiti结构化KG-triplet+LanceDB向量化，下游消费：出题Prompt ACP第3层+节点对话上下文注入）+ EI+SE双重策略激活（排除Active Recall——连线时两端可见不构成回忆检索，Karpicke & Blunt 2011）+ Layer 3回退：退化为静态标签边 |
| 4. 检验白板 | 18有效(21编号,3废除) | 空白生成+继承原白板全功能(07)+禁止嵌套生成(21) \| FSRS+BKT+KG三角协作薄弱节点选择(02) + 三种考察模式(点对点/综合题/混合)(11)+白板内容类型→模式自动映射(Constructive Alignment, Biggs 1996)(12)+类型定制出题策略(13) + 个性化出题利用Tips/Edge/错误(03) + 两入口（Dashboard全白板FR-DASH-03/学习档案单节点FR-EXAM-17）\| AutoSCORE两阶段隐形评分：Stage1证据提取(不打分)→Stage2按4维4分制Rubric(概念准确/推理质量/知识覆盖/知识整合,SOLO锚定)逐维打分×3次采样多数投票,分差>1标记AI低信心(04) + Topic-level触发(节点切换时后台执行,Stealth Assessment)(16) + 校准反馈"评分准确吗"(可选,few-shot样本)(15) \| 递归考察(06)+拖拽新节点实时同步回原白板(05/18) + 4级渐进提示(Chain-of-Hints 2025:方向→关键词→框架→脚手架)+跳过不惩罚BKT(19) + 认知负荷控制15/25/35/45分钟休息提醒(08) \| 考察记录永久保存+Dashboard历史浏览+同一原白板可生成不限数量检验白板(20) \| **约束**：用户驱动终止(不点=自然结束)(06)+不提供"直接告诉答案"选项(19)+禁止嵌套生成检验白板(21) \| **白板分类（软分类）**：外在属性=学科标签(用户手动打标为主+系统建议为辅+路径推断兜底)影响搜索范围subject隔离；内在属性=内容类型(知识点/题目/混合,系统自动分析推荐+用户可覆盖)影响考察模式映射(知识点→点对点考理解/题目→综合题考思维/混合→混合模式) |
| 5. 精通度追踪 | 6 | BKT+FSRS双引擎（BKT管掌握概率利用KG关联/FSRS管记忆稳定性和复习调度，effective_proficiency=min(p_mastery,R)）+ 精通度仅通过考察更新(非自评直修)(02) + 三通道传达：节点颜色+学习档案面板+FSRS Dashboard复习提醒(03) + 处方性展示"建议复习X"而非"你的X是40%",OLM三层面板延后Phase 2(03) + Area9式2x2置信度矩阵(自评vs实际)+三阶段渐进(<10收集/10-20趋势/20+可靠)(05) + 5-6核心信号→单维掌握度(BKT+FSRS+考察评分+校准偏差+自信度),信号互补性验收r<0.7,N信号动态接入架构(Phase 2 Beta-Bayesian),多维精通度Phase 3+远期(06) |
| 6. 检索与个性化 | 13 | **双系统架构**：LanceDB笔记内容检索+**Graphiti个人记忆引擎**(Tips/Edge理由/错误/问答的写入检索+图遍历+时序感知+矛盾检测,三通道写入:Agent自报告+对话蒸馏+考察提取,自定义Pydantic Schema实体类型) \| **四层路由+六路物理通道**：RAG层(LanceDB Dense语义+Sparse/jieba关键词+图片OCR文本)(3通道)/CLI层(Obsidian CLI图遍历+Vault笔记搜索)(2通道)/Graphiti层(时序记忆搜索)(1通道)/Grep层(A-RAG回源验证)(Agent侧执行) → 分层RRF融合(3组k=60+z-score跨组归一化) \| **增量索引管道**：文件指纹content_hash+delete-before-insert去重+标题智能分块512token(heading→句子→token三级+原子保护代码/公式/表格)+面包屑前缀(Anthropic验证降35%检索失败)+jieba中文预分词(Lance原生支持jieba tokenizer)+bge-m3 1024d Dense+Sparse双向量 \| **检索后处理**：gte-reranker-modernbert-base精排(149M,Hit@1=83%,延迟424ms,备选Qwen3-4B)+Adaptive-k动态截取(最大gap+buffer B=5)+A-RAG迭代Retrieve-Verify(Agent用Grep/Read回源验证Staleness Check content_hash+Context Expansion完整段落,最多2次重试)+安全降级(信息不足告知非幻觉) \| **上下文压缩**15K→3K(句子级提取,公式/代码整块保护)+掌握度信息前置注入prompt \| **输出**附带Obsidian双向链接`[[文件名#章节标题]]`(索引保留source_file+heading元数据) |
| 7. 命令技能系统 | 5 | 可扩展注册机制（借鉴Claude Code /skill范式,约定目录下prompt模板文件）+ 用户可自行添加模板扩展技能(03) + /输入触发模糊搜索列表(01) + 预装11个学习辅助技能(拆解/解释/对比/记忆/练习/检验)(02) + Agent执行时注入学习历史上下文个性化(04) + 结果显示在对话中可拉出为白板节点(05) |
| 8. 学习档案 | 5 | L1聚合精通度指示器+学习摘要(01) + L2 Tips列表·可展开查看来源对话上下文(02) + L2 需要加强方向(正面框架"需要加强"非"错误列表",聚合误解模式)(03) + L3关键问答按主题聚类(默认折叠按需展开)(04) + Hot-Warm-Cold自动提取归档管道(对话结束时LLM提取错误/Tips/关键问答→Graphiti+SQLite)(05) |
| 9. 质量保证 | 7 | Faithfulness>=0.85幻觉检测(RAGAS框架)(01) + Prompt版本管理+变更自动触发回归测试(02) + LLM调用结构化日志(输入/输出/延迟/token数)(03) + Token成本追踪+Dashboard展示(04) + Prompt注入防护(system/user隔离+LLM输出安全检查)(05) + 出题难度匹配率>=70%(06) + 结构化提取人工抽验(07) |
| 10. Dashboard | 4 | 原白板列表(点击打开)(01)+检验白板列表(考察状态/历史)(02)+考察入口(选模式→启动)(03)+历史检验白板详情(时间/掌握度变化/考察节点数,点击查看完整记录)(04) |
| 11. Agent集成与MCP | 6 | **Claude Code/OpenCode对话框作为核心交互引擎**（Mode D架构,Agent CLI驱动所有AI功能,/命令技能注册机制）\| **Mode D架构**：前端对话框通过Claude Agent SDK驱动,Tool-UI Bridge模式(Agent调用自定义工具→同时更新IndexedDB+Svelte Store→UI响应式更新,Dexie liveQuery桥接)(FR-AGENT-01) + per-node独立Session(createSession/resumeSession,节点切换保持独立上下文)(FR-AGENT-02) + 引擎可替换(Claude SDK/OpenCode/未来MCP兼容Agent,MCP开放标准不锁定厂商)(FR-AGENT-03) \| **MCP工具暴露**：FastAPI-MCP 3行代码暴露(ASGI直连无HTTP开销)+标准化工具(query_mastery/generate_question/score_answer/search_memories/update_fsrs/update_bkt/record_calibration/assemble_acp/archive_conversation/create_exam_node等)(FR-MCP-01) + 密码学令牌管道(每步产token,跳步拒绝,顺序不可绕过)(FR-MCP-02) + 后端审计守护(异步检测信号丢失/跳步/算法未更新)(FR-MCP-03) \| **6层防御**：Layer0后端算法权威(不可绕过)+Layer1密码学令牌(不可绕过)+Layer2 CLAUDE.md/AGENTS.md(建议性~80%)+Layer3 Claude Code Hooks(确定性,仅Claude Code,MVP不管替换降级)+Layer4后端审计(不可绕过,异步)+Layer5结构化输出(引导性~90%) |
| 12. 系统配置 | 7 | 安装引导向导(5步检测:Docker→后端API→Neo4j→LLM API Key→首个白板)(01) + 模型供应商/Key配置(02) + 按任务分配模型(对话/评分/Embedding)(03) + 系统健康面板(Docker/后端/Neo4j/LLM API/LanceDB常驻状态)(04) + **命令面板一键启动/重启后端**(05) + 数据备份+一键恢复(06) + 多学科隔离与切换(subject字段+跨课程Tag Jaccard桥接)(07) |

**非功能需求（6 类 33 项）：**

| 类别 | 项数 | 关键要求 |
|------|------|---------|
| 性能 | 7 | 白板操作<16ms 60fps(ReactFlow onlyRenderVisibleElements+React.memo) \| 节点CRUD同步<500ms(乐观更新) \| 对话首token<2s \| RAG检索<3s \| 图片OCR<10s(异步) \| 精通度更新<100ms(O(1)) \| 应用启动<1s(Tauri,对比Electron 1-2s) \| IPC单次<100KB |
| 可靠性 | 5 | 数据零丢失(500ms-1s同步) \| LLM断连降级(白板/FSRS正常) \| Neo4j异常降级(写操作队列暂存恢复重放) \| 备份可恢复 \| 错误不静默(所有异常UI明确反馈) |
| 可观测性 | 4 | 100%LLM调用日志(输入/输出/延迟/token/成本) \| 实时管道健康指标 \| 错误自动分类聚合 \| 按任务Token消耗统计 |
| 可维护性 | 4 | MCP工具接口schema验证+向后兼容 \| Prompt变更自动回归测试 \| BKT/FSRS确定性算法100%单元测试 \| 评分→精通度→FSRS端到端集成测试 |
| 安全与隐私 | 7 | 数据本地存储(Neo4j/SQLite/LanceDB不上传) \| API Key仅本地不明文不入日志 \| 网络请求仅向配置的LLM API \| 敏感数据首次提示 \| localhost通信 \| Prompt注入防护(system/user隔离+输出安全检查) \| 6层Agent行为约束 |
| 兼容性 | 11 | Tauri 2.10.3(WebView2 Win10 21H2+/WKWebView macOS 12+/webkit2gtk Linux) \| Windows 10 21H2+/macOS 12+/Linux Ubuntu 20.04+ \| Docker Desktop 4.x/Engine 20.10+ \| Neo4j 5.x Community \| LanceDB 0.4+ \| Graphiti 0.5+(graphiti_core) \| Ollama 0.3+ \| Python 3.11+ \| LiteLLM 1.0+ \| React ≥19.2.4 \| ReactFlow 12.10.1 |

### Scale & Complexity

- **Primary domain:** Full-stack（Tauri 桌面应用前端 + Docker Backend 微服务）
- **Complexity level:** HIGH — 9组件全球首次整合，17算法融合无先例
- **Project context:** Brownfield — 已有后端代码基础，前端从 Obsidian+Svelte 全量迁移至 Tauri+React+ReactFlow
- **Estimated architectural components:** 6大系统（Tauri 桌面壳/React 前端/API网关/算法管道/知识图谱/Agent引擎）+ Graphiti个人记忆引擎独立子系统

### Technical Constraints & Dependencies

| 约束 | 说明 |
|------|------|
| Tauri 2.0 桌面壳 | WebView2(Windows)/WKWebView(macOS)/webkit2gtk(Linux)，Rust 后端进程 + Web 前端，capability-based 权限模型 |
| 跨平台 WebView 差异 | 不同 OS 的 WebView 引擎渲染可能不一致，Linux WebKitGTK 偶有问题。**Windows-first 测试策略**（目标用户平台） |
| IPC 性能约束 | Tauri IPC：macOS ~5ms / **Windows ~200ms（10MB 载荷）**。**硬约束：单次 IPC 载荷 <100KB + delta 更新**（GDR-P1-4） |
| Docker依赖 | Neo4j+FastAPI+Ollama 必须 Docker 运行，最低 ~8GB RAM（Neo4j 4GB + Python 2GB + Ollama bge-m3 ~2GB），SSD 推荐 |
| Docker 管理 | Tauri Shell Plugin 管理 docker-compose 生命周期。**必须使用绝对路径**（Tauri 不继承 $PATH）。Windows spawn 挂起 bug(#11513) 需 HTTP IPC 备选（GDR-P1-3）。macOS/Linux 需 fix-path-env-rs |
| 组件启动顺序 | Tauri 应用启动→Shell Plugin 执行 docker-compose up→Neo4j(等待就绪)→Ollama(加载bge-m3)→FastAPI(等待Neo4j+Ollama)→Agent SDK→MCP连接→就绪 |
| 版本兼容性 | Tauri 2.10.3, React ≥19.2.4, ReactFlow 12.10.1(@xyflow/react), Vite 7.x(pin), TailwindCSS v4, Docker 20.10+, Neo4j 5.x, LanceDB 0.4+, Graphiti 0.5+, Ollama 0.3+, Python 3.11+, LiteLLM 1.0+ |
| CSP 策略 | 开发阶段 csp:null（DE-5）。上线前定向放行：`'self'` + Tauri 协议 + `'unsafe-inline'`(TailwindCSS 需要) + `connect-src ipc: http://localhost:*`。Tauri 编译时自动注入 nonce |
| LangGraph保留 | 已有LangGraph管道不受前端重构影响，Agentic RAG在此基础启用 |
| MCP Protocol | Agent CLI通过MCP JSON-RPC接入后端，FastAPI-MCP 3行代码ASGI直连暴露，开放标准不锁定厂商 |
| bge-m3本地运行 | Ollama容器运行bge-m3 1024d Dense+Sparse双向量(MVP)，ColBERT保留Phase 2评估，CPU可跑独立进程 |
| LiteLLM统一层 | 后端LLM调用统一接口支持100+模型，双层Key分离(外层Agent对话用户Key/内层评分提取后端Key) |
| ReactFlow 白板引擎 | @xyflow/react DOM 渲染，**~1000 节点天花板**（我们 50-300 安全）。自定义节点必须 React.memo()。onlyRenderVisibleElements + Zustand 状态管理 |
| 本地 JSON 存储 | Tauri fs API 读写本地 JSON 文件（Frontend-first）。delta sync 到后端（POST → 幂等 UUID → 指数退避）。单用户不需要 CRDT |
| 更新策略 | 桌面应用：tauri-plugin-updater 自动更新 \| Docker：docker-compose pull \| Schema：Alembic(SQL)+Cypher(Neo4j) |
| 离线降级4场景 | 无网络→白板正常+AI不可用 \| Docker未启→引导面板 \| Neo4j异常→503+队列暂存 \| LanceDB损坏→退化关键词搜索 |
| 首次引导 | 5步检测链(Docker/后端/Neo4j/LLM Key/首白板)+系统健康面板+一键启动脚本 |
| Brownfield技术债 | 后端：8 CRITICAL + 7 HIGH（config断裂/reranker空壳/CRAG误判等）。前端：Obsidian+Svelte 全部废弃，React+ReactFlow 全量重写 |

### Cross-Cutting Concerns（10项）

1. **数据同步一致性** — 本地JSON↔Neo4j异步delta sync，乐观更新+冲突处理(last-write-wins单用户)+操作队列暂存。IPC载荷<100KB硬约束(GDR-P1-4)
2. **离线降级策略** — 4种故障场景各有独立降级方案+SyncEngine状态机(IDLE→SYNCING→OFFLINE)
3. **LLM调用管理** — 成本追踪+幻觉检测Faithfulness>=0.85+多模型路由(LiteLLM)+双层Key分离+并发控制(上限3)
4. **算法管道完整性** — 信号从采集→评估(AutoSCORE)→更新(BKT/FSRS)→展示(节点颜色)不可断裂，密码学令牌保障顺序
5. **Agent行为约束** — 6层防御(Layer0-5)，MVP阶段Layer3(Hooks)仅Claude Code，Layer0/1/4三层硬防线不可绕过
6. **主题系统** — shadcn/ui oklch CSS变量 + TailwindCSS v4 utility + Catppuccin Mocha(暗色) / Latte(浅色,未来)。组件前缀 cl-{group}-*
7. **错误处理与可观测性** — 100%LLM日志+管道健康监控+错误不静默+结构化日志
8. **多学科隔离** — subject参数设计进每个数据写入/查询路径(Phase 0即预留)，学科标签：用户手动打标为主+系统建议为辅+路径推断兜底，跨课程Tag Jaccard桥接
9. **对话归档生命周期** — Hot-Warm-Cold作为数据生命周期策略影响搜索(Hot全文/Warm摘要/Cold提取)、上下文注入、学习档案、考察历史
10. **事件驱动协调(EventBus)** — 自建asyncio EventBus(~100行)连接FSRS/Graphiti/LanceDB/UI级联写入，三层优先级(Tier1 await内存计算/Tier2 fire+retry+JSONL outbox/Tier3 fire-and-forget WebSocket)，幂等保障(BKT/FSRS幂等+Neo4j MERGE+LanceDB重索引)，复用已有CircuitBreaker+FallbackSyncService

## Starter Template Evaluation（Brownfield 适配）

> 本项目为 Brownfield，技术栈已通过 PRD 创建、PRD 审查、UX 设计、10 个调研 Agent 验证确定。此章节记录已确定的技术基础，不做重新选型。

### 已确定的技术基础

| 层 | 技术选型 | 来源 |
|----|---------|------|
| 桌面壳 | Tauri 2.0（Rust + WebView2/WKWebView/webkit2gtk） | DE-1 + 6-agent 调研 + GDR 16-agent 验证 |
| 前端框架 | React 19 + TypeScript | DE-1 + GDR 验证（Langflow/Dify/Flowise 参考） |
| 前端 Canvas | ReactFlow 12.10.1（@xyflow/react，DOM 渲染） | DE-1 + GDR 验证（30k stars，生产级） |
| 前端状态 | Zustand（全局）+ useState（本地）+ TanStack Query（异步） | GDR-P1-2 + ReactFlow 官方推荐 |
| 前端构建 | Vite 7.x（pin，Vite 8 未验证 Tauri 兼容）+ @vitejs/plugin-react-swc | DE-1 + GDR-P1-1 |
| 前端 UI | shadcn/ui + TailwindCSS v4 + Catppuccin Mocha | DE-2 + GDR 验证（65k stars + tauri-ui 模板） |
| 前端存储 | 本地 JSON 文件（Tauri fs API） | DE-1 + Frontend-first 架构 |
| 后端框架 | FastAPI（Python 3.11+） | 已有代码（DE-3 保留） |
| Agent 引擎 | Claude Agent SDK spawn 官方 Claude Code CLI（Mode D，Tool-UI Bridge，用户订阅额度） | PRD 决策 #10 + Epics session 调研确认 |
| MCP 暴露 | FastAPI-MCP（ASGI 直连，3 行代码） | 调研 |
| 知识图谱 | Neo4j 5.x + Graphiti（graphiti_core 内嵌，方案 C） | PRD + 调研 |
| 个人记忆引擎 | Graphiti 独立子系统（三通道写入 + Pydantic Schema） | 本 session 决策 #1 |
| 向量存储 | LanceDB 0.4+（bge-m3 1024d Dense+Sparse） | PRD + 后端 PRD |
| 对话存储 | SQLite + aiosqlite | PRD |
| Embedding | bge-m3（Ollama 容器，CPU 可跑） | PRD + 调研 |
| Reranker | gte-reranker-modernbert-base（149M，备选 Qwen3-4B） | 本 session 决策 #2 |
| LLM 统一层 | LiteLLM SDK（100+ 模型，双层 Key） | PRD |
| 算法管道 | LangGraph（保留不变，Agentic RAG L1+L2） | PRD |
| 容器编排 | Docker Compose（Neo4j + FastAPI + Ollama），Tauri Shell Plugin 管理生命周期 | 已有代码 + DE-4 |
| Docker 管理 | Tauri Shell Plugin（主）+ HTTP IPC 备选（缓解 Windows spawn bug） | DE-4 + GDR-P1-3 |

## Core Architectural Decisions

> 经过 PRD 创建、PRD 审查、UX 设计、10 个调研 Agent 验证、20 个对抗审查 Agent、12 个冲突解决，5 个类别的核心决策全部已确认。

### Decision Priority Analysis

**Critical Decisions（已全部确认）：**
- 双系统架构：LanceDB 内容检索 + Graphiti 个人记忆引擎（独立子系统，三通道写入）
- Mode D 架构：Claude Agent SDK spawn 官方 Claude Code CLI（用户订阅额度，Claudian/Pencil/Zed ACP 模式验证）+ Tool-UI Bridge + MCP 暴露（FastAPI-MCP ASGI 直连）。参考实现：Claudian(YishenTu/claudian) spawn 模式，通过 Options.resume 管理 per-node session，Options.mcpServers 注入后端工具。认证自动继承 ~/.claude/.credentials.json。Fallback：FR-AGENT-03 引擎可替换，政策变化时可回退 API Key
- Frontend-first：本地 JSON local-first + Zustand 全局状态 + delta sync 到后端
- ReactFlow 白板引擎：@xyflow/react DOM 渲染自定义节点+边（~1000 节点天花板，50-300 安全）
- 6 层 Agent 防御：Layer0-5 各层约束强度已标注，Layer3 MVP 仅 Claude Code
- 算法管道：BKT+FSRS 双引擎 + 5-6 信号→单维掌握度 + AutoSCORE 两阶段 + Area9 校准
- 四层路由 + 六路物理通道 + A-RAG 回源验证（Agent 侧执行）

**Important Decisions（已全部确认）：**
- Reranker：gte-reranker-modernbert-base（149M），备选 Qwen3-4B
- 索引管道：bge-m3 Dense+Sparse(MVP) + 标题智能分块 512token + jieba 中文 + delete-before-insert
- 对话归档：Hot-Warm-Cold 三层时间归档 + 双触发（时间+容量 50K tokens）
- 对话上下文：三层 Tier（全量+observation masking / 摘要 / RAG）+ Claude Compaction 兜底
- EventBus：自建 asyncio 三层优先级 + 复用 CircuitBreaker/FallbackSyncService
- 白板分类：软分类（外在学科标签用户打标为主 / 内在内容类型系统分析+用户覆盖）
- 学科标签：用户手动打标为主 + 系统建议为辅 + 路径推断兜底

**Deferred Decisions（Phase 2+）：**
- ColBERT 三模态评估（Phase 2）
- N 信号→5 维 Beta-Bayesian 融合（Phase 3+）
- OLM 三层面板（Phase 2）
- Layer 3 替换引擎降级策略（远期）
- 概念关联推荐图分析（MVP 可延后）

### Data Architecture

| 存储层 | 技术 | 职责 | 数据类型 |
|--------|------|------|---------|
| 知识图谱 | Neo4j 5.x + Graphiti（graphiti_core 内嵌方案 C） | 节点关系/学习轨迹/语义边/个人记忆 | 结构化图数据 |
| 个人记忆引擎 | Graphiti 独立子系统 | Tips/Edge 理由/错误/问答写入检索+图遍历+时序感知+矛盾检测 | 三通道写入（Agent 自报告/对话蒸馏/考察提取），Pydantic Schema |
| 向量存储 | LanceDB 0.4+ | 笔记 chunk 语义检索 + 对话向量化 | bge-m3 1024d Dense+Sparse 向量 |
| 对话持久化 | SQLite + aiosqlite | 对话消息/结构化查询/会话管理 | Hot-Warm-Cold 三层时间归档 |
| 前端本地 | 本地 JSON 文件（Tauri fs API） | 白板数据 local-first 存储 | 节点/边/视图状态，Zustand 内存状态 |

**同步架构**：本地 JSON（Zustand 内存状态 ↔ Tauri fs 持久化）→ delta sync（2s debounce → 批量 POST → 幂等 UUID → 指数退避，IPC 载荷 <100KB）→ Neo4j/SQLite/LanceDB 三端。单用户不需要 CRDT，last-write-wins。

### Authentication & Security

| 层 | 机制 | 约束强度 |
|----|------|---------|
| Layer 0 | 后端算法权威（不可绕过） | 硬 |
| Layer 1 | 密码学令牌管道（跳步拒绝） | 硬 |
| Layer 2 | CLAUDE.md/AGENTS.md | 建议性 ~80% |
| Layer 3 | Claude Code Hooks | 确定性，仅 Claude Code，MVP 不管替换降级 |
| Layer 4 | 后端审计守护（异步检测信号丢失/跳步/算法未更新） | 硬 |
| Layer 5 | 结构化输出 | 引导性 ~90% |

API Key 仅存 Tauri 应用本地配置（Tauri Store Plugin），不明文不入日志。双层 Key 分离（外层用户 Key / 内层后端 Key）。

### API & Communication Patterns

| 通信路径 | 协议 | 用途 |
|---------|------|------|
| 前端 ↔ 后端 | REST（FastAPI :8001） | 数据 CRUD / 索引触发 / 健康检查 |
| 前端 ← 后端 | WebSocket | 实时推送（精通度变化/同步状态/评分通知） |
| Agent ↔ 后端 | MCP Protocol（JSON-RPC） | 算法工具调用（FastAPI-MCP ASGI 直连） |
| 前端 ↔ Rust | Tauri IPC（invoke/events） | 文件系统操作/Docker管理/系统信息。**载荷<100KB** |
| Agent → 前端 | Tool-UI Bridge | Agent 工具调用 → 同时更新本地 JSON + Zustand Store → React 重渲染 |
| 后端内部 | EventBus（asyncio） | FSRS/Graphiti/LanceDB/UI 级联写入，三层优先级 |

### Frontend Architecture

| 维度 | 决策 |
|------|------|
| 桌面壳 | Tauri 2.0（WebView2/WKWebView/webkit2gtk） |
| 框架 | React 19 + TypeScript + Vite 7.x |
| Canvas | ReactFlow 12.10.1（@xyflow/react DOM 渲染，~1000节点天花板，React.memo 必须） |
| 状态管理 | 三层：Zustand（全局白板+UI状态）/ TanStack Query（服务端异步）/ useState（组件本地） |
| 组件 | 30+ React 组件 7 组（A 对话/B 检验/C Dashboard/D 档案/E 白板/F 系统/G 全局），shadcn/ui 基础组件 |
| ChatPanel | 三模式复用（普通/考察/Edge），React 条件渲染差异化 UI |
| CSS | TailwindCSS v4 + shadcn/ui oklch 变量 + Catppuccin Mocha 主题 + cl- 组前缀 |
| 布局 | Tauri 窗口内 React 路由，面板切换即替换不叠加 |

### Infrastructure & Deployment

| 维度 | 决策 |
|------|------|
| 部署 | Tauri 桌面应用 + Docker Compose 本地（Neo4j + FastAPI + Ollama） |
| 硬件 | 最低 ~8GB RAM（Neo4j 4GB + Python 2GB + Ollama ~2GB + Tauri ~30MB），SSD 推荐 |
| 启动 | Tauri 应用启动(<1s) → Shell Plugin 执行 docker-compose up → 5步检测向导 + 健康面板 |
| 更新 | tauri-plugin-updater 自动更新(桌面) + docker-compose pull(后端) + Alembic(SQL)+Cypher(Neo4j) |
| 监控 | 100% LLM 调用日志 + 管道健康指标 + 错误不静默 + Token 成本追踪 |
| 离线 | 4 场景降级（无网络/Docker 未启/Neo4j 异常/LanceDB 损坏） |

### Decision Impact Analysis

**实施序列（依赖顺序）：**
1. Phase 0：Brownfield 修复（8 CRITICAL + 7 HIGH），4 Phase 渐进
2. 前端基础：esbuild-svelte 配置 + CanvasView + IndexedDB schema + Dexie liveQuery
3. 核心对话：ChatPanel + per-node Session + Tool-UI Bridge + MCP 连接
4. 算法激活：BKT/FSRS 管道连通 + EventBus + AutoSCORE
5. 检验白板：三种考察模式 + 递归 + 白板分类
6. 个人记忆：Graphiti 三通道写入 + 自定义 Schema + 检索 API
7. 精打磨：学习档案 + 校准追踪 + 质量保证

**跨组件依赖：**
- Tool-UI Bridge 依赖 IndexedDB schema + Dexie liveQuery + MCP 连接
- AutoSCORE 依赖 per-node Session + EventBus + BKT/FSRS
- Graphiti 个人记忆依赖 对话蒸馏管道 + Hot-Warm-Cold 归档
- 检验白板依赖 全部核心对话功能 + 精通度系统

## Implementation Patterns & Consistency Rules

> 以下模式确保多个 AI Agent 写的代码互相兼容。违反这些规则 = 集成冲突。

### Naming Patterns

**Python 后端（FastAPI + LangGraph）：**

| 类别 | 规范 | 示例 | 反例 |
|------|------|------|------|
| 文件名 | snake_case.py | `mastery_engine.py` | `MasteryEngine.py` |
| 函数/变量 | snake_case | `update_mastery()`, `node_id` | `updateMastery()` |
| 类名 | PascalCase | `MasteryEngine`, `GraphitiBridgeService` | `mastery_engine` |
| 常量 | UPPER_SNAKE | `MAX_RETRY_COUNT = 3` | `maxRetryCount` |
| API 端点 | snake_case 复数 | `/api/v1/exam_sessions` | `/api/v1/examSession` |
| Pydantic Model | PascalCase | `class ScoreResult(BaseModel)` | `class score_result` |
| EventBus 事件 | UPPER_SNAKE | `SCORE_SUBMITTED`, `BKT_UPDATED` | `scoreSubmitted` |

**TypeScript 前端（React 19 + Tauri 2.0）：**

| 类别 | 规范 | 示例 | 反例 |
|------|------|------|------|
| 文件名（组件） | PascalCase.tsx | `ChatPanel.tsx` | `chat-panel.tsx` |
| 文件名（store） | kebab-case.store.ts | `canvas.store.ts` | `CanvasStore.ts` |
| 文件名（工具） | kebab-case.ts | `sync-engine.ts` | `SyncEngine.ts` |
| 变量/函数 | camelCase | `selectedNodeId`, `updateMastery()` | `selected_node_id` |
| 类名 | PascalCase | `class CanvasState` | `class canvasState` |
| CSS 类名 | cl- 前缀 + kebab-case（TailwindCSS 自定义层） | `.cl-chat-panel` | `.chatPanel` |
| React props | camelCase | `masteryLevel`, `isSelected` | `mastery_level` |
| Zustand Store | camelCase 单例 | `export const useCanvasStore = create(...)` | — |

**Neo4j/Graphiti：**

| 类别 | 规范 | 示例 | 反例 |
|------|------|------|------|
| Node Label | PascalCase | `KnowledgePoint`, `Misconception` | `knowledge_point` |
| Relationship Type | UPPER_SNAKE | `HAS_MISCONCEPTION`, `RELATES_TO` | `hasMisconception` |
| Property | camelCase | `createdAt`, `pMastery` | `created_at` |

**本地 JSON 文件：**

| 类别 | 规范 | 示例 |
|------|------|------|
| 文件名 | kebab-case.json | `whiteboard-{id}.json`, `sync-queue.json` |
| 字段名 | camelCase | `nodeId`, `canvasId`, `createdAt` |
| 目录 | Tauri appDataDir | `{appDataDir}/whiteboards/`, `{appDataDir}/config/` |

**MCP 工具名：**

| 类别 | 规范 | 示例 |
|------|------|------|
| 工具名 | snake_case | `query_mastery`, `generate_question`, `score_answer` |
| 参数名 | snake_case | `node_id`, `canvas_path`, `exam_mode` |

### Structure Patterns

**前端目录结构：**
```
frontend/
├── src/
│   ├── components/          # React 组件（按 7 组分目录）
│   │   ├── chat/           # A 组：ChatPanel, MessageBubble, InputBar...（.tsx）
│   │   ├── exam/           # B 组：ExamModeSelector, HintButton...
│   │   ├── dashboard/      # C 组：DashboardView, CanvasCard...
│   │   ├── profile/        # D 组：LearningProfile, TipCard...
│   │   ├── canvas/         # E 组：CanvasView（ReactFlow 容器）, CustomNode, CustomEdge...
│   │   ├── system/         # F 组：SetupWizard, HealthPanel...
│   │   ├── global/         # G 组：SyncIndicator, OfflineBanner
│   │   └── ui/             # shadcn/ui 基础组件（Button, Dialog, Card...）
│   ├── stores/             # Zustand 状态（*.store.ts）
│   │   ├── canvas.store.ts
│   │   ├── chat.store.ts
│   │   ├── exam.store.ts
│   │   ├── mastery.store.ts
│   │   └── system.store.ts
│   ├── services/           # 业务服务
│   │   ├── sync-engine.ts
│   │   ├── api-client.ts       # REST API 封装（snake→camelCase 转换）
│   │   ├── tauri-fs.ts         # Tauri fs API 封装（JSON 读写）
│   │   ├── tauri-shell.ts      # Docker 管理（Shell Plugin + HTTP IPC 备选）
│   │   └── agent-bridge.ts     # Tool-UI Bridge 单一入口
│   ├── hooks/              # React 自定义 hooks
│   │   ├── useReactFlow.ts     # ReactFlow 封装 hooks
│   │   └── useTauriIPC.ts      # Tauri IPC 封装
│   ├── skills/             # 命令技能（prompt 模板）
│   │   ├── registry.ts
│   │   └── templates/
│   ├── lib/                # shadcn/ui 工具（cn, utils）
│   │   └── utils.ts
│   ├── types/              # TypeScript 类型定义
│   │   ├── canvas.d.ts
│   │   ├── chat.d.ts
│   │   ├── exam.d.ts
│   │   ├── mastery.d.ts
│   │   └── api.d.ts            # 基于后端 Pydantic Model 同步
│   ├── App.tsx             # 根组件（ReactFlow 容器 + 面板路由）
│   ├── main.tsx            # React 入口
│   └── index.css           # TailwindCSS 入口 + Catppuccin oklch 变量
├── src-tauri/              # Rust 后端
│   ├── src/
│   │   ├── main.rs             # Tauri 入口
│   │   ├── docker.rs           # Docker Compose 生命周期管理
│   │   └── lib.rs
│   ├── capabilities/
│   │   └── default.json        # Shell/fs 权限声明
│   ├── tauri.conf.json         # Tauri 配置（CSP/窗口/权限）
│   └── Cargo.toml
├── package.json
├── vite.config.ts
├── tailwind.config.ts      # TailwindCSS v4 配置
├── tsconfig.json
└── components.json         # shadcn/ui 配置
```

**后端目录结构（保持现有 + 新增）：**
```
backend/app/
├── api/                    # FastAPI 路由（保持现有）
├── services/               # 业务服务（保持现有 + 新增）
│   ├── mastery_engine.py   # BKT+FSRS（已有）
│   ├── event_bus.py        # EventBus（新建）
│   ├── graphiti_memory.py  # Graphiti 个人记忆引擎（新建）
│   ├── conversation_archive.py  # Hot-Warm-Cold 归档（新建）
│   └── exam_service.py     # 检验白板服务（新建）
├── models/                 # Pydantic 模型
├── core/                   # 配置/常量
├── agentic_rag/           # LangGraph 管道（保持现有）
├── mcp/                    # MCP Server（新建）
│   └── server.py           # FastAPI-MCP 暴露
└── graphiti/               # Graphiti Schema（新建）
    ├── entity_types.py     # Misconception/LearningTip/KnowledgePoint
    └── edge_types.py       # HasMisconception/LearnedFrom/RelatesTo
```

**测试位置：**
- 前端：`obsidian-plugin/src/__tests__/` 目录集中
- 后端：`backend/tests/` 目录（保持现有结构）
- 算法单测：`backend/tests/unit/` 下按模块

### Format Patterns

**API 响应格式（FastAPI）：**

```python
# 成功响应
{"data": {...}, "meta": {"timestamp": "2026-03-16T12:00:00Z"}}

# 错误响应
{"error": {"code": "RETRIEVAL_FAILED", "message": "检索失败", "detail": "..."}}

# 列表响应
{"data": [...], "meta": {"total": 42, "offset": 0, "limit": 20}}
```

**JSON 字段命名：**
- 前后端传输：**snake_case**（FastAPI 默认，前端适配）
- 前端内部（Svelte Store / IndexedDB）：**camelCase**
- 转换层：在 API service 层统一转换

**日期时间：**
- 传输格式：ISO 8601 字符串 `"2026-03-16T12:00:00Z"`
- 存储格式：SQLite 用 ISO 字符串，Neo4j 用 `datetime()` 类型
- 前端展示：用户 locale 格式化

**精通度数值：**
- 内部存储/传输：0.0 ~ 1.0 float
- 用户展示：不直接展示数字，用颜色/文字描述

### Communication Patterns

**EventBus 事件定义规范：**

```python
class LearningEvent:
    event_type: EventType      # UPPER_SNAKE 枚举
    payload: dict              # 必须包含 node_id + session_id
    timestamp: datetime        # 自动生成
    source: str                # 发送方标识 "autoscore" / "user_action" / "fsrs"
    tier: Tier                 # TIER_1_CRITICAL / TIER_2_IMPORTANT / TIER_3_BEST_EFFORT
```

**Zustand Store 更新规范：**

```typescript
// 正确：通过 Store action 更新（封装副作用）
useCanvasStore.getState().addNode(newNode);  // 内部处理 JSON 写入 + sync

// 错误：直接修改 state
useCanvasStore.setState({ nodes: [...nodes, newNode] });  // 绕过了持久化逻辑
```

**WebSocket 消息格式：**

```json
{
  "type": "mastery_update | sync_status | score_complete | health_check",
  "payload": {},
  "timestamp": "2026-03-16T12:00:00Z",
  "session_id": "xxx"
}
```

**MCP 工具调用令牌链：**

```
Agent 调用 generate_question → 返回 {result, token_A}
Agent 调用 score_answer(token=token_A) → 返回 {result, token_B}
Agent 调用 update_fsrs(token=token_B) → 完成
跳步 → 后端拒绝（token 不匹配）
```

### Process Patterns

**错误处理分层：**

| 层 | 策略 | 用户感知 |
|----|------|---------|
| LLM API 错误 | 重试 3 次 → 降级提示 | "AI 暂时不可用，请稍后再试" |
| 后端 API 错误 | CircuitBreaker → JSONL outbox | 健康面板变红 + Notice |
| 文件系统错误 | Tauri fs 重试 → 用户提示 | "保存失败，请检查磁盘空间" |
| React 组件错误 | ErrorBoundary 捕获 → 降级 UI | 组件区域显示错误提示，不崩溃整个应用 |
| 评分不确定 | 标记低信心 → 邀请用户复核 | "AI 对这次评分不太确定，你觉得准确吗？" |

**加载状态规范：**

```typescript
type LoadingState = 'idle' | 'loading' | 'success' | 'error';

// 每个异步操作都必须管理加载状态
// 全局加载状态在 system.store.ts (Zustand)
// 服务端异步状态用 TanStack Query 自动管理
// 组件级加载状态用 useState
```

**重试策略：**

| 场景 | 策略 | 参数 |
|------|------|------|
| LLM API 调用 | 指数退避 | 2s → 4s → 8s，最多 3 次 |
| 后端 sync | Outbox 指数退避 | 2s → 4s → 8s → 16s → 32s，最多 5 次 |
| WebSocket 重连 | 线性退避 | 每 30s ping，断连后 5s/10s/15s 重连 |
| Neo4j 写入 | CircuitBreaker | CLOSED → OPEN(5 次失败) → HALF_OPEN(30s 后) |

### Enforcement Guidelines

**All AI Agents MUST：**
1. 编辑 Python 文件后运行 `ruff check` + `ruff format --check`
2. 编辑 TypeScript/React 文件后确认无 TypeScript 编译错误
3. 新建文件必须遵循上述目录结构，不得在根目录随意创建
4. API 端点必须使用 Pydantic Model 定义请求/响应 schema
5. EventBus 事件必须定义在 `models/canvas_events.py` 的枚举中
6. React 组件必须使用 cl- 前缀 CSS 类名（TailwindCSS 自定义层）
7. 禁止在组件中直接操作文件系统/Tauri IPC — 必须通过 Store action 或 hooks
8. ReactFlow 自定义节点/边组件必须 React.memo()（性能硬性要求）
9. Tauri IPC 单次载荷 <100KB（Windows 性能约束）
10. 禁止 mock/空函数 — 每个函数必须有真实实现或明确的 NotImplementedError

**Pattern 违规检查：**
- 提交前：ruff lint + TypeScript 编译检查
- Code Review：独立 Agent 对抗性审查（DD-07）
- 命名检查：grep 搜索不符合规范的命名模式

## Project Structure & Boundaries

> 经过 Party Mode 4 角色审查（8 项发现）、Advanced Elicitation 5 轮深度分析（First Principles 6 假设检验 + Red Team 6 攻击向量 + Comparative Analysis 3 竞品对比 + Reverse Engineering 4 场景验证 + Mentor and Apprentice 5 盲区暴露），共产出 26 项改进纳入此章节。

### Complete Project Directory Structure

**前端（Tauri 桌面应用）：**

```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts               # TailwindCSS v4（CSS-first @theme inline）
├── components.json                   # shadcn/ui 配置
├── .env.example
├── src/
│   ├── main.tsx                      # React 入口（createRoot）
│   ├── App.tsx                       # 根组件（ReactFlow 容器 + 面板路由）
│   ├── index.css                     # TailwindCSS 入口 + Catppuccin oklch 变量映射（~100 变量）
│   ├── components/
│   │   ├── ui/                       # shadcn/ui 基础组件（不直接修改，wrapper 模式）
│   │   │   ├── button.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   ├── chat/                     # A 组：AI 对话（CSS: cl-chat-*）
│   │   │   ├── ChatPanel.tsx             # 三模式复用（普通/考察/Edge）
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── InputBar.tsx              # /命令触发 + 拖拽创建节点
│   │   │   ├── TipAnnotation.tsx
│   │   │   ├── SkillSelector.tsx
│   │   │   └── StreamingIndicator.tsx
│   │   ├── exam/                     # B 组：检验白板（CSS: cl-exam-*）
│   │   │   ├── ExamCanvas.tsx
│   │   │   ├── ExamModeSelector.tsx
│   │   │   ├── HintButton.tsx
│   │   │   ├── ScoreDisplay.tsx
│   │   │   ├── CalibrationPrompt.tsx
│   │   │   ├── CognitiveLoadTimer.tsx
│   │   │   └── ExamRecord.tsx
│   │   ├── dashboard/                # C 组：Dashboard（CSS: cl-dash-*）
│   │   │   ├── DashboardView.tsx
│   │   │   ├── CanvasCard.tsx
│   │   │   ├── ExamCard.tsx
│   │   │   ├── ExamLauncher.tsx
│   │   │   └── CostTracker.tsx           # Token 成本展示（FR-QA-04）
│   │   ├── profile/                  # D 组：学习档案（CSS: cl-profile-*）
│   │   │   ├── LearningProfile.tsx
│   │   │   ├── TipCard.tsx
│   │   │   ├── WeaknessPanel.tsx
│   │   │   └── QACluster.tsx
│   │   ├── canvas/                   # E 组：白板核心（CSS: cl-canvas-*）
│   │   │   ├── CanvasView.tsx            # ReactFlow 容器（onlyRenderVisibleElements）
│   │   │   ├── CustomNode.tsx            # ⚠️ 必须 React.memo()
│   │   │   ├── CustomEdge.tsx            # ⚠️ 必须 React.memo()
│   │   │   ├── EdgeDialog.tsx            # ⚠️ 必须与 ChatPanel(Edge模式) 同 Agent 同 Story
│   │   │   ├── NodeContextMenu.tsx
│   │   │   └── MasteryIndicator.tsx
│   │   ├── system/                   # F 组：系统管理（CSS: cl-sys-*）
│   │   │   ├── SetupWizard.tsx           # 5 步安装引导（shadcn Dialog）
│   │   │   └── HealthPanel.tsx
│   │   └── global/                   # G 组：全局 UI（CSS: cl-global-*）
│   │       ├── SyncIndicator.tsx
│   │       ├── OfflineBanner.tsx
│   │       └── ErrorBoundary.tsx
│   ├── stores/                       # Zustand 状态管理（*.store.ts）
│   │   ├── canvas.store.ts               # 白板节点/边/视图状态
│   │   ├── chat.store.ts
│   │   ├── exam.store.ts
│   │   ├── profile.store.ts
│   │   ├── mastery.store.ts
│   │   └── system.store.ts
│   ├── services/                     # 业务服务层（MVP 扁平，单文件>300行时允许拆子目录）
│   │   ├── tauri-fs.ts                   # Tauri fs API 封装（JSON 读写+文件监听）
│   │   ├── tauri-shell.ts                # Docker 管理（Shell Plugin + HTTP IPC 备选）
│   │   ├── sync-engine.ts                # delta sync 到后端
│   │   ├── agent-bridge.ts               # Tool-UI Bridge 单一入口
│   │   ├── websocket-client.ts
│   │   └── api-client.ts                 # REST API 封装（snake→camelCase 转换）
│   ├── hooks/                        # React 自定义 hooks
│   │   ├── useReactFlow.ts               # ReactFlow 操作封装
│   │   ├── useTauriIPC.ts                # Tauri invoke/events 封装
│   │   └── useDockerStatus.ts            # Docker 健康状态
│   ├── skills/                       # 命令技能（前端用户交互 prompt）
│   │   ├── registry.ts
│   │   └── templates/                    # 文件名 = 技能 ID
│   │       ├── basic-decompose.md
│   │       ├── four-level-explain.md
│   │       ├── concept-compare.md
│   │       ├── memory-anchor.md
│   │       ├── example-teach.md
│   │       ├── verify-question.md
│   │       ├── oral-explain.md
│   │       ├── deep-explain.md
│   │       ├── question-decompose.md
│   │       ├── deep-decompose.md
│   │       └── scoring.md
│   ├── lib/                          # shadcn/ui 工具
│   │   └── utils.ts                      # cn() 函数 + clsx + tailwind-merge
│   └── types/
│       ├── canvas.d.ts
│       ├── chat.d.ts
│       ├── exam.d.ts
│       ├── mastery.d.ts
│       └── api.d.ts                      # 基于后端 Pydantic Model 同步
├── src-tauri/                        # Rust 后端
│   ├── src/
│   │   ├── main.rs                       # Tauri 入口 + plugin 注册
│   │   ├── docker.rs                     # Docker Compose 生命周期（绝对路径 + 健康检查 + 进程组 kill）
│   │   └── lib.rs
│   ├── capabilities/
│   │   └── default.json                  # Shell/fs/http 权限声明
│   ├── tauri.conf.json                   # CSP / 窗口 / 权限 / 更新
│   └── Cargo.toml
├── __tests__/
│   ├── unit/
│   │   ├── stores/
│   │   └── services/
│   ├── components/
│   │   ├── ChatPanel.test.tsx
│   │   ├── CanvasView.test.tsx
│   │   └── ExamCanvas.test.tsx
│   └── integration/
│       ├── sync-engine.test.ts
│       └── agent-bridge.test.ts
└── docs/
    └── AGENTS.md

# 前端测试环境：vitest + @testing-library/react + jsdom
```

**后端（FastAPI + Docker）：**

```
backend/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── alembic/versions/
├── cypher/migrations/
├── app/
│   ├── main.py                       # FastAPI 入口 + MCP 暴露 + 启动时 MCP 工具重名检测
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── dependencies.py
│   │   └── litellm_config.py
│   ├── api/
│   │   ├── v1/
│   │   │   ├── canvas.py
│   │   │   ├── chat.py
│   │   │   ├── exam.py
│   │   │   ├── mastery.py
│   │   │   ├── search.py
│   │   │   ├── profile.py
│   │   │   ├── system.py
│   │   │   └── sync.py
│   │   └── websocket.py
│   ├── services/
│   │   ├── mastery_engine.py
│   │   ├── autoscore.py
│   │   ├── calibration_tracker.py
│   │   ├── event_bus.py
│   │   ├── graphiti/                     # Schema + 业务逻辑合并
│   │   │   ├── memory_service.py
│   │   │   ├── entity_types.py
│   │   │   ├── edge_types.py
│   │   │   └── client.py
│   │   ├── conversation_archive.py
│   │   ├── exam_service.py
│   │   ├── question_generator.py
│   │   ├── skill_executor.py             # 注入学习历史上下文（不存储模板）
│   │   ├── error_classifier.py
│   │   ├── context_assembler.py
│   │   ├── sync_service.py
│   │   └── health_monitor.py
│   ├── models/
│   │   ├── canvas_models.py
│   │   ├── chat_models.py
│   │   ├── exam_models.py
│   │   ├── mastery_models.py
│   │   ├── search_models.py
│   │   ├── canvas_events.py              # EventBus 事件枚举（追加式编辑）
│   │   └── sync_models.py
│   ├── agentic_rag/
│   │   ├── graph.py
│   │   ├── nodes/
│   │   │   ├── retriever.py              # 通过 lancedb_client 接口，不直接 import indexing/
│   │   │   ├── reranker.py
│   │   │   ├── adaptive_k.py
│   │   │   ├── arag_verifier.py
│   │   │   ├── context_compressor.py
│   │   │   └── faithfulness_check.py
│   │   └── state.py
│   ├── indexing/
│   │   ├── pipeline.py
│   │   ├── chunker.py
│   │   ├── breadcrumb.py
│   │   └── deduplicator.py
│   ├── mcp/
│   │   ├── server.py
│   │   ├── tools.py                      # 工具名顶部常量集中定义
│   │   └── token_chain.py
│   ├── db/
│   │   ├── sqlite_client.py
│   │   ├── neo4j_client.py
│   │   └── lancedb_client.py             # 双场景：批量索引 + 即时单条写入
│   ├── middleware/
│   │   ├── logging_middleware.py
│   │   ├── cost_tracker.py
│   │   └── prompt_injection_guard.py
│   └── audit/
│       └── guardian.py
├── tests/
│   ├── unit/
│   │   ├── test_mastery_engine.py
│   │   ├── test_autoscore.py
│   │   ├── test_token_chain.py
│   │   ├── test_adaptive_k.py
│   │   └── test_error_classifier.py
│   ├── integration/
│   │   ├── test_score_to_mastery.py
│   │   ├── test_retrieval_pipeline.py
│   │   ├── test_graphiti_memory.py
│   │   ├── test_sync_roundtrip.py
│   │   └── test_mcp_token_chain.py
│   ├── regression/                       # Prompt 变更回归测试
│   │   ├── test_autoscore_regression.py
│   │   ├── test_question_gen_regression.py
│   │   └── test_context_extract_regression.py
│   └── fixtures/
│       ├── sample_notes/
│       ├── exam_scenarios/
│       ├── graphiti_data/
│       ├── lancedb_index/
│       └── regression_baselines/
├── prompts/                          # 后端 LLM 系统 prompt（每个文件头标注引用 service）
│   ├── autoscore_v1.md               # 引用方: services/autoscore.py
│   ├── question_gen_v1.md            # 引用方: services/question_generator.py
│   ├── context_extract_v1.md         # 引用方: services/conversation_archive.py
│   └── CHANGELOG.md
└── scripts/
    ├── start.sh
    ├── health_check.sh
    └── backup.sh
```

### Architectural Boundaries

**API Boundaries（前端 ↔ 后端）：**

| 边界 | 协议 | 端点前缀 | 职责 |
|------|------|---------|------|
| 白板数据 | REST | `/api/v1/canvas/` | 节点/边 CRUD、批量同步 |
| 对话管理 | REST | `/api/v1/chat/` | Session 创建/恢复、消息历史 |
| 检验白板 | REST | `/api/v1/exam/` | 出题、评分、记录 |
| 精通度 | REST | `/api/v1/mastery/` | 查询精通度、复习建议 |
| 检索 | REST | `/api/v1/search/` | 四层路由统一入口 |
| 学习档案 | REST | `/api/v1/profile/` | Tips/错误/问答聚合 |
| 系统管理 | REST | `/api/v1/system/` | 健康检查、配置、备份 |
| 数据同步 | REST | `/api/v1/sync/` | 批量幂等同步（Outbox→后端） |
| 实时推送 | WebSocket | `/ws` | 精通度变化/同步状态/评分通知 |
| Agent 工具 | MCP | JSON-RPC | 算法工具调用（FastAPI-MCP 直连） |

**Component Boundaries（前端内部）：**

| 边界 | 通信方式 | 规则 |
|------|---------|------|
| 组件 → Store | Zustand hooks（useCanvasStore 等） | 组件只能通过 Store action 修改状态 |
| Store → 文件系统 | tauri-fs.ts 封装 | Store 内部封装 JSON 持久化，外部透明 |
| Store → Store | **禁止直接引用** | 通过 React props 向下传递 / WebSocket 事件分发 / Zustand subscribe 跨 Store |
| 组件 → API | 通过 services/ 或 TanStack Query | 禁止在组件中直接 fetch |
| Agent → UI | agent-bridge.ts | Tool-UI Bridge 单一入口，只调用 Store action |
| 前端 → Rust | Tauri invoke + events | 通过 hooks/useTauriIPC.ts 封装，载荷 <100KB |

**Service Boundaries（后端内部）：**

| 边界 | 通信方式 | 规则 |
|------|---------|------|
| API → Service | 直接调用 | API 层薄封装，业务逻辑在 Service |
| Service → Service | EventBus | 跨 service 走 EventBus，禁止反向 import |
| Service → DB | db/ 客户端 | 禁止 Service 直接操作数据库驱动 |
| MCP → Service | tools.py 路由 | MCP 工具调用统一走 tools.py 分发 |

**Import 依赖方向（单向，禁止反向）：**

```
api/ → services/ → db/
       services/ → models/
       mcp/     → services/
       agentic_rag/nodes/ → db/lancedb_client
       services/graphiti/ 内部不得反向 import services/ 根目录
```

**Data Boundaries（存储隔离）：**

| 存储 | 写入方 | 读取方 | 隔离策略 |
|------|--------|--------|---------|
| 本地 JSON | 前端 Store + Agent Bridge | 前端组件（Zustand subscribe） | subject + 文件目录隔离 |
| Neo4j | 后端 Service + Graphiti | 后端 Service（Cypher） | vault_id + subject 标签 |
| SQLite | 后端 chat/archive Service | 后端 Service（aiosqlite） | session_id + node_id |
| LanceDB | 后端 indexing 管道（批量）+ services（即时单条） | 后端 RAG 管道 | table per vault + subject |
| Graphiti | 后端三通道写入 | 后端检索 + 上下文组装 | group_id per vault |

### Agent Runtime Location（Agent 运行时位置）

```
用户操作 → Tauri 桌面应用 (WebView)
              ↓
         Agent SDK (客户端侧，spawn Claude Code CLI)
         ├── 读取 skills/templates/ prompt 模板
         ├── 构建完整 prompt（模板 + 学习上下文）
         ├── 发送给 LLM（用户 Claude 订阅额度）
         └── 调用 MCP 工具 → JSON-RPC → FastAPI 后端
                                          ├── 算法计算 / 数据读写
                                          └── 返回结果 → Agent → Tool-UI Bridge → 本地 JSON + Zustand → React UI
```

| 运行位置 | 组件 | 职责 |
|---------|------|------|
| Tauri WebView | Agent SDK（spawn CLI） | Prompt 构建、LLM 对话、工具调用编排 |
| Tauri WebView | skills/templates/ | 用户技能 prompt 模板 |
| Tauri WebView | agent-bridge.ts | Tool-UI Bridge |
| Tauri Rust | docker.rs | Docker Compose 生命周期管理（Shell Plugin） |
| Docker 后端 | mcp/tools.py | MCP 工具执行 |
| Docker 后端 | prompts/*.md | LLM 系统 prompt（评分/出题/提取） |
| Docker 后端 | services/skill_executor.py | 注入学习历史上下文 |

### API Type Sync Strategy（前后端类型同步）

| 策略 | 说明 |
|------|------|
| Schema 权威方 | 后端 Pydantic Model 是唯一权威定义 |
| 前端类型来源 | `types/api.d.ts` 基于后端 Pydantic Model 手动同步 |
| 变更规则 | API 字段变更的 Story 必须前后端同 Agent 同时改 |
| 转换层 | `api-client.ts` 统一 snake_case ↔ camelCase |
| 校验 | CI 可选：openapi-typescript-codegen diff 检查 |

### Requirements to Structure Mapping

**FR 能力域 → 文件映射：**

| FR 能力域 | 前端组件 | 后端服务 | 存储 |
|-----------|---------|---------|------|
| 1. 知识图谱管理 | `canvas/*`(ReactFlow) + `stores/canvas.store` | `api/canvas` + `db/neo4j_client` | Neo4j + 本地 JSON |
| 2. 节点AI对话 | `chat/*` + `stores/chat.store` | `api/chat` + `services/context_assembler` + `conversation_archive` | SQLite + Graphiti |
| 3. Edge对话 | `canvas/EdgeDialog` + `chat/ChatPanel`(Edge模式) | `services/graphiti/memory_service`(双写) | Neo4j + LanceDB |
| 4. 检验白板 | `exam/*` + `stores/exam.store` | `api/exam` + `services/exam_service` + `autoscore` | SQLite + Neo4j |
| 5. 精通度追踪 | `stores/mastery.store` + `canvas/MasteryIndicator` | `services/mastery_engine` + `calibration_tracker` | Neo4j + SQLite |
| 6. 检索与个性化 | `services/api-client` | `agentic_rag/*` + `indexing/*` + `services/graphiti/` | LanceDB + Graphiti |
| 7. 命令技能系统 | `skills/*` + `chat/SkillSelector` | `services/skill_executor` | prompt 模板文件 |
| 8. 学习档案 | `profile/*` + `stores/profile.store` | `api/profile` + `conversation_archive` | Graphiti + SQLite |
| 9. 质量保证 | `dashboard/CostTracker` | `middleware/*` + `audit/guardian` | 结构化日志 |
| 10. Dashboard | `dashboard/*` | `api/exam`(列表) + `api/canvas`(列表) | 本地 JSON + SQLite |
| 11. Agent集成与MCP | `services/agent-bridge` + `hooks/useTauriIPC` | `mcp/*` | MCP Protocol |
| 12. 系统配置 | `system/SetupWizard` + `system/HealthPanel` | `api/system` | Tauri Store(本地配置) |

### Integration Points

**关键数据流图：**

**检索请求流：**
```
用户输入查询 → ChatPanel(React) → agent-bridge → Agent SDK(spawn CLI)
  → MCP tool: search_memories(query)
  → api/search.py → agentic_rag/graph.py
  → retriever(四层路由) → reranker → adaptive_k → arag_verifier(回源)
  → context_compressor → faithfulness_check
  → 返回结果 → Agent 组装回复 → ChatPanel
```

**考察启动流：**
```
用户点击 ExamLauncher → exam-state 创建 session
  → POST /api/v1/exam/start → exam_service.py
  → question_generator(选节点+出题，注入 Tips/Edge/错误)
  → MCP tool: generate_question(token_A) → 返回题目+token
  → Agent 展示题目 → ChatPanel(考察模式) → 用户作答
  → MCP tool: score_answer(token_A) → autoscore(两阶段)
  → EventBus: SCORE_SUBMITTED → mastery_engine(BKT+FSRS)
  → EventBus: BKT_UPDATED → graphiti(写入) + WebSocket(推送)
  → mastery-state → 节点颜色变化
```

**对话归档流（Hot→Warm→Cold）：**
```
对话进行中 → SQLite 存储完整消息(Hot)
  → 双触发检测(30天 OR 50K tokens)
  → conversation_archive: LLM 提取摘要+关键错误+Tips
  → Warm: SQLite 保留摘要，原文标记归档
  → Graphiti 三通道写入: Agent自报告+对话蒸馏+考察提取
  → 6个月后 → Cold: 仅保留 Graphiti 提取物
  → 影响下游: 搜索(Hot全文/Warm摘要/Cold提取) + 上下文注入 + 学习档案
```

**白板操作流：**
```
用户操作 ReactFlow 节点 → CanvasView onNodesChange
  → useCanvasStore.addNode() → Zustand 内存更新 + Tauri fs 写入本地 JSON
  → sync-engine(2s debounce, 载荷<100KB) → POST /api/v1/sync/
  → Neo4j MERGE + LanceDB 索引触发 → WebSocket: sync_status
  → useSystemStore → SyncIndicator 更新
```

**评分完成流：**
```
Agent 调用 MCP tool: score_answer(token) → autoscore.py
  → EventBus: SCORE_SUBMITTED [Tier1, await]
  → mastery_engine: BKT + FSRS 更新
  → EventBus: BKT_UPDATED [Tier2, fire+retry]
  → graphiti: 写入评分记录 + Neo4j: 更新 pMastery
  → WebSocket: mastery_update → mastery-state → 节点颜色
```

**External Integrations：**

| 外部服务 | 集成方式 | 配置位置 |
|---------|---------|---------|
| Claude API / LLM Provider | LiteLLM SDK（HTTP） | `core/litellm_config.py` + Tauri 设置面板 |
| Ollama（bge-m3） | HTTP API（Docker 内网） | `docker-compose.yml` |
| Neo4j | Bolt 协议（Docker 内网） | `docker-compose.yml` + `db/neo4j_client.py` |
| 本地文件系统 | Tauri fs API | `src-tauri/capabilities/default.json` |
| Docker Compose | Tauri Shell Plugin（绝对路径） | `src-tauri/src/docker.rs` |

### Complexity Justification（复杂度合理性声明）

本项目比同类产品（Khoj / Obsidian Copilot / AnythingLLM）结构更复杂。这不是过度设计，而是 PRD 需求驱动：

| 复杂度维度 | Canvas | 竞品典型值 | 驱动需求 |
|-----------|--------|-----------|---------|
| 存储系统 4 种 | Neo4j+LanceDB+SQLite+本地JSON | 1-2 种 | 知识图谱(Neo4j)+向量检索(LanceDB)+对话持久化(SQLite)+白板离线(本地JSON) |
| 前端 7 组 30+ 组件 | React 场景分组 A-G + shadcn/ui | 扁平 5-10 | ReactFlow 白板+三模式ChatPanel+检验白板+Dashboard+学习档案 |
| 后端 13+ service | 按职责分离 | 5-8 个 | BKT+FSRS双引擎+AutoSCORE+Graphiti三通道+A-RAG+4类错误路由 |
| 通信协议 4 种 | REST+WS+MCP+EventBus | 1 种 | 数据CRUD+实时推送+Agent工具调用+内部级联 |

**AI Agent 开发者须知**：当你觉得"这个结构太复杂了，能不能简化"时——请先查 PRD 确认对应的 FR 需求是否真的需要这个组件。如果 FR 存在，则复杂度是必要的。

### Enforcement Guidelines — Structure Defense Rules

**共享文件编辑规则：**

| 共享文件 | 规则 |
|---------|------|
| `models/canvas_events.py` | 追加式编辑：新事件只能追加到枚举末尾 |
| `types/api.d.ts` | 后端变更 → 同 Agent 同 Story 同步改 |
| `index.css` | Catppuccin oklch 变量映射 + TailwindCSS 入口 + cl- 基础样式 |
| `components/ui/*` | shadcn/ui 组件不直接修改，用 wrapper 模式扩展 |

**Store 访问控制：**

- `tauri-fs.ts` 的文件操作**仅 `stores/` 目录可 import**
- 组件、services 层禁止直接操作 Tauri fs
- `agent-bridge.ts` 内部只调用 Store action

**跨 Store 数据流模式：**

| 场景 | 正确方式 | 错误方式 |
|------|---------|---------|
| 组件需要多个 Store | 组件分别 useXxxStore() → props 向下传递 | Store A 里 import Store B |
| Store A 变化触发 B | Zustand subscribe 跨 Store 监听 | Store A 直接调用 Store B 内部方法 |
| 后端事件更新多个 Store | WebSocket → websocket-client 分发各 Store | Store 互相通知 |

**MCP 工具注册：**

- 所有工具名在 `mcp/tools.py` 顶部常量列表集中定义
- `main.py` 启动时检查唯一性，重名 → raise ValueError

**CSS 组前缀约定：**

| 组 | 前缀 |
|----|------|
| A 对话 | `cl-chat-*` |
| B 检验 | `cl-exam-*` |
| C Dashboard | `cl-dash-*` |
| D 档案 | `cl-profile-*` |
| E 白板 | `cl-canvas-*` |
| F 系统 | `cl-sys-*` |
| G 全局 | `cl-global-*` |

- `:global()` 仅可用于 Obsidian 原生类，禁止用于 `cl-` 类名跨组
- **前缀跟随文件归属目录，不跟随视觉风格**

**跨组实现约束：**

| 约束 | 组件 | 规则 |
|------|------|------|
| Edge 对话一致性 | EdgeDialog(E) + ChatPanel Edge模式(A) | 同 Agent 同 Story |
| 跨组开发顺序 | — | 先触发入口(UI) → 再逻辑(Service) → 最后连通数据流 |

**测试对应规则：**

```
改了 services/X.py          → 跑 tests/unit/test_X.py
改了 agentic_rag/**          → 跑 tests/integration/test_retrieval_pipeline.py
改了 mcp/**                  → 跑 tests/integration/test_mcp_token_chain.py
改了 models/**               → 跑 tests/unit/ 全部
改了 components/{group}/X.tsx  → 跑 __tests__/components/X.test.tsx
改了 stores/X.store.ts       → 跑 __tests__/unit/stores/ 相关
改了 prompts/*.md            → 跑 tests/regression/ 对应
```

**Prompt 文件规范：**

```markdown
<!-- prompts/autoscore_v1.md -->
<!-- 引用方: services/autoscore.py:AutoScoreService.evaluate() -->
<!-- 版本: v1 | 创建: 2026-03-16 -->
<!-- 变更时: 1.创建新版本文件 2.更新service引用 3.跑tests/regression/ -->
```

**Prompt 模板划分：**

| 位置 | 用途 | 调用方 |
|------|------|--------|
| 前端 `skills/templates/` | 用户技能 prompt（/命令触发） | Agent SDK 客户端 |
| 后端 `prompts/` | LLM 系统 prompt（评分/出题/提取） | 后端 Service |

### Development Workflow Integration

**开发模式启动：** `cd frontend && npm run tauri dev`（自动启动 Vite HMR + Tauri 窗口）。Docker 单独：`docker-compose up -d`

**构建发布：** `npm run tauri build` → 平台安装包（.msi/.dmg/.AppImage）~10MB | 后端 `docker build`

**更新：** tauri-plugin-updater 自动更新(桌面) + `docker-compose pull`(后端) + Alembic(SQL)+Cypher(Neo4j)

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility：** 7 组技术栈组合验证通过（Tauri+React+Vite / ReactFlow+Zustand / shadcn/ui+TailwindCSS+Catppuccin / FastAPI+LangGraph+LanceDB / Neo4j+Graphiti / Claude SDK+MCP+FastAPI-MCP / bge-m3+Ollama+LanceDB）。GDR 16-Agent 全域验证无矛盾。

**Pattern Consistency：** Python(snake_case) / TypeScript(camelCase/PascalCase) / Neo4j(PascalCase/UPPER_SNAKE) / MCP(snake_case) / CSS(cl-{group}-* + TailwindCSS utility) 6 域命名规范无冲突。

**Structure Alignment：** 每项 Critical Decision 有对应文件/目录，所有边界定义在目录结构中体现，Enforcement 规则可直接验证。

### Requirements Coverage Validation ✅

**FR 覆盖率：12/12 能力域 = 100%**（70+ FR 全部有架构支撑）

| # | 能力域 | FR 数 | 覆盖 | 关键组件 |
|---|--------|-------|------|---------|
| 1 | 知识图谱管理 | 7 | ✅ | canvas/* + Neo4j + IndexedDB |
| 2 | 节点AI对话 | 9 | ✅ | chat/* + SQLite + per-node session |
| 3 | Edge对话 | 4 | ✅ | EdgeDialog + ChatPanel(Edge) + Graphiti双写 |
| 4 | 检验白板 | 18 | ✅ | exam/* + autoscore + token_chain |
| 5 | 精通度追踪 | 6 | ✅ | mastery_engine(BKT+FSRS) + calibration |
| 6 | 检索与个性化 | 13 | ✅ | agentic_rag/* + indexing/* + graphiti/ |
| 7 | 命令技能系统 | 5 | ✅ | skills/* + skill_executor |
| 8 | 学习档案 | 5 | ✅ | profile/* + conversation_archive |
| 9 | 质量保证 | 7 | ✅ | middleware/* + audit/* + tests/regression/ |
| 10 | Dashboard | 4 | ✅ | dashboard/* |
| 11 | Agent集成与MCP | 6 | ✅ | mcp/* + agent-bridge + 6层防御 |
| 12 | 系统配置 | 7 | ✅ | settings.ts + SetupWizard + api/system |

**NFR 覆盖率：33/33 项 = 100%**（性能7 + 可靠性5 + 可观测性4 + 可维护性4 + 安全隐私7 + 兼容性11 → 全部有架构措施）

### Implementation Readiness Validation ✅

| 就绪维度 | 状态 |
|---------|------|
| 决策完整度 | ✅ 7 Critical + 7 Important 全确认，5 Deferred 标注 Phase 2+ |
| 目录结构 | ✅ 前端 50+ 文件 / 后端 60+ 文件逐一列出 |
| 命名规范 | ✅ 6 个域全覆盖 |
| 通信模式 | ✅ REST + WebSocket + MCP + EventBus 4 协议全规范 |
| 错误处理 | ✅ 5 层 + 4 种重试策略 |
| 数据流文档 | ✅ 5 条关键路径数据流图 |
| 结构防御 | ✅ 6 项防御规则（Red Team 验证） |
| 测试对应 | ✅ 7 条映射规则 |
| 跨组约束 | ✅ Edge同Agent同Story + 开发顺序 |
| 跨Store通信 | ✅ props向下/事件推送/禁直接引用 |

### Gap Analysis Results

| 级别 | 数量 | 说明 |
|------|------|------|
| Critical | **0** | 无阻塞实现的缺失 |
| Important | **1** | 缺少可视化架构图（Phase 2 补充，当前文字版不阻塞 Agent） |
| Nice-to-Have | **2** | Service 依赖矩阵 + Brownfield 迁移映射（属 Epic/Story 规划） |

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] 12 个 FR 能力域 70+ FR 全覆盖
- [x] 6 类 33 项 NFR 全覆盖
- [x] 10 项横切关注点全映射
- [x] 15 项技术约束全列出

**✅ Architectural Decisions**
- [x] 7 Critical + 7 Important 决策全确认
- [x] 15 项技术选型全指定版本
- [x] 6 层 Agent 防御全设计
- [x] 4 离线降级场景全方案

**✅ Implementation Patterns**
- [x] 6 域命名规范
- [x] 前后端目录结构逐文件
- [x] 4 种通信协议格式规范
- [x] 5 层错误处理 + 4 种重试策略

**✅ Project Structure（26 项改进）**
- [x] 完整目录树（前端 50+ / 后端 60+ 文件）
- [x] 10 API 边界 + 5 内部边界 + 5 数据隔离
- [x] 12 FR→文件映射 + 10 横切→文件映射
- [x] 6 项结构防御 + 7 条测试对应 + Prompt 规范
- [x] Agent 运行时位置 + API 类型同步策略
- [x] 复杂度合理性声明

### Architecture Readiness Assessment

**Overall Status: ✅ READY FOR IMPLEMENTATION**

**Confidence Level: HIGH**
- Party Mode 4 角色审查 + Advanced Elicitation 5 轮深度分析
- 前 session 20 个对抗审查 Agent + 12 个冲突解决
- 0 Critical Gap

**Key Strengths:**
1. 多 Agent 开发友好——竞品中唯一考虑此场景
2. 结构防御规则全面——6 类攻击向量均有防御
3. 数据流文档化——5 条关键路径可直接参考
4. 复杂度有据可查——每项可追溯到具体 FR

**Areas for Future Enhancement:**
1. 可视化架构图（Phase 2，Mermaid/Excalidraw）
2. Service 依赖矩阵（Story 规划时补充）
3. Brownfield 迁移映射（Epic 规划时产出）

### Implementation Handoff

**AI Agent Guidelines:**
- 严格遵循所有架构决策
- 使用 Implementation Patterns 中的命名和格式规范
- 尊重 Project Structure 中的目录边界和防御规则
- 所有架构问题参考本文档

**First Implementation Priority:**
1. Phase 0：Brownfield 修复（8 CRITICAL + 7 HIGH）
2. 前端基础：esbuild-svelte + CanvasView + IndexedDB + Dexie liveQuery
3. 核心对话：ChatPanel + per-node Session + Tool-UI Bridge + MCP
4. 算法激活：BKT/FSRS 管道 + EventBus + AutoSCORE
5. 检验白板：三种考察模式 + 递归 + 分类
6. 个人记忆：Graphiti 三通道 + 自定义 Schema
7. 精打磨：学习档案 + 校准 + 质量保证

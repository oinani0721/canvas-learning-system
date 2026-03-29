# Decision Log（本地索引 — Graphiti 双写保底）

> **每次 add_memory [Decision] 时，同步追加一行到此文件。**
> **新 session 启动时 Read 此文件获取所有历史决策。**
> **格式：日期 | 决策编号 | 标题 | 状态 | 简述**

---

## 已确认决策

| 日期 | 编号 | 标题 | 状态 | 简述 |
|------|------|------|------|------|
| 2026-03-15 | #11 | 四层搜索+A-RAG | ✅ 确认 | RAG+CLI+Graphiti+Grep 四层路由 + A-RAG 回源验证 + Reranker 升级 |
| 2026-03-15 | #1-15 | 15项PRD决策 | ✅ 全部确认 | 用户逐项增量确认，详见 memory/decision_15_incremental_confirmed.md |
| 2026-03-15 | Mode D | Mode D 架构 | ⚠️ 已被Agent SDK sidecar取代 | 原MCP暴露方案→经SDK→Tier B→最终Agent SDK sidecar(2026-03-19) |
| 2026-03-16 | DD-01~10 | 10条开发纪律 | ✅ 固化 | 学术实证/符合实际/禁mock/参考案例/Pencil/Obsidian/测试/Graphiti/增量提问/防蔓延 |
| 2026-03-16 | MVP刚需 | 14项+2底层 | ✅ 用户确认 | 见 memory/project_mvp_essentials.md |
| 2026-03-16 | Edge策略 | Edge对话2重策略 | ✅ 确认 | 用户改为2重（非PRD原版3重） |
| 2026-03-16 | RAG级别 | L1+L2都要 | ✅ 确认 | 智能路由+自动重检索 |
| 2026-03-16 | 安装引导 | 延后 | ✅ 确认 | 先写文档 |
| 2026-03-16 | 精通度通知 | 延后 | ✅ 确认 | 先能考就行 |
| 2026-03-16 | 冷启动诊断 | 删除 | ✅ 确认 | V-01：设计前提不成立 |
| 2026-03-16 | Hook强制读取 | session-start强制Read+Stop阻止未读 | Review PENDING | 验证session未分配 |
| 2026-03-16 | 规则精简 | 616行→140行 | ✅ 实施 | 官方建议<150行，合并3个rules为1个 |
| 2026-03-16 | 双写模式 | Graphiti+本地decision-log | ✅ 实施中 | 解决Graphiti搜索不到已记录决策的问题 |
| 2026-03-16 | Epic结构 | 7个Epic覆盖96FR | ⚠️ 已被更新 | E1画布→E2检索→E3对话→E4Edge→E5精通度→E6检验白板→E7质量（已被下条取代） |
| 2026-03-17 | Epic结构v2 | 6个Epic覆盖96FR | ✅ 用户确认 | E7(QA)分散到各Epic。E4保持独立。FR-SYS-01留E1低优先级。Party Mode多角色审视后决策 |
| 2026-03-18 | Code-Review | Story 1-3/1-10/2-1 审查 | ✅ 全部通过 | 1-10可复用(3M2L)；2-1可复用(2L)；1-3已修复4C5H2M(API Key持久化+Scoring降级+健康面板+Provider下拉+Neo4j+安全提示+错误脱敏) |
| 2026-03-18 | Code-Review | Story 1-8/2-2/1-11 审查 | ✅ 全部通过 | 1-8:安全修复后PASS(tauri-plugin-fs替代cmd/sh,7/7检查项)；2-2:PASS(Multimodal格式+去重+Graphiti写+Reranker+CRAG+改写,7/7)；1-11:PASS(None guard+健康监控+RAGAS NLI,7/7) |
| 2026-03-18 | Code-Review | Story 2-3/1-9/2-4/2-13 审查 | ⚠️ 1-9+2-13需修复 | 2-3:可复用(2M1L);1-9:需修复(3C3H—cross_subject死代码+ContextVar未接入+driver泄漏);2-4:需修复minor(3M2L);2-13:需修复(2C2H—模板内容被丢弃只用1行+回归测试仅replay无live)。1-9/2-13 CRITICAL已修复(commit e12f592) |
| 2026-03-18 | Code-Review | BMAD审查 Story 2-5/2-7 | ⚠️ 需修复 | 2-5:3H3M4L(requirements版本+fusion组映射+单例ignoreConfig+z-score单文档bias);2-7:3H4M2L(TOCTOU竞态+vault_path回退C8+零测试+全文件hash读) |
| 2026-03-18 | Code-Review | BMAD全量补审38个Story | ✅ 153问题已全部修复 | 14C54H62M23L全部修复。Docker E2E 12/12通过，模块导入15/15通过，Vite构建通过 |
| 2026-03-18 | Code-Review | 15新前端组件BMAD审查 | ✅ 0C2H4M7L=13问题(已修复) | ExamCanvas双击deselect(H)+exam-store unsafe cast(H)+HintButton hintLevel local(M)+SkillSelector亮色主题(M)+Dexie silent catch×5(M)+ExamCanvas节点未持久化(M)。全部修复，tsc通过 |
| 2026-03-18 | Code-Review | 后端17新文件MVP对照审查 | ✅ 0功能蔓延 | 15文件对应MVP#2-#13，2文件(llm_call_logger+prompt_injection_guard)为安全/可观测基础设施。DE-3修正为"技术栈保留+功能扩展" |
| 2026-03-16 | 对话引擎 | Spawn官方CLI+订阅额度 | ✅ 确认(Review PENDING) | Claude Agent SDK spawn官方Claude Code CLI，用户订阅额度。参考Claudian/Pencil/Zed ACP。Fallback: API Key |
| 2026-03-17 | DE-1 | Tauri+React+ReactFlow | ✅ 用户确认 | 独立桌面应用替代Obsidian插件。社区+学术双重验证(20+案例+20+论文) |
| 2026-03-17 | DE-2 | UI全量重写 | ✅ 用户确认 | shadcn/ui+TailwindCSS+Catppuccin Mocha。80+Svelte文件删除。附：未来提供浅色切换 |
| 2026-03-17 | DE-3 | 后端技术栈保留+功能扩展 | ✅ 用户确认(已修正) | 技术栈(FastAPI/Neo4j/LanceDB)保留。服务层按MVP需求扩展(+17文件/+5746行)。审计确认0功能蔓延:15文件对应MVP#2-#13，2文件为安全/可观测基础设施 |
| 2026-03-17 | DE-4 | Docker Shell管理 | ✅ 用户确认(Review PENDING) | Tauri Shell Plugin管理Docker Compose生命周期。需验证全路径+退出清理 |
| 2026-03-17 | DE-5 | CSP策略 | ✅ 用户确认(Review PENDING) | 开发阶段csp:null，上线前改为定向放行(localhost+Claude API) |
| 2026-03-17 | 工作流 | Pencil UI范式在架构之后编码之前 | ✅ 用户确认(Review PENDING) | Session1架构→Session2 Pencil换皮→确认后编码 |
| 2026-03-17 | GDR-P1-1 | 版本锁定 | ✅ 用户确认 | ReactFlow 12.10.1 + React≥19.2.4 + Vite pin 7.x |
| 2026-03-17 | GDR-P1-2 | Zustand状态管理 | ✅ 用户确认 | ReactFlow官方推荐+Spacedrive/Clash Verge验证。三层:useState/Zustand/TanStack Query |
| 2026-03-17 | GDR-P1-3 | Docker HTTP IPC备选 | ✅ 用户确认 | DE-4主方案不变,增加HTTP IPC备选缓解Windows Shell bug(#11513/#4949) |
| 2026-03-17 | GDR-P1-4 | IPC载荷硬约束 | ✅ 用户确认 | 单次IPC<100KB+delta更新。Windows IPC 10MB=200ms vs macOS 5ms |
| 2026-03-17 | OBS-LINK | Obsidian跳转方案 | ⏳ 待用户确认(Review PENDING) | obsidian://adv-uri(Advanced URI插件)+Tauri Opener。三级降级:adv-uri→内置URI→文件级。修正:不用内部预览,直接跳转Obsidian |
| 2026-03-19 | Agent SDK sidecar | 对话引擎切换至sidecar模式 | ✅ 确认(Review PENDING) | Node.js sidecar运行Agent SDK。取代Mode D→SDK→Tier B。架构:Tauri 2+React+Node.js sidecar。待验证:进程管理/MCP注入/Windows spawn稳定性 |
| 2026-03-24 | GDR-P0-1 | 事件传输方式 | ✅ 用户确认(Review PENDING) | sidecar解析stream-json→Tauri Channel→React。参考Solo IDE(同架构生产运行)。否决WebSocket直连 |
| 2026-03-24 | GDR-P0-2 | 工具调用UI状态机 | ✅ 用户确认(Review PENDING) | Claudian 4态:pending→running→completed/error/blocked。blocked=Claude Code permission require。对话框须具备Claudian一切能力+学习扩展 |
| 2026-03-24 | GDR-P0-3 | Observer触发机制 | ✅ 用户确认(Review PENDING) | PostToolUse hook主触发(替代prompt-based解决触发率低)。辅助:轮次结束+出错+用户说不懂。BEA 4维度提取。fire-and-track Outbox写入 |
| 2026-03-24 | GDR-P0-4 | 安全+SDK修复 | ✅ 用户确认 | graphiti-core>=0.28.2修复CVE-2026-32247 + Agent SDK effort:high修复默认medium bug |
| 2026-03-24 | GDA-假命名 | 假命名全量审计 | ⛔ 42处发现(12C+13H) | backend/app/零graphiti-core调用,30+函数名含"graphiti"全是Neo4j Cypher或JSON文件。3个死代码调不存在方法。根因:AI混淆写入Neo4j≠写入Graphiti |
| 2026-03-24 | GDR-记忆重构 | 策略C asyncio.Queue+Worker | ✅ 官方验证(queue_service.py同模式) | 官方MCP server用完全相同模式。6Phase迁移计划9-13h。待P0:Gemini额度+Embedding维度 |
| 2026-03-24 | Neo4j拓扑修正 | 7691保留学习数据专用 | ✅ 用户纠正 | 7689=开发记忆，7691=学生学习数据，不合并 |
| 2026-03-24 | Gemini全家桶 | LLM+Embedder+Reranker | ✅ 用户确认 | GeminiClient+GeminiEmbedder+GeminiRerankerClient。CLIProxyAPI降级为备选 |
| 2026-03-24 | GDR-CRITICAL | Gemini免费额度+Embedding维度 | ⛔ 待用户P0确认 | 免费10RPM=1episode/min,250RPD=18-35/day不够。text-embedding-004废弃需选维度。阻塞实施 |
| 2026-03-25 | S27-GDA-1 | Neo4j用7691 | ✅ 用户确认 | docker容器Neo4j(7691)才是正确的，7688旧实例不再使用 |
| 2026-03-25 | S27-GDA-2 | 取消教材+跨Canvas检索 | ✅ 用户确认 | RAG 6路→4路。教材映射TODO和跨Canvas关联TODO先不做 |
| 2026-03-25 | S27-GDA-3 | group_id按白板命名 | ✅ 用户确认 | 白板名=group_id（如CS188→cs188），前端白板命名+笔记路径选择决定检索范围 |
| 2026-03-25 | S27-GDA-4 | prompt禁止硬编码 | ✅ 用户确认 | 检验白板5层prompt必须外部文件+参考成熟案例+用户试用确认 |
| 2026-03-25 | S27-GDA-5 | CognitiveLoadTimer移除 | ✅ 用户确认 | 计时功能已抛弃，移除组件+ExamSummary总用时 |
| 2026-03-25 | S27-GDA-6 | Profile功能优先级 | ✅ 用户确认 | 跳转(最高)→疑惑节点(选文本创建)→考察记录/错误历史(延后) |
| 2026-03-25 | S27-GDA-7 | Dashboard LLM管理放Phase4 | ✅ 用户确认 | Settings已有基础，Phase4补充Dashboard可见的模型状态面板 |
| 2026-03-25 | S27-GDA-8 | 评分Bug Phase1修复 | ✅ 用户确认 | 前端scale mismatch(×2.5溢出)+后端1分变100分，Phase1立即修 |
| 2026-03-25 | S27-GDA-9 | 考察中/命令可用 | ✅ 用户确认 | 考察中允许/explain等命令，AI引导性思考但不暴露当前题目答案（Layer4规则） |
| 2026-03-25 | S27-GDA-10 | 疑问节点=正常对话 | ✅ 用户确认 | 检验白板中拉出的疑问节点进入正常对话模式（先学再考），下次考察时可被考察 |
| 2026-03-27 | S29-1 | bypassPermissions修复 | ✅ 用户确认 | permissionMode→default+canUseTool白名单。旧PreToolUse hook格式错误从未生效 |
| 2026-03-27 | S29-2 | PostToolUse BEA提取 | ✅ 用户确认 | SDK native PostToolUse hook+fire-and-forget后端提取。学术依据:Anderson&Krathwohl+Dialogue-KT |
| 2026-03-27 | S29-3 | 记忆注入Layer3验证 | ✅ 已验证 | Context Enrichment已接入Phase2三层搜索(chat-store→LearningContextService→search_memories) |
| 2026-03-27 | S29-4 | Windows进程管理 | ✅ 已验证 | Tauri Plugin Shell原生处理Windows进程关闭,无需taskkill |
| 2026-03-27 | S29-5 | 格式补全 | ✅ 用户确认 | record_learning_memory增加source_session_id/source_canvas_id |
| 2026-03-27 | S29-6 | Phase4改进 | ⏳ Phase4 | transactional outbox+reranking+mid-turn retrieval(25+论文验证) |
| 2026-03-29 | S35-Step3 | Hybrid语义路由 | ✅ 已实现(Review PENDING) | regex主路径+LLM(Gemini Flash)低置信度fallback。否决全替换/纯LLM。社区:Semantic Router+MathDial+MOOCPost |
| 2026-03-29 | S35-Step4 | Fusion Engine单例接入 | ✅ 已实现(Review PENDING) | set_mastery_engine()统一全局单例。修复3处独立MasteryEngine。5信号加权融合替代min(p,R)。G-PIPE管道打通 |

## 已完成验证（Decision-Review VALIDATED）

| 日期 | 标题 | 验证方式 | 结论 |
|------|------|---------|------|
| 2026-03-17 | DE-1~DE-5 前端重构 | GDR 16-Agent全域调研(10信源×3波) | ✅ VALIDATED 零阻塞风险。4项P1补充决策已确认 |
| 2026-03-17 | Pencil UI换皮(DD-05) | 16提示词→18帧覆盖68场景 | ✅ VALIDATED Tauri+React+ReactFlow+shadcn/ui风格全覆盖 |

## 待验证决策（Decision-Review PENDING）

| 日期 | 标题 | 需验证的维度 |
|------|------|------------|
| 2026-03-15 | ~~Mode D 架构~~ | ~~已被Agent SDK sidecar取代(2026-03-19)，Review关闭~~ |
| 2026-03-16 | Hook强制读取规则 | 新session是否实际Read文件并遵守规则 |
| 2026-03-16 | Epic结构 | Epic边界清晰、FR覆盖完整、依赖链正确、Story可独立交付 |
| 2026-03-16 | ~~对话引擎Spawn CLI~~ | ~~已被Agent SDK sidecar取代(2026-03-19)，验证维度转移至sidecar条目~~ |
| 2026-03-19 | Agent SDK sidecar | 进程管理可靠性/MCP tool injection方法/Windows spawn稳定性 |
| 2026-03-17 | ~~Pencil UI范式工作流~~ | ~~已VALIDATED(18帧覆盖68场景)，见已完成验证区~~ |
| 2026-03-17 | OBS-LINK Obsidian跳转 | Advanced URI插件安装率/Windows协议注册可靠性/Tauri openUrl延迟/降级链自动检测/Linux .desktop配置 |
| 2026-03-24 | GDR-P0-1~P0-3 | P0-1:Tauri Channel Windows长时间streaming稳定性；P0-2:blocked状态UX流畅度；P0-3:hook触发率100%验证+Outbox WAL可靠性+graphiti-core 0.28 API兼容性 |
| 2026-03-24 | GDA-假命名审计 | 42处假命名(12C13H)需修复+重命名+接入graphiti-core | 验证session需：(1)确认所有C级问题已修复 (2)验证重命名后命名准确性 (3)验证graphiti-core add_episode调用链打通 |

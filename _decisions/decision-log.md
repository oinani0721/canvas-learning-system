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
| 2026-03-16 | 对话引擎Spawn CLI | spawn模式长期稳定性(政策风险)、per-node session性能、stream-json实时性、MCP动态注入可靠性、Fallback切换成本 |
| 2026-03-17 | ~~Pencil UI范式工作流~~ | ~~已VALIDATED(18帧覆盖68场景)，见已完成验证区~~ |
| 2026-03-17 | OBS-LINK Obsidian跳转 | Advanced URI插件安装率/Windows协议注册可靠性/Tauri openUrl延迟/降级链自动检测/Linux .desktop配置 |

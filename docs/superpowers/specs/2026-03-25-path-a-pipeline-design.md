# Path A 设计文档：先打通管道再打磨体验

> **日期**: 2026-03-25 | **状态**: ✅ APPROVED — 对抗性审查通过（4 Agent，15 问题已归入 review-checklist.md）
> **依据**: GDA S27 审计（32 Agent）+ 10 项用户确认决策 + decision-log.md 全量决策
> **方法**: Boris Tane 模式 — 用户批注后再编码

---

## 设计目标

让 Canvas Learning System **真正跑起来能用**：
1. 产品能启动，基本功能可操作
2. 学习记忆真正写入 Graphiti（不再是假的）
3. 考察/对话/笔记检索的管道真正打通
4. 你能看到一个符合设计的产品界面

---

## Phase 1: 启动验证（预估 1-2 session）

### 1.1 环境修复

**修改 1: Neo4j 端口**（决策 S27-GDA-1）— `backend/.env`
```
NEO4J_URI=bolt://localhost:7691
```

**修改 2: .env.example 同步**
```
NEO4J_URI=bolt://localhost:7691
```

**修改 3: DE-5 CSP 配置**（决策 DE-5）— `frontend/src-tauri/tauri.conf.json`
- 开发阶段设 `csp: null`（允许 localhost + 外部 API 调用）
- 上线前改为定向放行（self + localhost + Claude API）

### 1.2 启动流程

```bash
# Step 1: Docker 服务
docker-compose up -d
# 等待 ~90s，3 个服务全部 healthy

# Step 2: Ollama 模型（首次需要）
docker exec canvas-learning-system-ollama ollama pull bge-m3

# Step 3: 后端健康检查
curl http://localhost:8001/api/v1/health

# Step 4: 前端
# 从项目根目录运行（非 frontend/）
npm install && npm run tauri dev
```

### 1.3 逐项验证清单

| MVP # | 验证操作 | 预期结果 | 如果失败 |
|-------|---------|---------|---------|
| #1 原白板 | 创建白板 → 添加 3 个节点 → 连线 | 节点/边在画布可见，刷新后仍在 | 检查 Dexie DB |
| #2 检验白板 | 选白板 → Generate Exam → 选模式 | ExamCanvas 打开，ChatPanel 显示 | 检查 exam-store |
| #2+ 检验白板Tips | 在考察对话中选中文本 → 打 Tip 标注 | InlineAnnotation 浮窗出现，Tips 保存成功 | 检查 ExamCanvas 是否加载 InlineAnnotation |
| #7 Dashboard | 切换到 Dashboard 视图 | 三个选项卡（白板/考试/复习）可见 | 检查 App.tsx view 路由 |
| #4 节点对话 | 右键节点 → Chat | ChatPanel 打开，能输入消息 | 检查 sidecar spawn |
| #13 /命令 | 在 ChatPanel 输入 `/` | SkillSelector 浮窗弹出 | 检查 /api/v1/skills |
| #14 拉出节点 | 在 ChatPanel 选中文本 | SelectionToolbar 出现 | 检查 usePullToNode |

**待调研**: Claudian 注册了哪些 /命令，我们要对标学习。

### 1.4 评分 Bug 立即修复（决策 S27-GDA-8）

**Bug 1: 前端分数溢出** — `ScoringCheckpointService.ts:578-580`
- 问题: 按旧 0-40 制乘 2.5，导致 85 分显示为 212 分
- 修复: 移除 ×2.5 逻辑，直接使用后端返回的 0-12 分制

**Bug 2: 后端分数误判** — `agent_service.py:3618-3619`
- 问题: ≤1.0 的分数被误认为比例乘以 100，1 分变 100 分
- 修复: 移除自动乘 100 逻辑，使用 AutoSCORE 4D 的 0-12 原始分

### 1.5 移除 CognitiveLoadTimer（决策 S27-GDA-5）

- 删除 `frontend/src/components/exam/CognitiveLoadTimer.tsx`
- 修改 `ExamCanvas.tsx` — 移除 import 和渲染
- 修改 `ExamSummary.tsx` — 移除总用时显示

---

## Phase 2: Graphiti 真实接入（预估 2-3 session，9-13h）

### 2.0 环境配置（15 min）

**修改 `backend/.env`**:
```bash
NEO4J_URI=bolt://localhost:7691
GOOGLE_API_KEY=<照搬 Claude Code 的 Gemini API Key>
```

**修改 `docker-compose.yml`**: 后端容器新增 `GOOGLE_API_KEY=${GOOGLE_API_KEY}`

**SDK 版本约束**（决策 GDR-P0-4）:
- `graphiti-core>=0.28.2`（修复 CVE-2026-32247 安全漏洞）
- Agent SDK `effort: 'high'`（修复默认 medium 导致的智能体行为降级）

### 2.1 删除死代码（30 min）

W3-1 审计发现 3 处调用不存在方法的死代码。Grep 定位 → 删除 → `ruff check` 确认。

### 2.2 构建 GraphitiEpisodeWorker（2-3h）

**新建**: `backend/app/services/episode_worker.py`

**核心设计**（参考 `_decisions/research-asyncio-queue-graphiti-worker.md`）:
- asyncio.Queue (maxsize=100)
- graphiti_core.Graphiti 初始化（GeminiClient + GeminiEmbedder + Neo4j 7691）
- _worker_loop(): 消费队列 → add_episode()（sequential await，不能并行）
- 失败重试: 指数退避 (1s/2s/4s) + dead-letter store
- 监控: queue_depth / episodes_processed / failure_rate
- Graceful shutdown

**group_id 策略**（决策 S27-GDA-3）: 白板名 → `board_name.lower().strip().replace(" ", "-")`

### 2.3 替换假 Bridge 层（3-4h，临界交换）

**Step A**: MemoryService 新增 `_enqueue_episode()` 适配器
**Step B**: 替换 3 处 `record_learning_event()` 调用
**Step C**: `record_knowledge_entity()` 添加 enqueue（13 个 caller 不改）
**Step D**: 删除旧代码（5 项：_write_to_graphiti_json 系列 + graphiti_bridge_service.py + ENABLE_GRAPHITI_JSON_DUAL_WRITE）
**Step E**: 验证（ruff + grep + POST 测试 + Worker metrics + Neo4j 数据完整性）

### 2.4 假命名清理（1-2h，可与 2.5 并行）

26 个主要假命名函数分 3 级修复：
- CRITICAL: 公开 API 端点重命名（health/graphiti → health/knowledge-graph 等）
- HIGH: 内部服务重命名
- MEDIUM: 配置/日志/docstring 更新

### 2.5 Layered Search 替换（2-3h，可与 2.4 并行）

`search_memories()` 从内存字符串匹配 → 三层分级检索：
1. Graphiti search（语义+时序）
2. Neo4j fulltext index（关键词精确匹配）
3. 内存缓存 _episodes（最近事件快速返回）

**性能目标**: search latency < 2s

### 2.6 强制注入记忆 — PostToolUse Hook（决策 GDR-P0-3）

每次 AI 调用工具后，系统自动提取学习事件写入 Graphiti。目标触发率 100%。

**Step A: sidecar postToolUse hook** — BEA 4 维度提取（信念误解/执行错误/类比问题/引导思路）
**Step B: 辅助触发** — 轮次结束 + 出错 + 用户说"不懂"
**Step C: Fire-and-Track Outbox** — 学习事件写入 Dexie sync_outbox → SyncEngine 可靠投递（支持离线暂存）

### 2.7 强制检索记忆 — Session 启动注入

每次打开节点对话时，自动从 Graphiti 加载该节点的学习记忆，注入到 AI 系统提示中。

- chat-store.switchNode(nodeId) → ContextEnrichmentService.enrich(nodeId) → search_memories(nodeId) → 注入 systemPrompt Layer 3
- 非阻塞加载（2s 超时降级），第一条消息发送前 systemPrompt 必须就绪

**待调研**: SDK systemPrompt 与 CLAUDE.md 持久化配置文件的关系。

### 2.8 搜索路由（决策 #11 四层搜索架构）

根据问题类型自动选择搜索方式：
- L1: RAG 语义搜索（理解含义）
- L2: Graphiti 时序搜索（学习轨迹）
- L3: 结构化搜索（位置/路径）
- L4: 关键词搜索（精确匹配）
- 不确定时 → 并行多层 → RRF 融合排序

**实施优先级**: Phase 2 完成后在 Phase 3 实现。初期"默认 L1，用户指定时切换"。

### 2.9 MCP 工具迁移影响（Graphiti 接入后需更新的 6 个工具）

| MCP 工具 | 改动内容 |
|---------|---------|
| `record_learning_memory` | 写入路径改为 Graphiti add_episode |
| `search_memories` | 从字符串匹配升级为三层分级检索 |
| `record_error` | 错误分类后写入 Graphiti |
| `search_notes` | Graphiti 通道从空壳变为真正工作 |
| `archive_conversation` | 对话存档写入 Graphiti |
| `generate_question` | ACP 上下文从 Graphiti 获取更丰富的学习历史 |

其余 9 个工具（query_mastery、score_answer、assemble_acp、request_hint、skip_question、record_calibration、create_exam_node 等）不受影响。

---

## Phase 3: 管道修复（预估 2-3 session）

### 3.1 Sidecar Windows 验证（MVP #4 + #12）

**验证步骤**: npm run tauri dev → 右键节点 Chat → 对话返回

**可能的 Windows 问题**: Node.js PATH / Vault 路径转义 / 进程关闭残留
**Fallback**: engine-fallback 自动切换到 API Key 模式

**事件传输架构**（决策 GDR-P0-1）: sidecar stream-json → Tauri Channel → React

**工具调用 UI 状态机**（决策 GDR-P0-2）: Claudian 4 态
- pending → running → completed/error/blocked
- blocked = 需要用户授权的工具调用（如 record_learning_memory）

**Windows IPC 约束**（决策 GDR-P1-4）: 单次 IPC < 100KB + delta 更新
**HTTP IPC 备选**（决策 GDR-P1-3）: Tauri Shell 不可靠时降级为 HTTP

### 3.2 笔记索引修复（MVP #10）

诊断"索引成功但返回空"的 3 个可能原因 + force_rebuild 修复。
按学科索引：修改 index_vault_notes 端点接受 subject 参数（决策 S27-GDA-3）。

**待调研**: Obsidian Advanced URI 能否精确跳转到段落/行级别。

### 3.3 检验白板 Prompt 文件（决策 S27-GDA-4）

5 层 prompt 必须外部文件（`backend/prompts/exam/layer*.md`），禁止硬编码。
DD-04 调研成熟案例 → 创建文件 → 用户试用确认。

**GDA2-7 发现**: layer1/2/4/5 文件实际已存在，layer3（ACP）需外部化。

### 3.4 点击跳转功能（决策 S27-GDA-6，最高优先级）

Profile 中点击 Tip/Error → 跳转到当时的对话/考试白板。
- 数据层: TipItem 新增 sourceSessionId / sourceCanvasId / sourceExamId
- 前端路由: 复用 App.tsx 已有的 setSelectedNodeId() + goToCanvas()

### 3.5 record_learning_memory 格式修复

- entity_type 保持 PascalCase（Misconception, ProblemTrap 等）
- metadata 增加 source_session_id, source_canvas_id 字段

### 3.6 补救策略消费（GDA2-3 发现）

错误被分类和映射了，但出题时没有使用补救策略。修复：
- QuestionGenerator ACP Layer 3 注入补救策略信息
- 出题 prompt 根据错误类型选择针对性题型（破题→同结构新题、推理谬误→找错题等）

### 3.7 RAG 管道精简（决策 S27-GDA-2）

移除 2 个 TODO 空通道（textbook_retriever + cross_canvas_retriever）。
保留 4 路: LanceDB + Vault Notes + Graphiti + Multimodal。

### 3.8 考察中的交互规则

**考察中 /命令可用**（决策 S27-GDA-9）: 允许 /explain 等命令，AI 引导思考但不暴露当前题目答案。在 Layer 4 规则中新增此条。

**疑问节点 = 正常对话**（决策 S27-GDA-10）: 检验白板中拉出的新节点进入正常对话模式（先学再考），下次考察时可被考察。

---

## Phase 4: UI 对齐 + 体验打磨（预估 1-2 session）

### 4.1 全局深色主题

DD-05 先用 Pencil 展示范式 → 用户确认 → 统一 Catppuccin Mocha 色板。

### 4.2 Dashboard LLM 模型管理（决策 S27-GDA-7）

基于 Settings 已有基础，在 Dashboard 增加模型状态可见面板：
- 当前 AI 模型（Gemini/Claude/Ollama）
- 连接状态（在线/离线）
- API Key 有效性
- Ollama 运行状态

### 4.3 对话上下文管理

- per-node session（sessionMap 在 localStorage）
- 前端对话历史完整展示（不压缩）
- Claude SDK 1M 上下文支持长对话
- 参考 Claudian session 管理方式
- 待调研: 上下文压缩策略、Session 持久化/命名

### 4.4 颜色管理

**已确认**: 节点颜色仅用于个人标记，不与后端联动。无需额外开发。

---

## 验收标准

### Phase 1 完成标志
- [ ] docker-compose ps 显示 3 个服务 healthy
- [ ] curl /api/v1/health 返回 200
- [ ] CSP 配置不阻塞前端加载
- [ ] Tauri 窗口打开无崩溃
- [ ] 能创建白板 + 添加节点 + 连线
- [ ] CognitiveLoadTimer 已移除
- [ ] 2 个评分 Bug 已修复（前端不溢出 + 后端不误判）
- [ ] 检验白板中能打 Tips

### Phase 2 完成标志
- [ ] graphiti-core >= 0.28.2 安装成功
- [ ] POST /memory/episodes → worker enqueue → graphiti add_episode 成功
- [ ] search_memories("极限定义") → 返回之前写入的 episode
- [ ] 假命名 grep "graphiti" → 所有引用名实一致
- [ ] Worker 监控端点返回 queue_depth=0
- [ ] PostToolUse hook 触发率验证
- [ ] 6 个 MCP 工具迁移后功能正常

### Phase 3 完成标志
- [ ] 节点右键 Chat → 对话返回（sidecar 或 API Key fallback）
- [ ] 工具调用 UI 显示 4 态状态（pending/running/completed/blocked）
- [ ] 笔记索引 → 搜索返回精确片段
- [ ] 检验白板出题 → 回答 → AutoSCORE 评分 → 精通度更新
- [ ] 出题消费补救策略（破题→同结构新题等）
- [ ] Profile 中点击 Tip → 跳转到对话/白板
- [ ] 5 层 prompt 文件存在且用户试用通过
- [ ] 考察中 /命令可用但不暴露答案

### Phase 4 完成标志
- [ ] 全局 Catppuccin Mocha 深色主题
- [ ] Dashboard 模型管理面板可见
- [ ] 无已抛弃功能残留
- [ ] 用户完整走一遍学习闭环无阻塞

---

## 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Gemini API rate limit (10 RPM) | Phase 2 add_episode 频率受限 | Worker 指数退避 + dead-letter |
| Sidecar Windows spawn 失败 | #4 节点对话不可用 | engine-fallback 降级到 API Key |
| 向量维度不匹配 | 笔记索引返回空 | force_rebuild=true 重建索引 |
| Prompt 质量不佳 | 检验白板出题体验差 | 用户试用→迭代调整 |
| graphiti-core 版本不兼容 | Phase 2 启动失败 | 降级模式（Neo4j 直写继续） |

---

## 待调研项（实施前完成）

| 项目 | Phase | 说明 |
|------|-------|------|
| Claudian /命令列表 | P1 | 对标学习命令注册 |
| Obsidian 精确段落跳转 | P3 | Advanced URI 行级别支持 |
| PostToolUse hook BEA 提取 | P2 | DD-04 参考成熟案例 |
| SDK systemPrompt vs CLAUDE.md | P2 | 持久化配置方案 |
| 上下文压缩策略 | P4 | Claudian 实现参考 |
| Session 持久化/命名 | P4 | /resume 命名机制 |

---

## 决策索引（S27 session 确认的 10 项）

| # | 决策 | 内容 |
|---|------|------|
| GDA-1 | Neo4j 用 7691 | Docker 容器，7688 弃用 |
| GDA-2 | 取消教材+跨Canvas | RAG 6路→4路 |
| GDA-3 | group_id 按白板名 | CS188→cs188 |
| GDA-4 | prompt 禁硬编码 | 外部文件+成熟案例+用户试用 |
| GDA-5 | 移除 CognitiveLoadTimer | 计时功能已抛弃 |
| GDA-6 | Profile 优先级 | 跳转最高→疑惑节点→记录/历史延后 |
| GDA-7 | LLM 管理放 Phase4 | Settings 基础上补 Dashboard 面板 |
| GDA-8 | 评分 Bug Phase1 修 | 前端×2.5溢出+后端1分变100分 |
| GDA-9 | 考察中/命令可用 | AI 引导思考不暴露答案 |
| GDA-10 | 疑问节点=正常对话 | 先学再考，下次可被考察 |

# S40 Session 工作进度报告

> 日期: 2026-04-03
> Session 目标: 项目清场 + 环境检查 + PRD-代码 Gap Analysis
> 后续动作: 7 个算法子系统 Deep Research（Claude Code Desktop 执行）

---

## 一、项目清场（已完成）

### 1.1 归档操作

| 操作 | 源 | 目标 | 状态 |
|------|---|------|------|
| 合并两个 archive | `.archive/agents/`（6 个 md） | `_archive/legacy-agents/` | ✅ |
| WSL2/Windows 文件 | `wsl2-*.sh` + `.bat` | `_archive/obsolete-platform/` | ✅ |
| 15 个 PowerShell 脚本 | `scripts/*.ps1` | `_archive/obsolete-platform/` | ✅ |
| 旧 Obsidian 代码 | `src/`（整个目录） | `_archive/obsolete-obsidian/src` | ✅ |
| 旧 Canvas 数据 | `Canvas/` | `_archive/obsolete-obsidian/Canvas` | ✅ |
| 旧 demo | `demo/` | `_archive/obsolete-obsidian/demo` | ✅ |
| 一次性报告 | `COMMAND-VALIDATION-REPORT.md` 等 | `_archive/one-off-reports/` | ✅ |
| 松散根目录文档 | `CHANGELOG.md`, `PROGRESS.md` | `docs/project-status/` | ✅ |
| 杂项归档 | `ralph-runner.sh`, `rollback_config.yaml`, `requirements-lancedb.txt` | `_archive/obsolete-platform/` | ✅ |
| 配置整理 | `mastery_config.json` | `config/` | ✅ |
| 设计文件 | `UI 相关设计样式.pen` | `docs/design/` | ✅ |

### 1.2 .gitignore 更新

追加了运行时数据忽略规则：`logs/`, `*.db`, `data/*.db`, `data/*.jsonl`, `data/lancedb/`, `images/generated*`

### 1.3 ⚠️ 清场副作用

**CRITICAL**: 归档 `src/` 导致两条 import 链断裂：
- `rag_service.py` → `src.agentic_rag`（LangGraph 管道）→ `LANGGRAPH_AVAILABLE=False` 静默降级
- `mastery_engine.py` → `src.memory.temporal.fsrs_manager`（FSRS）→ `FSRS_ENGINE_AVAILABLE=False` 指数衰减 fallback

系统不崩溃但 RAG 和 FSRS 处于降级状态。需要将相关模块迁移到 `backend/app/` 下。

---

## 二、环境检查（已完成）

| 项目 | 状态 | 详情 |
|------|------|------|
| repomix | ✅ v1.13.1 | 全局可用 |
| Python | ✅ 3.14.3 | venv 存在 |
| Node | ✅ v25.8.2 | |
| Docker | ✅ v29.3.1 | Compose v5.1.1 |
| backend .env | ✅ | `.env` + `.env.example` 都有 |
| 测试收集 | ⚠️ 293 测试 / 12 error | 12 个 error 全是引用已归档旧代码（bmad_orchestrator/src/chromadb），不可修复 |
| TypeScript | ✅ 0 错误 | `tsc --noEmit` 通过 |
| `uv run` | ❌ | hatchling build 失败（无 `[tool.hatch.build]` 配置） |

### 代码骨架文件（已生成）

| 文件 | Token 数 | 文件数 |
|------|---------|--------|
| `.repomix/backend-api.xml` | 93,275 | 57 |
| `.repomix/backend-services.xml` | 124,731 | 51 |
| `.repomix/backend-agents.xml` | 37,479 | 8 |
| `.repomix/backend-core.xml` | 15,727 | 18 |
| `.repomix/frontend-ui.xml` | 16,161 | 33 |
| `.repomix/frontend-state.xml` | 30,649 | 17 |
| **总计** | **318,022** | **184** |

---

## 三、Gap Analysis 核心结论

### 3.1 FR 覆盖统计（99 个功能需求）

| 分类 | 总数 | ✅ 完整 | ⚠️ 部分 | ❌ 未实现 |
|------|------|--------|--------|----------|
| FR-KG 知识图谱 | 9 | 8 | 1 | 0 |
| FR-CONV 节点对话 | 13 | 11 | 2 | 0 |
| FR-EDGE 连线对话 | 4 | 4 | 0 | 0 |
| FR-EXAM 检验白板 | 18 | 18 | 0 | 0 |
| FR-MAST 精通度 | 6 | 4 | 2 | 0 |
| FR-RET 检索管道 | 13 | 1 | 6 | 6 |
| FR-SKILL Agent 技能 | 5 | 2 | 3 | 0 |
| FR-TRACE 学习轨迹 | 5 | 4 | 1 | 0 |
| FR-QA 质量保证 | 7 | 6 | 1 | 0 |
| FR-DASH Dashboard | 4 | 4 | 0 | 0 |
| FR-MCP 协议 | 3 | 3 | 0 | 0 |
| FR-AGENT 系统 | 3 | 0 | 3 | 0 |
| FR-SYS 系统配置 | 9 | 5 | 1 | 3 |
| **总计** | **99** | **70 (70.7%)** | **20 (20.2%)** | **9 (9.1%)** |

### 3.2 技术框架验证（12 项）

| # | 技术框架 | 匹配度 | 关键问题 |
|---|---------|--------|---------|
| 1 | BKT 贝叶斯知识追踪 | ✅ 100% | 公式正确，Deep Research 有更新推荐 |
| 2 | FSRS-6 间隔重复 | ⚠️ 70% | import 断裂→指数衰减 fallback |
| 3 | AutoSCORE 两阶段 | ✅ 100% | 未经实测验证 |
| 4 | Area9 2x2 校准 | ✅ 100% | 未经实测验证 |
| 5 | Chain-of-Hints 4 级 | ✅ 100% | 未经实测验证 |
| 6 | 交叉编码器 Reranker | ⚠️ 60% | gte-reranker 中文不匹配，推荐 Qwen3-Reranker |
| 7 | bge-m3 Embedding | ✅ 95% | Ollama 配置正确 |
| 8 | jieba 中文分词 | ❌ 0% | 完全未实现 |
| 9 | RRF 融合排序 | ⚠️ 40% | 仅在文档/归档中，生产代码无 |
| 10 | LangGraph StateGraph | ⚠️ 70% | import 断裂 |
| 11 | ACP 数据包 | ✅ 100% | 3K token 硬编码，1M context 为何只用 3K？ |
| 12 | SOLO 4 维 Rubric | ✅ 100% | 未经实测验证 |

### 3.3 用户前端测试发现

**几乎所有标记 ✅ 的功能，用户在前端测试中都没有看到。**

**根因分析（3 个运行时条件未满足）：**
1. 需要 `npm run tauri dev` 启动 Tauri 桌面应用（非 vanilla Vite server）
2. Claude Engine Sidecar 进程需要 Tauri 运行时才能启动（LLM 对话走 Sidecar，非后端）
3. 后端需要运行在 port 8001（前端硬编码 `localhost:8001`）

**前端-后端接线审计结论：** 所有 7 个核心功能（ChatPanel、EdgeGuideTooltip、ExamCanvas、LearningProfile、SkillSelector、Tips、Settings）的组件挂载、API 调用、端点注册**全部正确接通**，不是代码问题而是运行环境问题。

### 3.4 孤儿代码检测

- 扫描 59 个 backend service + 31 个 endpoint = 90 个文件
- **0 个疑似孤儿**（62 个 FR 对应 + 19 基础设施 + 9 工具函数）

---

## 四、个人记忆系统算法流程（已探明）

### 4.1 写入路径（双写架构）

```
record_learning_event(user_id, node_id, concept, score)
  │
  ├─→ Neo4j Cypher 同步写入（PRIMARY）
  │   └─ LEARNS(user → concept) + score/timestamp/group_id
  │
  ├─→ 内存缓存写入（max 10K episodes）
  │
  └─→ Graphiti 异步队列（SECONDARY）
      └─ GraphitiEpisodeWorker → graphiti_core.add_episode()
```

### 4.2 读取路径（三层搜索）

```
search_memories(query, group_id, limit)
  │
  ├─→ Tier 1: Graphiti 语义搜索（真实 graphiti-core search_()）
  │   └─ 返回 reranker 分数 0-1，超时 3s fallback 空列表
  │
  ├─→ Tier 2: Neo4j fulltext 索引（Lucene 关键词）
  │   └─ 分数归一化到 0-1
  │
  ├─→ Tier 3: 内存缓存子串匹配（固定 0.1 基线分）
  │
  ├─→ 去重 → 统一评分 → FSRS R-value 加权 → 排序
  └─→ 返回 top K
```

### 4.3 两套 RAG 系统（已分离）

| 系统 | 搜索对象 | 实现 | 入口 |
|------|---------|------|------|
| 个人记忆 RAG | Tips/错误/Edge理由/对话历史/精通度 | memory_service.search_memories() | LangGraph retrieve_graphiti 节点 |
| 笔记文件 RAG | 用户笔记文件夹中的文档 | lancedb_index_service.search() | LangGraph retrieve_lancedb 节点 |

两者通过 `rag_service.py` 协调，在 LangGraph StateGraph 中作为独立节点并行执行，fusion 节点合并结果。

### 4.4 硬编码 vs 智能化

| 组件 | 类型 | 机制 |
|------|------|------|
| 错误分类 | LLM 驱动 | LiteLLM → 4 类分类（LLM 不可用时 fallback 关键词） |
| 对话蒸馏 | LLM 驱动 | LiteLLM 结构化提取 Tips/errors/QA |
| 节点选择 | **硬编码** | `0.4*(1-p_mastery) + 0.3*(1-R) + 0.3*kg_relevance` |
| 5 信号融合 | **硬编码** | 加权平均 `Σ(w_norm * value)` |
| 上下文组装 | **硬编码** | 确定性 fetch Tier1+Tier2+Tier3 |
| 搜索路由 | **硬编码** | 4 通道全部执行，无 Adaptive Router |
| 搜索 Tier 1 | 智能 | Graphiti 语义向量搜索 |

---

## 五、Deep Research 报告已有的技术更新推荐

| 领域 | 当前实现 | Deep Research 推荐 | 报告位置 |
|------|---------|-------------------|---------|
| Reranker | gte-reranker-modernbert-base（英语为主） | **Qwen3-Reranker-0.6B**（100+ 语言原生中文） | `docs/deep-research/01-*/b1-design-review` |
| 搜索路由 | 静态 4 通道全执行 | **Adaptive Router L1**（按查询意图选通道） | `docs/deep-research/01-*/b1-design-review` |
| 信号融合 | 加权平均 MVP | **Beta-Bayesian 融合**（Phase 2 保留） | `docs/deep-research/01-*/b2-signal-fusion` |
| 上下文压缩 | 基础 ACP 截断（3K token） | **句子级提取 + 原子块保护 + 多查询改写** | `_bmad-output/implementation-artifacts/2-10-*` |
| CRAG 延迟 | ~150ms 开销 | **用 Reranker 置信度分数兼作质量门控** | `docs/deep-research/01-*/b1-design-review` |
| 评估框架 | 路由准确率 benchmark | **RAGAS + A/B 测试基础设施** | 未找到现有实现 |

---

## 六、用户决策（2026-04-03）

1. **最高优先级：理清算法设计** — 所有代码修改之前，先 Deep Research 验证 7 个算法子系统
2. **对话 AI 方向：复用 Claude Code 泄漏前端** — 社区已有类似项目，直接接模型获得原生能力
3. **硬件资源：M5 Max + 128GB RAM** — 可跑本地模型，解决 Gemini 额度问题
4. **量化迭代：引入 Auto Research / A/B 测试** — 当前无评估基础设施

---

## 七、待 Deep Research 的 7 个算法子系统

| # | 子系统 | 核心问题 | 相关代码 | 相关 Deep Research |
|---|--------|---------|---------|-------------------|
| 1 | 个人记忆系统 | Graphiti 三层搜索是否合理？42 处假命名影响？ | `memory_service.py`, `episode_worker.py` | `01-*/b3-graphiti-history` |
| 2 | 5 信号融合 | 固定权重可靠吗？Beta-Bayesian 何时升级？ | `mastery_fusion.py`, `signal_registry.py` | `01-*/b2-signal-fusion` |
| 3 | 笔记 RAG 管道 | 4 通道过度工程？Adaptive Router？Reranker 选型？ | `rag_service.py`, `_archive/obsolete-obsidian/src/agentic_rag/` | `01-*/b1-design-review`, `02-*/b1-retrieval-pipeline` |
| 4 | BKT + FSRS | Deep Research 推荐的替代方案？FSRS import 修复？ | `mastery_engine.py` | `01-*/b2-signal-fusion` |
| 5 | AutoSCORE 评分 | 两阶段+SOLO 可靠性？3x 投票成本？ | `autoscore.py`, `stage2_rubric.md` | `01-*/b4-exam-system` |
| 6 | 上下文压缩 | Claude Code 泄漏算法学习？Story 2.10 设计验证？ | `question_generator.py`, `2-10-context-compression-*.md` | `01-*/b5-conversation-langgraph` |
| 7 | ACP 出题数据包 | 3K token 为何这么小？5 要素组装逻辑？ | `question_generator.py:196-247` | `01-*/b4-exam-system` |

### 每个子系统的骨架文件可从 `.repomix/` 目录获取

---

## 八、产出文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| Gap Analysis | `docs/project-status/gap-analysis.md` | 99 FR 完整状态表（含用户批注） |
| Orphan Code | `docs/project-status/orphan-code.md` | 90 个文件分类 |
| 本报告 | `docs/project-status/s40-progress-report.md` | 完整工作进度 |
| 代码骨架 | `.repomix/backend-*.xml`, `.repomix/frontend-*.xml` | 6 个模块骨架（共 318K tokens） |

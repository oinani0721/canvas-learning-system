# 决策演化时间线（GDA W3-3）

> **生成日期**: 2026-03-26 | **数据来源**: decision-log.md + ADR-001 + memory/*.md + _decisions/*.md
> **方法**: 按日期排序所有决策，识别 supersede 关系链

---

## 一、对话引擎演化链

```
Spawn CLI (03-15) → Mode D (03-15) → SDK直接嵌入(否决) → Tier B增强CLI(否决) → Agent SDK sidecar (03-19) [当前活跃]
```

### 2026-03-15 — Spawn 官方 Claude Code CLI（初始方案）
- **决策**: 方案B — spawn 官方 claude binary，用户订阅额度免费
- **理由**: 成本为零（继承Max/Pro订阅）、社区验证（Claudian/Pencil/Zed/opencode-proxy）
- **否决**: API Key（额外付费）、ACP（MVP过度复杂）、直接OAuth（违反ToS）
- **文件**: `_decisions/ADR-001-dialogue-engine.md`
- **状态**: 核心决策（订阅额度）仍有效，实现路径已演进

### 2026-03-15 — Mode D MCP Server 暴露（架构升级）
- **决策**: FastAPI 后端不变，新增 MCP 接口。Agent是"对话路由器"，后端是"算法执行器"
- **理由**: 5/13算法Agent会搞坏（FSRS/BKT等），行业共识"LLM增强不替代后端"
- **否决**: Mode A（完全替代，确定性算法不能Agent化）、Mode B（兜底叠加，双重复杂度）、Mode C（混合拆分，边界维护成本高）
- **子决策**: Tool-UI Bridge对话框 + LiteLLM SDK + Ollama bge-m3 + 6层Agent防御 + 上下文压缩不影响学习记忆
- **文件**: memory/decision_mode_d_architecture.md, memory/research_agent_cli_integration.md
- **状态**: ⚠️ **已被 Agent SDK sidecar 取代**（2026-03-19）

### 2026-03-17 — SDK 直接嵌入尝试（中间过渡，被否决）
- **问题**: Tauri WebView 不支持 Node.js，SDK 无法直接嵌入
- **记录**: ADR-001 行54 注释："SDK直接嵌入（Tauri WebView不支持Node.js）"
- **状态**: **立即否决**，未形成正式决策

### 2026-03-17~18 — Tier B 增强 CLI（中间过渡，被否决）
- **问题**: CLI hanging + Tauri spawn bug（Issues #11513/#4949）
- **记录**: ADR-001 行54 注释："Tier B增强CLI（CLI hanging + Tauri spawn bug）"
- **状态**: **否决**，促成 sidecar 方案

### 2026-03-19 — Agent SDK sidecar（当前活跃方案）
- **决策**: Node.js sidecar 运行 @anthropic-ai/claude-agent-sdk 0.2.74
- **架构**: Tauri 2 桌面壳 + React 前端 + Node.js sidecar（独立进程，NDJSON IPC）
- **理由**: 绕过 Tauri WebView 不支持 Node.js 限制，绕过 CLI hanging/spawn bug
- **文件**: decision-log.md 行47, ADR-001 行52-55
- **验证状态**: [Decision-Review] PENDING — 进程管理/MCP注入/Windows spawn稳定性
- **Windows可用性**: ~70-75%（路径转义+上下文压缩风险）

### 2026-03-24 — sidecar 细化决策
- **GDR-P0-1**: sidecar解析stream-json → Tauri Channel → React（参考Solo IDE）
- **GDR-P0-2**: Claudian 4态状态机 pending→running→completed/error/blocked
- **GDR-P0-3**: PostToolUse hook主触发 + fire-and-track Outbox
- **GDR-P0-4**: graphiti-core>=0.28.2 CVE修复 + Agent SDK effort:high
- **文件**: decision-log.md 行48-51

### 演化原因总结

| 阶段 | 方案 | 失败/演进原因 |
|------|------|-------------|
| Spawn CLI | 直接spawn claude binary | 核心思路保留，但宿主从Obsidian→Tauri |
| Mode D | MCP Server暴露 | 架构层面保留（Agent路由+后端执行），实现路径变化 |
| SDK直接嵌入 | Agent SDK in WebView | Tauri WebView不支持Node.js |
| Tier B增强CLI | 增强CLI spawn | CLI hanging + Tauri spawn bug (#11513/#4949) |
| **Agent SDK sidecar** | Node.js独立进程 | **当前活跃** — 绕过所有限制 |

---

## 二、记忆系统演化链

```
JSON fallback (初始) → 双写模式 (03-16) → asyncio.Queue Worker 调研 (03-24) → 真实 Graphiti 接入 (03-26) [当前活跃]
```

### 初始状态 — JSON fallback + Neo4j Cypher（历史债务）
- **实际情况**: MemoryService 使用 Neo4j Cypher 直写 + JSON 文件双写 + 内存缓存
- **关键问题**: graphiti-core **零 import、零调用**。42+处函数名含"graphiti"但实际是Neo4j/JSON
- **发现时间**: 2026-03-24 GDA假命名审计（12C+13H级别问题）
- **根因**: AI混淆"写入Neo4j" ≠ "写入Graphiti"，函数名欺骗后续session

### 2026-03-16 — 双写模式决策
- **决策**: Graphiti + 本地decision-log.md 双写
- **理由**: 解决Graphiti搜索不到已记录决策的问题
- **文件**: decision-log.md 行25
- **注**: 这里的"双写"是开发记忆层面（Graphiti MCP + 本地文件），非代码层面

### 2026-03-24 — 假命名全量审计（转折点）
- **发现**: backend/app/ 零 graphiti-core 调用，30+ 函数名含"graphiti"全是 Neo4j Cypher 或 JSON
- **发现3个死代码**: 调用不存在的方法
- **根因**: AI混淆写入Neo4j ≠ 写入Graphiti，审查Agent看函数名就信了
- **文件**: decision-log.md 行52, memory/project_s25_context_cleanup.md
- **影响**: 触发 DD-13（名实一致）和 Certificate-Based Review 规则

### 2026-03-24 — asyncio.Queue + Worker 调研（策略C）
- **决策**: 策略C asyncio.Queue + 单Worker顺序消费
- **验证**: graphiti-core 官方MCP server (queue_service.py) 用完全相同模式
- **关键约束**: add_episode 必须 sequential await（官方docstring明确要求）
- **否决**: FastAPI BackgroundTasks（无顺序保证，不兼容graphiti）
- **文件**: `_decisions/research-asyncio-queue-graphiti-worker.md`
- **关联决策**: Gemini全家桶（GeminiClient+GeminiEmbedder+GeminiRerankerClient）、Neo4j 7691

### 2026-03-24 — 6Phase 迁移计划
- **文件**: `_decisions/migration-plan-graphiti-real-integration.md`
- **路径**: Phase 0环境 → Phase 1死代码 → Phase 2 Worker → Phase 3 Bridge替换 → Phase 4假命名 → Phase 5搜索
- **预估**: 9-13小时
- **阻塞**: 曾被 Gemini 免费额度阻塞（10RPM/250RPD），后用户说"照搬Claude Code配置"解除

### 2026-03-26 — 真实 Graphiti 接入完成（Phase 2 执行）
- **完成**: 12 Task + 6修复，10 commits
- **核心文件**: `backend/app/services/episode_worker.py`（436行，GraphitiEpisodeWorker）
- **删除**: 旧 Bridge/JSON 代码 -776行、graphiti_bridge_service.py 整文件删除
- **验证**: Worker启动成功，管道打通（对话→distiller→enqueue→Worker→add_episode）
- **遗留问题**: Gemini 免费10RPM速率限制触发死信（3次重试后）、Neo4j fulltext索引名不匹配
- **文件**: memory/project_s28_phase2_plan.md

### 演化原因总结

| 阶段 | 方案 | 失败/演进原因 |
|------|------|-------------|
| JSON fallback | JSON文件 + Neo4j Cypher | 假"Graphiti"，实际零graphiti-core调用 |
| 双写模式 | Graphiti MCP + 本地文件 | 开发记忆层面的双写，代码层面未变 |
| 假命名审计 | 发现42处假命名 | 触发重构决策 |
| asyncio.Queue Worker | 官方验证的模式 | 策略选型完成 |
| **真实Graphiti** | episode_worker.py + graphiti-core | **当前活跃** — Phase 2完成，速率限制待解 |

---

## 三、前端演化链

```
Obsidian Plugin + Svelte (初始) → Tauri+React+ReactFlow (03-17 DE-1) → UI全量重写 (03-17 DE-2) → Pencil设计验证 (03-17) [当前活跃]
```

### 初始状态 — Obsidian Plugin + Svelte
- **架构**: Obsidian 插件，Svelte UI，Plugin API
- **文件**: canvas-progress-tracker/ + obsidian-canvas-learning/（310 files）
- **问题**: Svelte 80+ 文件、Obsidian API 依赖深、Plugin 生态限制
- **Legacy代码**: src/ 目录 98文件/72942行，其中~47500行死代码（api/全mock, command_handlers/Obsidian CLI, canvas_utils.py 34641行monolith）

### 2026-03-17 — DE-1: Tauri+React+ReactFlow（架构转型决策）
- **决策**: 独立桌面应用替代 Obsidian 插件
- **验证**: 社区+学术双重验证（20+案例+20+论文）
- **文件**: decision-log.md 行36
- **状态**: ✅ 用户确认

### 2026-03-17 — DE-2: UI全量重写
- **决策**: shadcn/ui + TailwindCSS + Catppuccin Mocha 深色主题
- **影响**: 80+ Svelte 文件删除
- **附注**: 未来提供浅色切换（用户发现当前仍是浅色UI，全局主题切换未完成）
- **文件**: decision-log.md 行37
- **状态**: ✅ 用户确认

### 2026-03-17 — DE-3: 后端技术栈保留+功能扩展
- **决策**: FastAPI/Neo4j/LanceDB 保留，服务层按MVP需求扩展（+17文件/+5746行）
- **审计**: 15文件对应MVP#2-#13，2文件为安全/可观测基础设施，0功能蔓延
- **文件**: decision-log.md 行38

### 2026-03-17 — DE-4: Docker Shell管理
- **决策**: Tauri Shell Plugin 管理 Docker Compose 生命周期
- **补充(GDR-P1-3)**: HTTP IPC 备选方案缓解 Windows Shell bug
- **文件**: decision-log.md 行39, 44

### 2026-03-17 — DE-5: CSP策略
- **决策**: 开发阶段 csp:null，上线前改为定向放行
- **文件**: decision-log.md 行40

### 2026-03-17 — 前端技术栈细化决策（GDR系列）
- **GDR-P1-1**: ReactFlow 12.10.1 + React>=19.2.4 + Vite pin 7.x
- **GDR-P1-2**: Zustand 状态管理（ReactFlow官方推荐 + Spacedrive/Clash Verge验证）
- **GDR-P1-4**: IPC载荷硬约束（单次<100KB + delta更新，Windows IPC 10MB=200ms）
- **文件**: decision-log.md 行42-45

### 2026-03-17 — Pencil UI设计验证
- **决策**: Pencil 先创建 UI 范式，确认后编码
- **验证**: 16提示词 → 18帧覆盖68场景（VALIDATED）
- **文件**: decision-log.md 行41, 73

### 2026-03-24 — 上下文污染清理
- **操作**: Legacy归档（canvas-progress-tracker/ + obsidian-canvas-learning/ → _archive/ 310 files）
- **清理**: 全局CLAUDE.md Obsidian引用→Tauri+React，3个重复rules删除
- **文件**: memory/project_s25_context_cleanup.md
- **当前前端规模**: 48文件/8829行, 30组件, 12 services

### 演化原因总结

| 阶段 | 方案 | 失败/演进原因 |
|------|------|-------------|
| Obsidian Plugin + Svelte | 插件内Svelte UI | Plugin生态限制、80+文件Svelte债务 |
| **Tauri+React+ReactFlow** | 独立桌面应用 | **当前活跃** — 社区+学术验证，全新技术栈 |

---

## 四、全局时间线（按日期排序）

### 2026-03-13
| 决策 | 内容 | 状态 |
|------|------|------|
| A3 四方向确认 | Scope范围+Frontmatter+Wiki-links+Cross-Canvas | ✅ 确认 |

### 2026-03-15
| 决策 | 内容 | 状态 | 被取代? |
|------|------|------|---------|
| Spawn CLI | spawn官方claude binary，订阅额度 | ✅ 核心保留 | 实现路径→sidecar |
| Mode D | MCP Server暴露，Agent路由+后端执行 | ⚠️ 架构保留 | 实现→sidecar |
| Tool-UI Bridge | 自建对话UI + Agent SDK驱动 | ✅ 架构保留 | Svelte→React |
| LiteLLM+Ollama | 统一LLM层+bge-m3嵌入 | ✅ 保留 | — |
| 6层Agent防御 | Layer0~5防御体系 | ✅ 保留 | — |
| #1-15 PRD决策 | 15项逐个增量确认 | ✅ 全部确认 | — |
| 四层搜索+A-RAG (#11) | RAG+CLI+Graphiti+Grep四层 | ✅ 确认 | RAG 6路→4路(03-25) |

### 2026-03-16
| 决策 | 内容 | 状态 | 被取代? |
|------|------|------|---------|
| DD-01~10 | 10条开发纪律 | ✅ 固化 | DD-11~13 追加 |
| MVP刚需 | 14项+2底层 | ✅ 确认 | — |
| Edge策略 | 2重（非PRD原版3重） | ✅ 确认 | — |
| 双写模式 | Graphiti+本地decision-log | ✅ 实施 | — |
| Epic结构 | 7个Epic覆盖96FR | ⚠️ 已更新 | →v2 (03-17) |
| Hook强制读取 | session-start强制Read | PENDING | — |

### 2026-03-17
| 决策 | 内容 | 状态 | 被取代? |
|------|------|------|---------|
| **DE-1** | Tauri+React+ReactFlow | ✅ 确认 | **替代Obsidian Plugin** |
| **DE-2** | UI全量重写(shadcn/ui+Catppuccin) | ✅ 确认 | **替代Svelte UI** |
| DE-3 | 后端技术栈保留+功能扩展 | ✅ 确认 | — |
| DE-4 | Docker Shell管理 | ✅ 确认 | — |
| DE-5 | CSP策略 | ✅ 确认 | — |
| Epic结构v2 | 6个Epic(E7分散) | ✅ 确认 | **取代v1** |
| GDR-P1-1~4 | 版本锁定/Zustand/HTTP备选/IPC约束 | ✅ 确认 | — |
| Pencil工作流 | 架构→Pencil→编码 | ✅ VALIDATED | — |
| OBS-LINK | Obsidian跳转方案 | ⏳ 待确认 | — |

### 2026-03-18
| 决策 | 内容 | 状态 |
|------|------|------|
| Code-Review 全量 | 38 Story BMAD审查，153问题全修复 | ✅ 通过 |
| 15前端组件审查 | 0C2H4M7L=13问题全修复 | ✅ 通过 |
| 后端MVP对照审查 | 17文件，0功能蔓延 | ✅ 通过 |

### 2026-03-19
| 决策 | 内容 | 状态 | 被取代? |
|------|------|------|---------|
| **Agent SDK sidecar** | Node.js sidecar运行Agent SDK | ✅ 确认 | **取代Mode D→SDK→Tier B** |

### 2026-03-24
| 决策 | 内容 | 状态 | 被取代? |
|------|------|------|---------|
| GDR-P0-1~4 | 事件传输/状态机/Observer/安全 | ✅ 确认 | — |
| **GDA-假命名** | 42处发现(12C+13H) | ⛔ 待修复 | — |
| **策略C asyncio.Queue** | Worker顺序消费模式 | ✅ 官方验证 | **取代JSON fallback** |
| Neo4j拓扑修正 | 7689=开发, 7691=学习 | ✅ 用户纠正 | — |
| Gemini全家桶 | LLM+Embedder+Reranker | ✅ 确认 | — |
| 上下文污染清理 | Legacy归档310文件 | ✅ 完成 | — |

### 2026-03-25
| 决策 | 内容 | 状态 |
|------|------|------|
| **路径A** | 先打通管道再打磨体验(4Phase) | ✅ 确认 |
| GDA-1~10 | 10项用户批注决策 | ✅ 全部确认 |

### 2026-03-26
| 决策 | 内容 | 状态 |
|------|------|------|
| **Phase 2完成** | Graphiti真实接入，12Task+10commits | ✅ 验证通过 |
| Phase 1完成 | 端口修复+Timer移除+评分Bug修复 | ✅ 4 commits |
| Gemini速率限制 | 免费10RPM触发死信 | ⛔ 待决策 |

---

## 五、Supersede 关系图

```
[03-15] Spawn CLI ──────────────────────────────────────────────────┐
    └──→ [03-15] Mode D MCP暴露 ──→ (架构层面保留)                 │
              └──→ [~03-17] SDK直接嵌入 ──→ (否决: WebView无Node.js)│
              └──→ [~03-17] Tier B增强CLI ──→ (否决: CLI hanging)   │
              └──→ [03-19] Agent SDK sidecar ◄──────────────────────┘
                        └──→ [03-24] GDR-P0-1~4 细化

[初始] JSON fallback + Neo4j Cypher (假"Graphiti")
    └──→ [03-16] 双写模式 (开发记忆层面)
    └──→ [03-24] 假命名审计暴露真相 (42处)
    └──→ [03-24] asyncio.Queue Worker调研
    └──→ [03-24] 6Phase迁移计划
    └──→ [03-26] Phase 2 真实Graphiti接入 ◄── 当前活跃

[初始] Obsidian Plugin + Svelte
    └──→ [03-17] DE-1 Tauri+React+ReactFlow ◄── 当前活跃
    └──→ [03-17] DE-2 UI全量重写 (shadcn/ui)
    └──→ [03-24] Legacy归档 (310 files → _archive/)

[03-16] Epic结构 v1 (7个Epic)
    └──→ [03-17] Epic结构 v2 (6个Epic, E7分散) ◄── 当前活跃

[03-15] 四层搜索+A-RAG (RAG 6路)
    └──→ [03-25] GDA-2 取消教材+跨Canvas (RAG 4路) ◄── 当前活跃
```

---

## 六、仍处于 PENDING 状态的关键待验证决策

| 日期 | 决策 | 待验证维度 | 阻塞项 |
|------|------|----------|--------|
| 03-19 | Agent SDK sidecar | Windows spawn稳定性/MCP注入/进程管理 | Phase 3 |
| 03-24 | GDR-P0-1~3 | Channel streaming/blocked UX/hook触发率 | Phase 3 |
| 03-24 | GDA-假命名 | 42处修复完整性+重命名准确性+调用链打通 | Phase 4 |
| 03-26 | Gemini速率限制 | 升级付费 vs 增大重试间隔 | **P0 阻塞** |
| 03-26 | Neo4j fulltext索引名 | episode_content_index → episode_content | 待修复 |

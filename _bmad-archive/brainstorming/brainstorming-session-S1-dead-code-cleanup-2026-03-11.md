---
stepsCompleted: [1, 2, 3, 'review']
inputDocuments: []
session_topic: 'S1 死代码清理 — 安全删除 ~5090 行死代码 + 修复 ghost tables + fake verified'
session_goals: '制定安全高效的清理策略，不破坏 S3/S4 依赖链，覆盖 9 个死模块 + 2 测试文件 + ghost tables + fake verified 标记'
selected_approach: 'ai-recommended'
techniques_used: ['Constraint Mapping', 'Reverse Brainstorming', 'First Principles Thinking']
ideas_generated: 28
technique_execution_complete: true
review_complete: true
review_date: '2026-03-13'
review_findings: '2 CRITICAL + 3 HIGH + 4 MEDIUM — 已整合入验收标准'
review_agents: ['社区/论文 Deep Explore', '对抗性代码审查', '执行计划风险审查']
facilitation_notes: '用户高度参与，主动发现 agent 调研结果不一致问题，推动了三重验证方法论的建立'
---

# Brainstorming Session Results

**Facilitator:** ROG
**Date:** 2026-03-11 ~ 2026-03-13
**Status:** 已完成 — 待执行

## Session Overview

**Topic:** S1 死代码清理 — 安全删除 ~5090 行死代码（9 个模块 + 2 测试文件），清理幽灵表引用，移除假 "Verified" 标记
**Goals:** 制定安全高效的清理策略，不破坏 S3/S4 依赖链，为后续 Sprint 扫清障碍
**Related Issues:** #5, 11, 12, 13, 14, 26
**依赖关系:** S3（Pipeline 后处理重建）和 S4（Config 统一 + StateGraph 整理）依赖 S1 完成

### Context Guidance

_Graphiti 历史上下文：fusion/ 模块 7 文件从未被 pipeline 导入；nodes.py 有独立内联实现导致所有模块成为死代码；routing engine 被识别为"解决错误的问题"；Quality Gate 已被确认为死代码_

### Session Setup

_用户选择 AI 推荐技巧方式，会话聚焦于从风险识别到安全行动方案的完整链路_

---

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** S1 死代码清理，聚焦安全删除策略和依赖链保护

**Recommended Techniques:**

- **Constraint Mapping（约束映射）：** 系统性识别所有真实 vs 虚假依赖、幽灵引用、S3/S4 依赖边界
- **Reverse Brainstorming（逆向脑暴）：** 故意问"如何让清理彻底失败"，暴露隐藏风险点并反转为防护措施
- **First Principles Thinking（第一性原理）：** 从"pipeline 实际需要什么"出发，重建最小化最安全的清理方案

**AI Rationale:** S1 是下游 S3/S4 的关键前置任务。核心挑战不是"删什么"（已明确），而是"删的顺序、边界和验证方式"。三个技巧形成"映射约束 → 发现风险 → 重建方案"的完整链路。

---

## Technique Execution Results

### Topic 1：死代码识别与三重验证

#### 问题背景

初始 deep explore agent 调研结果出现**严重不一致**——同一模块，一个 agent 说"死代码"，另一个说"有引用"。用户发现此问题后，推动建立了三重验证方法论。

**根因分析：** 第一轮 agent 将 docstring 中的文本提及（如 `agents.py` 文档字符串中出现 "fusion" 一词）误判为 Python import。

#### 三重验证方法论

| 验证层 | 工具 | 查什么 | 局限性 |
|--------|------|--------|--------|
| **Layer 1: Grep** | `grep -rn "from agentic_rag.XXX"` | 文本模式匹配 import 语句 | 无法区分 docstring vs 真实 import |
| **Layer 2: AST** | `python ast.parse()` 扫描 806 个 .py 文件 | 解析 Python 语法树，只提取真实 import 节点 | 无法发现动态 import |
| **Layer 3: LSP** | `pyright findReferences` | 类型系统级别的引用查找 | 必须定位到具体符号（不能 line=1 char=1） |

**社区/论文验证：**
- **Meta SCARF (ESEC/FSE 2023):** 工业级死代码消除框架，处理过 1 亿+ 行代码，核心方法：增强依赖图 + 正确删除顺序 + 每次变更附带证据
- **ICSE-NIER 2024 "Beyond a Joke":** 动态分派路径可导致静态分析假阴性，建议结合运行时验证
- **Google SWE Book Ch.15:** 删除后必须建立防回退机制

#### 确认的 9 个死模块

所有模块经三重验证（grep + AST + LSP）确认 **0 个生产代码引用**：

| 模块 | 行数 | 文件数 | 说明 |
|------|------|--------|------|
| `fusion/` | ~1670 | 7 | RRF/Weighted/Cascade 融合算法，nodes.py 有完整内联版 |
| `observability/` | ~930 | 4 | LangSmith 可观测性，从未集成 |
| `reranking.py` | ~800 | 1 | Local/Cohere/Hybrid 重排序器，nodes.py 有 stub 版 |
| `quality/` | ~500 | 3 | QualityChecker/QueryRewriter 类 |
| `parallel_retrieval.py` | ~270 | 1 | 并行检索编排 |
| `env_config.py` | ~280 | 1 | 环境配置管理 |
| `quality_nodes/` | ~250 | 3 | 质量控制 LangGraph 节点 |
| `traced_nodes.py` | ~250 | 1 | 可观测性追踪包装器（依赖 observability/） |
| `routing/` | ~140 | 2 | 质量路由器 |
| **合计** | **~5090** | **23** | |

#### 需同步删除的测试文件

| 文件 | 原因 |
|------|------|
| `src/tests/test_multimodal_rag.py` | imports from `fusion.rrf_fusion`, `fusion.unified_result` |
| `src/tests/agentic_rag/test_observability.py` | imports from `observability.*`, `traced_nodes` |

#### 为什么插件还能正常运行？

**关键发现：** 活跃管道 `state_graph.py` → `nodes.py` 只导入 4 个模块：`config`, `nodes`, `retrievers`, `state`。所有死模块都是"专业版"——被写出来但从未集成。`nodes.py` 内部有所有功能的内联实现：

- `fuse_results()` (line 288) — 内联 RRF/Weighted/Cascade 融合
- `route_after_quality_check()` (state_graph.py line 104) — 内联路由
- `rewrite_query()` (state_graph.py line 146) — 内联查询重写
- `_rerank_local()` / `_rerank_cohere()` (nodes.py line 683/696) — stub 重排序器

#### 关键 Bug 发现

**RRF 分数 vs 质量阈值不匹配：** nodes.py 中 RRF 融合最大分数 = 0.098，但质量检查阈值 = 0.7。结果：质量检查永远返回 "low" → 触发 3 轮无意义的重新检索（每次查询 18 次检索器调用）。此 bug 留给 S3 修复。

#### 误判修正

两个模块最初被误判为死代码，后经 LSP 精确验证排除：

| 模块 | 误判原因 | 实际状态 |
|------|---------|---------|
| `agent_graph.py` | grep 格式不匹配 | 活跃 — `agent_service.py:L2787` 导入 `get_agent_rag_graph` |
| `graphiti_temporal_client.py` | 假设在顶层目录 | 活跃 — `dependencies.py:L858` + `clients/__init__.py:L14` 导入 |

---

### Topic 2：Ghost Tables + Fake Verified 标记

#### Ghost Tables（幽灵表）

`lancedb_client.py:112` 定义 `DEFAULT_TABLES = ["canvas_explanations", "canvas_concepts", "canvas_nodes", "vault_notes"]`

其中 `canvas_explanations` 和 `canvas_concepts` **从未在生产中创建**，查询时静默返回空结果 `[]`。

**修复计划：**

| 位置 | 当前值 | 修改为 |
|------|--------|--------|
| `lancedb_client.py:112` | `["canvas_explanations", "canvas_concepts", "canvas_nodes", "vault_notes"]` | `["canvas_nodes", "vault_notes"]` |
| `lancedb_client.py:810` | `search()` default `table_name="canvas_explanations"` | `table_name="canvas_nodes"` |
| `agent_graph.py:179` | fallback `table_name="canvas_explanations"` | `table_name="canvas_nodes"` |
| `test_lancedb_client.py:91` | `assert DEFAULT_TABLES == ["canvas_explanations", "canvas_concepts"]` | 更新为实际值 |

**注意：** `canvas_utils.py` 中的 `canvas_concepts` 是 **Graphiti group_id**（不同系统），不受此修改影响。

#### Fake Verified 标记

| 文件 | 行号 | 当前标记 | 实际情况 | 修改为 |
|------|------|---------|---------|--------|
| `canvas.py` | L6 | `✅ Verified from Context7` | 整个文件使用 `MOCK_CANVAS` 硬编码字典 | `⚠️ MOCK implementation` |
| `memory.py` | L32 | `✅ Verified from Context7` | 全部 5 个端点是 stub（11 个 TODO，全返回空） | `⚠️ STUB` |

#### 社区/论文对标（对抗性审查补充）

对抗性审查 agent 发现 3 处遗漏并补充到计划中：

1. **测试文件遗漏** — 原计划未列出 `test_multimodal_rag.py` 和 `test_observability.py`
2. **Ghost table 修复不完整** — 原计划遗漏 `lancedb_client.py:810` 默认参数和 `agent_graph.py:179` 回退值
3. **文档引用** — 约 10 处文档中提到已删模块，需后续清理

---

### Topic 3：最终执行计划

#### 执行策略（4 次原子化提交 + 6 步验证管道）

**依据：** Meta SCARF 叶节点优先 + Google SWE Ch.15 防回退 + ICSE-NIER 2024 运行时验证

#### Commit 1：删除测试文件（~200 行）

```
删除：
  src/tests/test_multimodal_rag.py
  src/tests/agentic_rag/test_observability.py
```

**理由：** 先删测试文件，避免删模块后这些文件 ImportError 导致 pytest 全红。保持每步"绿灯"状态。

#### Commit 2：删除 9 个死模块（~5090 行）

```
删除：
  src/agentic_rag/quality/           (~500 行, 3 files)
  src/agentic_rag/quality_nodes/     (~250 行, 3 files)
  src/agentic_rag/routing/           (~140 行, 2 files)
  src/agentic_rag/fusion/            (~1670 行, 7 files)
  src/agentic_rag/observability/     (~930 行, 4 files)
  src/agentic_rag/reranking.py       (~800 行)
  src/agentic_rag/parallel_retrieval.py  (~270 行)
  src/agentic_rag/env_config.py      (~280 行)
  src/agentic_rag/traced_nodes.py    (~250 行)

修改：
  src/agentic_rag/__init__.py 文档注释（移除对已删模块的描述）
```

**理由：** SCARF 叶节点一次性删除 > 分批删除。所有 9 个模块均为叶节点（0 个活代码引用），一次删除减少中间状态出错风险。

**前置操作：** 将 `reranking.py` 归档至 `_bmad-output/archive/` 作为 S3 Pipeline 重建参考。

#### Commit 3：修补残留问题

```
修改 ghost tables：
  lancedb_client.py:112  DEFAULT_TABLES → ["canvas_nodes", "vault_notes"]
  lancedb_client.py:810  search() default → "canvas_nodes"
  agent_graph.py:179     fallback → "canvas_nodes"

修改 fake verified：
  canvas.py:6    → "⚠️ MOCK implementation"
  memory.py:32   → "⚠️ STUB"

修改测试断言：
  test_lancedb_client.py:91  → 更新 DEFAULT_TABLES 期望值
```

#### Commit 4：防回退机制

创建 `scripts/check_dead_imports.sh`：
- 检测已删模块的 import 是否被重新引入
- 可集成至 CI 或 pre-commit hook

#### 每次提交后的验证管道（6 步）

| Step | 命令 | 检测目标 |
|------|------|---------|
| 1 | `python -m compileall src/agentic_rag/ -q` | 字节码编译，捕获语法/导入错误 |
| 2 | `python -c "from agentic_rag import *"` | 导入烟雾测试 |
| 3 | `python -c "from agentic_rag.state_graph import build_rag_graph; build_rag_graph()"` | StateGraph 构建完整性 |
| 4 | `ruff check src/agentic_rag/` | Lint 检查 |
| 5 | `python -m vulture src/agentic_rag/ --min-confidence 80` | 新增死代码扫描 |
| 6 | `pytest src/tests/ -x --tb=short` | 测试套件 |

#### 风险矩阵

| 风险 | 概率 | 兜底方案 |
|------|------|---------|
| 动态 import 遗漏 | 极低 | Step 2-3 运行时验证捕获 |
| `__init__.py` 隐藏导出 | 已排除 | 已验证只导入 state/config/state_graph |
| 其他 session 同文件冲突 | 中等 | 执行前 git pull + session 协调 |
| S3 需要的代码被删 | 低 | reranking.py 已归档 + git history 可恢复 |

---

## S1 执行验收标准（Review Session 2026-03-13 产出）

> **用途**：S1 执行完成后，验收 agent 读取本节内容，逐项执行验证命令，产出通过/失败报告。
> **来源**：三方独立对抗性审查（社区/论文 deep explore + 代码审查 + 执行计划审查）
> **审查发现**：2 CRITICAL + 3 HIGH + 4 MEDIUM 缺陷，已整合入以下验收标准

### 三方审查关键修正（vs 原方案）

| # | 问题级别 | 原方案 | 修正为 | 原因 |
|---|---------|--------|--------|------|
| 1 | **CRITICAL** | 验证 Step 3: `build_rag_graph()` | `build_canvas_agentic_rag_graph()` | 函数名不存在，state_graph.py:205 实际导出名 |
| 2 | **CRITICAL** | 验证 Step 2: `from agentic_rag import *` | `assert AGENTIC_RAG_AVAILABLE` | `__init__.py:75-109` try/except 吞掉 ImportError，原命令永远返回成功 |
| 3 | HIGH | 只归档 reranking.py | 同时归档 fusion/ | S3 需要参考融合算法（RRF/Weighted/Cascade） |
| 4 | HIGH | 防回退用 shell 脚本 | ruff banned-api 规则 | 零维护成本，集成现有工具链，自动阻止 import 已删模块 |
| 5 | HIGH | 引用 "Beyond a Joke" 论文 | 删除或更正 | 该论文实际讲编译器 DCE bug，不是 Python 动态分派 |
| 6 | MEDIUM | 无 backend import 验证 | 新增 `from app.services.rag_service import RAGService` | rag_service.py:45 也 import agentic_rag |
| 7 | MEDIUM | Commit 3 范围 | 新增 review.py:66 + conftest.py:176 | 悬空注释 + mock 数据未同步 ghost table 修复 |

### A. 删除完整性验证

```
# A1: 9 个死模块已删除
验证命令:
  ls src/agentic_rag/fusion/ 2>&1          # 应返回 "No such file or directory"
  ls src/agentic_rag/observability/ 2>&1   # 应返回 "No such file or directory"
  ls src/agentic_rag/quality/ 2>&1         # 应返回 "No such file or directory"
  ls src/agentic_rag/quality_nodes/ 2>&1   # 应返回 "No such file or directory"
  ls src/agentic_rag/routing/ 2>&1         # 应返回 "No such file or directory"
  ls src/agentic_rag/reranking.py 2>&1     # 应返回 "No such file or directory"
  ls src/agentic_rag/parallel_retrieval.py 2>&1  # 应返回 "No such file or directory"
  ls src/agentic_rag/env_config.py 2>&1    # 应返回 "No such file or directory"
  ls src/agentic_rag/traced_nodes.py 2>&1  # 应返回 "No such file or directory"
通过条件: 全部返回 "No such file or directory"

# A2: 2 个测试文件已删除
# ⚠️ 待确认项：需与 S3 session 交叉确认后再定最终处理方式
# 当前三个候选方案：
#   方案A: 直接删除（原方案，git history 可恢复）
#   方案B: 归档到 _bmad-output/archive/ 后删除（S3 有明确参考路径）
#   方案C: 暂不删，加注释标记"依赖已删模块，待 S3 评估"
# 原因：这两个测试文件 import 了死模块（fusion/observability），
#       删除后 S3 重建 pipeline 时可能需要参考其测试逻辑和用例设计。
#       需等与其他 session 结合后确认最终操作。
验证命令:
  ls src/tests/test_multimodal_rag.py 2>&1
  ls src/tests/agentic_rag/test_observability.py 2>&1
通过条件: 取决于最终确认的方案（A/B→文件不存在，C→文件存在且有标记注释）

# A3: __init__.py 文档注释已清理
验证命令:
  grep -n "fusion\|observability\|reranking\|quality_nodes\|traced_nodes\|routing\|parallel_retrieval\|env_config" src/agentic_rag/__init__.py
通过条件: 无匹配（或仅匹配显式标注"已删除"的说明）

# A4: 归档文件存在
验证命令:
  ls _bmad-output/archive/reranking.py
  ls _bmad-output/archive/fusion/
通过条件: 两者都存在
```

### B. 残留修复验证

```
# B1: Ghost tables — DEFAULT_TABLES
验证命令:
  grep -n "DEFAULT_TABLES" src/agentic_rag/lancedb_client.py
通过条件: 值为 ["canvas_nodes", "vault_notes"]（不含 canvas_explanations/canvas_concepts）

# B2: search() 默认参数
验证命令:
  grep -n "def search" src/agentic_rag/lancedb_client.py | head -3
  # 然后读取该函数签名
通过条件: table_name 默认值为 "canvas_nodes"

# B3: agent_graph fallback
验证命令:
  grep -n "table_name" src/agentic_rag/agent_graph.py | grep -i "fallback\|default\|explanations"
通过条件: 无 "canvas_explanations" 引用

# B4-B5: Fake verified 标记
验证命令:
  head -10 src/api/routers/canvas.py
  head -35 src/api/routers/memory.py
通过条件: 不含 "✅ Verified"，改为 "⚠️ MOCK" / "⚠️ STUB"

# B6: 测试断言
验证命令:
  grep -n "DEFAULT_TABLES" src/tests/*lancedb* 2>/dev/null || grep -rn "DEFAULT_TABLES" src/tests/
通过条件: 断言匹配新值 ["canvas_nodes", "vault_notes"]

# B7: conftest mock 数据（审查新增）
验证命令:
  grep -n "canvas_explanations\|canvas_concepts" src/tests/agentic_rag/conftest.py
通过条件: 无匹配或已更新为实际表名

# B8: 悬空注释（审查新增）
验证命令:
  grep -n "env_config" backend/app/api/v1/endpoints/review.py
通过条件: 无引用 env_config.py 的注释
```

### C. 运行时验证管道（修正版）

```
# C1: 字节码编译
命令: python -m compileall src/agentic_rag/ -q
通过条件: 退出码 0

# C2: 导入验证（⚠️ 修正：原方案静默成功）
命令: python -c "from agentic_rag import AGENTIC_RAG_AVAILABLE; assert AGENTIC_RAG_AVAILABLE, 'Silent import failure'"
通过条件: 退出码 0

# C3: StateGraph 构建（⚠️ 修正：函数名）
命令: python -c "from agentic_rag.state_graph import build_canvas_agentic_rag_graph; build_canvas_agentic_rag_graph()"
通过条件: 退出码 0

# C4: Backend import（审查新增）
命令: cd backend && python -c "from app.services.rag_service import RAGService"
通过条件: 退出码 0

# C5: Lint
命令: ruff check src/agentic_rag/
通过条件: 无 error

# C6: 类型检查（审查新增）
命令: pyright src/agentic_rag/
通过条件: 无新增 error（对比删除前基线）

# C7: 死代码扫描
命令: python -m vulture src/agentic_rag/ --min-confidence 70
通过条件: 无新增死代码

# C8: 测试套件
命令: pytest src/tests/ -x --tb=short
通过条件: 全部通过
```

### D. 防回退机制验证

```
# D1: ruff banned-api 规则存在
验证命令:
  grep -A 20 "banned-api\|banned_api" pyproject.toml
通过条件: 9 个已删模块全部列入 banned-api 规则

# D2: 规则实际生效
验证命令:
  echo 'from agentic_rag.fusion import rrf_fusion' > /tmp/test_banned.py
  ruff check /tmp/test_banned.py
  rm /tmp/test_banned.py
通过条件: ruff 报错并提示已删除
```

### E. 完整性保护验证

```
# E1-E2: 活跃模块未被误删
命令:
  python -c "from agentic_rag.agent_graph import get_agent_rag_graph"
  python -c "from agentic_rag.clients.graphiti_temporal_client import GraphitiTemporalClient"
通过条件: 两者都退出码 0

# E3: 覆盖率无退化
命令: pytest src/tests/ --cov=src/agentic_rag --cov-report=term-missing -q
通过条件: 覆盖率 ≥ 删除前基线（执行 S1 前需先记录基线值）
```

### 验收流程指引

```
验收 agent 执行步骤:
1. 读取本文档 "S1 执行验收标准" 一节
2. 按 A → B → C → D → E 顺序逐项执行验证命令
3. 每项记录: ✅ PASS / ❌ FAIL + 实际输出
4. 汇总产出验收报告，记录 [Test] 到 Graphiti
5. 如有 FAIL 项，分析原因并建议修复方案
```

---

## Decisions Log

| # | 决策 | 理由 | Graphiti 状态 |
|---|------|------|--------------|
| D1 | 范围从 5 模块扩大到 9 模块 | SCARF 一次性清理更安全 | `[Decision]` recorded |
| D2 | 三重验证方法论（grep + AST + LSP） | 单一工具存在假阳/假阴性 | `[Decision]` recorded |
| D3 | reranking.py 归档后删除 | S3 需要参考但不直接复用（Pyright 9 diagnostics，deprecated patterns） | `[Decision]` recorded |
| D4 | Ghost tables 修复为 `["canvas_nodes", "vault_notes"]` | 这 2 个是实际创建的表 | `[Decision]` recorded |
| D5 | 4-commit 原子化策略 | SCARF 叶节点优先 + 每步可验证 | `[Decision-Review]` PENDING |

---

## Follow-up Items

| 项目 | 所属 Sprint | 优先级 | Review 修订 |
|------|------------|--------|------------|
| 修复 RRF 分数 vs 质量阈值 bug | S3 | 高 | — |
| 清理 ~10 处文档中对已删模块的引用 | S1（收尾） | 低 | — |
| 基于归档 reranking.py + fusion/ 重建管道 | S3 | 中 | ⚠️ fusion/ 也需归档 |
| 修复 nodes.py stub rerankers | S3 | 高 | — |
| ~~将 check_dead_imports.sh 集成到 CI~~ | ~~S4~~ | ~~低~~ | ❌ 替换为 ruff banned-api |
| 新增: ruff banned-api 防回退规则 | S1 | 高 | ✅ 审查新增 |
| 新增: review.py:66 悬空注释清理 | S1 | 中 | ✅ 审查新增 |
| 新增: conftest.py:176 mock 数据同步 | S1 | 中 | ✅ 审查新增 |

---

## Creative Facilitation Narrative

本次 brainstorming 历时 3 天（2026-03-11 ~ 03-13），经历了一次关键转折：用户在 Topic 1 中发现不同 agent 的调研结果存在矛盾（同一模块被不同 agent 判断为"死/活"），这直接推动了三重验证方法论的建立。

用户展现了优秀的质疑能力——不轻信单一信息源，要求用 LSP 进行严格验证。这一推动使得最终结果从"可能有误的 5 模块删除"升级为"经三重验证确认的 9 模块安全删除 + 2 模块误判修正"。

Session 还发现了一个隐藏的关键 bug（RRF 分数阈值不匹配），虽然不属于 S1 范围，但为 S3 提供了重要线索。

### Session Highlights

**User Creative Strengths:** 对分析结果保持批判性思维，不盲信 AI 输出
**AI Facilitation Approach:** 从单工具验证升级到三重交叉验证，增加对抗性审查 agent
**Breakthrough Moments:** 发现 agent 调研不一致 → 建立三重验证 → 范围从 5→9 模块
**Energy Flow:** 持续高参与度，每个 topic 都有实质性互动和方向确认

# Story 2.1: Phase 0 — 死代码清理与配置修复

Status: ready-for-dev

## Story

As a 开发者,
I want 归档 9 个未使用模块、修复 adapter.py L195 配置传递 bug、删除废弃 env_config.py、清理 cs188 硬编码（20+ 处）,
so that 代码库清爽，所有配置参数正确生效，支持多学科。

## Acceptance Criteria

1. **AC-1: 9 个死模块归档** — 9 个经三重验证（grep + AST + LSP）确认无生产引用的模块移至 `_bmad-output/archive/` 目录，不影响活跃管道 import
2. **AC-2: 测试文件处理** — 依赖已删模块的 2 个测试文件归档或删除，归档至 `_bmad-output/archive/` 作为 Story 2.2 参考
3. **AC-3: adapter.py L195 配置传递修复** — `agentic_rag_adapter.py:195` 修复 LangGraph Context 传递方式，使 10/10 个 `_safe_get_config` 调用获取到真实配置值而非硬编码默认值
4. **AC-4: env_config.py 删除** — 删除 `src/agentic_rag/env_config.py`（283 行死代码），确认零残留引用
5. **AC-5: cs188 硬编码清理** — 全部 20+ 处 `cs188`/`CS188` 硬编码替换为配置化 `subject` 参数（默认值仍可为 "cs188"，但来源为配置而非硬编码）
6. **AC-6: Ghost Tables 修复** — `lancedb_client.py` 的 `DEFAULT_TABLES` 移除从未创建的 `canvas_explanations` 和 `canvas_concepts`，修复默认搜索表名
7. **AC-7: 虚假标记修复** — `canvas.py` 和 `memory.py` 中标记为"已验证"但实际为占位/空实现的标记改为如实标注
8. **AC-8: __init__.py 文档清理** — `src/agentic_rag/__init__.py` 中对已删模块的描述移除或标注"已归档"
9. **AC-9: ruff check 通过** — 所有修改文件通过 `ruff check`，无新增 lint 错误
10. **AC-10: 活跃管道完整性** — `state_graph.py` 到 `nodes.py` 管道 import 链和 graph 编译不受影响

## Tasks / Subtasks

- [ ] Task 1: 归档 reranking.py 和 fusion/ 作为 Story 2.2 参考 (AC: #1, #2)
  - [ ] 1.1 创建 `_bmad-output/archive/` 目录（如不存在）
  - [ ] 1.2 复制 `src/agentic_rag/reranking.py` 到 `_bmad-output/archive/reranking.py`
  - [ ] 1.3 复制 `src/agentic_rag/fusion/` 到 `_bmad-output/archive/fusion/`
  - [ ] 1.4 复制 `src/tests/test_multimodal_rag.py` 到 `_bmad-output/archive/test_multimodal_rag.py`
  - [ ] 1.5 复制 `src/tests/agentic_rag/test_observability.py` 到 `_bmad-output/archive/test_observability.py`

- [ ] Task 2: 删除 9 个死模块（约 5090 行）(AC: #1)
  - [ ] 2.1 删除 `src/agentic_rag/fusion/` (约 1670 行, 7 files)
  - [ ] 2.2 删除 `src/agentic_rag/observability/` (约 930 行, 4 files)
  - [ ] 2.3 删除 `src/agentic_rag/reranking.py` (约 800 行)
  - [ ] 2.4 删除 `src/agentic_rag/quality/` (约 500 行, 3 files)
  - [ ] 2.5 删除 `src/agentic_rag/parallel_retrieval.py` (约 270 行)
  - [ ] 2.6 删除 `src/agentic_rag/env_config.py` (约 283 行) — 同时满足 AC-4
  - [ ] 2.7 删除 `src/agentic_rag/quality_nodes/` (约 250 行, 3 files)
  - [ ] 2.8 删除 `src/agentic_rag/traced_nodes.py` (约 250 行)
  - [ ] 2.9 删除 `src/agentic_rag/routing/` (约 140 行, 2 files)

- [ ] Task 3: 删除依赖已删模块的测试文件 (AC: #2)
  - [ ] 3.1 删除 `src/tests/test_multimodal_rag.py`（imports fusion.rrf_fusion, fusion.unified_result）
  - [ ] 3.2 删除 `src/tests/agentic_rag/test_observability.py`（imports observability.*）

- [ ] Task 4: 清理 __init__.py 文档注释 (AC: #8)
  - [ ] 4.1 编辑 `src/agentic_rag/__init__.py`，移除对已删模块（fusion/observability/reranking/quality_nodes/traced_nodes/routing/parallel_retrieval/env_config）的描述

- [ ] Task 5: 修复 Ghost Tables (AC: #6)
  - [ ] 5.1 `src/agentic_rag/clients/lancedb_client.py:112` — `DEFAULT_TABLES` 改为 `["canvas_nodes", "vault_notes"]`（移除从未创建的两个表名）
  - [ ] 5.2 `src/agentic_rag/clients/lancedb_client.py:810` — `search()` 默认 table_name 改为 `"canvas_nodes"`
  - [ ] 5.3 `src/agentic_rag/agent_graph.py:179` — fallback table_name 改为 `"canvas_nodes"`
  - [ ] 5.4 更新 `src/tests/agentic_rag/test_lancedb_client.py:91` — DEFAULT_TABLES 断言值同步更新

- [ ] Task 6: 修复虚假标记 (AC: #7)
  - [ ] 6.1 `backend/app/api/v1/endpoints/canvas.py:6` — 修改标记为如实描述当前实现状态
  - [ ] 6.2 `backend/app/api/v1/endpoints/memory.py:32` — 修改标记为如实描述当前实现状态（全部端点为占位实现）

- [ ] Task 7: 修复 adapter.py L195 配置传递 bug (AC: #3)
  - [ ] 7.1 编辑 `src/canvas/adapters/agentic_rag_adapter.py:195` — 将 `config={"configurable": config}` 改为 `context=config`，使 LangGraph Context API 扁平传递配置
  - [ ] 7.2 验证：传入非默认 fusion_strategy，确认 node 中 `_safe_get_config` 收到正确值

- [ ] Task 8: 清理 cs188 硬编码（20+ 处）(AC: #5)
  - [ ] 8.1 `backend/app/api/v1/endpoints/mastery.py` — 6 处 `default="cs188"` 改为从配置读取
  - [ ] 8.2 `backend/app/services/mastery_store.py` — 8 处 `group_id: str = "cs188"` 改为从配置读取默认值
  - [ ] 8.3 `backend/app/services/react_agent.py` — 4 处硬编码（group_id/vault 名）改为配置化
  - [ ] 8.4 `backend/app/services/review_service.py` — 1 处 `group_id="cs188"` 改为配置化
  - [ ] 8.5 `backend/app/services/memory_service.py` — 1 处 `group_id: str = "cs188"` 改为配置化
  - [ ] 8.6 `backend/app/services/agent_service.py` — 3 处硬编码改为配置化
  - [ ] 8.7 `backend/app/services/graphiti_bridge_service.py` — 3 处 `group_id="cs188"` + 文档注释改为配置化
  - [ ] 8.8 `backend/app/core/memory_format.py` — 文档注释中 cs188 引用更新
  - [ ] 8.9 `backend/app/api/v1/endpoints/metadata.py` — 1 处 `subject="cs188"` 改为配置化
  - [ ] 8.10 `backend/config/subject_mapping.yaml` — 保持为参考配置，确保代码从此配置读取
  - [ ] 8.11 清理 `backend/app/api/v1/endpoints/review.py:66` 中引用已删 env_config.py 的悬空注释

- [ ] Task 9: 清理 env_config.py 残留引用 (AC: #4)
  - [ ] 9.1 检查并清理 `backend/app/api/v1/endpoints/review.py:66` 中引用 env_config.py 的注释

- [ ] Task 10: 验证管道完整性 (AC: #9, #10)
  - [ ] 10.1 运行 `python -m compileall src/agentic_rag/ -q` — 字节码编译通过
  - [ ] 10.2 运行 `python -c "from agentic_rag.state_graph import build_canvas_agentic_rag_graph; build_canvas_agentic_rag_graph()"` — StateGraph 编译通过
  - [ ] 10.3 运行 `ruff check src/agentic_rag/` — lint 通过
  - [ ] 10.4 运行 `ruff check backend/app/` — lint 通过
  - [ ] 10.5 验证 `from app.services.rag_service import RAGService` 不报错（rag_service.py 也 import agentic_rag）
  - [ ] 10.6 运行 `python -c "from agentic_rag import *; assert AGENTIC_RAG_AVAILABLE"` — 注意 `__init__.py` 的 try/except 可能吞错误，必须 assert 变量

## Dev Notes

### 关键架构约束

- **活跃管道只依赖 4 个模块**：`state_graph.py` 导入 `config`, `nodes`, `retrievers`, `state`。9 个死模块均为叶节点（0 个活代码引用），一次删除安全
- **adapter.py bug 本质**：LangGraph Context API 要求 `context=config` 扁平传递，当前多包了一层 `{"configurable": config}` 导致所有节点中 `_safe_get_config()` 永远命中默认值
- **env_config.py 死代码确认**：283 行，仅自引用，零外部 import。包含已过时的 embedding 模型配置（与当前系统不兼容）
- **cs188 清理策略**：将硬编码替换为从配置读取的参数（如 `subject_config.py` 或 `config.py` 中的默认值），保持 `"cs188"` 为默认值以确保向后兼容，但来源变为配置化

### 不可动的文件（活跃管道核心）

以下文件属于活跃管道，本 Story 只做最小修改（修 bug/清注释），不做功能重构：
- `src/agentic_rag/state_graph.py` — StateGraph 编排
- `src/agentic_rag/nodes.py` — 管道节点实现（含内联融合/重排序实现）
- `src/agentic_rag/config.py` — RAG 配置定义
- `src/agentic_rag/state.py` — State 类型定义

### 误判排除（不要删除）

以下模块曾被初始审查误判为死代码，经 LSP 精确验证为**活跃模块**：
- `agent_graph.py` — 被 `backend/app/services/agent_service.py:L2787` 导入
- `graphiti_temporal_client.py` — 被 `backend/app/dependencies.py:L858` + `clients/__init__.py:L14` 导入

### 提交策略（4 次原子化提交）

依据 Meta SCARF（ESEC/FSE 2023）叶节点优先删除策略 + Google SWE Book Ch.15 防回退：

1. **Commit 1**: 归档参考文件（Task 1）— 确保参考代码存在后再删除
2. **Commit 2**: 删除死模块 + 测试文件（Task 2, 3, 4）— 一次性删除所有叶节点
3. **Commit 3**: 修复残留问题（Task 5, 6, 7, 8, 9）— Ghost tables + 虚假标记 + Config bug + cs188
4. **Commit 4**: 验证通过后提交验证脚本（Task 10）

### Source Tree Components

| 组件 | 路径 | 操作 |
|------|------|------|
| 死模块（9 个） | `src/agentic_rag/{fusion,observability,quality,quality_nodes,routing}/`, `src/agentic_rag/{reranking,parallel_retrieval,env_config,traced_nodes}.py` | 归档后删除 |
| 测试文件（2 个） | `src/tests/test_multimodal_rag.py`, `src/tests/agentic_rag/test_observability.py` | 归档后删除 |
| __init__.py | `src/agentic_rag/__init__.py` | 编辑：清理已删模块描述 |
| adapter.py | `src/canvas/adapters/agentic_rag_adapter.py` | 编辑：L195 修复 config 传递 |
| LanceDB client | `src/agentic_rag/clients/lancedb_client.py` | 编辑：修复 ghost tables |
| Agent graph | `src/agentic_rag/agent_graph.py` | 编辑：修复 ghost table fallback |
| API endpoints | `backend/app/api/v1/endpoints/{canvas,memory,mastery,metadata,review}.py` | 编辑：虚假标记 + cs188 |
| Backend services | `backend/app/services/{mastery_store,react_agent,review_service,memory_service,agent_service,graphiti_bridge_service}.py` | 编辑：cs188 清理 |
| Core | `backend/app/core/memory_format.py` | 编辑：cs188 文档注释 |
| Config | `backend/app/core/subject_config.py`, `backend/config/subject_mapping.yaml` | 参考/使用配置源 |
| Test | `src/tests/agentic_rag/test_lancedb_client.py` | 编辑：断言值同步 |

### Project Structure Notes

- 死模块位于 `src/agentic_rag/` 下，活跃管道同目录。删除后目录结构不变，只是减少了文件
- 归档目标 `_bmad-output/archive/` 遵循项目归档惯例
- `backend/app/` 和 `src/agentic_rag/` 是两个独立子系统，cs188 硬编码分布在两边
- `backend/app/core/subject_config.py` 已有 subject 配置基础设施，cs188 清理应利用此现有机制

### References

- [Source: _bmad-output/brainstorming/brainstorming-session-S1-dead-code-cleanup-2026-03-11.md] — 9 个死模块三重验证结果、执行策略、验收标准
- [Source: _bmad-output/brainstorming/brainstorming-session-2026-03-12.md#S4-Config统一] — adapter.py L195 config 传递 bug 发现和修复方案
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#Phase-0] — Phase 0 任务清单 0.1-0.10
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#CRITICAL级] — C1 Config 传递断裂、C7 双重触发
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure] — 后端目录结构规范
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.1] — Story 原始定义和 AC

## Dev Agent Record

### Agent Model Used

(to be filled during implementation)

### Debug Log References

### Completion Notes List

### Change Statistics (Expected)

| 类别 | 行数 |
|------|------|
| 删除（死代码） | 约 5090 行 |
| 删除（env_config.py） | 约 283 行 |
| 删除（测试文件） | 约 200 行 |
| 修改（config bug） | 约 1 行 |
| 修改（ghost tables） | 约 4 处 |
| 修改（虚假标记） | 约 2 处 |
| 修改（cs188 清理） | 约 25 处 |
| **净减少** | **约 5500+ 行** |

### File List

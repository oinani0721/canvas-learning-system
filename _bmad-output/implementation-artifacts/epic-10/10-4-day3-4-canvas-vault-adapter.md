---
story_id: "10.4"
epic_id: "10"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 16
depends_on: ["10.3"]
blocks: ["10.5"]
trace: ["FR-DEEP-04", "M1", "M11", "M12"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
day: "Day 3-4"
target_date: "2026-05-09 ~ 2026-05-10"
key_api: "POST /books/confirm-spine (Agent 2.4 发现)"
uat_sheet: "_bmad-output/验收单/Story-10.4-day3-4-canvas-vault-adapter.md"
---

# Story 10.4: Day 3-4 CanvasVaultAdapter（路径 B 核心）

**Status**: ready-for-dev (target Day 3-4, 2026-05-09 ~ 2026-05-10)

## Story（用户故事）

As a 学习者, I want my Canvas vault wikilink network (NetworkX graph) to be directly injected as a DeepTutor Spine JSON so that DeepTutor renders my actual notes as a book — without AI inferring relationships, with my structure 100% preserved, and zero LLM cost.

> **映射对**: M1（vault 文件夹检索）+ M11（vault 不上传文件）+ M12（5 大核心总结：原白板/检验白板/记忆/返回/推测）
> **关键 API 发现**: Agent 2.4 在 fork 找到 `POST /books/confirm-spine` 接受完整 Spine payload，绕过 IdeationAgent + SpineSynthesizer

## 通俗化解释（给学习者）

> **一句话说**: 把你 vault 笔记网络（含 wikilink 关系）直接"塞"进 DeepTutor 的 Book 数据结构，让 DeepTutor 像渲染自己生成的 book 一样渲染你的笔记。

**你会遇到的场景**:
- 你已经在 Obsidian 写了 100 个笔记 + 200 条 wikilink 关系
- 期望 DeepTutor 不用重新让 AI 写一遍，直接读你的笔记网络
- 在 DeepTutor 的 Book 列表多一本 "我的 vault 笔记网络"

**这个功能帮你**:
- 笔记结构 100% 保留（你定义的关系不被 AI 推断覆盖）
- LLM 成本为零（不调用 OpenAI/Anthropic）
- 跨 book 复用（laterStory 的 mastery / exam 用同一组节点）

**用个比喻**: 🌳 就像把家里的家谱画好后直接照搬上"姓氏档案库"——你的家谱不变，只是"档案库"提供了搜索/查询的能力。

## Acceptance Criteria

### AC #1: CanvasVaultAdapter 模块 (~300 行 Python)

- **Given** Canvas vault 路径含 `节点/` 目录 + wikilink 笔记
- **When** 跑 `python -m adapter.vault_to_spine --vault <path> --output spine.json`
- **Then** 输出 `spine.json` 符合 DeepTutor Spine schema (chapters + concept_graph)
- **And** 使用 obsidiantools 解析 wikilink → NetworkX DiGraph
- **And** 不调用任何 LLM（cost = 0）

### AC #2: Spine JSON 注入 fork

- **Given** 有效的 spine.json
- **When** `curl -X POST :8001/books/confirm-spine -d @spine.json`
- **Then** fork 内 books 列表多一本（title 与 vault 主题相关）
- **And** 该 book 的 spine 含用户原 vault 节点 + 关系（不是 AI 推断的）
- **And** 整个流程不触发 IdeationAgent + SpineSynthesizer

### AC #3: 端到端验证（接力 S2 前置）

- **Given** Day 4 收官时 vault 已注入为 book
- **When** 用户在 DeepTutor 打开该 book
- **Then** 看到原 vault 节点作为 chapter
- **And** ConceptGraphBlock 渲染（Mermaid 静态图，Day 5 升级 ReactFlow）
- **And** 节点数 ≥ vault 笔记数

### AC #4: CLI 工具完整

- **Given** adapter 模块完成
- **When** 用户跑 `python -m adapter.vault_to_spine --help`
- **Then** 显示参数清单：`--vault <path>`, `--output <json>`, `--book-title <name>`, `--max-chapters <n>`
- **And** 错误处理：vault 不存在 → 友好错误信息（不是 traceback）

## Tasks / Subtasks

- [ ] Task 1: CanvasVaultAdapter 模块 (AC: #1)
  - [ ] 1.1: 新建 `~/Desktop/canvas/deeptutor-fork/adapter/__init__.py`
  - [ ] 1.2: 新建 `adapter/vault_to_spine.py` 主类 `CanvasVaultAdapter`
    - 方法：`__init__(vault_path: str)`
    - 方法：`build_graph() -> nx.DiGraph` 用 obsidiantools 读 wikilink
    - 方法：`to_spine() -> dict` 转 DeepTutor Spine schema
    - 方法：`save(output_path: str)` 写 JSON
  - [ ] 1.3: 新建 `adapter/cli.py` 入口点
  - [ ] 1.4: 新建 `adapter/requirements-adapter.txt` (networkx>=3.0, obsidiantools>=1.10, pydantic>=2.0)

- [ ] Task 2: Spine schema mapping (AC: #1)
  - [ ] 2.1: 拓扑排序 vault 节点 → chapters 顺序（depends_on 边）
  - [ ] 2.2: 每个 vault md 文件 → 1 个 chapter + 1 个 page + N 个 block (TextBlock 渲染原文)
  - [ ] 2.3: wikilink 边 → ConceptEdge `relation: depends_on/extends/related`
  - [ ] 2.4: 节点 chapter_id 自动分配（参考 SpineSynthesizer 逻辑但不调 LLM）

- [ ] Task 3: 单元测试 (AC: #1)
  - [ ] 3.1: `tests/adapter/test_vault_to_spine.py` 测 graph building
  - [ ] 3.2: 测 Spine schema 验证（用 DeepTutor Spine pydantic model）
  - [ ] 3.3: 边界：空 vault、单节点、循环引用

- [ ] Task 4: 端到端 (AC: #2, #3)
  - [ ] 4.1: Day 3 跑 `python -m adapter.vault_to_spine --vault canvas-vault --output spine.json`
  - [ ] 4.2: Day 4 `curl -X POST :8001/books/confirm-spine -d @spine.json`
  - [ ] 4.3: 浏览器 :3782 → Books 列表 → 看到新 book
  - [ ] 4.4: 打开 book → 看到 vault 节点 + ConceptGraph

- [ ] Task 5: CLI 完整化 (AC: #4)
  - [ ] 5.1: argparse 参数清单
  - [ ] 5.2: 错误处理 + 友好提示
  - [ ] 5.3: README 用法说明

## Dev Notes

### 关键 API 发现（Agent 2.4）

`POST /books/confirm-spine` 接受完整 Spine payload：
```python
{
  "book_id": "...",  # 先 POST /books 创建 draft 拿 id
  "chapters": [{"id": "ch1", "title": "...", "concept_nodes": [...], "pages": [...]}],
  "concept_graph": {
    "nodes": [{"id": "node_1", "label": "Concept A", "chapter_id": "ch1"}],
    "edges": [{"src": "node_1", "dst": "node_2", "relation": "depends_on"}]
  }
}
```

### 路径 B vs A 决策

- **路径 A**（vault → KB upload → AI 生成 book）：~0 行代码但 LLM 成本高 + AI 主导（不保留结构）
- **路径 B**（vault → POST Spine payload）：~300 行代码但 LLM 成本 0 + 用户主权 100%

**选 B**：用户痛点是"AI 推断关系不可靠 + 跨 book 不复用"（Agent 2.5 第 6 节"递归是归纳法的特例"例子）

### 工作量分解
- Graph building (obsidiantools)：~50 行
- Spine schema mapping：~200 行
- Test + CLI：~50 行

### 已知陷阱
- obsidiantools 期望标准 Obsidian vault（含 `.obsidian/` 目录）
- vault 必须先通过 Story 10.3 vault mount 验证

## UAT 验收

详见 `_bmad-output/验收单/Story-10.4-day3-4-canvas-vault-adapter.md`

## References

- Deep Explore §2.4 外部数据注入 API（路径 A/B/C 对比）
- Deep Explore §3.3 Day 3-4 路线
- DeepTutor `deeptutor/api/routers/book.py` confirm_spine endpoint

---

## Round-22 修订（2026-05-07 — CLI/SDK/Book Engine 深度调研）

> **修订源**: `_bmad-output/research/round-22-cli-sdk-book-engine-deep-explore-2026-05-07.md`（CLI/SDK 深度探索）

### 关键发现

**F1 ⛔ Guided Learning v1.2.0 已删除（Book Engine 是继任者）**

DeepTutor v1.2.0 Release Notes 明确：Guided Learning 模块（~5300 行）已完全删除。**Book Engine 替代了它**：
- Spine（章节骨架）+ 14 BlockType 渲染
- `POST /books/confirm-spine` 是 Book Engine 的 spine 确认入口
- 路径 B 注入的对象是 Book Engine（不是 Guided Learning）

**影响**: 本 Story spec 中 "ConceptGraphBlock" 等术语对应 Book Engine 的 14 BlockType 之一，**不是 Guided Learning**。spec 描述准确，但术语应明确为 Book Engine。

**F2 CanvasVaultAdapter 应拆为 5 模块（不是单文件 ~300 行）**

调研推荐拆分（P0-P4 优先级）:

| 模块 | 优先级 | 工作量 | 职责 |
|---|---|---|---|
| **CanvasVaultAdapter**（主类） | P0 | ~80 行 | 入口编排 + spine schema 输出 |
| **VaultBlockGenerator** | P0 | ~60 行 | md → 14 BlockType 之一映射 |
| **CalloutAnnotationParser** | P1 | ~80 行 | 7 callout 类型解析（UX-1 批注核心）|
| **WikilinkGraphBuilder** | P0 | ~60 行 | obsidiantools → NetworkX |
| **UserProgressExtractor** | P2 | ~50 行 | 已读/已完成状态从 frontmatter 提取 |

**总计**: ~330 行（接近原 spec 估算 300 行）

**F3 工作量重估 16h → 5-7 day（约 35-50h）**

调研指出原 spec 估算严重低估：
- VaultBlockGenerator 14 BlockType 映射 = 14 套渲染 spec（每个 1-2h）
- CalloutAnnotationParser 7 callout 类型 = 7 套样式适配
- 测试覆盖度（边界 + 循环引用 + 空 vault）

**修正**: 推荐 Day 3-4 完成 P0 模块（最小可用），P1-P2 模块推迟到 Day 5（与 Whiteboard 路由并行）。

**F4 BlockType Enum 无需扩展（Day 3-4 仅用 Spine 输出）**

Story 10.4 的 spine.json 仅用 Book Engine 现有 14 BlockType（TEXT/CONCEPT_GRAPH 等）。**不要在 Day 3-4 加新 BlockType**（避免 Pydantic 30+ 连锁错误）。

新 BlockType（MASTERY_DASHBOARD/EXAM_WHITEBOARD/ERROR_CANDIDATE）留给 Story 10.6/10.7（Day 7-8）。

### 修订后任务清单

#### Day 3 morning（P0 模块 — 最小可用 spine 输出）

- [ ] Task 6: 拆分 CanvasVaultAdapter 为 5 模块（重构原 Task 1）
  - [ ] 6.1: 新建 `adapter/canvas_vault_adapter.py`（主类，~80 行）
  - [ ] 6.2: 新建 `adapter/vault_block_generator.py`（14 BlockType 映射，~60 行）
  - [ ] 6.3: 新建 `adapter/wikilink_graph_builder.py`（obsidiantools 包装，~60 行）
  - [ ] 6.4: 主类 `__init__` 注入 3 个 builder

#### Day 3 afternoon（端到端最小注入）

- [ ] Task 7: P0 模块端到端
  - [ ] 7.1: 跑 `python -m adapter.cli --vault canvas-vault --output spine.json`
  - [ ] 7.2: 验证 spine.json 含 chapters + concept_graph
  - [ ] 7.3: `curl -X POST :8001/books/confirm-spine -d @spine.json` 返回 200
  - [ ] 7.4: 浏览器 :3782 看到新 book（最小验证）

#### Day 4 morning（P1 — Callout 解析）

- [ ] Task 8: CalloutAnnotationParser（UX-1 批注核心落地）
  - [ ] 8.1: 新建 `adapter/callout_annotation_parser.py`（~80 行）
  - [ ] 8.2: 解析 `> [!question]+ [!error]+` 等 7 callout 类型
  - [ ] 8.3: 转 Book Engine CalloutBlock（已 Story 10.3 修复 wikilink 渲染）
  - [ ] 8.4: 测试：CS 61B vault `[!error]+ NEG-3` 标注解析

#### Day 4 afternoon（P2 — 用户进度 + 端到端验证）

- [ ] Task 9: UserProgressExtractor（已读状态）
  - [ ] 9.1: 新建 `adapter/user_progress_extractor.py`（~50 行）
  - [ ] 9.2: 从 md frontmatter 解析 `status: read/completed` 字段
  - [ ] 9.3: 注入 spine.json 的 chapter `progress` 字段

- [ ] Task 10: 完整端到端 + UAT
  - [ ] 10.1: 跑完整 vault 注入（~100 节点 + 200 wikilink）
  - [ ] 10.2: 浏览器验证：book 渲染 + ConceptGraph 显示 + Callout wikilink 蓝链
  - [ ] 10.3: 性能：spine.json 生成 < 30s（100 节点）

### 推荐路径（Chat vs TutorBot 双轨）

| Canvas 核心 | 推荐 capability | Why |
|---|---|---|
| 5 大核心总结（M12，原白板/检验/记忆/返回/推测） | **Book Engine + spine 注入**（路径 B） | 用户主权 100% + LLM 成本 0 |
| 节点深度问答（"递归 vs 归纳法"） | TutorBot 长程伴学 | 多回合 + 跨节点关联 |

### 修订后估算

- **Day 3-4 完成 P0+P1**（~25-30h）：spine 注入端到端可用 + Callout 解析
- **Day 5 morning 顺手 P2**（~5h，与 Whiteboard 并行）：用户进度提取
- **AC 不变**（保持原 4 个 AC）：P0 模块即可满足；P1/P2 是"加分项"

### 新增 AC（Round-22 推荐）

#### AC #5: Callout 7 类型注入 spine（UX-1 落地）

- **Given** vault md 含 `> [!question]+ [[recursion]]` 类标注
- **When** spine.json 生成
- **Then** Book Engine CalloutBlock 渲染时 callout 类型正确（蓝色 question icon）
- **And** callout 内 `[[recursion]]` 渲染为蓝链（依赖 Story 10.3 CalloutBlock 修复）

---

## 下一步

→ Story 10.5 Day 5-6 Whiteboard 路由 + ReactFlow（让注入的 vault 图变成可交互白板）

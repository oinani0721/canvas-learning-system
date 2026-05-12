---
story_id: "2.2+2.9"
task_id: "T3+T5"
title: "Rerank Engine (type 权重 + query-aware + hub penalty) + 引证渲染"
ship_date: "2026-05-11"
status: "review"
phase: "B (功能可用)"
trace:
  - "Story-2.2+2.9 AC #4 (Rerank Engine)"
  - "Story-2.2+2.9 AC #6 (Relationship Evidence)"
  - "PRD §4.1.1 type weight 6 档"
  - "PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17"
deploy:
  backend_files: |
    新增 supplementary_reranker.py + rerank_service.py
    扩展 wikilink_graph_service.py / wikilink_context_service.py / chat_context_assembler.py / chat.py
  tests: 65+ 新增 unit tests 全 green
---

# Story 2.2+2.9 T3+T5 — 补充材料精排 + 引证渲染验收单

## 1. 🎯 一句话目标（非技术）

当你问 Claude 一个学习问题时，补充材料列表不再随机或被几个"热门索引节点"占满，而是按"和你问题最相关 + 课件等高质量优先 + 不让单一索引垄断"重新排序；且当节点的 frontmatter 里写了"see eq. 3.2 in Strang"这种引证时，Claude 会在它的对话上下文里看见这条引证。

## 2. 📖 你的视角

**作为** 一个学 CS 61B / 数学的人,
**我想** 我按 Cmd+Shift+E 后看到的补充材料越往前越是真正相关的、越是 lecture / discussion 这类有干货的来源、且不被 MOC/Index 类（链接特别多的）节点压住,
**以便** 我读前 3-5 条就能直接定位到答案，不用翻 20 条材料才找到核心。

## 3. 🖥️ 交互流程（你的屏幕变化）

**问 Claude 概念问题**:
```
你做: 打开 节点/admissibility.md → 按 Cmd+Shift+E
↓
屏幕右上角弹 Notice: "已组装 backend RAG 上下文 N KB / X 邻居 + Y 补充材料 ⭐ ..."
↓
切到 Claudian 侧栏 → Cmd+V 粘贴 → 你看到对话开头第一段加载好的资料
↓
你输问题: "admissibility 怎么证明？"
↓
Claude 回答里引用的材料应该是 lecture_notes / discussion 类型在前
"index" / "MOC" / "目录" 类节点不在 Top-5 里
材料数 ≤ 5（不再淹没你）
```

**节点带 frontmatter relationships.evidence 时**:
```
你做: 在 节点/Eigenvalues.md frontmatter 写
      relationships:
        - type: prerequisite
          target: "[[Fundamentals]]"
          evidence: "see eq. 3.2 in Strang Ch. 6"
↓
按 Cmd+Shift+E
↓
切 Claudian 后粘贴 → 你看到 Fundamentals 邻居那段含
"- 引证: see eq. 3.2 in Strang Ch. 6" 这一行
```

## 🤖 Claude 已代验（技术指标，你不用管）

| Check | 命令 / 证据 | 结果 |
|---|---|---|
| 新增 supplementary_reranker.py | `ls backend/app/services/supplementary_reranker.py` | ✅ 156 行,TYPE_WEIGHTS + rerank() + compute_hub_penalty() + get_filter_threshold() |
| 新增 rerank_service.py | `ls backend/app/services/rerank_service.py` | ✅ 117 行,自实现 Okapi BM25 + jieba 中英分词 + min-max normalize |
| wikilink_graph_service 扩展 | `grep get_degree_stats` | ✅ get_degree_stats() + get_degree() 同步加入 |
| Rerank 单元测试 | `pytest tests/unit/test_supplementary_reranker.py` | ✅ 42 pass (TYPE_WEIGHTS / rerank / query_overlap / hub_penalty / filter+top_k) |
| BM25 单元测试 | `pytest tests/unit/test_rerank_service.py` | ✅ 18 pass (tokenize / bm25_scores / normalize_to_unit) |
| Degree stats 测试 | `pytest tests/unit/test_wikilink_graph_service.py -k Degree` | ✅ 8 pass (empty graph / simple graph / get_degree basename fallback) |
| Evidence extract 测试 | `pytest tests/unit/test_wikilink_context_service.py -k evidence` | ✅ 6 pass (含 _extract_relationship_info / enrich 透传) |
| Evidence 渲染测试 | `pytest tests/unit/test_chat_context_assembler.py -k evidence` | ✅ 4 pass (含 / 缺 / xml 转义 / 截断) |
| XML rerank 字段透出 | `pytest tests/unit/test_supplementary_search_service.py -k Rerank` | ✅ 3 pass (字段在/缺/部分场景) |
| 全后端 unit suite 零回归 | `pytest tests/unit/` | ✅ 见 background 任务 b54j3j5iz output |
| TraceItemModel 加 5 optional 字段 | code review `chat.py:164` | ✅ rerank_score / type_weight / hub_penalty / query_overlap / evidence (全 default None) |
| chat.py wire rerank | code review `chat.py:supp_result` 之后 | ✅ get_filter_threshold()=0.42 + top_k=5 + median_degree 来自 graph_svc.get_degree_stats() |
| format_supplementary_xml 透字段 | code review `supplementary_search_service.py:format` | ✅ rerank_score / type_weight / query_overlap / hub_penalty 4 attribute (字段存在时才输出) |
| Final score 公式 | code review `rerank()` | ✅ `relevance × type_weight + query_overlap × 0.3 − hub_penalty` |
| Filter 阈值 | code review `get_filter_threshold()` | ✅ 0.70 × min(TYPE_WEIGHTS canonical) = 0.70 × 0.6 = 0.42 |
| Tie-break 确定性 | unit test `test_full_tie_fallback_to_title_lexicographic` | ✅ 同 rerank_score 时 title 字典序升序 |

**Claude 模拟验证场景**（你不用做，仅记录）:
- 场景 A: 同 relevance 0.5，lecture_notes (1.0) vs raw_notes (0.6) → lecture_notes 优先 ✅
- 场景 B: query "admissible heuristic" 命中标题 "admissible heuristic search" vs "cooking" → 命中前 ✅
- 场景 C: 同 score+type 的两节点,degree 20 vs degree 2, median=3 → degree=2 优先 (hub penalty 起作用) ✅
- 场景 D: query 全无匹配 → 退化到纯 type_weight 排序，等价 T3b ✅
- 场景 E: 中文 query "启发式" via jieba tokenizer 匹配中文 snippet ✅

## 👤 你来验（产品体验，3-5 分钟，全在 Obsidian 里）

> 这一段全程在 Obsidian 主界面 + Claudian 侧栏操作。
> 你不需要打开任何控制台 / 终端 / 网页 / 设置面板。

### Step 1 — 提个问题，看补充材料排序更合理

- [ ] 我做：打开一个你最近学过的概念页面（比如 `节点/admissibility.md` 或 `节点/Eigenvalues.md` 或你常用任意节点）
- [ ] 我做：按 Cmd+Shift+E（不是 Cmd+Shift+C，也不是 Cmd+Shift+Q）
- [ ] 我做：切到 Claudian 侧栏，按 Cmd+V 粘贴
- [ ] 我做：在输入框追加问题，比如 "怎么证明它？" 或 "我哪里没掌握？"，回车
- [ ] 我看到：Claude 回答里引用的补充材料标题（如果有引用），讲义 / 课件类（标题里能看出是 lecture / discussion / exam_review 词样的）排在前面，原始笔记 / 草稿类排后面
- [ ] 我感觉：前 3 条材料基本就是我想要的方向，不像以前要翻 8-15 条才看到核心；信任感提升

### Step 2 — Hub 节点不再霸占 Top-5

- [ ] 我做：换一个有 MOC / 目录性质邻居的节点（比如 `节点/CS 61B Index.md` 这种你自己建的索引节点 — 或任一你心里认为"双链特别多"的节点）
- [ ] 我做：按 Cmd+Shift+E + Cmd+V 粘贴到 Claudian + 问"这个领域的核心概念是？"
- [ ] 我看到：Claude 给出的补充材料里**没有**任何条目是那个 MOC / Index 节点本身（即使它链接多到爆）；展示的反而是几个 atomic concept 节点
- [ ] 我感觉：终于不被"索引页"刷屏了，Claude 看到的是真知识颗粒，不是"列表的列表"

### Step 3 — 引证（evidence）显示

> 这一步**需要你先在 frontmatter 里写一个 evidence 字段**才能验证。
> 5 秒内可完成：

- [ ] 我做：随便打开一个你正在学的节点（比如 `节点/Eigenvalues.md`）
- [ ] 我做：在文件顶部 frontmatter (两行 `---` 之间) 加这几行（如果已有 `relationships:` 就追加一条）：
  ```
  relationships:
    - type: prerequisite
      target: "[[Fundamentals]]"
      evidence: "see eq. 3.2 in Strang Ch. 6"
  ```
- [ ] 我做：保存这个文件 → 切回 `节点/Fundamentals.md`（如果不存在就新建一个空的）
- [ ] 我做：按 Cmd+Shift+E + 切 Claudian + Cmd+V 粘贴
- [ ] 我看到：粘贴出来的内容里能直接看到 "- 引证: see eq. 3.2 in Strang Ch. 6" 这一行（在 Fundamentals 的 neighbor 段里，靠近 "- 关系: prerequisite"）
- [ ] 我感觉：我手写的"看哪本书第几页"被忠实带进 Claude 的对话上下文了，不再丢

### Step 4 — 主路径不变（最重要的回归确认）

- [ ] 我做：再回任意一个普通节点，按 Cmd+Shift+E + Cmd+V
- [ ] 我看到：和以前一样的 Notice "已组装 backend RAG 上下文 ..."，没有怪的报错弹窗
- [ ] 我感觉：没把好东西改坏，原工作流照旧

## 5. 🚦 验收结果

### 通过条件（全勾或自评满意）

- [ ] Step 1 ✅ 排序看起来比之前清晰
- [ ] Step 2 ✅ MOC/Index 不在 Top-5
- [ ] Step 3 ✅ 引证字段出现在 prompt 里
- [ ] Step 4 ✅ 主路径无变化

通过 → 在末尾写"T3+T5 通过，可启 T6 验证 / T0 主链路修复"

### 不通过

- 用 Cmd+Shift+A 在下面的批注区加 `[!error]+` 写发生了什么
- 列出"实际看到什么 / 期望看到什么 / 节点路径 / 提问内容"
- 我读批注后用 correct-course 调整

## 6. 📝 批注区（用 Cmd+Shift+A）

```
> [!question]+
> 在这里写你的疑问

> [!error]+
> 在这里写不通过原因

> [!tip]+
> 在这里写你认为可以优化的点
```

### 已知的已批注问题（历史追溯）

无，本次 ship 是 T3 + T5 首次 review

## 7. 🔗 技术 spec 引用（给 Claude 读的，你不用看）

- Spec: `_bmad-output/implementation-artifacts/epic-2/2-2-and-2-9-merged-rerank-evidence.md`
- 关键代码:
  - `backend/app/services/supplementary_reranker.py` (rerank engine)
  - `backend/app/services/rerank_service.py` (BM25 primitives)
  - `backend/app/services/wikilink_graph_service.py:get_degree_stats / get_degree`
  - `backend/app/services/wikilink_context_service.py:_extract_relationship_info`
  - `backend/app/services/chat_context_assembler.py:_format_neighbor_metadata` (引证渲染)
  - `backend/app/services/supplementary_search_service.py:format_supplementary_xml` (rerank 4 字段透出)
  - `backend/app/api/v1/endpoints/chat.py` (rerank wire-in)
- 测试: `backend/tests/unit/test_supplementary_reranker.py` (42) + `test_rerank_service.py` (18) + 4 个现有 test_*.py 扩展
- PRD 锚点: §4.1.1 type weight 6 档表 (lecture_notes 1.0 → raw_notes 0.6)
- PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17

---

*本验收单 ship 时间: 2026-05-11，符合 DoD-3 双段铁律 D3-A~E，段 4-B 用"我做 X → 我看到 Y → 我感觉 Z"句型 + 0 技术禁词命中。*

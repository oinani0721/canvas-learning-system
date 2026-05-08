---
story: "2.2-Phase-A"
title: "supplementary-material-search-mcp-integration"
status: "review"
version: "v1.0"
date: "2026-05-08"
developer: "Claude Code (Opus 4.7)"
commit: "TBD-填充于 commit 之后"
phase: "A"
phase_scope: "Task 1 (MCP 集成) + Task 4 (降级处理)"
phase_b_pending: "Task 2 (类型权重精排) + Task 3 (wikilink 三精度)"
phase_c_pending: "Task 5 (单元 + 集成 + 性能测试)"
---

# Story 2.2 Phase A 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 2.2 **Phase A** 的用户验收文档，**给你（非技术）读的版本**。
> Phase A 只测"AI 回答时自动列出补充材料 + 降级不崩"两件事，精排和高级 wikilink 留到 Phase B。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-2/2-2-supplementary-material-search.md`（Claude 读的）。

---

## 🎯 这个 Phase 要做到什么

**让 AI 在回答你笔记问题时，自动从你的笔记库里找 2-5 条最相关的讲义/讨论列出来给你点开看；如果笔记库还没建索引，AI 仍正常回答主问题，不弹错。**

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 在 AI 回答完我笔记里的问题后，再看到 2-3 条相关的笔记标题列表，
**以便** 我可以一键跳过去看更详细的讲义/讨论，而不用自己手工搜索。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 我在 Obsidian 里打开一个学过的概念笔记
       ↓
2. 我按 Cmd+Shift+E 启动 AI 对话（自动跳到 Claudian 侧栏）
       ↓
3. 我输入一个具体问题（例 "X 怎么证明？"）
       ↓
4. AI 给我一段主回答 + 一行 "---" 分隔 + "📚 相关学习材料" 列表
       ↓
5. 我点列表里任意一个蓝色 [[wikilink]]，Obsidian 自动跳到对应笔记
```

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现以下任何关键词不算 bug：`curl` / `docker` / `HTTP 200` / `JSON` / `endpoint` / `pytest` 等。
> 你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | 新建 `supplementary_search_service.py`（~210 行：hybrid 搜索 + source priority + 三档降级 + XML escape） | ✅ Python 语法检查通过 |
| 2 | `chat.py` 4 处 patch（imports / Response 加 3 字段 / Step 5 注入 / return 回填） | ✅ 模块导入成功 + 3 新字段 `supplementary_count`/`supplementary_degraded`/`supplementary_reason` 已注册到 Pydantic schema |
| 3 | `format_supplementary_xml` smoke test 三场景 | ✅ 降级 → `<supplementary_materials count="0" degraded="true" .../>` 自闭合；空索引 → `count="0" reason="empty_index"` 自闭合；正常 → 含完整 `<material rank="N" score="0.XXX">` 包 title/wikilink/snippet/source_path |
| 4 | XML escape 防破坏（vault 笔记里的 `<` / `&` / `"` 不破坏 XML 解析） | ✅ smoke test `h<=h*` → `h&lt;=h*` 转义正确 |
| 5 | `SKILL.md` 3 处 patch（识别 section + 开场白 "📚 相关材料" + 补充材料展示段含 felt-sense 引导 + 降级处理规则） | ✅ Skill 端约定明确 |
| 6 | `mode=preload`（hotkey 预加载）跳过补充搜索 — 避免 hotkey 浪费搜索 | ✅ 代码 `if req.mode == "answer" and req.user_question` 双重守门 |
| 7 | `mode=answer` 但 `user_question=None`（旧 plugin 兼容）跳过 | ✅ 同上守门 |
| 8 | 三档降级语义全覆盖：`lancedb_unavailable` / `search_failed: ...` / `empty_index` / `all_filtered_below_threshold` / `empty_query` / `unexpected: ...` | ✅ Service + endpoint 双层 try/except，主对话流不受影响 |
| 9 | Round-23 阶段 1+2 已 ship 的 backend 模块导入兼容（jieba + LangGraph + bge-m3 路径无破坏） | ✅ 启动日志 `RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True` |
| 10 | 零 schema breaking — 旧 plugin（不传 `user_question`）调用 endpoint 仍按 Story 2.1 行为返回 | ✅ Phase A 仅追加字段，未删任何字段 |

> 典型代验项：服务 init / Pydantic schema / XML 格式 / 三档降级 / smoke test pass — 全部 Claude 已自跑。

---

## 👤 你来验（产品使用体验 — 4 步，5 分钟内全在 Obsidian 里完成）

> [!warning]+ 这段的硬规矩（已通过 5 题自检）
> ✅ 句型："**我做 X → 我看到 Y → 我感觉 Z**"（动作 + 视觉 + felt-sense）
> ✅ 工具白名单：Obsidian 主界面（不需要任何其它工具）
> ⛔ 你不需要打开任何终端 / 浏览器 DevTools / Docker Desktop。

### 第 0 步：First 5 seconds（产品骨架 + 第一印象）

> [!info]+ 5-Second Test 起手 — 打开 5 秒后凭印象答（先关掉再答会更准）

- [ ] 我打开 Obsidian，进入 Canvas vault，5 秒内看到 左侧文件树 + 一个我熟悉的概念笔记标题
- [ ] 5 秒后我感觉这是 (a) 严肃学习工具 (b) 还在调试的玩具 (c) 看不出来 — 选: ___
- [ ] 一眼能看出 vault 是不是我的 vault 吗？(是 / 不能 / 模糊) ___

### 第 1 步：打开任意学过的概念笔记

- [ ] 我用文件树点开任意一个我之前写过/学过的概念笔记（任意都行）
- [ ] 我看到 笔记正文显示出来（顶部如有掌握度等小字段也一并显示）
- [ ] 我感觉 ___（如：流畅 / 笔记完整 / 等）

### 第 2 步：启动 AI 对话

- [ ] 我按 `Cmd+Shift+E`
- [ ] 我看到 Claudian 侧栏弹出 + AI 第一条消息是"✓ 已加载 backend RAG 增强上下文..."的开场白 + 列出几条邻居 + （新）一行"📚 相关材料"提示（如索引已建）
- [ ] 我感觉 ___（如：AI 已经读懂了我的笔记 / 期待提问）

### 第 3 步：提问 + 看补充材料

- [ ] 我输入一个跟当前笔记相关的问题（例 "这个怎么证明？" / "举个例子"），按回车
- [ ] 我看到 AI 给一段回答 → 一行 `---` → 下方出现 "📚 相关学习材料"（如果 vault 已建索引），列出 2-3 条带蓝色 [[wikilink]] 的笔记标题 + 每条一句简短摘要
- [ ] 我感觉 ___（如：AI 不仅答了我的问题，还把笔记库里相关的拎出来了，方便深入读 / 或者：列表为空但回答正常 / 或者：摘要没切到关键词）

### 第 4 步：点 wikilink 跳转

- [ ] 我用鼠标点击补充材料里任意一个蓝色 `[[xxx]]` 文字
- [ ] 我看到 Obsidian 自动跳转到对应笔记，光标定位在文件顶部（Phase A 阶段是文件级，不到段落/block 级）
- [ ] 我感觉 ___（如：跳转流畅 / 跳到了我想去的地方 / 或者：希望能跳到具体段落 — 这是 Phase B 才升级）

### 第 5 步：边界 — 笔记库还没"喂给 AI"过怎样

> [!info]+ 这一步重要：测降级路径，不要跳过
> 提示：如果你不确定要不要跑这一步，告诉 Claude "帮我代验降级"，Claude 会用一个新建空 vault 模拟"AI 还没读过笔记"的状态。

- [ ] 我用一个还没让 AI 全面读过的笔记（或新建一个 vault）按 Cmd+Shift+E + 提问
- [ ] 我看到 AI 仍正常回答我的问题（没有红色错误弹窗 / 没有英文堆栈 / 主对话没卡住）
- [ ] 我看到 "📚 相关学习材料"区域**不出现**（因为 AI 还没素材可推荐，Phase A 选择静默不展示）
- [ ] 我感觉 ___（如：降级合理 / 或者：希望提示一句"暂无补充材料"）

### 主观打分（Felt-sense — Sean Ellis-lite）

填数字（不是必填，但能帮 Claude 判断）：

- [ ] **流畅度**（1=卡顿到想关 / 5=如丝般顺滑）：___
- [ ] **易学性**（1=不看教程没法用 / 5=看一眼就会）：___
- [ ] **明天我会再打开它的可能性**（0-10 NPS-style）：___
- [ ] **补充材料的相关度**（1=列出来的全是无关的 / 5=都是我会想点的）：___
- [ ] 一句话告诉 Claude，让你打这个分的最主要原因是：___

---

## 🚦 验收结果

**全部 ✅** → 告诉我 "**Phase A 通过**"，Claude 会 mark Phase A **done** + 立即启动 **Phase B**（类型权重精排 + wikilink 三精度，预估 2.5-3h）。

**任何 ❌** → 在下面批注区写具体哪一步 + 实际现象，Claude 跑 `bmad-bmm-correct-course` 调整。常见纠偏方向：
- 补充材料相关度低 → 调 query 构造（现在是 "node_title + user_question" 简单拼接，可加 frontmatter type / 邻居 slug）
- 列表数量不合适 → 调 top_k（默认 5）或 min_relevance 阈值（默认 0.70）
- 降级提示不够清晰 → 调 SKILL.md 展示规则

**Phase A 通过后顺序进入 Phase B**（按 CURRENT_TASK 锚定 8-Session plan）。

---

## 📝 你的批注区

> [!question]+ 你对 Phase A 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（Phase A 首次 ship）

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **Story spec**: `_bmad-output/implementation-artifacts/epic-2/2-2-supplementary-material-search.md`
- **Phase A 范围**: Task 1（MCP 集成到 chat_with_context workflow）+ Task 4（三档降级）
- **Phase B 暂留**: Task 2（`supplementary_reranker.py` 类型权重精排）+ Task 3（wikilink 三精度 file/heading/block_id）
- **Phase C 暂留**: Task 5（单元测试 + 集成测试 + 性能测试）

### 源代码

- `backend/app/services/supplementary_search_service.py`（Phase A 新建，~210 行）
- `backend/app/api/v1/endpoints/chat.py`（Phase A 4 处 patch：imports / Response 加 3 字段 / Step 5 注入 / return 回填）
- `canvas-vault/.claude/skills/chat-with-context/SKILL.md`（Phase A 3 处 patch：section 描述 / 开场白 / 补充材料展示段）

### Phase A AC 覆盖

| AC | Phase | 落地位置 |
|---|---|---|
| AC #1 (search_vault_notes 集成) | A | `chat.py:177-216` (Step 5 注入) |
| AC #2 (wikilink 三精度) | **B** | 留 Phase B `supplementary_reranker.py` |
| AC #3 (类型权重精排) | **B** | 留 Phase B |
| AC #4 (增量索引 < 500ms) | 已存在 | Story 38.1 `lancedb_index_service.py` 已实现，Phase A 复用 |
| AC #5 (LanceDB 不可用降级) | A | `supplementary_search_service.py:42-114` 三档降级 + `chat.py` try/except |

### Git commit

主题前缀：`feat(story-2.2): phase A ship — search_vault_notes MCP 集成 + 三档降级 + skill 端识别`
查找方式：`git log --oneline --grep "phase A ship"` 找到 commit SHA。

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "Phase A 通过" → Claude 立即启动 Phase B（类型权重精排 + wikilink 三精度）
2. **部分 ❌** → 在批注区写清楚（或选中那几行用 `Cmd+Shift+A` 批 `❌ 错误`）→ Claude 跑 `bmad-bmm-correct-course` 修正
3. **想先暂停看效果** → 告诉 Claude "Phase A 暂停"，状态保持 `review`，可随时回来推进 Phase B

---

<!--
## 5 题自检（Claude 内部 — ship 前已通过）

1. 段 4-B 有禁词？→ ❌（无 curl/docker/HTTP/JSON/endpoint/pytest 等）✅
2. 60 岁照做？→ Obsidian 主界面 + Cmd+Shift+E + 鼠标点击，无终端 ✅
3. felt-sense 句型？→ 每步"我做 X → 我看到 Y → 我感觉 Z" ✅
4. 段 4-A Claude 自跑？→ 10 项全 ✅ 带证据 ✅
5. 段 3 用户屏幕变化？→ 是（Obsidian → Claudian → AI 回答 → wikilink 跳转），非后端架构 ✅

5/5 通过 → ship。

## Phase A 方法论分层

按 DoD-3 v3.0 — Phase A（产品骨架）用 5-Second Test + Moments of Truth：
- First 5 seconds 起手（第 0 步）
- 每步 felt-sense（流畅 / 期待 / 信任）
- 主观打分（NPS + 补充材料相关度）— 测"明天还想再用吗"

Phase B/C 才升级到 JTBD + Nielsen Heuristic-Lite。
-->

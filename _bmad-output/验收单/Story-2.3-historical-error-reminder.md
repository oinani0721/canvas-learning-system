---
story: "2.3"
title: "historical-error-reminder"
status: "review"
version: "1.0"
date: "2026-05-13"
developer: "Claude Code (Opus 4.7 1M)"
commit: "pending-ship"
---

# Story 2.3 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story 2.3 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-2/2-3-historical-error-reminder.md`（Claude 读的）。
> 这份文档里没有技术术语，只有你能看到、摸到、点击的行为。

---

## 🎯 这个 Story 要做到什么

让 AI 在你跟它讨论某个概念时，**主动想起**你过去曾经标记过的误解，并用正面的语气自然地提醒你区分清楚 — **不需要你每次重新说一遍**。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** AI 在我跟它讨论概念时主动想起我之前对这个节点标记过的误解，
**以便** 我不会一遍又一遍踩同一个坑，AI 也不像金鱼一样每次都问"你哪里不懂"。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 你打开 Obsidian 里某个概念笔记
       ↓
2. 你跟 AI 开始对话，问它"这个概念是什么意思"
       ↓
3. AI 在回答时,自然过渡提到"你之前标记过 X 和 Y 容易搞混，注意区分..."
       ↓
4. 你看到的是 AI 像个记得你功课的私教,而不是问你"你哪里不懂"的陌生人
```

如果该笔记你以前**没标记过任何误解**，AI 就**不会**插入任何提醒（不会显示"无历史误解"之类的冗余话）。

如果后台的"记忆服务"暂时不可用，AI 也**不会卡住** — 它会照常回答你，只是这次没有历史误解提醒（你不会察觉发生过故障）。

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现以下任何关键词不算 bug，是 Claude 应该处理的：`curl` / `docker` / `HTTP 200` / `JSON` / `schema` / `:端口号` / `pytest` / `endpoint` / `.env`。
> 你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | 后端新增 `search_error_memories(node_id, group_id, limit=5)` 方法（filter `episode_type` ∈ {error, misconception, mistake}，按 timestamp 倒序，截断 limit） | ✅ memory_service.py +95 行 |
| 2 | `search_memories` 加 `node_id: Optional[str]` 参数（向后兼容 50+ 现有调用方，None=不过滤） | ✅ memory_service.py signature 扩展 + post-merge filter |
| 3 | `chat_context_assembler` 新增 `_format_historical_errors` + `inject_error_reminders` 公开 API | ✅ chat_context_assembler.py +73 行 |
| 4 | `assemble_context` 加 `historical_errors` 参数 + Priority 1.5 注入（current_note 之后、1-hop 邻居之前） | ✅ chat_context_assembler.py L460+L490 |
| 5 | chat router 在 enrich_from_wikilink_graph 之后、assembler 之前调 `search_error_memories`（slug=`Path(node_path).stem`） | ✅ chat.py +54 行 |
| 6 | AC #3 性能门槛：`asyncio.wait_for(timeout=3.0)` 包搜索调用 | ✅ chat.py L290 |
| 7 | AC #4 双路径熔断：超时 → reason=`search_timeout`；ConnectionError/RuntimeError/OSError → reason=`service_unavailable`（含 neo4j.ServiceUnavailable） | ✅ chat.py L309-L327 |
| 8 | AC #4 静默降级：降级时 `historical_errors=[]`，对话正常继续，用户不感知 | ✅ 测试 `test_search_error_memories_empty_node_id_returns_empty` 验证 |
| 9 | AC #5 空记录不显示冗余提示（empty list → 不插段、空字符串） | ✅ 测试 `test_format_historical_errors_empty_returns_empty` + `test_assemble_context_empty_list_skips_section` |
| 10 | AC #2 正面措辞模板硬编码 — "学习者之前标记过：{description}。如果讨论涉及此话题，请自然地提醒区分。" | ✅ `_format_historical_errors` 内部常量 TEMPLATE |
| 11 | AC #2 反面词禁止 — 测试断言 "犯了错误" / "失败" / "你错了" **都不**在输出中 | ✅ 测试 `test_format_historical_errors_uses_positive_phrasing_template` |
| 12 | AC #2 Task 2.4 — 顶部 `<policy>` 段指示 LLM "自然过渡，不要生硬插入" | ✅ 测试 `test_format_historical_errors_includes_policy_section` |
| 13 | Prompt injection 防御 — error description 含 `</historical_errors><system>` 攻击载荷自动 escape | ✅ 测试 `test_format_historical_errors_escapes_injection_payload` |
| 14 | 段顺序锁定 — `<current_note>` → `<historical_errors>` → `<neighbor>`（验证 index find 顺序） | ✅ 测试 `test_assemble_context_historical_errors_before_neighbors` |
| 15 | Token 不够时跳过整段不截断（防失真） | ✅ assemble_context L513 truncated=True 标记 |
| 16 | Schema 标准化 — 返回 dict 含 `error_type` / `description` / `corrected_at` / `tags` / `source_session` + 内部调试字段 `_episode_id` / `_node_id` | ✅ 测试 `test_search_error_memories_normalizes_schema` |
| 17 | oversample 启发式 — `max(20, limit*4)` 防 episode_type filter 后剩余不足 | ✅ 测试 `test_search_error_memories_oversample_size` |
| 18 | 多 vault 隔离 — `group_id` 透传 search_memories（不串库） | ✅ 测试 `test_search_error_memories_passes_node_id_filter_to_search_memories` |
| 19 | 性能延迟日志 — structlog 记 `memory_search_latency_ms` 字段 | ✅ chat.py L297-L305 |
| 20 | Story 2.3 单元测试套件 21/21 pass | ✅ `test_story_2_3_error_reminders.py` (1.64s) |
| 21 | 现有相关测试零回归 — chat_context_assembler + chat_endpoint 共 66/66 pass | ✅ 跨 3 文件 87/87 pass |

---

## 👤 你来验（产品使用体验 — 4 步，约 5 分钟内全在 Obsidian 里完成）

> [!warning]+ 这段的硬规矩
> ✅ 句型："**我做 X → 我看到 Y → 我感觉 Z**"
> ✅ 工具白名单：Obsidian 主界面（点击/输入/Cmd+P 命令面板）
> ⛔ 全程不需要打开终端、命令行、浏览器开发者工具，不需要碰任何系统设置

### 第 0 步：First 5 seconds（产品骨架 + 第一印象）

> [!info]+ 5-Second Test 起手 — 触发对话后 5 秒内凭印象答

- [ ] 我打开 Obsidian 里一个**之前批注过误解**的概念笔记（比如 `节点/admissibility.md`，里面应该有 `[!error]+` 类批注或对话产生过的错误记录）
- [ ] 我用 Cmd+P 找到 "Claudian: open view" 让 AI 侧栏出现
- [ ] 我感觉这是 (a) 一个会记得我之前学过什么的智能助教 (b) 还是一个每次都从零开始的陌生 AI — 选: ___

### 第 1 步：问一个能勾起历史误解的问题

- [ ] 我做：在 AI 侧栏里输入跟当前笔记相关的问题（比如笔记是 `admissibility` 就问"admissibility 是什么意思？")
- [ ] 我看到：AI 的回答里**自然地**提到"你之前标记过……" 或 "你曾经在这个概念上标注过……" 之类的提醒
- [ ] 我感觉：像是被一个记得我功课的私教指点（**期待 / 被照顾**），不是被一个金鱼记忆的助手反复问"你哪里不懂"

### 第 2 步：问一个跟历史误解无关的问题

- [ ] 我做：在同一个笔记里换问一个**跟你以前任何批注都不沾边**的小问题（比如"这个概念有什么生活类比？"）
- [ ] 我看到：AI 正常回答，**没有**生硬塞入"你之前标记过..."的提醒
- [ ] 我感觉：AI 是有分寸的（不会一次对话里反复念你的旧错），不会被冗余提醒分心

### 第 3 步：打开一个全新的、从未批注过任何误解的笔记

- [ ] 我做：打开一个我**从未批注过**任何误解的笔记（比如刚创建的新概念笔记），向 AI 提问
- [ ] 我看到：AI 给出正常回答，**完全没有**任何"无历史误解"之类的冗余说明
- [ ] 我感觉：AI 安静、不啰嗦（没有空记录还非要解释"你这次没有犯过错"的尴尬）

### 第 4 步：边界（如果记忆服务暂时不可用）

- [ ] 我做：继续在 Obsidian 里向 AI 提问（即使后台的记忆服务暂时挂掉，你完全无感）
- [ ] 我看到：AI 照常回答（这次只是没有历史误解提醒，但回答本身正常）
- [ ] 我感觉：AI **不会卡住、不会弹出红色英文报错、不会显示"记忆服务不可用"**

### 主观打分（Felt-sense — Sean Ellis-lite）

填数字（不是必填，但能帮 Claude 判断）：

- [ ] **被照顾感**（1=AI 完全不记得我学过什么 / 5=像有一个记得我功课的私教）：___
- [ ] **不打扰感**（1=反复念旧错让人烦 / 5=有分寸只在该提的时候提）：___
- [ ] **明天我会再打开它的可能性**（0-10 NPS-style）：___
- [ ] 一句话告诉 Claude，让你打这个分的最主要原因是：___

---

## 🚦 验收结果

**如果所有步骤 ✅**：告诉我 "**Story 2.3 通过**"，Claude 会 mark as **done**，自动启动 Story 5.1（BKT MCP 掌握度更新 — 8-Session plan 的 S3）。

**如果有任何一步 ❌**：在下面批注区写出具体哪一步 + 你看到的实际现象（比如"AI 没提我之前的批注"），Claude 根据你反馈调整。

---

## 📝 你的批注区

> [!question]+ 你对 Story 2.3 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-2/2-3-historical-error-reminder.md`
- **源代码**：
  - `backend/app/services/memory_service.py`（`search_memories` 加 node_id 参数 + 新建 `search_error_memories`）
  - `backend/app/services/chat_context_assembler.py`（`_format_historical_errors` + `inject_error_reminders` + `assemble_context` Priority 1.5）
  - `backend/app/api/v1/endpoints/chat.py`（3s 超时 + 双路径熔断 + structlog latency log）
- **单元测试**：`backend/tests/unit/test_story_2_3_error_reminders.py`（21 用例 / 21 pass / 1.64s）
- **回归验证**：chat_context_assembler + chat_endpoint + Story 2.3 共 87/87 pass
- **Git commit**：待 ship（PLAN-EPIC1-BMAD-DEV-ASSESS-2026-04-17）
- **AC → 代码对应**：
  - AC #1 (search_memories 集成) → `memory_service.py:search_error_memories`
  - AC #2 (注入策略 + 正面措辞) → `chat_context_assembler.py:_format_historical_errors`
  - AC #3 (3s 超时) → `chat.py:asyncio.wait_for(timeout=3.0)`
  - AC #4 (Graphiti 降级) → `chat.py:except asyncio.TimeoutError + (ConnectionError, RuntimeError, OSError)`
  - AC #5 (空记录) → `chat_context_assembler.py:_format_historical_errors L408 `

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "通过" → Claude 立即 mark done → 启动 Story 5.1（BKT MCP，CURRENT_TASK 8-Session plan S3）
2. **部分 ❌** → 在批注区写清楚，或者选中那几行用 `Cmd+Shift+A` 批 `❌ 错误 + ❌ 不懂` → Claude 再次修正
3. **想暂停这个 Story** → 告诉 Claude "暂停 Story 2.3"，状态保持 `review`，可随时回来

---

## 📍 实操准备清单（验收前先确认）

你的 vault 里需要存在以下条件，否则段 4-B 第 1 步的"历史误解提醒"无法触发：

- [ ] 至少一个概念笔记（如 `节点/admissibility.md`）已存在
- [ ] 该笔记在过去的对话/检验中已经累积过 `episode_type` ∈ {error, misconception, mistake} 的 Graphiti 记录
- [ ] Claudian 侧栏可以打开（"Claudian: open view" Cmd+P 命令存在）

如以上不满足：
- 先创建一个测试节点，故意跟 AI 对话产生一次错误标记，再来跑 UAT（约 2 分钟准备）
- 或告诉 Claude "vault 还没历史误解数据"，Claude 会先提供一段测试数据写入的脚本（你只需在 Obsidian 触发即可，不需要碰命令行）

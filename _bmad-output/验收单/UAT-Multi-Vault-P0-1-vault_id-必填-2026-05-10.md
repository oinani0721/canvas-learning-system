---
story: "Multi-Vault-P0-1"
title: "enrich-context-vault-id-required"
status: "review"
version: "1.0"
date: "2026-05-10"
developer: "Claude Code (Opus 4.7 1M context)"
commit: "460377c"
---

# 多 Vault P0-1 — enrich-context vault_id 必填验收单（给你看的版本）

> [!info]+ 这是什么
> 你之前反馈："Canvas learning system 会用到很多其他不同的 vault"。诊断发现：5 vault 共存时**最致命的串库点**是 Cmd+Shift+E/Q 调 backend 时不传 vault_id，会把 vault A 的笔记写到 vault B 的数据库。这次修复让 vault_id **必填且自动绑定每次请求**，5 vault 并发不互相串库。
> 这份文档只列你能看到、点击、感觉到的行为。

---

## 🎯 这个修复要做到什么

**以后你有 5 个 Obsidian vault（cs_61b / 数学 / 物理 / 算法 / 线性代数），每个 vault 的 AI 对话只看到自己 vault 的笔记，不会拿到隔壁 vault 的内容。**

---

## 📖 用户故事（你的视角）

**作为** 同时学多门课的学生（CS 61B + 数学 + 物理 ...），
**我想** 在 vault A 按 Cmd+Shift+E 提问时，AI 只用 vault A 里的笔记答；切到 vault B 后，AI 只用 vault B 里的笔记答，
**以便** 不会出现"我在数学 vault 问极限，AI 拿 CS 61B 的递归笔记答"这种串库灾难。

---

## 🖥️ 你会看到的交互（一步一步）

```
场景 A — 单 vault 内（你日常 90% 时间）：
1. 我在 vault cs_61b 里按 Cmd+Shift+E
       ↓
2. AI 回答只引用 vault cs_61b 的笔记（[[节点/recursion]]、[[raw/CS61B/lecture_05]]）
       ↓
3. 我不会看到 [[节点/极限]]、[[raw/数学/lecture_01]] 这种隔壁 vault 的笔记

场景 B — 切 vault 后（你切到第 2 个 vault）：
1. 我用 File → Open Vault... → 选 "数学"
       ↓
2. Obsidian 切到 vault "数学" → plugin 自动识别新 vault
       ↓
3. 我按 Cmd+Shift+E 提问
       ↓
4. AI 回答只引用 vault 数学的笔记，不再含 CS 61B 的内容
```

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现 `Pydantic` / `ContextVar` / `sanitize` / `asyncio.gather` / `pytest` 等技术词不算 bug，是 Claude 应该处理的。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | MV-1 `EnrichContextRequest.vault_id: str = Field(..., min_length=1)` 必填字段已加（参考 PostTurnExtractRequest 已建立的契约） | ✅ `test_vault_id_missing_rejected_422` passed |
| 2 | MV-1 vault_id 缺失时 backend 返回 422（plugin 旧版本不能 silent corruption） | ✅ `test_vault_id_missing_rejected_422` + `test_vault_id_empty_string_rejected_422` passed |
| 3 | MV-1 handler 调用链 `sanitize_vault_id → build_vault_group_id → set_current_subject_id` 全链路注入 ContextVar | ✅ `test_vault_id_provided_triggers_context_var_injection` passed |
| 4 | MV-1 中文 vault_id（如 "数学101"）不被 sanitize 坍缩 default（多中文 vault 数据泄漏点已根治） | ✅ `test_chinese_vault_id_not_collapsed_to_default` passed |
| 5 | MV-1 路径遍历 `../etc/passwd` 被 sanitize 净化 | ✅ `test_vault_id_with_special_chars_sanitized` passed |
| 6 | **MV-3 核心** asyncio.gather 并发 2 vault 跑 ContextVar 各自独立（防 5 vault 并发串库） | ✅ `test_concurrent_two_vaults_dont_share_context_var` passed |
| 7 | MV-2 plugin main.ts `handleChatWithContext` payload 加 `vault_id: inferVaultId(this.app.vault.getName())` | ✅ TypeScript tsc --noEmit 0 新 error |
| 8 | MV-2 plugin `handleStudyQuestion` payload 同步加 vault_id（Cmd+Shift+Q 也防串库） | ✅ tsc --noEmit + grep 确认 |
| 9 | 全套件 65 测试 0 regression（8 新 vault isolation + 19 chat endpoint + 8 sq + 17 rag-p0 + 13 supp） | ✅ `pytest tests/unit/test_enrich_context_vault_isolation.py tests/unit/test_chat_endpoint.py tests/unit/test_study_question_deep_mode.py` 65 passed |
| 10 | Pre-push A11 regression suite 19 passed / 13 skipped | ✅ commit 460377c backup + origin push 全通过 |

---

## 👤 你来验（产品使用体验 — 5 步，10 分钟内全在 Obsidian 里完成）

> [!warning]+ 这段的硬规矩
> ✅ 句型："**我做 X → 我看到 Y → 我感觉 Z**"
> ✅ 工具白名单：Obsidian 主界面（File 菜单 / 命令面板 / 编辑器 / Claudian 侧栏）
> ⛔ 不需要打开终端 / Docker — 全部 Obsidian 内完成
> ⛔ 不需要懂 vault_id / ContextVar — 那是 Claude 该处理的

### 第 0 步：First 5 seconds（plugin 重新加载后新 payload 生效）

> Plugin 这次改动加了 vault_id 字段到 backend payload，需要 Reload 让新 main.js 生效。

- [ ] 我在 Obsidian 按 **Cmd+P** 打开命令面板
- [ ] 我输入 "Reload app without saving" → 回车
- [ ] 5 秒内 Obsidian 重新加载完成（没有红色错误弹窗）
- [ ] 我感觉：(a) 一切正常 (b) plugin 报错 — 选: ___

### 第 1 步：单 vault 场景 — Cmd+Shift+E 正常工作

- [ ] 我在当前 vault 打开任意 `节点/<concept>.md`
- [ ] 我按 **Cmd+Shift+E** → 输入"什么是 X"→ Enter
- [ ] 我看到右上角 Notice 含 "已组装 backend RAG 上下文..."（不是红色 422 错误）
- [ ] 我感觉：vault_id 字段对我**完全透明**，按以前一样用

### 第 2 步：切 vault 场景 — File → Open Vault

> 这一步需要你有第 2 个 vault。如果你只有 1 个 vault，可以跳到第 4 步。

- [ ] 我点 **File** 菜单 → **Open Vault...**
- [ ] 我选另一个 vault（或新建一个用于测试的空 vault）
- [ ] Obsidian 切到新 vault → 我在新 vault 创建/打开任意节点
- [ ] 我按 **Cmd+Shift+E** → 输入"什么是 X"→ Enter
- [ ] 我看到右上角 Notice 正常弹出（不是 422 错误）
- [ ] 我感觉：vault 切换对 plugin 透明，hotkey 在新 vault 也工作

### 第 3 步：核心场景 — vault A vs vault B 内容隔离

> 这是最关键的一步：验证不串库。

- [ ] 我在 vault A 按 Cmd+Shift+E 问"什么是 [vault A 的某个核心概念]"
- [ ] 我看到 Claude 回答末尾的"📚 相关学习材料"列表里**全是 vault A 的笔记路径**
- [ ] 我切到 vault B（File → Open Vault）
- [ ] 我在 vault B 按 Cmd+Shift+E 问"什么是 [vault A 的概念]"（故意问 vault A 的概念）
- [ ] 我看到 Claude 回答**说"vault 内没找到 X"** 或者 **只引用 vault B 的笔记**
- [ ] **关键**：Claude **不应该** 跑去拿 vault A 的笔记答（如果出现 = ❌ 串库未根治）
- [ ] 我感觉：(a) 隔离干净 (b) 还能看到 vault A 内容 — 选: ___

### 第 4 步：中文 vault 名场景（如果你打算用中文命名 vault）

> 之前 bug：中文 vault 名会被 sanitize 坍缩成 "default"，两个中文 vault 共用一个数据库 → 数据泄漏。

- [ ] 我用 File → Open Vault... 打开/创建一个**中文命名**的 vault（如 "数学" / "线性代数"）
- [ ] 我在这个中文 vault 按 Cmd+Shift+E 提问
- [ ] 我看到 Notice 弹出正常（不是 422 错误）
- [ ] 我感觉：中文 vault 名也正常工作，没有特殊处理负担

### 第 5 步：边界 — 旧 plugin（如果你不 reload 直接用）

> 这一步演示"plugin 旧版本不 reload 直接用会怎样"。

- [ ] 假设你忘了 reload Obsidian（或者用了旧的 main.js）
- [ ] 你按 Cmd+Shift+E 提问
- [ ] **预期行为**：右上角 Notice 弹出 "❌ enrich-context 失败: vault_id field required（422）" — 而不是悄悄拿错 vault 的笔记答
- [ ] **解决**：用 Cmd+P → "Reload app without saving"
- [ ] 我感觉：失败时有明确错误提示，不会偷偷出错（"failing loudly is better than silent corruption"）

### 主观打分（Felt-sense）

- [ ] **vault 切换透明度**（1=每次切都要重设 / 5=完全透明）：___
- [ ] **隔离效果**（1=明显串库 / 5=干净到位）：___
- [ ] **中文 vault 支持**（5=完全正常 / 1=各种奇怪问题）：___
- [ ] **未来加更多 vault 信心**（0-10）：___
- [ ] 一句话：你打这些分的最主要原因是 ___

---

## 🚦 验收结果

**所有步骤 ✅** → 告诉我 "**多 Vault P0-1 通过**" → Claude mark as **done**，可以排期 P0-2（剩余 34 个 endpoint 全局中间件，12h）。

**第 3 步看到 vault A 内容出现在 vault B 答案** → ❌ **P0 串库未根治**。在批注区记录，Claude 排查（很可能是 hook endpoint `/rag/enrich-hook` 或其他 34 endpoint 之一漏改）。

**第 4 步中文 vault 报错** → 在批注区记录中文 vault 名，Claude 检查 sanitize_vault_id 是否回归。

---

## 📝 你的批注区

> [!question]+ 你对多 Vault P0-1 的批注
>
> 用 Cmd+Shift+A 在上面任何一段批注 `❌ 错误` / `❓ 提问` / `💡 建议`。
>
> （空）

### 已知的已批注问题（历史追溯）

无 — 首次 ship。

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **诊断报告**：3 个 parallel agent 报告 — 锁定根因为"39 endpoints 仅 5/39 真注入 vault_id（13% 覆盖率），其余 34 个用 DEFAULT_GROUP_ID='vault:default' 兜底导致 5 vault 物理共用一个 group"
- **设计参考**：
  - `_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md` — 5 共存翻车点完整诊断
  - PostTurnExtractRequest (Story 2.5.Y AC #2) — 已建立的 vault_id 必填契约
- **修改文件**：
  - `backend/app/api/v1/endpoints/chat.py` — EnrichContextRequest.vault_id 必填 + handler 入口注入 ContextVar
  - `frontend/obsidian-plugin/src/main.ts` — handleChatWithContext / handleStudyQuestion 两处 payload 加 vault_id
- **单元测试**：`backend/tests/unit/test_enrich_context_vault_isolation.py` — 8 用例 / 8 passed
  - 重点测试：`test_concurrent_two_vaults_dont_share_context_var`（asyncio.gather 并发隔离）
- **Git commit**：`460377c` — `fix(multi-vault-p0-1): mv1 vault_id 必填 + contextvar + mv2 plugin payload + mv3 8 tests`
- **后续工作**：P0-2（12h）需要补剩余 34 endpoint 的 vault_id 中间件，避免 hook / agents/dialog / review / exam 等 endpoint 串库

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "多 Vault P0-1 通过" → Claude mark done → 排期 P0-2（剩余 34 endpoint 中间件）
2. **第 3 步❌（看到串库）** → 在批注区记录哪个 vault 串到哪个 vault，Claude grep 找漏改 endpoint（最可能是 `/api/v1/agents/dialog` 或 `/api/v1/review/*`）
3. **想暂停验证** → 告诉 Claude "暂停多 Vault P0-1 UAT"

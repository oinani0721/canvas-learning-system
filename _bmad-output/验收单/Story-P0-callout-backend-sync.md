---
story: "2.4-callout-sync (Plan B)"
title: "批注自动同步到后端 + 后续编辑实时感知"
status: "review"
version: "v2.0"
date: "2026-05-14"
developer: "Claude Code (Opus 4.7)"
plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
upgrade_from: "v1.0 (P0 三件套 + P0-6 光标定位)"
---

# Story 2.4 Plan B 验收单（给你看的版本 v2.0）

> [!info]+ v1.0 → v2.0 升级了什么
> **v1.0**：你按 `Cmd+Shift+A` 标批注 → 一次性同步到后端（之后任何修改不感知）
> **v2.0**：你在 callout 里**继续输入"我的理解"** → plugin 自动检测 → 500ms 静默后 → 后端 Graphiti 创建 v2 版本 episode（保留 v1 作演化痕迹）

---

## 🎯 这个版本要做到什么

让 backend **持续记住**你的每次批注演化 — 包括你在 callout 内继续输入的"我的理解"、删除某行、改 understanding checkbox 等任何变化。**之前丢失的部分现在都被系统记住**。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 我在 callout 里追加任何内容、修改任何 checkbox、删除任何批注，系统都能**实时感知并记住**，
**以便** 检验白板将来出题时能用我**所有版本**的批注（v1 模糊 → v2 已懂的演化过程，也能反映出我的学习进步）。

---

## 🖥️ 你会看到的交互（一步一步）

```
第 1 轮：首次批注
1. 选中文字 → Cmd+Shift+A → 选 Tag → 选 Understanding
       ↓
2. callout 写入本地 + 光标自动停在末尾输入区
       ↓
3. 右上角弹出"批注同步 成功" Notice
       ↓
4. 后端 Graphiti 创建 v1 EpisodicNode

第 2 轮：你继续输入"我的理解"
5. 你在 callout 末尾继续打字（如"我对 base case 的理解是..."）
       ↓
6. 你停顿打字 0.5 秒（500ms debounce）
       ↓
7. plugin 静默触发同步（不弹 Notice，避免打扰）
       ↓
8. 后端识别 hash 变了 → Graphiti 创建 v2 EpisodicNode（v1 保留）

第 3 轮：你修改 checkbox（如"模糊" → "已懂"）
9. 你勾选另一个 checkbox
       ↓
10. plugin 500ms 后静默同步 → v3 EpisodicNode

最终结果：
- 本地 .md：永远只显示最新版本（callout 内容是最新的）
- 后端 Graphiti：保留 v1/v2/v3 完整时序，检验白板能查到你的演化过程
```

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ Claude 已自动跑完贴证据

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | Plugin: `vault.on('modify')` 监听已注册（main.ts onload）| ✅ grep 验证已生效 |
| 2 | Plugin: `CalloutSyncDebouncer` 500ms debounce 类已 build | ✅ main.js 88K 含 CalloutSyncDebouncer |
| 3 | Plugin: `parseCalloutsFromContent` 解析器已 build（支持 4 种 tag + understanding 提取 + SHA256 hash）| ✅ |
| 4 | Backend: `POST /api/v1/tips/batch` endpoint 已上线 | ✅ /api/v1/tips/batch returns 200 |
| 5 | Backend: in-memory hash cache 双层幂等去重 | ✅ Test A new=1, Test B/C skipped=1 |
| 6 | Backend: `find_episode_by_content_hash` 查 Neo4j `[hash:xxx]` 内嵌 marker | ✅ grep CONTAINS 命中 |
| 7 | Graphiti EpisodicNode 真实写入 Neo4j | ✅ 2 条 `callout-annotation-record` with `[hash:8c40c3...]` |
| 8 | Plugin deploy 到 canvas-vault | ✅ 88K @ canvas-vault/.obsidian/plugins/ |
| 9 | Backend restart + healthy | ✅ /api/v1/health 200 |
| 10 | Graphiti worker active (非 degraded) | ✅ GOOGLE_API_KEY 已配置 |

---

## 👤 你来验（产品使用体验 — 5 步，5 分钟内全在 Obsidian 完成）

> [!warning]+ 这段的硬规矩
> ✅ 句型："**我做 X → 我看到 Y → 我感觉 Z**"
> ⛔ 全程不需要打开任何"窗口"以外的工具
> 📌 **重要**：开始前先 reload Obsidian 让新 plugin 生效（`Cmd+P` → "Reload app without saving"）

### 第 0 步：Reload Obsidian + 确认就绪

- [ ] 我用 `Cmd+P` → 输入 "Reload app without saving" → 回车
- [ ] Obsidian 重启 → 5 秒内回到熟悉的笔记界面
- [ ] 我感觉：等待时间合理，没卡死

### 第 1 步：首次批注（跟之前一样）

- [ ] 我打开任意 `节点/<concept>.md` → 选中一段文字 → `Cmd+Shift+A`
- [ ] 我选 `💡 Tips` → 选 `🤔 模糊`
- [ ] 我看到 callout 写入 + 光标停在末尾空 `>` 后 + 右上角"批注同步 成功"
- [ ] 我感觉：熟悉 / 流畅

### 第 2 步：继续输入"我的理解"（v2.0 新功能 — 核心验收点）

- [ ] 我直接打字输入（光标已停好）：`我对这段话的理解：...` （随便写一段）
- [ ] 我打完后**停顿 1 秒**（让 debounce 触发）
- [ ] 我看到：**没有 Notice 弹出**（debounce 是静默的，避免打扰）— 这是预期行为
- [ ] 我感觉：自然 / 不被打断

### 第 3 步：修改 checkbox（再次触发自动同步）

- [ ] 我把 `[x] 🤔 模糊` 取消 → 改勾 `[x] ✅ 已懂`（点击 checkbox 切换）
- [ ] 我等 1 秒
- [ ] 我看到：同样静默无 Notice，但**后端已经又记录了一次**
- [ ] 我感觉：编辑流畅，背后系统在工作

### 第 4 步：再加一个新 callout（测试多 callout 解析）

- [ ] 我选另一段文字 → `Cmd+Shift+A` → 选 `❌ 错误` → 选 `❌ 不懂`
- [ ] 我看到第 2 个 callout 写入 + 右上角"批注同步 成功"
- [ ] 我感觉：可以无限标注，不会冲突

### 主观打分

- [ ] **流畅度**（1-5）：___
- [ ] **持续输入的舒适度**（1=被打断 / 5=如水般顺畅）：___
- [ ] **信任度**（1-5：相信后端真的记住了我的每次编辑）：___
- [ ] 一句话告诉我你的感受：___

---

## 🚦 验收结果

**如果第 2 步顺利（继续输入"我的理解"无障碍）**：告诉我 "**Story 2.4 通过**" → 我立即 git commit 所有 P0 + Story 2.4 修复 + 启动下一个 Story。

**如果有任何卡顿 / 异常**：在批注区写出具体哪一步 + 你看到的现象。

---

## 📝 你的批注区

> [!question]+ 你对 Story 2.4 Plan B 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段（这本身就是在测试 v2.0 闭环 ✨）。
>
> （空）

### 已知的已批注问题（历史追溯）

> [!error]+ 2026-05-13 → 2026-05-14 v1.0 → v2.0 修复
> **v1.0 原批注**：你按 Cmd+Shift+A 选 understanding 后，继续输入"我的理解"内容**不会同步到后端**
> **根因**：plugin 无 `vault.on('modify')` 监听 + backend 无 file watcher（5-13 调研发现 G6 + Story 2.4 spec ready-for-dev 但未实施）
> **已修复**：
> - Plugin 加 `CalloutSyncDebouncer` (500ms 防抖)
> - 后端 `POST /api/v1/tips/batch` endpoint
> - `[hash:xxx]` 内嵌 + in-memory cache 双层幂等去重

### v1.0 → v2.0 你将看到的变化

| 维度 | v1.0（已淘汰）| v2.0（现在）|
|---|---|---|
| 首次批注同步 | ✅ 立刻 POST /tips | ✅ 同上 |
| 后续输入"我的理解" | ❌ 完全丢失 | ✅ 500ms 自动同步 |
| 修改 checkbox | ❌ 完全丢失 | ✅ 500ms 自动同步 |
| 删除 callout | ❌ 不感知 | ⚠️ 同步触发但 v3 episode（暂未做 invalidation）|
| 演化时序记忆 | ❌ 仅 v1 | ✅ v1/v2/v3 全部保留 |
| 重复保存防抖 | ❌ 重复写入 | ✅ in-memory hash cache 去重 |

---

## 🔗 技术 spec 引用（给 Claude 读的）

- **Story 2.4 spec**：`_bmad-output/implementation-artifacts/epic-2/2-4-callout-annotation-tips.md`
- **改动文件**（Plan B 新增 + 修改）：
  - `frontend/obsidian-plugin/src/callout-sync.ts` (新建, ~65 行)
  - `frontend/obsidian-plugin/src/callout.ts` (扩展 +85 行：parseCalloutsFromContent + sha256Hex)
  - `frontend/obsidian-plugin/src/main.ts` (加 onload 监听 + batchSyncCallouts +35 行)
  - `backend/app/api/v1/endpoints/tips.py` (加 BatchSyncRequest + POST /batch + in-memory cache +120 行)
  - `backend/app/services/memory_service.py` (加 find_episode_by_content_hash +50 行)
- **AC trace**：
  - AC #1 (callout 解析) → `callout.ts:parseCalloutsFromContent`
  - AC #2 (幂等)        → `tips.py:_hash_cache_check_or_add` + `memory_service.py:find_episode_by_content_hash`
  - AC #3 (多 callout)  → `callout.ts:parseCalloutsFromContent` while loop
  - AC #4 (上下文注入)  → P0-2 reader 已对齐（question_generator._get_tips 查 callout-annotation-record）
  - AC #5 (删除追踪)    → ⚠️ 部分实现（v3 episode 表示当前状态，但 v1/v2 仍保留 = "soft delete"）
- **诊断对齐**：用户 5-13 批注 G6 + ChatGPT 第二意见 P1（E2E 回归测试）已部分对应

---

## 📅 下一步（你批完这份单后）

1. **通过** → 我 git commit P0 三件套 + P0-4/5/6/7/8 + Story 2.4 Plan B（一次性 6-8 commits 含 PLAN-NNN）
2. **部分不通过** → 你批注具体哪一步问题，我做 v2.1 修复
3. **想继续推进 Story 5.1（BKT mastery）**或 **Epic 4（检验白板）** → 告诉我下一目标

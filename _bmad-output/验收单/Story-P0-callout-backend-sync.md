---
story: "2.4-plan-a-frontmatter-tips-sync"
title: "批注自动同步到 frontmatter tips[] (Plan A — 文件即真相源)"
status: "review"
version: "v3.0"
date: "2026-05-14"
developer: "Claude Code (Opus 4.7)"
plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
upgrade_from: "v2.0 (Plan B — plugin push + Graphiti append-only, 已 deprecated)"
decision_source: "4 方对抗审查共识 (Canvas / Claude / ChatGPT-1 / ChatGPT-2) → 回退 Plan A"
postmortem: "_bmad-output/research/2026-05-14-plan-b-postmortem.md"
---

# Story 2.4 Plan A 验收单 v3.0

> [!info]+ v2.0 → v3.0 升级了什么
> **v2.0 (Plan B, deprecated)**: plugin debounce + POST /api/v1/tips/batch → Graphiti 写入 → Neo4j EpisodicNode
> **v3.0 (Plan A)**: plugin metadataCache.on('changed') → 自动写 frontmatter tips[] 到本地 .md → backend 读 frontmatter
>
> **关键改变**：批注现在写到**你能看见**的 YAML 头里，不是后端黑盒。删除天然支持，离线 100% 安全，无 Gemini API 成本。

---

## 🎯 这个版本要做到什么

让你 `Cmd+Shift+A` 写的 callout **自动同步到 .md 文件顶部的 properties 区**（frontmatter `tips[]`），你能看见、能编辑、能删除。后端读这个 properties 区给检验白板出题用。

---

## 📖 用户故事（你的视角）

**作为** 学习者，
**我想** 我每次按 `Cmd+Shift+A` 写的批注自动出现在文件 properties 列表里，
**以便** 我能**看到自己的批注累积**（不是黑盒），删掉一条批注也能立刻在 properties 中消失，检验白板能用我所有批注出题。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 你打开任意 节点/<concept>.md
       ↓
2. 选中一段文字 → Cmd+Shift+A → 选 tag → 选 understanding
       ↓
3. callout 写入本地 (跟之前一样)
       ↓
4. 等 1 秒后:
   - 文件 properties 面板自动出现 tips 数组 (你能看见)
   - 数组每项含 text / tag / understanding / added_at
       ↓
5. 你在 callout 里继续输入"我的理解"
       ↓
6. 等 1 秒后:
   - properties 里的对应 tips 条目自动更新
   - added_at 保持原值 (首次添加时间, 不被覆盖)
       ↓
7. 删除整个 callout
       ↓
8. 等 1 秒后:
   - properties 里的对应 tips 条目自动消失 ✅
```

---

## 🤖 Claude 已代验

> [!success]+ 这一段是 Claude 自动跑完贴证据

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | Plan B 入口禁用 — plugin 0 处调 saveCalloutToBackend | ✅ grep main.js 命中 0 |
| 2 | Plan B endpoint 拒绝 — /api/v1/tips/batch 返回 410 Gone | ✅ 代码 add deprecated marker + raise |
| 3 | Plan A FrontmatterTipsSync class 已 build (115 行 TS) | ✅ main.js 含 14 处 marker |
| 4 | callout parser 协议修复 — 兼容 [!tip]+/- 单复数 | ✅ regex `(tip|tips|...)` |
| 5 | 防无限循环 — tipsEqual 比对内容相同则跳过 | ✅ 代码 buildNewTips + tipsEqual |
| 6 | added_at 保留 — 旧 tip 沿用 added_at, 新 tip 写当前时间 | ✅ buildNewTips 实现 |
| 7 | backend learning_context_service 加第 3 source 读 frontmatter | ✅ yaml.safe_load + 3 路 fallback |
| 8 | Python syntax check passed | ✅ ast.parse OK |
| 9 | Plugin npm run build 通过 | ✅ main.js 88K |
| 10 | main.js 部署到 canvas-vault | ✅ 88K @ canvas-vault/.obsidian/plugins/ |
| 11 | Postmortem 决策文档已 ship | ✅ research/2026-05-14-plan-b-postmortem.md (212 行) |

---

## 👤 你来验 (产品使用体验)

> [!warning]+ 这段的硬规矩
> 工具白名单: Obsidian 主界面 / Properties 面板 (笔记右上 ... → Properties)
> 句型: "我做 X → 我看到 Y → 我感觉 Z"
> 重要: 开始前先 reload Obsidian (Cmd+P → "Reload app without saving")

### 第 0 步: Reload Obsidian + 确认就绪

- [ ] 我用 Cmd+P → 输入 "Reload app without saving" → 回车
- [ ] Obsidian 重启 → 5 秒内回到熟悉的界面
- [ ] 我感觉: 等待时间合理

### 第 1 步: 本地批注 (确认 Plan A 没破坏 Cmd+Shift+A)

- [ ] 我打开 节点/<concept>.md → 选中一段文字 → Cmd+Shift+A
- [ ] 我选 💡 Tips → 选 🤔 模糊
- [ ] 我看到 callout 写入本地, 光标停在 "✍️ 我的理解:" 后
- [ ] 我感觉熟悉, 没有"批注同步成功" Notice (这是预期 — Plan A 不调后端不弹通知)

### 第 2 步: 看 properties 自动出现 tips[] (Plan A 核心验收点)

- [ ] 我点笔记右上角 "..." → 选 "Properties" (或顶部直接看 YAML 头)
- [ ] 我等 1 秒
- [ ] 我看到 properties 里**自动出现 tips 数组字段**, 含我刚才标的批注 (text/tag/understanding/added_at)
- [ ] 我感觉: 透明 / 信任 / 数据在我看得见的地方

### 第 3 步: 继续输入"我的理解" + 看 properties 更新

- [ ] 我在 callout 末尾继续打字 (如 "我对这段话还是不太懂...")
- [ ] 我停 1 秒
- [ ] 我看到 properties 里的对应 tips 条目自动更新, 但**首次添加时间 added_at 保持不变**
- [ ] 我感觉: 系统聪明 / 记住了我的批注演化

### 第 4 步: 删除 callout + 看 tips[] 自动移除 (Plan B 做不到的)

- [ ] 我选中整个 callout 块 → 删除
- [ ] 我等 1 秒
- [ ] 我看到 properties 里**对应 tips 条目消失** (这是 Plan B 完全做不到的, Plan A 天然支持)
- [ ] 我感觉: 删得干净 / 隐私可控

### 第 5 步: 离线测试 (Plan A 优势)

- [ ] 我关掉 wifi (或 docker desktop)
- [ ] 我写一条新 callout
- [ ] 我看到 properties 仍然自动出现 tips (因为不调后端)
- [ ] 我感觉: 离线安全, 数据不依赖网络

### 主观打分

- [ ] **流畅度** (1-5): ___
- [ ] **透明度** (1=黑盒 / 5=完全可见): ___
- [ ] **信任度** (1-5: 相信数据真在文件里): ___
- [ ] 一句话告诉 Claude 你的感受: ___

---

## 🚦 验收结果

**如果第 2/3/4 步都 ✅**: 告诉我 "**Story 2.4 通过**" → 我 mark done + 启动下一个 Story (如 Epic 4 检验白板出题)。

**如果 properties 没出现 tips[]**: 在批注区写明哪一步 + 截图。

---

## 📝 你的批注区

> [!question]+ 你对 Story 2.4 Plan A 的批注
>
> (空)

### 已知的已批注问题 (历史追溯)

> [!error]+ 2026-05-14 v2.0 → v3.0 重大方向修正 (4 方对抗审查共识)
> **v2.0 原批注**: Plan B 实现端到端跑通 (用户实测一次输入 8 sync + 3 EpisodicNode)
> **根因**: 4 方对抗审查 (Canvas 自评 + Claude 5-Agent + ChatGPT-1 + ChatGPT-2) 一致建议回退 Plan A:
>   - Plan B 把 Story 2.4 简单问题复杂化 (plugin debounce + hash 染色 + append-only episodic + Graphiti projection 缺失 + tombstone design)
>   - ChatGPT 找到 7 个 Canvas 未发现盲点 (协议悄改 / 消费者各读各 / Notice 矛盾 / LRU 假象 / cosmetic edit / basename 当 ID / 违反 Graphiti 顺序约束)
>   - 真正的 B1 是 ghost field — Graphiti EpisodicNode 不存 node_id 字段, reader 查询永远 miss
>   - Plan A 完美解决 Story 2.4 5 件事 (写/取/读/删/不丢)
> **已修复 (v3.0)**:
>   - Plan B 入口 disable (plugin saveCalloutToBackend 调用 0 + /tips/batch endpoint 返回 410 Gone)
>   - Plan A 新建 FrontmatterTipsSync class (metadataCache.on('changed') → processFrontMatter)
>   - parser 协议修复 (兼容 [!tip]+/-)
>   - backend learning_context_service 加第 3 source 读 frontmatter
>   - Plan B 代码保留 git history (commit 3d10a02), 未来 Plan C 重启时复用
> **决策文档**: `_bmad-output/research/2026-05-14-plan-b-postmortem.md`

---

## 🔗 技术 spec 参考

- **Story 2.4 spec**: `_bmad-output/implementation-artifacts/epic-2/2-4-callout-annotation-tips.md` (Plan A 原 spec)
- **Postmortem**: `_bmad-output/research/2026-05-14-plan-b-postmortem.md`
- **改动文件 (Plan A v3.0)**:
  - `frontend/obsidian-plugin/src/frontmatter-tips-sync.ts` (新建 115 行)
  - `frontend/obsidian-plugin/src/callout.ts:60-66` (parser 协议修复 — 兼容 [!tip]+/-)
  - `frontend/obsidian-plugin/src/main.ts:95-115` (注册 metadataCache.on('changed'))
  - `backend/app/services/learning_context_service.py:200-250` (加第 3 source — 读 frontmatter)
- **Disable Plan B 改动**:
  - `frontend/obsidian-plugin/src/main.ts:106-119` (vault.on('modify') 注释掉)
  - `frontend/obsidian-plugin/src/main.ts:1994-2003` (saveCalloutToBackend 调用注释掉)
  - `backend/app/api/v1/endpoints/tips.py:300-318` (/batch endpoint 返回 410 Gone)
- **AC trace** (Story 2.4 spec AC #1-#5):
  - AC#1 (callout 解析) → `callout.ts:parseCalloutsFromContent` (兼容协议)
  - AC#2 (frontmatter 同步) → `frontmatter-tips-sync.ts:syncFile`
  - AC#3 (多 callout + [!tip]+/-) → `callout.ts:parseCalloutsFromContent` while loop + 协议修复
  - AC#4 (上下文注入) → `learning_context_service.py:_fetch_tips_and_errors` 第 3 source
  - AC#5 (删除追踪) → `frontmatter-tips-sync.ts:buildNewTips` 完全覆盖语义

---

## 📅 下一步

1. **通过** → 我 git commit Plan A 全套 + 启动下一个 Story (Epic 4 检验白板 / Story 5.1 BKT mastery)
2. **不通过** → 你批注具体哪一步问题, 我做 v3.1 修复
3. **想看 postmortem 决策文档** → 在 _bmad-output/research/ 打开

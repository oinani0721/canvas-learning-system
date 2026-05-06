---
type: uat-dashboard
date: "2026-05-01"
purpose: "整合所有 UAT 状态，避免重复验证"
generator: "Claude Code (Opus 4.7)"
---

# UAT 整合 Dashboard — 2026-05-01

> 你的诉求："不想重复验证"。本文档列出**已勾**项 + **应跳过**项 + **必须新测**项。
>
> **建议执行顺序**：从下方 🔥 必测最小集开始，约 30-40 分钟跑完全部新功能。

---

## 📊 各验收单状态总览

| 验收单 | 总步骤 | ✅ 已勾 | ⏳ 未勾 | 完成度 | 行动建议 |
|---|---|---|---|---|---|
| Story-1.16-批注-hotkey.md | 43 | **43** | 0 | **100%** ✅ | 无需操作（已 done）|
| Story-1.17-ai-linked-doc.md | 150 | 24 | 126 | 16% | 🔥 必测 v3.0 关键步骤（见下）|
| Story-1.19-configure-whiteboard.md | 126 | 20 | 106 | 16% | 🔥 必测 v4.0/v4.1 关键步骤 |
| Canvas-完整学习闭环-验收总流程.md | 68 | 0 | 68 | 0% | ⏳ 等单 Story 全过后再跑（跨 Story 联测）|

---

## ✅ Story 1.16 — 完全完成（不用动）

43/43 全勾，已 commit `2d20b49 feat(epic-1): story 1.16 ✅ done — 10-step UAT passed by user`。

---

## 📋 Story 1.17 已勾的 24 项（仍然有效，不用重测）

这些都是 v2.1 时期的**底层前置 + plugin 注册基础**，与版本无关，可继续作为已验证基础：

| 类别 | 已勾步骤 | 行号 |
|---|---|---|
| **环境**（4 项）| Cmd+P → reload app（让插件重读 main.js）| 375-378 |
| **测试笔记准备**（3 项）| 建 `wiki/canvases/math240/Fundamentals.md` 含 frontmatter | 383-385 |
| **Hotkey 绑定**（3 项）| Settings > Hotkeys 搜"AI 创建双链文档"= ⌘⇧D | 406-408 |
| **DevTools**（4 项）| Cmd+Opt+I → Console 清屏 | 416-419 |
| **编辑器就绪**（3 项）| 打开测试笔记 + Edit view 铅笔图标 + 光标进入正文 | 423-425 |
| **空选中防护**（5 项）| 不选中按 Cmd+Shift+D → Notice"请先选中文本"+ Claudian 不打开 | 429-433 |
| **选中文本**（2 项）| 鼠标 / Shift+Arrow 选中 + 高亮显示 | 439-443 |

→ **结论**：plugin 触发 + Hotkey + 选中防护**已经验证**。重新测 v3.0 时**可以直接跳过这些前置**，从"按 Cmd+Shift+D 后立即弹关系 modal"开始测。

---

## ⏭️ Story 1.17 应跳过的版本（已被 v3.0 替代）

这些版本的具体步骤**不用单独测**，因为 v3.0 hybrid 是它们的最优合集：

| 版本 | 时间 | 状态 | 为什么跳过 |
|---|---|---|---|
| v2.2（D4-1 toast + D4-2 重试）| 2026-04-30 | 被 v3.0 包含 | v3.0 plugin 阶段 1 自然实现 D4-1（不开 tab），retry notice 仍保留 |
| v2.4（关系类型 7 类 + 双写）| 2026-04-30 | 被 v3.0 包含 | v3 RelationTypeModal + 双写 callout/frontmatter 已迁移到 plugin 阶段 1 |
| v2.5（描述 modal + 三处落地）| 2026-04-30 | 被 v3.0 包含 | v3 DescriptionModal + 三处落地仍工作（plugin 直接处理 + Skill 仅做 prompt 注入） |
| v2.6（节点继承 source_board）| 2026-04-30 | 被 v3.0 包含 | v3 plugin 仍有 extractSourceBoardFromFrontmatter 逻辑 |

→ **跑 v3.0 UAT 时这些功能都会被自然覆盖**，不需要倒回去单独测。

---

## 🔥 Story 1.17 — 必测最小集（v4.0 全脚本，无 AI 阶段，约 5 分钟）

> 前置：**Cmd+Q 重启 Obsidian**（让 main.js v4.0 / 62480B 加载）
>
> ⚠ **v4.0 重大变化**（2026-05-01）：用户决策"派生 = 单独拉出来放新文档讨论，不需要 AI 生成正文"。
> v3 hybrid 阶段 2 砍掉，`ai-linked-doc-fill` Skill 删除。节点正文 = **选中文本 quote callout + 三段空白模板**，由你自己写或在 Claudian 节点级对话里讨论。
>
> 旧 v3 22 步 → v4.0 **6 步**（删 V3-9/10/11/12 异步阶段 2）。

### v4.0 必测 6 步

- [ ] **V3-1**：在 `节点/Characteristic-Equation-for-Eigenvalues.md`（已派生节点）选一段文字

> [!quote] 用户批注（2026-05-01）
> 这个节点目前是已有隶属的原白板，但是我这里拉出新节点的时候，却告诉我并没有找到隶属的白板。

> [!success]+ Round-1 回复（2026-05-01）— 双 bug 已修 + 立即解法
>
> **截图问题诊断**：你打开的是 `节点/Fundamentals.md`，frontmatter 只有 `type: concept`，**缺 `source_board` 字段**。v3 ai-linked-doc 派生时找不到归属白板 → 报错"未确定活动白板"。
>
> **根因 = 2 个 plugin bug**（已修，main.js 64183B → 65367B）：
>
> **Bug 1**：v4 `canvas:append-note-to-board` + `canvas:configure-whiteboard` 把笔记移到 `节点/` 时**没自动加 `source_board` frontmatter**。3 处 processFrontMatter callback 都缺这一行。修复：
>
> ```diff
>   if (!fm.type) fm.type = "concept";
>   if (typeof fm.subject === "string") delete fm.subject;
> + fm.source_board = `[[原白板/${boardName}]]`;
> + fm.created_from = "<append_note_to_board / configure_whiteboard_seed / configure_whiteboard_backlink_append>";
> ```
>
> **Bug 2**：v4.1 `executeAppendToBoard` 的 `skip` 模式直接 `return`，**完全跳过 frontmatter 处理 + 白板 ## Concepts 更新**。这意味着即使笔记已在 `节点/` 下（如你的 Fundamentals），用 append-note-to-board 选 skip 也没法补缺失的 source_board。
>
> **修复（v4.2）**：skip 模式语义重新定义：
> - 源**已在节点池**（如 `节点/Fundamentals.md`） + 选 skip → **就地补 frontmatter（含 source_board）+ 更新白板 ## Concepts**（不动文件）
> - 源**不在节点池** + 选 skip → 仍是"什么都不做"（保持原义）
>
> Notice 文案区分：
> - **move**：`✓ 笔记 X.md 已移动到 节点/ + 追加到白板 "Y"（XXms）`
> - **copy**：`✓ 笔记 X.md 已复制到 节点/ + 追加到白板 "Y"（XXms）`
> - **skip（已在节点池）**：`✓ 笔记 X.md 已就地补 source_board → 追加到白板 "Y"（XXms）`

> [!tip]+ 🔥 你现在立即要做的（修复 Fundamentals）
>
> **方案 A · 用修好的 plugin v4.2 自动修（推荐）**
>
> 1. Cmd+Q 退出 Obsidian → 再开（main.js v4.2 = 65367B）
> 2. 打开 `节点/Fundamentals.md`（让它成为 active file）
> 3. Cmd+P → 搜"把当前笔记追加到已有原白板"→ 选 **"特征值与特征向量"** 白板
> 4. SeedModeModal → **选 skip**（因为已在节点池）
> 5. 应弹 Notice：`✓ 笔记 Fundamentals.md 已就地补 source_board → 追加到白板 "特征值与特征向量"（<300ms）`
> 6. 打开 `节点/Fundamentals.md` 验证 frontmatter 多了 `source_board: "[[原白板/特征值与特征向量]]"`
>
> **方案 B · 手动改 frontmatter（如方案 A 不工作）**
>
> 在 obsidian 直接编辑 `节点/Fundamentals.md`，frontmatter 加一行：
>
> ```yaml
> ---
> type: concept
> source_board: "[[原白板/特征值与特征向量]]"
> ---
> ```
>
> 修复后回到 V3-1：在 Fundamentals 选文字 → Cmd+Shift+D → 关系 modal → 应正常派生（plugin 阶段 1 自动继承 source_board，**不再**报"未确定活动白板"）。

- [ ] **V3-2**：按 Cmd+Shift+D → 关系 modal 选 `extends`
      User：请你查看截图，我当前所选的节点是有隶属的白板的，但是这边还是失败了
- [ ] **V3-3**：描述 modal 输入"测试 v3 hybrid"→ Cmd+Enter
- [ ] **V4-5 ⭐**：modal 关闭后**立即**（< 200ms）弹 Notice：`✓ 派生完成 [[节点/<新名>]]（XXms）。新节点已开 — 在三段空白处写下你的理解，或打开 Claudian 围绕本节点对话。`
- [ ] **V4-6 ⭐ 关键验证**：立即打开新节点 md，应见：
  - frontmatter **无** status 字段（v4.0 砍掉，因为不再有 AI 阶段）
  - frontmatter 含 source_board / source_note / relationships[]
  - 正文是 `[!quote]+` callout 显示选中文本（友好原文展示）
  - 三段空白模板：## 核心概念（提示"你的 1-2 句精准定义"）/ ## 关键点（一个空 bullet）/ ## 关联概念（预填 `[[源笔记]] — extracted`）
  - 末尾 `[!tip] 💬 围绕这个概念讨论` callout 解释节点定位（讨论容器，非 AI 写好）
  - **不**含 AI_BODY_PLACEHOLDER 注释 / SELECTED_TEXT_START 注释 / "AI 正在生成"假承诺

→ 6 步全过 = "Story 1.17 v4.0 通过"

### v4.0 取消的步骤（不用测）

- ~~V3-9 plugin 切 Claudian + 自动粘贴 prompt~~ — 已砍，plugin 不切 Claudian / 不写剪贴板
- ~~V3-10 Claudian 按 Enter 跑 Skill v5.0~~ — 已砍，Skill 删除
- ~~V3-11 阶段 2 完成后 status: ai_complete~~ — 已砍，无状态机
- ~~V3-12 失败恢复 ai_pending~~ — 已砍，无失败可能（脚本同步执行）

### 可选（V3-13 至 V3-22 边界 + 性能）

跳过即可。如果你想严格验收，挑 1-2 步：
- V3-22 阶段 1 总耗时 < 200ms（看 Notice 中 XXms 数字）
- V3-19 节点池重名自动 `_2`

---

## 📋 Story 1.19 已勾的 20 项（仍然有效，不用重测）

| 类别 | 已勾步骤 | 行号 |
|---|---|---|
| **v4-A2 modal 立即弹**（3 项）| modal 弹出 + placeholder + hint 提示 | 58-60 |
| **v3 环境**（4 项）| Reload + canvas-vault 显示 + 三个文件夹存在 + 节点折叠 | 368-376 |
| **Claudian dropdown**（3 项）| `/config` 显示 + `/ai` 显示 + 5 个节点 | 380-396 |
| **Graph View**（1 项）| `path:节点/` 过滤显示 5 个节点 | 411 |
| **白板 wikilink**（3 项）| 打开 CS 61B 白板 + 看到种子 wikilink + Cmd+Click 跳转 | 417-419 |
| **中文编码**（2 项）| 终端能 ls / rm 中文目录 | 425, 447 |

→ **结论**：v3 时期的环境验证 + 中文编码 QA + Claudian Skill 发现机制**已经验证**。

---

## ⏭️ Story 1.19 应跳过的版本

| 版本 | 状态 | 为什么跳过 |
|---|---|---|
| v3 Skill 全流程（场景 A 从零 / 场景 B 派生） | 被 v4.0 替代 | v4 plugin 已接管 Skill 7 步，无需测 v3 Skill 流程 |
| v3 4 决策验收（节点折叠 / vault 级 subject / 中文目录 / 一 vault 零冲突）| 已勾环境部分 | 这 4 决策本质是架构定义，v4 继承 |

→ **直接跑 v4 UAT 即可**。

---

## 🔥 Story 1.19 — 必测最小集（v4.0 + v4.1 关键步骤，约 15 分钟）

> 前置：**Cmd+Q 重启 Obsidian**（main.js 64183B 加载）+ 命令面板搜到"建/配置原白板（v4 全 plugin 脚本）"

### 场景 V4-A 从零建白板（3 步）

- [ ] **V4-A2 ⭐**：Cmd+P → "建/配置原白板"→ 弹 BoardNameInputModal → 输入"测试白板 V4A"→ hint 绿色"✓ 将建到..."（不用测非法字符校验）
- [ ] **V4-A3 ⭐**：Enter → **<300ms** Notice"✓ 原白板已建立（XXms）"+ `原白板/测试白板 V4A.md` 立即可见
- [ ] **V4-A4 性能**：XXms < 300（关键卖点对比 v3 的 15-30s）

### 场景 V4-B 反向引用检测（4 步，你截图 bug 修复验证）

- [ ] **V4-B1**：打开一个**已被反向引用**的节点（如 `节点/Fundamentals.md`，`Characteristic-Equation-for-Eigenvalues` 引用它）
- [ ] **V4-B2**：触发命令 → BoardNameInputModal 输入"V4B Test"→ 提交
- [ ] **V4-B3 ⭐**：**立即**弹 BacklinkWarningModal 列出反向引用 + 3 选项
- [ ] **路径 A 任一**：选"追加到已有白板"→ Notice"✓ 种子已追加..."

### 场景 V4-E v4.1 新命令（3 步，回应你的批注）

- [ ] **V4-E2 ⭐**：Cmd+P → 搜"把当前笔记追加到已有原白板"→ 弹 SelectExistingBoardModal 列出已有白板
- [ ] **V4-E5**：选目标白板 → SeedModeModal 选 move
- [ ] **V4-E6 ⭐**：Notice"✓ 笔记 X.md 已移动到 节点/ + 追加到白板 'Y'（XXms）"

→ 10 步全过 = "Story 1.19 v4 通过"

### 可选（V4-D 错误恢复 / V4-C 无反向引用）

跳过即可。如果想严格验收，挑：
- V4-D2 BoardNameInputModal Esc 取消（< 5 秒）

---

## ⏳ Canvas-完整学习闭环-验收总流程（跨 Story，最后跑）

68 步 0 勾。这是**跨 Story 联测**（建白板 → 派生节点 → 批注 → AI 对话 → 检验白板），需要 Story 1.16/1.17/1.18/1.19 全 done 后才有意义。

→ 单 Story 全过后再考虑跑。**现在跳过**。

---

## 🎯 总执行清单（你今天要做的）

按顺序执行，约 30-40 分钟：

1. **Cmd+Q 退出 Obsidian → 再开**（让最新 main.js 64183B 加载）
2. **跑 Story 1.17 v3.0 必测 9 步**（V3-1 至 V3-12）— 约 15 分钟
3. **跑 Story 1.19 v4.0/v4.1 必测 10 步**（V4-A2/A3, V4-B1-B3, V4-E2/E5/E6）— 约 15 分钟
4. **告诉我"1.17 v3 通过 + 1.19 v4 通过"** → 我 mark done + 启动 Story 1.18 Dashboard MVP

如果任一步 ❌ → 截图 + 告诉我步骤 ID（V3-X / V4-X），我针对性修。

---

## 📝 验收完成回执模板

跑完后复制以下到对话给我：

```
Story 1.17 v3.0:
- V3-1 至 V3-12 全过 ✅ / 部分失败 ❌（哪步）

Story 1.19 v4.0/v4.1:
- V4-A2/A3 ✅ / ❌
- V4-B1-B3 ✅ / ❌
- V4-E2/E5/E6 ✅ / ❌

总耗时: XX 分钟
体感: <写一两句对 v3 hybrid 速度 / v4 反向引用 modal / v4.1 新命令的感受>
```

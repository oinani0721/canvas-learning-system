---
story: "MVP-α-3-exam-quick-skill"
title: "快速单题考察 — Claudian skill fallback 路径"
status: "review"
version: "v1.0"
date: "2026-05-14"
developer: "Session C (Claude Opus 4.7)"
plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
session: "C (skill writer 工种)"
reviewer_score: "38/40 (95%) — Agent A 调研评估"
parent: "MVP-α (用户 10 分钟核心闭环 — 批注 → AI 引用原话出题 → 评分反馈)"
---

# Story MVP-α-3 验收单 — Claudian fallback 单题考察

> [!info]+ 这是什么功能?
> **位置**: MVP-α 用户 10 分钟体验脚本里的"第 4 步 fallback":
>   - 主路径: 你点 Dashboard "🎯 一键考察" → plugin 调 `/api/v1/exam/quick` 出题
>   - 后备路径 (本 Story): plugin 失败 → 你在 Claudian 侧栏输 `/exam-quick` 拿 1 道题
>
> **价值**: 即使 backend 挂了 / 网络断了, 你仍然能用 Claudian 完成"批注 → 出题"循环.

---

## 🎯 这个 Story 要做到什么

让你在 Claudian 侧栏输 `/exam-quick` (或 `/exam-quick 节点名`) → 5-10 秒内拿到一道**针对你批注的练习题** (不是通用题).

---

## 📖 用户故事 (你的视角)

**作为** 学习者,
**我想** 当 plugin 一键考察失败时, 我能在 Claudian 直输 `/exam-quick` 拿到一道针对我批注的练习题,
**以便** 即使 backend 挂了 / 网络断了 / docker 没启动, 我的学习不被中断.

---

## 🖥️ 你会看到的交互 (一步一步)

```
路径 A — Claudian 裸触发 (最常用):

1. 你在 Obsidian 任意节点打开 Claudian 侧栏 (右栏)
       ↓
2. Claudian 输入框打: /exam-quick
   (或 /exam-quick 递归 — 指定节点)
       ↓
3. Claude (skill) 自动:
   - Glob 找到目标节点 .md 文件
   - Read 节点 frontmatter.tips[] + 正文
   - Read 1-hop wikilink 邻居节点
       ↓
4. 5-10 秒后, Claudian 输出 1 道题:
   ```
   question_id: claudian-fallback-{hash}
   question_text: "你在批注中提到「我对 base case 还不太理解」.
     请用 factorial(n) 为例: (a) base case 写 if n == 0
     时何时触发? (b) 你说的「栈溢出」和这里什么关系?"
   source: claudian-skill-exam-quick
   ```
       ↓
5. 底部提示 "ℹ️ 你正在使用 fallback 路径 (质量低于 plugin), 
   想看完整考察请确认 backend docker 在跑后用 Cmd+Shift+E"
```

```
路径 B — Plugin 注入触发 (未来 MVP-α-3 plugin 部分 ship 后):

1. 你点 Dashboard "🎯 一键考察" (但 backend 挂了)
       ↓
2. Plugin 自动 fallback → Cmd+Shift+E 触发 /exam-quick
   + 剪贴板注入 <exam_context>{节点+批注+1-hop}</exam_context>
       ↓
3. Claudian 立刻看到 <exam_context>, 跳过 Glob/Grep 直接出题
       ↓
4. 5 秒内输出题目 (比路径 A 快, 因为 context 已就绪)
```

---

## 🤖 Claude 已代验

> [!success]+ Agent A 调研评估 38/40 (95%)

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | skill 文件路径正确: `canvas-vault/.claude/skills/exam-quick/SKILL.md` | ✅ 8.6 KB |
| 2 | skill 已被 Claude 工具系统注册 (system reminder 含 exam-quick) | ✅ 可立即触发 |
| 3 | YAML frontmatter 5 字段齐全 | ✅ name/description/argument-hint/allowed-tools/model |
| 4 | 8 项 HARD CONSTRAINTS 完整 (禁改文件/禁MCP/中文/Prompt防护/延迟5-10s) | ✅ |
| 5 | 双路径触发识别 (路径 A 裸触发 vs B `<exam_context>` 注入) | ✅ tell-tale marker 清晰 |
| 6 | 批注 3 种 pattern 识别 (callout / **User：** / frontmatter tips) | ✅ 含 Grep 正则 |
| 7 | 输出格式跟 plugin /api/v1/exam/quick 对齐 (question_id / text / source) | ✅ markdown 等价 JSON |
| 8 | 出题策略 4 类路由 ([!question]+反向 / [!error]+巩固 / **User：**直问 / 无批注通用) | ✅ |
| 9 | 故障明示 + downgrade 告知 + 修复指引 | ✅ ℹ️ 标记 + 改走 backend 提示 |
| 10 | 风格一致性 vs node-chat / study-question (约束密度 5.3%) | ✅ 与 study-question 一致 |
| 11 | 与 Story 2.4 frontmatter tips[] 真相源对齐 (skill 能直接 Read) | ✅ |

**未阻塞但建议 v1.1 修复**:
- ⚠️ 路径 A 模糊节点名匹配策略未明示
- ⚠️ §5 出题策略缺 Q&A 实际示例
- ⚠️ 多批注时选哪条策略未规定

---

## 👤 你来验 (产品使用体验 — 5 步, 5 分钟内)

> [!warning]+ 这段的硬规矩
> 工具白名单: Obsidian 主界面 / Claudian 侧栏 (右栏)
> 句型: "我做 X → 我看到 Y → 我感觉 Z"
> 重要: 开始前先 reload Obsidian (Cmd+P → "Reload app without saving") 让新 skill 生效

### 第 0 步: Reload Obsidian + 打开 Claudian 侧栏

- [ ] 我用 Cmd+P → "Reload app without saving" → Enter
- [ ] Obsidian 重启 → 我点右上角 Claudian 图标 → 侧栏打开
- [ ] 我感觉: 界面熟悉, 没出现报错弹窗

### 第 1 步: 准备 — 给一个节点写批注

- [ ] 我打开任意 `节点/<某概念>.md` (推荐 `规划的分类-1549()` 因为已有 Story 2.4 ship 的 tips[] 测试)
- [ ] 我选中文字 → Cmd+Shift+A → 选 `💡 Tips` → 选 `🤔 模糊`
- [ ] 我在 callout 末尾 "✍️ 我的理解：" 后写: "我对这个概念还不太理解"
- [ ] 我等 1 秒 → 看 properties 自动出现 tips 数组 (Story 2.4 验证)

### 第 2 步: 路径 A 裸触发 — Claudian 输 `/exam-quick`

- [ ] 我在 Claudian 输入框打: `/exam-quick`
- [ ] 我看到 Claude 开始处理 (5-10 秒)
- [ ] 我看到 Claude 输出**一道针对我刚才批注的练习题**
- [ ] 我感觉: 题目引用了我的原话 (如"你提到... 还不太理解...")

### 第 3 步: 路径 A + 节点名 — 指定节点出题

- [ ] 我在 Claudian 输入框打: `/exam-quick 递归` (或你刚才批注的节点名)
- [ ] 我看到 Claude 自动找到该节点 + 读 tips + 出题
- [ ] 我看到题目跟节点内容 + 我的批注**精确对应**
- [ ] 我感觉: 系统懂我说的话

### 第 4 步: 边界 — 无批注节点 (通用题降级)

- [ ] 我换一个**没有任何批注**的节点 → `/exam-quick`
- [ ] 我看到 Claude 输出基于节点正文的通用题 + 提示 "未找到批注, 已生成通用题"
- [ ] 我感觉: 降级体验合理, 不报错

### 第 5 步: 边界 — fallback 告知

- [ ] 我看到题目下方有 "ℹ️ 你正在使用 Claudian fallback 路径"
- [ ] 我看到指引 "想看完整考察请确认 backend docker 在跑后用 Cmd+Shift+E"
- [ ] 我感觉: 透明 / 我知道自己用的不是最优路径但仍可用

### 主观打分

- [ ] **流畅度** (1-5: 1=卡 5=如丝): ___
- [ ] **题目针对性** (1=通用 5=精确引用原话): ___
- [ ] **fallback 透明度** (1=黑盒 5=完全知道): ___
- [ ] **你愿意把它作为 plugin 失败的后备路径吗** (1=不 5=愿意): ___
- [ ] 一句话告诉我感受: ___

---

## 🚦 验收结果

**如果第 2/3 步都能拿到针对性题目**: 告诉我 "**MVP-α-3 skill 通过**" → 我 mark done + 等 Session A/B (backend / plugin) 完成后做端到端 UAT.

**如果题目通用 / 没引用批注**: 在批注区写明哪一步 + 截图.

**如果 5 步全失败**: 可能 skill 没 reload — 重新 Cmd+P → "Reload app without saving".

---

## 📝 你的批注区

> [!question]+ 你对 MVP-α-3 skill 的批注
>
> (空)

### 已知设计缺陷 (Agent A 调研发现, 非阻塞)

> [!error]+ 2026-05-14 v1.0 → v1.1 待修 (P1/P2 非阻塞)
> **P1 — 多批注选择策略**: 节点有 3 条 callout 时, skill 没规定选哪条出题. 当前 fallback 是按 Grep 顺序拿第 1 条.
> **P2 — 路径 A 模糊节点名**: `/exam-quick 递归` vs `递归算法` 没规定 fallback 策略.
> **P2 — 出题策略缺示例**: §5 4 类路由清晰但无 Q&A 实例, Claude 执行可能解释偏差.
>
> 这些是 v1.1 待修, **不阻塞** v1.0 UAT.

---

## 🔗 技术 spec 参考

- **MVP-α 协调文档**: `_bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md` (336 行)
- **Session C 启动 prompt**: 协调文档第 5 段 "Session C — Skill"
- **改动文件**:
  - `canvas-vault/.claude/skills/exam-quick/SKILL.md` (新建 8.6 KB)
- **AC trace**:
  - AC#1 (Claudian 触发出题) → `SKILL.md §1 双路径识别`
  - AC#2 (用户原话引用) → `§5 4 类路由 + §6 第 1 回合出题`
  - AC#3 (与 plugin 接口对齐) → `§4 输出 markdown 等价 JSON`
  - AC#4 (fallback 告知) → `§8 ℹ️ 故障明示 + 修复指引`
- **设计评分**: 38/40 (95%) — Agent A 调研
- **未 commit** ⚠️ Session C 写完未 push, 需协调员补 commit

---

## 📅 下一步

1. **通过** → "MVP-α-3 skill 通过" → 我 commit Session C skill + mark sprint-status done + 等 Session A (backend α-1/α-2/α-4) + Session B (plugin α-5/α-3)
2. **不通过** → 你批注哪步问题, Session C v1.1 修复
3. **想看 Session C 启动 prompt 内容** → `_bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md` 第 5 段

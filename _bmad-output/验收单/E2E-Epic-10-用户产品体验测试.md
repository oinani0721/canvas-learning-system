---
epic: "10"
title: "Epic-10 E2E 用户产品体验测试清单"
type: "e2e-product-experience"
status: "living"
date_created: "2026-05-07"
maintained_by: "Claude"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
last_phase_a_ship: "2026-05-07 — Story 10.4 Phase A end-to-end injected book bk_a87d2cdff1"
---

# Epic-10 E2E 用户产品体验测试清单

> **范围**：100% "作为学习者使用产品"的视角。技术验证（API/schema/cost/docker logs）由 Claude 在每个 Story 验收单的"🤖 Claude 已代验"段处理 — 见 `feedback_uat_user_only_product_experience.md`。
>
> **使用方式**：每个 Story ship 后，Claude 把对应 TS 状态从 🔒 → 🟢 (可验) → ✅ (用户已验通过) / ❌ (用户已验失败)。

## 状态图例

| 标记 | 含义 |
|---|---|
| 🔒 | 锁定（前置 Story 未完成，无法验） |
| 🟢 | 可验（依赖 Story 已 ship，等用户跑） |
| ✅ | 用户已验通过 |
| ❌ | 用户已验失败（要 correct-course） |
| ⏸️ | 暂跳（Phase B/C 增强项，非阻塞） |

---

## Layer 1: 当前可验（Story 10.1-10.4 Phase A 已 ship）

### TS-1.1 🟢 vault 注入产物在 fork 可见

> **作为** 学习者，**我** 打开 fork UI，**期望** 看到我的 vault 已经被自动转成 DeepTutor 一本 book

- [ ] `open http://localhost:3782` — 没 502 / connection refused
- [ ] DeepTutor 主界面渲染正常（有 logo / 导航栏 / 主内容区）
- [ ] 中文 UI 元素不乱码
- [ ] Books 列表里有一本 `bk_a87d2cdff1`（title 可能显示 "Untitled Book"，原因见 Phase A 已知瑕疵）
- [ ] 点击该 book 不报错，能进入详情页

> **不通过怎么办**：如果 Books 列表是空 → fork storage 可能没持久化 → 截图 + Books 列表给 Claude 跑 GET `/api/v1/book/books` 对账

### TS-1.2 🟢 章节列表对应 vault 结构（中文 chapter title）

> **作为** 学习者，**我** 打开这本 book，**期望** 看到 vault 4 个白板对应 4 个 chapter，每个 title 是中文且不乱码

- [ ] 左侧 / 顶部 chapter 导航能看到 **5 个 chapter**
- [ ] **第 1 个**：本书导览（Overview，fork 自动注入，"How to read this book" 的中文版）
- [ ] **第 2-5 个 chapter title 全部正确显示**：
  - 特征值与特征向量
  - 线性代数
  - CS 61B 数据结构
  - 递归与分治 (Recursion & Divide-Conquer)
- [ ] 点击每个 chapter 切换不报错
- [ ] page 内容空白属于 Phase A 预期（Phase B 才填 vault md body）— 不是 bug

### TS-1.3 ⏸️ Overview chapter 内 ConceptGraph 渲染

> **作为** 学习者，**我** 打开 Overview chapter "本书导览"，**期望** 看到 vault 的概念关系图（节点 + 边）

- [ ] Overview chapter 内有图形 block（Mermaid 静态图 / svg / canvas）
- [ ] 看到至少 5 个节点（理想 18 个）
- [ ] 看到至少 3 条边（理想 15 条）
- [ ] 节点 label 显示概念名（cs-61b-csm / Fundamentals / my-recursion-notes 等）

> **暂跳原因**：Overview chapter 是 fork 自动 inject 的 — concept_graph 渲染依赖 fork 自带的 ConceptGraphBlock 组件，能否渲染我们注入的 graph 数据需用户实测。如不渲染，留 Phase B 调整 spine schema。

### TS-1.4 🟢 Wikilink 渲染（Story 10.2 Day 1 + 10.3 CalloutBlock 修复联动）

> **作为** 学习者，**我** 在 chat 或 book editor 写 `[[recursion]]`，**期望** 它显示为蓝色链接

- [ ] 在 chat 输入框写 `这个 [[recursion]] 很重要`
- [ ] 发送后看到 `[[recursion]]` 渲染为蓝色链接（不是纯文本 `[[recursion]]`）
- [ ] 鼠标悬停 / 点击有反应（不一定跳转，至少 hover 状态变化）

### TS-1.5 🟢 Callout 内 wikilink 渲染（Story 10.3 Task 1 一行修）

> **作为** 学习者，**我** 在 fork 看到含 `> [!question]+ See [[sorting]]` 的内容，**期望** callout 内的 `[[sorting]]` 也是蓝链（不是纯文本）

- [ ] 找一个 callout block（Quiz / Tip / Question / Error 类型任一）
- [ ] callout 用对应颜色 + icon 渲染（蓝问号 / 绿对勾 / 红叉等）
- [ ] callout 内的 `[[wikilink]]` 是蓝链，不是纯文本

> **没找到 callout 怎么办**：Phase A 注入的 chapter 都是空 page，可能没 callout。等 Phase B 注入 vault md body 后再试 — 或在 fork 自带的 example book 里找。

---

## Layer 2: Day 4 Phase B 后可验（Story 10.4 P1 + P2）

### TS-2.1 🔒 chapter page 显示 vault md 原文

> **作为** 学习者，**我** 打开 "CS 61B 数据结构" chapter，**期望** 看到 vault md 原文（不是空 PENDING）

- [ ] chapter 内显示 vault md 原文 body（标题 / 列表 / 粗体格式正确）
- [ ] frontmatter（`---` 之间）不显示（只显示 body）
- [ ] 中文段落、英文段落、混合段落都正常显示

### TS-2.2 🔒 vault 7 callout 类型注入并正确渲染（UX-1 落地）

> **作为** 学习者，**我** 在 vault 写过 `> [!question]+`、`> [!error]+`、`> [!tip]+` 等 callout，**期望** fork 也能用对应样式渲染

- [ ] 找到 vault 里有 callout 的 chapter
- [ ] 看到 7 类 callout 之一（question / error / tip / hint / note / warning / info）
- [ ] callout 颜色 + icon 与 Obsidian 内一致（视觉一致性）
- [ ] callout 内 `[[wikilink]]` 是蓝链（依赖 Story 10.3 修复）

### TS-2.3 🔒 vault 改 md → 重跑 cli → fork 看到更新

> **作为** 学习者，**我** 在 vault 编辑一个 md，**期望** 重新注入后 fork 内对应 chapter 显示更新内容

- [ ] 在 `canvas-vault/节点/Fundamentals.md` 加一行新文字
- [ ] 重跑 `python -m adapter.cli ... --inject`（产生新 book_id）
- [ ] fork :3782 Books 列表多一本（旧 book 也保留）
- [ ] 新 book 的 Fundamentals chapter / page 显示更新内容

### TS-2.4 🔒 用户进度（已读/已完成）从 frontmatter 同步

> **作为** 学习者，**我** 在 vault md frontmatter 写 `status: read`，**期望** fork 内对应 chapter 显示"已读"标记

- [ ] vault md 加 `status: read` 或 `status: completed`
- [ ] 重跑 cli 注入
- [ ] fork chapter 显示 progress 标记（绿勾 / 进度条 / "已完成" 标签）

---

## Layer 3: Day 5-10 全 Epic-10 完整 MVP（Round-22 S1-S5 + S6 Graphiti）

### TS-3.1 (S1) 🔒 Wikilink 全链路（Day 1-2 + Day 5）

> **作为** 学习者，**我** 在 fork 写 `[[recursion]]` → **期望** ① 自动完成 ② 渲染蓝链 ③ 点击跳转 < 1s

- [ ] 输入 `[[rec` 触发自动完成下拉（vault 内含 recursion 概念时）
- [ ] 选中后渲染为蓝链
- [ ] 点击跳转到 recursion 概念 page < 1s
- [ ] 跳转目标 page 是 vault 内 `节点/recursion.md` 对应的 chapter

### TS-3.2 (S2) 🔒 右键 callout → Canvas ACP 出题 → mastery 更新（Day 4）

> **作为** 学习者，**我** 在 fork 看到一个概念 callout，右键选 "Generate Quiz via Canvas ACP" → **期望** ① 弹出 quiz ② 答完 mastery 数字变化

- [ ] 右键 quiz callout 弹菜单，含 "Generate Quiz via Canvas ACP" 选项
- [ ] 点击后等 ~3-5s 看到 quiz 内容（题目 / 选项 / 输入框）
- [ ] 答题提交后 UI 显示 "已提交"
- [ ] 该概念的 mastery 数字（如 0.30 → 0.45）UI 上能看到变化

### TS-3.3 (S3) 🔒 AutoSCORE 4 维评分 → Dashboard（Day 7 = Story 10.6）

> **作为** 学习者，**我** 答完一道题，**期望** 看到 4 维评分（不是简单 √/×）+ Dashboard 趋势图

- [ ] 答题反馈含 4 个分项分数（理解 / 表达 / 完整性 / 准确性）
- [ ] Dashboard 页面看到 mastery 趋势图（折线 / 柱状）
- [ ] 趋势图能看到时间轴上的进步 / 退步

### TS-3.4 (S4) 🔒 Whiteboard 路由：节点 + 边 + 颜色（Day 5-6 = Story 10.5）

> **作为** 学习者，**我** 进入 `/whiteboard/<id>` 路由，**期望** 看到完整 vault 概念图（≥10 节点 + 边）+ 节点颜色按 mastery 着色

- [ ] URL `http://localhost:3782/whiteboard/<id>` 能打开（不 404）
- [ ] 看到 ≥ 10 个节点（vault 实际有 18 节点）
- [ ] 看到 ≥ 5 条边（vault 实际有 15 边）
- [ ] 节点颜色不是单色（按 mastery 着色：红/黄/绿）
- [ ] 拖动 / 缩放 / 选中节点流畅

### TS-3.5 (S5) 🔒 答错 → Day 0/3/7 复习推送（Day 8 = Story 10.7）

> **作为** 学习者，**我** 答错了一题，**期望** ① 立即 console 看到 `[REVIEW DUE T+0]` ② 3 天后再次 due ③ 7 天后第三次

- [ ] 答错后浏览器 console 立刻打印 `[REVIEW DUE] T+0 <concept-id>`
- [ ] 系统时间 +3 天后（或 mock）console 打印 `T+3`
- [ ] 系统时间 +7 天后 console 打印 `T+7`
- [ ] 推送来源（8 通道任一：notification / sound / desktop alert / etc）触发

### TS-3.6 (S6) 🔒 Graphiti 闭环：错题历史多 hop 召回（Day 9-10）

> **作为** 学习者，**我** 在 24h 后再答题，**期望** 系统提示 "3 天前你在 X 概念栽过，本次出题关联 Y"

- [ ] 答错某概念 → 写入 Graphiti episodic memory
- [ ] ≥ 24h 后触发复习
- [ ] 复习推送 / page 显示**关联历史错题摘要**（"3 天前栽过的概念" + "关联到本次的 Y 概念"）
- [ ] ACP 出题参数含历史 episodic 上下文（quiz 题目针对性测试关联概念）

---

## Layer 4: Day 10 UAT 收官（决策点）

### TS-4.1 🔒 5 验证场景全过 → Path A 决策

> **作为** 学习者，**我** 跑完 Day 1-9 所有 Story 后跑 Day 10 UAT，**期望** S1-S5 全 PASS + 主动用 5 天

- [ ] S1-S5 五场景按 TS-3.1 ~ TS-3.5 全验通过
- [ ] 主动使用产品 ≥ 5 天（不是测试，是真实学习）
- [ ] 想 ship 单一产品（不分两个工具）
- [ ] **决策 A**: 继续 fork 深度集成 → 启 Epic-11 桌面化（Day 11+）

### TS-4.2 🔒 部分场景失败 → Path B/C 决策

- [ ] S1+S2+S3 全过但用 < 6 天 → **Path B**: 退回独立 PyPI 包 `deeptutor-canvas`
- [ ] 5 个核心只用 2 个 → **Path C**: 混合（fork lite + 抽核心）

---

## 已知限制（Phase A 范围）

| # | 限制 | 影响 | Phase B/C 解决方案 |
|---|---|---|---|
| 1 | book.title = "Untitled Book"（fork ideation fallback 时不生成有意义 title） | UX：Books 列表标题不直观 | Phase B 改 cli 让 `--book-title` 直接覆盖 book.title |
| 2 | page 内容空白（PENDING） | UX：点 chapter 看不到 vault md body | Phase B 用 `/insert-block` endpoint 注入 vault_blocks |
| 3 | edge 重复（同 src→dst 出现两次） | UX：concept_graph 视觉重复 | Phase B 加 edge dedup（用 set） |
| 4 | 嵌套 wikilink id 含路径前缀（`cn_节点my-recursion-notes`） | UX：仅 ID，用户不直接看到 | Phase B 让 _slug 取 basename |
| 5 | broken link placeholder（31 nodes vs 22 实文件） | UX：concept_graph 多出虚节点 | Phase B 过滤未存在的 wikilink target |

---

## 验收纪律

1. **Claude 维护本文档**：每个 Story ship 后更新对应 TS 状态（🔒 → 🟢 → ✅）
2. **用户只在 🟢 标记的 TS 上跑 UAT**：技术指标（API status / schema / cost）由 Claude 跑
3. **不通过的处理**：用户填 ❌ + 截图 + 描述 → Claude correct-course
4. **新 Story 加新 TS**：Day 11+ Epic-11 启动时本文档加 Layer 5

---

*Living document. 上次更新：2026-05-07 Story 10.4 Phase A end-to-end ship 后。*

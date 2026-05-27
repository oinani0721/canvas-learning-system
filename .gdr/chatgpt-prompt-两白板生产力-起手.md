# 原白板 + 检验白板生产力审查 — 给 ChatGPT 的起手 prompt

> 用法: 复制下方分隔线之间 → 粘贴 ChatGPT (Pro Deep Research / Claude Desktop 1M / Gemini 2.5 Pro DR) → 同时**上传 `research-pack-two-whiteboards-audit.xml`** (541KB / 150K tokens / 34 文件) → 发送

---

✂️ ═══════════════ 复制下方开始 ═══════════════

请对我上传的 **`research-pack-two-whiteboards-audit.xml`** 做 **Deep Research 深度分析**。

## 议题: Canvas Learning System 原白板(剖析) + 检验白板(Active Recall) 两个核心学习功能的**生产力标准审查**

## 用户原话锚点 (不可妥协)

> "我们使用 Graphiti 本质上是要**原白板和检验白板的功能达到生产力标准来高质量使用**, 着重聚焦于我对这两个功能在我实际学习过程的需求是什么。"

## ⭐ 审查视角 (关键)

站在一个 **CS 61B 学生每天怎么学习** 的视角, 判定这两个白板能不能"高质量日常使用"。**不是审技术细节优不优雅, 是审"我学习时卡不卡 / 愿不愿意每天打开它"**。

## 📦 XML Bundle (541KB / 150K tokens / 34 文件)

- **<directory_structure>** — PRD 灵魂章节切片 + epics Epic 4 + 检验白板 11 spec + 原白板 spec + 关键 backend/plugin 代码
- **<files>** — 34 个 file 完整内容
- **末尾 <instruction>** ⭐ — 完整任务书 (3 学习闭环 + 5 实证风险 + 7 议题 + 7 Part 输出)

**请先读末尾 <instruction>** (完整任务书), 再通读 <directory_structure>, 再按议题分析。

## 两白板 PRD 灵魂定义

| | 原白板 (剖析) | 检验白板 (Active Recall) |
|---|---|---|
| 信息 | 可见 | **隐形** (完全空白 UI) |
| 机制 | 理解+剖析+Edge 对话 | 主动回忆 (Karpicke **d=1.50 最大效应量**) |
| 不可破 | wikilink 双链探索 | 三重隔离(reference_answer=None)+防嵌套+信息隐形 |

## 3 条学习闭环 (审查主线)

- **A 原白板剖析**: 批注 callout → 派生节点选关系 → 双链探索 → AI 对话
- **B 检验白板考察**: 一键考察 → 空白白板 → 针对性出题 → 手写答 → 评分 → 掌握度更新
- **C 学习飞轮**: 原白板学完 → 考察 → 暴露新疑问 → 归原白板 → 下次考到

## 5 个实证风险 (Claude 已查 codebase, 你深审对生产力影响)

- **P-1** 检验白板灵魂(防嵌套/隔离gate/PRD 10步workflow)代码中几乎无踪, 只有 MVP 简化版落地 (用户 2026-04-08 锁"100%等价"但当前是简化版)
- **P-2** 三套路径命名互不一致 (PRD `exam_boards/` vs CLAUDE.md `检验白板/` vs 代码 `节点/考察-`) — 用户找不到历史考察?
- **P-3** 三重隔离 reference_answer=None 是赋值级非 fail-closed gate 级 (隔离被破 = d=1.50 崩塌)
- **P-4** 两条评分链并存 (MCP 链 exam_tools.py:435 有 V-10 vs MVP 链 exam_grade.py:93 已规避)
- **P-5** 原白板上下文富集读 .canvas JSON (扁平架构下跑不通, epics AR11 已承认)

## 📋 7 Part 输出 (任务书 §6 详版)

请用中文, 必给:
- **Part 1**: 两白板生产力总评 (PRD 灵魂达成度 + 生产力评分 1-10 + 差距)
- **Part 2**: 3 条学习闭环逐条评分 (卡点 + 补什么)
- **Part 3**: 5 风险严重度 (是否阻塞"高质量使用")
- **Part 4**: 检验白板灵魂 100% 等价 vs MVP 简化版 (哪些必须补回)
- **Part 5**: 两白板缺的 spec 清单 (具体补什么)
- **Part 6**: 与 Graphiti runtime (5-ge) 的优先级 (先做哪个)
- **Part 7**: 一句话判定 (离生产力标准差 X%, 必须补 [...])

## 📌 严格要求

- **站用户学习视角**, 必给生产力评分 (1-10) + 卡点排序
- **必引用 file:line 证据** (bundle 内)
- **必区分 PRD 灵魂 vs MVP 简化版** 差距
- **避免** "整体不错, 建议优化" 无信息回答

开始你的 Deep Research 吧。

✂️ ═══════════════ 复制上方结束 ═══════════════

---

## 🚀 实操

### ChatGPT Pro / Claude Desktop / Gemini DR
1. 上传 `.gdr/research-pack-two-whiteboards-audit.xml` (Finder 已 reveal)
2. 粘贴上方 prompt
3. 发送 → 等 15-40 min

## 📂 路径速查

```
XML: .gdr/research-pack-two-whiteboards-audit.xml (541KB / 150K tok / 34 文件)
Prompt: .gdr/chatgpt-prompt-两白板生产力-起手.md
任务书: _bmad-output/审查/2026-05-27-两白板生产力审查-任务书-给-ChatGPT.md
```

## ❓ 追问模板

```
你的 Part 1 生产力评分基于哪个 file:line 证据? 引用具体内容.
你是否真审了 instruction §3 的 3 条学习闭环? 逐条说卡点在哪一环.
检验白板 P-1 (灵魂只有 MVP 版): 你认为哪些灵魂机制是生产力红线必须补, 哪些可简化? 给具体 spec.
```

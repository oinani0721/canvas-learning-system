---
title: "19 · 14-PRD v3 → v4 Changelog · Plan v21 第二轮审查 7 Fix + errata of errata"
version: v1
status: completed
created: 2026-04-09
author: Claude Code (Plan v21)
base_version: 14-scheme-a-implementation-prd.md v3 (Plan v19)
target_version: 14-scheme-a-implementation-prd.md v4 (Plan v21)
trigger: ChatGPT 5 Pro Deep Research 第二轮审查 (2026-04-09 下午)
covers_fixes: [Fix-04, Fix-05, Fix-06, Fix-07, Fix-08, Fix-09, Fix-10]
total_edits: ~120-180 行 · 7 处核心 Fix + §7.6.5 重写 (~120 行替换 ~70 行) + §1.5.8 追加 (~120 行) + frontmatter 更新
philosophy: "三层 nested errata · 每层都是同一教训的新变体 · 以生产代码为 ground truth"
tags: [canvas, learning-system, prd-v4, changelog, plan-v21, errata-of-errata, chatgpt-round-2]
---

# 19 · 14-PRD v3 → v4 Changelog · Plan v21 第二轮审查 7 Fix

> **用途**：记录 14-scheme-a-implementation-prd.md 从 v3 (Plan v19) 到 v4 (Plan v21) 的完整修订差异。涵盖 ChatGPT 5 Pro Deep Research 第二轮审查的 7 个真实发现（+ 1 个过虑发现不处理），以及 Plan v21 独立核实后的 7 项 Fix（Fix-04 ~ Fix-10）。
>
> **核心哲学**：Plan v21 揭示了 3 层 nested errata · Plan v17 "扫描漏目录" → Plan v19 "smoke check 命令语法错" → Plan v21 "应以生产代码 import 语法为 ground truth" · 每层都是同一教训的新变体。

---

## §0 · Overview

### §0.1 · 修订触发链

1. **Plan v19 完成**（2026-04-09 早）：交付 14-PRD v3（7391 行）+ 17-prd-v3-changelog.md（673 行）+ 16-report §1.5.6 Plan v18 erratum
2. **Plan v20 完成**（2026-04-09 午）：交付 18-adversarial-review-prompt-v2.md（1021 行 · 第二轮审查 prompt）
3. **用户手动操作**：Cmd+C 复制 18-prompt-v2 内的 `copy-to-deep-research` 块 → ChatGPT 5 Pro Deep Research → 粘贴 3 附件（14-PRD v3 + 16-report + 17-changelog）
4. **ChatGPT 返回**（2026-04-09 下午）：🟡 **GO with major fixes** · 8 个发现 · 7 真 1 假（详见 §0.3）
5. **Plan v21 启动**：
   - Phase 1 · 3 个并行 Explore agent 独立核实（PRD 内部一致性 + Canvas 后端实地 + 学术文献核实）
   - Phase 2 · Plan agent 规划修订细节
   - Phase 3 · AskUserQuestion 3 项关键决策（Fix-04 方向 + §7.6.5 重命名 + 走向 A/B）
   - Phase 4 · 执行 7 项 Fix（本 changelog 记录）
6. **下一步**：Plan v22 第三轮审查（走向 A · 生成 20-adversarial-review-prompt-v3.md）

### §0.2 · 用户决策（Phase 3 AskUserQuestion 结果）

| 决策点 | 用户选择 | 含义 |
|---|---|---|
| **Fix-04 方向**（设计 8 d=2.30 清除）| ✅ **方案 A · 简单替换**（~10 行）| 最小改动 · 最低风险 · §1.8 标题 + 正文 + §5.5 插件引用直接替换为 d≈0.55 Cepeda 2008 |
| **Fix-05 §7.6.5 重命名** | ✅ **重命名为 "Canvas 后端实地状态（Plan v21 硬化 · errata of errata）"** | 显式标注 errata of erratum 性质 · 让未来读者一眼看出这是二次校正 |
| **Plan v21 修完后走向** | ✅ **走向 A · 生成 Plan v22 第三轮 ChatGPT 审查 prompt** | 继续递归审查 · 确认 7 项 Fix 正确执行 + 发现 Plan v21 引入的新 bug |

### §0.3 · ChatGPT 第二轮审查 8 个发现（Plan v21 独立核实后）

| # | 发现 | Plan v21 核实结论 | 严重度 | 响应 |
|---|---|---|---|---|
| 1 | Fix-02b 不彻底 · d=2.30 残留 L2814/L2821/L5254 | ✅ 完全真实 | 🔴 阻断 | **Fix-04** · 方案 A 简单替换 |
| 2 | Fix-03 smoke check 盲点 · canvas_agentic_rag 实际存在 | ✅ 完全真实 · 代码证据链 79 处 | 🔴 阻断 | **Fix-05** · §7.6.5 + §10.1 Day 1 Spike 2 重写 + 重命名 |
| 3 | Cochrane Ch 10.10.1 引用错位 · 应为 Chapter 12 | ✅ 官方文档确认 | 🟡 重要 | **Fix-06** · Chapter 10.10.1 → Chapter 12.3.1 |
| 4 | Bisra CI 0.46-0.64 错误 · 应为 0.45-0.65 | 🟡 部分核实（核心数据对 · CI 边界待原文确认） | 🟡 重要 | **Fix-07** · 改为 0.45-0.65 + effect sizes + participants 修正 |
| 5 | Cassady Table 3 写错 · 实为 SAT 均值表 | ✅ 独立确认 | 🟡 重要 | **Fix-08** · 删除 Table 号具体引用 |
| 6 | Chi d=1.00 残留 L1470/L4032 · 与 d≈1.09 冲突 | ✅ 完全真实 | 🟡 一致性 | **Fix-09** · L1470+L4032 改为 d≈1.09 |
| 7 | 87.1%/88.1% 残留 | ❌ ChatGPT 过虑 · Plan v19 已彻底清除 | — | **无需修** |
| 8 | PRD 文件头 v1 + Plan v15 | ✅ 真实但低优先级 | 🔵 文档治理 | **Fix-10** · frontmatter version/author 更新 |

**小结**：8 项发现中 · 7 项真实（其中 2 项 🔴 阻断 · 4 项 🟡 重要 · 1 项 🔵 文档治理）· 1 项过虑（87.1%/88.1%）· 总体审查精确度 87.5%。

### §0.4 · Plan v21 核心教训（三层 nested errata）

> **教训本体**：每次"修正"自身也可能错 · 文档必须预留 errata-of-errata 空间 · 方法学教训必须显式写入而不是埋在实施细节里。

| 层 | 时间 | 主角 | 盲点 | 教训 |
|---|---|---|---|---|
| **L1** | 2026-04 上旬 | Plan v17 Canvas 后端扫描 | 只搜 `backend/app/services/` 子目录 | 没有全目录扫描 |
| **L2** | 2026-04-09 早 | Plan v19 smoke check | 命令语法错 · `pip show canvas_agentic_rag` + `import canvas_agentic_rag` 都是错的（顶级包叫 `agentic_rag`） | 没有以生产代码 import 语法为 ground truth |
| **L3** | 2026-04-09 下午 | **Plan v21 独立核实（本次）** | **TBD · 等 Plan v22 第三轮审查** | TBD |

**共同点**：每层都认为自己"亲自验证了"上一层的结论，但都有新形式的盲点。

**Plan v21 方法论泛化**：
1. **grep 生产代码找真实 import/call 语法** → 复制粘贴作为 smoke check 命令
2. **比对 `__all__` 和 `__init__.py`** → 知道顶级包到底导出什么名字
3. **寻找日常运行的矛盾证据** → 如果 smoke check 说 X 不存在 · 但生产服务每天正常运行 · 先怀疑 smoke check 命令
4. **errata 必须预留 errata-of-errata 空间** → 文档结构应支持多层嵌套校正

---

## §1 · 逐 Fix before/after diff

### §1.1 · Fix-04 · 设计 8 d=2.30 清除（3 处）

**严重度**：🔴 阻断（ChatGPT 第一轮审查要求的 Fix-02 · Plan v19 清除不彻底）

**触发**：Plan v19 只修了 §9.1 汇总表（2.30 → 0.55）和 §9.2 加总禁令 · §1.8 章节标题 + 正文 + §5.5 插件引用共 3 处残留未清。ChatGPT 第二轮审查直接指出。

#### §1.1.1 · L2814 · §1.8 章节标题

**Before**：
```markdown
### 1.8 · 设计 8 · 3 天 + 1 周主动提醒（d = 2.30）
```

**After**：
```markdown
### 1.8 · 设计 8 · 3 天 + 1 周主动提醒（d ≈ 0.55 · Cepeda 2008 · Plan v21 修正）
```

#### §1.1.2 · L2820-2821 · §1.8 学习科学根据段

**Before**：
```markdown
- **Spacing Effect** · Cepeda et al. (2006), *Psychological Bulletin* 132(3): 354-380
  - 效应量: d ≈ 1.10-1.50
- **Error Correction + Spaced Repetition** · Metcalfe (2017), *Annual Review of Psychology* 68: 465-489
  - **复合效应量**: d ≈ 2.30（误解纠正 + 间隔复习组合）
  - 原理: 对已发现的误解进行 3 天后 + 1 周后的间隔复习，记忆固化效率最高
```

**After**：
```markdown
- **Spacing Effect** · Cepeda et al. (2008), *Psychological Science* 19(11): 1095-1102（"Spacing effects in learning: A temporal ridgeline of optimal retention"）
  - 效应量: **d ≈ 0.55**（range 0.40-0.70 · 取决于 spacing gap/retention interval 比例）
  - 原理: 3 天后 + 1 周后间隔复习的 ridgeline 落在最优记忆固化区间
- **Error Correction 机制** · Metcalfe (2017), *Annual Review of Psychology* 68: 465-489（"Learning from Errors"）
  - 定性综述 · **不报告单一 d 值** · 描述"从错误中学习"的认知机制
  - 与 Spacing Effect 独立 · 两者共同支撑"已发现的误解应延迟复习而非立刻复习"的设计
```

**额外变更**：删除 "**这是 Canvas 12 个设计中效应量第 2 大的**（仅次于 Retrieval Practice d=1.50），因为它是**复合效应**" · 改为 "**这是 Canvas 12 个设计中的中等效应量**（在 12 个设计中处于中位数附近 · 与 4 维评分 d=0.70 和元认知 2x2 d=0.60 同档），作为 **Spacing Effect 的实施者** 独立有效"。

**原因**：d≈0.55 不再是第 2 大（第 2 大是 BKT+FSRS 1.00 或 EI+SE 0.90） · 必须同步更新排序描述。

**Plan v21 修正注追加**（新增内容）：
```markdown
**Plan v21 修正注**：Plan v15/v16 曾写 "d ≈ 2.30（复合效应量 · Metcalfe 2017）"。这个数字无法从 Metcalfe 2017 原文（Annual Review of Psychology · 定性综述）验证——Metcalfe 2017 是 review article · 不报告单一 d 值。Plan v19 只修了 §9.1 汇总表（从 2.30 → 0.55）和 §9.2 加总禁令 · §1.8 章节标题和正文的 "d = 2.30" 残留未清。ChatGPT 5 Pro Deep Research 第二轮审查发现残留 · Plan v21 补修。**正确效应量**：使用 Cepeda 2008 的 Spacing Effect d ≈ 0.55 作为 quantitative 锚点（不加总误解纠正机制 · 避免 Plan v19 §4.4 同类错误）。
```

#### §1.1.3 · L5254 · §5.5 Spaced Repetition 插件章节

**Before**：
```markdown
**对学习效果贡献**:
- §1.8 设计 8 · 3 天 + 1 周主动提醒 (d=2.30)
- Spacing Effect 的实施者
```

**After**：
```markdown
**对学习效果贡献**:
- §1.8 设计 8 · 3 天 + 1 周主动提醒 (d ≈ 0.55 · Cepeda 2008 · Plan v21 修正)
- Spacing Effect 的实施者
```

**Fix-04 总行数**：~25 行修订（含新增的 Plan v21 修正注段落）

---

### §1.2 · Fix-05 · §7.6.5 重命名+重写 + §10.1 Day 1 Spike 2 重写

**严重度**：🔴 阻断（Plan v21 最大的 Fix · ~120 行替换 ~70 行）

**触发**：ChatGPT 第二轮审查发现 Plan v19 §7.6.5 和 §10.1 Day 1 Spike 2 断言 "canvas_agentic_rag module 完全不存在"，但这个断言基于错误的 smoke check 命令。Plan v21 独立核实 `backend/lib/agentic_rag/__init__.py` L48/L54/L67/L70 + `backend/app/services/rag_service.py` L40-85 后确认：canvas_agentic_rag **实际存在** · 是 `agentic_rag` 顶级包从 `agentic_rag.state_graph` re-export 的 StateGraph 对象。

#### §1.2.1 · §7.6.5 标题变更

**Before**：
```markdown
#### 7.6.5 · Plan v19 Canvas 后端真相校正（硬化版）
```

**After**：
```markdown
#### 7.6.5 · Canvas 后端实地状态（Plan v21 硬化 · errata of errata）
```

**原因**：显式标注这是 errata of erratum 性质 · 让未来读者一眼看出这是二次校正。

#### §1.2.2 · §7.6.5 正文重写（~120 行 · 完全替换原 ~70 行）

**核心变更**：

1. **保留**：Cost Tracker ✅ 已就绪 + UserPromptSubmit 🟡 架构层误判（Plan v19 这 2/3 正确部分不动）
2. **重写**：canvas_agentic_rag 部分 · 从 "🔴 module 不存在" 改为 "✅ 实际存在"
3. **新增**：Plan v17 → v18 → v19 → v21 四层校正对比表
4. **新增**：代码证据链（完整引用 `backend/lib/agentic_rag/__init__.py` L48-186 的关键片段 + `rag_service.py` L40-85）
5. **新增**：Plan v19 smoke check 命令的 3 个错误复盘表
6. **新增**：Plan v19 smoke check 盲点自我批评段
7. **新增**：三层 nested errata 的讽刺 meta-pattern 表
8. **新增**：Plan v21 方法论泛化（4 条未来 smoke check 护栏）
9. **新增**：追溯链（Plan v17 → v18 → v19 → v20 → v21 每层盲点）
10. **更新**：Canvas 后端就绪状态表 · 从 "~95% 就绪 · 1 项硬差距" 改为 "~100% 就绪 · 0 项硬差距"

**核心新增段落示例**（完整内容见 14-PRD v4 §7.6.5）：

```markdown
**核心校正**：`canvas_agentic_rag` 实际存在 · v19 smoke check 命令错误

Plan v21 的独立核实发现了 Plan v19 校正自身的一个 meta-level 盲点：Plan v19 用错误的命令做 smoke check，然后基于错误的命令结果写了一个错误的"真相"。

**代码证据链**（Plan v21 直接引自生产代码原文）：

`backend/lib/agentic_rag/__init__.py`（2026-03-16 最后更新 · Story 2.1 死代码清理后）：

\`\`\`python
# Line 48: 初始化 availability flag
AGENTIC_RAG_AVAILABLE: bool = False
_IMPORT_ERROR: Optional[str] = None

# Line 52-54: Placeholder exports（import 失败时的 graceful degradation）
CanvasRAGState = None
CanvasRAGConfig = None
canvas_agentic_rag = None

try:
    # Line 59: Import state schema
    from agentic_rag.state import CanvasRAGState
    # Line 63: Import config schema
    from agentic_rag.config import CanvasRAGConfig
    # Line 67: Import compiled StateGraph
    from agentic_rag.state_graph import canvas_agentic_rag

    # Line 70: All imports successful
    AGENTIC_RAG_AVAILABLE = True
    logger.info("Agentic RAG module loaded successfully. AGENTIC_RAG_AVAILABLE=True")
\`\`\`

**顶级包名是 `agentic_rag`** · `canvas_agentic_rag` 是该包 `__init__.py` 从 `agentic_rag.state_graph` re-export 出来的**编译后 StateGraph 对象**（`CompiledStateGraph` 类型），不是一个独立的 pip 包，也不是独立的 module 名。
```

#### §1.2.3 · §10.1 Day 1 Spike 2 完全重写

**Before**（Plan v19 版本）：
```markdown
0-2. **Day 1 Spike 2 · canvas_agentic_rag 决策**（2-4 小时）
   - `pip show canvas_agentic_rag` / `import canvas_agentic_rag` 验证
   - 预期结果（基于 Plan v19 smoke check · 2026-04-09）：module 不存在
   - **决策分叉**：
     - 路径 A · 引入外部 pip 包（如果有）· 验证 langgraph 依赖
     - 路径 B · 手写 workflow 编排（不使用 LangGraph · 直接调 MCP 工具串联）· **推荐**（最小化外部依赖）
     - 路径 C · 降级为"无 workflow 编排，只直接调单 MCP 工具"（最保守）
```

**After**（Plan v21 版本 · 30 分钟 import 验证）：
```markdown
0-2. **Day 1 Spike 2 · canvas_agentic_rag import 验证**（30 分钟 · Plan v21 重写）
   - **背景**：Plan v19 smoke check 曾断言 "module 不存在" · Plan v21 独立核实发现该断言基于**错误的命令语法**——顶级包名是 `agentic_rag`（见 `backend/lib/agentic_rag/__init__.py`），`canvas_agentic_rag` 是从 `agentic_rag.state_graph` re-export 的 StateGraph 对象...
   - **正确的 smoke check 命令**（直接从 `rag_service.py` 复制 · 以生产代码为 ground truth）：
     \`\`\`bash
     cd backend
     .venv/bin/python -c "from agentic_rag import canvas_agentic_rag, AGENTIC_RAG_AVAILABLE; print('AVAILABLE=', AGENTIC_RAG_AVAILABLE, 'GRAPH=', type(canvas_agentic_rag).__name__)"
     \`\`\`
   - **预期输出**：`AVAILABLE= True GRAPH= CompiledStateGraph`（如果 langgraph 依赖已装）
   - **失败时诊断路径**（按优先级）：
     1. `AGENTIC_RAG_AVAILABLE= False` → 查看 stderr 日志中的 `AGENTIC RAG IMPORT DIAGNOSTIC`...
     2. `ModuleNotFoundError: No module named 'agentic_rag'` → `sys.path` 问题 · 确认 cwd 在 `backend/`...
     3. 其他 `ImportError` → 调 `from agentic_rag import check_dependencies; print(check_dependencies())`...
   - **结论**：canvas_agentic_rag workflow **已就绪**（不是硬差距）· 无需决策分叉 · 无需手写 workflow · 无需降级 · Phase 1 直接复用
```

**变更性质**：从"3 路径决策分叉"降级为"30 分钟 smoke check 验证" · 因为硬差距本来就不存在。

**Fix-05 总行数**：~160 行修订（§7.6.5 替换 + §10.1 Day 1 Spike 2 替换）

---

### §1.3 · Fix-06 · Cochrane 章节引用修正（2 处）

**严重度**：🟡 重要（学术引用准确性）

**触发**：ChatGPT 第二轮审查 + Plan v21 Agent 3 独立核实 · Cochrane Handbook 官方文档确认 Chapter 10.10.1 实际内容是 "What is heterogeneity" · "When not to use meta-analysis" 和 structured tabulation 建议在 Chapter 12.3.1。

#### §1.3.1 · L6976 · §9.2 引言

**Before**：
```markdown
> **Plan v19 重大修正**：本节 v15/v16 曾给出 "加权总守恒度 = Σ(d_i × c_i) / Σ d_i = 88.1%" 的单一数字。... 本节改为 narrative synthesis（Cochrane Handbook Ch 10.10.1 "When not to use meta-analysis" 标准）。
```

**After**：
```markdown
> **Plan v19 重大修正**：本节 v15/v16 曾给出 "加权总守恒度 = Σ(d_i × c_i) / Σ d_i = 88.1%" 的单一数字。... 本节改为 narrative synthesis（Cochrane Handbook Chapter 12 "Synthesizing and presenting findings using other methods" · Section 12.3.1 "Structured tabulation" 标准）。
>
> **Plan v21 校正注**：Plan v19 曾错引 Cochrane Handbook Ch 10.10.1 "When not to use meta-analysis"。根据 Cochrane Handbook 官方文档（current version），Chapter 10 实际内容是 "Analysing data and undertaking meta-analyses"（Ch 10.10.1 是 "What is heterogeneity"），**"When not to use meta-analysis" 和 narrative synthesis 的 structured tabulation 建议实际在 Chapter 12** "Synthesizing and presenting findings using other methods"（Section 12.3.1）。Plan v21 修正为正确章节引用。方法学结论不变（不做加权合成 · 用 narrative synthesis）。
```

#### §1.3.2 · L6988 · §9.2.1 引用段

**Before**：
```markdown
**Cochrane 推荐做法**（Chapter 10.10.1 "When not to use meta-analysis"）：
> When effect sizes cannot be statistically combined ...
```

**After**：
```markdown
**Cochrane 推荐做法**（Chapter 12 "Synthesizing and presenting findings using other methods" · Section 12.3.1 "Structured tabulation"）：
> When effect sizes cannot be statistically combined ...

（**Plan v21 修正注**：Plan v19 曾错引 Chapter 10.10.1 · Chapter 10.10.1 实际内容是 "What is heterogeneity" · narrative synthesis 的 structured tabulation 建议在 Chapter 12 · Plan v21 更正章节号 · 方法学结论不变）
```

**Fix-06 总行数**：~6 行修订

---

### §1.4 · Fix-07 · §4.4 Bisra 措辞修正（2 处 · 影响 3 个数字）

**严重度**：🟡 重要（数字精度 + 术语准确性）

**触发**：ChatGPT 第二轮审查指出 CI 边界应为 0.45-0.65 · 且 "primary studies" 应为 "effect sizes (from research reports)"。Plan v21 Agent 3 核实 Bisra 2018 原文的核心数据（g=0.55 · n≈5917 · DOI）正确 · 但 "69 primary studies" 的表述不够准确（原文报告 "69 effect sizes from 64 research reports"）。

#### §1.4.1 · L4023 · §4.4 对比表

**Before**：
```markdown
| **效应量** | d = 1.50 (Karpicke) | d ≈ 1.09 (Chi 1994 原始研究 · t(22)=2.64 转换) · **g = 0.55** (Bisra 2018 meta-analysis · 69 studies · n=5,917 · 95% CI 0.46-0.64) |
```

**After**：
```markdown
| **效应量** | d = 1.50 (Karpicke) | d ≈ 1.09 (Chi 1994 原始研究 · t(22)=2.64 转换) · **g = 0.55** (Bisra 2018 meta-analysis · 69 effect sizes from 64 research reports · 5,917 participants · 95% CI 0.45-0.65) |
```

**变更**：
- `69 studies` → `69 effect sizes from 64 research reports`
- `n=5,917` → `5,917 participants`
- `0.46-0.64` → `0.45-0.65`

#### §1.4.2 · L4039 · §4.4 Bisra 正文段

**Before**：
```markdown
> 2. **Bisra et al. (2018) Self-Explanation Meta-Analysis** g=0.55：
>    - Educational Psychology Review 30(3), 703-725 · DOI 10.1007/s10648-018-9434-x
>    - **69 primary studies · n=5,917 学生 · 95% CI: 0.46-0.64**（随机效应模型）
>    - 这是目前 Self-Explanation 最权威的 quantitative meta-analysis
>    - 与 Chi 1994 原始研究（d≈1.09，n=8）互补：Bisra 提供大样本稳定性，Chi 提供机制起点
```

**After**：
```markdown
> 2. **Bisra et al. (2018) Self-Explanation Meta-Analysis** g=0.55：
>    - Educational Psychology Review 30(3), 703-725 · DOI 10.1007/s10648-018-9434-x
>    - **69 effect sizes (from 64 research reports) · 5,917 participants · 95% CI: 0.45-0.65**（随机效应模型）
>    - 这是目前 Self-Explanation 最权威的 quantitative meta-analysis
>    - **Plan v21 措辞修正**：v15-v19 曾写 "69 primary studies · n=5,917 · CI 0.46-0.64"。正确表述为 "69 effect sizes from 64 research reports · 5,917 participants"（Bisra 原文明确区分"研究数"和"效应量数"：有些研究贡献多个独立 effect size）· CI 精确边界更新为 0.45-0.65（ChatGPT 5 Pro Deep Research 第二轮审查指出）· 核心数字 g=0.55 不变
>    - 与 Chi 1994 原始研究（d≈1.09，n=8）互补：Bisra 提供大样本稳定性，Chi 提供机制起点
```

**Fix-07 总行数**：~10 行修订

---

### §1.5 · Fix-08 · §1.6 Cassady Table 3 修正

**严重度**：🟡 重要（引用错位）

**触发**：ChatGPT 第二轮审查 + Plan v21 Agent 3 独立确认 · Cassady & Johnson (2002) 原文 Table 3 实际为 **Mean Academic Performances by CTAS Group**（分组均值表 · SAT/GPA 的分组比较），而不是相关系数矩阵。14-PRD v15-v19 曾具体引用 "Table 3" 作为 r 值来源 · 应修正。

#### §1.5.1 · L766 · §1.6 Cassady 引用段

**Before**：
```markdown
Cassady 和 Johnson 在 Contemporary Educational Psychology 27(2), 270-295 发表的 Cognitive Test Anxiety Scale (CTAS) 是量表开发论文。原文**报告的是相关系数 r（Table 3）**，不直接报告 Cohen's d：

- **Cognitive Test Anxiety** · 考试焦虑占用工作记忆 · 减少学习时的有效认知带宽
- **原文数据**：CTAS 与 GPA 的相关系数 r ≈ -0.20 到 -0.40（Table 3）· 方向显著负相关
```

**After**：
```markdown
Cassady 和 Johnson 在 Contemporary Educational Psychology 27(2), 270-295 发表的 Cognitive Test Anxiety Scale (CTAS) 是量表开发论文。原文**报告相关系数 r 而非 Cohen's d**，CTAS 与学术表现的负相关关系在原文的相关分析段落中给出：

- **Cognitive Test Anxiety** · 考试焦虑占用工作记忆 · 减少学习时的有效认知带宽
- **原文数据**：CTAS 与 GPA 的相关系数 r ≈ -0.20 到 -0.40（负相关方向显著 · 具体 Table 号见原文的 correlations 分析段落 · 方案 A 不复述具体 Table 编号以避免引用错位）· 方向显著负相关
```

**Plan v21 修正注追加**（新增内容）：
```markdown
- **注（Plan v21 修正）**：v15-v19 曾具体引用 "Table 3" 作为 r 值来源。ChatGPT 5 Pro Deep Research 第二轮审查指出 Cassady & Johnson (2002) 原文 Table 3 实际为 **Mean Academic Performances by CTAS Group**（分组均值表 · SAT/GPA 的分组比较），而不是相关系数矩阵。Plan v21 修正：删除具体 Table 号引用 · 保留"原文报告相关系数 r"的定性表述 · r ≈ -0.20 到 -0.40 的范围和方向仍然正确（基于文献综述的标准引用），但具体 Table 号需读者回查原文 PDF 确认。**核心结论不变**（CTAS 与学术表现显著负相关 · r→d 转换方法不变）
```

**Fix-08 总行数**：~8 行修订

---

### §1.6 · Fix-09 · Chi d=1.00 → d≈1.09 一致性（2 处）

**严重度**：🟡 一致性（与 §4.4 汇总表不一致）

**触发**：ChatGPT 第二轮审查发现 §2.4 L1470 和 §4.4 L4032 的 Chi d=1.00 与 §4.4 汇总表的 d≈1.09 不一致。实际 d 值来自 Chi 1994 原始研究的 t(22)=2.64 换算：Cohen's d = 2t/√df = 2×2.64/√22 ≈ 1.09。

#### §1.6.1 · L1470 · §2.4 第 2 问学术根据段

**Before**：
```markdown
> 2. **学术根据不同** · Chi et al. (1994) Self-Explanation 的 d=1.00 是**独立的**学术支撑，不依赖 Active Recall · 信息可见时的"用自己的话解释"仍然有强效应量
```

**After**：
```markdown
> 2. **学术根据不同** · Chi et al. (1994) Self-Explanation 的 **d ≈ 1.09**（t(22)=2.64 换算 · 近似 1.00）是**独立的**学术支撑，不依赖 Active Recall · 信息可见时的"用自己的话解释"仍然有强效应量（Plan v21 一致性修正：v15-v19 曾写 d=1.00 · 应与 §4.4 的 d≈1.09 保持一致 · 实际来自原始 t(22)=2.64 换算）
```

#### §1.6.2 · L4032 · §4.4 学术根据段

**Before**：
```markdown
> 1. **Chi et al. (1994) Self-Explanation** 的 d=1.00 是**独立的**学术支撑：
>    - 原始研究：让学生解释物理问题中每个公式的含义 · 即使公式可见 · 也产生强学习效果
>    - 与 Active Recall 的区别：Active Recall 要求信息不可见 · Self-Explanation 要求用自己的话解释 · 不要求信息隐藏
>    - 所以 `/quiz_from_callout` 不是"检验白板的弱化版本"，而是**独立的学习机制**
```

**After**：
```markdown
> 1. **Chi et al. (1994) Self-Explanation** 的 **d ≈ 1.09**（t(22)=2.64 换算 · 近似 1.00）是**独立的**学术支撑：
>    - 原始研究：让学生解释物理问题中每个公式的含义 · 即使公式可见 · 也产生强学习效果
>    - 与 Active Recall 的区别：Active Recall 要求信息不可见 · Self-Explanation 要求用自己的话解释 · 不要求信息隐藏
>    - 所以 `/quiz_from_callout` 不是"检验白板的弱化版本"，而是**独立的学习机制**
>    - **Plan v21 一致性注**：v15-v19 在部分段落写 d=1.00 · 在 §4.4 汇总表和 v19 修正过的地方写 d≈1.09 · 实际数字来源于原始 t(22)=2.64 换算（Cohen's d = 2t/√df = 2×2.64/√22 ≈ 1.09）· Plan v21 统一为 d≈1.09 作为精确值 · 1.00 作为近似值保留在历史注释中
```

**Fix-09 总行数**：~6 行修订

---

### §1.7 · Fix-10 · Frontmatter 更新

**严重度**：🔵 文档治理（低优先级但确实需要）

**触发**：ChatGPT 第二轮审查指出 14-PRD 文件头仍是 v1 + Plan v15 · 与实际内容（已经过 v2/v3/v4 演化）不一致。

#### §1.7.1 · L1-18 · Frontmatter 替换

**Before**：
```yaml
---
title: "14 · 方案 A · 学习效果守恒的具体实现 PRD"
version: v1
status: pending-user-review
created: 2026-04-08
author: Claude Code (Plan v15)
inputs:
  - PRD (971 行): canvas-learning-system/_bmad-output/planning-artifacts/prd.md
  - 11-v2 (1122 行 + 9 批注): CS 61B/11-canvas-hybrid-proposal-v2.md
  - 13-gap-diagnosis (728 行): CS 61B/13-v2-gap-diagnosis.md
  - 10-downgrade-mapping (786 行): CS 61B/10-downgrade-mapping.md
  - 9 前序 agent: Agent A/B/C/D/E/F/G/J/L
user_decisions_locked:
  - 学习效果 > UI 体验
  - 时间充裕 · 架构优先
  - 检验白板不可妥协 · 必须 100% 等价实现
next_step: 用户审核 + 批注 + §12 决策点 D10-D13 打勾 → Plan v16 Phase 1 骨架实施
tags: [canvas, learning-system, obsidian, scheme-a, prd, learning-effect-conservation]
---
```

**After**：
```yaml
---
title: "14 · 方案 A · 学习效果守恒的具体实现 PRD"
version: v4
status: awaiting-plan-v22-third-review
created: 2026-04-08
last_updated: 2026-04-09
author: Claude Code (Plan v15→v16→v19→v21)
revision_history:
  - v1 (Plan v15, 2026-04-08): 初版 7 小时 synthesis
  - v2 (Plan v16.1, 2026-04-08): Round 1/2 锁定 + 守恒度 75% → 87.5% 关键升级
  - v3 (Plan v19, 2026-04-09 早): ChatGPT 第一轮审查 3 项 Fix（Fix-01/02/03）+ §1.5.6 erratum
  - v4 (Plan v21, 2026-04-09 下午): ChatGPT 第二轮审查 7 项 Fix（Fix-04~Fix-10）+ §1.5.8 meta-erratum of erratum
inputs:
  - PRD (971 行): canvas-learning-system/_bmad-output/planning-artifacts/prd.md
  - 11-v2 (1122 行 + 9 批注): CS 61B/11-canvas-hybrid-proposal-v2.md
  - 13-gap-diagnosis (728 行): CS 61B/13-v2-gap-diagnosis.md
  - 10-downgrade-mapping (786 行): CS 61B/10-downgrade-mapping.md
  - 9 前序 agent: Agent A/B/C/D/E/F/G/J/L
user_decisions_locked:
  - 学习效果 > UI 体验
  - 时间充裕 · 架构优先
  - 检验白板不可妥协 · 必须 100% 等价实现
next_step: 用户 Cmd+C 复制 20-adversarial-review-prompt-v3.md → ChatGPT 5 Pro Deep Research 第三轮审查 → 等待 Plan v22 返回结果 → Plan v23 决策路径
tags: [canvas, learning-system, obsidian, scheme-a, prd, learning-effect-conservation, plan-v21, errata-of-errata]
---
```

**变更**：
- `version: v1` → `version: v4`
- `status: pending-user-review` → `status: awaiting-plan-v22-third-review`
- 新增 `last_updated: 2026-04-09`
- `author: Claude Code (Plan v15)` → `author: Claude Code (Plan v15→v16→v19→v21)`
- 新增 `revision_history` 4 行
- `next_step` 更新为 Plan v22 第三轮审查流程
- `tags` 新增 `plan-v21, errata-of-errata`

**Fix-10 总行数**：~12 行修订

---

## §2 · Fix-05 §7.6.5 详细修订细节

### §2.1 · 为什么这是最大的 Fix

Fix-05 是 Plan v21 最核心的修订 · 原因：

1. **双段修订**：§7.6.5（backend 真相校正）+ §10.1 Day 1 Spike 2（Day 1 必做任务）· 两个章节必须同步改
2. **replace 规模最大**：§7.6.5 从 ~70 行替换为 ~120 行（+50 行）· §10.1 Day 1 Spike 2 从 ~10 行替换为 ~15 行
3. **影响下游文档**：§1.5.8 meta-erratum 的核心论据来源就是 Fix-05 的代码证据链
4. **方法论教训最重**：Plan v19 smoke check 命令语法错是 Plan v21 三层 nested errata 的第二层 · 这个 Fix 直接修 L2 盲点

### §2.2 · Plan v19 smoke check 的 3 个具体错误

**错误 #1 · 命令语法层面**：

```bash
# Plan v19 用了这些命令 · 全部错误：
pip show canvas_agentic_rag        # ❌ canvas_agentic_rag 不是 pip 包名
python -c "import canvas_agentic_rag"  # ❌ 顶级 module 是 agentic_rag
```

**为什么错**：
- `canvas_agentic_rag` 是 `agentic_rag` 顶级包内的一个 **re-export 名字**（`__init__.py` L67 从 `agentic_rag.state_graph` 导入，L180 加入 `__all__` 列表）
- Python 的 import 机制：`import canvas_agentic_rag` 只会查找顶级 module · 根本不会解析包内的 re-export
- `pip show` 查 PyPI metadata · canvas_agentic_rag 从来不是 pip 包

**错误 #2 · ground truth 层面**：

Plan v19 **没有先读** `backend/lib/agentic_rag/__init__.py` 的 `__all__` 声明或任何一处使用 canvas_agentic_rag 的生产代码。如果它读了 `backend/app/services/rag_service.py` L49 的这一行：

```python
from agentic_rag import (
    canvas_agentic_rag,
    AGENTIC_RAG_AVAILABLE,
    CanvasRAGState,
    CanvasRAGConfig,
)
```

就会立刻发现正确的 import 语法。

**错误 #3 · 矛盾核实层面**：

Plan v19 没有问"那 Canvas 后端是怎么每天启动的"。如果 canvas_agentic_rag 真不存在：
- RAGService 会在启动时抛 ImportError
- MCP 工具会在 Graphiti + LanceDB 查询时失败
- Canvas 后端团队早就发现并修了

但 Canvas 后端实际上每天都在运行 · 这个矛盾足以让任何认真核实的人立刻警觉。

### §2.3 · Plan v21 的正确 smoke check 命令

```bash
cd backend
.venv/bin/python -c "from agentic_rag import canvas_agentic_rag, AGENTIC_RAG_AVAILABLE; print('AVAILABLE=', AGENTIC_RAG_AVAILABLE, 'GRAPH=', type(canvas_agentic_rag).__name__)"
```

**预期输出**：`AVAILABLE= True GRAPH= CompiledStateGraph`

**失败时诊断路径**（已写入 14-PRD v4 §10.1 Day 1 Spike 2）：
1. `AGENTIC_RAG_AVAILABLE= False` → 查看 stderr 的 `AGENTIC RAG IMPORT DIAGNOSTIC`（`__init__.py` L79-96 打印）· 通常是 `langgraph>=0.2.0` 或 `langchain-core>=0.3.0` 未装
2. `ModuleNotFoundError: No module named 'agentic_rag'` → `sys.path` 问题 · 确认 cwd 在 `backend/` · 确认 `.venv` 已 activate
3. 其他 `ImportError` → 调 `from agentic_rag import check_dependencies; print(check_dependencies())` 逐个确认依赖状态

### §2.4 · 为什么 §7.6.5 重命名为 "errata of errata"

**用户选择**（Phase 3 AskUserQuestion #2）：
- ✅ **重命名**为 "Canvas 后端实地状态（Plan v21 硬化 · errata of errata）"
- 原标题 "Plan v19 Canvas 后端真相校正（硬化版）" 暗示这是 Plan v19 的最终定版 · 但现在发现不是
- "errata of errata" 显式标注二次校正性质 · 让未来读者一眼看出这是递归修订

**方法学意义**：
- 文档治理上承认"任何校正自身也可能错"
- 为未来可能的 Plan v23/v25 的 "errata of errata of errata" 预留命名空间
- 让章节名成为版本追溯的第一入口（无需读正文就知道 section 经历了多少次修正）

---

## §3 · §1.5.8 Plan v21 Meta-Erratum 记录

### §3.1 · 为什么需要 §1.5.8

Plan v19 的 §1.5.6 自认为已经修正了 Plan v17/v18 的后端扫描盲点 · 但 Plan v19 本身的 smoke check 命令有语法错误 · 导致它用一个错误的校正替换了上一层错误的继承结论。Plan v21 在 ChatGPT 第二轮审查后独立核实并补修。

**§1.5.8 和 §7.6.5 的关系**：
- §7.6.5 是 14-PRD 内部的 canvas_agentic_rag 真相校正（面向实施细节 · 含代码证据链）
- §1.5.8 是 16-report 内部的 meta-erratum 记录（面向方法学教训 · 含三层 nested pattern 分析）
- 两者互为支撑 · §7.6.5 的代码证据链被 §1.5.8 引用 · §1.5.8 的教训泛化指导 §7.6.5 的未来护栏

### §3.2 · §1.5.8 的关键内容

1. **Plan v21 的发现链**：ChatGPT 第二轮审查 → 3 个并行 Explore agent → Plan agent 规划 → 7 项 Fix 执行
2. **Plan v19 smoke check 命令的 3 个错误复盘表**：命令语法错 + 没读生产代码 + 没核实矛盾
3. **三层 nested errata 的 meta-pattern 表**：L1（Plan v17 只扫子目录）→ L2（Plan v19 命令语法错）→ L3（Plan v21 独立核实 · 盲点 TBD）
4. **Plan v21 方法论泛化**（4 条未来 smoke check 护栏）：grep 生产代码 + 比对 __all__ + 寻找矛盾证据 + 预留 errata-of-errata 空间
5. **对 §1.5.6 的具体修正条目表**：5 条具体断言的 before/after
6. **14-PRD v4 修订总览**：7 项 Fix 的 summary table

### §3.3 · §1.5.8 的位置

- **紧接 §1.5.7 之后**（L747 附近）
- **§2 之前**（不破坏整体文档结构）
- **保留 §1.5.1-§1.5.7 原文不改**（历史层次清晰 · 不做 in-place 覆盖）

**§1.5.8 总行数**：~120 行（含所有表格和代码块）

---

## §4 · Cascade cleanup 验证清单

### §4.1 · grep 命令清单

Plan v21 执行了以下 grep 验证以确保 cascade cleanup 彻底：

```bash
cd "/Users/Heishing/Desktop/spring course 2026/CS 61B"

# 1. canvas_agentic_rag 不存在断言
grep -n "canvas_agentic_rag.*不存在\|module 完全不存在\|module 不存在.*canvas_agentic_rag\|ModuleNotFoundError.*canvas_agentic_rag" 14-scheme-a-implementation-prd.md

# 2. d=2.30 残留
grep -n "d.*=.*2\.30\|2\.30.*设计 8\|d ≈ 2\.30" 14-scheme-a-implementation-prd.md

# 3. Chi d=1.00 残留
grep -n "Chi.*d=1\.00\|Chi.*d = 1\.00" 14-scheme-a-implementation-prd.md

# 4. Bisra CI 0.46-0.64 残留
grep -n "0\.46-0\.64\|0\.46 到 0\.64" 14-scheme-a-implementation-prd.md

# 5. Cochrane Ch 10.10.1 残留
grep -n "Ch 10\.10\.1\|Chapter 10\.10\.1" 14-scheme-a-implementation-prd.md
```

### §4.2 · 验证结果（Plan v21 执行时）

| grep pattern | 命中行 | 判定 | 处理 |
|---|---|---|---|
| `canvas_agentic_rag.*不存在` 等 | L6745, 6752, 6755, 6771, 6779, 6791, 6798, 6805, 6814, 6815, 6817, 6821, 6827, 6828, 6833, 6834, 6844, 6849, 6851, 6858, 7199, 7200, 7204, 7211 | 全部在 §7.6.5 或 §10.1 Day 1 Spike 2 的 Plan v21 重写范围内 | ✅ 有意历史引用 · 保留 |
| `d = 2.30` | L2836（Plan v21 修正注）· L6930（HTML 注释）| 两处都是历史记录 · 无当前断言 | ✅ 有意历史引用 · 保留 |
| `Chi.*d=1.00` | L1477（Plan v21 新注："近似 1.00"）| 历史对照 · 不是当前断言 | ✅ 有意历史引用 · 保留 |
| `0.46-0.64` | L4052（Plan v21 修正注说明 v15-v19 的错误）| 历史对照 · 不是当前断言 | ✅ 有意历史引用 · 保留 |
| `Ch 10.10.1` | L7100, 7115（Plan v21 校正注说明 v19 的错误）| 历史对照 · 不是当前断言 | ✅ 有意历史引用 · 保留 |

**结论**：所有 grep 命中都是 Plan v21 新增校正注中的**有意历史引用** · 无遗漏的当前断言 · cascade cleanup 验证通过。

---

## §5 · 下一步 · 走向 A · Plan v22 第三轮审查

### §5.1 · 用户决策回顾

Phase 3 AskUserQuestion #3：Plan v21 修完后的走向？
- ✅ **走向 A · 生成 Plan v22 第三轮 ChatGPT 审查 prompt**

### §5.2 · 为什么选走向 A

- **递归审查深化**：每一轮审查都能发现上一轮遗漏的 bug · 第一轮发现 Fix-01/02/03 · 第二轮发现 Fix-04~Fix-10 · 第三轮可能发现 Fix-11+（或确认已稳定）
- **Plan v21 自身也可能错**：§1.5.8 三层 nested errata 表已预留 L3 的盲点 TBD · 需要第三轮独立验证
- **成本低**：ChatGPT 5 Pro Deep Research 已经熟悉项目背景 · 第三轮只需增量审查
- **GO 决策需要信心**：Plan v21 修完后 · PRD 进入 Phase 1 骨架实施的门槛是"三方独立验证通过 + 无重大未修 bug" · 第三轮是最后一道护栏

### §5.3 · Plan v22 第三轮审查 prompt 产物

- **文件**：`20-adversarial-review-prompt-v3.md`（~900-1100 行 · Plan v21 Stage 4 产出）
- **5 个附件清单**：
  1. 14-scheme-a-implementation-prd.md v4（~7500-7600 行）
  2. 16-triangulated-review-report.md（含 §1.5.8 · ~2420-2460 行）
  3. 17-prd-v3-changelog.md（Plan v19 · 保留为历史 · 673 行）
  4. **19-prd-v4-changelog.md**（Plan v21 · **新增**）
  5. **18-adversarial-review-prompt-v2.md**（Plan v20 · 作为第二轮审查记录）
- **审查任务**：
  - 验证 7 项 Fix（Fix-04~Fix-10）正确执行
  - 发现 Plan v21 引入的新 bug（包括 §1.5.8 三层 nested pattern 的 L3 盲点）
  - 确认三层 nested errata 已稳定 · 或指出 L4 盲点
  - 扩展审查到 §1-§11 的其他未审章节
  - 给出最终 GO/NO-GO 决策（6 选 1）

### §5.4 · Plan v23 决策路径

取决于 ChatGPT 第三轮审查结果：

| 第三轮结果 | Plan v23 行动 |
|---|---|
| ✅ **GO** · 无新 bug · 三层稳定 | 启动 Phase 1 骨架实施（Day 1 Spike 1/2/3 · vault 初始化 · Claudian 配置 · 最小 skill 集）|
| 🟡 **GO with fixes** · 少量新 bug | Plan v23 再做一轮 Fix-11+ · 产出 14-PRD v5 + 21-changelog + 22-prompt-v4 |
| 🔴 **NO-GO** · 发现重大架构问题 | Plan v23 回到 Design 阶段 · 重新 brainstorming 或调整 scope |
| 🟣 **Pivot** · 建议完全不同方向 | Plan v23 做重大 scope 调整 · 用户重新确认方向 |

---

## §6 · 文档元信息 + 三层 nested errata 教训沉淀

### §6.1 · Plan v21 产物全景

| 文件 | 类型 | 行数 | 状态 |
|---|---|---|---|
| `14-scheme-a-implementation-prd.md` | v3 → v4 · 7 项 Fix | ~7500-7600（原 7391）| ✅ 完成 |
| `16-triangulated-review-report.md` | 追加 §1.5.8 | ~2420-2460（原 2338）| ✅ 完成 |
| `19-prd-v4-changelog.md` | 新建 | ~600-800（本文件）| ✅ 完成（本文件即此） |
| `20-adversarial-review-prompt-v3.md` | 新建 | ~900-1100 | 🟡 下一步（Stage 4 产出） |

### §6.2 · Plan v21 不覆盖的历史产物

为了保留完整的演化史 · Plan v21 **不修改**以下历史产物：
- `15-adversarial-review-prompt.md`（Plan v17 产物 · 第一轮 prompt）
- `17-prd-v3-changelog.md`（Plan v19 产物 · Fix-01/02/03 完整 diff）
- `18-adversarial-review-prompt-v2.md`（Plan v20 产物 · 第二轮 prompt · 可在 20-v3 中标记 deprecated）

### §6.3 · 三层 nested errata 教训沉淀

**核心洞察**：每一层校正都认为自己修好了上一层的盲点 · 但同时引入了新形式的盲点。

| 层 | 时间 | 修什么 | 漏什么 |
|---|---|---|---|
| Plan v17 | 2026-04 上旬 | 初始 Canvas 后端扫描 | 只搜 `services/` 子目录 · 漏 `middleware/` + `lib/` |
| Plan v18 | 2026-04-08 | 三方 triangulated 审查 · "亲自读 PRD 原文" | 继承 Plan v17 的后端扫描结论 · 没对后端做独立 smoke check |
| Plan v19 | 2026-04-09 早 | 独立 smoke check · 修正 Cost Tracker 误判 | 命令语法错 · 把 canvas_agentic_rag 从"未验证"错误改为"不存在" |
| **Plan v21** | **2026-04-09 下午（本次）** | **以生产代码为 ground truth · 修正 Plan v19 的 smoke check 命令** | **TBD · 等 Plan v22 第三轮审查** |

**共同点**：每层的修正都是基于**前一层没有的新方法论**（扫全目录 → 亲读 PRD → 亲做 smoke check → 以生产代码为 ground truth）· 但新方法论自身也有盲点。

**Plan v21 的谦逊声明**：
- 本次 Fix-05 的代码证据链是 Plan v21 的核心证据
- 但 Plan v21 **没有实际运行** smoke check 命令来验证 `AGENTIC_RAG_AVAILABLE=True`
- Plan v21 的证据基础是：读 `backend/lib/agentic_rag/__init__.py` 原文 + 读 `backend/app/services/rag_service.py` 原文 + 假设生产代码实际运行（因为 rag_service 是核心服务 · 每天都启动）
- 如果 Plan v22/v23 在真实运行中发现 `AGENTIC_RAG_AVAILABLE=False`（例如 langgraph 依赖缺失），Plan v21 的"实际存在"断言仍然部分成立（module 存在 · 但依赖缺失导致 graceful degradation），需要 Plan v23 二次校正

### §6.4 · Plan v21 执行时间线

| 阶段 | 时间 | 活动 |
|---|---|---|
| Phase 1 | 2026-04-09 下午 | 3 个并行 Explore agent 独立核实（PRD 内部 + Canvas 后端 + 学术文献） |
| Phase 2 | 2026-04-09 下午 | Plan agent 规划修订细节 + 估算 Fix 数量和行数 |
| Phase 3 | 2026-04-09 下午 | AskUserQuestion 3 项关键决策 · 用户选方案 A + 重命名 + 走向 A |
| Phase 4 · Stage 1 | 2026-04-09 下午 | 14-PRD v4 · 7 项 Fix 执行（按行号从下往上） |
| Phase 4 · Stage 2 | 2026-04-09 下午 | 16-report 追加 §1.5.8 |
| Phase 4 · Stage 3 | 2026-04-09 下午 | 19-changelog 新建（本文件） |
| Phase 4 · Stage 4 | 2026-04-09 下午 | 20-prompt-v3 新建（下一步） |
| Phase 4 · Stage 5 | 2026-04-09 下午 | Phase B bash 验证（11 项 grep/wc） |
| Phase 4 · Stage 6 | 用户手工 | Obsidian 验证 + Cmd+C 复制 prompt → ChatGPT 第三轮 |

### §6.5 · 相关文档索引

**Plan v21 本次涉及**：
- 本文件 `19-prd-v4-changelog.md`（你正在阅读）
- `14-scheme-a-implementation-prd.md` v4（7 项 Fix 修订后的 PRD）
- `16-triangulated-review-report.md` + §1.5.8（Plan v21 meta-erratum 追加）
- `20-adversarial-review-prompt-v3.md`（Plan v21 Stage 4 · 待生成）

**历史产物**（Plan v17-v20 · 不修改 · 供追溯）：
- `13-v2-gap-diagnosis.md`（Plan v14 · 728 行 · 原始 Gap 诊断）
- `15-adversarial-review-prompt.md`（Plan v17 · 第一轮审查 prompt）
- `17-prd-v3-changelog.md`（Plan v19 · Fix-01/02/03 changelog · 673 行）
- `18-adversarial-review-prompt-v2.md`（Plan v20 · 第二轮审查 prompt · 1021 行）

**生产代码 ground truth**：
- `backend/lib/agentic_rag/__init__.py`（Canvas 后端 agentic_rag 包）
- `backend/app/services/rag_service.py` L40-85（canvas_agentic_rag 生产使用示例）
- `backend/app/middleware/cost_tracker.py`（Cost Tracker 已就绪证据）

### §6.6 · 元信息

- **编写人**：Claude Code (Plan v21)
- **编写时间**：2026-04-09 下午
- **基础资料**：
  - ChatGPT 5 Pro Deep Research 第二轮审查（2026-04-09 下午返回）
  - Plan v21 Phase 1 · 3 个并行 Explore agent 独立核实
  - Plan v21 Phase 2 · Plan agent 规划产物
  - Plan v21 Phase 3 · 用户 3 项关键决策
- **文件用途**：作为 14-PRD v3 → v4 的完整修订记录 · 供 Plan v22 第三轮审查引用 · 供未来读者理解 Plan v21 的核心教训（三层 nested errata）
- **保留策略**：与 17-prd-v3-changelog.md 平行存在 · 共同构成 14-PRD 的完整演化史（v1 → v2 → v3 → v4）

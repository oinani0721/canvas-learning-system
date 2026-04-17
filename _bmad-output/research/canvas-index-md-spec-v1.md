---
title: "Canvas Vault index.md 规范 v1"
date: 2026-04-13
trigger: "Story 1.3 line 55 用户批注 N2"
related_research: "karpathy-graphify-insights-2026-04-13"
based_on:
  - "Karpathy llm-wiki gist 原文"
  - "Canvas 白板/检验白板/批注结构深挖（N2a Agent 报告）"
  - "Obsidian 社区 MOC + Catalog 最佳实践"
type: "design-spec"
status: "deprecated-v1-superseded-by-round2"
superseded_by:
  - "[[obsidian-qa-round2-claude-answers-2026-04-14#R2-Q0-6-1-原白板为什么按-Concepts-Proofs-Gotchas-分组]]"
  - "[[obsidian-qa-round2-claude-answers-2026-04-14#R2-Q17-原白板节点内容真实定义]]"
deprecated_on: "2026-04-14"
---

# Canvas Vault index.md 规范 v1

> ⚠️ **[作废警示 2026-04-14]** 本文件的"Concepts / Proofs / Gotchas"分组方案 + mastery 分组排序 **偏离原 PRD**。
>
> **Explore 1 调研确认**：
> - 原 PRD **无节点分组展示规定**（Grep 零结果）— 分组属前端 UX 自由度
> - "Concepts / Proofs / Gotchas" 是我从 Karpathy `llm-wiki` gist 搬的，**非 PRD 原生**
> - 用户 round-2 Q0.6.1 明确指出此偏离
>
> **Round-2 正式决议**:
> - 分组展示交给用户按学科自定义（CS 用 概念/算法/易错点；数学用 定义/定理/反例；文学用 人物/主题/引文）
> - 原白板节点内容遵循 PRD Line 280-282 + 738-741（`source` + `content_type` + metadata）
>
> 详见 [[obsidian-qa-round2-claude-answers-2026-04-14#R2-Q0-6-1-原白板为什么按-Concepts-Proofs-Gotchas-分组|📚 R2-Q0.6.1]] + [[obsidian-qa-round2-claude-answers-2026-04-14#R2-Q17-原白板节点内容真实定义|📚 R2-Q17]]。
>
> **本文件保留供历史追溯**，不可作为实施依据。

> **用途**：定义 Canvas Learning System 中 `vault/index.md` 的生成规则、字段清单、更新机制。
> **触发**：Story 1.3 line 55 用户批注 N2（"index.md 归纳什么？"+ 明确要求 2 并行 Agent deep explore）

## 核心定位（一句话）

**index.md 回答"Hiching 现在该刷哪几个节点？"，不是"文件系统 ls"。**

它是 AI 冷启动时的**学习导航路标**，不是节点列表目录。

## 对用户 2 选 1 的答案

| 用户猜测 | 判决 | 理由 |
|---|---|---|
| 1. 表示原白板的节点或检验白板的节点 | 🟡 **部分正确** | 节点索引是底座，但只做到这一步 = 没用到 Canvas 的学习数据 |
| 2. 归纳批注，方便考察 | ❌ **不应这样做** | 批注**全文**不该放 index.md（太重）；批注**热点统计**可以放 |

**真答案：1 + 2 + 学习数据，三者融合。**

## 融合来源

| 来源 | 提供什么 |
|---|---|
| Karpathy llm-wiki（权威定义） | catalog 架构 + LLM 自动维护 + `- [[link]] — one-liner (metadata)` 格式 |
| Canvas 白板 / 检验白板 | 概念节点索引 + exam_board 索引 |
| Canvas 学习数据（FSRS/BKT/mastery） | mastery 分组（🔴🟡🟢） + exam 历史 + 批注热点 |

## 完整结构（带示例）

````markdown
---
auto_generated: true
maintained_by: claude-code
last_updated: 2026-04-13T14:23:00Z
total_concepts: 234
total_exam_boards: 18
schema_version: v1
---

# Canvas Vault Index

## 📊 学习概况
- 总概念数：234
- 已掌握：89（38%）
- 学习中：112（48%）
- 薄弱点：33（14%）
- 最近一次考察：2026-04-10

## 🔴 Weak (mastery < 0.5) — 优先复习
- [[LLRB 树]] — 红黑树的左倾变种 · mastery 0.32 · 3 errors · last_exam 2026-04-10 · tags: `type/concept` `state/weak`
- [[DFA 最小化]] — 等价类合并算法 · mastery 0.41 · 1 error · tags: `type/concept` `state/weak`

## 🟡 Learning (0.5 ≤ mastery < 0.8)
- [[2-3 树]] — 多路平衡搜索树 · mastery 0.67
- [[字符串匹配 KMP]] — 跳转表优化 · mastery 0.71

## 🟢 Mastered (mastery ≥ 0.8)
- [[BST 基础]] — 二叉搜索树基础 · mastery 0.91
- [[归并排序]] — 分治递归 · mastery 0.88

## 🎓 Entities（人/课程/教材）
- [[Prof. Hug]] — CS 61B Spring 2026 主讲
- [[CS 61B]] — UC Berkeley 数据结构课

## 📝 Recent Exams（最近 5 次）
- [[exam-2026-04-10]] — LLRB + 2-3 树对应关系 · score 3/5 · 涉及 [[LLRB 树]] [[2-3 树]]
- [[exam-2026-04-08]] — DFA 最小化 · score 2/5

## 🔥 Annotations 热点（批注密度 top 10 — 用于考察出题）
- [[LLRB 树]] — 7 条批注（4 tip · 2 error · 1 relation）
- [[DFA 最小化]] — 5 条批注（3 error · 2 tip）

## 📚 Sources（文档/论文/视频累计）
- 16 篇论文（见 [[papers-index]]）
- 47 节课程视频（见 [[lectures-index]]）
- 3 本教材章节（见 [[textbooks-index]]）
````

## 字段规范

### Frontmatter 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `auto_generated` | boolean | ✅ | 必须为 `true`（AI 维护） |
| `maintained_by` | string | ✅ | `"claude-code"` 或 `"user"` |
| `last_updated` | ISO datetime | ✅ | 最近一次增量更新 |
| `total_concepts` | int | ✅ | 当前节点总数 |
| `total_exam_boards` | int | ✅ | exam_board 总数 |
| `schema_version` | string | ✅ | 版本（当前 `v1`） |

### Section 清单

| Section | 必选 | 内容 | 排序规则 |
|---|---|---|---|
| 📊 学习概况 | ✅ | 统计数据 | 固定顺序 |
| 🔴 Weak (<0.5) | ✅ | 薄弱节点 | mastery **升序**（最低在前） |
| 🟡 Learning | ✅ | 学习中节点 | mastery **降序** |
| 🟢 Mastered | 🔲 可省 | 已掌握节点 | last_exam **降序** |
| 🎓 Entities | 🔲 可选 | 人/课程/教材 | 字母序 |
| 📝 Recent Exams | ✅ | 最近 5 次 exam_board | 时间 **降序** |
| 🔥 Annotations 热点 | ✅ | 批注密度 top 10 | 批注数 **降序** |
| 📚 Sources | 🔲 可选 | 文档索引 | 分类 |

### 单条节点格式

```
- [[NodeName]] — 一句话摘要（< 60 字）· mastery X · 可选 metadata · tags: ...
```

**硬约束**：
- `[[NodeName]]` 必须 Obsidian wikilink 格式
- 摘要 **< 60 字**，不含换行
- metadata 部分用 `·`（中文点号）分隔
- tags 列出 1-3 个，用反引号 `` ` `` 包裹

## 更新机制

### 自动更新触发点

| 触发事件 | 更新范围 |
|---|---|
| `/ingest` 新笔记 | 相关 section 追加条目 |
| exam_board 完成 | 更新 mastery 分组 + Recent Exams |
| 批注被添加/触发 | 更新 Annotations 热点 |
| 每周一次全量 rebuild | 修复 drift |

### 更新主体

- **LLM（Claude Code）自动维护**
- 用户**不手写** index.md（写了会被下次 rebuild 覆盖）
- 如需定制 schema，改 `CLAUDE.md` 里的 index 规则

### Drift 检测

借鉴 Karpathy `/second-brain-lint` 思路：
- 定期检查 index.md 和实际 vault 是否一致（节点数、mastery 值、exam 记录）
- 发现不一致 → 自动 rebuild 相关 section
- 记录到 `log.md`

## 对应 MCP 工具

Story 1.3 建议新增**第 9 个工具**（P0 优先级，见研究文档 Part 4）：

```python
def read_index() -> str:
    """
    返回 vault/index.md 全文。
    AI 冷启动首选工具 — 先读 index 找相关页，再 drill into 具体 page。
    """
    return Path("vault/index.md").read_text()
```

## 和 log.md 的分工

| 文件 | 内容组织 | 格式 | 用途 |
|---|---|---|---|
| **index.md** | 按 category 分组 | `- [[link]] — 摘要` | 找内容 / 学习导航 |
| **log.md** | 按时间 append-only | `## [2026-04-13] ingest \| Title` | 追踪时间线 / 操作审计 |

两者是"空间索引" vs "时间索引"的关系，互不替代。

## 开放问题（等你批注）

1. **MOC (Map of Content) 是否独立于 index.md？** 还是融合进来？Obsidian 社区两派做法都有
2. **Entities section 是否要拆分** — 人/课程/教材 各一个子 section？还是一起列？
3. **Sources section 精细度** — 只列索引文件，还是列最近访问的 5 个？
4. **mastery 分组阈值** — 0.5 / 0.8 是否可配置？（CS 课程要求高 vs 文学课程可松）

## 来源

- [Karpathy llm-wiki 原 gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — 权威定义
- [antigravity.codes — Karpathy llm-wiki idea file 复刻](https://antigravity.codes/blog/karpathy-llm-wiki-idea-file) — 含字面示例
- [VentureBeat — LLM Knowledge Base architecture](https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an) — LLM 自动维护动机
- [NicholasSpisak/second-brain — 社区实现 second-brain-lint](https://github.com/NicholasSpisak/second-brain) — drift 修复参考
- [Obsidian MOC Complete Guide](https://www.dsebastien.net/2022-05-15-maps-of-content/) — MOC vs index 差异

---

## Changelog
- 2026-04-13: 初版（v1），响应 Story 1.3 line 55 批注 N2（含 2 并行 Agent deep explore）

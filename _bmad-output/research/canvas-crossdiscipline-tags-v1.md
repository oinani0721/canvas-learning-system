---
title: "Canvas 跨学科通用 tag 体系 v1"
date: 2026-04-13
trigger: "Story 1.3 line 62 用户批注 N3"
related_research: "karpathy-graphify-insights-2026-04-13"
based_on:
  - "Andy Matuschak — Taxonomy of note types"
  - "Zettelkasten — fleeting/literature/permanent"
  - "Sönke Ahrens — How to Take Smart Notes"
  - "PARA Method (Tiago Forte)"
  - "Anki FSRS mature/learning 状态"
  - "dsebastien.net — type/ namespace 最佳实践"
type: "design-spec"
status: "deprecated-v1-superseded-by-round2"
superseded_by: "[[obsidian-qa-round2-claude-answers-2026-04-14#R2-Q16-Karpathy-仅作参考-Canvas-主体落地]]"
deprecated_on: "2026-04-14"
---

# Canvas 跨学科通用 tag 体系 v1

> ⚠️ **[作废警示 2026-04-14]** 本文件的 4 维正交 tag 体系（`type/*` `state/*` `src/*` `todo/*`）**偏离原 PRD**。
>
> **Explore 1 调研确认**（3 并行 Agent，参考 [[squishy-purring-hoare|Plan OBSIDIAN-QA-ROUND2-2026-04-14]]）：
> - 原 Tauri PRD **无独立 tag 体系**（Grep 零结果）
> - "理解程度 3 态"**不在 PRD**（用户 round-2 Q8 明确指出）
> - PRD 只有 `group_id` + `subject` + `source` + `content_type` + `mastery_score` + `fsrs_*` frontmatter 字段
>
> **Round-2 正式决议**: 撤回 4 维 tag，采纳 PRD 原生 frontmatter 字段 + 轻量 `#board/<name>` 单前缀 tag。详见 [[obsidian-qa-round2-claude-answers-2026-04-14#R2-Q16-Karpathy-仅作参考-Canvas-主体落地|📚 R2-Q16 新方案]]。
>
> **本文件保留供历史追溯**，不可作为实施依据。

> **用途**：定义 Canvas Learning System 笔记的 tag 规则，支持 CS / 数学 / 物理 / 文史哲 / 艺术 / 语言 等所有学科。
> **触发**：Story 1.3 line 62 用户批注 N3（"proof/gotcha 偏 CS，Canvas 不止于 CS"）

## 用户指出的问题

| 旧 tag | 跨学科测试 | 判决 |
|---|---|---|
| `concept:` | ✅ CS/数学/文史哲全通 | **保留** |
| `proof:` | ❌ 历史/文学没"证明"一说 | **淘汰** |
| `gotcha:` | ❌ 编程术语 | **改名** |
| `review:` | ✅ 所有学科都有复习 | **保留** |

**用户是对的**。旧设计用 CS 术语锁死了跨学科未来。

## 核心设计原则（基于调研）

1. **正交维度** — 4 维互不重叠，一个 note 可同时挂多维度 tag
2. **`type/` 命名空间** — 前缀清晰，grep/MCP 过滤友好
3. **学科无关** — 不用 CS 特化术语（proof/gotcha/algorithm）
4. **学习元信息单独成维度** — 不污染内容类型
5. **组合优于细分** — 用 2-3 个 tag 叠加表达，不造 100 个专有 tag

## 4 维正交体系

### 维度 1：笔记角色 `type/*`

**基于 Zettelkasten (Ahrens) + Andy Matuschak taxonomy**

| Tag | 含义 | 学科适用示例 |
|---|---|---|
| `type/concept` | 核心概念定义（通用） | CS "AVL 树" / 哲学 "本体论" / 物理 "角动量" |
| `type/claim` | 声明式命题（**替代 proof**） | 数学定理 / 历史观点 / 文学论断 / 哲学论证 |
| `type/question` | 存疑问题（Matuschak "questions as notes"） | "LLRB 为什么一定左倾？" / "拿破仑为何兵败俄国？" |
| `type/example` | 实例 / 案例 / 习题 / 史料 / 文本片段 | CS 题目 / 数学证明步骤 / 历史事件 / 诗歌段落 |
| `type/reference` | 来源引用（literature note） | 引用论文 / 教材 / 视频 |
| `type/moc` | Map of Content 索引节点 | 自建导航页 |
| `type/fleeting` | 未整理的临时想法（Zettelkasten 原语） | 课堂灵感 / 随手记 |

### 维度 2：学习状态 `state/*`

**基于 Anki FSRS mature/learning 模式 + Canvas 掌握度**

| Tag | 含义 |
|---|---|
| `state/new` | 新建，未学 |
| `state/learning` | 学习中 |
| `state/mastered` | 已掌握（等价 Anki mature ≥ 21 天） |
| `state/weak` | 薄弱点（**替代 gotcha，跨学科通用**） |
| `state/confused` | 混淆点（元认知层，易错） |

### 维度 3：输入来源 `src/*`

**保留 Karpathy `watch:` / `listen:` / `read:` 风格**

| Tag | 含义 |
|---|---|
| `src/read` | 书 / 论文 / 教材 |
| `src/watch` | 视频 / 讲座录像 |
| `src/listen` | 播客 / 音频讲座 |
| `src/lecture` | 现场课堂笔记 |
| `src/exercise` | 习题 / 作业 |

### 维度 4：活动状态 `todo/*`

**基于 PARA (Tiago Forte)**

| Tag | 含义 |
|---|---|
| `todo/review` | 待复习（由 FSRS 调度触发） |
| `todo/exam` | 待考察 |
| `todo/expand` | 待深化（fleeting → permanent） |
| `todo/link` | 待建立关联 |

## 跨学科组合示例

| 学科 | 场景 | Tag 组合 |
|---|---|---|
| CS | 算法定义 | `type/concept` · `state/learning` · `src/read` |
| 数学 | 定理证明 | `type/claim` · `type/example` · `state/mastered` |
| 文学 | 人物分析 | `type/claim` · `state/learning` · `src/read` |
| 历史 | 事件记述 | `type/example` · `state/weak` · `src/watch` |
| 哲学 | 论证展开 | `type/claim` · `type/question` · `state/confused` |
| 艺术 | 流派特征 | `type/concept` · `src/watch` · `state/learning` |
| 语言 | 语法点 | `type/concept` · `state/weak` · `todo/review` |
| 物理 | 实验记录 | `type/example` · `src/lecture` · `state/mastered` |

✅ **8 学科均覆盖**，无需新 tag。

## 旧 tag 迁移表

| 旧 tag | 保留？ | 新归位 | 理由 |
|---|---|---|---|
| `concept:` | ✅ 保留 | `type/concept` | 通用，无问题 |
| `proof:` | ❌ 淘汰 | 拆为 `type/claim` + `type/example` | 历史/文学无"证明"；命题用 claim，推导过程用 example |
| `gotcha:` | 🔄 改名 | `state/weak` | "薄弱点"跨学科通用 |
| `review:` | ✅ 改位 | `todo/review` | "待复习"属活动状态维度，更精确 |

## 实施要点

### Obsidian 原生支持

- Obsidian 的 tag 系统**原生支持前缀**（`#type/concept` 会自动分层）
- 右侧 tag panel 自动显示为树结构
- **零代码改动**

### MCP 工具按 tag 过滤

Story 1.3 的 MCP 工具可按 tag 过滤：

```python
# 找所有薄弱的课堂笔记
get_notes_by_tags(tags=["state/weak", "src/lecture"])
# 找所有待考察的概念
get_notes_by_tags(tags=["type/concept", "todo/exam"])
```

### 前端显示（Canvas 视图）

节点右上角显示前 3 个 tag 的彩色点：

| 维度 | 颜色 |
|---|---|
| `type/*` | 🔵 蓝 |
| `state/*` | 🔴 红 |
| `src/*` | ⚫ 灰 |
| `todo/*` | 🟢 绿 |

## 避免陷阱

### Andy Matuschak 的警告

Matuschak 反对过度用 tag（认为应该用 wikilinks 建立关联）。所以：

- ✅ **tag 只用于分类 / 过滤**（这个笔记属于哪类？）
- ✅ **关联仍用 wikilinks**（这个笔记和哪些笔记相关？）
- ❌ 不要用 tag 表达"A 和 B 相关" — 那是 wikilink 的事

### 不造学科特化 tag

- ❌ 不要 `math/theorem` / `cs/algorithm` / `history/event`
- ✅ 学科信息放 frontmatter 的 `subject: math` 字段，**不污染 tag 空间**
- 好处：新学科进来不用扩 tag schema，只改 frontmatter 枚举

## 来源

- [Andy Matuschak — Taxonomy of note types](https://notes.andymatuschak.org/Taxonomy_of_note_types)
- [Andy Matuschak — Tags are an ineffective association structure](https://notes.andymatuschak.org/Tags_are_an_ineffective_association_structure)
- [dsebastien.net — type/ namespace 最佳实践](https://www.dsebastien.net/2022-05-17-why-and-how-to-tag-notes-in-your-pkm/)
- [Zettelkasten types of notes](https://zk.zettel.page/types-of-notes)
- [Anki FSRS forum — mature/learning 状态](https://forums.ankiweb.net/t/how-to-use-the-next-generation-spaced-repetition-algorithm-fsrs-on-anki/25415)
- [PARA Method (Tiago Forte)](https://fortelabs.com/blog/para/)
- [Obsidian Forum — Questions-Claim-Evidence Discourse Graph](https://forum.obsidian.md/t/questions-claim-evidence-discourse-graph-in-obsidian/48685) — 人文学科 QEC 方法

## 开放问题（等你批注）

1. **`subject/*` 是否该作为第 5 维度？** — 或保留在 frontmatter 足够？
2. **老笔记迁移策略** — 批量脚本自动加新 tag？还是边学边改？
3. **`state/*` 是否和 FSRS 自动同步？** — FSRS 状态变化时 tag 自动更新？
4. **`type/moc` 生成策略** — 自动 vs 手动？

---

## Changelog
- 2026-04-13: 初版（v1），响应 Story 1.3 line 62 批注 N3

**User：Karpathy 的方式我们当然可以学习，但是 prd-tauri-archived-20260401.md ，你能从我们原本的 PRD 的思路中可以得知，我们 Canvas learning systeam 就是只会分为 3 种数据库，一个是我们的放着我们学科的所有资料的数据库，一个是放着我们原白板的数据库，一个是放着我们检验白板的数据库。**
**我觉得 Graphsify 可以用来处理我们的笔记资料，让他可以更好的被 claudian 检索来回复我**
		**然后 Karpathy 的做法我们 可以用于原白板和检验白板，已知我们现在的节点就是我们 md 文档，节点之间的关系就是我们用双向链接来连接，然后那么作为我们原本的白板是不是用来作为呈现各个节点所需要用的 index.md 的文件？本身也可以作为一个 wiki 目录专门记载各个节点之间的关系，然后我在剖析各个节点之间的关系时，然后 节点之间的关系会更新，那么 index.md 文档也会更新**
		**检验白板也是可以这样的思路；这是我提出新的思路，同时我想要知道我们原来的 PRD 和 Story 是怎么处理这一部分的内容的。**
		**2，还有关于 Tag 的问题，请你解释一下你的 Tag 在我们目前 story 的规划中是怎么使用的，请你先和我解释一下，因为我觉得和我的prd-tauri-archived-20260401.md 原本的 Canvas learning systeam 的学习思路有点出现了偏移，请你先阐述和对比向我增量提问包括research/canvas-index-md-spec-v1.md 里面的学科tag 体系我也觉得不太对劲
		
		


**User：我首先打开了 obsidian ，然后里面是收集好了，我的课程的所有相关的资料，然后我是从题目入手来自上而下的学习，所以我会在还没有看上课学习资料的情况下来直接解题，那么首先这时候，我就会选择题目，然后丢到原白板上作为一个节点，那么我首先是没有解这些题目的前置知识，所以我需要 ai 提供关于解这道题目的思路以及过程，还有解这道题目所需要的相关的知识点以及和解题思路相关的笔记，这时候你就是可以从 obsidian 里面我专门放着学习资料的文件夹里面精确的返回了相关的笔记片段，这时候我就可以点击你给我提供的双向链接进行跳转阅读了；对于你提供的笔记，以及解题的思路我不懂的地方，我会继续向ai 提问，也会调用我设置好的解释 skill，来让 ai 继续向我解释，或者我让 ai 针对我的疑问来返回更多的有针对性的笔记来补充我的疑问点，我在和 ai 对话的过程中，我会把我有价值的疑问，当作批注直接写在了当前的节点上，同时我也会把 ai 相关的有价值的解释我也会通过复制或者个人总结来粘贴到当前的节点上；然后如果我发现当前讨论的内容，有些知识点对于我来说实际上太难理解了，拿我会选择把这部分内容单独的拉出来作为一个新的节点然后也是和当前的节点进行连接的，对于新的节点我会单独又开了一个新的上下文窗口专门用于讨论和剖析，一样的提问，看解释，以及看相关的笔记返回。以上这里就是关于原白板的一个剖析的核心流程。**

**然后检验白板又是怎么回事，一样的，我会开出一个检验白板，这个检验白板专门是来检验我在原白板的剖析过程中是否真正的理解，你可以根据我原白板的剖析过程来提问考察我，如果以题目为例子，你是可以明显的看出来我在原白板剖析题目过程中，提出的疑问，不解的知识点，以及还有缺失的解题思维，所以检验白板的考察最终目的，就是我提出的疑问，不解的知识点，以及还有缺失的解题思维，是否都是已经真正掌握了，然后最终的目的就是再次解同样的类型题目时，再也不会犯下相同的错误，这是检验白板所需要的设计的考核目的，然后检验白板在使用的过程中，如果出现了新的疑问的话，那么是可以拖出来单独讨论的，然后也是链接会原白板作为一个新的节点**

**然后再次切换到的是 FERS，我每次可以通过使用检验白板来明白我对原白板的知识点的掌握程度，然后 FERS 是可以让我精确明白每天要复习哪些白板，避免原本掌握的白板知识点，因为时间流失而遗忘，所以我要知道重新对相关的原白板开检验白板的时机。**

User：
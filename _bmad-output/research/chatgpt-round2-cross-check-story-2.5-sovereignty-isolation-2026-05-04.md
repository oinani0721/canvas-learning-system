# ChatGPT Round-2 Cross-Check — Story 2.5 Sovereignty + Isolation

> **本文档是给 ChatGPT 的 Round-2 prompt**。我们用 4 个并行 Explore agent + WebFetch + Context7 cross-check 了你 Round-1 的所有论断。整体准确度 9/10，但发现 2 个关键 caveat 影响最终决策。请基于本 cross-check 修正你的推荐。
>
> **Round-1 文件**：`_bmad-output/research/chatgpt-deep-research-story-2.5-sovereignty-isolation-2026-05-04.md`
> **Cross-check 触发**：用户希望 ChatGPT 在看到验证结果后再次评分自己的推荐
> **commit HEAD**：`2f7690e`（worktree-feature-obsidian-hybrid-dev 分支，含本 prompt 自身）

---

## ⛔ 给 ChatGPT 的明确指令

```
你 Round-1 给的回复整体很高质量（代码论断 100% 准确，DOI 全部真实），
但我们 4 个并行 agent 发现 3 个需要你修正的地方：

1. 学术论证有 1 个隐性缺陷：
   - 你引用了 7 个支持论文 + 3 个反方
   - 但没有论文直接对比"学生编辑 AI 反馈"vs"全自动 AI 反馈"的学习效果
   - 反方 VanLehn/Kulik/Ma 强烈支持全自动 ITS 有效 (d=0.42-0.79)
   - Amershi 2019 是 HCI 原则不是教育有效性
   - Khosravi 2022 谈的是"信任"不是"学习效果"

2. 你推荐的 B+E（44-56h）有死数据风险：
   - Agent 4 提出方案 C（渐进式确认，15-22h）
   - 用 frontmatter error_candidates[] + Dashboard Dataview 保活
   - 不需要 ReviewQueueModal（最贵的 14-18h UI 工作）
   - 复用 Obsidian 现有 callout 编辑流程

3. 你推荐的 VaultContextResolver 已有等价物：
   - 项目已有 backend/app/core/subject_config.py（ContextVar 级隔离）
   - 不需要新建抽象
   - Story 2.5.Y 应是"复用 SubjectConfig + 修硬编码 DEFAULT_GROUP_ID"

请你做的事：
1. 不要全盘否认 Round-1。只修正这 3 点
2. 必须直接回应反方证据（VanLehn 2011 / Kulik 2016 / Ma 2014）
3. 必须评估方案 C（15-22h）vs 你 B+E（44-56h）哪个更优
4. 给出最终一句话推荐 + 工作量 + commit-ready 程度
5. 如果你坚持 B+E，请给出"克服死数据风险"的具体机制
```

---

## 📊 Cross-Check 总览（4 Agent 并行结果）

### Agent 1 — 代码论断验证：5/5 全真 ✅

| 你 Round-1 的论断 | 验证结果 | 证据 |
|---|---|---|
| `error_writer.write_error_to_graphiti()` 直接 import `DEFAULT_GROUP_ID` | ✅ 真 | `error_writer.py:270` import + `:308` 传 group_id 参数 |
| `config.py` `DEFAULT_GROUP_ID` 默认值 = `cs188` | ✅ 真 | `config.py:471-474` Pydantic Field default |
| `PostTurnExtractRequest` 没有 vault_id/group_id 字段 | ✅ 真 | `chat.py:236-260` 仅 4 字段（node_id/session_id/messages/fire_and_forget_graphiti） |
| `errors[]` 缺 user_confirmed/user_disputed/ai_reasoning/evidence_turns | ✅ 真 | `error_writer.py:79-95` 列了 12 字段，4 个主权字段全缺 |
| 历史 group_id 漏洞文档存在 | ✅ 真 | R4/R8/R12/epic-1.9 多份 review 文档已识别 cross_canvas_retriever / vault_notes_retriever 漏洞 |

**额外发现**：`backend/app/core/subject_config.py` 已有 `get_current_subject_id()` / `set_current_subject_id()` ContextVar 级抽象。你建议的 `VaultContextResolver` 与它**职能重叠**——应是"统一并强化 SubjectConfig"而不是新建。

---

### Agent 2 — 学术 DOI 验证：10/10 真，但有 caveat ⚠️

| # | 论文 | DOI 真实 | 元数据准确 | 关键发现解读准确性 |
|---|---|---|---|---|
| 1 | Bjork 2013 | ✅ | ✅ | ✅ 准确 |
| 2 | Kapur 2016 | ✅ | ✅ | ✅ 准确 |
| 3 | Bisra 2018 | ✅ | ✅ | ✅ 准确（g=0.55 实证） |
| 4 | Khosravi 2022 | ✅ | ✅ | ⚠️ **范围问题** |
| 5 | Kasneci 2023 | ✅ | ✅ | ✅ 准确 |
| 6 | Amershi 2019 | ✅ | ✅ | ⚠️ **HCI 不是教育** |
| 7 | **Dietvorst 2018** | ✅ | ✅ | ✅ **B+E 最强证据** |
| 8 | VanLehn 2011 | ✅ | ✅ | ✅ 真（d=0.79 ITS 有效） |
| 9 | Kulik & Fletcher 2016 | ✅ | ✅ | ✅ 真（d=0.66） |
| 10 | Ma et al. 2014 | ✅ | ✅ | ✅ 真（g=0.42） |

**⚠️ 你需要修正的 3 个引用问题**：

1. **Amershi 2019**：18 条 Human-AI Interaction Guidelines 是 **HCI 原则**（透明性 / 用户控制 / 纠正机制），不是**教育学有效性**证据。你 Round-1 把它当作"AI 应允许用户纠正"的支撑——准确，但不能等同于"学生编辑反馈 → 学习效果更好"。

2. **Khosravi 2022**：XAI-ED 框架讨论的是**信任 / 可审计性**（学习者要求 AI 解释自己），**不是学习效果**。你 Round-1 用它支持"解释字段（ai_reason）"——这部分准确（解释字段确实需要），但不能用它论证"B+E 学习效果优于全自动"。

3. **缺失关键论文 — 直接对比证据**：
   - 你 7 篇支持论文 + 3 篇反方，全部都是**间接证据**
   - **没有任何论文直接对比**："学生编辑 AI 反馈"组 vs "AI 全自动反馈"组在学习效果（如 post-test / retention）上的差异
   - 而反方 VanLehn 2011 (d=0.79) / Kulik 2016 (d=0.66) / Ma 2014 (g=0.42) 强力证明**全自动 ITS 已经有效**
   - 你 Round-1 在 §A2 末尾用一句话带过反方（"开放式对话错误边界更含糊，不能直接套用 ITS 自动判题逻辑"）—— **这个理由不够**，因为 LLM-based ITS 在对话场景的最新研究尚未明确反对全自动模式

**唯一直接证据**：**Dietvorst 2018**（"Algorithm Aversion"）。但 Dietvorst 测的是**采纳度**（用户愿意用算法），不是**学习效果**（用算法后学得更好）。这两件事的因果链需要你明确区分。

---

### Agent 3 — 业界产品验证：5.5/6 ⚠️

| 你 Round-1 论断 | 验证结果 |
|---|---|
| Graphiti MCP `--group-id` 参数存在 | ✅ 真（Context7 docs 确认）— Story 2.5.Y 隔离硬化的实施基础 |
| Mem0 用 user_id 作过滤维度 | ⚠️ 真但**不完整**——实际有 6 维度：user_id / agent_id / run_id / session_id / app_id / created_at。**session_id 对 Story 2.5 更精细**（每对话隔离）|
| Khoj 是 personal AI 支持 Obsidian + multi-vault | ⚠️ **声称过强**——Khoj 文档是 single-user focused，**multi-tenant 细节未公开**，对 Obsidian 多 vault 隔离的支持记录不足 |
| Zep sub-200ms at scale | ✅ 真（Graphiti README 对比表）+ ⚠️ caveat 合理（实际 P95 ~300ms，本地不能直接承诺）|
| LlamaIndex 用 storage context / metadata 隔离（不是多容器）| ✅ 真 |
| 业界对话产品无"纯 AI 自动判错+无确认写入永久档案"先例 | ✅ **真**——Khanmigo 要求教师确认；Duolingo 自动判但答案空间明确；Synthesis Tutor 文档未公开自动写入机制 |

**你需要修正的**：把 Khoj 的"Obsidian 多 vault 支持"声称弱化或去掉。可以保留它作为 self-host personal AI 的对照（"Khoj 也是单服务多 namespace"），但不要暗示它给"多 vault 隔离"提供了直接参考。

---

### Agent 4 — B+E 方案落地评估：Agent 提出方案 C（更优）⚡

**你 Round-1 推荐的 B+E（44-56h）经我们核对**：

| 工作项 | 你的估时 | 我们核对 | 偏差 |
|---|---|---|---|
| post-turn-extract 增加 mode 参数 | 4-6h | 2-3h | 偏保守 |
| ErrorCandidate schema + store | 6-8h | 3-5h | 偏保守 |
| **Obsidian Review Queue / Modal / 批量确认 UI** | **12-16h** | **14-18h** | **偏紧** |
| errors[] 加主权字段 | 4-6h | 2-3h | 偏保守 |
| Graphiti 仅 confirmed 写入 | 4-6h | 2-3h | 偏保守 |
| 单测/E2E/回归 | 10-14h | 12-16h | 偏紧 |
| 文案 + onboarding | 4h | 4-6h | 持平 |

整体准确（44-56h 是合理保守值），但 **UI 部分被低估**（ChatGPT 12-16h 实际需 14-18h）。

**关键问题：B+E 的死数据风险**

```
对话结束 → AI 提取 candidate → 写 review queue
                                    ↓
                    （用户从不打开 review queue）
                                    ↓
                              candidate 沦为死数据
                              无论"4 状态" 设计多复杂都失效
```

**Agent 4 提出方案 C（渐进式确认）**：

```
对话结束 → AI 生成 candidate → 写 frontmatter error_candidates[]
                  ↓
        非阻塞 Notice："发现 N 个可能误区"
                  ↓
        Dashboard Dataview 显示"待复盘 N 个"（保活机制）
                  ↓
        用户 Cmd+Click 编辑 candidate → 自然移入 errors[]
                  （复用 Obsidian 现有 callout 编辑流程）
```

**方案 C 优势**：

| 维度 | B（modal-on-each） | B+E（你的推荐） | **C（渐进式确认）** |
|---|---|---|---|
| 工作量 | 36-40h | 44-56h | **15-22h** |
| 用户主权 | 高 | 高 | **高** |
| 死数据风险 | 低 | **中-高** | **低** |
| UI 改造代价 | 4-6h（Modal）| 14-18h（Modal+Queue UI） | **2-4h**（无需新 Modal）|
| Dashboard 保活 | 不需要 | 需要 | **天然保活**（Dataview 显示）|
| 与 callout 系统协调 | 平行 | 平行 | **复用** |

**核心差异**：
- B+E 需要新建 ReviewQueueModal class（最贵 14-18h）
- C 只需要 frontmatter 加一个 array + Dashboard 加一个 Dataview block
- C 让"用户编辑错误描述"成为自然的 confirmation（不是被弹 modal 打断）

---

## ❓ Part A 修正：用户主权回归（请你重答）

### Q-A-修1：你是否同意 Amershi/Khosravi 引用范围问题？

请明确回答：
- **同意 / 部分同意 / 反对** — Amershi 2019 是 HCI 而不是教育学有效性证据
- **同意 / 部分同意 / 反对** — Khosravi 2022 讨论"信任"不是"学习效果"
- 如果同意：你 Round-1 用它们论证 B+E 的部分应该如何修正？
- 如果反对：请给具体引用（论文中哪一段直接讨论"学生编辑 AI 反馈→学习效果"）

### Q-A-修2：你如何回应反方证据 VanLehn 2011 / Kulik 2016 / Ma 2014？

这 3 篇是 Story 2.5.X 的最大学术挑战：
- VanLehn 2011：人类辅导 d=0.79 vs ITS d=0.76（几乎相同）
- Kulik & Fletcher 2016：50 项 RCT meta-analysis，ITS 平均 d=0.66
- Ma et al. 2014：107 项研究，14,321 参与者，ITS g=0.42 持续有效

**它们论证的核心**：全自动 ITS 已经有效，且人工干预（教师/编辑/确认）**没有显著 incremental effect**。

请回答：
- 如果全自动 ITS 已经 d=0.66-0.79，为什么 Story 2.5 还需要花 44-56h（B+E）甚至 15-22h（C）改成"用户确认"？
- 你 Round-1 §A2 末尾的"开放对话场景不能套 ITS 模式"理由 — 有学术支撑吗？给具体论文。
- LLM-based 对话 ITS（如 GPT-tutor 时代）的最新研究（2023-2025）是否倾向 user-in-the-loop？给至少 1 篇 DOI。

### Q-A-修3：B+E vs 方案 C，你怎么选？

我们的 Agent 4 论证方案 C 等价用户主权 + 工作量减半 + 复用现有 UI。

**请你**：
- 若同意 C：给出"采用 C 而非 B+E"的明确理由（至少 3 条）+ C 的最大风险（至少 2 个）
- 若坚持 B+E：你必须给"克服死数据风险"的具体机制（不是"加 Dashboard 横幅"这种泛泛而言）
- 若有第 4 方案：明确描述 + 工作量 + 与 C 的差异

### Q-A-修4：Dietvorst 2018 是采纳度证据，不是学习效果证据。你怎么补强？

我们认可 Dietvorst 2018 是 B+E/C 最强证据。**但它测的是采纳度**（用户愿意用算法），**不是学习效果**（用算法后学得更好）。

**两者的因果链**：
```
用户更愿意用 → 更频繁交互 → 更多数据 → 更好个人化 → 学习效果更好
（每一步都需要补强）
```

请回答：
- 这个因果链中哪几步有论文支撑？
- 如果只有第 1 步（采纳度）有证据，是否仍然支持采用 B+E/C？为什么？

---

## ❓ Part B 修正：多 Vault 隔离（请你重答）

### Q-B-修1：你是否同意 VaultContextResolver 与 SubjectConfig 重叠？

我们项目 `backend/app/core/subject_config.py:42-60` 已有：

```python
def get_current_subject_id() -> str:
    return _current_subject_id.get()

def set_current_subject_id(subject_id: str) -> None:
    _current_subject_id.set(subject_id if subject_id else DEFAULT_SUBJECT_ID)
```

这是基于 `contextvars.ContextVar` 的请求级隔离。

**你 Round-1 推荐新建 VaultContextResolver**，但这与 SubjectConfig 职能重叠。请回答：
- **同意 / 反对** — 应"统一并强化 SubjectConfig"而不是"新建 VaultContextResolver"？
- 如果同意：Story 2.5.Y 应该写成"复用 SubjectConfig + 修硬编码 DEFAULT_GROUP_ID"，对吗？
- 如果反对：SubjectConfig 缺什么 VaultContextResolver 才能提供？

### Q-B-修2：Khoj 多 vault 引用过强，需要修正吗？

我们 Agent 3 验证发现 Khoj 文档**未明确说明 multi-tenant 架构细节**，主要是单用户 personal AI。

请：
- 撤回 Khoj 作为"多 vault 隔离参考"的引用？
- 替换为更准确的对照（LlamaIndex tenant-aware vector store / Mem0 6 维度过滤 / 或其他）？

### Q-B-修3：Mem0 的 6 个隔离维度你怎么评价？

你 Round-1 只提了 user_id。但 Mem0 实际支持：
- user_id（每用户）
- agent_id（每 AI 角色）
- session_id（每会话）⭐ 对 Story 2.5 最相关
- run_id（每执行）
- app_id（每应用）
- created_at（时间窗口）

**对 Story 2.5 的启示**：
- frontmatter 应不应该加 `session_id` 字段（每对话独立）？
- 跨 session 的同类错误是否应该 dedupe（已有 dedupe_hash 处理）？
- 如果用户想"只 review 今天的 candidates"，session_id + created_at 是否需要前置？

请你重新评估隔离维度推荐。

### Q-B-修4：本地工作量真实估算

你 Round-1 给 Story 2.5.Y 估 33-48h。我们核对：

| 工作项 | 你估时 | 我们核对 |
|---|---|---|
| VaultContextResolver | 4-6h | 0h（复用 SubjectConfig）|
| post-turn-extract 加 vault_id | 4-6h | 3-4h |
| error_writer 移除 DEFAULT_GROUP_ID | 3-4h | 2-3h |
| Graphiti/Cypher/LanceDB 隔离审计 | 8-12h | 8-10h |
| group_id 命名迁移（cs188/cs_61b → vault:<id>）| 4-6h | 4-6h |
| per-vault export 脚本 | 4-6h | 3-4h |
| E2E 隔离测试 | 6-8h | 6-8h |
| **总计** | **33-48h** | **26-35h** |

请你重新评估总工作量。

---

## 📐 Desired Output Format

```markdown
# ChatGPT Round-2 Reply — Story 2.5 修正稿

## Round-1 自我评分（修正后）

- 代码论断准确度：5/5 ✅
- 学术 DOI 真实性：10/10 ✅
- 学术解读准确性：__/10（修正后）
- 业界产品引用：__/6（修正后）
- 推荐方案有效性：__/10（修正后）

## Part A 修正

### A-修1: Amershi/Khosravi 引用范围
- 我承认 / 反对 / 部分同意：______
- 修正后的论证：______

### A-修2: 反方证据回应
- VanLehn/Kulik/Ma 的解读：______
- LLM-based ITS 最新研究 DOI：______
- "ITS d=0.66 已经有效" 的反驳：______

### A-修3: B+E vs 方案 C
- 我选 ______（B+E / C / 第 4 方案）
- 理由（3 条）：______
- 风险（2 个）：______

### A-修4: Dietvorst 采纳度→学习效果链路
- 因果链补强论文：______
- 仅采纳度证据是否足够：______

## Part B 修正

### B-修1: SubjectConfig 复用
- 同意复用 / 反对：______
- 修正后的 Story 2.5.Y 实施路线：______

### B-修2: Khoj 撤回
- 撤回 / 保留 / 替换为：______

### B-修3: Mem0 6 维度对 frontmatter 的启示
- session_id 加不加：______
- 影响 dedupe 逻辑吗：______

### B-修4: 工作量真实估算
- Story 2.5.Y 修正后总时：______ h

## 最终一句话推荐

> Story 2.5.X 选 ______（B+E / C / X）+ Story 2.5.Y 选 ______，
> 总工作量 ______ h，commit-ready 程度 ______ /10。
```

---

## 🔗 给 ChatGPT 的可 fetch URL（commit `2f7690e`）

```
# Round-1 prompt + cross-check（本文档自身）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/_bmad-output/research/chatgpt-deep-research-story-2.5-sovereignty-isolation-2026-05-04.md
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/_bmad-output/research/chatgpt-round2-cross-check-story-2.5-sovereignty-isolation-2026-05-04.md

# Story 2.5 后端代码（验证 5 个论断）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/backend/app/services/error_writer.py     # 论断 1（DEFAULT_GROUP_ID 硬编码）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/backend/app/config.py                    # 论断 2（cs188 默认值）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/backend/app/api/v1/endpoints/chat.py     # 论断 3（无 vault_id 字段）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/backend/app/services/error_classifier.py # 论断 4（缺主权字段）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/backend/app/core/subject_config.py        # SubjectConfig 已有抽象（你的 VaultContextResolver 与之重叠）

# Story 2.5 UAT
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/_bmad-output/验收单/Story-2.5-error-extraction.md

# Plugin（验证 ReviewQueueModal 工作量）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/frontend/obsidian-plugin/src/main.ts

# Dashboard（验证方案 C 的保活机制）
https://raw.githubusercontent.com/oinani0721/canvas-learning-system/2f7690e/canvas-vault/Dashboard.md
```

---

## 🚧 我们已锁定的事实（不要再质疑）

1. ✅ **Story 2.5 后端 ship 通过 ChatGPT 8/10**（commit `0d05ad8`），不要重新审查后端代码
2. ✅ **6 个 AC 全部对齐 PRD §FR-CONV-06**，不要质疑 PRD 一致性
3. ✅ **D 方案双标签共存合理**（兼容 Story 3.6 production data）
4. ✅ **代码层面 5 个漏洞确认**（你 Round-1 全说对了）
5. ✅ **学术 10 篇 DOI 全真**（你 Round-1 全说对了）

**本轮 Round-2 只解决 3 件事**：
- 学术解读 caveat 修正
- B+E vs 方案 C 二选一
- VaultContextResolver vs SubjectConfig 复用决策

---

## 📅 时间盒

请在 20-30 分钟内完成 Round-2，预算：
- 学术补充检索：3-5 篇 LLM-based ITS 论文（2023-2025）
- 因果链 cross-validation：1-2 篇直接对比"AI 自动 vs 用户编辑"的论文
- 业界产品复核：跳过（Round-1 已确认）

**预计返回长度**：1500-2500 字（短于 Round-1 因为只修正 3 点）。

**审查后的下一步**：用户基于 Round-2 决议在 §12 决策区批注 D15（用户主权方案）+ D16（隔离方案），Claude Code 据此 ship Story 2.5.X + Story 2.5.Y。

---

> **生成时间**：2026-05-04（commit `2f7690e` 之后）
> **生成人**：Claude Code (Opus 4.7)
> **触发原因**：用户希望 ChatGPT 看到我们 4 个 agent cross-check 后再次评分
> **关联 commit**：`2f7690e`（Round-1 prompt 已 push 到 origin/backup）
> **下一步**：Round-2 反馈 → 用户决策 → ship Story 2.5.X/Y

---
story: "S2-2 (5-ge-1 + 5-ge-2)"
title: "graphiti-belief-spine"
status: "review"
version: "1"
date: "2026-06-03"
developer: "Claude Code (Opus 4.8 1M)"
commit: "33662d6"
---

# Story S2-2 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 S2-2「Graphiti 个人记忆脊柱 — belief 时序链」的验收文档，**给你（非技术）读的版本**。
> ⚠️ **本期是纯后端能力（记忆端的地基）**，还没接到你能在 Obsidian 里点的界面（那个"读出来给你看"的部分是后续 5-ge-5）。
> 所以这份单子里 **大部分是 Claude 已代验**，你只需读"段 4-A 的证据"，"段 4-B 你来验"这次只是**预告未来你会看到什么**。

---

## 🎯 这个 Story 要做到什么

**当你对同一个知识点的批注（tip / 错误标记 / 双链关系）改来改去时，系统会偷偷把你「以前怎么想的」和「现在怎么想的」都存下来，将来你能回头问『我以前认为 X，后来改成 Y』。**

---

## 📖 用户故事（你的视角）

**作为** 一个边学边改笔记的学习者，
**我想** 改一条批注时系统别把旧的直接覆盖掉、而是留个时间线，
**以便** 将来复盘时能看到我的理解是怎么一步步演化的（这正是你当初选 Graphiti 的核心理由，此前 0% 被用上）。

---

## 🖥️ 你（未来）会看到的体验（一步一步）

```
1. 你在「递归」节点写下 tip：“递归一定要先想 base case”
       ↓
2. 一周后你改成：“base case 必须能直接返回，不再递归”
       ↓
3. 系统不丢掉旧的 —— 旧版本被打上「截止到改动那天有效」的时间戳
       ↓
4. 新版本成为「当前有效」；旧版本静静躺在时间线里
       ↓
5.（未来接上读侧后）你能问“我对 base case 的理解是怎么变的”，
   系统按时间线列出 v1 → v2 → v3
```

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段 Claude 自动跑完贴证据
> 你只看右边"结果"列是不是 ✅。出现 `pytest` / `schema` / `commit` 等词不是 bug，是 Claude 该处理的。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | belief 版本链单测全过 | ✅ `test_belief_version_chain.py` 7 passed |
| 2 | 统一事件 schema + narrative 单测全过 | ✅ `test_canvas_episode_v1.py` 19 passed |
| 3 | 同一批注改 3 次 → 保留 3 个版本 | ✅ demo：前 2 版 superseded(带失效时间)、最新版 active |
| 4 | 旧版失效时间 == 新版生效时间（时间线无缝） | ✅ `edges[0].invalid_at == edges[1].valid_at` 断言通过 |
| 5 | 时序回溯：问"2026-05-22 当时我怎么想" → 返回当时版本 | ✅ demo：返回 v1，而 current 仍是 v3 |
| 6 | "演化事件禁用批量写入"契约（防丢时间线） | ✅ `use_bulk=True` → 抛 ValueError 断言通过 |
| 7 | 跨学科隔离（不串 vault） | ✅ 写入经 `sanitize_group_id_for_graphiti` |
| 8 | 代码风格 + lint 干净 | ✅ ruff All checks passed |
| 9 | P0 前序批次零新增失败后独立提交 | ✅ 基线对比 22→22 failed，commit `25f94c4` |
| 10 | 接入主写入管道（演化事件旁路 hook） | ✅ `episode_worker._process_episode` add_episode 成功后旁路，失败非致命 |

**段 4-A demo 实跑输出（belief 时序链）：**

```
belief_key = callout:recursion-base-case:d8acdb1ef6b92bea
用户对同一节点的 tip 先后改了 3 次：
  v1 @ 2026-05-20：写下 “递归一定要先想 base case”
  v2 @ 2026-05-27：写下 “base case 必须能直接返回，不再递归”
  v3 @ 2026-06-02：写下 “base case = 最小可解子问题，直接给答案”

get_belief_history() → 完整时序版本链（旧版保留 + 新版 active）：
  v1 [superseded] 有效自 2026-05-20 失效于 2026-05-27
  v2 [superseded] 有效自 2026-05-27 失效于 2026-06-02
  v3 [    active] 有效自 2026-06-02 失效于 —（仍有效）  ← current（当前有效）

时序回溯 get_belief_history(as_of=2026-05-22) → 当时用户的认知是：
  2026-05-22 当时有效：“递归一定要先想 base case”
  而今天的最新版：“base case = 最小可解子问题，直接给答案”
  → 证明：用户能问『我以前认为 X，后来改成 Y』
```

---

## 👤 你来验（本期受限说明）

> [!warning]+ 这次没有你能点的界面 —— 这是诚实告知，不是遗漏
> 本期做的是**记忆端的地基**（写入 + 存版本链）。把版本链**读出来给你看**的那块界面，是后续 5-ge-5（关系读取 facade）+ 真实 Neo4j 接通后才有。
> 所以这次**你不需要做任何 hands-on**。下面只是**预告**：等读侧接上后，你将能这样验。

### 未来（接读侧 5-ge-5 后）你将能这样验：

- [ ] 我在某个节点写一条 tip → 过几天改掉它 → 我打开"这个节点的历史" → **我看到旧版和新版都在，按时间排好** → 我感觉「系统真的记住了我的思路变化，踏实」
- [ ] 我问"我对 X 的理解是怎么变的" → **我看到一条时间线 v1→v2→v3** → 我感觉「像翻自己的成长日记」

### 主观打分（本期暂不适用）

> 本期纯地基，无 hands-on，打分留到读侧接通后的验收单。

---

## 🚦 验收结果

**本期验收方式 = 读「段 4-A」证据**：如果你认可上面 10 项 ✅ + demo 输出体现了"改批注→留旧版+标新版"，就告诉我 "**S2-2 地基通过**"，我会把 5-ge-2 mark done、5-ge-1 留 in-progress（传输层/edge_type_map 是已解锁的后续）。

**如果你觉得这个"记忆脊柱"的行为不对**（比如你其实希望改批注就直接覆盖、不留历史），在批注区告诉我，我用 `bmad-bmm-correct-course` 调整。

---

## 📝 你的批注区

> [!question]+ 你对 S2-2 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）。

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **Story spec**：
  - `_bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md`（in-progress）
  - `_bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-2-belief-key-version-chain.md`（review）
- **源代码**：
  - `backend/app/graphiti/canvas_episode.py`（统一 episode schema，C-1 owner）
  - `backend/app/graphiti/narrative_builder.py`（narrative 渲染）
  - `backend/app/services/graphiti_belief_service.py`（belief 版本链核心）
  - `backend/app/services/episode_worker.py`（演化事件 belief 旁路 hook）
- **单元测试**：
  - `backend/tests/unit/test_belief_version_chain.py`（7 用例 / 100% 通过）
  - `backend/tests/unit/test_canvas_episode_v1.py`（19 用例 / 100% 通过）
- **Git commit**：`33662d6`（main 主线）+ P0 前序 `25f94c4`
- **AC → 代码对应**：
  - 5-ge-2 AC#2 belief_key → `graphiti_belief_service.py::BeliefKeyResolver`
  - 5-ge-2 AC#3/#4 版本链 → `graphiti_belief_service.py::update_belief_version_chain`
  - 5-ge-2 AC#6 历史查询 → `graphiti_belief_service.py::get_belief_history`
  - 5-ge-2 AC#5 协同 → `episode_worker.py::_process_episode`（belief hook）
  - 5-ge-1 AC#2 schema → `canvas_episode.py::CanvasGraphEpisodeV1`
  - 5-ge-1 AC#6 narrative → `narrative_builder.py::build_narrative`

---

## 📅 下一步（你读完这份单后）

1. **认可地基** → 说 "S2-2 地基通过" → 我 mark 5-ge-2 done
2. **行为不符预期** → 批注区写清楚 → 我跑 `bmad-bmm-correct-course`
3. **想先接读侧再一起验** → 告诉我 "先做 5-ge-5 读侧"，本期 status 保持 review

> ⚠️ 偏离记录（透明告知）：实读 graphiti-core 0.28.2 源码发现 spec 原写法（`search` 按属性精确查 / `update_edge` / `add_triplet`）在该版本不可行或成本过高，已改为 driver 原生 Cypher + `EntityEdge.save()` 确定性直写，行为等价且更省。详见 5-ge-2 spec 的 Change Log D1/D2/D3/R5。

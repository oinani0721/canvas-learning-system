---
title: "Plan B Postmortem — Story 2.4 Plan B 实施回顾 + 回退 Plan A 决策"
date: "2026-05-14"
status: "决策完成 — 回退 Plan A 短期交付 + Plan B 经验沉淀为 Plan C 长期参考"
plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
decision_source: "4 方对抗审查共识 (Canvas 自评 + Claude 5-Agent + ChatGPT-1 5-13 + ChatGPT-2 5-14)"
related_commits: ["3d10a02 feat plan-b code", "df88716 docs uat v2", "f34518c chore pack"]
---

# Plan B Postmortem — Story 2.4 实施回顾

## TL;DR

5-14 实施了 Story 2.4 Plan B（plugin debounce + Graphiti append-only），4 路对抗审查（Canvas / Claude / ChatGPT-1 / ChatGPT-2）一致建议回退 Plan A。Plan B 代码保留在 git history 作为 Plan C 未来参考。

**核心教训**：把简单问题（Story 2.4 = 提取批注 + 注入上下文 + 删除追踪 + 文件不坏 + 不丢数据）做成了复杂问题（plugin debounce + hash 染色 + append-only episodic + in-memory cache + Graphiti projection + tombstone design）。

**触发 Plan C 的条件**：DD-08 跨文件复发追踪诉求被用户确认（如 ChatGPT 给的"base case 在递归 / 树遍历 / 动态规划 三个文件复发"用户故事）。

---

## 决策链时间线

### 2026-05-13：起点
- 用户 5-13 批注（`_bmad-output/验收单/批注回复/2026-05-13-设计可行性评估-用户核心闭环.md`）指出 10 Gap（G1-G10）
- Claude 5-Agent Deep Explore：判定核心闭环 FAIL（10 步中 8 步 ❌）
- 启动 ChatGPT Deep Research：78% 置信确认 FAIL，建议 Option A（修 P0 数据层 bug 10h）

### 2026-05-14：Plan B 实施（错误决策起点）
- 选择 Plan B（plugin debounce + Graphiti 真相源）而非 Plan A（frontmatter spec）
- 理由：(1) 时序演化 (2) 跨白板推理 (3) P0 已接通
- 8 层根因逐一修复：
  - P0-1: handleAnnotateCallout 接 backend
  - P0-2a/b/c: source_description schema 三方对齐
  - P0-3: memory_format.py 加 LearningTip + CalloutAnnotation
  - P0-4: Graphiti protected attr 冲突 rename (3 处)
  - P0-5: group_id 边界 sanitize (D16 冒号 → 双下划线)
  - P0-6 + F1: 光标定位 + visible prompt
  - P0-7/8: hash 内嵌 content + in-memory cache
- Phase 1-4 dev：vault.on('modify') + 500ms debounce + batch endpoint + find_episode_by_content_hash
- 用户实测端到端打通：一次输入 = 8 sync = 3 EpisodicNode v1/v2/v3 + Gemini 抽取 LearningConcept

### 2026-05-14 晚：4 Agent 自我对抗审查
- Agent A (Plan B vs spec): 6 处偏离 + 5 个对抗问题
- Agent B (content_hash 边界): V1-V14 共 14 个漏洞
- Agent C (长期成本): 1 年 ~$140-280 Gemini API + dedupe 无 temporal
- Agent D (失败场景): F1-F15 共 15 个失败模式
- 汇总：34 个对抗性问题（4 BLOCKER + 8 HIGH + 11 MEDIUM + 11 LOW）

### 2026-05-14 凌晨：ChatGPT-2 对抗审查
- 打包 21 文件 + 4 Agent 报告 inline → 553 KB / 123K tokens
- ChatGPT 判定：**当前 Plan B 不准单独上线**
- 给硬决策：短期 Plan A / 中期 Plan C / 当前 Plan B 否决
- 找到 4 BLOCKER 重排：
  - B1 死链 — 理由错（context_enrichment 实际能注入），真因是 **Graphiti EpisodicNode 不存 node_id 字段 → reader 查 ghost field**
  - B2 删除 — 致命确认
  - B3 Cmd+Q — 致命确认但"100%"措辞过头
  - B4 hash 碰撞 — **降级**，真正 BLOCKER 是 **basename 当 ID 的身份模型错位**
- 找到 7 个 Canvas 团队未发现的盲点
- 给 1 个具体的"用户故事"作为 Plan C 触发条件（base case 复发）

### 2026-05-14：路径 1 决策
- 4 方意见高度一致：Plan A 短期交付 + Plan C 中期路线 + Plan B 推倒
- 用户确认路径 1
- Plan B 代码保留在 git history (commit 3d10a02)，作为 Plan C 未来参考

---

## 决策错误根因（为什么选 Plan B）

**Canvas 团队的认知偏差**：

1. **沉没成本**：5-13 Claude/ChatGPT-1 确认 FAIL 后，团队倾向于"修补现有 P0"而非"重新设计"
2. **技术诱惑**：Graphiti 的"时序演化 + 跨白板推理"听起来比 frontmatter 数组先进
3. **AC#4 误读**：以为"注入 LLM 上下文"只能走 Graphiti search，没看 context_enrichment 实际已读 frontmatter tips[]
4. **Spec 偏离合理化**：spec 写"Backend file watcher"但实际不存在 → 选择"绕过 spec 用 plugin push"而不是"先建 file watcher"
5. **8 层根因修复正反馈**：每修一层都觉得"快通了"，没退一步问"这条路是不是错的"

---

## ChatGPT 的关键发现（Canvas 团队未发现的）

### 7 个 Canvas 未发现盲点

| # | 盲点 | 严重性 | 未来 Plan C 必避 |
|---|---|---|---|
| 1 | 协议悄改 — spec 写 `[!tip]+/-` 但 parser 只认 `+` 且不识 tip 单数 | 🔴 兼容性 | 严格按 spec 协议实施，UI 文案不能决定协议 |
| 2 | 消费者各读各 — LearningContextService 只看 `episode_type==learning_tip`，QuestionGenerator 查 ghost field | 🔴 死链确证 | 统一 read model + projection 层 |
| 3 | Notice 矛盾 — 声称 silent 但 callBackend 默认弹 success Notice | 🟡 体验 | sync 用 silent transport，不走 UI Notice |
| 4 | LRU 假象 — set + list[-800:] 是随机保留 | 🟡 幂等失效 | OrderedDict / TTL cache / Redis SETNX |
| 5 | Cosmetic edit = 语义新版本 — 改空格触发新 hash | 🟠 成本爆炸 | canonicalized content hash + stable callout_id |
| 6 | basename 当 ID — 身份漂移 | 🔴 身份模型 | 持久 file_uid + callout_id |
| 7 | 违反 Graphiti 顺序约束 — 上游要求 sequential await | 🟠 数据竞争 | 每文件串行 async queue + sync_seq + ACK |

### 真正的 B1（不是 Canvas 以为的死链，而是 ghost field）

```python
# Graphiti 上游保存 EpisodicNode 只落 9 字段:
#   {uuid, name, group_id, source_description, source, content,
#    entity_edges, created_at, valid_at}
# 没有 node_id 字段！

# 但 QuestionGenerator._get_tips() 查:
MATCH (e:EpisodicNode) ... AND e.node_id = $node_id
# ↑ 永远 0 命中（除非 record_episode 另写到非 Episodic label）
```

**这意味着即使用户实测看到 EpisodicNode 写入，question_generator reader 仍是死链**（除非 backend 有未在打包范围的同步写入路径 — ChatGPT 标"未能判断"）。

---

## DD-08 触发条件 — Plan C 应该什么时候启动

ChatGPT 给的具体用户故事（Plan A 做不到 + Plan B 当前实现做不到 + Plan C 唯一能做的）：

> 用户在 `递归.md` / `树遍历.md` / `动态规划.md` 三个文件分别留下三条 callout：
> - 第一周：把 "base case" 当成"退出条件的语法糖"
> - 第二周：在树遍历里把"递归深度"和"栈帧数量"混为一谈
> - 第三周：在动态规划里再次"子问题边界没收住"
>
> 系统需要识别：这三条不是孤立 tips，而是**同一个根因在不同知识点上的复发**。然后在考察白板出**跨概念诊断题**，把"第一次出现 → 暂时纠正 → 再次复发"的演化轨迹解释给用户看。

**触发 Plan C 的信号**：
- ✅ 用户明确表达"跨文件 + 跨时间 + 复发追踪"诉求
- ✅ Epic 4 检验白板出题需要这种 KG 推理能力
- ✅ Plan A 已稳态运行 N 个月，frontmatter 真相源不动摇

**不该启动 Plan C 的反信号**：
- ❌ 仅为"系统看起来更智能"
- ❌ Plan A 还在不稳定期
- ❌ 没有具体的跨文件复发故事

---

## Plan B 代码资产保留位置

**不 git revert**（保留作为 Plan C 参考）：
- `3d10a02` feat code (944 insertions): P0 三件套 + Plan B Phase 1-4
- `df88716` docs uat v2.0 验收单 + ChatGPT 第二意见报告
- `f34518c` chore research pack

**可重用经验**：
- Graphiti protected attr 清单（uuid/name/group_id/labels/created_at/summary/attributes）→ 未来定义任何 entity_type 必避
- group_id 边界 sanitize 设计（`group_id_compat.py`）→ 任何与 Graphiti 集成都要复用
- entity_type_from_event 映射 → memory_format.py canonical schema 设计模式
- SHA256 content_hash + canonicalization → Plan C 仍可用（但要修 basename → file_uid + canonicalized content）

**Plan C 重用时要做的事**：
- frontmatter SoT（不动）+ Graphiti 派生索引（后台 shadow write）
- 修 7 个盲点（特别是 basename → file_uid + 协议兼容 + 顺序写）
- ghost field 问题：要么改用 Graphiti edge.fact / node.summary 读，要么新建 CalloutProjection label 显式存 node_id
- tombstone 设计（manifest diff + deleted_at 软删）

---

## Cost 与 Lessons

### 实际投入
- Dev：~5h（P0 + Plan B Phase 1-4 + F1 visible prompt）
- 调试 8 层根因：~3h（每个根因 ~20min）
- 4 Agent 对抗审查：~30min（4 路并行）
- ChatGPT 第二意见：~15-20min（用户 deep research 时间）
- Postmortem：~30min（本文档）
- **总计 ~9-10h**

### 学到的教训（按重要性排序）

1. **Spec 不能绕过** — Story 2.4 spec 写得清楚（Plan A frontmatter），偏离 spec 必有代价
2. **简单问题先用简单方案** — Plan A 6-8h，Plan B 走完发现仍要回退，**净损 9-10h**
3. **对抗审查应该在实施前做** — 4 Agent 并行 30min 能挡掉 Plan B 决策，比实施完再审省 9h
4. **ChatGPT-2 vs ChatGPT-1 价值差异** — ChatGPT-1（5-13 起点低）只能 78% 确认；ChatGPT-2（5-14 在 4 Agent 调研基础上）能直接给出"否决"决策。**先自己 deep explore，再 ChatGPT 二审，才能拿到真深度**
5. **Graphiti 不是 magic** — 上游 dedupe_nodes 无 temporal、save query SET n = {} 全字段覆盖、Episodic 只 9 字段固定 — 这些约束让 Graphiti **不适合做精细批注存储**
6. **用户初衷 DD-08 是决策权重最大的标尺** — 用户从未说"需要 AI 自动抽取实体边"，跑题就是 over-engineering

---

## 给未来 Plan C 实施的 checklist

启动 Plan C 前必须满足：
- [ ] Plan A 已稳态运行 ≥ N 周（建议 ≥ 4 周）
- [ ] 用户具体表达"跨文件复发追踪"诉求（不是 Canvas 团队自己想做）
- [ ] Epic 4 检验白板进入 dev 阶段（这是真正消费 Plan C 数据的下游）
- [ ] 修复 ChatGPT 找的 7 个盲点的设计已 ship
- [ ] frontmatter SoT 不可动摇（Plan A 仍是 fallback）
- [ ] Graphiti 派生索引"后台 shadow write" 模式（异步 + 失败不影响主业务）

启动 Plan C 时必须避免：
- ❌ basename 当 ID（用持久 file_uid）
- ❌ cosmetic edit 当语义新版本（canonicalized content hash）
- ❌ append-only 当唯一删除手段（manifest diff + tombstone）
- ❌ 协议悄改（严格 spec 兼容 `[!tip]+/-` 单复数）
- ❌ Plugin push 当唯一同步路径（backend file watcher / WAL 兜底）

---

## 4 方意见原始报告位置

- Claude 5-Agent 5-13：`_bmad-output/验收单/批注回复/2026-05-13-设计可行性评估-用户核心闭环.md`
- ChatGPT-1 5-13：`_bmad-output/research/2026-05-13-chatgpt-dr-response-core-loop-second-opinion.md`
- Canvas 团队 4 Agent 5-14：`.gdr/plan-b-agent-summary.md`（已 commit 在 f34518c）
- ChatGPT-2 5-14（本次）：未持久化（在对话历史里），关键结论已整合进本 postmortem

---

## Sign-off

**决策日期**：2026-05-14
**决策路径**：Plan A 短期交付 + Plan B 经验沉淀 + Plan C 长期路线
**Plan B 代码状态**：保留 git history，禁用入口
**下一步**：Phase 2 disable + Phase 3 dev Plan A + Phase 5 UAT v3.0

Co-Authored-By: Claude Opus 4.7 (1M context)

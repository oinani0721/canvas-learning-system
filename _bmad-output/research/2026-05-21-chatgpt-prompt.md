# ChatGPT 对抗审查 Prompt — Canvas Obsidian Hybrid

> **使用方法**:
> 1. 打开 ChatGPT (推荐 GPT-5 + Deep Research 模式, 或 Claude 4 Opus / Sonnet 4.5)
> 2. 拖入附件: `_bmad-output/research/2026-05-21-chatgpt-adversarial-review.xml` (728.9 KB)
> 3. 复制下面 prompt 全文粘贴
> 4. (可选) 把 GitHub URL `https://github.com/oinani0721/canvas-obsidian-hybrid` 告诉 ChatGPT 让 ta 也访问 (private repo 需要 access)
> 5. 等 5-15 分钟拿到完整对抗审查报告

---

## Prompt 正文（复制以下全部）

```
# Tech Decision: Canvas Obsidian Hybrid 仓库治理 + Story 推进 对抗审查

## Context

我是单人 PM 在维护一个 Obsidian + FastAPI + Neo4j 学习工具.

**项目演化历史 (重要)**:
1. Tauri v0 桌面 app (2026-03) — 已弃用
2. Obsidian Hybrid v1 — 当前架构, 5 个反馈瞬间学习闭环
3. DeepTutor fork 提议 (2026-05-06) — 已回滚
4. **2026-05-20 开了新仓库 canvas-obsidian-hybrid** — 从旧 canvas-learning-system 瘦身 99.95% (8 GB → 4.3 MB)

**新仓库 9 个 commit (P1-P9) 完成的事**:
- P1: 仓库骨架 + 单一 CLAUDE.md (取代旧 6 个散乱)
- P2: backend 113 .py 按 domain/* 重组 + import path 重写 (207 行) + scope creep 优雅降级 _stubs.py
- P3: plugin 13 .ts cherry-pick
- P4: 6 Skills cherry-pick
- P5: 稳定 ID 契约 (ConceptRef / CanvasRef / AssessmentRef)
- P6: MasterySignal V1 Protocol 升级 (含 SignalAdapter 向后兼容)
- P7: 接通 AutoScorer (解决 MVP-α exam_grade.py 黑盒评分)
- P8: 测试金字塔 5 层基线 (51 testcase)
- P9: smoke test PASS (117 .py / 325 imports / 0 错)

GitHub: https://github.com/oinani0721/canvas-obsidian-hybrid (private)

## Scope 锁定 (重要约束)

**单人自用 Obsidian Hybrid**, 不做:
- LMS / 多用户 / 协作
- LTI / xAPI / 教师面板
- Postgres / Redis / K8s / WCAG / GDPR
- CRDT / Presence / 课程级分析

任何超出此 scope 的建议直接 reject.

## 附件说明 (728.9 KB / ~186K tokens)

XML 含 55 文件分 4 类:

1. **new-repo/** — 新仓库 canvas-obsidian-hybrid 关键代码
   - backend/app/domain/exam/{scorer.py 17.8K, grading.py 5.6K, generator.py 51.3K}
   - backend/app/domain/mastery/{v1.py 6.2K, signals.py 9.4K, engine.py 35.6K, fusion.py 7.6K}
   - backend/app/domain/refs.py 5.5K
   - backend/app/_stubs.py 2.5K (scope creep 优雅降级)
   - plugin/src/{main.ts 87.4K, exam-quick.ts 12.8K, status-bar.ts 9.3K, callout.ts 6.5K, ai-linked-doc.ts 5.7K, configure-whiteboard.ts 13.1K}
   - CLAUDE.md / README.md / domain/README.md (元数据 + service catalog)

2. **new-repo/skills/** — 6 Claudian Skill + capability-registry.md
   - ai-linked-doc / chat-with-context / configure-whiteboard / exam-quick / node-chat / study-question

3. **old-repo/** — 旧仓库设计文档
   - planning-artifacts/{prd.md 41.2K, epics.md 41.9K, architecture.md 67.9K}
   - implementation-artifacts/sprint-status.yaml 27.6K (90 Story 状态)
   - epic-4/ 考察系统 (11 Story spec, 81.7K)
   - epic-5/ 掌握度 BKT/FSRS/融合 (8 Story spec, 59.2K)
   - epic-6/ Edge 讨论 (3 Story spec, 31.0K)

4. **prd-anchor/** — PRD v5 锚定文档关键章节 (§1.4 评分双框架 + §1.5 5 信号融合 + §1.10 元认知 2x2 矩阵 + §10 实施路线)

## 已知背景 (帮你聚焦, 别浪费 token 调研)

我已做过 3 轮 deep research 发现以下事实:

1. **autoscore.py 旧时被 exam_grade.py 绕过 (DEAD CODE)** — P7 grading.py 修复, 但 endpoint 还没接通 grading.py
2. **学生自评是 1 维不是 4 维** — 跟 AutoSCORE 4 维(系统评)完全分离, 且前端 0 UI (DEAD CODE)
3. **新仓库代码已迁但 endpoint 没重写** — main.py 是 stub, endpoint 调用关系不完整
4. **EPIC 1 v2 done 17 Story 中只 4 有 R4 验收单** (1.16/1.17/1.18/1.19), 其余 13 backend Story 缺验收单
5. **Epic 2-3 in-progress, Epic 4-9 backlog** — 共 90 Story, 22 done / 57 ready-for-dev / 10 review
6. **PRD §1.4 设计的 AutoSCORE 4 维 4 分制 + Story 4.6 silent scoring + Story 5.3 5 信号融合** 是核心闭环, 但代码层 grading.py 跟 endpoint 还没连通

## 请你做 5 件事 (对抗性审查)

### 1️⃣ 功能 vs 代码 vs Story 对照矩阵

把 PRD 锚定文档的"灵魂功能" (例如 §1.4 AutoSCORE / §1.5 5 信号融合 / §1.10 元认知矩阵) 跟 Epic 4-6 Story 跟新仓库代码做 3 列对照表:

| PRD § | EPIC Story | 新仓库代码状态 | 距离 (0-100%) |
|---|---|---|---|

至少 8-12 条对照. 标 ❌ DEAD CODE / 🟡 PARTIAL / ✅ CONNECTED.

### 2️⃣ 哪些代码可复用衔接

逐个 trace:
- `backend/app/domain/exam/scorer.py` (AutoScorer 4 维) — 现在被谁调? 应该被谁调? 距离 endpoint 多远?
- `backend/app/domain/exam/grading.py` (P7 修复) — 接通了 scorer + 发 SCORE_SUBMITTED event, 但 endpoint 在哪? 需要新建 routes 吗?
- `backend/app/domain/mastery/{v1.py, signals.py, engine.py, fusion.py}` — 5 信号融合是否真通了 SCORE_SUBMITTED → BKT_UPDATED → MASTERY_CHANGED 链?
- `backend/app/domain/refs.py` (P5) — ConceptRef / CanvasRef / AssessmentRef 是否真在所有跨 domain 调用中用了, 还是新代码用旧代码用 raw string?
- plugin/src/exam-quick.ts — Cmd+Shift+Q 触发链, 用的是新 grading endpoint 还是旧 exam_grade.py 黑盒?

每条给"修复 1 处接通"的最小 PR 描述.

### 3️⃣ 90 Story 推进顺序 + 时间预算

考虑:
- 单人 PM (我), 单人 Claude Code 协作
- 已 done 22 (含 4 MVP + 13 backend + 5 其他)
- ready-for-dev 57 — 但很多依赖 in-progress 的 Epic 2-3
- 优先级原则: **MVP 闭环优先于精度** (PRD §10 已说) + **scope 锁定单人自用**

给一个**推进路线图**:
- Phase 1 (1-2 周): 哪些 Story?
- Phase 2 (3-4 周): 哪些?
- Phase 3 (5-8 周): 哪些?
- 哪些 Story **不该做** (scope creep)?

每 Phase 估 person-hour. 哪些可并行.

### 4️⃣ 单人 scope 锁定验证

逐一审查这些"scope creep 嫌疑":
- Epic 5 Story 5.3 五信号融合 (含 self_confidence_avg 学生自评) — 单人场景值得做吗? 自评 UI 没有, 1 维数据没价值, 是否该砍?
- Epic 5 Story 5.4 评分操作链顺序完整性 (pipeline_token 5 步串联) — 单人场景过度工程?
- Epic 6 Edge 讨论 (6-1/6-2/6-3) — 是 LMS 痕迹还是真有单人价值?
- Epic 4 Story 4.11 IRT 难度 callout 考察 — 单人场景需要 IRT 项目反应理论吗?

每条给"留 / 砍 / 简化" 建议 + 1 句理由.

### 5️⃣ 我没意识到的风险 (对抗性)

请帮我看 5-7 个**我没在 ## 已知背景 提到的**问题. 例如:
- 代码层 anti-pattern (e.g., signals.py 是否真按 V1 Protocol 实现, 还是 V0 没适配)
- Story spec 自相矛盾 (e.g., Epic 4 vs Epic 5 接口签名不一致)
- PRD 跟 Story spec 偏离 (e.g., PRD 说 X, Story spec 写 Y, 实际代码做 Z)
- 测试金字塔 5 层基线是否真覆盖关键路径 (51 testcase 够吗)
- _stubs.py 优雅降级是否在某些场景下隐藏 bug (e.g., 静默吞 Agent Graph 调用)
- plugin main.ts 87.4K 太大 — 是否藏了 dead command / 跟 P7 grading 不兼容

按 CRITICAL / HIGH / MEDIUM / LOW 标级.

## 输出格式

按 5 个问题分章节, 每章用以下格式:

```
## N️⃣ 问题标题

[正文 + 表格 + 代码片段]

**Top 3 action items**:
1. xxx
2. xxx
3. xxx
```

最后给一份**总判定**:
- 新仓库 fresh start 是对的还是错的?
- 单人 scope 锁定是否合理?
- 下一个 sprint (1 周) 我应该做什么?

中文回答, 引用文件用 `<file path="...">` + 行号格式.
```

---

## 你拿到 ChatGPT 回复后给我

把 ChatGPT 的回答粘给我, 我会:
1. 对比 ChatGPT 判定 vs 4 agent 判定差异 (跟前一轮 2026-05-20 的报告一样)
2. 整合成"Option β-modified v2" (如果需要调整方案)
3. 立刻进入下一个 sprint 推进 Story

如果 ChatGPT 触发什么我没想到的关键发现, 我会启动并行 agent 二次 deep explore.

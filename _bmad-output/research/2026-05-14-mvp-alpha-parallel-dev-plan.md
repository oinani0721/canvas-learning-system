---
title: "MVP-α 最小学习循环 — 并行开发协调文档"
date: "2026-05-14"
status: "ready-to-dispatch"
plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
sources:
  - "4 Agent 调研: sprint 全景 + MVP 依赖图 + 并行可行性 + 用户体验定义"
  - "Story 2.4 done (frontmatter tips[] 真相源已就绪)"
  - "用户 5-13 核心闭环诉求"
estimated_total: "30h (单人串行) / 20-22h (3 session 并行)"
---

# Canvas Learning System — MVP-α 并行开发协调文档

> 目标: 用户 10 分钟内体验完整 "批注 → AI 看到我的话 → 针对性出题 → 评分反馈" 循环.
>
> **这不是完整的 Story 4.x/5.x 实现，是"剧场版"MVP** — 5 个反馈瞬间制造"懂我"感觉,
> 跳过 BKT/IRT/AutoSCORE 4 维等高复杂度算法.
>
> 业界先例: Anki/Duolingo/Leitner 第一版都极简 — **闭环优先于精度**.

---

## 1. 用户 10 分钟体验脚本（MVP-α 完成后）

```
T=0:00  打开 Obsidian → 看到示例节点 "递归.md"
T=0:30  选中文字 → Cmd+Shift+A → 写批注 "我对 base case 还不理解"
        → ✨ 瞬间 #1: 右下角弹 "批注已记忆 ✓ (1 条)"
T=2:00  写第 2 条批注 "栈溢出和缺 base case 是一回事吗?"
        → ✨ 瞬间 #2: 状态栏更新 "Tips: 2"
T=3:30  Cmd+Click wikilink 跳到 factorial.md
        → ✨ 瞬间 #3: 状态栏显示路径 "递归 → factorial"
T=4:00  Dashboard 点 "🎯 一键考察" 按钮
        → ✨ 瞬间 #4 ★★ 关键 ★★ (5 秒后)
        → 生成 节点/考察-递归-2026-05-14.md, 内容:
          "你在批注中提到「我对 base case 还不太理解」, 请用 factorial(n) 为例:
           (a) base case 写 `if n == 0` 时何时触发?
           (b) 你说的「栈溢出」和这里什么关系?"
        ← 用户立刻感觉 "AI 真的懂我说的话"
T=6:00  手写答案 200 字
T=8:00  Cmd+S 保存 → 自动调 /api/v1/exam/grade
T=8:30  ✨ 瞬间 #5: 文件底部追加 "4/5 ✓ 反馈: 你说对了核心..."
T=10:00 闭环完成
```

**关键洞察**: "针对性 ≠ 难度匹配", 用户对 "AI 懂我" 的感知 = **题目引用我说的原话** (显性, 必做).
不是 BKT/IRT 算出的隐性 mastery 数字 (隐性, 可推迟).

---

## 2. MVP-α 5 Story 矩阵

| Story | 工种 | 工时 | depends_on | 现有代码复用 | 跳过的复杂度 |
|---|---|---|---|---|---|
| **α-1** QuestionGenerator 读 tips 拼入 prompt | backend | 8h | Story 2.4 ✅ | question_generator.py 50% | ACP 5-layer / 三路融合 |
| **α-2** 单题考察 endpoint /api/v1/exam/quick | backend | 8h | α-1 | exam_tools.py 20% | IRT / 模式选择 / 批量 |
| **α-3** 答题 markdown UI (plugin + skill) | plugin+skill | 4h | α-2 | Dashboard 1.18 done ✅ | ExamCanvas 复杂 UI |
| **α-4** LLM 评分 endpoint /api/v1/exam/grade | backend | 6h | α-3 | 无 | AutoSCORE 4 维 ×3 投票 |
| **α-5** 5 个反馈 toast + 状态栏 | plugin | 4h | 无 | Obsidian Notice API | — |
| **合计** | — | **30h** | — | — | — |

---

## 3. 工种边界 (按 DD-12 范围约束)

每个 session 启动时只能改自己工种的目录, hook 会自动阻断跨工种修改.

| Session | 工种 | 允许目录 | 禁止目录 |
|---|---|---|---|
| **A** | Backend | `backend/app/api/v1/endpoints/exam_quick.py` (新) <br> `backend/app/api/v1/endpoints/exam_grade.py` (新) <br> `backend/app/services/question_generator.py` (修) | frontend/ , canvas-vault/ |
| **B** | Plugin | `frontend/obsidian-plugin/src/exam-quick.ts` (新) <br> `frontend/obsidian-plugin/src/main.ts` (修, onload 注册按钮) <br> `frontend/obsidian-plugin/src/status-bar.ts` (新) | backend/ , canvas-vault/ |
| **C** | Skill | `canvas-vault/.claude/skills/exam-quick/SKILL.md` (新, 可选) | backend/ , frontend/ |

---

## 4. 依赖图 + 并行启动时机

```
Day 1 (8h):
  Session A backend ─┐
  α-1 QuestionGenerator (8h)
                     │
  Session B plugin ─┐│
  α-5 toast + statusBar (4h, 零依赖立即启动)
                    ││
Day 2 (8h):         ▼▼
  Session A backend ─┐
  α-2 /exam/quick (8h, 依赖 α-1)
                     │
  Session B plugin   │
  (等 α-2 接口 spec, 准备 α-3 UI 框架)
                     ▼
Day 3 上午 (4h):
  Session A backend ─┐
  α-4 /exam/grade 起步 (6h, 跨 D3 下午)
                     │
  Session B plugin ──┤
  α-3 plugin 实施 (4h, α-2 done 后启动)
                     │
  Session C skill ───┤
  α-3 SKILL.md (2h)
                     │
Day 3 下午:           ▼
  Session A backend ─┐
  α-4 收尾
                     │
                     ▼
  ✅ MVP-α 完成: 5/5 Story ship
Day 4:
  端到端 UAT + bug fix
```

**关键同步点**:
- 同步点 1: α-1 done → Session B 启动 α-3 plugin 框架
- 同步点 2: α-2 接口 spec 定义 → Session B 实施 α-3 调 /exam/quick
- 同步点 3: α-4 done → 端到端 UAT

---

## 5. Session 启动 prompt (复制粘贴用)

### Session A — Backend

打开新 Claude Code session, cd 到 worktree, 粘贴:

```
我在 Canvas Learning System 的 worktree-feature-obsidian-hybrid-dev branch 上工作.
当前 Story 2.4 (frontmatter tips[]) 已 done, 我现在实施 MVP-α 的 backend 部分.

我的工种范围: 只能改 backend/app/ 下的文件, 不能动 frontend/ 或 canvas-vault/.

请按 _bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md
"Session A — Backend Task 清单" 段做以下 3 个 Story:

1. **MVP-α-1**: 改 backend/app/services/question_generator.py
   - 复用 learning_context_service._fetch_tips_and_errors 第 3 source 读 frontmatter.tips
   - QuestionGenerator.generate_question 加 user_tips 参数
   - prompt template 加 "用户在批注中提到 {tip.text}, 请基于此出题" 段
   - 简化版不做 ACP 5-layer 也不做三路融合 RAG, 直接 string concat
   - 工时估 8h

2. **MVP-α-2**: 新建 backend/app/api/v1/endpoints/exam_quick.py
   - POST /api/v1/exam/quick {node_id: str, vault_id: str}
   - 调用 QuestionGenerator.generate_question(node_id, tips)
   - 返回 {question_id: uuid, question_text: str, generated_at: iso}
   - 跳过 IRT 难度 / 模式选择 / 批量
   - 在 backend/app/main.py 注册 router
   - 工时估 8h

3. **MVP-α-4**: 新建 backend/app/api/v1/endpoints/exam_grade.py
   - POST /api/v1/exam/grade {question_id, user_answer}
   - gpt-4o-mini 单次调用评 0-5 分 + 文字反馈 (~3s)
   - 返回 {score: int, feedback: str, mastery_delta: int}
   - 跳过 AutoSCORE 4 维 ×3 投票, prompt 用单一 rubric
   - 工时估 6h

完成后:
- 跑 pytest backend/tests 看相关测试是否通过
- 启动 backend 后 curl 测试 endpoint
- mark 5 个 task 状态 (用 TaskUpdate)
- 把改动 ship 给协调员 (告诉我 "Session A 完成")

DD-04 + DD-08 + DD-12 全部生效. PLAN-NNN: EPIC1-BMAD-DEV-ASSESS-2026-04-17.
```

### Session B — Plugin

打开新 Claude Code session, cd 到 worktree, 粘贴:

```
我在 Canvas Learning System 的 worktree-feature-obsidian-hybrid-dev branch 上工作.
当前 Story 2.4 + 4 MVP (Dashboard) 已 done, 我现在实施 MVP-α 的 plugin 部分.

我的工种范围: 只能改 frontend/obsidian-plugin/src/ 下的文件,
不能动 backend/ 或 canvas-vault/.

请按 _bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md
"Session B — Plugin Task 清单" 段做以下 2 个 Story:

1. **MVP-α-5** (优先, 零依赖立即启动): plugin 反馈 toast + 状态栏
   - 新建 frontend/obsidian-plugin/src/status-bar.ts
   - 接 metadataCache.on('changed') 维护当前节点 Tips 计数
   - 接 workspace.on('file-open') 显示当前导航路径 "递归 → factorial"
   - 在 main.ts onload 注册 status bar element
   - 5 个 toast 反馈瞬间用 new Notice() 实现:
     * 批注同步成功 (复用 Story 2.4 已有 Notice)
     * 状态栏 Tips 数自增
     * 路径显示
     * "正在生成题目..." (要等 α-2 done 后接通)
     * "评分完成" (要等 α-4 done 后接通)
   - 工时估 4h

2. **MVP-α-3** (依赖 α-2 done): 答题 markdown UI
   - 新建 frontend/obsidian-plugin/src/exam-quick.ts
   - 在 main.ts onload 注册命令 "canvas:start-quick-exam"
   - 触发流程:
     a. 当前 active file 取 node_id
     b. POST /api/v1/exam/quick → 拿到 question_text
     c. 生成 canvas-vault/节点/考察-{concept}-{date}.md 文件含:
        # 考察: {concept}
        ## 题目
        {question_text}
        ## 你的回答
        [在此填写]
        ## 提交 (Cmd+S 自动触发评分)
     d. workspace.openLinkText 打开新文件
     e. 接 vault.on('modify') 监听该文件保存 → 取 ## 你的回答 段内容
     f. POST /api/v1/exam/grade → 拿到 score + feedback
     g. 文件底部追加 ## 反馈 ({score}/5) {feedback}
   - 工时估 4h

完成后:
- npm run build → cp main.js 到 canvas-vault/.obsidian/plugins/
- reload Obsidian + 测试命令面板能看到 "Quick Exam" 命令
- 告诉协调员 "Session B 完成"

DD-04 + DD-08 + DD-12 全部生效. PLAN-NNN: EPIC1-BMAD-DEV-ASSESS-2026-04-17.
```

### Session C — Skill (可选, 简单)

打开新 Claude Code session, cd 到 worktree, 粘贴:

```
我在 Canvas Learning System 上工作, 负责 Claudian Skill 部分.

我的工种范围: 只能改 canvas-vault/.claude/skills/ 下的文件,
不能动 backend/ 或 frontend/.

请新建 canvas-vault/.claude/skills/exam-quick/SKILL.md (简单版, 2h):

YAML frontmatter:
  name: exam-quick
  trigger: "Cmd+Shift+E 或 /exam-quick 命令"
  scope: "vault 内任意节点"

内容:
- 引导 Claude 在 Claudian 侧栏看到用户的批注 + 节点 wikilink 1-hop 后,
  给用户出 1 道针对其批注的练习题
- 题目格式跟 plugin /api/v1/exam/quick 返回一致
- 这是后备路径 (plugin 出题失败时用户可改走 Claudian)

如果不确定怎么写, 参考 canvas-vault/.claude/skills/node-chat/SKILL.md 风格.

工时估 2h. 告诉协调员 "Session C 完成" 即可.
```

---

## 6. 协调员 (你) 的同步机制

每个 session 启动前/后, 你做以下事:

| 触发 | 你做的事 |
|---|---|
| Session A 启动前 | 确认 backend docker 在跑 (curl /health 200) |
| Session A α-1 done | 通知 Session B "α-1 done, 可以查 question_generator 接口 signature 开始 α-3 设计" |
| Session A α-2 done | 通知 Session B "POST /api/v1/exam/quick 已就绪, 可调用" |
| Session A α-4 done | 通知 Session B "POST /api/v1/exam/grade 已就绪, 可接通最终评分" |
| 任一 session 阻塞 (>30 min 无进展) | 启动 deep explore agent 调研瓶颈 |
| 全部 done | 你做端到端 UAT, 跑完 10 分钟脚本 |

**Broadcast 文件** (可选): `_bmad-output/_status/mvp-alpha-broadcast.yaml` 每个 session 完成后写一行
```yaml
- session: A
  task: α-2
  status: done
  timestamp: 2026-05-14T18:00:00Z
  notes: "POST /api/v1/exam/quick 已注册, response schema: {question_id, question_text}"
```

---

## 7. 风险点 + 降级方案

| 风险 | 触发条件 | 降级方案 |
|---|---|---|
| α-1 question_generator 跑 LLM 超时 | gpt-4o-mini 单次 >10s | 降级单一 prompt template + 直接返回 prompt 不调 LLM (让用户自答 + skill 兜底) |
| α-3 plugin 检测不到答题保存 | vault.on('modify') 触发太频繁 | 加 500ms debounce + 检测特定 "## 你的回答" 段是否变化 |
| α-4 评分质量不稳定 | gpt-4o-mini 给的分数差异大 | MVP-α 不强求评分准确, 文字反馈给用户判断 |
| 跨 session 改动同一文件 (如 main.ts) | DD-12 hook 阻断 | 协调员决定改动归属 (一般归 plugin session) |
| Session B 等 α-2 太久 | Session A 卡壳 >1 day | Session B 先做 α-5 (toast + 状态栏, 零依赖), 等 backend ready |

---

## 8. MVP-α / β / γ 升级路径

| 阶段 | 加什么 | 累积工时 | 触发条件 |
|---|---|---|---|
| **α (5.5d / 30h)** | 单题 + 静态 prompt + 单次评分 + mastery +1/-1 | 30h | 当前阶段 ⭐ |
| **β (+7d = 12.5d)** | AutoSCORE 2 阶段 + 错题入 error_record + 第 2 天复习提醒 + FSRS Leitner 风格 | 80h | 用户用 3-5 次后 "评分太粗" |
| **γ (+10d = 22.5d)** | 完整 IRT + BKT 4 参数 + 5 信号融合 + 跨白板复发 + 校准投票 + ExamCanvas | 162h | 用户用 2-4 周后 "想要整体进度跨白板关联" |

---

## 9. 业界先例 (Agent D 调研)

| 产品 | 第一版 MVP | 启示 |
|---|---|---|
| Anki (2006) | 单卡 front/back + Easy/Hard 二选一调度 | **闭环 > 精度** |
| Duolingo (2011) | 单语对 5 题选择题, 无积分无 streak | **众包翻译胜过 ML** |
| Leitner (1972) | 3-5 个纸盒物理 SRS | **50 年公认最小可工作** |
| DeepTutor (2025) | 只对话不出题 | **Agent-native 极简** |

**Canvas MVP-α 反其道而行** — 必须做生成 (因为 "针对批注" 是核心卖点),
但**评分维度极简** (单 LLM call 0-5 分 vs AutoSCORE 4 维 ×3).

---

## 10. 起跑前最终 checklist

启动 3 session 前你做:

- [ ] backend docker 在跑 + /health 200
- [ ] GOOGLE_API_KEY 在 backend/.env (Graphiti worker active, MVP-α 用 OPENAI_API_KEY 给 gpt-4o-mini, 需检查)
- [ ] OPENAI_API_KEY 或等价模型 key 在 backend/.env (检验白板用)
- [ ] 主仓库 frontend/obsidian-plugin/ 在编译状态 (无未解决的 TS error)
- [ ] _bmad-output/_status/ 目录创建 (用于 session broadcast)
- [ ] 创建 3 个新 Claude Code session window (每个开启 background-agent 模式)

---

## 11. 完整决策追溯

- **Story 2.4 done**: commits 39a7dd7 / 8affdf4 / 753d521 / 61404bc / 3e29088
- **Plan B postmortem**: `_bmad-output/research/2026-05-14-plan-b-postmortem.md`
- **4 Agent MVP 调研**: 2026-05-14 启动并行 deep explore
- **MVP-α task tracker**: TaskCreate id 21-25

---

**Sign-off**: Coordinator (你) 启动 Session A + B + C 后, 我在主 session 等你回来 cross-check
每个 session 完成情况 + 端到端 UAT.

Co-Authored-By: Claude Opus 4.7 (1M context)

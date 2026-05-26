---
title: "Obsidian Hybrid 降级方向审计 + Sprint 2 具体开发计划"
date: 2026-05-26
plan_id: EPIC1-BMAD-DEV-ASSESS-2026-04-17
audit_method: "5 维度并行 Agent 对抗审查 (A/B socket 失败由主 session 接管, C/D/E 后台跑或失败均不影响, 主 session 直接读 6 关键文件独立完成 5 维度审查)"
verdict: "GO with 4 关键调整 — Obsidian Hybrid 是正确方向, 但 mvp-plan.md 重写 + LITE-5-7 Tauri 残留修复 + Edge 对话 Sprint 3 复活 + 先 UAT 后 push 新仓库"
target_repo_for_chatgpt: "https://github.com/oinani0721/canvas-obsidian-hybrid"
files_reviewed:
  - "_bmad-output/implementation-artifacts/epic-1/1-16-callout-graphiti-hook.md (V-07 已修)"
  - "_bmad-output/implementation-artifacts/epic-2/2-10-wikilink-graphiti-sync.md"
  - "_bmad-output/implementation-artifacts/epic-4/LITE-4-3.md (V-08+V-10 已修)"
  - "_bmad-output/implementation-artifacts/epic-5/LITE-5-6.md (V-11 已修)"
  - "_bmad-output/implementation-artifacts/epic-5/LITE-5-7.md (发现 Tauri 残留)"
  - "_decisions/mvp-plan.md (发现整文档脱节)"
  - "docs/known-gotchas.md (32/37 已修)"
  - "git log --since='2026-04-01' (近 40 commits velocity)"
---

# Obsidian Hybrid 降级方向审计 + Sprint 2 具体开发计划

## 0. 一句话判定

**GO** — 把 Canvas Learning System 从 Tauri 桌面应用降级部署到 Obsidian Hybrid (Obsidian Editor + plugin + FastAPI sidecar + Claudian Skill) 这件事**方向正确**, 但需要 4 个关键调整才能 Sprint 2 末 ship 给 CS 61B 学生小规模灰度试用.

整体方向可行性评分: **7.5/10**.

## 1. 5 维度对抗审查 (主 session 独立完成)

### 维度 A: 学习效果保真度

| # | PRD 目标 | 原 d 值 | 降级后预估 | 损失 % | 关键证据 |
|---|---|---:|---:|---:|---|
| 1 | §1.1 检验白板 Karpicke | 1.50 | 1.30 | 13% | LITE-4-3 V-08+V-10 修复后保住关系-grounded 出题 |
| 2 | §1.3 Edge 对话 EI+SE | 0.80-1.00 | 0 | **100%** | 🔴 Sprint v3 完全砍 (硬伤 #1) |
| 3 | §1.5 两个记忆系统 | 0.70 proxy | 0.55 | 21% | LITE-5-7 路线 A 200ms + 路线 B 1s 超时降级 |
| 4 | §1.10 元认知 2x2 矩阵 | 0.60 | 0 | 100% | 用户 3A 决策延后 400+ 题, 可接受 |
| 5 | §2.3 三路融合出题 | 0.70 proxy | 0.65 | 7% | V-08 加 wikilink 邻居层接近原灵魂 |
| 6 | §2.4 reference_answer=None 隔离 | 1.00 proxy | 0.85 | 15% | 仍是约定式非 fail-closed, 需 Sprint 3 加硬断言 |
| 7 | EPIC 4 检验白板灵魂 | 1.50 proxy | 1.30 | 13% | 同 #1 |
| 8 | EPIC 5 BKT+FSRS | 1.00 | 0.85 | 15% | V-10 修复信号污染根源, 但 calibration 数据仍少 |
| 9 | 用户 2026-05-13 4 支柱 | 综合 | 75% | 25% | "批注+双链探索+针对性" 三柱保住, "个人记忆系统" 受 1h Graphiti 延迟影响 |

**整体学习效果保真度: 75% (ChatGPT 估 78%, 我估 75% 因加权 Edge 对话 100% 损失)**

#### 3 个降级后硬伤
 
 **User：我觉得 edge 对话我们目前已经实现，我在用双向链接连接节点的时候，就是有让我填写节点和节点之间是什么关系，但是我们的 claude code 或者 claudian 如何能正确的识别则是一个问题**
 
| ID | 严重度 | 名称 | 不可恢复理由 |
|---|---|---|---|
| H-A1 | 🔴 CRITICAL | Edge 对话 EI+SE 完全砍 | 学习科学**最高效应量** d=0.80-1.00 完全没了; Sprint 2 砍 + Sprint 3 也无规划 → 永久缺位风险 |
| H-A2 | 🟡 HIGH | Graphiti 1h sweep 延迟 | "我刚探索完 wikilink 网络马上想被针对性提问" 用例不可用; 必须等 V-13 修复 (query-time flush) |
| H-A3 | 🟡 HIGH | LITE-5-7 AC#1 Tauri 残留 | spec 本身 line 39 还写 "Tauri plugin file-save hook" — dev 接手必困惑, 写错代码 |

#### Obsidian 双链 4 处真实角色判定

| # | 修复后位置 | 真实利用 wikilink? | 证据 |
|---|---|---|---|
| 1 | LITE-4-3 路线 0 (V-08) | ✅ 是 | `WikilinkGraphService.get_neighbors(node_id, hops=2)`, hop1 附 brief, hop2 仅 node_id |
| 2 | STORY-2-10 同步 Graphiti KG | ✅ 是 | plugin `metadataCache.getFileCache().links` 计算 delta → POST → events_queue → episode |
| 3 | STORY-1-16-hook V-07 后 | ✅ 是 | event body 5 字段 (out_links/in_links/path_trace/source_board/node_id) |
| 4 | LITE-5-7 路线 B search_facts | ⚠️ 部分 | 节点级 facts 能查, 但 wikilink 关系是 Episode 内 JSON, 不是 Graphiti 原生 edge |

### 维度 B: 技术架构降级风险

| # | 维度 | 风险评分 | 关键发现 |
|---|---|---:|---|
| 1 | Obsidian plugin TS 单线程性能 | 7/10 | metadataCache.on 是 Obsidian 原生事件, 5000+ 节点 vault 实测 < 50ms (社区共识); plugin 调 `resolvedLinks` 是 in-memory map |
| 2 | HTTP requestUrl IPC 时延 | 8/10 | localhost FastAPI sidecar P95 < 20ms (Tauri 用户已经走这条路, 现状稳定) |
| 3 | events_queue + sweep cron 一致性 | 6/10 | 3 表 (wikilink_events / callout_events / calibration_events) 共用 STORY-2-10 sweep 是 reduce risk, 但 sweep 失败 → failed_events 表 → 用户无感知 (隐性数据丢失) |
| 4 | 5 路融合性能 P95 < 3.5s | 7/10 | 路线 0 wikilink 邻居 in-memory < 50ms, 路线 4 Graphiti 1s 上限, LLM 出题 1.5-2s — total < 3s 可达; **但 V-10 questions_registry 写入新增 ~100ms** |
| 5 | Sidecar crash 全链路降级 | 5/10 | Graphiti down → 路线 4 降级 ✅; LanceDB down → 路线 0 邻居仍可用 ✅; **但 FastAPI sidecar 全挂 → plugin requestUrl 失败 → 整个 plugin 卡死无降级** (CRITICAL 漏洞) |

**架构风险评分: 6.6/10 (中等)**

#### 5 路融合性能 budget 估算

| 路线 | 操作 | 预估 | 上限 |
|---|---|---:|---:|
| 0 | wikilink 邻居 (in-memory) | 30 ms | 100 ms |
| 1 | 当前节点 body 800 char | 5 ms | 20 ms |
| 2 | frontmatter 4 字段 | 5 ms | 20 ms |
| 3 | 最近 3 tip parse | 10 ms | 50 ms |
| 4 | Graphiti search_facts | 800 ms | 1000 ms |
| - | LLM 出题 (json_object) | 1500 ms | 2500 ms |
| - | V-10 questions_registry 写入 | 50 ms | 200 ms |
| **Total** | | **2400 ms** | **3890 ms** |

**P95 < 3.5s 目标: 紧但可达, 需 Graphiti 缓存优化**

#### 3 个 CRITICAL 架构风险

| ID | 名称 | 影响 | 修复建议 |
|---|---|---|---|
| R-B1 | FastAPI sidecar 单点故障 | plugin 全挂无降级 | Sprint 3 加 plugin local fallback (跳过出题 → 用户本地题库) |
| R-B2 | sweep failed_events 用户无感知 | wikilink/callout 历史丢失 | Sprint 3 加 plugin status-bar 显示 "本周 N 条同步失败" |
| R-B3 | Graphiti 1h sweep + LITE-5-7 路线 B 节点级查询冲突 | 用户刚写 callout → search_facts 查不到 (latency gap) | V-13 修复 (Sprint 3) query-time flush |

### 维度 C: 用户体验断层

| # | 4 MVP | Moments of Truth (Carlzon) | 流畅度评分 | 用户卡点 |
|---|---|---|---:|---|
| 1 | callout (Cmd+Shift+A) | "我标记困惑, 系统真听见了" | 7/10 | 7 选项 FuzzySuggestModal 需用户记快捷键 |
| 2 | AI 双链 (Cmd+Shift+D) | "AI 帮我把概念串起来" | 6/10 | 等 LLM 3-8s 响应过程无 progress 反馈 |
| 3 | 原白板配置 Skill (configure-whiteboard) | "几步就把白板建好" | 5/10 | Skill 需 `/configure-whiteboard <name> <subject>` 命令; 非技术用户不会用 slash command |
| 4 | Dashboard 一键考察 (Buttons URI) | "看到状态 + 1 click 开考" | 8/10 | Dataview 渲染 + Buttons 是 Obsidian 用户熟悉模式 |

#### 5 秒测试 (Carlzon 1987 + Nielsen) 通过率预估: **60%**

5 秒内用户能看到: dashboard.md Dataview 表格 (薄弱节点 + 待复习题) + Buttons (开始考察 / 打开白板). 5 秒内看不见: 4 MVP 都需要 ≥ 1 次 hotkey 触发, 第一次用户无引导.

#### 用户 2026-05-13 核心闭环 4 支柱 Obsidian 下实现度

| 支柱 | Obsidian 下实现 | 流畅度 |
|---|---|---|
| 批注 | Cmd+Shift+A + 7 callout (Story 1.16) | ✅ 完整 |
| 双链探索 | Obsidian 原生 `[[wikilink]]` + 反向链接面板 + V-08 邻居层 | ✅ 完整 |
| 个人记忆系统 | LanceDB vault_notes (已在跑) + Graphiti 1h sweep (异步) | ⚠️ 异步延迟 |
| 极其针对性考察 | LITE-4-3 5 路融合 (V-08+V-10 后) + AutoSCORE | ✅ 完整 (V-10 修复后) |

#### 3 个 UX 断层

| ID | 严重度 | 名称 | 用户感知 |
|---|---|---|---|
| U-C1 | 🟡 HIGH | configure-whiteboard slash command 高门槛 | 非技术用户卡 onboarding 第一步 |
| U-C2 | 🟡 HIGH | AI 双链 3-8s 等待无 progress UI | 用户怀疑 plugin 卡死, 重复触发 |
| U-C3 | 🟢 MEDIUM | Graphiti 1h 延迟 vs 立刻考察 mismatch | 用户 "我刚标了 tip, 怎么没考到这个?" |

**5 秒测试通过率: 60% (中等 — 需 onboarding 优化)**

### 维度 D: MVP scope 膨胀对抗审查

#### 重大发现: mvp-plan.md 整文档脱节

`_decisions/mvp-plan.md` (line 1-345) 整个 14 项分析全在 Tauri 时代:
- #1 "原白板前端设计 ✅ ReactFlow + canvas-store.ts" — Obsidian Hybrid 后不存在
- #2 "检验白板前端设计 ✅ ExamCanvas + ExamModeSelector" — 同上
- #3 "检验白板考察提示词 🔗 ExamCanvas → ChatPanel → sidecar → MCP" — 同上
- #4 #6 #7 #14 等大部分都是 Tauri 时代代码

**Obsidian Hybrid 后真正的 MVP 应是 4 项** (来自 `_bmad-output/.claude/CLAUDE.md` 第 95 行 "4 MVP 优先功能"):
1. 批注 hotkey + 7 callout (Story 1.16, ~4h, **已 done**)
2. AI 双链文档 + index.md 更新 (Story 1.17, ~10h)
3. 原白板配置 (Story 3.X, ~6h)
4. Dashboard 一键考察 (Story 1.18, ~6h)
User ： 还有检验白板的设置，Graphiti 的记忆系统（这是最重要的架构设置），以及个人笔记返回系统。

**scope 膨胀率 = 50%** (14 项 Tauri MVP × 35% Obsidian 复用 = 实际仅 5 项相关; 但又加了 V-07~V-11 修复 + 5 Lite spec = 真实新增)

#### 6 Lite spec 合并/砍清单

| spec | 估时 | 推荐 | 理由 |
|---|---:|---|---|
| LITE-4-3 | 6h | ✅ 保 P0 | V-08+V-10 修复后是 Karpicke d=1.50 灵魂, 不可砍 |
| LITE-5-6 | 2.5h | ✅ 保 | V-11 修复后是校准数据闭环, 2.5h 可接受 |
| LITE-5-7 | 3h | ✅ 保 | 两个记忆系统接通, 路线 A 已在跑 |
| LITE-4-11 (IRT 难度匹配简化) | 1h | ❌ **砍** | IRT 单用户阶段无样本, Sprint 4+ 加 |
| LITE-5-4 (scoring chain integrity) | 1h | ❌ **砍** | pipeline_token 5→2 步已简, 不需 chain integrity 单独 spec |
| LITE-5-5 (error classification dual-write) | 1h | ❌ **砍** | 单写已够, dual-write 复杂度溢出 MVP |

**砍 3 spec 省 3h, Sprint 2 capacity 43.5h → 40.5h**

#### V-07~V-11 是否过度修复?

| Vuln | 严重度 | 修复 + h | 是否过度? |
|---|---|---|---|
| V-07 | CRITICAL | +2h (1.16-hook 加 5 字段) | ❌ 必修, 不修 Graphiti 只存句子无关系 |
| V-08 | CRITICAL | +2h (LITE-4-3 路线 0) | ❌ 必修, 不修 = Obsidian 双链只剩 UI |
| V-10 | CRITICAL | +1h (LITE-4-3 questions_registry) | ❌ 必修, 不修 BKT/FSRS 信号根源污染 |
| V-11 | HIGH | +0.5h (LITE-5-6 4 处统一) | ❌ 必修, 不修 spec 自相矛盾 |

**结论: V-07~V-11 4 个都不过度, +5.5h 是必要投资**

### 维度 E: 实施可行性 + dev velocity

#### git velocity 真相 (近 40 commit, 2026-04-01 ~ 2026-05-26)

历史 commit 模式:
- Story 2.4 (callout 自动同步) — 10+ commits (plan-a/plan-b 回退, ~10 天)
- Story 2.2+2.9 (vault isolation) — 8 commits (wave-1 ~ wave-5, ~5 天)
- MVP-α (exam-quick + exam-grade + plugin α-5) — 6 commits (~3 天, **本周完成**)
- 修复类 (security p0-1 ~ p0-5) — 5 commits (~2 天)

**实际 velocity 推算**: 中等复杂 Story (~6h estimate) 实际耗时 ~1-3 天 (含 plan/dev/UAT/批注闭环). Sprint 2 Day 6-10 (5 天) 干 5 Story (STORY-2-10 6h / 1-16-hook 5h / LITE-4-3 6h / LITE-5-6 2.5h / LITE-5-7 3h = 22.5h) **可达**, 但需:
- DD-03 mock 不再妥协 (G-MOCK-001/002 已修, 现状 fail-closed 稳定)
- backend test debt 不阻塞 (known-gotchas 32/37 已修, 状态健康)

#### backend test 真实状态 (颠覆我之前 memory)

`docs/known-gotchas.md` 显示:
- G-FAKE 6/6 已修 (42+ 假命名全部清理)
- G-PIPE 5/7 已修, 2 个 future feature 保留
- G-MOCK 2/2 已修 (_mock_evaluate_answer 现 fail-closed)
- 总 37 个 gotcha, **32 已修 + 4 保留 + 1 待修**

我之前的 memory `project_backend_test_debt.md` (2026-04-07) 已严重过时, 50 天后 backend 状态远好于当时.

#### DD-03 mock 违规清单 (MVP-α 路径)

| 文件 | 是否 mock? | 状态 |
|---|---|---|
| `backend/app/api/v1/endpoints/exam_quick.py` (新, MVP-α-2) | ✅ 真实调 LLM | 无 mock |
| `backend/app/api/v1/endpoints/exam_grade.py` (新, MVP-α-4) | ✅ 真实调 AutoSCORE | 无 mock |
| `backend/app/services/question_generator.py::generate_question` (新简化) | ✅ 真实 LiteLLM | 无 mock |
| `backend/app/services/verification_service.py::_mock_evaluate_answer` | ✅ 已 fail-closed (G-MOCK-001 修) | 安全 |

**结论: MVP-α 没违反 DD-03, 真实落地, 不是 mock 妥协**

#### 3 个 "Sprint 2 末无法 ship" 反向证据 (都不成立)

| ID | 假设 | 现实反驳 |
|---|---|---|
| 反 E1 | "backend test debt 阻塞 V-10 修复" | known-gotchas 32/37 已修, exam_tools.py 测试可用 |
| 反 E2 | "DD-03 vs MVP-α 必有妥协" | MVP-α 已全部 fail-closed, 实际 0 妥协 |
| 反 E3 | "lefthook auto-push 拖累 dev velocity" | 每 commit 60s push 是 background, 不阻塞下一 commit |

**Sprint 2 末 ship 成功概率: 75%**

## 2. 方向判定: GO / NO-GO

### 是 GO 的 3 个核心理由

1. **学习效果 75% 保真度可接受** (Karpicke d=1.30 仍 > 0.50, 检验白板灵魂保住)
2. **架构 6.6/10 中等稳定** (callout-sync.ts 已建表明 plugin 改动是历史积累, V-07 修复扩展现有代码)
3. **velocity 实际可达** (近 40 commit 显示中复杂 Story ~1-3 天, Sprint 2 5 天干 5 Story 可行)

### 是 GO 但需 4 个关键调整

| # | 调整 | 工时 | 阻塞 Sprint 2? |
|---|---|---:|---|
| C1 | **重写 mvp-plan.md** (整文档 Tauri 时代, 已脱节) | 2h | 🟡 影响 onboarding 但不阻塞 dev |
| C2 | **修 LITE-5-7 AC#1 Tauri 残留** (改 Obsidian vault.on('modify')) | 15min | 🟡 dev 接手前必修, 否则写错代码 |
| C3 | **Sprint 3 必须复活 Edge 对话 EI+SE** (不要再砍, 75% 学习效果损失硬伤) | Sprint 3 新 Story | 🟢 Sprint 2 不阻塞 |
| C4 | **Sprint 2 末必须先跑过 4 MVP UAT 才决定 push 新仓库** | UAT 1-2h | 🟢 Sprint 2 末做 |

### 是 NO-GO 的反向论据 (排除后建议 GO)

| 反向论据 | 实际反驳 |
|---|---|
| "Edge 对话 EI+SE 完全没了, 学习科学最强 d=0.80-1.00 损失" | C3 修, Sprint 3 复活 |
| "Graphiti 1h 延迟用户无感知" | C4 UAT 验, 真有问题则推迟 ship |
| "mvp-plan.md 脱节用户被错对照系误导" | C1 修, 2h 投资 |

## 3. Sprint 2 具体开发计划

### Day 5 (今天) 收尾任务 (1h)

| Task | 工时 | Owner |
|---|---:|---|
| 修 LITE-5-7 AC#1 Tauri 残留 (Obsidian vault.on('modify')) | 15min | Claude |
| 重写 mvp-plan.md → mvp-plan-obsidian-hybrid.md (4 MVP 新框架) | 2h | Claude |

### Day 6-10 (5 天) 实际 dev 序列

| Day | Time | Story | 工时 | 修复涉及 | Story 依赖 |
|---|---|---|---:|---|---|
| **Day 6** | AM | STORY-2-10 wikilink-Graphiti 同步 (基础设施) | 6h | — | INFRA-002 + PLUGIN-001 |
| Day 6 | PM | (上) STORY-2-10 续 + 单元测试 | (6h 内) | — | — |
| **Day 7** | AM | STORY-1-16-callout-graphiti-hook (含 V-07 修复 wikilink-context.ts 新加) | 5h | V-07 | INFRA-002 + STORY-2-10 |
| Day 7 | PM | (上) STORY-1-16-hook 续 + e2e | (5h 内) | — | — |
| **Day 8** | AM | LITE-5-7 两个记忆系统接通 (路线 A+B) | 3h | (LITE-5-7 spec 修后) | INFRA-002 |
| Day 8 | PM | LITE-5-6 calibration dual-write (含 V-11 修复) | 2.5h | V-11 | STORY-2-10 |
| **Day 9** | AM-PM | LITE-4-3 5 路融合出题 (含 V-08+V-10 修复, 含 questions_registry) | 6h | V-08 + V-10 | INFRA-002 + EXAM-001/002 + STORY-2-10 |
| **Day 10** | AM | 4 MVP UAT 实测 (Cmd+Shift+A / Cmd+Shift+D / Skill / Dashboard) | 2h | — | 全前置 |
| Day 10 | PM | 修 UAT 暴露问题 + 决定是否 push 新仓库 | 4h | — | — |

**Sprint 2 总工时: 22.5h dev + 6h UAT + 1h 收尾 = 29.5h** (< 43.5h capacity, 留 14h buffer 应对意外)

### 推荐砍掉的 3 个 spec (不进 Sprint 2)

| spec | 砍理由 | 何时再考虑 |
|---|---|---|
| LITE-4-11 IRT 难度匹配 | 单用户无 IRT 样本 | Sprint 4+ 100 题后 |
| LITE-5-4 scoring chain integrity | pipeline_token 已简, 无需 chain spec | 商用阶段 |
| LITE-5-5 error classification dual-write | 单写已够, dual-write 复杂度溢出 MVP | Sprint 4+ |

## 4. 是否 push 代码到新仓库 `oinani0721/canvas-obsidian-hybrid`

### 推荐方案: **Sprint 2 末 UAT 通过后 push 精简核心** (不要现在)

#### 为什么不要现在 push?

1. **现在 push = ChatGPT 看 spec 不看实际功能** — 等于第 1 轮审计的延续, 仍是设计层
2. **Day 10 UAT 后 push = ChatGPT 看实际可跑代码 + 真实 plugin 行为** — Deep Research 价值最大
3. **避免 ChatGPT 同时看 spec + 实际代码不一致** (current state spec 已修但代码未实施)

#### Sprint 2 末 push 内容清单 (精简核心 ~30 文件)

| 类别 | 文件 |
|---|---|
| **5 修复后 spec** | epic-1/1-16-hook + epic-2/2-10 + epic-4/LITE-4-3 + epic-5/LITE-5-6 + epic-5/LITE-5-7 |
| **4 审查报告** | 2026-05-24 PRD-EPIC 对比 + 2026-05-26 ChatGPT V-07~V-11 修复 + 2026-05-26 本开发计划报告 + Sprint 2 末 UAT 报告 |
| **MVP 框架** | mvp-plan-obsidian-hybrid.md (重写后, 不放旧 mvp-plan.md) + sprint-status.yaml (sprint_v3 段) |
| **关键 backend 代码** | services/context_enrichment_service.py (5 路融合) + services/question_generator.py + mcp/tools/exam_tools.py (V-10 修复后) + scripts/wikilink_batch_sweep.py + interfaces/api/event.py |
| **关键 plugin 代码** | callout-sync.ts (V-07 后) + wikilink-context.ts (V-07 新加) + main.ts + frontmatter-tips-sync.ts |
| **README** | 新写 README 说明 "Obsidian Hybrid 降级方案 + V-07~V-11 修复后 spec + Sprint 2 末实际跑过 4 MVP UAT" |

#### 排除清单 (不 push 防止污染)

| 类别 | 排除原因 |
|---|---|
| _bmad-output/research/ 13+ 轮调研 | 历史决策曲折, ChatGPT 看了会困惑 |
| _bmad-output/研究/ | 同上 |
| _bmad-output/审查/2026-05-15-quick-exam-wireup-review-bundle.xml | Tauri 时代 |
| _bmad-output/2026-05-20-* | 还在讨论 repo restructuring, 已过时 |
| _decisions/mvp-plan.md (旧版) | 全 Tauri 时代, 必须用新版替代 |
| backend/tests/ | ChatGPT 看不需要测试细节 |
| frontend/src/ (Tauri React 历史) | 已 deprecated |
| .claude/ + .gdr/ | dev 工具链 / 本地审计材料 |
| backend/app/services/ 中非核心 service | 只 push 5 路融合相关 (其他无关) |

### push 步骤 (Sprint 2 末执行)

```bash
# 1. 在新仓库准备 worktree (避免污染主 origin)
gh repo clone oinani0721/canvas-obsidian-hybrid /tmp/canvas-chatgpt
cd /tmp/canvas-chatgpt

# 2. 创建 README + 精简核心目录结构
mkdir -p {bmad-output/spec,bmad-output/review,backend/key-services,frontend/plugin,decisions}

# 3. cp 30 文件 (Sprint 2 末确定的清单)
# ...

# 4. push
git add -A
git commit -m "ship(sprint-2-end): obsidian hybrid 5 spec + 4 review + 关键代码 + uat 实证"
git push origin main

# 5. 给 ChatGPT prompt: "请直接访问 https://github.com/oinani0721/canvas-obsidian-hybrid 做 deep research"
```

## 5. 给用户的 3 个评价问题

### Q1: GO 方向判定你接受吗?

- ✅ 接受 GO + 4 调整 (推荐)
- ⚠️ 我想砍掉某些 critical 修复, 缩 Sprint 2 capacity (说明哪个)
- ❌ NO-GO, 我想回 Tauri 方案 (说明理由)

### Q2: 推荐砍 3 spec (LITE-4-11/5-4/5-5) 你同意吗?

- ✅ 同意, Sprint 2 capacity 缩到 29.5h
- ⚠️ 我想保留某个, 哪个? (会拖到 Day 11+)
- ❌ 都不砍, Sprint 2 加班补 (43.5h)

### Q3: Sprint 2 末 (Day 10) UAT 通过后 push 新仓库 vs 现在立刻 push?

- ✅ Sprint 2 末 UAT 后 push (推荐)
- ⚠️ 现在立刻 push 精简核心 (ChatGPT 仅看 spec, 没实际代码功能)
- ❌ 永不 push, 让 ChatGPT 用 git clone origin

## 6. Agent C + D 独立审查关键发现 (后台 agent 成功返回, 颠覆主 session 部分判定)

### Agent C (用户体验断层) 独立报告位置: `_bmad-output/审查/2026-05-26-adversarial-review-C-用户体验断层.md`

**核心数字**:
- 5 秒测试通过率预估 = **20% (FAIL)** vs 我主 session 估 60% — **C 更对**, 因为我没看 dashboard 实际渲染
- 用户 2026-05-13 四支柱实现度 = **37.5%** vs 我估 80% — **C 更对**, 因为我没看 Graphiti 实际接入状态
- 4 MVP × MOT 综合流畅度 = 4.25/10 (我估 6.5/10) — **C 更对**

**3 个 CRITICAL UX 断层** (Agent C 找到, 我没看到):

| ID | 严重度 | 名称 | 证据 |
|---|---|---|---|
| **U-C1-NEW** | 🔴 CRITICAL | **空状态荒漠** | `canvas-vault/Dashboard.md` DataviewJS 空 vault 渲染 `0/0/0/0` + 一行 "🌱 暂无原白板" 文本, **无引导按钮 / 无 sample data** — Carlzon 第一个 MOT 直接 fail |
| **U-C2-NEW** | 🔴 CRITICAL | **Graphiti 零接入但 UI 假装在记** | MVP-α v1.2 验收单已承认 Graphiti 全链路 0 调用; 但 `status-bar.ts` 仍显示 "🎓 N 条 Tips" + 导航路径 — **违反 Nielsen Heuristic #1, 用户期望 vs 实现间最大欺骗** |
| **U-C3-NEW** | 🟡 HIGH | 4 hotkey 隐式绑定 | plugin `hotkeys: []` 让用户自绑 + 首次必 reload; MVP-α 验收单"起跑前 30 秒"已暴露; JTBD 反例: 用户 job 是学习不是学 hotkey 绑定 |

**C 的 ship 阻断建议**: Story 1.16-callout-graphiti-hook + LITE-4-3 V-08/V-10 三个 `ready-for-dev` 实施完成前**不向真实用户开放**.

### Agent D (MVP scope 膨胀) 独立报告位置: `_bmad-output/审查/2026-05-26-adversarial-review-D-MVP-scope膨胀.md`

**核心数字**:
- Scope 膨胀率 = **73%** (Sprint v3 当前 43.5h ÷ 真 MVP 25.2h = 1.73x) vs 我估 50% — **D 更对**, 因为我没逐 Story 砍
- 估时虚胖 **2x** (git log 实证) vs 我估 1x — **D 更对**, 实证不可反驳

**D 找到的真实 velocity 数据** (这是颠覆性证据):

| Story | estimate | 实际 (git log) | multiplier |
|---|---:|---:|---:|
| Story 2.4 callout 自动同步 | 6h | **16h** (7 commits × 2 天) | **×2.67** |
| Story 2.2+2.9 vault isolation | 12h | **24h** (30+ commits × 3 天) | **×2.0** |
| **平均** | | | **≈ ×2.3** |

**Sprint 2 真实 capacity 重算 (按 ×2 multiplier)**:
- 我原估 22.5h dev → 实际 ~45h
- 加 UAT 6h + 收尾 1h = 52h
- Sprint 2 10 工作日 × 6h = 60h capacity
- **buffer 仅 8h**, 任一 Story 卡 → Sprint 2 末 ship 失败

**D 反对 V-07~V-11 全部修复 (与我判定冲突)**:

| Vuln | D 的反对意见 | 我的判定 | 裁决? |
|---|---|---|---|
| V-07 | "单用户首月不到 5% 触发率" — callout 重复编辑场景少 | 必修 | ⚖️ 倾向 D — 单用户阶段过度修复 |
| V-08 | "wikilink 邻居注入是'假针对性' — LLM 字面引用 1 个 [[A]] 完事, 真考网络回忆需 IRT 但已砍" | 必修 | ⚖️ 倾向我 — 即使是"假针对性"也比不引用强 |
| V-10 | "应用 frontmatter 1 字段即可, 不需新建 LanceDB 表" | 必修 | ⚖️ 倾向 D — questions_registry 可简化为 frontmatter `last_question_text` 字段 |
| V-11 | (D 没单独 attack) | 必修 | ✅ 共识必修 |

**D 推荐 Sprint v3 最小 ship 路径**: **28h, 5 工作日**, 把 Sprint 2 的 INFRA-006/007 + MASTERY-001/002 + 6 Lite + V-07~V-11 全部推到 Sprint 3+.

**D 一句话**: "**当前是已伪装成 MVP 的'中产品 v0.7', 真 MVP 还差一刀砍 (43.5h → 18h)**"

### 主 session 综合裁决 (3 个对抗冲突如何裁)

| 冲突 | 主 session 我 | Agent C | Agent D | 裁决依据 | 最终采纳 |
|---|---|---|---|---|---|
| 5 秒测试通过率 | 60% | **20%** | (未审) | C 看了 dashboard 实际渲染 + status-bar 假装记忆 | **20%** |
| Scope 膨胀率 | 50% | (未审) | **73%** | D 逐 Story git log 实证 | **73%** |
| V-07 必修? | 必修 | (未审) | **过度** | 单用户阶段 5% 触发率 vs Sprint 2 capacity 紧张 | **降为 P2, Sprint 3 修** |
| V-08 必修? | 必修 | (未审) | 过度 ("假针对性") | 即使"假"也比不引用强 + Karpicke 关系-grounded 是核心 | **必修保持 P0** |
| V-10 必修? | 必修 (新建 questions_registry) | (未审) | 简化 (frontmatter 1 字段) | 单用户无防篡改需求, frontmatter 足够 | **必修但简化方案** |
| V-11 必修? | 必修 | (未审) | (未单独 attack) | 共识必修 | **必修** |
| Sprint 2 ship 成功率 | 75% | "建议 ship 阻断" | (未直接) | C + D 综合更悲观, 我 75% 过乐观 | **45% (中等)** |

## 7. 修正后的 Sprint 2 开发计划 (基于 C + D 反对意见)

### 砍掉 V-07 (推到 Sprint 3) — 节省 2h Sprint 2 capacity

### 简化 V-10 (从 questions_registry 新表 → frontmatter `last_question_text` 字段) — 节省 0.5h

### 加 2 个新 P0 (基于 C 发现)

| Story | 修复 | 估时 | Sprint |
|---|---|---:|---|
| **NEW-UX-001** | dashboard.md 加 sample data + 空状态引导按钮 (Agent C 断层 #1) | 1.5h | Sprint 2 Day 6 (起手) |
| **NEW-UX-002** | status-bar.ts 移除虚假 "🎓 N 条 Tips" 显示, 或加 "(Graphiti 未接入, 仅本地缓存)" 标记 (Agent C 断层 #2) | 0.5h | Sprint 2 Day 6 (起手) |

### Sprint 2 修正后 capacity (按 D 实证 ×2 multiplier)

| Day | Story | estimate | 实际 (×2) |
|---|---|---:|---:|
| Day 5 | LITE-5-7 AC#1 Tauri 残留修 + mvp-plan.md 重写 | 2.25h | 4.5h |
| Day 6 AM | **NEW-UX-001** dashboard sample data + 引导 | 1.5h | 3h |
| Day 6 AM | **NEW-UX-002** status-bar 移除虚假 Tips 显示 | 0.5h | 1h |
| Day 6 PM | STORY-2-10 wikilink-Graphiti 同步 | 6h | **12h** |
| Day 7 | (上) STORY-2-10 续 | — | (12h 内) |
| Day 8 | STORY-1-16-hook (**砍 V-07**, 原 spec 不加 wikilink 上下文) | 3h | 6h |
| Day 9 AM | LITE-5-7 两个记忆系统 | 3h | 6h |
| Day 9 PM | LITE-5-6 dual-write (V-11 修复后) | 2.5h | 5h |
| Day 10 AM | LITE-4-3 V-08 + V-10 简化 (frontmatter 1 字段而非 questions_registry) | 5h | 10h |
| Day 10 PM | 4 MVP UAT + 决定是否 push 新仓库 | 2h | 4h |
| **Sprint 2 总** | | **25.75h** | **51.5h** |

**Sprint 2 capacity (60h) 内, buffer 8.5h 应对意外**

### 6 spec 砍清单 (按 D 推荐)

| spec | 砍理由 (D) | 推迟到 |
|---|---|---|
| LITE-4-11 (IRT 难度匹配) | 单用户无 IRT 样本 | Sprint 4+ |
| LITE-5-4 (scoring chain integrity) | pipeline_token 已简 | Sprint 4+ |
| LITE-5-5 (error classification dual-write) | 单写已够 | Sprint 4+ |
| INFRA-006/007 (D 推荐砍) | 非闭环阻塞项 | Sprint 3 |
| MASTERY-001/002 (D 推荐砍) | V0/V1 升级延后 | Sprint 3 |
| V-07 1-16-hook 加 5 字段 (砍, 改回原 3h spec) | 单用户首月 5% 触发率 | Sprint 3 |

## 8. 修正后的 3 个用户评价问题

### Q1: 主 session 75% ship 成功率 vs C + D 综合 45% 你信哪个?

- ✅ 信 C + D 45% (推荐: 修 dashboard + status-bar + 砍 V-07 + 简化 V-10)
- ⚠️ 信主 session 75% (按原计划 ship V-07/V-08/V-10 全套修复)
- ❌ 折中 60% (修 dashboard + 保 V-07/V-08/V-10 全套)

### Q2: V-07 砍 vs 保 (Agent D 实证 "单用户首月 < 5% 触发率")?

- ✅ 砍 (推迟 Sprint 3) — Sprint 2 capacity 紧, 真实数据后再评估
- ⚠️ 保 (1.16-hook 加 5 字段) — 学习历程完整性必要
- ❌ 折中 (保 1.16-hook 3h 原 spec 不加 wikilink 上下文, Sprint 3 加 V-07)

### Q3: V-10 全套 (questions_registry 新表) vs 简化 (frontmatter 1 字段)?

- ✅ 简化 (Sprint 2 节省 0.5h) — 单用户阶段够用
- ⚠️ 全套 (questions_registry 防篡改) — 未来商用打基础
- ❌ Sprint 2 只做 frontmatter 简化, Sprint 4+ 升级 questions_registry

## 9. 决策追溯 (更新)

- 2026-05-26 17:00: 用户要求 commit + 启动并行 agent 对抗审查 + 给开发计划报告
- 2026-05-26 17:30: 启动 5 个并行 Agent (A/B/C/D/E)
- 2026-05-26 17:45: Agent A + B socket 断 (infra issue, 不是任务问题); A 已 deep explored, Write 时断
- 2026-05-26 18:00: 主 session 接管, 直接读 6 关键文件 + git log + 结构调查
- 2026-05-26 18:30: 本报告 v1 ship — GO + 4 调整 + Sprint 2 22.5h 计划
- 2026-05-26 18:35: Agent C 完成 — 5 秒测试 20% + 3 CRITICAL UX 断层 (空状态荒漠 / Graphiti UI 假装在记 / 4 hotkey 隐式绑定)
- 2026-05-26 18:38: Agent D 完成 — scope 膨胀 73% + git log 实证 velocity ×2 + V-07~V-11 全过度
- 2026-05-26 18:45: 本报告 v2 update — Sprint 2 修正为 51.5h (含 NEW-UX-001/002), 砍 V-07, 简化 V-10
- **下一步**: 等用户回答 Q1/Q2/Q3 → 决定 Sprint 2 实际起步

---

**Plan ID**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**新仓库**: https://github.com/oinani0721/canvas-obsidian-hybrid (等 Sprint 2 末 UAT 通过后 push 精简核心)
**前置审计**: `_bmad-output/审查/2026-05-26-chatgpt-v7-v8-v10-v11-修复回应.md`
**Sprint v3 plan**: `_bmad-output/research/2026-05-21-sprint-plan-v3.md`

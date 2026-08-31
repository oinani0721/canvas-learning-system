# CARD-DEBT-16 验收单 — 五轮审查包轻量收官（Codex 终裁台账）

> **批次**: BATCH-2026-08-31-第七批 · **车道**: V7 (`card-v7-debt`)
> **基线**: `9cf0fb85` · **性质**: 纯审查 + 文档产出，零代码改动
> **产出**:
> - `_bmad-output/审查/codex-review-CARD-DEBT-16-P1残项单轮终裁.md`（终裁原文逐字存档 + 送审提示词全文）
> - `_bmad-output/审查/2026-08-31-DEBT-16-P1残项CLOSED-STILL-OPEN台账.md`（台账本体）
> - `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md`（回填，append 未重排）

---

## 一、完成条件逐条对照

### (a) 终裁存档 + 七项逐项裁定 + owner 映射

| 要求 | 状态 | 证据 |
| --- | --- | --- |
| 第 0 分钟异步送审，往返被 DEBT-13 作业吸收 | ✅ | 送审在本 session 第 3 个工具轮次发出（后台），随后全程在做 DEBT-13；终裁返回时 DEBT-13 台账、复跑证据、变异测试已全部完成 |
| 终裁记录**全文**存档 | ✅ | `codex-review-CARD-DEBT-16-P1残项单轮终裁.md`，含终裁原文逐字 + 送审提示词全文 + 模型/参数/基线/沙箱声明 |
| 七残项逐项 CLOSED/STILL-OPEN + 证据链接 | ✅ | 台账 §一 汇总表 + §二 逐项展开，每项带 `文件:行号` 或 commit |
| STILL-OPEN 项 100% owner 映射 | ✅ | 6/6。3 张现成卡（G4-8、G4-2、G4-3）+ 3 项显式登记的补卡需求（DEBT-17、DEBT-18、INFRA-DEBT-01） |
| TOCTOU 归属裁定 | ✅ | 裁为**独立 infra-debt 补卡 `INFRA-DEBT-01`**，不归 G4-8——理由写在台账 §二.5：G4 族六张卡的范围（读作用域/四态/VaultScope/outbox/payload 准入/DLQ）没有一张覆盖文件系统准入原子性，而该窗口跨 5 个读取面 |
| 提示词点名近期修复的可能覆盖 | ✅ | 提示词 §「送审后发生的事」列出 6 条并明令「你必须实查确认，不要采信我的转述」；Codex 据此独立核了 G4-2 的实际覆盖面并判部分闭合 |

### (b) 回填 G8-9 底账（只引用不重定义）

| 要求 | 状态 | 证据 |
| --- | --- | --- |
| 回填对应维度 | ✅ | §2.3 故障诚实 →「服务层（Memory/RAG）四态贯穿」行（G8-9 §4 明文指定的落点） |
| 只引用不重定义 | ✅ | 未新增维度、未改 `source_criterion`、未改判定纪律 |
| append 更新不重排 | ✅ | 只在既有行内追加 evidence/note、升 coverage、补 owners；§5 追加一段；**行序未动** |
| outcome 处理 | ✅ | **维持 `not_yet`**——按 G8-9 §1「存在未闭合反例时 fail-closed」，不因 coverage 升级就改判 |
| 三处一致 | ✅ | §2.3 表行 / §3 YAML 同行 / §5 残余登记，三处口径相同 |

### (c) 此后 P1 残项「CLOSED」宣称可指认

| 要求 | 状态 | 证据 |
| --- | --- | --- |
| 效力条款写进台账 | ✅ | 台账头部「⛔ 本台账的效力」：未记 CLOSED 的项，任何文档里的「已闭合/已解决/已收官」一律视为未经复核的自宣；升级路径必须回本台账改行，不允许别处另起口径 |

---

## 二、裁定结果

**1 项 CLOSED / 6 项 STILL-OPEN**

| ID | 裁定 | owner |
| --- | --- | --- |
| P1-01 快照 generation 不迁移 | 🟢 **CLOSED** | — |
| P1-05 vault 准入边界 | 🔴 STILL-OPEN（部分闭合） | DEBT-17（补卡） |
| P1-08 锚点文档失实 | 🔴 STILL-OPEN | DEBT-18（补卡） |
| B4 payload 准入与快照完整性 | 🔴 STILL-OPEN | G4-8（裁定拆 A/B） |
| TOCTOU 判定与 open 非原子 | 🔴 STILL-OPEN | INFRA-DEBT-01（补卡） |
| P1-03 服务层四态贯穿 | 🔴 STILL-OPEN（部分闭合） | G4-2 重开 / G4-2R |
| P1-04 API/trace/UI 四态 | 🔴 STILL-OPEN | G4-3（范围准确，无需拆） |

**最小收官清单（针对 P1-05/P1-01/P1-08 三判词）**：DEBT-17 + DEBT-18 两张卡，封闭可枚举。P1-01 无追加动作。

---

## 三、我方独立复核（不照单全收）

送审的同时并行做了独立取证，收到终裁后逐条比对。**Codex 的关键判词我全部自己复核过代码，未发现夸大或误判**：

| 判词 | 我方复核 | 结论 |
| --- | --- | --- |
| P1-05：`if not md_files: return 0` 早于指纹 diff 与删除清理 | 实读 `lancedb_client.py:1663-1666`（提前返回）vs `:1680`（`_get_changed_files`）vs `:1697-1701`（删除循环）——顺序确如所述 | ✅ 属实 |
| P1-05：direct 入口在生产被使用 | 实读 `endpoints/metadata.py:590` 直调 `lancedb_client.index_vault_notes(...)`，不经 orchestrator | ✅ 属实 |
| P1-01 CLOSED：跳写条件已与 generation 解耦 | 实读 `board_manifest_service.py:958-985`，四条件 AND（same_generation + `type(prev_version) is int` + `== SNAPSHOT_SCHEMA_VERSION` + `_snapshot_passes_v3_validation`），否则强制重写并落自愈日志 | ✅ 属实 |
| P1-08：`CURRENT_TASK.md:7` 落盘 `517 passed` | **我方在收到终裁前已独立抓到同一行**（见下） | ✅ 双向印证 |
| P1-08：`:11` 把已完成的合并写成未来动作 | 实读 `:11` 写「本合并（s6-recap）+ t2-closeout 后…」，而 `git log` 显示 `270c1716`(s6-recap) 与 `9cf0fb85`(t2-closeout) 都已在 HEAD | ✅ 属实 |
| P1-03：生产兼容入口剥状态 | 实读 `memory_service.py:1091-1106`——`get_review_suggestions` 委托后 `return result.items`，docstring 自陈「空 list 无法区分『没有待复习概念』与『Neo4j 挂了』」 | ✅ 属实（但**是 G4-2 显式声明的兼容取舍，不是疏漏**——台账已如实标注） |
| P1-03：history 固定判 degraded 与统一折算不一致 | 实读 `memory_service.py:795-805`（`if retrieval_failure: DEGRADED`）vs `service_status.py:172-192`（有失败+无结果+无健康源 → `unavailable`） | ✅ 属实 |

**我方独立发现（与 Codex 各自到达同一处，可互为印证）**：送审后我在等待期自查 `CURRENT_TASK.md`，
发现纪律写在 `:16`（「②不落盘 CI run 号/通过数」），而 `:7`——**恢复锚点前 15 行内、由第六批收官写入**——
落了 `517 passed`。终裁返回后确认 Codex 独立落到同一行并追加了 `:11` 的过期动作陈述。
两条独立路径同点命中，这条 STILL-OPEN 不是单方转述。

**我方补充的防混淆登记**（终裁未展开、但会误导后来人的两处）：

1. **B4 的 provenance ≠ 仓内已有的 provenance**：`error_writer.py:83,98` 与 `candidate_callout.py:72` 的
   `provenance` 是 `seeded|distilled` 的**测试种子角标**（2026-07-20 裁决），与 B4 要的「episode payload
   来源证明」不同域，不得拿来充数。
2. **P1-04 的 `degraded_reason` ≠ 统一四态透出**：仓内有一批 D3 血统的分散加性 `degraded_reason`
   （chat / exam_sessions / review / schemas / review_models / board_manifest），加上 MCP `source_status`
   三态与 memory health 三态，是**三套不齐的词汇**；不得据此宣称 P1-04 已闭合。

---

## 四、本轮的 UNVERIFIABLE（如实登记）

| 项 | 原因 | 需要什么 |
| --- | --- | --- |
| 真实存量 Neo4j episode / 快照的不合规数量 | 本轮只读沙箱只用合成临时 vault 与 LanceDB，未连生产 7691 | 获用户批准的只读生产 census |
| TOCTOU 交错后对图写入的实际影响 | 同上（Lance 持久化反例已足以判开，图侧未验） | 同上 |

两条均**不影响**本轮任何代码路径裁定。

---

## 五、⛔ 待用户裁决（3 项）

| # | 事项 | 建议 |
| --- | --- | --- |
| 1 | **3 张补卡是否落进总账 v2**（`DEBT-17` 3h/wave1、`DEBT-18` 2h/wave1、`INFRA-DEBT-01` 10h/wave1 建议拆 01A+01B） | 建议落账。按 G8-9 §1「owner 只引用未完成的正式卡」，不落账它们就进不了底账 owners，P1-05/P1-08/TOCTOU 的 owner 链在底账层面仍是断的 |
| 2 | **G4-8 拆 A/B** — G4-8A（payload 准入，5–7h，wave 3，deps G4-5+DEBT-11）/ G4-8B（快照来源完整性，6–8h，wave 2，不受 G4-5+DEBT-11 阻塞） | 建议拆。G4-8B 与 Graphiti episode 契约无依赖，捆在 wave 3 会被无关前置拖住 |
| 3 | **G4-2 重开 vs 新建 G4-2R** — 已收官卡能否重开是流程问题，不是技术问题 | 若流程不允许重开，建 `G4-2R`，owner 链仍记在 G4-2 名下（本台账与 G8-9 回填已按此写） |

> 这三项都**不阻塞本卡验收**——台账本身已把裁定与 owner 映射写死并可指认；落账是主 session 排卡动作。

---

## 六、硬边界遵守情况

| 边界 | 遵守 |
| --- | --- |
| 全程只读（除新脚本/台账/文档） | ✅ 零代码改动；Codex 走 `--sandbox read-only` |
| live vault 与 Neo4j 7691 只读 | ✅ Codex 声明只用合成临时 vault/LanceDB，未连生产库；我方复核全部是 `sed`/`grep` 读取 |
| G8-9 底账按 append 更新不重排 | ✅ 见 §一(b) |
| 不落盘 CI run 号与通过数 | ✅ 本卡产出中的测试计数均带 commit/文件锚点、标为时点证据（这正是 P1-08 纪律本身的要求） |
| 不 push | ✅ |

---

## 七、复核入口（验收者自行核对）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt

# 终裁原文（含送审提示词）
sed -n '1,40p' "_bmad-output/审查/codex-review-CARD-DEBT-16-P1残项单轮终裁.md"

# 台账七项裁定表
sed -n '/^## 一、七项裁定表/,/^## 二、/p' "_bmad-output/审查/2026-08-31-DEBT-16-P1残项CLOSED-STILL-OPEN台账.md"

# G8-9 回填行（确认 outcome 仍是 not_yet、行序未变）
grep -n "服务层四态贯穿\|服务层（Memory/RAG）四态贯穿" "_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md"

# 抽验两条最有代价的判词
sed -n '1660,1705p' backend/lib/agentic_rag/clients/lancedb_client.py   # P1-05 空集提前返回
sed -n '955,990p' backend/app/services/board_manifest_service.py        # P1-01 跳写四条件
```

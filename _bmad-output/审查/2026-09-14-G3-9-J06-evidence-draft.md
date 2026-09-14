# J06 证据底稿（G3 层）— 不可变事件 / 幂等 / 乱序安全

> 来源卡：CARD-G3-9 [BATCH-2026-09-11-第十四批 / 车道 T4-A]，绑定 SHA = **`72b1cabd` 的代码树**（基线 `08100483`；含 Codex r1–r3 共 31 条修复；r4 那批修复因引入回归已整轮退回，见验收单 §5.1）
> ⛔ **这是底稿，不是 J06 验收**。J06（出题与 FSRS 旅程验收）的完整 E2E 属 Phase 4 RC 阶段。
> 本文件只登记 **G3 层**已产出的、可被机器复跑的那部分证据，并**逐条点名尚未证明的部分**。
> 任何下游引用本文件时，不得把 §2 的内容当成 §3 的结论。

---

## 0 J06 的硬断言（原文口径）

总账 `2026-08-28-主goal全量分goal总账-v2.md:868`：

> 旅程脚本在 clean RC 上无 skip/mock 跑通；**重复/乱序/并发用例断言唯一调度状态且 event 账
> append-only（改写检测 FAIL）**；J06/manifest.json 过 R-EVD 校验并归档。

拆成三个可分别取证的命题：

| 编号 | 命题 | 本卡贡献 |
|---|---|---|
| J06-a | 事件账 append-only（改写可被检出） | **无**（本卡不读也不写事件账） |
| J06-b | 重复 / 乱序 / 并发后**唯一**调度状态 | **部分**：给出读侧「唯一状态」的机器判据（见 §2） |
| J06-c | 旅程脚本在 clean RC 上无 skip/mock 跑通 | **无**（本卡不跑 E2E） |

---

## 1 本卡产出的可复跑件

| 件 | 路径 | 作用 |
|---|---|---|
| 三面对账脚本 | `backend/scripts/g39_three_view_reconcile.py` | 只读；对同一份投影跑三面逐项对账，`rc=0` ⟺ 无 `semantic_diff` |
| 对账测试 | `backend/tests/regression/test_g39_three_view_reconcile.py` | **57 用例**：绿例 + 负控三段 + 验伪锚两例 + 镜像保真加固 + Codex r1–r3 共 31 条的回归钉 |
| 变异对照件 | `_bmad-output/审查/evidence-g39/g39_mutation_negctl.py` | 逐条抽掉判据，要求**被点名的那条测试**变红 |

跑法（只读，不连库，不起后端）：

```
backend/.venv/bin/python backend/scripts/g39_three_view_reconcile.py \
  --vaults-root "$VAULTS_ROOT" [--overview-url http://127.0.0.1:<port>] --out <报告路径>
```

---

## 2 本卡**已证**的（G3 层，可引用）

### 2.1 读侧「唯一调度状态」的机器判据 — 对 J06-b 的部分贡献

同一份 `<vault>/outputs/今日复习.json` 有三个消费面（picker 原始投影 / Dashboard 的
DataviewJS 归约 / 总览页 `GET /api/v1/review/overview`）。本卡把它们的**到期卡片数、板集、
板级到期数、板序、板内节点身份与行序**做成逐项机器对账；`semantic_diff` 非空即 `rc=1`。

意义（严格表述）：这是「唯一调度状态」在**读侧/显示层**的一条**必要条件**——三个界面若对同一
数据集给出不同数字，唯一状态一定不成立。⛔ 反过来不成立：三面一致**不能**推出调度状态本身正确。

**live 实测（2026-09-14，只读跑一次）**

| 项 | 值 |
|---|---|
| 报告 | `_bmad-output/审查/evidence-g39/reconcile-live-v2-20260914T201845.json` |
| 终端存档 | `_bmad-output/审查/evidence-g39/gates-final-20260914T201845.txt` |
| `canvas-vault` | `semantic_diff` = 0（已对账面：picker + dashboard） |
| `test-vault` | `semantic_diff` = 0（已对账面：picker + dashboard） |
| overview 面 | **缺席**——后端未在运行，本卡硬边界禁止启动后端 |

⛔ 因此 live 这一次是**两面**对账，`rc=0` **不代表总览页已验**。脚本自身会在终端与报告里
点名这一点（`compared_views` 字段 + `vaults_without_overview` 列表），防止 `rc=0` 被读成三面已验。
三面 live 对账须等 mini-UAT 陪跑窗口（用户为 Web UI 起后端时）补做。

### 2.2 判据有牙齿（不是空转）

变异对照实测 **27/27**：抽掉任一判据，**被点名的那条测试**即红；脚本还原后 shasum 与跑前逐字节相同
（`5ce5eea6…affa` → `5ce5eea6…affa`）。其中 M7–M28 是把 Codex r1–r3 指出的 31 条**修复各自改回缺陷形态**——
证明修复本身也有牙齿，不只是「代码改了一下」。

| 变异 | 抽掉的判据 | 被点名的测试 | 结果 |
|---|---|---|---|
| M1 | overview 板级 due 对账 | `test_negctl_overview_board_due_plus_one` | KILLED |
| M2 | 板序对账 | `test_negctl_picker_top_boards_order_swapped` | KILLED |
| M3 | stats 与明细长度对账 | `test_negctl_stats_due_nodes_mismatch` | KILLED |
| M4 | corrupt 计入差异（改成豁免） | `test_falsify_anchor_overview_corrupt_counts_as_semantic_diff` | KILLED |
| M5 | 行序对账（退化成集合比较） | `test_node_order_mirrors_urgency_not_scan_order` | KILLED |
| M6 | JS number 判定（改用 isinstance） | `test_dashboard_bool_is_not_a_js_number` | KILLED |
| M7 | 板序退回子序列比较（r1 HIGH-2 缺陷形态） | `test_r1_high2_board_order_is_prefix_not_subsequence` | KILLED |
| M8 | 板集退回只比到期板（r1 HIGH-1 缺陷形态） | `test_r1_high1_zero_due_board_missing_from_overview_is_a_diff` | KILLED |
| M9 | picker 解析退回宽松（r1 HIGH-3 缺陷形态） | `test_r1_high3_nan_is_rejected_like_js_json_parse` | KILLED |
| M10 | 已连接后的读取失败退回豁免（r1 HIGH-4） | `test_r1_high4_read_failure_after_connect_is_not_exempted` | KILLED |
| M11 | boards 损坏退回当成旧投影（r1 MEDIUM-5） | `test_r1_medium5_corrupt_boards_key_is_a_diff_not_scope_note` | KILLED |
| M12 | 重复 vault_id 退回取首条（r1 LOW-9） | `test_r1_low9_duplicate_vault_entries_is_a_diff` | KILLED |
| M13 | 去掉代理旁路（本卡自查出的缺陷形态） | `test_fetch_overview_opener_bypasses_system_proxy` | KILLED |

存档：`_bmad-output/审查/evidence-g39/mutation-negctl-v3-20260914T201517.txt`；工具 `evidence-g39/g39_mutation_negctl.py`（已入库）

### 2.3 反假绿的两条边界（对 J06 的直接可复用价值）

- **结构降级不得伪装成一致**：投影结构校验不过时，Dashboard 面记 `not-comparable` 并**计入**
  `semantic_diff`，⛔ 不记 0。记 0 会把「投影损坏」显示成「三面一致的 0 到期」。
- **连上但 corrupt 不得当成取不到**：`not-fetched` 豁免**只**给连接层失败。总览页网关
  (`_gate_boards_rollup`) 判 corrupt 的原因恰恰是它内部抓到了「rollup ≢ group-by 派生」，
  跳过它等于把网关抓到的不一致读成「对账通过」。验伪锚 ② 钉死这一条。

### 2.4 三源独立性的如实分级（后人勿把恒真当验证）

`review_overview.py:283` 的 `_gate_boards_rollup` 在网关**内部**已断言「rollup 的到期板集合 + 计数
≡ due_nodes group-by 派生」，不等即 raise → entry 变 corrupt。⇒ **overview 成功返回 entry 时，
该子项在 overview 侧恒真**。真正能翻转它的只有 picker 自身的两源。

脚本因此给每条判据带 `independence` 三档字段（`cross-source` / `reimplementation` / `structurally-guaranteed`；
中间那档是 Codex r1 MEDIUM-6 促成的——overview 的 group-by 与本脚本是**同一契约的两个实现**，
能抓实现漂移但不是第三个独立源，原先误标成 cross-source），并把
picker 侧 rollup ↔ group-by 的对账**直接在 picker JSON 上算**，不假手 overview——否则 overview
一 corrupt，这一条就没人算了。

---

## 3 本卡**未证明**的（引用者必读）

| # | 未证明 | 归属 |
|---|---|---|
| 1 | **J06-a 事件账 append-only 完全未触及**——本卡不读 `canvas-vault/learning_events.jsonl`，改写检测无任何证据 | Phase 4 RC / 另立卡 |
| 2 | **重复 / 乱序 / 并发**三类操作后的状态唯一性——本卡只对**静态一份**投影做对账，没有做任何写操作或时序编排 | J06 E2E |
| 3 | 总览页网关本体（`_gate_due_groups` / `_collect`）逻辑正确——本卡只对账其输出与 picker 一致 | 移交 T3 |
| 4 | 完整 E2E（无 skip / 无 mock 在 clean RC 上跑通） | Phase 4 RC |
| 5 | live 对账只跑了**一次当日数据集**，未覆盖多日 / 空 vault / 损坏投影的组合 | 后续 |
| 6 | Dashboard 面是 **Python 镜像**，未在真实 Obsidian DataviewJS 运行期比对；mini-UAT 的用户肉眼一致是唯一 runtime 旁证 | mini-UAT |
| 7 | `not-fetched` 分支只做了静态边界核，**没有真起停后端做对照** | 后续 |
| 8 | G3-5 甲支本体（service 侧按 vault 分桶）在 live 数据上的正确性——本卡只**消费**甲支键 | G3-5 / R-B14-12 |
| 9 | **Dashboard 面的降级判定尚不完备**：`_js_interp_throws` 不模拟 JS 自身的**栈溢出**（Node 约 3000 层嵌套抛 `RangeError`）⇒ 深嵌套输入上脚本给数字而界面不出数字（Codex r5 HIGH，本 session 已复现） | 待主 session 裁定 |
| 10 | **r4 的 8 条 MEDIUM 随退回回到未修状态**：深嵌套触发 `RecursionError` 打断报告 / `0.0↔0` 假红 / 畸形 URL 的 `ValueError` 逃逸 / 四条损坏输入漏检 / 计数宽松相等。**有意识的取舍**——r5 那条 HIGH 是**不可见的假绿**，比崩溃与漏检更致命 | 移交：另立卡 |
| 11 | **JS 运行时镜像的完整性未证明**：栈溢出、数字渲染、解析器严格度三类「被镜像方的失败模式」目前只覆盖了解析器严格度一条 | 移交：另立卡 |

---

## 4 建议 J06 E2E 阶段如何复用本卡

对账脚本可直接当 J06 旅程的**读侧收口探针**：在「重复提交 / 乱序到达 / 并发评分」每一类用例
跑完之后，对受影响 vault 跑一次

```
g39_three_view_reconcile.py --vaults-root <RC vault 根> --overview-url <RC 后端> --out <该用例的证据路径>
```

并要求 `rc=0`。它**不能**替代 J06-a（事件账 append-only）与写侧幂等断言——那两条需要各自的判据。

---

## 5 mini-UAT 勾选记录

验收单：`_bmad-output/验收单/UAT-CARD-G3-9-2026-09-14.md`

> Codex 复核收口于 **round-4**（BLOCKER 0 / HIGH 0，绑最终 HEAD 的代码树）。
> round-5 曾新增 1 条 HIGH（车道自引入的回归），已**整轮退回**，详见
> `_bmad-output/验收单/UAT-CARD-G3-9-2026-09-14.md` §5.1。
> ⚠️ 退回的代价（r4 那 8 条 MEDIUM 回到未修状态）已登记在 §3 未证明清单第 9/10 条之后。
>
> 状态：**待用户勾选**（本卡完成时用户未到场）。勾选结果回填本节后，本底稿的 §2.1 才可补上
> 「用户肉眼三处一致」这条 runtime 旁证；在此之前该旁证**空缺**，不得预先声称。

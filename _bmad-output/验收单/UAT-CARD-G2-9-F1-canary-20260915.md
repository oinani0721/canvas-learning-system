# CARD-G2-9-F1-canary 验收单（给你看的版本）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-G2-9-F1-canary]` · 车道 `card-t1-lance`（本车道第 2/2 张，收工卡）
> 分支 `card/t1-lance` · `$PREREQ` = `60600433`（T1-A / CARD-G2-9-F2 末 commit）
> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T1-B.md`
> **本卡零生产改动**：canary 脚本 sha 跑前 = 跑后，新增文件全部在 `_bmad-output/**` 下。

---

## 🎯 这个卡要做到什么

第十三批 U5-A（CARD-G2-9-F1）修好了「打开 A 资料库会删掉 B 资料库的表」这个数据丢失缺陷，但它当时**只做了静态检查**（读代码、数点数），**没有真的把整套跑一遍**。U5-A 自己把这件事写成移交项交给本卡。

本卡就干一件事：**真的跑**。三个存储（Neo4j 图库 + Graphiti 记忆 + LanceDB 向量库）端到端跑完整流程，并且把那个「连带删表探针」开关的**两种状态都跑一遍**，证明：

1. 开着探针时，B 资料库的表在 A 初始化之后**还在**（缺陷确实修好了）；
2. 关掉探针时，程序不会因为少了那个键而崩掉（`side_effect_probe` 是条件键，早期写法会 `KeyError`）。

**本卡不修任何代码。** 跑出问题就如实登记、停下交主 session 排卡。

---

## 📖 用户故事（你的视角）

> 我在这个系统里放了两门课的资料库。以前有个毛病：我打开 A 课，B 课的向量索引会被悄悄删掉——下次搜 B 课的内容，搜不到了，而且没有任何报错。
> 我要的是：**打开一门课，另一门课的东西一张都不能少。**

---

## 🖥️ 你会看到的交互（一步一步）

这张卡是**底层验证卡**，没有新界面。它验证的是你在日常使用中「**不该发生的事没有发生**」：

1. 你打开 A 课的资料库 → 系统初始化 A 的向量表
2. 这时系统会检查库里所有表的向量维度对不对
3. **修复前**：它会把 B 课的表也一起检查，发现维度不一样就删掉
4. **修复后**：它只检查属于 A 的表，B 课的表原封不动

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> 全部证据在 `_bmad-output/审查/evidence-g29f1-canary/`。承重裁判的 tee 末行都带 `rc=`。

### (a) 第 0 分钟自证

| 项 | 实测 | 证据 |
|---|---|---|
| pwd / 分支 | `…/worktrees/card-t1-lance` / `card/t1-lance` | `prereq-20260915T120845.txt` |
| `$PREREQ`（T1-A 末 commit） | `60600433` | 同上 |
| `git status --porcelain` | **非空** —— 见下方 §偏差登记 B-1 | 同上 |
| venv | `card-v5-lance/backend/.venv/bin/python`（symlink，Python 3.14.4） | `venv-env-selfcheck-20260915T120920.txt` |
| `backend/.env` | 存在，133 行 | 同上 |
| **`$SHA0`（canary 开工 sha）** | `5411cf14da00cabfec8e1f8ddd1f56c8ffeeda745b1eb147536d4927e200ee7a` | `canary-sha-start.txt` |
| `side_effect_probe` 字面量计数 | `5` | `probe-key-count-start.txt` |
| 红参照（历史，U5-A 修复前） | `B_table_survived_A_init = False`；`finding = CONFIRMED: vault A 的 LanceDBClient.initialize() 删掉了 vault B 的表` | `red-ref-20260915T120948.txt` |
| 本卡 evidence 目录跑前报告数 | **0**（验伪锚：同提取式对历史 `evidence-g29/` = 7） | `pre-run-zero-reports.txt` |

> `$SHA0` 与卡文记录的 B14_BASE 值**逐字节相同** ⇒ 前一卡 T1-A 未改动 canary 脚本。

### (b) 前置可用性

| 项 | 实测 | 证据 |
|---|---|---|
| 7692 测试容器 | `nc -z 127.0.0.1 7692` → **rc=0** | `precheck-7692.txt` |
| canary 是否依赖嵌入端 | `grep -ciE -e 'bge-m3' -e 'ollama' <canary>` → **0** | `no-embed-dep.txt` |
| ↑ 正对照（证这个 0 是真 0） | 同命令对 `backend/app/config.py` → **3** | 同上 |
| ↑ 验伪锚 | 常量向量三处命中 `:118` / `:613` / `:724` | 同上 |
| lazy import 清点 | **13** 条，全为 `graphiti_core` / `app.*` / `lib.agentic_rag`，**无任何 embedding 客户端** | 同上 |

> 故本卡**不设** bge-m3/Ollama 前置门。
>
> ⚠️ **但上面这条 grep 的搜索面只覆盖 canary 脚本自身，不覆盖它调用的 client。** 本卡实测发现 canary 运行时**确实会加载嵌入模型**（详见 §本卡实测更正 ①）：`LanceDBClient.initialize()` 里无条件调 `_init_vectorizer()` 预热，ON 态日志里 `Loading weights: 391/391` 出现 **4 次**。
>
> **⇒「不设前置门」这个做法，本卡只能作为「本次成功环境下的执行选择」保留，不是一个无条件成立的结论**（按 Codex r1 MEDIUM 收窄，初稿写的「结论仍然成立」过强）。理由链逐层收窄如下：
> 1. 「canary 不碰 embedding」——**不成立**（实测加载 4 次）；
> 2. 换成「预热失败被 `_init_vectorizer` 的 `except` 吞掉」——**只有代码结构依据，无运行时实证**：本次 4 次预加载**全部成功**（`Loading weights: 100%` 计数 4 = 总计数 4，失败告警 0），`except` 分支没被走到；且本卡的读取面只看到调用点与构造片段，**没有逐行核过完整的 `except` 实现**；
> 3. 因此本卡**不能**证「嵌入端挂掉时 canary 照样绿」。
> 见 `embed-dep-correction-ADDENDUM-*.txt` 与「本卡未证明什么」第 5、9 条。

### (c) 两态真跑（核心判据）✅

两次运行各用一个全新 `mktemp -d` 的 LanceDB 路径，`NEO4J_TEST_URI=bolt://localhost:7692`。
**两份报告各自从自己那次运行的 tee 里「报告:」行抓路径**（产出方自报的内容锚），不是靠文件排序位置猜配对。

| 态 | 命令 | rc | 报告 |
|---|---|---|---|
| **ON**（默认带探针） | 不带 `--no-probe-schema-drift` | **0** | `canary-report-20260915T101823Z.json` |
| **OFF** | `--no-probe-schema-drift` | **0** | `canary-report-20260915T102343Z.json` |

ON 态三条判据（`assert-on-*.txt` / `two-state-assert-*.txt`）：

| 判据 | 实测 |
|---|---|
| `side_effect_probe.verdict == "PASS"` | ✅ `PASS` |
| `B_table_survived_A_init == true` | ✅ `True` |
| `B_table ∈ tables_after_A_init` | ✅ `True` |
| `tables_before_A_init` | `['g29drift_b_canvas_nodes']` |
| `tables_after_A_init` | `['g29drift_b_canvas_nodes']` ← **一张没少** |
| `finding` | `NOT REPRODUCED（本次未观察到连带删表）` |
| `verdicts` 14 条 | 全 `True`（逐条见下） |

ON 态 14 条 `verdicts` 全名单（`on-report-detail-*.txt`）——判据名本身说明了隔离的覆盖面：

| 判据 | 值 | 管的是什么 |
|---|---|---|
| `A_cannot_see_B` / `B_cannot_see_A` | True / True | 读隔离：任一边都看不到对面 |
| `A_unaffected_by_B_write` | True | B 写入不影响 A |
| `B_unchanged_after_deleting_A` | True | **删掉 A 之后 B 一条没少**（本卡核心关切） |
| `A_gone_after_delete` | True | 删 A 是真删（不是没删成看起来像隔离） |
| `graphiti_delete_is_load_bearing` | True | Graphiti 侧的删除真的承重 |
| `lancedb_delete_is_load_bearing` | True | LanceDB 侧的删除真的承重 |
| `A_counts_positive` / `B_counts_positive` | True / True | 两边都**真写进去了**（防「空对空」的假绿） |
| `identities_distinct` | True | 两个 vault 身份互异 |
| `A_equals_B` | True | 对称性 |
| `shared_concept_split_per_group` | True | 同名概念按组分裂，不合并 |
| `read_scope_sentinels_clean` | True | 读作用域哨兵干净 |
| `purge_left_nothing` | True | 本轮 purge 之后、该判据所查的那组对象计数归零 |

> `A_counts_positive` / `B_counts_positive` 这两条尤其重要：它们排除了「两边都是空的，所以当然互相看不见」这种退化的假绿。
>
> ⚠️ **`purge_left_nothing` 的含义已按 Codex r1 MEDIUM 收窄**：初稿把它解读成「跑完清理干净 / 没在共享 7692 留脏数据」——**过宽**。验伪报告里对应的变异 `M11_purge_leaves_residue` 把这条判据明确描述为**起点前提**（「计数是本轮写的，不是上轮遗留」），两态报告给出的也是**特定对象、特定阶段**的计数，**不是对共享容器的最终对账**。本卡既没做跑后全库快照，也没列举 canary vault 之外的残留面 ⇒ 既不能据此说留了脏数据，也**不能据此说没有残留**（已列入「本卡未证明什么」第 12 条）。

`identities` 实测（**报告记录的** A/B 身份如下）：
`A → vault__g29canary_a` / `g29canary_a_canvas_nodes`；`B → vault__g29canary_b` / `g29canary_b_canvas_nodes`（物理 group_id 为双下划线格式，符合 R5）。

> ⛔ **措辞已收窄（Codex r2 MEDIUM，新发现）**：初稿写「证实只动了本卡自己的 vault」——**过强**。`identities` 只说明**报告记录的目标身份**，单凭它**不能**证明执行期间没有触及其他对象（那是一个排他性结论，需要独立的越界观测）。
> **另有一条独立的旁证**（不是靠 `identities`）：本卡跑完后对 7692 做了只读残留对账（`residue-recon-7692-*.txt`）——按 `vault__g29canary` / `vault__g29drift` 前缀查，节点与关系**各 0 行**；同次验伪锚显示全库 114 个节点、84 个带 `group_id`、13 个其他 `group_id`（`test` / `vault__canvas_vault__*` / `数学` / `物理` 等），证明该查询不是恒空、连接是活的。
> ⚠️ 这条旁证的覆盖面也要说清：它只覆盖 **Neo4j 图侧、按 group_id 前缀可见的、跑后时点**的对象；不覆盖执行过程中的瞬时行为，也不覆盖 LanceDB 侧（本卡全程写 `mktemp` 临时目录）。所以它能支持「**跑后图侧无本卡残留**」，仍**不能**支持「执行期间未触及其他对象」。

OFF 态：

| 判据 | 实测 |
|---|---|
| 报告**无** `side_effect_probe` 键 | ✅ 顶层键 = `['duration_s','evidence_dir','guard_summary','identities','lancedb_path','phases','timestamp','verdicts']` |
| rc 仍为 0（条件键 opt-out 不 KeyError） | ✅ `rc=0` |
| tee 中 `KeyError`/`Traceback` 计数 | **0** |

> ⚠️ **OFF 态「没有 `side_effect_probe` 键」的正确含义是「探针没跑」，不是「探针通过」。** 本卡不把它当作任何隔离结论的依据。

#### 📌 这次复跑真正的增量价值：它跑在 T1-A 大改之后

本卡**不是**在 B14_BASE 上复跑，而是在 T1-A（CARD-G2-9-F2）改完之后跑的。T1-A 的代码面实测（`git diff --stat 08100483 60600433 -- . ':(exclude)_bmad-output'`）：

| 文件 | 改动量 |
|---|---|
| `backend/lib/agentic_rag/clients/lancedb_client.py` | **+633** |
| `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` | **+1105** |

`lancedb_client.py` 正是当年那条「A 的 `initialize()` 删掉 B 的表」缺陷的所在文件，T1-A 在它上面动了 633 行（把归属判定改成最长前缀优先，经 7 轮 Codex 整改）。

⇒ **本卡 ON 态 probe 仍 `PASS`，等于一条回归证据：T1-A 这 633 行没有把 U5-A 修好的隔离面弄坏。** 这是「F2 之后复跑」这件事本身的价值，也是它与 U5-A 当初那次跑的区别。
⚠️ 但**反过来不成立**：canary 全绿**不能**为 T1-A 的前缀修复本身背书（见「本卡未证明什么」第 1 条——canary 的四个 vault id 都不是前缀重叠形状）。

端口门（`blocked-tokens.txt`）：两态 summary_line 均为
`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`
等值断言（非取尾行）通过；同次两条验伪锚证明这条 grep 与等值断言对 `blocked=7` 的假行会正确判红。

> ⚠️ `blocked=0` 只说明这次运行**没有连到受拦端口**，它**不是**「vault 之间隔离成立」的证据。隔离结论只来自上表的 probe 三条判据与 14 条 verdicts。

### (d) 验伪锚：`--verify-judges` ✅

真跑（`verify-judges-20260915T182632.txt`，`rc=0`，耗时约 40 分钟 —— 12 条变异各跑一次完整三存储 canary + 每条之后两次 purge）。
报告 `canary-verify-judges-20260915T102632Z.json`，路径从 tee 的「验伪报告:」行抓（产出方自报）。

| 卡文 (d) 要求 | 实测 |
|---|---|
| `rc` | **0** |
| `all_killed` | **True** |
| `coverage.complete` | **True** |
| `coverage.covered` / `total` | **14 / 14** |
| `coverage.uncovered` | `[]` |
| `coverage.phantom_targets` | `[]`（点名了不存在的判据会静默失效，此处为空） |

**⚠️ 不只信 `all_killed` 这个汇总字段——逐条交叉验证了明细**（`verify-judges-assert-*.txt`）：

| 交叉判据 | 实测 |
|---|---|
| `mutations` 条数 | **12**（M1–M12） |
| 每条 `verdict` | 全 `KILLED`（分布 `{'KILLED': 12}`） |
| 每条 `applied` | 全 `True`（分布 `{True: 12}`） |
| 明细结论与 `all_killed` 汇总是否一致 | **一致** |
| `baseline_verdicts`（未变异的干净基线） | 14 条**全 True** |

> `applied` 全为 True 这一条是关键：脚本自己会把「变异后报告与基线逐字相同」判成 `NOT_APPLIED`。若有 `NOT_APPLIED`，那条的「没红」就分不清是**门够硬**还是**变异压根没打进去**——本次 12 条全部确认打进去了。

12 条变异各自打击的面（tee 逐条）：`M1` vault 命名空间 / `M2` 读契约 R4·R1 / `M3` 写契约 W2 / `M4` 判据形状前提 / `M5` LanceDB 表名命名空间 / `M6`·`M7` 「写进去了」这个前提本身 / `M8` 两套读口径等价性 / `M9` 删除路径 / `M10` 写侧 vault 归属 W1 / `M11` 计数起点前提 / `M12` graphiti 删除路径。

**⚠️ 如实声明（范围收窄）**：`--verify-judges` **只覆盖** `report["verdicts"]` 的 14 条，**不覆盖** `side_effect_probe` 的 verdict。代码结构依据：`_run_canary_cli` 里 `--verify-judges` 分支是 **early return**，根本走不到 `run_canary` 之后写 `side_effect_probe` 的那一段。probe 判据的翻红能力只有 (a) 的历史红参照，本卡零生产改动不重建——见「本卡未证明什么」第 2 条。

该次运行 guard：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。

### (e) 前置负控两条 ✅

判据不是「rc=2」而已，而是**三重绑定**：① rc ② 横幅阶段是 `preflight` 不是 `runtime` ③ `NEGCTL_REJECTED_BY` 指向应当拒它的那一层。

| 负控 | rc | 阶段横幅 | `REJECTED_BY` | live 端口尝试 |
|---|---|---|---|---|
| ① 未设 `NEO4J_TEST_URI` | **2** | `CANARY REJECTED (preflight)` | `_preflight_neo4j_uri` | `ATTEMPTS=0` |
| ② `--lancedb-path <tmp>/data/lancedb` | **2** | `CANARY REJECTED (preflight)` | `_preflight_lancedb_path` | `ATTEMPTS=0` |

**⛔ 这里我又写过一句过强的话，当场更正**（`attempts-semantics-correction-*.txt`）：初稿把 `ATTEMPTS=0` 注释成「零 socket，根本没连库」——**错**。ledger 的 `blocked_ports = [7687, 7691]`，这个计数器**只盯现网端口**；ON 态真的连了 7692 并跑满 260 秒，它的 ledger **同样是 `total=0`**。所以：

- `ATTEMPTS=0` 能支撑的结论是「**没碰现网库 7691/7687**」——这仍是本卡硬边界的重要证据，但仅此而已。

**⛔ 再收一层（Codex r1 MEDIUM，已接受）：本卡不再声称「负控零 socket」。**
初稿的替代论证是「`_amain` 里 preflight 抛异常时 `_run_canary_cli` 未被调用 + 横幅写 `(preflight)`」。Codex 指出：**`preflight` 是程序的阶段标签，不是网络活动记录**；而且负控②在被拒之前已经走过 `_preflight_neo4j_uri` 里的 `live_port_guard.assert_test_uri_not_blocked()`。因此收窄为：

| 能证 | 不能证 |
|---|---|
| 两条负控**按预期的那一层、在进入 canary runtime 主流程之前**被拒（建立数据库连接的是 `_run_canary_cli` 里的 `VaultScope.open()`，它没被调用；⚠️ 本卡未穷举全进程的建连点，故不写「唯一」） | 「整个进程没有打开任何 socket、没有连接任何库」——本卡没有进程级网络抓包，也未覆盖解释器启动、依赖导入、拒绝处理路径上的全部行为 |

补充的**代码结构依据**（`negctl-preflight-no-connect-evidence-*.txt`，明确标注不是运行时网络证据）：在该 evidence 所截取的 `assert_test_uri_not_blocked` 片段内，对 `socket|connect|GraphDatabase|driver|session|verify_connectivity` 的命中数为 **0**（验伪锚：同一提取式对该文件全文命中 **69**）。
⛔ **这条证据的三重局限（Codex r2 MEDIUM，如实登记）**：① 该 evidence 标题写「函数全文」，实际用 `sed +45p` **截断**了、未覆盖函数尾部；② 提取式与匹配位置未随结果一并落盘，读者无法独立复核覆盖面；③ **即使片段完整，关键字搜索也证明不了它调用的 helper（如 `canonical_target_ports`）内部没有网络行为**。⇒ 故此处**不写**「它只做 X、Y、Z」这类全称描述，只陈述「在所截片段内未出现上述建连关键字」。
⇒ 已列入「本卡未证明什么」第 4 条。

- 负控②的 `NEO4J_TEST_URI` 是**设好的**（tee 里有 env 回显），所以第一道 preflight 放行；实测 `NEGCTL_REJECTED_BY` 为 `_preflight_lancedb_path`，即拒绝来自第二道——归因由实测字段给出，不靠推断。
- 负控②额外证据：**被拒的路径没有被建出来** —— 判据确实在 `mkdir` 之前。拒一条路径的同时把它建出来，等于 canary 自己在现网位置留痕。
  ⛔ **证据引用更正（Codex r1 LOW，已接受）**：初稿在 `negctl-summary-*.txt` 里写「见 tee 同次输出的 `test -e` 行」——**那条输出当时并没有落进 tee**（`negctl-forbidden-path-20260915T182702.txt` 全文仅 9 行、末行 `rc=2`，不含该检查）。引用一条不在证据里的检查，等于凭记忆背书。
  **已补跑并完整落档**：`negctl-forbidden-path-rerun-mkdir-check-*.txt`（20 行），含 **PRE: NOT EXISTS** → canary `rc=2` → **POST: NOT EXISTS** → 父目录 `ls` 为空（连 `data/` 都没建）→ 验伪锚（`test -e` 对确实存在的 `$T` 返回 EXISTS，证这条检查不是恒假）。
  ⚠️ 该文件末行 `rc=0` 是**外层包装组**的 rc；canary 自身的 `rc=2` 在组内由 `echo "canary rc=$?"` 打出。
- **对照组**（证这两条不是恒红的假门）：ON 态用合法 tmp 路径 + 已设 URI 走同一份 preflight，放行并跑到底 `rc=0`，拒绝横幅出现 **0** 次。
- 证据：`negctl-no-uri-*.txt` / `negctl-forbidden-path-*.txt` / `negctl-summary-*.txt`

### (f) 脚本 sha 跑前 = 跑后 ✅

| 项 | 开工 | 收工 | 判定 |
|---|---|---|---|
| `g29_dual_vault_canary.py` sha256 | `5411cf14da00…e200ee7a` | `5411cf14da00…e200ee7a` | ✅ **逐字节相同** |
| `grep -cF 'side_effect_probe'` | `5` | `5` | ✅ 不变 |

- 验伪锚：同一条 `shasum -a 256` 对 `lancedb_client.py` 给出完全不同的值（`0ff52a5e…`），证明它不是恒定输出。
- 另一重佐证（**时点 = commit `49db0305` 之前的那一刻**，Codex r1 LOW 要求标清）：彼时 `git diff --stat HEAD`（全树、不限路径）**输出为空**，即本卡对已跟踪文件零修改、全部产物都是新增文件。
  ⚠️ 此后本验收单本身按 Codex r1 意见被整改，所以**当前**工作树相对 HEAD 已有本文件的改动——这不影响 (g)（`_bmad-output` 外的差异仍为空），但那句话是历史快照、不是当前状态。
- 证据：`canary-sha-start.txt` / `canary-sha-end.txt` / `probe-key-count-start.txt` / `probe-key-count-end.txt` / `sha-end-and-turf-*.txt`

> `--verify-judges` 注入的 12 条变异全部作用在**内存里的 `_MUTATION` 全局变量**上，不落文件——这是 sha 在跑了 13 次完整 canary 之后仍然逐字节不变的原因。

### (g) 地盘核 ✅

`$PREREQ` = `60600433`（T1-A 末 commit）→ 本卡 commit `49db0305`。

| 判据 | 实测 |
|---|---|
| `git diff --stat --no-color 60600433 HEAD -- . ':(exclude)_bmad-output'` | **输出为空**，`rc=0` |
| **同次验伪锚**（不加排除） | `54 files changed, 5108 insertions(+)` —— 证命令跑得通、区间有内容 |
| 本卡 commit 文件数 | **54** |
| 其中在 `_bmad-output/` 下 | **54** |
| 其中在 `_bmad-output/` 之外 | **0** |

**硬边界文件逐个核**（每个都必须 0 次出现在本卡 diff 里）：

| 文件 | 出现次数 |
|---|---|
| `backend/scripts/g29_dual_vault_canary.py` | 0 ✅ |
| `backend/lib/agentic_rag/clients/lancedb_client.py` | 0 ✅ |
| `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` | 0 ✅ |
| `canvas-vault/.claude/scripts/fsrs_bridge.py` | 0 ✅ |
| `canvas-vault/.claude/scripts/decay_beta.py` | 0 ✅ |

> **验伪锚**：同一条命令对一个**确实在本卡 diff 里**的文件（本验收单自身）返回 **1** —— 证明上面那一圈 0 是真 0，不是命令恒空。

**⚠️ pathspec 写法实测**（`pathspec-selfcheck-*.txt`，复现协议点名的假绿陷阱）：

| 写法 | 结果 |
|---|---|
| `':(exclude)_bmad-output'`（协议要求） | rc=**0**，空输出 = 真的没差异 |
| `':!_bmad-output'`（坏写法） | `fatal: Unimplemented pathspec magic '_'`，rc=**128** ← 空输出是「没跑成」 |

本机 `git version 2.50.1 (Apple Git-155)`。

**另一重佐证**（时点 = commit `49db0305` 之前）：彼时 `git diff --stat HEAD` 全树输出为空。**当前**该命令会列出本验收单（按 Codex r1 整改后重新提交），(g) 的代码面结论不受影响。

### (h) tests/unit 目录级 diff ✅

跑法与批级基线**逐字一致**（R-B14-3：先 `cd backend`，`--ignore` 用相对路径 `tests/unit/test_deploy_vault_sh.py`）：

| | 开工快照 | 收工快照 |
|---|---|---|
| 文件 | `unit-start-20260915T121159.txt` | `unit-end-20260915T184953.txt` |
| 汇总行 | `35 failed, 5102 passed, 48 skipped, 17 xfailed, 231 warnings, 29 errors in 465.68s` | `35 failed, 5102 passed, 48 skipped, 17 xfailed, 231 warnings, 29 errors in 235.24s` |
| FAILED/ERROR nodeid 数 | **64** | **64** |

**nodeid 集合 `diff` → `rc=0`，完全相同**（0 新增 `>`，0 消失 `<`）。符合卡文「只许 `<`」的要求（本卡零代码改动，连 `<` 也不该有，实测确实没有）。

**⛔ 前置自检（本卡踩坑后新增的一道）**：先证 `unit-start-*.txt` 与 `unit-end-*.txt` **各只匹配 1 个文件**（实测 1/1）。不加这道，我自己新建的 `unit-start-vs-b14base-*.txt` 会让两侧取错文件、diff 空 = 假绿——详见 §本卡实测更正 ④。

**三条验伪锚**（空集对空集的 diff 也是空）：开工侧 64 > 0 ✓ / 收工侧 64 > 0 且与开工相等 ✓ / 批级基线同形行 64（已知正例，证提取式能命中同形行）✓

**附加对账（非本卡判据）**：车道开工红集与批级基线 `08100483` 的 nodeid **集合完全相同**（`diff rc=0`，两侧各 64）。这与卡文 (h) 的预期（「F2 去掉 6 条 xfail 锁 ⇒ 红集本就不同」）**不符**——原因是 xfail→XPASS 的翻转**不产生 FAILED/ERROR 行**，对 nodeid 口径的红集是不可见的。证据 `xcheck-redset-vs-b14base-*.txt` / `xfail-redset-invisibility-*.txt`。
⇒ **对主 session 的提醒**：不能用「红集变了没」来判断某卡是否解锁过 xfail。

---

## 👤 你来验（产品使用体验）

> 零技术词。你只需要照做，然后说说**看到什么、感觉怎样**。

### 第 0 步：First 5 seconds

**你做**：打开系统，看一眼你的两门课的资料库都还在不在。
**你该看到**：两门课都在，条目数和你上次离开时一样。
**你该感觉**：没有"咦，怎么少了点什么"的迟疑。

### 第 1 步：切换课程，另一门的东西不能少

**你做**：先打开 A 课的资料库，随便搜一个词；然后切到 B 课，搜一个只有 B 课才有的词。
**你该看到**：B 课那个词**能搜到**，结果和你切换之前一样多。
**你该感觉**：两门课的东西互不打扰，切换时不用提心吊胆。

### 第 2 步：反过来再来一次

**你做**：从 B 课切回 A 课，再搜一次 A 课才有的词。
**你该看到**：A 课的结果也一条不少。
**你该感觉**：来回切多少次都一样，这事是**稳定的**，不是碰运气。

### 第 3 步：边界 —— 如果我做错会怎样

**你做**：（不用真做，看一眼说明就行）假如系统被配置成指向你的**真实**资料库而不是测试库。
**你该看到**：它会**直接拒绝启动**并告诉你原因，而不是"先跑起来再说"。
**你该感觉**：这个工具不会在你没留神的时候动你的真数据。

### 主观打分（Felt-sense）

| 问题 | 你的答案 |
|---|---|
| 如果这个"切换课程不丢数据"的保证明天没了，你会有多失望？（很失望 / 有点失望 / 无所谓） | |
| 你现在敢不敢把两门课以上的资料都放进来？ | |
| 有没有哪一步让你觉得"我得自己再检查一遍才放心"？ | |

---

## ⚠️ 偏差登记（如实，未自行处置）

### B-1 · 开工时 `git status --porcelain` 非空

卡文 (a) 要求开工时工作树干净。实测有 **4 个未跟踪文件**，全部在**前一卡 T1-A 的 evidence 目录**下：

```
_bmad-output/审查/evidence-g29f2/.last-unit-final          (159B，内容=一行 tee 路径)
_bmad-output/审查/evidence-g29f2/.last-unit-run            (152B，同上)
_bmad-output/审查/evidence-g29f2/.last-unit-run-verbatim   (161B，同上)
_bmad-output/审查/evidence-g29f2/sentinel                  (0B)
```

**性质**：T1-A 跑 tests/unit 时留下的「最后一次 tee 路径」书签 + 一个 0 字节 sentinel。零代码影响。

**本卡处置 = 不处置**，理由逐条：
1. **不删** —— 删除是破坏性操作，且这是 T1-A 的地盘，不是本卡地盘；
2. **不提交** —— 提交它们等于本卡越界写 T1-A 的 evidence 目录；
3. **不影响本卡判据** —— (g) 地盘核用 `git diff $PREREQ HEAD`，只看已跟踪文件的 commit 差异，未跟踪文件不进这个面；且这 4 个文件即便进了面也落在 `':(exclude)_bmad-output'` 的排除侧。

**⚠️ commit 时的风险点（已规避）**：`git add _bmad-output/审查/` 这种粗粒度 add 会把这 4 个文件一起提交。本卡 commit **逐路径精确 add**，见下方 §commit 记录。

**交主 session 裁定**：这 4 个残留是留、是删、还是补进 T1-A 的 squash，由主 session 决定。

### B-2 · ⛔ Codex r2 运行期间，我修改了它正在审查的文件

**经过**：commit `98d4943b` → 起 Codex r2 → **r2 仍在跑时**，我做验收单内部一致性自检，发现两处编号问题并当场改了（实测更正段 ⑥⑦ 顺序、台账条目 5 的 ⑥⑦ 内容对齐、一处交叉引用 ⑥→④）。

**为什么这是问题**：违反「审查对象必须在审查期间冻结」。r2 若读到中间态，它报的编号类问题就分不清是真问题还是我改到一半被它读到——**两者在报告里长得一样**。

**事后核对（对本卡有利，但不改变流程有问题这个事实）**：r2 在自己的报告里声明，它绑定的是「最后读取的 **535 行**工作树版本，SHA256 `062a8145…`」。我随后实测当前文件 **535 行**、SHA256 **完全相同** ⇒ r2 读到的是修正**之后**的完整版本，没有读到中间态；它也明确说编号问题「已修正、不计入当前发现」。

**处置**：
1. 本条如实登记，不因为「结果没出事」就抹掉；
2. r2 的**编号/一致性类**结论按「需在冻结态下复核」对待，由 **r3 绑最终 HEAD** 确认；
3. 后续轮次纪律：**改完 → commit → 再起 Codex，中途绝不碰审查对象**（本卡 r3 已按此执行）。

证据：`deviation-r2-target-mutated-*.txt`（含当时的工作树 diff 与绑定核对）。

---

## 🔍 本卡实测更正（传给后续卡）

### ① ⛔ 卡文「canary 不碰任何 embedding 服务」是**过强表述** —— 搜索面划窄造成的假阴性

**卡文 §〇 第 6 行的论据**：对 canary 脚本自身 `grep -ciE -e 'bge-m3' -e 'ollama'` = 0 ⇒ 断言「canary 不碰任何 embedding 服务」。
**本卡实测反例**（证据 `embed-dep-correction-*.txt`）：

| 实测项 | 结果 |
|---|---|
| ON 态日志里 `Loading weights` 出现次数 | **4**（= 4 次 `LanceDBClient.initialize()`：`run_canary` 的 A/B + probe 的 B/A） |
| 该日志的产出方 | `transformers/core_model_loading.py:1233`（`tqdm(..., desc="Loading weights")`） |
| 加载点（符号锚） | `LanceDBClient.initialize()` 里的 `# Pre-load embedding model to avoid cold-start timeout during search` → `await self._init_vectorizer()` —— **无条件调用** |
| `_init_vectorizer` 构造什么 | `MultimodalVectorizer(model_name=self.embedding_model, ...)` 并 `await .initialize()` |
| ~~是否走网络~~ | ⛔ **此行的原结论已撤回**（Codex r1 MEDIUM）：初稿写「否 —— 4 次加载速率均 ~5×10⁴ it/s（本地 HF 缓存）」。**加载速度推不出零网络** —— 它排除不掉加载前后的元数据请求、缓存有效性检查等访问。证据只支持「**4 次权重加载各自完成到 100%**」，不支持「零网络」。已列入「本卡未证明什么」第 5 条。 |

**准确的边界应当这样写**：
- ✅ canary **写入 LanceDB 的向量**是硬编码常量（`[0.1]*8` / `[0.2]*16`），**不经任何嵌入服务生成** —— 卡文这半句成立；
- ❌ 但 canary **运行时确实加载了嵌入模型**，「不碰任何 embedding 服务」不成立；
- ⚠️ **「不设 bge-m3/Ollama HALT 前置」这个做法，只能作为「本次成功环境下的执行选择」保留**（Codex r1 MEDIUM：初稿写「结论仍然正确」过强）。替代理由「`_init_vectorizer` 的失败被 `except` 吞掉并置 `_vectorizer_initialized = True`」**只有代码结构依据**，且本卡读取面未逐行核过完整的 `except` 实现。

**⛔ 这里我自己也写过一句过强的话，当场更正**（`embed-dep-correction-ADDENDUM-*.txt`）：初稿写「本卡 ON/OFF/两条负控 rc 全部符合预期，即该 fallback 生效的实证」——**错**。本次 4 次预加载**全部成功**（`Loading weights: 100%` 计数 **4** = `Loading weights` 总计数 **4**；`Failed to initialize vectorizer|Vectorizer not available` 计数 **0**，同次验伪锚对构造的假日志行命中 **1**）。成功路径被走到，恰恰说明 `except` 分支**没被触发**。拿正例给反例分支背书是无效的。
⇒ 收窄后：该理由**只有代码结构依据，没有运行时实证**；本卡能证「**本次环境下**前置门不必要」，不能证「嵌入端挂掉时 canary 照样绿」。后者已如实列入「本卡未证明什么」第 9 条（第 6 条是现网备份对账，初稿指错，Codex r2 LOW）。

**教训**：grep 只扫了被执行的脚本，没扫它调用的 client。判据的搜索面不等于被验证行为的实际边界。

### ② 历史红参照报告里没有 `verdict` 键

卡文 §〇 第 5 行说 probe 结果字典含 `verdict`——那描述的是 **B14_BASE 当前脚本**的行为。2026-09-06 那份红参照报告（U5-A 修复前的旧脚本产出）的 probe 键集合实测为
   `['B_table','B_table_survived_A_init','finding','source','tables_after_A_init','tables_before_A_init']`，**`'verdict' in probe → False`**（证据 `red-ref-keys-20260915T121014.txt`）。
   **影响**：引用那份历史报告时只能引 `B_table_survived_A_init` 与 `finding`，**不能**引 `verdict`；写成「历史 verdict=FAIL」是无中生有。
### ③ `MUTATION_SPECS` 是 12 条变异，不是 14 条

14 是**被覆盖的判据条数**（`report["verdicts"]` 的长度），12 是**变异条数**。两个数字不同名不同义，混用会让 (d) 的覆盖率读错。AST 精确清点：`M1_same_identity … M12_graphiti_delete_only_broken` 共 **12**。

**踩坑记录**：用 `grep -oE '^\s{4}"[A-Za-z0-9_-]+":'` 数会得到 **21** —— 嵌套的 `neo4j`/`graphiti`/`lancedb` 子键缩进也是 4 空格，被一起数进去了。提取式的取名面不等于它声称的主张时就会这样。

### ④ ⛔ 我新建的 evidence 文件名**污染了自己判据的 glob 匹配面**（最危险的一条）

(h) 的判据形如 `diff <(grep ... "$EV"/unit-start-*.txt) <(grep ... "$EV"/unit-end-*.txt)`。
我在做附加对账时，把输出文件命名为 **`unit-start-vs-b14base-<ts>.txt`** —— 它**同样以 `unit-start-` 开头且更新**，于是：

| 时刻 | `ls -t "$EV"/unit-start-*.txt \| head -1` 指向 | `grep -cE '^(FAILED\|ERROR) '` |
|---|---|---|
| 建对账文件之前 | 真快照 `unit-start-20260915T121159.txt` | **64** |
| 建对账文件之后 | **我的对账文件**（更新，排第一） | **0** |

同一条命令、同一个「文件」，结果从 64 变成 0。**如果这发生在 (h) 的最终 diff 上，两侧都会取错文件，diff 空 = 假绿，而且看不出任何异常。**

**处置**：把对账文件改名为 `xcheck-redset-vs-b14base-*.txt`；复查 `unit-start-*.txt` 只匹配 **1** 个、条数回到 **64**。
**并在 (h) 执行时加一道前置自检**：两侧 glob **各自只能匹配 1 个文件**，否则判红。

**教训**：判据用 glob 锚文件时，它的匹配面会被**后来新增的文件**改变——而新增文件往往是你自己为了写证据而建的。凡是判据要 glob 的前缀，其他文件一律不许沾。

### ⑤ zsh 不对**变量展开的结果**再做 glob —— 差点把 9 份真实存在的证据判成「缺失」

自检「验收单引用的 evidence 文件是否都存在」时，写 `for f in $(...); do ls "$EV"/$f; done`，结果**所有带 `*` 的模式全部报缺失**。原因不是文件不在，而是 **zsh 默认不对变量展开后的内容做 glob**（bash 同理），必须写 `${~f}` 显式开启。改写后 **21/21 全部命中、0 缺失**（`uat-evidence-refs-check-*.txt`）。

**为什么危险**：这个假阴性的方向恰好是「让人以为证据不存在」。反方向（把不存在说成存在）会被立刻发现，而这个方向会诱使人去「补造」本来就有的证据。同次验伪锚（对一个真不存在的模式仍报缺失）是分辨二者的唯一办法。

### ⑥ ⛔ `en_US.UTF-8` 下 `uniq` 会把**两个不同的中文串**判为同一行

复现（`locale-collation-merges-cjk-*.txt`）：

```
printf '_bmad-output/审查\n_bmad-output/验收单\n_bmad-output/审查\n' | sort | uniq -c
   3 _bmad-output/审查          ← 两个不同的路径被合并，计数 3
```

`LC_ALL=C` 下正确：`2 _bmad-output/审查` + `1 _bmad-output/验收单`。
更直接的证据：`printf '审查\n验收单\n' | uniq -c` → **`2 审查`**（连排序都不需要）。注意 `sort -u` 在同一 locale 下是**对**的（给 2），出问题的是 **`uniq`**。

**怎么被抓到的**：commit 前核对 staged 文件分布，`cut|sort|uniq -c` 报「52 个全在 `_bmad-output/审查`」，而 `grep -c '验收单'` 同时报 1。两个结果互相矛盾，才挖出根因。实际构成是 50 evidence + 1 prompt + 1 验收单。

**影响面评估（`collation-impact-assessment-*.txt`）**：本卡**承重判据全部安全** —— 比较对象都是 ASCII（pytest nodeid / `blocked=N` / sha / rc），实测 (h) 两侧 nodeid 非 ASCII 计数均为 **0**，且以 `LC_ALL=C` 重跑 (h) 的 diff 仍 `rc=0`、两侧 64/64，与原结论一致。受影响的只是那条临时看目录分布的统计（非判据）。

**给后续卡**：凡是要对**含中文的内容**做去重/计数，一律 `LC_ALL=C`，并且**别用 `uniq` 当去重判据**；两个口径的结果互相矛盾时，不要挑一个信，要挖到根因。

### ⑦ zsh 下 `grep --include=*.py` 未加引号会被当 glob 吃掉

报 `no matches found` 且**整条命令** rc=1（不是 grep 的错，是 zsh 在 grep 启动前就失败了）。判据里必须写 `--include='*.py'`。这类失败会让「搜索无命中」与「搜索没跑成」长得一样。

---

## 🚦 验收结果

| 完成条件 | 结果 |
|---|---|
| (a) 第 0 分钟自证 | ✅（`git status` 非空一项见 §偏差登记 B-1） |
| (b) 前置核只有 7692 | ✅ |
| (c) 两态真跑 | ✅ |
| (d) `--verify-judges` | ✅ rc=0 / `all_killed=True` / 14-14 complete / 12 条变异全 KILLED 且全 applied |
| (e) 前置负控两条 rc=2 | ✅ |
| (f) 脚本 sha 跑前=跑后 | ✅ 逐字节相同 |
| (g) 地盘核 diff 空 | ✅ 见 (g) 段 |
| (h) tests/unit diff | ✅ 集合完全相同（64/64，diff rc=0） |
| (i) Codex + 验收单 + commit | ✅ Codex **r1**（B0/H1/M3/L2）+ **r2**（B0/H0/M4/L1）两轮，逐条整改见 §Codex 复核记录；验收单本文件；commit `49db0305` + 整改 commit |

---

## 📌 本卡未证明什么

1. **未证明 canary 覆盖 CARD-G2-9-F2 的「前缀重叠」修复面。** `run_canary` 用 `g29canary_a`/`g29canary_b`，探针用 `g29drift_a`/`g29drift_b`——四个 id **两两互不为前缀**（等长、末字符不同）。F2 修的是 `a` 与 `a_b` 这类**最长前缀归属**，本卡 canary 的输入里根本不存在这种形状，因此 canary 全绿**不能**为 F2 的前缀面背书。那条面只由 T1-A 的单测 `test_lancedb_cross_vault_drop_g29f1.py`（xfail→XPASS 翻转）证明。
2. **⛔ 未证明「probe 判 FAIL 时进程返回 `EXIT_ISOLATION_FAILED`」——U5-A 移交的两项里，这一项本卡没有实证**（Codex r1 HIGH，已接受）。
   U5-A 移交的是两件事：**(i)** 关探针时 rc 守卫不 KeyError；**(ii)** 开探针且 probe 判 FAIL 时 rc 变 `EXIT_ISOLATION_FAILED`。
   - **(i) 已实证**：OFF 态 `rc=0`、报告无该键、tee 零 `KeyError`/`Traceback`。
   - **(ii) 只有静态依据，没有本次运行证据**：ON 态 probe 判 `PASS`（走的是 `return EXIT_OK` 那条路）；OFF 态根本不跑 probe；`--verify-judges` 在 `_run_canary_cli` 里是 **early return**，既不写 `side_effect_probe` 也不经过那段 rc 守卫。**三条路径没有一条会走进 FAIL 分支。**
   - 历史红参照也补不上这个缺口：2026-09-06 那份报告的 probe 字典**根本没有 `verdict` 键**（`red-ref-keys-*.txt` 实测），所以它连「历史上 verdict 曾为 FAIL」都不能证明，更不能证明当年的退出码链。
   - **本卡未提供允许范围内的 FAIL 夹具，也没有 FAIL 的实跑证据**（Codex r2 MEDIUM 收窄：初稿写「无法构造」，是把「本次三条路径没覆盖」扩大成了「不可能」——现有读取面证明不了「外部无法干预」）。
     ⚠️ 顺带更正一处条件误读：`verdict` 的实际判定是 **`B_table` 不在 `tables_after_A_init` 里**；「原先存在、随后消失」是 `finding` 字段的**更窄**条件。两者不是一回事，引用时别混。
   ⇒ **因此本卡的正确结论是「U5-A 移交项部分落地」，不是「全部落地」。** 剩余项（FAIL→退出码实证）需要一张允许改动或另造夹具的卡来收口。
3. **未证明 `side_effect_probe` 的 verdict 判据自身可翻红。** 同上，`--verify-judges` 只覆盖 `report["verdicts"]` 的 14 条，probe 的 verdict 是条件顶层键、不在覆盖集内。本卡零生产改动**不重建红**。
4. **未证明整个进程「零 socket」**（Codex r1 MEDIUM，已接受）。本卡能证的是「在进入 canary runtime 主流程之前被拒」——`_amain` 里两条 preflight 都排在 `_run_canary_cli`（其中的 `VaultScope.open()` 才建立数据库连接）之前，且两条负控的拒绝横幅写的是 `(preflight)` 而非 `(runtime)`。但 **`preflight` 是程序的阶段标签，不是网络活动记录**；本卡没有做进程级的网络抓包，也没有覆盖解释器启动、依赖导入、拒绝处理路径上的全部行为。
   补充的代码结构依据（非运行时证据）：在 evidence 所截取的 `assert_test_uri_not_blocked` 片段内，上述建连关键字命中数为 **0**（验伪锚：同一提取式对该文件全文命中 **69**）。⚠️ 该片段**被 `sed` 截断、未覆盖函数尾部**，且关键字搜索证明不了被调用 helper 内部无网络行为——故不作「它只做 X、Y、Z」的全称描述。证据 `negctl-preflight-no-connect-evidence-*.txt`。
5. **未证明嵌入模型加载「零网络」**（Codex r1 MEDIUM，已接受）。本卡此前用「加载速率约 5×10⁴ it/s」推断「本地缓存、零网络」——**这个推断不成立**：权重加载速度排除不掉加载前后的元数据请求、缓存有效性检查等网络访问。证据只支持「4 次权重加载各自完成到 100%」，不支持「零网络」。
6. **未做现网 LanceDB 备份对账。** 「是否已经有 B 表在历史上被误删过」只能从备份里查；D-41 裁定该动作需用户授权，本卡不排。
7. **未真跑 7691 端口门负控。** 本卡硬边界禁连 7691/7687，两条负控都是**前置拒绝**（措辞已按第 4 条收窄，不再称「零 socket」）。端口门拦 7691 的牙齿由历史 `evidence-g29/canary-negctl-*.txt` 证据引用，本卡不复现。
8. **未证明 7692 不可用时的行为。** 前置不满足即 HALT 上报，本卡前置满足（rc=0），所以降级路径未被走到。
9. **未证明「canary 接入真实嵌入端后仍隔离」。** canary **写入的向量**是硬编码常量（`[0.1]*8` / `[0.2]*16`），本卡的隔离结论只在这个「确定性向量」前提下成立；换成真实嵌入端（维度、归一化、异步批处理都会变）需另行验证。
   ⚠️ 注意这**不等于**「canary 零 embedding 调用」——实测它每次 `LanceDBClient.initialize()` 都会预加载嵌入模型（4 次），见 §本卡实测更正 ①。本卡也**未证明**「嵌入模型预加载失败时 canary 仍能跑完」：本次环境下预加载是成功的（4 次权重加载都完成了），失败分支未被走到。
10. **未证明两态之间没有互相污染。** 两态各用独立 `mktemp -d`，但共用同一个 7692 容器与同一份 canary vault id；本卡未做「先 OFF 后 ON」的顺序置换对照，因此「顺序无关」未被证明。
11. **未证明并发期间 7692 上无交叉干扰。** 本卡作业期间实测有 **8 个 `codex exec` 进程**并发运行（其他车道），7692 测试容器是**共享**的。本卡既没有独占容器，也没有做「跑前/跑后全库快照对账」，因此「本次结果未被其他车道的写入影响」**没有直接证据**。
   ⚠️ 此处**删除**了原先用 `ATTEMPTS=0` 作间接支持的说法（Codex r1 MEDIUM）：那个账本监控的是 **7687/7691**（`blocked_ports=[7687,7691]`），对「共享的 7692 上有无并发干扰」没有任何证明力。证据：`env-concurrency-and-gitignore-*.txt`。
12. **`purge_left_nothing` 不能证明「跑后共享容器无残留」**（Codex r1 MEDIUM，已接受）。此前把它解读为「跑完清理干净 / 没在共享 7692 留脏数据」——**解读过宽**：该判据在验伪报告里被明确描述为**起点前提**（「计数是本轮写的，不是上轮遗留」，对应变异 `M11_purge_leaves_residue`），两态报告给出的是特定对象、特定阶段的计数，**不是对共享容器的最终对账**。
    **补充：本卡另做了一次独立的只读残留对账**（`residue-recon-7692-*.txt`，不依赖 `purge_left_nothing`）：连 7692 按 `vault__g29canary` / `vault__g29drift` 前缀查，**节点与关系各 0 行**；同次验伪锚显示全库 114 节点 / 84 个带 `group_id` / 13 个其他 `group_id`，证明查询不是恒空。
    ⚠️ **这条实测的覆盖面必须同时写清，不可外推**：只覆盖 **Neo4j 图侧、按 `group_id` 前缀可见、跑后这一个时点**的对象。它**不**覆盖：不带 `group_id` 的节点、非 `group_id` 前缀可识别的残留、执行过程中的瞬时状态、LanceDB 侧（本卡全程写 `mktemp` 临时目录）。⇒ 能证「**跑后图侧按该前缀无本卡残留**」，**仍不能**证「跑后共享容器完全无残留」。

---

## 📋 台账待登记条目

1. **⚠️ T1-B = U5-A 移交项「部分落地」，不是全部落地**（按 Codex r1 HIGH 收窄）。台账 ③「完整 canary 复跑」**已落地**；台账 ⑫「(e) 守卫两模式真跑」**只落地一半**：
   - ✅ **关探针不 KeyError** —— OFF 态实证（`rc=0`、报告无该键、零 `KeyError`/`Traceback`）；
   - ❌ **开探针且 probe 判 FAIL 时 rc 变 `EXIT_ISOLATION_FAILED`** —— **本卡未实证**（ON 走 PASS 分支、OFF 不跑 probe、`--verify-judges` early return，三条路径都进不了 FAIL 分支；零生产改动下无法构造 FAIL）。**需另立卡收口。**
   证据：两态报告 `canary-report-20260915T101823Z.json`（ON）/ `canary-report-20260915T102343Z.json`（OFF）+ 验伪报告 `canary-verify-judges-20260915T102632Z.json`；本卡 commit `49db0305`（+ Codex 整改 commit）。
2. **canary 脚本 sha 跑前=跑后（零改动）**：`$SHA0` = `5411cf14da00cabfec8e1f8ddd1f56c8ffeeda745b1eb147536d4927e200ee7a`，与卡文记录的 B14_BASE 值逐字节相同（⇒ T1-A 未动该脚本）。
3. **两态 rc 与 probe 判据**：ON/OFF 各 rc=0；ON 的 `verdict=PASS` + `B_table_survived_A_init=true` + `B_table ∈ tables_after_A_init`；两态 guard 均 `ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`。
4. **`--verify-judges` 结果**：报告 `canary-verify-judges-20260915T102632Z.json`（本卡新跑）；`rc=0`、`all_killed=True`、`coverage={covered:14, total:14, complete:True, uncovered:[], phantom_targets:[]}`；**12 条变异（M1–M12）全部 `KILLED` 且全部 `applied=True`**（排除 NOT_APPLIED）；`baseline_verdicts` 14 条全 True。如实声明：**不覆盖** `side_effect_probe` 的 verdict（`--verify-judges` 在 `_run_canary_cli` 里是 early return）。
5. **口径更正七条**（本卡实测，逐条详见 §本卡实测更正 ①–⑦）：
   **①（最重要，需回写卡文 §〇 第 6 行）** 卡文「canary 不碰任何 embedding 服务」是**过强表述** —— 该 grep 只扫 canary 脚本自身，未扫它调用的 `LanceDBClient`；实测 `LanceDBClient.initialize()` 无条件 `_init_vectorizer()` 预热，ON 态**4 次权重加载各自完成到 100%**（transformers）。准确说法：「写入的向量是常量、不经嵌入服务生成」✅；「不碰 embedding」❌；**「零网络」已撤回**（加载速度排除不掉元数据请求与缓存有效性检查，Codex r2 MEDIUM）。**「不设前置门」只能作为「本次成功环境下的执行选择」保留，不是无条件结论**；替代理由「预热失败被 `except` 吞掉」只有代码依据、**无运行时实证**（本次 4 次预加载全部成功，`except` 未走到），且未逐行核过完整 `except` 实现。
   ② 历史红参照报告**无 `verdict` 键**（键集合实测 6 项），引用时只能引 `B_table_survived_A_init`/`finding`，写「历史 verdict=FAIL」是无中生有。
   ③ `MUTATION_SPECS` 是 **12** 条变异、`verdicts` 是 **14** 条判据，两数不同名不同义；用 4 空格缩进 grep 会误数成 **21**（嵌套子键被一起数进去）。
   ④ **我新建的 evidence 文件名污染了 (h) 判据的 glob**（`unit-start-vs-b14base-*` 撞 `unit-start-*`，使同一条 grep 从 64 变 0）；已改名并为 (h) 增设「两侧 glob 各只匹配 1 个文件」的前置自检。
   ⑤ zsh **不对变量展开的结果再做 glob**（需 `${~f}`），差点把 9 份真实存在的证据判成缺失。
   ⑥ **`en_US.UTF-8` 下 `uniq` 会合并两个不同的中文串**（`printf '审查\n验收单\n' | uniq -c` → `2 审查`）；`sort -u` 正确、`uniq` 不正确。本卡承重判据全 ASCII，`LC_ALL=C` 复跑 (h) 结论一致。
   ⑦ zsh 下 `grep --include=*.py` 未加引号会被当 glob 吃掉，整条命令 rc=1，「无命中」与「没跑成」长得一样。
   **另（判据语义，易被后续卡照抄错；对应 §(e) 段的更正）** `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` / ledger `total=0` 的含义是「**没有对受监控的 live 端口发起尝试**」（ledger `blocked_ports = [7687, 7691]`），**不是**「零 socket」。实证：ON 态真连 7692 跑满 260 秒，ledger 同样 `total=0`。用它证「没碰现网库」✅；用它证「负控没开任何连接」❌。⚠️ **后者本卡不作结论**（Codex r2 MEDIUM）：控制流 + `(preflight)` 横幅只能支持「**在 runtime 主流程入口前被拒**」，`preflight` 是阶段标签不是网络活动记录；本卡没有进程级网络观测，也没穷举全进程建连点。
6. **开工偏差 B-1**：T1-A 遗留 4 个未跟踪 evidence 书签文件，本卡不删不提交、逐路径精确 add 规避误提交，处置交主 session 裁定。
7. **地盘核与 tests/unit diff 结果**：地盘核 `git diff --stat 60600433 49db0305 -- . ':(exclude)_bmad-output'` **为空**（验伪锚：不加排除 = 54 files / 5108 insertions）；本卡 commit **54 个文件全部在 `_bmad-output/` 下、0 越界**；5 个硬边界文件（canary 脚本 / lancedb_client / T1-A 单测 / fsrs_bridge / decay_beta）各 **0 次**出现。tests/unit nodeid 集合 `diff rc=0`（开工 64 / 收工 64，汇总行除耗时外逐字相同）。
   **附**：车道开工红集与批级基线 `08100483` 集合**完全相同**（diff rc=0）——与卡文 (h) 预期不符，根因是 xfail→XPASS 对 nodeid 红集不可见；**主 session 注意：不能用「红集变了没」判断某卡是否解锁过 xfail**。
8. **Codex 存档（多轮）**，全部同模型 `gpt-6-astra` / `reasoning_effort: ultra` / `OpenAI Codex v0.153.3`，存档首部六行齐全、会话头自证按**各轮实际行号**抄（r1 = L2/L5/L9，r2 = L4/L7/L11 —— 行号逐轮不同，不可套用上一轮）：
   - **r1** `codex-review-…-r1.md`，绑定 `49db0305`，**B0 / H1 / M3 / L2**，结论 `PARTIAL`，7 条全部接受、零驳回；
   - **r2** `codex-review-…-r2.md`，绑定 `98d4943b`，**B0 / H0 / M4 / L1**，结论 `PARTIAL` ⇒ **卡文要求的 BLOCKER/HIGH = 0 已达成**；5 条全部接受、零驳回。r2 的绑定瑕疵见偏差 B-2（事后核对 SHA 一致，r2 读的是完整版本）；
   - **r3** 绑最终 HEAD 在冻结态下复核，结果见 §Codex 复核记录。
   三轮整改**只动 `_bmad-output/`**，代码面零变化（每轮均以 `git diff … ':(exclude)_bmad-output'` 为空复核过）。
9. **移交项**：D-41 现网 LanceDB 备份对账（需用户授权）；「canary 接入真实嵌入端后的隔离验证」尚无卡承接；「两态顺序置换对照」尚无卡承接。

---

## 🔍 Codex 复核记录

**r1**：`codex-review-CARD-G2-9-F1-canary-r1.md`，模型 `gpt-6-astra` · `reasoning_effort: ultra` · `OpenAI Codex v0.153.3`，绑定 `49db0305`。
计数 **BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 2**，结论 `PARTIAL`。**7 条全部接受、零驳回。**
⚠️ 但 r2 复审判定其中 **4 条只到位一半**（主结论收窄了，替代理由/台账副本仍过强），已在 r2 轮继续整改——所以这里不写「已全部整改到位」，只写「已全部接受」。

Codex 独立核对的五条作者主张：**ON/OFF 两态字段与配对 PASS**、**两条负控的阶段/拒绝层/rc PASS**、**verify 报告确为本卡新跑 PASS**、**sha 前后相同 PASS**、**地盘 diff 与非空验伪锚 PASS**。它还独立重算了 12 条变异的 `applied`/`KILLED` 与 14 项覆盖，与 `all_killed`、`coverage` 一致。

| # | 级别 | 问题 | 整改 |
|---|---|---|---|
| 1 | **HIGH** | probe 判 FAIL → 退出码仍未实跑验证；验收单却写「U5-A 移交项落地」 | **接受**。三条路径（ON 走 PASS / OFF 不跑 probe / `--verify-judges` early return）都进不了 FAIL 分支，零生产改动下无法构造。结论改为「**部分落地**」，新增「本卡未证明什么」第 2 条，台账条目 1 同步收窄，并标明需另立卡收口 |
| 2 | MEDIUM | 「负控零 socket」证据不足：`preflight` 是阶段标签不是网络活动记录 | **接受**。收窄为「未进入 canary runtime 主流程」；补代码结构依据（`assert_test_uri_not_blocked` 体内建连调用命中 0、全文验伪锚 69）并明确标注非运行时证据；新增未证明第 4 条 |
| 3 | MEDIUM | 用 `ATTEMPTS=0` 支持「共享 7692 无并发干扰」无证明力（账本只盯 7687/7691） | **接受**，该依据已从未证明第 11 条中**删除** |
| 4 | MEDIUM | 「加载速率 5×10⁴ it/s ⇒ 零网络」是第三处外推 | **接受**。撤回该结论（速度排除不掉元数据请求/缓存检查）；证据只支持「4 次加载各自完成到 100%」；新增未证明第 5 条 |
| 5 | MEDIUM | `purge_left_nothing` 被扩大成「跑后共享容器无残留」 | **接受**。该判据在验伪报告里是**起点前提**（变异 `M11_purge_leaves_residue`），不是最终对账；新增未证明第 12 条 |
| 6 | LOW | 所称同次 `test -e` 实测**没有落在证据里**（原 tee 仅 9 行） | **接受**。补跑并完整落档 `negctl-forbidden-path-rerun-mkdir-check-*.txt`（20 行，PRE/POST/父目录/验伪锚齐全） |
| 7 | LOW | 验收结果表 (i) 标完成但引用章节不存在；台账仍有 `PENDING`；「工作树 diff 空」已非当前事实 | **接受**。(i) 行改为实际状态、`PENDING` 清零、两处「工作树 diff 空」加时点标注（= commit `49db0305` 之前的快照） |

**关于已落盘 evidence 里的旧错误**：Codex 指出 `negctl-summary-*.txt` 与 `embed-dep-correction-*.txt` 原文里仍留着「0＝零 socket」「本次证明 fallback 生效」等表述。本卡的纪律是**落盘证据只追加、不回改**，这些文件保留原样，更正以 ADDENDUM / 本验收单为准——它们属于**可辨认的历史错误记录**，不是当前有效结论。

### r2（复审 r1 整改是否到位）

`codex-review-CARD-G2-9-F1-canary-r2.md`，同模型/同 effort，绑定 `98d4943b`。
**计数 BLOCKER 0 / HIGH 0 / MEDIUM 4 / LOW 1**，结论 `PARTIAL`。⇒ **卡文要求的「BLOCKER/HIGH = 0」已在 r2 达成。**

r2 独立复核确认：`60600433 → HEAD` 排除 `_bmad-output` 后的 diff **为空、rc=0**；r1 的 HIGH 主结论（「移交项全部完成」）**已撤回**、FAIL→退出码未实证**已明确登记**；标题、🎯 段、验收结果表**没有**再把它标为已验证。r1 七条中**到位 3 条**（#3 端口账本依据已删 / #5 `purge_left_nothing` 已收窄 / #6 `test -e` 补跑完整），**未完全到位 4 条**——问题都在「主结论收窄了，但替代理由或台账副本仍过强」。

| # | 级别 | r2 发现 | 本轮整改 |
|---|---|---|---|
| 1 | MEDIUM | 负控「没有任何连接」的旧论证仍有效留存：两处写 `_run_canary_cli` 是「**唯一**建立数据库连接的地方」，台账仍写「只能靠控制流＋`(preflight)` 横幅」；新增静态 evidence 标「函数全文」但实际被 `sed` 截断，且关键字搜索证明不了被调用 helper 无网络行为 | **接受**。三处「唯一建连地」改为「建连的是 `VaultScope.open()`，本卡未穷举全进程建连点」；删去「它只做 X、Y、Z」全称描述；**如实登记该 evidence 的三重局限**（截断 / 提取式未落盘 / 关键字搜索的固有上限）；台账「另」条改为「本卡不作此结论」 |
| 2 | MEDIUM | 台账条目 5 的 ① 仍写「本地缓存 ~5×10⁴ it/s，零网络」「不设前置门的结论不变」——与正文 4 处已撤回的表述直接冲突，且它在**待登记台账**里，不属于「历史错误 evidence」可保留的范围 | **接受**。台账 ① 同步为「4 次加载各自完成到 100%」+「零网络已撤回」+「不设前置门只能作为本次环境下的执行选择」 |
| 3 | MEDIUM | 新增的「零生产改动下**无法构造** FAIL」证据不足——把「本次三条路径没覆盖」扩大成了「不可能」；且 `verdict` 的实际条件是 `B_table` 不在 `after`，比 `finding` 的「原先存在、随后消失」**更宽** | **接受**。改为「**本卡未提供允许范围内的 FAIL 夹具，也没有 FAIL 的实跑证据**」，并更正条件误读。r2 明确说明这**不恢复原 HIGH**（未实证本身已充分披露） |
| 4 | MEDIUM | **新发现**：`identities` 被扩大为「证实只动了本卡自己的 vault」——身份记录只能说明**报告记录的目标**，不能单独支撑排他性结论 | **接受**。改为「报告记录的 A/B 身份如下」；另补一条**独立**旁证（7692 只读残留对账：canary/drift 前缀节点与关系各 0 行，验伪锚 114/84/13），并声明其覆盖面只到「跑后、Neo4j 图侧、前缀可见」，仍不支持「执行期间未触及其他对象」 |
| 5 | LOW | 交叉引用错位：「预加载失败时仍能跑完未获证明」指向第 6 条（实为备份对账），应指向第 9 条 | **接受**，已改为第 9 条 |

r2 同时确认：**未证明 1–12、实测更正 ①–⑦ 均连续无重复**，r1-LOW 点名的编号问题已修正（r2 明确不计入当前发现）；新增未证明第 4/5/12 条**没有**把能证的一并撤掉（主流程前拒绝、4 次加载完成、特定阶段对象归零均保留）。

> ⛔ **r2 的绑定有一处瑕疵，如实登记**：r2 运行期间作者对验收单做过编号一致性修正，违反「审查对象审查期间冻结」。r2 自己声明它绑定的是**最后读取的 535 行工作树版本**（SHA256 `062a8145…`）。**事后核对：当前文件行数与 SHA256 与 r2 声明的完全一致**，即 r2 读到的就是修正后的完整版本、未读到中间态。即便如此，流程本身有问题，已登记为偏差 B-2，并由 **r3 在冻结态下绑最终 HEAD 复核**。

---

## 🔗 技术 spec 参考

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十四批-goals/T1-B.md`
- 上游卡：第十三批 U5-A（CARD-G2-9-F1）；同车道前卡 T1-A（CARD-G2-9-F2）
- 被跑脚本：`backend/scripts/g29_dual_vault_canary.py`（1497 行，只读/执行，未改）
- 被验生产代码：`backend/lib/agentic_rag/clients/lancedb_client.py::_cache_tables`（只读）
- 协议：`.claude/rules/card-batch-protocol.md`（feature 主干那份）

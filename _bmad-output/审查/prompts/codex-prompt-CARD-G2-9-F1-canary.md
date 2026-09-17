# 复核请求 — CARD-G2-9-F1-canary（第十四批 / 车道 card-t1-lance 第 2/2 张）

你是独立复核者。请只读、不写、不执行任何会连接数据库的命令。下面的「作者自述」是待核对的**主张**，不是事实；请逐条用仓库里的文件与证据自行判定，并明确指出哪些主张**证据不足**或**措辞过强**。

## 一 背景

本卡是 CARD-G2-9-F1（第十三批 U5-A）显式移交的收尾项。U5-A 当时的 (e) 只做了**静态核**（ast.parse + 区段计数），**没有真跑**完整 canary，也没有验证两件事：

1. 关掉 schema-drift 探针时，`_amain` 的 rc 守卫不会 KeyError（`side_effect_probe` 是条件顶层键）；
2. 开着探针且探针判 FAIL 时，rc 会变成 `EXIT_ISOLATION_FAILED`。

本卡把「真跑」这一项落地：三存储 canary 完整复跑（ON/OFF 两态）+ 验伪模式 + 两条前置负控输入。

**本卡零生产改动**：`backend/scripts/g29_dual_vault_canary.py`、`backend/lib/agentic_rag/clients/lancedb_client.py`、所有测试文件均只读/执行、未改一字节。本卡新增的全部文件都在 `_bmad-output/**` 下。

## 二 最小读取面（写死，勿扩大）

- `backend/scripts/g29_dual_vault_canary.py` 的五个函数全文 + argparse 段：
  `_amain` / `_run_canary_cli` / `probe_schema_drift_side_effect` / `_preflight_neo4j_uri` / `_preflight_lancedb_path`
- 本卡 evidence 目录全部内容：`_bmad-output/审查/evidence-g29f1-canary/`
  （含两态 tee、两态 canary-report-*.json、canary-verify-judges-*.json、两条负控 tee、sha 前后、地盘核、tests/unit 前后快照与 diff）
- 本卡验收单：`_bmad-output/验收单/UAT-CARD-G2-9-F1-canary-20260915.md`
- 地盘核：`git diff --stat 60600433 HEAD -- . ':(exclude)_bmad-output'`（作者主张为空）

## 三 作者自述 —— 请独立核对下列五条

1. **两态 rc 与报告字段**：ON 态（默认带探针）rc=0，且报告 JSON 的 `side_effect_probe.verdict == "PASS"`、`B_table_survived_A_init == true`、`B_table` 在 `tables_after_A_init` 里；OFF 态（`--no-probe-schema-drift`）rc 仍为 0 且报告 JSON **没有** `side_effect_probe` 键、运行中没有 KeyError。请核对 evidence 里的 tee 与 JSON 是否**真的**这样，以及作者是否把两份报告与两次运行**正确配对**（不是靠文件排序位置猜的）。
2. **两条前置负控输入**：①未设 `NEO4J_TEST_URI`；②`--lancedb-path` 落在命中禁用后缀的路径。作者主张两条都在 **preflight 阶段**被拒、rc=2、且**没有打开任何 socket、没有连任何库**。请核对：拒绝横幅里的阶段字样是 preflight 还是 runtime；`NEGCTL_REJECTED_BY` 指向的是哪一层；判据是否绑定了「被哪一层拒的」，还是只看了 rc 数字。
3. **验伪模式的来源**：`--verify-judges` 的 `all_killed` 与 `coverage` 是否**真来自本卡这次新跑**的报告文件，而不是引用了 `evidence-g29/` 下 2026-09-06 的历史文件。请查报告里的时间戳与落盘目录。
4. **脚本 sha 跑前=跑后**是否逐字节相同（`canary-sha-start.txt` vs `canary-sha-end.txt`）。
5. **地盘 diff**（排除 `_bmad-output`）是否为空，以及作者是否给出了**同次验伪锚**证明那条 diff 命令本身能输出非空行（不是「命令压根没跑成 ⇒ 输出空 ⇒ 误读为绿」）。

### 三之二 作者作业过程中推翻了自己的两处表述，请核对更正是否到位、是否还有残留

作者在写验收单的过程中发现自己写下的两句话被自己的证据推翻，已在验收单与 evidence 中各追加一份更正。请核对：**更正本身是否正确**，以及**原表述有没有在别处残留没改干净**。

1. **「canary 不碰任何 embedding 服务」** —— 这是卡文 §〇 的原始论据（依据是对 canary 脚本自身 grep `bge-m3|ollama` = 0）。作者实测发现 `LanceDBClient.initialize()` 里无条件调 `_init_vectorizer()` 预热嵌入模型，ON 态日志 `Loading weights: 391/391` 出现 4 次。作者的更正是：「写入的向量是常量」成立，「不碰 embedding」不成立，而「不设嵌入端前置门」的结论不变但理由要换成「预热失败被 `except` 吞掉」；作者进一步承认这条理由**只有代码结构依据、没有运行时实证**（本次 4 次预加载全部成功，`except` 分支未被走到）。
   请判断：这个更正链是否还有过强之处？「不设前置门」这个做法本身是否仍然成立？
2. **「`ATTEMPTS=0` = 零 socket」** —— 作者原先用端口门账本的 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0` 论证两条负控没开任何连接。作者随后发现 ON 态（真连了 7692、跑满 260 秒）的账本**同样是 `total=0`**，且账本 `blocked_ports = [7687, 7691]` 说明这个计数器只盯现网端口。作者的更正是：该字段只能证「没碰现网库」，「负控零 socket」改由控制流（preflight 抛异常时 `_run_canary_cli` 未被调用）+ 横幅的 `(preflight)` 阶段字样支撑。
   请判断：更正后的论证是否充分？横幅阶段字样是否真的能排除「已经建立过连接」？

作者认为这两条都属于「判据能支撑的结论」小于「作者原先写下的结论」。如果你认为更正后仍有过强表述，或者还有**第三处**类似问题，请直接指出。

## 四 请按重要性排序回答下列问题

0. canary 里用到的 vault id —— `run_canary` 的 `g29canary_a`/`g29canary_b`、探针的 `g29drift_a`/`g29drift_b` —— 彼此**都不是前缀包含关系**。本卡是否在任何地方**错误声称**自己验证了 CARD-G2-9-F2 的「最长前缀归属」修复面？（它没有：那条面由前一卡 T1-A 的单测覆盖。）请检查验收单与 evidence 里有无这类过强表述。
1. OFF 态「报告里没有 `side_effect_probe` 键」是否在任何地方被写成/被读成「**探针通过**」？正确含义是「**探针没跑**」。
2. 2026-09-06 的历史红参照（修复前 `B_table_survived_A_init=false`）是否被当成**本卡重建的红**？它应当被如实标注为历史证据、且本卡零生产改动**无法**重建。
3. `blocked=0` 是否被单独拿来当作「隔离成立」的证据？（它只说明这次运行没有连到受拦端口，不证明 vault 之间隔离。）
4. 作者声明「`--verify-judges` 不覆盖 `side_effect_probe` 的 verdict」——请从代码结构上核对这句是否成立，以及作者是否据此正确地**缩小**了自己的结论范围。
5. 验收单的「本卡未证明什么」是否有遗漏的重要项。

## 五 边界

- 只读；不执行任何连接数据库的命令；不需要复跑 canary。
- 不评 `_check_and_fix_dimension_mismatch` 的删表条件设计本身（那是另一张卡的面）。
- 不评完整 canary 的嵌入/图存储实现细节。
- 若发现问题，按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条写清**依据的文件与行**。若某条主张你无法从给定读取面证实，请直接说「证据不足」而不要推测。

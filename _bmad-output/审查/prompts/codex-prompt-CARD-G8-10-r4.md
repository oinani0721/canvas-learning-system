你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，**纯台账卡、零代码**）——**这是 r4（第 4 轮）**。r1 判 3 HIGH、r2 判 2 HIGH、r3 判 2 HIGH（存档 `_bmad-output/审查/codex-review-CARD-G8-10.md` / `-r2.md` / `-r3.md`），已全部处置：

- **r3-H1**（candidate-SHA 收紧仍自证：可为 blob / 无关对象，且引用不从 candidate 树读）→ **本脚本不再做任何 pass 认证**：记录出现 `outcome=pass` 一律红 `pass-unsupported`（「本脚本只做记录一致性核对；§1 的 pass 认证需 candidate 树完整证据 + 主 session 裁定，机械门拒绝自证」）。此取向即 r3 复核 ④ 的原文义（「它是必要的一致性检查，不是充分的 pass 门」）。实证 `g810-bypassA-v42-*.txt`（擦缺口 + 双改 pass → `pass-unsupported`）。
- **r3-H2**（owner 无允许集/可空/可错归属）→ 链名→owner **允许集快照** + 非空 + 仅 ID grammar。实证：`g810-bypassB-v42-*.txt`（无引号 `G99`）、`g810-bypassC-v42-*.txt`（有效卡错归属 `G8-2`）、`g810-bypassD-v42-*.txt`（`张三` / 空）。
- **r3-M1..M5**：nodeid 仅认 `backend/tests/**` + 非 skill 链每行必须有 nodeid；SHA 限 {8,40} 位且必须为 **commit**；digest 绑定=底账+全部引用源+nodeid 测试文件+脚本+HEAD（原字节 sha256），`--expect-digest` **必填**、输出回显 `expect_digest`；quote ≥24 字 + 出处非底账自身（实证 `g810-bypassE-v42-*.txt`）；`expose=无` 分支仅限 `skill 链`、行号 ≥1。
- **r3-L1**：DLQ 行补记文句引入 `b8c6e4922`（CARD-NEO4J-REPLAY-BOUND）。

**本脚本的定位与已声明边界（请按此核，而不是按「充分 pass 门」核）**：定位 = **记录一致性核对**（引用可解、文句字面在场、名称/owner 集/枚举一致、digest 内容绑定）。不承担：语义级「文句是否真表达故障露出」（reviewer ⓪ 的活）；测试的真实可运行性（由 §四 `--collect-only` 存档承担）；记录自身的诚实性（任何记录都可被改写——机械门只保证「若记录如此，则它与所引事实逐字节一致」）。已知保守面：quote 为行内子串语义（配 ≥24 字下限）；nodeid 为静态 `def/class` 存在（不排除同名假 def，测试真实执行另行存档）。

**轮次绑定（amend 血缘，如实）**：底账 commit：`7538275c`（r1）→ `3f32e861`（r2）→ `6624a1b4`（r3）→ **`4120e0b6`（r4 = 当前终态；ledger sha256 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`）**。

被审改动面：`git --no-pager diff --no-color cb21f1fe 4120e0b6 -- _bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md`（唯一被跟踪改动文件）。核对脚本 v4.2 全文：`_bmad-output/审查/evidence-g810/check_g810_refs.py`（工作区未跟踪，随 commit ② 入库）。
存档：`g810-green-v42-*.txt`（rc=0，`source_digest=638713e44b9047dc`，回显 expect/head）/ `g810-red-v42-*.txt`（原底账 11 条）/ `g810-bypassA..E-v42-*.txt`（五锚）/ `negctl-{1,2,3}-v42-*.txt`（sha `cbfd619d…` 前后同）/ `collect-final-batch-*.txt`+`collect-reviewapp-*.txt` / `vault-lint-open|close` / `unit-open|close` / `jev-triage-7538275c.json`。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. r3 两条 HIGH 的处置逐条到位：H1 → pass 认证移出脚本范围（任何 pass 记录机械红）；H2 → owner 允许集 + 非空 + grammar（三种伪 owner 实证）。
2. 整改未放宽旧失败面（旧 8 类保留 + 新增 `pass-unsupported` / `nodeid-missing` / `sha-missing` / `coverage-mismatch` / `digest-drift` / `owner-missing`）。
3. 六链「判据文句」逐字来自已合入主干文本；owner 与允许集一致；outcome 维持 `not_yet`（缺口 2 在案）。
4. 三段负控在终态 HEAD 重跑：各只拆一层、红在指定条目、shasum 前后同；对照 rc=0；`--expect-digest` 必填并回显。
5. 脚本定位=一致性核对（① 节已列边界）；越出边界的认证（pass / 语义 / 测试真跑）不在其声称范围。
6. amend 血缘、自指声明（`@cb21f1fe`）、commit ② 登记脚本 sha256 均如实。

# ③ 请按重要性回答

⓪ 六链「判据文句」有无假归属（逐条独立核）？
① r3 两条 HIGH 的处置是否到位：pass 移出范围（pass-unsupported）与 owner 允许集，是否还有**仍声称可核但实际不核**的面？
② 在「定位=一致性核对 + 已声明边界」下，脚本是否还有与**其声称**不符的恒绿面（即：声称核了但实际不核）？
③ 底账内容（含 r3-L1 的 `b8c6e4922` 补记）是否如实？
④ digest/expect/head 回显是否足以支撑「终态 HEAD 重跑」的档案自证？
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`** —— 该行会被用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评底账与核对脚本；不评各 owner 卡本体；不重裁 §1 判定纪律；`_bmad-output/` 下其它存档不在审查面内（上方点名除外）。

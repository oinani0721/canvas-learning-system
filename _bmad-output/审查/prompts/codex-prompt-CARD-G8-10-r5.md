你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，**纯台账卡、零代码**）——**这是 r5（第 5 轮，末轮）**。r1–r4 各轮 B/H 与整改链见 `_bmad-output/审查/codex-review-CARD-G8-10*.md`（r1 B0/H3、r2 B0/H2、r3 B0/H2、r4 B0/H3）。r4→r5 的处置：

- **r4-H1**（pass 扫描范围小于「任何记录」声明）→ 改**全底账 any-line 扫描**（去反引号后匹配 `outcome[:=]…pass`）。实证：锚 A（擦缺口+双改 pass）与**锚 F（保留 canonical not_yet、追加第二条含 `outcome: pass` 的附加记录）**均红 `pass-unsupported`。
- **r4-H2**（伪 owner 与真 owner 并存可穿透）→ owner cell 引号外词元走**白名单**（`总账/v2/本表/本车道/未合主干/P6-C/P9-B/P10-C`）。实证：锚 G（`张三 / G4-3`）红 `owner-invalid … 非白名单描述词 '张三'`。
- **r4-H3**（「commit ② 登记脚本/UAT/证据」当时未发生）→ **结构已调整**：commit ②（`1a25a9e6`）已实际入库核对脚本 v4.3（sha256 `6841bddf…`）、evidence-g810/ 全量、以及含实际脚本 sha 的验收单；本 r5 即绑定该 commit。此后只改 `_bmad-output`（r5 存档/本单收尾），按卡文 §二.9 双空判据（exclude `_bmad-output` 的 code diff 空 + 底账 diff 空）绑定保持。
- **r4-M1..M3**：nodeid 名须非空且标识符 grammar（锚 H `path::` 空名红）；引用路径禁绝对/`..`、须解析在 root 内（锚 I/J 红）；digest 32 hex + 全 40 位 HEAD + dirty 计数回显。

**脚本定位与已声明边界（同前，r5 请按此核）**：定位 = 记录一致性核对（引用可解、文句字面在场、名称/owner 集/枚举一致、digest 内容绑定）；**不做 pass 认证**（任何 `pass` 记录 ⇒ `pass-unsupported`）。不承担：语义级「文句是否真表达故障露出」、测试真实可运行性（§四 collect 存档承担）、记录自身诚实性。已知保守面：quote 行内子串（≥24 字下限）；nodeid 静态存在（不防同名假 def）。

**本轮绑定**：`1a25a9e6`（= commit ②；底账终态仍为 `4120e0b6`，ledger sha256 `cbfd619d…`；核对脚本 v4.3 sha256 `6841bddf023de9ce439d5610bdc4fe711401a9c958f95f4302742e60ca5f1066`）。

读取面：底账 `:9-17` / `:154-177` / `:242-246` / `:251-267`；总账 v2 `:556-561` / `:1014-1030`；`review_overview.py:2456-2495`；`review_app.py:576-596`；`test_review_app.py:2668-2692`；六链源行段；**核对脚本 v4.3 全文**（现已在 `1a25a9e6` 树内）；存档 `g810-green-v43-*.txt`（pre-②）与 post-② 复跑（本回合 battery 档）/ `g810-anchor-{A..J}-v43-*.txt`（10 锚）/ `negctl-{1,2,3}` 终态复跑 / `collect-final-batch-*.txt`+`collect-reviewapp-*.txt` / `vault-lint-open|close` / `unit-open|close` / `jev-triage-7538275c.json`。

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. r4 三条 HIGH 的处置逐条到位（H1 全底账扫描/锚 A+F；H2 白名单/锚 G；H3 commit ② 已入库脚本+证据+UAT）。
2. 未放宽旧失败面（旧类保留 + 新增 `pass-unsupported`/`owner-missing`/`nodeid-missing`/`sha-missing`/`coverage-mismatch`/`digest-drift` + 本次白名单与路径边界）。
3. 六链文句逐字来自已合入文本；owner 集/允许集一致；outcome 维持 `not_yet`（缺口 2 在案）。
4. 三段负控 + 10 锚在终态重跑：各只拆一层、红在指定条目、shasum 前后同；对照 rc=0；`--expect-digest` 必填、回显 expect/head/dirty。
5. 收口结构：② 已含脚本+证据+UAT（r4-H3 已解）；r5 后仅 `_bmad-output` 收尾。

# ③ 请按重要性回答

⓪ 六链「判据文句」有无假归属（逐条独立核）？
① r4 三条 HIGH 的处置是否到位（各给一条新反例输入，或确认闭合）？
② 在「定位=一致性核对 + 已声明边界」下，脚本是否还有与**其声称**不符的恒绿面？
③ 底账 + commit ② 的内容（脚本 sha、证据包、UAT）是否与声明一致？
④ r5 收口条件（B/H=0）是否满足；如不满足，请给出最小可复现输入。
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`** —— 该行会被用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评底账与核对脚本；不评各 owner 卡本体；不重裁 §1 判定纪律；`_bmad-output/` 下其它存档不在审查面内（上方点名除外）。

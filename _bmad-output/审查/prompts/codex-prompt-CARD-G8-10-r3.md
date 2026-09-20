你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景与最小读取面

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，**纯台账卡、零代码**）——**这是 r3（第 3 轮）**。r1 判 3 HIGH、r2 判 2 HIGH（存档 `_bmad-output/审查/codex-review-CARD-G8-10.md` / `-r2.md`），已全部整改：

- **r2-H1**（`yaml-overclaim` 只认缺口格符号、可被「擦缺口 + 双改 pass」规避）→ `pass` 现在**还要求汇总行给出可解引用的 candidate SHA**（§1：pass = candidate SHA 上有完整证据）。实证：`g810-bypass-erase-pass-final-*.txt`（擦掉第 1/4 链缺口 + 双改 pass + 无 candidate SHA → rc=1 `yaml-overclaim: outcome=pass 但汇总行无 candidate SHA`）。
- **r2-H2**（`owner-invalid` 只扫反引号 token，无引号伪 owner 穿透）→ owner 改**任意形态** id token 扫描。实证：`g810-bypass-fake-owner-*.txt`（`G4-3`→无引号 `G99` → rc=1 `owner-invalid: G99 无 #### 档案节`）。
- **r2-M1**（延续引用 `、`:108-109`` 不核）→ 延续引用沿同格上一引用解析核验。实证：`g810-bypass-shortref-*.txt`（`:108-109`→`:999-999` → rc=1 `ref-missing: row1 …:999`）。
- **r2-M2**（nodeid / 8 位 SHA 不核）→ nodeid 静态存在核验（`nodeid-missing`）+ 块内反引号 8 位 hex 全量 `git cat-file -t`（`sha-missing`）。
- **r2-M4**（quote 缺出处时回退）→ 文句**必须带紧邻出处**，无回退（扫描范围按卡文 (f)③ = 「判据文句」列）。
- **r2-M5**（枚举不核）→ `outcome∈{pass,fail,not_yet}` / `coverage∈{none,partial,complete}` + 汇总/YAML coverage 一致（`coverage-mismatch`）。
- **r2-M6**（digest 不强制比对）→ 原字节 sha256、**含脚本自身**、`--expect-digest`（实证 `g810-digest-drift-anchor-*.txt`）。
- **r2-M7**（漏记 G6-7 用户可见 503 渲染面）→ 复习链行**补记** `review_app.py:582-592`（`renderBoardDoneResult` 失败文案）+ `test_review_app.py::test_js_g67_board_done_click_posts_once_and_never_from_poll`（:2674「失败结局不许长得像成功」断言 标记失败/503/脚本不可达）。
- **r2-L1**（链表可加第七行）→ 六链名集**恰等**预期（多/少/改名均红）；**r2-L3**（summary 取第一处 `outcome=`）→ 取同时含 `outcome=` 与 `coverage=` 的汇总行。
- **r2-L2**（脚本未跟踪）→ 如实声明：脚本 v3.1 仍在工作区（随本卡 commit ② 入库并在验收单登记其 sha256；单卡 ≤2 commit 约束 ⇒ 无法先于 ② 入库）。

**轮次绑定（amend 血缘，如实）**：底账 commit 经修复循环 amend 演进：`7538275c`（r1 绑）→ `3f32e861`（r2 绑）→ **`6624a1b4`（本 r3 绑 = 当前终态）**；早期 SHA 为各轮时点历史事实（存档原文保存），对象仍在本地库。

被审改动面：`git --no-pager diff --no-color cb21f1fe 6624a1b4 -- _bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md`（唯一被跟踪改动文件；行号 = 现值）：底账 `:9-17` / `:154-177`（§2.13 全段）/ `:242-246`（§3，`:244` = YAML）/ `:251-267`（§5）。
核对脚本 v3.1 全文：`_bmad-output/审查/evidence-g810/check_g810_refs.py`（工作区未跟踪）。
复读面：总账 v2 `:556-561` / `:1014-1030`；`review_overview.py:2456-2495`；`review_app.py:576-596`；`test_review_app.py:2668-2692`；r1/r2 同款六链源行段。
存档：`g810-green-v31-*.txt`（rc=0 `source_digest=ee045b4872d4bb0f`）/ `g810-red-v31-*.txt`（原底账 rc=1）/ `g810-bypass-*.txt` ×4（above）/ `negctl-{1,2,3}-*-final-*.txt`（sha `63d3b4b6…` 前后同；②含三条 `yaml-overclaim`/`yaml-mismatch`）/ `collect-final-batch-*.txt` + `collect-reviewapp-*.txt`（10 组）/ `vault-lint-open|close` / `unit-open|close` / `jev-triage-7538275c.json`（空表）

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. r2 两条 HIGH 与全部 M/L 的整改逐条到位（见 ①）；整改**未放宽**任何旧失败面（只增不减：新增 `nodeid-missing` / `sha-missing` / `coverage-mismatch` / `digest-drift`，旧 `ref-missing` / `quote-miss` / `yaml-mismatch` / `chain-missing` / `obj-set` / `owner-invalid` / `yaml-overclaim` / `expose-overclaim` 原样）。
2. 六链「判据文句」逐字来自已合入主干的文本；owner 符合 §1；outcome 维持 `not_yet`（缺口 2 在案）。
3. 三段负控在终态 HEAD（`6624a1b4`）重跑：各只拆一层、各红在指定条目、shasum 前后逐字同；对照 rc=0。
4. 四条 r2-规避实证（erase+pass / 无引号伪 owner / 短引用篡改 / digest 漂移）均按预期红。
5. amend 血缘与自指声明（`@cb21f1fe` 基点）如实；commit ② 将登记脚本 sha256。

# ③ 请按重要性回答

⓪ 六链「判据文句」有无假归属（逐条独立核）？
① r2 两条 HIGH 的整改是否真闭环（各给一条新的反例输入或确认闭合）？
② 脚本 v3.1 的失败面之外还有哪些恒绿面（重点：nodeid 静态核验能否被同名 def 伪造、sha 核验的覆盖边界、`--expect-digest` 与 source_digest 的绑定强度）？
③ 底账内容本轮新增（review_app 503 渲染面）是否如实、quote/出处纪律是否保持？
④ `yaml-overclaim` 的 candidate-SHA 收紧与 §1 语义是否一致？还有哪些「pass 可被自证」的残余？
⑤ 其它你判断重要的问题。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`** —— 该行会被用作轮次闭合的依据。

# ⑤ 边界

只读；不连任何库；只评底账与核对脚本；不评各 owner 卡本体；不重裁 §1 判定纪律；`_bmad-output/` 下其它存档不在审查面内（上方点名除外）。

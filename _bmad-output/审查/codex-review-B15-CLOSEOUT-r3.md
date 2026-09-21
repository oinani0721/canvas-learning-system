# D-15 r3 终审（目标绑定 `d5555a18e946b4f27344a1e895590987c4199501`）

**只读边界**：未连接数据库/网络服务；未运行 pytest / pyright / openapi drift / schemathesis。只读 Git、读文件、静态解析 JSON/AST，并本地只读复跑了 `cross-lane-semantic.py`（其内部仅调用本地 `git show/diff`）。目标 commit `d5555a18` 存在且可审计。

**审计开始时 HEAD 曾为 `d5555a18`；审计期间本地 HEAD 被并发推进到 `1e907037`，origin/backup 的本地 remote-tracking ref 仍为 `d5555a18`。** 因此下面先按用户指定 SHA `d5555a18` 审计，同时把 live HEAD 漂移列为阻断。

**r2 结果闭合判定**：
- r2-H1：名义上已有 `cross-lane-semantic-FINAL = PASS`，但语义门本身对 YAML/shell/INI 有假绿面，见 H-3；不能判完全闭合。
- r2-H2：unit/contract/semantic 有 post-P9 档；openapi/pyright 没有最终树重跑档，见 H-2；只算部分闭合。
- r2-M1：汇报措辞已收窄，但 G8-7 签字与 J07 未验收仍是非 pass 项，见 M-1；不闭合。
- r2-M2：schemathesis 改为显式 skip，但范围计数与超时归因仍有矛盾，见 M-2；按“全零”口径不闭合。
- r2-M3：G4-13 台账 §二已补 `89be3d0e`/`da825921`，闭合。
- r2-L1/L6：只在部分声明面更正，最终汇报/整改说明仍留旧口径，见 M-4；部分闭合。
- r2-L2：openapi/pyright provenance 仍未闭合，并入 H-2。
- r2-L3：UNION 门被语义门取代，但新语义门有假绿面，并入 H-3。
- r2-L4/L5/L6 对应本报告 L-1/L-2/L-3，仍开放。

---

## BLOCKER

### B-1 审计期间“最终 HEAD”失稳：本地分支已被 post-d555 amend 到 `1e907037`，且相对双远端 ahead 1

- 证据：目标 `d5555a18` 之后出现 `b31361b1` → amend 为 `1e9070375759a1044d087f385423a20727dd8249`；本地 branch = `1e907037`，`origin/worktree-feature-obsidian-hybrid-dev` 与 `backup/worktree-feature-obsidian-hybrid-dev` 的本地 tracking refs 均仍为 `d5555a18`。`1e907037` 还新增了 `2026-08-30-主goal全量状态账.md:161-176` 的 B15 收口/推送登记。
- 复现思路：连续执行 `git rev-parse HEAD`、`git rev-parse refs/remotes/{origin,backup}/worktree-feature-obsidian-hybrid-dev`、`git reflog --date=iso -5`；本地与目标 SHA、远端 tracking ref 三者不再一致。
- 未被拦下的输入：在宣称最终 HEAD 后继续追加或 amend docs/ledger commit，并把新的“已推送/已收口”账写进未推送 commit。
- 对照输入：本地、origin、backup 均停在 `d5555a18`，且 reflog 在 d555 后无新 commit/amend。
- 负控输入：只创建一个 `_bmad-output` docs commit；现有“final SHA 字符串仍出现在旧证据中”的门不会阻止当前 tip 漂移。
- 门未覆盖的路径：final-HEAD quiescence / “d555 后零新 commit” / 本地 branch 与双远端 live tip 一致性。

---

## HIGH

### H-1 G8-7 终版证据包宣称已合入，但 B15 相关《车道回复 3》仍是 untracked，且内容本身列出未完成用户项

- 证据：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20-车道回复-3.md:20-24` 仍列出“③复跑、⑥成功页、思维导图触发者确认、签字”等只差用户的收口项；当前 `git status --porcelain` 显示该文件为 `??`，而 `d5555a18` tree 中不存在该路径。`d5555a18` commit message 却宣称“终版证据包”。
- 复现思路：`git status --porcelain | grep 'G8-7.*车道回复-3'` 有 untracked；`git cat-file -e d5555a18:_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20-车道回复-3.md` 失败。
- 未被拦下的输入：把承重用户回复/未完成验收清单留在工作区，不入最终 evidence manifest。
- 对照输入：该文件在 `d5555a18` 中入库，或明确登记为非 B15 资产并被移出收口面。
- 负控输入：把该文件第 4 行结论或第 20-24 行待办改成相反结论；`d5555a18` 的 G8-7 manifest/汇报不会变化。
- 门未覆盖的路径：final tree 的 B15/G8-7 evidence inventory 与 `git status B15 untracked = 0` 检查。

### H-2 “post-P9 全门复跑”声称不实：openapi/pyright 仍引用 `8a651d2a` 旧档，且无命令、`test -x`、完整 stdout/stderr 与各自 rc

- 证据：`_bmad-output/审查/evidence-b15-closeout/FINAL-HEAD-gates-20260920T181646.txt:1-8` 绑定 `8a651d2a`，只有手工摘要；`534f01d5` commit message 却称“openapi/pyright/unit/contract 均在新 HEAD 复跑并落原始日志”。P9 `89be3d0e` 之后实际改变 7 个 backend scripts/tests 文件。协议 `.claude/rules/card-batch-protocol.md:49,54` 要求承重 stdout+stderr+rc、pyright 绝对路径与 `test -x`。
- 复现思路：`git show 534f01d5 --stat` 中没有新的 openapi/pyright 原始日志；全目录只有一个 `FINAL-HEAD-gates-20260920T181646.txt`，头行是 `8a651d2a`；`git diff --name-only 8a651d2a..d5555a18 -- backend` 返回 P9 7 文件。
- 未被拦下的输入：在 P9 scripts 中引入类型/行为错误，或直接手写 `DRIFT none` / `0 errors` 摘要；旧日志不会变红。
- 对照输入：post-P9 或 `d5555a18` 代码等价树上重跑，日志头绑定新 SHA，并包含完整命令、`test -x`、stdout/stderr、rc。
- 负控输入：向 `backend/scripts/gold_set_manifest_tool.py` 插入 pyright 错误；`pyright app` 旧摘要不变，且该脚本本来也不在 `app` 范围内。
- 门未覆盖的路径：最终树 openapi/pyright 的执行 provenance、scripts 类型面、以及“证据确实在声称树上运行”的机器绑定。

### H-3 跨车道“语义等价”门对 YAML/shell/INI 使用去空白文本比较，存在假绿；输出也未钉住各 lane tip

- 证据：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic.py:4-8` 宣称语义等价；`:44-45` 对非 Python 删除全部空白，`:55-59` 对所有非 `.py` 应用该比较。实际检查面包含 YAML（如 `backend/tests/regression/gold_set_manifest.yaml`）、shell（`scripts/j01_e2e.sh`）、INI（`backend/pytest.ini`）。脚本 `:49-52` 读取 lane tip 但不输出；`cross-lane-semantic-FINAL-...txt:3,11-12` 只记录 candidate `fe19b5bb`。
- 复现思路：两个 YAML `a:\n  b: c` 与 `a: b: c` 去空白后均为 `a:b:c`，但前者可解析、后者语义/语法不同；shell 中换行也是语法边界。当前复跑虽仍 `checked=129 equiv=123 exceptions=6 verdict=PASS`，但这是 gate 能力缺口，不是严格语义证明。
- 未被拦下的输入：仅改变 YAML 缩进/换行或 shell 换行，使语义改变但去空白后相同；或在日志生成后移动 lane worktree tip。
- 对照输入：YAML 用 `yaml.safe_load` / schema-aware 比较，shell 至少 `bash -n` 加结构化 AST/字节比较，并逐 lane 输出 full tip SHA。
- 负控输入：对 `gold_set_manifest.yaml` 交付一个去空白等价但解析结果不同的候选；当前 gate 会计 `equiv` 而非 `[DIFF]`。
- 门未覆盖的路径：非 Python 格式的真实语法/语义等价、lane tip 可重复绑定、candidate 与 d555 的显式代码树等价证明。

---

## MEDIUM

### M-1 B15 仍有两个显式非 pass 验收面：G8-7 用户签字 pending，J07 未跑/转批

- 证据：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:104-114` 六个体验 checkbox 和旅程签字全未勾；`_bmad-output/审查/evidence-g87-journey/manifest.json:607-612` 为 `signoff.status=pending`、`result=partial`。`d5555a18` 台账 `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:156-157` 分别登记 G8-7“非 pass”和 J07 “not_run / SKIP / 不得写 pass”。
- 复现思路：读取上述 checkbox 与 manifest signoff，再对照用户“B/H/M/L 全零才可复核”的判据。
- 未被拦下的输入：下游把“代码/证据面收口完成”误读为用户验收完成。
- 对照输入：用户补签，或用户明确把 G8-7/J07 从 B15 验收目标中改派并以机器可读状态闭合。
- 负控输入：所有体验项仍空白，但最终通报只强调“32 卡合入”；没有机器门阻止这种阅读偏差。
- 门未覆盖的路径：用户验收状态与批次总收口状态的机器联动。

### M-2 schemathesis 面仍是显式 skip，且 skip 面积/归因登记不准确：实际 operation 是 90 而非 89，“首个 op Timeout”与原始日志相反

- 证据：`backend/tests/contract/test_openapi_contract.py:42-45` 写“93 GET − 4 = 89”；但当前 openapi 静态复算为 94 GET，减 4 个 exclude 后为 90；`schemathesis-ops-90.txt` 恰 90 行，collect manifest 中 `SchemathesisFunction` 也为 90（总 collected 92 另含 2 个非 schemathesis 测试）。`schemathesis-nonhealth-v-20260920T194546.txt:14-15` 显示 `GET /api/v1/ping` 是 FAILED，随后 `GET /api/v1/system/startup-check` 才 Timeout；同档 `:1350-1352` 却写“首个 op ping 即 Timeout”。
- 复现思路：统计 openapi GET 方法数并减去 `:81-84` 四个 exclude；再并排读取该日志第 14-15 行与第 1351 行。
- 未被拦下的输入：任一未纳入 3-file gate 的 GET response schema 回归，尤其被“89”口径漏计的第 90 个 operation。
- 对照输入：生成精确 90-operation nodeid manifest，分组执行并机器断言执行并集等于 manifest；或把 skip 作为明确不满足全零的开放项。
- 负控输入：修改一个未覆盖 GET 的 response schema；contract 3-file 与 skip 登记均不变红。
- 门未覆盖的路径：90-operation schema conformance、失败/超时的机器归因一致性。

### M-3 `d5555a18` commit message / 台账宣称 r4-r11 与 10 commits，但树内只有 r4-r10 存档，lane 范围实数 11 commits

- 证据：`d5555a18` message 写“r4-r11 复核轮”和“10 commits（d9d64ea1..34c29691）”；`git ls-tree d5555a18` 只有 `codex-review-CARD-G8-7-r4.md` 到 `r10.md`，无 r11；`git rev-list --count d9d64ea1..34c29691 = 11`。台账 `未合卡追踪台账.md:156` 也写 r4-r11。
- 复现思路：`git log -1 --format=%B d5555a18`；`git ls-tree -r --name-only d5555a18 | grep 'CARD-G8-7-r11'` 为空；`git rev-list --count d9d64ea1..34c29691` 为 11。
- 未被拦下的输入：把未落盘的 r11 复核当作证据引用，或让 commit count/轮次编号与 git 实况漂移。
- 对照输入：入库 r11 存档与 prompt，且 commit message 写真实 11-commit 范围。
- 负控输入：删除 r10 存档或把主 session 人审改称 r11；当前没有机器门发现。
- 门未覆盖的路径：commit message ↔ tree evidence ↔ `rev-list` 数量的一致性检查。

### M-4 r2-L1/L6 只做了局部口径更正；最终声明层仍留三组旧数字/旧表述

- 证据：`cross-lane-semantic-FINAL-...txt:11-12` 是 `equiv=123 exceptions=6`，但 `STATUS.md:15` 仍写 `119 equiv + 10 exceptions`。`d5555a18` 的最终汇报 `_bmad-output/第十五批-完成的卡-汇报.md:14` 仍写 D40“480 文件”和 contract“与基线逐字同”；`D-15-r1-整改说明.md:11` 也仍写“逐字同”。D40 实际 diff-tree 为 481 文件（480 `.py` + openapi timestamp），contract 实际只是红 nodeid/计数等价。
- 复现思路：并排读取 semantic FINAL 末两行与 STATUS 第 15 行；`git diff-tree --name-only -r 04eb9a9f | wc -l` 得 481；对比两份 contract 日志 rootdir/plugins/warnings/耗时并不逐字相同。
- 未被拦下的输入：读者按错误 exception 集合、错误 D40 文件数或过强的 contract 等价口径做后续裁决。
- 对照输入：在同一 commit 内同步更新 STATUS、最终汇报、整改说明和 evidence 摘要。
- 负控输入：把 semantic exceptions 从 6 改成 10 而不更新 STATUS；当前无跨文档一致性门。
- 门未覆盖的路径：声明层与机器输出的自动对账。

### M-5 `d5555a18` 树内没有最终 branch/tag 推送证据；旧推送档仍绑 `51acf6cd` 与 33 tag，新增两个 tag 的双远端状态只出现在 post-d555 未推送说明

- 证据：`push-and-tags-evidence-20260920T182427.txt:1-6` 只证明 origin/backup/local 当时为 `51acf6cd` 与 33 tag；`d5555a18` 中没有更新后的 push/tag evidence。新增 `merged-squash/card/p9-testinfra-G4-13-verdicts`、`merged-squash/card/p3-deploy-G8-7-final` 的“双远端 OK”只写在 post-d555 `1e907037` 的状态账 `:175-176`，而该 commit 本身 ahead/unpushed。
- 复现思路：在 `d5555a18` tree 中搜索新的 tag 名与 `d5555a18` push transcript；只能找到本地 tag 对象，找不到目标树内远端验证档。
- 未被拦下的输入：任一新 tag 未推、误推或远端被删；目标树内证据不会变化。
- 对照输入：`d5555a18` 内入库 `ls-remote`/push 原始输出，覆盖 branch + 35 tag 的 local/origin/backup SHA。
- 负控输入：删除 origin 上 `p3-deploy-G8-7-final`；本审计因禁网络无法发现，目标树旧证据也不变红。
- 门未覆盖的路径：远端活态 tag/branch 校验；本轮只能确认本地 remote-tracking branch refs 为 `d5555a18`，不能确认远端 tag。

---

## LOW

### L-1 r2 quarantine 全域零写盲区仍未闭合

- 证据：`backend/tests/integration/test_cypher_contract_gate.py:651-655` 自己声明 User/Node/Canvas、CONTAINS_NODE/SCORED、存量属性改写不在零写断言面；仅 Concept 与按 `record_id` Episode 被点名。
- 复现思路：让 `_replay_scoring_entry_to_neo4j` 在 `_resolve_entry_source` 返回 None 前先写 User-only、边-only、无前缀 Episode 或更新存量属性；现有断言不全红。
- 未被拦下的输入：无 gate 前缀/无 `record_id` 的 Episode、User、关系、属性更新。
- 对照输入：当前生产实现在解析失败后先返回，未见图写。
- 负控输入：对测试作用域内节点/关系/属性做完整快照与 delta。
- 门未覆盖的路径：全域图写零增量。

### L-2 replay 来源优先级矩阵仍缺 vault-vs-env 与三源同冲突

- 证据：`backend/tests/integration/test_cypher_contract_gate.py:670-716` 只测 group_id 胜 vault_id；`:719-776` 只测无 group/vault 时 env branch；没有 `{vault_id:B, env:C}` 与 `{group:A,vault:B,env:C}`。
- 复现思路：把实现顺序改为 group → env → vault；现有两个用例仍可绿，但 vault 应压 env 的场景会错。
- 未被拦下的输入：vault-vs-env 二源冲突、三源冲突。
- 对照输入：当前实现顺序为 group → vault → env。
- 负控输入：新增两个矩阵用例并断言 B / A。
- 门未覆盖的路径：完整优先级排列。

### L-3 7692 测试固定 `g21gate` 前缀，不能隔离并发运行

- 证据：`backend/tests/integration/test_cypher_contract_gate.py:89-115` 固定 `GATE_PREFIX="g21gate"`，cleanup 以全局前缀删除。
- 复现思路：两个 pytest 进程共享 7692 并发运行；B 的模块 cleanup 可删除 A 正在断言或使用的数据。
- 未被拦下的输入：多 pytest 进程/CI job 复用同一 7692；外部进程同前缀增删。
- 对照输入：顺序执行时当前 cleanup 有效。
- 负控输入：一次性 run-id 前缀，并让 seed/query/delta/cleanup 全绑定该 run-id。
- 门未覆盖的路径：并发隔离与数据所有权。

### L-4 G8-10 同一 `46984d80` 出现两个不同 source digest，且 FINAL 汇总带 `dirty_tracked=1` 但未列出脏文件

- 证据：`g810-checker-FINAL-20260920T172022.txt:1-3` 为 digest `088fdb09...`、`dirty=1/dirty_tracked=0`；`FINAL-HEAD-gates-20260920T181646.txt:10` 同 head 却为 digest `411a4175...`、`dirty=101/dirty_tracked=1`，均 rc=0。
- 复现思路：并排读取两档同 head 输出；没有 dirty-file 清单，无法解释 digest 变化和 tracked 脏项是否影响 checker 输入。
- 未被拦下的输入：在 tracked 工作区改动任意承重文件后 rerun，只要 checker 自身 rc=0，摘要仍可被读作 final tree green。
- 对照输入：同 head、`dirty_tracked=0`、同一 digest，并记录 checker ledger blob SHA。
- 负控输入：修改 G8-10 ledger 或相关 tracked 文件再跑；当前证据无法定位差异来源。
- 门未覆盖的路径：dirty-file manifest、输入 blob SHA 与 checker digest 的确定性绑定。

---

清零：否；B/H/M/L = 1/3/5/4



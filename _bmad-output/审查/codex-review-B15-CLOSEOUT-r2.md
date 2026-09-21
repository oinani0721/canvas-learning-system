## 审计绑定与只读边界

- 工作目录：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev`
- 分支：`worktree-feature-obsidian-hybrid-dev`
- 实测最终 HEAD：`fe19b5bbc7ff48f72f5f2eff31cf87852465a4e8`
- 本地 remote-tracking refs：`origin/worktree-feature-obsidian-hybrid-dev` 与 `backup/worktree-feature-obsidian-hybrid-dev` 均指向同一最终 SHA。未做 `ls-remote`/网络验证。
- tracked 工作区净；untracked 共 149 项，其中 B15 相关仅当前 0 字节 `_bmad-output/审查/codex-review-B15-CLOSEOUT-r2.md` 占位，其余为既有用户资产/研究产物。
- 全程未改文件、未连数据库或网络服务。测试/pyright/schemathesis 结论来自入库日志与静态/只读 Git 复算。
- B15 窗口 reflog 只见 commit 与 fast-forward；未见 reset/checkout/stash 破坏性移动。既有 stash 均为旧分支/旧批次。

### r1 结论先行判定

| r1 | r2 判定 |
|---|---|
| H-1 fixture 终局失绑 | **窄口径已闭合**：`46984d80..8a651d2a` 排除 `_bmad-output` 后为空，fixture blob 三方一致；但之后 P9 又引入 backend 代码面，形成新的终局绑定问题，见 H-2。 |
| H-2 107 无原始日志 | **闭合**：`e2e-7692-FINAL-107` 与 P9 后 `e2e-7692-FINAL-P9` 均 collected 107 / 107 passed。 |
| H-3 cross-lane FAIL 被人工读成 PASS | **未闭合，升级为假绿证据**：新增语义门原始日志本身就是 `FAIL(3)`，整改说明却写 PASS，见 H-1。 |
| M-1 push/tag 证据空 | **基本闭合**：33 tag 三列 SHA 与逐 tag push 转录入库；本地 remote branch refs 现亦指向最终 SHA。远端活态未复核。 |
| M-2 89 operation skip | **口径已收窄，但按“总收口全证据”仍不闭合**，见 M-2。 |
| M-3 r1 0 字节/untracked | **闭合**：r1 全文、prompt、整改说明已入库；当前 r2 占位属本轮输入。 |
| M-4 G8-7 pending 与完成语矛盾 | **未闭合**，见 M-1。 |
| L-1 D40 非 strict format-only | **未闭合**，见 L-1。 |
| L-2 openapi/pyright provenance | **未闭合**，见 L-2。 |
| L-3 UNION 判据弱 | **设计上被 AST/保序去空白比较取代**，但实际语义门未在 P9 后重跑且日志 FAIL，归入 H-1。 |
| L-4 quarantine 全域零写盲区 | **未闭合**，见 L-3。 |
| L-5 vault-vs-env 优先级缺测 | **未闭合**，见 L-4。 |
| L-6 固定前缀并发不隔离 | **未闭合**，见 L-5。 |

### 只读复算通过面

- `f26e6a85` 只改 `.claude/rules/card-batch-protocol.md`；G1-1、G1-3、§2.4.2、§3、§6 条款均在最终协议中。
- `69d26ed5` 的 `docs/release-evidence/slo-manifest.yaml:5-15` 为 `slo-manifest@2026-09-20-r2` / `locked`，记录用户口令与逐项裁定；tag `merged-squash/card/p10-docs-R-SLO-locked` 指向该 SHA。
- `2bdbc685`、`d0e42bc4`、`4f6d17ca` 均只改 `backend/tests/integration/test_cypher_contract_gate.py`；与 `fallback_sync_service.py:619-646` 的 group_id > vault_id > env > quarantine 顺序一致。
- `0400d848` 381 个路径全部在 `_bmad-output/**`，非 `_bmad-output` product diff 为 0；r21 存档自报且登记 `B/H/M/L = 0/0/0/0`。
- D40：480 个 `.py` 中仅 `test_security_p0_vulnerabilities.py` AST 不等，仍只对应 docstring 行尾空白；未发现 Python 行为语义变化。
- openapi 静态计数复算：paths=199、schemas=357。
- unit nodeid 差集复算：33→32，引入 `[]`，修复仅 `test_vault_install_manifest.py::test_digest_is_injective_over_adversarial_leaves`。
- contract 3 文件红 nodeid 集合复算不变：2 既有红 / 75 passed。
- 台账 §二第 286–317 行恰 32 张卡；卡级 squash SHA 均存在并可达最终 HEAD。
- 7692 四文件 P9 后日志为 107 passed / 0 failed。
- regression P9 后日志为 2289 passed / 6 skipped / 1 xfailed。

---

## BLOCKER

无。

---

## HIGH

### H-1：r1-H3 未闭合；新增“语义等价机器门”原始 verdict 是 `FAIL(3)`，整改说明和最终 commit 却宣称 PASS

- 证据：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic-20260920T183601.txt:13-19` 明确列出 3 个 P9 YAML `[DIFF]`，并给出 `checked=129 equiv=116 exceptions=10 undecided_diff=3`、`verdict=FAIL(3)`。但 `_bmad-output/审查/evidence-b15-closeout/D-15-r1-整改说明.md:9` 写成 `equiv=119 ... verdict=PASS`；`STATUS.md:15` 与 `fe19b5bb` commit message 也写“机器 PASS”。
- 复现思路：直接读取同一最终 HEAD 中两份文件并比较第 9/15 行与语义门第 18–19 行；无需运行任何服务。
- 未被拦下的输入：三个 YAML 中任一 query、期望集、阈值或 source 语义被 P9 合入改变，当前归档不会变绿，声明层仍可写 PASS。
- 对照输入：应有 P9 合入后在 `fe19b5bb` 或其代码等价树上重跑的日志，且 `verdict=PASS`、计数与声明逐字一致。
- 负控输入：在 `memory_gold_set.yaml` 改一个 `expect_any` 或 query 后不重跑；现有 `FAIL(3)` 未被消费，STATUS 仍可照抄 PASS。
- 门未覆盖的路径：P9 合入后的语义等价复算。并且 `cross-lane-semantic.py:49-54` 只记录 candidate HEAD，不记录各 lane 当前 tip SHA；lane worktree 后续移动会使重跑对象漂移。
- 判定：**FAIL / 假绿**。这不是“解释差异”，而是承重机器输出与收口声明直接相反。

### H-2：P9 在多数“FINAL-HEAD”门之后引入 7 个 backend 文件，最终 tip 的门覆盖声明失真

- 证据：`FINAL-HEAD-gates-20260920T181646.txt:1` 绑定 `8a651d2a`；`cross-lane-semantic-...txt:3` 也绑定 `8a651d2a`。其后 `89be3d0e` 修改：
  - `backend/scripts/gold_set_manifest_tool.py`
  - `backend/scripts/run_memory_retrieval_regression.py`
  - `backend/scripts/run_vault_retrieval_regression.py`
  - `backend/tests/regression/gold_set_manifest.yaml`
  - `backend/tests/regression/memory_gold_set.yaml`
  - `backend/tests/regression/test_gold_set_manifest_g413.py`
  - `backend/tests/regression/vault_gold_set.yaml`
  
  合计约 2505 insertions / 492 deletions。`STATUS.md:10-15` 却写成“全部在 8a651d2a / P9 合入后 da825921 复跑”；实际 P9 后仅见 7692 与 regression 目录级日志，openapi/pyright/unit/contract/semantic 均无最终树重跑证据。
- 复现思路：`git diff --name-only 8a651d2a..fe19b5bb -- backend` 返回上述 7 文件；再按时间与日志头部核对，openapi/pyright/semantic 均绑旧 SHA。
- 未被拦下的输入：在 P9 新增脚本中引入语法/类型/行为错误，只要 regression 点名面不红，旧 `pyright app`、unit、contract 日照仍可被引用为终局门。
- 对照输入：应在 `fe19b5bb` 重跑全部承重门；或入库机器证明“旧门覆盖面自 8a 后 path-identical，P9 变更面由 regression/7692 全覆盖”。
- 负控输入：向 `gold_set_manifest_tool.py` 插入一个 pyright 错误；`FINAL-HEAD-gates` 的 `pyright app` 摘要不变。若插入 regression 不覆盖的 helper 分支，regression 门也可能不变。
- 门未覆盖的路径：最终树的 scripts 类型面、unit/contract 的 HEAD 自证、P9 后 cross-lane 语义等价。
- 判定：**FAIL**。`backend/app` 与 openapi 面 static 上未变，因此未按 BLOCKER 处理；但按 r1-H1 同一“最终代码树绑定”标准，不能称 FINAL-HEAD 全门闭合。

---

## MEDIUM

### M-1：r1-M4 未闭合——G8-7 用户旅程签字仍 pending，汇报层仍写“B15 总收口完成”

- 证据：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:92-102` 六个体验 checkbox 与旅程签字均为 `[ ]`，且明示未勾选则 `manifest.signoff.status` 保持 pending；`_bmad-output/第十五批-完成的卡-汇报.md:14` 却使用“B15 总收口完成”。`STATUS.md:25-27` 仍把 G8-7 列为待签字。
- 复现思路：读取 UAT 签字区 checkbox，再读取最终汇报第 14 行。
- 未被拦下的输入：用户未认可完整旅程时，自动化汇报的“总收口完成”被下游读成验收完成。
- 对照输入：应写成“代码/证据面收口，G8-7 用户签字未闭合”，或用户补签/显式 SKIP 后再升格。
- 负控输入：把六项 felt-sense 全部留空但保留完成语；当前没有机器门阻止。
- 门未覆盖的路径：用户旅程认可与 manifest signoff 状态。
- 判定：**PARTIAL/FAIL**。

### M-2：89-operation schemathesis 面仍是显式 skip；若按“总收口”标准，必须至少有分组实跑证据

- 证据：`STATUS.md:7,16` 明示 89 操作未跑全量；`backend/tests/contract/test_openapi_contract.py:95-100` 对每个 operation 生成 10 个 examples；早前 `contract-4files-dbup-20260920T150040.txt:14-22` 已在多个 health operation 上失败后中断。
- 复现思路：检查 evidence 目录无 89-operation 完整汇总；3-file gate 排除了该文件。
- 未被拦下的输入：任一未被 3-file 覆盖的 GET response schema 回归。
- 对照输入：89 个 operation 的完整执行汇总、失败归因与最终 HEAD 绑定。
- 负控输入：篡改一个未被 3-file 覆盖的 GET response schema；当前收口门不变红。
- 门未覆盖的路径：89-operation schema conformance。
- 最小可行执行口径：
  1. 在最终 HEAD `pytest --collect-only -q tests/contract/test_openapi_contract.py`，落 nodeid manifest，并机器断言恰好 89 个 operation。
  2. 不用模糊 `-k`，按精确 nodeid 分组，例如 9 组 × ≤10 operations。
  3. 每组独立进程执行，外层 `timeout`（10-op 组建议 ≥20 分钟），固定 seed/venv/cwd，捕获 stdout+stderr、selected count、HEAD、rc、跑前跑后 backend 清洁状态。
  4. 任何红项先归因 W4/环境或真实 schema failure；不能把超时/连库红直接记为 contract pass。
  5. 所有组汇总后机器核对“执行 nodeid 并集 = collect manifest”，再谈闭合。
- 判定：**PARTIAL**。作为登记过的范围限制是诚实的；作为 B15 总收口全证据面，不足以清零。

### M-3：G4-13 台账 §二 与 git/§一.b 矛盾，仍说 P9 后续加固“未合入本批”

- 证据：`未合卡追踪台账.md:158` 说 r3–r26 已随 `89be3d0e` 合入；同文件 `:314` 却写“车道后续加固（r3–r15）未合入本批”。最终 git 实况是 `89be3d0e` 在本批主干。
- 复现思路：比较同一台账 §一.b 与 §二的 G4-13 行，再执行 `git merge-base --is-ancestor 89be3d0e fe19b5bb`。
- 未被拦下的输入：读者按 §二忽略 P9 工具加固与用户裁定面，或误以为批内只含 r2。
- 对照输入：§二 G4-13 行应补充“后续补关 squash `89be3d0e` / r3-r26 / 尾档 `da825921`”。
- 负控输入：从 `89be3d0e` 删除或替换部分加固代码；当前 §二旧描述不会产生机器红灯。
- 门未覆盖的路径：台账 §一.b、§二 与 git ancestor 的一致性检查。
- 判定：**PARTIAL**。

---

## LOW

### L-1：r1-L1 未闭合——D40 不是 strict format-only；实际 481 文件，唯一非 `.py` 是 openapi 生成时间

- 证据：`04eb9a9f` diff-tree 为 480 `.py` + 1 JSON；`backend/openapi.json:15852` 的 `x-generated-at` 从 `2026-09-20T10:52:34...` 变为 `2026-09-21T00:18:19...`。`d40-format-...txt:2-7` 只登记 480。
- 复现思路：`git diff-tree --no-commit-id --name-only -r 04eb9a9f | grep -v '\.py$'` 返回 `backend/openapi.json`；两 blob 顶层 JSON 差异仅该 metadata。
- 未被拦下的输入：把生成时间或其他 openapi metadata 混入 style commit。
- 对照输入：commit message 应写 481 文件并说明 metadata 再生，或 strict 门拒绝非 ruff 文件。
- 负控输入：修改 openapi 非 timestamp metadata；format-only 声明本身不红。
- 门未覆盖的路径：D40 的文件类型/非 ruff hunk 拒绝。
- 判定：**PARTIAL**。

### L-2：r1-L2 未闭合——openapi/pyright FINAL 摘要缺命令、`test -x`、完整 stdout/stderr 与 rc 自证

- 证据：`FINAL-HEAD-gates-...txt:2-8` 只有结果摘要和文字说明；协议 `.claude/rules/card-batch-protocol.md:49` 要求承重裁判 stdout+stderr+末行 rc，`:54` 要求 pyright 绝对路径与 `test -x` 自证。
- 复现思路：读取 FINAL-HEAD gate 文件，找不到原始命令行与每命令 rc。
- 未被拦下的输入：错误二进制、错误 cwd、命令失败后被手工摘要成通过。
- 对照输入：应归档命令全文、`test -x` 输出、pyright/openapi 原始汇总和各自 rc。
- 负控输入：把 pyright 路径换成不存在路径但手写 `0 errors`；当前摘要无法发现。
- 门未覆盖的路径：命令 provenance 与退出码。
- 判定：**PARTIAL**。

### L-3：r1-L4 未闭合——quarantine 拒写路径的全域零写仍有明确盲区

- 证据：`backend/tests/integration/test_cypher_contract_gate.py:651-667` 自己声明 User/Node/Canvas、CONTAINS_NODE/SCORED、存量属性改写不在零写断言面；只查 Concept、按 `record_id` 的 Episode，以及 Node/Canvas 数量 delta。
- 复现思路：让 `_replay_scoring_entry_to_neo4j` 在 `_resolve_entry_source` 返回 None 前先写 random-id Episode、User-only、关系-only 或更新存量属性；现有探针不全红。
- 未被拦下的输入：无 gate 前缀/无 `record_id` 的 Episode、User、边、属性更新。
- 对照输入：当前生产实现 `fallback_sync_service.py:503-506` 在解析失败后先返回，未见图写。
- 负控输入：对测试前缀的 Node/User/Episode/关系总量与属性快照做前后 delta。
- 门未覆盖的路径：全域图写零增量。
- 判定：**PARTIAL**。

### L-4：r1-L5 未闭合——来源优先级矩阵缺 vault-vs-env 与三源同冲突

- 证据：现有矩阵只有 `test_replay_entry_group_id_beats_vault_id`（`:670-706`）和 env-only（`:719-767`）；生产顺序在 `fallback_sync_service.py:627-644` 为 group → vault → env。
- 复现思路：把实现改成 group → env → vault；现有 group/vault、env-only 用例仍可绿，漏掉 `{vault_id:B, env:C}` 应落 B。
- 未被拦下的输入：vault-vs-env 二源冲突、`{group:A,vault:B,env:C}` 三源冲突。
- 对照输入：当前实现顺序正确。
- 负控输入：新增两个冲突矩阵。
- 门未覆盖的路径：完整优先级排列。
- 判定：**PARTIAL**。

### L-5：r1-L6 未闭合——固定 `g21gate` 前缀与共享 7692 不能隔离并发运行

- 证据：`backend/tests/integration/test_cypher_contract_gate.py:89-115` 定义固定 `GATE_PREFIX` 与全局 cleanup 查询。
- 复现思路：同一 7692 上并发跑两个该文件进程，B 的 cleanup 可删除 A 正在断言或使用的前缀数据。
- 未被拦下的输入：多 pytest 进程/CI job 复用同一 7692；外部进程同前缀增删。
- 对照输入：顺序执行时当前 function/module cleanup 有效。
- 负控输入：一次性 run-id 前缀，并把 seed、查询、delta、cleanup 全绑定该 run-id。
- 门未覆盖的路径：并发隔离与数据所有权。
- 判定：**PARTIAL**。

### L-6：contract“与基线逐字同”是过头表述；实际只是红 nodeid 集合/计数等价，完整日志并不逐字相同

- 证据：基线 `contract-3files-20260920T151657.txt:3-7` rootdir 为 `batch15-integ`、插件含 timeout；终局 `contract-3files-FINAL-20260920T181823.txt:3-7` rootdir 为 feature、插件无 timeout。两文件 `cmp` rc=1，且 warning 数/耗时不同。
- 复现思路：`cmp` 两份日志；只有 FAILED nodeid 集合均为同 2 条、总计均为 2 failed / 75 passed。
- 未被拦下的输入：新增 warning、失败正文变化、环境插件差异会被“逐字同”口径掩盖。
- 对照输入：应写“红 nodeid 集合与 passed/failed 计数相同”，或用规范化机器 diff 证明比较面。
- 负控输入：改变失败原因文本但保持 nodeid；当前声明无法机器发现。
- 门未覆盖的路径：日志级等价口径。
- 判定：**PARTIAL**。

---

清零：否；B/H/M/L = 0/2/3/6



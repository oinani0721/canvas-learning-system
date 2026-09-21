只读 r7 终审完成；本轮未改文件、未连接数据库/网络服务。完整 `cross-lane-semantic2.py` 主跑会为 `.sh` 比较创建 temporary file，为严格遵守“只读”，我没有整跑该脚本；改为逐对象复算其 Git/blob/AST/结构化等价核心，并实跑其 `--self-test` 与只读 G8-10 checker。

## 绑定与独立复算摘要

- **HEAD 绑定成立**：`git rev-parse HEAD = 9b96e5a6492cd4564395ead786a8cbe390e98fe1`；branch 为 `worktree-feature-obsidian-hybrid-dev`；本地 `origin/*` 与 `backup/*` tracking refs 也均为同一完整 SHA。你提供的活态 `ls-remote` transcript 与本地 refs 不冲突；本轮未自行连网复证。
- **工作区**：tracked dirty = 0；untracked = 102。与 `g810-clean-rerun-L4-20260920T202805.txt:16-24` 的 103 项相比，唯一差异是其中 `_bmad-output/审查/codex-review-B15-CLOSEOUT-r3.md` 已由后续 commit 入库；无新增 B15 相关 untracked 证据。
- **最终档 docs-only 成立**：`9b96e5a6` 恰 14 文件，全部在 `_bmad-output/**`；非 `_bmad-output` diff 为 0。`1e907037..9b96e5a6` 非 `_bmad-output` 仅 `backend/tests/contract/test_openapi_contract.py:42-46` 注释变化，父/当前 AST 相等。
- **r6-H1 闭合**：`cross-lane-semantic2.py:50-54` 任一侧空 blob 生成 failure；`:191-195` 在 exception 前执行并 `continue`；`:211` 将 `empty_n==0` 纳入 clean。本轮实跑 `--self-test`，三 case 全 OK、rc=0。
- **r6-M1 大体闭合但有残留**：`b15-freeze-exclusions.json` 由 `cross-lane-semantic2.py:56-73` 解析；缺 registry/空 allowlist 红；`:165-179` 区分 P3 docs-drift 与未登记 lane tip drift。独立复算十个 lane：非 P3 full tip 均等于 pin，P3 `32a405a4..1726b695` code-face diff = 0；`34c29691..1726b695` 排除 `_bmad-output` 后亦为 0。残留见下方 M-1。
- **r6-L1 闭合**：四个 negative 脚本与主脚本各自恰一行差异：badbase 改 BASE、drift 改 p3 pin、tipdrift 改 p1 pin、missingkey 删 p1 key；本轮重算 SHA256 与 `cross-lane-semantic2-v23-negcontrols-20260920T212852.txt:13-14,64-65,90-91,119-120` 一致。全文负控无省略号，badbase `failures=21/rc=1`、drift/tipdrift/missingkey 均失败。
- **语义等价核心独立复算**：在最终 HEAD 与十个 lane branch refs 上重算，per-lane files = 17/15/5/7/32/11/6/15/16/5，总计 129；结果 `equiv=123 exceptions=6 diff=0 missing=0 empty=0`，与 `cross-lane-semantic2-v23-20260920T212852.txt:20-21` 一致。
- **门证据**：
  - openapi：当前 JSON 实算 paths=199、schemas=357；日志 `openapi-pyright-postP9-20260920T202117.txt:4` 为 `DRIFT: none`，pyright `:134` 为 `0 errors, 83 warnings`，绑定 `1e907037`。
  - unit：基线 33 红 vs final 32 红，canonical nodeid 差集仅移除 `test_digest_is_injective_over_adversarial_leaves`；汇总见 `unit-FINALPOSTP9-20260920T192431.txt:1006`。
  - 7692：`e2e-7692-FINAL-P9-20260920T183808.txt:75` = 107 passed。
  - contract：三档红 nodeid 集合完全相同；final `contract-3files-FINALPOSTP9-20260920T192431.txt:2040` = 2 failed / 75 passed。
  - regression：`regression-FINAL-P9-20260920T183808.txt:194` = 2289 passed / 6 skipped / 1 xfailed。
  - G8-10：本轮在最终 HEAD 只读复跑 checker，先探针后回填 actual digest；最终 `chains=6 obj07=5 failures=0 source_digest=expect_digest=ef13b8ede259f442a2c0451be733ca57 head=9b96... dirty_tracked=0 dirty_untracked=102 rc=0`。
  - schemathesis：`schemathesis-ops-90.txt` 90 行、collect manifest 90 个 `SchemathesisFunction`；`schemathesis-nonhealth-v-20260920T194546.txt:1349-1363` 明确按范围限制 skip，不称全量 pass。
- **收口对象**：台账 §二第 290-321 行为 32 张卡，322-323 为协议/集成分外行；35 个本批 tag 的 local 对象与 `push-and-tags-evidence-20260920T203021.txt:8-43` 逐项一致。P9 金集实算 75+28=103、0 pending，manifest `status=approved`。R-SLO manifest 为 locked/r2。D40 为 480 `.py` + OpenAPI timestamp；raw AST 有已知 1 文件 docstring 尾随空白差异，r4 口径为归一化后全等，非隐藏事实。
- **破坏性痕迹**：branch reflog 近段仅正常 commit、fast-forward 与已登记的 `b31361b1 -> 1e907037` amend；未发现 reset/force/checkout/stash 类破坏性移动。G8-7 主干签字仍是显式 pending / 非 pass，已由台账 `未合卡追踪台账.md:156` 登记为第十六批补签；本轮按你给定的 B15 冻结/复核边界不把它当隐藏假绿，但不能将其表述为产品验收已完成。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

### M-1 semantic v2.3 的“未登记 lane tip 精确相等”实际只比较 8 位前缀，可构造同前缀 docs-only commit 绕过冻结口径

- **位置**：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:35-38,163-177`；对应声称见 `_bmad-output/审查/evidence-b15-closeout/D-15-r6-整改说明.md:6`。
- **复现思路**：脚本先取得 full tip，再截成 `tip_full[:8]`，与同样只有 8 hex 的 `CODE_TIPS[pin]` 做字符串相等；因此“精确相等”实为 32-bit 前缀相等。
- **未被拦下的输入**：在 p1/p2/p4–p10 任一未登记 lane 上制造一个 full SHA 前 8 位与 pin 相同但不等于 pin 的 `_bmad-output/**`-only commit；`tip_drift=False`、`code_drift=0`，不会输出 `[FAIL] tip-drift`。
- **对照输入**：当前 p1 full SHA 正是 `39144558946094707a5223e4cedbf599e73b2ba7`；普通不同前缀的 docs-only lane commit 会红。
- **负控输入**：`cross-lane-semantic2-v23-negcontrols-20260920T212852.txt:90-117` 的 tipdrift 用 `deadbeef` 这类显式不同前缀，只证明普通漂移会红，不覆盖同 8 位前缀碰撞。
- **门未覆盖的路径**：未保存/比较 40-hex pin，也未将 `rev-parse pin^{commit}` 的 full SHA 与 lane full tip 比较；code-drift 缓解代码面漂移，但不能证明未登记 lane 的冻结 tip 身份。

## LOW

### L-1 冻结登记的 `guard` 元数据仍写 semantic v2.2，与最终 v2.3 执行面不一致

- **位置**：`_bmad-output/审查/evidence-b15-closeout/b15-freeze-exclusions.json:15`；对照 `_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:2` 与 `STATUS.md:15` 均为 v2.3。
- **复现思路**：逐字读取当前 freeze registry，`guard` 仍声明 “semantic v2.2”，而最终入库并复跑的执行脚本是 v2.3；读者会按 v2.2 的旧 empty-blob 语义理解冻结监控。
- **未被拦下的输入**：信任 `guard` 字段的读者或后续工具选择/审计 v2.2 语义，误以为 empty blob fail-open 仍是当前守卫行为。
- **对照输入**：当前主脚本 `:50-54,191-195,211` 与 `--self-test` 输出均证明 v2.3 空 blob fail-closed。
- **负控输入**：把 registry 的 `guard` 改成 v2.3 后应与脚本/STATUS 一致；当前无该机器一致性负控。
- **门未覆盖的路径**：semantic 脚本只解析 `excluded_faces[]`，不校验 `guard` 字段与执行脚本版本/SHA 的一致性。

清零：否；B/H/M/L = 0/0/1/1



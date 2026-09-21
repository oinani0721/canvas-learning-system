## 绑定与只读复核摘要

- 绑定通过：`HEAD = 9d799e226b80ee8e9d133de33e38ae9c641ba6f0`；本地 `origin/*`、`backup/*` tracking refs 同 SHA。按约束未连数据库/网络，采信用户提供的 23:08:51 活态 `ls-remote` 自证。
- tracked 工作区干净：`git diff` / `git diff --cached` 均 exit 0；仍有用户既有 untracked 资产，未见 B15/D-15/G4-13/G8-10/J07 相关未跟踪收口产物。
- r11 三项指定整改均真实落盘：
  - 台账 `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:24` 已改为 J07 18:23 已开、旧 SKIP 口径作废；
  - `_bmad-output/第十五批-完成的卡-汇报.md:15` 已由「上行 18:02」改为「上行 17:50」；
  - `_bmad-output/审查/evidence-b15-closeout/STATUS.md:46` 已改为「除 D-15 终审进行中外均已执行」；
  - `git diff 96835a44..9d799e22` 仅 7 个 `_bmad-output/**` 文件，另含 r11 review / remediation / prompt 入库。
- 代码/文档面分离复算通过：`1e907037..9d799e22` 非 `_bmad-output` 仅 `backend/tests/contract/test_openapi_contract.py` 注释差；`a6303136..9d799e22` 每个 commit 非 `_bmad-output` 改动数均为 0。
- 门证据复算通过：
  - OpenAPI 当前 JSON：paths=199、schemas=357、operations=211、GET=94；与 `DRIFT none` 证据一致。
  - unit：基线 33 → 终局 32；canonical set-diff introduced=0，removed 唯一为 `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`。
  - 7692 四文件：`collected 107 / 107 passed`。
  - contract 3 非 pact：两档红 nodeid 集合同为 `test_node_id_patterns.py::test_pattern_matches_json_schema` 与 `test_health_contract.py::test_health_contract[GET /api/v1/health]`，均为 2 failed / 75 passed。
  - G8-10 在最终 HEAD 只读两跑：actual/expect 同为 `a576d706967a66284391909bf0dd0514`，`chains=6 obj07=5 failures=0`，head 精确为 `9d799e22…`，`dirty_tracked=0`。
  - semantic v2.4 在最终 HEAD 复跑：`checked=129 equiv=123 exceptions=6 undecided_diff=0 missing=0 empty=0 lane_empty=0 failures=0 verdict=PASS`；6 个负控档案均 `rc=1`。
  - D40 `04eb9a9f`：481 文件 = 480 `.py` + `backend/openapi.json` 时间戳；hook exclusion 档含 hook 定义、2×F821 原始输出、两处报错父子 AST/名次证明、format check rc=0。
  - 32 卡台账行均在最终主干祖先链上；35 个 B15 merged-squash tag 本地可解，push/tag 档为 35/35 OK、mismatch=0。

# BLOCKER

无。

# HIGH

无。

# MEDIUM

### MEDIUM-1 J07 已开窗的终态没有同步到主 UAT / release manifest，主验收面仍写成「未授权、前置未发生」

- **位置 / SHA**：
  - `_bmad-output/验收单/UAT-CARD-G6-13-J07-2026-09-20.md:5`、`:29-33`、`:82`、`:122-124`、`:183`、`:207-208`
  - `docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json:4`、`:10`、`:106-112`、`:303-310`
  - 对照终态：`_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:157`、`_bmad-output/审查/evidence-b15-closeout/STATUS.md:41`、`_bmad-output/第十五批-完成的卡-汇报.md:15`
  - 陈旧 UAT/manifest 来自 `6fd4da95`；J07 开窗登记来自 `1e907037`，r11 终档为 `9d799e22`。r11 的同类排查范围只写到状态账：`_bmad-output/审查/evidence-b15-closeout/D-15-r11-整改说明.md:5`。
- **复现思路**：读最终树的主 UAT 与 J07 manifest，仍看到「口令未给出」「主 session P5-A/P5-B 合入部署前置未发生」「用户步骤全部 not_run」；但同一最终树的权威台账、STATUS 与汇报均写「J07 窗口 2026-09-20 18:23 已开，前置四查通过，Day-0 进行中」。
- **未被拦下的输入**：第十六批执行者若从 J07 主 UAT / release manifest 起步，会误判窗口从未授权、live 部署前置从未满足，从而重复请求口令、重开 Day-0，或丢弃已开始的跨日窗口。
- **对照输入**：G4-13 主 UAT 顶部有终态勘误指针，明确正文历史口径不代表终态；J07 UAT/manifest 没有等价的 superseding/correction 指针。
- **负控输入**：`git grep '18:23' HEAD -- UAT-CARD-G6-13-J07-2026-09-20.md docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json` 为 0；同文件 `grep '未授权'` 多处命中。二者与台账 `:157` 不能同时作为当前权威口径。
- **门未覆盖的路径**：semantic/G8-10/OpenAPI/unit/contract 都只校验代码或各自证据链，不交叉校验 J07 UAT/manifest 的授权与前置状态是否被台账/STATUS 终态 supersede。

# LOW

### LOW-1 J07「前置四查」只有台账与 commit message 断言，最终 tracked 树没有原始输出档

- **位置 / SHA**：`_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:157` 断言「live 5/5 == 车道验证版 / 容器 StartedAt / :05 档 / 8011 GET」；`1e907037` commit message 重复同一断言，但 `git show --name-status 1e907037` 只改台账与状态账两个文档。车道契约 `_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P5-C.md:26` 要求 launchd/log 与 `docker ps` 等开窗前置证据存档。
- **复现思路**：在最终 tracked 树中精确检索 `live 5/5`，只命中台账 `:157`；检索 `StartedAt` 只命中其他 dogfood 协议/审查文档；J07 收口证据目录没有对应的原始 preflight 输出。
- **未被拦下的输入**：一条伪造、时间错误或只部分完成的 preflight 结论，只要写进台账句子，即可通过现有收口门；后续复审者无法从仓库对象复核 18:23、容器启动时间、:05 档或 8011 GET。
- **对照输入**：R-SLO 有锁版输入/输出与 manifest；G4-13 有 `gold_set_manifest.yaml` 103/103 与 signed adjudication；G8-7 有终版证据包。J07 开窗前置四查目前缺少同等级原始对象。
- **负控输入**：把台账中的四查结果任意改错或删除原始时间戳，semantic、G8-10、OpenAPI、unit、contract 均不会红。
- **门未覆盖的路径**：没有机器门要求「J07 状态 = 已开窗」时必须存在 live 版本一致性、容器 StartedAt、launchd :05、8011 GET 的可复核 artifact；该状态只靠文档交叉一致性人工维护。

清零：否  
B/H/M/L = 0/0/1/1

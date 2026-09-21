# B15-CLOSEOUT 状态（2026-09-20 17:40 · 主 session · 候选树已就绪）

## 候选树就绪（历史阶段快照：tip 6819f74e，树净；全部门已跑）——已由 ff-only + 收尾登记取代
- 32 卡全合（G8-10 squash `0400d848` = 24 lane commits，r21 绑 67db0c61 = B/H/M/L 0/0/0/0）。
- 协议回写 `f26e6a85`；R-SLO 锁版 `69d26ed5`（用户口令+签字）；集成修复 `2bdbc685`/`d0e42bc4`/`4f6d17ca`（7692 门新契约）；底账重锚 `62151cf1`/`46984d80`；D40 `04eb9a9f`；台账/总账 `2d6d9abf`；复核存档 `22f68228`；终证据 `6819f74e`。
- 终跑门（全部在最终 tip）：openapi `DRIFT: none`；pyright `app` **0 errors**；tests/unit **只减**（32 vs 基线 33，0 引入/1 修）；**7692 四文件 107 passed**；contract 3 文件 = 2 既有红/75 passed（红 nodeid 集合/计数与基线等价）；G8-10 checker failures=0 rc=0。
- schemathesis 面（test_openapi_contract.py 90 操作）本机 ≈2 分钟/条 → 显式 skip 登记（未跑全量）。


## 终局门（全部在 8a651d2a / P9 合入后 da825921 复跑，原始日志已入库）
- openapi `DRIFT: none (paths=199 schemas=357)`；pyright `app` **0 errors**（绝对路径 + nvm node 自证；feature 树 venv 无 pyright）。
- tests/unit：**只减**（32 vs 基线 33；0 引入 / 1 修 = `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`〔r8-L2 勘误；r1–r7 存档中 digest 测试归因为误〕）——**含 node 相关 33 条的两次跑**：homebrew node 崩（llhttp 9.3 缺）致 65 红的跑档亦入库并归因；nvm node v24.16.0 复跑 = 32。
- 7692 四文件：**107 passed / 0 failed**（FINAL-107 原始日志）；contract 3 非 pact：2 既有红 / 75 passed（红 nodeid 集合与计数与基线等价）。
- tests/regression 目录级（P9 合入后）：**2289 passed / 6 skipped / 1 xfailed，rc=0**。
- G8-10 checker：候选/主干树 failures=0 rc=0；语义等价机器门 **v2.4.1** verdict=PASS（129 文件：122 equiv + **7** 声明例外〔含 J07 manifest 收口期修正，r13-B1 登记〕；missing=0/empty=0/lane_empty=0/failures=0）——fail-closed（git rc + 退出码 + 空 blob 即红 + 计数下限 + **40-hex 全 SHA pin**〔8 位前缀不豁免〕+ P3-only docs-drift 白名单〔解析 `b15-freeze-exclusions.json`〕）；`--self-test` + **6 个 one-line 变异负控**（badbase/drift/tipdrift/missingkey/shortpin/prefixcollision）全文入库。
- **schemathesis 90-operation 面：显式 skip 登记**（本机 ≈2 分钟/op，全量不可行）——收口不表述为“全门已跑”。
- J07 开窗前置证据补档：`j07-window-open-preflight-recapture-20260920T2326.txt`（r12-L1 处置；5/5 部署一致 + docker StartedAt + :05 档 + 8011 GET 200；原 18:23 原始档缺失已登记）。
- D40 `04eb9a9f`：format-only（480 `.py` + openapi 时间戳）；`LEFTHOOK_EXCLUDE=python-lint` 归因证据 = `d40-hook-exclusion-evidence-20260920T225429.txt`（协议 §2.3：hook 原始输出 2×F821 rc=1 + 父子 AST 全等/名次相同 + `ruff format --check` 复跑 rc=0）。
- 推送：分支 local=origin=backup 逐 commit 对齐；`83a280db` 的 branch push 自证 = `branch-push-verify-20260920T203135.txt`（local/origin/backup 三列 + ls-remote 活态）；**35 tag 逐个三列 SHA 全 OK**（`push-and-tags-evidence-20260920T202239.txt` + `push-and-tags-evidence-20260920T203021.txt`）。
- 冻结声明（r6 前置）：B15 面 = 主干冻结档；P3 lane 冻结后 docs-only 证据推进（32a405a4→ec9845fa→80665fc1→…）**显式排除**（`b15-freeze-exclusions.json`），登记第十六批；semantic v2.4 以 40-hex 全 SHA pin 监控（仅登记工作树容忍 docs-only 前进；未登记车道全 SHA 精确相等；代码面异动即红）。
- 注：代码面门共绑 `1e907037`（openapi/pyright post-P9）与 P9/8a651d2a 树；`1e907037..83a280db` 的 tracked 差异全部在 `_bmad-output/**`（docs-only）；r4/r5 两轮整改的代码面改动累计 = `backend/tests/contract/test_openapi_contract.py:42-46` 注释行（89→90 / 93→94 GET、206/117→211/121 口径），行为零变更（schemathesis 面仍显式 skip；contract 3-file 门不含该文件）。

## D-15 轮次
- r1（绑 51acf6cd）：B0/H3/M4/L6 → 处置见 `D-15-r1-整改说明.md`（H-1 fixture 回退 / H-2 107 原始日志入库 / H-3 语义门 / M-1 推送证据 / M-2 口径收窄 / M-3 存档入库）。
- r2（绑 fe19b5bb）：B0/H2/M3/L6 → 语义门 v2、post-P9 全门复跑入库、口径更正（见 `D-15-r1-整改说明.md` + `cross-lane-semantic2-*.txt` + `openapi-pyright-postP9-*.txt` + `FINAL-HEAD-gates-*`）。
- r3（绑 d5555a18）：B1/H3/M5/L4 → 整改见 `D-15-r3-整改说明.md`（推送对齐 / 车道回复-3 入库 / post-P9 openapi+pyright 原始档 / 语义门 v2 / M-2~M-5 口径 / 35 tag 刷新）；**r3 复核存档已入库**。
- r4（绑 `83a280db`）：**B0/H1/M2/L2**（H1=post-final G8-7 用户回复-3 漂移；M1=总账 §六口径；M2=r4 prompt / tip push transcript 未入库；L1=源码注释 89/93；L2=semantic blob 未查 rc）→ 整改见 `D-15-r4-整改说明.md`（用户回复-3+UAT 链接入库 / 总账口径 / prompt+push transcript 入库 / 注释 89→90 / semantic v2.1 fail-closed）；**r4 复核存档已入库**。
- r5（绑 `85a157dc`）：**B1/H1/M0/L2**（B1=P3 lane 冻结后证据面推进/未显式排除；H1=semantic 仍 fail-open；L1=源码注释 206/117 残余；L2=旧 push 档 tag 分解公式）→ 整改见 `D-15-r5-整改说明.md`（P3 面显式排除冻结档 + semantic v2.2 fail-closed（含两负控）+ 注释 211/90/121 + tag 分解勘误）；**r5 复核存档已入库**。
- r6（绑 `a6303136`）：**B0/H1/M1/L2**（H1=empty blob 未 fail-closed；M1=冻结容忍未限定 P3；L1=负控脚本/全文未入库；L2=freeze JSON 措辞）→ 整改见 `D-15-r6-整改说明.md`（semantic v2.3 + 4 变异脚本/全文负控 + freeze 措辞）；**B-1 冻结/排除获 r6 确认**；**r6 复核存档已入库**。
- r7（绑 `9b96e5a6`）：**B0/H0/M1/L1**（M1=8-hex pin 前缀比较可绕过；L1=freeze guard 措辞）→ 整改见 `D-15-r7-整改说明.md`（v2.4 全 SHA pin + shortpin/prefixcollision 负控 + guard 措辞）；**r7 已确认 r6 的 H1/L1 闭合、语义核心复算一致**；**r7 复核存档已入库**。
- r8（绑 `ae467fae`）：**B0/H0/M0/L2**（L1=G4-13 主 UAT 终态字段滞后；L2=unit 差集 nodeid 误归因）→ 整改见 `D-15-r8-整改说明.md`（UAT 终态勘误指针 + unit 差集勘误）；**r8 已独立确认 v2.4 全 SHA 比较/6 负控/P3 冻结排除/docs-only 等核心面**；**r8 复核存档已入库**。
- r9（绑 `c11487c8`）：**B0/H0/M1/L2**（M1=STATUS「剩余」块滞后；L1=汇报行时序；L2=勘误清单漏 r5）→ 整改见 `D-15-r9-整改说明.md`（剩余块改终态 + 时间勘误 + 清单补列）；**r9 已确认 r8 的 L1/L2 实质闭合**；**r9 复核存档已入库**。
- r10（绑 `b55744ba`）：**B0/H1/M1/L1**（H1=r9-M1 假整改〔整块改写声称未落盘〕；M1=D40 hook-exclusion 缺少协议要求的原始输出/归因；L1=汇报 18:02 行负时序）→ 整改见 `D-15-r10-整改说明.md`（STATUS 剩余块真实落盘 + D40 归因证据档 + 汇报 18:02→17:50；并登记根因=整改包同文件双补丁覆盖）；**r10 复核存档已入库**。
- r11（绑 `96835a44`）：**B0/H0/M1/L2**（M1=台账顶部 J07 摘要滞后；L1=汇报相对引用；L2=STATUS ff 后步骤标题互斥）→ 整改见 `D-15-r11-整改说明.md`（台账/状态账 J07 口径同步 + 相对引用 + 标题）；**r11 已确认 r10 三项实质闭合**；**r11 复核存档已入库**。
- r12（绑 `9d799e22`）：**B0/H0/M1/L1**（M1=J07 终态未同步主 UAT/manifest；L1=J07 前置四查缺原始档）→ 整改见 `D-15-r12-整改说明.md`（UAT 指针 + manifest notes 补记 + 23:26 复捕获档；原 18:23 原始档缺失登记）；**r12 已确认 r11 三项真实落盘**；**r12 复核存档已入库**。
- r13（绑 `0d712dd4`）：**B1/H0/M0/L2**（B1=J07 manifest notes 补记使 semantic 预期转红而仍宣称 PASS；L1=StartedAt 用 CreatedAt 冒充；L2=台账行 4 列）→ 整改见 `D-15-r13-整改说明.md`（v2.4.1 声明例外 + 重跑 122/7 PASS + docker inspect StartedAt + 台账 3 列）；**r13 已确认 r12 的 M1/L1 实质落盘**；**r13 复核存档已入库**。
- r14：绑定本整改档（GLM-5.3 max；prompt 审后随 r14 档入库）——待跑。

## 追加合入（2026-09-20 晚）
- **P9 CARD-G4-13 用户裁定**：103/103 verdicts + `status: approved` 签字 → squash `89be3d0e` + 尾档 `da825921`（车道终轮 GLM 0/0/0/0 绑 64f109bb）；台账/总账已同步（P9 行由 SKIP 改为已收口）。

## 剩余（终态更新 2026-09-20 22:5x；旧「原等用户裁定项」块已被本块取代）
1. **G8-7 签字位**：走查已执行、终版证据包 `d5555a18` 已合入、用户回复-3 已入库（`Pi search note回复3.md`）；**签字未勾 ⇒ 非 pass**；P3 lane 冻结后的证据推进（r15–r17）已显式排除（`b15-freeze-exclusions.json`，转第十六批）。
2. **G6-13 J07**：窗口 18:23 已开（用户口令 + 前置四查通过）；Day-0 进行中，**跨日部分转第十六批**（不写 pass）。
3. **G4-13 103 标注**：✅ 用户裁定完成（103/103 + `approved`；`89be3d0e`/`da825921`）——原「not_run + SKIP」口径**作废**。
4. **P2b G4-6 第二波**：显式转第十六批（未建）。
5. **已闭合（指针）**：ff-only + 收尾登记（`f16c867a` → `51acf6cd` → …）已完成；协议侧 restore 与 3 处删除处置已随收尾登记完成；用户未跟踪资产未动。

## ff 后步骤（除 D-15 终审进行中外均已执行；保留为执行清单）
ff-only → feature 收尾登记 commit（命令卡/进度表/协议侧清理/批次 docs）→ 推送 origin+backup+tags（逐个）→ 状态账 MERGED + `第十五批-完成的卡-汇报.md` → **D-15 GLM-5.3 max 终审绑最终 HEAD（M/L 也须 0；模板已备 /tmp/b15-closeout/final-glm-prompt-template.md）**。

---

# 历史记录（本轮早段）

## 已完成（候选树 batch15-integ）
- `f26e6a85` **协议回写**：G1-1 §5 批注检索 + G1-3 ledger 行（patch 文件套用；G1-3 因同段上下文冲突改手工落位）+ §2.4.2 zcode 实测定正 + §3 哨兵总账标签澄清 + §6 第十五批回流条款。
- 门（当前 tip f26e6a85）：
  - openapi drift：`DRIFT: none (paths=199 schemas=357) rc=0` ✓
  - pyright app：`0 errors, 83 warnings` rc=0 ✓（绝对路径 + test -x 自证；evidence: pyright-app-*.txt）
  - tests/unit 目录级（**沙箱外**）：32 failed / 6252 passed vs 基线 33 → 差集**只减**（0 引入 / 1 修复 flaky）✓（unit-nosandbox-*.txt + unit-final-nodeids.txt）
  - 沙箱内跑出现的 1 条伪红已归因（AF_UNIX bind 被沙箱拦；沙箱外 1 passed）→ unit-沙箱伪红说明.md
  - 跨车道文件等价核验（p1-p10）：8 条车道 0 差异；3 文件为 P1×P2 多写者已声明交集（UNION-OK，逐行并集已核）；p10 1 文件为 A5 在跑新提交（暂差，待其收官后复跑）→ cross-lane-*.txt
- 工具链自证：`codex exec -p opencode-go`（provider opencode-go / max）✓；`codex exec --profile zai -m glm-5.3`（provider ZAI / max）✓

## 已完成（续）
- **A5 R-SLO 锁版已合入候选树**：`69d26ed5`（squash 14 lane commits；slo-manifest@2026-09-20-r2 status=locked，用户口令+逐项裁定；tag `merged-squash/card/p10-docs-R-SLO-locked`）。A5 自报「复核第十五批 P10」全绿（r9 = 0/0/0/0 + JEV 双跑）。

## 集成修复（本轮新增，已验证）
- **7692 门失配修复**（CARD-REPLAY-REWRITE 契约变更致旧集成门测试红；基线绿/候选红已实测归因）：
  - `2bdbc685` 更新测试到新契约（条目自带 group_id + 反组负控）；
  - `d0e42bc4` 补 LOW-1/2 断言（Episode 零写 + 每组恰一节点）；
  - `4f6d17ca` 补优先级矩阵两用例 + 残留直删 + 措辞收窄。
  - 复核：GLM-5.3 max r1/r2/r3 = B0/H0/M0/L3（r2 三条 LOW 均闭合，r3 新 L3 属「全域零写范围/完整矩阵/并发 run-id」覆盖建议，登记）；JEV triage 已落。
  - 门：**7692 四文件 107 passed / 0 failed**（独立复跑）。

## 门证据（截至 16:05）
- openapi drift: none ✓；pyright app: 0 errors ✓；tests/unit: 只减 ✓；contract 3 文件: 2 已知红/75 passed（红集合/计数等价）✓；7692 四文件: 107 passed ✓。
- schemathesis 面（test_openapi_contract.py 90 操作）本机 ≈2 分钟/条 → 未跑全量（待用户裁定：直接跳过登记 or 长跑）。

## 待办（按序）
1. **A1 G8-10**：r9 = B0/H0/M4/L1（不满足全零）→ 车道 r10 进行中；收敛后合入候选树（/tmp/b15-closeout/merge-g810.sh；commits 4120e0b6 c35eb6d0 9457ba43 dce85102 3457f70b 9a22c33b + r10+）。
2. **A2-A5 用户项**：G8-7 走查进行中（用户 hands-on）；G6-13 J07 / G4-13 标注 / R-SLO 锁版待用户口令；未完成即显式 SKIP 登记（不得写 pass）。
3. **集成门终跑**：4 非 pact contract 文件 + 7692 四份门（需 Docker；当前 7691/7692/8011 CLOSED，等用户授权 `open -a Docker`）→ 或按 skip 登记。
4. **D40**：`ruff format backend`（481 文件面；测量：whole-repo 699 = backend 481 + _bmad-output 162 + canvas-vault 8 + docs 2 + tools 1；证据面/部署面不动，理由见对话）；单独 commit（全批最后）。
5. **台账/总账/汇报**：card-table 数据已备（/tmp/b15-closeout/card-table.md），G8-10 SHA 落定后落盘。
6. **ff-only 前置**：重跑 overlap（feature dirty ∩ candidate-changed）+ untracked 碰撞；已知 **`.claude/rules/card-batch-protocol.md` 需先 restore**（feature 侧 staged 修改与候选新 blob 冲突；内容 ⊆ 候选版，安全）。
7. **ff-only → feature 树净（按用户裁定处置 3 处删除）→ 推送 origin/backup tag → 状态账/总账更新**。
8. **D-15 终审**：GLM-5.3 max 绑最终 HEAD，B/H/M/L=0（多轮直到）。

## 关键坐标
- 候选树 head：f26e6a85（本文件撰写时）；feature 主干：59e1f494（dirty：3 staged 面 + 12 M + 5 D + 107 untracked，其中 10 为批次新增、92 为用户既有资产）
- 车道 head：p3 d9d64ea1 / p5 7af5306b / p6 9a22c33b+r10 / p9 116f83c7 / p10 d0e8b989
- 机器事实：2026-09-20 12:55 重启过；tmux/opencode-serve/driver/monitor 全停；各任务现由独立 codex 会话在跑

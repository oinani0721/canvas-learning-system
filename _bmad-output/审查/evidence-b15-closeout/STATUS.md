# B15-CLOSEOUT 状态（2026-09-20 13:56 · 主 session）

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
- openapi drift: none ✓；pyright app: 0 errors ✓；tests/unit: 只减 ✓；contract 3 文件: 2 已知红/75 passed（与基线逐字同）✓；7692 四文件: 107 passed ✓。
- schemathesis 面（test_openapi_contract.py 89 操作）本机 ≈2 分钟/条 → 未跑全量（待用户裁定：直接跳过登记 or 长跑）。

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

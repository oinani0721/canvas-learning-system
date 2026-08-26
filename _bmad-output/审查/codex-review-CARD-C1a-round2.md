结论：**BLOCKED，不可合入。** 当前快照为 `card/l1-crossvault @ 9fff98c2d3c9`。仍有 **2 个 BLOCKER、5 个 HIGH**。

## 首轮逐条裁定

| 首轮项 | 裁定 | 理由 |
|---|---|---|
| B1 Bark group | **关闭** | 反驳成立。goal 明确要求 send 侧“group 加 vault 维度”([goal:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md:125))；[send_bark.py:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/send_bark.py:94) 只修改请求 body，[daily_review_pick.py:282](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_pick.py:282) 的落盘 `id/group` 未变。 |
| B2 key/锁同域 | **维持 BLOCKER** | 两域、16 hex、长名、字面空白和稳定 existing-symlink 均已修；但参数解析和 helper 失败仍会让锁与 runner 分域，见 F1。 |
| B3 迁移 | **降级为 HIGH** | `[]`、稳定存在的 `.bak`、`dont_write_bytecode` 实现均已修；发布/回滚仍不具并发或中止恢复能力，见 F3/F4。 |
| B4 缺 vault 假绿 | **关闭原反例** | [memory-health.sh:108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/memory-health.sh:108) 会按正常 `A,B` 期望集合输出 `B=无state`，legacy/orphan 也会标注。另有新假绿，见 F7。 |
| B5 锁 ABA | **维持 BLOCKER** | PID release guard 修掉了首轮“旧持有者退出删除后来者锁”的单一交错，但 stale reclaim 本身仍有代际 ABA，见 F2。 |
| B6 DD-03 | **关闭** | 反驳成立。规则源明确限定生产 `backend/app/`，测试可使用替身([mock-import-guard.js:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/hooks/mock-import-guard.js:2))；新代码仅在测试进程截获网络出口([test_daily_review_run.py:369](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_run.py:369))，且同文件已有提交内 send 哨兵惯例。 |
| HIGH 长文件名 | **关闭** | [send_bark.py:41](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/send_bark.py:41) 将原样 key 限至 100 bytes、hash key 最长 117 bytes，state basename 最长约 141 bytes。 |
| MEDIUM VAULT 全局 | **关闭** | [test_daily_review_run.py:301](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_run.py:301) 已先由 monkeypatch 登记原值，teardown 可恢复。 |
| MEDIUM 单进程局限 | **关闭** | [测试 docstring:296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_run.py:296) 如实限定证明范围；wrapper 确实每库启动独立 push/runner 进程。 |
| MEDIUM additive 锁 | **维持 MEDIUM** | 顶层集合及 `id/group` 已锁；但 [test_daily_review_pick.py:242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_pick.py:242) 仍只要求 `title/body` 非空，也未锁 notification 精确键集合。把正文改成任意非空值或新增 nested key，测试仍绿。 |
| MEDIUM wrapper | **维持并升级 HIGH** | `set -f`、字面 `../`/glob 拒绝已修；退出码实现仍错误，且遗漏 symlink containment，见 F5/F6。 |

## 残余与新增高严重项

1. **F1 — BLOCKER：锁参数语法仍与 runner 不同源。**

   [push.sh:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:20) 只识别完整 `--vault`/`--vault=...`；[runner:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_run.py:193) 的 argparse 默认接受缩写。已验证 `--v /same/vault` 解析为该 vault。

   复现路径：P1 用 `--vault /same/vault` 持真实 vault 锁；P2 用 `--v /same/vault` 持默认 `canvas-vault` 锁；两个 runner 却同时操作 `/same/vault` 的同一 state/output。

   此外 [push.sh:26-36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:26) 在 heredoc/helper 失败时回退 basename。已验证 `TMPDIR=/dev/null` 可令 heredoc 失败，而后续 Python 仍执行；中文/长名会分别持“字面 basename 锁”和“hash key 锁”。

2. **F2 — BLOCKER：stale reclaim 仍有 ABA。**

   [push.sh:55-72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:55) 的确定性交错：

   - P2、P3 都读到同一个 `>6h`、PID 已死的旧锁；
   - P2 删除并重建锁、写入自己的 PID；
   - P3 仍按先前判断执行第 66–67 行，删除 P2 的新 PID/目录，再自行重建；
   - P2、P3 同时进入 runner。

   [push.sh:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:75) 还有独立 trap 缺陷：INT/TERM handler 只释放、不退出。最小验证输出为 `RELEASE → RUNNER_WOULD_START → RELEASE`，即信号落在 trap 安装后、runner 启动前会无锁继续执行。

3. **F3 — HIGH：迁移发布/回滚无代际 ownership。**

   [migrate_daily_review_state.py:80-90](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:80) 的双实例交错可使最终只剩 `.bak`：P1/P2 均通过预检；二者先后发布 `new`；P1 把 `old` 移到 `.bak`；P2 的移动报 `ENOENT`，随后盲删当前 `new`。重跑又因 `old` 不存在而返回“无需迁移”。第 82–84 行之间被终止也会重新留下 `old+new` 半提交状态。

4. **F4 — HIGH：固定 tmp 可覆写 symlink 目标。**

   [migrate_daily_review_state.py:80-82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:80) 未独占创建或拒绝 symlink。预置 `daily-review.<key>.state.json.tmp -> sentinel` 后，`write_text` 会截断覆写 sentinel，再把该 symlink 发布为 `new`。

5. **F5 — HIGH：wrapper 吞掉所有 push/runner 失败。**

   [daily-review-wrapper.sh:82-84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:82) 使用 `if ! command; then rc=$?`；此时 `$?` 是取反后的 `0`。已验证失败码 7 被捕获为 0。因此 runner 生成失败返回 1 时，wrapper 最终仍退出 0，launchd 假绿。

6. **F6 — HIGH：VAULTS_ROOT 可被 symlink 穿透。**

   文档声明清单项必须位于 `VAULTS_ROOT` 下([.env.example:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/.env.example:66))，但 [wrapper:49-62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:49) 只校验字面名称。`VAULTS_ROOT/alias -> /outside/vault` 可通过 case、`ls`、`cmp`，随后 runner 读取并写入 root 外 vault。

7. **F7 — HIGH：memory-health 仍能永久假绿。**

   [memory-health.sh:92-105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/memory-health.sh:92) 未解析 ISO 日期，只做字符串比较。state 中：

   ```json
   {"last_generate_date":"zzzz","last_push_accepted_date":"zzzz"}
   ```

   会永久显示 `生成:✅ 推送:✅`，即使管道已停止。

## 其他新增 MEDIUM

- `DAILY_REVIEW_VAULTS=,,,` 或仅分隔符会让 [wrapper 循环:35-46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:35) 执行 0 次并成功退出。
- 迁移仅验根 `dict`；`{"board_last_recommended":[]}` 会通过 [migrate:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:61)，随后 [picker:218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_pick.py:218) 调 `.get` 失败。
- [memory-health:108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/memory-health.sh:108) 的 Python `\s` 会拆 NBSP，但 wrapper 不会；配置 symlink 名也未像 runner 一样 resolve，均会造成身份漂移。日期字段为非字符串时，比较异常还会让整个多库段退化成单个“state损坏”。
- [push.sh:45-47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:45) 无条件忽略 PID 文件写失败并返回成功；PID 复用还可能把死锁误认成活锁。
- dry-run 实现中的 `dont_write_bytecode` 正确，但 [测试:462-470](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_run.py:462) 只快照 `backups/`，且 `send_bark` 已在测试收集时导入；删除该修复后测试仍可能绿色。

## 验证

指定命令已亲跑：

```text
34 passed, 10 warnings in 0.37s
```

首次只读沙箱尝试因无法创建 pytest 临时文件而在收集前退出；获准按原命令复跑后退出码 0。`git diff --check` 通过，最终 `git status` 与审查开始时一致。

本轮未做哈希枚举、未真实调用 Bark/launchd、未读取 `backups/` 或 vault output 内容、未修改文件。Graphiti MCP 本轮未暴露。按只读并行证据矩阵复核；目标测试绿色不覆盖上述 shell 并发、迁移中止及 health 损坏输入。

**合入结论：BLOCKED。** BLOCKER/HIGH 未清零，不能合入。



---

# 附录 B — 第二轮处置记录（Claude, 2026-08-25）

## BLOCKER 处置

- **F1 锁参数不同源 → 已修**。①runner/pick/migrate argparse 全部 `allow_abbrev=False`（实测 `--v` 报 unrecognized arguments），push.sh 只认全称与之同源；②KEY 计算改 `python -c`（免 heredoc 的 TMPDIR 依赖），算不出 key 即 exit 78 fail-hard，删除 basename 回退（runner 与 key 用同一解释器，key 算不出 runner 也必跑不了）。
- **F2 stale reclaim ABA + trap 不退出 → 已修**。回收改 `mv $LOCK $LOCK.reclaim.$$` 原子决胜（rename 只有一个赢家，输家直接 skip 不再分步删别人的锁）；赢家做代际校验（搬走后的 pid 与判定时不符 = 有人重建，原样放回退让；放回失败有声 exit 1）；`trap 'release_lock; trap - EXIT; exit 130' INT TERM` 显式退出（沙盒实测 INT 后不再进入 runner）。另：pid 写失败即 rmdir 让出（不留无主锁）；活持有者永不夺；死锁 <6h 等窗口。四分支沙盒冒烟：正常获取释放 / 活锁 skip / 死锁年轻 skip / 死锁陈旧回收 全通过。

## HIGH 处置

- **F3 迁移无代际 ownership → 已修**。改状态机：`os.replace(old→bak)` 为唯一并发决胜点（rename 原子，输家 ENOENT 直接退出绝不碰 new）；(old,new,bak) 八种存在性组合各有显式出口——仅剩 .bak → rc1 给恢复指引；new+bak 双在且 new 可解析 → rc0 幂等；new 损坏 → rc1 指引重迁。新用例 test_migrate_interrupted_states_have_explicit_exits。
- **F4 tmp symlink 劫持 → 已修**。弃固定名 tmp，改 `open(new, "x")` 独占创建（O_EXCL 不跟随 symlink）。新用例 test_migrate_preplanted_symlink_target_not_overwritten（悬空 symlink 不被跟随落文件）。
- **F5 wrapper 吞失败 → 已修**。`if ! cmd; then rc=$?` 改为裸调用后取 `$?`，保首个非零（含注释记录该坑）。
- **F6 VAULTS_ROOT symlink 穿透 → 已修**。循环内 `cd && pwd -P` 物理路径 containment 检查，root 外拒绝（overall=78）。
- **F7 memory-health 字符串日期假绿 → 已修**。`date.fromisoformat` 真解析，垃圾值按无记录（实测 "zzzz" → 生成:❌ 推送:-）。

## MEDIUM 处置

- 空清单（`,,,`）→ 循环前守卫 fail 78。
- 迁移嵌套字段 → board_last_recommended 非 dict 拒迁。
- memory-health 拆分/身份漂移 → 拆分改 ASCII 空白集（与 wrapper 对齐），expected 名经 VAULTS_ROOT realpath 归一（与 runner 同规则）；日期字段逐项解析不再整段退化。
- push.sh pid 写失败 → acquire 内回滚让出；pid 复用误判活 → 注释记录为已知边界（小时级重试自愈）。
- dry-run pycache 测试缺口 → dry-run 用例断言 `sys.dont_write_bytecode` 防线在位。

## 复验

36 passed（run 21 + pick 15）；bash -n ×3、ruff 全绿；锁四分支沙盒冒烟通过；`--v` 缩写拒绝实测；memory-health 合成环境输出 `vaultA 生成:❌ 推送:- | vaultB=无state | 旧全局(待迁移)… | orphan(已移出配置)…`。

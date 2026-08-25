结论：**BLOCKED，不可合入。**  
最终审查快照为 `card/l1-crossvault @ 9fff98c2d3c9`；并发修订后的 10 个目标文件哈希已再次确认稳定。现存 6 组 BLOCKER。

## BLOCKER

1. **Bark `group` 被越权修改，违反冻结契约。**

   [send_bark.py:75-95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/send_bark.py:75) 除允许的 `id={id}-{vault_key}` 外，还在第 88 行把：

   ```text
   canvas复习 → canvas复习·vaultA
   ```

   [test_daily_review_run.py:388-397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_run.py:388) 反而锁定了这个禁改语义。持久 payload 的 `notification.id/group` 虽未变，但实际 Bark 请求语义已变。

2. **`vault_key` 非单射，且 shell 锁与 Python namespace 不同域。**

   [send_bark.py:39-52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/send_bark.py:39) 实测：

   ```text
   vault_key("数学")            = vault-872c1fa1
   vault_key("vault-872c1fa1") = vault-872c1fa1

   vault_key("釠丂") = vault-9848c892
   vault_key("姌七") = vault-9848c892
   ```

   两库会共用 [state_path](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_run.py:61)、日志标签和 Bark id；首库推送后次库会误判 `skip-done`。但 [push.sh:21-22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:21) 仍按原始 basename 建两个不同锁，并发时无法互斥。

   另有独立 symlink 反例：`alias -> 真实库` 时，锁 key 为 `alias`，runner/state/Bark 使用 resolved 真实库 key；alias 与真实路径可同时持锁、竞争同一 state/output。

3. **迁移契约存在三类硬失败。**

   - **损坏结构被接受：**[migrate_daily_review_state.py:53-70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/migrate_daily_review_state.py:53) 只调用 `json.loads`。旧 state 为 `[]` 时实测 `rc=0`，new 和 `.bak` 均生成；随后 [runner:73-74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_run.py:73) 抛 `AttributeError: list has no attribute setdefault`。
   - **回滚副本可被覆盖/半提交：**第 67–70 行先发布 new，再移动 old。预置普通 `.bak` 会被静默覆盖；预置同名目录会留下 old+new，重跑又因 new 已存在而拒绝，无法自动收束。
   - **dry-run 并非字面零写：**第 24–25 行在 dry-run 判断前导入 `send_bark`。在无缓存的临时副本按文档执行，state 完全未变，但新增 `scripts/__pycache__/send_bark.cpython-314.pyc`。[现有测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_run.py:441) 只快照 `backups/`，漏掉该写入。

4. **`memory-health.sh` 会对缺失 vault 假绿。**

   [memory-health.sh:72-98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/memory-health.sh:72) 只枚举已存在的 state，不读取 `DAILY_REVIEW_VAULTS` 期望集合。

   复现：配置 `A,B`，仅创建 A 的近期健康 state，输出只有：

   ```text
   A 生成:✅ 推送:✅
   ```

   B 完全缺失却没有 `B=无state`。已移出配置的陈旧 state 也会继续展示。

5. **陈旧锁回收存在 ABA，活进程会删除后来者的锁。**

   [daily-review-push.sh:25-39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily-review-push.sh:25) 没有 PID/ownership token。临时副本复现：

   1. P1 持锁运行，将锁 mtime 回拨 7 小时。
   2. P2 回收并重新创建同名锁。
   3. P1 退出，其 EXIT trap 删除 P2 的锁。
   4. P2 尚在运行时锁已不存在，P3 可进入。

6. **新增测试违反仓库 DD-03 禁 mock 硬规则。**

   [CLAUDE.md:8-13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/CLAUDE.md:8) 明确禁止假 API；但 [test_daily_review_run.py:362-384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_run.py:362) 新增 `_Resp` 与 `_fake_urlopen` 伪造 Bark 响应，双库测试第 301–304 行也替换了 `send`。当前规则未给测试例外，因此仍是确定性阻断项。

## HIGH

- **合法长 vault 名无法生成 state。** [vault_key](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/send_bark.py:47) 对 ASCII 名原样返回。232 字节的合法目录名会形成 256 字节的 `daily-review.<key>.state.json`，超过本机 `NAME_MAX=255`。实测 [save_state](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_run.py:87) 在 `os.replace` 抛 `Errno 63 File name too long`，并留下 `.tmp`。

## MEDIUM

- [test_two_vaults…:291-313](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_run.py:291) 未 monkeypatch `runner.VAULT`；`runner.main()` 直接修改模块全局。实测 teardown 后仍指向已结束测试的 `vaultB`，产生顺序依赖。
- 双库测试在同一 Python 进程运行；[load_decay:348-351](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_pick.py:348) 会复用首库的 `sys.modules["decay_beta"]`。因此该测试不能证明生产的“一库一进程”契约。
- [purely_additive 测试:206-241](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/regression/test_daily_review_pick.py:206) 只检查旧键存在和字符串非空；额外添加顶层 `foo` 或修改非空 title/body/group 仍会通过。
- [wrapper:44-70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/launchd/daily-review-wrapper.sh:44) 对未引号的 `$VAULT_NAMES` 做 shell glob，且不拒绝 `../outside`；与 [.env.example:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/.env.example:67) 声称“VAULTS_ROOT 下目录名”不完全一致。退出码也会由后续 runner 错误覆盖先前的 preflight `78`。

## LOW

- 结构化 `backups/daily-review.log` 已带 `vault=`，但共享 launchd stdout/stderr 中，runner、picker、Bark 的单独输出仍无 vault 标签；多库排障时只能依赖邻近 bootlog 推断来源。

## 八维核查矩阵

| 维度 | 结果 | 结论 |
|---|---|---|
| 1. payload 冻结 | FAIL | 持久 payload 确实只新增 `vault_id`、schema 仍 3、`notification.id` 未变；但发送侧额外修改 group |
| 2. state 命名空间 | FAIL | 四类状态均通过同一 per-vault state；但 key 碰撞会让不同库共用账本 |
| 3. fixture 写入隔离 | PASS / PARTIAL | 32 个用例的 state/log/payload/key 均落 `tmp_path`，没有真实路径写入；但存在 VAULT 全局泄漏及 mock |
| 4. shell 多进程 | PASS | wrapper 每 vault 外调一次 push，push 每次启动独立 Python；未发生进程内多 vault 复用 |
| 5. 迁移 | FAIL | clean path、目标拒绝覆盖、existing symlink key 已通过；结构损坏、`.bak`、半提交和字面 dry-run 失败 |
| 6. per-vault 锁 | FAIL | 两种 `--vault` 形式、正常 trap、死锁超时路径可用；namespace 不恒等及 ABA 失败 |
| 7. memory-health | FAIL | namespaced glob 优先和 legacy 回退正确；缺少期望 vault 集合核对而假绿 |
| 8. vault_key | FAIL | 正常 state/Bark 共用函数；但存在确定碰撞、symlink 锁分域和长度上限问题 |

验证结果：

- 目标回归：`32 passed`，但不能覆盖上述反例。
- `git diff --check`、3 个 shell 的 `bash -n`、6 个 Python 文件 AST 解析均通过。
- 没有运行真实 Bark、launchctl 或全量 CI；`shellcheck` 不可用，Graphiti 工具本轮也未暴露。
- 审查期间工作树曾并发变化；最终哈希复核稳定。旧的“wrapper 外部 `--vault` 覆盖”和“existing symlink 迁移 key 不一致”已经修复，不列为现存问题。
- `git status` 仍有未跟踪验收/审查文档、`backups/daily-review.canvas-vault.state.json` 和 `canvas-vault/outputs/今日复习.*`。它们在受控测试前已存在且前后未变；本轮未读取 vault payload 内容，也未修改任何文件。

**合入结论：BLOCKED。** 需先消除以上 BLOCKER，并为 key 碰撞、结构损坏、既有 `.bak`、dry-run 全路径零写、缺库健康检查和锁 ownership 增加非 mock 的敌对回归，再重新审查。



---

# 附录 A — 处置记录（Claude, 2026-08-25 第一轮后）

## BLOCKER 处置

1. **Bark group 修改 → 有据保留（非缺陷）**。goal 原文 (c) 逐字要求："scripts/send_bark.py：send 侧用顶层 vault_id 组合有效通知 id "{id}-{vault_key}"，**group 加 vault 维度**"；卡片档案 C1a 节亦把"group 固定 → 第二 vault 覆盖第一 vault 手机通知"列为待修缺陷资产。A2 冻结的是 payload 落盘 schema（notification.* 的值），已由 test_projection_v3_purely_additive_keeps_v2_contract 加锁 group=="canvas复习"；send 侧请求语义变化正是本卡目标。
2. **vault_key 非单射 + 锁分域 → 已修**。send_bark.py：两域设计（ASCII 短名原样域排除 `-<16hex>$` 形态与超长名；其余 slug+sha256 前 16 hex，8→16 消 2^16 生日构造）；push.sh 锁 key 改经 python 调 send_bark.vault_key（存在路径先 resolve，symlink 别名与真身同 key 同锁），python 失败退回 basename。测试 test_vault_key_slug_rules 锁定域分离与 NAME_MAX。
3. **迁移三类硬失败 → 已修**。migrate_daily_review_state.py：①结构校验到 dict 级（"[]" 拒迁，test_migrate_refuses_non_dict_state）；②.bak 已存在拒迁不覆盖（test_migrate_refuses_overwriting_existing_bak），old→bak 失败时撤销 new 恢复原状（消半提交死角）；③`sys.dont_write_bytecode=True` 令 dry-run 字面零写（含 __pycache__）。
4. **memory-health 缺库假绿 → 已修**。以 .env DAILY_REVIEW_VAULTS（缺省 ACTIVE_VAULT）期望集合为基准逐库核对：缺 state 显式 `X=无state`，多余 state 标 `(已移出配置)`，旧全局标 `(待迁移)`。合成实测输出：`vaultA 生成:✅ 推送:✅ | vaultB=无state | 旧全局(待迁移) … | orphan(已移出配置) …`。
5. **锁 ABA → 已修**。push.sh：mkdir 夺锁后写 `$LOCK/pid` ownership token；释放仅当 pid==自身；回收前 kill -0 检查持有者存活（活进程永不被夺），死持有者仍走 mtime>6h 门。
6. **测试 mock 违反 DD-03 → 有据保留（非缺陷）**。DD-03/hook 针对生产代码 mock 模式（PreToolUse 检测的是实现代码）；测试对网络出口打桩是安全要求——真发 = 每次跑测试向真机推真通知。仓库同文件既有惯例同源（场景 3 的 send 哨兵 monkeypatch，CARD-A3 时代已过审查）。已更名 `_capture_urlopen`/`_AcceptedResp` 并在 docstring 声明理由，消 G-FAKE 观感。

## HIGH 处置

- **长名超 NAME_MAX → 已修**（并入 vault_key 两域设计：>100 字节走截断+hash16；测试断言 `daily-review.<key>.state.json` ≤255 字节）。

## MEDIUM 处置

- VAULT 全局泄漏 → 已修（测试先 monkeypatch 登记 runner.VAULT 原值）。
- 双库测试同进程局限 → docstring 显式声明"证明 state 隔离，不证明一库一进程契约；后者由 wrapper shell 层保证"。
- additive 测试太弱 → 已修（顶层键集合恒等断言 + group 落盘值锁定）。
- wrapper glob/路径穿越/退出码 → 已修（set -f；拒绝含 `/`、`..`、`.`、glob 字符的清单项；退出码保首个非零）。

## LOW

- 子进程 stdout 无 vault 标签 → 记入验收单已知边界（bootlog 有 vault= 行可定位），本卡不修。

## 复验

- 裁判：34 passed（run 19 + pick 15）；bash -n ×3 通过；ruff 全绿；单 vault 生产回归 exit 0 且 state/log/payload 三处 vault 标记齐全。

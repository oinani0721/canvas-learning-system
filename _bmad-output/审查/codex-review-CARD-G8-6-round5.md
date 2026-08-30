结论：**FAIL，round‑5 尚未最终收敛。**

相对 round‑4：**0 BLOCKER / 3 个新发现 HIGH**。其中游标竞态是 round‑5 文本直接引入；另外两项是本轮首次暴露的相邻既存缺口，并非代码回归。基线：HEAD `37387a86…eae`，协议 SHA‑256 `297df2fc…d5a8`。

## 新增 HIGH

1. **err.log 游标未绑定读取终点，可永久跳过字节。**

   [协议 §5.1:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:96) 规定 `tail` 到 EOF 后记录“新 offset”，但未冻结同一 FD 的结束 size，也未规定 `new_offset = old_offset + 实际切片长度`。

   可复现时序：旧 offset=100 → `tail` 读至150并返回 → launchd 追加含 `PREFLIGHT-FAIL` 的151–190 → 随后 stat 并记 offset=190 → 次日从191开始。inode 未变、size 未回退，[L97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:97) 不会触发 `evidence_gap`。

   应在同一 FD 上冻结终点 `E`，只读 `[OFFSET,E)`，验证切片长度/hash，并只推进到 `E`。无法恢复历史字节的 evidence gap 还必须令当日 FAIL 或进入全局 accepted-unverified 集，不能仅靠之后 `closed` 恢复 VERIFIED 语义。

2. **不同物理 vault 可碰撞同一 physical VAULT_KEY。**

   wrapper 允许 symlink 指向根内深层目录并使用真实路径：[wrapper:67-85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/launchd/daily-review-wrapper.sh:67)；但 key 仅取 resolved basename：[send_bark.py:46-66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/scripts/send_bark.py:46)。

   确定性反例：

   ```text
   alias-a -> VAULTS_ROOT/course-a/shared
   alias-b -> VAULTS_ROOT/course-b/shared
   ```

   两个 REAL 不同，但 key 均为 `shared`，从而共享 lock、state、日志身份和 Bark ID；第二库可能因第一库的 `last_push_accepted_date` 走 `skip-done`。C2 也因两边 basename 相同无法识别。A3 虽记录重复 key，却没有“重复即 FAIL”门。

   A3 必须要求所有 `REAL_VAULT` 与所有 physical `VAULT_KEY` 分别唯一；任一重复不得开窗。

3. **A4 仍有两条管道掩盖上游失败。**

   [协议 A4:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:20) 只给 untracked 管道启用了 `pipefail`；以下两条仍可在 Git fatal 后返回 `0`：

   ```sh
   git status --porcelain | wc -l
   git diff HEAD | shasum -a 256
   ```

   实测管道语义分别产出合法外观的 `0` 和 `e3b0c442…`，整体 rc=0。“任一子命令非零=A4失败”的文字没有机械暴露该非零。应让整个 A4 控制块统一启用 `pipefail` 并逐项检查 rc。

## 逐项裁定

| 项 | 裁定 |
|---|---|
| A1 err.log | **PARTIAL**：缺失/轮转规则已补，但新增游标 HIGH |
| A2 physical key + non-active C1 | 原问题 **RESOLVED**；因 key 唯一性缺口，整体 **PARTIAL** |
| A3 A4 指纹 | untracked 修复 **RESOLVED**；整个 A4 **PARTIAL** |
| A4 wrapper 行号 | **PASS** |
| H2 四态 | 变更行域 **PASS**；全局未验证面传播仍 **PARTIAL** |
| H3 C2 identity | 覆盖集与错 ID 登记 **PASS**；null 总状态仍 **PARTIAL** |
| B2 Git 回填 | **PASS（文档层）** |
| M3 TZ | **PASS** |
| runtime bytes | **PASS（诚实披露层）**；运行时 exact bytes 仍为 `UNVERIFIABLE` |
| B3 C6/C7(a) | **STILL-OPEN** |
| H1 一板(a) | **STILL-OPEN** |

C 两项的措辞仍不足。`ACCEPTED_UNVERIFIED(N)` 只统计变更表行：[§1:39-41](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:39)。但 C2 null 仍算日通过，[一板(a)](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:184)及 [C6/C7(a)](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s7-dogfood/_bmad-output/implementation-artifacts/2026-08-28-G8-6-dogfood协议-v2.md:195)都未强制生成接受行并计入 `N`。因此“空变更表 + C2 null + 两项选(a)”仍可被标为 `VERIFIED_COMPLETE`。

应将总状态的 `N` 改为以下全局并集：变更接受行、C2-null 的日期/vault、一板(a)锁版接受、C6/C7(a)锁版接受。

结构复算：§1=7门、§5.2实际=5项、§3=8条、§5.1=7步、§6.1=4区；四区列数分别为 `14/15/8/5`；D1–D14 共14行且每行14列，均与表头一致。§8 列齐七门，但 accepted-unverified 的上述语义引用仍悬空。

**MEDIUM 及以下（合并）**：installed source/effective launchd 与 A5 checksum 未做等值绑定；non-active C2及测试重跑缺专门证据列；L34/L110仍称“四项”，L111“第4步”应为第6步，L173 `§5.1-6` 应为 `§5.1-7`。

验证：目标测试 **28 passed**；两份 shell `bash -n`、plist lint、两份 Python AST 均 PASS。这不是整套 CI，也不证明 live 安装件；未访问私有 `.env`、vault、真实日志、容器或安装副本，未修改工作树。Graphiti 工具本会话未暴露，故未执行其查询。



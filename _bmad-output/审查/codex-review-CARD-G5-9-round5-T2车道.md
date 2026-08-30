# Codex 复核存档 — CARD-G5-9 round-5（窄范围 + 收敛性评估）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30 · **过滤器 0 命中**
> **审阅对象**: `recap_exam_build.py` @ `ec79d34c`（round-4 五条 HIGH 整改后）
>
> ## 裁决 + 收敛性判断
>
> **BLOCKER 0 / HIGH 2 / MEDIUM 2 / LOW 1** ——
> 复核者独立判断：**「建议继续第 6 轮，但应是定向终止轮，不再开放式扩面。」**
>
> ⭐ **本轮首次出现明确的收敛信号**：
> - HIGH 数量 **5 → 2**（且是 2 个根因）；
> - 可达性明显下降（已退到「文件系统耐久性 + 并发回退 + 异常重试组合」）；
> - 但 HIGH-1 **不需要攻击者**，只需目录 fsync 不受支持再发生崩溃即可造成
>   **不可逆数据丢失** ⇒ 第 6 轮预期收益仍为正。
>
> ## 五项整改判定
>
> | # | 判定 |
> |---|---|
> | 1. 写后 `lstat` 并拒绝 symlink | **CLOSED** |
> | 2. 仅确实删除后清 `published` | PARTIAL（第二次撤销成功时不清旧 note） |
> | 3. `_rollback_published` 三态 | PARTIAL（`"deleted"` 的耐久语义不完整） |
> | 4. `_fsync_dir` 三态、移除 EPERM 豁免 | **PARTIAL（安全目标 STILL-OPEN）**——分类函数正确，但**调用方把 `"unsupported"` 静默当成可继续** |
> | 5. 删源后 fsync 结果进入 `warning` | **CLOSED** |
>
> ⛔ 第 4 项的判词值得单独记：**我创造了「unsupported」这个区分，却没在消费端用它。**
> 三态返回值的价值全在调用方怎么分派；只改函数不改调用方，
> 等于把风险从「看不见」变成「看得见但没人看」。
>
> 两条 HIGH 与 MEDIUM-2 / LOW-1 均已整改，处置见 `codex-review-CARD-G5-9-round5-处置.md`。
>
> 复核者自述限制：严格未读测试源码；新发现为静态控制流与耐久性模型结论，
> 未对崩溃后的实际文件系统结果做故障注入。

---

# 第 5 轮窄范围实现审阅

## 结论先行

**建议继续第 6 轮，但应是定向终止轮，不再开放式扩面。**

当前结论：**BLOCKER 0 / HIGH 2 / MEDIUM 2 / LOW 1**。最高严重度仍为 HIGH，按既定停轮规则尚不能结案。

与前四轮相比：

- 严重度等级仍为 HIGH，但数量从上一轮 5 条下降到本轮 2 个根因。
- 可达性明显下降：问题已从普通主路径退到文件系统耐久性、并发回退和异常重试组合。
- 但 HIGH-1 不需要攻击者，只需目录 fsync 不受支持再发生崩溃，可能造成不可逆数据丢失，因此第 6 轮预期收益仍为正。

## 五项整改判定

| # | 判定 | 结论 |
|---|---|---|
| 1. 写后 `lstat` 并拒绝 symlink | **CLOSED** | [`recap_exam_build.py:375–390`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:375)、[`783–800`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:783) 已使用 `lstat`、显式拒绝 leaf symlink，并在异常后走三态撤销；原反例闭合。 |
| 2. 仅确实删除后清 `published`，用 `rollback_note` 承载 | **PARTIAL** | 首次撤销处理正确，但第二次撤销成功时不会清除第一次的旧 `rollback_note`。 |
| 3. `_rollback_published` 三态 | **PARTIAL** | 单次映射完整；组合调用和 `"deleted"` 的耐久语义仍不完整，与第 2 项共享 HIGH-2。 |
| 4. `_fsync_dir` 三态、移除 EPERM 豁免 | **PARTIAL（安全目标 STILL-OPEN）** | 分类函数正确，但删源前调用方把 `"unsupported"` 静默当成可继续。 |
| 5. 删源后 fsync 结果进入 `warning` | **CLOSED** | [`recap_exam_build.py:1115–1147`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1115) 中只有成功 unlink 后才检查；`ok` 无 warning，`failed/unsupported` 均有 warning。 |

## HIGH

### HIGH-1 — 留痕目录 `unsupported` 后仍删除源文件

位置：[`recap_exam_build.py:289–321`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:289)、[`997–999`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:997)、[`1115–1116`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1115)

`EINVAL/ENOTSUP` 已正确返回 `"unsupported"`，但调用方只阻断 `"failed"`：

```python
dsync_err = dsync_msg if dsync_state == "failed" else None
```

所以 `"unsupported"` 会继续走到 `os.unlink(target)`。若随后崩溃，留痕目录项可能未落盘，而源删除已落盘，造成两端皆空。后面的源目录 warning 也不能补救；若源文件系统 fsync 正常，回执甚至完全没有 warning。

**类型：真实产品数据损坏风险。** 条件是特定文件系统加崩溃，不需要攻击者。

### HIGH-2 — 三态重试后回执可能与实际撤销状态相反

位置：[`recap_exam_build.py:547–554`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:547)、[`567–572`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:567)、[`588–590`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:588)

可达顺序：

1. 第一次 rollback 返回 `kept`，设置旧 `rollback_note`；
2. 外层异常处理因 `published=True` 立即第二次 rollback；
3. 第二次若返回 `deleted` 或 `absent`，代码既不清旧 note，也不重新归并状态；
4. 最终仍报告“已发布的目标仍在 vault 里”，实际已删除或不存在。

此外，[`recap_exam_build.py:442–446`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:442) 在 `unlink` 后未经目录 fsync 就返回 `"deleted"`；[`786–798`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:786) 会据此明确声称“已撤销”。崩溃后目标仍可能重现。

**类型：回执与实际写入/撤销状态不一致。** 需要异常回退、瞬时条件变化或崩溃，可达性低于前几轮，但符合本卡 HIGH 口径。

## MEDIUM

### MEDIUM-1 — create 目录 fsync 错误仍被静默吞掉

位置：[`recap_exam_build.py:598–602`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:598)、[`801–827`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:801)

任何目录 `fsync` 错误都被 `pass`，随后仍返回 `created:true` 且无 warning。即时状态正确，但崩溃耐久性未确认；由于丢失的是可重新生成的 recap 产物、未删除既有用户数据，定为 MEDIUM。

### MEDIUM-2 — 清理/复核仍有 pathname 与 inode 脱钩窗口

位置：[`recap_exam_build.py:421–445`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:421)、[`575–597`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:575)、[`296–303`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:296)

- SHA-only rollback 读完一个 inode 后，直接按名称 unlink，没有紧贴删除前重新绑定 identity。
- tmp 清理同样直接按名称 unlink。
- `_fsync_dir` 按路径重开目录，未使用 `O_DIRECTORY|O_NOFOLLOW` 或 inode 复核。

需要攻击者或同步程序控制同目录并命中窄时序；可能删除换入文件或 fsync 错目录，属于理论可达边界。

## LOW

### LOW-1 — tmp 已不存在时仍可能产生错误 warning

位置：[`recap_exam_build.py:594–597`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:594)、[`825–826`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:825)

成功路径没有像失败路径那样单列 `FileNotFoundError`。若 tmp 已被并发删除，仍会提示“临时文件未能清理、请手动删除”。这是误告警，不影响最终 target。

新加的“源目录项持久化未确认” warning 本身没有发现误设或漏设。

## fd 结论

未发现普通成功或 `OSError` 分支上的确定性 fd 泄漏：

- `_fsync_dir` 使用 `finally`；
- rollback、发布复核和 undo 的读取 fd 均有 `finally`；
- create 的目录 fd 在外层 `finally` 关闭；
- 留痕写 fd 由 `with os.fdopen(...)` 管理。

`close()` 自身失败时的 POSIX 状态未做故障注入，不能据静态代码证明绝对无泄漏，但没有普通可达泄漏证据。

## 承重性、回归与限制

- 19 个变体全部如期变红；还原前后均为 `68 passed`，`RESULT: PASS`。
- 还原后实现 SHA-256 与基线完全相同：`166a1cf18be4dd66fb5817882dc7753d399a5eb998a89f58af6d4ab99c072ce1`。
- 指定回归：`173 passed in 13.49s`。
- 最终 `git diff --exit-code` 为 0，`git status` 干净。
- 第一次 pytest 因只读沙箱没有可写临时目录而在收集前失败；授权重跑后通过，不是实现失败。
- 未打开测试源码或 round-4 处置文档；仓库源码人工阅读仅限指定实现文件。
- 没有对本轮新发现做额外故障注入，因此崩溃后的实际文件系统结果仍属静态控制流与耐久性模型结论。

## 收敛性判断

**建议继续第 6 轮，预期收益仍为正。** 原因不是继续搜边角，而是 HIGH-1 是集中、可整改且可能造成不可逆数据丢失的确定控制流错误；HIGH-2 则直接影响撤销回执可信度。

第 6 轮若关闭这两个 HIGH，建议即停止继续扩轮，并将以下事项写入验收单后结案：

- create 目录 fsync 仍是 best-effort；
- pathname/inode 极窄竞态仍存在；
- tmp `ENOENT` 可能产生保守假 warning；
- 本次只验证了定向套件，不代表全量 CI、live UAT 或生产文件系统耐久性。

**残留清单：BLOCKER 0 / HIGH 2 / MEDIUM 2 / LOW 1。**



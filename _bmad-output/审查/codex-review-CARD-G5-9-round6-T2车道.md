# Codex 复核存档 — CARD-G5-9 round-6（定向终止轮）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30 · **过滤器 0 命中**
> **审阅对象**: `recap_exam_build.py` @ `d88892f8`
>
> ## 本轮定位（round-5 复核者自己定的）
>
> > 建议继续第 6 轮，但应是**定向终止轮**，不再开放式扩面。
>
> ⇒ 提示词把「不要开放式扩面」写成**硬约束**：范围外发现只列 MEDIUM/LOW、不计入 HIGH。
> 复核者遵守了：「**范围外观察：无。本轮未开放式扩面。**」
>
> ## 裁决
>
> **HIGH-1 CLOSED / HIGH-2 STILL-OPEN（2a 已关，2b 仍有确定性反例）⇒ 仍需一轮**
> 残留清单：**HIGH 1 / MEDIUM 0 / LOW 0 / INFO 0** —— MEDIUM 与 LOW 首次全部归零。
>
> ## 2b 的三条反例（全部属实，已整改）
>
> 1. `EINVAL/ENOTSUP` 被误归为 `deleted` —— 「不支持 fsync 目录」同样意味着**持久化未获确认**，
>    却被当成已确认，回执可能声称「已撤销该文件」而崩溃后目标重现。
> 2. ⛔ **首次 `deleted_unsynced` 分支必然抛 `UnboundLocalError`** —— 该调用点接收的是
>    `rb_err`，却读了尚未赋值的 `rb_err2`。此刻目标**已 unlink**，异常又不属 `OSError`
>    ⇒ 越过外层捕获、**删完了却没有任何结构化回执**。这是我引入的确定性 bug，
>    `ruff check` 与 73 个测试都没抓到——因为**没有测试走过首次调用点的这个状态**。
> 3. 二次 `deleted_unsynced` 的最终文案仍输出「已发布的目标仍在 vault 里」，与事实相反。
>
> ## 复核者给出的四条关闭条件（已逐条落地）
>
> 1. 所有目录 `fsync` 未确认情形均产生 `deleted_unsynced`；
> 2. 首次调用点不再引用错误变量；
> 3. `deleted_unsynced` 回执明确为「当前已删除，但持久化未确认、崩溃后可能重现」；
> 4. **三个调用点的四态矩阵均有承重验证**。
>
> 整改与判据见 `codex-review-CARD-G5-9-round6-处置.md`。

---

# 第 6 轮定向终止复核报告

## 结论先行

> **两条 HIGH 未全部 CLOSED。**
>
> - **HIGH-1：CLOSED**
> - **HIGH-2：STILL-OPEN**（2a 已关闭，2b 仍存在确定性反例）
>
> **建议：仍需一轮。** 下一轮应继续定向验证 HIGH-2，不应开放式扩面；当前不能结案。

复核对象为分支 `card/s6-recap`、提交 `d88892f8e8c4db39767a0f37164ba1e2c6e4b6eb`。

## HIGH-1 — `unsupported` fail-closed

**判定：CLOSED**

控制流成立：

- `_fsync_dir()` 对 `EINVAL/ENOTSUP` 返回带非空原因的 `unsupported`：[L313](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:313)。
- undo 调用方同时阻断 `failed` 和 `unsupported`：[L1026](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1026)、[L1032](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1032)。
- 拒绝分支在删源前直接返回：[L1033](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1033)、[L1049](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1049)。
- undo 唯一的源文件删除点位于其后：[L1151](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1151)。

未发现 `unsupported` 后仍可走到删源的其他路径。

正常支持目录 `fsync` 的文件系统会返回 `ok`，不会被误拒。路径被替换、权限不足或持久化无法确认时拒绝属于预期 fail-closed。

拒绝时状态与回执一致：

- vault 内源文件未动；
- vault 外留痕已经写入并完成文件自身 `fsync`，但目录项耐久性未确认；
- 回执为 `undone:false`，明确说明“未删除 vault 内文件”“持久化未获确认”，并给出当前 `retained_at`：[L1034](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:1034)。

## HIGH-2 — 撤销状态与回执一致性

**判定：STILL-OPEN**

- **HIGH-2(a)：CLOSED。** 第二次 rollback 为 `deleted/absent` 时确实清除了第一次 `kept` 留下的旧 note：[L587](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:587)、[L591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:591)。
- **HIGH-2(b)：STILL-OPEN。**

### 四态 × 三调用点

| 状态 | 首次撤销 L561 | 外层二次撤销 L584 | 目录移出后撤销 L814 |
|---|---|---|---|
| `deleted` | 正确清 `published` | 正确清旧 note | 正确声称已撤销，但依赖 helper 状态真实 |
| `absent` | 正确 | 正确清旧 note | 正确声称已不存在 |
| `deleted_unsynced` | **错误：读取未赋值的 `rb_err2`** | 状态更新，但最终文案反述事实 | 分派文案本身正确 |
| `kept` | 记录 note，并进入第二次撤销 | 以最终结果重写 note | 正确说明文件仍在 |

### 决定性反例

1. **`EINVAL/ENOTSUP` 被误归为 `deleted`**

   `_rollback_published()` 在目录 `fsync` 抛出 `EINVAL/ENOTSUP` 时没有返回 `deleted_unsynced`，而是落到 `deleted`：[L455](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:455)、[L458](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:458)、[L460](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:460)。

   此时删除持久化并未确认，却可能被回执为“已撤销该文件”；崩溃后目标重现时，回执与持久事实相反。

2. **首次 `deleted_unsynced` 分支必然抛 `UnboundLocalError`**

   该调用接收的是 `rb_err`，却读取尚未赋值的 `rb_err2`：[L561](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:561)、[L567](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:567)。

   此时目标已经 `unlink`，异常又不属于 `OSError`，会越过 [L575](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:575) 的捕获并无结构化回执外逸。

3. **二次 `deleted_unsynced` 的最终文案仍自相矛盾**

   状态被更新为“已删但持久化未确认”后，统一模板仍输出“已发布的目标仍在 vault 里”：[L593](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:593)、[L612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:612)。

`os.fsync(dir_fd)` 的正常系统调用失败通常是 `OSError`；未验证合法 fd 在真实环境中自然抛出其他异常。但代码确实未封闭非 `OSError`，且上述 `UnboundLocalError` 已构成确定性的“删后无回执”路径。

## 承重性与回归

- 24 个变体：全部如期变红。
- 还原后字节与备份逐字相同。
- 还原后内部套件：`73 passed`。
- 最终输出：`RESULT: PASS — 全部新门均为承重门`。
- 指定回归：`178 passed in 13.63s`。

这些结果证明现有门具备承重性且一般回归通过，但没有覆盖或推翻 HIGH-2 的当前实现反例。

测试后文件 SHA-256 仍为：

`16a6c8aabd15408f98c41e8d31d62abfffd3fdd0474e6570477d251264f44f4f`

`git diff` 与 `git status --porcelain` 均无输出，工作树干净。未读取禁止的测试源码。

## 范围外观察

无。本轮未开放式扩面。

## 未验证部分

- 未在真实返回 `EINVAL/ENOTSUP` 的文件系统上执行断电/崩溃恢复实验。
- 未运行用户指定两条命令以外的全项目 CI 或完整测试集。
- 对抗测试文件仅由 pytest 执行，复核过程中未打开或读取其源码。

## 下一轮唯一关闭条件

仅需定向确认：

1. 所有目录 `fsync` 未确认情形均产生 `deleted_unsynced`；
2. 首次调用点不再引用错误变量；
3. `deleted_unsynced` 回执明确为“当前已删除，但持久化未确认、崩溃后可能重现”；
4. 三个调用点的四态矩阵均有承重验证。

## 残留清单

按 round-5 finding 计数，不重复计算同一 HIGH 下的子反例：

- **HIGH：1**
- **MEDIUM：0**
- **LOW：0**
- **INFO：0**



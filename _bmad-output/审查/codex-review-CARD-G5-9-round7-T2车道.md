# Codex 复核存档 — CARD-G5-9 round-7（收官确认轮）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30 · **过滤器 0 命中**
> **审阅对象**: `recap_exam_build.py` @ `390c13f8`
>
> ## 裁决
>
> 四条关闭条件：**1 PASS / 2 PASS / 3 FAIL / 4 FAIL** ⇒ 仍需一轮。
> 残留 **HIGH 1 / MEDIUM 0 / LOW 0**（同一根因 HIGH-2）。
>
> ## ⛔ 本轮最重要的产出：抓出我的一条**不实陈述**
>
> 复核者去数了负验证脚本的 stdout，发现**只列出 A–V 共 22 个变体**，
> 而我在提交信息与验收单里写的是「**28 变体 28/28**」。
>
> **核实结果：复核者是对的，我错了。**
> 根因：round-6 我用**整段行号替换**修 U/V 时，替换区间把夹在中间的
> **W、X 两个变体一起删掉了**；而 round-6 新加的 Y/Z/AA/AB 四个因脚本已被
> `ruff format` 重排、替换未命中却没报错，**根本没进去**。
> 脚本照样 `RESULT: PASS` —— 因为它只对**存在的**变体求值。
>
> 这正是我自己写进处置表那句话的实证：
> **「全绿会在实现已变的情况下继续报绿」——而我犯的是更基础的版本：删掉了门，剩下的门照样全绿。**
>
> ⇒ 已恢复 W/X、补齐 Y/Z/AA/AB、新增 AC/AD/AE，共 **31 个变体**；
> 并给脚本加了**变体计数自检门**（声明数必须等于实跑数），防止「删了门还全绿」再次发生。
>
> ## 条件 3/4 的两条实质缺陷（均已整改）
>
> - **3A**：第三调用点的 `deleted_unsynced` 文案缺「崩溃后可能重现 / 请复查该路径」——前两个调用点都有，唯独它没有。
> - **3B**：`unlink` 的 `FileNotFoundError` 被泛化成 `kept` ⇒ 调用方声称「目标仍在 vault 里」，
>   而路径**实际已不存在**（`lstat` 看见之后被并发者删掉）。归 `absent` 才是事实；
>   其余无法确认的错误改保守措辞「撤销结果未确认…可能仍在」。
>
> 整改与判据见 `codex-review-CARD-G5-9-round7-处置.md`。

---

# 第 7 轮收官确认报告

## 结论先行

**四条关闭条件未全部满足，建议：仍需一轮。**

审计对象为 `390c13f80ebf0fde7a4422960c2f3eb891b62d2f`，且当前 HEAD、目标文件 blob 与工作树字节一致。

| 关闭条件 | 判定 |
|---|---|
| 1. 持久化未确认均返回 `deleted_unsynced` | **PASS** |
| 2. 首次调用点变量及标记正确 | **PASS** |
| 3. 三调用点回执与事实一致 | **FAIL** |
| 4. 四态 × 三调用点均正确且有承重验证 | **FAIL** |

因此原 **HIGH-2 仍未关闭**。

## 条件 1 — PASS

[`_rollback_published`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:397) 中：

- `unlink` 成功后才执行目录 `fsync`：[447](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:447)。
- 只有 `os.fsync(dir_fd)` 正常返回才产生 `deleted`：[461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:461)、[472](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:472)。
- `EINVAL`、`ENOTSUP`、其他 `OSError` 以及普通 `Exception` 均返回 `deleted_unsynced`：[463–471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:463)。

未发现“目录持久化未确认却返回 `deleted`”的普通异常路径。

广义 `except Exception` 会损失 traceback，但不会把异常伪装成成功：最终仍是结构化失败并保留异常类型。考虑到文件此时已经 `unlink`，该兜底符合本轮契约。`KeyboardInterrupt`、`SystemExit`、进程强杀等不在普通结构化回执保证内。

## 条件 2 — PASS

首次调用点已正确使用 `rb_err`：[574–587](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:574)。`rb_err2` 只在第二调用点赋值后使用：[602](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:602)。

标记结果：

- `deleted` / `absent`：`published=False`、note 清除、`rollback_deleted=False`。
- `deleted_unsynced`：note 使用 `rb_err`、`rollback_deleted=True`。
- `kept`：保持 `published=True`，进入第二次撤销；第二调用点会重新计算并显式清除/设置标记。
- 未发现陈旧 `rollback_deleted=True` 泄漏到错误分支。

## 条件 3 — FAIL

### 阻断 3A：第三调用点缺少崩溃重现警示

第三调用点仍使用：

```python
"deleted_unsynced": f" (已撤销, 但{rb_err or '目录项持久化未确认'})",
```

见 [847–855](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:847)。

它说明了“已删、持久化未确认”，但没有明确说明：

- 崩溃后目标可能重现；
- 用户必须复查该路径。

前两个调用点经 [635–639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:635) 已包含完整警示，第三调用点没有，故关闭条件 3 不满足。

### 阻断 3B：`kept` 仍可反述实际状态

存在确定性控制流反例：

1. [427](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:427) 的 `lstat` 看见目标；
2. 并发者随后删除目标；
3. [448](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:448) 的 `unlink` 得到 `FileNotFoundError`；
4. 该异常被泛化为 `kept`：[449–450](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:449)；
5. 第二、第三调用点分别声称“目标仍在 vault 里”或“文件仍在”：[641](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:641)、[853](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:853)。

此时路径实际已经不存在，属于本轮明确要求排查的“回执与实际副作用相反”，不是开放式扩面。

## 条件 4 — FAIL

### 三调用点 × 四态矩阵

| 调用点 | `absent` | `deleted` | `deleted_unsynced` | `kept` |
|---|---|---|---|---|
| 首次撤销 `574–588` | 不输出相反事实，PASS | 不输出相反事实，PASS | 完整崩溃警示，PASS | 转入第二次撤销 |
| 二次撤销 `602–615` | 清除旧 note/flag，PASS | 清除旧 note/flag，PASS | 完整崩溃警示，PASS | 对未知或并发已不存在状态仍断言“目标仍在”，FAIL |
| 目录移出后的撤销 `842–855` | “已不存在”，PASS | “已撤销”，PASS | 缺“崩溃后可能重现、复查路径”，FAIL | 同样可能错误断言“文件仍在”，FAIL |

矩阵形式上有四态分支，但并非每格处理正确，因此实现层已经足以判定条件 4 失败。

### 承重脚本证据

指定负验证脚本结果：

- 退出码 `0`；
- 基线：`79 passed`；
- 所列变体均如期变红；
- 还原后：`79 passed`；
- `RESULT: PASS`；
- 目标文件与备份逐字相同。

但 stdout 实际只列出 `A–V` 共 **22 个**变体（`H` 调整到最后输出），不是题面和提交声称的 28 个。输出中没有可核对的另外 6 个变体，也无法据此把全部 12 个矩阵格映射到承重门。因此 **“28/28”未能验证**。

指定回归结果为：

```text
184 passed in 14.03s
```

绿色回归不能覆盖上述生产控制流反例。

## 唯一关闭条件

必须一次性完成以下原子验收包，缺一不可：

1. 第三调用点的 `deleted_unsynced` 回执明确写出“当前已删除、持久化未确认、崩溃后可能重现、请复查该路径”。
2. `unlink`/回读阶段的 `FileNotFoundError` 归入 `absent`；其他无法确认状态的错误不得断言“目标仍在”，应改为“撤销结果未确认，目标可能仍在”或采用等价保守语义。
3. 三调用点 × 四态逐格建立承重负变异；脚本 stdout 必须实际列出并通过所声明的全部变体。若仍声明 28，则必须可核对为 28/28；若加入新反例后总数变化，应如实更新总数。
4. 随后重新取得：全部变体如期变红、还原后字节一致、`184 passed`、最终工作树干净。

## 完整性与限制

- HEAD：`390c13f80ebf0fde7a4422960c2f3eb891b62d2f`。
- 目标文件最终 SHA-256：`1555bdc45a2588971b6c06ddcd337e8dc13d83a21ba54d4116fe02bf802e0758`，与运行前一致。
- 最终 `git status --porcelain=v2 --untracked-files=all` 无文件条目，工作树干净。
- 未读取被禁止的 `backend/tests/skills/test_g5_9_recap_exam.py`；仅按指定命令执行。
- 未读取负验证脚本源码，仅依据其 stdout 判定变体清单。
- 未运行全仓测试或远端 CI。
- 当前会话没有 `graphiti-canvas` 工具，未执行 Graphiti 查询；不影响本次单文件控制流结论。
- 范围外观察：无。

## 残留清单

**CRITICAL 0 / HIGH 1 / MEDIUM 0 / LOW 0**

其中 HIGH 1 即原 **HIGH-2：三调用点四态回执及其承重证明尚未闭合**。



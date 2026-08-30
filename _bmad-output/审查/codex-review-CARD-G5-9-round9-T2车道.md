# Codex 复核存档 — CARD-G5-9 round-9（定向终止轮）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30 · **过滤器 0 命中**
> **审阅对象**: `recap_exam_build.py` + `round1-high-negverify.py` @ `bc918dbb`
>
> ## 裁决
>
> 条件 **1 PASS / 2 FAIL / 3 FAIL / 4 PASS**；残留 **HIGH 2 / MEDIUM 0 / LOW 0**。
>
> ## ⭐ 复核者的收敛性判断（本轮特意请其独立给出）
>
> > 再开这一轮的预期收益**仍为正**，因为是在补齐已经明确承诺但缺失的逐格证据，
> > 并封住零测试假红；**但已经进入明显的边际收益递减区。
> > 完成上述唯一条件后应停止扩轮，不再开放式寻找新问题。**
>
> ## 两条 FAIL
>
> **条件 3 的反例极精彩，也是我该自己想到的**：
> ```
> run_pytest("__selector_matches_nothing__") → (5, "96 deselected")
> ```
> `rc=5` 是 pytest 的「没有收集到任何测试」，而我的脚本只判 `rc != 0` 就记「如期变红」
> ⇒ **一个匹配不到任何测试的 selector 会被判为承重**。
> 这与我修过的「否定断言恒真」是同一类错：**把「没有发生」当成了「验证通过」**。
>
> **条件 2**：AG/AH 用了合并 selector（`test_matrix_..._each_state` 覆盖全部 8 格 / 4 格），
> 只有 2 格明确承重；其余格没有独立变异与独立 selector，不能逐格归因。
>
> 两条已全部整改，见 `codex-review-CARD-G5-9-round9-处置.md`。
>
> 复核者自述限制：按禁令未读测试源码；仅执行指定 pytest。

---

# 第 9 轮定向终止复核

## 结论

**四条未全部满足：仍需一轮。**

| 条件 | 判定 |
|---|---|
| 1. 回读 `FileNotFoundError → absent` | PASS |
| 2. 三调用点 × 四态、12 格独立变异 | **FAIL** |
| 3. 独立冻结名称与真实执行集合 | **FAIL**（主要结构已修，但仍存在零执行假阳性） |
| 4. 变体变红、字节还原、201 passed、净树 | PASS |

## 逐项证据

### 1. PASS

回读块在宽泛 `except OSError` 前单列了 `FileNotFoundError`，并返回 `("absent", None)`：[recap_exam_build.py:435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:435)。

关键顺序：

- `except FileNotFoundError`：第 444 行
- `return "absent", None`：第 449 行
- `except OSError`：第 450 行

第三调用点确实传入 `expect_sha`：[recap_exam_build.py:855](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:855)。

### 2. FAIL — 没有 12 个可单独归因的格子

证据脚本只有两个新增矩阵变体：

- AG 只弱化调用点①的 `deleted_unsynced`，却使用合并 selector `test_matrix_callsite1_2_consumes_each_state`：[round1-high-negverify.py:508](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:508)
- AH 只弱化调用点③的 `absent`，selector 合并该调用点全部四态：[round1-high-negverify.py:519](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:519)

实跑结果进一步确认：

- AG：`1 failed, 7 passed`
- AH：`1 failed, 3 passed`

即 12 个参数格可能被执行了，但只有两个 mutation、各自只压红一个格；其余格没有独立变异与独立 selector，不能逐格归因。明确违反“不用合并调用点/状态代替逐格证明”。

### 3. FAIL — 冻结门主体正确，但不能证明测试项实际执行

已正确的部分：

- `EXPECTED_NAMES` 是独立字面冻结常量，不由 `VARIANTS` 生成：[round1-high-negverify.py:532](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:532)
- 当前冻结、定义均为 34 个且唯一。
- mutation 未命中会在第 595 行 `continue`，不会运行或记名。
- `executed_names.append` 确实位于 `run_pytest` 返回后：[round1-high-negverify.py:598](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:598)
- 删除 X 与跳过 X 的独立模拟均得到 `33 / 34，缺失 ['X']`。

但脚本把任何 `rc != 0` 都当成“如期变红”：[round1-high-negverify.py:600](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:600)。

定向反例：

```text
run_pytest("__round9_selector_matches_nothing__")
→ (5, "96 deselected in 0.03s")
```

该路径会追加 `executed_names`，并把零测试执行误报为“如期变红”。所以：

- 能检出误删变体：是
- 能检出 mutation 未命中而 `continue`：是
- 能检出 selector 零命中、目标测试实际没跑：**否**

### 4. PASS

指定负验证：

- 基线：`96 passed`
- 34/34 当前变体均输出实际 `failed`，没有零命中
- 冻结期望 / 定义 / 实跑：`34 / 34 / 34`
- 还原后：`96 passed`
- 被测文件还原 SHA-256：`57ffeb405ecbef3bd86322771c4a5bb67428bcbbb2fd64a426c4eb4d2ce50b44`

指定回归：

```text
201 passed in 14.01s
```

最终：

- HEAD：`bc918dbbfbfcaaede5885d421c377cdfe1d8d2cb`
- `git status --short --untracked-files=all`：无输出
- 两份准入文件相对 HEAD 无差异

首次回归在平台只读沙箱内因没有可写临时目录而在收集前失败；获准按同一命令重跑后得到上述 `201 passed`，不属于测试失败。

## 唯一关闭条件

将 AG/AH 合并门替换为明确命名的 **12 个独立变体**（调用点①②③ × `deleted`、`deleted_unsynced`、`absent`、`kept`）：

1. 每格只弱化对应调用点的对应状态。
2. 每格使用一个精确、独立 selector；不得共享 helper、合并状态、合并调用点或使用 `or`。
3. 每格必须确认目标测试确实执行并因 mutation 失败；仅接受 pytest `rc=1` 且输出明确失败项，拒绝 `rc=5`、收集错误和基础设施错误。
4. 手工同步独立冻结名称集合；再证明误删与跳过任一格都会失败。
5. 重跑后取得：12 格逐格变红、全部既有变体变红、字节一致、`201 passed`、最终净树。

## 收敛性判断

再开这一轮的预期收益仍为正，因为是在补齐已经明确承诺但缺失的逐格证据，并封住零测试假红；但已经进入明显的边际收益递减区。完成上述唯一条件后应停止扩轮，不再开放式寻找新问题。

## 未验证边界

按禁令未读取 `backend/tests/skills/test_g5_9_recap_exam.py` 内容，因此未检查其内部是否使用共享 helper；仅执行了指定 pytest。仅凭获准证据脚本已经足以判定条件 2 不满足。

**残留清单：BLOCKER 0 / HIGH 2 / MEDIUM 0 / LOW 0。**

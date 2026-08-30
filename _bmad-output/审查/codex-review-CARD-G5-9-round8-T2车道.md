# Codex 复核存档 — CARD-G5-9 round-8（终局确认轮）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30 · **过滤器 0 命中**
> **审阅对象**: `recap_exam_build.py` @ `a405dfda`
>
> ## 裁决
>
> 四条关闭条件 **1 PASS / 2 FAIL / 3 FAIL / 4 PASS** ⇒ 仍需一轮。残留 **HIGH 3**。
>
> ## 三条 HIGH 的性质各不相同，处置也不同（但**全部实修**）
>
> | # | 发现 | 性质 | 处置 |
> |---|---|---|---|
> | **HIGH-1** | 3B 只修了 `unlink` 一半，**回读块仍被宽泛 `except OSError` 兜住** ⇒ `lstat` 成功后并发者删文件、`os.open` 抛 `FileNotFoundError` 被归 `kept`，回执说「目标可能仍在」而它已不存在 | **产品行为错误** | ✅ 回读块单列 `FileNotFoundError → absent`（变体 **AF**） |
> | **HIGH-3** | ⛔ **我 round-7 加的自检门是循环论证**：`ran` 在 mutation 校验与 pytest 执行**之前**就自增，而「声明数」取同一个 `VARIANTS` 的长度 ⇒ 再误删 W/X 两数**一起减少仍显示一致**；mutation 未命中、pytest 没跑也计入「实跑」 | **方法论错误** | ✅ 改为**独立冻结**的 `EXPECTED_NAMES` 常量 + 只在 pytest 真返回后记名 + 三集合一致校验。**并做了验伪**：模拟误删变体 X，新门精确报「定义 30 / 期望 31 / 缺失 ['X']」 |
> | **HIGH-2** | 12 格「调用点 × 状态」矩阵只有 2 格明确承重；共享 helper 变异只证明**生产端**，不能证明三个调用点**分别正确消费**四态 | **验证工装的归因完整性** | ✅ 评估后判定可做（每格一条注入门）⇒ **补齐 12 格**，不移交（变体 **AG/AH**） |
>
> ⚠️ HIGH-2 本可按停轮规则理由里那句「发现性质已从产品缺陷转为验证工装归因完整性」结案移交。
> 本卡的选择是：**先评估工作量，能做就做**——12 格各一条注入式测试，代价可接受，
> 且它确实堵住了「某调用点误消费某状态而无门察觉」的真实缺口。
>
> 复核者自述限制：严格未读测试源码；未运行全量 CI。

---

# 结论：仍需一轮

commit `a405dfda6a5710b2e8ed8d40c4536db93605d1a5` 的四条关闭条件为：

| 条件 | 判定 |
|---|---|
| 1. 第三调用点 `deleted_unsynced` 回执 | **PASS** |
| 2. `FileNotFoundError` 与保守措辞 | **FAIL** |
| 3. 3×4 承重负变异及可信计数 | **FAIL** |
| 4. 全红、字节一致、188 passed、工作树干净 | **PASS** |

## 阻断证据

### HIGH-1：回读 `FileNotFoundError` 未归 `absent`

`unlink` 阶段已正确处理，但回读阶段仍由宽泛的 `except OSError` 捕获：

- [`recap_exam_build.py:434`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:434)
- [`recap_exam_build.py:443`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:443)

可达路径是：`lstat` 成功 → 并发者删除文件 → `os.open` 抛 `FileNotFoundError` → 被归为 `kept`，外部回执变成“撤销结果未确认……目标可能仍在”。

第三调用点传入 `expect_sha`，因此该路径实际可达；正确结果应走 [`recap_exam_build.py:855`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:855) 的“该文件已不存在”。

### HIGH-2：3×4 逐格承重证明未建立

严格按“调用点消费语义”映射，现有 31 个变体中只有 **2/12 格明确承重**：

| 调用点 | `deleted` | `deleted_unsynced` | `absent` | `kept` |
|---|---|---|---|---|
| ① 首次撤销 | 缺 | **AA/AB** | 缺 | 无法独立归因 |
| ② 二次撤销 | 无法独立归因 | 缺 | 无法独立归因 | 无法独立归因 |
| ③ 目录移出 | 无法独立归因 | **AE** | 缺 | 缺 |

`AC/AD` 等共享 helper 变异只能证明状态生产端，不能证明三个调用点分别正确消费四态；`P/U/K` 又存在共享 renderer、合并状态或 `or` selector，不能逐格归因。

### HIGH-3：计数自检不是独立可信门

[`round1-high-negverify.py:528`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:528) 初始化 `ran`，但在 mutation 校验和 pytest 执行前即递增；[`round1-high-negverify.py:571`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:571) 又以同一个 `VARIANTS` 列表的长度作为“声明数”。

因此：

- 再次误删 W/X 时，`len(VARIANTS)` 与 `ran` 会一起减少，仍显示一致。
- mutation 未命中、pytest 未执行，也已计入“实跑”。
- 该比较不能防止上一轮同型漏门。

## 实际运行结果

负变异脚本本轮 stdout：

- 实际列出 **31 个**变体；
- W/X、Y/Z/AA/AB、AC/AD/AE 均存在；
- 31 项均输出“如期变红”；
- 自检行实际为：`声明 31 个; 本次实跑 31 个`；
- 脚本退出码 `0`。

还原与回归：

- 目标及备份 SHA-256 均为  
  `3c5e2a486fe053d557f14b0f7d561ec5bf3838dadae025eabeb89a4e20476c8e`
- 独立 `cmp` 退出码 `0`；
- 指定回归：**188 passed in 13.76s**；
- 最终 `git status --short --branch` 仅显示 `## card/s6-recap`，工作树干净。

## 唯一关闭条件

提交一个原子整改并重新复证：

1. 回读块在 `except OSError` 前单列 `FileNotFoundError → ("absent", None)`。
2. 为三个调用点 × 四态建立可单独归因的 12 格变异清单；不得用共享 helper、合并状态或 `or` selector 代替逐格证明。
3. 使用独立冻结的预期名称集合/数量；仅在对应 pytest 实际返回后记录 `executed_names`，校验定义集合、唯一性和执行集合完全一致。
4. 如实更新变体总数，再取得全部变体如期变红、还原字节一致、`188 passed`、最终工作树干净。

## 验证边界

未读取、搜索或打开被禁止的 `backend/tests/skills/test_g5_9_recap_exam.py`；仅按指定命令执行。因此未直接审查其断言内容。未运行全量 CI，本报告只确认用户指定的负变异与 188 项回归。

## 残留清单

- CRITICAL：0
- HIGH：3
- MEDIUM：0
- LOW：0



# Codex 复核存档 — CARD-G5-9 round-10（终局：可结案）

> **模型**: `gpt-5.6-sol` · `ultra` · `--sandbox read-only` · 2026-08-30 · **过滤器 0 命中**
> **审阅对象**: @ `8dbd14a6`
>
> ## 🎯 裁决：**可结案**
>
> - 条件 2（12 格可单独归因）：**PASS，已关上**
> - 条件 3（零命中不得算变红）：**PASS，已关上**
> - **HIGH 0 / MEDIUM 0 / LOW 2 / INFO 3**
> - *"未发现不可逆数据丢失或回执与实际写入相反的新问题。
>   round-9 的『完成后停止扩轮』判断继续适用，**不建议再开第 11 轮**。"*
>
> ## 复核者的十轮总结（原文）
>
> > 经过 10 轮，G5-9 已形成**实现、逐格负验证、完整回归和字节还原的闭环**，可正式结案；
> > 剩余的是 `cs1 × kept` 必经二次撤销及合并状态分支等**结构性形态**，
> > **不是尚可修复的正确性缺口**。
>
> ⭐ 这句区分是终点的真正标志：**能识别「这条不是缺陷而是形态」，才是到了终点**。
>
> ## 两处「如实拒绝硬凑」被复核者认可
>
> 1. **`cs1 × kept` 无独立出口** —— 判为 `INFO`：*"这是二次撤销覆盖首次状态的结构事实；
>    已由『恰好调用两次』的承重门锁定，**不是漏测或待修缺陷**。"*
> 2. **M1/M2 的 `deleted`/`absent` 共享生产分支锚点** —— 判为 `INFO`：
>    *"两对 mutation 文本相同，但变体、参数化 selector 和执行过程均独立；
>    现场每格只命中一个测试并单独变红，**不影响逐格归因**。"*

---

# Round‑10 独立复核报告

## 结论

**可结案。**

- 条件 2：**PASS，已关上**
- 条件 3：**PASS，已关上**
- `HEAD`：`8dbd14a6a387120111c2bfbfa08ede2efa81b062`
- 未发现不可逆数据丢失或回执与实际写入相反的新问题。
- round‑9 的“完成后停止扩轮”判断继续适用，**不建议再开第 11 轮**。

## 条件 2：12 格可单独归因

12 个 `M1/M2/M3 × 四态` 变体均为直接定义、独立 selector，且 12 个 selector 内无 `or`：[round1-high-negverify.py:509](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:509)。冻结集合也独立列出全部 12 格：[round1-high-negverify.py:644](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:644)。

动态结果：

- 12 格均各自执行为 `1 failed, 96 deselected`
- 44 个变体全部如期变红
- 冻结期望 / 定义 / 实跑：`44 / 44 / 44`

### `cs1 × kept` 例外判断

**声明属实，当前处理恰当，不应硬造独立出口。**

首次撤销返回 `kept` 时不会清除 `published`，随后固定抛出 `OSError`：[recap_exam_build.py:587](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:587)。外层因 `published` 仍为真而必然执行第二次撤销，并覆盖最终回执状态：[recap_exam_build.py:614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py:614)。

因此首次 `kept` 没有独立最终回执；`M1-kept` 锁定“撤销必须执行恰好两次”正是可观察的结构事实：[round1-high-negverify.py:542](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:542)。

## 条件 3：零命中不得算变红

当前判据解析 `passed`/`failed`，并仅允许 `rc==1 && failed>0` 算承重：[round1-high-negverify.py:727](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s6-recap/_bmad-output/审查/g5-9-evidence/round1-high-negverify.py:727)。

现场核验：

| 场景 | 实际结果 | 判定 |
|---|---:|---|
| 零命中 | `rc=5, 97 deselected` | 拒绝，不算变红 |
| 正常变红 | `rc=1, failed>0`；12 格各 `1 failed` | 算承重 |
| 弱化后仍全绿 | `rc=0, 1 passed, 96 deselected` | 判非承重 |

`deselected` 已不参与零命中判断，v2 的误判已消除。

## 承重、回归与还原

- 负验证：`RESULT: PASS — 全部新门均为承重门`
- 还原后负验证套件：`97 passed`
- 指定回归：`202 passed in 16.42s`
- 被测文件 SHA‑256：`57ffeb405ecbef3bd86322771c4a5bb67428bcbbb2fd64a426c4eb4d2ce50b44`
- 工作区文件 blob 与 `HEAD` blob 相同：`2c6848bf5ba61e67c496b773c5d80d4eb362c525`
- 最终 `git status --porcelain`：**空，工作树干净**

## 必须写入验收单的残留清单

1. **INFO — `cs1 × kept` 无独立最终回执出口。**  
   这是二次撤销覆盖首次状态的结构事实；已由“恰好调用两次”的承重门锁定，不是漏测或待修缺陷。

2. **INFO — M1/M2 的 `deleted` 与 `absent` 共享生产分支锚点。**  
   两对 mutation 文本相同，但变体、参数化 selector 和执行过程均独立；现场每格只命中一个测试并单独变红，因此不影响逐格归因。

3. **LOW — `passed+failed==0` 的诊断文案可能把纯 skipped/xfailed/error 称为“零命中”。**  
   这些情况仍会令验证失败，属于 fail‑closed，不会产生假承重。

4. **LOW（范围外观察）— `-k` 子串选择及“stdout 最后一行”解析存在未来维护脆弱性。**  
   名称碰撞或异常插件输出可能造成假阴性，但不会把零命中或全绿误算为承重；当前实跑均精确命中一项。

5. **INFO — 禁读测试源码带来的验证边界。**  
   本轮没有打开被禁止的测试文件，因此未静态核验测试体内部是否使用共享 helper；只确认负验证脚本自身为 12 个直接定义，并通过指定 pytest/负验证入口完成动态核验。

**十轮一句话总结：**经过 10 轮，G5‑9 已形成实现、逐格负验证、完整回归和字节还原的闭环，可正式结案；剩余的是 `cs1 × kept` 必经二次撤销及合并状态分支等结构性形态，不是尚可修复的正确性缺口。

**残留清单四级条数：HIGH 0 / MEDIUM 0 / LOW 2 / INFO 3。**

> 批次: BATCH-2026-09-11-第十四批 · 车道 T3（`card-t3-review`）· 卡 CARD-G6-9c-R2 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`--version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R2-r4.md)"`
> 审查绑定: `08100483 → 75f5102b`（送审时 HEAD = `75f5102b`；本轮审后按其意见又改了代码 ⇒ **不绑最终 HEAD**，另送 round-5 绑 `ebe0db58`）
> 会话头自证（抄 `.stderr` 中含版本 / model / reasoning 的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（L2） / `model: gpt-6-astra`（L5） / `reasoning effort: ultra`（L9）

---

复核绑定 **`08100483 → 75f5102b`**。结论：**1 HIGH + 3 LOW，整改尚未闭合**。两份副本均复现；既有问题不计入新增数量。

**BLOCKER：无。**

**HIGH：1 条。**

**HIGH-1｜本卡新增：多字节引用名仍能绕过长度限制，造成错日。**  
位置：[backend/app/core/display_tz.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:186)、[scripts/local_tz.py:187](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:187)。

`len(spec)` 统计 Unicode 字符，未限制传给 C 库的字节数。复现：

```python
spec = "AAA0<" + "中" * 170 + ">"
# 176 字符，516 UTF-8 字节
```

在 `2026-07-01T23:30Z`：

| 对象 | 结果 |
|---|---|
| BASE | 拒收，退 UTC：`07-01 23:30+00:00` |
| 本机 libc | 退 UTC：`07-01 23:30+00:00` |
| HEAD 两副本 | 接受：`07-02 00:30+01:00` |

标准侧引用名同样可复现。长度防线需要按实际编码后的字节衡量；不能由此推导出“所有非 ASCII 引用名都该拒”。

**MEDIUM：无。**

**LOW：3 条。**

**LOW-1｜本轮新增：上界统一截到 9998，漏掉合法的 9999 年季度。**  
位置：[backend/app/core/display_tz.py:299](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:299)、[scripts/local_tz.py:300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:300)。

复现 `AAA0BBB,M3.2.0,M11.1.0`，换算 `9999-07-01T23:30Z`：

- BASE：`9999-07-02T00:30+01:00`
- HEAD：`9999-07-01T23:30+00:00`

该北半球季度不需要计算 `year+1`，却被整体跳过。应区分本年规则计算与确实需要次年的分支。按极远年份影响评 LOW。

新门 [test_g6_9c_single_tz_source.py:595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:595) **没有守住上界**：内存变异为仅保留 `if year < 1:` 后，原三个时刻仍全部通过；9998 年七月提前命中，根本没有触及高端候选年。

**LOW-2｜本轮新增注释仍不准确：“跨几个年界”不足以决定是否需要 `y−2`。**  
位置：[test_g6_9c_single_tz_source.py:493](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:493)。

复现直接使用现有表第一条：

```text
start(2022) = 2023-01-01T04Z
end(2023)  = 2024-01-01T02Z
```

实际季度**只跨一个年界**，但覆盖 `2024-01-01T00:30Z` 的名义起始年仍是 `2022=y−2`。新写的“2024 季度跨两个年界”示例本身正确；将它推广成总区分点不成立。需要比较目标年份与**名义起始年**，同时考虑端点滚年。

**LOW-3｜本轮新增注释：长度及换行接受域的说明仍与实测不符。**  
位置：[backend/app/core/display_tz.py:183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:183)、[scripts/local_tz.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:184)、[test_g6_9c_single_tz_source.py:649](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:649)。

三处可直接证伪的断言：

- **507/508 不是统一的整串边界。** `"A"*507+"0BBB"` 总长 **511**，libc 接受；当前拒绝用例 `"A"*508+"0BBB"` 实际长 **512**。
- **“只退 UTC，不会归错日”不成立。** `"A"*252+"0BBB"` 总长 256；在上述七月探针，libc 日期为 **07-02**，HEAD 为 **07-01**。但 **BASE 同样归为 07-01，这是既有支持缺口，不计新增行为错误**。
- **“C 库拒绝所有带换行的串”过宽。** `AAA0<B\nBB>`、`AAA0<B\rBB>` 的换行在引用名内部，本机 libc 接受。HEAD 拒绝它们的行为相对 BASE 仍属既有缺口。

其余问题的核验结果：

- **空白与引用名：**尾部 TAB、VT、NBSP 均被正则拒绝；短引用名内部的这些字符，libc 也接受，未发现偏移分歧。不能将它们列为新增错误接受。
- **255 的现实影响：**本机 tzdata **2026c** 的 599 个 TZif、94 种不同尾串中，最长是 Pacific/Chatham 的 **44 ASCII 字节**。255 不影响这份系统样本，但不能证明所有现实自定义 TZ 都只有几十字符。
- **年份安全：**下界 `1` 正确；`9998` 足以避免候选年份计算越界，却有 LOW-1 的语义损失。J/n 分支的 `calendar.timegm` 也要求合法年份；未发现另一处显式年份递增。常规 9997/9998 探针通过，不能据此宣称整个 9998/9999 年安全。
- **四种指定偏移退化已被覆盖：**内存变异确认以下用例均不依赖另一侧检查顺带拦截。

| 退化 | 独立承重用例 |
|---|---|
| 删除 std 检查 | `AAA24BBB23` |
| 删除 dst 检查 | `AAA23BBB24` |
| 删除差值检查 | `AAA12BBB-12`，负向也会失败 |
| 差值去掉 `abs` | `AAA-12BBB12` |

16 拒绝＋3 正控对这四种变异有效，**并非完整输入域防线**，HIGH-1 就未被覆盖。±2h 的剩余说明均为历史引述；`s <= e` 的改写正确。

**既有、不重新计数：**同偏移换名＋搬桶；显式规则路径的偏移越界；真实墙钟越过 datetime 范围时的溢出。例如 `AAA24BBB,M3.2.0,M11.1.0` 的 `ValueError`、`AAA-1` 在公元 9999 年末的 `OverflowError`，BASE/HEAD 均复现。

验证采用本地内存加载：原样执行 40 个相关测试实例，并完成两副本共 1,578 个时刻探针；未运行写临时文件的完整 pytest 或端到端链路。六个范围内文件最终均与指定 HEAD 字节一致，全程未修改文件、联网或连接数据库。

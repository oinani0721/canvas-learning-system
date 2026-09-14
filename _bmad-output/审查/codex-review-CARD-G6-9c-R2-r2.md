> 批次: BATCH-2026-09-11-第十四批 · 车道 T3（`card-t3-review`）· 卡 CARD-G6-9c-R2 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`--version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R2-r2.md)"`
> 审查绑定: `08100483 → 130e2dd2 → 25933d55`（送审时 HEAD = `25933d55`；本轮审后按其意见又改了代码 ⇒ **不绑最终 HEAD**，另送 round-3）
> 会话头自证（抄 `.stderr` 中含版本 / model / reasoning 的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（L2） / `model: gpt-6-astra`（L5） / `reasoning effort: ultra`（L9）

---

**复核未通过：2 HIGH、2 MEDIUM、5 LOW。** 绑定 `08100483 → 130e2dd2 → 25933d55ede2b21bc907ff8b89dd2a03d40d26d0`。其中一条 HIGH 是 BASE 已有的同风险残留。

**BLOCKER：无。**

**HIGH-1：同偏移换名＋搬桶仍可通过。**

位置：[review_overview.py:541](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:541)、同文件 `:550、:605`。

`same_offset` 只证明生成瞬间自洽，不能证明自报时区就是生产者实际使用的时区。

复现：保持 `generated_at=2026-03-08T00:30:00-05:00`、`fsrs_due=2026-03-09T04:30:00Z`，其余计数和明细一致，内存执行完整真实桶位门得到：

| 自报时区 | 桶 | 结果 |
|---|---|---|
| America/New_York | future | 放行 |
| America/New_York | due_today | 拒绝 |
| America/Bogota | due_today | **放行** |
| 缺失/null | 任一上述桶 | 拒绝 |

到期时纽约已是 **03-09 00:30**，波哥大仍是 **03-08 23:30**。这是 **BASE 已有残留，非本轮新增**；缺/null 整改有效，但不能据此宣称错误归桶全部堵死。没有独立来源约束，自洽检查无法辨认这种联合伪造。

**HIGH-2：省略规则分支仍新增接受 C 库拒收的输入，继续错日。**

位置：[local_tz.py:168](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:168)、[display_tz.py:167](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:167)。

秒字段 **61..99 没有被拦**。复现 `AAA0:0:61BBB`，在 `2026-01-20T00:00:30Z`：

- BASE 返回 `None`，本机 C 库退 UTC：**01-20 00:00:30**。
- HEAD 接受：**01-19 23:59:29−00:01:01**。

另有两个同类新增接受面：`\d` 接受 Unicode 数字，`AAA１BBB` 可错日；标准偏移可缺省，`<AAA><BBB>` 在 `2026-07-01T23:30Z` 被算成 **07-02 00:30**，C 库仍为 **07-01 23:30 UTC**。因此 r1 HIGH-2 只修掉了列举的五个输入，没有完成收口。

**MEDIUM-1：两侧偏移分别小于 24h，不保证 `dst()` 返回值可表示。**

位置：[local_tz.py:172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:172)、同文件 `:299`；后端对应 `:171、:298`。

复现：`parse_posix_tz("AAA12BBB-12")` 放行，夏季转换结果可以正常 `.isoformat()`，但调用 `.dst()` 或 `.timetuple()` 会抛 `ValueError`，因为 DST 差值恰为 **24h**。这是省略规则新分支新增可达的异常面。

**MEDIUM-2：两张表未守住 DST 侧约束。**

位置：[test_g6_9c_single_tz_source.py:577](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:577)、同文件 `:587、:610`。

复现：仅在内存删除 `or abs(dst_off) >= 86400`，两副本的 **5 拒绝＋3 正控全部仍绿**，但 `AAA0BBB24` 被接受，夏季 `.isoformat()` 抛偏移 −24h 的异常。当前实现检查了双侧；测试不能防止它退化为单侧检查。正控的“非 None”也没有验证秒 60 的实际换算结果。

**LOW-1：候选窗界仍有错误，四年候选窗结论目前成立。**

位置：[local_tz.py:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py:240)、[display_tz.py:239](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py:239)。

`999:99:99` 实为 **41.6948958333 天**，已经大于 41.69；显式规则路径的隐式 `dst_off=std_off+3600` 还能达到 **41.7365625 天**。

复现：`AAA-999:99:99BBB,0/0,0/0` 的 `_dst_window(2027)` 相对元旦为 **−41.6948958333、−41.7365625 天**，推翻偏移界及端点下界。另“y+2 的差 ≥730 天”不成立，年末探针的差可接近 365 天。

`406.70` 和 `448.39` 两个上界仍成立；修正这些数值后，尚未发现突破 `(y−2,y−1,y,y+1)` 的反例。

**LOW-2：“任何有限带宽都能被更大 Δ 打破”不是实际输入域的性质。**

位置：[review_overview.py:559](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:559)、测试 `:1086`。

复现思路：按正则字段位宽计算最大偏移，取值域有限；省略规则分支更已限制双侧偏移小于 24h。**未知不等于无界**。统一 corrupt 可以保留为明确取舍，但这段“无限量”证明不成立。

**LOW-3：LOW-3 的替代说明仍与实测不符。**

位置：[test_g6_9c_single_tz_source.py:487](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:487)、同文件 `:490`。

复现：既有 NZST 的季度从 **2024-09-28** 延续到 **2025-04-05**；WART 的窗口从 **2024-01-01T04Z** 到 **2025-01-01T04Z**。所以“既有 11 串季度不跨年”和“WART 整个落在同一年内”均不成立。WART 的结束时间及 **366.17 天** 本身已改对。

**LOW-4：固定偏移旧说明没有全部清理。**

位置：[test_g6_9c_single_tz_source.py:1067](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py:1067)、[review_overview.py:470](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py:470)。

复现：测试仍写缺键退固定偏移、Bogota“必须放行”，但紧邻 `:1093` 明确断言拒绝；生产 docstring 仍称按 `generated_at` 自带偏移，实际使用完整 `ref_tz` 规则。

另有既有笔误：`local_tz.py:45`／`display_tz.py:44` 仍写缺省 **02:02:00**，实际常量和 `_parse_rule()` 返回 **02:00:00**。

**LOW-5：验收单尚未登记本轮取舍。**

位置：[UAT-CARD-G6-9c-R2-2026-09-14.md:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/验收单/UAT-CARD-G6-9c-R2-2026-09-14.md:4)、同文件 `:161、:180`。

复现思路：对照当前代码，验收单仍绑定 `130e2dd2`，仍保证远离午夜条目照常显示，并继续解释 ±2h 方案；它没有记录 HEAD 的统一 corrupt 行为。

r1 逐条核对结果：

| r1 条目 | 结论 |
|---|---|
| HIGH-1 | **已解决指定缺/null路径**；另有本轮 HIGH-1 所述既有残留 |
| HIGH-2 | **部分解决**；非法秒数等仍漏收 |
| MEDIUM-1 | 代码已落实取舍；验收单未同步 |
| LOW-1 | 部分修正，界仍有误 |
| LOW-2 | **已解决**：负值条件确为 Δ＜−1h |
| LOW-3 | WART 数值已修正，解释仍错 |
| LOW-4 | 未完全清理 |
| LOW-5 | **已解决**：独立复算 2024—2028 为 604/603/603/603/604 |

对另外两项加固：AST 名称集合实测为 **19 → 23 → 25**，相对 BASE/r1 均无丢名；但同名替换函数体、删除断言或缩减参数表都能绕过，因此它只能证明“名字未丢”。八段负控存档的前后哈希与当前三文件一致，⑥⑦ 的区分性也已独立内存复现；目录未留执行脚本，无法进一步核实 `atexit` 注册和异常退出恢复，“无条件恢复”不能由这些摘要日志证明。

符号、字段长度和秒 60 本身的处理已核对：入口限制一个 ASCII 正负号及字段位宽，缺失尾字段按零，隐式 DST 偏移参与总量检查；秒 60 归一化达到 24h 时会被拒绝。未运行会写盘的 pytest 或负控脚本；全程未修改文件、未连接数据库或网络，未评完整端到端链路。



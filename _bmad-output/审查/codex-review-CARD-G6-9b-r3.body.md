绑定 SHA：`baf8a693e7b781bc64fe72d9e153f37b54e65e8a`，HEAD 一致。完成只读静态复核，未执行测试、启动服务或连接数据库。

**结论：BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2。round-2 的 MEDIUM 已消除；本轮两项均为测试覆盖缺口，当前生产实现没有对应错误。**

1. **LOW — [test_review_overview.py:4796](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/unit/test_review_overview.py:4796)、`:4804`：空值断言无法区分读函数正确降级与 `_collect` 异常兜底。**  
   当非 dict／坏 JSON 的处理回归成抛异常时，`_collect` 仍返回两个 `None`，但会把正常投影误标为 `corrupt` 并清空 projection；现有四门仍可全绿。其余缺失／null／未知值子例也有同一盲点，需要断言原投影及状态保留。

2. **LOW — [test_review_overview.py:4820](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/unit/test_review_overview.py:4820)：徽标门缺少“成功但带陈旧原因”的页面反例。**  
   若徽标条件误改成 `is True or bool(entry.get("last_error"))`，输入 `{"last_result":"pushed","last_error":"陈旧原因"}` 会错误显示降级徽标，而四门仍可全绿：门①对该输入只查 JSON，门④的成功卡只用空原因。

逐点结论：

- **core 点 0：未发现问题。** `review_overview.py:2565–2586` 只认两个枚举；其余一律 `(None, None)`。已知结果配非字符串或不可编码原因时，仅原因归 `None`，成功／失败信号保持。
- **core 点 1：未发现实现问题。** `:1650` 严格使用 `is True`。门④的成功卡、缺失卡反例及整页计数确实能排除无条件渲染；更细的覆盖缺口见 LOW-2。
- **core 点 2：未发现问题。** 三处字典在 `:1077–1078`、`:1182–1183`、`:2085–2086` 均齐带新键，四种投影状态保留初始字段。refresh corrupt 补空容器，对已读页面消费者等价：原有 `get(...) or 空值` 已作同样处理，且 corrupt 无 projection 时不进入板列表分支。读取面外消费者未作保证。
- **core 点 3：未发现本卡引入的问题。** I/O、解析、类型与 UTF-8 过滤符合现成读侧纪律；不调用 state 写入、隔离或重建。坏原因不进入日志，新字段不会带出容器、非有限数字或孤立 surrogate；未发现经这些新字段导致整个 `/overview` 序列化成 500 的输入。
- **core 点 4：未发现问题。** 指定时区函数、board_done／snooze 读写、refresh 去抖与锁、两个既有读取函数均无修改。其余输入相同时，非降级卡片只是把原 span 提取后拼回，HTML 逐字节相同。
- **core 点 5：未发现问题。** 普通 `dict` 返回声明没有因新增内部键改变字段级 schema；base 与 target 的 `backend/openapi.json` blob 均为 `a2d461dc940b5c703ae197f928f5637302ec3bf6`，最终文件完全相同。目标 commit 相对父提交也确实只还原时间戳；本轮未重跑生成器。
- **core 点 6：发现上述两项 LOW。** 门①②③及新增子例均逐值检查；`:4796`、`:4804` 的 `and` 两侧也都是 `is None`。门④使用逐卡正反断言与数量检查，没有退化为字段存在性检查。

`_read_push_status` 的**全部六个显式出口**与对应断言如下；生产行号属于 `review_overview.py`，测试行号属于 `test_review_overview.py`：

| 生产出口 | 输入／返回 | 对应测试断言 |
|---|---|---|
| `:2546` | 无文件／坏 JSON → `(None, None)` | 门③ `:4745–4746`、`:4804` |
| `:2550` | 缺结果键／非 dict → `(None, None)` | 门③ `:4754–4755`、`:4796` |
| `:2575` | null／未知字符串／null 配噪声 → `(None, None)` | 门③ `:4766–4767`、`:4772–4773`、`:4786–4787` |
| `:2577` | 失败＋原因 `123` → `(True, None)` | 门② `:4727–4728` |
| `:2585` | 失败＋孤立 surrogate → `(True, None)` | 门② `:4716–4717`，另有 JSON／页面 200 |
| `:2586` | 成功空原因／成功陈旧原因／正常失败 | 门① `:4666–4667`、`:4677–4678`；门② `:4699–4700` |

**没有完全缺少输出断言的显式 return，但不能据此称所有路径都被守住。** 前三个出口存在 LOW-1 的兜底掩盖；`:2577`、`:2585` 尚未覆盖成功态组合。门③两个噪声例的 `last_result` 实际都为 `null`，没有“未知字符串＋噪声”组合。另有非法原始 UTF-8、权限错误及 `_push_status:2598/:2603` 的不可用出口未被这四门直接覆盖；当前代码的静态处理正确。

**撤回余量未引入当前 runner 已记录失败的漏报。** `daily_review_run.py:745–746` 写出的失败仍映为 `True`；`:739` 的成功映为 `False`。`:743–744` 的 `skip-nokey` 不更新 `last_result`，可能保留历史状态，这是既有状态记录边界，不是本轮撤回分支新增的漏报。

负控的静态判断：

| 变异 | 预期首次失败位置 |
|---|---|
| degraded 恒 False | 门② `:4699`；全跑四门时，门④ `:4829` **也会失败**，不能宣称只红一门 |
| 徽标条件恒真 | 门④ `:4830`，成功卡出现徽标 |
| 缺失态返回 `(False, "")` | 门③ `:4745` |
| 负控⑤：保留前置出口及 null 的完整 `(None, None)`，仅让非 null 未知值冒充成功 | 门③ `:4772`，即 `e4["push_degraded"] is None` |

负控⑤的**精确变异源码与运行记录不在指定读取面内**，因此最后一项是条件性推导。若只保住 null 的 `push_degraded=None`，却让 `last_error=""`，会先红在 `:4767`，仍不能声称隔离到了 e4。



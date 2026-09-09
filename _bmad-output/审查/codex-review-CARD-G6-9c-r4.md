> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u6-reviewtime · 卡 CARD-G6-9c round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（/opt/homebrew/bin/codex）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-r4.md)"`
> 审查绑定: `b1e58489 → 96d3013e`（送审时 HEAD = 96d3013e；本轮之后有整改，末轮绑定见 round-5 存档）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

已核实 `b1e58489 → 96d3013e`。**round-3 两条 HIGH 均未完全关闭；未发现这两条之外的新增 BLOCKER／HIGH。**

**BLOCKER：无。**

**HIGH**

- **HIGH-1 未关闭：墙钟正确，但偏移与 UTC 时刻仍可能错误。** [display_tz.py:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:84)、[local_tz.py:79](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/local_tz.py:79)：`mktime(..., tm_isdst=-1)` 并不保证选择较早时刻，而代码只修正 `fold=1`；错误偏移会进入生产 `generated_at` 并导致合法投影被判 `corrupt`，保持 **HIGH**。

  两份副本均独立复现：

  | TZ | 输入 UTC | 实际本地结果 | 转回 UTC |
  |---|---|---|---|
  | `:America/New_York` | `2026-11-01 05:45Z` | `01:45−05:00`，应为 `−04:00` | **06:45Z** |
  | `:Australia/Lord_Howe` | `1985-03-02 15:00Z` | 次日 `01:30+11:30`，应为 `+10:30` | **14:00Z** |
  | `:Asia/Shanghai` | `1991-09-14 17:30Z` | 次日 `01:30+09:00`，应为 `+08:00` | **16:30Z** |

  历史两例另涉及 [display_tz.py:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:65)：Lord Howe 当前跨度为 **1800 秒**、该历史回拨为 **3600 秒**；上海当前跨度为 **0**、历史为 **3600 秒**。因此漏标 `fold=1`。这些案例**墙钟判据通过，时刻守恒判据失败**。

  `dst()` 也仍忽略 fold、使用当前跨度：Santiago 回拨后的 `2026-04-05T03:30Z` 返回一小时，应为零。生产影响已进一步验证：[daily_review_pick.py:1056](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_pick.py:1056) 写出纽约错误的 `01:45−05:00` 后，原本尚未到期的 `06:00Z` 节点被真实 `_summarize` 拒绝。

- **HIGH-2 未关闭：缺失／null 回退仍会误拒合法桶并放行错误桶。** [review_overview.py:529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:529)：继续使用当前显示时区，不能保证生产时区的桶位语义，保持 **HIGH**。

  真实生产规则为 Bogota、显示区为 New York，使用 `generated_at=2026-03-08T00:30:00−05:00`、`fsrs_due=2026-03-09T04:30:00Z`，正确桶为 `due_today`。真实 `_summarize` 的其他形状、身份和计数门均通过：

  | `display_tz` | 正确 `due_today` | 错误 `future` |
  |---|---|---|
  | `America/Bogota` | 放行 | 拒绝 |
  | 缺失或 `null` | **拒绝** | **放行** |
  | `12`、`{}`、空串 | **拒绝** | **放行** |

  这覆盖旧投影，也覆盖 [daily_review_pick.py:1054](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_pick.py:1054) 当前无名时区正常输出 `null` 的路径。**准确 IANA 名称路径已修复，整个 HIGH 尚不能关闭。**

**MEDIUM**

- **回归门仍漏掉上述存活缺陷。** [test_g6_9c_single_tz_source.py:322](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:322)、同文件 `:649`：原有 80 次换算本次全部通过，却遗漏纽约 `05:45Z` 和历史跨度变化；旧投影正例只验同区，遗漏缺键后切区，仍不足以锁住两条 HIGH，保持 **MEDIUM**。

- **门⑧／⑨的失败身份混入其他检查。** [test_g6_9c_single_tz_source.py:572](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:572)、同文件 `:471`：任意 `_summarize` 的 `ValueError` 都被包装为“参照系取错”。实测错误 schema、错误容器、不可解析时区均得到该身份，因此只匹配外层文案不能证明桶位断言承重，判 **MEDIUM**。**本轮 M16 实际是真杀**；负控的具体拒因匹配没有同样问题。

- **原 `null` 浏览器归日分歧仍在。** [review_app.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:203)：无名服务端时区仍退回浏览器本地，可能不同日，保持 **MEDIUM**；新增投影字段没有改变这条链。

- **原“切区必 stale”问题仍在。** [review_overview.py:1040](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:1040)：只比较日期，上海 `7/31 23:00+08:00` 切 UTC 后仍为 `7/31`，不会因切区自动触发 stale，保持 **MEDIUM**。

- **原跨进程配置差异仍在。** [app/__init__.py:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/__init__.py:16)、[vault_lint.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/scripts/vault_lint.py:95)：后端加载 `.env`，独立 CLI 不加载，同源函数仍可能收到不同配置，保持 **MEDIUM**。

**LOW**

- **门⑦只证明整体有区分力，部分参数格会退化。** [test_g6_9c_single_tz_source.py:401](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:401)：错误实现“返回宿主时区”在 UTC 宿主的 `UTC0` 两格、纽约宿主的两个纽约表示共四格仍全部通过，聚合前提也通过；这是覆盖解释限制，判 **LOW**，不意味着整个门恒真。

- **原门⑥宿主依赖仍在。** [test_g6_9c_single_tz_source.py:685](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:685)：允许的无名固定偏移回退仍会被“必须有 `.key`”拒绝，保持 **LOW**。

按记录描述重建内存变异后，承重结果如下；测试行号均指 `test_g6_9c_single_tz_source.py`，M8 除外：

| 变异 | 独立确认的首个失败点 |
|---|---|
| M1 | `:93` 函数体漂移 |
| M2 | `:279` 求值时机固化 |
| M3 | 未复放子进程变异；仅确认 `:685` 判据 |
| M4／M6 | `:370` 墙钟断言 |
| M5／M7 | 真实桶日期检查，分别两例失败 |
| M8 | `test_vault_lint.py:700`，没有 NameError |
| M9 | `:644`，伪造 Tokyo 实际被放行 |
| M10／M11 | `:116` 类存在性 |
| M12 | `:122` 类体一致性 |
| M13／M14 | `:370` 墙钟断言，各三格失败 |
| M15 | `:375` 时刻守恒，三格失败 |
| M16 | 真实桶日期检查，Bogota→NY、上海→UTC 两例失败 |

**未发现已复放变异的实际假杀，原类体覆盖问题可以关闭。** 但仓内只有汇总，没有确切 harness 和完整 traceback，不能据此认证历史“正文命中”匹配器或每条原始变异的逐字内容。

消费兼容性方面，`daily_review_run` 整体保留并按已知键读取，`send_bark` 只取通知字段，`vault_lint` 忽略陌生键，`review_overview` 没有顶层键白名单；未发现新增键造成解析破坏。JS 读取的是 overview 响应中的**当前服务端时区**，并非投影新增的生产时区。

偏移自洽校验使用**自报名称对应的完整 ZoneInfo 规则**，不能认证真实生产来源。同偏移、相关时段规则相同的替代名称不会改变桶位；2026 年上海／澳门属于这种情况。但两者并非全历史同规则，1991 年存在夏令时差异。协调修改名称与桶位仍可能整体自洽通过，这是单份自报数据的核验边界，不另列重复 HIGH。

本次未修改文件、未连接网络或数据库；动态验证通过真实函数的内存执行完成，未运行需要落盘夹具的完整 pytest。

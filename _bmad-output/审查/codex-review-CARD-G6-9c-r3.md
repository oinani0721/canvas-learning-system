已核实绑定 `d858c357 → b1e58489`。**两条 HIGH 均未真正解决；HIGH-2 还新增了 round-2 原本能拦住的错误投影放行。**

**BLOCKER：无。**

**HIGH**

- **HIGH-1 仍未解决：`_SystemLocalTZ` 在 DST 回拨时仍会错日。** [scripts/local_tz.py:45](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/local_tz.py:45)、[display_tz.py:50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:50)：未实现 `fromutc()`，而 `_isdst()` 用 `tm_isdst=-1` 解析墙钟、忽略 `fold`，足以影响“今天”和桶位，保持 **HIGH**。两份副本均实测：`TZ=:America/Santiago`，`2026-04-05T03:30Z` 应为 **4/4 23:30−04:00**，实际得到 **4/5 00:30−04:00**；转回 UTC 变成 **04:30Z**，连原时刻都未保持。空缺时段的 `mktime()` 归一化也未提供 `fold` 区分。此外，不缓存 `time.timezone/altzone` 仍不等于读取历史偏移：上海 `1991-07-01T15:30Z` 应为次日 `00:30+09:00`，实际为当日 `23:30+08:00`。

- **HIGH-2 仍未解决：单时刻偏移不能证明生成时区，两个分支都存在误拒与误放。** [review_overview.py:506](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:506)、同文件 `:543`：真实 `_gate_buckets` 仍会把合法投影判成整库 `corrupt`，并放行错误桶，保持 **HIGH**。以下均使用 `generated_at=2026-03-08T00:30:00-05:00`、`fsrs_due=2026-03-09T04:30:00Z`，其他计数、身份与板级对账全部通过：

  | 生成区 → 显示区 | 正确桶 | 本轮结果 |
  |---|---|---|
  | Bogota → New York | `due_today` | 正确桶被拒，错误 `future` 通过；**round-2 原会拒绝这个错误桶** |
  | New York → UTC | `future` | 正确桶被拒，错误 `due_today` 通过；**保留 round-2 原缺陷** |

  上海与新加坡在待验时段规则相同时不会产生差异，但不能据此证明这个选择算法成立。

**MEDIUM**

- **新增类未被副本对照门覆盖。** [test_g6_9c_single_tz_source.py:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:91)、同文件 `:315`：门①只比较函数，门⑦只测后端；内存中仅将 scripts 类的偏移改为零，两门仍全部通过，而两侧日期已经不同，因此新增逻辑可静默漂移。

- **门⑦／⑨仍缺少两条 HIGH 的必要反例。** [test_g6_9c_single_tz_source.py:287](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:287)、同文件 `:439`：⑦避开转换当刻且只比较墙钟，⑨缺少“DST 加切区”“同偏移不同规则”和错误桶负例，因而现有全绿不能锁住上述失败路径。

- **`display_tz=null` 的端到端语义仍不自洽，维持已登记的 MEDIUM。** [review_overview.py:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:114)、[review_app.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:203)：POSIX 回退类没有 `.key`，于是已知服务端时区仍无法传给浏览器；实测服务端 `TZ=UTC0`、浏览器上海，对 `2026-07-31T16:30Z` 分别显示 **7/31、8/1**。`null` 本身可以表示“没有 IANA 名”，却不能保证统一归日。

- **切区不保证 stale，原 MEDIUM 仍在。** [review_overview.py:1010](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:1010)：上海 `7/31 23:00+08:00` 转 UTC 仍为 `7/31`，日期比较无法识别切区；`:503–504` 关于切区后变 stale 并触发重建的说明仍不成立。

- **跨进程配置入口差异仍为 MEDIUM。** [app/__init__.py:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/__init__.py:16)、[vault_lint.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/scripts/vault_lint.py:95)：后端加载 `.env`，独立 CLI 不加载，同源解析器仍可能收到不同配置；登记不修没有消除这个边界。

**LOW**

- **门⑥宿主依赖仍在。** [test_g6_9c_single_tz_source.py:554](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:554)：合法固定偏移回退仍被“必须有 `.key`”拒绝，属于测试适用范围限制，保持 **LOW**。

独立承重复核结果：

| 对象 | 结果 |
|---|---|
| 门⑦：M4／M6 | 均在目标 `:319` 断言失败，承重成立 |
| 门⑨：M5／M7 | 生产桶位前提、三个上游门均通过，仅目标桶日期检查失败，承重成立 |
| lint 接线门 | 硬编码上海或东京均只在 `:700` 目标断言失败，原接线覆盖问题可关闭 |
| `host_tz` | teardown 后环境 TZ 与 `time.tzname` 均恢复，原 LOW 可关闭 |

门⑦改比墙钟后，UTC0 与 EST5 已互不相同，正常的固定宿主不可能与全部探针同解；整文件运行 M4 时，新增“前提断言”还会额外失败，不能说整文件只有一个失败身份。

本次未修改文件、未连接网络或数据库。动态验证通过真实函数的内存执行完成，未运行会创建临时夹具的完整 pytest。

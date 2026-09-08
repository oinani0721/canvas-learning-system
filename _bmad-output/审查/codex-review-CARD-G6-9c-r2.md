绑定已核实为 `0e8dc06e → d858c357`。**两条 HIGH 仍不能关闭，其中桶校验整改引入了新的 DST 回归。**

**BLOCKER：无。**

**HIGH**

- **HIGH-1 未真正解决：进程本地回退丢失 DST 规则。** [scripts/local_tz.py:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/local_tz.py:48)、[display_tz.py:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:53)：返回的是当前固定偏移，仍会造成错日、错桶。实测 `TZ=EST5EDT,M3.2.0,M11.1.0`，冻结现在为 `2026-11-01T04:00Z`，解析器取得 `-04:00`；到期时间 `11-02T04:30Z` 实际为纽约 **11/1 23:30**，解析结果却是 **11/2 00:30**，把当天节点推入未来。

- **HIGH-2 发生缺陷位移：合法 DST 投影被拒，错误投影反而通过。** [review_overview.py:500](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:500)、同文件 `:537`：`generated_at` 的固定偏移不能代表生产器完整时区规则，因此仍可令整库变成 `corrupt`。纽约在 `2026-03-08T00:30-05:00` 生成，节点于 `03-09T04:30Z` 到期，生产器正确归入 `future`；旧门通过，新门却要求 `due_today`。反过来，把该节点错误归入 `due_today`，旧门拒绝、新门通过。秋季回拨的反方向误拒也已复现。

**MEDIUM**

- **切换时区并不保证缓存失效。** [review_overview.py:498](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:498)、同文件 `:1004`：上海 `7/31 23:00+08:00` 生成后切 UTC，仍得到 `stale=False`，runner 同日也可返回 `cached`，使旧 `future` 桶和“明天”说明继续与当前显示日并列，造成业务展示不一致；页面轮询 GET 也不会自动调用刷新。

- **门⑦复制了被测错误，并依赖宿主才能杀 M4。** [test_g6_9c_single_tz_source.py:298](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:298)：oracle 同样取得当前固定偏移，测不出上述 DST 错日；将 `/etc/localtime` 解析结果设为 UTC 后，M4 三个参数全部通过，因此不能作为跨宿主稳定的 HIGH-1 回归门。

- **round-1 的 lint 接线覆盖问题仍在。** [test_vault_lint.py:642](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_vault_lint.py:642)：判别门直接替换 `_display_tz`，其余用例固定上海，实际 `_display_tz()` 硬编码回上海仍能逃过检查，尚不能证明 lint 接到了统一来源。

- **已登记的 JS 回退问题仍为 MEDIUM。** [review_app.py:202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:202)：服务端没有时区名时使用浏览器本地，仍不能保证两端同日。

- **已登记的跨进程配置问题仍为 MEDIUM。** [app/__init__.py:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/__init__.py:16)、[vault_lint.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/scripts/vault_lint.py:95)：后端加载 `.env`，独立 CLI 路径不加载，相同解析器仍可能收到不同配置。

**LOW**

- **新增测试没有完整恢复时区状态。** [test_vault_lint.py:640](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_vault_lint.py:640)：`monkeypatch` 还原环境变量后没有对应 `tzset()`；实测环境恢复 LA 后 `time.tzname` 仍为上海，留下测试间状态污染。未将此扩大为所有日期换算持续错误。

- **门⑥的宿主依赖仍为 LOW。** [test_g6_9c_single_tz_source.py:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:415)：合法固定偏移回退仍会被“必须有名”拒绝，不能作为通用环境判据。

其余问题的独立核验结果：

- **问题 2／4：** `_display_day` 的生产调用点没有站错参照系：`_display_today` 使用默认分支，桶门显式传入时区。错误在于把偏移当成完整时区。门只能发现会导致节点日界矛盾的 `generated_at` 错配，不能独立证明它与实际分桶时区一致。
- **问题 3：** 当前上海宿主的内存复现中，M4 在门⑦唯一日期断言失败；M5 在上海通过，切 UTC 后前三个上游门通过，仅桶门触发目标异常。没有导入失败或前置断言抢先失败。归档仅保存摘要，不能单凭它证明历史执行的归因。
- **问题 5：** `dedent` 已挡住原缩进变异；仍不比较模块导入、全局绑定，`rstrip` 还会忽略多行字符串的尾随空白。当前未发现因此产生的业务漂移。
- **问题 6：** `_real_runner_today` 实际同进程调用 runner 和 picker，没有 runner 子进程，也未发现清理后重新加载 `CANVAS_TZ` 的路径；但已在 collection 时初始化的 `picker._DISPLAY_TZ` 会保留旧覆盖，矩阵没有核验其 payload 日期和桶位。
- **问题 7：** 本次运行日三条变异均可杀；“与当前日期无关”仍不成立，真实系统日若为 `2026-08-31`，`date.today()` 变异会通过。
- **问题 8：** 全部 47 个合法整小时偏移逐字节一致；半小时、三刻钟输出正确，未发现依赖旧取整结果的既有断言。
- **问题 9：** 转换仅包住时区解析器，未吞掉 vault 检查的其他 `ValueError`；实际入口的无效时区已验证返回 **3**。

未修改文件、未连接网络或数据库。动态验证使用内存执行，未运行会创建临时夹具的完整 pytest；三个变异目标文件均与提交及归档 SHA-256 一致。



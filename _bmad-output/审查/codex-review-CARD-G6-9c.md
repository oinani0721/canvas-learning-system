> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u6-reviewtime · 卡 CARD-G6-9c round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（/opt/homebrew/bin/codex）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-G6-9c.md)"`
> 审查绑定: `0e8dc06e`（本轮送审时的 HEAD；本轮之后有整改，末轮绑定见 round-2 存档）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

审查基线已核实为 `da690bf8 → 0e8dc06e`。发现以下问题。

**BLOCKER：无。**

**HIGH**

- **默认时区可能静默算错日期。** [scripts/local_tz.py:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/local_tz.py:43)、[display_tz.py:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/core/display_tz.py:48)：合法的 `TZ=UTC0`、`EST5`、`:America/New_York` 被 `ZoneInfo` 拒绝后，解析器改读 `/etc/localtime`；实测上海宿主上 `TZ=UTC0`、`2026-07-31T16:30Z` 被算成 **8 月 1 日**，违背机器本地日期，影响归日和完成账。

- **切换时区后，合法缓存会被判成 corrupt。** [review_overview.py:483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:483)、[daily_review_run.py:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:211)：上海时区在 `7/31 15:00Z` 将 `17:00Z` 到期节点归入 `future`，切换 UTC 后日期仍为 7/31，runner 实际返回 `cached`，但后端按新时区校验时抛出“应属 due_today”，导致有效投影不可用。

**MEDIUM**

- **JS 仍保留独立时钟。** [review_app.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_app.py:203)：服务端下发 `null` 后改用浏览器本地，UTC 服务端与纽约浏览器在 `03:30Z` 会显示不同日期；已有测试覆盖了“回退”，没有证明服务端同日，而且固定偏移回退还会让同地浏览器在跨 DST 日期上分叉。

- **源码对照门能漏掉改变语义的缩进漂移。** [test_g6_9c_single_tz_source.py:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:82)：`strip()` 删除了 Python 控制流缩进；内存变异仅把 `env_tz` 赋值缩进进 `if name`，比较仍通过，正常调用却抛 `UnboundLocalError`；此外实际比较包含函数签名、函数 docstring 和装饰器，普通语义等价改写会被拒绝，并非只比函数体。

- **外部覆盖会削弱边界矩阵。** [test_g6_9_boundary_matrix.py:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9_boundary_matrix.py:150)：矩阵只改 `TZ`，未清除 `CANVAS_TZ`；内存执行确认，外部设置 `CANVAS_TZ=Asia/Shanghai` 后，16 格退化为同一区比较，runner 硬编码上海的变异仍通过。

- **lint 判别门杀不掉所宣称的变异。** [test_vault_lint.py:628](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_vault_lint.py:628)：所选 UTC 23:00 与纽约恰好同日，直接取 UTC 日的变异在上海、洛杉矶、UTC 三态均通过，无参换算在后两态也通过；同时，固定上海的 autouse 与直接替换 `_display_tz`，使 lint 硬编码回上海的接线错误仍能逃过相关断言。

- **配置入口没有跨进程统一。** [app/__init__.py:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/__init__.py:16)、[vault_lint.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/scripts/vault_lint.py:95)：覆盖仅写在 `backend/.env` 时，后端及 refresh 会读取并继承，独立启动的 picker／runner／lint 不会自动读取，因此相同函数源码仍可能收到不同配置。

**LOW**

- [test_g6_9c_single_tz_source.py:300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/regression/test_g6_9c_single_tz_source.py:300)：无条件“必须有名”依赖宿主能力；`/etc/localtime` 为普通复制或文件 bind mount、最终路径没有 `zoneinfo`、文件或对应 tzdata 缺席时，合法固定偏移回退也会报红，不能作为跨环境通用回归判据。

- [review_overview.py:652](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:652)：偏移仍按整小时取整，实测 Kolkata 的 `+05:30` 显示成 `UTC+5`、St. John’s 的 `-02:30` 显示成 `UTC-3`，属于显示错误。

- [vault_lint.py:939](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/scripts/vault_lint.py:939)：无效 `CANVAS_TZ` 的 `ValueError` 逃过 `main()` 的 `LintConfigError` 捕获，配置错误以退出码 **1** 而非约定的 **3** 结束；没有静默退化，但错误分类不正确。

- [daily_review_pick.py:375](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_pick.py:375)：`_sh_local` 仍保留旧名，实际已经使用任意显示时区；调用点有效，属于改名遗漏，未发现失效旧调用，搜索包含测试目录。

另已独立确认：

- **问题 1／2：** 同一容器内，父子均未设置 `TZ` 时会读取同一 `/etc/localtime`，透传本身没有制造分叉；这不保证容器与宿主 runner 同区。正常业务归日已使用解析器，剩余无参 `astimezone()` 用于输入解释、日志或极值校验。
- **问题 4／7：** 空登记表没有变成恒真，仍比较实测的 16 格；将 `display` 放在改时区之后求值是正确修复。显示侧确实逐次求值，门⑤能杀掉模块级常量 M2。
- **问题 8／11：** freshness 的期望仍是独立字面量，没有与被测计算一起退化；三处常量 patch 适合对应的非时区场景，但不覆盖生产器初始化接线，矩阵也没有核验其 payload 日期与桶位。
- **问题 10：** 新 import 位于禁止字节码写入之后，未发现新增零写违规；隔离副本已携带依赖，模块缺席直接报错，无硬编码兜底。库 import 自身 `.pyc` 的既有例外仍存在。

未修改文件、未连接网络或数据库。动态证据来自内存复现；未执行会创建临时夹具的完整 pytest，因此未独立确认两态各 415 passed。

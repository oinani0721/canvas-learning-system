结论：发现 4 个 HIGH，当前应判 FAIL。

## HIGH

1. [review_app.py:304-383](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:304) — 刷新结果会被重绘抹掉，且反馈字段不完整。

   - `:381` 写入按钮旁提示后，成功分支 `:382` 立即 `poll()`；GET 成功后 `:349` 整体替换 `#cards`，提示随即消失。
   - 若 POST 尚未完成时自动 GET 先重绘，回调只会更新已脱离 DOM 的旧节点，用户完全看不到结果。
   - `debounced`/`in_progress` 未显示 API 已返回的 `rebuild_count`。

   建议：将每库 `inFlight/result` 放入持久状态，重绘后恢复提示；协调刷新期间的轮询，并在所有响应分支显示 `rebuilt/reason/rebuild_count`。

2. [test_review_app.py:220-255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:220) — Node 缺失时 10 个核心 JS 门全部假绿跳过。

   实证：移除 Node 后测试返回 `12 passed, 10 skipped`、退出码 0；四态、unavailable、W6、轮询、refresh、due 权威口径等均未执行。卡文要求 Node 不可用时采用 Python fallback，并未允许跳过。

   建议：Node 缺失或无法启动时 fail closed，或实现规定的 Python fallback；裁判锁定 `skipped == 0`。

3. [test_review_app.py:223-230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:223) — Node marker 可被注释中的测试专用副本欺骗。

   在真实响应的实际代码前放置一个块注释，注释内包含第一组 markers 和“好函数”；浏览器忽略它并执行后面的坏代码，但正则会提取注释内死代码给 Node 测试。未检查 marker 唯一性或活动代码归属。

   建议：执行完整实际 `<script>`；或至少用 JS AST 验证 marker 唯一、位于活动语句区，且区段外不能重定义导出函数。

4. [g62_mutation_negative_controls.py:264-323](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/_bmad-output/审查/evidence-g62/g62_mutation_negative_controls.py:264)、[test_review_app.py:209-213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:209) — “30/30 指定门变红”的判据不真实。

   - 脚本只判断 `returncode != 0`。不存在的 nodeid 实测为 `exit 4 / collected 0`，仍会被算作“变红”；collection error、fixture error、Node 崩溃同样会误认证。
   - M30 使用 `if False`，根本不读盘；真正触发测试的只是注释里的 `subprocess` 字样。`json.load(open(...))` 或 `Path.open()` 可实现第二管道却绕过四个字符串。
   - 因此本次 30/30 只能证明目标 pytest 命令非零，不能证明指定断言因预期行为失败。

   建议：要求精确收集一个节点、pytest 退出码 1，并用结构化报告验证 call phase 的目标断言失败；M30 改成真正执行第二读取/汇总管道的变异。

## MEDIUM

1. [review_app.py:295-302,342-354](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:295) — HTTP 200 的语义坏 JSON 被冒充成功。`{}` 或 `{"vaults":"bad"}` 会清除旧数据、隐藏 unavailable 横幅并显示“已连接/未发现 vault”。

   建议：修改 DOM 前强校验顶层对象及 `vaults` 数组；契约错误进入 unavailable 分支并保留旧数据。

2. [test_review_app.py:375-565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:375) — 隐藏恢复、到点 GET、unavailable 保留数据只测纯 helper，未测实际副作用链。改坏 `setTimeout(poll, ms)`、前台 `poll()` 调用或 catch 中 DOM 操作，测试仍绿。

   建议：用实际内联脚本配 fake DOM/fetch/fake timers，覆盖 `visibilitychange → poll`、`timer → GET → render` 和失败保留链。

3. [review_app.py:258-260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:258) — 休息日“最近到期”直接截 UTC 日期。`2026-09-02T16:30:00Z` 显示 9 月 2 日，上海本地应为 9 月 3 日。

   建议：复用 `parseDueMs`、`shDay` 或 `humanizeDue`，补 16:00Z 跨日边界测试。

4. [test_review_app.py:82-105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:82) — 外链门覆盖不完整，会漏掉 CSS `url(//evil)`、`@import`、`<a href="//evil">`、`data:` 和 `javascript:`。

   建议：解析 HTML/CSS 中所有 URL-bearing 属性和规则，统一按解析后的 scheme/origin 白名单裁决。

## LOW

- [review_app.py:338-361,389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:338) — 初次加载和已入队 timer 会在页面已隐藏时仍发一轮 GET；只会停止后续排程。若“隐藏暂停”要求后台零请求，应在 `poll()` 入口直接检查 `document.hidden`。

## 未发现

- 当前响应体零 HTTP(S) 外链；只 fetch 两个注入 URL。
- 换前缀挂载门有效，M27 能区分 `request.url_for` 注入与硬编码当前 `/api/v1/...`。
- clamp 5–60 秒、自动轮询不 POST、状态文案从 `_STATUS_META` 注入、stale + `due_count=0` 不显示休息日：当前实现未发现问题。
- 未发现 JS 重算到期成员、计数、过滤或排序；`humanizeDue` 只影响显示。
- W6 三字段的条件渲染本身正确，但当前分支尚未合入 W6 透传，真实 GET 集成仍需合并后复核。
- `review_overview.py` 与基线 blob 相同；router 仅新增 import/include。
- 可用的 NVM Node 24 下定向测试为 `78 passed`。负变异后 `review_app.py` SHA-256 恢复为 `b65d866d…`，Git blob 与 HEAD 均为 `427e1987…`，目标文件 diff/status 为空。

总结论：FAIL（存在 4 个未清零 HIGH，当前不应验收或合并）。



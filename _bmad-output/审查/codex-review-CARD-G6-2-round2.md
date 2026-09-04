结论：**FAIL**。HEAD `a9410c9f…`；确认 4 个 HIGH，其中 HIGH-1、HIGH-3、HIGH-4 未完成整改。

## BLOCKER

未发现。

## HIGH

1. [review_app.py:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:310)（`:310-317,377-397,419-423`）— 刷新反馈与数据提交不一致，可能持续显示“数字已更新”但仍是旧数字。

   - POST 返回 `rebuilt` 后先写“✅ 已重建 · 数字已更新”，忽略响应自带的 fresh `entry`，再异步启动 GET。
   - 实际整段脚本复现：新 GET 已显示 fresh 数据后，较早发出的旧 GET 后返回并覆盖为旧投影，反馈仍显示“已重建”。
   - 更直接的失败场景：POST 成功、跟进 GET 503 时，旧卡保留、unavailable 横幅出现，但提示仍声称数字已更新；若 GET 持续失败，该矛盾可长期存在。
   - 建议：使用 generation/`AbortController`，仅最新 GET 可提交状态与排程；优先原子应用 `payload.entry`，或只显示“正在同步”，待受保护的 GET 成功后再声称数字已更新。

2. [test_review_app.py:324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:324)（`:324-355`）— HIGH-3 的“浏览器与 Node 执行同一段字节”仍可被 HTML tokenizer 差异欺骗。

   - `_extract_script()` 用大小写敏感正则寻找 `</script>`；浏览器对 `</SCRIPT>` 大小写不敏感，并会在 JS 注释中结束脚本。
   - 独立复现：在 `// </SCRIPT>` 后放“好函数”，结果为 `regex_has_good=True`、`browser_has_good=False`。Node 执行后置好代码，浏览器只执行前置坏代码。
   - 建议：用 HTML5 tokenizer或真实浏览器提取脚本节点，大小写不敏感地强制响应中恰有一个脚本，并拒绝脚本正文中的任何 HTML script 终止序列。

3. [g62_mutation_negative_controls.py:352](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/_bmad-output/审查/evidence-g62/g62_mutation_negative_controls.py:352)（`:352-358`）— HIGH-4 的三重字符串判据仍可把 collection error 误认证为指定门变红。

   - 临时副本让模块打印 `1 failed` 和精确 `FAILED ...::nodeid` 后抛 `ImportError`。
   - pytest 实际 `exit 4`、测试未收集，但当前 `red` 表达式得到 `True`。
   - 建议：至少要求 `returncode == 1`；使用结构化报告或 pytest hook，验证精确收集一个节点、目标测试 call phase 失败、且 collection/setup/teardown error 和 skip 均为 0。stdout 只能用于诊断。

4. [test_review_app.py:248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:248)（`:248-263`）— AST 门仍可换形绕过，第二读盘管道可保持全绿。

   - 注入 `__builtins__["open"]("今日复习.json").read()` 无需新增 import，也不命中直接 `open()` 或 `.open/read_text/read_bytes` 检查。
   - 指定 AST 测试实跑 `1 passed`；模块中的 `__builtins__` 确为含 `open` 的字典。
   - 建议：改为 endpoint Python 代码的正向 AST 合约；至少禁止危险 builtin 的引用、别名、下标及 `getattr` 数据流，并新增对应负变异。

## MEDIUM

1. [review_app.py:300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:300)（`:300-304,334,351-365,405-410`）— `notes/inflight` 使用普通对象，合法 vault 名可碰撞原型键。`vault_id="__proto__"` 实测按钮初始禁用、提示出现 `[object Object]`，点击永远 0 POST。建议使用 `Map` 或 `Object.create(null)` 加 own-key 检查。

2. [review_app.py:377](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:377)（`:377-396`）— round-1 的语义坏 JSON 问题仍在。HTTP 200 的 `{}` 或 `{"vaults":"bad"}` 会清除旧数据并标成“已连接”。建议提交状态前强校验根对象及 `vaults` 数组。

3. [test_review_app.py:298](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:298)（`:298-312,773-874`）— HIGH-1 的六场景门未锁住全部声明。删除 inflight 重绘态的 `disabled`、或绕过 `freshNotes()`，六个 Node 子场景仍全部通过；DOM stub 还会自动制造真实页面不存在的节点。建议从实际渲染 HTML 构建 DOM，并断言 deferred POST 期间重绘后的按钮状态及 TTL 后真实 DOM 退场。

4. [review_app.py:257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:257)（`:257-263`）— 最近到期日期仍截取 UTC 字面值；`2026-09-02T16:30:00Z` 显示 9 月 2 日，上海应为 9 月 3 日。建议复用 `parseDueMs()` 和 `shDay()`。

5. [test_review_app.py:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:93)（`:93-116`）— 外链门仍漏 CSS `url()`/`@import`、普通 `<a href="//…">`、`data:` 和 `javascript:`。当前响应确实无外链，但这些回归可假绿。建议统一解析所有 URL-bearing 属性和 CSS URL。

## LOW

- [test_review_app.py:56](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/tests/unit/test_review_app.py:56)、`:361-366`：`which(...) or ""` 后却判断 `is None`，因此 Node 缺失不会走承诺的 `pytest.fail`，而是 `PermissionError("")`。仍属 fail-closed；建议改成 `if not _NODE` 并先探测 `node --version`。

- [review_app.py:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:161)、`:360-375`：15 秒 TTL 只是下次成功重绘时惰性过滤；DOM 提示可留到 60 秒，GET 持续失败时可无限残留。

- [review_app.py:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w5-reviewapp/backend/app/api/v1/endpoints/review_app.py:370)、`:399-404,433`：隐藏态首次加载或已开始的 GET 仍执行一轮，只暂停后续排程。

## 四项整改裁决

- **HIGH-1：NOT VERIFIED。** 正常 vault 名下，持久 note、detached DOM 恢复、inflight guard 和三分支 `rebuild_count` 均已实现；但反馈可与旧数据长期矛盾，且六场景门不承重。
- **HIGH-2：VERIFIED。** 已无 skip 路径；隐藏 Node 后测试非零失败、0 skip。仅错误诊断分支存在上述 LOW。
- **HIGH-3：NOT VERIFIED。** 旧 marker 割取已删除，但大小写 script 终止符仍可让浏览器与 Node 执行不同字节。
- **HIGH-4：NOT VERIFIED。** M01–M35 的固定变异确实全部由指定节点变红，M30/M35 也是真变异；但认证判据与 AST 门均有实际反例。

## 未发现问题的维度与实测

- 当前生产响应：HTTP 200、`external []`、单一内联脚本；换前缀 `url_for` 行为门通过。
- clamp 5–60 秒、后续隐藏暂停、自动轮询不 POST：通过。
- `_STATUS_META`/桶位从对照模块注入；stale + `due_count=0` 不伪装休息日：通过。
- due 权威计数不在 JS 重算；W6 三字段有/无条件渲染：通过。
- NVM Node 24：`test_review_app.py` 为 `24 passed`；与 overview 联跑为 `80 passed`。
- 隔离 HEAD 快照：35/35 变异通过，结束后 SHA-256 恢复为 `3d31b047…a355b`。
- `review_overview.py` 基线与 HEAD blob 均为 `91c7e5c8…`；router 仅新增 import/include 两行。
- 以上是定向套件与临时对抗 harness，不代表全量 CI 或部署走查。

**总结论：FAIL（HIGH-1、HIGH-3、HIGH-4 未清零，并发现刷新因果一致性的新 HIGH）。**



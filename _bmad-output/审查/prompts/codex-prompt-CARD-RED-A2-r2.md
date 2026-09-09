# CARD-RED-A2 独立复核请求 round-2（第十三批 / 车道 U10 末卡）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
审查绑定：`052a9289..0b9be419`（本卡两个代码 commit：`fe3787ce` 初版 + `0b9be419` r1 整改）

## 一 背景（含 round-1 对我方论证的更正）

`backend/tests/unit/` 下 3 条测试长期红着，失败身份 `assert 500 == 503`：

- `test_sync_batch_auth.py::TestProductionFailClosed::test_no_key_configured_fails_closed_503`
- `test_system_endpoint_auth.py::TestSystemConfigAuth::test_prod_no_key_configured_503`
- `test_system_endpoint_auth.py::TestSystemTestLLMAuth::test_prod_no_key_configured_503`

它们是**真负控**（验「生产配置下空 key 必须被拒」），不允许配 key 变绿、不允许放宽生产校验。

红因在配置层：`_settings_factory(debug=False, key="")` 在 `get_settings` override 闭包里
实例化 `Settings(...)` 时被 `app/config.py::validate_security_defaults` 抛 `ValueError`，
该异常在请求处理期被 `app/main.py::CORSExceptionMiddleware` 兜成 500，请求没走到
`app/security.py`。存档里 bug_tracker 记的 `error_type` 为 `ValidationError`。

**⚠️ round-1 更正（我方原论证有误，已采纳你的反证）**：我方 round-1 曾断言「Branch 1 在
任何经 pydantic 校验的 Settings 上都不可达」。这是错的。本方已独立复现你的反例：
`INTERNAL_API_KEY="   "`（空白字符）能通过 `config.py:295` 的真假值检查，而
`security.py:91` 先做 `.strip()`，于是命中 Branch 1 并返回 503 + 精确 detail +
该日志事件。正确表述应为：**对精确空串 `""` 不可达**（校验先拒，且 `config.py:966`
在模块导入期就 `settings = get_settings()`），**对空白字符 key 可达**。本卡三条测的是
「非法配置一旦抵达鉴权依赖，最后一道防线仍拒绝请求」，不是「漏配 key 的部署能起来并返回 503」。

## 二 round-1 各条的处置（请核对处置是否到位、有无引入新问题）

- **MEDIUM-1（Branch 1 可达性）**：接受。已在上文更正论证；结论写入验收单与台账移交条目。
  未改代码——你也判定「两层防御各有价值，没有依据删除 Branch 1 或放宽校验」。
- **LOW-3（裸子串不唯一绑定）**：接受并**改代码**（commit `0b9be419`）。已独立复现你指出的碰撞：
  `security.py:220` 的标记以 `ws_` 打头因而包含裸 token（实测裸子串在其中为 True，
  带括号的完整标记为 False），且该处与 Branch 1 同 logger、同 ERROR 级别。三处断言改为遍历
  `caplog.records` 并同时限定 `name == "app.security"`、`levelno == ERROR`、
  `funcName == "require_internal_api_key"`、`"(auth_fail_closed)" in r.getMessage()`；
  请求前加 `caplog.clear()`。
- **LOW-2（model_construct 的其他偏差）**：接受为已知限制，登记不改。你已独立遍历 77 字段确认
  仅 `DEBUG` 不同；我方在验收单「本卡未证明什么」里如实登记「该对象同时带
  `NEO4J_ENABLED=True` + 空 `NEO4J_PASSWORD`，违反另一条生产不变量，不等同真实生产配置」。
  未采用你建议的 `model_copy(update=...)` —— 理由：它同样不是正常启动路径，且会把「该档不读
  `.env`」这一确定性丢掉（合法基底仍会合并 `.env`）。请判断这个取舍是否成立。
- **LOW-4（detail 文案耦合）**：接受为已知限制，登记不改（文案漂移会显式打红，不静默通过）。
- **LOW-5（两处自述超出证据粒度）**：接受。①test-llm 那条基线本就只有状态码断言、没有模糊
  detail，我方「三条原有两项断言均保留」的说法过宽，正确表述是「全部既有断言均保留，三条断言
  数分别 2→4 / 2→4 / 1→3」；②本轮五段负控每段都完整记录了变异前 sha、还原后 sha 与
  `git diff --quiet` rc。

## 三 本轮五段负控（存档 `evidence-red-a2/negctl-suite-*.txt` 及各 `negctl-L*-red-*.txt`）

全部在 commit `0b9be419` 上重跑（判据已变，round-1 的负控证据不再覆盖新判据）：

1. `L1-layer`：override 换 Branch 2 档 ⇒ 3 条红在 detail 精确等值上；
2. `L2-funcname`：`funcName` 绑定换成 WebSocket 侧函数名 ⇒ 3 条红在日志判据上（证明该条件承重）；
3. `L3-token`：完整标记换成不存在的 token ⇒ 3 条红在日志判据上（证明不恒真）；
4. `L4-caplog-solo`：移除 detail 等值断言 + 换 Branch 2 档 ⇒ 3 条红在日志判据上
   （证明日志判据可独立分层，不依赖 detail 断言）；
5. `L5-revert`：实例化改法退回原样 ⇒ 3 条回到 `assert 500 == 503`。

每段均以 `git show HEAD:<path> > <path>` 还原，并记录变异前 sha / 还原后 sha /
`git diff --quiet` rc=0。

## 四 其余自述（请独立核对）

1. 生产代码零改动：`git diff --stat 052a9289 HEAD -- backend/app` 为空；
   `config.py` / `security.py` / `main.py` 逐一为空。
2. 改动面只有那两个测试文件（`git diff --name-only 052a9289 HEAD -- . ':(exclude)_bmad-output'`）。
3. 只改 `debug=False and key==""` 这一档的实例化方式，其余档位仍走 `Settings(**fields)`。
4. 两文件 17 条全 PASSED；`tests/unit` 目录级 120 failed → 117 failed，
   相对本卡开工快照的 nodeid diff 只有 3 条 `<`（恰为上述三条）、无 `>` 行；29 errors 不变。
5. 判据计数：`auth_fail_closed` 逐文件 sync=1 / system=2 / 合计 3；裸 `in caplog.text` 判据残留 0。

## 五 请按重要性排序回答

1. 新的日志判据是否仍有可被无关事件满足的路径？`funcName` 绑定是否会因装饰器、
   包装函数或 `functools.wraps` 而失真？
2. `caplog.clear()` 放在 `at_level` 上下文内、请求之前，是否足以排除同一测试早前阶段的记录？
   有没有更可靠的位置？
3. LOW-2 的取舍（不采用 `model_copy`、保留 `model_construct` 以维持「不读 `.env`」的确定性）
   是否成立？如果不成立，请给出反证。
4. 本轮五段负控是否仍有未覆盖的假绿面？特别是：有没有一种改动能让三条同时变绿、
   但请求其实没到 Branch 1？
5. 验收单/台账里对「Branch 1 可达性」的更正表述是否准确？还有没有别的把推断当事实的地方？

## 六 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与判断依据。
若某条自述经核对不成立，请直接指出并给出反证。

## 七 边界

不评 U10-A~D 的改动（`.claude/agents/**`、`backend/app/api/v1/system.py`、
`backend/app/services/agent_service.py`、`backend/tests/unit/conftest.py`、
`backend/tests/support/authed_client.py`）；不评 W4 真连门；不评 pyright 存量；
不评 `_archive/`；不评 `_bmad-output/` 下的文档措辞。

## 最小读取面

- `git diff 052a9289 0b9be419 -- backend/tests/` 全文
- `backend/tests/unit/test_sync_batch_auth.py` 全文
- `backend/tests/unit/test_system_endpoint_auth.py` 全文
- `backend/app/config.py` 第 270-300 行、第 960-970 行
- `backend/app/security.py` 第 60-230 行
- `_bmad-output/审查/evidence-red-a2/*.txt`

# CARD-RED-A2 独立复核请求（第十三批 / 车道 U10 末卡）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
审查绑定：`052a9289..fe3787ce`（本卡唯一代码 commit = `fe3787ce`）

## 一 背景

`backend/tests/unit/` 下有 3 条测试长期红着，失败身份是 `assert 500 == 503`：

- `test_sync_batch_auth.py::TestProductionFailClosed::test_no_key_configured_fails_closed_503`
- `test_system_endpoint_auth.py::TestSystemConfigAuth::test_prod_no_key_configured_503`
- `test_system_endpoint_auth.py::TestSystemTestLLMAuth::test_prod_no_key_configured_503`

这三条是**真负控**：它们要验的正是「生产配置（DEBUG=False）下空 `INTERNAL_API_KEY`
必须被拒（503）」。因此**不允许**通过给它们配一个 key 来变绿，也**不允许**放宽
生产侧的配置校验 —— 那样等于删掉它们要守的那条规则。

红的真实原因不在鉴权层，而在配置层：两个测试文件里的 `_settings_factory(debug=False,
key="")` 会在 FastAPI 的 `get_settings` override 闭包里实例化 `Settings(...)`，而
`backend/app/config.py::validate_security_defaults`（一个 `@model_validator(mode="after")`）
在 `DEBUG=False` + 空 key 时抛 `ValueError("INTERNAL_API_KEY required outside local dev...")`。
该异常发生在**请求处理期**，被 `backend/app/main.py::CORSExceptionMiddleware` 兜成
**500**，请求根本没走到 `backend/app/security.py`。开工存档里 bug_tracker 记录的
`error_type` 是 `ValidationError`（不是 HTTPException），可佐证这条归因。

推论：`security.py` 里那个「生产 + 未配置 key ⇒ 503 fail-closed」的分支（下称
Branch 1）在**任何经 pydantic 校验的 Settings** 上都到达不了 —— 校验先一步拒掉了。

本卡的改法只在测试侧：让 `debug=False and key==""` 这一档能造出该非法配置对象，
使请求真正到达 Branch 1；并把判据从「状态码 + 模糊文案」升级为「层身份」。

## 二 作者自述，请独立核对（不要默认它们成立）

1. 生产代码零改动：`app/config.py::validate_security_defaults`、`app/security.py`、
   `app/main.py` 一字未动（`git diff --stat 052a9289 HEAD -- backend/app` 为空）。
2. 只改 `debug=False and key==""` 这一档的实例化方式（改用 `Settings.model_construct`，
   它跳过 pydantic 校验与 `.env` 读取），其余档位仍走原来的 `Settings(**fields)`。
3. 新判据能分辨 Branch 1 与 Branch 2（dev + 空 key + 无开发态放行）：作者实测
   Branch 2 的 `detail` **以 Branch 1 的整句为前缀**（`startswith` 为真），所以任何
   `in` 形式的 detail 断言两层都命中；本卡改用**精确等值**，并补一条 `caplog` 断言
   Branch 1 的 `logger.error` 独有串 `auth_fail_closed`。原有的 `assert
   response.status_code == 503` 与既有 detail 断言均保留、未删未弱化。
4. 两段负控证明判据承重、且这三条变绿的原因就是这处改动：
   - 层负控：把该档 override 换成 `debug=True`（Branch 2 档）后，3 条全红，且红在
     **新加的精确等值**上（`assert 'Internal API...loopback dev.' == 'Internal
     API...ot configured'`），而原有的 503 与模糊 detail 两条**都没红**；
   - 回退负控：把实例化改法退回原样后，3 条精确回到 `assert 500 == 503`。
   - caplog 专项负控①：断言串换成不存在的 token ⇒ 3 条全红在该断言上；
   - caplog 专项负控②：移除 detail 等值断言 + 换 Branch 2 档 ⇒ 3 条全红在
     caplog 断言上，且失败信息显示捕到的是 Branch 2 的 `security.py:126` 日志。
   四段均以 `git show HEAD:<path> > <path>` 还原并做 `shasum -a 256` 与
   `git diff --quiet` 对账。
5. 同族用例未回退：两文件全量 17 条全 PASSED（含 4 条 403/200 档与 3 条 dev 档）。
6. `tests/unit` 目录级：开工 120 failed → 收工 117 failed；nodeid diff 相对**本卡
   开工快照**只有 3 条 `<`（恰为上述三条）、无任何 `>` 行。

## 三 请按重要性排序回答的问题

1. 跳过 pydantic 校验建出的 `Settings` 是否在**别的字段**上偏离了真实生产值，
   以致这三条测到的不再是它们声称要测的东西？作者只自检了 `DEBUG` /
   `INTERNAL_API_KEY` / `CORS_ORIGINS` / `NEO4J_PASSWORD` 四个字段。
2. 新判据是否与文案强耦合 —— 生产侧 detail 改一个字就静默失效？有没有更稳的
   层身份判据（例如绑到某个不随文案漂移的信号）？
3. Branch 1 在**真实运行的进程**里是否根本不可达（进程启动装配 `Settings()` 时
   校验就会抛，容器起不来）？若是，这三条测的究竟是什么？这个事实是否应当反过来
   质疑 Branch 1 或该校验之一的存在价值？
4. `caplog` 断言是否可能恒真或恒假？它是否受 logger 传播、级别配置、
   `tests/conftest.py` 里那个把 structlog 桥接进 stdlib 的 autouse fixture 影响？
   作者补跑了两段 caplog 专项负控（存档 `negctl-caplog-*`），请核对其充分性：
   - ①把断言串换成一个不存在的 token ⇒ 3 条全红在该断言上（证明不恒真）；
   - ②移除 detail 等值断言、只留 caplog 断言，并换到 Branch 2 档 ⇒ 3 条全红在
     该断言上，失败信息显示 caplog 捕到的是 `security.py:126` 那条 Branch 2 日志、
     其中不含 `auth_fail_closed`（证明捕获机制在工作，且该串确为 Branch 1 独有、
     该断言可独立分层，不依赖 detail 断言）。
   这两段是否足以支撑「该断言承重」？还缺哪一类反例？
5. 有没有比 `model_construct` 侵入更小、或更贴近「运维忘了配 key」真实形态的做法
   能让请求到达 Branch 1？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与判断依据。
若某条自述经核对不成立，请直接指出并给出反证。

## 五 边界

不评 U10-A~D 的改动（`.claude/agents/**`、`backend/app/api/v1/system.py`、
`backend/app/services/agent_service.py`、`backend/tests/unit/conftest.py`、
`backend/tests/support/authed_client.py`）；不评 W4 真连门；不评 pyright 存量；
不评 `_archive/`；不评 `_bmad-output/` 下的文档措辞。

## 最小读取面

- `git diff 052a9289 fe3787ce -- backend/tests/` 全文
- `backend/tests/unit/test_sync_batch_auth.py` 全文
- `backend/tests/unit/test_system_endpoint_auth.py` 全文
- `backend/app/config.py` 第 270-300 行
- `backend/app/security.py` 第 88-166 行
- `backend/app/main.py` 第 630-645 行
- `_bmad-output/审查/evidence-red-a2/*.txt`

终裁：**FAIL，不建议合并 `2fb779b3`**。共确认 **4 个 BLOCKER、2 个 HIGH**；本地正门、4 个负控和 19 个测试虽绿，但没有覆盖核心反例。

## 阻断发现

1. **BLOCKER / A、F — `required` 归一化会吞掉真实 enum 契约变化**

   [check-openapi-drift.py:119-126](<repo>/scripts/spec-tools/check-openapi-drift.py:119) 仅凭键名 `required` 排序字符串数组，不判断它是否真是 Schema keyword。

   合法 JSON Schema 的 `enum` 可包含对象；对象值中的数组有序。把：

   ```python
   {"enum": [{"required": ["first", "second"]}]}
   ```

   改成反序后，真实入口 `compare()` 实得：

   ```text
   (True, [])
   ```

   即假绿。`example`、`default`、扩展对象也同样受影响。这直接违反脚本宣称的“enum/其余数组保序”。

   当前快照的 281 个 `required` 数组都位于 `components.schemas`，尚未触发；但门对未来合法契约不健全。现有测试只覆盖真正 Schema `required`（[test:155-203](<repo>/backend/tests/contract/test_openapi_snapshot_drift.py:155)），M3 也只挑顶层 schema（[negative-control:89-95](<repo>/backend/scripts/openapi_drift_negative_control.py:89)）。

2. **BLOCKER / E — clean GitHub runner 会在漂移门前失败**

   workflow 没设置应用导出所需环境，直接导入 `app.main`（[api-spec-sync.yml:44-66](<repo>/.github/workflows/api-spec-sync.yml:44)）。应用强制读取未入库的 `backend/.env`（[app/__init__.py:10-16](<repo>/backend/app/__init__.py:10)），而 clean 默认会被安全校验拒绝（[config.py:274-298](<repo>/backend/app/config.py:274)）。

   无 TestClient、无写入复现：

   ```sh
   env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
     DEBUG=false CORS_ORIGINS=http://localhost:3000 \
     NEO4J_ENABLED=true NEO4J_PASSWORD= INTERNAL_API_KEY= \
     backend/.venv/bin/python -c \
     'import sys;sys.path.insert(0,"backend");import app.config'
   ```

   结果 exit 1：`NEO4J_PASSWORD must be set explicitly...`。同仓 [test.yml:108-121](<repo>/.github/workflows/test.yml:108) 已记录并补过这组 CI 环境，api-spec-sync 没有复用。本地裁判因加载未跟踪的 `backend/.env` 而不等价于 clean CI。

3. **BLOCKER / C、E — 保鲜链漏掉真实 OpenAPI 入口**

   workflow 只监听 `api/models` 等少数目录，push 甚至不监听 `backend/openapi.json`（[api-spec-sync.yml:21-35](<repo>/.github/workflows/api-spec-sync.yml:21)）；lefthook 也只覆盖 `{api,models,schemas}`（[lefthook.yml:31-40](<repo>/lefthook.yml:31)）。

   但契约还直接受 `main.py`、`config.py`、`mcp/server.py` 控制。真实历史反例：

   ```sh
   git show --name-only --oneline c44c48e8
   ```

   该提交只改 `backend/app/mcp/server.py`、测试和文档，却修复了 requestBody/OpenAPI 参数面丢失；当前 hook 和 workflow 都不会因它触发。`--no-verify`、未安装 lefthook、snapshot-only 收官提交均可能让快照继续陈旧。路径过滤只有匹配变更路径才触发 workflow，见 [GitHub Actions path filters](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)。

4. **BLOCKER / E — breaking-change 基线继续 fail-open**

   [api-spec-sync.yml:165-168](<repo>/.github/workflows/api-spec-sync.yml:165) 将任意 `git show` 失败退化成 `{}`；随后 [175-202](<repo>/.github/workflows/api-spec-sync.yml:175) 又用 `|| true` 吞掉 oasdiff 错误，并把解析异常计为 0。日志虽有 warning，最终输出及 summary 却显示“无 breaking changes”。

   当前基线实际存在：

   ```sh
   git cat-file -e 9af18b27:backend/openapi.json
   # exit 0
   ```

   所以取基线失败应 fail closed/UNKNOWN，不能伪装为零变化。oasdiff 的错误本应非零退出，见 [oasdiff error behavior](https://github.com/oasdiff/oasdiff/blob/main/docs/ERRORS.md)。

5. **HIGH / B — 跨机器缺口不止 Python 3.11/3.14**

   `fastapi>=0.104`、`pydantic>=2.5`、`fastapi-mcp>=0.1` 均未锁版本（[requirements.txt:18-47](<repo>/backend/requirements.txt:18)），CI 每次 fresh resolve；schema 还受项目名称、版本、API prefix、可选 MCP 注册等环境影响。

   正向证据：两个不同 `PYTHONHASHSEED` 均为 `DRIFT: none`；当前无多 method 路由、204 个 operationId 唯一、首次调用才建立 schema cache。结论只能是“当前本机依赖集合稳定”，不能缩写成“仅缺 Python 跨版本实测”。

6. **HIGH / D、H — Dredd 停用可接受，但替代覆盖声明不实**

   停用一个 24/24 红、根因不可考且已登记独立候选卡的 job，是合理的可逆隔离。况且旧 Dredd 本身同时有 `continue-on-error` 和 `|| true`（[api-spec-sync.yml:346-376](<repo>/.github/workflows/api-spec-sync.yml:346)），并不是真契约红门。

   但 workflow 声称“覆盖面并未丢失”不成立：

   - Schemathesis 文件会 `importorskip`，且只走 in-process ASGI（[test_openapi_contract.py:17-27](<repo>/backend/tests/contract/test_openapi_contract.py:17)）。
   - `test.yml` 的显式 CI 白名单没有运行它。
   - uvicorn/TCP、Neo4j service、example 回放及 `dredd-hooks.js` 覆盖确实丢失。

   `if:false` 导致 job skipped、`summary if:always()` 仍运行的 needs 行为本身正确，见 [GitHub job dependencies](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs)。但 push 时 breaking job 被跳过，summary 仍显示绿色 `None`，属 MEDIUM 假摘要。

## A–H 逐项裁决

- **A：FAIL / BLOCKER。** 易变 info 键 PASS；dict 排序实现 PASS、但测试不承重；真正 Schema `required` PASS；其他数组直接反序 PASS，但被同名嵌套键穿透；bool/number 标签修复 PASS。int/float 合并按 JSON 数值等值策略可接受。
- **B：PARTIAL / HIGH。** 当前 operationId、route order、cache/hash seed 未复现漂移；依赖、环境和 MCP 条件注册未封闭。
- **C：FAIL / BLOCKER。** 删除失效的 update-spec 本身 PASS；三层保鲜链因触发面与人工合并协议不完整而失败。
- **D：PARTIAL / HIGH。** “停用并另立卡”可接受；“Schemathesis 已承担覆盖”不成立。
- **E：FAIL / BLOCKER。** clean runner 前置失败；breaking 检测 fail-open；跨依赖版本可能意外红。
- **F：PARTIAL。** 四变异本身真实承重：M1/M2/M3 exit 1 且点名，M4 exit 0；19 tests 通过、7691 连接尝试为 0。但它们没有覆盖 BLOCKER 反例。`DETAIL_LINE_CAP=50` 不影响 exit/孤立负控，却能隐藏大量漂移中的目标点名行，MEDIUM。
- **G：PASS。** 对 `2fb779b3^..2fb779b3` 使用完整正确 pathspec，所有禁改文件均 0 行；`backend/app/**` 零改动。审查后快照 SHA 仍为 `5360e9d6…`。
- **H：PARTIAL / HIGH。** 三项均明确写成“建议默认、待裁决”，GitHub 未实跑及 HTTP 不等价也有显著声明；但没有声明 clean-CI 确定失败、触发面漏洞、依赖未锁、Schemathesis 未接入 CI。另 [验收单:24](<repo>/_bmad-output/审查/CARD-DEBT-openapi-sync-验收单.md:24) 把三个 workflow pathspec 写错到仓库根；正确命令虽仍证明 G=PASS，但原证据是假空口径。`17:2x`、7/8 文件计数及裁判 5/8 的“不证明什么”不完整为 LOW。

本轮未运行 GitHub Actions、Dredd、Schemathesis、TestClient 或 7691；GitHub 24/24 与日志 410 未独立刷新。`graphiti-canvas` 本会话未暴露，故未执行 Graphiti 搜索/记录。审查未修改任何文件，工作树状态保持原有验收单修改及 Codex 输出文件。

BLOCKER/HIGH 清零: 否



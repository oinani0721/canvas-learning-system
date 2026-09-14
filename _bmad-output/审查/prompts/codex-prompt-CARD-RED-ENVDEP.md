# 代码审查请求 — CARD-RED-ENVDEP（BATCH-2026-09-11-第十四批 / 车道 card-t10-red）

## 一 背景与最小读取面

本卡只改**两个文件**，目的是让 `backend/tests/unit/test_agent_service_extraction.py` 的三条既有红
不再依赖执行机器的环境：两条因缺 `pytest-mock` 而在 fixture 解析期 ERROR、一条因读到本机
`backend/.env` 的 `DEBUG_AGENT_RESPONSE=true` 而 FAILED。**不触及 `backend/app` 生产代码**。

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red`
分支 `card/t10-red`；PREREQ（前一卡 tip）= `8381417b`；本次审查绑定 SHA = `ee16b85a`（当前 HEAD）。

**请只读以下面，不要全仓扫描**：

1. 本卡代码 diff：`git diff 8381417b ee16b85a -- . ':(exclude)_bmad-output'`
2. `backend/tests/unit/test_agent_service_extraction.py`：文件头 import 段（含模块级
   `_HAS_PYTEST_MOCK`）+ `class TestDebugAgentResponseLogging` 全类（约 :301-:378）
3. `backend/requirements.txt` 的 `# Testing & Security Audit` 段（约 :140-:150）
4. `backend/app/config.py` 的 `:137-140`（`DEBUG_AGENT_RESPONSE` 字段声明）与 `:943`
   （`model_config = SettingsConfigDict(env_file=".env", …, case_sensitive=True, extra="ignore")`）
5. `backend/app/__init__.py` 的 `:14-16`（import 期 `load_dotenv(backend/.env)`）

环境事实（已实测）：本车道 venv 与其 symlink 目标 venv 里
`importlib.util.find_spec("pytest_mock")` 均为 `None`；`backend/.env:17` 为
`DEBUG_AGENT_RESPONSE=true`；ruff 0.15.9；pytest 9.0.2；Python 3.14.4。

## 二 作者自述（请独立核对，不要采信）

1. env 档（`test_config_has_debug_agent_response_field`）的修法**同时**隔离了两条输入面：
   `monkeypatch.delenv("DEBUG_AGENT_RESPONSE", raising=False)` 清进程环境变量，
   `Settings(_env_file=None)` 关 pydantic-settings 的文件读取。作者主张单靠 `_env_file=None`
   **不够**，因为 `app/__init__.py:16` 在 import 期已把 `.env` 的键注入 `os.environ`。
   作者实测三行对照：裸 `Settings()` → True；仅 `_env_file=None` → True；两者并用 → False。
2. 两条 `mocker` 档用 `@pytest.mark.skipif(not _HAS_PYTEST_MOCK, reason=…)`，作者主张在缺
   `pytest-mock` 时得到 **SKIPPED 而非 ERROR**，且 reason 可读；作者主张不能改用函数体内的
   `pytest.importorskip`，因为 fixture 解析早于函数体。
3. 负控三段各自红在**指定正文**：② 还原 env 修法 → `assert True is False` 于
   `assert settings.DEBUG_AGENT_RESPONSE is False`；③ 删两处 skipif → 2 条
   `fixture 'mocker' not found`；每段跑前/跑后全文件 `shasum -a 256` 逐字相同。
4. 地盘恰为两个文件，无第三个；`ruff check` rc=0；`ruff format --check` rc=1 但该 rc=1 在
   基线 `08100483` 的同一文件上**已经成立**，作者主张本卡新增格式违规为 0。

## 三 请按重要性排序回答的问题

0. env 档是否**仍有未被拦下的输入**能让 `DEBUG_AGENT_RESPONSE` 回到 True？请特别检查：
   其它 dotenv 注入点、`model_config` 的 `env_prefix` / `env_nested_delimiter` / `secrets_dir`
   之类来源、`case_sensitive=True` 下的大小写变体、以及 `app.config` 模块级 `settings =
   get_settings()`（`@lru_cache`）这一**单例**是否会被本档间接读到而绕开新建实例。
1. 两条 `mocker` 档在缺 `pytest-mock` 时是否**真的 SKIP**——既不是 ERROR，也不是"静默变成
   通过"（即断言从未执行却被计为 passed）？`reason` 文案是否足够让读报告的人知道为什么跳过？
2. `skipif` 以 `find_spec` 作判定面，是否覆盖不足？例如"装了但版本低于 `>=3.14.0`"
   或"装了但插件被 `-p no:pytest_mock` 停用"这类**门未覆盖的路径**，会表现成什么？
3. `requirements.txt` 只声明 `pytest-mock>=3.14.0` 而本批不安装，是否在别处留下**被 SKIP 掩盖
   的消费方**？（作者已核 `grep -rln mocker backend/tests/unit/*.py` 只命中本文件，请独立复核
   这个判据的取名面是否等于其主张。）
4. `_env_file=None` 这一写法与卡文允许的等价改法（改断言
   `Settings.model_fields["DEBUG_AGENT_RESPONSE"].default is False`）相比，是否**漏掉了**原断言
   "字段存在"（`hasattr`）的语义？当前实现保留了实例化，请判断这是否是更强的选择。
5. 其它你认为影响正确性或可信度的问题。

## 四 输出格式

每条发现写成：
`[BLOCKER|HIGH|MEDIUM|LOW] <一句话结论> — <file:line> — <一句核对思路>`
没有发现就明确写 `BLOCKER: 0 / HIGH: 0 / MEDIUM: n / LOW: n`。请给出这四档的计数汇总。

## 五 边界

- 只读，不要修改任何文件，不要执行写操作。
- 不要连接任何数据库（Neo4j 7691/7687）、不要访问 `canvas-vault/`。
- 不要评审 `backend/tests/unit/test_sync_batch_auth.py` / `test_system_endpoint_auth.py` 里的
  `_settings_factory`——那是另一张卡（T10-E）的地盘。
- 不要评审 `app/__init__.py` 里 `load_dotenv` 这一**设计本身**是否合理（既有决策，非本卡范围）；
  只评本卡的测试侧修法在该设计下是否成立。
- 不要建议本卡顺手做整仓 `ruff format`（已有裁定：语义卡不得代劳，另有专门的批次处理）。

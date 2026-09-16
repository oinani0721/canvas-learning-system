# 复核任务：CARD-RED-HYGIENE（BATCH-2026-09-11-第十四批 · 车道 T10 第 5/5）

你是独立复核者。只读审查，不要修改任何文件。

工作树：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red`
分支：`card/t10-red`
本卡最终 HEAD：`2c7402168ed4f44cbad3c7d3413ba4ff2233dcff`
本卡共三个 commit：`8bfcdfce`（主体）→ `b38e1d04`（只读对抗自审整改）→ `2c740216`（按你 r1 的整改）
`$PREV`（= 同车道上一张卡 CARD-EPW-COVERAGE 的 commit）：`f294878bb677ae54dcbf17277004efa2fa1ef97b`

看改动（对 `$PREV` 的累计代码面）：

```
git --no-pager diff --no-color f294878b 2c740216 -- . ':(exclude)_bmad-output'
```

只看本轮相对你 r1 的增量：

```
git --no-pager diff --no-color 8bfcdfce 2c740216 -- . ':(exclude)_bmad-output'
```

（`':(exclude)…'` 的写法是必需的，本机 git 不认 `':!…'`。）

---

## ⓪ 你的 r1 已被逐条处置，请重点复核这部分

你上一轮（绑 `8bfcdfce`）给出 **BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 4**。
逐条处置写在 `_bmad-output/审查/evidence-red-hygiene/RESPONSE-codex-r1-20260916.md`。摘要：

- **HIGH-1（目录级不增）**：车道**不自判通过**（D-15 规定车道对 HIGH 只能写理由、由主 session 裁定）。
  车道给的三条理由：① 你第一跑的 33 条 `>` 是你环境 Node 缺 `libllhttp.9.3.dylib`，你已自行归因；
  ② 你第二跑唯一那条 `>` 是 `candidate422`，而协议 `.claude/rules/card-batch-protocol.md` §3 第 79 行
  明确记载这条与 `mock_warning` 是 W4 哨兵红的载体、会在彼此之间翻转，并规定判据
  「绑 `blocked=` 次数 + 失败正文，**不绑 nodeid**」，且你那跑 `blocked=1` 而车道两跑 `blocked=0`；
  ③ 归属侧你自己给了更强证据（`$PREV` 已入库的 `epw-unit-close7.nodeids` 与本卡存档同为 34 条红）。
  **请复核这三条理由是否站得住**，并给出你对该 HIGH 的最终意见。
- **MEDIUM-1（guard 漏「绑定后就地改表」）**：已修。作用域改为只看 `health_check` 自己的语句
  （不下钻嵌套函数）；绑定后的就地修改（`AugAssign` / 下标赋值 / `Delete` / 八个 list 变更方法）
  一律报红；顶层必须是单个函数定义；覆盖声明收窄为「钉住生产在**绑定处声明**的名单」。
  **请用你 r1 那套方法复验**（抽真实 helper、内存替换 `inspect.getsource` 输入），
  尤其确认你演示的 `+= ["new"]` 与 `[0]="renamed"` 现在确实红。
  车道自己的复验落在 `FINAL3-guard-shapes-*.txt`（11 种形态）。
- **MEDIUM-2（第 0 分钟工作树干净证据不足）**：接受，记为**未证实 PARTIAL**，不追认。
- **MEDIUM-3（最终 commit 的 python-typecheck 未被独立证明）**：接受。本轮落盘
  `FINAL-precommit-hooks-*.txt`，并区分该 hook 的两种 skip（glob 不匹配 vs pyright 缺席）：
  实测本卡只有 commit1 暂存了 `backend/app/*.py`，commit2/3 是 glob 型 skip；
  commit1 成功那次的 hook 原始输出没留下，标记**历史 PARTIAL 不追认**。
- **LOW-1**：`_handler_was_not_reached` 的措辞已收窄（零 await 只证明没走到那一次 LLM 调用）。
- **LOW-2**：三处计数/索引/行号已修，含把格式豁免存档的 hunk 跨度收紧为实际被改行
  （`$PREV` 284-286 / `8bfcdfce` 247-249 / 当前 HEAD 250-252）。
- **LOW-3 / LOW-4**：已修（送 r1 之前的自审已同批处理；地盘证据已入库）。

### ⚠️ 本轮的新事实：最终 HEAD 上车道自己也跑出了 `>` = 1，与你 r1 第二跑同形

绑最终 HEAD `2c740216` 的目录级跑（`FINAL-R2-unit-close-*.txt`）实测：

    35 failed / 5165 passed / 35 skipped / 19 xfailed
    '<' = 30，**'>' = 1**
    NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)

那条 `>` 是 `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`，
失败正文首行逐字为

    - ('::1', 7691, 0, 0) on thread MainThread (owner=…test_accept_candidate_already_accepted_returns_422)

即协议 §3 指定的 W4 哨兵指纹（唯一指纹数实测 = 1）。连接**被拦下**（blocked，非 connected），
随后走 JSON 降级。三跑对照：`8bfcdfce` 34/`>`=0/blocked=0；`b38e1d04` 34/`>`=0/blocked=0；
`2c740216` 35/`>`=1/blocked=1。

⇒ 车道**没有**把 `>` = 0 写进验收单，如实记的是「最终 HEAD 这一跑 `>` = 1，该条是哨兵载体」。
**请你判**：这是否就是你 r1 HIGH-1 说的那件事？按协议 §3「绑 blocked= 次数 + 失败正文、
不绑 nodeid」的口径，本卡该不该被这一条拦住？还是说这条口径本身有问题、该另立卡修哨兵归属？
（车道三个 commit 都没碰任何与端口 / Neo4j / conftest 相关的文件，diff 面见上方命令。）

另：送你 r1 之前，本卡先跑过一轮只读多维对抗自审（记录入库
`SELF-REVIEW-adversarial-20260916.md`，23 条 findings，主 session 自核后判 17 条成立）。
**该记录里对自审流程本身的批评（反驳式验证偏松、把严重度混进成立性）也请你核一核是否属实。**

---

## ① 任务与地盘边界

本卡是 RED 卫生收尾卡，做了七件事：

- **(b)** `backend/tests/api/v1/endpoints/test_agents_health.py`：mock 的模板期望表由 12 项对齐到生产的 13 项（生产真相源 = `backend/app/services/agent_service.py` 的 `AgentService.health_check` 内局部变量 `expected_templates`），并把该列表提为类属性 `MockAgentService.EXPECTED_TEMPLATES`；新增一条防漂 guard `test_mock_expected_templates_match_production_truth_source`，用 AST 从生产源码取该字面量与 mock 逐元素比对。
- **(c)** `backend/tests/unit/test_sync_batch_auth.py` 与 `backend/tests/unit/test_system_endpoint_auth.py`：文件头鉴权矩阵中「DEBUG=True + 空 key」那一档由 200 改写为 503（P0-2 加固后的实际行为），并注明例外条件。纯文案改动。
- **(d)** `test_system_endpoint_auth.py`：新增 `TestSystemTestLLMAuthPrecedesHandler` 两条用例，把文件头声称的「dependency runs BEFORE the body handler」变成断言。新增 fixture `auth_client_with_llm_spy` 外露业务替身 `litellm.acompletion` 的句柄；承重用例与对照用例共用谓词 `_handler_was_not_reached`。对照用例只用 `app.dependency_overrides` 摘掉鉴权依赖这一个变量。**不改任何生产源码**。
- **(e)** 两条已知 flaky（`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`、`test_mock_degradation_transparency.py::TestMockScoringWarningLogs::test_mock_mode_logs_warning`）只定性、未改。
- **(f)** 退役死配置 `MEMORY_RETRY_BASE_DELAY` / `MEMORY_RETRY_MAX_DELAY`：删 `backend/app/config.py` 两个 Field 与其段注释、删 `backend/.env.example` 对应注释段，同批改 `backend/tests/unit/test_cache_configuration.py`（删整个 `TestMemoryRetryDelayFromSettings` 类、去掉两条真 `Settings` 默认值断言、从 `required_keys` 去掉两键、清掉两行 MagicMock 赋值），另把该文件里 4 处 `config.py:678` 的行号引用改成符号名（因为本卡删了 16 行，该行号已漂到 `:662`）。
- **(g)** `tests/contract/test_node_id_patterns.py::TestNodeIdPatternConsistency::test_pattern_matches_json_schema` 只定性、未改。
- **(h)** 地盘硬约束：**只允许改这 6 个文件**

  ```
  backend/.env.example
  backend/app/config.py
  backend/tests/api/v1/endpoints/test_agents_health.py
  backend/tests/unit/test_cache_configuration.py
  backend/tests/unit/test_sync_batch_auth.py
  backend/tests/unit/test_system_endpoint_auth.py
  ```

  `backend/app/config.py` 与同批另一条车道（T5）有声明交集：T5 只在该文件**新增** `TASK_CLEANUP_INTERVAL_SECONDS` 且避开 `MEMORY_RETRY` 段，本卡只**删除** `MEMORY_RETRY` 两字段，两侧 hunk 不重叠。

  明确禁改：`agent_service.py` / `agents.py` / `security.py` / `system.py` / `main.py` / `backend/app/models/**` / `specs/**` / 任何 `conftest.py` / `backend/requirements.txt` / 上面两条 flaky 的文件。

---

## ② 要核的判据

证据目录（已入库，可直接读）：`_bmad-output/审查/evidence-red-hygiene/`

1. **第 0 分钟自证**（`minute0-*.txt`）：pwd / 分支 / `$PREV` / 工作树干净 / venv+env / `pyright app` = 0 errors / 红基线 64。
   ⚠️ 该存档「工作树干净」一项卡方已按你 r1 MEDIUM-2 记为**未证实 PARTIAL**、不追认
   （存档只留计数不留 porcelain 原始路径，而空目录本身不计脏项）。请核这个处置是否到位，
   以及是否有别的办法能事后证明或证伪它。

2. **(b) 先红后绿 + 防漂负控**：
   - `agents-health-RED-*.txt` 应显示 2 failed，失败身份为 `assert 12 == 13` 与 `assert 10 == 11`；
   - `agents-health-GREEN-*.txt` 应显示 12 passed；
   - `agents-health-GUARD-GREEN-*.txt` 应显示 13 passed；
   - `agents-health-NEGCTL-rename-*.txt` 是负控输入：把 mock 里一个模板名改名（长度仍 13），期望**只有** guard 那条红、其余 12 条数量判据全绿，跑前跑后 `shasum -a 256` 逐字节相同。
     请判断这个负控是否真的证明了它声称的那件事。

3. **(c)** 两文件里陈述性的旧口径字面量应已清零；请自己 grep 核实，并判断替换后的文案是否与 `backend/app/security.py` 的实际分支行为一致。

4. **(d) 承重断言与对照输入**：
   - `auth-GREEN-*.txt`：两文件合计 19 passed；
   - `auth-NEGCTL-3mutants-*.txt` 是三段负控输入，逐段期望：
     M1 把对照用例的断言方向翻成与承重同向 → **对照**那条红；
     M2 把共用谓词改恒真 → **对照**那条红、承重仍绿；
     M3 把共用谓词改恒假 → **承重**那条红。
     三段跑完还原，跑前跑后 `shasum -a 256` 逐字节相同。
   - 请重点判断：承重那条断言是否可能恒真（即它是否能区分「鉴权确实前置」与「这个替身根本不在被测请求的路径上」）；对照用例只摘掉鉴权依赖是否真的是单变量。

5. **(f) 退役**：
   - census：`git grep` 证 `backend/app` 下生产消费方为 0（卡方的 census 排除了 `_bmad-output` / `.gdr` / `_bmad-archive` / `docs` 四个面——请核这个排除是否掩盖了真消费方）；
   - `cachecfg-RED-*.txt`：删字段后未改测试时应 3 failed（两条真 `Settings` 默认值断言 + 一条 `.env.example` 文档断言）；
   - `cachecfg-GREEN-*.txt`：同批改测试后 9 passed / 4 xfailed；
   - `pyright-after-retire-*.txt`：`pyright app` 仍 `0 errors`。
   - 请核前后测试计数的算术是否与「删了哪几条、修了哪几条」严格对得上，尤其：删掉一条 `xfail(strict=True)` 用例会让 xfailed 计数减一，卡方是否把「删掉」记成了「转绿」。

6. **(h)(i) 地盘与目录级**（⚠️ 以 `FINAL-*` 系列为准；无前缀的旧存档已被取代，多数带自查更正段）：
   - `FINAL-territory-*.txt`：代码面恰好 6 文件；`backend/openapi.json` 与 `$PREV` blob 逐字节相同；
     exclude 验伪锚 36 vs 0；本卡 commit 面含 `stderr` 的 = 0（取名面已按你 r1 的同类批评修正）。
   - `FINAL-R2-unit-close-*.txt` / `FINAL-R2-unit-comm-*.txt`：绑最终 HEAD `2c740216` 的目录级与 comm。
   - `attribution-*.txt`：卡方原先只用「本卡 4 个测试文件不在 BASE 红集」论证归属，
     **你 r1 指出那不充分，卡方已接受**并在存档加了更正段；归属现以你给的对照
     （`$PREV` 已入库的 `epw-unit-close7.nodeids` 与本卡存档同为 34 条红）为准。请复核。

7. **本卡 commit 用了 `LEFTHOOK_EXCLUDE=python-lint,spec-sync-root`**，依据写在 `lefthook-exclude-justification-*.txt`：
   - `python-lint` 依协议 §2.3 的 `ruff format --check` 主干既有漂移过渡条款，卡方声称剩余漂移只在 `test_cache_configuration.py` 且不在本卡改动行上，并已自清了本卡引入的那一处（`test_agents_health.py`）；
   - `spec-sync-root` 的跳过依据是「本卡不改变 OpenAPI 面」；
   - `python-typecheck` **未**放进 `LEFTHOOK_EXCLUDE`；按你 r1 MEDIUM-3，卡方已落盘
     `FINAL-precommit-hooks-*.txt` 并区分该 hook 的两种 skip（glob 不匹配 vs pyright 缺席），
     且把 commit1 成功那次标记为历史 PARTIAL 不追认。
   请独立复核这三条，尤其自己重算一遍格式漂移的**实际被改行**（不是 hunk 跨度），不要采信卡方结论。

8. **证据自身的诚实性**：evidence 目录里有两份文件名带 `SUPERSEDED`，是卡方自查后标注作废的（一份是关于证据的陈述与实际输出矛盾，一份是验伪锚跑挂了却当成锚）。请核它们的作废说明是否诚实、取代它们的文件是否真的修好了那个问题。另请自行检查其余存档里有没有类似的「硬编码结论句与紧邻输出矛盾」。

---

## ③ 最小读取面

- 上述 6 个地盘文件
- `backend/app/services/agent_service.py` 的 `AgentService.health_check`（生产真相源，只读）
- `backend/app/security.py` 的 `require_internal_api_key`（只读）
- `backend/app/api/v1/system.py` 的 `/system/test-llm` handler（只读）
- `backend/tests/contract/test_node_id_patterns.py`（只读）
- `lefthook.yml`（`python-lint` 与 `spec-sync-root` 两节）
- 红基线：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`
- `_bmad-output/审查/evidence-red-hygiene/` 全部存档

跑测试用：

```
cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider <target>
```

⛔ 禁止连 7691 / 7687，禁止写 live vault，禁止修改任何文件。

---

## ④ 反面问题（请逐条正面回答）

1. **(f) 的退役是否漏改了连带消费方？** 除静态引用外，有没有 `getattr` / `model_dump()` / 环境变量注入之类的动态访问路径会在运行期读这两个键？`Settings` 的 `extra` 策略是什么，若某个部署的 `.env` 仍设了这两个键会发生什么？

2. **(d) 的「拒绝时业务替身未被调用」断言是否恒真？** 也就是：如果有人把 patch 目标写错、把端点写错、或让请求在 body 校验阶段就被挡下，这条断言会不会照样绿？对照用例是否足以排除这些情形？对照用例结束时只 `pop` 掉鉴权依赖、保留 `get_settings` 覆盖，会不会污染同文件后续用例？

3. **(b) 的防漂 guard 是否存在门未覆盖的路径？** `_production_expected_templates()` 用 AST 解析生产源码。在什么形态下它会静默取到空表或错的赋值？它的两条断言（`len(...) == 13` 与 `== production`）是否有一条恒真？生产若把该列表改成从常量或文件读取，这条 guard 是会红，还是会以别的异常掩盖过去？

4. **目录级是否真的没有 `>`？** 请自己重跑一次目录级并对基线做差集，不要采信 `unit-comm-*.txt` 的结论。跑法（R-B14-3：`cd backend` 之后 `--ignore` 必须用相对路径）：

   ```
   cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit \
     --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider
   ```

   基线自证口径：`grep -vc '^#' <基线文件>` 应为 64。

5. **`pyright` 是否被跳过了？** 请核 commit 时 `python-typecheck` 确实实跑并通过，且 `pyright app` 在当前 HEAD 上仍是 `0 errors`。跑法（cwd 必须是 `backend/`，禁止 `| tail -1` 取汇总行）：

   ```
   P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright
   ( test -x "$P" || { echo 缺席; exit 1; }; cd <树>/backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' )
   ```

6. **(e)(g) 的「只定性不改」是否掩盖了本该在本卡处理的事？** 还是说它们确实越出了本卡地盘、登记移交是正确处置？

---

## ⑤ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 四级分组逐条列出，每条写明：

- 文件与符号名（有行号请一并给，但以符号名为准）
- 你实际跑了什么命令、看到什么输出
- 具体的失败场景：怎样的输入或怎样的后续改动会让它出错
- 建议处置（修 / 登记移交 / 不成立）

最后请单独给一行绑定声明：你本次审查绑定的 SHA，以及
`git --no-pager diff --stat --no-color <你审的SHA> HEAD -- . ':(exclude)_bmad-output'` 是否为空。
（本轮的目标是绑最终 HEAD `2c740216` 且 BLOCKER = 0、HIGH = 0；若你仍判有 HIGH，请写清它是
本卡引入的缺陷，还是环境/既有 flaky/协议口径问题。）

若某一级为 0 条，请显式写「BLOCKER: 0」「HIGH: 0」，不要省略。

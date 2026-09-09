> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u10-red-a · 卡 CARD-RED-A1-sentinel round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-A1-sentinel.md)"`
> 审查绑定: `0acea4e3..b8017248c59d6091c2827d5772cd20718502e6d1`（阶段一，**未** merge 候选树；提交后 HEAD，审时工作树干净）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> ⚠️ 字面「前三行」是 `Reading additional input from stdin...` + 两条 `codex_models_manager` 刷新超时 ERROR，不含 model 行；
> 故抄真正的会话头四行: `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra` / `session id: 01a085b2-cf37-7e50-85da-51e8f3f78306`

---

**审查结论：阶段一 PARTIAL；未发现可坐实的 BLOCKER/HIGH。** 12 条消红的核心结论成立，但存在新增 OpenAPI 契约缺陷，以及若干需要纠正的验收表述。

审查绑定仍为 `0acea4e3..b8017248c59d6091c2827d5772cd20718502e6d1`，八个代码文件与 HEAD 一致。以下按严重性排列。

1. **MEDIUM｜Q6：新增 14 个悬空 security 引用，不能仅以“根因已有”登记免修。**

   [openapi.json:28622](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/openapi.json:28622) 显式引用 `APIKeyHeader`，但组件在同文件 `:15737` 只定义 `InternalApiKey`。

   独立比较 U0/HEAD：悬空引用 operation 总数 **17→31**，其中 `/system/*` **2→16**。这 14 个新增 operation 原先继承 `main.py:568` 的有效全局声明，现在被无效的局部声明覆盖，属于本卡扩大的契约缺陷，建议交付前消除新增部分。

   插件的实际请求头是正确的：[main.ts:1753](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/frontend/obsidian-plugin/src/main.ts:1753) 手工发送 `X-CLS-Internal-Key`，与后端一致；它不会直接受方案标签影响。**插件请求正确与 OpenAPI 契约正确是两个结论。**

2. **MEDIUM｜Q2：装机验收尚未闭合，但没有证据证明现役插件出现启动死锁。**

   [system.py:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/api/v1/system.py:35) 确实同时保护 `/health` 和 `/setup-wizard`。但“没有 key 就返回 403”不准确：

   - 后端已配置 key、请求缺头：403，见 `security.py:144`。
   - 后端未配置 key：通常为 503，见 [security.py:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/security.py:96) 和 `:110`；非本地配置还可能先被 `config.py:295` 拒绝启动。
   - DEBUG 下的例外要求显式 bypass 和 loopback，并非自动放行。

   容器探针不受影响成立：`docker-compose.yml:229` 访问 `/api/v1/health`。裸调 `/system/health` 的 Tauri 调用方也确实已废弃，依据 [DEPRECATED.md:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/frontend/DEPRECATED.md:14) 及根构建脚本。

   **阶段一可以保留风险登记，但不能据此宣布装机验收通过。** 本卡完成该项验收前，应明确并验证“先配置后端 key，再向客户端提供 key”的流程。没有依据要求直接开放无 key 的 setup-wizard；它在 `system.py:492` 写入 vault，也不负责生成内部 key。

3. **LOW｜Q1：同一实例不移债成立；“进程终态逐项相同”不成立。**

   [neo4j_client.py:402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/app/clients/neo4j_client.py:402) 的实际顺序是：

   `health_check=False` → `_fallback_to_json()` → `:431` 设置 `_use_json_fallback=True` → 关闭 driver → 初始化 JSON → `:467` 设置 `_initialized=True`。捕获 JSON/IO 异常的分支在 `:473` 也设置 `_initialized=True`。

   因此下一次 `run_query()` 在 `:554` 不再初始化；即使 `cleanup()` 清除 initialized，fallback 标志仍然存在，重新初始化仍走 JSON。**这支持“不把同一实例的首次连接推给后续用例”。**

   但真实连接失败会在 `:534` 更新 `_last_health_check`，`AsyncMock(False)` 不会。隔离执行当前生命周期方法也确认：两条路径的连接控制状态相同，时间戳分别为有效时间与 `None`。因此应修正 [test_mock_degradation_transparency.py:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_mock_degradation_transparency.py:43) 的“逐项相同”，无需据此否定打桩方案。

4. **LOW｜Q5：spec 副本负控有效，但作者对负控和超时机制的两项解释不成立。**

   [status_conformance_probe.py:109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-sentinel/status_conformance_probe.py:109) 复用真实观测结果、删除声明再判断，足以证明探针能识别**本轮 403 未声明**这一缺陷。存档 `status-conformance-after-20260909T173152.txt:27–49` 的正负控结果成立。

   两处解释需要纠正：

   - [验收单:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-sentinel-2026-09-09.md:214) 声称真实声明变异必然执行业务体、连接 Neo4j，**不成立**。我们保留鉴权，仅在实际 `app.routes` 内存对象中删除 403 声明、清除 schema 缓存，原探针重新观测仍得到 **16 个 403、16 个未声明**，无需连接数据库。
   - `probe.py:10–11` 声称“尚未执行 schema 校验就超时”，**依据不足**。当前 Hypothesis 在 `core.py:1016` 先执行测试函数，`:1041` 才检查耗时并抛 `DeadlineExceeded`。日志没有出现检查名称，不能证明检查没有执行。

   可接受的结论应限定为：**已配置 key、请求缺头时，16 个实际 403 均已声明。** 它没有动态验证未配置 key 的 503、正确 key 后的业务状态及完整 contract。

5. **LOW｜自述⑦：“format-dirty 文件集合相同 ⇒ 零新增格式违规”不成立。**

   独立只读运行 `ruff format --diff`，仍要求修改本卡新增行：

   - `backend/app/api/v1/system.py:41–43`
   - `backend/tests/unit/test_mock_degradation_transparency.py:53–55`
   - `backend/tests/unit/test_review_mode_support.py:45–47`

   [ruff-format-baseline 存档:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-sentinel/ruff-format-baseline-20260909T181430.txt:2) 使用的是文件级集合，无法识别已脏文件中新增的违规。可以只整理新增块，保留存量行；`ruff check` 通过不能替代 format 检查。

其余关键核验结果如下，未发现相应新增缺陷：

- **Q3：鉴权断言 PASS。** [test_startup_health_check.py:191](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_startup_health_check.py:191) 只覆盖 `get_settings`，没有覆盖鉴权函数。隔离组装当前源码、直接执行原三条测试体：保留 router 依赖时三条通过；仅删除依赖后，无 key、错 key 两条均因实际返回 **200** 而失败，正确 key 那条仍通过。没有发现“依赖根本没挂也三绿”。这项反证不是完整 pytest 重跑。

- **Q4：已采样顺序没有移债，但不能外推任意顺序。** 独立重算原始日志：

  | 比较 | 删除红项 | 新增红项 |
  |---|---:|---:|
  | 开工 161 → 定稿 149 | **12** | **0** |
  | 202 基线 → 定稿 149 | **53** | **0** |

  因此问题中的“对 202 基线只少 12”混用了基线。定稿 [unit-final 日志:2187](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-sentinel/unit-final-20260909T181456.txt:2187) 的端口总账为 **0**，双序存档各 **72 passed、零哨兵**，这些比单看失败集合更有力。

  原本绿的冷首触候选仍包括 `test_verification_service_activation.py:221`：它可经真实 VerificationService 到 `verification_service.py:1931` 的 `get_mastery_store()`，未安装本卡的 health-check 桩。提前运行可能承担首拨；这是已有隔离边界，不能据此称本卡新增移债。

  作者未定位的重置者也有明确线索：[test_neo4j_client.py:653](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_neo4j_client.py:653) 在每条单例测试前后 reset，位于默认收集顺序中两族 C 文件之间，能解释全量两条红、五文件单跑仅一条红。

另外，`system.py` 仅 router 初始化发生变化，函数 AST 全部相同；六个测试文件原有断言全部保留。OpenAPI 同步检查独立运行得到 **`DRIFT: none (paths=194 schemas=354)`**，生成脚本与 hook 一致。上述结论仅绑定阶段一，未覆盖候选树 merge 后的复判；审查未修改文件或连接现网 Neo4j。



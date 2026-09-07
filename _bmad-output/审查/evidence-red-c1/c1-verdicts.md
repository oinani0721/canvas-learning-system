# CARD-RED-C1 — 10 条契约演进依据表

> 批次: BATCH-2026-09-07-第十三批 · 车道 `card-u11-red-c` · 卡 CARD-RED-C1
> 树: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c` · 分支 `card/u11-red-c` · 开工 HEAD `da690bf8`
> nodeid 来源: `red-align-da690bf8.md:117-126`（§二 C1 节），经三道「取错节」交叉核对（见 §0）
> 失败身份来源: `identity-open-20260908T065447.txt`（`-rA --tb=short`，5 文件文件级）

---

## §0 取错节交叉核对（§二.8 判据 c，开工实测）

| 锚 | 命令 | 结果 |
|---|---|---|
| 锚1 逐字节 | `diff c1-nodeids.txt c1-nodeids.expected.txt`（后者 = 卡文 §〇 附录人抄副本） | 无输出，rc=0 ✅ |
| 锚2 文件名分布 | `sed 's/::.*//' c1-nodeids.txt \| sort -u` vs `files-a.txt` | 无输出，rc=0（恰为 §一.(i) 那 5 个文件）✅ |
| 锚3 逐条在 202 内 | 逐条 `grep -cF -- '<nodeid>' red-baseline-202.bare.txt` | 10 条全 = 1 ✅ |
| 外来红 | `comm -23 reds-in-a-files.txt c1-nodeids.txt` | 9 行，与卡文 §〇 预声明逐条相同 ✅ |

基线形态复核：`grep -c '^#'` = 4 / `grep -vc '^#'` = 202（与卡文 §〇 第 3 轮更正一致）。
开工目录级 nodeid diff（`red-diff-open-20260908T064547.txt`）= **空**，汇总行 `= 173 failed, 4749 passed, 48 skipped, 122 warnings, 29 errors in 255.38s =`，末行 `rc=1` —— 基线在本车道树上完全复现。

---

## §1 依据表（10 条）

> 「依据栏空 ⇒ 处置只能是移交 U5-C」。本表 10 条依据栏均非空，但 **(e) 两条虽有依据仍判移交** —— 依据证明的是「lifespan 调用被删」这一事实，不足以证明「该删」；数据面判定归 U5-C（详见 §2）。

### ① `_retry_base_delay` 族（1 条）→ xfail(strict=True) 交接

| 项 | 内容 |
|---|---|
| **nodeid** | `tests/unit/test_cache_configuration.py::TestMemoryRetryDelayFromSettings::test_retry_delay_reads_settings` |
| **开工失败身份（原文）** | `E   AttributeError: 'MemoryService' object has no attribute '_retry_base_delay'` |
| **测试断言 file:line** | `test_cache_configuration.py:61-62`（改动前）`assert svc._retry_base_delay == 2.5` / `assert svc._retry_max_delay == 15.0` |
| **现行契约（实测）** | `grep -n 'retry_base\|retry_max\|MEMORY_RETRY\|_retry_' backend/app/services/memory_service.py` → **无输出（rc=1）**。`config.py:644 MEMORY_RETRY_BASE_DELAY default=1.0` / `:650 MEMORY_RETRY_MAX_DELAY default=10.0` 字段仍在 |
| **契约演进依据（1 行）** | `59586af1` 2026-03-26 `refactor(phase2): delete fake bridge/JSON dual-write code, replaced by GraphitiEpisodeWorker` —— `git show 59586af1 -- backend/app/services/memory_service.py` 实见删除行 `-            self._retry_base_delay = _settings.MEMORY_RETRY_BASE_DELAY` / `-            self._retry_max_delay = _settings.MEMORY_RETRY_MAX_DELAY` / `-                    delay = min(self._retry_base_delay * (2 ** attempt), self._retry_max_delay)`（×2）；`git log -S'_retry_base_delay' -- …memory_service.py` 首行即 `59586af1`（次行 `23512e86` 2026-02-11 为引入） |
| **消费方 census（(f) 分叉依据）** | `grep -rn 'MEMORY_RETRY_BASE_DELAY\|MEMORY_RETRY_MAX_DELAY' backend/app` → **只有 `config.py:644` / `:650` 两处定义，零消费方**；全仓其余命中全是 `.env.example:261/:264` 注释、测试、docs、`.gdr` 打包件 ⇒ 走「无消费方」分支 |
| **处置** | **xfail(strict=True)**，reason 写明「config.py:644/:650 字段零消费方，属死配置项，**接收卡 = `CARD-CONFIG-CLEANUP`**（死配置项清理，第十四批候选，已登记台账）」+ `[CARD-RED-C1]`。⚠️ r1 初版只写泛称「配置清理卡（登记）」，无可定位标识（Codex r1 LOW-1），已具名 |

### ② 桩值自相矛盾族（3 条）→ 全部 xfail(strict=True) 交接（走卡文默认 B）

| 项 | 内容 |
|---|---|
| **nodeid ×3** | `test_story_38_6_scoring_reliability.py::TestAC1TimeoutRetryAlignment::{test_inner_per_attempt_timeout_increased, test_retry_backoff_base_is_1_second, test_backoff_progression}` |
| **开工失败身份（原文）** | `E   assert 0.5 >= 2.0` / `E   assert 0.1 == 1.0` / `E   AssertionError: Attempt 0: expected 1.0s, got 0.1s` |
| **测试断言 file:line** | 改动前 `:37-39` / `:41-43` / `:60-65`；被断言物 = 同文件模块级本地桩 `:26-27` `GRAPHITI_JSON_WRITE_TIMEOUT = 0.5` / `GRAPHITI_RETRY_BACKOFF_BASE = 0.1`（`:25` 注释自述 "Constants removed from memory_service; define locally for test compatibility"） |
| **现行契约（实测）** | `grep -rn 'GRAPHITI_JSON_WRITE_TIMEOUT\|GRAPHITI_RETRY_BACKOFF_BASE' backend/app` → **无输出（rc=1）**，两符号在生产侧已不存在 |
| **契约演进依据（1 行）** | `59586af1` 2026-03-26 同上 —— `git show 59586af1 -- …memory_service.py` 实见 `-            self._retry_base_delay = GRAPHITI_RETRY_BACKOFF_BASE` 等删除行，两常量随 `_write_to_graphiti_json_with_retry` 一并删除 |
| **A/B 选择与理由** | **选 B（卡文默认）**。A（桩值改回 2.0/1.0）需要「能把断言重锚到某个现存生产符号」，而本卡实测 `backend/app` 下两符号 **0 命中** ⇒ 改成 2.0/1.0 后被断言物仍是**同文件模块级本地桩**，与「改断言去匹配 0.5/0.1」是同一种自证、只是数值方向相反，落在 §三「禁把断言改成锁本地桩的自证」射程内 ⇒ A 不可用 |
| **桩值处置** | `:26-27` 本地桩**保留不动**（删除会让同文件 `test_outer_timeout_covers_inner_total` import 期崩） |
| **同类两条仍绿（实测）** | `test_outer_timeout_is_at_least_10_seconds`：比 `agent_service.py:93 MEMORY_WRITE_TIMEOUT = 15.0` ≥ 10.0 ✅（⚠️ 该常量在 `agent_service.py` 而非 `memory_service.py`，后者 `grep` 0 命中——卡文第 3 轮更正，本卡复核确认）；`test_outer_timeout_covers_inner_total`：`inner_total = 3×0.5 + (0.1+0.2) = 1.8 ≤ 15.0` ✅。文件级 `files-20260908T065833.txt` 汇总 `42 passed`（开工 39 + 本卡翻绿 3），两条均未出现在 FAILED 集合 |
| **处置** | **xfail(strict=True)** ×3，reason 写明「重试/退避语义归 GraphitiEpisodeWorker，等价覆盖缺口归 CARD-EPW-COVERAGE（第十四批，登记）」+ `[CARD-RED-C1]` |

### ③ DEPRECATED 默认族（4 条）→ 3 条改断言 + 1 条 xfail 交接（**依据 sha 两个，非同一个**）

#### ③-a 改断言 3 条（被断言物 = 生产 config，非本地桩）

| 项 | 内容 |
|---|---|
| **nodeid ×3** | `test_story_38_4_dual_write_default.py::TestAC1SafeDefault::{test_settings_field_default_is_true, test_lowercase_alias_returns_true_by_default}` + `::TestAC3MissingEnvVar::test_missing_env_var_defaults_to_true` |
| **开工失败身份（原文）** | `E   AssertionError: Expected default=True for safe default, got default=False. …` / `E    +  where False = FieldInfo(annotation=bool, required=False, default=False, description='[DEPRECATED] Legacy JSON dual-write. Replaced by GraphitiEpisodeWorker.').default`；`E   AssertionError: Lowercase property alias should return True by default`；`E   AssertionError: Expected True when env var missing, got False. …` |
| **测试断言 file:line** | 改动前 `:38-42`（`Settings.model_fields[...].default is True`）/ `:55-59`（`settings.enable_graphiti_json_dual_write is True`）/ `:252-257`（`settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE is True`） |
| **现行契约 file:line（sed -n 实测）** | `config.py:473` + `:476` 各一行 `# DEPRECATED: Phase 2 replaced JSON dual-write with GraphitiEpisodeWorker.`；`:477-480 ENABLE_GRAPHITI_JSON_DUAL_WRITE: bool = Field(default=False, description="[DEPRECATED] Legacy JSON dual-write. Replaced by GraphitiEpisodeWorker.")`；`:928 def enable_graphiti_json_dual_write(self) -> bool:` 小写别名 property 仍在并直返该字段 |
| **契约演进依据（1 行）** | **`daa9fd37`** 2026-03-26 `refactor(phase2): rename misleading 'graphiti' functions to match actual behavior` —— `git show daa9fd37 -- backend/app/config.py` 实见 `-        default=True,` → `+        default=False,` 与 `+    # DEPRECATED: Phase 2 replaced JSON dual-write with GraphitiEpisodeWorker.` |
| **⚠️ 为何不是 59586af1** | `git show 59586af1 --stat -- …memory_service.py …main.py …config.py`（**限定这三条路径**）只列出 main.py 与 memory_service.py，`config.py` **不在列** ⇒ 若把这 3 条的依据也写成 59586af1 即为伪证。此为卡文 (b)「不得一个 sha 抄十遍」条款的实际命中。<br>⚠️ **表述更正（Codex r1 LOW-4）**：早先此处写成「输出只有两个文件」，读起来像是该 commit 全量只动了两个文件——**不对**。`git show 59586af1 --stat`（**不限路径**）实测是 **3 个文件**：`backend/app/main.py` / `backend/app/services/graphiti_bridge_service.py`（−409，整文件删除）/ `backend/app/services/memory_service.py`。`config.py` 在两种口径下都不在列，结论不变，但措辞必须绑定「限定路径的那条命令」 |
| **处置** | **改断言对齐现行契约**：`is True` → `is False`（3 处）；按 DD-13 改函数名 `…_is_true` → `…_is_false` / `…_returns_true_by_default` → `…_returns_false_by_default` / `…_defaults_to_true` → `…_defaults_to_false`；更正过期注释 `Verifies: config.py Field(default=True) at L409-412` → `Field(default=False) at L477-480 ([DEPRECATED], daa9fd37)`；`TestAC1SafeDefault` 类 docstring 说明 safe 语义已反转（**不改类名**，U11-B 的 C2 用例 `test_startup_log_dual_write_enabled_default` 挂在该类下） |
| **为何不是自证** | 被断言物是 `Settings.model_fields[...]` / `Settings(_env_file=None)` 实例 / 生产 property，全部来自 `app.config` 生产模块，**不在测试文件内** |
| **承重验证（实测，不止于论证）** | `loadbearing-3assertions.txt`：把生产 `config.py` 的 `FieldInfo.default` 在**内存里**改回 `True`（= `daa9fd37` 之前的契约）+ `model_rebuild(force=True)` 后，3 条**全部翻红 KILLED 3/3**，且每条都由**它自己那条断言的拒因**打红（逐条贴了拒因首行），不是被别的失败喂饱。三阶段设计防假杀：① 未变异时 3 条须全 PASS（前提门，防「基线就红」被误记成 KILLED）② 打印变异后的 `model_fields default` 与 `Settings(_env_file=None)` 实测值，自证变异真的生效（防「变异没打进去」的假 SURVIVED）③ 只把 `AssertionError` 记 KILLED，其它异常单独标注（防「导不进来 / 语法坏了」被记成击杀）。末行 `rc=0` |
| **承重验证零磁盘改动** | 脚本在 session scratchpad、非项目内；跑后 `backend/app/config.py` 的 sha256 与 `git show HEAD:` 版**逐字节相同**（`e5a8ce3e9b19ce922941e3fa9f0f9b3a6a5a30beeed79820878097e707155605`），`git diff --stat -- backend/app` 无输出 ⇒ 未违反「禁改 `backend/app/**`」 |
| **该验证的边界（如实）** | 只覆盖「字段默认被改回 True」这一路径；不覆盖「改的是 `.env` 或环境变量而非字段默认」——那条路径下 `test_settings_field_default_is_false` 按设计本就不该红（它锁的是字段默认，不是运行值） |

#### ③-b xfail 交接 1 条

| 项 | 内容 |
|---|---|
| **nodeid** | `test_qa_38_4_dual_write_extra.py::TestQAGetAttrDefenseInDepth::test_memory_service_getattr_fallback_is_false` |
| **开工失败身份（原文）** | `E   assert False is True` + `E    +  where False = Settings(…).ENABLE_GRAPHITI_JSON_DUAL_WRITE` |
| **测试断言 file:line** | 改动前 `:63 assert fresh_settings.ENABLE_GRAPHITI_JSON_DUAL_WRITE is True` / `:66-69 result = getattr(fresh_settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", False); assert result is True` |
| **现行契约（实测）** | `grep -n 'getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE"' backend/app/services/memory_service.py` → **无输出（rc=1）**；`grep -c 'ENABLE_GRAPHITI_JSON_DUAL_WRITE' …memory_service.py` = **1**，唯一命中 `:28` 是模块 docstring 的历史 AC 罗列（不是代码） |
| **契约演进依据（1 行）** | `59586af1` 2026-03-26 —— `git log -S'getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE"' -- …memory_service.py` 首行即 `59586af1`（次行 `f4838b30` 2026-03-26 为 `_enqueue_episode` 适配期，三行 `abf1d585`） |
| **⚠️ 对卡文的事实更正（本卡实测）** | 卡文 (d) 给的 reason 措辞「本用例的被测防御模式已无实现」**过宽**。全 `backend/app` census 实测：同形 `getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True)` 在 **`canvas_service.py:267 / :360 / :440 / :457 / :986 / :995` 仍有 6 处**，且其 fallback 默认值是 **True** 而非本用例名所称的 False。被删的是「memory_service 侧的那个防御点」，不是整个防御模式 ⇒ 已按此收窄 reason 措辞 |
| **为何不能只翻断言** | 翻成 `is False` 会变成「断言一个 memory_service 侧已无实现的防御模式」——函数名（`memory_service_getattr`）与 docstring（`:49` 声称 memory_service.py 用该 getattr）两层都指向一个不存在的被测对象，翻断言只掩盖不解决 |
| **处置** | **xfail(strict=True)**，reason 含上述收窄措辞 + canvas_service 6 处如实声明 + 归 `CARD-EPW-COVERAGE`（登记）+ `[CARD-RED-C1]` |

### ④ main.py 源码文本族（2 条）→ **移交 U5-C RED-R**（见 §2 完整论证）

| 项 | 内容 |
|---|---|
| **nodeid ×2** | `test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration::{test_main_imports_fallback_sync, test_fallback_sync_called_in_lifespan}` |
| **开工失败身份（原文）** | `E   assert 'get_fallback_sync_service' in '# Canvas Learning System - FastAPI Application Entry Point…'` / `E   assert 'sync_all_fallbacks' in '…'` |
| **测试断言 file:line** | `:441-446` / `:448-453`（读 `Path(main_module.__file__).read_text()` 做子串断言） |
| **现行契约（实测）** | `grep -n 'sync_all_fallbacks\|get_fallback_sync_service\|fallback_sync' backend/app/main.py` → **无输出（rc=1）**；lifespan 定义仍在 `main.py:82-83` |
| **依据（事实层，1 行）** | `59586af1` 2026-03-26 —— `git show 59586af1 -- backend/app/main.py` 实见删除整段 `# ✅ Story 38.8: Sync all JSON fallback files to Neo4j on startup` 块（含 `from app.services.fallback_sync_service import get_fallback_sync_service` / `await asyncio.wait_for(sync_svc.sync_all_fallbacks(), timeout=60.0)`）；`git log -S'sync_all_fallbacks' -- …main.py` 首行即 `59586af1` |
| **处置** | **移交 U5-C RED-R**。两条 nodeid **留在红集合不动**，本卡不改 `main.py`、不改这两条测试（`test_qa_38_6_scoring_reliability_extra.py` 收工 sha256 与开工逐字节相同：`b87a39a4fbcc0adbffadcef3eff5421fdd581467646152ba42155de92997a1ba`） |

---

## §2 (e) 为何怀疑是回归而非演进（移交理由，全部只读 grep 实测，未跑服务、未连库）

判据设计：**「演进」要求写侧与读侧同时退役，或写侧产物被替代者接管**；只要写侧仍在生产热路径产出、而全部回收路径断开且无接管者，就是数据面回归。

| # | 事实 | 实测命令 / 位置 |
|---|---|---|
| 1 | **写侧活着（热路径）**：`_record_failed_write` 在 `agent_service.py:5085`（`except asyncio.TimeoutError`）与 `:5101`（`except Exception`）被调，二者位于 `_trigger_memory_write`（`:5013`）内 | `cat -n backend/app/services/agent_service.py \| sed -n '5070,5105p'` |
| 2 | **写侧可达性**（⚠️ 计数口径已按 Codex r1 LOW-3 更正，原写「11 处」与本行自身的枚举 8+1+1 自相矛盾）：**直接调用 `AgentService._trigger_memory_write` 的生产调用点 = 10 处** —— `agent_service.py:3872 / :3992 / :4226 / :4932 / :5156 / :5169 / :5479 / :5653`（同类内 8）+ `batch_orchestrator.py:1013`（`self.agent_service._trigger_memory_write(`）+ `verification_service.py:3045`（`self._agent_service._trigger_memory_write(`）。**另有** `batch_orchestrator.py:974` 定义的**同名包装方法**，由 `:307` / `:735` 调用后转发到 `:1013` ⇒ 若按「名为 `_trigger_memory_write` 的调用点」计则为 **12 处**。三个数字对应三种单位，本表统一采「直接调用 AgentService 该方法」= **10**。任一口径下写侧均未被 `59586af1` 触及，结论不变 | `grep -rn 'self\._trigger_memory_write(\|_agent_service\._trigger_memory_write(\|agent_service\._trigger_memory_write(' backend/app --include='*.py'`（12 行，其中 `batch_orchestrator.py:307/:735` 打的是本类同名方法）；`grep -n '_trigger_memory_write' backend/app/services/batch_orchestrator.py`（见 `:974` 定义与 `:1013` 转发） |
| 3 | **第二条写侧**：`memory_service.py:499 _record_structured_outbox` 由 `:1662` 生产调用，append 写 `FAILED_WRITES_FILE`；其 docstring `:503` 明写「条目带 kind='knowledge_entity' 判别符, **recover_failed_writes 据此重放**」= 写侧**显式依赖**回收侧 | `cat -n …memory_service.py \| sed -n '495,516p'`；`grep -rn '_record_structured_outbox' backend/app --include='*.py'` |
| 4 | **回收路径 1 断**：`FallbackSyncService.sync_all_fallbacks`（`fallback_sync_service.py:54`）在 `backend/app` 下**零生产调用方**（命中只有自身定义 `:54` / `:657` 与 `memory_service.py:2682` 的 docstring 文字引用） | `grep -rn 'sync_all_fallbacks\|get_fallback_sync_service' backend/app` |
| 5 | **回收路径 2 断**：`MemoryService.recover_failed_writes`（`memory_service.py:2679`）全仓调用方**只有测试**（`test_a7_honest_failure.py` / `test_story_38_6…` / `test_qa_38_6…` / `tests/integration/…`），生产 0 | 全仓 `grep -rn 'recover_failed_writes'`（排除 .venv/.git/_bmad-*/.gdr） |
| 6 | **替代者未接管**：`episode_worker.py` 对 `failed_writes` / `FAILED_WRITES_FILE` / `outbox` **零引用** | `grep -rn 'FAILED_WRITES_FILE\|failed_writes\|outbox' backend/app/services/episode_worker.py` → rc=1 |
| 7 | **⚠️ 最像「已接管」的假象**：`main.py:216 recovered = await event_bus.recover_outbox()` 启动期确实在跑，但它恢复的是 `event_bus.py:49 OUTBOX_DIR = backend/data/outbox`（Story 5.7 EventBus Tier-2），与 `backend/data/failed_writes.jsonl`（Story 38.6）**不是同一文件、不是同一机制**。只看「启动期还有没有恢复动作」会得出反向结论 | `grep -rn 'outbox' backend/app --include='*.py'`；`event_bus.py:47-49` |
| 8 | **删除是「以 X 之名扫到 Y」**：`59586af1` commit message 自述 `remove Story 38.4/38.8 dual-write blocks from main.py`。但被删的 Story 38.8 块调用的 `sync_all_fallbacks` 同步的是**三个**文件（`fallback_sync_service.py:7-8` 头注释：`data/failed_writes.jsonl` Story 38.6 / `app/data/canvas_events_fallback.json` Story 38.5 / learning_memories）。真正退役的「JSON dual-write」只是其中一支；`failed_writes.jsonl` 属 Story 38.6 **评分失败回收**，是另一条机制，被顺带切断 | `git show 59586af1 -- backend/app/main.py`；`sed -n '1,40p' backend/app/services/fallback_sync_service.py` |

**结论**：写侧 11 处生产调用仍活、两条回收路径双双零生产调用方、替代者未接管、启动期恢复的是另一机制 ⇒ 怀疑 `59586af1` 以「删 dual-write」之名连带切断了 Story 38.6 评分失败回收这条独立链路 = **数据面回归，非契约演进** ⇒ 移交 U5-C RED-R 定性。

**本卡在 (e) 上未证明的**（不得据本表宣称已证）：
- **未证明现网真的有 pending 条目在丢**。`backend/data/failed_writes.jsonl` 今日 06:46 的 mtime 是**本车道自己的 pytest 跑**造成的（`backend/data/.gitignore:5 *.jsonl` 覆盖 ⇒ `git status` 恒绿看不见这类污染），**不能**当作生产在写的证据；本卡未碰 live vault、未跑服务、未连 7691/7687。
- **未证明「应恢复 lifespan 调用」**这一处置 —— 那是 U5-C 的定性范围，本卡只提供上述 8 条源码层证据。
- **未评价这两条测试本身的门强度**：`"sync_all_fallbacks" in source` 是子串断言（对复制/位移/末尾追加失明），即便回归属实它也不是好门；但「无替代覆盖不许删」，移交分支下本卡本就不改它们。

---

## §3 处置汇总与算术

| 处置 | 条数 | nodeid |
|---|---|---|
| 改断言对齐现行契约 | **3** | `test_story_38_4_dual_write_default.py::TestAC1SafeDefault::test_settings_field_default_is_true` / `::TestAC1SafeDefault::test_lowercase_alias_returns_true_by_default` / `::TestAC3MissingEnvVar::test_missing_env_var_defaults_to_true` |
| xfail(strict=True) 交接 | **5** | `test_story_38_6_scoring_reliability.py::TestAC1TimeoutRetryAlignment::{test_inner_per_attempt_timeout_increased, test_retry_backoff_base_is_1_second, test_backoff_progression}` / `test_qa_38_4_dual_write_extra.py::TestQAGetAttrDefenseInDepth::test_memory_service_getattr_fallback_is_false` / `test_cache_configuration.py::TestMemoryRetryDelayFromSettings::test_retry_delay_reads_settings` |
| 移交 U5-C RED-R | **2** | `test_qa_38_6_scoring_reliability_extra.py::TestStartupIntegration::{test_main_imports_fallback_sync, test_fallback_sync_called_in_lifespan}` |
| **合计** | **10** | ✅ |

⇒ 收工目录级 nodeid diff 的 `<` 行应**恰为 8 条**（3 条因改名转绿使旧 nodeid 消失 + 5 条转 xfailed）；移交 2 条既不在 `<` 也不在 `>`。
⇒ 文件级 `expected-failed.txt` = 外来红 9 条 ∪ 移交 2 条 = **11 条**。

### 依据 sha 分布（自证「不是一个 sha 抄十遍」）

| sha | 日期 | 覆盖条数 | 被删/被改符号 |
|---|---|---|---|
| `59586af1` | 2026-03-26 | 7（① 1 + ② 3 + ③-b 1 + ④ 2） | `_retry_base_delay` / `_retry_max_delay` / `GRAPHITI_JSON_WRITE_TIMEOUT` / `GRAPHITI_RETRY_BACKOFF_BASE` / memory_service 侧 getattr 防御点 / main.py Story 38.8 sync 块 |
| `daa9fd37` | 2026-03-26 | 3（③-a） | `config.py` `ENABLE_GRAPHITI_JSON_DUAL_WRITE` `default=True` → `default=False` + `[DEPRECATED]` |

---

## §4 预声明例外集（(g)：33 + 4 条，本卡一条不动）

本卡**不改**下列五处 Y4-D（`f19dcff6`, 2026-04-07）skip 标记，33 条同族被掩盖项与另 4 条被顺带关掉的原本绿测试**全部不去 skip**：

| # | 标记位置 | 掩盖条数 |
|---|---|---|
| 1 | `test_memory_service_write_retry.py:37-44` 模块级 `pytestmark` | 18 |
| 2 | `test_graphiti_json_dual_write.py:33-40` 模块级 `pytestmark` | 8 |
| 3 | `test_failure_observability.py:263-266` 类级 `TestMemoryServiceDualWriteFailure` | 3 |
| 4 | `test_story_38_6_scoring_reliability.py`（`TestAC3StartupRecovery` 类级） | 3 |
| 5 | `test_qa_38_6_scoring_reliability_extra.py:326-329` 类级 `TestFullCycleIntegration` | 1（另 1 条归 R/U5-C） |

另 4 条被 Y4-D 顺带关掉的**原本绿**：`test_graphiti_json_dual_write.py::TestGraphitiJsonDualWrite::{test_config_flag_disables_dual_write, test_fire_and_forget_doesnt_block_return, test_timeout_protection}` + `test_story_38_6_scoring_reliability.py::TestAC3StartupRecovery::test_recover_no_file`。

**理由**：去掉任一 skip ⇒ 被掩盖条目重回目录级红集合 ⇒ nodeid diff 出现 `>` 行 = 阻断；且 `skip` 优先于 `xfail`，两种标记不能叠加。这 37 条归第十四批 Y4-D 尾巴微卡 + `CARD-EPW-COVERAGE`（等价覆盖缺口独立卡，只登记）。

**证据**：
- `y4d-skip-marks-open.txt` / `y4d-skip-marks-close.txt` 留存五处标记原文；
- **硬判据**：`git diff --no-color -- backend/tests/unit/ | grep -E '^[+-][^+-]' | grep -i 'skip'` → **无输出（rc=1）**，本卡 diff 里一处 skip 相关改动都没有；
- `git diff` 里出现的 `def test_` 增删行**恰为** 3 组改名（其余 5 条只加装饰器，def 行未动）；
- SKIPPED 集开工/收工 `diff` —— 见 §5。

---

## §5 裁判证据索引（全部落 `_bmad-output/审查/evidence-red-c1/`，`.txt`，末行 `rc=`）

| 判据 | 文件 | 结果 |
|---|---|---|
| 开工目录级 | `unit-open-20260908T064547.txt` / `red-diff-open-20260908T064547.txt` | diff **空**；汇总 `173 failed, 4749 passed, 48 skipped, 122 warnings, 29 errors`；末行 `rc=1` |
| 开工 SKIPPED 集 | `rs-open-20260908T065015.txt` / `skips-open-20260908T065015.txt` | 汇总 `48 skipped`；末行 `rc=1` |
| 失败身份原文 | `identity-open-20260908T065447.txt` | `19 failed, 39 passed, 6 skipped`；FAILED 集合 = C1 10 ∪ 外来红 9 |
| 文件级（收工） | `files-20260908T065833.txt` / `files-failed-20260908T065833.txt` | `11 failed, 42 passed, 6 skipped, 5 xfailed`；`grep -c XPASS` = **0**；`diff files-failed expected-failed` **无输出** |
| 格式存量对照 | `ruff-format-baseline-open.txt` / `ruff-diff-head.txt` / `ruff-diff-after.txt` | 开工收工同为 3 红 2 绿；**内容口径**：HEAD 版与本卡版 `ruff format --diff` 的 ± 内容行**多重集逐条相同**（`diff` rc=0）⇒ 本卡零新增漂移，3 红全为存量（D-16 甲：不顺手修） |
| 5 文件 sha | `files5-sha-open.txt` | `test_qa_38_6_scoring_reliability_extra.py` 收工 sha 与开工**逐字节相同** ⇒ 移交路线确未碰 |
| xfail 基线 | `xfail-baseline-open.txt` | 5 文件开工**均无既有 xfail** ⇒ 收工出现的 5 处 `strict=True` 全为本卡新增，可区分 |
| **收工目录级（终审绑定轮）** | `unit-after-20260908T071724.txt` / `red-diff-20260908T071724.txt` | 汇总 `165 failed, 4752 passed, 48 skipped, 5 xfailed, 121 warnings, **29 errors**`（errors 回到基线 29）；末行 `rc=1`；`grep -c '^>'` = **0**；`grep -c '^<'` = **8**，逐条 `grep -cF` = 1 且恰为本卡 8 条处置；移交 2 条各 `grep -cF` = **0**（不在 `<` 行）✅ |
| 收工 SKIPPED 集 | `rs-close-20260908T070403.txt` / `skips-close-20260908T070403.txt` | 汇总 `48 skipped`；末行 `rc=1`；与开工集的差异**仅为行号标签位移**，详见下方 §5.1 |
| 被弃的两轮（环境噪音） | `unit-after-20260908T065956.txt` / `unit-after-20260908T071053.txt` | 各 30 errors + 1 条 `>`（teardown ERROR），归属见 `tmp-window-attribution.txt`；两轮的 `<` 行集合与终审轮**逐条相同**，差别只在那一条噪音 |

### §5.1 SKIPPED 集 diff 非空的成因（如实登记卡文判据的一处盲区）

卡文 §二.2 要求 `diff skips-open skips-close` **为空**。实测**非空**，但差异有且只有 4 行，全部来自 `test_story_38_6_scoring_reliability.py`，且**只是行号标签位移**：

| 开工行号 | 收工行号 | 位移 |
|---|---|---|
| 154 / 165 / 190 / 236 | 181 / 192 / 217 / 263 | **27 / 27 / 27 / 27** |

- `git diff --numstat -- backend/tests/unit/test_story_38_6_scoring_reliability.py` = `27  0`（净增 27 行、零删除）；
- 三个 hunk 头 `@@ -36,0 +37,9 @@` / `@@ -40,0 +50,9 @@` / `@@ -59,0 +78,9 @@` **全部在 skip 标记之前** ⇒ 常数位移 27 正是预期结果；
- 归一化行号后（`sed -E 's/\.py:[0-9]+:/.py:<LN>:/'` 再 `sort` 后 `diff`）**rc=0，集合逐条相同**；
- 其余 4 个含 skip 的文件在原始 diff 里**一行未出现**。

**不依赖归一化的硬判据**：`git diff --no-color -- backend/tests/unit/ | grep -E '^[+-][^+-]' | grep -i 'skip'` → **无输出（rc=1）**，本卡 diff 里零 skip 相关改动。

⇒ 该判据对「同文件插入行导致的行号标签位移」失明。本卡**不拿归一化结果冒充「原始 diff 为空」**，而是如实登记：原始 diff 非空、成因已定量归因、集合未变。建议后续 RED 卡的 §二.2 判据改为「归一化行号后 diff 为空 **且** `git diff` 内零 skip 改动」双条件。

### §5.2 `-rs` 标志的语义陷阱（本卡实测，记入台账）

pytest 的 `-r` 是**替换**而非追加短摘要类别：默认 `-q` 给 `fE`，显式传 `-rs` 后短摘要**只剩 SKIPPED**，FAILED/ERROR 行消失。同一 HEAD 两轮实测：

| 存档 | `grep -c '^FAILED '` | `grep -c '^SKIPPED'` |
|---|---|---|
| `rs-close-20260908T070403.txt`（`-q -rs`） | **0** | 48 |
| `unit-after-20260908T071053.txt`（`-q`） | **165** | 0 |

⇒ 不能从 `-rs` 那一轮派生 nodeid 差集（会得到「202 条全部消失」的假差集）。本卡的 nodeid 判据自始至终只用 `-q` 轮，SKIPPED 判据只用 `-rs` 轮，未受影响；曾一度从 `rs-close` 派生差集，当场自查发现并把两个派生文件移出 evidence 目录（未入库）。若要一轮同时取两者，应传 `-rfEs`。

---

## §6 本卡对卡文的事实更正（3 处，均写卡期未预见、开工实测发现）

1. **(d) 3 条的依据 sha 不是 `59586af1` 而是 `daa9fd37`** —— `git show 59586af1 --stat` 的文件列表**只有 main.py 与 memory_service.py**，`config.py` 不在列。卡文 §二.4 已预留「config.py 若不在列，另用 `-S'[DEPRECATED] Legacy JSON dual-write'` 找」的分支，本卡走该分支取到 `daa9fd37`。
2. **(d) ③-b 的 reason 措辞须收窄** —— 卡文原稿「本用例的被测防御模式已无实现」过宽；实测同形 `getattr(settings, "ENABLE_GRAPHITI_JSON_DUAL_WRITE", True)` 在 `canvas_service.py` 仍有 **6 处**（`:267/:360/:440/:457/:986/:995`）且 fallback 默认值是 **True**（与用例名所称 False 相反）。已改为「memory_service 侧的该防御点已删」并把 6 处如实写进 reason。
4. **写侧调用点计数 11 → 10**（Codex r1 LOW-3 抓到，见 §2 行 2）—— 原文的枚举本身是 8+1+1=10，写出来的数字却是 11，是**内部自相矛盾**；三种单位（直接调用 AgentService 该方法 10 / 含同名包装的全部调用点 12 / 按上游入口 11）必须择一并写明。
5. **`git show 59586af1 --stat` 的措辞**（Codex r1 LOW-4）—— 不限路径实测是 **3** 个文件（多一个整文件删除的 `graphiti_bridge_service.py`），原文写「只有两个文件」把限定路径的输出说成了全量。结论（`config.py` 不在列）两种口径下都成立。
6. **收工 skip 快照采法**（Codex r1 LOW-2）—— 原版按开工行号 `sed` 抓，本卡插入 27 行后 `test_story_38_6` 那段抓空，导致「五处标记原文均已留存」这句**比证据宽**。已改内容锚定重采 → `y4d-skip-marks-close-v2.txt`，五块正文归一化后与开工**逐条相同**（`diff` rc=0），实测行号 `37 / 33 / 263 / 162 / 326`。
7. **配置清理卡缺可定位标识**（Codex r1 LOW-1）—— 原 reason 只写「配置清理卡（登记）」，解除 xfail 时无法从记录定位接收卡。已改为具名 `CARD-CONFIG-CLEANUP`。

3. **同文件模块 docstring 未改，如实登记** —— `test_story_38_4_dual_write_default.py:8/:10` 仍称 "AC-1: Fresh installation defaults … to True" / "AC-3: Missing env var defaults to True"。卡文 §三 只授权改「§〇 点名的 10 个用例的函数名/函数体/装饰器/docstring」与（(d) 明文授权的）`TestAC1SafeDefault` 类 docstring，**未授权**改模块级文件头；该文件头同时描述 AC-2（U11-B 的 C2 地盘）。为免与 U11-B 冲突且不越界，本卡**不改**，登记为残留名实不一致项。

---

## §7 独立复核（Codex）轮次与裁定

### r1 — `343fce8e`，**BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4**

存档 `_bmad-output/审查/codex-review-CARD-RED-C1.md`。四条 LOW **全部经本车道独立复验成立，全部整改**（未驳回任何一条）：

| # | 发现 | 我的复验 | 整改 |
|---|---|---|---|
| LOW-1 | `test_cache_configuration.py` 的 xfail reason 只写「配置清理卡（登记）」，无可定位接收卡标识 | 成立。卡文硬约束要求 reason「写明归哪张卡」，泛称不满足 | reason 改为具名 **`CARD-CONFIG-CLEANUP`**（死配置项清理，第十四批候选） |
| LOW-2 | 收工 skip 快照按旧行号抓，`test_story_38_6` 那段抓空 ⇒「五处原文均已留存」比证据宽 | 成立。实测 `y4d-skip-marks-close.txt` 该段确为空标题，下一行已进入第五个文件 | 内容锚定重采 `y4d-skip-marks-close-v2.txt`（`-A7`；`-A4` 会截断两个模块级块末行）；与开工归一化 `diff` **rc=0** |
| LOW-3 | 「11 处生产调用方」未说明统计口径（直接调用 10 / 含同名包装 12 / 按上游入口 11） | 成立，且比 Codex 说的更糟：**我自己那一行的枚举是 8+1+1=10，数字却写 11**，内部自相矛盾 | §2 行 2 改为三口径写明，本表统一采「直接调用 `AgentService._trigger_memory_write`」= **10** |
| LOW-4 | 「`59586af1 --stat` 只有两个文件」有误，不限路径实测有第三个 `graphiti_bridge_service.py` | 成立。实测 3 文件（多一个 −409 整文件删除） | ③-a 行措辞改为绑定「限定这三条路径的那条命令」，并贴出不限路径的真实 3 文件列表 |

### Codex 独立确认的判据（第二来源印证，非我自述）

- 从**原始日志重算**：`202 → 194，移除恰好 8 条、新增 0 条`，两条移交测试仍红 —— 与本卡 §3 的算术独立吻合。
- 三条翻绿断言「均能捕捉生产默认值变回 True」—— 与本卡 A18 的内存变异实测（KILLED 3/3）结论一致。
- `canvas_service.py` 的 6 处 getattr「真实存在，第三参数全部为 True」—— 印证本卡 §6.2 的措辞收窄是必要的。
- 五条 xfail「全部为 `strict=True`」；两个 `MEMORY_RETRY_*` 在 `backend/app` 下「只有配置定义，无消费引用」。
- 历史删除行「逐项吻合」，**7＋3 分组成立**。
- 最终提交「仅在 AC1 三个方法前各新增 9 行，类级 skip 与被遮蔽用例均未改」；「其他用例、所有类名和类级装饰器保持不变，移交文件也完全未改」。

### Codex 提出的两条实质性观察（本卡采纳并记录，不改结论）

1. **选 B 的依据可以更准**：「两个旧名字零命中」只证明**旧符号消失**。现存 `episode_worker` 仍有 `can_retry` / `backoff_seconds`，但采用**随机退避**，并不实现原来固定的 2 秒 / 1·2·4 秒契约 ⇒ 「无可重锚生产符号」的结论**成立且更强**（不是没有重试概念，而是没有实现同一契约的符号），A 方案仍不可用。
2. **`test_episode_worker_retry.py` 5 个用例的实际覆盖面**（对 `CARD-EPW-COVERAGE` 有直接价值，原样收录）：入队处理成功 / 失败三次后第四次成功与退避范围 / 耗尽重试写死信 / 指标 / 显式 `request_id` 进入死信。**未覆盖**：旧单次超时、固定退避、`MemoryService` 配置读取、getattr 防御、旧失败文件恢复；且「退避范围断言甚至允许恒零延迟通过」。⇒ 支持「已有替代机制和部分覆盖」，**不足以证明完整等价覆盖或完成退役** —— 与本卡「只登记缺口、不宣称等价」的处置一致。

### Codex 明确未能独立确认的面（如实转录，不代为背书）

- (e) 的静态调用关系它只确认了 `backend/app` 范围，**未扩面**背书「全仓只有测试」，**未验证现网 pending 数据** —— 与本卡「本卡未证明什么」第 4 条一致。
- `/tmp` 归属的 `stat` / `ps` / 跨 session 通告**只有作者转述**，它无法独立确认写者身份。
- 它指出「不能单凭『终审绑定轮』这个名称证明其输入精确绑定 `343fce8e`」。**本卡据此补证**（见下）。

### 补证：终审轮的输入确实是后来提交为 `343fce8e` 的那份内容

| 环节 | 实测 | 命令 |
|---|---|---|
| 4 个被改测试文件最后修改时刻 | `06:57:40` / `06:57:26` / `06:57:07` / `06:56:21` | `stat -f '%Sm %N'` |
| 终审轮起跑 → 结束 | `07:17:24` → 落盘 `07:21:34` | 存档文件名 TS + `stat` |
| commit 时刻 | `07:24:48` | `git log -1 --format='%h %ad'` |
| 工作树内容 == commit 内容 | **4/4 SAME**（`f1073d45…` / `86c6f161…` / `f6395cde…` / `27c5ea1b…`） | 逐文件 `shasum -a 256` vs `git show 343fce8e:<file> \| shasum -a 256` |

链条：**所有代码编辑（≤06:57:40）< 终审轮起跑（07:17:24）< 终审轮结束（07:21:34）< commit（07:24:48）**，且期间无任何编辑（mtime 为证），工作树内容与 commit 内容逐字节相同 ⇒ 终审轮跑的正是 `343fce8e` 的代码内容。

> ⚠️ 该补证覆盖的是 **r1 送审时的状态**。r1 之后为整改 LOW-1 改动了 `test_cache_configuration.py`（reason 文案），**属代码改动 ⇒ 按 D-15 必再送一轮**，见 r2。

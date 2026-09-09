# CARD-RED-NEW — tests/unit 既有红「新」类 8 条三选一裁定表

> 批次: BATCH-2026-09-07-第十三批 · 车道 U11-C · 卡 CARD-RED-NEW
> 树: `card-u11-red-c`（分支 `card/u11-red-c`）· 开工 HEAD `f043f5d4`
> 统一基线: `evidence-b13/unit-red-baseline-da690bf8.txt`（202 nodeid @ `da690bf8`）
> 裁定计数: **测试写错 7 / 契约演进 1 / 回归 0**（#8 = 契约演进，处置性质为「防御深度加强」；Codex r1 MEDIUM-4 指出「防御深度不足」是第四类别、未回答三选一，已归类）

---

## 〇 裁定方法学（本卡对卡文推理的一处升级 + 一处更正）

**卡文给的判据**是「生产与测试同 commit 诞生 ⇒ 不可能是回归」。开工核验发现这条**不充分**：

- 同 commit 只说明两者同批引入。若此后某个 commit 改了判定行或断言行，仍可能是回归。
- 因此本卡把判据升级为：**判定行与断言行的语义自引入后从未变过**（`git log -L <行区间>:<文件>` 逐行追史）。若两侧语义都没变过，则「今天红 ⇒ 当初也红 ⇒ 从未绿过」，按定义排除回归。证据落 `line-history.txt` / `line-history-detail.txt`。
- 该升级立即抓到**两处卡文未覆盖的多 commit 情形**：
  - #1/#2 断言行另有 `836d0986`（2026-03-31）——实测为 **black 纯换行**，语义一字未变 ⇒ 仍排除回归。
  - #3 生产另有 `14f2d5a5` / `836d0986`——实测**均为格式化折行**，`EDGE_CREATED` 自引入起就在发。
  - ⚠️ **#3 测试侧另有 `14f0412d`（2026-02-07）是实质变更**，见 #3 行。

**更正（本卡实测推翻卡文推定）**：#3 **不是**「诞生即矛盾」。`14f0412d` 把 `await asyncio.sleep(0.1)` 换成 `await wait_for_call(...)`。把等待写法还原成 `14f0412d` 之前的形态、**生产保持当前 HEAD 不动**（单变量分离），该测试 **5/5 稳定 PASSED**（`canvas-pre14f0412d-*.txt`）。

> ⚠️ **归因边界收窄（Codex r1 MEDIUM-2 打回，已改）**：上述实验**只**证明「在当前 HEAD 的生产代码上，旧等待写法可通过」，即**等待写法是致红的充分原因**；它**不能**推出「历史上某个时点该测试实际为绿」——那需要在历史 commit 的完整环境里跑，本卡未做。Codex 另查出 `c01bd39c`（2026-02-08，**晚于** `14f0412d` 一天）把 `create_task(asyncio.wait_for(self._write_memory_event(...), timeout=0.5))` 改成 `create_task(self._safe_write_memory_event(...))`，同样改动了后台 task 的结构与时序。⇒ **致红点候选是 `14f0412d` 与 `c01bd39c` 两者（或其交互），本卡未逐一分离**。裁定仍归「测试写错」，理由不依赖历史归因：生产当前行为已被 `call_args_list` 证明正确（确实发出 `edge_created` 且 id 匹配），因此当前唯一正确的修法就是修等待写法。

---

## 一 裁定表

| # | nodeid | 开工失败身份原文 | 测试断言 file:line | 生产判定行 file:line | 引入 commit（生产 / 测试） | 裁定 | 依据（含运行期或 git 证据） | 处置 |
|---|---|---|---|---|---|---|---|---|
| 1 | `test_calibration_tracker.py::TestCalibrationRating::test_over_confident_boundary` | `AssertionError: assert <...over_confident> == <...well_calibrated>` | `test_calibration_tracker.py:266` `assert compute_calibration_rating(0.15, 20) == CalibrationRating.WELL_CALIBRATED` | `calibration_tracker.py:189` `if abs(signed_bias) < CALIBRATION_BIAS_THRESHOLD: return WELL_CALIBRATED` | 生产 `43d291d8` 2026-03-16 / 测试 `43d291d8` 2026-03-16（+ `836d0986` 纯 black 换行） | **测试写错** | ① **诞生 commit 上的直接验算**（Codex r1 MEDIUM-4 要求补，`codex-r1-followup-git.txt`）：`git show 43d291d8:...calibration_tracker.py` 里 `_load_calibration_thresholds` **命中数 = 0**（配置覆盖链当时根本不存在）、`:37 CALIBRATION_BIAS_THRESHOLD = 0.15`、`:130` 判定用 `<`、docstring 写 `|signed_bias| < 0.15 → WELL / > 0.15 → OVER` ⇒ 诞生那一刻阈值恒 0.15、`0.15` 必落 OVER ⇒ **诞生即红，直接证明**。② 常量行 `git log -L 40,40` 仅 `43d291d8`，从未变过；历史 `mastery_config.json`（`9d3326ee` 曾入库、后删）内**无 `calibration_thresholds` 键**（只有 mastery_thresholds / bkt_defaults / topic_exam_weights）⇒ 排除「阈值历史上曾是 0.155」这一反例。③ 断言与**自身 docstring** 互斥。④ 同文件 `test_well_calibrated_boundary:256-262`（0.14 / -0.14 / 0.0 → WELL）当前**绿**，实现的 `<` 语义已被绿用例锁定 | 改测试：`0.15 → OVER_CONFIDENT`；阈值改从模块导入 `CALIBRATION_BIAS_THRESHOLD` 参与计算，**并单独断言** `CALIBRATION_BIAS_THRESHOLD == 0.15`（防自证）；补内侧正控 `threshold - 0.001 → WELL` |
| 2 | `...::test_under_confident_boundary` | `AssertionError: assert <...under_confident> == <...well_calibrated>` | `test_calibration_tracker.py:272-274` `(-0.15, 20) == WELL_CALIBRATED` | 同 #1（`:193-194` else 分支 → UNDER_CONFIDENT） | 同 #1 | **测试写错** | 同 #1，对称。docstring 写 `<= -0.15 → UNDER_CONFIDENT`，断言却要 -0.15 == WELL | 同 #1 镜像 |
| 3 | `test_canvas_memory_trigger.py::TestAddEdgeMemoryTrigger::test_add_edge_triggers_memory_event` | `AssertionError: assert 'node_created' == 'edge_created'` | `test_canvas_memory_trigger.py:268` `assert call_args.kwargs["event_type"] == "edge_created"` | `canvas_service.py:895-901` `await self._trigger_memory_event(event_type=CanvasEventType.EDGE_CREATED, ...)` | 生产 `abf1d585` 2026-02-04（+ `14f2d5a5`/`836d0986` **仅格式化**） / 测试 `abf1d585`（+ `14f0412d` 2026-02-07 **实质：sleep → wait_for_call**） | **测试写错（async 竞态；错在 `14f0412d`，非诞生时）** | ① **运行期取证**（`canvas-callargs-*.txt`）：`call_args_list` = `[node_created(node2), edge_created(edge_id='23b01549')]`，`total_calls=2` ⇒ **生产确实发出 edge_created 且 edge_id 匹配**，排除「生产没发」。② **运行期反证**（`canvas-pre14f0412d-*.txt`）：仅把等待写法还原为 `14f0412d` 之前的 `asyncio.sleep(0.1)`、生产保持当前 HEAD，**5/5 PASSED** ⇒ 曾经绿过，致红点是 `wait_for_call`（默认 `expected_count=1`）一有调用即返回，而 `:244 reset_mock()` 早于 `add_node` 的后台 task，迟到的 node_created 成了「最后一次调用」 | 改测试：`:244` reset **之前**先 `await wait_for_call(...)` 等 node_created 落地；断言改为在 `call_args_list` 中**存在且仅一次** `event_type == "edge_created"` 且其 `edge_id == result["id"]`（强度高于原「看最后一次」写法） |
| 4 | `test_difficulty_matcher.py::TestSlidingWindowStats::test_empty_window_stats` | `assert False is True` — `DifficultyMatchStats(total_in_window=0, match_rate=0.0, is_healthy=False)` | `test_difficulty_matcher.py:113` `assert stats.is_healthy is True  # No data -> no alert` | `difficulty_matcher.py:382` `is_healthy=rate >= MATCH_THRESHOLD` | 生产 `e90dbf93` 2026-03-16 / 测试 `e90dbf93` 2026-03-16 | **测试写错 / 契约未定 ⇒ 按现行契约改测试** | ① git：`git log -L` 两侧**各仅 1 个 commit**（双侧从未变过）⇒ 诞生即红。② **消费方证据**（`empty-window-consumers.txt`，(d) 要求）：唯一告警面 `health_monitor.py:435-442` 显式 `if stats.total_in_window == 0: return status="warning", value="no data"` —— **根本不读 `is_healthy`** ⇒ 「空窗告警造成误报」在告警面上不成立；内部消费方 `difficulty_matcher.py:314-315` 位于 `_window.append(matched)` 之后 ⇒ 空窗**不可达**。③ 契约证据：`qa_models.py:63` 字段 description = `"True if match_rate >= 0.7"`，与实现一致；改生产会让字段与自身 description 矛盾。④ 同文件绿用例 `:127`（0.7→True）/ `:138`（0.6→False）已锁定 `rate >= threshold` 语义 | 改测试断言为 `is_healthy is False` + docstring 写明现行契约与消费方分流；产品语义（空窗该不该告警）登记 `CARD-DIFFMATCH-EMPTY-WINDOW`。**未改生产** |
| 5 | `test_event_bus.py::TestTier2Important::test_tier2_retry_then_success` | `assert 0 >= 2`（`call_count`） | `test_event_bus.py:159` `assert call_count >= 2` | `event_bus.py:299-300` `if attempt < TIER2_MAX_RETRIES: await asyncio.sleep(delay)` | 生产 `43d291d8` / 测试 `43d291d8`（两侧 `git log -L` 各仅 1 commit） | **测试写错（patch 面过宽）** | ① git：两侧各仅 1 commit ⇒ 诞生即红。② **运行期铁证**（`identity-open-*.txt`）：断言是 `assert 0 >= 2`（handler 零调用），但同一次运行的日志里有 `EventBus[T2]: flaky_handler FAILED (attempt=1/3 ... retry in 2.0s)` —— 该日志是**断言失败后**事件循环清理 pending task 时才产生的 ⇒ 断言时 wrapper 一次都没跑。③ 机理：`app.services.event_bus.asyncio` **就是全局 asyncio 模块对象**，patch 它的 `sleep` 连带把测试自己 `:158` 的让步（以及 conftest `wait_for_*` 内部的 `asyncio.sleep(interval)`）一并变成 no-op ⇒ 事件循环从不让出。④ 同类绿对照：`:136 test_tier2_success`（同 Tier 2，**未** patch sleep）当前绿 | 改测试：不再 patch `asyncio.sleep`；改用 `monkeypatch.setattr("app.services.event_bus.TIER2_BASE_DELAY_S", 0.0)` 缩短**测试期**退避（生产常量 `:54 = 2.0` 一字未动），等待改用 conftest 的 `wait_condition` fixture；`assert call_count >= 2` **原样保留** |
| 6 | `...::test_tier2_all_retries_exhausted_writes_outbox` | `assert 0 >= 1`（`_stats["outbox_written"]`） | `test_event_bus.py:172` `assert bus._stats["outbox_written"] >= 1` | `event_bus.py:302-304` `self._stats["handled_failed"] += 1; self._write_outbox(event, ..., "retries_exhausted")` | 同 #5 | **测试写错（patch 面过宽）** | 同 #5（同一机理、同一份日志证据：`always_fail FAILED (attempt=1/3)` 出现在断言之后）。**另有负控**见下节 | 同 #5 写法；`assert ... >= 1` **原样保留** |
| 7 | `test_mastery_fusion.py::TestPearsonCorrelation::test_no_correlation` | `assert 1.0 < 0.5` where `1.0 = abs(-1.0)` | `test_mastery_fusion.py:316-317` `a = [1,0,1,0,1]; b = [0,1,0,1,0]` + `:320 assert abs(r) < 0.5` | `mastery_fusion.py:157-168`（教科书 Pearson 公式，无缺陷） | 生产 `43d291d8` / 测试 `43d291d8`（两侧各仅 1 commit） | **测试写错（数据非正交）** | ① git：两侧各仅 1 commit ⇒ 诞生即红。② 数学：`b = 1 - a` 是**完全负相关**，r = −1.0 是**数学正确值**，与 docstring `"Orthogonal signals → r near 0"` 不符 ⇒ 错在数据不在实现。③ 非实现错的独立证据：同文件 `:307-312 test_perfect_negative_correlation`（`a=[.1..,.5]` / `b=[.5..,.1]` → `r == approx(-1.0)`）当前**绿** ⇒ 实现对「完全负相关 = −1.0」已有正确覆盖 | 改测试数据为真正正交：`a=[1,0,1,0]` / `b=[1,1,0,0]`（mean 均 0.5，cov = .25−.25−.25+.25 = 0 ⇒ r = 0.0，算式写进 docstring）；`assert abs(r) < 0.5` **判据强度原样保留**；公式**未动** |
| 8 | `test_multimodal_path_security.py::TestValidateSafePath::test_path_traversal_windows_style` | `Failed: DID NOT RAISE <class MultimodalServiceError>` | `test_multimodal_path_security.py:63-65`（**一字未改**） | `multimodal_service.py:507-508`（改前）`resolved_path = file_path.resolve()` / `if not resolved_path.is_relative_to(self.storage_base_path.resolve()):` | 生产 `e626bef6` 2026-02-09 / 测试 `d12856dd` 2026-02-09（两侧各仅 1 commit） | **契约演进**（处置性质 = 防御深度加强，选 B 改生产判定行） | 见下节单列。归类理由：测试断言的是一个**比实现所满足的更强的契约**（「Windows 风格穿越应被拒绝」不限平台），实现只满足了 POSIX 单一读法下的弱契约；本卡令实现向该已声明契约靠拢 ⇒ 属契约演进，不是「测试写错」（测试意图正确）、也不是「回归」（从未绿过） | 只改判定行使实现**更严**；断言、`match=` 串、返回值、warning/raise 均未动 |

---

## 二 #8 安全面单列（(g) 要求）

### 定性（运行期实测，`posix-path-semantics.txt`）

| 输入 | `resolve()` 是否在 base 内 | `\` 归一为 `/` 后 resolve 是否在 base 内 |
|---|---|---|
| `..\..\windows\system32\config`（本用例） | **True**（不越界） | **False**（越界） |
| `../../etc/passwd`（同文件绿用例） | False | False |
| `x.a\b`（POSIX 合法含反斜杠文件名） | True | **True**（不会被误拒） |
| `x.png\..\..\..\evil` | True | False |
| `20260209_abc123.png`（正常） | True | True |

⇒ POSIX 上反斜杠是**普通文件名字符**，整串是**单个路径分量**，`resolve()` 后仍在 storage 内 ⇒ **「实现漏判越界」不成立**，`DID NOT RAISE` 是平台语义差异。同文件 unix `../..`、deep-nested、mixed 三条穿越用例当前**绿**，是这一层判定正确的对照。

### 为什么仍选 B（改生产）而不是 A（skipif）

1. **A 的代价**：`skipif(os.name != "nt")` 会让该断言在 macOS/Linux（本项目唯一实跑平台）**永久零覆盖**。而 `_validate_safe_path` 的 docstring 契约是「Validate that file_path is within storage_base_path (path traversal defense)」，没有限定平台。
2. **它是第二道门**：第一道门 `_detect_media_type:353-364` 有一个真实缺口——`ext` 不在白名单时，只要 `content_type` 命中 `SUPPORTED_MIME_TYPES` 就放行，而 `_generate_unique_filename:489-492` 仍把**未经白名单校验的 ext** 拼进文件名。用「第一道门当前挡住了」论证第二道门不必严格，等于取消防御深度的意义。
3. **只扩大拒绝面**：新判定是 `A or B` 的**拒绝**条件（原来只有 A），放行面严格变小，不可能引入安全回退。断言一字未改，测试变绿是因为**实现变严**。

### 收益边界（如实，不夸大）

实测 `Path(filename).suffix` 恒为「`.` + 不含点的串」（`posix-path-semantics.txt` 末节：`x.png\..\..\evil` → `.\evil`），因此**无法经 ext 注入 `..`**；两个生产调用方 `:565` / `:709` 的文件名均由服务端 `_generate_unique_filename` 生成。⇒ **在当前两个调用方上，本修复堵的是一条不可达路径，收益是前瞻性的**，不是修一个当前可利用的漏洞。这一点不得表述为「修复了高危漏洞」。

### 改法与副作用逐条核对

```python
resolved_path = file_path.resolve()                                              # :507
storage_root = self.storage_base_path.resolve()                                  # :508
normalized_root = Path(str(self.storage_base_path).replace("\\", "/")).resolve()  # :517
backslash_normalized = Path(str(file_path).replace("\\", "/")).resolve()          # :518
if not resolved_path.is_relative_to(storage_root) or not backslash_normalized.is_relative_to(normalized_root):  # :519
    <warning / raise 原样, :520-529>
return resolved_path          # :530 ← 返回值不变
```

- 返回值仍是 `file_path.resolve()` ⇒ 两个调用方（`:576` / `:720`）拿到的路径与改前**逐字节相同**（对所有未被新条件拒绝的输入）⇒ 写盘位置不变。
- 未新增任何类型注解（新增的三个名字都是赋值，非注解）。
- 未改常量、未改 `warning` / `raise` 文案与 error_code。

> ⚠️ **`normalized_root` 是 Codex r1 HIGH 打回后补的（初版缺失 = 真缺陷）**：初版把**归一化后的候选**与**未归一化的 `storage_root`** 相比，于是当 storage base 自身合法含反斜杠时，**每一次普通上传都会被拒**（旧判定接受、初版拒绝）。这不是理论风险——两个生产调用方都会在写盘前撞上。本卡原先只把它写进「本卡未证明什么」而没有修，属**明确预见却未处置**。修法是让比较的两侧都归一化。逐场景实测见 `codex-r1-HIGH1-repro.txt`：

| 场景 | 旧实现 accept | 初版 accept | 修后 accept |
|---|---|---|---|
| base 含反斜杠 + 正常服务端文件名 | True | **False（误拒）** | **True** ✅ |
| 正常 base + 正常文件名 | True | True | True |
| 正常 base + 本卡用例（win 穿越） | True | False | **False** ✅ |
| 正常 base + unix 穿越 | False | False | False |
| base 含反斜杠 + win 穿越 | True | False | **False** ✅ |
| 正常 base + 合法含反斜杠文件名 `x.a\b` | True | True | True |

⇒ 误拒消除，且**拒绝面一格未放宽**。

### 先红后绿两份存档

| 阶段 | 存档 | 结果 |
|---|---|---|
| 改前 | `sec-before-RED-*.txt` | `1 failed` · `Failed: DID NOT RAISE` · `rc=1` |
| 改后 | `sec-after-GREEN-*.txt` | `1 passed` · `rc=0` |
| 合法路径不被误拒（同文件全量） | `sec-samefile-*.txt` | `16 passed` · 0 failed |
| 消费面窄口径 2 文件 | `sec-consumers-*.txt` | `38 passed` · 0 failed · `rc=0` |

---

## 三 #5/#6 负控（(e) 要求，`negctl-eventbus-*.txt`）

| 项 | 结果 |
|---|---|
| 变异 | `event_bus.py:302-304` 的 `self._write_outbox(event, handler.__name__, "retries_exhausted")` → `pass  # [NEGATIVE-CONTROL]`（**只改 retries_exhausted 那一处**，`:264` circuit_open 分支未动） |
| 指定断言那条（#6） | **FAILED** · 失败正文 `TimeoutError: outbox written after retries exhausted not met within 2.0s` —— 逐字指向 `outbox_written >= 1` 这条判据，非 import/collect 错 |
| **负控特异性**（本卡自加） | 同轮 #5 `test_tier2_retry_then_success` 与同类 `test_tier2_success` **仍 2 passed** ⇒ 变异精准打在指定判据上，不是把整个文件搞坏 |
| 还原 | `shasum -a 256` 前后均 `7072eead8977ec8f0f4733135cfb528c7a51e84eabce2cbd6f0bceee123a4062` ⇒ 逐字节还原；`git diff --stat -- backend/app/services/event_bus.py` 为空 |

失败形态如实说明：判据以 `wait_condition` 的 `TimeoutError` 形式抛出（其 `description` 逐字命名该判据），而非 `AssertionError`。语义等价于「等到超时也没等到 `outbox_written >= 1`」，且早于断言捕获；不是 import/collect 错。

---

## 四 本卡对卡文事实的更正 / 补充

1. **HEAD 不等于 U11-B 末 commit**：开工 HEAD = `f043f5d4`（U11-B 末 commit `b17b710d` 之后多一个 docs commit）。实测 `git diff --stat b17b710d f043f5d4 -- . ':(exclude)_bmad-output'` **为空** ⇒ 代码面等价。本卡地盘门基线取 `b17b710d`（更保守，能覆盖全部代码改动）。
2. **#3 不是「诞生即矛盾」**（见 §〇），卡文 §〇 第 3 行未覆盖 `14f0412d` 的等待原语替换。
3. **`multimodal_service` 子集的模块名口径与窄口径实测重合**：`grep -rln 'multimodal_service' backend/tests/unit` 与 `grep -rln 'upload_file\|_validate_safe_path' ...` **同为 2 文件**，且基线里只有本卡 #8 一条红 ⇒ **0 failed 可达**，(j) 与 (g)-B② 无口径冲突（卡文 §〇 担心的 8 文件 / 5 条外来红是宽口径 `grep 'multimodal'` 的情形，本卡未采用）。
4. **`comm` 口径**：卡文 §二.0 的 `.bare` 副本方案实测正确——带前缀基线直接 `comm` 会吐出全部 8 行。本卡全程用 `.bare` 副本做 `comm`、带前缀两侧做 `diff`。
5. **`_validate_safe_path` 行号位移（终态，Codex r1 LOW 指出前一版数字已过期，已复核）**：判定行 `:507-508` → **`:507-519`**；返回行 `:519` → **`:530`**；两个生产调用方 `:565` / `:709` → **`:576` / `:720`**（`grep -n` 实测）。生产 diff 实数以 `git diff --numstat b17b710d HEAD -- backend/app` 为准，见 §五。

---

## 五 Codex round-1 整改记录

> 存档 `codex-review-CARD-RED-NEW.md`（绑定 `9a5bc79d`）· 结论 **BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 1**
> 车道处置：**全部接受，无驳回**。其中 HIGH 与 LOW 改代码/数字，4 条 MEDIUM 中 3 条补证据或收窄表述、1 条加强判据。

| 级别 | Codex 发现 | 车道处置 | 证据 |
|---|---|---|---|
| **HIGH** | #8 归一化后的候选与**未归一化**的 `storage_root` 相比 ⇒ storage base 合法含反斜杠时**每次普通上传都被误拒**，两个调用方都会撞上；「当前调用方不可达」的限定没覆盖这条新增副作用 | **接受，改生产代码**：新增 `normalized_root`，让比较两侧都归一化。逐场景实测确认误拒消除、拒绝面一格未放宽 | `codex-r1-HIGH1-repro.txt`；`multimodal_service.py:517,519` |
| **MEDIUM-1** | #1/#2 的「从未绿过」只追了比较分支与断言，**遗漏配置覆盖链**；若历史阈值曾为 `0.155`，旧断言成立 | **接受，补更强证据**（结论未变）：在诞生 commit `43d291d8` 上直接验算——`_load_calibration_thresholds` **命中数 = 0**（覆盖链当时不存在）、常量恒 `0.15`、判定用 `<`；且历史 `mastery_config.json`（`9d3326ee`）内**无 `calibration_thresholds` 键** ⇒ 该反例被排除，「诞生即红」由推理升级为直接验算 | `codex-r1-followup-git.txt` |
| **MEDIUM-2** | #3 的单变量实验缺可核验绑定；且 `c01bd39c`（2026-02-08）**晚于** `14f0412d` 也改过后台 task 包装，仅追事件调用点不足以锁定致红提交 | **接受，收窄表述**（裁定未变）：实验只证明「等待写法是致红的**充分**原因」，不证明「历史某时点实际为绿」；致红点候选为 `14f0412d` 与 `c01bd39c` 两者，**本卡未逐一分离**，已如实写入 §〇 与「本卡未证明什么」 | `codex-r1-followup-git.txt`（`c01bd39c` 的 diff 已落盘） |
| **MEDIUM-3** | format 多重集丢弃了文件、位置与增删方向，挡不住「消一处旧债 + 引一处同文本新债」的等长替换；也未绑定基线 SHA | **接受，加强判据**：口径改为 `<文件名>\|<方向±>\|<内容>` 的多重集，显式绑定基线 `b17b710d`，两侧统一 `--config backend/ruff.toml`。加强后新增仍为**空** | `format-multiset-compare-v2.txt` |
| **MEDIUM-4** | #8 用「防御深度不足」作第四类别，未回答三选一 | **接受，归入三选一**：#8 = **契约演进**（测试断言的契约强于实现所满足的；本卡令实现向该已声明契约靠拢），「防御深度加强」降为处置性质描述。计数更正为 **测试写错 7 / 契约演进 1 / 回归 0** | 本文件计数行与 #8 裁定行 |
| **LOW** | 行号与改动量已过期：返回行实际 `:526`、调用方 `:572`/`:716`、diff 是 +8/−1 | **接受，复核后更正**（HIGH 修复又使行号位移，故取终态实测值）：返回行 **`:530`**、调用方 **`:576`**/**`:720`**、判定行 **`:507-519`**；`backend/app` diff 实数 **+12/−1**（`git diff --numstat b17b710d HEAD -- backend/app`） | `grep -n` 与 `numstat` 实测 |

### Codex 明确核验通过的项（原文摘要）

- #8：接受条件确由 `A` 收紧为 `A∧B`；安全断言、`match=`、返回值、warning/raise 均未改。
- #5/#6：`>= 2` / `>= 1` 原样保留；生产常量仍为 `2.0`，monkeypatch 改的是测试期模块状态；负控针对 #6 同一 outbox 判据，`TimeoutError` 形态**不削弱**它。
- #3：取证存档确有匹配 ID 的 `edge_created`；新断言能检测漏发、重复发和错误 ID；`== 1` 没有放宽判据，且**现有材料不足以认定它新增脆性**（本卡另补 10 次连跑，10/10 PASSED，`flaky-check-*.txt`）。
- #4：消费方证据支持「空窗不读取 `is_healthy`」，内部读取确在 append 之后。⚠️ Codex 提醒：健康检查明确返回 `status="warning"`，**不能扩述为「空窗不告警」**——本文件与验收单已按此措辞校准。
- #1/#2/#7：阈值既参与计算又被独立断言；`±0.149` 稳定位于 WELL 侧；新 Pearson 数据独立算得 **r = 0**，判据与公式均未改。
- 范围：仅一个生产文件 + 五个测试文件；**未发现**跨车道修改、类型注解变更、删用例、skip/xfail；两份目录 diff 的 `>` 均为零，减少的失败恰好是本卡八条。

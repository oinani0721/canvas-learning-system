# CARD-RED-NEW — tests/unit 既有红「新」类 8 条三选一裁定表

> 批次: BATCH-2026-09-07-第十三批 · 车道 U11-C · 卡 CARD-RED-NEW
> 树: `card-u11-red-c`（分支 `card/u11-red-c`）· 开工 HEAD `f043f5d4`
> 统一基线: `evidence-b13/unit-red-baseline-da690bf8.txt`（202 nodeid @ `da690bf8`）
> 裁定计数: **测试写错 7 / 契约演进 1 / 回归 0**（#8 = 契约演进，处置性质为「防御深度加强」；Codex r1 MEDIUM-4 指出「防御深度不足」是第四类别、未回答三选一，已归类）

---

## 〇 裁定方法学（本卡对卡文推理的一处升级 + 一处更正）

**卡文给的判据**是「生产与测试同 commit 诞生 ⇒ 不可能是回归」。开工核验发现这条**不充分**：

- 同 commit 只说明两者同批引入。若此后某个 commit 改了判定行或断言行，仍可能是回归。
- 因此本卡把判据升级为：**判定行与断言行的语义自引入后从未变过**（`git log -L <行区间>:<文件>` 逐行追史）。若两侧语义都没变过，则「今天红 ⇒ 引入时也红」，即**排除「后来某次改动把它弄红了」这个解释**。证据落 `line-history.txt` / `line-history-detail.txt`。
  - ⚠️ **措辞边界（Codex r3 LOW 打回后收窄）**：这**不等于「从未绿过」**——那还需要排除中间 commit 上的环境/配置差异，本卡只对 #1/#2 在**诞生 commit** 上做了完整排除（见 #1 依据 ①），没有逐 commit 重放。裁定「测试写错」不依赖「从未绿过」这一更强主张。
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
| 1 | `test_calibration_tracker.py::TestCalibrationRating::test_over_confident_boundary` | `AssertionError: assert <...over_confident> == <...well_calibrated>` | `test_calibration_tracker.py:266` `assert compute_calibration_rating(0.15, 20) == CalibrationRating.WELL_CALIBRATED` | `calibration_tracker.py:189` `if abs(signed_bias) < CALIBRATION_BIAS_THRESHOLD: return WELL_CALIBRATED` | 生产 `43d291d8` 2026-03-16 / 测试 `43d291d8` 2026-03-16（+ `836d0986` 纯 black 换行） | **测试写错** | ① **诞生 commit 上的直接验算**（`codex-r1-followup-git.txt` + `codex-r2-M1-threshold-writepoints.txt`）：在 `43d291d8` 那个版本上——该常量全模块只有 **2 处**出现（`:37` 定义 = `0.15`、`:130` 使用）、**无** `_load_calibration_thresholds`（命中 0）、**无** `global` 改写、**无**环境变量读取、**无**模块级副作用调用、**全树除定义模块外 0 处引用**、当时的测试文件**不 monkeypatch 该常量**；判定用 `<`，docstring 写 `|signed_bias| < 0.15 → WELL / > 0.15 → OVER` ⇒ **该 commit 运行期阈值恒为 0.15、`0.15` 必落 OVER ⇒ 诞生即红**。② 常量行 `git log -L 40,40` 仅 `43d291d8`；历史 `mastery_config.json`（`9d3326ee` 曾入库、后删）内**无 `calibration_thresholds` 键**。⛔ **本条只证明「诞生那一刻即红」**，不主张「从诞生到今天的每个中间 commit 上阈值都恒定」（那需逐 commit 重放，本卡未做）——但裁定只需要前者。③ 断言与**自身 docstring** 互斥。④ 同文件 `test_well_calibrated_boundary:256-262`（0.14 / -0.14 / 0.0 → WELL）当前**绿**，实现的 `<` 语义已被绿用例锁定 | 改测试：`0.15 → OVER_CONFIDENT`；阈值改从模块导入 `CALIBRATION_BIAS_THRESHOLD` 参与计算，**并单独断言** `CALIBRATION_BIAS_THRESHOLD == 0.15`（防自证）；补内侧正控 `threshold - 0.001 → WELL` |
| 2 | `...::test_under_confident_boundary` | `AssertionError: assert <...under_confident> == <...well_calibrated>` | `test_calibration_tracker.py:272-274` `(-0.15, 20) == WELL_CALIBRATED` | 同 #1（`:193-194` else 分支 → UNDER_CONFIDENT） | 同 #1 | **测试写错** | 同 #1，对称。docstring 写 `<= -0.15 → UNDER_CONFIDENT`，断言却要 -0.15 == WELL | 同 #1 镜像 |
| 3 | `test_canvas_memory_trigger.py::TestAddEdgeMemoryTrigger::test_add_edge_triggers_memory_event` | `AssertionError: assert 'node_created' == 'edge_created'` | `test_canvas_memory_trigger.py:268` `assert call_args.kwargs["event_type"] == "edge_created"` | `canvas_service.py:895-901` `await self._trigger_memory_event(event_type=CanvasEventType.EDGE_CREATED, ...)` | 生产 `abf1d585` 2026-02-04（+ `14f2d5a5`/`836d0986` **仅格式化**） / 测试 `abf1d585`（+ `14f0412d` 2026-02-07 **实质：sleep → wait_for_call**） | **测试写错（async 竞态：等待原语选错）** | ① **运行期取证**（`canvas-callargs-*.txt`）：`call_args_list` = `[node_created(node2), edge_created(edge_id='23b01549')]`，`total_calls=2` ⇒ **生产确实发出 edge_created 且 edge_id 匹配**，排除「生产没发」。② **运行期反证**（`canvas-pre14f0412d-*.txt`）：仅把等待写法换成 `14f0412d` 之前的 `asyncio.sleep(0.1)`、生产保持当前 HEAD，**5/5 PASSED** ⇒ **等待写法是致红的充分原因**（`wait_for_call` 默认 `expected_count=1`，一有调用即返回，而 `:244 reset_mock()` 早于 `add_node` 的后台 task，迟到的 node_created 成了「最后一次调用」）。⛔ **本条不主张「该测试历史上曾经为绿」**——那需要在历史 commit 的完整环境里重放，本卡未做；且 `c01bd39c`（2026-02-08，晚于 `14f0412d`）也改过后台 task 包装，致红点候选为两者或其交互，未逐一分离。裁定不依赖历史归因 | 改测试：`:244` reset **之前**先 `await wait_for_call(...)` 等 node_created 落地；断言改为在 `call_args_list` 中**存在且仅一次** `event_type == "edge_created"` 且其 `edge_id == result["id"]`（强度高于原「看最后一次」写法） |
| 4 | `test_difficulty_matcher.py::TestSlidingWindowStats::test_empty_window_stats` | `assert False is True` — `DifficultyMatchStats(total_in_window=0, match_rate=0.0, is_healthy=False)` | `test_difficulty_matcher.py:113` `assert stats.is_healthy is True  # No data -> no alert` | `difficulty_matcher.py:382` `is_healthy=rate >= MATCH_THRESHOLD` | 生产 `e90dbf93` 2026-03-16 / 测试 `e90dbf93` 2026-03-16 | **测试写错 / 契约未定 ⇒ 按现行契约改测试** | ① git：`git log -L` 两侧**各仅 1 个 commit**（双侧从未变过）⇒ 诞生即红。② **消费方证据**（`empty-window-consumers.txt`，(d) 要求）：唯一告警面 `health_monitor.py:435-442` 在 `total_in_window == 0` 时**独立分流**，返回 `status="warning", value="no data", message="No difficulty evaluation data yet"`，**根本不读 `is_healthy`**。⚠️ 措辞校准（Codex r1 指出）：**这不等于「空窗不告警」——它确实报 warning**；成立的结论只是「**改不改 `is_healthy` 都不会改变空窗时的告警行为**」，因此把 `is_healthy` 改成空窗返回 True 并不能消除任何现有告警。内部消费方 `difficulty_matcher.py:314-315` 位于 `_window.append(matched)` 之后 ⇒ 空窗**不可达**。③ 契约证据：`qa_models.py:63` 字段 description = `"True if match_rate >= 0.7"`，与实现一致；改生产会让字段与自身 description 矛盾。④ 同文件绿用例 `:127`（0.7→True）/ `:138`（0.6→False）已锁定 `rate >= threshold` 语义 | 改测试断言为 `is_healthy is False` + docstring 写明现行契约与消费方分流；产品语义（空窗该不该告警）登记 `CARD-DIFFMATCH-EMPTY-WINDOW`。**未改生产** |
| 5 | `test_event_bus.py::TestTier2Important::test_tier2_retry_then_success` | `assert 0 >= 2`（`call_count`） | `test_event_bus.py:159` `assert call_count >= 2` | `event_bus.py:299-300` `if attempt < TIER2_MAX_RETRIES: await asyncio.sleep(delay)` | 生产 `43d291d8` / 测试 `43d291d8`（两侧 `git log -L` 各仅 1 commit） | **测试写错（patch 面过宽）** | ① git：两侧各仅 1 commit ⇒ 诞生即红。② **运行期铁证**（`identity-open-*.txt`）：断言是 `assert 0 >= 2`（handler 零调用），但同一次运行的日志里有 `EventBus[T2]: flaky_handler FAILED (attempt=1/3 ... retry in 2.0s)` —— 该日志是**断言失败后**事件循环清理 pending task 时才产生的 ⇒ 断言时 wrapper 一次都没跑。③ 机理：`app.services.event_bus.asyncio` **就是全局 asyncio 模块对象**，patch 它的 `sleep` 连带把测试自己 `:158` 的让步（以及 conftest `wait_for_*` 内部的 `asyncio.sleep(interval)`）一并变成 no-op ⇒ 事件循环从不让出。④ 同类绿对照：`:136 test_tier2_success`（同 Tier 2，**未** patch sleep）当前绿 | 改测试：不再 patch `asyncio.sleep`；改用 `monkeypatch.setattr("app.services.event_bus.TIER2_BASE_DELAY_S", 0.0)` 缩短**测试期**退避（生产常量 `:54 = 2.0` 一字未动），等待改用 conftest 的 `wait_condition` fixture；`assert call_count >= 2` **原样保留** |
| 6 | `...::test_tier2_all_retries_exhausted_writes_outbox` | `assert 0 >= 1`（`_stats["outbox_written"]`） | `test_event_bus.py:172` `assert bus._stats["outbox_written"] >= 1` | `event_bus.py:302-304` `self._stats["handled_failed"] += 1; self._write_outbox(event, ..., "retries_exhausted")` | 同 #5 | **测试写错（patch 面过宽）** | 同 #5（同一机理、同一份日志证据：`always_fail FAILED (attempt=1/3)` 出现在断言之后）。**另有负控**见下节 | 同 #5 写法；`assert ... >= 1` **原样保留** |
| 7 | `test_mastery_fusion.py::TestPearsonCorrelation::test_no_correlation` | `assert 1.0 < 0.5` where `1.0 = abs(-1.0)` | `test_mastery_fusion.py:316-317` `a = [1,0,1,0,1]; b = [0,1,0,1,0]` + `:320 assert abs(r) < 0.5` | `mastery_fusion.py:157-168`（教科书 Pearson 公式，无缺陷） | 生产 `43d291d8` / 测试 `43d291d8`（两侧各仅 1 commit） | **测试写错（数据非正交）** | ① git：两侧各仅 1 commit ⇒ 诞生即红。② 数学：`b = 1 - a` 是**完全负相关**，r = −1.0 是**数学正确值**，与 docstring `"Orthogonal signals → r near 0"` 不符 ⇒ 错在数据不在实现。③ 非实现错的独立证据：同文件 `:307-312 test_perfect_negative_correlation`（`a=[.1..,.5]` / `b=[.5..,.1]` → `r == approx(-1.0)`）当前**绿** ⇒ 实现对「完全负相关 = −1.0」已有正确覆盖 | 改测试数据为真正正交：`a=[1,0,1,0]` / `b=[1,1,0,0]`（mean 均 0.5，cov = .25−.25−.25+.25 = 0 ⇒ r = 0.0，算式写进 docstring）；`assert abs(r) < 0.5` **判据强度原样保留**；公式**未动** |
| 8 | `test_multimodal_path_security.py::TestValidateSafePath::test_path_traversal_windows_style` | `Failed: DID NOT RAISE <class MultimodalServiceError>` | `test_multimodal_path_security.py:63-65`（**一字未改**） | `multimodal_service.py:507-508`（改前）`resolved_path = file_path.resolve()` / `if not resolved_path.is_relative_to(self.storage_base_path.resolve()):` | 生产 `e626bef6` 2026-02-09 / 测试 `d12856dd` 2026-02-09（两侧各仅 1 commit） | **契约演进**（处置性质 = 防御深度加强，选 B 改生产判定行） | 见下节单列。归类理由：测试断言的是一个**比实现所满足的更强的契约**（「Windows 风格穿越应被拒绝」不限平台），实现只满足了 POSIX 单一读法下的弱契约；本卡令实现向该已声明契约靠拢 ⇒ 属契约演进，不是「测试写错」（测试意图正确）、也不是「回归」（两侧各仅 1 commit，本平台上引入时即红）。⚠️ 此处**不用「从未绿过」**：#8 是**平台相关**的，同一份代码在 Windows 上本来就会绿 | 只改判定行使实现**更严**；断言、`match=` 串、返回值、warning/raise 均未动 |

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

实测 `Path(filename).suffix` 恒为「`.` + 不含点的串」（`posix-path-semantics.txt` 末节：`x.png\..\..\evil` → `.\evil`），因此**无法经 ext 注入 `..`**；两个生产调用方（终态 `:586` / `:730`）的文件名均由服务端 `_generate_unique_filename` 生成。⇒ **在当前两个调用方上，本修复堵的是一条不可达路径，收益是前瞻性的**，不是修一个当前可利用的漏洞。这一点不得表述为「修复了高危漏洞」。

### 改法与副作用逐条核对

```python
resolved_path = file_path.resolve()                       # :507
storage_root = self.storage_base_path.resolve()           # :508
below_root = (                                            # :523
    str(resolved_path.relative_to(storage_root)) if resolved_path.is_relative_to(storage_root) else None
)
reinterpreted = (                                         # :526
    (storage_root / below_root.replace("\\", "/")).resolve() if below_root is not None else resolved_path
)
if not resolved_path.is_relative_to(storage_root) or not reinterpreted.is_relative_to(storage_root):  # :529
    <warning / raise 原样, :530-539>
return resolved_path          # :540 ← 返回值不变
```

> ⚠️ **这一处经过两轮打回才收敛，两次都是「合法路径被误拒」**：
> - **round-1 HIGH**：初版把归一化后的候选与**未归一化的 root** 比较 ⇒ storage base 自身含反斜杠时，每次普通上传都被误拒。
> - **round-3 MEDIUM-1**：第二版把 root 也归一化，但**归一化后的 root 是另一条真实路径** —— 若那条路径上有指向别处的符号链接（Codex 的构造：真实存储是 `/T/a\b/image`，而 `/T/a/b/image -> /T/outside`），普通上传又被误拒。
> - **第三版**：root 不参与归一化，只把 storage root **之下**的那段按 `\` 重读一遍——但 `relative_to` 用的是**未 resolve 的字面路径**，于是 base 写成相对还是绝对会走到不同分支（`ValueError` 分支让第二重检查退化）。（round-4 MEDIUM-1）
> - **终版（第四版）**：`relative_to` **两侧都用 resolve 后的路径**，base 的拼写在比较前就已归一，再也不能影响结果；`try/except` 随之消失（第一重已保证 `relative_to` 必然成功）。

- 返回值仍是 `file_path.resolve()` ⇒ 两个调用方（终态 `:586` / `:730`）拿到的路径与改前**逐字节相同**（对所有未被新条件拒绝的输入）⇒ 写盘位置不变。
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

⇒ 误拒消除，且**相对原始实现 `b17b710d`，拒绝面一格未放宽**。

> ⚠️ **基线必须写明（Codex r2 LOW 指出）**：「未放宽」只对 **`b17b710d`（原始实现）** 成立。相对 **round-1 初版**它确实放宽了——那正是修复本身（初版误拒的合法路径重新放行），而且重新放行的不只普通文件名：Codex 给的 `base=Path(r"/storage\..")` 一例里，`normalized_root` 退化为 `/`，接受结果为 `b17=True / r1=False / r2=True`。该输入的**实际返回路径仍在原生 root 内**（`resolved_path.is_relative_to(storage_root)` 这个必要条件从未去掉），所以不是新增的磁盘越界面。
>
> 单调性由枚举实测支撑（`sec-monotonicity-selfcheck.txt`）：5 种 base × 12 种候选 = 60 例，「旧接受→新拒绝」10 例，**「旧拒绝→新接受」0 例**；另在真实文件系统上测了符号链接 base、base 名含反斜杠且 `a/b` 同时存在、符号链接指向含反斜杠目录（`sec-alias-edgecase-selfcheck.txt`）。Codex r2 独立复核后的原话：**「当前接受必然意味着 `b17b710d` 接受，返回的写盘目标也不变。此结论覆盖反斜杠、符号链接和 `..`」**。

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
5. **`_validate_safe_path` 行号位移（终态，经 r1 LOW / r2 / r3 三轮复核）**：判定行 `:507-508` → **`:507-529`**；返回行 `:519` → **`:540`**；两个生产调用方 `:565` / `:709` → **`:586` / `:730`**（`grep -n` 实测）。`backend/app` diff 实数 **+22/−1**。

---

## 五 Codex round-1 整改记录

> 存档 `codex-review-CARD-RED-NEW.md`（绑定 `9a5bc79d`）· 结论 **BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 1**
> 车道处置：**全部接受，无驳回**。其中 HIGH 与 LOW 改代码/数字，4 条 MEDIUM 中 3 条补证据或收窄表述、1 条加强判据。

| 级别 | Codex 发现 | 车道处置 | 证据 |
|---|---|---|---|
| **HIGH** | #8 归一化后的候选与**未归一化**的 `storage_root` 相比 ⇒ storage base 合法含反斜杠时**每次普通上传都被误拒**，两个调用方都会撞上；「当前调用方不可达」的限定没覆盖这条新增副作用 | **接受，改生产代码**：新增 `normalized_root`，让比较两侧都归一化。逐场景实测确认误拒消除；拒绝面相对 **`b17b710d`** 一格未放宽（相对 r1 初版则是有意放宽 = 修复本身，见 §二） | `codex-r1-HIGH1-repro.txt`；`multimodal_service.py:517,519` |
| **MEDIUM-1** | #1/#2 的「从未绿过」只追了比较分支与断言，**遗漏配置覆盖链**；若历史阈值曾为 `0.155`，旧断言成立 | **接受，补更强证据**（结论未变）：在诞生 commit `43d291d8` 上直接验算——`_load_calibration_thresholds` **命中数 = 0**（覆盖链当时不存在）、常量恒 `0.15`、判定用 `<`；且历史 `mastery_config.json`（`9d3326ee`）内**无 `calibration_thresholds` 键** ⇒ 该反例被排除，「诞生即红」由推理升级为直接验算 | `codex-r1-followup-git.txt` |
| **MEDIUM-2** | #3 的单变量实验缺可核验绑定；且 `c01bd39c`（2026-02-08）**晚于** `14f0412d` 也改过后台 task 包装，仅追事件调用点不足以锁定致红提交 | **接受，收窄表述**（裁定未变）：实验只证明「等待写法是致红的**充分**原因」，不证明「历史某时点实际为绿」；致红点候选为 `14f0412d` 与 `c01bd39c` 两者，**本卡未逐一分离**，已如实写入 §〇 与「本卡未证明什么」 | `codex-r1-followup-git.txt`（`c01bd39c` 的 diff 已落盘） |
| **MEDIUM-3** | format 多重集丢弃了文件、位置与增删方向，挡不住「消一处旧债 + 引一处同文本新债」的等长替换；也未绑定基线 SHA | **接受，加强判据**：口径改为 `<文件名>\|<方向±>\|<内容>` 的多重集，显式绑定基线 `b17b710d`，两侧统一 `--config backend/ruff.toml`。加强后新增仍为**空** | `format-multiset-compare-v2.txt` |
| **MEDIUM-4** | #8 用「防御深度不足」作第四类别，未回答三选一 | **接受，归入三选一**：#8 = **契约演进**（测试断言的契约强于实现所满足的；本卡令实现向该已声明契约靠拢），「防御深度加强」降为处置性质描述。计数更正为 **测试写错 7 / 契约演进 1 / 回归 0** | 本文件计数行与 #8 裁定行 |
| **LOW** | 行号与改动量已过期：返回行实际 `:526`、调用方 `:572`/`:716`、diff 是 +8/−1 | **接受，复核后更正**：返回行 `:530`、调用方 `:576`/`:720`、判定行 `:507-519`、diff `+12/−1`。⚠️ **这些是 round-1 整改当时的值，保留作历史记录**；r3 又改了一次生产代码，**终态**为判定行 `:507-527`、返回行 `:538`、调用方 `:584`/`:728`、diff **+20/−1**（见 §七） | `grep -n` 与 `numstat` 实测 |

### Codex 明确核验通过的项（原文摘要）

- #8：接受条件确由 `A` 收紧为 `A∧B`；安全断言、`match=`、返回值、warning/raise 均未改。
- #5/#6：`>= 2` / `>= 1` 原样保留；生产常量仍为 `2.0`，monkeypatch 改的是测试期模块状态；负控针对 #6 同一 outbox 判据，`TimeoutError` 形态**不削弱**它。
- #3：取证存档确有匹配 ID 的 `edge_created`；新断言能检测漏发、重复发和错误 ID；`== 1` 没有放宽判据，且**现有材料不足以认定它新增脆性**（本卡另补 10 次连跑，10/10 PASSED，`flaky-check-*.txt`）。
- #4：消费方证据支持「空窗不读取 `is_healthy`」，内部读取确在 append 之后。⚠️ Codex 提醒：健康检查明确返回 `status="warning"`，**不能扩述为「空窗不告警」**——本文件与验收单已按此措辞校准。
- #1/#2/#7：阈值既参与计算又被独立断言；`±0.149` 稳定位于 WELL 侧；新 Pearson 数据独立算得 **r = 0**，判据与公式均未改。
- 范围：仅一个生产文件 + 五个测试文件；**未发现**跨车道修改、类型注解变更、删用例、skip/xfail；两份目录 diff 的 `>` 均为零，减少的失败恰好是本卡八条。

---

## 六 Codex round-2 整改记录

> 存档 `codex-review-CARD-RED-NEW-r2.md`（绑定 `9848c2c1`）· 结论 **BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 1**
> **HIGH 已清零。** 3 条 MEDIUM + 1 条 LOW 车道**全部接受、无驳回**。

| 级别 | Codex r2 发现 | 车道处置 | 证据 |
|---|---|---|---|
| **MEDIUM-1** | #1/#2「历史反例已排除」仍超出证据：同名 loader 命中为零 + 默认赋值 `0.15`，不足以证明**运行期**阈值恒定；未排除其他赋值 / 导入副作用 / 测试初始化 / 后续配置 | **接受，补齐排除项 + 收窄主张**：在诞生 commit 上实测——该常量全模块仅 2 处出现、无 `global`、无环境变量、无模块级副作用调用、**全树除定义模块外 0 处引用**、当时测试**不 monkeypatch**。主张同时收窄为「只证明**诞生那一刻**即红」，不再声称覆盖中间 commit | `codex-r2-M1-threshold-writepoints.txt` |
| **MEDIUM-2** | #3 **裁定行仍写着「曾经绿过」「错在 `14f0412d`，非诞生时」**，与 §〇 的收窄说明**直接矛盾** | **接受，改掉矛盾表述**（这是真实疏漏——在 §〇 收窄了，却没从结论行里减掉）：裁定列改为「async 竞态：等待原语选错」，依据列明写「本条不主张该测试历史上曾为绿」并列出 `c01bd39c` 这个未分离的候选 | 本文件 #3 行与 §〇 |
| **MEDIUM-3** | format v2 补了文件名与方向后**仍丢位置**：同文件内「A 处修好 + B 处改坏」可让两侧多重集完全相等 | **接受，补位置维度（v3）**：改用**同一文件同一版本**上的行集合交集——A = 本卡改动行（`git diff -U0` 的 `+`hunk），B = ruff 真正要替换的行（`--diff` 里带 `-` 前缀的行，**不是**整个 hunk 范围）。判据 `A ∩ B = ∅`，六文件**合计 0**。⚠️ **v3 仍非完备**（Codex r3 再次指出）：它漏掉「本卡的纯删除」与「formatter 的纯插入」——例如补齐一处函数间空行、同时删掉另一处，v2 多重集相同且 v3 交集为空，债却已迁移。⇒ 最终表述改为「**两个独立判据（v2 内容+文件+方向多重集、v3 位置交集）均未发现新增**」，**不再声称「证明新增为零」** | `format-multiset-compare-v2.txt` / `format-position-gate-v3.txt` |
| **LOW** | 「拒绝面一格未放宽」没限定比较基线：相对 round-1 并不成立，且重新放行的不只普通文件名（`base=Path(r"/storage\..")` ⇒ `b17=True / r1=False / r2=True`） | **接受，写明基线**：该表述只对 `b17b710d` 成立；相对 r1 的放宽正是修复本身。Codex 同时确认该输入**不是新增磁盘越界面**（原生包含关系作为必要条件从未去掉） | 本文件 §二 |

### v3 判据的一处自纠（如实记录）

位置判据 v3 的**初版实现有假阳性**：把 ruff hunk 的**整个范围**（含上下文行）当作「需 format 的行」，于是在 `test_calibration_tracker.py` 报出 291–293 三行。查证后确认那三行是本卡写的、**本身 format-clean**，只是恰好落在一个针对**存量行**（294–296 的 `-0.16` 断言，本卡未碰）的 hunk 的上下文里。判据改为只统计带 `-` 前缀的实际替换行后，六文件交集**全为 0**。

> 记这一笔是因为：如果不查就按初版结果改代码，会把三行**本来就干净**的代码「修」一遍，并在验收单里写下一个不存在的问题。判据报红时，第一步是验判据、不是改代码。

### Codex r2 明确核验通过的项（原文摘要）

- **路径安全**：`multimodal_service.py:519` 保留原生包含关系作为**必要条件** ⇒ 在同一文件系统状态下，**当前接受必然意味着 `b17b710d` 接受，返回的写盘目标也不变**；此结论**覆盖反斜杠、符号链接和 `..`**。
- **两种 root 确实可能不同**（Codex 实算 `base=r"/var\foo/../tmp"`：原生 root `/private/tmp`、归一化 root `/private/var/tmp`），但两个现有调用方用的都是 `base / rel` 拼法，**不能据此认定上传已回归**。
- **#8 分类**：作为「本次采纳更强跨平台规则」的处置分类，**「契约演进」可以接受**；它不证明历史契约曾发生变化。
- **改动范围与裁判**：增量只改路径比较和注释，**未碰** #3、#5/#6、#7、类型注解、conftest 或其他车道代码；独立计算三份目录 diff，`>` **均为零**，开工后减少的恰好是本卡 **8 条**；判定 / 返回 / 调用行号及 `+12/−1` 均正确（⚠️ 此为 **round-2 当时**核验的值；r3 再次改动后终态为 **+20/−1**，见 §七）。

---

## 七 Codex round-3 整改记录

> 存档 `codex-review-CARD-RED-NEW-r3.md`（绑定 `0266fb083d5526aab456c72f97d6f70c10caaa97`）
> 结论 **BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 1**。⚠️ **该轮的 B/H=0 不能作为「当前 HEAD 已通过最终审查」的依据**（Codex r4 MEDIUM-2 指出）：r3 之后本卡又改了生产判定，`0266fb08` 已不是最终 HEAD。D-15 的达成以**最后一轮**为准。
> 3 条发现车道**全部接受、无驳回**；其中 MEDIUM-1 再次改了生产代码。

| 级别 | Codex r3 发现 | 车道处置 | 证据 |
|---|---|---|---|
| **MEDIUM-1** | 正常上传**仍存在**合法路径误拒：归一化后的 root 是**另一条真实路径**，若那条路径上有指向别处的符号链接（构造：真实存储 `/T/a\b/image`，而 `/T/a/b/image -> /T/outside`），普通上传被拒；实际写盘目标并未越界。Codex 注明此项为静态推导、未创建复现场景 | **接受，改生产（第三版）**：实测复现 Codex 的构造确认成立，随后把修法改为 **root 完全不参与归一化**——只把 storage root **之下**的那段按 `\` 重读。base 怎么拼写都不再影响判定 ⇒ r1 与 r3 两类误拒一并消失 | `sec-r3-M1-fix-verify.txt`（[A] Codex 构造 3/3 符合期望；[B] 单调性 60 例「旧拒→新放」= 0；[C] 合法上传误拒 = 0；[D] 返回值不变） |
| **MEDIUM-2** | format v3 **仍不能证明**新增为零：漏掉「本卡的纯删除」与「formatter 的纯插入」——补齐一处函数间空行、同时删掉另一处，v2 多重集相同且 v3 交集为空，债却已迁移 | **接受，改主张而非改判据**：v2/v3 都保留，但最终表述改为「**两个独立判据均未发现新增**」，**不再声称「证明新增为零」**。判据的不完备性如实写进本表与验收单 | 本表 §六 MEDIUM-3 行 |
| **LOW** | 历史结论的收窄**仍未同步完整**：`test_calibration_tracker.py:272` 的 docstring 仍写 `it was never a regression`；`new-verdicts.md:15`（§〇）仍保留「从未绿过」的推论 | **接受，两处都改**。⚠️ 这是**同一个病第三次出现**（r2 MEDIUM-2 → 本卡自查发现验收单 5 处 → r3 这两处）：收窄写在一处，其余出现处没跟着改。docstring 改为「排除『后来某次改动把它弄红了』这个解释，不是对每个中间 commit 的主张」；§〇 同步加措辞边界 | 本表 §〇 与 `test_calibration_tracker.py` docstring |

### Codex r3 明确核验通过的项（原文摘要）

- **「同一文件系统状态下，新接受条件包含旧条件，返回路径不变，不存在相对 `b17b710d` 的旧拒绝→新接受；这一逻辑结论强于 60 例枚举。」** —— 这是本卡安全性的最强背书：它是**逻辑蕴含**，不依赖枚举面是否完整。
- 本轮代码增量确实只有 docstring；#1/#2 防自证、#3 新断言、#5/#6 判据及负控相关代码、#7 数据与公式**均未被增量破坏**。
- round-2 期间修改三文件的瑕疵**已在存档首部明确声明**。

### 一条贯穿三轮的教训

`_validate_safe_path` 的修法改了**三版**，前两版都在「让判定更严」的同时引入了**合法路径误拒**，而且两次都不是靠我自己的枚举自查发现的——第一次是 Codex r1，第二次是 Codex r3。我的 60 例、48 例枚举都跑过「符号链接 base」，但都没造出「**归一化后的那条路径上**有符号链接」这个结构。

⇒ **枚举自查的盲区不是样本数量，是结构想象力**。终版之所以可靠，不是因为枚举更多，而是因为它**把变量消掉了**——root 不参与归一化，base 的拼写就再也不能影响判定。**能消掉的变量，不要用枚举去覆盖。**

---

## 八 Codex round-4 整改记录

> 存档 `codex-review-CARD-RED-NEW-r4.md`（绑定 `7f16c916492546f6b3227f68ef566727afed1c6a`）
> 结论 **BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 1**。3 条发现车道**全部接受、无驳回**；MEDIUM-1 第四次改生产。

| 级别 | Codex r4 发现 | 车道处置 | 证据 |
|---|---|---|---|
| **MEDIUM-1** | `ValueError` 分支可**绕过**新增的反斜杠检查：`base=Path("backend")`（相对）+ 绝对路径候选 ⇒ `file_path.relative_to(base)` 抛 ValueError ⇒ `below_root=None` ⇒ 第二重检查退化 ⇒ **r3 拒绝、r4 接受**；同候选改绝对 base 又拒绝。因此「base 拼写再也不能影响判定」**不成立**。Codex 注明未发现实际磁盘越界、现有调用方不采用该拼法，故不定 HIGH | **接受，改生产（第四版）**：`relative_to` 两侧都改用 **resolve 后**的路径（`resolved_path.relative_to(storage_root)`），并用 `is_relative_to` 前置判断取代 `try/except`。实测：相对 base 与绝对 base **结果一致**，Codex 的构造两种拼法都被拒 | `sec-r4-M1-fix-verify.txt`（[A] 相对/绝对 base 均拒；[B] r3 构造 3/3 符合期望；[C] 60 例无放宽无误拒；[D] 返回值不变） |
| **MEDIUM-2** | §七 把 r3 记为「绑最终 HEAD，D-15 达成轮」，但 r3 之后又改了生产判定 ⇒ **r3 的 B/H=0 不能作为当前 HEAD 已通过最终审查的依据** | **接受，改表述**：§七 标题去掉「D-15 达成轮」，并加注「D-15 的达成以**最后一轮**为准」 | 本文件 §七 |
| **LOW** | `format-position-gate-v3.txt` 记录的是 `A∩B=3 [525,526,527]`，与裁定表宣称的「合计 0」**不一致** —— 证据未同步 | **接受，重跑并落盘**：那份存档是**修 format 债之前**的快照（重跑时用了内联脚本、忘了 `tee`）。现已绑最终代码重跑并落盘，六文件合计 **0**，同时把 v2/v3 的**不完备性**一并写进存档 | `format-position-gate-v3.txt`（已更新） |

### Codex r4 明确核验通过的项（原文摘要）

- **「固定文件系统状态下，原生包含检查仍是必要条件，返回路径不变：不存在相对 `b17b710d` 的旧拒绝→新接受；`below_root` 含 `..` 也不改变这一结论。」**
- **r3 指出的普通上传误拒机制已消除**；相对 base、正常拼接及普通 `..` 输入**未发现新的上传误拒**。
- calibration docstring 与 §〇 已同步收窄；增量**未改断言、类型注解、conftest 或其他车道代码**；生产全卡 diff 确为 **+20/−1**（r4 送审时值；第四版整改后见 §九）。

### 第四版修法为什么比第三版更彻底

第三版用 `file_path.relative_to(self.storage_base_path)`——**两侧都是未 resolve 的字面路径**，所以 base 写成相对还是绝对会走到不同分支。第四版改用 `resolved_path.relative_to(storage_root)`——**两侧都在 resolve 之后**，base 的拼写（相对/绝对、含不含 `..`、是不是符号链接）在比较前就已经归一，因此再也不能影响结果。`try/except ValueError` 也随之消失：第一重检查已经保证 `resolved_path` 在 `storage_root` 之下，`relative_to` 必然成功。

⇒ 这是「**消变量**」这条思路的第二次应用：第三版消掉了「base 的归一化拼写」，第四版消掉了「base 的字面拼写」。每消掉一个变量，就少一整类需要枚举的场景。

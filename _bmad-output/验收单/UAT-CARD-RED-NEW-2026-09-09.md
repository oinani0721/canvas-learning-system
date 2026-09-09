# UAT — CARD-RED-NEW（第十三批 · 车道 U11-C · U11 末卡）

> 批次标记 `[BATCH-2026-09-07-第十三批 / CARD-RED-NEW]`
> 树 `card-u11-red-c` · 分支 `card/u11-red-c` · 开工 HEAD `f043f5d4`
> 统一基线 `evidence-b13/unit-red-baseline-da690bf8.txt`（202 nodeid @ `da690bf8`）

---

## 1. 🎯 一句话目标

`tests/unit` 既有红里被分诊为「新」类的 **8 条**，逐条判定它是**真坏了**（回归）、**规矩变了没人改灯**（契约演进）、还是**灯当初就装反了**（测试写错），每条给依据后再分派处置——其中管「别人拿歪路径进来」的那一条属安全面，判定标准一个字不许改。

---

## 2. 📖 你的视角

这 8 盏红灯在基线里挂了很久。以前的处理方式容易滑向「改断言让它绿」，那等于把灯泡拧下来。本卡要求的是：**先说清楚每盏灯为什么红**，再决定动灯还是动被测的东西；安全那盏只允许把标准**收紧**，不允许放松。

---

## 3. 🖥️ 交互流程

本卡不改产品交互。唯一的对外行为变化在多模态文件上传的路径校验上：**同样的输入，现在被拒绝的更多了，被放行的一个没多**。合法上传路径的行为逐字不变。

---

## 4-A. 🤖 Claude 已代验（技术判据 + 证据路径）

### DoD (a) 第 0 分钟 + 8 条 nodeid

| 项 | 结果 |
|---|---|
| `pwd` / 分支 | `…/worktrees/card-u11-red-c` / `card/u11-red-c` ✅ |
| HEAD | **`f043f5d4`，不是 U11-B 末 commit `b17b710d`** —— 中间多一个纯 docs commit。实测 `git diff --stat b17b710d f043f5d4 -- . ':(exclude)_bmad-output'` **为空** ⇒ 代码面等价。**本卡地盘门基线取 `b17b710d`**（更保守，覆盖全部代码改动） |
| `git status --porcelain` | 空 ✅ |
| venv / `.env` | 均在 ✅ |
| 8 条 nodeid 全在 202 基线内 | ✅ `comm -23 new-nodeids.txt red-baseline-202.bare.txt` 无输出；逐条 `grep -c` = 1 |
| 6 个测试文件在 202 里**只有**这 8 条红 | ✅ 双向 `comm` 均空（`reds-in-c-files.txt`）⇒ (j) 允许 failed 集合 = 空 |
| 开工目录级 `>` 行 | **零** ✅（`red-diff-open-20260909T214440.txt`）；`<` 行 74 = U11-A ∪ U11-B 已翻绿集合 |
| 开工时本卡 8 条 | 全部**仍红** ✅ |
| 失败身份原文 | `identity-open-20260909T215002.txt`（`8 failed, 135 passed`，rc=1） |
| 改生产前的子集开工基线 | `subset-multimodal_service-open-20260909T220107.txt`（1 failed = 本卡 #8） |

### DoD (b) 8 条三选一裁定 → **测试写错 7 / 防御深度不足 1 / 回归 0 / 契约演进 0**

完整表在 `evidence-red-new/new-verdicts.md`。摘要：

| # | 用例 | 裁定 | 一句话依据 |
|---|---|---|---|
| 1 | calibration `test_over_confident_boundary` | 测试写错 | 断言与**自身 docstring** 互斥；判定行 `git log -L` 仅 1 commit ⇒ 从未绿过；同文件 `test_well_calibrated_boundary` 绿已锁定 `<` 语义 |
| 2 | calibration `test_under_confident_boundary` | 测试写错 | 同上，对称 |
| 3 | canvas `test_add_edge_triggers_memory_event` | 测试写错（async 竞态） | **两条运行期证据**，见下「一处推翻卡文推定」 |
| 4 | difficulty `test_empty_window_stats` | 测试写错 / 契约未定 ⇒ 改测试 | 唯一告警消费方 `health_monitor` 先判 `total_in_window == 0`，**根本不读 `is_healthy`**；内部消费方在空窗上不可达 |
| 5 | event_bus `test_tier2_retry_then_success` | 测试写错（patch 面过宽） | `assert 0 >= 2` 却在同一次运行的日志里看到 `attempt=1/3` ⇒ 那行日志是断言**之后**才产生的 |
| 6 | event_bus `test_tier2_all_retries_exhausted_writes_outbox` | 测试写错（同因） | 同上 + 负控 |
| 7 | fusion `test_no_correlation` | 测试写错（数据非正交） | `b = 1 - a` 是**完全负相关**，r = −1.0 是数学正确值；同文件 `test_perfect_negative_correlation` 绿 |
| 8 | multimodal `test_path_traversal_windows_style` | **防御深度不足**（改生产判定行） | 单列一节，见下 |

### 4-A 附：一处**方法学升级**（卡文给的判据不充分，已加强）

卡文的判据是「生产与测试同 commit 诞生 ⇒ 不可能是回归」。这条**不充分**：同 commit 只说明同批引入，若此后有 commit 改过判定行或断言行，仍可能是回归。

本卡升级为：**用 `git log -L <行区间>:<文件>` 追判定行与断言行的完整变更史**，只有两侧语义**自引入后从未变过**，才能推出「今天红 ⇒ 当初也红 ⇒ 从未绿过」，按定义排除回归。证据 `line-history.txt` / `line-history-detail.txt`。

这一升级立刻抓到 3 处卡文未覆盖的多 commit 情形：#1/#2 断言行另有 `836d0986`、#3 生产另有 `14f2d5a5`/`836d0986` —— 逐条查 diff 后确认**均为纯 black 折行、语义一字未变**，裁定不变。但第 4 处不是：

### 4-A 附：一处**推翻卡文推定**的改判（#3）

卡文把 #3 归为「诞生即矛盾」。`git log -L` 查出测试侧另有 **`14f0412d`（2026-02-07）是实质变更**：

```
-        await asyncio.sleep(0.1)
+        await wait_for_call(mock_memory_client.record_temporal_event)
```

于是补了两条运行期证据：

1. **取证**（`canvas-callargs-*.txt`）：把 `call_args_list` 全量打出来 —— `total_calls=2`，序列 `[node_created(node2), edge_created(edge_id='23b01549')]`。⇒ **生产确实发出了 edge_created 且 edge_id 正确**，排除「生产没发」。
2. **反证**（`canvas-pre14f0412d-*.txt`）：**只**把等待写法还原成 `14f0412d` 之前的 `asyncio.sleep(0.1)`、**生产保持当前 HEAD 不动**（单变量分离，顺带排除 `4104020d` 的 `context=ctx` 嫌疑）—— **5/5 稳定 PASSED**。

⇒ 这条**曾经绿过**，致红点是那次等待原语替换：`wait_for_call` 默认 `expected_count=1`，一有调用就返回，而 `reset_mock()` 早于 `add_node` 的后台 task，迟到的 `node_created` 就成了「最后一次调用」。裁定仍归「测试写错」（错在 `14f0412d` 那次改动选错等待原语），但**依据必须这样陈述，不能沿用「诞生即错」**。

两次取证都用 EXIT trap 无条件还原 + 前后 `shasum -a 256` 逐字节比对（`7f0d1199…`，两次均一致）。

> ⚠️ 过程中出过一次真实事故并被自己的判据抓回：第一次取证的 trap 里写了**相对路径**，而命令中途 `cd backend`，trap 退出时以新 cwd 求值 ⇒ `cp: No such file or directory`，**文件没有还原**。是「还原后必须比 shasum」这一步把它抓出来的；随后用绝对路径重做并复验。

### 4-A 附：安全面 #8 单列（(g) 要求）

**定性**（`posix-path-semantics.txt`，运行期实测）：

| 输入 | `resolve()` 在 base 内 | `\`→`/` 归一后 resolve 在 base 内 |
|---|---|---|
| `..\..\windows\system32\config`（本用例） | **True**（不越界） | **False**（越界） |
| `../../etc/passwd`（同文件绿用例） | False | False |
| `x.a\b`（POSIX 合法含反斜杠文件名） | True | **True ⇒ 不会被误拒** |
| `20260209_abc123.png`（正常） | True | True |

POSIX 上反斜杠是普通文件名字符，整串是**单个路径分量** ⇒「实现漏判越界」不成立，`DID NOT RAISE` 是平台语义差异。

**选 B（改生产）而非 A（skipif）的理由**：

1. `skipif(os.name != "nt")` 会让该断言在 macOS/Linux（本项目唯一实跑平台）**永久零覆盖**；而 `_validate_safe_path` 的 docstring 契约没有限定平台。
2. 它是**第二道门**：第一道门 `_detect_media_type` 有真实缺口——`ext` 不在白名单时只要 `content_type` 命中就放行，而 `_generate_unique_filename` 仍把未校验的 ext 拼进文件名。用「第一道门当前挡住了」论证第二道门不必严格，等于取消防御深度的意义。
3. 新判定是 `not A or not B` 的**拒绝**条件（原来只有 `not A`）：**放行面严格变小，不可能引入安全回退**。断言一字未改，测试变绿是因为实现变严。

**收益边界（如实，不夸大）**：实测 `Path(filename).suffix` 恒为「`.` + 不含点的串」⇒ **无法经 ext 注入 `..`**；两个生产调用方的文件名均由服务端生成。⇒ **在当前两个调用方上这条路径不可达，收益是前瞻性的**，不是修一个当前可利用的漏洞。

**先红后绿两份存档**：

| 阶段 | 存档 | 结果 |
|---|---|---|
| 改前 | `sec-before-RED-20260909T220118.txt` | `1 failed` · `Failed: DID NOT RAISE` · rc=1 |
| 改后 | `sec-after-GREEN-20260909T220215.txt` | `1 passed` · rc=0 |
| 合法路径不被误拒（同文件全量） | `sec-samefile-20260909T220215.txt` | `16 passed` · 0 failed |
| 消费面窄口径 2 文件 | `sec-consumers-20260909T220215.txt` | `38 passed` · 0 failed · rc=0 |

**改动**（`multimodal_service.py`，+10/−1，返回值 `return resolved_path` 未变，warning/raise/error_code 未变，无类型注解改动）。

### 4-A 附：#5/#6 负控（(e) 要求，`negctl-eventbus-20260909T220559.txt`）

| 项 | 结果 |
|---|---|
| 变异 | `event_bus.py:302-304` 的 `self._write_outbox(..., "retries_exhausted")` → `pass`（**只改这一处**，`:264` circuit_open 分支未动） |
| 指定判据（#6） | **FAILED** · `TimeoutError: outbox written after retries exhausted not met within 2.0s` —— 逐字指向 `outbox_written >= 1`，非 import/collect 错 |
| **负控特异性**（本卡自加的一步） | 同轮 #5 与同类 `test_tier2_success` **仍 2 passed** ⇒ 变异精准打在指定判据上，不是把文件搞坏 |
| 还原 | 前后 `shasum -a 256` 均 `7072eead8977…` ⇒ 逐字节还原；`git diff -- event_bus.py` 为空 |

失败形态如实说明：判据以 `wait_condition` 的 `TimeoutError` 抛出（其 `description` 逐字命名该判据）而非 `AssertionError`，语义等价于「等到超时也没等到 `outbox_written >= 1`」。

### DoD (i) 统一裁判（收工目录级）

| 判据 | 结果 |
|---|---|
| 命令 | `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit -q -p no:cacheprovider`，存档 `unit-after-20260909T221328.txt` |
| 汇总行 | `= 91 failed, 4820 passed, 48 skipped, 17 xfailed, 121 warnings, 29 errors in 247.51s (0:04:07) =` ✅ 在 |
| 末行 rc | `rc=1` ✅ 在 |
| 红总数 | 开工 `99 failed + 29 errors = 128` → 收工 `91 + 29 = 120`，**正好少 8** |
| `>` 行（新增红） | **零** ✅（`red-diff-20260909T221328.txt`） |
| `comm -12`（本卡贡献） | **恰好 8 条**，与本卡 8 条 nodeid 逐条对上；转出数 0 ⇒ 8 − 0 = 8 ✅ |
| `comm -13`（U11-A ∪ U11-B 贡献） | 74 条，与开工 `<` 行数一致 ✅ |
| 子集 `multimodal_service` | `subset-multimodal_service-close-*.txt` — `38 passed`, rc=0；与**开工基线** `diff` 只有 1 个 `<`（本卡 #8 翻绿），`grep '^>'` 无输出 ✅ |

> ⚠️ 这一轮目录级是在 format 修正**之后**重跑的，绑定最终代码。format 修正前那次（`SUPERSEDED-unit-after-20260909T220734-pre-format-fix.txt`）已标记作废，不作判据。

### DoD (j) 文件级 + 生产文件对应子集

| 判据 | 结果 |
|---|---|
| 六测试文件文件级 | `files-20260909T221302.txt` — **143 passed**, rc=0；`FAILED` 集合与 `transferred.txt`（空）`diff` 无输出 ✅ |
| `grep -c XPASS` | **0** ✅ |
| 转出清单 | **空**（无「判回归但改不动」的条目） |
| `multimodal_service` 子集 | 见下 |

**子集口径的一处实测更正**：卡文 §〇 担心宽口径 `grep -rln 'multimodal'` = 8 文件含 5 条外来红。本卡实测 **模块名口径 `grep -rln 'multimodal_service'` 与窄口径 `grep -rln 'upload_file\|_validate_safe_path'` 完全重合（同为 2 文件）**，且基线里只有本卡 #8 一条红 ⇒ **0 failed 可达**，(j) 与 (g)-B② 无口径冲突。

### DoD (k) 地盘门 + 禁顺手修存量（`territory-gate.txt`）

| 门 | 结果 |
|---|---|
| 改动文件清单（排除 `_bmad-output`） | 1 生产（`multimodal_service.py`）+ 5 测试文件，⊆ 允许集合 ✅。**`test_multimodal_path_security.py` 不在清单里 ⇒ #8 断言确实一字未改** |
| `backend/app` 改动 | 仅 `multimodal_service.py` +10/−1，全部在已裁定的判定行 ✅ |
| 类型注解门 | `grep -E '^\+' \| grep -nE '->\|: *(str\|int\|…)'` **无输出** ✅ |
| 两个 conftest / `tests/support/` | 均未动 ✅ |
| `fsrs_bridge.py` / `decay_beta.py` / `board_manifest_last_run.json` | 均未碰 ✅ |

### 4-A 附：lefthook `python-lint` 走了带存档跳过（协议 §2.3 / D-16 甲）

`python-lint` = ruff **lint** + ruff **format --check** 两段，hook 无法只跳其中一段。

- ruff **lint** 段：本卡 6 个改动文件 **全绿**（`All checks passed!`）。
- ruff **format** 段：5 个文件报 `Would reformat` —— 这是**存量**（`ruff.toml line-length = 120`，而这些文件按 black-88 排版）。跑一次 `ruff format` 会重排整个文件、产生数十处与本卡无关的改动 = D-16 明令禁止的「顺手修存量」。
- **本卡新增 format 债 = 0**，判据用**多重集对照**（协议 §2.3 指定，⛔ 非行号交集）：把 `ruff format --diff` 的变更行内容剥前缀、trim、排序做多重集，`base` = `git show HEAD:<file>`，`mine` = 工作树版本。`comm -13` **为空**；文件级名单 `identical name sets = True`。存档 `format-multiset-compare-config120.txt` / `format-gate-bypass-evidence.txt`。
- ⚠️ **口径修正记录**：第一版对照把两侧副本都放在项目树外，ruff 找不到 `ruff.toml`、双双退回默认 `line-length=88` —— 判据自洽，但**测的不是 hook 实际执行的口径**。已重做，两侧统一 `--config backend/ruff.toml`，结论一致（早期存档 `format-multiset-compare.txt` 保留但以 `-config120` 那份为准）。
- 本卡**自己写的行**曾引入 5 处 format 债（black-88 风格换行），已按 ruff 期望全部改为单行——这是修自己的代码，不是修存量。

---

## 4-B. 👤 你来验（3 分钟，不用打开任何工具）

剩下这八盏灯，我逐盏问了同一个问题：是东西真坏了，还是规矩变了没人改灯，还是灯本身当初就装反了——每盏都写了答案和理由；其中管「别人拿歪路径进来」的那一盏，我一个字都没改它的判定标准，只让它更严；我看到八盏灯的去向都能说清，没有一盏是被蒙住的，心里踏实。

**你可以只核这三句**：

1. **没有一盏灯是被蒙住的**——八条全部真的亮绿了，没有用「跳过」「标记为预期失败」「删掉」「把判断改成永远成立」这类手法。转出清单是空的。
2. **安全那盏只收紧、没放松**——它的判定标准（那句"必须报出 path traversal"）一个字都没动，是被测的东西变严了才亮绿。同一个文件里另外 15 条（含"正常路径应当放行"）仍然全绿，说明没有误伤。
3. **我说"这灯当初就装反了"时，是查过账的**——不是凭"生产和测试同一次提交"就下结论（那条推理不够），而是逐行追了变更史。追出来有一盏（第 3 盏）其实**曾经亮过绿**，我就改了口径、补了两次实测，没有硬套原来的说法。

### 我的感受（felt-sense）

最踏实的一处是第 3 盏灯。按卡文给的推理，它本该和另外几盏一样归入「诞生即错」，写起来最省事。是 `git log -L` 里多出来的那个 commit 让我停了一下——那次改动看起来完全是**好意**：把含糊的"等 0.1 秒"换成确定性的"等到被调用"。恰恰是这个改进让它红了。我把旧写法还原、只留这一个变量跑了 5 次，全绿。那一刻我确认了：**省事的那条路会写出一句假话**。

另一处是那个没还原成功的 trap。它提醒我，"我加了还原保护"和"文件真的还原了"是两件事，中间隔着一次 shasum。

---

## 5. 🚦 验收结果

- [ ] 通过
- [ ] 有问题（写在批注区）

---

## 6. 📝 批注区

（用户填写）

---

## 7. 🔗 技术引用

- 裁定表：`_bmad-output/审查/evidence-red-new/new-verdicts.md`
- 证据目录：`_bmad-output/审查/evidence-red-new/`
- Codex prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-RED-NEW.md`

### Codex 轮次记录

<PLACEHOLDER-CODEX>

---

## 8. ⛔ 本卡未证明什么（必填）

1. **不证明 #8 在 Windows 部署下的行为**——本机 macOS，只能测 POSIX 语义；`os.name == "nt"` 下 `resolve()` 自身就会按反斜杠切分，本卡的归一化判定在那里是否冗余或产生额外拒绝，未验。
2. **不证明 #8 的归一化在 storage base 自身含反斜杠时不误拒**——`str(file_path).replace("\\", "/")` 会把 base 前缀一起归一化。macOS/Linux 的 storage 路径不含反斜杠，但这是理论误拒面，未验。
3. **不证明 POSIX 下文件名合法含反斜杠的所有形态都不被误拒**——只实测了 `x.a\b`（归一化后仍在 base 内 ⇒ 放行）这一类；形如 `a\..\b` 的名字会被新判定拒绝，这是**故意的**，但它在 POSIX 上确实是合法单文件名。
4. **不证明 #3 的竞态在别的事件循环调度 / 机器负载下的复现率**——取证与反证各跑一次 / 5 次，均在本机空载。
5. **不证明 #5/#6 的新等待写法在所有 CI 负载下都不 flaky**——只在本机跑通并配了负控；`wait_condition` 默认 timeout 2.0s，极慢的机器上可能不足。
6. **不证明 #4「空窗该不该告警」的产品语义**——本卡只对齐现行契约并拿消费方证据说明改生产不解决真实误报；产品裁定归 `CARD-DIFFMATCH-EMPTY-WINDOW`。
7. **不证明 `mastery_config.json` 存在时 #1/#2 的新断言仍成立**——本树两处候选路径均不存在，故 `CALIBRATION_BIAS_THRESHOLD == 0.15`；新测试**单独断言了这个值**，配置覆盖会让它显形而不是静默漂移，但「漂移后正确行为是什么」未定义。
8. **不证明 `_validate_safe_path` 之外的多模态路径入口没有同类问题**——只核了 `:565` / `:709` 两个调用方。
9. **不证明六个生产文件的 pyright 存量为零**——归 U1 阶段 2，本卡禁顺手修存量；`python-typecheck` 未单独跑。
10. **只在 `tests/unit` 目录级验证**，未跑 `tests/integration` / `tests/e2e`（卡文禁）。

---

## 9. 📋 台账待登记条目（必填，主 session 登记）

1. **8 条三选一裁定计数**：测试写错 **7** / 防御深度不足 **1** / 回归 **0** / 契约演进 **0**。表在 `evidence-red-new/new-verdicts.md`。
2. **安全面 #8 处置 = B（改生产判定行）**，断言一字未改；候选卡 **`CARD-MULTIMODAL-PATH-NORMALIZE`**（跨平台路径归一化的完整处理，含本卡未覆盖的 Windows 侧行为与 base 含反斜杠的误拒面）。
3. **候选卡 `CARD-DIFFMATCH-EMPTY-WINDOW`**：空窗健康的产品语义裁定（`is_healthy` 是否应特判空窗）。本卡只对齐现行契约。
4. **环境依赖登记**：`calibration_tracker._load_calibration_thresholds()` 在 **import 时**从 `mastery_config.json`（仓根 / `backend/` 两处候选）覆盖模块常量 = 测试结果的隐藏可变量；本树两处均不存在。新测试已单独断言 `CALIBRATION_BIAS_THRESHOLD == 0.15` 使漂移显形。
5. **`event_bus` Tier2 测试的等待写法与 `TIER2_BASE_DELAY_S=2.0` 的耦合**：测试改为 `monkeypatch.setattr(..., 0.0)`；若后续调整生产退避需同步复核该测试。
6. **本卡对 `backend/app` 的实际改动清单**（供 U1 阶段 2 清 pyright 时对照）：仅 `backend/app/services/multimodal_service.py` 的 `_validate_safe_path` 判定行（原 `:507-508` → 现 `:507-517`，返回行 `:519` → `:528`），+10/−1，无类型注解改动。
7. **Codex 各轮存档路径 / 绑定 SHA / B-H-M-L 计数**：<PLACEHOLDER-LEDGER-CODEX>
8. **开工/收工 nodeid diff 与 comm 拆分结果**：`red-diff-open-20260909T214440.txt`（开工，`>` 零、`<` 74）/ 收工见 §DoD (i)。
9. **负控 sha 前后一致的存档**：`negctl-eventbus-20260909T220559.txt`（`7072eead8977…` 前后一致）；#3 两次取证的 trap 还原 sha `7f0d1199…` 前后一致。
10. **卡文事实更正（本卡实测）**：
    - (i) **#3 不是「诞生即矛盾」**——测试侧 `14f0412d`（2026-02-07）把 `asyncio.sleep(0.1)` 换成 `wait_for_call`，是致红点；还原旧写法 5/5 PASSED。卡文 §〇 第 3 行未覆盖该 commit。
    - (ii) **开工 HEAD = `f043f5d4` 而非 U11-B 末 commit `b17b710d`**（中间一个纯 docs commit，代码面 diff 为空）。
    - (iii) **`multimodal_service` 的模块名口径与窄口径实测重合**（同为 2 文件、基线仅 1 条红），(j) 与 (g)-B② 无冲突；卡文 §〇 预声明的 8 文件 / 5 条外来红是宽口径 `grep 'multimodal'` 的情形，本卡未采用。
    - (iv) `_validate_safe_path` 修复后行号位移：判定行 `:507-508` → `:507-517`，返回行 `:519` → `:528`。
11. **方法学升级建议入协议**：「生产与测试同 commit ⇒ 不是回归」不充分，应升级为「判定行与断言行语义自引入后从未变过（`git log -L` 追史）」。本卡据此抓到 3 处纯格式化 commit（结论不变）与 1 处实质变更（结论改判）。
12. **format 门对照的口径陷阱**：把对照副本放到项目树外时 ruff 找不到 `ruff.toml`、退回默认 `line-length=88`，判据仍自洽但测错了口径。两侧必须显式 `--config backend/ruff.toml`。
13. **EXIT trap 陷阱**：trap 内写相对路径 + 命令中途 `cd` ⇒ 还原静默失效。必须绝对路径，且**必须**用前后 shasum 复核（本卡就是靠这一步抓回的）。

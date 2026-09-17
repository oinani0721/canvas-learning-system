# UAT — CARD-RED-MOCKFIX（第十四批 T10-A）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-RED-MOCKFIX]` · 车道 `card-t10-red`（分支 `card/t10-red`）
> 基线 `08100483`（B14_BASE） → 修复 commit **`f6e4f8a1`** · 日期 2026-09-14（机器本地时区，D-18）
> 证据目录 `_bmad-output/审查/evidence-red-mockfix/`（下文一律引用**全文件名**，不用通配）
> 状态：**未 push**。Codex round-1 绑定最终 HEAD `f6e4f8a1`，BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2。

---

## 4-A Claude 已代验（技术证据）

### (a) 第 0 分钟锚核 + 基线自证

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-t10-red` |
| 分支 / HEAD | `card/t10-red` / `08100483` |
| `git status --porcelain` | 0 行 |
| `backend/.venv/bin/pytest`、`backend/.env` | 均在 |
| `grep -vc '^#' $BASE` | **64**（`$BASE` = feature 主干树绝对路径 `…/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`；车道树无此文件） |
| 主干代码同源 | 主干 HEAD `8856390d`，`git diff --name-only 08100483 HEAD -- backend \| wc -l` = **0** |

**生产锚点逐字复核，无行漂**：`initialize` = (276, 288)（AST）、`_recover_episodes_from_neo4j` = (320, 443)（AST）、
`:381` = `if self._episodes_recovered:`、`:384` = `records = await self.neo4j.get_all_recent_episodes(`。
**7 处 `mock_neo4j` fixture 行号与卡文逐字同**：30_11 `:29/:143/:263/:338/:400`、30_13 模块级 `:21`、batch `:23`；
`grep -c 'def mock_neo4j'` = **5 / 1 / 1 = 7**；改前 `grep -c get_all_recent_episodes` = **0 / 0 / 0**。

### (b) 分母重清（实测结论，D-3 的 38 与 D-30 的 27 均不沿用）

`08100483` 基线 64 条中，MOCKFIX 实测恰 **27**，分布 **6 / 10 / 11**
（`test_memory_service_batch.py` 6、`test_story_30_11_batch_parallel.py` 10、`test_story_30_13_batch_idempotency.py` 11）。
27 条 nodeid 逐条与卡文 §〇 清单 diff **为空**（`red27.nodeids` vs `base27.nodeids`，`diff_rc=0`）。
⇒ **手册 D-3 的 38 不成立；台账 D-30 的 27 经实测确认。**

开工目录级（`unit-open-20260914T195126.txt`，末行 `rc=1`）：`35 failed, 5077 passed, 48 skipped, 23 xfailed, 29 errors`，
nodeid 口径 `open.nodeids`(64) 与 `base.nodeids`(64) **diff 空**。
验伪锚：把 base 抽掉 1 行做对照集，同一 diff 立刻报 `64d63 <…`（rc=1）⇒ 「diff 空」不是判据失灵。

**跑法口径**：开工/收工两跑均用基线头第 2 行的**同一条命令**
（`cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider`）。
卡文 §二 写的是 `$PYTEST`(=`.venv/bin/pytest`)，本卡改用基线原文的 `python -m pytest`；
两者**实测收集面同为 5212**（`--collect-only` 对照），故非放宽，是对齐基线。

### (c) 先红

`mockfix-red-20260914T195832.txt`（末行 `rc=1`）：**`1 passed, 27 errors`**。
- 失败身份**精确文案**（实跑抄录）：`TypeError: 'MagicMock' object can't be awaited`，命中 **27/27**。
- 第 11 条 `TestBatchIdempotencyCompat::test_config_batch_neo4j_concurrency_exists` = **PASSED**（改前就绿）。

> ⛔ **口径更正④（本卡实测，新增）**：卡文 §二.2 要求 `grep -c 'memory_service.py:384'` 对齐 27，
> 但 `--tb=line` 对 **setup ERROR** 只输出一行 `E   TypeError: …`、**不带任何 file:line** ⇒ 该判据在此跑法下**恒 0 = 假阴性**。
> 本卡改用 `--tb=long` 定向探针补证崩点：`mockfix-red-traceback-20260914T195908.txt`
> —— `memory_service.py:285` → `memory_service.py:384`，正文含 `> records = await self.neo4j.get_all_recent_episodes(`，
> 收集数自证 `1 error`（非 rc=5 空收集）。**后人写身份判据须按跑法选：`--tb=line` 只能拿文案，拿不到行号。**

### (d) 修法（只碰三测试文件，纯新增 22 行）

7 处 `mock_neo4j` fixture 各补一行 `neo4j.get_all_recent_episodes = AsyncMock(return_value=[])`
（补桩后 `grep -c` = **1 / 5 / 1 = 7**，与 `def mock_neo4j` 计数一致，每处均落在该 fixture 的 `return neo4j` 之前）。
`AsyncMock` 三文件原有 import，未新增 import。**生产 `memory_service.py` 一行未动**；未改 conftest；未引入 `autouse`；
未把 `MagicMock()` 整体换成 `AsyncMock()`（`neo4j.stats` 是同步 dict，换掉会让 `:1384` 的 `neo4j_available` 判定失真）。

**桩值取 `[]` 的理由（正面回答 Codex ⓪）**：生产 `:388` 是 `if records:`，空列表走「什么都不追加」分支。
若桩成非空，`_episodes` 会被预置 `episode_type="recovered"` 条目，
`test_neo4j_unavailable_still_processes_to_memory` 的 `assert len(memory_service._episodes) >= 1` 将**恒真被掏空**。
⚠️ **措辞收紧（采纳 Codex r1）**：「与恢复前逐字节等价」只限于 **`_episodes` 仍为空**；
新桩使流程抵达 `:430`，把 `_episodes_recovered` 由 False 置 True —— 这是真实状态变化。
三文件 `grep -c '_episodes_recovered'` = **0 / 0 / 0**，无任何断言读它；`record_batch_learning_events` 也不读它。

### (e) 改后绿 + 验伪锚

**① 三文件**：`mockfix-green-20260914T200112.txt`（末行 `rc=0`）—— **`28 passed`**，0 error / 0 failed，
残留失败身份计数 **0**。28 = 翻绿的 27 + 原本就绿的第 11 条。

**② 负控 ×2（承重，证「逐处补桩」逐处生效）**——均用「变异前 `cp` 副本 + EXIT trap 还原」，
⛔ 未用 `git stash` / `git checkout`（HEAD 在当时还是**未修**的 `08100483`，用它还原会把修复一起抹掉）：

| 负控 | 存档 | 结果 | shasum 前/后 |
|---|---|---|---|
| A：删 30_13 **模块级**桩（3 个类共用） | `mockfix-negctl-A-30_13-20260914T200216.txt` | **11 errors**、身份命中 **11/11**、`pytest_rc=1` | `06a4cda6…` / `06a4cda6…` **逐字同** |
| B：只删 30_11 `TestBatchNeo4jDegradation` 一处 | `mockfix-negctl-B-30_11-degradation-20260914T200248.txt` | **恰 1 error**（正是该类唯一用例）**+ 同文件其余 10 条仍 passed**、`pytest_rc=1` | `2fe51a42…` / `2fe51a42…` **逐字同** |

B 的价值：证明 5 处补桩**各自独立必要**，不存在「某一处兜底」。

**③ 3 条「修后必重看」的 flip 验伪锚**——逐条把该用例**自身的「不可用」设定** `initialized` False→True，
观察其降级断言是否**结果改变**，且必须红在**点名的那条断言**（不是红在别处就算数）：

| # | nodeid | 设定点 | flip 前 | flip 后 | 红点 | shasum |
|---|---|---|---|---|---|---|
| ① | `test_memory_service_batch.py::…::test_neo4j_disconnected_still_stores_in_memory` | **用例体内**（fixture `initialize()` 之后） | passed | failed | `record_episode.assert_not_called()` → `Called 1 times.` | `e137cd1e…` 逐字同 |
| ② | `test_story_30_11_batch_parallel.py::TestBatchNeo4jDegradation::test_neo4j_unavailable_still_processes_to_memory` | **fixture 内** `stats={"initialized": False}` | passed | failed | 同上 → `Called 1 times.` | `2fe51a42…` 逐字同 |
| ③ | `test_story_30_13_batch_idempotency.py::TestBatchPartialFailureRecovery::test_neo4j_unavailable_fallback` | **用例体内** | passed | failed | 同上 → `Called 10 times.` | `06a4cda6…` 逐字同 |

存档：`mockfix-flip1-batch-disconnected-20260914T200317.txt` /
`mockfix-flip2-30_11-degradation-20260914T200400.txt` / `mockfix-flip3-30_13-fallback-20260914T200400.txt`。

**三条的定性结论（卡文要求逐条给）**：三者的「不可用」设定点**全部在写侧**——
`record_batch_learning_events:1384` 的 `neo4j_available = self.neo4j.stats.get("initialized", False)`；
而恢复路径 `_recover_episodes_from_neo4j`（320-443）**全文不读 `stats`**
（`grep -n 'neo4j.stats'` 命中 302 / 1208 / 1238-1246 / 1384 / 2624，**320-443 区间零命中**）。
⇒ 恢复桩与被断言的降级行为**正交**，返回 `[]` 不干扰、也未顺带满足任何前置。
①③ 的设定还发生在 fixture 的 `initialize()` **之后**，时序上与恢复桩不重叠。

### (f) 收工目录级 diff 只 `<`

**两轮都入库，如实并陈**：

| 轮 | 存档 | 汇总 | W4 哨兵 | nodeid 数 |
|---|---|---|---|---|
| run1 | `unit-close-20260914T200513.txt`（`rc=1`） | `36 failed, 5103 passed, 48 skipped, 23 xfailed, 2 errors` | `ATTEMPTS=1 (blocked=1…)` | 38 |
| run2 | `unit-close-run2-20260914T201256.txt`（`rc=1`） | `35 failed, 5104 passed, 48 skipped, 23 xfailed, 2 errors` | `ATTEMPTS=0 (blocked=0…)` | **37** |

**判据以 run2 为准**（`diff-base-close2.txt`）：`base.nodeids`(64) vs `close2.nodeids`(37) ⇒
**`<` 27 行、`>` 0 行**，且 `<` 集合逐条等于 MOCKFIX 全集（`vanished.nodeids` vs `base27.nodeids` diff rc=0）。
非本卡的 37 条红（含 `test_agent_service_extraction.py` 等 T10-B 面）**原样保留**，未出现在 diff 里。
验伪锚：同一 diff 命令作用在 run1 上能报出 **1 条 `>`** ⇒ 「0 个 `>`」不是判据失灵。

**run1 多出的那条 `>` 的归因**：`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`。
三条独立证据支持「与本卡改动无因果」：
1. **同一份代码两轮结果不同**（run1 红 / run2 连出现都没有）⇒ 非确定性，直接证成抖动；
2. **执行顺序**：`collection-order-20260914T202652.txt` 实测该文件在收集序 **670**，本卡三文件在 **2899 / 4341 / 4370**；
   `backend/pytest.ini` 的 `addopts` 只有 `-v` 与 `--tb=short`（无 `-n`），且 `pytest-randomly` / `pytest-random-order` 均未安装（计数 0）
   ⇒ 执行序 = 收集序，本卡 fixture 在它之后才被加载；
3. 协议 §3 已点名 `candidate422` 是会在 nodeid 间翻转的 W4 哨兵。
   ⚠️ **如实限定（采纳 Codex r1 LOW-2）**：W4 门在 run1 确实拦下了一次到 `('::1', 7691)` 的真连接尝试
   （`unit-close-20260914T200513.txt:383-388`，正文显示是 `MemoryService singleton` 首次创建走真 `Neo4jClient` 健康检查所致），
   **该次连接尝试的触发原因本卡未查清**；结论只到「与本卡改动无直接因果的证据较强」，不宣称「哨兵误报」。

### (g) 地盘门

`turf-ruff-gate-20260914T202057.txt`：
`git --no-pager diff --name-only --no-color 08100483 HEAD -- . ':(exclude)_bmad-output'` = **恰 3 个文件**，
`--stat` = `3 files changed, 22 insertions(+)`（**零删除**）。
验伪锚：去掉 `':(exclude)_bmad-output'` 后多出 **22** 条 `_bmad-output/` 路径 ⇒ exclude 语法真的在起作用。

### (h) 边界只读

`ruff-boundary-20260914T201931.txt`：三文件 `grep -nE -e lancedb -e 7691 -e 7687 -e canvas-vault` **无命中**（rc=1）；
`fsrs_bridge` / `decay_beta` 命中 **0 / 0 / 0**。未设任何指向现网的库路径或 `ACTIVE_VAULT` 环境变量。
全程未连 7691 / 7687（W4 门的 `blocked=` 计数见上表），未写 live vault，未动 LanceDB。

### ruff / 格式门

- `ruff check`（zsh 数组写法，卡文 §二.7 原形态：`08100483 HEAD` + `--diff-filter=AM`）：`files=3` → **All checks passed!**，`rc=0`。
  验伪锚：喂一个已知 `F821`（该规则在 `backend/ruff.toml` 的 `select` 内）的文件 → **rc=1** ⇒ 该 ruff 调用确实能红，不是 zsh 标量坑下的假绿。
- `ruff format --check` **rc=1**，走协议 §2.3 过渡条款，以 `LEFTHOOK_EXCLUDE=python-lint` 提交。**举证两条**：
  1. **被跳过门的原始输出**：`commit-attempt-20260914T202037.txt`
     （可见 `ruff check` → `All checks passed! / Lint OK.`，仅 `ruff format --check` 报 `3 files would be reformatted`）；
  2. **漂移不在本卡改动行**：`format-drift-attribution-20260914T201943.txt` ——
     三文件在**基线 `08100483`** 上就已 `ruff format --check` **rc=1**（用 `--stdin-filename` 保证 config 按同路径解析）⇒ dirty 集 ⊆ 主干既有；
     `ruff format --diff` 提议改的全是**既有行**（测试函数签名换行、`assert` 换行），
     对本卡新增行 `get_all_recent_episodes` 的命中数 = **0**。
  未顺手 `ruff format` 重排既有行：整仓 462 文件格式化是第十五批末位主 session 的单独一 commit（D-40），语义卡不得代劳。
- `python-typecheck` 未触发（glob 为 `backend/app/*.py`，本卡零 `backend/app` 改动），pyright 面本卡零贡献。

### (i) Codex

| 轮 | 存档 | 绑定 | 结果 |
|---|---|---|---|
| r1 | `_bmad-output/审查/codex-review-CARD-RED-MOCKFIX-r1.md` | `f6e4f8a1`（= 送审时 HEAD，审后仅改 `_bmad-output`） | **BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2** |

命令与协议 §2 逐字同（`gpt-6-astra` + `ultra`，`--sandbox read-only`，`</dev/null`）；
存档首部六行齐（`模型` / `reasoning_effort` / `codex` 三字段实测 `codex-cli 0.153.3`；会话头三行按字段找行并括注 L2 / L5 / L9）。
prompt 逐词 `grep -cF` 协议 §2 四个禁用措辞 → **各 0**（`prompt-wording-gate-20260914T202123.txt`，
验伪锚：同一 grep 对确实存在的 `AsyncMock` 命中 3）；旧模型名 `gpt-5.6` 命中 0。`*.stderr*` 由 `.gitignore:264` 覆盖，未入库。

**两条 LOW 的处置（登记不阻断，本卡不改代码）**：
- **LOW-1**「两条『仍落内存』用例只验返回计数与未调 Neo4j，没直接验内存内容」——
  Codex 自己判定是**既有弱点、本卡未引入也未放大**。加强既有断言超出本卡最小修法面，登台账移交。
- **LOW-2**「收集序 670/2899/4341/4370 当时无入库证据」——**已补落盘**（`collection-order-20260914T202652.txt`，
  数字逐条复现 + 验伪锚），并按其建议把 run1 那条红的结论限定为「无直接因果证据较强、具体原因未确认」（见 (f)）。
  该补证只改 `_bmad-output`，按 §1 不破坏绑定、按 D-15 不占轮次。

---

## 4-B 用户视角（零技术词）

我打开跟批量复习记录有关的功能时，系统内部有一批原本会报错的自检项，现在都能正常跑过了。
我不需要改变任何使用方式，之前偶尔会出问题的「一次记录一批学习动作」变得稳定了——
包括在后台数据库连不上的时候，东西也照样先存在本机、不会丢。我感觉这部分终于可以放心依赖了。

---

## 本卡未证明什么（必填 ≥4，实填 7）

1. 未证明生产 `_recover_episodes_from_neo4j` 在**真实 Neo4j** 下的恢复正确性 —— 本卡只补 mock 桩，全程未连 7691。
2. 未证明 `get_all_recent_episodes` **返回非空**时这 27 条用例仍全绿 —— 桩固定返回 `[]`，非空分支零覆盖。
3. 未证明 T10-B 的 ENVDEP 3 条、T10-C / D / E 的面 —— 本卡不碰 `test_agent_service_extraction.py` 等。
4. 未证明三文件里**未被当前断言触达**的其它潜在漏桩异步子属性不存在 —— 只保证当前 28 条绿 + 目录级 diff 只 `<`；
   Codex r1 独立核对后同样只说「未发现其他直接漏桩」，并声明范围外辅助函数的传递调用未作保证。
5. 未证明 3 条「修后必重看」用例的「不可用」语义在**生产真实降级路径**下等价 —— 只在 mock 层做了定性 + flip。
6. 未证明本卡改动对 `tests/api` / `tests/integration` / `tests/regression` / `tests/contract` 零影响 —— 只跑了 `tests/unit` 目录级。
7. 未查清 run1 里那次到 `('::1', 7691)` 的真连接尝试**由什么触发**（只证明它与本卡改动无直接因果的证据较强，且第二轮未复现）。

---

## 台账待登记条目（必填 ≥4，实填 10；⛔ 台账只由主 session 改）

1. **CARD-RED-MOCKFIX 修复 sha `f6e4f8a1`**（未 push）：27 条 MOCKFIX 由 `ERROR` 翻 `passed`；
   失败身份 = `'MagicMock' object can't be awaited` @ `memory_service.py:384` / `_recover_episodes_from_neo4j`；
   修法 = 测试侧 7 处 `mock_neo4j` fixture（5/1/1）各补 `get_all_recent_episodes = AsyncMock(return_value=[])`，纯新增 22 行、零删除。
2. **口径更正②（确认卡文结论）**：red-align 记的身份锚 `memory_service.py:381` 有误，`08100483` 实测 await 在 **`:384`**
   （`:381` 是 `if self._episodes_recovered:`）；两者都是**生产代码**锚、非文档行号，后人 grep 勿写死 `:381`。
3. **口径更正③（分母）**：`08100483` 实测 MOCKFIX 恰 **27（6/10/11）**；手册 D-3 的 **38 不成立**，台账 D-30 的 27 经实测确认。
4. **口径更正④（新增，判据级）**：`--tb=line` 对 **setup ERROR** 只打印 `E   TypeError: …` 一行、**不带 file:line**，
   故卡文 §二.2 的 `grep -c 'memory_service.py:384'` 对齐 27 在该跑法下**恒 0 = 假阴性**。
   要拿崩点行号必须换 `--tb=long`（本卡已用定向探针补证）。**建议回写协议/后续卡文。**
5. **跑法口径**：目录级须与基线头第 2 行逐字同——`cd backend` 后相对路径 `--ignore tests/unit/test_deploy_vault_sh.py`，
   且用 `.venv/bin/python -m pytest`（非 `.venv/bin/pytest`）；本卡实测两种启动方式收集面同为 **5212**，故等价，但按基线原文执行。
6. **3 条「修后必重看」定性结论**：「不可用」设定点统一在写侧 `record_batch_learning_events:1384`（读 `stats["initialized"]`），
   恢复路径 320-443 全文不读 `stats` ⇒ 恢复桩正交；三条 flip 均由 passed 翻 failed 且红在 `record_episode.assert_not_called()`。
7. **Codex r1**：`codex-review-CARD-RED-MOCKFIX-r1.md`，绑 `f6e4f8a1`，**B0 / H0 / M0 / L2**；
   LOW-1（两条「仍落内存」用例未直接验内存内容，既有弱点）建议另开卡；LOW-2 已补 `collection-order-*.txt` 落盘。
8. **目录级 diff 结果**：run2 与 64 基线 diff = **27 条 `<`、0 条 `>`**；run1 曾多出 `candidate422`（W4 哨兵抖动，两轮存档并陈）。
   建议按协议 §3「W4 哨兵绑 `blocked=` 次数不绑 nodeid」口径复核本卡。
9. **`ruff format --check` 豁免**：`LEFTHOOK_EXCLUDE=python-lint` 提交，举证 = `commit-attempt-20260914T202037.txt`（被跳过门原始输出）
   + `format-drift-attribution-20260914T201943.txt`（基线同三文件已 dirty；提议改动 0 次触及本卡新增行）。`ruff check` 本身 rc=0。
10. **基线文件位置口径（本批共同）**：`unit-red-baseline-08100483.txt` 在 feature 主干树且 `08100483` 时 **untracked**，
    NEW @ `08100483` 的车道树没有它 ⇒ 引用必须用主干树**绝对路径**，开工 `grep -vc '^#'` = **64** 自证。
11. **移交**：`get_all_recent_episodes` 返回**非空**分支未覆盖（建议移交 T10-D EPW 或后续卡）；
    run1 那次真连接尝试的触发源未查清（建议并入 W4 哨兵专项）。

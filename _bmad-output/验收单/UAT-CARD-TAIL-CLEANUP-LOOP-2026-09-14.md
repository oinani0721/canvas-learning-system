# UAT — CARD-TAIL-CLEANUP-LOOP（后台清理调度器不再忙循环）

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-TAIL-CLEANUP-LOOP]` · 车道 `card-t5-bugs`（分支 `card/t5-bugs`）
> 基准 `B14_BASE` = `08100483` · **最终 HEAD = `6ce8b286`** · 代码终审 SHA = `970f7eaa`（其后仅 docstring 尾巴与 `_bmad-output`）
> 缺陷来源：`TAIL-handover.txt` §A **T-new-4**；`RULINGS-2026-09-10.md` §R-10 定为 TAIL **最高优先**
> 证据目录：`_bmad-output/审查/evidence-tail-cleanup/`（`README.md` 是索引与边界声明，标注权威/被取代）

---

## 〇 缺陷与修法（一句话）

`cleanup_loop` 的 `while True` 里，唯一的 yield 点是 `await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)`。
`Settings` 上**没有**这个字段 ⇒ **参数求值发生在 `await` 执行之前**，直接抛 `AttributeError`，
被同一个 try 的 `except Exception` 接住、**无任何等待**就回到循环顶 ⇒ 整个清理调度退化为
**从不交还事件循环的 CPU 紧循环**。

三处最小修（只碰地盘三文件）：

| # | 文件 | 改动 |
|---|---|---|
| 1 | `backend/app/config.py` | 新增 `TASK_CLEANUP_INTERVAL_SECONDS: int = Field(default=3600, gt=0, ...)`，hunk 在 `:725-735` |
| 2 | `backend/app/services/background_task_manager.py` | 删掉已多余的 `reportAttributeAccessIssue` 抑制注解 + 改写 `:345-356` 注释 |
| 3 | 同上 | `except Exception` 分支在 `logger.error` 之后补 `await asyncio.sleep(settings.TASK_CLEANUP_INTERVAL_SECONDS)` |

`default=3600` 的依据：`cleanup_old_tasks(max_age_hours: int = 24)` 的保留截止**以小时计**，
每小时扫一次远小于该截止；同类既有间隔项 `VAULT_INDEX_SCAN_INTERVAL_S`=60、`ROLLBACK_SNAPSHOT_INTERVAL`=300。
`gt=0` 承重：防配 0 值再次退化为紧循环。

---

## 4-A Claude 已代验（逐条贴证据路径与末行）

| 完成条件 | 判据 | 结果 | 存档 |
|---|---|---|---|
| (a) 第 0 分钟 | pwd/分支/HEAD=08100483/porcelain 空、pytest+env+pyright `test -x`、基线 `grep -vc '^#'`=64（R-B14-2）、§〇 逐条 file:line 核对 | 全部通过，**§〇 无一条漂移** | `a-minute0-selfproof-20260914T194929.txt` |
| (b)① 根因门 先红 | `( cd backend && PY -c "...assert hasattr(settings,'TASK_CLEANUP_INTERVAL_SECONDS'), 'no field'" )` | `rc=1` + 含 `AssertionError: no field` + **无** `no such file`（排除 rc=127 路径错） | `b1-rootcause-gate-RED-20260914T195006.txt` |
| (b)② 单测 先红 | 未修代码上跑 `TestCleanupScheduler` | pytest 阶段 **0.95s**（非 hang）、`FAILED` ×2、回溯含守卫行与 `AssertionError: no field`、**回溯 `AttributeError` = 0**（验伪锚：正文 `Error` 总命中 = 2） | `b2-testcleanupscheduler-RED-20260914T195230.txt`（末尾附「判据自污染更正」段） |
| (d) 后绿 | 根因门 + `TestCleanupScheduler` | 根因门 `ok value= 3600` rc=0；两测 `2 passed`；全文件 `5 passed`（含 3 条既有） | `d1-*`/`d2-*-GREEN-final-*.txt`、`l-d32-comment-tail-*.txt` |
| (e) 负控 | **8 个**负控输入各红在**指定**断言，整批跑前跑后三文件 `shasum -a 256` 逐字节相同 | 全部命中，见下表 | `e-negctl-r5-20260914T212[0-9]*.txt` |
| (f) 地盘门 | `git --no-pager diff --name-only --no-color 08100483 HEAD -- . ':(exclude)_bmad-output'` | 恰为三文件；验伪锚：不带 exclude = 59 个文件、其中 `_bmad-output/` 开头 56 个（59−56=3，exclude 确在起作用） | `f-territory-gate-20260914T201602.txt` |
| (f) hunk 不落 :640-655 | `git diff -U0 … config.py \| grep '^@@'` | 唯一 hunk `@@ -724,0 +725,11 @@`；MEMORY_RETRY 在 `:644`/`:650`（T10-E 面），**无交集** | 同上 |
| (g) tests/unit 目录级 | nodeid 口径 vs 64 条基线 | `base=64 close=64`，**diff 完全为空**（`diff_rc=0`，`>` 行 0 条）；本卡新增类未进红集 | `g-unit-close-r5-*.txt` + `base.nodeids` / `close.nodeids` |
| (h) pyright 保持 0 | `( cd backend && "$P" app 2>&1 \| grep -E '^[0-9]+ errors?, ' )`（R-B14-10，绝对路径 + `test -x`，禁 `\| tail -1`） | `0 errors, 81 warnings, 0 informations` rc=0 | `h-pyright-app-r5-*.txt` |
| (h) 81↔82 **对照输入** | 把抑制注解加回去 → 82；删回 → 81 | `81 → 82 → 81`；第 82 条精确诊断 = `background_task_manager.py:358:83 - Unnecessary "# pyright: ignore" rule: "reportAttributeAccessIssue"` | `h2-pyright-81vs82-control-*.txt` |
| (i) ruff | 三文件 `ruff check`（zsh 数组）+ 验伪锚 | `files=3` / `All checks passed!` rc=0；**验伪锚 F821 rc=1** | `i-ruff-r5-*.txt` |
| (i) ruff format | `config.py` 仍 clean；另两文件漂移逐 hunk 归因 | `config.py` rc=0；漂移 hunk 与 `08100483` 原版一一对应（偏移量 = 本卡插入行数） | `i2-ruffformat-drift-attribution-final-*.txt` |
| (j) Codex | `gpt-6-astra` + `ultra`，**5 轮**（D-15 上限） | **r5 绑最终代码 SHA `970f7eaa`：BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2** | `codex-review-CARD-TAIL-CLEANUP-LOOP-r{1..5}.md` |
| (k) 提交 | header ≤100（`wc -m`）含批次标记与卡号；body 行 ≤100；`*.stderr*` 不入库；不 push | 6 个 commit 全部通过长度门（`wc -m`：72/87/85/89/86/88）；本卡 5 份 `codex-review-*.stderr` **全部未跟踪**（`.gitignore` 覆盖）；**未 push** | `k-commit-*.txt` |

### 8 个负控输入 ↔ 它们杀掉的断言（round-5 行号）

| # | 负控输入 | 声称杀掉 | 实测 |
|---|---|---|---|
| 1 | config 新字段改名 `..._NEGCTL1` | 根因门 + 两测守卫 `:210` / `:290` | ✅ 根因门 `rc=1`；两测红在守卫 |
| 2 | 删掉 `except` 分支的 `await` 等待 | `:339` | ✅ 只红 `:339`（测试 A 仍绿） |
| 3 | 该 `await` 换成**直接** `create_task` | `:339` | ✅ 实测事件出现 `sleep-enter, sleep-enter, sleep-exit`（两个 enter 连着） |
| 4 | `cleanup` 之后注入 `break` | `:269` + `:368` | ✅ 两测同时红 |
| 5 | 首轮等配置间隔、**之后各轮 `sleep(0)`** | `:269` + `:368` | ✅（Codex r2 点名；这是实质忙循环） |
| 6 | 一轮里连做两次 `cleanup` 后退出 | `:269` + `:368` | ✅（Codex r2 点名） |
| 7 | `if await self.cleanup_old_tasks(): break` | `:269` + `:368` | ✅（Codex r3 点名，truthy 方向） |
| 8 | `if not await self.cleanup_old_tasks(): break` | `:269` + `:368` | ✅（Codex r4 点名，falsy 方向） |

> ⚠️ `shasum -a 256` 是**整批前后各一组**（跑前一组、八段跑完还原后一组），**不是每段一组** ——
> 每段之间从 scratchpad 副本 `cp` 回，中间态不落档。此边界由 Codex round-2 指出，如实记录。
> 还原一律走 **EXIT trap + 副本 `cp`**，⛔ 全程未用 `git stash` / `git checkout`。

### Codex 五轮（D-15）

| 轮 | 绑定 SHA | B / H / M / L | 处置 |
|---|---|---|---|
| r1 | `8ace89c1` | 0/0/0/3 | 认 2.5 条：补「循环继续周期运行」断言、spy 改 enter/exit 成对、修失实文案；「不钉死退避值」rejected（卡文 (c).3 契约就是「> 0 即可」） |
| r2 | `85d2c18c` | 0/0/0/3 | 认 1.5 条：升级为**整段序列精确比对**（新增负控 5/6）；协程依赖追踪 rejected（与本卡范围不成比例） |
| r3 | `e68c50d3` | 0/0/0/2 | 全认：成功清理返回值改非零（新增负控 7）；**落实**边界声明（见下「自述失实」一条） |
| r4 | `19c96f0e` | 0/0/0/2 | 全认：返回值改为 0 与非零**各一次**（新增负控 8）；局部 docstring 措辞收窄；补完整 ruff 规则集证据 |
| **r5** | **`970f7eaa`** | **0/0/0/2** | **轮次上限，两条 LOW 登记不修**（见「本卡未证明什么」⑤⑥）；仅做 D-32 纯 docstring 尾巴 |

存档首部六行 blockquote（协议 §2.1）与会话头自证（`.stderr` 的 codex 版本行 / model 行 / reasoning 行，
括注行号；`.stderr` 本身不入库）见各轮存档。实测 `codex-cli 0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`。

### ⚠️ 本卡一次自述失实（如实记录，不隐去）

round-3 的 commit message 声称「已在测试类 docstring 的『本类不证明什么』里写明 await 依赖边界」，
**实际没写**。Codex round-3 LOW-2 核出这条自述不成立，round-4 才真正落实。evidence `README.md`
同样记了这一笔。这是本卡唯一一次「自述与实际不符」。

### 过渡条款使用记录（协议 §2.3 / 手册 §零.3）

- 全部 6 个 commit 用了 `LEFTHOOK_EXCLUDE=python-lint`。被跳过门的**原始输出**见
  `k-commit-attempt-bare-20260914T201457.txt` 与各 `k-commit-r*.txt` 的「裸跑」段
  （`Would reformat: …` + `[Python] Format check FAILED!` + rc=1）。
  「漂移不在本卡改动行」的**逐 hunk 归因**见 `i2-ruffformat-drift-attribution-final-*.txt`。
- ⛔ **`python-typecheck` 全程未跳过**（裸跑实测 `0 errors` / `exit 0`），符合本卡硬边界。
- 第 1 个 commit 另加了 `spec-sync-root`：该 hook 会重生成并**自动 staged** `backend/openapi.json`
  （T5-D 的面，本卡地盘门不允许）。实测它产生的**唯一**差异是 `x-generated-at` 时间戳
  （`git diff --numstat` = 1 增 1 删，仅 `:15852` 一行）⇒ 本卡改动对 OpenAPI schema **零影响**，
  跳过它没有掩盖任何真实 drift；已用 `git show HEAD:backend/openapi.json` 写回并 `git add` 还原，
  最终 `git diff 08100483 HEAD -- backend/openapi.json` 为空。

---

## 4-B 用户产品体验（零技术词，一句话 + felt-sense）

> **「以前这个后台清理会一直空转耗 CPU（像一个没装定时器的开关一直被拨来拨去），
> 现在它会按固定节奏安静地清一次、出错也先歇一会儿再试——我感觉后台终于不再无谓空转、
> 可以放心让它长期开着。」**

**felt-sense**：打开应用放着不管的时候，风扇不再无缘无故转起来；电脑摸上去是凉的。
后台那件事从"一直在使劲"变成了"该做的时候才做一下"——不需要盯着它，也不用担心它偷偷把机器烤热。

---

## 本卡未证明什么（≥4）

1. **未证明 3600 秒是生产最优间隔**。只证了「有界、不紧循环、`gt=0`」；具体值待运维按负载调。
2. **未证明单测里 `asyncio.sleep` 的 monkeypatch 口径等同真实定时器在高并发下的行为**。
   spy 拦截、不走真实时间，只证逻辑路径，不是压力测试。
3. **未证明 `cleanup_old_tasks` 本体在大量任务下的耗时与正确性**。本卡整体把它 monkeypatch 掉了，没改它。
4. **未真跑一个长周期（> 1h）观测实际清理触发**。终止全靠 spy 抛 `CancelledError`。
5. **（Codex r5 LOW-1，登记不修）未覆盖 `gt=0` 与 `default=3600` 本身**：删掉 `gt=0`、
   或把默认值改成 7200，两测仍绿 —— 因为测试的期望值取自同一份运行时配置。
   要拦这一类需要对 `Settings` 字段做独立的 Pydantic 校验测试。
6. **（Codex r5 LOW-2，登记不修）未覆盖异常类型收窄**：把生产 `except Exception` 改成
   `except RuntimeError`，两测仍绿（测试 B 只抛 `RuntimeError`）。要拦需要再加一条抛
   非 `RuntimeError` 的对照输入。
7. **（Codex r2/r3/r5 反复点名，已在测试类 docstring 边界第 3 条明写）事件成对不证明协程依赖**：
   把异常分支写成「等待丢进 `create_task`，再 `await` 一个立刻兑现的检查点」，精确四事件照样成立，
   而那个正数等待其实没人等。**该写法仍违反本卡契约，属于门没覆盖，不是行为被判到卡外。**
8. **未证明删掉抑制注解后在非 basic pyright 模式下仍 0 errors**（本仓固定 `typeCheckingMode: basic`）。
9. **`ruff check` 的覆盖面有限**：`backend/**` 生效配置是 `backend/ruff.toml`，
   `select = ["E9","F63","F7","F82"]` —— **F401 与 isort(I) 都未启用**（完整 enabled 列表实测：
   F401 命中 0 / I001 命中 0 / F821 命中 1）。所以「ruff 通过」**不**代表风格规则被检查过；
   卡文 §二.5 模板给的 F401 验伪锚在本面上恒不触发，已改用启用集里的 F821。

## 台账待登记条目（≥4）

1. **T-new-4 忙循环修复**：commit 链 `8ace89c1`（生产修复）→ `85d2c18c` / `e68c50d3` / `19c96f0e` /
   `970f7eaa`（测试补强，生产零改动）→ `6ce8b286`（D-32 纯 docstring 尾巴）。
   nodeid = `backend/tests/unit/test_background_task_manager.py::TestCleanupScheduler`（2 条）。
   先红后绿证据路径见本单 4-A。
2. **路径更正**（设计稿/handover 写错，已实测更正并落 §〇）：
   `backend/app/core/background_task_manager.py` **不存在** → 真身 `backend/app/services/background_task_manager.py`；
   `backend/app/core/config.py` **不存在** → `Settings` 在 `backend/app/config.py:77`。
3. **`backend/app/config.py` 与 T10-E 的声明交集**：本卡只加 `TASK_CLEANUP_INTERVAL_SECONDS`，
   hunk = `@@ -724,0 +725,11 @@`；T10-E 退役的 `MEMORY_RETRY_BASE_DELAY`/`MEMORY_RETRY_MAX_DELAY`
   在 `:644` / `:650`。**两者无交集**，集成期可直接核。
4. **`:350` 多余 `reportAttributeAccessIssue` 抑制注解删除**：pyright `0 errors / 81 warnings`；
   81↔82 已由对照输入独立证明，第 82 条诊断 = `background_task_manager.py:358:83`。
5. **移交设计：错误等待复用间隔 vs 独立常量**。Codex 各轮一致指出：失败后到下一次清理是
   **`2 × interval`**（异常分支等待 + 循环顶等待），默认约 2 小时。本卡按卡文 (c).3 默认口径
   复用同一间隔（零新增配置面）；若要快速恢复，需**一起**明确重试时序，不能只加一个短常量。
6. **Codex 五轮存档**：`codex-review-CARD-TAIL-CLEANUP-LOOP-r{1..5}.md`，
   绑定 SHA 依次 `8ace89c1` / `85d2c18c` / `e68c50d3` / `19c96f0e` / `970f7eaa`，
   B/H/M/L = 0/0/0/3、0/0/0/3、0/0/0/2、0/0/0/2、0/0/0/2。`*.stderr*` 未入库。
7. **tests/unit 目录级**：对 64 条基线 diff **完全为空**（不只是「只有 `<`」），本卡新增类未进红集。
8. **`backend/tests/unit/test_background_task_manager.py` 地盘：已批（R-B14-8），T5-A 独占**。
   名义差异如实登记：裁定/手册写「新文件」，实测 `B14_BASE` **已有**该文件
   （`git ls-tree 08100483` blob `cf8d02a9`，156 行）⇒ `git diff --stat` 上它是**修改**不是**新增**，
   集成期核地盘时别按「新文件」判。本卡只新增 `TestCleanupScheduler` 类 + 一行模块级
   `from app.config import settings`（守卫要求「测试首行」就是 assert，故 `settings` 必须模块级可见），
   未动既有 `TestContextVarInheritance` 与 autouse fixture。
9. **`spec-sync-root` hook 会把 `backend/openapi.json` 塞进任何触及 `backend/app/**` 的 commit**
   （即使实际 schema 零变化，只差 `x-generated-at` 时间戳）。本卡第 1 个 commit 因此临时
   `LEFTHOOK_EXCLUDE` 了它并还原文件。**同批其它触及 `backend/app` 的卡会遇到同一情况**，
   建议主 session 在集成期统一口径。
10. **车道树 guard hook 禁 `rm`**：本卡想剔除一份「显示过滤过头」的早期负控存档被拦下，
    改为保留并在 `evidence-tail-cleanup/README.md` 逐份标注「权威 / 被取代」。
11. **`ruff check` 在 `backend/**` 上的真实覆盖面**（见「本卡未证明什么」⑨）：
    `backend/ruff.toml` 的 `select` 只有 4 条必错级规则，遮蔽了仓根与 `pyproject.toml` 的声明。
    **卡文模板里的「F401 验伪锚」在 `backend/**` 上恒不触发**，建议批级模板更正为 F821。

---

## 硬边界自查

- ⛔ 未写 live vault（`git diff 08100483 HEAD -- canvas-vault` = 0 个文件）
- ⛔ 未连 7691 / 7687（目录级跑法带 `live_port_guard`，各轮 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`）
- ⛔ 未碰 `fsrs_bridge.py` / `decay_beta.py`（三改动文件 `grep -rn fsrs_bridge` = 0 命中）
- ⛔ 未碰 `main.py` / `conftest.py` / `pyrightconfig.json` / `lefthook.yml` / `models/**` / `requirements.txt`（地盘门实证 = 0）
- ⛔ 未碰 `backend/openapi.json`（最终 diff 为空）
- ⛔ 未用 `git stash`；⛔ 未跳过 `python-typecheck`；⛔ 批中未装/升任何包；⛔ 未改台账；⛔ **未 push**

### ⚠️ 一条判据口径更正（自查时发现，如实记）

初稿写的判据是「`git ls-tree -r --name-only HEAD | grep -c stderr` = 0」，实测 = **3**，不是 0。
逐条查清后：那 3 个是 **`08100483` 就已存在**的历史文件，**文件名里含 `stderr` 但后缀是 `.txt`**
（`G4-9-evidence/census-stderr.txt`、`evidence-g29f1/stderr-not-tracked-*.txt`、
`evidence-pyright-svc/stderr-gate-*.txt`），与本卡无关。

正确口径应当把面收到本卡改动上：`git --no-pager diff --name-only --no-color 08100483 HEAD | grep -c stderr`
= **0**；逐 commit 复核 `git show --name-only` 也是 6 个全 0。本卡自己产出的 5 份
`codex-review-CARD-TAIL-CLEANUP-LOOP-r{1..5}.stderr` 在工作树里是 `??` 未跟踪（`.gitignore` 覆盖）。

⇒ 结论不变（`*.stderr*` 未入库），但**初稿那条判据取的面大于它的主张**，会把主干既有文件算进来。
记在这里给集成期复核参考。

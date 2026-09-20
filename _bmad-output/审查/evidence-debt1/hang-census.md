# 挂起清单 hang-census — CARD-DEBT-1

> `[BATCH-2026-09-18-第十五批 / CARD-DEBT-1]` · 车道 `card-p9-testinfra` · 树 `card-p9-testinfra` ·
> 开工 HEAD `a7341ca4`（P9-A 末 commit）
> 本文件只写**从存档里读得出来的事实**。⛔ 不写「疑似」「大概率」：拿不出存档的，写「未实测」。
> 每条都给：nodeid 或文件 → 等待对象 → 证据存档**全名 + 行号** → 处置归属。

## 〇 怎么跑的 / 怎么读

- 分批跑批器：scratchpad 里的 `census_batch.py`（不入库），每批起一个真的 pytest 子进程，
  stdout+stderr 全量落盘，**外层墙钟硬上限 1200 秒**（卡文 §一(e)①「每批 20 分钟」）。
  到点由 `subprocess.run(timeout=…)` 终止**本脚本自己起的那个进程**，⛔ 不按名字批量杀。
- 每份存档的**末两行**是 `wall_clock_s=<墙钟>` 与 `rc=<被测命令的退出码>` —— 判据读这两行，
  不读跑批器的 stdout（管道会吃掉 rc）。
- 每批都带 `--timeout=300`（与 `backend/pytest.ini` 的 `timeout` 同值，显式传一遍，
  免得「到底有没有生效」要靠猜）。
- ⚠️ **「有没有超时」的判据口径改了两次，两次都是本卡自己抓到的假阴性**。记在这里，
  因为这条判据是整份清单的地基 —— 它错了，「没有挂死」这个结论就是空的。

  | 口径 | 写法 | 在已知超时的栈探针上 | 在**被砍断**的 schemathesis 存档上 | 判定 |
  |---|---|---|---|---|
  | A（卡文 §二.7 原文） | `grep -c 'Timeout >'` | **0** | **0** | ❌ 恒假阴性 |
  | B（第一次更正） | `grep -c 'from pytest-timeout'` | 3 | **0** | ⚠️ 对完整存档有效，对被砍断的无效 |
  | C（最终采用） | `grep -cF '+ Timeout +'` | **6** | **2** | ✅ 两种存档都有效 |

  - A 为什么恒 0：pytest-timeout 2.4.0 打的是 `Failed: Timeout (>30.0s) from pytest-timeout.`
    —— 中间多一个左括号，`Timeout >` 永远匹配不上。
  - B 为什么对被砍断的存档无效：那句 `Failed: Timeout … from pytest-timeout.` 只在**收尾的
    FAILURES 段**打印。跑被外层墙钟砍在半路时，收尾段根本没打出来，而超时**确实发生过**。
  - C 是什么：`timeout_sigalrm` 在 dump 线程栈的**前后各打一次** `+ Timeout +` 横幅，
    所以横幅**成对**。这一点由两份独立存档自证：studyq **3 个 ERROR ↔ 6 个横幅**、
    chat **1 个 ERROR ↔ 2 个横幅**。据此 `横幅数 / 2 = 超时发生次数`。
  - **用 C 口径重扫全部存档**，非 0 的共**四份**（⚠️ 2026-09-19 人审替代更正：原写「只有三份」，漏了 `contract3-close-20260918T222224.txt` = 2 —— 而本文件 §二.5 自己就写了它，属同份文档自相矛盾）：
    `census-stackprobe-studyq-…:6`（= 3 次，故意的）、`census-stackprobe-chat-…:2`（= 1 次，故意的）、
    `census-contract-schemathesis-…:2`（= **1 次，非故意，见 C-2b**）。
    其余每一批都是 **0** —— 结论未变，但现在是用一条在两种存档上都有效的口径得出的。
- ⚠️ **「W4 汇总行恰 1 次」这条判据有两个合法例外**（不是违规，写明以免复核时误判）：
  ① **被外层墙钟砍断**的跑 → `pytest_terminal_summary` 根本没跑到 → **0 次**
     （`census-contract-schemathesis-20260918T210833.txt`）；
  ② **本卡新门的失败正文里嵌着子进程的完整输出** → 子进程各自也打一行（带 `E` 前缀）
     → 多次（`gate-before-r2-20260918T195344.txt` 的 `:108` / `:161` 是子进程的，
     `:210` 才是父进程自己的）。绿的那两份没有失败正文，所以恰 1 次
     （`gate-after-20260918T200043.txt` / `gate-durations-20260918T221632.txt`）。
  ⇒ 正确的说法是「**每份目录级跑的存档**恰 1 次」，而不是「每份 `.txt` 恰 1 次」。
  本卡全部**目录级**存档实测均为 1 次。
- `tests/integration` / `tests/e2e` **只做 `--collect-only`**，⛔ 不执行：这两个目录里有
  20 / 7 个文件在 import 期 `from app.main import app`，执行会真起 lifespan，而 W4 对它们
  只记不拦。

## 一 结论摘要（先说结果）

1. **在「默认门」覆盖的那些目录里，本次实测没有任何一条用例挂死。**
   unit / regression / skills / api / security / smoke / core / bdd / benchmark / load /
   performance / 仓根 27 文件，全部在外层 20 分钟墙钟内**自己**跑完
   （`killed=False`，没有一批是被墙钟砍掉的）；用**最终口径 C**
   `grep -cF '+ Timeout +'` 重扫，超时命中 **0**、`DeadlineExceeded` 命中 **0**
   （口径为什么改了两次，见 §〇 那张表）。
   ⚠️ 但 `tests/regression` 是 **1175.32 秒 = 19 分 35 秒**，距那条 20 分钟上限只差 25 秒
   —— 「这次没被砍」和「它不会被砍」是两件事，见 C-1b。
2. **真正让人以为「挂死」的是三件互不相同的事**，它们在没有 timeout 的年代长得一模一样：
   - ① `tests/unit` 里四条**超长 teardown**（217/134/118/55 秒），加起来 525 秒 ≈ 那次
     1013 秒总时长的一半；
   - ② `tests/contract` 的 **collection 本身**就要两分钟，而执行面
     `test_openapi_contract.py` 单文件 **20 分钟跑不完**，期间 300 秒 item 超时触发过 1 次。
     ⚠️ 那次超时的栈是 **obsidiantools 建 vault 图 + lxml 解析 markdown**，
     该存档里到现网端口的连接尝试 = **0**（见 C-2b 的更正）；
     `blocked=19` 与 `DeadlineExceeded 45.9s` 是同目录**另一个文件**
     `test_health_contract.py` 的事；
   - ③ `tests/integration` 的 **collection 期**有到现网 Neo4j 的连接尝试，被 W4 拦下后
     进程以 `rc=3` 结束 —— 这不是慢，是**收集就出事**。
3. **协议 §2.2 :60 写的「`tests/contract` 目录级挂起 = pact provider 面等真服务」与实测不符**
   —— **本次配置下** pact 两个文件 0.55 秒跑完（provider 验证类被 `:298` 的 skipif 整类跳过）；
   20 分钟没跑完的是 `test_openapi_contract.py`。
   ⚠️ 这只排除**本次配置下**的 pact 探针，**不能**反证历史批次、也不能反证
   provider 真被执行时的行为（那需要 `PACT_DIR` 存在或配了 broker）。见 C-2b 与 §六。
4. **默认门实跑：不挂死、有总结行，但 47 分 33 秒，未达 20 分钟目标**（见 §二.4）。
   `147 failed, 9041 passed, 51 skipped, 196 deselected, 18 xfailed in 2831.38s`，
   `rc=1`（有测试失败，不是挂死），超时触发 **0** 次。
   **卡在哪**：`tests/unit` ≈ 17 分 + `tests/regression` ≈ 15-19 分 = 全部墙钟的三分之二以上；
   两者都不是「卡住」，是一大片慢用例摊出来的（C-1 / C-1b）。
   ⇒ 总账 v2 :56 的「≤20 分钟」这一条**本卡未达成**，如实登记；
   「允许 fail、不允许挂死 / 无总结行」这一条**达成**。

## 二 分批结果表

| 批次 | 总结行 | 收集数 | W4 | 超时（C 口径 ÷2） | `DeadlineExceeded` | 红 | 墙钟 | rc | 存档全名 |
|---|---|---|---|---|---|---|---|---|---|
| **regression** | 1913 passed, 6 skipped, 1 xfailed | - | blocked=0 | 0 | 0 | 0 | **1175.32s（19:35）** | 0 | `census-regression-20260918T202641.txt` |
| skills | 555 passed | - | blocked=0 | 0 | 0 | 0 | 138.88s | 0 | `census-skills-20260918T201642.txt` |
| security | 42 passed, 1 skipped, 4 xfailed | - | blocked=0 | 0 | 0 | 0 | 31.46s | 0 | `census-security-20260918T201901.txt` |
| smoke | 6 passed | - | blocked=0 | 0 | 0 | 0 | 16.84s | 0 | `census-smoke-20260918T201933.txt` |
| core | 28 passed | - | blocked=0 | 0 | 0 | 0 | 17.55s | 0 | `census-core-20260918T201950.txt` |
| bdd | 2 passed | - | blocked=0 | 0 | 0 | 0 | 41.14s | 0 | `census-bdd-20260918T202007.txt` |
| benchmark | 7 passed | - | blocked=0 | 0 | 0 | 0 | 27.31s | 0 | `census-benchmark-20260918T202048.txt` |
| load | 4 passed | - | blocked=0 | 0 | 0 | 0 | 56.59s | 0 | `census-load-20260918T202116.txt` |
| performance | 16 passed | - | blocked=0 | 0 | 0 | 0 | 44.48s | 0 | `census-performance-20260918T202212.txt` |
| api | 269 passed | - | blocked=0 | 0 | 0 | 0 | 21.78s | 0 | `census-api-20260918T202257.txt` |
| 仓根 27 文件 | **114 failed**, 440 passed | - | blocked=1 | 0 | 0 | 114 | 202.97s | 1 | `census-rootfiles-20260918T202318.txt` |
| unit（开工基线，改前） | 32 failed, 5755 passed, 44 skipped, 13 xfailed | - | blocked=0 | 0 | 0 | 32 | 1013.59s | 1 | `unit-open-20260918T192142.txt` |
| contract 三文件（改前等价） | 2 failed, 75 passed | - | **blocked=19** | 0 | 0 | 2 | 514.90s | 1 | `contract3-preequiv-20260918T200525.txt` |
| contract 目录（只收集） | — | **196** | blocked=0 | 0 | 0 | 0 | 收集 123.57s | 0 | `contract-collect-20260918T202937.txt` |
| integration（只收集） | — | **1139** | **blocked=1, unacc=1** | 0 | 0 | 0 | 15.85s | **3** | `census-collect-integration-20260918T201549.txt` |
| e2e（只收集） | — | **108** | blocked=0 | 0 | 0 | 0 | 37.07s | 0 | `census-collect-e2e-20260918T201605.txt` |

### 二.1 控制组（`-p no:timeout`：把插件整个关掉，ini 那两个键随之失效）

这两个目录**没有改动前的基线**（census 是在改完 ini/conftest 之后跑的），所以用控制组
证明「那些红在没有本卡改动时也一样红」。hook 对这两个目录本来就是 no-op ——
`rel.parts[0]` 对仓根文件是**文件名**、对 regression 是 `regression`，都不在三条映射里。

| 对照 | 带插件 | 关插件（控制组） | nodeid 集 diff |
|---|---|---|---|
| 仓根 27 文件 | 114 failed / 440 passed（`census-rootfiles-20260918T202318.txt`） | **114 failed / 440 passed**（`census-control-rootfiles-20260918T204620.txt`） | **完全相同**（114 vs 114，`diff` rc=0） |
| regression | 1913 passed / 6 skipped / 1 xfailed，**红 0**（`census-regression-20260918T202641.txt`） | **1913 passed / 6 skipped / 1 xfailed，红 0**（`census-control-regression-20260918T205023.txt`） | **两侧都是空集** |

⚠️ 墙钟不可直接相比：带插件那次 1143.50s，控制组 884.05s —— 控制组**更快**。
这不是「插件有开销」的反证也不是正证，而是**争用**：带插件那次（20:26-20:46）与我并发跑的
`contract-collect-20260918T202937.txt`（20:29 起、耗时 123.57s）抢了 CPU。
本卡不主张任何关于插件开销的结论 —— 没做过隔离测量。

**副产品（正好答了「没装插件会怎样」）**：控制组比带插件那次多出的两条 warning 正是
`census-control-rootfiles-20260918T204620.txt:1801` 的
`PytestConfigWarning: Unknown config option: timeout` 与 `:1806` 的 `… timeout_method`，
而该次**照常跑完**、红集不变、rc=1（不是 error）。带插件那次这两条命中 0。
⇒ 「没装 `pytest-timeout` 的 venv 读到这两个键只会警告」这句话是**实测**，不是推论。
⚠️ 适用范围（Codex round-1 MEDIUM）：这条只对**本仓当前的默认配置**成立。
加上 `-o strict_config=true` 或 `-W error::pytest.PytestConfigWarning` 之后，未知 ini 键
**可以**变成失败；而「全仓没有 `--strict-markers`」这条 grep 依据本身也不充分 ——
`--strict-markers` 管的是未注册 marker，**不管未知 ini 键**，而且 grep 仓内文件
排除不了命令行现场注入。所以正确说法是：**在本次实测的调用方式下**只警告。

### 二.2 取证探针（**必然红**，它们不是门）

用 `--timeout=30 --timeout-method=signal` 主动打断，目的就是拿栈。

| 探针 | 结果 | 超时次数（C 口径 ÷2） | 墙钟 | 存档全名 |
|---|---|---|---|---|
| `test_study_question_deep_mode.py` 整文件 | 8 passed, **3 errors**（3 个都在 teardown） | **3** | 121.1s | `census-stackprobe-studyq-20260918T210537.txt` |
| `test_chat_endpoint::test_enrich_context_accepts_user_question_and_mode_answer` | 1 passed, **1 error**（teardown） | 1 | 55.1s | `census-stackprobe-chat-20260918T210738.txt` |

两者给出**同一条**等待链，见 C-1。

### 二.3 contract 两面定向探针（把协议 §2.2 的说法交给实测）

| 探针 | 总结行 | 超时（C 口径 ÷2） | W4 | 墙钟 | rc | 存档全名 |
|---|---|---|---|---|---|---|
| pact 面（2 文件） | **25 passed, 2 skipped, in 0.55s** | 0 | blocked=0 | 17.68s | **0** | `census-contract-pact-20260918T212833.txt` |
| schemathesis 面（`test_openapi_contract.py`） | **无总结行**（被砍） | **1** | — | **1200.09s，`outer_wall_clock_kill: True`** | **124** | `census-contract-schemathesis-20260918T210833.txt` |

⇒ 详见 C-2b 与 §六。

### 二.4 默认门实跑（总账 v2 :56 完成判据的实体）

跑法（卡文 §一(e)③ / §二.8）：

```
cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests \
  --ignore=tests/integration --ignore=tests/e2e \
  -m "not integration and not e2e and not contract" \
  -q -p no:cacheprovider -rfE --durations=40 --timeout=300
```

存档 `census-default-gate-20260918T212851.txt`：

| 判据 | 结果 |
|---|---|
| **有总结行**（不许挂死 / 不许无总结行） | ✅ `:3180` = `147 failed, 9041 passed, 51 skipped, 196 deselected, 18 xfailed, 795 warnings in 2831.38s (0:47:11)` |
| 是否被外层墙钟砍掉 | ❌ 没有：`# outer_wall_clock_kill: False`，`rc=1`（= 有测试失败，不是挂死） |
| **墙钟** | **2853.11s = 47 分 33 秒** —— ⚠️ **未达标**（目标 ≤ 20 分钟） |
| `deselected` 数 | **196**，与 `tests/contract` 的收集数 **196**（`contract-collect-20260918T202937.txt:239`）**数量相等**。⚠️ 这是**数量**判据不是**身份**判据（Codex round-1 MEDIUM）：两次收集若都变化，「195 条 contract + 1 条目录外带排除 marker 的用例」同样满足这个等式。本卡**没有**导出同一次跑的 deselected nodeid 清单去逐条比对，所以只能说「数量对得上、且没有发现可点名的额外排除用例」，不能签「集合已独立核对」。支持性证据：其余目录具名存档的收集数合计与 `9257 selected` 吻合 |
| 超时（C 口径） | **0** —— 没有任何一条用例是被 `timeout = 300` 杀掉的 |
| `DeadlineExceeded` | 0 |
| W4 汇总行 | 恰 **1** 次，`blocked=1, advisory=0, unaccounted=0` |

**147 条红的逐条归属**（三方集合运算，`comm`）：

| 来源 | 条数 |
|---|---|
| `tests/unit` 开工基线（`unit-open-20260918T192142.txt`） | 32 |
| 仓根 27 文件（`census-rootfiles-20260918T202318.txt`，已由 `-p no:timeout` 控制组证明与本卡无关） | 114 |
| 已知合集（去重） | **146** |
| 默认门实际 | **147** |
| **多出 1 条** | `tests/unit/test_deploy_vault_sh.py::test_preflight_npm_build_failure_is_not_reported_as_timeout[fail-8253]` |

多出那条的**失败正文**（`census-default-gate-20260918T212851.txt:2267-2273`）：

```
AssertionError: 假 npm 根本没被调到 ⇒ 没走到 build 分支:
'… [1/6] preflight: FAIL npm run build 超时（墙钟上限 5s, 已杀 npm 所在进程组）…'
```

⇒ 红在 **被测脚本 `deploy_vault.sh` 自己那个 5 秒预算**上：满负载的 47 分钟长跑里，
假 npm 没能在 5 秒内被调度，脚本的内建超时先动手了。**与本卡无关的两条硬证据**：
① 该次跑的 pytest-timeout 触发次数（C 口径）= **0**，不是 `timeout = 300` 杀的；
② `tests/unit` 不在本卡 hook 的三条目录映射里（`rel.parts[0]` = `unit`），hook 对它是 no-op。
参数 id `[fail-8253]` 是**硬编码**的（`backend/tests/unit/test_deploy_vault_sh.py:2971`
`@pytest.mark.parametrize(("mode","port"), [("fail","8253"),("rc124","8254")])`），
不是随机端口 ⇒ nodeid 稳定，这不是「同一条测试换了个 id」。
**四份存档的对照（这才是归因的依据，不是推理）**：

| 存档 | 代码状态 | 负载 | 该测试 |
|---|---|---|---|
| `evidence-b15/unit-red-baseline-9c4e7e82.txt` | 改前 | 目录级 | **绿**（不在 33 条里） |
| `unit-open-20260918T192142.txt` | **改前** | 目录级 | **绿** |
| `unit-close-20260918T223447.txt` | **改后** | 目录级 | **绿** |
| `census-default-gate-20260918T212851.txt` | 改后 | **47 分钟全量** | **红** |

⇒ 可证的只有这一句：**改前 / 改后的目录级跑都绿，只有全量跑出现这条新增红**。
⚠️ 「所以与本卡无关」这个免责**本卡没有证明**（Codex round-2 MEDIUM）：
超时未触发、hook 对 unit 不打标，这两条只排除了**两种直接机制**；
「全量跑里它与新装的插件或新增用例经由顺序 / 共享状态产生交互」这条解释
**同样符合**这四格记录。**原因未定**，登记 DEBT-3。
⚠️ 但「变量是**负载**」只是其中一种解释，本卡**没有**把它做成对照实验（Codex round-1 MEDIUM）：
目录级与全量之间同时变了**四件事** —— 用例顺序、import 集合、进程内共享状态、以及总时长。
要归因到负载，得固定其余三项只改负载。所以这里只写到可证的那一步：
**它在改前/改后的目录级跑里都绿，只在全量跑里红**。
**处置**：登记为**上下文敏感的不稳定测试** → DEBT-3（与 §四 的已知 flaky 并列）。

### 二.5 收工套件（卡文 §一(i)：nodeid 集只许 `<`）

| 套件 | 开工 | 收工 | nodeid 集 diff | 存档全名（收工） |
|---|---|---|---|---|
| `tests/api` | 269 passed / 红 0 | 269 passed / 红 0 | 空 vs 空，`diff` rc=0 | `api-close-20260918T222032.txt` |
| `tests/skills` | 555 passed / 红 0 | 555 passed / 红 0 | 空 vs 空，`diff` rc=0 | `skills-close-20260918T222104.txt` |
| 契约三文件 | 2 failed / 75 passed | **2 failed / 75 passed** | **完全相同**（2 vs 2，`diff` rc=0） | `contract3-close-20260918T222224.txt` |
| P9-A 的三个门 | — | **243 passed / 红 0** | — | `p9a-guard-20260918T222016.txt` |
| 本卡新门 | — | **5 passed**（收集数 5，format 后） | — | `gate-durations-20260918T221632.txt` |
| `tests/unit` | 32 红（`unit-open-20260918T192142.txt`） | **32 红**，5760 passed，21:20 | **`diff` rc=0 完全相同**；与 b15 基线 33 的唯一差异仍是那条已知 flaky，方向 `<` | `unit-close-20260918T223447.txt` |
| `tests/regression` | 1913 passed / 红 0 | **1913 passed / 红 0**，12:29 | **两侧都是空集**，`diff` rc=0 | `regression-close-20260918T225628.txt` |

#### ⚠️ 契约三文件：nodeid 没变，但其中一条红的**原因**被本卡改变了（如实登记）

`contract3-close-20260918T222224.txt`：

- `:22` 与 `:140` 各一个 `+ Timeout +` 横幅（C 口径 2 ÷ 2 = **1 次超时**）；
- `:221` `| Failed: Timeout (>300.0s) from pytest-timeout.`；
- 被杀的是 `test_health_contract[GET /api/v1/health]` —— 它**本来就是**手册 §零.15 记的
  主干既有 2 红之一，所以红集没变（仍 2 条、同 nodeid）；
- 但**失败原因变了**：改前等价那次（`--override-ini=timeout=0`）它以
  `DeadlineExceeded: Test took 45867.46ms` 收场（`contract3-preequiv-20260918T200525.txt:29`），
  收工这次它跑到 **300 秒被按停**。
- 横幅下面 dump 出的栈顶是 `Stack of Thread-14 (_do_shutdown)`（`:23` 起）——
  与 C-1 那条 `_default_executor.shutdown(wait=True)` **同源**。

⇒ 这是 `timeout = 300` **第一次在非探针的真实用例上动手**，机制按设计生效；
同时它也是本卡对既有行为的一处**真实改变**：那条测试以前会跑到自己结束，现在会被按停。
两种情况下它都是红的、nodeid 相同，故不构成 (i) 的 `>`。**登记 → C1-09**。

## 三 逐条清单

### C-1 `tests/unit` 四条超长 teardown（本次最大的「像挂死」来源）

| nodeid | 阶段 | 耗时 | 存档 + 行号 |
|---|---|---|---|
| `tests/unit/test_study_question_deep_mode.py::test_mode_answer_keeps_top_k_20_and_hard_cap_15` | teardown | **217.38s** | `unit-open-20260918T192142.txt:1006` |
| `tests/unit/test_study_question_deep_mode.py::test_mode_deep_accepted_by_request_model` | teardown | 134.30s | `unit-open-20260918T192142.txt:1007` |
| `tests/unit/test_study_question_deep_mode.py::test_mode_deep_uses_top_k_30_and_hard_cap_20` | teardown | 118.08s | `unit-open-20260918T192142.txt:1008` |
| `tests/unit/test_chat_endpoint.py::test_enrich_context_accepts_user_question_and_mode_answer` | teardown | 55.22s | `unit-open-20260918T192142.txt:1009` |

四条都**通过**（不在 `unit-open-20260918T192142.txt:1031-1064` 的 FAILED 段里），
合计 525.0 秒 ≈ 该次 1013.59 秒（`:1064`）的 51.8%。

- **不是 lifespan**：这四条用的 `authed_client` fixture（`tests/support/authed_client.py:90-120`）
  把 `no_lifespan(app)` 包在 `TestClient` 外面，`app.main` 的 lifespan 是 no-op。
- **等待对象（实测，不是推断）**：拿 `--timeout=30 --timeout-method=signal` 当取证手段跑一遍
  （这两个探针**必然红**，它们不是门），pytest-timeout 在 30 秒处打断并 dump 全部线程栈。
  存档 `census-stackprobe-studyq-20260918T210537.txt`（`8 passed, 3 errors`，3 个 ERROR 正是
  C-1 表里前三条的 **teardown**，`:605-607`）与 `census-stackprobe-chat-20260918T210738.txt`
  （`1 passed, 1 error`）给出**同一条链**：

  1. `tests/support/authed_client.py:115` → `starlette/testclient.py:699` 的 `__exit__`
     → `contextlib` → `anyio/from_thread.py:556` `start_blocking_portal` → **`thread.join()`**
     （`threading.py:1133`）—— 主线程卡在「等 TestClient 的 blocking portal 线程退出」。
     （`census-stackprobe-studyq-20260918T210537.txt:441-455`）
  2. 那个 portal 线程（`Stack of asyncio-portal-…`，`:114-138`）并没有在跑用户代码，它卡在
     `asyncio/runners.py:73` 的 `close()` → `loop.run_until_complete(...)` → `run_forever`
     —— 即**事件循环正在关闭**，而关闭没关完。
  3. 关不完的原因在第三个线程（`Stack of Thread-2 (_do_shutdown)`，`:30-42`）：
     `asyncio/base_events.py:621 _do_shutdown` → `self._default_executor.shutdown(wait=True)`
     → `concurrent/futures/thread.py:273` → **`t.join()`** —— 事件循环的默认线程池
     在等一个 worker 线程跑完。
  4. 那个 worker 在干什么，看同一存档的 `Captured stdout call`：
     `{"event": "Load pretrained SentenceTransformer: BAAI/bge-m3", …}`（全文件命中 6 次）。

  ⇒ **等待对象 = 事件循环关闭时在等一个正在加载 `BAAI/bge-m3` 向量模型的 executor 线程。**
  同时还活着的线程有 `LanceDBBackgroundEventLoop`（`:139` 起，在 `run_forever` 的
  `selector.select`，命中 3 次）与 `Thread-auto_conversion`（`:289`）。
- **处置**：本卡只登记。`timeout = 300` 现在罩得住它们（217 < 300），但余量只有约 1.35 倍
  —— 它们再慢一点会先撞上超时。**修它们 = DEBT-3**（方向：请求结束后别让模型加载吊在
  事件循环的默认线程池上；本卡不改任何断言，也不碰 `backend/app`）。

### C-1b `tests/regression` 距 20 分钟上限只差 25 秒（慢，但不是挂）

- **存档**：`census-regression-20260918T202641.txt`
  - `:220` `1913 passed, 6 skipped, 1 xfailed, 425 warnings in 1143.50s (0:19:03)`
  - `:224` `wall_clock_s=1175.32` · `:225` `rc=0`（`killed=False`，**不是**被外层墙钟砍的）
- **不是挂起**：`Timeout >` 命中 0、`DeadlineExceeded` 命中 0、红 0、W4 `blocked=0`（`:193`）。
- **慢在哪**：没有单点，是**一大片 25-62 秒的用例**摊出来的。最慢一条
  `test_g68_five_view_contract.py::test_two_runs_are_byte_identical` = **62.16s**，
  离 `timeout = 300` 还有 4.8 倍余量。
- **对本卡的意义**：**本次**这个目录的最慢单项 62.16s < 300 ⇒ `timeout = 300` 在这一跑里
  没有、也不可能改变任何一条用例的结果。⚠️ 这是**这一次**的观测，不是「以后也不会」——
  下游若变慢仍可能撞上它（那时它会显示成一条超时红，是预期内的信号）。
  同理 仓根 27 文件最慢 127.53s
  （`census-rootfiles-20260918T202318.txt` durations 段首行）也 < 300。
  这就是为什么本卡把 census 那一跑同时当作「改动前等价」的开工基线是成立的
  —— 另有 `-p no:timeout` 控制组做二次确认（见下）。
- **处置**：登记。它是「默认门 20 分钟目标」最大的单一成本项，怎么提速 = DEBT-2 / DEBT-3。

### C-2 `tests/contract` 的收集期成本（196 条收集要两分钟）

- **文件**：`backend/tests/contract/test_openapi_contract.py:78-85`
- **等待对象**：`schemathesis.openapi.from_asgi("/api/v1/openapi.json", app)` 在**模块 import 期**
  经 ASGI 取一次 schema，并为每个 GET/HEAD operation 生成一条参数化用例。
  该文件 `:18` 还先做过一次 `from app.main import app`。
- **证据**：`contract-collect-20260918T202937.txt:239` = `196 tests collected in 123.57s (0:02:03)`
  （⚠️ 该次与 `tests/regression` 批次并发，123.57s 含争用，是**上界** —— 本卡没有做空闲复测，
  这个数只用来说明「收集不是免费的」，不作为精确基准）
- **影响**：默认门用 `-m "not … not contract"` 能把这 196 条**排除掉执行**，
  但**收集成本照付** —— `-m` 是收集之后才 deselect 的。
- **处置**：登记。真要省掉这两分钟得动 `--ignore=tests/contract` 或改 schemathesis 配置
  （后者 = C1-09，本卡不碰）。

### C-2b **`tests/contract` 目录级「挂死」的元凶就在这一个文件里**（定向实测）

把 `tests/contract` 拆成两个探针各跑一遍，答案没有第二种解释：

| 探针 | 内容 | 结果 | 墙钟 | rc | 存档全名 |
|---|---|---|---|---|---|
| pact 面 | `test_pact_provider.py` + `test_multimodal_pact_interactions.py` | **25 passed, 2 skipped, in 0.55s** | 17.68s | **0** | `census-contract-pact-20260918T212833.txt` |
| schemathesis 面 | `test_openapi_contract.py` 单文件 | **没有总结行**（`grep -cE '^=+ .*(passed\|failed)'` = 0） | **1200.09s，被外层 20 分钟墙钟砍掉**（`# outer_wall_clock_kill: True`） | **124** | `census-contract-schemathesis-20260918T210833.txt` |

- **pact 面 0.55 秒跑完**，其中 2 条 skip 就是 `:298` 那个 skipif 跳过的 provider 验证类，
  W4 `blocked=0`。⇒ 协议 §2.2 :60 说的「pact provider 面等真服务」**不成立**。
- **schemathesis 面在 20 分钟里没跑完**，而且期间 **`timeout = 300` 真的触发过 1 次**
  （C 口径横幅 2 个 = 1 次）。
- ⚠️ **那 300 秒花在哪里 —— 实测更正（Codex round-1 MEDIUM，我原来的写法是错的）**：
  我最初把 contract 的慢笼统归给「W4 端口门下的连接重试」。但超时快照
  （`census-contract-schemathesis-20260918T210833.txt:32-49`）的栈是：
  `backend/app/services/wikilink_graph_service.py:73 _build_sync`
  → `obsidiantools/api.py:503 Vault.connect()` → `:579` → `md_utils.py:239 get_tags`
  → `:329 get_source_text_from_md_file` → `:310 BeautifulSoup(html, 'lxml')`
  → `bs4/__init__.py:476 __init__` → `builder/_lxml.py:494 feed`。
  而该存档全文 **`grep -c '7691'` = 0** —— **一次到现网端口的连接尝试都没有**。
  ⇒ **超时那一刻**，一个 worker 正在**解析 Obsidian vault 的 markdown**
  （obsidiantools 建图 + lxml 解析）。
  ⚠️ 证据只到这里（Codex round-2 MEDIUM）：栈是**那一瞬间**的快照，
  **不能**推出「这 300 秒全部耗在解析上」；`grep -c '7691'` = 0 也只说明
  **已经打印出来的输出**里没有连接尝试 —— 进程是被外层墙钟砍断的，
  捕获的输出未必完整。可证的是：**这个 item 的 setup+call+teardown 合计超过 300 秒，
  且被打断时栈在 markdown 解析里**。
  `blocked=19` 与 `DeadlineExceeded 45.9s` 是**另一个文件**
  （`test_health_contract.py`，见 §五）的事，我原先把两件事混成了一件。
  ⚠️ 同样别读宽：`test_health_contract` 的慢**不能**只归给连接重试 ——
  它那份存档里还有建图、模型加载、executor shutdown 等待（Codex round-2 MEDIUM）。
- ⇒ **`tests/contract` 目录级跑不完，是 `test_openapi_contract.py` 一个文件造成的**
  —— 但**两个 contract 文件慢的原因互不相同**：
  `test_openapi_contract` 慢在 vault 建图 / markdown 解析，
  `test_health_contract` 慢在 lifespan 对受拦端口的健康检查（`blocked=19`）。
- ⚠️ 本条的**证据边界**（别读宽）：一次 item 级 timeout 只能证明
  「**这个 item** 的 setup+call+teardown 合计超过 300 秒」，**不能**推出
  「某一个 HTTP 请求或某一条 hypothesis example 单独超过 300 秒」。
  pact 那半边也只能排除**本次配置下**的 pact 探针，不能反证历史批次或
  provider 真正被执行时的行为。
- **处置**：登记 → **C1-09**（下批 lefthook 卡）。本卡不改 schemathesis 配置、不加
  `--ignore=tests/contract` 到任何既有跑法 —— 默认门用 `-m "not contract"` 已经把它排除出
  **执行**面（收集成本仍在，见 C-2）。

### C-3 `tests/integration` 收集期就有到现网端口的连接尝试（rc=3）

- **存档**：`census-collect-integration-20260918T201549.txt`
  - `:1187` `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=1)`
  - `:1192` `*** live Neo4j port connect attempted —— 1 次拦截无人结账（迟到线程 / collection 期 / 未知线程），进程将以退出码 3 失败 ***`
  - `:1199` `rc=3`
- **等待对象**：`ResolvedIPv6Address(('::1', 7691, 0, 0)) on thread MainThread (owner=<unknown>)`
  —— 现网 Neo4j 端口，`owner=<unknown>` 说明它发生在任何用例的归属区间之外（= 收集期）。
- **收集本身是成功的**：`1139 tests collected in 1.01s`，没有 ERROR 行（`grep -cE '^ERROR ' = 0`）。
  rc=3 完全来自 W4 的「迟到连接不得以 0 收场」。
- **这条直接支撑本卡的一个硬边界**：执行式跑法必须
  `--ignore=tests/integration --ignore=tests/e2e`，**不能只靠 `-m`** —— `-m` 在收集**之后**
  才 deselect，挡不住 import 期的副作用。
- **处置**：登记 → DEBT-3。本卡不修。

### C-4 W4 拦截面（`blocked > 0` 的批次）

| 批次 | blocked | 归属 | 存档 + 行号 |
|---|---|---|---|
| contract 三文件 | **19** | 逐次 lifespan 里的 Neo4j 健康检查（`app/clients/neo4j_client.py:531` / `app/main.py:291` / `app/services/schema_gate.py:92` 的 warning 反复出现）。⚠️ 这 19 次属于**这三个文件**（主要是 `test_health_contract`）；`test_openapi_contract` 单独跑的存档里 `grep -c '7691'` = **0**，两者不要混为一谈 | `contract3-preequiv-20260918T200525.txt:2043` |
| 仓根 27 文件 | 1 | `tests/test_dependencies.py::TestGetCanvasService::test_get_canvas_service_returns_correct_type`（W4 哨兵把它转成 FAILED） | `census-rootfiles-20260918T202318.txt:106` |
| integration（只收集） | 1 | `owner=<unknown>`，收集期 | `census-collect-integration-20260918T201549.txt:1187` |

全部是**已经被拦下**的尝试（fail-closed 生效，没有真连上现网）。**处置：登记 → DEBT-3**，本卡不修。

## 四 单列：已知 flaky（不算挂起）

`tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`

- 依据：`2026-09-15-第十四批复核裁定与待裁决登记.md` §2.7「不稳定测试清单」。
- 本卡实测：它在第十五批基线
  `evidence-b15/unit-red-baseline-9c4e7e82.txt` 里是红的，在本卡开工那次
  `unit-open-20260918T192142.txt` 里**是绿的** —— 基线 33 与开工 32 的唯一差异就是它，
  方向是 `<`（红变绿），按噪声处理。
- **不是挂起**，与 timeout 无关。

## 五 单列：schemathesis 的 `DeadlineExceeded`（并入 C1-09）

- **仓内第一手记录**（不是本卡的推断）：`backend/tests/contract/test_openapi_contract.py:213-214`
  写着「`test_api_contract` 每个 operation 都发真实 HTTP 请求, 在 W4 端口门下每次 **16-19s**
  > `deadline=10000` ⇒ 恒 `DeadlineExceeded`」；同文件 `:124` 记了一次具体读数
  `hypothesis.errors.DeadlineExceeded: Test took 20857.69ms`。
- hypothesis profile：根 conftest `backend/tests/conftest.py:43` 注册 `dev` = `max_examples=20,
  deadline=10000`，`:45` 载入 `dev`。
- **本卡实测（新发现）**：手册 §零.15 记的「主干既有 2 红」里，
  `test_health_contract[GET /api/v1/health]` 那一条**就是这件事**——
  `contract3-preequiv-20260918T200525.txt:29`：
  `hypothesis.errors.DeadlineExceeded: Test took 45867.46ms, which exceeds the deadline of
  10000.00ms`。45.9 秒 / 单条 example，而 deadline 是 10 秒。
  该文件 `test_health_contract.py:16-17` 用的也是 `from_asgi` + `case.call_and_validate()`，
  与 `test_openapi_contract.py:213-214` 自述的「每个 operation 16-19s」同一机制，
  本次读到的是更大的数。
  ⇒ 这条红**不是断言不成立**，是**跑得太慢**。它和「`tests/contract` 为什么久」是同一件事。
- 另一条主干既有红 `test_node_id_patterns::test_pattern_matches_json_schema` 与超时无关：
  `contract3-preequiv-20260918T200525.txt:20` 是
  `FileNotFoundError: … /specs/data/canvas-node.schema.json`（文件不存在）。
- `test_openapi_contract.py` 整文件的实测（`census-contract-schemathesis-20260918T210833.txt`）：
  **20 分钟没跑完**，被外层墙钟砍掉（`# outer_wall_clock_kill: True`、`rc=124`、无总结行），
  期间 `timeout = 300` 触发过 **1 次**（C 口径横幅 2 个）。
  ⇒ 该文件里至少有一条 operation **单条超过 300 秒**，比 `:213-214` 自述的 16-19s 差一个量级。
  ⚠️ 该存档的 W4 汇总行是 **0 次**（不是违规）：进程被砍在半路，
  `pytest_terminal_summary` 根本没跑到。
- **处置**：本卡只登记。改 schemathesis 配置 = **C1-09**（下批 lefthook 卡），本卡不碰。

## 六 协议 §2.2 :60 措辞更正建议

**原文**（`.claude/rules/card-batch-protocol.md` §2.2）：

> `tests/contract` 目录级会在候选树挂起（pact provider 面等真服务；第十三批
> `contract-integ-*.txt` 0 行、第十四批波 0 >10 分钟被中止）

**与实测不符的地方**：pact 那两个文件跑不到需要服务的地方 ——

- `backend/tests/contract/test_pact_provider.py:35-40`：`PACT_DIR` =
  `<仓根>/canvas-progress-tracker/obsidian-plugin/pacts`，而 `ls -d canvas-progress-tracker`
  **不存在**；
- 同文件 `:43`：`PACT_BROKER_URL = os.environ.get("PACT_BROKER_URL", "")` 默认空串；
- 同文件 `:298`：`@pytest.mark.skipif(not PACT_DIR.exists() and not PACT_BROKER_URL, …)`
  —— 两个条件都成立 ⇒ **整个 `TestPactProviderVerification` 类被 skip**，
  永远走不到 `:283` 的 `PROVIDER_URL`（默认 `http://localhost:8000`）。
- `test_multimodal_pact_interactions.py` 只读本目录的 `pacts/*.json` 做结构断言
  （`grep -n -e 'Consumer' -e 'start_service'` → 0），不起任何服务。

**本卡实测（把两边分开各跑一遍，见 C-2b）**：

- pact 面单跑：**25 passed, 2 skipped, in 0.55s**，wall 17.68s，rc=**0**，W4 `blocked=0`
  （`census-contract-pact-20260918T212833.txt`）。
- schemathesis 面单跑：**20 分钟没跑完**，被外层墙钟砍掉，rc=**124**，无总结行，
  期间 `timeout = 300` 触发过 **1 次**（`census-contract-schemathesis-20260918T210833.txt`）。

**建议改成**（按本卡证据）：

> `tests/contract` 目录级跑不完，元凶是 **`test_openapi_contract.py` 一个文件**，与 pact 无关：
> ① 收集期 `:78-85` 的 `from_asgi` 要为每个 GET/HEAD operation 生成参数化
>    （本卡实测：整个 `tests/contract` 收集 196 条要 ~2 分钟）；
> ② 执行期每个 operation 发真实 HTTP 请求，在 W4 端口门下该文件 `:213-214` 自述
>    「每次 16-19s」，而本卡实测**至少有一条单条超过 300 秒**（ini `timeout=300` 触发），
>    整文件 20 分钟仍未跑完。
> pact 两个文件实测 **0.55 秒跑完**（`PACT_DIR` 不存在且 `PACT_BROKER_URL` 为空 ⇒ `:298`
> 的 skipif 把 provider 验证类整类 skip），**不是原因**。

## 七 本清单没有覆盖什么

1. **没有跑 `tests/integration` / `tests/e2e` 的执行面** —— 只做了收集。它们在 W4 下
   是 advisory（只记不拦），执行会真连现网，本卡硬边界禁止。
2. **没有覆盖 xdist（`-n`）下的行为** —— DEBT-2 的面。
3. **没有覆盖 CI 环境** —— DEBT-4 的面；CI 的 venv 没装 `pytest-timeout`。
4. **没有证明 `signal` 方法能中断所有 C 级阻塞** —— 只证明了它能中断本次实测到的那些等待。

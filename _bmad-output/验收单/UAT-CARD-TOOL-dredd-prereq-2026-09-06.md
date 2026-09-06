# UAT — CARD-TOOL-dredd-prereq

> 批次 `[BATCH-2026-09-05-第十二批 / CARD-TOOL-dredd-prereq]` · 车道 `card-y5-review`（分支 `card/y5-review`）
> 开工基线 HEAD `67ee147c`（Y5-C / CARD-TOOL-openapi-R2 末 commit，工作树干净）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y5-D.md` · 协议 `.claude/rules/card-batch-protocol.md`
> 裁判原始输出全部落盘 `_bmad-output/审查/evidence-dredd-prereq/`；本文只引用路径与判据行，不自述数字（协议 §2.2）。
> **本卡零代码改动**：`.github/workflows/**`、`backend/tests/conftest.py`、`backend/app/**`、`scripts/spec-tools/dredd-hooks.js`、`backend/tests/support/live_port_guard.py` 全部未动。

---

## 一 本卡做了什么

Z7-C（`CARD-TOOL-dredd-decide`）已裁「Dredd 退役 + schemathesis 接 CI」，但留下两个前置**都没解**：

- **前置一（耗时）**：「重复 lifespan 的机制已确认，耗时瓶颈尚未定位」——单次 7.1s 解释不了 20–50s。
- **前置二（门）**：合约测试在 W4 live-port 门下必红，探针实测 `blocked=19`。

本卡**只出证据与判据，不改任何 CI / 生产代码**，做了四件：

1. **分段 profile**（完成条件 a）：写一个临时 pytest 探针，固定 `GET /api/v1/health`、同一 ASGI transport，
   把一次 `case.call()` 拆成六段（客户端构造 / `__enter__` / before_call hooks / 序列化 / 请求 / `__exit__`），
   每段 ≥5 样本，各段之和与整次墙钟对账。跑完探针**已从工作树删除**，源码原样存档 `evidence-dredd-prereq/profile_harness.py`。
2. **门下跑**（完成条件 b）：不挂豁免 marker、不设 `W4_GUARD_NO_EXEMPT`、不改豁免面，如实记退出码与门计数。
3. **一页判据文档**（完成条件 c/d）：`_bmad-output/审查/2026-09-06-Dredd-schemathesis-接CI可行性判据与成本.md` ——
   分段表 + 门侧三问逐条 `file:line` + 4 条接 CI 达标判据 + 成本清单 + 口径边界。
4. **卡文之外自加的两个对照组**（不做就答不完整，也答不准）：
   - **对照组-A**（与主用例同进程）：把 lifespan 换成 no-op，把完成条件 c② 里那条「其它」路径从**推理**变成**实测**；
   - **对照组-B**（**干净进程**单跑）：Codex round-1 HIGH-2 指出 A 复用了跑过 5 次 lifespan 的同一个 app 单例、
     不能称「没启动的 app」——补这一轮把「进程新鲜度」这一维补上。

---

## 二 完成条件逐条对账

| 条 | 要求 | 状态 | 证据 |
|---|---|---|---|
| (a) | 分段 profile，每段 ≥5 样本 + 中位数/极差 + 各段和与墙钟对账 | ✅ | `evidence-dredd-prereq/profile-20260906T103504.txt:516-569`（run-1）、`profile-both-20260906T104054.txt:516-570`（run-2）；判据页 §1.2 |
| (a) | 必答「20–50s 里 7.1s 之外是什么」 | ✅ 已答（段级 + 对照组把 lifespan 从包装区间里分离出来），段内归因如实标为采样证据 | 判据页 §二 |
| (a) | 探针源码存档 + 跑完删除 | ✅ ⚠️ **两轮不同源，已如实登记** | `evidence-dredd-prereq/profile_harness.py`；sha 存档 `harness-sha256-20260906T104022.txt`（只与 run-2 / 对照组-B 同源）；判据页 §1.0；裁判 7a 已证探针不存在 |
| (b) | 门下跑，记门计数行与 rc | ✅ **rc=1 不是卡文预期的 3**，已给机制 | 判据页 §三；两份存档末行 `rc=1` |
| (c) | 门侧三问逐条 `file:line` | ✅ | 判据页 §四①②③ |
| (d) | 一页判据文档，标注 208.70s 口径，禁 ×206 外推，禁「根因已定位」 | ✅ | 判据页；裁判 6 两条 grep 在**整改后**复跑仍 = 0 |
| (e) | 零改动面 + `contract-test` 维持 `if: false` + 临时文件不入 commit | ✅ | 裁判 4（diff 空）、`api-spec-sync.yml:330`、裁判 7a |
| (f) | 实验产物跑前跑后 `ls` + `shasum` + `git check-ignore` | ✅ **三条跑前全不存在、跑后全被创建**，均 gitignored | 判据页 §三末表 |
| (g) | Codex 一轮五分节 | ✅ | `_bmad-output/审查/codex-review-CARD-TOOL-dredd-prereq.md`（首部按协议 §2.1）；处置见 §五 |
| (h) | 「本卡未证明什么」+「台账待登记条目」 | ✅ | §六 / §八 |

---

## 三 裁判 1–7 原始输出引用

| # | 裁判 | 结果 | 存档 |
|---|---|---|---|
| 1 | `--collect-only -q` 选中数 | `2 tests collected in 0.06s`（主用例 + 对照组），rc=0 | `collect-only-20260906T104022.txt`（另有 run-1 前的 `collect-only-20260906T103437.txt` = `1 test collected`，是两轮不同源的独立证据） |
| 2 | 分段 profile（`-s`，门下） | 每段 5 样本 + 中位数/极差 + 墙钟 + 门计数行；rc=1 | `profile-20260906T103504.txt`（run-1）、`profile-both-20260906T104054.txt`（run-2 + 对照组-A），末行 `rc=1` |
| 2′ | 对照组-B（干净进程，`-k no_lifespan_control`） | `1 passed, 1 deselected … in 1.03s`；`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`；rc=**0** | `control-fresh-process-20260906T105637.txt` 末 4 行 |
| 3 | 实验产物对账 | 跑前三条 ABSENT；跑后三条被创建；`git check-ignore -v` 三行均命中 | 判据页 §三末表（含 shasum） |
| 4 | 零改动面 | `git diff --stat 67ee147c HEAD -- .github/ backend/tests/conftest.py backend/app/ scripts/spec-tools/dredd-hooks.js backend/tests/support/live_port_guard.py` → **空输出**；`grep -n 'if: false' .github/workflows/api-spec-sync.yml` → `330:` | 见本节末注 |
| 5 | 门锚 | `grep -n 'status = 3' backend/tests/conftest.py` → `200:` 与 `202:`；`grep -n '^EXEMPT_MARKERS\|^EXEMPT_PATH_PREFIXES\|^def is_exempt' backend/tests/support/live_port_guard.py` → `157:` / `164:` / `1061:` | 判据页逐行引用 |
| 6 | 措辞门 | `grep -c '×206\|x206\|\* 206'` = **0**；`grep -c '根因已定位'` = **0**（送审前、整改后各跑一次，均 0） | 判据页 |
| 7 | 收工干净 | 临时探针不存在；`git status --porcelain \| grep -v '^??'` 为空；`evidence-dredd-prereq/` 含 `profile_harness.py` + 4 份带时间戳原始输出；`git ls-files --cached \| grep -c '\.stderr'` = 0 | — |

> 裁判 4/5/6/7 是即时 grep/diff，输出短且在本文逐字抄录，未单独落盘（协议 §2.2 要求落盘的是**承重长跑**裁判，即裁判 1/2/2′）。

---

## 四 三个最硬的数字（判据页 §一 / §三）

1. **分段对账残差在毫秒量级**：run-2 五轮的「整次墙钟 − 六段之和」= 0.001099 / 0.000343 / 0.000199 / 0.000193 / 0.000245 秒。
   ⚠️ 残差小是**补充旁证**，不是「同时排除漏计与重复计」的独立证明（Codex MEDIUM-1，已改）；串行性由读源码得出。
2. **退出段与进入段同量级，且 Z7-C 的表里没有它**：`__exit__` 整体中位 12.256s（run-2）/ 12.638s（run-1）。
3. **对照组把 lifespan 从包装区间里分离出来，并一次翻转两个前置**：同一探针、同一边界，
   lifespan 换 no-op 后进入段中位 0.001s（干净进程 0.000s）、退出段中位 0.001s（干净进程 0.000s）
   ⇒ 进入/退出段里非 lifespan 的部分在毫秒量级。
   干净进程单跑：单次调用中位 0.003s、整 session `blocked=0`、rc=**0**、1.03s 跑完。

---

## 五 Codex 一轮（`gpt-6-astra` · `ultra`）

存档：`_bmad-output/审查/codex-review-CARD-TOOL-dredd-prereq.md`（首部按协议 §2.1，含 `codex-cli 0.153.3` / `model: gpt-6-astra` / `sandbox: read-only` 自证）。
审查绑定：`67ee147c`（本卡零代码改动，代码树与该 SHA 一致；被审对象是 `_bmad-output/` 下的判据页与测量存档，送审版 sha256 `c8f75787…8a55`）。

**结果：BLOCKER 0 / HIGH 2 / MEDIUM 8 / LOW 3。末行「BLOCKER/HIGH 清零：否」。**
Codex 自述「已核对指定行号，**未发现纯行号错位**；问题主要是措辞超出对应代码或测量的支持范围」。

### 5.1 逐条处置（13 条，**全部采信，无驳回**）

| 条 | 指出的问题 | 处置 |
|---|---|---|
| **HIGH-1** | ①④ 计时的是 `TestClient.__enter__/__exit__` 包装区间（含 portal 建/收），不能直接称「纯 app lifespan」；③ 也含应用处理 | **采信**。判据页 §1.1 新增「探针实际计时的是什么」一栏并加警示；§〇/§二 改口径。**并补证据**：用对照组把非 lifespan 余量量出来（毫秒量级），使「其余是 lifespan」成为同 harness 内的减法而非断言 |
| **HIGH-2** | 对照组只跳过后续 lifespan，未证明被测 app 是「从未启动」；它复用跑过 5 次 lifespan 的同一进程单例 | **采信**。判据页 §1.3 明写对照组-A 的两条限制；**并补实验**：新增对照组-B（干净进程 `-k` 单跑，整 session `blocked=0`、rc=0）。「启动期装配的对象不存在」这句已删，改为陈述 `no_lifespan` 只替换 `lifespan_context` 这一事实 |
| **MEDIUM-1** | 小残差不能独立排除漏计与重复计（可互相抵消） | **采信**。改为「串行性由源码顺序读出，残差是补充旁证」，并限定只覆盖当前固定成功路径 |
| **MEDIUM-2** | 采样标签可能错桶；app 帧占比 ≠ 墙钟占比；0.2s 是休眠间隔不是误差上界 | **采信**。§二 新增三条限制（错桶 / 线程共用标签 / 条件分母），删除全部墙钟份额暗示，误差上界写「未给出」 |
| **MEDIUM-3** | shutdown 的任务归属与模型装载**完成**次数未闭合 | **采信**。改为「每轮**观察到**两条装载日志」；「是那个 `create_task` 在阻塞退出」明标为推断未证明；「线索不是结论」覆盖整条归因 |
| **MEDIUM-4** | 存档脚本的 6 位小数格式产不出 run-1 的 3 位小数输出 ⇒ 逐字节同源声明需收窄 | **采信**（这是真的：run-1 用的是更早一版）。判据页新增 §1.0，列出三处差异 + 独立证据（两份 collect-only 的 `1 test` vs `2 tests`），承重数字改以 run-2 / 对照组-B 为准 |
| **MEDIUM-5** | 不能跨轮反推旧 7.1s 的组成；且探针的 `from_asgi` 计时**还含 operation 查找** | **采信**（后半是我探针的事实错误）。整条减法**已撤回**；§1.2 该行改名为「`from_asgi` + operation 查找」；「shutdown 从来没被量过」改为「Z7-C 表里没有这一项」 |
| **MEDIUM-6** | 门立即抛不排除调用方重试；「mock 几乎无收益」未测 | **采信**。§三 加「只证明门自己不等待，调用方成本未测」；§四② (a) 行的效果两列改「未测」 |
| **MEDIUM-7** | 仍有跨 operation / 未实施方案的文字外推；且「乘起来会重复计一次性成本」这个理由对本卡的单次数字不成立 | **采信**。删「每 operation ~9ms」「边际成本从 31.6s 降到 9ms」「11 → 2~3」；§6.1 重写外推禁止的**理由** |
| **MEDIUM-8** | 豁免只证明不抛拦截，不证明连接建立/写入成功；且裸线程永不豁免 | **采信**。§四①③ 改为「连接尝试得以继续 ≠ 一定建立成功」，写路径的两个前置条件 `if … is not None:` 写明，并补裸线程 `<unknown>` 永不豁免的例外 |
| **LOW-1** | 「30–37s」漏了 run-1 的 min 23.117s；「全部」过强 | **采信**。全体区间统一改 **23.117–37.045s**；「全部」改「绝大部分」 |
| **LOW-2** | 中位数不能相加，「合计中位 9ms」不可核实 | **采信**。删除合计说法，只报 request 段中位 9ms，并注明 `0.000s` 是舍入显示值 |
| **LOW-3** | 探针只包了模块级 `after_call` dispatch，`schema.hooks.dispatch`（`case.py:413-414`）未包 | **采信**。§1.2 新增「未归类的构成」段，≤9µs 限定到被包的那个 global dispatch |

### 5.2 送审后改动登记（失绑 / 未复审）

1. **送审期间的两处措辞收紧**（Codex 仍在推理时我改的，均**只收窄不放宽**）：
   §二 第 1 条关于 7.1s 的表述、第 2 条关于「只覆盖 startup」的表述。Codex 读到的是哪一版无法确定。
2. **整改版是审后重写**：判据页从送审版 sha256 `c8f75787…8a55` 改到当前版本，13 条全部落地。
   **按协议 §1 登记「整改未复审」**——整改后的措辞未再送 Codex（本卡轮次 = 1 轮）。
3. **对照组-B 是审后新增的实验**（`control-fresh-process-20260906T105637.txt`，产生于 Codex 仍在跑时）。
   它用的是与 run-2 **同一个** sha（`70378e38…fce1`）的探针，跑法是 `-k no_lifespan_control`。
   该轮结果未经 Codex 复核。

---

## 六 DoD-3

### 4-A Claude 已代验

- ✅ **收集面**：`--collect-only -q` → `2 tests collected`，rc=0（`collect-only-20260906T104022.txt`）。
- ✅ **分段 profile 跑通两轮**：run-1 `1 failed … in 168.89s`、run-2 `1 failed, 1 passed … in 160.98s`，
  每段 5 样本，对账残差 0.000193–0.001099s（run-2）。
- ✅ **门下跑口径如实**：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=11 (blocked=11, advisory=0, unaccounted=0)`，
  rc=**1**（不是卡文预期的 3；机制写在判据页 §三，引 `conftest.py:197-204`）。
- ✅ **对照组-B（干净进程）**：`1 passed, 1 deselected … in 1.03s`，整 session `blocked=0`，rc=**0**。
- ✅ **零改动面**：`git diff --stat` 五个路径全空；`api-spec-sync.yml:330` 仍是 `if: false`。
- ✅ **临时探针已删**：`test ! -e backend/tests/contract/test_zz_dredd_prereq_profile.py` 通过；
  `git status --porcelain | grep -v '^??'` 为空。
- ✅ **探针与产出同源（限定范围）**：存档副本与 run-2 / 对照组-B 的工作树版本 sha256 均为 `70378e38…fce1`；
  **run-1 用的是更早一版，已在判据页 §1.0 登记差异**。
- ✅ **实验产物**：三条路径跑前全不存在、跑后全被创建，`git check-ignore -v` 三行均命中，`git status` 不含它们。
- ✅ **措辞门**：判据页 `grep -c '×206\|x206\|\* 206'` = 0、`grep -c '根因已定位'` = 0（送审前 / 整改后各跑一次）。
- ✅ **未连真库**：11 次到 `::1:7691` 的连接尝试**全部被门拦下**（`blocked=11, advisory=0`），无一建立；live vault 只读。
- ✅ **Codex prompt 合规**：协议 §2 禁用词 4 项 + `gpt-5.6` 计数全 0，五分节齐备，末行判据在位；存档首部按协议 §2.1。
- ✅ **Codex 13 条全部采信并落地**，逐条处置见 §五.1；整改未复审已登记。

### 4-B 你来验

**无变化。**

这张卡什么都没改。它只做了一件事：把「那个自动检查为什么慢、为什么在保护罩下必然报错」量清楚，写成一页判断标准。

具体说：

1. 有一个自动检查，用来核对「系统给出的数据长相」和「说明书上写的长相」是不是一致。它现在是**关着的**，
   之前有人发现它慢得没法用。这次我们把它慢在哪里量出来了：慢的不是这个检查本身，是它每核对一条，
   就要把整套系统**从头启动一遍、再关一遍**——而这台机器上启动一遍要十几二十秒、关一遍也要十几秒。
   检查自己那部分只花千分之九秒。
2. 还有一层保护罩，专门拦「测试偷偷去连你正在用的那份资料库」。这个自动检查一启动系统就会去连，
   所以每次都会被拦下来、被判失败。这次我们确认了：**这是两件独立的事**——就算把慢的问题解决了，
   保护罩这一关照样过不去。
3. 我们试了一个办法：让它「不要真的启动整套系统，只借用它的地址簿」。试出来的结果是，两个问题**同时**没了。
   但这个办法有代价，代价也写进那一页了：这样测的就不是「跑起来的系统」，而是「没跑起来的系统」，
   那还算不算数，得下一张卡去验。

所以：你不需要点开任何页面、不需要做任何操作，界面上也不会有任何差别。
这一页是给下一次「要不要把这个检查打开」那个决定用的。

---

## 七 本卡未证明什么

> 与判据页 §6.2 同源（14 条），此处列要点。

1. **不证明进入段/退出段等于「纯 app lifespan」**——它们是 `TestClient.__enter__/__exit__` 的整体；
   lifespan 的占比由对照组减法给出（非 lifespan 余量在毫秒量级），不是直接测量。
2. **不证明启动过程内部每一步各花多少秒**；「主项是 wikilink 图 eager-build」是采样证据，
   受错桶 / 线程共用标签 / 条件分母三条限制，**不能换算成墙钟份额**，误差上界未给出。
3. **不证明退出段那个后台任务的身份与等待关系**；模型装载**完成**次数、TLS 对端均未确认。
4. **不证明「各段之和 ≈ 墙钟」能独立排除漏计与重复计**；串行性由读源码得出，残差只是补充旁证。
5. **不证明残差里剩下的是哪几行**（`case.py:413-414` 的 `schema.hooks.dispatch` 未被探针包住）。
6. **不证明两轮由同一字节版本的探针产出**（run-1 更早一版，见判据页 §1.0）。
7. **不反推 Z7-C 那个 7.1s 的组成，也不主张它测错了**；本卡没测 `import app.main`，
   `from_asgi` 那个数还含 operation 查找。
8. **不证明「只屏蔽连接后耗时会怎样」**；门自身立即抛出，但调用方的重试 / 退避成本未测。
9. **不证明豁免后连接会成功建立、DDL / 写调用会真的执行**——那是读代码得出的风险判断，本卡没有放行过任何连接。
10. **不证明 `no_lifespan` 下其余 205 个 operation 的响应仍与 schema 相符**（判据 C 未测）。
11. **不证明 CI 机器上的数字**（本机 3.14.4 vs CI 3.11/3.12，未控制）。
12. **不证明 rc 在别的配置下也是 1**（`conftest.py:199-200` 那条在本卡运行里从未触发）。
13. **不证明本探针与生产用例逐字等价**（三处已声明差异写在 `profile_harness.py` docstring）。
14. **不裁 Dredd 去留**（Z7-C 已裁乙），**不改 CI**，**不改** `conftest.py` / 豁免面 / `backend/app/**` /
    `dredd-hooks.js` / `live_port_guard.py`。
15. **整改后的判据页措辞未经复审**（§五.2），**对照组-B 未经复核**。

---

## 八 台账待登记条目

> 台账只由主 session 写（协议 §5）。以下为本卡请求登记的条目。

1. **Z7-C 前置一（耗时瓶颈未定位）→ 段级已定位，残差毫秒量级**：单次 `case.call()` 中位 31.636s（run-2）/ 35.630s（run-1），
   十样本区间 23.117–37.045s；其中 `__enter__` 整体中位 19.082s / 23.016s、`__exit__` 整体中位 12.256s / 12.638s、
   request 段中位 9ms、未归类 0.000193–0.001099s。**lifespan 在那两段里的占比由对照组减法给出**
   （非 lifespan 余量在毫秒量级），不是直接测量。段内归因是采样证据，未做步骤级计时。
2. **Z7-C 前置二（门下 exit 3）→ 口径更正为「非零，本卡观测形态是 1」**：实测 rc=**1**（结账哨兵判红），不是 3。
   `conftest.py:201-202` 的 `status = 3` 只在「哨兵翻红被吃掉」的残余形态下出现；`:199-200` 那条本卡从未触发。
   **结论不变**（非零即 CI 红）。
3. **新证据：`no_lifespan` 同时翻转两个前置**（实测，含**干净进程**一轮）：
   干净进程单跑 `1 passed, 1 deselected … in 1.03s`、整 session `blocked=0`、rc=0、单次调用中位 0.003s。
   代价转移到「被测对象等价性」（判据 C），只测了 1 个 operation，未测其余 205 个。
4. **判据页路径**：`_bmad-output/审查/2026-09-06-Dredd-schemathesis-接CI可行性判据与成本.md`
   （含 4 条达标判据 A/B/C/D 与成本清单）。
5. **blocked 计数**：`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=11 (blocked=11, advisory=0, unaccounted=0)`，
   全部到 `::1:7691`，分布 `[3,2,2,2,2]`（每次 lifespan 2–3 次），无一建立。
6. **Z7-C 数字的处置**：本卡**未复现**其 7.1s，也**不反推**其组成（此前写过的「主项是模块导入」那条减法已撤回）；
   本卡只主张「本机这条链路上进入段是 19–23s」。另：Z7-C 计时表里**没有**退出段这一项。
7. **副作用登记**：跑一次这个合约测试会在工作树落三个文件（`backend/data/llm_call_logs.db`、
   `backend/data/neo4j_memory.json`、`backend/app/data/vault_index_pending__canvas_vault.jsonl`），
   三条均 gitignored，跑前均不存在。
8. **本卡零代码改动**，`contract-test` job 维持 `.github/workflows/api-spec-sync.yml:330` 的 `if: false`。
9. **⛔ 整改未复审**：Codex round-1 的 13 条（0B/2H/8M/3L）全部采信并落地，但整改后的判据页措辞
   **未再送审**（本卡轮次 = 1 轮）；送审期间还有两处措辞收紧、审后新增了对照组-B，均见 §五.2。
10. **移交建议（不占本卡范围）**：判据 C 需要一次「启动态 vs 未启动态」的全 operation 对照跑；
    启动态那一半在本机跑不成（门会判红），需先解决判据 B 或在 CI 镜像上跑。

---

## 九 批注区

> [!question]+ 你的提问
>

> [!error]+ 你发现的问题
>

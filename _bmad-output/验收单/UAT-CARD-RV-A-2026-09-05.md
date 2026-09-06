# UAT — CARD-RV-A：Z1-A / Z4-A / Z4-B 审后 diff 复审

> 批次: `BATCH-2026-09-05-第十二批` · 车道 `Y5`（`card-y5-review`，分支 `card/y5-review`）
> 基线 HEAD: `03ac8bf8de4acd164d51c92db001ae42ada14a73`（开工与收工同一 SHA）
> 日期: 2026-09-05 · 性质: **只读复审卡，零代码/测试改动**（commit 只含 `_bmad-output/`）
> 卡文: `_bmad-output/implementation-artifacts/goal-cards/第十二批-goals/Y5-A.md`
> 协议: `.claude/rules/card-batch-protocol.md`（§1 合并门与 pathspec / §2 Codex 命令与措辞 / §2.1 存档首部 / §2.2 裁判落盘）

---

## §0 环境与绑定核对（第 0 分钟）

| 项 | 实测 |
|---|---|
| pwd | `/Users/…/.claude/worktrees/card-y5-review` |
| 分支 | `card/y5-review` |
| HEAD | `03ac8bf8de4acd164d51c92db001ae42ada14a73` |
| 工作树 | 干净（`git status --porcelain` 空） |
| venv | `backend/.venv` → `card-v5-lance/backend/.venv`（目录级 symlink，在位） |
| `backend/.env` | 在位 |
| codex | `codex-cli 0.153.3`（`/opt/homebrew/bin/codex --version` 实测） |

**三面与 HEAD 的绑定**（卡文〇 事实逐条复验，全部成立）：

- `git diff --stat 8e8fd737 HEAD -- backend/tests/unit/test_review_app.py backend/app/api/v1/endpoints/review_app.py` → 空（逐字节相同）
- `git diff --stat d9f7b544 8e8fd737 -- backend/app/api/v1/endpoints/review_app.py` → 空（Z1 面生产文件零改动，作者自述属实）
- `git show HEAD:backend/app/api/v1/endpoints/review_app.py | wc -l` → 550；`27e61454` 版 → 543
- 轮询符号 `computePollDelayMs` / `visibilityAction` / `visibilitychange` / `nextpoll` 命中数：`27e61454` = 11，HEAD = 11（**同数** → 负控换版后不会因符号缺失而崩，负控结果非预设）

---

## §1 裁判 1-10 原始输出

全部承重裁判按协议 §2.2 落盘至 `_bmad-output/审查/evidence-rv-a/`，文件名含时间戳，末行 `rc=`。本节只引用路径与末行，不自述数字。

| # | 裁判 | 期望 | 实测 | 落盘 |
|---|---|---|---|---|
| 1 | `git diff --stat d9f7b544 8e8fd737 -- backend/tests/unit/test_review_app.py` | 1 file, +161/-12 | **`1 file changed, 161 insertions(+), 12 deletions(-)`** ✅ | `j1-j3-diffstat-*.txt` |
| 1b | 同上换 `-- . ':(exclude)_bmad-output'` | 同一行 | **同一行** ✅（面上确无其它文件） | 同上 |
| 2 | `git diff --stat 304f03ca 7283a8df -- . ':(exclude)_bmad-output'` | 5 files, +298/-66 | **`5 files changed, 298 insertions(+), 66 deletions(-)`** ✅ | 同上 |
| 3 | `git diff --stat a5e0ce79 c8611a89 -- . ':(exclude)_bmad-output'` | 4 files, +22/-9 | **`4 files changed, 22 insertions(+), 9 deletions(-)`** ✅ | 同上 |
| 4 | 基线 `pytest …::test_js_poll_contract_wiring_g63` | 1 passed | **`1 passed, 10 warnings in 0.78s`** rc=0；`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` | `j4-baseline-g63-*.txt` |
| 5 | 负控：换入 `27e61454` 版跑同一 nodeid | 如实记 | **`1 passed`** rc=0（四断言全绿）→ 触发卡文 (b) 分支，见 §2 | `b-negctrl-27e61454-*.txt` + `b-negctrl-sha-*.txt` |
| 6 | `pytest tests/unit/test_review_app.py`（单文件，不设期望） | 记实测 | **`88 passed, 10 warnings in 3.36s`** rc=0；门计数 0/0/0 | `j6-test_review_app-full-*.txt` |
| 7 | Z4-A 五文件**显式路径**（非目录级） | 记 passed/failed + 门计数 | **`104 passed, 10 warnings in 1.88s`** rc=0；`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)` | `j7-z4a-five-files-*.txt` |
| 8 | `check-openapi-drift.py --snapshot openapi.json` | `DRIFT: none (paths=193 schemas=353)` | **`DRIFT: none (paths=193 schemas=353)`** rc=0 ✅ 逐字对上 | `j8-openapi-drift-*.txt` |
| 9 | Z4-A 两口径 diff 哈希 | 原样抄 | 见 §4（三口径一致 `eb3ed96d…`） | `j9-z4a-hashes-*.txt` |
| 10 | 零代码改动 | 空 / 0 | 见 §8 收尾核对 | — |

> 裁判 7 的 **104 passed** 与存档 B（`codex-review-CARD-REDBASE-R1-round2.md` 末段）记录的「104 passed」逐字一致 —— 这条独立佐证了 Z4-A 五文件的**行为面**自 round-2 起未变。
> 裁判 6 实测 88 passed；卡文提到的「HEAD 40 个 `def test_`」是**函数定义数**，与收集到的用例数（含类方法与参数化）不是同一口径，本卡不把二者互推（沿用「计数判据把函数定义数成一条数据」的既往教训）。

---

## §2 (b) Z1 专项负控 —— 四条断言能不能红

### 2.1 操作规程与自证（卡文 (b) 逐条）

- 换入源：`git show 27e61454:backend/app/api/v1/endpoints/review_app.py > <scratch>/review_app.27e61454.py`
- 还原手段：**只用 `cp`**，未使用任何 git 工作树回退命令；**未使用 stash**（stash 栈跨 worktree 共享）
- trap：`trap '…' EXIT INT TERM`（在卡文要求的 EXIT 之外加挂 INT/TERM —— SIGTERM 不做栈展开，只挂 EXIT 时被中断会留下变异体）
- 三段 sha 落盘：`b-negctrl-sha-*.txt` / `b-mutation-sha-*.txt` / `b-mutation-234-*.txt`

| sha 段 | 值 |
|---|---|
| HEAD 版（换入前 / 备份件 / 最终还原后，三处相同） | `b7e4a8d94f82b1a6a8e9b07ff636690801d5d1b53c071d21273562def1224a77` |
| `27e61454` 版（换入源 / 换入后，两处相同） | `4ff348f19d6082908ca19aa66f2016292a611a58233dd2bdccc5d74a9e432b73` |

**⚠️ 如实登记一次操作失误（本卡自己踩的坑，已修正）**：第一次负控的 trap 里写的是**相对路径**，而命令体中途 `cd backend` 跑 pytest，EXIT 时 cwd 已变 → `cp: backend/app/…/review_app.py: No such file or directory`，**自动还原失效**，工作树里留下了 `27e61454` 版。发现后立即以绝对路径手工 `cp` 还原，并复验 sha 与 `git status`。其后所有变异的 trap 一律用绝对路径，还原全部生效（每条变异的「还原后 sha」都等于基线）。教训已列入 §10 台账待登记条目。

### 2.2 负控 1：换入 `27e61454` 版（四断言全绿）

```text
1 passed, 10 warnings in 0.75s
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
rc=0
```

**判读（按卡文 (b) 的措辞要求）**：该负控**只证明**「四条断言不依赖 `92734207` 之后落在 `review_app.py` 上的那 17 行生产改动」，**不证明它们能红**。两版之间 `review_app.py` 为 `+17/-10`，且四个轮询符号命中数两版同为 11 —— 换版不会因符号缺失而崩，所以「全绿」是真结果而非崩溃掩盖。

### 2.3 负控 2：四条独立临时变异（卡文 (b) 只要求 ①，本卡补齐 ②③④）

卡文 (b) 规定「若四断言在 27e61454 上也全绿 → 补一条临时变异看 ① 是否红」。① 已按要求做；因 Codex §三 问题 ① 问的是**四条**断言是否承重，只证 ① 不足以回答，故补做 ②③④。四条变异串行、各自从干净基线出发、跑完无条件还原。

| 变异（施加于 `review_app.py`） | 变异生效自证 | 变红的断言 | 失败身份（该断言自己的 assert 消息） | 其余三条 |
|---|---|---|---|---|
| `POLL_MIN_MS` 5000→2000（`:159`） | sha `b818f9a8…` ≠ 基线；`grep` 实证变异行 | **①** | `AssertionError [ERR_ASSERTION]: 下限没生效 = 会按 2 秒打后端` | 未逐条记录 |
| `POLL_MAX_MS` 60000→30000（`:160`） | sha `eb7730d1…` ≠ 基线 | **②** | `上限没生效 = 一小时不问后端` | ①③④ 全 ✔ |
| `visibilityAction` 回前台分支 `pollNow: true`→`false`（`:214`） | sha `ec249e63…` ≠ 基线 | **③** | `回前台必须立即拉一轮 (pollNow 的接线端)` | ①②④ 全 ✔ |
| `poll()` 内注入一次 `fetch(URLS.refresh, {method:"POST", …})`（`:439`） | sha `0920646d…` ≠ 基线 | **④** | `Expected values to be strictly equal` | ①②③ 全 ✔ |

**结论**：四条断言**各自承重，且互不遮蔽** —— 每条变异只杀一条断言，失败身份都是该断言自身的断言消息（不是崩溃、不是别的异常、不是被更早的防线拦下）。这满足「判据必须绑定被哪一层拒的」这条既往教训。

**本条负控**没有**证明的**（如实）：

- ① 的那次变异未逐条记录 ②③④ 的绿/红（首轮只筛了失败行）；②③④ 三轮均完整记录，故「互不遮蔽」这一结论的证据基础是后三轮。
- 变异只覆盖了四条断言各自最直接的一个常量/分支。**没有**排除「某条断言实际测的范围比它的名字更窄」——例如 ④ 数的是沙箱 fetch 收到的 POST 次数，能抓住经 `fetch` 发出的 POST，抓不住走别的传输方式的写请求。该问题已作为 Codex §三 问题 ① 的追问送审。
- 全部变异都是**临时**的，跑完还原至逐字节相同；本卡零代码改动（见 §8）。

---

## §3 (a) 三份逐条定性表

三态定义：**Codex 未见** = 该处落在既有存档绑定区间之外 / **已见且成立** = 是对存档某条意见的回应且回应成立 / **已见但整改引入新问题**。

### 3-A. Z1 面（`d9f7b544` → `8e8fd737`，6 hunk，全部在 `backend/tests/unit/test_review_app.py`）

存档 A = `codex-review-CARD-CX-G6-2b-R1.md`，绑定右端 `d9f7b544`（正文自证「相对 `92734207`，确为测试文件 +34/-0」，本卡实测 `git diff --stat 92734207 d9f7b544 -- <该文件>` = 34 行，**逐字对上**）。故 `3d30bde6` 与 `8e8fd737` 两个 commit **全部**在存档 A 的绑定之后 —— 即协议 §1 所称「同一卡内审后再改 = 真失绑，须登记『整改未复审』」。

| # | 位置（hunk 头） | **归属** | 内容 | 定性 | 依据 |
|---|---|---|---|---|---|
| Z1-1 | `test_review_app.py` `@@ -260,6 +260,12` | `3d30bde6`（Z1-A 整改） | `_BANNED_REBINDS` 集合加入 `"Request"` + 5 行理由注释 | **已见且成立** | 存档 A HIGH「`Request` 绑定可以被替换，注解豁免并未证明可信接收者」（:256，另见 :494/:505）建议「保护豁免所依赖的 `Request` 绑定」。整改与建议一致。 |
| Z1-2 | `@@ -455,7 +461,13` | `3d30bde6` | 装饰器接收者比对 `_root_name(dec.value)` → `ast.unparse(dec.value).split("(",1)[0]` + 6 行理由注释 | **已见且成立**（附 LOW：注释措辞不准，见右） | 存档 A HIGH「链式装饰器漏检能够执行白名单外函数」（:454，尤其 :458）建议「校验装饰器的完整接收者路径」。<br>**Codex round-1 就此判「已见但回应引入新问题」，本卡实测证伪该定性**（`evidence-rv-a/g-codex-claims-probe-*.txt`）：它给的候选 `@_PAGE_TEMPLATE.replace("x","y").replace` 经新判据得接收者 `'_PAGE_TEMPLATE.replace'`，**不在** `_ALLOWED_RECEIVERS`（`{json, request, review_app_router, _STATUS_META, _PAGE_TEMPLATE}`）→ 真门实跑**拒绝**，拒因 `非白名单装饰器接收者 @_PAGE_TEMPLATE.replace.replace`；同一表达式经**旧**判据 `_root_name` 得 `''`（下钻遇 `Call` 即停）→ **旧门也拒**。**旧拒新亦拒，不存在「旧拒新允」。**<br>结构性理由：`split("(",1)[0]` 的产物相对根名**只会更长或相等**，而白名单是**按整串**比对的有限集合 ⇒ 该改动只可能收窄接受集（误拒方向），不可能扩大。<br>**采信 Codex 的事实部分（LOW）**：注释自称「完整接收者路径」不准确 —— 实际是「截断到第一个 `(` 之前」，调用结构确被丢弃。措辞归 **Y2**。 |
| Z1-3 | `@@ -491,17 +503,26` | `3d30bde6` | **只改声明不改判据**：把原「豁免只认裸 `Name`」的适用面注释推翻重写为「两个方向都不准」，新增 (二) 漏网小节，明记 `Request.__class__` / `Request[0]` 经 `_root_name` 下钻**仍被豁免** | **已见且成立**（但须注意性质） | 存档 A 同条 HIGH 明确指出「`Request.__class__`、`Request[0]` 注解也被放行，"只认裸 Name"的新增声明不准确」。本 hunk 把**错误声明**改正并声明判据未收紧、归后续卡 —— 这是**如实声明**，不是漏网的修复。漏网面仍在（由 Z1-1 的名字锁定部分抵消）。 |
| Z1-4 | `@@ -613,6 +634,18` | `3d30bde6` | `_AST_PROBES` 新增两条负向探针：`"Request名被重绑定"`、`"装饰器-链式中间层穿透"` | **已见且成立** | 与 Z1-1 / Z1-2 两项整改各自配一条探针，符合「加严必须配反例」的既有做法。 |
| Z1-5 | `@@ -820,6 +853,23` | `3d30bde6` | `_assert_node_green()` 新增三条计数不变量：`len(counts)==3`、`tests>0`、`fail==0`、`pass==tests` | **已见且成立**，**但整改未达成其自述覆盖（本卡实测，重要）** | 存档 A MEDIUM「通用 Node 裁判仍允许零测试收集假绿」（:818）建议「校验实际测试数量、通过数量及取消情况」。方向一致、只收紧不放宽 ⇒ 定性「成立」。<br>**但本卡实测（`evidence-rv-a/g-codex-claims-probe-*.txt` 之外另跑，Node v24.16.0）**：`node --test` 把**被测文件本身**计为一个 test —— 空文件 `/dev/null` 与「语法合法但零 `test()` 注册」的文件都输出 `tests 1 / pass 1 / fail 0`，**三条不变量全部满足**。<br>⇒ 该 hunk 的注释自述「零条 test 被收集 — 门是空跑, 不是绿」**在这个场景下不成立**：`tests > 0` 在它声称要防的场景里**恒为真**，是一条死断言。它实际堵住的只是**语法错误**场景（模块加载失败 → 文件那个 test 记 `fail=1` → 被 `fail == 0` 抓住），而注释里举的例子恰好就是这一种，所以自述听起来比实际覆盖宽。<br>另（Codex 指出，读码确认）：`re.search` 取**首次**匹配，输出中若先后出现两组计数摘要，只会读到前一组。<br>**归 Y2**：要真正堵住空跑，判据需锁「业务用例数」而非 node 的 `tests` 总数。**登记不阻断**（只收紧、无新放行面）。 |
| Z1-6 | `@@ -2060,3 +2060,102` | **`8e8fd737`（CARD-G6-3 / Z1-B，不是 Z1-A）** | 新增**一个** pytest 用例 `test_js_poll_contract_wiring_g63`（99 行），内含 node 侧四条断言 ①②③④ | **Codex 未见** | 落在存档 A 绑定右端 `d9f7b544` 之后；且 commit 归属为另一张卡。本卡以 §2 的负控 + 四条变异独立检验其承重性（结论：四条各自承重）。 |

> **归属勘误（台账须改）**：台账与第十一批复核报告把 `8e8fd737` 的 99 行计入「Z1-A 审后零外审」。实测 `git log --format='%h %s' -1 8e8fd737` = `test(review): G6-3 5 秒闭环取证 … [CARD-G6-3]` —— 它是 **Z1-B** 的 commit。本卡沿用该复审面（99 行确实零外审，需要审），但归属须更正。

### 3-B. Z4-A 面（`304f03ca` → `7283a8df`，10 hunk，5 个测试文件，单 commit）

存档 B = `codex-review-CARD-REDBASE-R1-round2.md`，绑定 `HEAD=304f03ca` + **未提交的**五文件工作树 diff（正文原话「当前五文件 diff SHA-256」）。因此这 10 个 hunk 中**绝大部分**是存档 B **看过**的内容 —— 与 Z1 面（整段在绑定之后）性质不同。判定依据见 §4 的行号指纹实验。

每条额外标注「改的是**期望值**还是**断言结构**」。

| # | 位置 | 改的是 | 内容 | 定性 | 依据 |
|---|---|---|---|---|---|
| A-1 | `test_subject_resolver.py` `@@ -13,6 +13,8` | 断言结构（工具） | `from unittest.mock import patch` | **已见且成立** | 存档 B M2 项通篇讨论 patch 注入方案，说明该 import 在其视野内。 |
| A-2 | `@@ -22,6 +24,11` | 断言结构（期望值来源） | 新增哨兵常量 `_PROBE_VAULT = "probe_vault_id"` + 注释「期望值来源与被测实现无关」 | **已见且成立** | 独立哨兵使期望值不再取自被测实现（避免两侧都调 `get_current_vault_id()` 的自证）。存档 B L1 项核对过同族改动。 |
| A-3 | `@@ -86,7 +93,10` | **期望值** | `assert "custom-subject" in group_id` → `assert ":custom_subject:" in group_id` | **已见且成立** | 依据是实现侧 `sanitize_subject_name` 把连字符归一为下划线；原断言是前 D16 裸格式遗留。属期望值随实现归一化而更新，非掩盖。 |
| A-4 | `@@ -108,16 +118,23` | **断言结构 + 语义翻转** | 用例更名 `test_manual_requires_both_subject_and_category` → `test_manual_subject_alone_defaults_category_to_subject`；断言由 `source != MANUAL` / `== CONFIG` 翻转为 `source == MANUAL` + `category == subject` | **已见且成立**（依据已独立实测，见右） | 这是本面**唯一一条把断言语义整个翻转**的改动，风险最高，故本卡对其声称依据做了独立实测：<br>①`backend/app/services/subject_resolver.py:207-210` 实测确有 `# Story 1.9: Accept manual_subject alone (category defaults to subject)` + `if manual_subject: category = manual_category or manual_subject` —— 与 docstring 所述**逐字相符**；<br>②`git log -S 'Accept manual_subject alone'` 实测该实现引入于 **`9f554748`（2026-03-18）** `feat(sprint): complete Story 2-3 (bge-m3) + Story 1-9 backend (subject isolation)` —— 有独立 Story 编号与独立 commit；<br>③即：**实现先变更，测试晚了近 6 个月才追上**（2026-03-18 → 2026-09-05）。掩盖回归的形态应是「改动与被掩盖的缺陷同期引入」，本条不符合该形态。<br>**判定：属测试过时补正，不构成掩盖。** 产品语义（Story 1.9 那次契约变更本身是否恰当）仍不在本卡范围，已随 Codex §三 问题 ③ 送审。 |
| A-5 | `@@ -372,26 +389,47` | **期望值 + 断言结构** | `TestGroupIdFormat` 三个用例：期望值 `"math54:离散数学"` / `"custom:path"` / `"general:random"` → `f"vault:{_PROBE_VAULT}:…"`；三处各加 `patch("app.config.get_current_vault_id")` 包裹；类 docstring 加 D16 出处精确化 | **已见且成立** | 存档 B L1 项**逐条核对过**本处（引用 `test_subject_resolver.py:400`，本卡实测该行正是「⚠️ 出处精确化 (Codex round-1 L1)」首行，**行号精确命中**），结论「三处均准确区分 D16 与四段组合」。 |
| A-6 | `test_vault_switch.py` `@@ -244,15 +244,47` | 断言结构（去环境耦合） | `test_vault_id_changes_after_reload` 改为把 `CANVAS_BASE_PATH` 指向无 yaml 的 `tmp_path`，使 yaml-first 分支不触发，从而真正测到 `ACTIVE_VAULT` fallback；手工 try/finally 还原 env 并 `reload_settings()`（不用 monkeypatch，因其还原晚于用例体、`lru_cache` 会留在 tmp 目录污染后续用例） | **已见且成立** | 存档 B 明确核对过本文件：「[yaml 用例及相邻缓存用例 :138–245] 与基线逐字节相同，本卡修改的用例在 finally 恢复环境并 reload」。本卡实测本 hunk 起点正是 `@@ -244`，与该行号边界吻合。**期望值未变**（仍是 `cs_61b`），只改了让它成立的环境前提 → 不构成掩盖。 |
| A-7 | `test_lancedb_vault_isolation.py` `@@ -45,33 +45,81` 前半 | 断言结构（**鉴别力恢复**） | `test_dynamic_vault_id_follows_config`：改为**复用同一个 client**，在两次不同 patch 下各解析一次并要求结果跟着变 | **已见且成立** | 存档 B **M1 项专门验证本处**：复跑同类变异，`current_test_constructor_freeze_mutation=FAIL assertion_line=81`、`current_test_resolve_lru_cache_mutation=FAIL assertion_line=81`。本卡实测 `7283a8df` 该文件 `:81` **正是第二次断言那一行**（行号精确命中）→ 存档 B 所见与 `7283a8df` 在此处一致。这条是**修复了初版丢失的鉴别力**，不是掩盖。 |
| A-8 | `@@ -45,33 +45,81` 后半 | **期望值 + 断言结构** | `test_group_id_has_vault_prefix`：`reload_settings` → `patch`；期望 `startswith("cs61b:")` → `startswith(f"vault:{switched_vault}:")` 并补一条全等断言 `== f"vault:{switched_vault}:math:test_canvas"` | **已见且成立** | 存档 B L1 项核对过（引用 `:99`，本卡实测该行正是「⚠️ 出处精确化 (Codex round-1 L1)」首行，**行号精确命中**）。注意本条是**加强**：从 `startswith` 加到全等。 |
| A-9 | `@@ -324,24 +372,28` | 断言结构（去环境耦合） | `reload_settings(overrides={'ACTIVE_VAULT': 'level3_target'})` → `patch("app.config.get_current_vault_id", return_value=level3_target)`；期望值仍是 `level3_target` | **已见且成立** | 与 A-6 同型（yaml-first 让 override 恒失效）。期望值未变，只换了造值方式。 |
| A-10 | `test_metadata_subject_mapping.py` `@@ -306,10 +306,29` | **期望值** | `assert data["group_id"] == "math54:线性代数"` → `== f"vault:{get_current_vault_id()}:math54:线性代数"` + 大段出处注释 | **已见且成立**，**但有一处口径不一致（登记不阻断）** | 存档 B L1 核对过（引用 `:317`，本卡实测正是「⚠️ 出处精确化」首行，**行号精确命中**）。**口径不一致**：本条的 vault 段直接调 `get_current_vault_id()` 取值，而同批的 A-2/A-5（`_PROBE_VAULT`）与 Z4-A 其余处用的是**独立哨兵 + patch**。A-2 的注释自己写着「不靠『两侧都调 `get_current_vault_id()`』自证」—— 本条恰好就是那个被点名的形态。它在本卡实跑中是绿的（裁判 7），但期望值与被测实现同源，鉴别力弱于同批其它条。**登记，交 Y6-A/Y6-C，本卡不修。** |
| A-11 | `test_write_side_group_guard.py` `@@ -6,26 +6,117` | **断言结构（整条重写）+ 新增用例** | ①`_PROBE_ACTIVE_VAULT` 哨兵；②`_pinned_settings()` 替身（固定 `active_vault_aliases()` 读的两个 settings 字段）；③autouse fixture 做 ContextVar 逐用例隔离；④`test_missing_vault_and_group_derives_current_vault` 从断言调用链（`mock_derive.called`）改为断言**行为**；⑤`test_explicit_vault_id_still_wins` 把稳定 ID 设成与目录名不同的 `cs61b_stable` 以区分「别名归一」与「请求值直落」；⑥**新增** `test_explicit_foreign_vault_id_raises_409` | **已见且成立**；其中 ⑤ 的 docstring 含**审后新增**的 LOW 回应，见 §4 | 存档 B M2 项逐条验证过 ①②③④⑤⑥（原文引 `_pinned_settings :26–28`、`:74–76`、`:87`，并给出三组实跑输出）。存档 B 对 ⑤ 记了一条 **LOW**（「路径证明过强」）。`7283a8df` 中该 docstring **已包含对这条 LOW 的回应**（明写鉴别力边界）→ 属审后 LOW 整改，详见 §4。 |

### 3-C. Z4-B 面（`a5e0ce79` → `c8611a89`，7 hunk，4 文件）

存档 C = `codex-review-CARD-REDBASE-R2.md`，绑定 `7283a8df..a5e0ce79`。本面右端 `c8611a89` 在其**之后** → 7 个 hunk **全部**是「Codex 未见」。

每条额外标注「与 Z4-A 措辞是否一致」。

| # | 位置 | 内容 | 与 Z4-A 措辞 | 定性 | 依据 |
|---|---|---|---|---|---|
| B-1 | `metadata.py` `@@ -122,7 +122,10`（源，-1/+4） | 端点 docstring 的 `group_id` 行扩写：D16 前缀规约 + 「SubjectResolver 在其上再拼 canvas 段，产出四段组合形态」+ 「vault 段是**部署期变量占位符**（取自 `get_current_vault_id()`），实际值随部署而变 — 勿硬编码」 | **一致** | **Codex 未见** | 与 Z4-A 的「出处精确化」措辞同型：都区分「D16 原文三段」与「resolver 再拼 canvas 的四段组合」，都强调 vault 段是部署变量。 |
| B-2 | `intelligent_parallel_models.py` `@@ -283,8 +283,12`（源，-2/+6） | `subject_group_id` 的 `description` 从 `format: {subject}:{canvas_name}` 改为 D16 vault 格式并说明段数随作用域而变（有请求作用域原样透传 ContextVar；无作用域回落 `vault:default:<subject>`，附 `intelligent_grouping_service.py:202-214` 出处）；`examples` 由 `"数学:离散数学"` 改为 `"vault:cs_61b:数学"` | **一致**（同样给了实现出处行号） | **Codex 未见** | 同上。 |
| B-3 | `metadata_models.py` `@@ -49,7 +49,13`（源，-1/+7） | `CanvasMetadataResponse.group_id` 的 Field `description` 扩写，与 B-1 逐字同型（结尾多「勿按字面值硬编码」） | **一致** | **Codex 未见** | 同上。 |
| B-4 | `openapi.json` `@@ -1873,7 +1873,7`（生成物，1↔1） | `components.schemas.CanvasMetadataResponse.properties.group_id.description` | — | **Codex 未见** | **对应 B-3**（`metadata_models.py:49` 的 Field description），逐字相同（JSON 里是单行化形式）。 |
| B-5 | `openapi.json` `@@ -5877,9 +5877,9`（生成物，2↔2） | `subject_group_id` 的 `description`（1 行）+ `examples[0]`（1 行） | — | **Codex 未见** | **对应 B-2**（`intelligent_parallel_models.py:283` 的 `description` 与 `examples`），两行分别对应。 |
| B-6 | `openapi.json` `@@ -15679,7 +15679,7`（生成物，1↔1） | `info.x-generated-at`：`2026-09-04T23:47:48.360386+00:00` → `2026-09-05T01:36:01.005895+00:00` | — | **Codex 未见** | **对应「再生动作本身」**的时间戳。该键在 `check-openapi-drift.py:68` 的 `VOLATILE_INFO_KEYS` 中，比对时被吸收 → 不产生 DRIFT。同一行的 `x-generator` 自述 `--write`。 |
| B-7 | `openapi.json` `@@ -17902,7 +17902,7`（生成物，1↔1） | `paths./api/v1/canvas-meta/metadata.get.description` | — | **Codex 未见** | **对应 B-1**（`metadata.py:122` 的 docstring），JSON 里以 `\n` 转义保留了原 docstring 的换行与缩进。 |

**10 行逐一对应完毕**：`openapi.json` 的 5 增 5 删 = B-4(1) + B-5(2) + B-6(1) + B-7(1)，每一行都能落到某个源文件的具体改动或再生动作上，**无孤儿行**。

---

## §4 (c) Z4-A 专项 —— 钉值不可复现，改用行号指纹判定

### 4.1 存档钉值不可机械复现（登记为事实）

存档 B 正文（`:15` 前后）给出「当前五文件 diff SHA-256」：

```text
0a8ee996ac5efb74de16be74635669aba91ca4542f9d0aeb86a19d9b0b6b0d38
```

本卡以**三种口径**实跑 `git diff 304f03ca 7283a8df … | shasum -a 256`（落盘 `j9-z4a-hashes-*.txt`）：

| 口径 | 完整 64 位哈希 |
|---|---|
| 全树 `-- . ':(exclude)_bmad-output'` | `eb3ed96d39380a9cb4eafdad023052441635e115481e5da8112fde70317eb042` |
| 五文件显式路径（非目录级） | `eb3ed96d39380a9cb4eafdad023052441635e115481e5da8112fde70317eb042` |
| `--no-color` 全树 | `eb3ed96d39380a9cb4eafdad023052441635e115481e5da8112fde70317eb042` |

三口径**互相一致**，且**均不等于**存档钉值。合理解释：存档 B 审的是**未提交的工作树状态**（其正文原话是「当前五文件 diff」，绑定只写 `HEAD=304f03ca`），而 `7283a8df` 是其后落的 commit —— 两者本就不必相等。

> 本节**不包含**、也不允许出现「已核对哈希一致」或任何等价措辞（卡文 (c) 明令）。哈希在这里**无法**用于判定审后是否又改过。

### 4.2 改用行号指纹：可证伪的重建实验

存档 B 正文引用了大量**当时工作树的行号**。插入 N 行会让插入点之后的所有锚点整体位移 N —— 所以行号是比哈希更有用的指纹：哈希对不上只说明「变了」，行号能定位「哪一段变了、变了几行」。

**逐条对照结果**（在 `7283a8df` 上实测 `git show 7283a8df:<file> | sed -n '<n>p'`）：

| 存档 B 的引用 | 它描述的东西 | `7283a8df` 同行号的实际内容 | 判定 |
|---|---|---|---|
| `test_lancedb_vault_isolation.py:81`（M1「新门在第二次断言 :81 抓住它」，附 `assertion_line=81` 两条实跑） | 第二次断言 | `assert client.resolve_table_name("vault_notes") == f"{vault_after}_vault_notes"` | **精确命中** |
| `test_lancedb_vault_isolation.py:99`（L1「已核对」） | 出处精确化段 | `⚠️ 出处精确化 (Codex round-1 L1): D16 原文只列 …` 首行 | **精确命中** |
| `test_metadata_subject_mapping.py:317`（L1） | 同上 | `⚠️ 出处精确化 (Codex round-1 L1): …` 首行 | **精确命中** |
| `test_subject_resolver.py:400`（L1） | 同上 | `⚠️ 出处精确化 (Codex round-1 L1): …` 首行 | **精确命中** |
| `test_vault_switch.py:138–245`（「与基线逐字节相同」，本卡改的用例在其后） | 未改区间的上界 | 本卡 diff 的唯一 hunk 头正是 `@@ -244,15 +244,47` | **边界吻合** |
| `test_write_side_group_guard.py` 的逐字 diff 片段 `@@ -17,6 +17,7 @@`（上下文：`# patch 注入…` / `_PROBE_ACTIVE_VAULT = …` / 空 / **+空** / `# ⛔ Codex round-1 M2 整改:`） | 文件头部 :17–21 的逐字内容 | `:17` = `# patch 注入…`、`:18` = `_PROBE_ACTIVE_VAULT = "probe_active_vault"`、`:19`/`:20` = 两个空行、`:21` = `# ⛔ Codex round-1 M2 整改:` | **逐字 + 行号双重命中** |
| `test_write_side_group_guard.py:74–76`、`:87`（M2 c「路径证明过强」，记 LOW） | 路径证明的声明行与断言行 | `:74–75` 仍是 round-1 5a 整改段；`:87` 处已**不是**当时那几行 —— 中间插入了 `:76–84` 共 9 行 | **位移 9 行** |

**插入的那 9 行是什么**：`7283a8df` 的 `test_write_side_group_guard.py:76–84`，内容是 `test_explicit_vault_id_still_wins` docstring 里新增的一段：

```text
⚠️ 鉴别力边界 (Codex round-2 LOW): 这**排除了「直接采用 sanitize 后的请求值」**
这一类实现 (变异实测: 把 :177-181 的 ``active_vault`` 换成 ``requested``
→ 得 ``vault:cs_61b``, 本条断言红)。它**不能**排除「把两个参数都丢掉、
走双缺失分支 (:191-202)」—— 那条分支同样返回 ``vault:<active_vault>``,
本条断言照样绿 (Codex round-2 内存变异实测 PASS)。
「显式优先于 legacy」这一层由 legacy 值与结果不同来保证; 「显式参数确实被
消费」则由本文件的 409 用例 (跨 vault 显式值必须触发 409, 双缺失分支不会)
与 tests/unit/test_vault_scope_409.py:95 共同兜底。
```

它**逐字引用了存档 B 自己的 round-2 结论**（「Codex round-2 LOW」「Codex round-2 内存变异实测 PASS」）—— 而存档 B 不可能引用自己的结论。这是**审后改动的直接证据**，且内容恰好是对存档 B 那条 LOW 的整改。

全文件 `grep -c 'round-2'` 结果：`test_write_side_group_guard.py` = 2（即上面这段），`test_lancedb_vault_isolation.py` / `test_subject_resolver.py` / `test_metadata_subject_mapping.py` 各 = 1（均为 `Codex round-1 L1` 之外的措辞，非 round-2 回应），`test_vault_switch.py` = 0。

### 4.3 判定（卡文 (c) 要求的那一条）

**可判定的部分**：`7283a8df` 相对存档 B 所见工作树，**唯一可检出的改动**是 `test_write_side_group_guard.py` 中 9 行 docstring 插入，即对存档 B **LOW-1**（M2 c「路径证明表述过强」）的整改；其余四个文件的行号锚点在 `7283a8df` 上**全部精确命中**，未见位移。存档 B 的 **LOW-2**（格式：`_PROBE_ACTIVE_VAULT` 后多一个空行）在 `7283a8df` 中**仍然保留**（那条 LOW 指的是「与基线逐行相同」这个声明不成立，不是要求删空行）。

**未验证的部分（如实声明，附「需要什么才能判定」）**：

- 行号锚点只能证明「锚点之前无**净**增删行」。它**不能**排除**等行数替换**（改字不改行数），也不能排除锚点之后、hunk 之内的改动。要完全判定，需要**存档 B 当时的未提交工作树快照**（或存档 B 对这四个文件的逐字引用）—— 该快照未落盘，现已不可得。
- 存档 B 引用的 `_pinned_settings :26–28` 与 `7283a8df` 实际的 `:27–29`（`def` 在 `:27`）差 1 行。本卡**不**把它读作改动证据：同文件 `:17–21` 已被存档 B 的逐字 diff 片段钉死，中间不可能凭空少一行；更合理的读法是 Codex 把前置注释行 `:26` 算进了函数区域。**登记此歧义，未据此下结论。**
- 本卡**不判**这些期望值改写在**产品语义**上是否正确（卡文范围外）。A-4 那条语义翻转的风险已在 §3-B 单独标出并送 Codex。

---

## §5 (d) Z4-B 专项 —— openapi.json 是机器再生

裁判 8 在 HEAD 上实测（四文件与 `c8611a89` 逐字节相同）：

```text
DRIFT: none (paths=193 schemas=353)
rc=0
```

**推论**：当前 `openapi.json` 与「从源码现场生成」的结果一致 → `c8611a89` 的 `openapi.json` 是 `metadata_models.py`(+7/-1)、`intelligent_parallel_models.py`(+6/-2)、`metadata.py`(+4/-1) 三处改动的**机器再生**，排除手改。10 行的逐行对应见 §3-C 表（B-4 ↔ B-3、B-5 ↔ B-2、B-7 ↔ B-1、B-6 = 再生时间戳）。

**该推论的边界（如实）**：`--snapshot` 证明的是「当前内容 = 现在跑生成器的输出」。它不能证明**当时**是用生成器产生的（手改成与生成器输出逐字节相同的内容，也会得到 `DRIFT: none`）。存档 C 对同类问题的表述是「当前内容与生成器输出一致；历史编辑方式无法据此证明」——本卡沿用该口径，不把它写成「证明了没手改」。

---

## §6 Codex 一轮（gpt-6-astra / ultra）—— 逐条先实测再采信

- 命令：协议 §2 原样（`--sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra"`），1 轮，rc=0，正文 12477 字节 / 113 行。
- prompt：`_bmad-output/审查/prompts/codex-prompt-CARD-RV-A.md`（741 行 / 33210 字符，五分节；协议 §2 禁用词与旧模型名 grep 计数**全 0**，内嵌 `review_app.py` 全文实测 550 行完整）。
- 存档：`_bmad-output/审查/codex-review-CARD-RV-A.md`，首部按协议 §2.1 六行 blockquote + `---`（模型 / reasoning_effort / `codex-cli 0.153.3` 实测 / 绑定 / 会话头三行自证）。`.stderr` 由 `.gitignore:261` 覆盖，**不入库**。
- Codex 末行：**`BLOCKER/HIGH 清零：否`**（其自述该「否」= "清零尚未获证"，非"已确认存在 HIGH"）。按协议 §1，Codex 的 PASS/FAIL 字样**不进门**；本卡阻断级判定见 §6.3。

### 6.1 驳回（本卡实测证伪）

| Codex 条目 | 它的判定 | 本卡实测 | 处置 |
|---|---|---|---|
| Z1 装饰器整改（`test_review_app.py:470`） | **「已见但回应引入新问题」**；候选 `@_PAGE_TEMPLATE.replace("x","y").replace`，称构成「值得复核的新增放行候选」 | 落盘 `evidence-rv-a/g-codex-claims-probe-*.txt`：新判据得接收者 `'_PAGE_TEMPLATE.replace'` → **不在** `_ALLOWED_RECEIVERS` → 真门实跑**拒绝**（拒因 `非白名单装饰器接收者 @_PAGE_TEMPLATE.replace.replace`）；旧判据 `_root_name` 得 `''` → **旧门同样拒绝** | **驳回定性**。不存在「旧拒新允」。结构性理由：截断产物相对根名只会更长或相等，白名单按整串比对 ⇒ 只可能收窄接受集。Codex 自己已声明「允许集合不在读取面，尚不能确认」——本卡有读取面，补上了这一步。**Z1-2 维持「已见且成立」。** |

### 6.2 采信（实测后确认成立）

| Codex 条目 | 内容 | 本卡实测 | 处置 |
|---|---|---|---|
| 计数门格式反例 | `node --test /dev/null` → `tests 1 / pass 1 / fail 0`，三条不变量全过 | **独立复现**（Node v24.16.0），并补测「语法合法但零 `test()` 注册」的文件 → 同样 `tests 1 / pass 1 / fail 0`，三条不变量全 PASS | **采信**。已写进 Z1-5 依据栏：`tests > 0` 在其声称要防的场景里恒为真 = 死断言；整改实际只堵住语法错误场景。归 **Y2**，登记不阻断（只收紧、无新放行面）。 |
| 计数正则取首次匹配 | `re.search` 分别取各字段**第一次**匹配，两组摘要时只读前组 | 读码确认 `re.search(rf"^[ℹ#]\s*{k}\s+(\d+)\s*$", …, flags=re.M)` 确为首次匹配 | **采信**，并入 Z1-5 条目。 |
| ① 的真实时钟 LOW | ① 用真实时钟且 `toISOString` 截毫秒，新鲜窗口仅 ~1–2 秒；执行暂停足够久 → 数据过期 → **回落 60 秒** → 正确实现偶发红 | **本卡起初打算驳回**（以为过期使 `raw` 为负、clamp 到下限 5000 仍绿），实测源码后**推翻自己**：上游 `if (ms !== null && ms > nowMs && …) best = ms;` 使过期数据**根本进不了 `best`** → `best` 保持 `null` → `raw = POLL_MAX_MS` → 60000 ≠ 5000 ⇒ ① 红。生产注释亦自述「已过期的 next_due …→ 回落上限 60s」 | **采信**。① 存在真实 flakiness 风险。归 **Y2**，登记不阻断（本卡三次实跑 ① 均绿）。 |
| ② 诊断文字与变异方向不符 | ② 的失败文字「一小时不问后端」描述的是排程过长；本卡把 60000 改 30000 是让它**更早**轮询 | 读码确认：断言 `assert.equal(b.timers[0].ms, 60000)` 对该变异有效（30000≠60000 → 红），但**诊断文字**方向不匹配 | **采信（LOW）**。不影响「② 承重」结论，只说明该变异证明的是「② 对该常量敏感」，**不是**「② 测到了『不睡死』这一语义」。已在 §9 补记。 |
| ③ 只证一半 | ③ 的变异只证明「恢复前台再 GET」承重；「运行中转入后台时取消已有定时器」这一半无保证 | 读码确认 ③ 的 `assert.equal(b.timers.length, 0)` 发生在 `boot({hidden:true})` 的**初始隐藏**场景，非「运行中转入后台」 | **采信**。已写进 §9「本卡未证明什么」。 |
| ④ 覆盖范围小于「自动轮询整条路径」 | ④ 只覆盖固定成功响应；未覆盖网络失败 / 非 200 / JSON 渲染失败 / 竞态分支 | 读码确认 `feedIn()` 只产出 `{ok:true, status:200}` | **采信**。已写进 §9。 |
| 第一次变异的「其余三条」未记录 | 表格只完整支持后三次单杀 | 属实（首轮只筛失败行） | **采信**。§2.3 已如实标注，「互不遮蔽」的证据基础限定为后三轮。 |
| Z4-A 覆盖归属不能靠哈希判定 | 「哈希不匹配不能确定哪些 hunk 审过」，拒绝把本面判成「未见」 | 与本卡判法**一致**（Z4-A 全判「已见且成立」） | **采信且本卡证据更强**：Codex 只拿到存档 B 首部，无从判断；本卡用存档 B 正文的**行号锚点**做重建实验（§4.2），把审后改动面锁定到单个 docstring 的 9 行。这是本卡相对 Codex 的独立增量。 |
| Z4-A 措辞仍过强（`:82` / `:95`） | 「输出相同不能证明执行路径」；409 用例排除不了「成功分支消费了显式参数」 | 读码确认两处措辞仍在 | **采信（LOW）**。归 **Y6-A**，登记不阻断。 |
| A-4 归因「未验证」 | Codex 称 docstring 引用 Story 1.9 不能自证旧失败是假红，需要契约/实现/历史失败证据 | 本卡**已独立补上该证据**：`subject_resolver.py:207-210` 逐字相符；`git log -S` 实测实现引入于 `9f554748`（**2026-03-18**），比测试改动早近 6 个月 | **部分采信**：Codex 的谨慎正确（它没有这份证据）；本卡补测后**可以**判「属测试过时补正、不构成掩盖」。产品语义仍不判。 |
| Z4-B 示例段数 LOW | description 列举二/四段与 `vault:default:<subject>`，示例 `vault:cs_61b:数学` 是三段 | 读码确认：三段形态 `vault:<vault_id>:<subject>` 只在 `vault:default:` 那一支被列出，示例用的是非 default vault | **采信（LOW）**。示例合法（`vault:default:<subject>` 即其特例），但列举未明说「有作用域时也可能三段」。归 **Y5-C/Y6-A**，登记不阻断。 |
| Z4-B「不足以证明历史上由机器生成」 | `DRIFT: none` 区分不了机器生成 / 手写成相同内容 / 生成后编辑 | 与本卡 §5 的自我限定**逐字同口径** | **采信**。§5 已写明，不改。 |

### 6.3 阻断级判定（协议 §1 口径）

Codex 末行「否」不进门。按协议 §1 的阻断级五项逐条对：

| 阻断项 | 本卡 |
|---|---|
| 数据丢失 | 无（零代码改动，工作树逐字节还原） |
| live vault / Neo4j 7691 写入 | 无（全程未连 7691/7687；W4 门计数全程 `0 (blocked=0, advisory=0, unaccounted=0)`；live vault 未触碰） |
| 安全 | 无 |
| 指定裁判红 | 无（裁判 1-9 全部达成预期或如实记录，无红） |
| 负控假绿（负控本身谎报 PASS） | 无 —— 负控如实报「四断言在旧版上全绿」并据此**升级**为四条变异；四条变异均单杀且失败身份精确 |

**⇒ 阻断级 = 0。** Codex 提出的全部条目为 LOW/MEDIUM 级或「未验证」，逐条登记见 §10，**不阻断**。

---

## §7 DoD-3 双段

### 4-A. Claude 已代验（技术面）

- 裁判 1-10 全部实跑并落盘 `_bmad-output/审查/evidence-rv-a/`（见 §1 表，每条含路径与末行 `rc=`）；三条 `git diff --stat` 与卡文预期**逐字对上**；`--snapshot` 输出与卡文预期**逐字对上**。
- (b) 负控完整走完，含一次**如实登记的操作失误**（trap 相对路径导致还原失效，已修正并复验）；四条断言经四条独立变异证明**各自承重、互不遮蔽**。
- (a) 三份逐条定性表：Z1 6 条（≥6 hunk）、Z4-A 11 条（≥10 hunk）、Z4-B 7 条（=7 hunk），全部到 `文件:行` 粒度。
- (c) 钉值不可复现已登记，本卡三口径完整哈希已贴；改用**行号指纹重建实验**判定审后改动面 = 单个 docstring 的 9 行 LOW 整改，并如实写明该方法的盲区。
- (d) 10 行逐一对应到源码行，无孤儿行。
- 零代码/测试改动：见 §8 收尾核对。

### 4-B. 你来验（一句话，零技术词）

**无变化。**（把上一批那三张卡审完之后又改过的部分，请第三方再看了一遍。软件本身没有任何改动，你不需要做任何操作，也不会看到任何不同。）

---

## §8 收尾核对（零代码改动）—— 裁判 10

commit 前实测：

| 判据 | 命令 | 结果 |
|---|---|---|
| 零代码/测试改动 | `git diff --cached --stat -- . ':(exclude)_bmad-output'` | **空** ✅（staged 15 文件 / 1729 行**全部**在 `_bmad-output/` 下） |
| `.stderr` 不入库 | `git -c core.quotepath=false ls-files --cached \| grep -c '\.stderr'` | **0** ✅（`.gitignore:261` `_bmad-output/审查/**/*.stderr*` 覆盖） |
| 工作树代码未被变异残留污染 | `git diff --stat HEAD -- backend/` | **空** ✅ |
| `review_app.py` 逐字节还原 | `shasum -a 256` | `b7e4a8d94f82b1a6a8e9b07ff636690801d5d1b53c071d21273562def1224a77`，与全部四次变异的「变异前 sha」相同 ✅ |
| 未跟踪残留 | `git status --porcelain \| grep '^??'` | 仅 `codex-prompt-CARD-RV-A.head.md` / `.tail.md` 两个 prompt 拼接中间件（**未 add，不入库**；本机 guard hook 拦 `rm`，故保留在工作树） |

**禁跑清单遵守情况**：全程未跑 `tests/unit` / `tests/integration` / `tests/e2e` 目录级（只跑单文件与 nodeid）；未连 7691 / 7687（W4 门计数全程 `0 (blocked=0, advisory=0, unaccounted=0)`）；live vault 未触碰；未使用 stash；`check-openapi-drift.py` 只跑 `--snapshot`、未 `--write`；`backend/openapi.json` 未动；台账未改。

---

## §9 本卡未证明什么

1. **不复跑 `tests/unit` 目录级** —— 主干既有红基线 247 nodeid（`evidence-b12/unit-red-baseline-03ac8bf8.txt`），会淹没本卡结论；既有红分诊归 **Y6-C**。本卡只跑了单文件与显式五文件（裁判 6/7），它们各自全绿，但**不代表**目录级无红。
2. **不判 Z4-A 期望值改写的产品语义正确性** —— 特别是 A-4（`test_manual_requires_both_subject_and_category` → 语义整个翻转）与 A-10（vault 段与被测实现同源）。本卡只判「是否掩盖真实回归」的形式面，产品语义归 **Y6-A/Y6-C**。
3. **不证明 G6-3 的目标句「答错卡 5 秒可见」成立** —— 本卡只证明了那四条断言各自承重（对四个具体常量/分支敏感）；「承重」≠「目标句成立」。目标句归 **Y2-A**（且第十一批已记录该目标句实测不成立）。
4. **Z4-A 钉值不可复现 ⇒ 「LOW 整改是否在审后」不能机械判定** —— §4 的行号指纹是**推断性**证据，能定位插入面，不能排除等行数替换。要完全判定需存档 B 当时的未提交工作树快照（已不可得）。
5. **四条变异不排除「断言测的范围比其名字窄」** —— 例如 ④ 数的是沙箱 `fetch` 收到的 POST，抓不住走别的传输方式的写请求。
6. **① 那轮变异未逐条记录 ②③④ 的绿/红** —— 「互不遮蔽」这一结论的证据基础是后三轮（②③④ 三轮均完整记录）。
7. **不判 Z1-3 的判据收窄** —— `_root_name` 对 `Request.__class__` / `Request[0]` 的下钻豁免仍在，本卡沿用 `3d30bde6` 的处置（只改声明、不动判据），收紧归后续卡（**Y2**）。
8. **三份既有存档均无协议 §2.1 六行首部** —— 模型名 / reasoning_effort / codex 版本三个字段**无法自证**。按协议 §2.1 的「牙齿」条款，这三轮严格说不计入卡族轮次配额。本卡如实登记，不追认、不代补。

**以下 9-13 条源自 Codex round-1 并经本卡实测确认，一并计入「未证明」：**

9. **② 的变异只证明「② 对 `POLL_MAX_MS` 常量敏感」，不证明它测到了「不睡死」这一语义** —— 本卡把 60000 改成 30000 是让它**更早**轮询，而 ② 的失败文字「一小时不问后端」描述的是排程**过长**的危害，方向不匹配。断言有效，诊断文字不准。
10. **③ 只证明了「恢复前台再拉一轮」这一半承重** —— ③ 里的 `timers.length == 0` 发生在 `boot({hidden:true})` 的**初始隐藏**场景；「运行中转入后台时取消已有定时器」这一半，四条断言均无保证，本卡也未变异验证。
11. **④ 只覆盖固定成功响应下的路径** —— `feedIn()` 只产出 `{ok:true, status:200}`；网络失败、非 200、JSON/渲染失败、不同数据与竞态分支均未覆盖。「自动轮询绝不 POST」的实际证明面小于其名称所声称的范围。
12. **① 存在真实的时钟 flakiness 风险（未在本卡触发）** —— ① 用真实时钟且 `toISOString()` 截去毫秒，新鲜窗口仅约 1–2 秒；若 `boot`→`flush` 之间执行暂停足够久，`next_due` 过期后被上游 `ms > nowMs` 过滤掉 → `best` 保持 `null` → 回落 `POLL_MAX_MS` 60000 → ① 红。本卡三次实跑 ① 均绿，**但这不是不变量**。归 **Y2**。
13. **node harness 自身的捕获能力本卡未独立认证** —— `boot()` 如何识别 POST、如何维护 `calls` 计数、如何模拟定时器，本卡未逐一验证（只验证了「注入一个 POST 会让 ④ 红」这一端到端事实）。若 harness 的 POST 识别有盲区，④ 的证明力会低于表面。

---

## §10 台账待登记条目（车道不改台账，只列）

1. **【Z1 面结论】** `d9f7b544 → 8e8fd737` 173 行审后 diff 复审完毕：6 hunk 中 5 条（`3d30bde6`）为「已见且成立」——逐条对应存档 A 的两条 HIGH + 一条 MEDIUM 的建议；1 条（`8e8fd737` 的 99 行）为「Codex 未见」，本卡以四条独立变异证明其四条断言**各自承重、互不遮蔽**。**阻断级 0。**
2. **【Z4-A 面结论】** `304f03ca → 7283a8df` 364 行复审完毕：10 hunk / 11 条定性，全部「已见且成立」。审后改动面经行号指纹实验锁定为**单个 docstring 的 9 行**（对存档 B LOW-1 的整改）。**阻断级 0**；两条 advisory 见第 6/7 条。
3. **【Z4-B 面结论】** `a5e0ce79 → c8611a89` 31 行复审完毕：7 hunk 全部「Codex 未见」（落在存档 C 绑定 `7283a8df..a5e0ce79` 之后）；措辞与 Z4-A 同型一致；`openapi.json` 10 行逐一对应源码改动，`--snapshot` 无漂移。**阻断级 0。**
4. **【勘误 · 归属】** 台账与第十一批复核报告把 `8e8fd737`（99 行）计入「Z1-A 审后零外审」。实测该 commit 是 **CARD-G6-3（Z1-B）** 的：`test(review): G6-3 5 秒闭环取证 — 实测不可达 + 轮询契约接线四断言 [BATCH-2026-09-05-第十一批 / CARD-G6-3]`。复审面沿用，**归属须更正为 Z1-B**。
5. **【Z4-A 哈希不可复现】** 存档 `codex-review-CARD-REDBASE-R1-round2.md` 的钉值 `0a8ee996ac5efb74de16be74635669aba91ca4542f9d0aeb86a19d9b0b6b0d38` 在 `304f03ca → 7283a8df` 上**三种口径均不可复现**，三口径一致得 `eb3ed96d39380a9cb4eafdad023052441635e115481e5da8112fde70317eb042`。原因：存档审的是未提交工作树，`7283a8df` 是其后的 commit。**该钉值不可用作绑定判据。**
6. **【advisory · 交 Y6-A/Y6-C】** `test_metadata_subject_mapping.py:334` 的期望值 vault 段直接调 `get_current_vault_id()`，与被测实现**同源**；同批 A-2/A-5 用的是独立哨兵 + patch，且 A-2 注释明确点名要避免这一形态。口径不一致，鉴别力弱。**登记不阻断。**
7. **【已实测排除掩盖 · 仅留产品语义 advisory 交 Y6-A】** `test_subject_resolver.py` 的 `test_manual_requires_both_subject_and_category` → `test_manual_subject_alone_defaults_category_to_subject` 是 Z4-A **唯一一条断言语义整个翻转**的改动（`source != MANUAL` → `== MANUAL`）。本卡独立实测其依据：实现侧 `subject_resolver.py:207-210` 逐字相符，且该实现引入于 **`9f554748`（2026-03-18，Story 1.9 独立 commit）**——**比测试改动早近 6 个月**。掩盖回归的形态应是改动与缺陷同期引入，本条不符合 ⇒ **属测试过时补正，不构成掩盖**。仅「Story 1.9 那次契约变更本身是否恰当」这一产品语义问题仍在本卡范围外。**登记不阻断。**
8. **【advisory · 交 Y2】** Z1-3 只改声明未动判据：`_root_name` 对 `Request.__class__` / `Request[0]` 的下钻豁免仍在（存档 A HIGH 已点名）。**登记不阻断。**
9. **【协议 §2.1 存量】** `codex-review-CARD-CX-G6-2b-R1.md` / `codex-review-CARD-REDBASE-R1-round2.md` / `codex-review-CARD-REDBASE-R2.md` 三份存档**均无**六行首部（模型 / reasoning_effort / codex 版本 / 绑定 / 会话头自证）；协议 §2.1 自述「第十一批 9 份由主 session 于 2026-09-05 补首部」，**实测未补**。按「牙齿」条款这三轮不计入卡族轮次配额。**待主 session 处置。**
10. **【方法论教训 · 建议进 rules】** 变异/换文件类裁判的 `trap` 里若写**相对路径**，而命令体中途 `cd` 过，EXIT 时 cwd 已变 → 还原静默失效（本卡实测 `cp: … No such file or directory`，工作树留下了变异体）。**trap 内一律用绝对路径**；且 `trap … EXIT` 应加挂 `INT TERM`（SIGTERM 不做栈展开）。
11. **【Z4-B `--snapshot` 结果】** `DRIFT: none (paths=193 schemas=353)`，rc=0，落盘 `evidence-rv-a/j8-openapi-drift-*.txt`。
12. **【裁判 7 交叉佐证】** Z4-A 五文件显式路径实测 `104 passed`，与存档 B 记录的 `104 passed` 逐字一致 → 独立佐证五文件**行为面**自 round-2 起未变。
13. **【Codex round-1 结论】** `gpt-6-astra` / `ultra` / `codex-cli 0.153.3`，1 轮 rc=0，存档 `codex-review-CARD-RV-A.md`（首部按 §2.1 补齐）。末行 **`BLOCKER/HIGH 清零：否`**（其自述该「否」= 清零尚未获证，非已确认 HIGH）。协议 §1：Codex 的 PASS/FAIL 字样不进门；本卡逐条对阻断级五项 ⇒ **阻断级 = 0**。逐条采信/驳回见验收单 §6。
14. **【驳回一条 Codex 定性 · 附实测】** Codex 判 Z1 装饰器整改为「已见但回应引入新问题」，给出候选 `@_PAGE_TEMPLATE.replace("x","y").replace`。本卡实测：新判据得 `'_PAGE_TEMPLATE.replace'` **不在** `_ALLOWED_RECEIVERS` → **真门拒绝**；旧判据 `_root_name` 得 `''` → **旧门亦拒**。**不存在「旧拒新允」**，定性驳回，Z1-2 维持「已见且成立」。（Codex 自己已声明「允许集合不在读取面，尚不能确认」——本卡补上了这一步。）
15. **【advisory · 交 Y2】** `_assert_node_green` 的计数不变量**未达成其自述覆盖**：`node --test` 把被测文件本身计为一个 test，故空文件与「语法合法但零 `test()` 注册」的文件均输出 `tests 1 / pass 1 / fail 0`，三条不变量全过。`tests > 0` 在其声称要防的场景里**恒为真 = 死断言**；实际只堵住语法错误场景。另 `re.search` 取首次匹配，两组摘要时只读前组。要真正堵空跑须锁「业务用例数」而非 node 的 `tests` 总数。**登记不阻断**（只收紧、无新放行面）。
16. **【advisory · 交 Y2】** `3d30bde6` 装饰器整改的注释自称「完整接收者路径」措辞不准 —— 实际是「截断到第一个 `(` 之前」，调用结构被丢弃。门的行为正确（只会更严），**措辞需修正**。
17. **【advisory · 交 Y2】** G6-3 断言 ① 存在时钟 flakiness 风险：真实时钟 + `toISOString()` 截毫秒 ⇒ 新鲜窗口仅 ~1–2 秒；过期后经 `ms > nowMs` 过滤 → `best=null` → 回落 60000 → ① 红。本卡三次实跑均绿，但非不变量。② 的失败文字「一小时不问后端」与「更早轮询」方向不符（诊断文字 LOW）。
18. **【advisory · 交 Y6-A】** `test_write_side_group_guard.py:82`「legacy 值不同保证显式优先」与 `:95`「证明别名归一化确实发生」两处措辞仍强于证据（输出相同不能证明执行路径）；`7283a8df` 新增的鉴别力边界披露诚实，但周边措辞未随之收敛。
19. **【advisory · 交 Y5-C/Y6-A】** `intelligent_parallel_models.py` 的 `subject_group_id` description 列举了二段 / 四段 / `vault:default:<subject>`，而 `examples` 给的是三段 `vault:cs_61b:数学`。示例合法（`vault:default:<subject>` 即三段特例），但列举未明说「有作用域时也可能是三段」。**措辞 LOW，不阻断。**

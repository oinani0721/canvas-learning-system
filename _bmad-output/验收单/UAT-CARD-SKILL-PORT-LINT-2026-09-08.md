# UAT — CARD-SKILL-PORT-LINT（2026-09-08）

> 批次：`[BATCH-2026-09-07-第十三批 / CARD-SKILL-PORT-LINT]` · 车道 `card-u4-hosts`（分支 `card/u4-hosts`）
> 绑定：`9303201a`（U4-A 末 commit）→ **`4446ac81`**（当前最终 HEAD）。区间内八个 commit：
> `ae6a68f3` 初版 → `3b98081a` r1 整改 → `8bb94475` 作者自查（钉住门测不到的 8011）
> → `98ca073c` r2 整改 → `83cd6104` r3 整改 → `4446ac81` r4 整改（越界判据 v2 引号感知）
> 代码面改动恰两项：`backend/tests/skills/test_skill_portability_lint.py`（新增）、
> `canvas-vault/.claude/skills/start-exam-board/SKILL.md`（改）

---

## 一 做了什么

**9 份进 lint / 8 份为整改候选 / 实际改动 1 份 = `start-exam-board`。**

### 新门：`backend/tests/skills/test_skill_portability_lint.py`（**59 用例**）

| 判据 | 覆盖 | 内容 |
|---|---|---|
| 层 1 frontmatter | 9 份 SKILL.md | 键集**精确相等** `{name, description, argument-hint, allowed-tools, model}`；`name` == 目录名且 kebab-case；`description` 非空；`allowed-tools` 形态（非空 YAML list） |
| 层 2 正文 | 9 份 × **9 指标** | `AskUserQuestion` / `mcp__canvas-learning-mcp__` / `.claude/(skills\|scripts)/` / **`tmp_all` + `tmp_ns`** / **`p8011_all` + `p8011_ns`** / 树名 / `/Users/`，**精确计数，增红减也红** |
| 层 3 scripts | 7 份 × 3 指标 | `/tmp` / `/Users/` / 树名 精确计数 + **文件集合钉死**（新增脚本即红） |
| **越界路径 v2**（r1 新增，r4 引号感知） | 9 份 SKILL.md | 越出 `/tmp/cls-exam/` 的 **normpath 集合**精确相等（字面量原子化 + fence 拼接组求值 + 白名单裸 token） |
| **可疑行**（round-2 新增，r3 加宽） | 9 份 SKILL.md | `/tmp` 与 `..` 或**任意 `$`** 同一**逻辑行**（续行/相邻字面量拼接已合并）的行号集合精确相等 —— **不依赖 token 切分**（现状 quiz-answer `:98` + start-exam-board `:577`） |

五类判据都是纯函数 `check_frontmatter` / `check_body` / `check_scripts` /
`check_escaping_tmp` / `check_suspicious_tmp_lines`（外加交接判据 `check_handoff_constants`），`root` 可注入
⇒ 正控跑树、负控跑 tmp 副本。每条断言消息含 **skill + 指标 + 期望 + 实测**。

**为什么 `/tmp` 与 8011 各钉两端而不是钉裸值**：差值对「一增一减」失明——把一处裸路径搬进
命名空间（ns +1）同时另加一处新的裸路径（all +1），裸值不变、门照绿，而本门存在的理由
（「新增一处 `/tmp` 没人能抓」）就被击穿。钉两端 ⇒ 自动钉住它们的差，反之不成立。

**为什么子串计数之外还要越界判据**：子串规则看不见路径语义。`/tmp/cls-exam/../x` 在计数下
裸值为 0（放行），`normpath` 后却是 `/tmp/x`。两条判据分工——计数管「命中数变没变」，
越界判据管「命中的路径指向哪里」；对同一输入可以给出不同结论，那是分工不是矛盾。

### 档 A 整改（只落在 `start-exam-board` 一份）

| 点位 | 改前 | 改后 |
|---|---|---|
| `:188` | 散文「写到 `/tmp/exam-candidates.json`」 | `/tmp/cls-exam/exam-candidates.json` + 前置 `Bash: mkdir -p /tmp/cls-exam/` |
| `:198` | `P = "/tmp/exam-candidates.json"` | `P = "/tmp/cls-exam/exam-candidates.json"` |
| `:304` | `curl … http://localhost:8011/api/v1/exam/targeting-material` | `curl … "${CLS_BACKEND_URL:-http://localhost:8011}/api/v1/…"` |
| `:430/:435` | `/tmp/exam-created-event.json` | **未动**（只钉，见 §四 ②'） |

⇒ 裸 `/tmp/` **4 → 2**；裸 `8011` **1 → 0**；`rel` / `AskUQ` / `mcp` 三项与开工逐字相同。

---

## 二 DoD-3 双段

### 4-A Claude 已代验（技术指标）

| # | 裁判 | 结果 | 存档 |
|---|---|---|---|
| 1 | 基线计数开工 | 9 行；AskUQ 30 / mcp 33 / rel 16 / tmpAll 8 / 8011 1 / tree 0 / users 0 —— **与勘探值全同** | `evidence-skill-lint/baseline-counts-open-20260908T090832.txt` |
| 1' | 基线计数收工 | **只有 `start-exam-board` 一行变**（`tmpAll 4→6 tmpNS 0→4 p8011NS 0→1`），quiz-answer 与其余七行**逐字相同** | `baseline-counts-close-20260908T092313.txt` |
| 2 | 新门 改前红 | **4 failed / 13 passed**；红的正是 `bare_tmp 期望=2 实测=4` 与 `bare_8011 期望=0 实测=1` | `test-red-20260908T092057.txt` |
| 2' | 新门 改后绿 | **17** → r1 **31** → r2 **45** → r3 **53** → r4(v2) **59 passed, rc=0** | `portlint-green-final-…` / `portlint-r4-…` / `dir-tests-skills-r5-20260908T171630.txt` |
| 3 | `tests/skills` 目录级 | 开工 **369 passed** → 收工 **428 passed** = 369 + 59，**0 新红** | `dir-tests-skills-open-…` / `dir-tests-skills-r5-20260908T171630.txt` |
| 4 | 只钉不改 shasum | quiz-answer / fsrs_bridge.py / decay_beta.py 开工收工 **逐字节相同** | `shasum-pinned-open-…` / `shasum-pinned-close-…` |
| 4' | live vault 零写 | `find -newer sentinel-live` = **0** | `live-newer-count-20260908T092313.txt` |
| 5 | ruff | `check` rc=0 + `format --check` rc=0 | `ruff-final-20260908T092702.txt` |
| 6 | 地盘门 | `git diff --name-only 9303201a 4446ac81 -- . ':(exclude)_bmad-output'` = **恰 2 项**（八个 commit 后仍恰两项） | `domain-gate-final-20260908T092702.txt` |
| 7 | regression `--collect-only` | 改前 / 改后**同为 226 collected, rc=0, ERROR 计数 0** | `regression-collect-open-…` / `regression-collect-close-…` |
| 8 | live≠HEAD 三份 diff | board-recap / quiz-answer / start-exam-board 落存档，**以 HEAD 为准、不合回** | `live-vs-head-<skill>-20260908T090832.txt` |

**卡文未列、本卡新发现并补跑的两个下游裁判**（见 §四 ⑧）：

| # | 裁判 | 结果 | 存档 |
|---|---|---|---|
| 9 | `check_skill_routing_block.py` | 开工 **66/66** → 收工 **66/66**（C1 ROUTING 逐字节 / C7 FALLBACK 块内 python `ast.parse` / C8 降级≠中止 全绿） | `routing-check-open-…` / `routing-check-close-…` |
| 10 | 5 个 `PYEOF` 块 `compile()` 自检 | quiz-answer 2 + start-exam-board 3 = **5 块全过**（`mutation_kill_identity.py` 的广义提取口径） | 本单 §三 |
| 11 | **层 1 两条无负控断言的承重自验** | 13 条负控没覆盖到「`name` == 目录名」与「kebab-case」这两条。补做定向变异（tmp 副本、先验对照组为绿以保归因）：`name: exam-quick → exam-slow` ⇒ 被**点名的那条**拦下（消息含实测 `'exam-slow'`）；目录 + name 一并改成 `Exam_Quick` ⇒ 被 **kebab-case 那条**拦下。两条**均承重**，且不是被别的断言误杀 | 本单 §二.4-A 本行 |

### 4-B 用户可感（零技术词）

我的九个学习技能现在有一张「体检表」：谁用了临时文件、谁写死了地址、谁依赖了只有一家助手才有的按钮，
一目了然。这次只动了一份、两处最稳妥的地方——出题时那个临时文件搬进了自己的小抽屉（不再和别的程序
挤在同一个大杂物间），后端地址也不再焊死，换台机器换个端口就能用。其余全部先如实记下来、不硬改。
改动不影响我现在的用法：环境变量没设时，行为和以前**完全一样**。

我看到它们更整齐，也更放心——因为没有为了好看去动没把握的东西：有四处路径写法看着刺眼，但要改对
得先确认助手运行命令时站在哪个目录，这件事还没验过，所以原样留着并写清了「要验什么才能动」。

**felt-sense**：像是给一柜子工具贴了标签，还顺手把最常掉出来的那两件放进了固定格子；没贴标签的那些
没有硬塞，而是写了张便条说明为什么先不动。

---

## 三 与卡文的偏离（一处，请复核者重点看）

**卡文 (c) 档 A ① 原写**：「`:198` 那段 python 写前加 `os.makedirs(os.path.dirname(P), exist_ok=True)`」。

**实测该段 python 是读取方**：`:195-237` 的内容是 `P = …` → `json.load(open(P, encoding="utf-8"))`
→ 排序打印 → 末尾 `os.remove(P)`。它**不写** `P`；写入方是 `:188` 那一步的 **Write 工具**（散文指令）。

⇒ 把 `makedirs` 加在读之前是**死代码**：目录存在时 no-op，目录不存在时 `open(P)` 照样失败。
而「首次运行 `/tmp/cls-exam/` 不存在」是本次整改**自己新引入**的前提，必须在 Write **之前**处理。

**处置**：改在 `:188`（Write 前）加 `Bash: mkdir -p /tmp/cls-exam/`。`mkdir -p` 是 POSIX 标准命令，
不依赖 Claude Code 的任何解析行为 ⇒ **不属档 B**。该字面量**带尾斜杠** ⇒ 同时进 `tmpAll` 与 `tmpNS`，
裸值不受影响——这正是卡文明确授权的**第二种写法**（卡文原文：「唯一允许的写法是带尾斜杠的
`os.makedirs("/tmp/cls-exam/", exist_ok=True)`，此时 tmpAll=5 / tmpNS=3 ⇒ 裸仍 2」）。

**数字更正**：卡文预估 5/3，**收工实测 6/4**——差 1 是因为文件末尾新增的「变更记录」小节自身也写了
一次 `/tmp/cls-exam/`（同进 All 与 NS）。**裸值 = 6 − 4 = 2，与卡文 §二.2 的期望一致**。
⚠️ 这句话在 round-2 后已更新：新门**不再只钉裸值**，而是钉 `all`/`ns` 两端（差值对「一增一减」失明，见 §五 round-2）。6/4 这组数字本身不变。

---

## 四 台账待登记条目

① **基线口径与实测数字**（9 份 × 9 指标 + 越界多重集，开工/收工两份路径见 §二）。
**决策页 §四 四个数字更正**：`mcp__` 32 → **33**；相对路径 12 → **16**（口径含 `.claude/scripts/`）；
`/tmp/*.json` 9 → **8**；`AskUserQuestion` 30 ✓ 无误。

①' **`UserPromptSubmit` 口径已定位（比卡文更精确）**：卡文说「0 命中、口径不可复现」——
前半对、后半不够准。9 份 SKILL.md 里确实 0 命中，但它**真实存在**于
`canvas-vault/.claude/settings.json`（`:3` 键名 + `:9` 降级 payload），是一个调
`/api/v1/chat/rag/enrich-hook` 的 hook，往每轮对话注入笔记片段。
⇒ 不是「找不到」，是**找错了地方**；那个文件不在本门覆盖面内（归 U3-C）。
「注入 26 行」这个数**仍未证实**（要跑后端看它实际注入多少行，本卡禁连）。

①'' **本门覆盖面外的 8011 债，实测逐处定位并已钉成判据**：
`hooks/session-end-archive.py:21`（1）/ `mcp.json:5` URL + `:13` 说明（2）/ `settings.json:9`（1）
＝ **4 处**，全归 U3-C 步 3。
⚠️ **卡文 §〇 的分布记错了**：它写「`.claude/mcp.json:5` / 仓根 `.mcp.json:5`」，实测
**仓根 `.mcp.json` 根本没有 8011**，而 `canvas-vault/.claude/mcp.json` 有**两处**。总数对，分布不对。
⇒ 新增 `OUT_OF_SCOPE_8011` 常量 + `test_out_of_scope_hardcoded_ports_are_registered`
（带验伪锚：断言这些文件确实**不在**四类判据覆盖面内，否则该用例多余）。
这样「本门测不到什么」由判据撑着而非散文：变少 = U3-C 已模板化（回来删常量项），
变多 = 有人新写了写死端口。
`skills/configure-whiteboard/templates/whiteboard.md.template` 同样在覆盖面外，实测 0 债。

② **档 A 整改清单（1 份 = `start-exam-board`，逐行见 §一）+ 档 B 未做清单与理由**：
相对路径改写整体退回（**解锁条件 = Bash cwd 实证**：在探针 vault 放一份只跑 `pwd` 的 skill、由
Claude Code 真实触发一次并落盘；U4-A 的 P4 只测「skills 目录是否被扫」，不构成该证据）；
frontmatter 挪字段 / `allowed-tools` 改字符串 / 替换 `AskUserQuestion` / 改 `mcp__` 名 = E-1 一线行为面。
**初稿更正**：「8 份最小整改 / 4 份有整改 / `.claude/skills` → 0」→「**9 份进 lint、8 份候选、1 份有整改**、
`.claude/(skills|scripts)` 指标只钉现状」。

②' **`:430/:435` 不改的依据与去向**：`/tmp/exam-created-event.json` 被
`backend/tests/regression/test_g3_3_cas.py:49`（**模块级** `assert len(_SEB_BLOCKS) == 1`，改了整个文件
collect 期 ERROR）、同文件 `:144`、`test_learning_events_schema_contract.py:1013` 与 `:1017` 钉死。
⚠️ **卡文 §〇 只列了 2 处、台账 ⑩ 补到 3 处，实测共 4 处代码引用**（另有 `:1014` 断言消息文本、
`:1016` 的 `tmp_path` 文件名，不含 `/tmp/` 前缀，不构成钉点）。
`start-exam-board` 裸 `/tmp/` **4 → 2** 的残留归**第十四批 `tests/regression` 解耦卡**。
旁证存档：`regression-collect-{open,close}-20260908T092313.txt`。

③ **`QUIZ_ANSWER_BASELINE` 交接**：U4-B 先合（合并队列第 2 组）；**U5-B（CARD-G3-3-R2）改
`quiz-answer/SKILL.md` 后必须同步更新该常量**（已单列成段 + 注释写死）。

③' **`U6_SCRIPTS_BASELINE` 交接**：层 3 钉死了 `board-recap/scripts/recap_exam_build.py` 与
`clear-inbox/scripts/inbox_preview.py` 的三项计数（**实测均 0 = 零余量**）与整个 scripts 文件集合，
而这两份是手册 §一 明列的 **U6 地盘**、U6-A/B/C 在合并队列**第 3 组**。
⇒ **请主 session 在手册 §一 合并队列 U6 行加注**：「rebase 到含 U4-B 的候选树后，改 `board-recap` /
`clear-inbox` 的 scripts 或新增脚本必须同步 `backend/tests/skills/test_skill_portability_lint.py` 的
`U6_SCRIPTS_BASELINE`」（形式照 quiz-answer 那条）。本卡侧已把常量单列 + 注释写死。

④ **live≠HEAD 三份差异存档**（board-recap / quiz-answer / start-exam-board），**不合回**，E-4 以 HEAD 为准。
⚠️ **卡文 §〇 把 quiz-answer 的两个 shasum 标反了**：实测 **live = `9652e1e1…` / HEAD = `63b51029…`**
（卡文写成 live `63b51029` vs HEAD `9652e1e1`）。数值本身对得上，只是标签互换。

⑤ `.claude/scripts/` 共享脚本引用（ai-linked-doc `:270` / configure-whiteboard `:255` / quiz-answer）
保留为**真依赖不改**；`fsrs_bridge.py` 的 `/Users/` 1 + 树名 1 钉住（零写者，本卡硬边界禁碰）。

⑥ 其它 4 处 8011（`canvas-vault/.claude/hooks/session-end-archive.py:21` / `.claude/settings.json:9` /
`.claude/mcp.json:5` / `.mcp.json:5`）归 **U3-C 步 3** 模板化。

⑦ **Codex 五轮存档路径、绑定 SHA、B/H/M/L 计数**：
   r1 绑 `ae6a68f3`（B0/H1/M2）→ r2 绑 `3b98081a`（B0/H1/M5/L1）→ r3 绑 `98ca073c`
   （B0/H2/M5/L1）→ r4 绑 `83cd6104`（B0/H2/M4/L5）→ r5 绑 `4446ac81`（B0/**H4**/M1/L3，
   D-15 上限轮 ⇒ 交主 session 人审）。存档 `_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r1..r5.md`，
   prompt `…/prompts/codex-prompt-CARD-SKILL-PORT-LINT[-r2..-r5].md`，evidence
   `_bmad-output/审查/evidence-skill-lint/`（开收工基线/红绿/目录级/regression-collect/
   routing/shasum/domain-gate 各时戳件）。

⑧ **本卡新发现、卡文未列的两个下游裁判**（建议写进手册 §三「最低覆盖」，供后续改 SKILL.md 的卡照跑）：
- `backend/scripts/check_skill_routing_block.py`：C1 要求 **ROUTING 块（`:17-38`）9 份逐字节相等**、
  C7 要求 **FALLBACK 块内 python 能 `ast.parse`**、C8 要求「降级 ≠ 中止」（措辞黑名单）。
  本卡改的 `:188/:198` **就落在 FALLBACK 块 `:162-239` 内** ⇒ 受 C7/C8 直接约束。开工收工均 66/66。
- `backend/scripts/mutation_kill_identity.py` 的广义 `PYEOF` 提取（`<<'PYEOF'`，比
  `test_g3_3_cas.py:37` 的窄正则宽）覆盖 5 块：quiz-answer 2 + start-exam-board 3，逐块 `compile()`。
- 另：`backend/tests/regression/test_g3_2_review_ledger.py:521-534` 门⑪ 钉死了含
  `learning_events.jsonl` 的**文件集合**（4 份），改 SKILL.md 时若新增该字面量会打红。本卡未触及。

⑨ `tests/skills` 开工 **369** / 收工 **386**（+17，0 新红）。

⑩ **手册措辞核对（开工实测，比卡文 §四 ⑨ 更新）**：

- ✅ **卡文 §四 ⑨ 要登记的那处偏差已不存在**。卡文说「手册写『以卡文 **(d)** 收敛为准』，
  请主 session 顺手更正」；开工实测手册 `:239` 现写的是
  「实际改动以卡文 **(c)** 收敛为准（**(d) 是负控**），主干实测只 `start-exam-board` 一份需改」
  —— 主 session 已改好，且连「(d) 是负控」的说明都补上了。**本条登记为「已过期，无需处置」**
  （自证命令：`grep -n '主干实测只' <手册绝对路径>` → 命中 `:239`）。
- ⚠️ **另发现一处未更正的不一致**（登记不阻断）：手册 `:36`（§二 车道表）仍写
  「B CARD-SKILL-PORT-LINT（… 三层基线 **+ 8 份 SKILL.md 最小整改**；quiz-answer 只钉现状不整改）」，
  与同一份手册 `:239` 的出口描述（「主干实测只 `start-exam-board` 一份需改」）互相矛盾。
  实况以 `:239` 与本卡一致：**9 份进 lint、8 份候选、1 份有整改**。请主 session 顺手对齐 `:36`。
- ✅ 手册 `:57` 明列 U6 地盘含 `board-recap/scripts/recap_exam_build.py` 与
  `clear-inbox/scripts/inbox_preview.py`，并注明「U4-B lint **只读扫描**」—— 与本卡层 3 的
  只读计数一致，`U6_SCRIPTS_BASELINE` 交接（本单 ③'）正是为这条服务。
- ✅ 手册 `:71` 明列 `backend/tests/skills/test_skill_portability_lint.py` 为 **U4-B 独占新文件**
  —— 与地盘门实测一致（`9303201a → 98ca073c` 恰两项）。

---

## 五 Codex 复核

### round-1（绑 `ae6a68f3`）— `codex-review-CARD-SKILL-PORT-LINT-r1.md`

**BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 0**。三条都是真缺陷，**全部已修**：

| 级别 | 缺陷 | 处置 |
|---|---|---|
| **HIGH** | `/tmp/cls-exam/../x` —— 路径穿越发生在**进入命名空间之后**。子串计数下 `/tmp/` 1 次 + `/tmp/cls-exam/` 1 次 ⇒ 裸值 0 ⇒ **放行**，而 normpath 后是 `/tmp/x`，已越出命名空间。作者原负控只覆盖了穿越在**前**的 `/tmp/a/../cls-exam/`，漏了对称变体 | 新增**第四类判据** `check_escaping_tmp()`：把每份的越界 normpath **多重集**钉死（现状 6 处，全是只钉不改的已知项）。与子串计数**互补**：计数管「命中数变没变」，越界判据管「命中的路径指向哪里」。配 3 条参数化负控（`../x` / `a/../../y` / `./../z`），每条同时断言「计数判据看不见」+「越界判据看得见」，绑定被哪一层拒 |
| **MEDIUM** | `U6_SCRIPTS_BASELINE` 的 `== {两份}` 断言与该常量自己的交接注释**自相矛盾**——注释要求 U6 新增脚本必须登记进来，而 `==` 会把照做的 U6 直接打红。Codex 已在内存复现 | 改成两条各管一面的判据：(i) 原两份 `⊆`（不许删交接项）；(ii) 新登记条目必须落在 U6 的两个 scripts 目录下（不许拿它当垃圾桶绕过 `SCRIPTS_BASELINE` 审阅）。「未登记的新脚本立刻红」仍由层 3 文件集合精确相等保证。新增用例 `test_u6_can_register_a_new_script_without_being_blocked` 正反双向验证 |
| **MEDIUM** | 「一增一减」总数相等 ⇒ 保持绿 | **本 session 独立发现并已先行修好**（Codex 独立确认同一形态）：基线从「钉裸值差值」改为**钉 `tmp_all`/`tmp_ns`/`p8011_all`/`p8011_ns` 四端**；差值降级为派生算式 `bare_tmp()`/`bare_8011()`，只用于断言消息与对账用例。配负控 `test_negative_control_equal_count_swap_must_redden`（前置断言「裸值此时不变」以保归因） |

Codex 同时确认的几点（无需改动）：**档 B 退回成立**（相对路径按执行进程 cwd 解析，SKILL.md 所在目录不改变这个规则；但也不能断言 Claude Code 必在 vault 根执行 ⇒ 需真实调用实证，且**单次 `pwd` 不够**，要比较从 vault 根与子目录启动两种情形）；**`exam-created-event` 无遗漏的独立钉点**；**U5-B 并非 rebase 必红**（只有指标变化才红）；**负控归因成立**，无被别层误打红。

Codex 指出但按设计保留的两点（登记）：① 放行口径只认字面量 `:-http://localhost:8011`，不验证变量名 ⇒ `${X:-http://localhost:8011}` 亦放行；反向 `${CLS_BACKEND_URL:-http://127.0.0.1:8011}` 被计入裸值。这是「写死字面量而非结构解析」的既定权衡，**不据此宣称那些形态不可移植**。② `mkdir -p /tmp/cls-exam`（无尾斜杠）会红——本卡 SKILL.md 写的是带尾斜杠形态，不受影响。

### 指标数变更

层 2 由 **7 指标 → 9 指标**（`/tmp` 与 8011 各拆 all/ns 两端），另加**第四类越界判据**。
⇒ Codex round-1 报告里「9×7＝63 项」的描述对应的是修复**前**的版本。

### round-2（绑 `3b98081a`）— `codex-review-CARD-SKILL-PORT-LINT-r2.md`

**BLOCKER 0 / HIGH 1 / MEDIUM 5 / LOW 1**。作者**逐条实测复现**，确认反例全部属实，
HIGH + 四条 MEDIUM + LOW 已修（commit `98ca073c`）：

| 级别 | 缺陷 | 处置 |
|---|---|---|
| **HIGH (a)** | `/tmp/cls-exam/a,b/../../x.json` —— 逗号把 token 截成 `/tmp/cls-exam/a`（判在命名空间内），完整路径规范化却是 `/tmp/x.json`；计数裸值也为 0 ⇒ **两条判据一起漏** | 见下「三管齐下」第 3 条 |
| **HIGH (b)** | `/tmp/cls-exam/..,x` 被截成 `/tmp/cls-exam/..` ⇒ **误报**越界 | 同上（保守报红优于漏检） |
| **HIGH (c)** | `/var/cache/tmp/cls-exam/x.json` 的子串同时喂饱 `tmp_all` 与 `tmp_ns` ⇒ **冒充命名空间**。把一处真路径「等计数替换」成它，四端纹丝不动、越界判据也看不见 | 见下第 1、2 条 |
| **MEDIUM-2** | 删掉 `ESCAPING_TMP_BASELINE["start-exam-board"]` ⇒ 该 skill **静默不再被检查**，所有既有断言照绿 | `test_every_per_skill_baseline_covers_all_nine_skills`：三个 per-skill 基线一起钉 `== 9 份` |
| **MEDIUM-3** | U6 合法登记锁不住「零余量」；还能把主基线脚本挪进 U6 常量换维护归属 | 正式判据加「新登记项必须零余量」+「只收 U6 地盘」两条；带债的必须走 `SCRIPTS_BASELINE` 人工审阅 |
| **MEDIUM-5** | 越界负控用**追加** —— 而追加会让 `tmp_all`/`tmp_ns` 双双变化 ⇒ **计数判据也会红**，所以那三条负控根本没证明「计数看不见」 | 改成**等计数替换** `_swap_in_start_exam_board()`，并**实际断言** `check_body(...) == []` |
| **MEDIUM-6** | U6 正反用例自己重写集合判断 ⇒ 正式判据退回 round-1 旧版，用例照绿，它声称防守的回归抓不到 | 抽出正式判据 `check_handoff_constants()`（三基线全走参数），用例全部经由它。**实测**：判据退回 `== U6_SEED` 时那条「必须放行」立刻翻转 |
| **LOW-8** | 多重集诊断用 `in` 判断 ⇒ 期望 `[x,x]` 实测 `[x]` 时消息显示「缺失=[]」 | 改 `Counter` 比**次数** |

**HIGH 的修法：三管齐下，不追求「完美切分」**——从自由文本用正则提取路径是启发式，
修一次换一种坏法（(a) 漏检与 (b) 误报同源）。所以：

1. `_TMP_TOKEN_RE` 加左边界 `(?<![A-Za-z0-9_.~$-])`，要求 `/tmp/` 是**绝对路径起点** → 修 (c) 的误提取；
2. `tmp_ns` 改用带左边界的 `_TMP_NS_RE` 计数 → 修 (c) 的等计数替换。
   **判据设计原则：放行端要窄，计入端可以宽** —— `tmp_all` 仍用裸子串，把 `/var/cache/tmp/x`
   也算成债是偏保守（安全）；放行端偏宽才是漏洞；
3. 新增 `suspicious_tmp_lines()` / `check_suspicious_tmp_lines()`：**不依赖 token 切分**的
   行级判据，凡 `/tmp` 与 `..`（或变量展开）同行一律要登记 → 修 (a)(b)，并顺带覆盖
   MEDIUM-4 的 shell 变量展开。基线 `SUSPICIOUS_TMP_LINES_BASELINE` 现状仅 quiz-answer `:98`
   一行（该行的 `..` 来自省略号而非路径穿越，属误报友好项）——**登记它而不是放宽判据**，
   放宽会把真穿越一起放过去，登记一行的成本远更低。

**登记不修（如实声明）**：MEDIUM-4 变量展开的运行期落点（静态门固有边界，已由行级判据
要求登记）；MEDIUM-7 覆盖面外的 cwd 依赖与其它绝对路径形态（Codex 亦明确指出「限定材料
未提供这些位置现存债的可核实内容，不能将构造反例冒充仓内实物」）。

**分工表扩到三列九行**（含 Codex 找到的四个形态），并断言「三列全放行」的行必须真在
命名空间内 —— 将来放宽任一条判据，对应行立刻翻转。

### round-3（绑 `98ca073c`）— `codex-review-CARD-SKILL-PORT-LINT-r3.md`

**BLOCKER 0 / HIGH 2 / MEDIUM 5 / LOW 1**。反例逐条实测复现属实，HIGH + 四条 MEDIUM
已修（commit `83cd6104`）：

| 级别 | 缺陷 | 处置 |
|---|---|---|
| **HIGH-1** | 黑名单式左边界漏 `/`、`+`、非 ASCII —— `/var/cache//tmp/cls-exam/…`（双斜杠）、`/var/cache+/tmp/…`、`/var/缓存/tmp/…` 里内层 `/tmp` 前的字符不在黑名单，照样被当路径起点 ⇒ 等计数替换后三判据全盲 | 左边界改**分隔符白名单**（`/tmp` 前只允许空白/引号/反引号/开括号）：三形态 ns 全部掉零 ⇒ 计数判据红。代价 = 登记在案的保守误报（`P=/tmp/x`、`>/tmp/x`、`-o/tmp/x`、`file:///tmp/…` 判成债；方向安全，树上无） |
| **HIGH-2** | 物理行切分漏跨行拼接 —— `P = ("/tmp/cls-exam/"`␊`"../x")` 是合法 Python 隐式拼接，`/tmp` 与 `..` 不同行 ⇒ 行级判据失明，token 在引号处截断 ⇒ 越界也看不见；覆盖表最终断言 `startswith` 还会被内嵌真换行的字面量骗过 | 新增 `_logical_lines()`（反斜杠续行 + 相邻同引号字面量拼接合并，有界 4 次）；覆盖表最终断言改**整字面量 normpath** 在命名空间内（与越界判据同定义） |
| **MEDIUM-3** | `$1` 位置参数与引号外拼接 `"/tmp/cls-exam/"$REL` 逃过变量展开正则 | 可疑行触发放宽到「行内**任意** `$`」；基线随之加 start-exam-board `:577`（变更记录行的 `${CLS_BACKEND_URL:-…}`，无害展开照样登记） |
| **MEDIUM-4** | 已登记行在 ASCII 逗号后**静默变质**（`/tmp/quiz-answer-incr.json,sub/../../x` 的提取结果与基线逐字相同） | ASCII 逗号不再截断 token（中文标点 `，、。` 仍截断防散文污染），整段进 normpath ⇒ 变质尾巴改变越界多重集 ⇒ 红 |
| **MEDIUM-5** | 删 `OUT_OF_SCOPE_8011` 条目 = 该文件**静默失明**（r2 MEDIUM-2 同类在新常量再现） | 改**动态发现**：rglob 全树扫描覆盖面外含 8011 的文件，与常量做**集合级**对照 —— 删条目/清空/新增债/U3-C 模板化四方向全红 |
| **MEDIUM-6** | U6 seed 两份不受零余量约束（`inbox_preview.py` 登记成 tmp=1 也过交接判据） | 零余量覆盖**全部**条目（seed 不豁免）；U6 要给 seed 加 `/tmp` 须把条目挪去 `SCRIPTS_BASELINE` 人工审阅 |
| **LOW-7** | `curl -o/tmp/cls-exam/…` 短选项连写 ⇒ `tmp_ns=0` 误报为债 | **登记不修**（修它会重开冒充面）；已写进 docstring「已知的保守误报方向」 |

Codex 同时确认：六个交接用例各自承重（含删除对应判据分支的逐一变异表）；
round-2 的 MEDIUM-2/5/6、LOW-8 整改成立；U5-B/U6/U3-C 的基线维护矩阵已给出
（验收单 §四 各交接条目与之一致）。

### round-4（绑 `83cd6104`）— `codex-review-CARD-SKILL-PORT-LINT-r4.md`

**BLOCKER 0 / HIGH 2 / MEDIUM 4 / LOW 5**。两条 HIGH 同根因：**正则切自由文本看不见
引号上下文**——r1→r4 每轮出现的新绕过（逗号截断→冒充子串→白名单边界→跨行拼接→
**引号内空格/开括号冒充**→混合引号拼接→单行点号拼接）都是这一根因的换皮。
本轮不再打正则补丁，对越界判据做**根本性重构（v2 引号感知）**（commit `4446ac81`）：

| 级别 | 缺陷 | 处置 |
|---|---|---|
| **HIGH-1** | `P = "/var/cache /tmp/cls-exam/…"`、`"/var/cache(/tmp/…"` —— 引号内的空格/开括号被白名单当作路径起点证据，冒充成立 | **字面量原子化**：`_literals_in()` 扫描引号字面量（fence 全认、散文只认 backtick span），引号内的空格/括号/逗号/分号/中文标点都是路径字符——整串进 normpath ⇒ 越界红 |
| **HIGH-2** | 混合引号跨行拼接 `("/tmp/cls-exam/"`␊`'../x')`（同引号合并管不到）；单行点号拼接 `("." "./x")`（源码无连续 `..`） | fence 逻辑行合并放宽到**任意引号混用、原样拼接**（引号配对交给扫描器）；`_concat_groups_in()` 把间隙只含空白/括号的相邻字面量**整组求值** ⇒ 拼组后 normpath 越界红。⚠️ 作者自踩一坑：拼接间隙必须取「前闭引号+1→后开引号」，否则间隙永含开引号、分组恒失败——已修并有覆盖表行 |
| **MEDIUM-3** | 引号内分号/中文逗号变质（r3 只修了 ASCII 逗号） | 字面量原子化直接封住，不再依赖「逗号入 token」 |
| **MEDIUM-4** | 跨行负控被 `:577→578` 移位**代为打红**（合并在不在都会红 ⇒ 不承重） | 改**直接函数断言**：合并在 ⇒ 拼出的逻辑行含 `..`；拼接组求值 ⇒ 越界消息含 `/tmp/exam-candidates.json`——两断言各自只被自己考的那层满足 |
| **MEDIUM-5** | U6 seed 带债迁去 `SCRIPTS_BASELINE` 被 seed 完整性断言堵死（留 U6 报零余量、迁过去报「被删」，怎么做都错） | seed 改「**两张表至少一张**登记」；参数用例双向：迁移放行 / 留驻拦截（后者同时抓住 r2 版 seed 豁免的回退） |
| **MEDIUM-6** | 动态扫描可能读未跟踪文件/经符号链接读出树外/整读超大文件 | 符号链接不跟随、>1MB 不整读、`.DS_Store`/`__pycache__`/`.git` 跳过；未跟踪文本文件**仍读（有意）**——覆盖面外新债就该被看见 |
| **LOW-7/9** | 全角标点紧贴（`路径：/tmp/…` ns=0）；fence 裸 token 把尾逗号并进条目 | 登记为保守误报方向，不修（修它会重开冒充面） |
| **LOW-10** | 覆盖表最终 normpath 断言退回 `startswith` 不会被现有合规行抓住；seed 豁免回退无负控 | 前者如实声明为纵深防御（不存在前缀失败而 normpath 成立的合规形态）；后者由 MEDIUM-5 留驻拦截用例覆盖 |
| **LOW-11** | 基线表多出的指标键不被消费（假登记） | 每张 per-file 表钉 `set(键) == 指标集` |

越界基线随 v2 重测（**集合语义**：相同 `(候选, normpath)` 去重）：board-recap 多
`/tmp`（`:58`「禁写 /tmp」声明）、start-exam-board 多 `/tmp`（`:128`）与
`Bash: mkdir -p /tmp/cls-exam`（`:188` 变更行 backtick 命令 span）、quiz-answer 去重为
2 条。另：对照组负控补齐越界/可疑行两条判据（r2 遗留）；覆盖表扩到 **17 行**（含 r4
五形态）。

### round-5（绑 `4446ac81`，D-15 上限最终轮）— `codex-review-CARD-SKILL-PORT-LINT-r5.md`

**BLOCKER 0 / HIGH 4 / MEDIUM 1 / LOW 3**。Codex 收尾判断原文：「**不能认定残余风险
只剩已登记误报和运行期不确定性**；以上仍包含可静态确定、未经声明的漏检」。
⇒ **按 D-15（第 5 轮仍有 HIGH ⇒ 停下交主 session 人审），本卡到此为止，车道不再改
代码**。四条 HIGH 全部实测复现属实（Codex 用 `shlex.split`/`ast.literal_eval` 自证）：

| # | 缺陷 | 性质 |
|---|---|---|
| **HIGH-1** | **拼接组遮蔽**（v2 引入的回归）：`cp "/tmp/cls-exam/a" "/var/cache(/tmp/cls-exam/x"` —— 两个**独立参数**被保守拼组连成一个仍落在命名空间前缀下的串，第二个参数的真实越界被**掩盖**（只查组、不查单字面量） | 修法明确且小：判据改为「每个单字面量 ∪ 每个拼组」的**并集**——v2 实现时只加了组没加单字面量，与设计意图相悖 |
| **HIGH-2** | 扫描器与语言字面量语义的差距：三引号 `"""…"""` 被错误闭合/吞尾；`\x2e\x2e` 源码级转义把 `..` 藏住；shell 单引号内 `\` 不转义、扫描器却吞到行尾 | 手写扫描器无法完全等价语言解析器——需 `ast`/`tokenize`/`shlex` 级方案，超出本卡 |
| **HIGH-3** | 合法拼接仍漏拼：字符串前缀 `r"."`/`u` 阻断间隙匹配；行尾 `+`、行尾注释阻断合并 | 同上，属于「保守超集」假设的反例 |
| **HIGH-4** | fence 识别遗漏：`~~~` 围栏不认；四反引号嵌套三反引号内容行错误切换状态；相邻独立代码块可能跨块合并（叠加 HIGH-1 的遮蔽） | fence 状态机需扩展标记集与嵌套处理 |
| MEDIUM-5 | 去重 + 正文不计裸 `/tmp` ⇒ 已登记的 `/tmp` 条目是**可复用盲槽**（新增 `P = "/tmp"` 不红）；`A,A,B→A,B,B` 次数重分配不可见 | 集合语义已声明、后果未界定 |
| LOW-6 | 分号变质覆盖表行不承重（`/tmp/quiz-answer-incr.json` 本身已越界，截断回归后 16 行仍全过） | 需换「原本合规的载体」做该行 |
| LOW-7 | 三条 v2 新基线条目（`/tmp`×2、backtick 命令 span）的红只能读作**文本基线漂移**，不能直接解释为新增越界/完成整改 | 措辞登记 |
| LOW-8 | rglob 先枚举后过滤，巨型目录仍被遍历（无现存故障证据） | 性能边界登记 |

r4 十一条处置逐项被确认（MEDIUM-4/5/6、LOW-7/8/9/10/11 均成立；HIGH-1/2 的**原始样本**
已拦，本轮报的是推广形态）。覆盖表实际 **16 行**（r4 commit message 误写 17，登记）。

#### 终局裁定与去向（交主 session）

1. **D-15 出口 = 人审**，非通过。五轮轨迹：r1 H1 → r2 H1 → r3 H2 → r4 H2 → r5 H4——
   r1-r3 是**真缺陷递减**（每轮整改后被确认成立），r4-r5 转为**同一根因（手写切分器
   ≠ 语言解析器）的换皮递增**。v2 把最常见形态全封住了，但手写扫描器在语言语义面
   （三引号/转义/前缀/嵌套 fence）注定追不完。
2. **建议的处置**（供人审参考，车道不自行实施）：
   - **最小修**：HIGH-1（单字面量 ∪ 拼组并集，几行改动）+ LOW-6（换载体行）——
     若主 session 判「这两条足以合入」，可授权一轮整改 + 第 6 轮送审（D-15 允许
     主 session 破上限，车道不自破）；
   - **根治**：HIGH-2/3/4 需要真正的解析器方案（fence 内 python 用 `ast.walk` 取
     `ast.Constant`、shell 用 `shlex.split`、fence 标记集扩展 `~~~`/嵌套）——
     建议另立卡（如 `CARD-SKILL-PORT-LINT-PARSER`，排第十四批），本卡的门在其
     合入前作为「第一道防线」继续跑（16 行覆盖表 + 59 用例对已知形态全部有效）。
   - **MEDIUM-5 的盲槽**：根治卡里把越界集合改回多重集 + 把散文裸 `/tmp` 计入
     `tmp_all` 之外再单列一档即可消除。
3. **不因 r5 否定既得结论**：r5 确认 r1-r4 全部整改成立；四条 HIGH 是**新增推广面**，
   不是旧整改失效（旧样本全拦）。门对「新增一处裸 /tmp / 写死 8011 / 树名 / 冒充
   命名空间的常见写法」仍然即红——本卡立项的原始目标（决策页四数字失真、无门锁面）
   已达成并钉住。

### 本 session 额外做的对抗验证（卡文未要求）

#### ① 多视角 Workflow 假绿面搜索 —— ⛔ **未产出，不得当作「无假绿面」的证据**

设计：5 个不同攻击视角（计数语义 / 命名空间放行口径 / 门未测量的面 / 基线维护路径 /
断言是否承重）各自独立找假绿面，每条候选再由 3 个不同角度的裁判（correctness /
reproducibility / materiality）独立投票，要求裁判**亲手执行判据函数复现**，二票以上才计入。

**实际结果：5 个攻击者 agent 全部因 Claude session 配额上限失败**（`agents_error: 5`，
`agents_done: 0`）。workflow 返回 `{confirmed: [], rejected_count: 0}` —— 这个空数组是
**「没跑成」而不是「没找到」**。按「搜索面划窄 = 假阴性」的教训，本条**不构成**任何
「门无假绿面」的证据，如实登记为未完成。

> Run ID `wf_35e15bcd-123`，transcript 在 session 目录下；可在配额恢复后
> `Workflow({scriptPath, resumeFromRunId})` 重跑（失败的 agent 不会命中缓存，会真跑）。

#### ② 层 1 两条无负控断言的承重自验（已完成，见 §二.4-A 第 11 行）

#### ③ 越界判据的边界自验（已完成）

对 11 个形态逐个跑 `escaping_tmp_paths()`，含引号内 / 反引号内 / 中文夹裹 / 中文括号 /
前缀粘连 / 穿越到 `/tmp` 本身；另跑两个验伪锚（无 `/tmp` 文本、裸 `/tmp` 无斜杠）确认
判据不会因异常静默返回空。

⚠️ 其中一个「不符」是**我的期望写错了**而非判据错：`/tmp/cls-exam`（无尾斜杠）
`normpath` 后就是命名空间目录本身 ⇒ 语义上没越界；它的问题是「写法不是钦定形态」，
由子串判据以 `bare_delta=1` 拦下。这个分工已固化成
`test_two_judges_cover_each_other_without_gap`（6 行分工表），并断言「两条都放行」的行
必须真在命名空间内 —— 将来放宽任一条判据，对应行会立刻翻转。

---

## 六 本卡未证明什么

① **不证明整改后的 `start-exam-board` 在 Claude Code 里仍能被触发并跑通** —— 本卡只有静态 lint，
   无端到端 UAT。**建议用户在 Obsidian 里真实触发一次出题流程**（`/start-exam-board from <板>`），
   确认候选池临时文件落到 `/tmp/cls-exam/` 且选点正常。

② **不证明 `scripts/<x>.py` 相对写法被 Claude Code 2.1.263 按 skill 目录解析** —— 正因未证明才把
   相对路径改写整体退回档 B。解锁需 Bash cwd 实证（见 §四 ②）。

③ **不证明 `${CLS_BACKEND_URL:-…}` 在 Claude Code 执行 Bash 时会展开成用户期望的值** —— 只证「不再是
   裸 8011」，没证「换个后端地址真能生效」。缺省分支的行为与改前逐字等价，这一半是可推的；
   非缺省分支未验。

③' **不证明 `mkdir -p /tmp/cls-exam/` 这一步会被 Claude Code 照做** —— 它是散文指令而非代码，
   与整个 skill 的其余步骤同属「模型照办」假设面；本卡没有、也无法用静态门证明这一点。
   相较之下，改前依赖的 `/tmp` 是系统目录、无需创建 —— 这是本次整改**新增**的一个执行前提，如实登记。

④ **不证明 `/tmp/cls-exam/` 与仍在用的 `/tmp/exam-created-event.json` 在多 vault 并发时不互撞** ——
   固定命名空间**不含 vault 维度**（正文 `:107` 只读 `active_board`，全文唯一的 `vault_id` 在 `:307`
   且是占位符，跨 Step 拿不到）。这是为绕开「正文拿不到 vault_id」付出的代价，
   与 `:430/:435` 一并归第十四批解耦卡。

⑤ **不证明档 B 各项在二线宿主的可用性**（U4-A 只证「能被列出」）。

⑥ **不证明决策页「`UserPromptSubmit` 注入 26 行」指的是什么**（9 份 SKILL.md 内 0 命中，口径不可复现）。

⑦ **不证明 live 上 3 份 ≠ HEAD 的差异该不该合回**（只登记，E-4 以 HEAD 为准）。

⑧ **不证明 CI（Python 3.11）上行为一致** —— 本地 venv 是 3.14。新门只用 `re` / `yaml` / `pathlib` /
   `shutil`，无版本敏感 API，但未实跑 3.11。

⑧' **不证明越界判据能看穿 symlink** —— `check_escaping_tmp()` 用 `posixpath.normpath()`
做**纯字符串**规范化，不碰文件系统（也碰不到：SKILL.md 是给模型读的文本，路径在运行期
才存在）。若 `/tmp/cls-exam/link` 是一个指向 `/tmp/elsewhere` 的符号链接，本判据看不见。
这是静态门的固有边界，登记不修 —— 修它需要运行期证据，属另一类卡。

⑧'' **不证明 `_TMP_TOKEN_RE` 的切分覆盖了全部书写形态** —— 它按「空白 / 反引号 / 引号 /
圆括号 / 中文括号 / 逗号 / 分号 / 冒号」切分，已对 11 个形态实测（含引号内、反引号内、
中文夹裹、中文括号、前缀粘连、穿越到 `/tmp` 本身）。但**枚举不等于穷尽**；Codex round-2
被显式要求找这里的反例。

⑧''' **不证明手写扫描器等价于语言解析器**（r5 四条 HIGH 的共同根因）：三引号字面量、
   `\x2e` 源码级转义、字符串前缀 `r`/`u`、行尾 `+`/注释阻断拼接、`~~~` fence、嵌套
   fence —— 手写 `_literals_in`/`_concat_groups_in`/fence 状态机在这些语言语义面上
   有**静态可确定**的漏检（Codex 已逐条实测复现）。根治需 `ast`/`shlex` 级解析器，
   已登记为根治卡建议（见 §五 round-5 终局裁定），本卡的门作为第一道防线继续有效。

⑧'''' **不证明 v2 拼接组的保守超集方向**：r5 HIGH-1 证明「保守拼组」会**遮蔽**独立
   参数的真实越界（只查组不查单字面量）——这是 v2 实现与设计意图（并集）相悖的
   回归，修法明确但按 D-15 停轮未实施，交人审裁定。

⑨ **不证明本卡枚举的下游是穷尽的** —— §四 ⑧ 的两个下游是卡文未列、本卡通过
   `git grep -ln 'start-exam-board'` 逐个排查发现的；已跑的兜底是「`tests/skills` 目录级 + regression
   `--collect-only` + routing 校验器 + PYEOF `compile()`」四重，但**不等于**证明没有第五个下游。

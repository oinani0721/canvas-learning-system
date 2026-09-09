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

### 新门：`backend/tests/skills/test_skill_portability_lint.py`（**114 用例 · 9 条判据**）

| 判据 | 覆盖 | 内容 |
|---|---|---|
| 层 1 frontmatter | 9 份 SKILL.md | 键集**精确相等** `{name, description, argument-hint, allowed-tools, model}`；`name` == 目录名且 kebab-case；`description` 非空；`allowed-tools` 形态（非空 YAML list） |
| 层 2 正文 | 9 份 × **9 指标** | `AskUserQuestion` / `mcp__canvas-learning-mcp__` / `.claude/(skills\|scripts)/` / **`tmp_all` + `tmp_ns`** / **`p8011_all` + `p8011_ns`** / 树名 / `/Users/`，**精确计数，增红减也红** |
| 层 3 scripts | 7 份 × **6 指标** | `/tmp` / **`p8011_all` + `p8011_ns` + `localhost`**（r7 补，原先层 3 一个端口指标都没有 = 与层 2 口径分叉）/ `/Users/` / 树名 精确计数 + **文件集合钉死**（新增脚本即红） |
| **④ 越界路径 v3**（r1 新增；r5 后改真解析） | 9 份 SKILL.md | 越出 `/tmp/cls-exam/` 的 **normpath 集合**精确相等。候选来源：整块 `ast.parse` → **按语法单元累积解析**（`_parse_units`，r7 补）→ `shlex.split` → 白名单裸 token → 散文 backtick span。fence 标记行也按散文扫（r7 补） |
| **⑤ 可疑行**（r2 新增，r3 加宽） | 9 份 SKILL.md | `/tmp` 与 `..` 或**任意 `$`** 同一**逻辑行**的行号集合精确相等 —— **不依赖任何解析**，最后一道（现状 quiz-answer `:98` + start-exam-board `:577`） |
| **⑥ 动态拼接**（本卡自查；r7 换取反口径） | 9 份 SKILL.md | 含 `/tmp` 的常量**参与了折不出来的运算**的行号集合精确相等。口径不是节点白名单，而是「从该常量往上走父链，祖先还能被 `_fold_str()` 完全折成字符串就继续；折不出来 ⇒ 登记」⇒ 新表达式形态默认落进「要登记」一侧（现状全 9 份空） |
| **⑦ 散文父目录**（50-agent 复核找出） | 9 份 SKILL.md | 散文里 `/tmp` 与「上一级/父目录/parent dir」同行的行号集合精确相等 —— SKILL.md 的散文**就是给 agent 的执行指令**，落点可以完全写在中文里（现状全 9 份空） |
| **⑧ 不透明记号**（r6 三类 HIGH 同因收口） | 9 份 SKILL.md | fence 内 `/tmp` 行带反引号（shell 命令替换）或反斜杠（转义含义由读它的语言决定 / 续行）的行号集合精确相等，按**续行组**扫。散文侧看 backtick span 内容 + **嵌入式** span（两侧紧贴非空白）+ 词内反斜杠 + 跨行 span（现状全 9 份空） |
| **⑨ URL 覆盖**（r9 MEDIUM-2） | 9 份 SKILL.md | fence 内给 `CLS_BACKEND_URL` **赋值**的行号集合精确相等 —— 给它赋值就把 `${CLS_BACKEND_URL:-…}` 的缺省形态架空了，等于就地取消本卡的整改，而九项计数与五集合全不变（现状全 9 份空） |

九条判据都是纯函数 `check_frontmatter` / `check_body` / `check_scripts` /
`check_escaping_tmp` / `check_suspicious_tmp_lines` / `check_dynamic_tmp_joins` /
`check_parent_dir_prose` / `check_opaque_tmp` / `check_url_override`
（外加交接判据 `check_handoff_constants`），
`root` 可注入 ⇒ 正控跑树、负控跑 tmp 副本。每条断言消息含 **skill + 指标 + 期望 + 实测**。

**判据 ④⑤⑥⑦⑧⑨ 的分工（不是冗余）**：④ 问「这条路径**算出来**指向哪」，只在能算时定论；
⑤⑥⑦⑧ 都属「**算不出来 ⇒ 要人登记**」这一档，触发面互补 —— ⑤ 看行内 `..`/`$` 的字面
证据（不依赖解析，最后一道）、⑥ 看 `ast` 层面有没有折不出来的运算、⑦ 看散文措辞、
⑧ 看跨语言不可判的记号、⑨ 看整改有没有被同块内的赋值就地取消。⑥⑦⑧⑨ 四条现状**全树命中 0** ⇒ 零余量、零维护成本，任何新写
的此类形态都必须先被人看见。

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
| 2' | 新门 改后绿 | **17** → r1 **31** → … → r6 **79** → 50-agent **88** → r7 **96** → r8 **103** → r9 整改 **114 passed, rc=0** | `portlint-green-final-…` / `dir-tests-skills-r10-20260909T*.txt` |
| 3 | `tests/skills` 目录级 | 开工 **369 passed** → r5 **428** = 369+59 → r10 **483 passed** = 369+114，**全程 0 新红** | `dir-tests-skills-open-…` / `dir-tests-skills-r10-20260909T*.txt` |
| 4 | 只钉不改 shasum | quiz-answer / fsrs_bridge.py / decay_beta.py 开工收工 **逐字节相同** | `shasum-pinned-open-…` / `shasum-pinned-close-…` |
| 4' | live vault 零写 | `find -newer` 在 `.claude` 与 `.claude/skills` 下**均 0**，且**前提「live 路径存在」已断言** | `live-and-domain-r7b-20260909T*.txt` |
| 4'' | 域门 | `fsrs_bridge.py` / `decay_beta.py` 开发树 ↔ live **逐字节一致**（本卡一字节未碰，`daily-review-wrapper.sh` 的 `cmp` 门不会 exit 78） | 同上 |
| 5 | ruff | `check` rc=0 + `format --check` rc=0 | `ruff-final-20260908T092702.txt` |
| 6 | 地盘门 | `git diff --name-only 9303201a fcab3216 -- . ':(exclude)_bmad-output'` = **恰 2 项**（十三个 commit 后仍恰两项：新测试文件 + `start-exam-board/SKILL.md`） | `domain-gate-final-…` + `live-and-domain-r8-…` |
| 7 | regression `--collect-only` | 改前 / 改后同 **rc=0, ERROR 0**；r8 复跑 **1480 collected, rc=0** ⇒ `:430/:435` 被逐字钉死的两个模块级断言未破 | `regression-collect-open-…` / `regression-collect-r8-20260909T*.txt` |
| 8 | live≠HEAD 三份 diff | board-recap / quiz-answer / start-exam-board 落存档，**以 HEAD 为准、不合回** | `live-vs-head-<skill>-20260908T090832.txt` |

**卡文未列、本卡新发现并补跑的两个下游裁判**（见 §四 ⑧）：

| # | 裁判 | 结果 | 存档 |
|---|---|---|---|
| 9 | `check_skill_routing_block.py` | 开工 **66/66** → 收工 **66/66**（C1 ROUTING 逐字节 / C7 FALLBACK 块内 python `ast.parse` / C8 降级≠中止 全绿） | `routing-check-open-…` / `routing-check-close-…` |
| 10 | 5 个 `PYEOF` 块 `compile()` 自检 | quiz-answer 2 + start-exam-board 3 = **5 块全过**（`mutation_kill_identity.py` 的广义提取口径） | 本单 §三 |
| 13 | **性能与断言承重的两次自查** | ① 解析窗口一度开到「块末尾」⇒ `quiz-answer` 的 2746 行 fence 块让 `escaping_tmp_paths()` 单次 **35.9s**、整套超时；`_unit_end()` 定界后 **0.12s** 且漏检面未回来。② 两条 r7 LOW 的修复各做内存变异验证：删掉 fence 同字符判断 ⇒ 指名断言变红；旧分号载体截断后仍越界 ⇒ 证明不了「不截断」 | `evidence-skill-lint/low-fix-mutation-r8-…txt` |
| 12 | **⛔ 一次自我发现的假绿（如实登记）** | r7 首跑 live 零写时用错了 live 根路径（`canvas/canvas-vault/`，实际是 `canvas/canvas-learning-system/canvas-vault/`），且 `2>/dev/null` 把 `find` 的「目录不存在」吞成了 `0` —— **那个 0 是假绿**。同一条命令里的域门 `cmp` 也因此报「不一致」才暴露。修法：判据里**先断言前提**（`test -d` 打印 ✅/⛔），再取数；stderr 不再吞。r7b 存档三项均带前提断言 | `live-and-domain-r7-…`（错的，保留）/ `live-and-domain-r7b-…`（对的） |
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

## 三 与卡文的偏离（两处，请复核者重点看）

### 偏离 ②：Codex 轮次突破 D-15 的 5 轮上限（甲方裁定，非车道自判）

卡文收尾要求「Codex 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0；有代码改动 ⇒ 上限 5」。
**r5 是第 5 轮，仍有 HIGH 4**，车道已按 D-15 停下并在本单写了「交主 session 人审」的终局
裁定（见 §五 round-5）。随后**用户（甲方）指示「请你继续」**，据此继续跑 r6→r9。

协议原文允许这条路：「第 5 轮仍有 HIGH → 停下交主 session 人审」，而主 session 可破上限
（协议 §1 D-15 括注：「D-15 允许主 session 破上限，车道不自破」）。⇒ **本卡的 r6+ 属于
授权后的延续，不是车道自判通过**。若复核者认为该授权不成立，应回到 r5 的终局裁定处置。

**破上限后实际发生的**：r6→r8 三轮又找出 15 条真缺陷（含 4 条 BLOCKER 级形态，虽被 Codex
判为 HIGH），另有一路 50-agent 独立复核找出 8 条。若停在 r5，这些都不会被发现。

---

## 三' 偏离 ①（原第一处）

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
`skills/configure-whiteboard/templates/whiteboard.md.template` 同样在覆盖面外。
⚠️ **本单初稿写「实测 0 债」是声明比证据宽**（2026-09-09 自查更正）：九项里 `claude_dir_ref` 实测 **2**，其余八项才是 0。且该模板会被**逐字复制进每张新白板 md** ⇒ 它是这两处 `.claude/…/` 引用的传播源头，覆盖面外意味着传播不被计数。归 U3-C / configure-whiteboard 卡。

①''' **越界基线改多重集 + 来源前缀（r7/r8）——U5-B / U6 rebase 时必读**：
`ESCAPING_TMP_BASELINE` 的值形如 `fence:/tmp/x` / `prose:/tmp/x`，**按 normpath 那一端**
填（`Bash: mkdir -p /tmp/cls-exam/` 的 normpath 无尾斜杠）。次数与来源都钉死：
· 同一物理路径可能被解析器与裸 token 各计一次 ⇒ **「新增一条」不等于「新增了一处物理路径」**；
· fence 标记行按散文产出，所以格式调整可能让归属在 `fence:` / `prose:` 之间翻转；
· 一增一减不再互相抵消（这正是加来源前缀的原因）。
U5-B 改 quiz-answer 时要同步的不止 `QUIZ_ANSWER_BASELINE`，还有本表 8 项 + 可疑行 `[98]`。

③' ⛔ **下一批排卡依据：另立「Markdown 分块」卡**（Codex r19 的整体判断，原文见 §五 round-19）
本卡的 fence/段落分块不是完整的 CommonMark 容器栈，剩余六条缺陷（列表退出被当 closing、
fence 额度、opening 缺段落上下文、容器过剥、散文段界双向缺陷、code span 空白归一化）
**单层列表、单层引用就能触发**，已复现「只删两个空格，全部正文门仍静默」。
⚠️ **块指纹兜底网接不住这一类**——它继承分块结果，分块错了指纹跟着错。
⇒ 建议下一批排一张卡：要么接入真正的 CommonMark 解析器（`markdown-it-py` 已在
Codex 侧用于对照），要么把分块收敛到「只认最简单的三反引号 fence，其余一律当散文」
并接受由此产生的误报。**本卡不做**（超出「可移植性指标基线」的范围）。

②''' **层 3 补了三项端口指标（r7）**：`p8011_all` / `p8011_ns` / `localhost`，7 份实测全 0。
U6 改 `recap_exam_build.py` / `inbox_preview.py` 时，`U6_SCRIPTS_BASELINE` 的每条要带全 6 个键
（键集有精确相等断言，少一个就红）。

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

### ⛔ 上述「终局裁定」已被用户裁定推翻 —— 后续轮次实际走向

r5 停在 D-15 上限后，用户（甲方）指示「请你继续」。据此**破 5 轮上限继续**，且
**没有走「另立解析器卡」的建议路线，而是在本卡内把根治做完**。r5 之后的代码 commit：

| commit | 内容 |
|---|---|
| `a709856a` | 越界判据 v2 → **v3 真解析**（整块 `ast.parse` + `_fold_str` 折 `+` 链 + `shlex.split`），r1→r5 全部 23 个反例 23/23 通过 |
| `ee4d0913` | **第六条判据**（动态拼接）—— 本卡自查发现的残余边界，非 Codex 报 |
| `069c2150` | 按 r6 四类 HIGH：**第七条**（散文父目录）+ **第八条**（不透明记号）+ fence 行内 span 与缩进降级两处 bug |
| `26d6df62` | 按另一路独立复核：**`_parse_units` 语法单元解析** + 第六条**换取反口径** + fence 标记行入扫 + 层 3 补端口指标 |

### round-6（绑 `a709856a`）— `codex-review-CARD-SKILL-PORT-LINT-r6.md`

**BLOCKER 0 / HIGH 4 / MEDIUM 1 / LOW 5**。Codex 自证「审计期间出现外部修改，收尾采样
HEAD 已推进到 `ee4d0913`」⇒ **它的四条 HIGH 全部早于第六条判据**。逐条实测后的处置：

| r6 HIGH | 实测结论 | 处置 |
|---|---|---|
| **HIGH-1 表达式层**（7 形态：`f"…{'.'}…"` / `% "."` / `.format(".")` / `"".join` / `"."*2` / `"."[0]` / `".x"[:1]`） | **7/7 已被 `ee4d0913` 的第六条判据报红** —— r6 审的版本里没有这条判据 | 不重复修，如实登记 |
| HIGH-1 shell 命令替换 `` `printf .` `` | 真漏 | 第八条（反引号记号） |
| **HIGH-2 语言语义**（JSON `\u002e\u002e\/`、shell 反斜杠续行） | 真漏 | 第八条（反斜杠记号 + 续行组） |
| **HIGH-3 逐行降级丢语义**（heredoc 续行 / 缩进致 `IndentationError`） | 真漏 | 缩进 ⇒ `dedent`+`strip` 重试（bug 修）；续行 ⇒ 第八条 |
| **HIGH-4 fence 边界** | 行首内联 span ` ```…``` ` 真漏；**列表内缩进 fence 实测原本就已抓到**（r6 该项不成立） | 前者按 CommonMark 判为行内 span（bug 修） |
| MEDIUM / LOW ×6 | 登记不阻断 | — |

### 另一路独立复核（50 agent，每条候选三票裁决，绑 v3）

r7 送审前另跑一路多视角复核。它报回 **8 条 confirmed / 7 条 rejected**（rejected 全部
0/3 票，多为「越界串整个不含 `/tmp`，被 `add()` 早退」这一类——**该早退是设计**，门的
名字就是「越出 `/tmp/cls-exam/` 命名空间」）。8 条 confirmed 逐条在**当时 HEAD** 实测：

| # | 报告标题（节选） | 当时 HEAD 实测 | 处置 |
|---|---|---|---|
| 1 | 行尾 `` ; \`` 续行 ⇒ 七条判据全绿（BLOCKER） | 已被第八条报红 | 已关闭 |
| 2 | 续行/开括号换行拆字面量（BLOCKER） | 反斜杠形态已关闭；**开括号换行真漏** | `_parse_units` |
| 3 | bytes 字面量对 `_py_strings` 不可见（HIGH） | 带转义的已被第八条抓；**无转义的真漏** | 第六条取反口径纳入 bytes |
| 4 | fence 标记行整行不进 body（HIGH） | **真漏** | 标记行按散文产出 |
| 5 | `_has_dynamic_tmp_join` 白名单漏 `IfExp`/`Subscript`/`Tuple`（HIGH） | **真漏** | 第六条换取反口径 |
| 6 | `os.pardir` / 双 `dirname` 表达「上一级」（HIGH） | 已被第六条报红 | 已关闭 |
| 7 | 层 3 `SCRIPT_METRICS` 无任何端口/URL 指标（HIGH） | **真漏，口径分叉属实** | 补 3 项，7 份实测全 0 |
| 8 | 散文侧「上一级目录」（MEDIUM） | 已被第七条报红 | 已关闭 |

⛔ **不把它的严重度当裁定**：它绑的是 v3，4 条在实测时已被更晚的判据关闭。真漏的 4 条
按根因归并成 3 项改动（见 `26d6df62`）。

**两路复核合并 16 个形态，当前 HEAD 实测 16/16 报红**；4 个合规形态里 3 个绿、第 4 个
（散文里的裸 `/tmp`）本就在越界基线内 —— 树上八条判据全绿即证它不是误报。

### round-7（绑 `26d6df62`）— `codex-review-CARD-SKILL-PORT-LINT-r7.md`

**BLOCKER 0 / HIGH 6 / MEDIUM 1 / LOW 2**。九条**全部整改**（`fcab3216`），无一条按
「登记不修」处理。动手前先复现：8 个反例当时 **8/8 全漏**，与报告逐字吻合 —— 含
HIGH-6 那条模 7 锯齿边界（实测 6 抓 / 7 漏 / 8 抓 / 14 漏，与 Codex 描述完全一致）。

| r7 意见 | 根因 | 整改 |
|---|---|---|
| **HIGH-1** 双反引号 code span 内的命令替换 | ① span 正则只认单反引号 ② 第八条跳过散文 | ① `_BACKTICK_SPAN_RE` 改 N 开 N 闭（CommonMark）② 第八条在散文侧看 **span 的内容**（不是整行——散文里反引号是 markdown 语法）。全树命中 0 |
| **HIGH-2** `~~~` info 含 `~~~` 被误判 / ` ```not-a-close ` 错误闭合 / 列表首行 fence 不识别 | 三处与 CommonMark 不符 | 行内 span 判定抽成 `_is_inline_span()` 且**只对反引号生效**；闭合行剩余必须为空；`_FENCE_RE` 允许列表项前缀 |
| **HIGH-3** 九行括号语句超窗后拼接关系消失 | 固定 8 行窗口 | `_unit_end()`：边界由**括号深度/引号奇偶/行尾续行符**决定，不由常数决定 |
| **HIGH-4** `AugAssign` 被当安全停止点 | `+=` 本身就是拼接 | 从 `_STATEMENT_NODES` 移除 |
| **HIGH-5** 合法 shell 跨行引号被拆坏 | 降级只累积 Python 侧 | shell 窗口同样累积 |
| **HIGH-6** 续行链切窗丢跨组关联 | 链长上限 6 | 去掉小上限 |
| **MEDIUM** 已登记裸 `/tmp` 成可复用盲槽 | 越界候选去重 | 改**多重集**（顺带修掉「消息写多重集、实现在去重」的名实不符）；基线 4 → 16 项 |
| **LOW-1** fence 同字符要求不承重 + `sandbox` 空跑 | 只考了「长度」那一半 | 补 `~~~` 开、``` 试图闭合的用例；去掉未使用的 fixture 参数 |
| **LOW-2** 分号样本不能证明尾部未截断 | 载体前半本就越界 | 换成 `/tmp/cls-exam/a;sub/../../../x`：截断 ⇒ 合规、不截断 ⇒ `/x` |

**⛔ 整改期间自己踩到并修掉的两处回归（如实登记，已写进 docstring）：**

1. **性能回归**：一度把解析窗口开到「块末尾」以关掉 HIGH-3 的固定上限 ⇒ `quiz-answer`
   有个 **2746 行**的 fence 块，`escaping_tmp_paths()` 单次 **35.9 秒**，整套测试超时。
   `_unit_end()` 轻量定界后回到 **0.12 秒**，而固定上限那个漏检面**没有回来**。
2. **窗口交错回归**：把 Python 与 shell 两个窗口写进同一循环 ⇒ `shlex` 对 `P = (`
   这种单行也「成功」（返回 `['P','=','(']`），Python 的多行累积永远轮不到，HIGH-3
   与开括号换行**整类回来**。改成两个窗口**先后**而非交错。

**新增 `_R7_HIGH_FORMS` 八行形态表**：每行 = 坏形态 + 结构相同的安全对照 + **指名判据**。
指名是必要的 —— 越界判据把整个 backtick span 当路径（已登记的保守方向），若只问
「有没有人红」，HIGH-1 那一行会用一个**错误的理由**通过（实测：安全对照也被越界判据红）。
两条 LOW 的修复各做内存变异验证（删掉同字符判断 ⇒ 指名断言变红；旧载体截断后仍越界
⇒ 证明不了「不截断」），证据 `evidence-skill-lint/low-fix-mutation-r8-*.txt`。

判据仍 8 条，测试 88 → 96；`tests/skills` 457 → **465 passed**。

### round-8（绑 `fcab3216`）— `codex-review-CARD-SKILL-PORT-LINT-r8.md`

**BLOCKER 0 / HIGH 5 / MEDIUM 1 / LOW 1**。⛔ **其中 3 条是 r7 整改自己引入的新回归** ——
这个事实比条数更重要，如实登记在下表「新/旧」一列。九条全部整改，复现率 10 个反例中
7 个当场全漏（另 3 个是我构造得与 Codex 不完全一致、被别的判据代打红，不算关闭）。

| r8 意见 | 新/旧 | 根因 | 整改 |
|---|---|---|---|
| **HIGH-1** `_unit_end()` 把合法语句**定短**（注释里的 `)` / 字符串里的 `)` / 三引号奇偶 / 缺函数体 / 200 行上限） | **新回归** | 用**纯文本**数括号与引号奇偶判语句边界，判不了语言语义。上一版 docstring 声称「只会定长（误报方向）」——**那个声明是错的** | 删掉手写计数，改用 `codeop.compile_command()`（标准库为 REPL 写的语句完整性判据）：返回 code ⇒ 完整、None ⇒ 还没写完、抛错 ⇒ 根本不是 Python。语义正确的同时也解决性能（bash 行立刻判「语法错误」⇒ 不累加 ⇒ O(n)） |
| **HIGH-2** 转义 opening 反引号让 span 整个提不出来 | **新回归** | `\`` 被当作 run 的一部分 | 匹配前先把 `\x` 掩成等长占位符（`_backtick_spans()`） |
| **HIGH-3a** 列表前缀被用于**闭合** | **新回归** | r7 为支持 `- ```python` 而放宽的正则同时用在闭合侧 | `_FENCE_OPEN_RE` / `_FENCE_CLOSE_RE` 拆开：开启允许列表与引用前缀，闭合不允许 |
| **HIGH-3b** 引用块内 fence 整体当散文 | 既存 | `> ` 前缀让 body 无法解析 | 开启行允许 `> `，body 按引用深度剥前缀 |
| **HIGH-4** `AnnAssign` 不区分注解与实际值 | 既存 | `P: "/tmp/cls-exam/x" = "/etc/passwd"` 的常量只是注解 | 上溯时若常量落在 `.annotation` 子树 ⇒ 判为动态 |
| **HIGH-5** 散文里裸写的 shell / 跨行 span | 既存 | 只看「成功提取的 span 内容」 | 加「**嵌入式** span」判据：span 两侧紧贴非空白（分隔符集**刻意不含引号**——命令替换的反引号正是被引号夹住的） |
| **MEDIUM** 候选抵消 | 既存 | 散文与 fence 共用一个多重集额度：去掉散文反引号（−1）可抵消 fence 新增（+1） | normpath 带**来源前缀**（`fence:` / `prose:`）分开钉。同「/tmp 与 8011 各钉两端」一个道理 |
| **LOW** HIGH-3 断言遗漏 heredoc 背景 | 既存 | 纯 python fence 走「整块 ast 成功」那条路，**整个绕开** `_parse_units()` | 形态表那行裹进 heredoc |

**两条不承重的整改各做了内存变异验证**（`evidence-skill-lint/low-heredoc-mutation-r9-*.txt`）：
禁掉 `_py_needs_more` 后，heredoc 形态**由红转漏**（✅ 承重），而纯 python fence 形态
**变异后仍红**（❌ 考不到）—— Codex 这条 LOW 完全成立。

**误报侧的两次自查**（整改中实测踩到，都已收紧）：HIGH-5 第一版写成「行内有反引号」
⇒ 误报 board-recap `:139`（那行的反引号是 `` `Write` `` 之类正常 markdown）；第二版写成
「同一非空白片段」⇒ 仍误报 `:58` / quiz-answer `:98`/`:205`（中文标点不是 `isspace()`）。
最终判据是「嵌入式 span」+ 中英文标点分隔符集，树上八条全绿。

形态表并入 r8 七个形态（共 15 行），测试 96 → **103**。

### round-9（绑 `b5d0e78d`）— `codex-review-CARD-SKILL-PORT-LINT-r9.md`

**BLOCKER 0 / HIGH 5 / MEDIUM 2 / LOW 3**。11 个反例**当场 11/11 全复现**。
⛔ 又有 **2 条是 r8 整改引入的新回归**，另有 **1 条是 r8 已报、r8 整改时漏修的**
（200 行硬上限）。十条整改、一条明确不修并登记（见 §六 ⑬）。

| r9 意见 | 新/旧 | 整改 |
|---|---|---|
| **HIGH-1a** 复合语句续接子句被切断（`if/pass` 认走、孤立 `elif` 转交 shlex） | 既存 | 认走之前先看下一行是不是 `elif`/`else`/`except`/`finally`/`case` |
| **HIGH-1b** 200 行硬上限（201 行整段漏检） | **r8 已报未修** | **去掉行数上限**——`_py_needs_more()` 的剪枝已保证 O(n)（quiz-answer 实测 0.09s） |
| **HIGH-2** 转义掩码作用于 span **内部**，毁掉闭合反引号 | **新回归** | 掩码只用于定位 **opening**；closing 在原串上找（CommonMark：span 内反斜杠是普通字符） |
| **HIGH-3a** closing 允许任意引用前缀 | **新回归** | closing 的引用深度必须**等于** opening 的 |
| **HIGH-3b** 列表→引用嵌套开启行不识别 + body 前缀剥不干净 | 既存 | 开启正则认两种嵌套顺序；body 按 `_CONTAINER_PREFIX_RE` 整体剥 |
| **HIGH-4** 常量与实际赋值脱钩（`"/tmp/…"; P = "/etc/passwd"`） | 既存 | `Expr` 移出安全停止点（树上实测 0 处受影响） |
| **HIGH-5a** `_` `:` 在分隔符表里但也是合法 shell 词的一部分 | 既存 | 分隔符表**去掉全部 ASCII 标点**，只留空白与全角标点 |
| **HIGH-5b** 散文里裸写、连反引号都没有（`P="/tmp/cls-exam/"\.\./x`） | 既存 | 含 `/tmp` 的**词里带反斜杠**即登记 |
| **HIGH-5c** 跨物理行的 code span | 既存 | 新增 `_prose_segments()`：把连续散文并成段再找 span（`_fence_blocks` 对散文是逐行产出的，两行都拿不到完整 span） |
| **MEDIUM-2** `CLS_BACKEND_URL=;` 把缺省形态架空 | 既存 | **新增第九条判据** `check_url_override`（fence 内给该变量赋值即登记，全树 0） |
| **MEDIUM-1** 同一来源内部仍可抵消 | 既存 | ⛔ **明确不修**，登记为设计取舍（§六 ⑬）——唯一修法是候选带物理行号，代价是基线对任何行号移动都红，比问题本身更伤交接 |
| **LOW-1** 安全锚漏更新来源前缀（空跑） | **新回归** | 断言加 `fence:` 前缀 |
| **LOW-2** 中文引号造成新误报 | **新回归** | 分隔符表补 `“”‘’『』〔〕` |
| **LOW-3** 来源翻转的报错会误导交接 | 既存 | 越界判据的消息补一句：`fence:`/`prose:` 是**提取来源**，翻转不等于物理债增减 |

**整改期间的两次自查**：① `_prose_segments()` 第一版把 fence **标记行**也并进段，导致
相邻两个 ``` 凑成假的跨行 span（树上误报 board-recap `:135` / quiz-answer `:165`）——
标记行虽按散文产出（为了让裸 token 扫到 info string 上的路径），但它是段边界。
② 形态表两个安全对照选错了：`elif (P := "/tmp/cls-exam/x")` 的海象、以及孤立的
`"/tmp/cls-exam/x"` 表达式，**本来就该红**（判据行为正确，是对照没选对）。

判据 8 → **9 条**，测试 103 → **114**；形态表 15 → 25 行。

### round-10（绑 `f4dacfe3`）— `codex-review-CARD-SKILL-PORT-LINT-r10.md`

**BLOCKER 0 / HIGH 6 / MEDIUM 1 / LOW 3**，8 反例全复现，十条全整改（`8386e41f`）。
3 条是 r9 引入的新回归。要点：closing run 必须**恰好**等长；剥引用标记后只吃**一个**
空格（`>\s*` 会删掉 Python 缩进）；续接检查要跳过整个缩进块；**空行是块边界**；
分隔符表去掉 `*` 与中文引号（代价：树上三行成保守误报并登记）；预筛改用**解析出的
字符串**（隐式拼接后才出现 `/tmp`）。
⛔ **LOW-3 推翻了我写的 O(n) 声明**：实测 1000/2000/4000 行 = 0.10/0.37/1.40s，
**二次增长**。已更正为 O(k²)，并新增成本断言把「单元长度有界」这个前提钉住。

### round-11（绑 `8386e41f`）— `codex-review-CARD-SKILL-PORT-LINT-r11.md`

**BLOCKER 0 / HIGH 9 / MEDIUM 1 / LOW 1**，11 反例全复现，全部整改（`2c2b6471`）。
3 条是 r10 引入的新回归。**HIGH-3 直接推翻了我上一轮的取舍**：

> r10 我登记三行保守误报时写「零余量不变」——**不成立**。基线只钉行号的话，登记一条
> 误报就等于把那个行号变成**可以塞真实债的槽**：把 `:577` 里的 `` `/tmp/cls-exam/` ``
> 换成 ``P="/tmp/cls-exam/"`printf .`"./x"``（真命令替换，落点 `/tmp/x`），opaque 仍报
> 同一行号、其余判据全空 ⇒ 完全静默。
> ⇒ 修法：登记项带**内容指纹**（`行号:sha8`），换内容即红。

其余：续接判定**第三次重写**（不再猜缩进，交给 `ast.parse`）；`_strip_quote_prefix`
改迭代剥（支持 `>  > ` 且不吃代码缩进）；ATX 标题等纳入块边界；fence info string 不得
含任何反引号、closing 缩进相对 opening；分隔符表**清空**只认真空白（再多两行误报，
共 5 行带指纹登记）；bytes 不预筛；起点纳入可折叠子树；同单元重复赋值；`unset` 形态。

**那条成本哨兵在本轮当场发挥了两次作用**：closing 缩进一度写成绝对阈值、续接判定
一度写得过宽，两次都让块被吞成一整段（最长单元 278 → 545、整套 15s → 66s），
两次都是它先红。终版最长单元 612 行（**语义正确**），加 `lru_cache` 后整套 **3.9s**。

### round-12（绑 `2c2b6471`）— `codex-review-CARD-SKILL-PORT-LINT-r12.md`

**BLOCKER 0 / HIGH 6 / MEDIUM 2 / LOW 3**，11 反例全复现，全部整改。

⛔ **LOW-2 是一条诚信问题，必须单列**：我在 r11 的 commit message 里声称新增了
`test_opaque_baseline_entries_are_content_bound`，Codex 指出**它不在最终提交里** ——
实测 `grep -c` = 0。根因：我在「用 `repr` 重写形态表」时删除了一段区间，把那个测试
一并删掉了，而 commit message 没跟着改。已补回，并在其 docstring 里记下这条教训：
**声称加了断言就要能 grep 到**。

| r12 意见 | 新/旧 | 整改 |
|---|---|---|
| HIGH-1 续接探针拒绝多行 `elif` 头与单行 suite | 新回归 | **去掉探针**——它是多余的：直接继续累加，`_py_strings` 自己会在整条语句完整时成功。同时跳过同级注释 |
| HIGH-2 NBSP/U+3000 被 `isspace()` 放行 | 既存 | 只认 **ASCII 空白**；另加 `_shell_words()` 按 shell 词边界切（`split(" ")` 会错拆引号内空格） |
| HIGH-3 散文仍跨列表项拼段 | 既存 | 列表 marker / HTML 注释纳入块边界；**且块边界行本身是新块首行，不能 `continue` 掉**（整改中踩到） |
| HIGH-4 opening 允许任意缩进 | 既存 | 无容器前缀时缩进 ≥4 是**缩进代码块**，不开 fence |
| HIGH-5 `AnnAssign` 覆盖不算重复赋值 | 既存 | 重复赋值计数纳入 `AnnAssign` |
| HIGH-6 散文裸 shell 的相邻引号拼接 | 既存 | 散文分支入口不再要求「行内有记号」；含 `/tmp` 的词里引号 >2 即登记 |
| MEDIUM-1 多字符列表 marker 下 fence 闭不上 | 新回归 | `open_indent` 取 **fence marker 的列位置**；closing 正则收回 `^[ \t]*` ——**r11 那次的替换其实失败了，正则一直是绝对 `^ {0,3}`** |
| MEDIUM-2 `unset` 多变量 / `-f` 误报 | 既存 | 覆盖多变量与选项；`unset -f` 只删同名函数 ⇒ 排除。残余：`unset C'LS'_BACKEND_URL` 这类引号拼接的变量名，登记不修 |
| LOW-1 耗时哨兵未清缓存 | 新回归 | 断言前 `cache_clear()` |
| LOW-2 声称的测试不在提交 | — | 补回（见上） |
| LOW-3 重复赋值对无关变量误报 | 新回归 | 只在「同名多次赋值 **且其中至少一次的值含 `/tmp`**」时登记 |

判据仍 9 条，测试 132 → **142**，形态表 42 → 51 行。

### round-13（绑 `51282213`）— `codex-review-CARD-SKILL-PORT-LINT-r13.md`

**BLOCKER 0 / HIGH 6 / MEDIUM 3 / LOW 2**，全部复现，全部整改。
⛔ **6 条 HIGH 里 5 条是我 r12 引入的新回归**。

#### ⛔ 八轮的收敛数据（这一轮开始用它做设计决策，而不是只当背景）

| 轮次 | HIGH | 我自己引入的新回归 | 占比 |
|---|---|---|---|
| r7 | 6 | 3 | 50% |
| r8 | 5 | 3 | 60% |
| r9 | 5 | 2 | 40% |
| r10 | 6 | 3 | 50% |
| r11 | 9 | 3 | 33% |
| r12 | 6 | 5 | 83% |
| r13 | 6 | 5 | 83% |

**HIGH 数量七轮没有下降，新回归占比在上升。** 根因一直是同一件事：判据 ④~⑨ 要做的
是「静态判断一条路径最终指向哪」，那需要 markdown + shell + python **三个真解析器**；
我用手写近似做，每补一个边界就开一个新边界。

#### ⇒ 新增**第十条判据 = 兜底网**（本轮最重要的产出，用数据立的）

`tmp_block_fingerprints()`：含 `/tmp` 的 fence 块钉**整块指纹**，含 `/tmp` 的散文行钉
**行指纹**。**不做任何语义分析** —— 没有解析、没有正则边界、没有缩进猜测，
因此几乎没有回归空间。

**立它的实测依据**（不是想法，是数字）：
- 对形态表 51 个反例：**45 个可区分**，分不开的 6 个全是不含 `/tmp` 的 URL/`unset` 形态（归第九条）；
- 对 r13 这一轮的 9 条：**九条判据全部看不见，兜底网区分 8/9**（第 9 条是 `${OTHER:-…:8011}`，不含 `/tmp`，已补进第九条判据）；
- 树上代价：**12 项**（vs 当前 5 项登记）。

它与前九条**互补不取代**：那九条告诉你「是哪一类问题」（报错里有形态名），
这条保证「不管什么形态，块变了就红」。r13 MEDIUM-3 指出的「多行 opaque 记录只绑首行
⇒ 换第二行仍静默」也由它直接封住。新增 `_NET_ONLY_FORMS`（8 行）+ 两条承重断言把
「45/51」和「兜底网自己不能失效」钉住。

#### r13 其余整改

| 意见 | 新/旧 | 整改 |
|---|---|---|
| HIGH-3 `pos += len(word) + 1` 坐标失真（40 空格即漏） | 新回归 | 用 `finditer` 拿真实坐标 |
| HIGH-4 closing 把 opening 自身缩进算成额外额度 | 新回归 | 阈值 = 3 + **容器 marker 宽度**（不含 fence 自身缩进）——CommonMark 说 closing 最多 3 空格是**绝对**的，列表/引用内只是整体右移了 marker 宽度 |
| MEDIUM-1 `unset -f` 排除条件越过命令边界 | 新回归 | 改判定函数：选项只看紧跟 `unset` 的，变量列表止于 `;&\|` |
| MEDIUM-2 URL 放行没绑定约定变量 | 既存 | 含 `8011` 但不含 `CLS_BACKEND_URL` 即登记 |
| LOW-2 指纹测试没检查正式消费端 | 既存 | 直接对 `check_opaque_tmp()` 发问：给「行号对、指纹错」的基线必须红 |
| HIGH-1/2/5/6、MEDIUM-3 | 混合 | **由兜底网接住**（实测 8/9），不再逐个补语义判据 |

判据 9 → **10 条**，测试 142 → **152**，形态表 51 行 + 兜底网专项 8 行。

### round-14（绑 `7dcf96f2`）— `codex-review-CARD-SKILL-PORT-LINT-r14.md`

**BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 5** —— ⛔ **HIGH 从 6 降到 1，八轮来第一次显著收敛。**

**Codex 独立复核确认了兜底网的三个数字**（不是我自证）：
- `_NET_ONLY_FORMS` 八组 **8/8 可由新网区分**（九项计数相同、六项语义输出双方全空）；
- 指名形态表 **51/51 通过**，未发现指名判据选错；
- 「45/51」成立。⚠️ 但**我写的归因是错的**：分不开的六例**不是**「全归 URL/unset」，
  实测是**四例 URL/`unset` + 两例 Python `"/t"`+`"mp/…"` 拼接**（后者由第六条检出）。
  已把断言从「必须不含 `/tmp`」改成「必须能被别的判据接住」——后者才是真正要保证的。

唯一的 HIGH 正是我在 r14 prompt 里**主动请它优先复核**的那个风险：**分块错了，兜底网
跟着错**。两个反例都成立，也都修掉了：

| r14 意见 | 根因 | 整改 |
|---|---|---|
| **HIGH-1A** 一个真实 tab 开头的 ``` 提前闭合围栏 | 缩进按**字符数**算 | 按 **tab 展开后的列数**（CommonMark 就是按列） |
| **HIGH-1B** 把一行移进/移出引用块对指纹静默 | 指纹取的是**剥过容器前缀**的 body，`> P=…` 与 `P=…` 剥完一样 | 指纹改用**原文行**（含容器前缀） |
| **MEDIUM-1** `strip()` 删掉有 shell 语义的尾随空格 | `P="…/.."\␠` 删掉那个空格后反斜杠变续行、路径规范化成 `/tmp` | 指纹**不 strip**，只归一化行尾换行符；opaque 也改存原文行 |
| **MEDIUM-2** `_lead` 减法错删列表容器整体缩进 | r13 我引入的 | 退掉减法，阈值以 fence 标记的**列位置**为基准 |
| **MEDIUM-3** URL 只绑名字**子串** | `${CLS_BACKEND_URL_OTHER:-…}` 用户配了也不生效 | 改**词边界**匹配 |
| **MEDIUM-4** URL 按物理行 | `unset -v \`␊`CLS_BACKEND_URL` 是合法续行 | 改走**逻辑行** |
| **LOW-1** 新网负控没验正式消费端 | 把 `check_tmp_blocks()` 改成恒返 `[]` 后所有断言仍过 | 加断言：给「键对、指纹错」的基线必须红 |
| **LOW-2** sha8 只有 32 位，Codex 真的撞出一对 | 摘要长度是零成本的 | 加长到 **16 位** |
| **LOW-3** 标为 NBSP 的样本实际是 ASCII 空格 | 样本写错 | 更正 |
| **LOW-4** 45/51 的归因不符 | 见上 | 断言改写 |
| **LOW-5** `case = 0` 被软关键字正则当续接 | `case` 是**软关键字** | 要求后跟模式且行尾冒号（200 行独立 `case = 0` 原先被合成一个单元，0.072s vs 0.0016s） |

判据仍 10 条，测试 152。

### round-15（绑 `7245a67a`）— `codex-review-CARD-SKILL-PORT-LINT-r15.md`

**BLOCKER 0 / HIGH 3 / MEDIUM 4 / LOW 1**，全部复现、全部整改。

**Codex 独立确认的事实**（本轮值得单独记）：
- `_R7_HIGH_FORMS` **51/51** 指名判据坏红/安全绿；`_NET_ONLY_FORMS` **8/8** 指纹区分；
- 「45/51」成立，且**未区分的六例确为四 URL + 两 Python 拼接**（我 r14 更正的归因正确）；
- 把 `check_tmp_blocks()` / `check_opaque_tmp()` 在内存改成恒返 `[]`，**当前消费端断言
  均失败 ⇒ 承重**（r14 LOW-1 的整改有效）；
- ⚠️ **r13 的「8/9」无法完整复核**（它的读取面里没有 r13 报告全文）—— 如实登记，
  不能拿 r14 的 8/8 替代。

| r15 意见 | 新/旧 | 整改 |
|---|---|---|
| **HIGH-1** 提前闭合回归 + 引用前缀后的 tab 不计列 | **新回归**（我 r14 引入） | CommonMark 的额度算法**三轮才算对**：closing 缩进 ≤ **容器内容基线** + 3；**无容器时基线 = 0**（opening 自己的缩进不给额度），有容器时 = 容器前缀的**展开列宽**（含 `>`/`- `） |
| **HIGH-2** 标题后段边界缺失 + 散文只绑含 `/tmp` 的物理行 | 既存 | ATX 标题**自成一块**（前后都是边界）；散文指纹改**按段**取 —— 跨行 code span 的第二行可能不含 `/tmp` |
| **HIGH-3** heredoc 结束标记恰好叫 `else` 被当续接 | 既存 | `else`/`try`/`finally` **必须紧跟冒号**；`elif`/`except`/`case` 只要求后面有非空白（冒号可能在续行 —— 这一点我第一版又改错了，把多行 `elif` 头切断，当场被形态表抓住） |
| **MEDIUM-1** URL 只证明名字出现在行内 | 既存 | 绑 `${CLS_BACKEND_URL` 的**展开**，不是裸名字（注释里出现不算） |
| **MEDIUM-2** 逻辑行六次续接上限 | 既存 | 去掉上限（与 `_parse_units` 同理：固定上限只是把缺口挪个位置） |
| **MEDIUM-3** 围栏语言标记未绑定 | 既存 | 块指纹纳入**开启标记行** —— 只把 `sh` 改成 `python`，同一段 `'\x2e\x2e'` 从合规变越界 |
| **MEDIUM-4** `splitlines()` 把 VT 当换行 | 既存 | 新增 `_lines()`：只按 `\n` 切、顺手去 `\r` |
| **LOW** NBSP 样本仍是 ASCII 空格 | 既存 | 用 `\u00a0` 转义写出来 + 加前提断言（`"NBSP" in why ⇒ "\u00a0" in bad`），防它再被静默改回 |

判据仍 10 条，测试 152。

### round-16（绑 `798bbef7`）— `codex-review-CARD-SKILL-PORT-LINT-r16.md`

**BLOCKER 0 / HIGH 3 / MEDIUM 2 / LOW 2**。

⛔ **LOW-1 是本轮最重要的一条，虽然它只是 LOW**：Codex 在内存里恢复我 r15 的两处修复
（旧续接正则、"无容器也给 opening 缩进额度"），**51 条指名形态 + 8 条兜底形态仍
59/59 通过** —— 我修了，但**没有任何断言能证明修的有效**。
⇒ 补了两条**局部回归断言**：`test_fence_indent_budget_has_no_allowance_without_container`
与 `test_continuation_ambiguity_is_resolved_by_union_not_by_guessing`。
**局部修复要有局部断言，不能指望形态表兜。**

#### HIGH-3：同一处被推翻三次之后，改成「歧义取并集」

`else:` 在一段混合 shell + python 的文本里，到底是 **Python 续接子句**还是**恰好长这样
的 heredoc 终止符**（`python3 - <<'else:'` … `else:`），**静态区分不了**。我三次改规则去猜：

| 版本 | 规则 | 被什么推翻 |
|---|---|---|
| r13/r14 | 「后面有非空白就算续接」 | heredoc 的 `else` 被当续接，已解析的整段被丢弃 |
| r15 初版 | 「一律要求带冒号」 | 多行 `elif` 头被切断（当场被形态表抓住） |
| r15 终版 | 「`else` 要冒号、`elif` 要有内容」 | `else:` 形态的终止符又被当续接；合法的 `else \`␊`:` 显式续行反被拒（Codex 给了**双向**反例） |

⇒ **猜不出来就不猜**：歧义点上把**短单元**（在此切断）与**长单元**（继续累加）的候选
**都收进来**。代价是候选变多（误报方向、都要人登记），收益是这一类不再漏。
整改中还踩到两个自己的坑：收了长单元没跳过它覆盖的行（那几行又走 shell 分词，切出
`(/tmp/cls-exam/` 假候选，四个安全对照全被误报）；内层循环遇到 `if` 体内的行就 break，
走不到后面的 `elif`。

| 其余 r16 意见 | 整改 |
|---|---|
| **HIGH-1** closing 忽略引用标记**后**的缩进 + 尾部接受 NBSP/VT/FF | `_indent_cols()` 改数**fence 标记之前的全部内容**的展开列；尾部只 `strip(" \t")` |
| **HIGH-2** `2. ` 被一律当新列表项 + NBSP-only 行被当空行 | CommonMark 里**只有 `1.`/`1)` 能打断段落**；空行判定只认空格/tab |
| **MEDIUM-1** URL 只证明变量展开了、没证明用于该 URL | 只看**含 8011 的那个 shell 词**里有没有 `${CLS_BACKEND_URL`；另纳入 `env -u CLS_BACKEND_URL` |

**登记不修（残余面）**：
- **MEDIUM-2** 容器识别的若干组合（`>    ~~~python` 的 quote 后缩进、列表延续行内开
  fence、`- ` 后五空格的缩进代码、代码里的 `>` 重定向被当引用标记剥掉）。这些需要
  完整的 CommonMark 容器栈，本卡不做；已知**具体改动由原文指纹接住**（Codex 复核确认）。
- **LOW-2** 常量链的**中间值**也进候选：`"/tmp/cls-exam/" + "../" + "cls-exam/x"` 最终
  合规，但中间的 `/tmp/cls-exam/../` 被误报。保守误报方向，登记。

判据仍 10 条，测试 152 → **154**（两条局部回归断言）。

### round-17（绑 `af2d0faf`）— `codex-review-CARD-SKILL-PORT-LINT-r17.md`

**BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 1**，全部整改。

| r17 意见 | 整改 |
|---|---|
| **HIGH-1** 并集只扩张**一次**、且有 40/38 行固定窗口 ⇒ 连续多个 `elif` 仍漏 | 扩张改成**循环**（只要后面还有续接子句就继续），去掉固定窗口 |
| **MEDIUM-1** ⛔ 短长单元**重叠**导致候选重复计数 ⇒ **可抵消额度**（我 r16 引入的新风险） | 长单元只贡献它比上一版**多出来**的候选（多重集差）。实测：一处路径 → 1 个候选，两处 → 2 个 |
| **HIGH-2** 空列表项（`+ ` 后无内容）被当块边界 + `#<NBSP>x` 被当标题 | 列表 marker 后**必须有内容**才算新块；`#` 后只接受空格/tab |
| **MEDIUM-2** URL 的三个残余形态 | `${X:+}`（展开成空、不控制地址）不算放行；先按 `;&\|` 切段再看含 8011 的词；`env -i` 纳入；shell 注释剥离 |
| **MEDIUM-3** 引用 fence closing 双向判错 | 额度基线改成**容器标记本身**的宽度，**不含**标记之后的内容缩进（`>   ~~~py` 的基线是 `> ` 的 2 列，不是 4 列）|
| **LOW-1** 我 r16 新加的续接断言**只修好一半** | 补两条：短单元也必须在（并集的定义是两种都留）；真的检验合法的 `else \`␊`:` 显式续行 |

⛔ **MEDIUM-1 值得单独记**：我 r16 用「并集」解决歧义，本身方向对，但**重叠部分的候选
被计了两次** —— 登记之后就成了一个可以抵消新增路径的额度。这说明「保守方向 = 只增加
误报」这个直觉**在多重集基线下不成立**：多出来的候选也会占位置。修法是长单元只贡献
多重集差。

判据仍 10 条，测试 154。

### round-18（绑 `0dbd2195`）— `codex-review-CARD-SKILL-PORT-LINT-r18.md`

**BLOCKER 0 / HIGH 4 / MEDIUM 6 / LOW 2**。六条整改、六条登记。
⛔ HIGH-1 是我 r17 修 MEDIUM-1 时引入的：`if delta:` 让「候选为空但源码有料」的长单元
被丢弃而 `cur_j` 照样前进。⛔ LOW-1 **第三次**指出「整改没有断言锁住」⇒ 改用**回退
验证**，逐个把修改回退掉、逐个确认断言变红（五处全部承重；过程中发现两次「断言写了
但打不红」）。另修 bytes 进解析、常量链只收最外层、URL 的 fragment 与 `env` 展开顺序。

### round-19（绑 `cb35d97e`）— `codex-review-CARD-SKILL-PORT-LINT-r19.md`

**BLOCKER 0 / HIGH 3 / MEDIUM 4 / LOW 2**。

#### ⛔⛔ 本轮最重要的产出：Codex 对「登记不修那六条」给出了整体判断

我在 r19 prompt 里第一问不再问「还有什么缺陷」，而是问**决策所需的判断**：
「在当前树的实际写法下，这些缺陷是『理论存在』还是『随手一改就中』？」

> **Codex 原文**：「六项登记缺陷**不能归为「理论存在」**。**单层列表、单层引用就能触发**；
> 其中已经复现『**只删两个空格**，全部正文门仍静默』。原文指纹能接住多数正文修改，
> 但**没有消除容器边界的漏检**。**我建议另立 Markdown 分块卡。**」

⇒ **这条进台账（§四 ③'）作为下一批排卡依据**。它推翻了我原先「登记不修 = 可接受残余」
的判断：可触发面比我以为的大得多，且**块指纹兜底网接不住容器边界那一类**。

| r19 意见 | 新/旧 | 整改 |
|---|---|---|
| **HIGH-1** 列表退出被当 closing（只删两个空格即全门静默） | 既存登记 | ⛔ **不修，升级为「另立卡」建议**（见上） |
| **HIGH-2** 长单元源码保住了，但动态判据的**预筛**用扣重后的 `delta` | **我 r18 整改未贯通消费端** | 预筛改用**整段源码**解析出的全部字符串 |
| **HIGH-3** bytes 的普通显式 `+` 加法仍完整漏检 | 既存 | `_fold_str()` 支持 bytes（单块、合法 Python、普通常量加法，不需要特殊转义或跨块分析） |
| **MEDIUM** URL 变量在 path/query 里仍被当作控制地址 | 既存 | 只看 `?` `#` **之前**的主机+端口段 |
| **MEDIUM** `env` 修复出现新回归 + 反向误报 | **我 r18 引入** | `env -i bash -c '…'` 要抓（清环境后子 shell 再展开）；`env -u OTHER sh -c` 不算（删的不是目标变量）；`env -i curl "${X:-…}"` 不算（外层已展开）|
| **MEDIUM** 注释剥离只作用于 `env` 分支 | **我 r18 引入** | 三个分支统一先剥注释 |
| **LOW** 「只收最外层折叠链」「bytes 收录」仍缺承重断言 | 既存 | 补一条三段断言，**逐个回退验证全部变红** |

URL 判据现覆盖 **9/9** 形态（含我 r18 引入的三类回归/误报）。
判据仍 10 条，测试 155 → **156**。

### round-20（绑最终 HEAD 待填）— `codex-review-CARD-SKILL-PORT-LINT-r20.md`

（结果待 Codex 返回后回填。）

### 两个口径反转 —— 本卡最后两轮的实质

r1→r5 是「想到一种写法就补一条规则」，五轮换了五种坏法。r6→r7 把两个判据的**提问方向**
反了过来，这才是收敛的原因：

| 判据 | 原口径（列举式） | 现口径（取反式） |
|---|---|---|
| 第六条 `_has_dynamic_tmp_join` | 「这是不是我认识的动态节点类型」——白名单 `BinOp(+/%)` / `JoinedStr` / `Call` | 「这个表达式能不能被完全折成一个常量」——折不出来就登记 |
| 越界判据的降级 | 「这**一物理行**能不能解析」 | 「从这里起累加几行才构成一个**语法单元**」 |

列举式要求作者先想到 `IfExp`、想到 `Subscript`、想到 bytes、想到开括号换行；取反式让
**任何没想到的新形态**自动落进「要登记」一侧。判据的覆盖面不该由「作者想到了多少种
写法」决定——那是个永远追不上的列表，r1→r5 的轨迹就是证据。

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

### round-20（绑 `8c34481a`）— `codex-review-CARD-SKILL-PORT-LINT-r20.md`

**BLOCKER 0 / HIGH 2 / MEDIUM 5 / LOW 3**。两条 HIGH 里 **1 条是本卡未闭环缺口**，
另 1 条是已裁定另立分块卡的既存问题。

#### ⛔ 本轮最重要的一条：同一个根因的**第三个消费端**

r18 我把「长单元源码保住」改对了，r19 把「预筛用整段源码」改对了 —— r20 发现
`_has_dynamic_tmp_join()` 里判「这次赋值含不含 `/tmp`」的那圈**还停在叶常量**，
而同一个函数下面的 `starts` 那圈从 r11 起就用 `_fold_str()` 了。**同一个文件里两套口径。**

```python
P = "/t" + "mp/cls-exam/x"; P = "/etc/passwd"    # 最终路径是 /etc/passwd
```
两个叶都不含 `/tmp` ⇒ `P` 进不了 `tmp_targets` ⇒ 重复赋值检查整条静默。Codex 实测
**九项计数全部为零、七组附加结果全部为空，含块指纹**。

> **教训写进本轮 commit**：一个判据由「解析 → 预筛 → 判定」三段组成时，改中间那段的
> 输入形态**必须顺着数据流走一遍全部读者**。我连着三轮每轮只修一个读者。

| r20 意见 | 新/旧 | 整改 |
|---|---|---|
| **HIGH-1** 折叠常量的重复赋值漏检（bytes 同形态并入） | **我 r19 整改未贯通第三个消费端** | `tmp_targets` 改用 `_fold_str()` 折叠值 |
| **HIGH-2** 列表退出被当 closing，closing 又不进指纹 | 既存登记 | ⛔ 不修，归 §四 ③' 分块卡（Codex 复核确认「另立分块卡的处置正确」） |
| **MEDIUM-1** 注释剥离不识别引号/参数展开，`printf "#"; unset …` 被截断 | **我 r19 引入** | 换 `_strip_sh_comment()`：POSIX 词首规则 + 引号状态机；`${#VAR}` 不再误判 |
| **MEDIUM-2** 截掉 query/fragment ≠ 只检查主机端口 | 既存（r19 的整改方向对、判准不对） | 判准换成「端口号本身必须**落在** `${CLS_BACKEND_URL:-…}` 这次展开里」 |
| **MEDIUM-3** `env` 双向缺陷：长选项/粘连漏检；无关子进程/外层展开误报 | 半新半旧 | 拆出 `_env_clears_url()`，**逐命令段**判 + 只认单引号 `-c` 脚本且脚本里真出现该变量 |
| **MEDIUM-4** `decode(…, "replace")` 把不同 bytes 折成同一候选 | **我 r19 引入** | 拆 `_fold_const()` 保类型 → 整条折完解**一次** → `backslashreplace` 保身份 |
| **MEDIUM-5** code span 未做 CommonMark 空白归一化 | 既存 | ✅ **在本卡就地修**（Codex 明确说这条不需要容器栈）：换行→空格 + 剥一对首尾空格 |
| **LOW-1** bytes **叶**常量收集缺承重断言 | 既存 | 补断言（隐式相邻拼接走的不是 `+` 那条路，是两处代码） |
| **LOW-2** URL 整体重写一条回归断言都没有 | **我 r19 引入** | 新增 `test_r20_judge_branches_are_load_bearing`，5 组、每组配结构相同的安全对照 |
| **LOW-3** 性能哨兵测不到 r19 新增的整段预筛成本 | **我 r19 引入** | 哨兵改量**整条 `dynamic_tmp_join_lines()`**；`_py_strings` 加缓存（存 tuple、返回复制 list） |

#### 回退验证（9 条，全部承重）

每条整改**单独回退**后，我声称的那一条断言都变红了，且红的是**指名的那一条**：

| 回退的整改 | 变红的断言 |
|---|---|
| HIGH-1 折叠 → 叶常量 | 「折叠常量的重复赋值没被抓到」 |
| MEDIUM-1 注释剥离 → 旧正则 | 「引号内的 `#` 被当成注释开头」 |
| MEDIUM-2 → 截 query/fragment | 「地址由 `OTHER` 决定…判据却放行了」 |
| MEDIUM-3a 去掉长选项/粘连 | 「`env` 清环境形态漏检」 |
| MEDIUM-3b 不看 `-c` 脚本 | 「`env` 误报（清的不是这条命令的环境）」 |
| MEDIUM-4a → `replace` | 「两个不同的不可解码字节折成了同一个候选」 |
| MEDIUM-4b → 逐叶解码 | 「bytes 链被逐叶解码了」 |
| MEDIUM-5 撤销归一化 | 「首尾各一个空格没剥掉 ⇒ 误报」 |
| LOW-1 撤销 bytes 叶收集 | 「bytes 叶常量（隐式相邻拼接）没被收进候选」 |

#### 本轮一次自我发现的探针错误（如实登记）

MEDIUM-4 我第一版探针写的是 `b"/t" + b"mp/\xff/../x"` —— `posixpath` 归一化把
`\xff/..` 整段消掉，两个不同字节都得到 `/tmp/x`，探针**避开了缺陷显形点**，
差点判成「已修好」。改掉 `..` 后才看见真实差异。同 §六「探针避开显形点」一类。

#### Codex 对既有维度的复核结论（未发现问题的部分）

长短单元差集/重叠/扩张失败、heredoc 与续接词歧义、AST 节点覆盖、缓存纯性、
原文切片行号对应、指纹空白/行序/CRLF/末尾换行、来源前缀与交接、`_SPAN_SEP_CHARS`、
backtick 掩码与等长 run —— **均未发现问题**。`_shell_words()` 的边界（转义引号、
未闭合引号、`$'…'`、反引号内空格）仍在，属已登记残余。

### round-21（绑 `55330069`）— `codex-review-CARD-SKILL-PORT-LINT-r21.md`

**BLOCKER 0 / HIGH 2 / MEDIUM 5 / LOW 1**。

#### ⛔ 本轮第一问拿到了想要的东西：折叠口径这条线**收口**

r20 我连着三轮每轮只修一个消费端，于是 r21 prompt 第一问改成「**把名单一次列全**」。
Codex 给了完整的消费端清单（19 行表，逐个标注用的是叶常量 / 折叠值 / 源码字面），
结论是：

> **未发现第四个漏用折叠值的可达 AST `/tmp` 判断**；存在仍只看原文的外围入口，
> 尤其第十条（块指纹），**不能把它宣传成覆盖所有折叠形态的兜底**。

同时 Codex **驳回了我提的「注释剥离要不要统一」**，理由成立、已采纳：

> 注释处理**不应机械统一**：计数、内容指纹本就绑定原文；Python AST 自然忽略 Python
> 注释；可疑／opaque 是保守文本证据。它们不统一调用 `_strip_sh_comment()` 本身不是
> 新缺陷，**URL 语义判据使用一个不完整的 shell 注释器才是本轮确认的问题**。

⇒ 「口径分叉」不等于「缺陷」。判据的**输入面本来就不同**时，统一反而是错的。

#### 两条 HIGH 都在重赋值判据上，但是**两个不同的修点**

| | 形态 | 根因 |
|---|---|---|
| **HIGH-1** | `P = "/t" + "mp/cls-exam/x"; P, = ("/etc/passwd",)` | r20 修好了赋值**值**的折叠口径，没补齐**写入目标**的识别 |
| **HIGH-2** | 同一 fence 里两条**相邻**语句各占一个语法单元 | 判据的**作用域**只到语法单元，两次写入从来不同时被看见 |

两者的坏形态源码里都没有连续的 `/tmp` ⇒ **块指纹兜底网同样不进**。Codex 强调
HIGH-2「**不是已声明的跨块数据流边界**，是同 fence 的普通相邻语句」。

| r21 意见 | 新/旧 | 整改 |
|---|---|---|
| **HIGH-1** 解包 / walrus / 增量赋值 / `for` 重绑都不计写入 | 既存 | 抽出 `_target_names()` + `_assignments()`，覆盖 6 类写入目标 |
| **HIGH-2** 判据只在语法单元内跑 | 既存 | 新增 `_reassigned_after_tmp()`，在**整个 fence 块**上按行序再跑一次 |
| **MEDIUM-1** 按原文切 `;` 会切开单引号脚本（只加 `true;` 就漏） | **我 r20 引入** | `_sh_segments()` 引号感知切段；另补 `-lc` 组合选项、`$'…'` 脚本 |
| **MEDIUM-2** 注释状态机不跟踪参数展开/嵌套引用 | **我 r20 引入** | 抽出 `_sh_protect_mask()`：`${…}` / `$(…)` 用**栈**、每层独立引号状态、`$'…'` |
| **MEDIUM-3** 端口落在展开里 ≠ 展开控制主机（`@userinfo` / 展开整体在 path） | 既存（r20 方向对判准不对） | 判准改为「展开必须是**该 URL token 的开头**，且后面不是 `@`」 |
| **MEDIUM-4** `CLS_BACKEND_URL[0]=''`、`printf -v` 可架空配置 | 既存 | `_URL_ASSIGN_RE` 加数组下标；新增 `_URL_PRINTF_V_RE` |
| **MEDIUM-5** `backslashreplace` 与**字面反斜杠**撞名 | **我 r20 引入** | 抽出 `_decode_bytes()`：先把已有 `\` 转义成 `\\`，编码才是单射 |
| **LOW-1** bytes **叶**分支缺自己的防回归断言 | 既存 | 隐式相邻拼接的单射断言（走的不是 `_fold_str()` 那条路） |

判据仍 **10 条**，测试 157 → **159**。r21 清单点出的冗余分支（`starts` 里旧的
bytes `replace` 解码）已删。

#### 回退验证（12 条，全部承重）+ 一条**被验证为不承重、已删**

12 处整改逐条单独回退，全部让指名的那条断言变红。另有**一条没通过**：

> 我给 `_env_clears_url()` 写过「双引号脚本里 `$` 被转义就算」的分支，回退验证显示
> **它恒不决定结果** —— `\$` 挡在展开前面，那个展开就不再是 URL token 的开头，
> 词级判据 `_url_word_is_controlled()` 必然已经报了。⇒ **删掉该分支**，并把对应断言的
> 失败信息改成真实机制（原文写的是「转义的 `$` 是留给子 shell 展开的」，
> 那是我以为的原因，不是实际生效的那条）。

这正是回退验证的用处：绿的断言里，有一条绿得**不是因为我以为的那个原因**。

#### 本轮我引入的一次回归（当场抓到、当场修）

MEDIUM-3 第一版判准写成「展开必须在**词**的开头」，立刻把
`env -u OTHER sh -c 'curl "${CLS_BACKEND_URL:-…}/x"'` 判成误报 —— 被引号包住的
整条 shell 脚本**也是一个词**，它的开头是 `curl`。改成绑 **URL token 边界**
（前面到最近一个分隔符之间没有别的字符）后两边都对。

#### 仍然登记不修

- `SCRIPT='curl …'; env -i bash -c "$SCRIPT"` —— 需要**数据流**，不是词法。
- 跨**物理行**的引号内容（`_sh_protect_mask()` 逐行重置状态；`_logical_lines()` 只合并
  反斜杠续行）。
- `_shell_words()` 仍不是完整 shell lexer（转义引号 / 未闭引号 / 反引号内空格）。
- 容器栈四条双向反例（`:421/:555`、`:421/:443`、`:283`、`:626`）—— 归 §四 ③' 分块卡。

### round-22（送审绑 `7fc33b61`）— 首发 **0 字节：Codex 配额用尽**，已按协议 §1 重发

#### ⛔ 如实登记：本轮首发未产出结论

首发 stdout **0 字节**，stderr 尾部：

```
ERROR: You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage
       or try again at Sep 15th, 2026 9:25 AM.
tokens used 75,949
```

按协议 §1「0 字节存档重发一次，再 0 字节 → 主 session 人审替代，**不等配额**」执行了
那一次重发。重发**未再报配额错误**并正常推进 ⇒ 走正常轮次，不启用人审替代。
首发存档（0 字节 .md）与其 stderr 保留为证据；`*.stderr*` 按协议不入库。

#### ⛔ 绑定偏差（如实声明，不掩盖）

重发时工作树已含**未提交的 r22 自查整改**，Codex 读到的行号
（`_assignments:1096` / `_sh_protect_mask:1950` / `_url_word_is_controlled:2050`）
属工作树而非 `7fc33b61` 的 blob。⇒ **本轮是「审工作区」不是「绑合并态」**，
按 D-15 它**不能充当**「绑最终 HEAD 且 BLOCKER/HIGH=0」的那一轮，收尾仍需 r23。

#### 我从首发 stderr 里做的事：只取**输入**，不取结论

Codex 首发在耗尽配额前跑过一批探针。按「抢救的推理标题不是裁定」，我**没有**把它的
推理标题当成发现，而是把**探针输入**取出来自己跑了一遍。实测结果（我的复现）：

| 方向 | 形态 | 结论 |
|---|---|---|
| 漏检 | `except … as P` / `import … as P` / `match: case P` | 真漏 —— 这三类的名字在 `ast` 里是**裸字符串**（`ExceptHandler.name` / `alias.asname` / `MatchAs.name`），不是 `Name` 节点 |
| **误报** | 函数体内同名 `P`、`class` 体内同名 `P` | 真误报 —— 上一版对整棵树 `walk` 后**按名字**比，那是另一个绑定 |
| 不是误报 | `if c: P=合规 / else: P=越界` | **应当报** —— 最终值静态不可判，正是本判据的契约 |

⇒ 整改：`_own_nodes()` 按作用域分组（不下钻 `def`/`class`/`lambda`）、`global`/`nonlocal`
声明的名字并回外层、补三类裸字符串绑定 + `def`/`class` 自身的写入。
**推导式刻意不算作用域边界** —— PEP 572 规定其中的海象绑在外层。
27 条形态实测全过，**7 处回退验证全部承重**（第 7 条我第一版变异体不合法，
它让 `_assignments` 去取 `ListComp.name` 直接崩，重做成只改「作用域边界」两处判定才有效）。

#### 重发进行中已实测出的两条（我已独立复现，**留待与重发结论一并整改**）

| | 形态 | 根因 |
|---|---|---|
| ① | `b"mp/\xff/x"`（无效字节）与 `r"mp/\xff/x"`（字面反斜杠）**同名** | r21 MEDIUM-5 我只让 **bytes↔bytes** 单射；单射性是**整个值域**（str ∪ bytes）上的性质 |
| ② | `env -i bash -c 'true' "${VAR:-…8011}/x"` 误报 | `(?P<script>.*)$` 贪婪 —— `bash -c SCRIPT ARG0 …` 里 `-c` 后**只有第一个词**是脚本，其余是位置参数 |

⚠️ 发现后**没有立即改**：Codex 正在读这个文件，中途改动会让它的
「收尾时被审文件与提交一致」自检失败、整轮作废。补丁已备好，等结论一并应用。

#### 重发结果（绑 `7fc33b61`，测试文件 blob `03125650`）— **BLOCKER 0 / HIGH 3 / MEDIUM 8 / LOW 1**

重发未再报配额错误，正常产出。Codex 声明「期间工作区发生外部修改，**动态验证已固定使用
提交中的内存源码**」⇒ 它绑的是**提交态**，所以 HIGH-3（`match: case P`）与 MEDIUM-1
（跨作用域按裸名字合并）在我 r22 自查里**已经修掉**，本轮无需重复整改。

#### ⛔ 本轮最重要的产出：判据**应该长什么样**

> **正确边界应是「同一执行区内的实际绑定与可达执行关系」。** 单个 Python heredoc 应保留
> 跨语句关系；模块、函数、class 的同名局部绑定应区分，`global/nonlocal` 另按实际绑定
> 处理。**相邻 fence 可能是不同示例或不同进程，不应仅凭同名默认串联。**

这句话把我一直在补的东西拆成**三件独立的事**，而我此前把它们混成一件：

| | 我原来的做法 | 正确做法 | 出处 |
|---|---|---|---|
| **绑定** | 整棵树按裸名字比 | 按作用域分组，`global`/`nonlocal` 并回外层 | MEDIUM-1（已在自查修） |
| **可达执行关系** | 按源码行序 | **循环回边 / 互斥分支 / 直线** 三分 | HIGH-1 |
| **执行区** | 「整块是合法 Python」 | 整块 **+ 每个 Python heredoc**；相邻 fence 不串联 | HIGH-2 |

#### ⛔ 它推翻了我上一轮的一个辩护

我把 `if/else` 报红辩护成「静态不可判 ⇒ 该报」。Codex：

> 你担心的互斥分支也确实误报：**即使 `if/else` 两支都赋命名空间内常量，仍报两处**。
> 因此，「整块按直线看」**同时存在漏报与误报**。

⇒ 该辩护不成立。「静态不可判」只在**结果真的取决于运行时**时才成立；两支都合规时，
不可判的是分支，**不是结论**。我拿契约给一个缺陷找了理由。

#### 整改一览（11 处）

| r22 意见 | 整改 |
|---|---|
| **HIGH-1** 源码行序 ≠ 执行顺序（循环回边漏 + 互斥分支误） | `_risky_reassign()` 三分法：任一处在循环体内 / 落在互斥分支 ⇒ 一含一不含即登记；都在直线 ⇒ 只有「先合规后越界」才登记。位置用 `(行号, 列偏移)` |
| **HIGH-2** 整块不是合法 Python 时补查整个跳过 | `_python_regions()`：整块 + 每个 Python heredoc（`<<EOF` / `<<'EOF'` / `<<"EOF"` / `<<-`） |
| **HIGH-3 / MEDIUM-1** | ✅ 我 r22 自查已修（本轮复核绑提交态，故仍报） |
| **MEDIUM-2** 顶层转义字符被当结构字符 | 掩码里被转义的字符**永远**算数据 |
| **MEDIUM-3** `$( (:) … )` 提前出栈 / 反引号无层 | `$(` 层内跟踪裸括号；反引号自成一层（顶层裸 `(` 刻意不跟踪 —— `case x)` 不配对） |
| **MEDIUM-4** URL 边界按原串字符判 | 先 `_sh_strip_quotes()` **剥到不动点**再按 token 判；`\"`（结构）去转义、`\$`（延后展开）保留 |
| **MEDIUM-5** 一处受控放行整词 | `_url_word_hits()` **逐处**判 |
| **MEDIUM-6** `backslashreplace` 与字面反斜杠撞名 | `_ident_text()`：str 与 bytes 走同一套编码，**两边都**先转义已有反斜杠 |
| **MEDIUM-7** `printf -v` 跨命令边界 | 锚在**命令段开头**且 `-v` 在 `--` 之前 |
| **MEDIUM-8** `bash -l -c` 漏 / `-c` 后参数被当脚本 | shell 名进正则参与回溯；opts 的空格参数只放给 `-u`/`--unset`；`-c` 后只取**第一个词** |
| **LOW** 无序 Counter 残留（分号版报、换行版不报） | 单元内与块级共用同一个 `_risky_reassign()`，不一致从根上消掉 |

#### 我自己踩的两个坑（当场发现、当场纠正）

1. **第一版整改改成完全顺序无关** —— 当场把形态表 HIGH-4 的安全对照
   （`P = "/var/cache"` 后 `P = "/tmp/cls-exam/x"`，最终值合规）判红。收紧一处、
   丢掉一整个轴。三分法两边才都保住。
2. **单层剥引号不够** —— `'curl "${V:-…}/x"'` 剥掉外层单引号后 token 仍带内层双引号，
   展开不在第 0 位，把合规写法误报。改成剥到**不动点**。

#### 回退验证（15 处，全部承重）+ 三条**变异体自身写错**的教训

15 处整改逐条单独回退，全部让指名断言变红。过程中有**三条变异体本身不合法**：
把 `ListComp` 加进 `_SCOPE_NODES` 让 `_assignments` 去取 `.name` 直接崩、
`lstrip()` 当字符串前缀用、只加注释的空变异 —— 它们「让测试红了」但红的是**崩溃**
不是断言。重做后其中 **HIGH-1b 暴露出真的缺一条断言**：互斥判定只有在
「**越界分支在前、合规分支在后**」时才独立于直线规则起作用，我原来的用例正好被
直线规则顺带覆盖了。已补该断言。

#### 本轮实测

tests/skills **531 passed**（369 + 162）/ regression 1480 collected / routing 66/66 /
live newer 0（前提已断言）/ 禁改三份逐字节一致 / 地盘门恰 2 项 / ruff 干净 /
动态判据全路径真实树耗时 冷 **337ms** 暖 **107ms**（阈值 10s）。

⚠️ 首发的 0 字节存档 `codex-review-CARD-SKILL-PORT-LINT-r22.md` **保留入库**，
它是配额事件本身的证据（协议 §1 的「0 字节重发一次」由此可追溯）。

### round-23（绑 `b001cf83`，blob `40966c7c`）— `codex-review-CARD-SKILL-PORT-LINT-r23.md`

**BLOCKER 0 / HIGH 5 / MEDIUM 4 / LOW 1**。HIGH 数比上轮**上升**（3 → 5），
但这不是退步 —— 它指出的是**判据的默认方向**错了，而不是又漏了几种结构。

#### ⛔ 本轮最重要的一句

> **暂不支持的执行关系应明确触发登记，不能因源码顺序或解析失败静默放行。**

前几轮我一直在试图证明「这处是安全的」，于是每补一种结构就漏一种新结构：

```python
P = "/etc/passwd"
if False:
    P = "/t" + "mp/cls-exam/x"     # 源码在后, 但根本不执行
```
「源码在后 ⇒ 后执行 ⇒ 最终值」这个推断**只有在后写必经时才成立**。
生成器 `((P := "/etc/passwd") for _ in (1,))` 更直接：求值推迟到 `next()`。

⇒ **翻转默认**：只有同时满足下面五条才沉默，其余一律登记。

| 条件 | 为什么 |
|---|---|
| **必经** | 祖先里没有 `if`/`try`/`except`/`match`/循环（循环体可能一次都不进） |
| **非延迟求值** | 不在生成器表达式里 |
| **源码在后** | 位于全部越界写入之后（位置用 `(行号, 列偏移)`） |
| **双方都非搬运** | `global`/`nonlocal` 迁移过来的记录，父链与调用时机都不可信 |

#### 五条 HIGH 的整改

| r23 意见 | 整改 |
|---|---|
| **HIGH-1** 「非循环非互斥」不等于必经；生成器延迟执行；反向还有循环后无条件赋值的误报 | 翻转默认（见上）。误报侧一并消掉：循环之后的无条件合规写入现在能证明「必然最后执行」⇒ 沉默 |
| **HIGH-2** `nonlocal` 被统一并进模块 | `nonlocal` 解析到**最近的外层函数**（跳过 class），与 `global` **不同目的地** |
| **HIGH-3** 截断整个作用域节点，把在外层求值的默认参数/基类划进内层 | `_outer_eval_children()`：装饰器、默认参数、注解、基类、`returns` 仍属外层 |
| **HIGH-4** 搬运 `global` 写入只合并名字，丢失父链与调用时序 | `_Write.foreign` 标记；`_provably_last()` 对 foreign 记录一律判「证不出」 |
| **HIGH-5** heredoc 定界/重定向/接收命令语义 + 漏 `-c` 字面脚本 | `_python_regions()` 重写：多 heredoc 只有**最后一个**是 stdin；结束标记**整行相等**；`<<-` 逐行剥 tab；定界符可含 `-`；`python -c` 是执行区；接收命令不读 stdin 时**不是**执行区 |

#### 四条 MEDIUM

`builtin`/`{`/`then` 前缀的 `printf -v`；`env -u "VAR"` 的闭引号；`bash -cl` 顺序；
userinfo 要看整个 authority 段（`"${V:-…}":pw@localhost`）；展开层里**双引号内**的
字面 `(` 不该压进结构栈。

#### LOW：二次退化已消

`_risky_reassign()` 原为两两配对 O(tmp×other)。三个判据都能先在 `other` 上**聚合**
（位置取最大、foreign/延迟取存在性）⇒ 每个 `tw` 降到 O(1)。
实测 N=100/200/400/800：**1.6 / 3.2 / 6.4 / 12.7 ms**，每翻倍 **×1.99**
（Codex 测的旧版是 10/39/158/597 ms，×4）。

#### 又一条死代码（回退验证照出来的，本卡第三次）

我给三分法写过「共同循环」判定，回退后**没有任何断言变红** —— `For`/`While` 本来就在
`_CONDITIONAL_NODES` 里，循环体内的写入在上一步「必经性」就已经判掉了，那个检查
**永远到不了**。已删并写明。前两次同类：r21 的 `env` 转义分支、r22 清单点出的
bytes `replace` 冗余分支。**回退验证是唯一能照出这类代码的手段。**

#### 「验过」不等于「钉住」

四条 MEDIUM 我先用临时探针验过就往下走了；回退验证当场照出来：撤掉整改后**一条断言
都不红**。已补 `test_r23_url_judge_edges_are_load_bearing`。
另有一条用例**分不出差异**：我用 `PY_ = 0` 考「结束标记 strip 还是整行相等」，
两种判法都不闭区。换成 Codex 的实际形态（正文里恰好有一行 `PY ` 带尾随空格，
且先 `PY = 0` 让它成为合法 Python 表达式语句）才真正分得开。

#### 刻意保留的保守面（Codex 归为误报，我登记而不放行）

- `try:` 体内写越界、`else:` 写合规 —— try 体抛异常时 `else` 不执行，合规值不保证；
- `match` 的 guard 失败后落到下一个 `case` —— guard 的副作用会留下。

两者最终值确实取决于运行时，按「暂不支持的执行关系应明确触发登记」的口径应当登记。
**如实记入 §六。**

#### 本轮实测

tests/skills **534 passed**（369 + 165）/ regression 1480 collected / routing 66/66 /
live newer 0（前提已断言）/ 禁改三份逐字节一致 / 地盘门恰 2 项 / ruff 干净 /
真实树动态判据全路径 冷 **324ms** 暖 **111ms**。回退验证 **16 处全部承重**。

### round-24（绑 `e22c6d27`，blob `8c13199e`）— `codex-review-CARD-SKILL-PORT-LINT-r24.md`

**BLOCKER 0 / HIGH 6 / MEDIUM 2 / LOW 1**。

#### ⛔ 首先：方向确认了

> **默认方向正确，但目前的沉默条件还不够严。**「没有名单中的祖先」并不等于必经。

r23 的翻转（证明不了安全就登记）被确认是对的。本轮修的是**沉默条件的具体判据**，
不是再次改方向。

#### ⛔ 其中两条是我 r23 引入的回归（Codex 明确标注）

| | 形态 | Codex 原话 |
|---|---|---|
| HIGH-3 | `python3 - 3<<'A' <<'B' <&3` | 「fd 示例已验证属于相对 `b001cf83` 的**回归**」 |
| HIGH-4 | `python3 -W ignore <<'A'` / `'python3' - <<'A'` | 「已验证为 `b001cf83` **能抓**、`e22c6d27` **漏掉**」 |

我 r23 重写 `_python_regions()` 时把「取整行最后一个 heredoc」当成了 shell 语义，
实际语义是**按 fd 与重定向顺序**归属；同时新写的 `_python_reads_stdin()` 没处理
带参数的解释器选项和带引号的可执行词。

#### 六条 HIGH 的整改

| r24 意见 | 整改 |
|---|---|
| **HIGH-1** 祖先黑名单证明不了必经（`with suppress` 吞异常 / `return` 在前 / `except*`） | `_CONDITIONAL_NODES` 补 `With`/`AsyncWith`/`TryStar`；新增**提前离开**判定（同块里 `return`/`raise`/`break`/`continue` 在它之前 ⇒ 到不了） |
| **HIGH-2** `nonlocal` 要找最近**实际绑定该名字**的函数（含形参），且搬运要**迭代到不动点** | `_bound_names()`（赋值目标 + 形参）+ `nonlocal_target()` 逐层外找 + 不动点循环 |
| **HIGH-3** heredoc 按命令/fd/重定向顺序归属 | `_REDIR_RE` 逐条解析 `N<<tag` / `<&N` / `<file`，逐命令段维护 fd 表，取 fd 0 的最终来源 |
| **HIGH-4** 解释器参数与命令边界 | 可执行词先去引号；`-W`/`-X`/`-Q` 吃掉下一个词；`-c'脚本'` 连写；**每个命令段**都看，不再只取第一处 |
| **HIGH-5** 原文里的假 heredoc 标记吞掉后续执行区 | heredoc 扫描改用**去注释 + 引号感知**的版本（`# <<'NO'` / `echo '<<NO'` 不再是重定向） |
| **HIGH-6** 反射式写入完全静默 | `globals()[…]=` / `globals().update(…)` / `exec(…)` / `type P = int` 一律进「证明不了 ⇒ 登记」 |

#### 两条 MEDIUM + 一条 LOW

- **MEDIUM-1** 定义处表达式被**重复归属**：`_own_nodes(root)` 从作用域自己出发时要按
  **字段名**（`args`/`decorator_list`/`bases`/`keywords`/`returns`/`type_params`）整个跳过。
  上一版按「外层求值子节点的 id」比对，而 `iter_child_nodes` 产出的是 `arguments` 节点，
  id 对不上 ⇒ 照样下钻、同一处写入计两次，再被内层 `global` 搬到模块 ⇒ 误报。
- **MEDIUM-2** 「整块能被 `ast` 解析」≠「整块是一个执行区」：`cat <<'A'` 恰好能解析成
  左移表达式。**块里只要出现真 heredoc 就不再取整块**。
- **LOW** `_branch_index` / `_branch_path` / `_in_loop` / `_mutually_exclusive` 整组
  已成死代码（r23 换成必经性判定后），**已删**。

#### 一个两处共用的错误：`&` 不总是命令分隔符

`<&3` / `2>&1` / `&>log` 里 `&` 是**重定向的一部分**。我按字符切段，于是
`python3 - 3<<'A' <<'B' <&3` 被从 `<&` 中间切成两段（fd 关联丢失），
而**同一个 bug** 在 URL 判据那边表现为 `2>&1` 被错切。⇒ 抽出 `_is_sh_separator()`
让两个切段函数共用，免得再分叉。

#### 差点打破三条负控的一次收紧

反射写入检测第一版把 `globals().<任意方法>` 都算成写，结果树上 quiz-answer `:1431` 的
`globals().get("n_att", "null")`（一个**读**）被判成动态拼接，
`test_negative_control_opaque_tmp_must_be_registered` 等**三条负控的前提当场失效**。
收紧到 `update`/`setdefault`/`pop`/`popitem`/`clear`/`__setitem__` 才对。

#### 回退验证 16 处全部承重 —— 但过程中照出**三条考不出差异的断言**

| 断言 | 为什么考不出 | 改法 |
|---|---|---|
| `except* E:` 里放合规写入 | 那是 `ExceptHandler`，早被覆盖 | 写入放进 **`try` 体**，祖先才是 `TryStar` |
| nonlocal 不动点（中间层写 `/var/cache`） | 中间层那次**越界**写入自己迁到 outer 就够报了 | 中间层改成**合规**值 `/tmp/cls-exam/y` |
| 绑定查找含形参 | 原来**没有**对应用例 | 补一条**误报方向**的：`middle(P)` 用形参绑定，`nonlocal` 不该越过它 |

⇒ 「断言通过」有两种：因为修复生效，和**因为别的机制顺带覆盖**。只有单独撤掉修复
再看这条断言会不会红，才分得清。

#### 本轮实测

tests/skills **536 passed**（369 + 167）/ regression 1480 collected / routing 66/66 /
live newer 0（前提已断言）/ 禁改三份逐字节一致 / 地盘门恰 2 项 / ruff 干净 /
真实树动态判据全路径 冷 **363ms** 暖 **154ms**。

### round-25（绑 `cb4fa9f8`）— `codex-review-CARD-SKILL-PORT-LINT-r25.md`

**BLOCKER 0 / HIGH 6 / MEDIUM 2 / LOW 0**。

#### ⛔ 主动指方向奏效：4 条我自己的回归被逐 commit 对照抓出

r24 里 Codex 用逐 commit 对照抓出我两条回归，所以我在 r25 prompt 的**第一问**直接写：

> 请优先对照 **`e22c6d27` 能抓、`cb4fa9f8` 漏掉** 这个方向找。

结果：**确认 4 条**新回归，每条都附「旧版命中、新版 `[]`」的实测与等结构安全对照。

#### 四条回归的**共同形状**：为修一个缺陷新加的判据自己太宽

| 我 r24 加的东西 | 本意 | 副作用 |
|---|---|---|
| `_REDIR_RE` 逐条解析重定向 | 修 fd 归属 | 引号里的 `'<not-a-file'`（普通 argv）也被当重定向，覆盖 fd 0 ⇒ 执行区消失 |
| `_HEREDOC_RE` 带 fd 前缀 | 认 `3<<'B'` | `N = 1 << 2`（左移）也匹配上，`saw_heredoc=True` ⇒ 整块执行区被取消 |
| `_is_sh_separator` 排除 `<&`/`>&` | 修 fd 关联 | `\>&` 里**被转义**的 `>` 也算 ⇒ `printf` 被拼进前段 |
| `body.startswith("c")` | 认 `-c'脚本'` | `-Bc` 里 `c` 不在串首 ⇒ 脚本被当文件名 |

⇒ 整改：三处补**掩码判定**（引号/转义），一处补**存在性检验**。
`1 << 2` 那条的修法不是收紧正则（`<< 2` 在 shell 里确实是合法 heredoc 语法），
而是**要求结束标记确实出现在后面的行里** —— 用「这个解释成立吗」代替「这个模式像吗」。

#### 两条整改未闭合

- **HIGH-5** 裸 `return` / `raise` / `break` **没有子节点**，永远只当父表的**键**、
  不当**值**。我从 `parent.values()` 里找提前离开语句 ⇒ 整类看不见。
  原用例写的是 `return P`，**恰好因为有 `Name` 子节点才被发现** —— 断言绿了一整轮，
  纯属巧合。改成从 `_own_nodes(scope)` 取。
- **HIGH-6** 反射写入名单从 4 项扩到 **10 项**：写入目标要**整棵**走一遍
  （`(globals()["P"],) = (…)` 顶层是 `Tuple`、`for globals()["P"] in …`），
  另补 `dict.update(globals(), …)` / `setattr(sys.modules[__name__], …)` /
  `sys.modules[__name__].__dict__[…]` / `importlib.reload(…)` / `from x import *`。

#### 两条 MEDIUM

- **MEDIUM-1（新误报）**：`_bound_names()` 漏了**仅注解**（`P: str`）与 `del P` 形成的
  局部绑定 ⇒ `nonlocal` 越过那一层、误报外层的合规值被改。
- **MEDIUM-2**：`unset C'LS'_BACKEND_URL` 的变量名**完全由字面词确定**，只是被引号
  拆开。Codex 明确指出这属于本卡正在维护的词法判据，不该归入「另立卡的数据流问题」。
  改法：按命令词定位 `unset` 后，把后续词**逐个去引号**再比 —— 不整行去引号，免得把
  `printf '%s' 'unset CLS_BACKEND_URL'` 这类**数据**也算成命令。

#### 回退验证 10 处全部承重 —— 本轮**零**「考不出差异」

前两轮各出现三条「断言绿得不是因为我以为的原因」，本轮一条都没有。

#### Codex 对我五个提问的实测回答（未发现问题的部分）

`2>&1` / `>&2` / `a |& b` / `a&&b` / `a & b` 五种分隔形态**命令边界均正确**；
`_own_nodes()` 按字段排除、形参识别、不动点搬运**未发现旧抓新漏**；
`globals()[…]=` 触发而 `globals().get(…)` 不触发**未发现整改失效**；
删掉的四个控制流 helper **未发现独立回归**。

#### 本轮实测

tests/skills **538 passed**（369 + 169）/ regression 1480 collected / routing 66/66 /
live newer 0（前提已断言）/ 禁改三份逐字节一致 / 地盘门恰 2 项 / ruff 干净 /
真实树动态判据全路径 冷 **438ms** 暖 **196ms**。

## 六 本卡未证明什么
- **`_provably_last()` 的「整段最早退出」是近似**：Codex r25 指出两个明确的**误报**
  方向 —— `return P` 落在 `if False` 里、或前面的 `raise` 已被对应 `except` 接住时，
  最终的合规赋值其实能执行，本卡仍登记。这是刻意保留的保守面，**不是已证明正确**。

- **`try/else` 与 `match` guard 的保守登记**：`try:` 体内写越界、`else:` 写合规，
  以及 guard 失败后落到下一个 `case` —— Codex r23 把这两类归为**误报**，本卡按
  「暂不支持的执行关系应明确触发登记」的口径**登记而不放行**。两者最终值确实取决于
  运行时，但「登记」意味着有人要看一眼，这是刻意选的方向，**不是已证明为正确**。
- **判据不做真正的可达性分析**：`_provably_last()` 只识别有限几种「能证明安全」的模式，
  其余一律登记。因此**误报面未被量化** —— 只知道 9 份正文上为 0，不知道别的写法密度。
- **`_shell_words()` / `_sh_protect_mask()` 不是完整 shell 词法器**：跨物理行的引号、
  转义引号的完整规则、`$((…))` 算术展开仍是已登记边界。


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

⑧''' ~~不证明手写扫描器等价于语言解析器~~ —— **已在本卡内关闭**（用户授权破 5 轮上限后）：
   `a709856a` 起改真解析（`ast.parse` + `shlex.split`），`26d6df62` 起按**语法单元**
   而非物理行降级。r5 的三引号 / `\x2e` / `r`·`u` 前缀 / 行尾 `+` / `~~~` / 嵌套 fence
   六个面全部由解析器还原。原「另立解析器卡」的建议**作废**。

⑧'''' ~~不证明 v2 拼接组的保守超集方向~~ —— **已关闭**：v3 删掉了整个「保守拼组」机制
   （每个 `Constant` / shell 词是独立候选），r5 HIGH-1 的遮蔽随之消失。

⑨ **不证明八条判据合起来没有漏检** —— 只能声明当前的残余面。**静态可判但未覆盖**的已知
   面：① `_parse_units` 的窗口上限 8，跨 9 行以上的单条语句会切错（树上最长 3 行）；
   ② 第八条只在 fence 内认反引号，散文 backtick span 内的命令替换不认（散文里 backtick
   是 markdown 语法，认了会全树误报）；③ 越界判据的 `add()` 对**整个不含 `/tmp` 的**越界
   串早退（如 `P = "/etc/passwd"`）—— 这是门的名义边界（它叫「越出 `/tmp/cls-exam/`」），
   但落点从 `/tmp` 系搬到别处同样是可移植性债，**当前由第六条的取反口径间接兜住**
   （表达式选择形态会红），纯字面量替换（`tmp_all` 会 −1）由计数判据的「减也红」兜住。

⑩ **不证明「运行期展开」这一档能被静态确定** —— `$1` / `${REL}` / `os.environ.get()` /
   symlink 落点，静态门只能**要求登记**（判据 ⑤⑥⑧ 三条的共同处置），不能算出落点。
   这是设计选择，不是缺陷：假装能算出来才是缺陷。

⑪ **不证明「手写近似」已经从这道门里清干净** —— r5→r8 连续三次栽在同一件事上：
   r5 手写扫描器模拟解析器、r7 手写括号计数判语句边界、r7 手写 span 正则判 code span。
   每次整改都在关掉旧洞的同时开新洞（r8 的 5 条 HIGH 里 **3 条是 r7 整改引入的**）。
   现在剩下的手写件还有两处：`_SPAN_SEP_CHARS`（枚举白名单，判 span 两侧是不是分隔符）
   与 `_backtick_spans()` 的转义掩码（只处理 `\` + 单字符，CommonMark 的转义规则更严：
   只有 ASCII 标点可被转义）。**它们没有对应的标准库判据可换**，故如实登记为残余面。

⑭ **已登记的三条保守误报**（r10 起，`OPAQUE_TMP_BASELINE` 不再全空）：
   quiz-answer `:205`、start-exam-board `:188`/`:577` —— markdown 的 `**粗体**` 紧贴
   code span 边界，被「嵌入式 span」判据当成了 shell 命令替换。
   **为什么不把 `*` 加回分隔符表**：`*` 同样能属于合法 shell 词
   （`P="/tmp/cls-exam/"*`printf a`*` 实测漏检），表里多一个字符 = 多一条放行。
   **方向取舍**：漏检不可接受，误报可以登记 ⇒ 登记这三行，零余量不变（新增仍即红）。
   同族的已知保守误报还有：函数**默认参数**里的合规常量（`def f(p="/tmp/cls-exam/x")`）
   会被第六条判为动态（常量父链是 `arguments`，不是安全停止点），树上实测 0 处。

⑮ **`_parse_units()` 在单元内是 O(k²) 不是 O(n)**（r10 LOW-3，**声明更正**）：
   去掉行数上限后，一个合法的长括号单元里每加一行都要对整个累积块重解析一次。
   Codex 实测 1000/2000/4000 行注释 = 0.10/0.37/1.40s，二次增长。
   **上一版 docstring 与 commit message 里写的「⇒ O(n)」是错的、未经验证** ——
   和 §六 ⑫ 记的是同一个毛病，我在写完那条之后又犯了一次。
   可接受的理由是**单元长度**有界（树上最长 278 行，九份全跑五条判据 0.63s），
   不是块长度有界；该前提由 `test_parse_unit_length_on_current_tree` 钉住（>400 行即红）。

⑬ **不证明多重集能防住「同一来源内部」的抵消**（r9 MEDIUM-1，**明确不修，登记为设计取舍**）：
   把散文里的 `` `/tmp` `` 去掉反引号（`prose` −1）同时另写一处 `` `mktemp -p` `/tmp` ``
   （`prose` +1），多重集总量与来源分布都不变 ⇒ 门照绿。
   **为什么不修**：唯一能防住的办法是让候选带**物理行号**，而那会让基线对任何行号移动
   都报红 —— Codex 自己在 r9 LOW-3 警告过「来源翻转的报错会误导交接」，行号会把这个
   问题放大一个量级（U5-B 改 quiz-answer 时每次插一行就全表红）。**任何不带位置的
   多重集都有这个性质**，这是判据形态的固有代价，不是实现缺陷。
   ⇒ 处置：如实声明，不假装已覆盖。真要堵这一面，应该另立一张「按位置钉」的卡，
   并同时解决基线维护成本，那不是本卡的范围。

⑫ **本卡的保守性声明只覆盖已验证的方向** —— r8 HIGH-1 的教训：上一版 docstring 写着
   「三引号/引号内的括号会让计数偏大 ⇒ 单元偏长（误报方向）」，那句话**没有验证过**，
   Codex 一个反例（`P = ( # )`）就推翻了。凡本文件里说「保守方向 = 误报」的地方，
   除非同时给了反例或变异证据，否则只应读作**作者的意图**，不是已证事实。

⑨ **不证明本卡枚举的下游是穷尽的** —— §四 ⑧ 的两个下游是卡文未列、本卡通过
   `git grep -ln 'start-exam-board'` 逐个排查发现的；已跑的兜底是「`tests/skills` 目录级 + regression
   `--collect-only` + routing 校验器 + PYEOF `compile()`」四重，但**不等于**证明没有第五个下游。

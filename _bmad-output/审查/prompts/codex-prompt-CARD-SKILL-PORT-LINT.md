# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-1）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`，本卡绑定：`9303201a`（U4-A 末 commit） → `ae6a68f3`（HEAD，本卡唯一 commit）。

这张卡做两件事：(1) 新增一道静态门，把 vault 内 9 份 SKILL.md 与 7 份 scripts 的
「可移植性指标」逐份逐项钉成基线，新增命中即红、减少也红；(2) 在 `start-exam-board`
一份 SKILL.md 上做最小整改（临时文件进固定命名空间、后端地址改缺省形态）。

**请只读下面这些**：

1. 本卡代码 diff：
   `git -C <树根> diff 9303201a ae6a68f3 -- . ':(exclude)_bmad-output'`
2. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
3. 改动的那份 SKILL.md 的 diff（已含在 1 里；如需上下文可读
   `canvas-vault/.claude/skills/start-exam-board/SKILL.md` 的 `:160-240`、`:300-310`、`:425-440`、`:575-578`）
4. 基线两份：`_bmad-output/审查/evidence-skill-lint/baseline-counts-open-20260908T090832.txt`
   与 `baseline-counts-close-20260908T092313.txt`
5. regression collect 两份：`_bmad-output/审查/evidence-skill-lint/regression-collect-open-20260908T092313.txt`
   与 `regression-collect-close-20260908T092313.txt`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、任何 live vault
路径下的文件、其它车道的卡文。

## 二 作者自述（请独立核对，不要采信）

1. **三层都是精确相等**，不是 `≤`：层 1 frontmatter 键集、层 2 正文 9 份 × 7 指标、
   层 3 scripts 7 份 × 3 指标 + 文件集合。
2. **负控每条拆到它该拦的那一层**：新增裸 `/tmp/` 只打层 2、frontmatter 多一个键只打层 1、
   新增脚本打层 3 的文件集合与计数两条；另有「未改副本三层全绿」作对照组。
3. **放行口径是写死的字面量，不是前缀类**：`/tmp/cls-exam/`（带尾斜杠）与
   `:-http://localhost:8011`。裸值算式 `bare = 总数 − 放行形态数`，与 shell 裁判逐字同源。
4. **档 B 两条未做的理由**：相对路径改写取决于 Claude Code 执行 Bash 时的 cwd（无实证）；
   frontmatter / allowed-tools / AskUserQuestion / mcp__ 改名都是 Claude Code 行为面。
5. **`:430/:435` 的 `/tmp/exam-created-event.json` 未动**：该字面量被
   `backend/tests/regression/test_g3_3_cas.py:49`（模块级 assert）、`:144`、
   `test_learning_events_schema_contract.py:1013/:1017` 逐字钉死。
6. **quiz-answer / fsrs_bridge.py / decay_beta.py 逐字未动**（shasum 开工收工相同）。
7. **作者对卡文的一处偏离（请重点判）**：卡文原写「`:198` 那段 python 写前加
   `os.makedirs(os.path.dirname(P), exist_ok=True)`」。作者认为那段 python 是**读取方**
   （`json.load(open(P))` + 末尾 `os.remove(P)`），写入方是上一步的 Write 工具，
   所以 makedirs 加在读侧是死代码；改为在 `:188`（Write 之前）加一条
   `mkdir -p /tmp/cls-exam/`。相应地收工实测 `tmpAll=6 / tmpNS=4`（卡文预估 5/3），
   裸值仍 = 2。请判这个偏离是否成立、数字是否自洽。

## 三 请按重要性排序回答的问题

1. **放行口径会不会放过本该拦的形态**？作者只放行两个写死字面量。请判
   `${X:-8011}`（X 不是 CLS_BACKEND_URL）、`/tmp/cls-exam`（无尾斜杠）、
   `/tmp/a/../cls-exam/`、`/tmp/cls-exam/../x` 这类是否都仍被计入裸值。
   反过来：有没有**本该放行却被误拦**的合理形态。
2. **档 B 退回的理由是否成立**——`scripts/<x>.py` 这种相对写法，是否**真的**取决于
   Claude Code 执行 Bash 时的 cwd？若其实按 skill 目录解析，则本卡是过度保守，请指出依据；
   若确取决于 cwd，请说明解锁需要什么形态的实证。
3. **`:430/:435` 只钉不改的依据是否完整**：`grep -rn 'exam-created-event' backend/`
   还有没有作者没列到的钉点？以及 `/tmp/exam-candidates.json` 的「测试零引用」是否穷尽
   （生产侧 / hooks / scripts 有没有读它）？
4. **精确相等基线的维护成本 vs 假绿面**：「减少也红」会不会让 U5-B（要改 quiz-answer）
   rebase 必红？作者的处置是把 `QUIZ_ANSWER_BASELINE` 单列成一段常量 + 注释交接，够不够？
5. **层 3 把 U6 将改的两份脚本锁成零余量**（`board-recap/scripts/recap_exam_build.py`、
   `clear-inbox/scripts/inbox_preview.py`，三项计数实测均 0），而 U6 三张卡在合并队列
   第 3 组、本卡在第 2 组先合。作者的处置是 `U6_SCRIPTS_BASELINE` 单列 + 注释 + 请主 session
   在手册加注。请判这套交接够不够，以及有没有比「钉死 + 交接」更好且**不牺牲**
   「新增命中即红」的写法。
6. **新测试自身有没有假绿面**：某条断言在它声称能看见的漂移下是否真的会红？
   有没有哪条负控其实是被别的原因弄红的（而不是被它点名的那一层）？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出：`file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性——那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量——本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。

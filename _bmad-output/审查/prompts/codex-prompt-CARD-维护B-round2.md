# Codex 独立复核 · CARD-维护B round-2（第八批整改车道）

你是独立对抗复核者。上一轮（round-1）你判 FAIL（BLOCKER 3 / HIGH 5 / MEDIUM 3）。
此后车道经历了第七批主 session 复核（裁定 F-4：三个变异体在最新代码上仍存活）、
以及本卡（CARD-维护B-R2）的定向整改。你的任务：复核整改是否真实、是否引入新洞。

工作树: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix
分支: card/v2-recapfix · 审对象 = `git diff 0c4afeb7..HEAD`（3 个 commit）+ 上述 worktree 的当前文件。
⛔ **读取范围限定**（重要）: 只读下面列出的文件；**不要**读
`backend/tests/regression/fixtures/recap_live_reports/` 下的 .md 内容
（对抗性语料，曾触发你侧过滤器导致输出被截断；需要哈希时用 shasum 即可）。
可自由运行只读命令（git/grep/pytest）与临时副本上的变异重放。

## 审对象清单（delta 文件）

1. `canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py`
   - 模块级 `_SIGNAL_TAIL_NOTES`（≈:876-886）与信号行 strict 模板的可选注记槽（≈:1127-1140）
   - `_FALLBACK_DERIVE_ALLOW` 模块级表（≈:1195-1253，含每条「依据」元数据）+
     `_verify_report` 内改用该表（≈:1955 附近）
   - ⑦/⑧ 收紧（谓语「缺来源锚点」+ 尾段禁裸数字 `[^。\n0-9]`）
   - 删除 `_has_numeric` / `_EXTRA_QUANTITY_CHARS` / `import unicodedata`
2. `canvas-vault/.claude/skills/board-recap/SKILL.md`（仅 ③段铁律附注条款与白名单⑤条目两处；ROUTING 块未动）
3. `backend/tests/regression/test_recap_scan_signals.py`（尾部「CARD-维护B-R2 · survivor 承重门」节，≈:2185 起；含 b1/b2/c1/c2/old-1/d1/d2/⑦门/e1-e4/(f)放行+篡改）
4. `backend/tests/regression/recap_domain_negverify.py`（MUTANTS 5→10；survivor-2 锚点缩进更新）
5. `backend/tests/regression/fixtures/recap_synthetic_signals/`（2 份新 fixture）
6. `_bmad-output/验收单/UAT-CARD-维护B-数字治理域-2026-08-31.md`（覆盖为 v2）
7. `_bmad-output/审查/evidence-maintb-r2/`（车道自存的裁判证据；可对照复跑）

## 车道自称（逐条验证，不要采信）

- (a) 开工在隔离副本重放 S1/S3/S4 + 3 个旧 survivor：三个 F-4 survivor 失败集与原版逐字相同（=确认门没锁住）；旧 survivor-2/3 等已被 v1 新门锁住（有新增红）。
- (b) S1 两道门：b1 SKILL 同步锁（解析 SKILL.md 原因表与 `_NODATA_REASONS` 全等 + 三种篡改门）；b2 表外原因行为门（5 参量，含前缀逃逸「分母为零（补充）」）。
- (c) S3 两道门：c1 多层引用围栏行为门（深度 2/3 + `>>` 无空格，断言拦截理由含「代码块内出现信号名」或「缺信号行」）；c2 `_strip_code_blocks` 单元契约（字面 `> > ``` 三行剥空 + 合法结构误伤锁）。
- (d) S4：允许式表提模块级（纯搬家，196 全绿证明零行为变化）+ d1 自由叙述行为门（7 前缀+裸句）+ d2 允许式绑定结构门（逐条依据可解析/匹配模板正例/不放行 d1 反例 + 反向锁防删空表）+ ⑦/⑧ 收紧（D3 默认）。
- (e) 「口径一致」封闭注记槽（第七批 §三 B-1 建议甲）：e1 放行（紧接/` · `分隔/无来源结论行）、e2 拦截（6 种夹带/近似 + 无据行不适用）、e3 表锁+篡改门、e4 独立叙述行现状锁。开工前先红证据 `evidence-maintb-r2/e1-pre-implementation-red.txt`。
- (f) 含 signals 真语料：live 只读 collect（前后 8 份 shasum+mtime 对账逐字相同）→ scan 真、③段按模板渲染（synthetic 标记落**目录名**——verifier 强制文件名板名==frontmatter board，文件名带后缀会被判「绑定另一块板」，实测）；放行门 + 6 种篡改门。
- (g) 负验证脚本 5→10 条全承重（rc=0），survivor-2 锚点因 (d) 搬家更新缩进。
- (h) 死代码删除（grep 0 命中）+ 卡文 §零 补 E9/死代码/⑦ 口径 + 验收单覆盖 v2（v1 不实行改写+追溯）。
- 裁判：套件 239 passed / 扩大 571 passed / negverify 10/10 / ruff 全绿 / live 8 份前后逐字相同 / skill 协议两脚本与基线一致。

## 你的复核动作（必须做）

1. **亲自重放承重**（在系统临时副本上，像你 round-1 做的那样）：
   S1（`_NODATA_REASONS` 增「任意原因」）、S3（:1011 附近 `bare = re.sub` 改单层剥离）、
   S4（`_FALLBACK_DERIVE_ALLOW` 表尾增 `(re.compile(r"^\s*备注[：:].*派生.*$"), "skill:③段固定句式")`）、
   survivor-9（注记槽三行替换为 `note_slot = r"(?:[^【】]*)"`）、
   survivor-10（`_SIGNAL_TAIL_NOTES` 增「另有仨条」）、
   ⑦ 退化（`派生角色成员缺来源锚点[^。\n0-9]*` → `派生角色成员[^。\n]*`）。
   每条验证**指定的新门**变红（不是随便哪条红），还原逐字节一致。
2. **审注记槽实现**：是否正向封闭表（而非黑名单/自由文本）；槽是否可能被重复/嵌套/分隔符滥用绕过；无据行是否确实不适用。
3. **审三张表同步锁**（`_NODATA_REASONS` / `_SIGNAL_TAIL_NOTES` / `_FALLBACK_DERIVE_ALLOW`）：测试解析 SKILL.md 的锚点是否稳健；⑦ 与 SKILL.md:267（信号行模板）/ :203（叙述句式）的同步是**匹配语义**还是比字面（:203 原文无「角色」二字——车道声称语义归口是正确选择，你裁断）。
4. **审每道放行门是否配了篡改门**（e1 有 e2、(f) 放行有 6 篡改、b1 有 3 篡改、d2 有反向锁；c1 的基线断言是否足够）。
5. **审验收单 v2 每句声明是否比门证明的宽**（尤其：「全部承重」「FOUND 与指定门一致」「(f) 证据边界」「本卡未证明什么」一节是否如实；v1→v2 追溯是否掩盖了别的不实）。
6. **找整改引入的新洞**（注记槽与既有 H-3 尾部黑名单的交互、⑦ 收紧的误伤面、d2 判据的可绕过性、negverify 锚点更新的正确性）。
7. 跑 `pytest tests/regression/test_recap_scan_signals.py -q`（worktree 的 `backend/.venv/bin/pytest`）核对 239。

## 输出格式

- 逐条 finding：severity（BLOCKER/HIGH/MEDIUM/LOW）+ 标题 + `file:line` 实证（附最小复现命令/输入）+ 一句判词。
- 车道自称 8 条（(a)-(h)）逐条给 ✅ 确认 / ⚠️ 部分成立 / ❌ 不成立。
- 最后一行必须是明确的裁决句：「BLOCKER/HIGH 清零：是/否」（若 stdout 被你侧过滤器截断，车道会从 stderr 抢救正文——请把裁决句放在正文开头也重复一遍）。

# 独立复核请求 · CARD-SEB-WRITER-SUBSTRING-TMP · round-2（补读取面）

## ① 背景 + 本轮与 round-1 的差别

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w`
审查绑定：`13ab1b37bd7840a26e568a71a5c77bd3e6d30b13`（与 round-1 **同一个** HEAD；round-1 之后**零代码改动**，只改了 `_bmad-output/` 下的文档）

round-1 的结论是 **BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3**，但它对三个问题明确写了「需要超出限定读取面、未能独立核实」：

- **④** 四张 lint 基线表是否恰等于对应判据函数的实测输出（原读取面只给了表，没给判据函数与完整输入）；
- **⑤** SKILL.md 全文件旧裸字面量计数是否为 0（原读取面只给了 diff）；
- **⑥** `quiz-answer/SKILL.md:3087-3095` 的同族登记是否准确（原读取面没包含它）。

**本轮只做一件事：把那三块读取面补上，请你独立重算/核对。** ①②③⑦ 已在 round-1 作答，无需重复；若你在补读的过程中发现新的 BLOCKER/HIGH，照报。

## ② 本轮补充的读取面（在 round-1 读取面之上追加）

1. `backend/tests/skills/skill_portability_lint.py` 的**判据函数本体**（④ 需要）：
   - `_body_counts()` **`:2309-2330`**、`bare_tmp()` **`:133-138`**、`_TMP_NS_RE` **`:110-120`**
   - `escaping_tmp_paths()` **`:869-935`**、`check_escaping_tmp()` **`:2414-2448`**
   - `suspicious_tmp_lines()` **`:1892-1915`**、`opaque_tmp_lines()` **`:1812-1890`**、`_line_fingerprint()` **`:3015-3028`**、`check_opaque_tmp()` **`:3028-3074`**
   - `tmp_block_fingerprints()` **`:2915-2966`**、`check_tmp_blocks()` **`:2967-2990`**
   - `managed_file_digests()` **`:3302-3325`**、`check_managed_files()` **`:3325-3350`**
   - 四张表本体：`BASELINE` 的 `"start-exam-board"` 段、`ESCAPING_TMP_BASELINE` **`:2037-2072`**、`SUSPICIOUS_TMP_LINES_BASELINE` **`:2074-2095`**、`OPAQUE_TMP_BASELINE` **`:2110-2140`**、`TMP_BLOCK_BASELINE` **`:2141-2215`**、`MANAGED_FILE_DIGESTS` **`:3236-3260`**
2. `canvas-vault/.claude/skills/start-exam-board/SKILL.md` —— **全文**（⑤ 需要全文件计数；④ 的四张表也要拿全文当输入）。
3. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` **`:3070-3100`**（⑥ 需要；本卡对它**只读**，不改）。
4. `_bmad-output/审查/evidence-seb-writer/lint-table-close-20260918T171623.txt` 与 `lint-table-head-*.txt` —— 作者贴出的实测输出（请与你自己重算的结果对照，不要采信）。

⚠️ **round-1 的一条 LOW 是我的 prompt 路径写错造成的**：台账的权威副本在**另一棵树**
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md`（295 行，`:293` = §三.22 (a)(b)）；本车道树里那份 225 行的是**过期副本**。本轮如需核台账请读前者。

## ③ 请回答的问题（只这三条 + 新发现）

- **④ 四张表的独立重算**：以 SKILL.md 全文为输入，分别跑（或按函数语义手算）`_body_counts` 的 `tmp_all`/`tmp_ns`、`escaping_tmp_paths` 的 normpath 多重集、`suspicious_tmp_lines` 的行号集、`opaque_tmp_lines` 的 `行号:指纹` 集、`tmp_block_fingerprints` 的指纹集、以及整文件 sha256，逐项与仓库里那四张表 + `MANAGED_FILE_DIGESTS` 对照。**有没有哪一项对不上？**（作者声称全部实测后贴入。）另请判断：这些表按**行号**钉，本次改动使查重段由 5 行变 31 行、其后每行 +26 —— 有没有**应该漂而没漂**、或**漂了却没被任何测试盖住**的项？
- **⑤ 全文件计数**：SKILL.md 全文里 `/tmp/exam-created-event.json`（旧裸字面量）出现几次？`/tmp/cls-exam/exam-created-event.json` 几次？`CARD-SEB-WRITER-SUBSTRING-TMP` 几次？`in ln for ln in _lines` 几次？`decode("utf-8", "replace")` 几次？（作者声称分别是 0 / 2 / 1 / 0 / 0。）
- **⑥ quiz-answer 同族登记**：`quiz-answer/SKILL.md:3087` 的 `decode("utf-8", "replace")` 之后，`:3091-3095` 是否确实是逐行 `json.loads` + `event_id` 等值？作者据此登记「它无子串面、缺陷面只剩有损解码半个」——**这个描述准确吗**？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：

```
[级别] <一句话结论>
  file:line
  复现思路: <一句话>
```

请在措辞上区分：**负控输入** / **对照输入** / **未被拦下的输入** / **门未覆盖的路径**。
若 ④⑤⑥ 三项经重算全部相符，请明确写「④⑤⑥ 独立重算相符」，不要用「未能核实」代替。

## ⑤ 边界

- **只读**。不要修改任何文件，不要运行会写盘的命令。
- **不连任何数据库**。
- round-1 已报的 1 项 MEDIUM（五门未约束「字段精确等值」，`evid in _rec.get("event_id","")` 这种变异能通过全部五门）与 3 项 LOW **已被接受并登记**，本轮无需重复；其中两项关于验收单表述的 LOW 已按你的意见改正。
- 本卡刻意不做的相邻面（LF 守卫、event_id 形态门）与 quiz-answer 的 4 处裸 `/tmp/` 归后续卡，不按本卡缺陷计。

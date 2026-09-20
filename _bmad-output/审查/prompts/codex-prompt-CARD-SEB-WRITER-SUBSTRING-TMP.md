# 独立复核请求 · CARD-SEB-WRITER-SUBSTRING-TMP

## ① 背景与最小读取面（请只读下列文件/区间，不要全仓扫描）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w`

本次改动的完整差异：

```
git --no-pager diff --no-color 9c4e7e82 13ab1b37bd7840a26e568a71a5c77bd3e6d30b13 -- . ':(exclude)_bmad-output'
```

除该 diff 外，请只读以下区间：

1. `canvas-vault/.claude/skills/start-exam-board/SKILL.md` **`:428-521`** (Step 6.5 标题 :428、```bash fence :432、PYEOF 收尾 :520、fence 关闭 :521) —— Step 6.5 落账块全块（改后）。这是一份 Claude Code Skill 文档，其中 ```` ```bash ```` fence 内的 `python3 - <<'PYEOF' … PYEOF` 块是**会被逐字执行的真代码**。
2. `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` **`:296-352`** —— 同一套写规的参照实现（第十四批 T7-B 落地），本卡逐字沿用其结构。
3. `backend/tests/regression/test_g3_3_cas.py` **`:31-52`, `:134-146`** —— 跨进程锁 / CAS 门，模块级从 SKILL.md 提取落账块。
4. `backend/tests/regression/test_learning_events_schema_contract.py` **`:1012-1040`** —— producer 真跑门。
5. `backend/tests/skills/skill_portability_lint.py` **`:1-45`**（模块 docstring 交接登记）、**`:1985-2015`**（`BASELINE["start-exam-board"]`，字典起始 :1916）、**`:2037-2072`**（`ESCAPING_TMP_BASELINE`）、**`:2074-2095`**（`SUSPICIOUS_TMP_LINES_BASELINE`）、**`:2110-2140`**（`OPAQUE_TMP_BASELINE`）、**`:2141-2215`**（`TMP_BLOCK_BASELINE`）、**`:3236-3260`**（`MANAGED_FILE_DIGESTS`）、**`:3302-3325`**（`managed_file_digests()`）。
6. `backend/tests/skills/test_skill_portability_lint.py` **`:251-280`**（裸值对账 `test_bare_values_match_card_expectations` + 越界基线）、**`:1302-1316`**（受管文件指纹）、**`:2082-2120`**（⑦ 一增一减负控 `test_negative_control_equal_count_swap_must_redden`，本卡改靶）。
7. `backend/tests/skills/test_seb_writer_exact_match.py` —— **全文**（本卡新增的五条承重门）。
8. `_bmad-output/审查/evidence-skill-port-lint-parser/HANDOFF-seb-tmp-decoupling.md` —— 4 处硬钉点的权威描述（本卡的交接来源）。
9. `_bmad-output/验收单/UAT-CARD-SEB-WRITER-SUBSTRING-TMP-20260918.md` —— 本卡验收单（含全部裁判输出的引用）。
10. `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md` **`:293`** —— 台账 §三.22 (a)(b) 两条来源登记。

**这块代码在做什么**：`/start-exam-board` 生成一张检验白板后，Step 6.5 往 vault 根的 `learning_events.jsonl` 追加一条 `exam_created` 事件。该账本有**四方写者**（backend 的 `append_event`、quiz-answer SKILL、ai-linked-doc SKILL、本块），并发时靠 `fcntl.lockf` 记录锁互斥；校验器对**重复 event_id** 判整个账本不合规，所以「查重 → 追加」必须整体互斥且查重必须准确。

**本卡修的两条缺陷**（改前）：
- `:477` `seen = any(json.dumps(evid, ensure_ascii=False) in ln for ln in _lines)` —— 子串查重。历史行里任意**非 event_id** 字段的值恰等于新 evid 时，带引号的 JSON token 在该行命中 ⇒ 新事件被判 duplicate ⇒ **零次落账**。
- `:473` `b"".join(_chunks).decode("utf-8", "replace")` —— 整本有损解码。非法字节换成 U+FFFD 后，一条**无法解码**的历史行变成「有效 JSON」，其 event_id 若等于本次 evid 同样导致零次落账。

## ② 作者自述（请独立核对，不要采信）

1. 查重已从子串改为 **parsed-field 等值**（`json.loads` 后比 `event_id`），且**坏行不构成 duplicate 证据**（逐行严格解码，解不开就跳过）。
2. 坏行**不中止整次追加** —— `except (ValueError, RecursionError): continue` 只吃掉它自己那一行；没有改成整本严格解码（那样一条坏行会让整次事件不落账，方向更坏）。
3. `exam-created-event` 临时路径从裸 `/tmp/` 迁入 `/tmp/cls-exam/` 命名空间，**4 处硬钉点同批改齐**：`test_g3_3_cas.py` 侧在**导入期**（模块级列表推导 + `assert len(_SEB_BLOCKS) == 1`，不改 = collect-time ERROR）、`test_learning_events_schema_contract.py` 侧在**测试函数体内**（运行期断言红）。
4. lint 的全部基线值与 `MANAGED_FILE_DIGESTS` 均为**实测后贴入**，非手写推算；digest 另用 `shasum -a 256` 独立算法互验。
5. ⑦ 一增一减负控改靶到 quiz-answer 后，仍在测「ns +1 与 all +1 同时发生、差值不变」这同一个假绿面（quiz-answer 本卡**只读**）。
6. 普查只登记零改动：9 份 SKILL.md 中「写点嵌在 prompt 模板 fence 内」= 0 处。

## ③ 请按重要性回答的问题

- **⓪ 新门①② 是否真绑在写规上**，而不是绑在夹具自写的账本上？（作者跑了两段负控：段① 只把等值判定改回子串 ⇒ 只有门① 红；段② 只把逐行严格解码改回 `"replace"` ⇒ 只有门② 红。这两段是否**充分**证明两门各自绑在一条独立路径上？有没有哪种改法能让两门同时变绿而缺陷仍在？）
- **① `RecursionError` 与 `ValueError` 合并捕获**是否会吞掉与坏行无关的真实错误？在这个 `try` 的作用域内还有哪些异常可能来自**非坏行**原因？
- **② 迁入 `/tmp/cls-exam/` 后**，`node` 参数路径（`:126` 写明该路径整步跳过 Step 3）上目录是否真有 `mkdir -p`？prose 的顺序是否确实「先建目录、后 `Write`」？有没有**未被拦下的输入**会让 `Write` 落到不存在的目录？
- **③ `test_g3_3_cas.py` 的锁 / CAS 语义是否漂移**？读回从 `decode → str.split` 改成 `bytes.split → 逐行 decode` 之后，`os.lseek` / `os.read` 是否仍在**同一个 fd** 上（POSIX 记录锁按「进程 × 文件」释放，任何第二个 `open()` 都会让锁整体消失）？
- **④ `ESCAPING_TMP_BASELINE` / `TMP_BLOCK_BASELINE` / `OPAQUE_TMP_BASELINE` / `SUSPICIOUS_TMP_LINES_BASELINE` 四张新表**是否恰等于对应函数的实测输出？（手写猜值 = 假绿。）另：这四张表按**行号**钉，本次改动让查重段由 5 行变 31 行、其后每行 +26 —— 有没有哪一项漂移被漏改而恰好没被现有测试覆盖？
- **⑤ 变更记录条目**是否把旧的裸字面量写回了文件？（判据：SKILL.md 里 `/tmp/exam-created-event.json` 计数应为 0，同时 `CARD-SEB-WRITER-SUBSTRING-TMP` 计数 ≥ 1。）
- **⑥ quiz-answer `:3087` 的同族登记是否准确**？（作者称它 `:3091-3095` 已有逐行 `json.loads` + `event_id` 等值 ⇒ 无子串面、缺陷面只剩有损解码半个。本卡对 quiz-answer 只读。）
- **⑦ 门未覆盖的路径**：这五条门之外，落账块还有哪些输入面完全没有门看着？（作者已自陈：尾行无 LF、event_id 形态非法两类是刻意不做的相邻面。除此之外还有吗？）

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：

```
[级别] <一句话结论>
  file:line
  复现思路: <一句话>
```

请在措辞上区分：**负控输入**（为验证门而故意注入的变异）、**对照输入**（改前改后都应绿的输入）、**未被拦下的输入**（现有门放过去的真实输入）、**门未覆盖的路径**（根本没有门看着的代码路径）。

## ⑤ 边界

- **只读**。不要修改任何文件，不要运行会写盘的命令。
- **不连任何数据库**（本卡无库依赖；7691/7687/7692 都不涉及）。
- **不评**以下不属本卡的面：`quiz-answer/SKILL.md` 的 `harness_tree` 解析与它那 4 处裸 `/tmp/`（归 P6-B / U5-B）；本卡刻意不做的两个相邻面（LF 守卫、event_id 形态门）——如认为它们是缺陷，请标 `LOW` 并注明「相邻面、已登记」，不要按本卡缺陷计。
- 评价标准是**这次改动是否正确且完整**，不是「还能加什么功能」。

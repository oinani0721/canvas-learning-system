# CARD-G1-1 H1R 复审请求（BATCH-2026-09-18-第十五批 · 车道 card/p8-backend · round-4）

> 本轮是 r3（GLM-5.3）判「PARTIAL」后的**补漏复审**。r3 发现：**HIGH-1R**（`**用户批注 L128**:` 形式仍漏召回 + census 3 处不实）与 **LOW-1**（空行跨行层可收未加粗 `> Claude：…` 引用行，未见真数据实例）。本 commit 修 HIGH-1R；LOW-1 的处置说明见 §②-4。请独立复核：HIGH-1R 是否闭合、census 是否已真、是否引入新问题、LOW-1 的处置是否可接受。
> r3 存档：`_bmad-output/审查/codex-review-CARD-G1-1-r3.md`；r2（ZCode）存档：`_bmad-output/审查/zcode-review-CARD-G1-1-r2.md`。

## ① 背景与最小读取面（只读这些，不要漫游仓库）

- 树根（你的 cwd）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend`；分支 `card/p8-backend`
- **审查绑定**：`bf3a765c`（= `git rev-parse HEAD`；`git --no-pager diff --stat --no-color bf3a765c HEAD -- . ':(exclude)_bmad-output'` 为空即仍绑定）
- 本卡 H1+H1R 全整改面 = `git --no-pager diff --stat --no-color a07608b8 bf3a765c`（恰 2 文件，+156/−3；**全文内嵌于附录 A**）
- 请读取（相对树根）：
  1. `scripts/annotation_search.py` **全文**（890 行；重点 `MARKERS["user_bold_zh"]` 与 `extract_block` 中文空行分支）。
  2. `backend/tests/unit/test_annotation_search.py` **全文**（1102 行；`(g)①′` 段四形态 + 三负控 + 真锚 `:23`/`:174`）。
  3. `_bmad-output/审查/codex-review-CARD-G1-1-r3.md` **全文**（你要闭合的 HIGH-1R/LOW-1 原文）。
  4. 整改裁判存档（`_bmad-output/审查/evidence-g11/`）：`h1r-behavior-*.txt`（**87 passed**）、
     `h1r-negctl-3H-*.txt`（摘除定位符分支 → 4 条指定测试红、HEAD 还原 sha 逐字同）、
     `unit-close-h1r-*.txt` + `close-h1r.nodeids`（目录级 32 failed，与基线 diff 只 `＜`、与上一轮 close **逐字同**）、
     `h1r-annotation-search-*.txt`（r3 的 L128 原输入现 `marker_hits=1 shown=1`；r2 输入回归 `shown=1`；确定性 sha ×2 同）、
     `jev-triage-bf3a765c.json`（本 delta 分诊：两文件均 **pass**）、
     `h1-behavior-final-*.txt` / `h1-negctl-1-*.txt` / `h1-negctl-2-*.txt`（上一 commit 的 85 passed 与两段负控，供对照）。
  5. `_bmad-output/审查/phase0a-annotation-truth/A01-source-boundary-draft.json`（私人 root 面）与契约 `…批注真相层实施契约.md` `:126-144`。

## ①附录 A：H1+H1R 全整改 diff（a07608b8 → bf3a765c，逐字内嵌；文中个别用词出自被审代码自身，非本请求措辞）

```diff
diff --git a/backend/tests/unit/test_annotation_search.py b/backend/tests/unit/test_annotation_search.py
index e125fba5..1910de86 100644
--- a/backend/tests/unit/test_annotation_search.py
+++ b/backend/tests/unit/test_annotation_search.py
@@ -31,6 +31,12 @@ ANCHOR_PLAN = "_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力
 ANCHOR_PLAN_LINE = 494
 ANCHOR_CARD = "_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md"
 ANCHOR_CARD_LINE = 163
+# H1 整改（ZCode r2）真数据锚：中文容器头 + 空行 + 引用用户原话的布局。
+ANCHOR_ZH = "_bmad-output/审查/2026-08-02-规模化结构检索-审查请求-给ChatGPT.md"
+ANCHOR_ZH_LINE = 23
+# H1R（ZCode r3）真数据锚：未括注定位符形态 `**用户批注 L128**:`。
+ANCHOR_ZH_LOC = "_bmad-output/implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md"
+ANCHOR_ZH_LOC_LINE = 174
 
 # 与真 A01 同 root_id / privacy_ceiling 的最小副本（8 root）。fixture 自带，
 # 这样「私人 root 从 A01 算出来」这件事在 fixture 上也是真的被算出来的。
@@ -175,6 +181,87 @@ def test_user2_continuation_is_captured_in_excerpt(six_forms, capsys):
     assert records[0]["excerpt"].split("\n") == ["**User2：**", "续写正文第一行 kw-alpha", "续写正文第二行"]
 
 
+# --------------------------------------------------------------------------
+# (g)①′ 中文容器头（H1 整改，ZCode r2 HIGH-1；评审样例 = 本 fixture 的 f7）
+# --------------------------------------------------------------------------
+@pytest.fixture()
+def zh_container(tmp_path: Path):
+    """中文粗体容器头四形态 + 三个负控输入。
+
+    真数据对应：审查/2026-08-02-…:23（空行 + 引用）、验收单/Story-2.1-…:429
+    （冒号在粗体外）、research/round-23-…:13（限定词「触发」）、
+    implementation-artifacts/epic-1/1-8-…:174（未括注定位符，r3 HIGH-1R 补）。
+    """
+    base = tmp_path / "zh"
+    base.mkdir()
+    # 评审样例形态：冒号在粗体内，正文在**空行之后**的 blockquote 里
+    (base / "f7-zh-inside.md").write_text(
+        "**用户批注原文（这是本轮要回答的靶心）：**\n\n> 「我这里引用的真正原因 kw-zh」\n\n尾巴\n",
+        encoding="utf-8",
+    )
+    # 冒号在粗体外（真数据 :429 形态，紧邻续行）
+    (base / "f8-zh-outside.md").write_text(
+        '> **用户批注（步骤 1，line 125）**：\n> "你这里给我的快捷键我无法使用 kw-zh"\n', encoding="utf-8"
+    )
+    # 限定词「触发」（真数据 round-23:13 形态）
+    (base / "f9-zh-suffix.md").write_text('> **用户原话触发**:\n> "你这里返回笔记的精确片段 kw-zh"\n', encoding="utf-8")
+    # 定位符形态（真数据 epic-1/1-8:174 形态——r3 HIGH-1R 补漏）
+    (base / "f13-zh-locator.md").write_text(
+        "3. **用户批注 L128**: 确认 Claudian 应自动检测 vault 变化 kw-zh\n", encoding="utf-8"
+    )
+    # 负控①：Claude 自述语（关键词与冒号之间夹长正文）不得命中
+    (base / "f10-claude-label.md").write_text(
+        "**用户原话 3 个 callout 名字对应 Canvas 真实机制**: 这是 Claude 自己的话 kw-zh\n", encoding="utf-8"
+    )
+    # 负控②：无冒号的 topic 描述不得命中
+    (base / "f11-topic.md").write_text(
+        "核心决策：**用户批注（Obsidian callout）是否应该直接写入 Graphiti 作为燃料**，kw-zh\n", encoding="utf-8"
+    )
+    # 负控③：裸中文形态（无粗体）属 T3 转述面，不得命中
+    (base / "f12-naked.md").write_text("采纳用户原话：Claude 转述了用户的话 kw-zh\n", encoding="utf-8")
+    return base, write_a01(tmp_path)
+
+
+def test_zh_container_heads_hit_with_exact_lines(zh_container, capsys):
+    base, a01 = zh_container
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-zh", "--json"], capsys)
+    assert code == 0, err
+    got = {(os.path.basename(r["path"]), r["line"]): r["marker"] for r in json.loads(out)}
+    assert got == {
+        ("f7-zh-inside.md", 1): "**用户批注原文（这是本轮要回答的靶心）：",
+        ("f8-zh-outside.md", 1): "**用户批注（步骤 1，line 125）**：",
+        ("f9-zh-suffix.md", 1): "**用户原话触发**:",
+        ("f13-zh-locator.md", 1): "**用户批注 L128**:",
+    }
+    assert len(set(got.values())) == 4, "四个形态的 marker 文本必须各异"
+
+
+def test_zh_container_blank_line_then_quote_is_not_empty(zh_container, capsys):
+    """评审样例的真数据布局：标签行与引用之间隔一个空行 —— 必须仍可召回。
+
+    修复前该布局被判空槽、默认不列（08-02:23 即此形态——marker 修好了却「看不见」）。
+    """
+    base, a01 = zh_container
+    code, out, err = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-zh", "--json"], capsys)
+    assert code == 0, err
+    assert "empty=0" in err
+    record = [r for r in json.loads(out) if os.path.basename(r["path"]) == "f7-zh-inside.md"][0]
+    assert record["empty"] is False
+    assert record["excerpt"].split("\n") == [
+        "**用户批注原文（这是本轮要回答的靶心）：**",
+        "> 「我这里引用的真正原因 kw-zh」",
+    ]
+
+
+def test_zh_precision_controls_do_not_fire(zh_container, capsys):
+    """负控三个：Claude 自述语 / 无冒号 topic / 裸中文转述 均不得出现。"""
+    base, a01 = zh_container
+    code, out, _ = run_cli(["--root", str(base), "--a01", str(a01), "--keyword", "kw-zh", "--json"], capsys)
+    assert code == 0
+    names = {os.path.basename(r["path"]) for r in json.loads(out)}
+    assert names == {"f7-zh-inside.md", "f8-zh-outside.md", "f9-zh-suffix.md", "f13-zh-locator.md"}
+
+
 # --------------------------------------------------------------------------
 # (g)② --story
 # --------------------------------------------------------------------------
@@ -499,6 +586,28 @@ def test_real_anchor_card_line_163(capsys):
     assert hits[0]["date"] == "2026-08-25"
 
 
+def test_real_anchor_zh_container_line_23(capsys):
+    """H1 整改真数据锚：zcode r2 点名的关键文件（除该容器头外整文件零 marker）。"""
+    code, out, _ = run_cli(["--keyword", "靶心", "--a01", str(REAL_A01), "--json"], capsys)
+    assert code == 0
+    hits = [r for r in json.loads(out) if r["path"] == ANCHOR_ZH and r["line"] == ANCHOR_ZH_LINE]
+    assert len(hits) == 1, f"08-02 请求书:{ANCHOR_ZH_LINE} 必命中（H1 修复点）"
+    assert hits[0]["marker"].startswith("**用户批注原文（")
+    assert hits[0]["category"] == "审查"
+    assert hits[0]["date"] == "2026-08-02"
+    assert hits[0]["date_source"] == "filename"
+    assert "真正担心的问题" in hits[0]["excerpt"], "空行后的引用必须进摘录（否则仍读作空批注）"
+
+
+def test_real_anchor_zh_locator_line_174(capsys):
+    """H1R 真数据锚：未括注定位符 `**用户批注 L128**:`（zcode r3 HIGH-1R 修复点）。"""
+    code, out, _ = run_cli(["--keyword", "L128", "--a01", str(REAL_A01), "--json"], capsys)
+    assert code == 0
+    hits = [r for r in json.loads(out) if r["path"] == ANCHOR_ZH_LOC and r["line"] == ANCHOR_ZH_LOC_LINE]
+    assert len(hits) == 1, f"epic-1/1-8:{ANCHOR_ZH_LOC_LINE} 必命中（H1R 修复点）"
+    assert hits[0]["marker"] == "**用户批注 L128**:"
+
+
 @pytest.mark.parametrize("keyword", ["FSRS", "跨vault", "README"])
 def test_real_themes_are_non_empty(keyword, capsys):
     code, out, _ = run_cli(["--keyword", keyword, "--a01", str(REAL_A01), "--json"], capsys)
@@ -918,9 +1027,10 @@ def test_output_is_deterministic_across_separate_processes(six_forms):
 
 
 def test_marker_table_shape():
-    assert len(mod.MARKERS) == 10
+    assert len(mod.MARKERS) == 11
     callouts = sorted(k[len(mod.CALLOUT_PREFIX) :] for k in mod.MARKERS if k.startswith(mod.CALLOUT_PREFIX))
     assert callouts == ["BMAD-ANNO", "error", "hint", "info", "note", "question", "tip", "todo", "warning"]
+    assert "user_bold_zh" in mod.MARKERS
 
 
 @pytest.mark.parametrize(
@@ -932,12 +1042,18 @@ def test_marker_table_shape():
         ("> [!WARNING] 同上", "[!WARNING]"),
         ("**User 修正：改口", "**User 修正："),
         ("**User Comment: english variant", "**User Comment:"),
+        ("**用户批注原文（这是本轮要回答的靶心）：**", "**用户批注原文（这是本轮要回答的靶心）："),
+        ("> **用户批注（步骤 1，line 125）**：", "**用户批注（步骤 1，line 125）**："),
+        ("**用户原话触发**:", "**用户原话触发**:"),
+        ("3. **用户批注 L128**: 确认 Claudian 应自动检测 vault 变化", "**用户批注 L128**:"),
     ],
 )
 def test_contract_t1_t2_variants_are_matched(line, expected):
     """契约 :131/:134 点名、且真数据里确实出现过的形态，逐条钉住。
 
-    实测支撑：`**User**：` 1 处、`[!todo]+` 10 处、大写 callout 3 处（2026-09-19 于本树）。
+    实测支撑：`**User**：` 1 处、`[!todo]+` 10 处、大写 callout 3 处（2026-09-19 于本树）；
+    中文容器头 4 处真容器头（审查/2026-08-02-…:23、验收单/Story-2.1-…:429、
+    research/round-23-…:13、implementation-artifacts/epic-1/1-8-…:174——r2/r3 两轮整改补测）。
     """
     hits = mod.find_markers(line)
     assert hits, f"{line!r} 应当命中"
diff --git a/scripts/annotation_search.py b/scripts/annotation_search.py
index 53e501f0..913e1d1d 100644
--- a/scripts/annotation_search.py
+++ b/scripts/annotation_search.py
@@ -9,6 +9,15 @@
 
 * 粗体 User 族：``**User：`` / ``**User:`` / ``**User ：`` / ``**User2：`` /
   ``**User 修正：`` / ``**User Comment:`` 等（契约 ``:134``）。
+* 中文容器头族（H1 整改，2026-09-19；ZCode r2 → r3 两轮复核）：契约 ``:130/:134`` 的
+  「明确中文『用户批注/反馈/修正/原话』」。覆盖冒号两形态——冒号在粗体内
+  （``**用户批注原文（这是本轮要回答的靶心）：**``）与冒号在粗体外
+  （``**用户批注（步骤 1，line 125）**：``）——外加限定词（原文/触发）、定位符
+  （``**用户批注 L128**:``）与括注（≤30 字符）。
+  真数据 4 处真容器头：``_bmad-output/审查/2026-08-02-…:23``、
+  ``_bmad-output/验收单/Story-2.1-…:429``、``_bmad-output/research/round-23-…:13``、
+  ``_bmad-output/implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md:174``。
+  ⚠️ 不带粗体的裸中文形态（``用户批注：``）多系转述（T3 面），不纳入。
 * callout 族：``[!question]+`` / ``[!error]+`` / ``[!tip]+`` / ``[!note]+`` /
   ``[!warning]+`` / ``[!hint]+`` / ``[!info]+`` / ``[!BMAD-ANNO]``，blockquote
   （``> [!x]+``）与行内两种形态都算。
@@ -61,13 +70,25 @@ DEFAULT_A01 = os.path.join(
 PRUNE_DIRS = frozenset({".obsidian", "__pycache__", "node_modules", ".git"})
 
 # --- marker 表 -------------------------------------------------------------
-# name -> 正则。一族粗体 User + 八个 callout 类型，逐条可数（len(MARKERS) == 9）。
+# name -> 正则。两族粗体（ASCII User 族 / 中文容器头族）+ 九个 callout 类型，
+# 逐条可数（len(MARKERS) == 11；callout 九个 = question/error/tip/note/warning/hint/info/todo/BMAD-ANNO）。
 # `\*{0,2}` 覆盖契约 :131 T2 的「marker 被粗体符号拆开」形态（`**User**：`，
 # 真数据 1 处：`验收单/Story-2.1-Phase1-成熟度升级-2026-05-03.md:279`）。
 # callout 一律 IGNORECASE —— Obsidian 的 callout 类型本就大小写不敏感，
 # 真数据里 `[!WARNING]` / `[!NOTE]` 共 3 处，逐字小写匹配会漏掉。
 MARKERS = {
     "user_bold": re.compile(r"\*\*User(?:\s?\d)?\s?(?:修正|Comment)?\*{0,2}\s?[：:]"),
+    # H1 整改（ZCode r2 HIGH-1 → r3 HIGH-1R）：中文粗体容器头。两形态 = 冒号在粗体内
+    # (`**用户批注原文（…）：**`) / 冒号在粗体外 (`**用户批注（步骤 1，line 125）**：`)；
+    # 限定词只收真数据出现过的「原文 / 触发」与定位符 ` L<n>`（`**用户批注 L128**:`
+    # 形态，epic-1/1-8 真数据）；括注 ≤30 字符覆盖 `（步骤 1，line 125)` 这类行号引用。
+    # ⚠️ 刻意**不**收 Claude 自述语（`**用户原话 3 个 callout…**` 这类关键词与冒号间
+    # 夹长正文、无括注的形态）与裸中文转述（T3 面）。
+    # 真数据 4 处真容器头：审查/2026-08-02-…:23、验收单/Story-2.1-…:429、
+    # research/round-23-…:13、implementation-artifacts/epic-1/1-8-…:174。
+    "user_bold_zh": re.compile(
+        r"\*\*用户(?:批注|反馈|原话|修正)(?:原文|触发)?(?:\s?L\d+)?(?:[（(][^*]{0,30}?[）)])?\*{0,2}[：:]"
+    ),
     "callout_question": re.compile(r"\[!question\][+-]?", re.I),
     "callout_error": re.compile(r"\[!error\][+-]?", re.I),
     "callout_tip": re.compile(r"\[!tip\][+-]?", re.I),
@@ -600,6 +621,22 @@ def extract_block(lines, index, marker_name, marker_end, context):
                 break
             collected.append(nxt)
             cursor += 1
+        if not collected and marker_name == "user_bold_zh":
+            # H1 整改：中文容器头的真数据布局之一是「标签行 + 空行 + blockquote 引用
+            # 用户原话」（审查/2026-08-02-规模化结构检索-审查请求-给ChatGPT.md:23）。
+            # 紧邻续行被那个空行截断 ⇒ 整条会被判空槽、默认不列——marker 修好了却仍然
+            # 「看不见」。只对该族、且仅在紧邻无续行时：跨**一个**空行，且下一行必须是
+            # `>` 引用，收该引用块。不跨更多空行、不收非引用文本（没有证据，不猜）。
+            peek = cursor
+            if peek < len(lines) and QUOTE_BLANK_RE.match(lines[peek]):
+                peek += 1
+                if peek < len(lines) and lines[peek].lstrip().startswith(">"):
+                    while peek < len(lines) and len(collected) < limit:
+                        nxt = lines[peek]
+                        if not nxt.lstrip().startswith(">") or stops_block(nxt):
+                            break
+                        collected.append(nxt)
+                        peek += 1
 
     return [line] + collected[:context], rest, len(collected) > 0
 
```

## ② 作者自述——请独立核对，不要采信

1. **HIGH-1R 修法**：`user_bold_zh` 补定位符分支 `(?:\s?L\d+)?`（覆盖 `**用户批注 L128**:` 形态；真数据 = `implementation-artifacts/epic-1/1-8-vault-switch-runtime-api.md:174`）。按 r3 建议不动宽泛 `[^*]{0,30}`（会重新放进 f10 负控）。
2. **census 订正**：真容器头 3→**4** 处——`08-02:23` / `Story-2.1:429` / `round-23:13` / `epic-1/1-8:174`；docstring、`MARKERS` 注释、`test_contract_t1_t2_variants_are_matched` docstring 三处已同步；`len(MARKERS)==11` 实现/注释/测试一致。
3. **门**：87 passed（+2：parametrize L128 行 + 真锚 `:174`）；负控③（摘除定位符分支）4 条指定测试红；目录级 diff 与上一轮逐字同（只 `＜` 基线）；ruff rc=0；地盘恰 2 文件；L128 原输入与 r2 原输入均 `shown=1`。
4. **LOW-1 的处置（登记不改，请裁）**：理由——(i) r3 自评「未见真数据实例、不足以升 MEDIUM」；(ii) 「未加粗 speaker 行」是续行收集器**既有**性质（普通紧邻收集同样会收 `> Claude：…`），非空行跨行层引入；(iii) 现有 `stops_block` 词汇表只有「粗体标签 / marker / 空行」，为未加粗的 `Claude：` 加启发式会牵连 `> Note：` 等正常引用行、有截断真内容的反向风险；(iv) 已登记进整改档待主 session 裁。若你认为必须在合并前处理且给出真数据依据，请明确。
5. **未动面**：私人 root / fail-closed / 只读 / 日期 / 排序 / 输出格式零改动；`**用户决策/已裁/澄清` 等非四关键词形态仍未纳入（r3 已核，未要求扩）。

## ③ 请优先回答的问题（按重要性排序）

0. **HIGH-1R 是否闭合**：`--root <epic-1/1-8 文件> --keyword L128` 是否 `shown=1` 且 marker = `**用户批注 L128**:`；census「4 处」在脚本/注释/测试三处是否一致且可按你复扫证实。
1. **定位符分支的正则面**：`(?:\s?L\d+)?` 有没有未被拦下的输入会误纳（对照输入：`**用户原话 L128…**`、表格内、标记后跟其他 `L\d+` 语义）或漏纳（同族定位符变体，如有真数据请点名）。
2. **LOW-1 处置**：接受「登记不改」还是要求处理？给出你的依据（真数据优先）。
3. **残余同类**：中文 T1 容器形态还有没有**真数据**未召回面（你上轮找的是 L128；如有新的请给 file:line 与形态）。
4. **声明与一致性**：docstring「T1 全部」、census「4 处」、`MARKERS==11` 是否还有未同步处；测试是否有空门（删掉整改哪一层仍全绿）。
5. **回归**：只读 / 确定性 / 私人面 / fail-closed 有无被本轮改动碰到（以文件与存档对照）。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级；每条给：

- `file:line`
- 一句能让人自己验证的思路：具体的**负控输入**或**对照输入** → 观察到的错误输出。
- 若属于「**门未覆盖的路径**」或「**未被拦下的输入**」，请明确说是哪道门、哪类输入。

宁可少报也不要报推测：不确定的降级为 LOW 或不报，并说明不确定在哪里。
措辞请用：负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径。

## ⑤ 边界

- 只读复核（不改文件、不连库、不写 live vault）。
- 只评**本次整改**（HIGH-1R 闭合、LOW-1 处置、是否引入新问题）；M1/M2/L1–L8（r2 的既有登记）不在本轮。
- 不评契约 `:132` 的 T3 层、`:82` 的非 md 容器、G1-2/G1-3（另卡）。
- 不要求对 live vault / 锚定 PRD 实跑 `--include-private`。

# CARD-G1-1 H1 整改复审请求（BATCH-2026-09-18-第十五批 · 车道 card/p8-backend · round-3）

> 背景：ZCode 补审 r2（GLM-5.3）在绑 `4a6524aa` 的一轮报出 **HIGH-1「中文 T1 粗体容器形态漏召回」**（存档 `_bmad-output/审查/zcode-review-CARD-G1-1-r2.md` 的 `## HIGH` 节），主 session 已裁「整改」。本请求送审的 = 整改 commit 之后的树；请独立复核：整改是否真正闭合 H1、是否引入新问题。
> 上一轮（r2）通道是 ZCode；本轮按协议 §2.4 走 codex+zai GLM-5.3。你在只读沙箱内，可以运行只读命令自验。

## ① 背景与最小读取面（只读这些，不要漫游仓库）

- 树根（你的 cwd）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend`；分支 `card/p8-backend`
- **审查绑定**：`8c546e72`（= `git rev-parse HEAD`；`git --no-pager diff --stat --no-color 8c546e72 HEAD -- . ':(exclude)_bmad-output'` 为空即仍绑定）
- 本卡 H1 整改面 = `git --no-pager diff --stat --no-color a07608b8 8c546e72`（恰 2 文件，+131/−3；**全文已内嵌于附录 A**——若 git 不可用，直接读附录）
- 请读取（相对树根）：
  1. `scripts/annotation_search.py` **全文**（889 行；重点：`MARKERS` 表、`extract_block` 的形态 B 分支）。
  2. `backend/tests/unit/test_annotation_search.py` **全文**（1096 行；新增段 `(g)①′ 中文容器头`、真数据锚 `:23` 与扩展后的 `test_contract_t1_t2_variants_are_matched`）。
  3. `_bmad-output/审查/zcode-review-CARD-G1-1-r2.md` 的 `## HIGH` 节（H1 原文 + 两个真容器头例）。
  4. 整改裁判存档（绑本次整改，均在 `_bmad-output/审查/evidence-g11/`）：
     `h1-behavior-final-*.txt`（点名套件 **85 passed / 0 skipped**）、
     `h1-negctl-1-*.txt`（摘除 `user_bold_zh` 表项 → 8 条指定测试红）与 `h1-negctl-2-*.txt`（停用空行跨行层 → 4 条红），两段源码 sha 前后逐字同；
     `unit-close-h1-*.txt` + `close-h1.nodeids`（tests/unit 目录级 32 failed，与基线 diff 只 `＜`）、
     `h1-annotation-search-*.txt`（评审 H1 的原输入命令现 `marker_hits=1 shown=1`）、
     `jev-triage-8c546e72.json`（本 2 文件分诊：均判 REVIEW，risk=logic / test_or_docs）。
  5. 契约 `_bmad-output/审查/phase0a-annotation-truth/2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md` 第 `126-144` 行。

## ①附录 A：H1 整改 diff（a07608b8 → 8c546e72，逐字内嵌；文中个别用词出自被审代码自身，非本请求措辞）

```diff
diff --git a/backend/tests/unit/test_annotation_search.py b/backend/tests/unit/test_annotation_search.py
index e125fba5..9fe0089f 100644
--- a/backend/tests/unit/test_annotation_search.py
+++ b/backend/tests/unit/test_annotation_search.py
@@ -31,6 +31,9 @@ ANCHOR_PLAN = "_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力
 ANCHOR_PLAN_LINE = 494
 ANCHOR_CARD = "_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md"
 ANCHOR_CARD_LINE = 163
+# H1 整改（ZCode r2）真数据锚：中文容器头 + 空行 + 引用用户原话的布局。
+ANCHOR_ZH = "_bmad-output/审查/2026-08-02-规模化结构检索-审查请求-给ChatGPT.md"
+ANCHOR_ZH_LINE = 23
 
 # 与真 A01 同 root_id / privacy_ceiling 的最小副本（8 root）。fixture 自带，
 # 这样「私人 root 从 A01 算出来」这件事在 fixture 上也是真的被算出来的。
@@ -175,6 +178,81 @@ def test_user2_continuation_is_captured_in_excerpt(six_forms, capsys):
     assert records[0]["excerpt"].split("\n") == ["**User2：**", "续写正文第一行 kw-alpha", "续写正文第二行"]
 
 
+# --------------------------------------------------------------------------
+# (g)①′ 中文容器头（H1 整改，ZCode r2 HIGH-1；评审样例 = 本 fixture 的 f7）
+# --------------------------------------------------------------------------
+@pytest.fixture()
+def zh_container(tmp_path: Path):
+    """中文粗体容器头三形态 + 三个负控输入。
+
+    真数据对应：审查/2026-08-02-…:23（空行 + 引用）、验收单/Story-2.1-…:429
+    （冒号在粗体外）、research/round-23-…:13（限定词「触发」）。
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
+    }
+    assert len(set(got.values())) == 3, "三个形态的 marker 文本必须各异"
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
+    assert names == {"f7-zh-inside.md", "f8-zh-outside.md", "f9-zh-suffix.md"}
+
+
 # --------------------------------------------------------------------------
 # (g)② --story
 # --------------------------------------------------------------------------
@@ -499,6 +577,19 @@ def test_real_anchor_card_line_163(capsys):
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
 @pytest.mark.parametrize("keyword", ["FSRS", "跨vault", "README"])
 def test_real_themes_are_non_empty(keyword, capsys):
     code, out, _ = run_cli(["--keyword", keyword, "--a01", str(REAL_A01), "--json"], capsys)
@@ -918,9 +1009,10 @@ def test_output_is_deterministic_across_separate_processes(six_forms):
 
 
 def test_marker_table_shape():
-    assert len(mod.MARKERS) == 10
+    assert len(mod.MARKERS) == 11
     callouts = sorted(k[len(mod.CALLOUT_PREFIX) :] for k in mod.MARKERS if k.startswith(mod.CALLOUT_PREFIX))
     assert callouts == ["BMAD-ANNO", "error", "hint", "info", "note", "question", "tip", "todo", "warning"]
+    assert "user_bold_zh" in mod.MARKERS
 
 
 @pytest.mark.parametrize(
@@ -932,12 +1024,17 @@ def test_marker_table_shape():
         ("> [!WARNING] 同上", "[!WARNING]"),
         ("**User 修正：改口", "**User 修正："),
         ("**User Comment: english variant", "**User Comment:"),
+        ("**用户批注原文（这是本轮要回答的靶心）：**", "**用户批注原文（这是本轮要回答的靶心）："),
+        ("> **用户批注（步骤 1，line 125）**：", "**用户批注（步骤 1，line 125）**："),
+        ("**用户原话触发**:", "**用户原话触发**:"),
     ],
 )
 def test_contract_t1_t2_variants_are_matched(line, expected):
     """契约 :131/:134 点名、且真数据里确实出现过的形态，逐条钉住。
 
-    实测支撑：`**User**：` 1 处、`[!todo]+` 10 处、大写 callout 3 处（2026-09-19 于本树）。
+    实测支撑：`**User**：` 1 处、`[!todo]+` 10 处、大写 callout 3 处（2026-09-19 于本树）；
+    中文容器头 3 处真容器头（审查/2026-08-02-…:23、验收单/Story-2.1-…:429、
+    research/round-23-…:13——H1 整改补测）。
     """
     hits = mod.find_markers(line)
     assert hits, f"{line!r} 应当命中"
diff --git a/scripts/annotation_search.py b/scripts/annotation_search.py
index 53e501f0..e9084aad 100644
--- a/scripts/annotation_search.py
+++ b/scripts/annotation_search.py
@@ -9,6 +9,13 @@
 
 * 粗体 User 族：``**User：`` / ``**User:`` / ``**User ：`` / ``**User2：`` /
   ``**User 修正：`` / ``**User Comment:`` 等（契约 ``:134``）。
+* 中文容器头族（H1 整改，2026-09-19；ZCode r2 复核发现）：契约 ``:130/:134`` 的
+  「明确中文『用户批注/反馈/修正/原话』」。覆盖冒号两形态——冒号在粗体内
+  （``**用户批注原文（这是本轮要回答的靶心）：**``）与冒号在粗体外
+  （``**用户批注（步骤 1，line 125）**：``）——外加限定词（原文/触发）与括注（≤30 字符）。
+  真数据 3 处真容器头：``_bmad-output/审查/2026-08-02-…:23``、
+  ``_bmad-output/验收单/Story-2.1-…:429``、``_bmad-output/research/round-23-…:13``。
+  ⚠️ 不带粗体的裸中文形态（``用户批注：``）多系转述（T3 面），不纳入。
 * callout 族：``[!question]+`` / ``[!error]+`` / ``[!tip]+`` / ``[!note]+`` /
   ``[!warning]+`` / ``[!hint]+`` / ``[!info]+`` / ``[!BMAD-ANNO]``，blockquote
   （``> [!x]+``）与行内两种形态都算。
@@ -61,13 +68,21 @@ DEFAULT_A01 = os.path.join(
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
+    # H1 整改（ZCode r2 HIGH-1）：中文粗体容器头。两形态 = 冒号在粗体内
+    # (`**用户批注原文（…）：**`) / 冒号在粗体外 (`**用户批注（步骤 1，line 125）**：`)；
+    # 限定词只收真数据出现过的「原文 / 触发」；括注 ≤30 字符覆盖 `（步骤 1，line 125）`
+    # 这类行号引用。⚠️ 刻意**不**收 Claude 自述语（`**用户原话 3 个 callout…**` 这类
+    # 关键词与冒号间夹长正文、无括注的形态）与裸中文转述（T3 面）。
+    # 真数据 3 处真容器头：审查/2026-08-02-…:23、验收单/Story-2.1-…:429、research/round-23-…:13。
+    "user_bold_zh": re.compile(r"\*\*用户(?:批注|反馈|原话|修正)(?:原文|触发)?(?:[（(][^*]{0,30}?[）)])?\*{0,2}[：:]"),
     "callout_question": re.compile(r"\[!question\][+-]?", re.I),
     "callout_error": re.compile(r"\[!error\][+-]?", re.I),
     "callout_tip": re.compile(r"\[!tip\][+-]?", re.I),
@@ -600,6 +615,22 @@ def extract_block(lines, index, marker_name, marker_end, context):
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

## ② 作者自述——请独立核对，不要采信（每条都有 ①-4 的证据）

1. **修法选 a（加识别而非订正 census）的理由**：契约 `:130/:134` 把「明确中文『用户批注/反馈/修正/原话』」列在 T1 高精度层与「至少覆盖」清单，不是可选面；真数据存在真容器头（如 `_bmad-output/审查/2026-08-02-规模化结构检索-审查请求-给ChatGPT.md:23`——该文件除该容器头外零 marker，工具此前把它读成「没有任何批注」）。
2. **正则召回面**：四关键词（批注/反馈/原话/修正，紧跟 `**用户`）+ 限定词（原文/触发）+ 括注 ≤30 字符 + 冒号在粗体内/外两形态。真数据复算（2026-09-19）：3 处真容器头（`08-02:23` / `Story-2.1:429` / `round-23:13`）+ 若干讨论该形态的元档（评审/验收单自身）。
3. **正则刻意不收的面**：Claude 自述语（`**用户原话 3 个 callout…**：` 类——关键词与冒号间夹长正文、无括注）、裸中文转述（无粗体，T3）、`**用户决策/已裁/澄清…：`（探针另见 22 行；不在契约四关键词面，未纳入——如需扩面请给出真数据依据）。
4. **第二层（同属 H1 布局）**：`**用户批注原文（…）：**` 与引用之间**隔一个空行**的真数据布局（`:23`）会被原逻辑判空槽而默认不列；整改对该族、且仅紧邻无续行时跨**一个**空行收 `>` 引用块（不跨更多、不收非引用文本）。缺这层，「读作没说过」在默认输出上仍成立。
5. **门与裁判**：85 passed（+7：三形态 fixture / 空行布局 / 三负控 / 真锚 `:23`）；负控两段只红在指定断言且源码 sha 前后逐字同；目录级 diff 只 `＜`（32 failed 同前，唯一 flaky 噪声消失）；ruff check/format rc=0；地盘恰 2 文件；同参两次 `--json` sha 逐字同；L5 注释失真（9→11）随计数修正。
6. **未动面**：私人 root / fail-closed / 只读 / 日期 / 排序 / 输出格式零改动；M1/M2/L1–L8 不在本轮（主 session 已裁仅 H1 整改）。

## ③ 请优先回答的问题（按重要性排序）

0. **H1 是否真闭合**：两处被点名的真容器头现在可召回？`_bmad-output/审查/2026-08-02-规模化结构检索-审查请求-给ChatGPT.md:23` 是否 `shown=1` 且摘录含用户原话？三个负控形态（Claude 自述语 / 无冒号 topic / 裸中文转述）是否仍不命中？
1. **正则面**：`(?:[（(][^*]{0,30}?[）)])` 与 `\*{0,2}[：:]` 的组合有没有**未被拦下的输入**（嵌套括注、半/全角混用、超长括注、紧贴标点）会误纳；`原文|触发` 限定词集是否该缩/扩（给出真数据依据才动）。
2. **空行跨行层**：只跨一个空行 + 只收 `>` 引用的约束，在什么**对照输入**下会把不属于该批注的引用算进来？与 `--context`、空槽计数、`stops_block` 的交互有没有意外。
3. **门是否锁得住**：删/改任一整改层，测试是否必红（反向看变异存活面）；有没有哪条新测试删掉后仍全绿（空门）；真锚 `:23` 行号脆性按 L7 口径登记是否足够。
4. **声明漂移**：docstring「T1 全部」在新覆盖面下是否成立；`MARKERS==11` 与注释、测试三处是否一致；还有没有别的文档/注释停在旧数。
5. **回归**：只读 / 确定性 / 私人面 / fail-closed 有没有被这次改动碰到（用文件与存档对照，不要采信自述）。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级；每条给：

- `file:line`
- 一句能让人自己验证的思路：具体的**负控输入**或**对照输入** → 观察到的错误输出。
- 若属于「**门未覆盖的路径**」或「**未被拦下的输入**」，请明确说是哪道门、哪类输入。

宁可少报也不要报推测：不确定的降级为 LOW 或不报，并说明不确定在哪里。
措辞请用：负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径。

## ⑤ 边界

- 只读复核（不改文件、不连库、不写 live vault），以你只读沙箱内的工具自验为准。
- 只评**本次整改**（H1 闭合、是否引入新问题）；M1/M2/L1–L8 的既有登记不在本轮，不要求整改。
- 不评契约 `:132` 的 T3 层、`:82` 的非 md 容器、G1-2/G1-3（另卡）。
- 不要求对 live vault / 锚定 PRD 实跑 `--include-private`。

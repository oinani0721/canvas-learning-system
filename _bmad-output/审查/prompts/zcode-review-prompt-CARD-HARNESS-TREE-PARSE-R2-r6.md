你是一位独立对抗性代码审查者。本通道为**只读**：本模式没有 Bash（不要尝试运行任何命令），不得写入任何文件，不得连接任何数据库或网络服务。判断只依据下方内嵌的改动集与点名可读的文件。

# ① 背景与最小读取面

本卡 `CARD-HARNESS-TREE-PARSE-R2`（`BATCH-2026-09-18-第十五批` · 车道 `card-p6-skills-w`，本车道第 2/4 张）。本轮为**补审**（协议 §2.4.2 通道）一轮，审查对象 = 本卡**最终态**：绑定 `43bea775`（= 含代码改动的最后一个 commit；四个被审文件自 `43bea775` 至当前 HEAD 零改动，车道已实测 `git --no-pager diff --stat --no-color 43bea775 HEAD -- <四文件>` 为空）。

**这张卡修的是什么**：

`/quiz-answer` 写点在写学习账本之前，先用 `_harness_tree()` 解析 `.canvas-config.yaml` 的 `harness_tree` 键决定「记到哪棵树 / 哪个账本」。上一轮复核（Codex r10）抓到的 HIGH：原实现只有一条行为探针 `yaml.safe_load("a: 1")`（问「它像不像解析器」）。一个 `safe_load` 恒返 `{"a": 1}` 的假 `yaml` 模块答得对探针，随后对写着 `harness_tree: <目标树>` 的 config 也返回「无键」⇒ 被读成「用户没写这个键」⇒ **静默回退父树** ⇒ 学习事件记到另一棵 harness 的账本，而用户看到的是一次成功写入。缺的维度 =「解析结果是否忠于文件内容」。

本卡补上：键级探针 + 词法否决（只否决不采用）+ 契约门 `_harness_contract` + `## Step 2.9` 预检（先拒后写）。改动集 = 下方四个文件：

1. `canvas-vault/.claude/skills/quiz-answer/SKILL.md`
   - `_harness_tree`（`:446` 起）：改「先读原文再 `safe_load(str)`」；加**键级探针**（`:596`，三行探针文档、键在末行）；加**词法否决**（`:650`，`^harness_tree[ \t]*:` 命中而解析结果无该键 ⇒ 拒写；**只否决不采用**）。威胁模型（防 / 不防 / 代价）写在 docstring（`:492` 起）。
   - 新函数 `_harness_contract(REPO)`（`:705-801`）：影子门（`:754`，比较 `abspath`）/ 版本门（`EVENT_VERSION == 1`、排除 `bool`）/ 形状门（7 名字：5 callable + 2 `re.Pattern`）/ 纯函数行为探针；主块 `:820` 改为一行解包。
   - 新增 `## Step 2.9 · harness 预检`（`:189-264`；fence 块 `:205-262`）：Step 3 写分**之前**先自证「树在、库在、契约对」，块体从本 SKILL.md 里 AST 抽取 `_harness_tree` + `_harness_contract`（与主块**同一份实现**）；纯读零写；既有半态白板不回滚（`_HALFSTATE`，`:552` / `:736`）。
2. `backend/tests/regression/test_g3_2_review_ledger.py`：`..._never_returns_a_tree` 加 `_mode` 维（`_HEADED_LINES` 60 条 + `_WHOLE_DOCS` 13 条；参数表 `:7696-7698`；门体 `:7700-7774`）；`parse_returns_junk` 改真 PyYAML + 文件本身是列表（`:7970`）；`_extract_harness_tree` / `_ht_outcome`（`:7532-7571`）。
3. `backend/tests/skills/test_harness_tree_parse_r2.py`（新文件，1252 行；22 个测试函数 → 47 nodeid）：忠实性门、契约门、预检门、结构门、词法否决形态门。
4. `backend/tests/skills/skill_portability_lint.py`：quiz-answer 指纹两处（`B305` / `S281`）+ `MANAGED_FILE_DIGESTS` 一行 digest + 交接注释（共 35 行改动）。

**最小读取面（写死）**——除下方内嵌 diff 外，以下文件可在 cwd（本车道树）直接读取（行号为现值，已实测）：

1. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` — Step 2.9 全段 `:189-264`；主块 `def _harness_tree` `:446` 至解包行 `:820`（含 `_harness_contract` `:705-801`）。
2. `backend/tests/regression/test_g3_2_review_ledger.py` — `:7532-7571`（`_extract_harness_tree` / `_ht_outcome`）；`:7696-7698`（`_mode` 参数表）；`:7700-7774`（`..._never_returns_a_tree`）；`:7444-7486`（`..._refuses_whole_flow_document`）；`:7973-8051`（`..._pyyaml_available_failures_are_not_missing_config`，「既有 16 门」出处 `:7989`）。
3. `backend/tests/skills/test_harness_tree_parse_r2.py` — 全文。
4. `backend/tests/skills/skill_portability_lint.py` — `:2118-2195`（`OPAQUE` / `TMP_BLOCK_BASELINE` 的 quiz-answer 相关两处）、`:2242-2265`（交接注释 + `QUIZ_ANSWER_BASELINE`）、`MANAGED_FILE_DIGESTS` 的 quiz-answer 行。
5. `backend/scripts/validate_learning_events.py` — `:66-75` / `:132-137` / `:239-252` / `:1737-1748`（契约探针的依据；本卡零写者）。
6. 上下文（只读）：`_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md:190`；`_bmad-output/审查/codex-review-CARD-HARNESS-TREE-PARSE-REDO-r10.md:18-31`；`_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:872-941`（四个处置选项）。

**内嵌改动集**（`git --no-pager diff --no-color a05732c9 43bea775 -- backend/tests/regression/test_g3_2_review_ledger.py backend/tests/skills/skill_portability_lint.py backend/tests/skills/test_harness_tree_parse_r2.py canvas-vault/.claude/skills/quiz-answer/SKILL.md` 原文；本通道无 Bash，改动前形态看 `-` 行）：

````diff
diff --git a/backend/tests/regression/test_g3_2_review_ledger.py b/backend/tests/regression/test_g3_2_review_ledger.py
index 656b5a52..b65ff0a5 100644
--- a/backend/tests/regression/test_g3_2_review_ledger.py
+++ b/backend/tests/regression/test_g3_2_review_ledger.py
@@ -7348,6 +7348,15 @@ def _run_writer_no_yaml_at_harness_tree(vault: Path, payload: dict):
 #: 缺库时写点打出来的拒因（点名 PyYAML）。门靠它证明「确实是缺库这条路拒的」，
 #: 而不是碰巧被别的判据拒了。
 _NO_YAML_REFUSAL = "PyYAML 不可用 — harness_tree 指向哪棵树不可证"
+#: 生产键级探针喂给解析器的那份文档 —— **从写点里逐字抽出来，不手抄**。
+#: ⛔ round-3 把它从单行改成三行（丢文件尾巴的坏解析器对单行文档没有尾巴可丢，照样答对）。
+#: 当时这里写的是手抄常量 + `assert _KEY_PROBE_DOC in CODE` 的防漂移 —— 那条 assert
+#: **没红**，因为新文档恰好**包含**旧串（`in` 是子串判定）。两格门红才提醒了我。
+#: ⇒ 改成正则抽取：写点改一个字，这里跟着改，零手抄面。
+_KPROBE_M = re.search(r'_KPROBE_DOC = (".*?")\n', CODE)
+assert _KPROBE_M, '⛔ 写点里找不到 `_KPROBE_DOC = "..."` —— 键级探针的文档定义漂了，先核写点'
+_KEY_PROBE_DOC = ast.literal_eval(_KPROBE_M.group(1))
+assert "harness_tree" in _KEY_PROBE_DOC, f"⛔ 抽出来的探针文档里没有 harness_tree: {_KEY_PROBE_DOC!r}"
 
 
 def test_g33r2_harness_tree_no_pyyaml_refuses_canonical_form_accepted_cost(vault):
@@ -7562,97 +7571,133 @@ def _ht_outcome(_fn, _vault_dir):
         return ("exit", str(_e))
 
 
+#: 既有 60 条：每一条都是**接在固定三行 block 配置头之后的一行**（`_mode="headed"`）。
+#: ⛔ 本列表逐字保持原样（CARD-HARNESS-TREE-PARSE-R2 只加维度，不动既有参数）。
+_HEADED_LINES = [
+    # ── 规范写法(两条分支必须给出同一个结果)──
+    "harness_tree: /a/b",
+    "harness_tree:    /a/b   ",
+    "harness_tree: /a/b c",
+    "harness_tree: /a/b　c",
+    "harness_tree: /a/b c",
+    "harness_tree: /a/b　",
+    "harness_tree: /a/b,c",
+    "harness_tree: /a/[b]",
+    "harness_tree: /a/{b}",
+    "harness_tree: /a/b\\",
+    "harness_tree: /a/b'",
+    'harness_tree: /a/b"',
+    "harness_tree: /a",
+    # ── 本卡自查(2026-09-14)发现的四类: 正则取到值而 PyYAML 整份拒 ──
+    "harness_tree:\t/a/b",
+    "harness_tree: /a/b: c",
+    "harness_tree: /a/b:",
+    "harness_tree: /a/b\t",
+    # ── Codex round-1 MEDIUM 指出的结构形态: 逐行扫描看不见 YAML 在哪里换行 ──
+    "harness_tree: /a/bx",
+    "harness_tree: /a/b",
+    "harness_tree: /a/b x",
+    "harness_tree: /a/b x",
+    "harness_tree: /a/b\n  cont",
+    "harness_tree: /a/b\n\n  cont",
+    "{harness_tree: /a/b}",
+    # ── 既有三条分界与 M-c 家族(降级侧允许更窄, 但不许给出不同的树)──
+    "harness_tree:",
+    'harness_tree: ""',
+    "harness_tree: null",
+    "harness_tree: # reset",
+    "harness_tree: /a/b #c",
+    "harness_tree: /a/b#c",
+    "harness_tree: '/a/b'",
+    'harness_tree: "/a/b"',
+    "harness_tree : /a/b",
+    '"harness_tree": /a/b',
+    "'harness_tree': /a/b",
+    "harness_tree: ../rel",
+    "harness_tree: ~/x",
+    "harness_tree: 　#alt",
+    "# harness_tree: /a/b",
+    "other: 1",
+    # ── round-3: 文档结构与语法上下文(本卡自查 + Codex round-2 MEDIUM-2/3)──
+    #: `safe_load` 只收单文档; 逐行扫描看不见文档边界, 会把第二份文档里的那行当成有效值
+    "harness_tree: /a/b\n---\nharness_tree: /c/d",
+    "harness_tree: /a/b\n...\nharness_tree: /c/d",
+    #: 连「整份文件里根本没有这个键」的多文档也不行 —— PyYAML 整份拒而降级会回退
+    "other: 1\n---\nmore: 2",
+    "harness_tree: /a/b\n...",
+    #: 转义键: YAML 还原出同一个键, 而原文里根本不含 `harness_tree` 这串字符。
+    #: ⛔ 反斜杠用 chr(92) 拼: 本卡实测被中间工具层把转义展开成真字符一次。
+    '"harness' + chr(92) + 'u005ftree": /a/b',
+    #: 别名 / 合并键: 键可以不在它出现的那一行上定义
+    "note: &a /a/b\nharness_tree: *a",
+    #: 块标量: 那串字符在 YAML 眼里是**值的内容**, 不是键
+    "x: |\n  harness_tree: /a/b",
+    #: 指令行 + 内容之后的文档开始 —— 实测 PyYAML 在这里抛的是 ComposerError
+    #: (「只收单文档」), 不是指令语义; 如实标注, 不按「指令行」宣称。
+    "%YAML 1.1\n---\nharness_tree: /a/b",
+    #: 跨行引号标量: 开引号之后每一行的语法身份都不再是它看上去的样子
+    'note: "open\n  harness_tree: /a/b"',
+    # ── round-4: Codex round-3 MEDIUM-1/2/4 + 本卡自查 ──
+    #: M-1 同一函数里「什么算空白」两处口径不一致(裸 .strip() 按 Unicode 判空行,
+    #: 续行判据只认 ASCII) ⇒ 这类行既不算空行也不算续行, 被整个跳过, 降级照样
+    #: 采用前一行的值 —— 与本文件 round-3 的老教训同源。
+    #: ⛔ 不可见字符一律用 chr() 拼: 本卡实测被中间工具层把转义展开过三次。
+    "harness_tree: /a/b" + chr(10) + chr(0x3000) + "more",
+    "harness_tree: /a/b" + chr(10) + chr(0xA0) + "more",
+    "harness_tree: /a/b" + chr(10) + chr(0x3000) + chr(10) + "other: 1",
+    "harness_tree: /a/b" + chr(10) + chr(0x3000) + "# c",
+    #: M-4 非换行类的 YAML 非法字符: PyYAML 整份 ReaderError, 逐行扫描照样取到树
+    "other: " + chr(1) + "x" + chr(10) + "harness_tree: /a/b",
+    #: M-2 文档标记同行还有内容 / 连续起始标记 / 开头就是结束标记
+    "--- {a: 1}",
+    "---",
+    "...",
+    # ── round-5: 给三组「读不懂就停」判据各配一个专属哨兵（Codex round-4 LOW-1）──
+    #: 本卡原先登记「门结构上测不到判据失效、必须另立变异卡」—— **那是错的**。
+    #: 漏掉的一点: 判据一删, 降级就比 PyYAML **更宽**, 于是落进「违反」而不是「更窄」。
+    #: 下面三条各自只让**一组**判据的删除变红(本卡逐变体实测的对角线), 其余全绿。
+    "%FOO bar" + chr(10) + "harness_tree: /a/b",
+    "note: *undefined" + chr(10) + "harness_tree: /a/b",
+    'note: "unclosed' + chr(10) + "harness_tree: /a/b",
+]
+
+#: ── `_mode="whole"`：**整份文档**形态（CARD-HARNESS-TREE-PARSE-R2 补的维度）──
+#: ⛔ 为什么非补不可：上面 60 条**每一条**都被接在三行 block 配置头之后，于是「整份文档
+#: 级」的形态——文档起始/结束标记、`%YAML` 指令、BOM、多文档、顶层根本不是 block mapping
+#: ——在那张表下**一格都碰不到**。先例 `..._no_pyyaml_refuses_whole_flow_document` 已经
+#: 为「整份 flow mapping」单立过一门，本维度把它一般化。
+#: ⛔ 缺的是**一个维度**而不是一格：往 60 条里再加几行补不上它，因为那 60 格固定死了
+#: 同一个前提（顶层是一个 block mapping，且前三行合法）。那个被固定死的前提就是盲区。
+#:
+#: 第三元 `_truth` = **真 PyYAML 对这份文本的实际结局**，2026-09-18 于本车道共享 venv
+#: 逐条实测后写死。它在门里被当作**控制组前提**断言：少了这一半，「缺库时拒了」可能只是
+#: 因为这份文档本来就不合法 —— 那就什么也没证明。表与实际结局漂了，门会红在前提那一行。
+_WHOLE_DOCS = [
+    #: ── 文档标记族（UAT #16「首文档标记那一半测不到」的出处）──
+    ("---\nharness_tree: /a/b\n", "dict_with_key", "文件首 `---` 文档起始标记"),
+    ("%YAML 1.2\n---\nharness_tree: /a/b\n", "dict_with_key", "`%YAML` 指令 + `---`"),
+    ("\ufeff---\nharness_tree: /a/b\n", "dict_with_key", "BOM + `---`"),
+    ("--- # 这是一份 config\nharness_tree: /a/b\n", "dict_with_key", "`---` 同行带注释"),
+    ("harness_tree: /a/b\n...\n", "dict_with_key", "文末 `...` 文档结束标记"),
+    ("{vault_id: v, harness_tree: /a/b}\n", "dict_with_key", "整份 flow mapping（一般化了 `:7435` 那一门）"),
+    ("a: 1\n---\nharness_tree: /a/b\n", "raises:ComposerError", "多文档（`safe_load` 只收一份）"),
+    #: ── 引号奇偶（Codex r5 `:19`「一行里引号成不成对证不出引号闭没闭合」的出处）──
+    ('note: "他说 \\"hi\\""\nharness_tree: /a/b\n', "dict_with_key", "值里含转义引号：合法，PyYAML 照常给出键"),
+    ('note: "没闭合\nharness_tree: /a/b\n', "raises:ScannerError", "未闭合引号：PyYAML 整份拒"),
+    #: ── 隐式类型 / 复杂键 / 块结构（Codex r4 `:24-26` 三类的出处）──
+    ("when: 2026-08-01\nharness_tree: /a/b\n", "dict_with_key", "隐式日期类型：合法"),
+    ("when: 2026-02-30\nharness_tree: /a/b\n", "raises:ValueError", "生成不出来的隐式日期：整份 ValueError"),
+    ("? [a, b]\n: c\nharness_tree: /a/b\n", "raises:ConstructorError", "不可哈希的复杂键：整份 ConstructorError"),
+    ("a:\n  b: 1\n c: 2\nharness_tree: /a/b\n", "raises:ParserError", "块结构缩进不齐：整份 ParserError"),
+]
+
+
 @pytest.mark.parametrize(
-    "_line",
-    [
-        # ── 规范写法(两条分支必须给出同一个结果)──
-        "harness_tree: /a/b",
-        "harness_tree:    /a/b   ",
-        "harness_tree: /a/b c",
-        "harness_tree: /a/b　c",
-        "harness_tree: /a/b c",
-        "harness_tree: /a/b　",
-        "harness_tree: /a/b,c",
-        "harness_tree: /a/[b]",
-        "harness_tree: /a/{b}",
-        "harness_tree: /a/b\\",
-        "harness_tree: /a/b'",
-        'harness_tree: /a/b"',
-        "harness_tree: /a",
-        # ── 本卡自查(2026-09-14)发现的四类: 正则取到值而 PyYAML 整份拒 ──
-        "harness_tree:\t/a/b",
-        "harness_tree: /a/b: c",
-        "harness_tree: /a/b:",
-        "harness_tree: /a/b\t",
-        # ── Codex round-1 MEDIUM 指出的结构形态: 逐行扫描看不见 YAML 在哪里换行 ──
-        "harness_tree: /a/bx",
-        "harness_tree: /a/b",
-        "harness_tree: /a/b x",
-        "harness_tree: /a/b x",
-        "harness_tree: /a/b\n  cont",
-        "harness_tree: /a/b\n\n  cont",
-        "{harness_tree: /a/b}",
-        # ── 既有三条分界与 M-c 家族(降级侧允许更窄, 但不许给出不同的树)──
-        "harness_tree:",
-        'harness_tree: ""',
-        "harness_tree: null",
-        "harness_tree: # reset",
-        "harness_tree: /a/b #c",
-        "harness_tree: /a/b#c",
-        "harness_tree: '/a/b'",
-        'harness_tree: "/a/b"',
-        "harness_tree : /a/b",
-        '"harness_tree": /a/b',
-        "'harness_tree': /a/b",
-        "harness_tree: ../rel",
-        "harness_tree: ~/x",
-        "harness_tree: 　#alt",
-        "# harness_tree: /a/b",
-        "other: 1",
-        # ── round-3: 文档结构与语法上下文(本卡自查 + Codex round-2 MEDIUM-2/3)──
-        #: `safe_load` 只收单文档; 逐行扫描看不见文档边界, 会把第二份文档里的那行当成有效值
-        "harness_tree: /a/b\n---\nharness_tree: /c/d",
-        "harness_tree: /a/b\n...\nharness_tree: /c/d",
-        #: 连「整份文件里根本没有这个键」的多文档也不行 —— PyYAML 整份拒而降级会回退
-        "other: 1\n---\nmore: 2",
-        "harness_tree: /a/b\n...",
-        #: 转义键: YAML 还原出同一个键, 而原文里根本不含 `harness_tree` 这串字符。
-        #: ⛔ 反斜杠用 chr(92) 拼: 本卡实测被中间工具层把转义展开成真字符一次。
-        '"harness' + chr(92) + 'u005ftree": /a/b',
-        #: 别名 / 合并键: 键可以不在它出现的那一行上定义
-        "note: &a /a/b\nharness_tree: *a",
-        #: 块标量: 那串字符在 YAML 眼里是**值的内容**, 不是键
-        "x: |\n  harness_tree: /a/b",
-        #: 指令行 + 内容之后的文档开始 —— 实测 PyYAML 在这里抛的是 ComposerError
-        #: (「只收单文档」), 不是指令语义; 如实标注, 不按「指令行」宣称。
-        "%YAML 1.1\n---\nharness_tree: /a/b",
-        #: 跨行引号标量: 开引号之后每一行的语法身份都不再是它看上去的样子
-        'note: "open\n  harness_tree: /a/b"',
-        # ── round-4: Codex round-3 MEDIUM-1/2/4 + 本卡自查 ──
-        #: M-1 同一函数里「什么算空白」两处口径不一致(裸 .strip() 按 Unicode 判空行,
-        #: 续行判据只认 ASCII) ⇒ 这类行既不算空行也不算续行, 被整个跳过, 降级照样
-        #: 采用前一行的值 —— 与本文件 round-3 的老教训同源。
-        #: ⛔ 不可见字符一律用 chr() 拼: 本卡实测被中间工具层把转义展开过三次。
-        "harness_tree: /a/b" + chr(10) + chr(0x3000) + "more",
-        "harness_tree: /a/b" + chr(10) + chr(0xA0) + "more",
-        "harness_tree: /a/b" + chr(10) + chr(0x3000) + chr(10) + "other: 1",
-        "harness_tree: /a/b" + chr(10) + chr(0x3000) + "# c",
-        #: M-4 非换行类的 YAML 非法字符: PyYAML 整份 ReaderError, 逐行扫描照样取到树
-        "other: " + chr(1) + "x" + chr(10) + "harness_tree: /a/b",
-        #: M-2 文档标记同行还有内容 / 连续起始标记 / 开头就是结束标记
-        "--- {a: 1}",
-        "---",
-        "...",
-        # ── round-5: 给三组「读不懂就停」判据各配一个专属哨兵（Codex round-4 LOW-1）──
-        #: 本卡原先登记「门结构上测不到判据失效、必须另立变异卡」—— **那是错的**。
-        #: 漏掉的一点: 判据一删, 降级就比 PyYAML **更宽**, 于是落进「违反」而不是「更窄」。
-        #: 下面三条各自只让**一组**判据的删除变红(本卡逐变体实测的对角线), 其余全绿。
-        "%FOO bar" + chr(10) + "harness_tree: /a/b",
-        "note: *undefined" + chr(10) + "harness_tree: /a/b",
-        'note: "unclosed' + chr(10) + "harness_tree: /a/b",
-    ],
+    ("_mode", "_line", "_truth"),
+    [pytest.param("headed", _l, None, id=f"headed-{_i}") for _i, _l in enumerate(_HEADED_LINES)]
+    + [pytest.param("whole", _d, _tr, id=f"whole-{_i}") for _i, (_d, _tr, _why) in enumerate(_WHOLE_DOCS)],
 )
-def test_g33r2_harness_tree_no_pyyaml_never_returns_a_tree(tmp_path, monkeypatch, _line):
+def test_g33r2_harness_tree_no_pyyaml_never_returns_a_tree(tmp_path, monkeypatch, _mode, _line, _truth):
     """⛔ 缺 PyYAML 时, `_harness_tree` **对任何 config 都不返回任何树** —— 一律抛并点名 PyYAML。
 
     这是用户 2026-09-14 裁定「缺库即拒写」之后的不变量, 比它取代的那条更强也更简单。
@@ -7678,10 +7723,34 @@ def test_g33r2_harness_tree_no_pyyaml_never_returns_a_tree(tmp_path, monkeypatch
     _fn = _extract_harness_tree()
     _vd = tmp_path / "canvas-vault"
     _vd.mkdir()
-    (_vd / ".canvas-config.yaml").write_text(
-        '# 测试 config\nvault_id: "canvas-vault-测试"\nsubject: cs-61b\n' + _line + "\n",
-        encoding="utf-8",
+    #: `headed` = 接在固定三行配置头之后的一行; `whole` = 这一条**就是整份文档**。
+    _text = (
+        '# 测试 config\nvault_id: "canvas-vault-测试"\nsubject: cs-61b\n' + _line + "\n" if _mode == "headed" else _line
     )
+    (_vd / ".canvas-config.yaml").write_text(_text, encoding="utf-8")
+
+    #: ── 有库控制半(whole 格): 先用**真 PyYAML** 跑同一份文本, 把它的真实结局断言成
+    #: 夹具前提。⛔ 少了这一半, 下面那句「缺库时拒了」可能只是因为这份文档本来就不合法,
+    #: 什么也没证明。⛔ 且这里**不许** `pytest.skip` —— skip 会把「前提不成立」吞成绿色;
+    #: 前提不成立的形态该做的是**不入表**(写进验收单「未入表形态与原因」), 不是跳过。
+    if _truth is not None:
+        import yaml as _real_yaml
+
+        try:
+            _parsed = _real_yaml.safe_load(_text)
+            _verdict = (
+                "dict_with_key"
+                if (isinstance(_parsed, dict) and "harness_tree" in _parsed)
+                else ("dict_no_key" if isinstance(_parsed, dict) else "not_a_dict")
+            )
+        except Exception as _pe:
+            _verdict = "raises:" + type(_pe).__name__
+        assert _verdict == _truth, (
+            f"⛔ 控制组前提没成立: 真 PyYAML 对这份整份文档给出的是 {_verdict!r}, 表里声明的是 {_truth!r}\n"
+            f"   文本: {_text!r}\n"
+            f"   ⇒ 表里写死的结局与 PyYAML 的实际行为漂了(换了版本? 改了文本?)。\n"
+            f"     先核实际结局再改表 —— 别为了让门变绿去松判据。"
+        )
 
     #: 前提自证: 屏蔽之前 PyYAML 确实可用 —— 否则下面那次「缺库」什么也没证明。
     assert "yaml" in sys.modules, "⛔ 前提没成立: 本进程里 PyYAML 本就不可用, 这一跑证不到东西"
@@ -7690,7 +7759,7 @@ def test_g33r2_harness_tree_no_pyyaml_never_returns_a_tree(tmp_path, monkeypatch
     _outcome = _ht_outcome(_fn, _vd)
     assert _outcome[0] == "exit", (
         f"⛔ 缺 PyYAML 时 `_harness_tree` 返回了一棵树, 而不是拒绝\n"
-        f"   配置行: {_line!r}\n"
+        f"   配置({_mode}): {_text!r}\n"
         f"   返回值: {_outcome[1]!r}\n"
         f"   ⇒ 降级解析被加回来了。它的每一个版本都留下过「采用一棵 PyYAML 不会给出的树」\n"
         f"     的实测反例; 真要加回来, 先读本门与 SKILL.md 里 `_harness_tree` 的 docstring。"
@@ -7898,7 +7967,7 @@ def test_g33r2_harness_tree_pyyaml_available_no_config_falls_back_to_parent(tmp_
     [
         ("parse_oserror", "解析途中抛 OSError（读流 EIO 之类）"),
         ("parse_valueerror", "解析途中抛 ValueError"),
-        ("parse_returns_junk", "解析返回一个非 dict 的东西"),
+        ("parse_returns_junk", "config 文件本身就是个列表（真 PyYAML，无假模块）"),
     ],
 )
 def test_g33r2_harness_tree_pyyaml_available_failures_are_not_missing_config(tmp_path, monkeypatch, _failure, _why):
@@ -7928,18 +7997,43 @@ def test_g33r2_harness_tree_pyyaml_available_failures_are_not_missing_config(tmp
 
     import yaml as _real_yaml
 
+    if _failure == "parse_returns_junk":
+        #: ⛔ **本参数改用真 PyYAML + 一份真的是列表的 config**(CARD-HARNESS-TREE-PARSE-R2)。
+        #: 原先这一格用**说谎的解析器**制造「非 dict」: config 文件里明明写着目标树, 假模块
+        #: 却返回一个列表, 然后断言「回退父树是对的」—— 那把**错误结果固化成了期望**。
+        #: 「YAML 本身是列表 ⇒ 按没写这个键回退」这条语义要成立, 文件就得**真的是列表**;
+        #: 而「解析器谎报无键」现在是另一回事, 由 tests/skills/test_harness_tree_parse_r2.py
+        #: 的 `..._lying_parser_is_refused` 钉住(拒写, 不是回退)。
+        (_vd / ".canvas-config.yaml").write_text("- a\n- b\n", encoding="utf-8")
+        #: 前提自证: 这份文件在真 PyYAML 眼里确实是个 list, 且**没有** harness_tree 字面键
+        #: (有的话会撞上词法否决, 那就测的是另一条路了)。
+        assert isinstance(_real_yaml.safe_load("- a\n- b\n"), list), "⛔ 前提没成立: 这份 config 不是列表"
+        assert re.search(r"^harness_tree[ \t]*:", "- a\n- b\n", re.M) is None, (
+            "⛔ 前提没成立: 文件里有 harness_tree 字面键"
+        )
+
+        _fn = _extract_harness_tree()
+        _outcome = _ht_outcome(_fn, _vd)
+        assert _outcome == ("ok", str(tmp_path)), (
+            f"⛔ config 真的是个列表(没有这个键)⇒ 应按「没写」回退父树({_why}), 实得 {_outcome!r}"
+        )
+        return
+
     _fake = types.ModuleType("yaml")
 
     def _safe_load(_stream, *_a, **_kw):
-        #: 自证探针(生产会先用 "a: 1" 验它像不像解析器)照常放行, 只在读**文件对象**时发难 ——
-        #: 否则这个假模块在自证那一步就被拒了, 本门就测不到「解析这一步」。
-        if isinstance(_stream, str):
+        #: 生产的**两道**自证探针都照常放行, 只在读 config 时发难 —— 否则这个假模块在自证
+        #: 那一步就被拒了, 本门就测不到「解析这一步」。
+        #: ⛔ 按**内容**分辨而不是按类型(CARD-HARNESS-TREE-PARSE-R2): 生产改成「先读原文、
+        #: 再 `safe_load(str)`」之后, 探针与 config **都是 str** —— `isinstance(_stream, str)`
+        #: 会把 config 也一起放行, 这三格当场全部失效(且是静默失效: 门照样绿)。
+        #: ⛔ 第二道探针是 round-1 整改加的**键级探针**; 漏放行它, 这两格会从「解析这一步坏了」
+        #: 掉回「拿不到 PyYAML」那一档(2026-09-18 实测, 拒因整句当场变)。
+        if _stream in ("a: 1", _KEY_PROBE_DOC):
             return _real_yaml.safe_load(_stream)
         if _failure == "parse_oserror":
             raise OSError(5, "Input/output error")
-        if _failure == "parse_valueerror":
-            raise ValueError("boom")
-        return ["not", "a", "dict"]
+        raise ValueError("boom")
 
     _fake.safe_load = _safe_load
     monkeypatch.setitem(sys.modules, "yaml", _fake)
@@ -7947,23 +8041,6 @@ def test_g33r2_harness_tree_pyyaml_available_failures_are_not_missing_config(tmp
     _fn = _extract_harness_tree()
     _outcome = _ht_outcome(_fn, _vd)
 
-    if _failure == "parse_returns_junk":
-        #: ⛔⛔ **本参数的期望有误, 已登记待主 session 裁定（Codex round-10 HIGH 的一部分）。**
-        #: 问题: 这里用的是一个**说谎的解析器**（config 文件里明明写着目标树, 假模块却返回
-        #: 一个列表）, 然后断言「回退父树是对的」—— 这等于把**错误结果固化进了门**。
-        #: 「YAML 本身是列表 ⇒ 回退」这条语义要成立, 场景应当是**config 文件里本来就是个
-        #: 列表**、用**真 PyYAML** 跑; 而不是让假模块谎报。
-        #: ⚠️ 未就地改断言的原因: 本卡 Codex 轮次已用满（新增范围 5/5）, 改测试属代码改动、
-        #: 需再送一轮。按协议「第 5 轮仍有 HIGH ⇒ 停下交主 session 人审」, 此处只标注不改。
-        #: 修法建议（给接手的人）: 把本参数换成 config 文件内容为 `- a\n- b` 的真实场景,
-        #: 并**删掉**假模块那一支; 同时补上 round-10 指出的第四种形态 ——
-        #: 「探针答对、但对真实 config 返回的东西不忠于文件内容」。
-        #: 解析**成功**但结果不是 dict ⇒ 按「没写这个键」回退, 与既有 16 门同口径。
-        assert _outcome == ("ok", str(tmp_path)), (
-            f"⛔ 解析出非 dict 时应按「没写这个键」回退父树({_why}), 实得 {_outcome!r}"
-        )
-        return
-
     assert _outcome[0] == "exit", (
         f"⛔ config 打得开、解析却失败时返回了一棵树而不是拒绝({_why}): {_outcome[1]!r}\n"
         f"   ⇒ 多半是把解析期的异常又并回了「没有 config」那一档 —— 这两件事必须分开:\n"
diff --git a/backend/tests/skills/skill_portability_lint.py b/backend/tests/skills/skill_portability_lint.py
index f63b9ab4..c5341764 100644
--- a/backend/tests/skills/skill_portability_lint.py
+++ b/backend/tests/skills/skill_portability_lint.py
@@ -2118,7 +2118,12 @@ OPAQUE_TMP_BASELINE: dict[str, list[str]] = {
     # 「嵌入式 span」判据当成了 shell 命令替换。`_SPAN_SEP_CHARS` 已清空(只认 ASCII
     # 空白)——因为任何标点都可能是合法 shell 词的一部分。方向取舍: 漏检不可接受,
     # 误报可以登记。⛔ 登记项带**内容指纹**(r11 HIGH-3), 16 位、不 strip(r14)。
-    "quiz-answer": ["98:918de56473d5be1b", "205:44b7655dd97c27b7"],
+    # ⛔ 2026-09-18 CARD-HARNESS-TREE-PARSE-R2(第十五批): `:205` → `:267` 纯行号位移
+    # (Step 2.9 预检段插在 Step 2 与 Step 3 之间, +62 行), **指纹 `44b7655dd97c27b7`
+    # 一个字节未变** —— 那一行散文本身没动。本基线与 `TMP_BLOCK_BASELINE` 的 `S205`
+    # 是**同一行**的两套登记, 必须同批一起位移(漏改一处 ⇒ tests/skills 连带 7 道负控门
+    # 一起红, 因为它们断言「全量 lint 只应报我注入的那一个 problem」)。
+    "quiz-answer": ["98:918de56473d5be1b", "281:44b7655dd97c27b7"],
     # ⛔ CARD-SEB-WRITER-SUBSTRING-TMP(第十五批)实测重算: `:430` 的内容变了(Step 6.5 prose
     # 新增 `mkdir -p` 与命名空间路径)⇒ 指纹换; `:577` 行号下移到 `:603`(指纹不变, 该行
     # 一个字节没动); 新增 `:604` = 本次追加的变更记录条目。四条都是**保守误报登记**
@@ -2167,9 +2172,26 @@ TMP_BLOCK_BASELINE: dict[str, list[str]] = {
         #: 空的同名 yaml.py 照样导得进, 故改判 safe_load 在不在; 安装命令改 shlex.quote)。
         #: → `9a1ec16c27149217…`(Codex round-9 HIGH: 「打不开 config」与「打开了却解析失败」
         #: 拆成两个作用域; 并把「拿到 PyYAML」的判据从「可调用」升级为在已知输入上自证)。
-        "B229:9a1ec16c27149217",
+        #: → `14da24c2df92c341…`(CARD-HARNESS-TREE-PARSE-R2, 第十五批 · r10 H1 收口 + round-1/2/3/4 整改):
+        #:   主块里 `_harness_tree` 改「先读原文再 `safe_load(str)`」+ 加词法否决(文件明文
+        #:   有 `harness_tree:` 键而解析器没给出 ⇒ 拒写, 只否决不采用), 并新增
+        #:   `_harness_contract(REPO)`(影子/版本/形状/纯函数探针) ⇒ 整块哈希变。
+        #: ⛔ 块**起始行**从 `:229` 下移到 `:299`: Step 2.9 预检段(prose + 一个新 PYEOF
+        #:   fence)插在 Step 2 与 Step 3 之间, 共 +70 行(round-2 整改给预检块加了
+        #:   `sys.dont_write_bytecode = True` 与其理由注释, 又 +8; round-3 把它提到首行 import
+        #:   之前又 +6)。同一位移让散文条目 `S205` → `S281`
+        #:   ——**指纹一个字节没变**, 只是行号跟着走(那一行本身没动)。
+        #: ⛔ **无新增条目**: 预检块里一个 `/tmp` 都没有(节点路径经环境变量传入, SKILL.md
+        #:   路径用 `os.path.join` 分段拼), 所以它不进 `tmp_block_fingerprints` 的登记面。
+        #: ⛔ round-1 整改后**块起始行仍是 `:291`**(加的行都落在 `_harness_tree` 函数体内,
+        #:   不越过块首), 只有整块哈希再变一次: `ddee88b6…` → `39a76e33…`。改动内容 = 键级
+        #:   探针(`safe_load("harness_tree: <哨兵>")` 必须给出该键)+ 词法否决的「值内文本」豁免
+        #:   round-2 复核后**整段去掉了那个豁免**(它是整份文档一个布尔, 一处命中落在值内
+        #:   就让整份文件的否决失效; 按处数比也修不了, 因为 PyYAML 折叠跨行标量的换行);
+        #:   round-3 把键级探针的文档从单行改成三行(丢文件尾巴的坏解析器对单行没有尾巴可丢)。
+        "B305:14da24c2df92c341",
+        "S281:44b7655dd97c27b7",
         "S96:b55afbca27229028",
-        "S205:44b7655dd97c27b7",
     ],
     #: 2026-09-18 CARD-SEB-WRITER-SUBSTRING-TMP(第十五批): Step 6.5 落账块的查重段
     #: 从「整本有损解码 + 子串命中」改成「切 bytes + 逐行严格解码 + parsed-field 等值」,
@@ -2220,6 +2242,11 @@ PARENT_DIR_PROSE_BASELINE: dict[str, list[int]] = {
 #:
 #: quiz-answer 的 `harness_tree` 解析(E-2)归 U5-B, 本卡只钉现状、一个字节都不改。
 #: U5-B 改 `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 后**必须**同步改这一段。
+#: ⛔ 2026-09-18 CARD-HARNESS-TREE-PARSE-R2(第十五批): 改 quiz-answer 写点后要同时重算
+#: **两处** —— `TMP_BLOCK_BASELINE["quiz-answer"]` 的块指纹(块起始行号会随插入段位移)与
+#: 下面这行整文件 digest; `QUIZ_ANSWER_BASELINE` 九项本卡实测**逐字未变**(⚠️ 新写的拒因
+#: 文案里别出现 `.claude/skills/` 这种连续路径串 —— `_CLAUDE_DIR_RE` 按文本计数, 一句
+#: 散文就能让 `claude_dir_ref` 从 4 变 5, 与实际可移植性无关)。
 #: 单列在这里就是为了让那次 diff 一眼可见。
 #: 行号标注(2026-09-14 CARD-HARNESS-TREE-PARSE-REDO 实测): 4 处裸 `/tmp/` 在
 #: `:98/:106/:205/:233`, 4 处 `claude_dir_ref` 在 `:74/:3104/:3112/:3203`。
@@ -3240,7 +3267,7 @@ MANAGED_FILE_DIGESTS: dict[str, str] = {
     "skills/configure-whiteboard/SKILL.md": "9eb21ecc6ac044a914ce11009025f8a84e51c5135221ec3b50f8c021ccfa2177",
     "skills/exam-quick/SKILL.md": "eb30e407a14145477710cbf439e7e85705afeb157c98c5993ee0b3616c324853",
     "skills/node-chat/SKILL.md": "3b15bc91dabea7e7b3876b75c2c0973e7a9284d48081e5d1b864623258b40fb7",
-    "skills/quiz-answer/SKILL.md": "6ae2558f1def3e94588bf0a043bb2d9e4b5904a618de5ec4b5260f5c206601b0",
+    "skills/quiz-answer/SKILL.md": "d64d3b8cd0a8c0fc78a59c9e736f67273acf6a65d7209cbdcb18d1c2e02e4f38",
     # CARD-SEB-WRITER-SUBSTRING-TMP（第十五批）：Step 6.5 写规修复 + 临时路径解耦后重算。
     "skills/start-exam-board/SKILL.md": "c3c0434d385c66f33c097c051d4aac2d05f908a881bc1471785beeaf52493473",
     "skills/study-question/SKILL.md": "0142b7833ff3ab54c9307227d59ebaa7d5ff3f9c18a76b07344d0ab295fa22e4",
diff --git a/backend/tests/skills/test_harness_tree_parse_r2.py b/backend/tests/skills/test_harness_tree_parse_r2.py
new file mode 100644
index 00000000..d31a67e1
--- /dev/null
+++ b/backend/tests/skills/test_harness_tree_parse_r2.py
@@ -0,0 +1,1252 @@
+"""CARD-HARNESS-TREE-PARSE-R2 — quiz-answer 主写点选树的三层收口。
+
+本文件钉住 T7-A r10 H1 的收口与并入的两件同族缺口：
+
+1. **忠实性**（`..._lying_parser_is_refused`）：`_harness_tree` 的 PyYAML 行为探针
+   （`yaml.safe_load("a: 1")` 是否给出 `{"a": 1}`）只证明「它像个解析器」，**不证明
+   它对真实 config 的解析忠于文件内容**。一个恒返 `{"a": 1}` 的假 `yaml` 模块能过
+   探针，随后对写着 `harness_tree: <目标树>` 的 config 也返回 `{"a": 1}` ⇒ 生产按
+   「没写这个键」**静默回退父树** ⇒ 学习事件绑到另一棵 harness 上。收口 = 文件明文
+   有 `harness_tree:` 键时解析结果**不得沉默**（词法只做否决，绝不采用）。
+
+2. **契约**（`..._harness_contract_refuses`）：写点从选中的树无条件导入 7 个名字，
+   除「导得进」外零判据 ⇒ 任意旧版/异版 harness 分发被静默采用并按其语义写账本。
+   收口 = `_harness_contract(REPO)` 的影子门 / 版本 / 形状 / 纯函数行为探针。
+
+3. **半态**（`..._preflight_refuses_before_step3`）：缺 PyYAML 时 Step 3 已写分、
+   Step 4 主写点才拒写 ⇒ 白板停在「已记分、节点未更新」。收口 = Step 2.9 预检块
+   （先拒后写），既有半态**不回滚**（用户口径，分数保留并在拒因里点名）。
+
+⛔ **零 mock（DD-03）**：假 `yaml` 模块、假 validator 树、`PYTHONPATH` 前置的
+`yaml.py` 都是**负控输入**（坏环境本身的形态），不是对被测代码的 mock。被测实现
+一律从 `SKILL.md` 逐字抽取（AST）或用 `subprocess` 真跑，本文件不另抄一份。
+
+⛔ **全部路径 `tmp_path` 派生**：主干树的 `SKILL.md` / `validate_learning_events.py`
+只作**读源**（`shutil.copy` / `symlink_to`），本文件不写 live vault、不连任何库。
+"""
+
+from __future__ import annotations
+
+import ast
+import os
+import re
+import shutil
+import subprocess
+import sys
+import types
+from pathlib import Path
+
+import pytest
+
+#: 车道树根（本文件在 `backend/tests/skills/` ⇒ parents[3]），与 test_g3_2_review_ledger.py:43 同深度。
+WT = Path(__file__).resolve().parents[3]
+SKILL = WT / "canvas-vault" / ".claude" / "skills" / "quiz-answer" / "SKILL.md"
+VALIDATOR = WT / "backend" / "scripts" / "validate_learning_events.py"
+_SKILL_TEXT = SKILL.read_text(encoding="utf-8")
+
+_BLOCK_RE = r"python3 - <<'PYEOF'\n(.*?)\nPYEOF"
+_ALL_BLOCKS = re.findall(_BLOCK_RE, _SKILL_TEXT, re.DOTALL)
+
+#: 主写点块（与 test_g3_2_review_ledger.py:49-56 同一条过滤器，逐字同）。
+_MAIN_BLOCKS = [b for b in _ALL_BLOCKS if 'P = "/tmp/quiz-answer-payload.json"' in b]
+assert len(_MAIN_BLOCKS) == 1, f"SKILL.md 应恰有 1 个主写点 PYEOF 块, 实见 {len(_MAIN_BLOCKS)}"
+CODE = _MAIN_BLOCKS[0]
+
+#: 缺库拒因整句（与 test_g3_2_review_ledger.py:7350 逐字同 —— 两处锚同一句，漂了一起红）。
+_NO_YAML_REFUSAL = "PyYAML 不可用 — harness_tree 指向哪棵树不可证"
+#: 半态标记的稳定子串（Step 2.9 / 主块缺库拒因 / 契约拒因三处共用）。
+_HALFSTATE_MARK = "分数保留"
+#: 忠实性拒因的稳定子串。
+_UNFAITHFUL_MARK = "解析结果与文件内容不符"
+
+
+# ══════════════════════════════════════════════════════════════════════════
+# 被测实现的逐字抽取（不另抄一份 —— 抄一份 = 两份手写清单，必然漂移）
+# ══════════════════════════════════════════════════════════════════════════
+def _extract(*names: str) -> tuple:
+    """把主写点里指名的顶层函数**逐字**抽出来，在本进程里直接调用。
+
+    ⛔ 与 `test_g3_2_review_ledger.py:7523 _extract_harness_tree()` 同法同口径：
+    锚不到就当场断言失败（而不是悄悄测了个别的东西）。
+
+    ⛔ 命名空间只镜像**被抽函数中最早那个定义之前**的顶层 import。这不是图省事 ——
+    主写点顶层还有 `from decay_beta import …`（vault 脚本，需要 `sys.path` 先插
+    `<vault>/.claude/scripts`），盲目 exec 全部顶层 import 会在这里 `ImportError`，
+    把「夹具装不起来」伪装成「被测代码有毛病」。Step 2.9 预检块用的是同一条口径。
+    """
+    _mod = ast.parse(CODE)
+    _fns = [n for n in _mod.body if isinstance(n, ast.FunctionDef) and n.name in names]
+    assert len(_fns) == len(names), (
+        f"⛔ 写点里 {names} 应各恰 1 处定义, 实见 {[n.name for n in _fns]} —— 锚不到就等于没测生产代码"
+    )
+    _cut = min(n.lineno for n in _fns)
+    _ns: dict = {}
+    for _st in _mod.body:
+        if isinstance(_st, (ast.Import, ast.ImportFrom)) and _st.lineno < _cut:
+            exec(compile(ast.Module(body=[_st], type_ignores=[]), "<skill-prelude>", "exec"), _ns)  # noqa: S102
+    for _need in ("os", "re", "sys"):
+        assert _need in _ns, f"⛔ 写点的顶层 import 里没有 {_need} —— 本 helper 的假设漂了, 先核写点"
+    exec(compile(ast.Module(body=_fns, type_ignores=[]), "<skill-harness>", "exec"), _ns)  # noqa: S102
+    return tuple(_ns[n] for n in names)
+
+
+def _outcome(_fn, *args):
+    """跑一次，把结局归一成 `("ok", <返回值>)` / `("exit", <拒因全文>)`。"""
+    try:
+        return ("ok", _fn(*args))
+    except SystemExit as _e:
+        return ("exit", str(_e))
+
+
+def _usable_tree(root: Path) -> Path:
+    """造一棵能通过 `isdir(<tree>/backend/scripts)` 的树（不含 validator）。"""
+    (root / "backend" / "scripts").mkdir(parents=True, exist_ok=True)
+    return root
+
+
+def _real_harness(root: Path) -> Path:
+    """造一棵**真能用**的 harness 树：validator 是 symlink → 主干那一份。
+
+    ⛔ symlink 而不是 copy 是有意的：契约门的影子判据因此**只能**比未 realpath 的
+    `__file__` 目录 —— 比 realpath 会把这棵合法的 alt 树判成影子（它的 validator
+    物理上就在主干树里）。这一格同时是影子判据「没写成 realpath」的守卫。
+    """
+    (root / "backend" / "scripts").mkdir(parents=True, exist_ok=True)
+    (root / "backend" / "scripts" / "validate_learning_events.py").symlink_to(VALIDATOR)
+    return root
+
+
+def _fake_validator_tree(root: Path, body: str) -> Path:
+    """造一棵 validator 是**手写占位**的树（契约门的负控输入）。"""
+    _s = root / "backend" / "scripts"
+    _s.mkdir(parents=True, exist_ok=True)
+    (_s / "validate_learning_events.py").write_text(body, encoding="utf-8")
+    return root
+
+
+#: 契约门占位 validator 的「全对」底本 —— 每格只在此基础上拆掉**一项**。
+_VALIDATOR_STUB_OK = """\
+import re
+
+EVENT_VERSION = 1
+_TS_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z$")
+_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$")
+
+
+def classify_card_state(fields):
+    return ("new", "占位")
+
+
+def _vault_id_of(p):
+    return "占位"
+
+
+def _looks_like_review_ext(rec):
+    return False
+
+
+def validate_record_full(record, manifest=None, vault_id=None):
+    if not isinstance(record, dict):
+        return (["顶层必须是 JSON object"], [])
+    return ([], [])
+
+
+def _golden_manifest(*a, **kw):
+    return {}
+"""
+
+
+@pytest.fixture(autouse=True)
+def _no_validator_leak():
+    """每格前后都把 `validate_learning_events` 从 `sys.modules` / `sys.path` 摘干净。
+
+    ⛔ 不摘的话，前一格 import 进来的那棵树会被后一格直接复用 —— 契约门看起来全绿，
+    实际上第二格之后压根没去选中的树里找过。
+    """
+    _path0 = list(sys.path)
+    sys.modules.pop("validate_learning_events", None)
+    yield
+    sys.modules.pop("validate_learning_events", None)
+    sys.path[:] = _path0
+
+
+# ══════════════════════════════════════════════════════════════════════════
+# ① 忠实性：说谎的解析器不得被采用（r10 H1 收口）
+# ══════════════════════════════════════════════════════════════════════════
+#: 生产键级探针喂给解析器的那份文档 —— **从写点里逐字抽出来，不手抄**。
+#: ⛔ round-3 把它从单行改成三行（丢文件尾巴的坏解析器对单行文档没有尾巴可丢，照样答对）。
+#: 当时这里写的是手抄常量 + `assert _KEY_PROBE_DOC in CODE` 的防漂移 —— 那条 assert
+#: **没红**，因为新文档恰好**包含**旧串（`in` 是子串判定）。两格门红才提醒了我。
+#: ⇒ 改成正则抽取：写点改一个字，这里跟着改，零手抄面。
+_KPROBE_M = re.search(r'_KPROBE_DOC = (".*?")\n', CODE)
+assert _KPROBE_M, '⛔ 写点里找不到 `_KPROBE_DOC = "..."` —— 键级探针的文档定义漂了，先核写点'
+_KEY_PROBE_DOC = ast.literal_eval(_KPROBE_M.group(1))
+assert "harness_tree" in _KEY_PROBE_DOC, f"⛔ 抽出来的探针文档里没有 harness_tree: {_KEY_PROBE_DOC!r}"
+
+
+def test_g33r2_key_probe_doc_must_be_multiline_with_the_key_last():
+    """⛔ 键级探针的文档必须是**多行、且那个键在最后一行** —— 这是 round-3 HIGH 的结构守卫。
+
+    单行探针没有尾巴可丢，于是一整类**丢文件尾巴**的坏解析器（缓冲截断 / 流被提前关闭 /
+    只读前 N 行）照样答对、活过这一层；配上词法否决只认顶格裸键，两层一起落空。
+
+    ⚠️ 本门是结构判据，不测行为——行为由 `..._truncating_parser_is_refused` 三格钉。
+    它单独立在这里，是为了让「有人把探针改回单行」这件事红在一句看得懂的话上，
+    而不是红成一堆行为门的连带失败。
+    """
+    _lines = _KEY_PROBE_DOC.splitlines()
+    assert len(_lines) >= 3, (
+        f"⛔ 探针文档只有 {len(_lines)} 行: {_KEY_PROBE_DOC!r}\n"
+        f"   ⇒ 丢文件尾巴的坏解析器对它没有尾巴可丢，会照样答对（round-3 复核的 HIGH）。"
+    )
+    assert _lines[-1].startswith("harness_tree:"), (
+        f"⛔ 探针文档的**最后一行**必须是那个键，否则丢尾巴也丢不到它: {_lines!r}"
+    )
+    #: ⛔ 这里**不能**写 `_KEY_PROBE_DOC in CODE`：`literal_eval` 解出的是**真换行**，
+    #: 而 CODE 里是源码形式的 `\n`（反斜杠 + n 两个字符）—— 那条断言必假（实测栽过）。
+    #: 抽取本身的正确性由模块级的 `_KPROBE_M` 断言保证。这里改为核**源码形式**确实在写点里。
+    assert '_KPROBE_DOC = "' in CODE, "⛔ 写点里找不到探针文档的赋值 —— 抽取正则漂了"
+
+
+def _fake_yaml(_file_answer, *, _honest_probes: bool):
+    """造一个负控输入用的假 `yaml` 模块（= 坏环境本身的形态，不是对被测代码的 mock）。
+
+    `_honest_probes=False` ⇒ **恒返** `_file_answer`（r10 H1 的原形态：它连探针带文件
+    一视同仁，正因为答案恰好是第一道探针要的 `{"a": 1}` 才混过去）。这类模块死在
+    **键级探针**那一层 —— 它对一份只写着 `harness_tree` 的最简文档也给不出那个键。
+
+    `_honest_probes=True` ⇒ 对生产的**两个探针输入**（`"a: 1"` 与 `_KEY_PROBE_DOC`）
+    用真 PyYAML 老实回答，只对别的输入（= 用户那份 config）返 `_file_answer`。
+    ⛔ 这一档存在的理由：不老实答探针的模块活不到词法否决那一层，于是词法否决就成了
+    **门未覆盖的路径**。要测第二层，负控输入就得能通过第一层。
+
+    ⛔ 按**内容**分辨而不是按类型：生产把 config 改成「先读原文、再 `safe_load(str)`」
+    之后，探针与 config 都是 `str`，`isinstance(_stream, str)` 会把 config 也一起放行。
+    """
+    import yaml as _real_yaml
+
+    _m = types.ModuleType("yaml")
+
+    def _safe_load(_stream, *_a, **_kw):
+        if _honest_probes and _stream in ("a: 1", _KEY_PROBE_DOC):
+            return _real_yaml.safe_load(_stream)
+        return _file_answer
+
+    _m.safe_load = _safe_load
+    return _m
+
+
+#: config 的三种**合法书写形式** —— 生产都支持（见既有门 `..._noncanonical_key_form_is_honored`
+#: 与 `..._no_pyyaml_refuses_whole_flow_document`），而词法正则只认得第一种。
+_CFG_FORMS = {
+    "bare": 'vault_id: "v"\nharness_tree: {t}\n',
+    "quoted": 'vault_id: "v"\n"harness_tree": {t}\n',
+    "flow": "{{vault_id: v, harness_tree: {t}}}\n",
+    #: ⛔ 键与冒号之间有空白 —— 真 PyYAML 认（ledger 侧另有一格 `[键与冒号之间有空格]`
+    #: 专门钉「必须认」），而生产正则靠 `[ \t]*` 才命中它。
+    #: 没有这一格，把 `^harness_tree[ \t]*:` 缩成 `^harness_tree:` 会让 r10 H1 原样复活，
+    #: 而 42 格 + ledger 165 格一格不红（人审替代轮 v2 HIGH，两镜头各自实测复现）。
+    "spaced_before_colon": 'vault_id: "v"\nharness_tree : {t}\n',
+}
+
+_LYING_CASES = {
+    # ── 第一层：键级探针。恒返式假模块一律死在这里，**与用户怎么写这份 config 无关** ──
+    #: r10 H1 的原形态。
+    "constant_bare": dict(honest=False, file={"a": 1}, form="bare", want="读不出本写点唯一关心的那个键"),
+    #: ⛔ 本卡 round-1 复核抓到的**未被拦下的输入**之一：键带引号 ⇒ 词法正则行首不命中。
+    "constant_quoted_key": dict(honest=False, file={"a": 1}, form="quoted", want="读不出本写点唯一关心的那个键"),
+    #: ⛔ 同上之二：整份 flow mapping ⇒ 行首是 `{`，词法正则同样不命中。
+    "constant_flow_mapping": dict(honest=False, file={"a": 1}, form="flow", want="读不出本写点唯一关心的那个键"),
+    # ── 第二层：词法否决。对两个探针都老实、只对这份 config 说谎 ⇒ 活得到这一层 ──
+    "honest_probes_empty_mapping": dict(honest=True, file={}, form="bare", want=_UNFAITHFUL_MARK),
+    "honest_probes_list": dict(honest=True, file=["not", "a", "dict"], form="bare", want=_UNFAITHFUL_MARK),
+    #: ⛔ 钉住词法正则的 `[ \t]*` 那一向（人审替代轮 v2 HIGH）：同样是「探针诚实、只对
+    #: 这份 config 谎报无键」，只是 config 用**冒号前带空格**的合法写法。
+    #: 正则一旦缩成 `^harness_tree:`，这一格是唯一会红的地方。
+    "honest_probes_spaced_key": dict(honest=True, file={}, form="spaced_before_colon", want=_UNFAITHFUL_MARK),
+}
+
+
+@pytest.mark.parametrize("_case", sorted(_LYING_CASES))
+def test_g33r2_harness_tree_lying_parser_is_refused(tmp_path, monkeypatch, _case):
+    """⛔ 解析器说不出 config 里那个键 ⇒ **拒写**，不得静默回退父树。
+
+    这是 T7-A r10 H1 的收口，**两层**：
+
+    1. **键级探针**（`constant_*` 三格）：问「给它一份只写着 `harness_tree` 的最简文档，
+       它给不给得出这个键」。这一层**不看用户的文件**，所以与书写形式无关。
+       ⛔ 三格用的是三种**不同的合法书写形式**（裸键 / 带引号的键 / 整份 flow mapping）：
+       收口的第一版只有词法否决，而词法问的是「文件里有没有**顶格裸键**」—— 后两种写法
+       行首都不是 `harness_tree`，正则一条都不命中，恒返 `{"a": 1}` 的模块在它们下面
+       **照样静默回退父树**（本卡 round-1 复核实测复现）。缺的又是**一个维度**：
+       判据挂在了「用户怎么写」上，而不是「解析器能不能读出这个键」上。
+    2. **词法否决**（`honest_probes_*` 两格）：假模块对两个探针都老实作答、只对用户这份
+       config 说谎 ⇒ 它活得过第一层，于是第二层才谈得上被测到。
+
+    ⛔ 收口只做**否决**，绝不**采用**词法命中的那个值：采用 = 逐行降级解析回潮，
+    那条路被四轮同族缺陷打回过（见 SKILL.md `_harness_tree` docstring）。
+    """
+    _c = _LYING_CASES[_case]
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _usable_tree(tmp_path)  # 父树可用 ⇒ 一旦静默回退就会「成功」地绑错树
+    _target = _usable_tree(tmp_path / "target-tree")
+    _raw = _CFG_FORMS[_c["form"]].format(t=_target)
+    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+    #: ── 前提自证：这份 config **本来就是对的**（这一种写法真 PyYAML 认） ──
+    #: 少了这一步，「被拒」可能只是因为文件本身有毛病，本门什么也没证明。
+    import yaml as _real_yaml
+
+    _truth = _real_yaml.safe_load(_raw)
+    assert isinstance(_truth, dict) and str(_truth.get("harness_tree")) == str(_target), (
+        f"⛔ 前提没成立({_case}): 真 PyYAML 对这份 {_c['form']} 写法的 config 给出的是 {_truth!r}, 目标树应是 {_target}"
+    )
+
+    monkeypatch.setitem(sys.modules, "yaml", _fake_yaml(_c["file"], _honest_probes=_c["honest"]))
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+
+    assert _got[0] == "exit", (
+        f"⛔ 解析器说不出这份 config 里的 harness_tree, `_harness_tree` 却返回了一棵树\n"
+        f"   形态: {_case}（书写形式 {_c['form']}，解析器对这份 config 给出 {_c['file']!r}，"
+        f"对两个探针是否老实={_c['honest']}）\n"
+        f"   文件明文: {_raw!r}\n"
+        f"   返回值: {_got[1]!r}  (父树 = {str(tmp_path)!r})\n"
+        f"   ⇒ config 指着 {_target}, 系统却把学习事件记到了另一棵树的账本上。"
+    )
+    assert _c["want"] in _got[1], (
+        f"⛔ 拒因须落在该落的那一层({_case} 期望含 {_c['want']!r}): {_got[1]!r}\n"
+        f"   ⇒ 拒因跑到另一层 = 这一格实际测的不是它声称的那道判据。"
+    )
+    assert _HALFSTATE_MARK in _got[1], f"⛔ 拒因须带半态标记(既有半态白板分数保留、不回滚)({_case}): {_got[1]!r}"
+
+
+#: 三种「那串字落在**某个值内部**」的合法文档 —— 嵌套深度递增。
+#: 「那串字落在某个值内部」的三种合法文档 —— 本层**已知且接受**的误拒面。
+_VALUE_NEST_FORMS = {
+    "toplevel_scalar": 'note: "open\nharness_tree: /a/b"\n',
+    "inside_a_list": 'items:\n  - "open\nharness_tree: /a/b"\n',
+    "inside_a_nested_dict": 'outer:\n  inner: "open\nharness_tree: /a/b"\n',
+}
+
+
+@pytest.mark.parametrize("_form", sorted(_VALUE_NEST_FORMS))
+def test_g33r2_harness_tree_lexical_veto_false_refusal_cost_is_accepted(tmp_path, _form):
+    """⚠️ 这三格钉的是本层**已知且接受的代价**，不是「正确行为」。
+
+    形态（真 PyYAML 解析完全正确、顶层确实没有这个键）：
+
+        note: "open
+        harness_tree: /a/b"
+
+    值是一个**跨行的流式标量**，续行**可以顶格**，于是词法正则在第 2 行命中 ⇒ **被拒**。
+    这是一次**误拒**。本门断言它确实发生，并说明为什么接受它。
+
+    ⛔ **为什么不用「豁免」去修**（三次尝试，全部实测，留档给后人）：
+      v1 豁免只看顶层 `_doc.values()`      → 嵌套一层的值仍被误拒；
+      v2 遍历整棵结构 + 环防护             → round-2 复核抓到：它是**整份文档一个布尔**，
+         只要已解析结果里任意一个字符串含那串字，否决就对文件里**每一处**（含真正的
+         顶层 `harness_tree` 键）一起失效；一个**截断式解析器**（非敌意）配一份普通的
+         自文档 config 就能静默绑父树（由 `..._truncating_parser_cannot_disarm_the_veto` 钉住）；
+      v3 改按「处数」比                    → **修不了**：PyYAML 把双引号跨行标量的换行
+         **折叠成空格**，误拒形态（顶格 1 处 / 值内子串 1 次）与缺陷形态（同样 1 / 1）
+         **完全同构**，计数区分不了。
+    根本原因：豁免要拿**解析器的输出**去决定要不要相信解析器，而解析器正是这一层唯一
+    不可信的那一方 —— 换 `yaml.compose()` 的位置跨度也一样（它可以谎报跨度覆盖全文）。
+
+    ⇒ 取舍：**误拒**是可见的拒绝、拒因指明行号、用户改一下写法就好；**豁免**带来的是
+    **静默绑错树**，用户无从察觉。方向不同，接受前者。
+    """
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _usable_tree(tmp_path)
+    _raw = _VALUE_NEST_FORMS[_form]
+    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+    #: 前提自证：① 词法正则确实命中；② 真 PyYAML 解析**成功**且顶层没有这个键
+    #: （⇒ 这确实是一份合法文档，被拒确实是误拒，而不是文档本身有毛病）。
+    import yaml as _real_yaml
+
+    assert re.search(r"^harness_tree[ \t]*:", _raw, re.M) is not None, (
+        f"⛔ 前提没成立({_form}): 词法正则对这份文本不命中 —— 那它连误拒都产生不了"
+    )
+    _truth = _real_yaml.safe_load(_raw)
+    assert isinstance(_truth, dict) and "harness_tree" not in _truth, (
+        f"⛔ 前提没成立({_form}): 真 PyYAML 给出的是 {_truth!r} —— 这份文档并不合法/并非无键"
+    )
+
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+
+    assert _got[0] == "exit", (
+        f"⛔ 本门钉的是**已知代价**({_form})：这份合法文档应当被拒（可见的拒绝）。\n"
+        f"   实得 {_got!r}。若这里变绿，多半是有人又加回了「值内豁免」——\n"
+        f"   先读本门 docstring 里那三次尝试，再读 SKILL.md `_harness_tree` 的同段记录。"
+    )
+    assert _UNFAITHFUL_MARK in _got[1], f"⛔ 该落在词法否决那一层({_form}): {_got[1]!r}"
+    assert "行明文写着" in _got[1], f"⛔ 误拒的拒因必须**指明是第几行**，否则用户无从知道该改哪里({_form}): {_got[1]!r}"
+
+
+def _truncating_yaml(_n_lines):
+    """**非敌意**的坏解析器：只读前 `_n_lines` 行（缓冲截断 / 流被提前关闭那一类事故）。
+
+    ⛔ 它是坏环境的形态，不是对被测代码的 mock。两道探针（`"a: 1"` 与 `_KEY_PROBE_DOC`）
+    都是**单行**文档，所以它照样答对 —— 于是活得过键级探针那一层，正好用来测词法否决。
+    """
+    import yaml as _real_yaml
+
+    _m = types.ModuleType("yaml")
+
+    def _safe_load(_stream, *_a, **_kw):
+        return _real_yaml.safe_load("\n".join(str(_stream).splitlines()[:_n_lines]))
+
+    _m.safe_load = _safe_load
+    return _m
+
+
+#: round-3 复核 H1 的三种形态 —— 截断解析器 + 三种**不同书写形式**。
+#: 前两种词法正则行首不命中（`"harness_tree"` 以引号开头、`{...}` 以花括号开头），
+#: 所以它们**只能**靠键级探针拦；第三种裸键两层都拦得住，放在一起是为了对照。
+#: 每格 = (config 文本, 截断到第几行)。⛔ **截断行数必须按这份文本定**：
+#: `flow_mapping` 只有 2 行，截断到 2 行等于没截断 —— 那一格会红在「前提没成立」，
+#: 而不是红在被测判据上（实测栽过一次）。前提断言把这件事挡在了判据之前。
+_TRUNCATING_FORMS = {
+    "bare_key": ("vault_id: v\nnote: docs\nharness_tree: {t}\n", 2),
+    "quoted_key": ('vault_id: v\nnote: docs\n"harness_tree": {t}\n', 2),
+    "flow_mapping": ("# config\n{{harness_tree: {t}}}\n", 1),
+}
+
+
+@pytest.mark.parametrize("_form", sorted(_TRUNCATING_FORMS))
+def test_g33r2_harness_tree_truncating_parser_is_refused(tmp_path, monkeypatch, _form):
+    """⛔ round-3 复核的 HIGH：**丢文件尾巴**的坏解析器必须在键级探针层就被拦下。
+
+    当时键级探针喂的是**单行**文档 `harness_tree: <哨兵>` —— 一整类丢尾巴的坏解析器
+    （缓冲截断 / 流被提前关闭 / 只读前 N 行）对单行文档**没有尾巴可丢**，照样答对。
+    它们过了这一层；而词法否决只认**顶格裸键**，`"harness_tree": v` 与 `{harness_tree: v}`
+    行首都不是它 ⇒ 两层一起落空 ⇒ **静默回退父树**。
+
+    整改：探针文档改成**三行、那个键在最后一行**。本门的三格就是当时的三种形态。
+    ⚠️ **如实**：这只是把阈值从「1 行」推到「探针行数」，不是关门 —— 一个只读前 5 行的
+    解析器仍能答对这份 3 行探针。根本限制在于探针永远是**另一份**文件。
+    """
+    _tmpl, _cut = _TRUNCATING_FORMS[_form]
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _usable_tree(tmp_path)  # 父树可用 ⇒ 一旦静默回退就会「成功」地绑错树
+    _target = _usable_tree(tmp_path / "target-tree")
+    _raw = _tmpl.format(t=_target)
+    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+    #: 前提自证：① 真 PyYAML 对这份 config 给出**真键**（文件本身没写错）；
+    #: ② 截断解析器确实把那个键丢了（它确实在谎报无键）。
+    import yaml as _real_yaml
+
+    _truth = _real_yaml.safe_load(_raw)
+    assert str(_truth.get("harness_tree")) == str(_target), f"⛔ 前提没成立({_form}): 真 PyYAML 给出 {_truth!r}"
+    _bad = _truncating_yaml(_cut)
+    assert "harness_tree" not in (_bad.safe_load(_raw) or {}), (
+        f"⛔ 前提没成立({_form}): 截断到 {_cut} 行没把真键丢掉, 那它就不是这一格要的负控输入"
+    )
+    #: 前提自证②：它仍答得对**两道探针**（否则它活不到词法层，这一格就成了别的门的重复）。
+    assert _bad.safe_load("a: 1") == {"a": 1}, f"⛔ 前提没成立({_form}): 截断器答不对第一道探针"
+
+    monkeypatch.setitem(sys.modules, "yaml", _bad)
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+
+    assert _got[0] == "exit", (
+        f"⛔ 丢尾巴的解析器没被拦住({_form})：返回 {_got[1]!r}\n"
+        f"   （父树 = {str(tmp_path)!r}，config 指着 {_target}）\n"
+        f"   ⇒ round-3 复核的 HIGH 回潮了。多半是键级探针的文档又变回单行了 ——\n"
+        f"     单行文档没有尾巴可丢，丢尾巴的解析器对它照样答得对。"
+    )
+    assert "读丢了文档的尾巴" in _got[1] or "读不出本写点唯一关心的那个键" in _got[1], (
+        f"⛔ 该落在**键级探针**那一层({_form}): {_got[1]!r}\n   ⇒ 拒因跑到别层 = 这一格实际测的不是它声称的那道判据。"
+    )
+
+
+@pytest.mark.parametrize("_form", sorted(_TRUNCATING_FORMS))
+def test_g33r2_harness_tree_truncating_forms_control_group(tmp_path, _form):
+    """控制组：同样三种书写形式 + **真 PyYAML** ⇒ 照常采用 config 指的那棵树。
+
+    ⛔ 少了这一格，上一门的「被拒」可能只是因为这三种写法本身生产就不支持 —— 那就
+    证不到「差别在于解析器丢没丢尾巴」。两门唯一的变量就是解析器。
+    """
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _usable_tree(tmp_path)
+    _target = _usable_tree(tmp_path / "target-tree")
+    _raw = _TRUNCATING_FORMS[_form][0].format(t=_target)
+    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+    assert _got == ("ok", os.path.realpath(str(_target))), (
+        f"⛔ 控制组不成立({_form}): 真 PyYAML 下这种合法写法也没被采用 ⇒ 上一门证不到因果: {_got!r}"
+    )
+
+
+def _tail_only_yaml(_n_lines):
+    """**非敌意**的坏解析器：只解析**最后** `_n_lines` 行（丢头，不是丢尾）。
+
+    ⛔ 它是 round-4 复核 L1 给的负控输入：对三行探针它只读到 `harness_tree: <哨兵>`，
+    于是**那个键的校验照样通过** —— 唯一拦得住它的是探针对 `a` / `b` 两项的校验。
+    """
+    import yaml as _real_yaml
+
+    _m = types.ModuleType("yaml")
+
+    def _safe_load(_stream, *_a, **_kw):
+        return _real_yaml.safe_load("\n".join(str(_stream).splitlines()[-_n_lines:]))
+
+    _m.safe_load = _safe_load
+    return _m
+
+
+def test_g33r2_harness_tree_tail_only_parser_is_refused(tmp_path, monkeypatch):
+    """⛔ 丢**头**的解析器也必须被拦 —— 拦它的是探针对前两行 `a` / `b` 的校验。
+
+    round-4 复核 L1：删掉生产那两项校验后，当时的 15 格（含新增七格）**仍全部通过** ——
+    因为所有既有负控都是「丢尾巴」形态，对它们来说末行的 `harness_tree` 才是关键，
+    前两行是不是对的无所谓。⇒ `a` / `b` 那两项校验当时是**门未覆盖的路径**。
+
+    本门补上它：一个只解析**最后一行**的解析器，对探针读到的正是
+    `harness_tree: <哨兵>`（那个键的校验会过），只有 `a` / `b` 拦得住它。
+    """
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _usable_tree(tmp_path)  # 父树可用 ⇒ 一旦静默回退就会「成功」地绑错树
+    _target = _usable_tree(tmp_path / "target-tree")
+    _raw = f'"harness_tree": {_target}\nnote: docs\n'
+    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+    import yaml as _real_yaml
+
+    #: 前提自证（四条，缺一这一格就测不到它声称的判据）：
+    _truth = _real_yaml.safe_load(_raw)
+    assert str(_truth.get("harness_tree")) == str(_target), f"⛔ 前提没成立: 真 PyYAML 给出 {_truth!r}"
+    _bad = _tail_only_yaml(1)
+    assert "harness_tree" not in (_bad.safe_load(_raw) or {}), "⛔ 前提没成立: 丢头解析器没把真键丢掉"
+    _probe_answer = _bad.safe_load(_KEY_PROBE_DOC)
+    assert _probe_answer.get("harness_tree") == "__quiz_answer_key_probe__", (
+        f"⛔ 前提没成立: 它对探针的**那个键**答错了 ⇒ 本格测的就不是 a/b 校验了: {_probe_answer!r}"
+    )
+    assert "a" not in _probe_answer and "b" not in _probe_answer, (
+        f"⛔ 前提没成立: 它没丢掉探针的前两行 ⇒ a/b 校验拦不到它: {_probe_answer!r}"
+    )
+
+    monkeypatch.setitem(sys.modules, "yaml", _bad)
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+
+    assert _got[0] == "exit", (
+        f"⛔ 丢**头**的解析器没被拦住：返回 {_got[1]!r}（父树 = {str(tmp_path)!r}）\n"
+        f"   ⇒ 多半是探针里对 `a` / `b` 的两项校验被删了 —— 那两项不是装饰，\n"
+        f"     它们是唯一拦得住「丢头」这一类的判据。"
+    )
+    assert "读不出本写点唯一关心的那个键" in _got[1] or "读丢了文档的尾巴" in _got[1], (
+        f"⛔ 该落在**键级探针**那一层: {_got[1]!r}"
+    )
+
+
+#: round-4 复核 L2 的负控输入：不是 `re.Pattern`，但把 `fullmatch` 委托给真正则 ——
+#: 四条行为探针全过，只有形状层的 `isinstance(..., re.Pattern)` 拦得住它。
+_VALIDATOR_STUB_WRAPPED_RE = (
+    _VALIDATOR_STUB_OK.replace(
+        "import re\n",
+        "import re\n\n\nclass _W:\n"
+        "    def __init__(self, r):\n        self._r = r\n"
+        "    def fullmatch(self, s):\n        return self._r.fullmatch(s)\n",
+        1,
+    )
+    .replace(
+        "_TS_RE = re.compile(",
+        "_TS_RE = _W(re.compile(",
+        1,
+    )
+    .replace(
+        '(?:\\.\\d+)?Z$")',
+        '(?:\\.\\d+)?Z$"))',
+        1,
+    )
+)
+
+
+def test_g33r2_harness_contract_refuses_a_non_pattern_wrapper(tmp_path):
+    """⛔ 名字在、行为对、但**不是编译正则** ⇒ 仍须拒（形状层）。
+
+    round-4 复核 L2：删掉生产那两行 `isinstance(..., re.Pattern)` 检查后，当时的六格契约
+    负控**仍全部通过** —— 因为它们拆的都是「行为」或「缺名字」，没有一格拆「类型对不对」。
+    ⇒ 形状层的这一半是**门未覆盖的路径**。
+
+    本门补上：一个把 `fullmatch` 委托给真正则的包装对象 —— 四条行为探针它全答得对，
+    只有 `isinstance` 拦得住它。
+    """
+    assert _VALIDATOR_STUB_WRAPPED_RE != _VALIDATOR_STUB_OK, "⛔ 前提没成立: 变体与底本逐字相同"
+    assert "_TS_RE = _W(re.compile(" in _VALIDATOR_STUB_WRAPPED_RE, "⛔ 前提没成立: 包装没生效"
+    _repo = _fake_validator_tree(tmp_path / "wrapped-re-tree", _VALIDATOR_STUB_WRAPPED_RE)
+
+    (_harness_contract,) = _extract("_harness_contract")
+    _got = _outcome(_harness_contract, str(_repo))
+
+    assert _got[0] == "exit", (
+        f"⛔ 一个不是 `re.Pattern`、但 `fullmatch` 委托给真正则的对象通过了契约门: {_got[1]!r}\n"
+        f"   ⇒ 多半是形状层的 `isinstance(..., re.Pattern)` 两行被删了。"
+    )
+    assert "不是编译正则" in _got[1], f"⛔ 该落在**形状层**: {_got[1]!r}"
+
+
+def test_g33r2_harness_tree_truthful_parser_still_binds_alt_tree():
+    """控制组：真 PyYAML + config 指向 alt 树 ⇒ 照常采用（词法否决没误伤正路）。"""
+    import tempfile
+
+    with tempfile.TemporaryDirectory() as _td:
+        _root = Path(_td)
+        _vd = _root / "canvas-vault"
+        _vd.mkdir()
+        _usable_tree(_root)
+        _alt = _usable_tree(_root / "alt-harness")
+        _raw = f'vault_id: "v"\nharness_tree: {_alt}\n'
+        (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+        (_harness_tree,) = _extract("_harness_tree")
+        _got = _outcome(_harness_tree, str(_vd))
+        assert _got == ("ok", os.path.realpath(str(_alt))), (
+            f"⛔ 真解析器给出了键, 就该采用那棵树({_alt}), 实得 {_got!r} —— 词法否决误伤了正路"
+        )
+
+
+def test_g33r2_harness_tree_real_list_document_falls_back():
+    """控制组：config 文件**本来就是个列表**（真 PyYAML）⇒ 按「没写这个键」回退父树。
+
+    ⛔ 这一格是 `parse_returns_junk` 的**正确场景**。原门用一个说谎的假模块制造
+    「非 dict」，再断言「回退父树是对的」—— 那把错误结果固化成了期望：文件里明明
+    写着目标树。「YAML 本身是列表 ⇒ 回退」这条语义要成立，文件就得真的是列表。
+    """
+    import tempfile
+
+    with tempfile.TemporaryDirectory() as _td:
+        _root = Path(_td)
+        _vd = _root / "canvas-vault"
+        _vd.mkdir()
+        _usable_tree(_root)
+        _raw = "- a\n- b\n"
+        (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+        #: 前提自证：真 PyYAML 对这份文件确实给出一个 list，且文件里**没有** harness_tree 字面键。
+        import yaml as _real_yaml
+
+        assert isinstance(_real_yaml.safe_load(_raw), list), "⛔ 前提没成立: 这份 config 不是列表"
+        assert re.search(r"^harness_tree[ \t]*:", _raw, re.M) is None, "⛔ 前提没成立: 文件里有 harness_tree 字面键"
+
+        (_harness_tree,) = _extract("_harness_tree")
+        _got = _outcome(_harness_tree, str(_vd))
+        assert _got == ("ok", str(_root)), (
+            f"⛔ 文件真的是列表(没有这个键)⇒ 应按「没写」回退父树 {str(_root)!r}, 实得 {_got!r}"
+        )
+
+
+# ══════════════════════════════════════════════════════════════════════════
+# ② 契约：选中的树必须是本写点认识的那套 validate_learning_events
+# ══════════════════════════════════════════════════════════════════════════
+_CONTRACT_CASES = {
+    "event_version_2": _VALIDATOR_STUB_OK.replace("EVENT_VERSION = 1", "EVENT_VERSION = 2"),
+    "version_bool": _VALIDATOR_STUB_OK.replace("EVENT_VERSION = 1", "EVENT_VERSION = True"),
+    "missing_name": _VALIDATOR_STUB_OK.replace("def _golden_manifest(*a, **kw):\n    return {}\n", ""),
+    "ts_re_rejects_z": _VALIDATOR_STUB_OK.replace(
+        '_TS_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z$")',
+        '_TS_RE = re.compile(r"^\\d{4}$")',
+    ),
+    #: round-3 复核 LOW-1：原表没有守住**形状层**（callable / 编译正则）的删除 ——
+    #: 内存删掉生产那两段后五格负控结局全不变。这一格补上：名字在、但不是函数。
+    "vault_id_of_not_callable": _VALIDATOR_STUB_OK.replace(
+        'def _vault_id_of(p):\n    return "占位"\n',
+        "_vault_id_of = None\n",
+    ),
+    "validate_accepts_scalar": _VALIDATOR_STUB_OK.replace(
+        '    if not isinstance(record, dict):\n        return (["顶层必须是 JSON object"], [])\n',
+        "",
+    ),
+    #: ⛔ 下面 5 格补的是**实测出来的门未覆盖的路径**（2026-09-19 变异探针，存档
+    #: `evidence-harness-tree-r2/probe-uncovered-judges-20260919T043826.txt`）：
+    #: 把生产里这 5 条判据逐条换成 `if False:`，349 格**一格不红** —— 它们当时完全没有
+    #: 门看着。round-4 复核指过这个方向（「表里缺专属负控」）并补了 2 格，但**没人去数
+    #: 还剩几条**，于是剩下这 5 条一直裸奔。⇒ 审查意见指出方向 ≠ 方向上的缺口都补完了。
+    #:
+    #: ⚠️ 注意 `ts_re_rejects_z`(旧) 与 `ts_re_accepts_bare_date`(新) 是同一个正则的
+    #: **两向**判据：旧表只锁了「该认的认」，「该拒的拒」删掉没人知道。
+    #: 契约是个**合取**（认该认的 ∧ 拒该拒的），门只测一半 ⇒ 一个恒返回 match 的假正则
+    #: 能过掉所有旧格。`_WHOLE_SECOND_RE` 当时**两向都没门**，下面两格各补一向。
+    "ts_re_accepts_bare_date": _VALIDATOR_STUB_OK.replace(
+        '_TS_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z$")',
+        '_TS_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}(?:T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?Z)?$")',
+    ),
+    "whole_second_re_rejects_whole_second": _VALIDATOR_STUB_OK.replace(
+        '_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$")',
+        '_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d+Z$")',
+    ),
+    "whole_second_re_accepts_missing_seconds": _VALIDATOR_STUB_OK.replace(
+        '_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$")',
+        '_WHOLE_SECOND_RE = re.compile(r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}(?::\\d{2})?Z$")',
+    ),
+    "classify_says_review_for_empty_frontmatter": _VALIDATOR_STUB_OK.replace(
+        'def classify_card_state(fields):\n    return ("new", "占位")\n',
+        'def classify_card_state(fields):\n    return ("review", "占位")\n',
+    ),
+    #: ⛔ 这一格刻意返回 `0` 而不是 `True`：生产判的是 `is not False`，
+    #: 写成 `if _vle._looks_like_review_ext({}):` 的话 `0` 会被放行。
+    #: 返回 `True` 两种写法都红 ⇒ 区分不出来；返回 `0` 才钉得住「用的是 `is not False`」。
+    "looks_like_returns_zero_not_false": _VALIDATOR_STUB_OK.replace(
+        "def _looks_like_review_ext(rec):\n    return False\n",
+        "def _looks_like_review_ext(rec):\n    return 0\n",
+    ),
+}
+
+
+@pytest.mark.parametrize("_case", sorted(_CONTRACT_CASES))
+def test_g33r2_harness_contract_refuses(tmp_path, _case):
+    """⛔ 选中的树不是本写点认识的那套 validator ⇒ **拒写**，不得静默按它的语义写账本。
+
+    收口前：写点从 `REPO` 无条件 `from validate_learning_events import <7 个名字>`，
+    除「导得进」外零判据。于是任意旧版/异版 harness 分发都会被采用 —— T7-A 已实测
+    的反例就是本仓 `b85a168a` 那棵旧树（`_vault_id_of` 是另一套实现，账本照写）。
+
+    每格只拆**一项**（版本 / 名字 / 正则语义 / 纯函数行为），其余全对 ⇒ 红了就一定
+    是那一项被抓住的，不是「随便哪里坏了都会红」。
+    """
+    _body = _CONTRACT_CASES[_case]
+    assert _body != _VALIDATOR_STUB_OK, f"⛔ 前提没成立: {_case} 的占位 validator 与全对底本逐字相同 = 没拆到东西"
+    _repo = _fake_validator_tree(tmp_path / f"tree-{_case}", _body)
+
+    (_harness_contract,) = _extract("_harness_contract")
+    _got = _outcome(_harness_contract, str(_repo))
+
+    assert _got[0] == "exit", f"⛔ 契约被拆了一项({_case}) 却照常放行 —— 写点会按这棵树的语义写账本: {_got[1]!r}"
+    assert ("契约不符" in _got[1]) or ("不是选中的树" in _got[1]), f"⛔ 拒因须点名契约({_case}): {_got[1]!r}"
+    assert _HALFSTATE_MARK in _got[1], f"⛔ 契约拒因须带半态标记({_case}): {_got[1]!r}"
+
+
+def test_g33r2_harness_contract_refuses_shadowed_module(tmp_path, monkeypatch):
+    """⛔ `sys.modules` 里先坐着一个同名模块 ⇒ 拒（影子门）。
+
+    树选对了不等于**导进来的就是那棵树的**：`sys.modules` 先到先得，一个早于本写点
+    被 import 的同名模块会让 `sys.path.insert` 完全失效，而 7 个名字照样导得到。
+    """
+    _repo = _real_harness(tmp_path / "real-tree")
+    _elsewhere = _fake_validator_tree(tmp_path / "elsewhere", _VALIDATOR_STUB_OK)
+    _shadow = types.ModuleType("validate_learning_events")
+    _shadow.__file__ = str(_elsewhere / "backend" / "scripts" / "validate_learning_events.py")
+    _shadow.EVENT_VERSION = 1
+    monkeypatch.setitem(sys.modules, "validate_learning_events", _shadow)
+
+    (_harness_contract,) = _extract("_harness_contract")
+    _got = _outcome(_harness_contract, str(_repo))
+
+    assert _got[0] == "exit", f"⛔ 导进来的是别处那一份, 却照常放行: {_got[1]!r}"
+    assert "不是选中的树" in _got[1], f"⛔ 影子拒因须说清来源不对: {_got[1]!r}"
+    assert str(_elsewhere) in _got[1], f"⛔ 影子拒因须报出**实际**来源路径, 否则用户无从查: {_got[1]!r}"
+
+
+def test_g33r2_harness_contract_accepts_real_tree(tmp_path):
+    """控制组：validator 是 symlink → 主干那一份的真树 ⇒ 返回 7 元组。
+
+    ⛔ 本格同时守着「影子判据比 `abspath` 不比 `realpath`」：这棵树合法，但它的
+    validator 物理上就在主干树里 —— 比 realpath 会把它判成影子，控制组当场红。
+    """
+    _repo = _real_harness(tmp_path / "real-tree")
+
+    (_harness_contract,) = _extract("_harness_contract")
+    _got = _outcome(_harness_contract, str(_repo))
+
+    assert _got[0] == "ok", f"⛔ 控制组不成立: 真树被契约门拒了 ⇒ 上面那些拒绝证不到是契约抓的: {_got[1]!r}"
+    _names = _got[1]
+    assert isinstance(_names, tuple) and len(_names) == 7, f"⛔ 应返回 7 个名字, 实得 {_names!r}"
+
+    import validate_learning_events as _vle
+
+    assert _names[6] is _vle._TS_RE, "⛔ 返回的 `_TS_RE` 不是选中那棵树里的那一个"
+    assert os.path.dirname(os.path.abspath(_vle.__file__)) == os.path.join(str(_repo), "backend", "scripts"), (
+        f"⛔ 前提没成立: 导进来的 validator 不在选中的树里 ({_vle.__file__})"
+    )
+
+
+# ══════════════════════════════════════════════════════════════════════════
+# ③ 半态：Step 2.9 预检先拒后写（subprocess 真跑，零 mock）
+# ══════════════════════════════════════════════════════════════════════════
+def _preflight_block() -> str:
+    """把 Step 2.9 预检块从 SKILL.md **逐字**抽出来（第 2 个 PYEOF 块）。"""
+    _pf = [b for b in _ALL_BLOCKS if "quiz-answer/preflight" in b]
+    assert len(_pf) == 1, (
+        f"⛔ SKILL.md 里应恰有 1 个 Step 2.9 预检块(含 `quiz-answer/preflight` 标记), 实见 {len(_pf)}"
+        " —— 改前红在这里属预期(还没加 Step 2.9)"
+    )
+    return _pf[0]
+
+
+def _preflight_vault(root: Path) -> Path:
+    """在 `tmp_path` 下搭一个标准布局 vault，把主干 SKILL.md 复制进去。"""
+    _vd = root / "canvas-vault"
+    _sk = _vd / ".claude" / "skills" / "quiz-answer"
+    _sk.mkdir(parents=True)
+    shutil.copy(SKILL, _sk / "SKILL.md")
+    (_vd / "节点").mkdir()
+    (_vd / "节点" / "概念.md").write_text("# 概念\n", encoding="utf-8")
+    return _vd
+
+
+def _pycache_dirs(root: Path) -> list:
+    """`root` 下所有 `__pycache__` 目录 —— 「纯读零写」里最容易漏掉的那一种写。"""
+    return sorted(str(_p.relative_to(root)) for _p in root.rglob("__pycache__"))
+
+
+def _run_preflight(_vd: Path, _env_extra: dict) -> subprocess.CompletedProcess:
+    """按**真实用户环境**跑预检。
+
+    ⛔ 这里**显式删掉** `PYTHONDONTWRITEBYTECODE`（round-2 复核 MEDIUM）：本函数原先把它
+    设成 `"1"`，理由写的是「否则 import validator 会在 fixture 树里落 `__pycache__`，零写
+    断言当场自毁」—— 那句话把因果说反了。真实用户跑 `/quiz-answer` 时环境里**没有**这个
+    变量，所以那条落盘路径是真实存在的，而这道门恰好把它关掉了 ⇒ **门未覆盖的路径**。
+    现在改成：门按真实环境跑，由**预检块自己** `sys.dont_write_bytecode = True` 去保证
+    零写 —— 声称是它作出的，保证也该由它给。
+    """
+    _env = dict(os.environ)
+    _env.pop("PYTHONDONTWRITEBYTECODE", None)
+    _env["QUIZ_ANSWER_NODE"] = str(_vd / "节点" / "概念.md")
+    _env.update(_env_extra)
+    return subprocess.run(
+        [sys.executable, "-"],
+        input=_preflight_block(),
+        env=_env,
+        capture_output=True,
+        text=True,
+        cwd=str(_vd),
+        timeout=120,
+    )
+
+
+def _write_face(root: Path) -> set:
+    """vault 下每个文件的 (相对路径, 大小, mtime_ns) —— 零写断言的比较面。"""
+    _face = set()
+    for _p in sorted(root.rglob("*")):
+        if _p.is_file():
+            _st = _p.stat()
+            _face.add((str(_p.relative_to(root)), _st.st_size, _st.st_mtime_ns))
+    return _face
+
+
+_PREFLIGHT_REFUSALS = ("no_pyyaml", "bad_tree", "contract_broken")
+
+
+@pytest.mark.parametrize("_case", _PREFLIGHT_REFUSALS)
+def test_g33r2_preflight_refuses_before_step3(tmp_path, _case):
+    """⛔ Step 2.9 预检在 **Step 3 写分之前** 就拒，且**一个字节都不写**。
+
+    收口前的顺序是：Step 3 用 `Edit` 写分 + 置 `scored_pending_node_update` →
+    Step 4 主写点建锁 → 才发现拿不到 PyYAML ⇒ 拒。白板就停在「已记分、节点未更新」
+    这个半态上（UAT #23）。用户看到的是一个记了分却没更新的检验白板，而真正的原因
+    （装错了解释器）只出现在一段早已滚过去的 stderr 里。
+
+    ⛔ 「不写」是本门的承重断言，不是「rc≠0 就算」：预检若顺手建了锁 / 落了
+    `__pycache__` / 起了 payload 暂存，它就不再是**纯读**的前置检查，放在 Step 3
+    之前反而多了一处可失败的写。
+    """
+    _vd = _preflight_vault(tmp_path)
+    _env_extra: dict = {}
+
+    if _case == "no_pyyaml":
+        #: 负控输入 = 坏环境的形态：`PYTHONPATH` 前置一个导入即抛的同名 `yaml.py`。
+        _stub = tmp_path / "no-yaml"
+        _stub.mkdir()
+        (_stub / "yaml.py").write_text('raise ImportError("本机没有装 PyYAML")\n', encoding="utf-8")
+        _env_extra["PYTHONPATH"] = str(_stub)
+        _repo = _real_harness(tmp_path / "harness")
+        (_vd / ".canvas-config.yaml").write_text(f"harness_tree: {_repo}\n", encoding="utf-8")
+        _want = _NO_YAML_REFUSAL
+    elif _case == "bad_tree":
+        (_vd / ".canvas-config.yaml").write_text(
+            f"harness_tree: {tmp_path / 'this-tree-does-not-exist'}\n", encoding="utf-8"
+        )
+        _want = "指向不存在的树"
+    else:  # contract_broken
+        _repo = _fake_validator_tree(
+            tmp_path / "broken-harness",
+            _VALIDATOR_STUB_OK.replace("EVENT_VERSION = 1", "EVENT_VERSION = 2"),
+        )
+        (_vd / ".canvas-config.yaml").write_text(f"harness_tree: {_repo}\n", encoding="utf-8")
+        _want = "契约不符"
+
+    _face0 = _write_face(_vd)
+    _r = _run_preflight(_vd, _env_extra)
+
+    assert _r.returncode != 0, (
+        f"⛔ 预检放行了({_case}) ⇒ 流程会往 Step 3 写分, 半态白板照旧: stdout={_r.stdout[-400:]!r}"
+    )
+    assert _want in _r.stderr, f"⛔ 拒因须点名「{_want}」({_case}): {_r.stderr[-600:]!r}"
+    assert _HALFSTATE_MARK in _r.stderr, (
+        f"⛔ 拒因须带半态标记(既有半态白板分数保留、不回滚)({_case}): {_r.stderr[-600:]!r}"
+    )
+    assert _write_face(_vd) == _face0, f"⛔ 预检是纯读的前置检查, 拒绝时写入面必须逐字节不变({_case})"
+    assert not (_vd / ".locks").exists(), f"⛔ 预检不得建锁({_case}) —— 锁是主写点 Step 4 的事"
+    assert _pycache_dirs(tmp_path) == [], (
+        f"⛔ 预检落了字节码({_case}): {_pycache_dirs(tmp_path)}\n"
+        f"   ⇒ 「纯读零写」的声称不成立。本门按**真实用户环境**跑（不设 PYTHONDONTWRITEBYTECODE），"
+        f"该由预检块自己 `sys.dont_write_bytecode = True` 保证。"
+    )
+
+
+def test_g33r2_preflight_refuses_without_node_env(tmp_path):
+    """⛔ 环境变量没传进来 ⇒ 给一句话拒因，不是一段 traceback。
+
+    预检整个的价值就在于「把拒绝说清楚」——用户看到 `KeyError: 'QUIZ_ANSWER_NODE'`
+    是学不到任何东西的，而这恰恰是最容易发生的一种失败（prose 里那行 `QUIZ_ANSWER_NODE=…`
+    被漏抄了）。
+    """
+    _vd = _preflight_vault(tmp_path)
+    _env = dict(os.environ)
+    _env.pop("PYTHONDONTWRITEBYTECODE", None)  # 真实用户环境，见 `_run_preflight` 的 docstring
+    _env.pop("QUIZ_ANSWER_NODE", None)
+    _face0 = _write_face(_vd)
+    _r = subprocess.run(
+        [sys.executable, "-"],
+        input=_preflight_block(),
+        env=_env,
+        capture_output=True,
+        text=True,
+        cwd=str(_vd),
+        timeout=120,
+    )
+
+    assert _r.returncode != 0, f"⛔ 环境变量没传却放行了: {_r.stdout[-300:]!r}"
+    assert "QUIZ_ANSWER_NODE" in _r.stderr, f"⛔ 拒因须点名是哪个环境变量没传: {_r.stderr[-400:]!r}"
+    assert "Traceback" not in _r.stderr, (
+        f"⛔ 这条路径吐了 traceback 而不是一句话拒因 —— 多半是 `os.environ[…]` 下标写法: {_r.stderr[-400:]!r}"
+    )
+    assert _write_face(_vd) == _face0, "⛔ 拒绝时写入面必须逐字节不变"
+
+
+def test_g33r2_preflight_passes_on_a_good_vault(tmp_path):
+    """控制组：库在、树在、契约对 ⇒ 预检 rc=0 并报出选中的树。
+
+    少了这一半，上面那三格「被拒」可能只是因为预检块本身压根跑不起来。
+    """
+    _vd = _preflight_vault(tmp_path)
+    _repo = _real_harness(tmp_path / "harness")
+    (_vd / ".canvas-config.yaml").write_text(f"harness_tree: {_repo}\n", encoding="utf-8")
+
+    _r = _run_preflight(_vd, {})
+
+    assert _r.returncode == 0, f"⛔ 控制组不成立: 好 vault 也被预检拒了: {_r.stderr[-600:]!r}"
+    assert "契约 ok" in _r.stdout, f"⛔ 预检通过时应报出结论: {_r.stdout!r}"
+    assert os.path.realpath(str(_repo)) in _r.stdout, (
+        f"⛔ 预检应报出**选中的那棵树**, 否则用户无从确认它找对了本子: {_r.stdout!r}"
+    )
+    #: ⛔ 控制组这一格才是最会落盘的：它一路走到 `import validate_learning_events`。
+    #: 按真实用户环境跑（`_run_preflight` 已删掉 PYTHONDONTWRITEBYTECODE）⇒ 若预检块
+    #: 自己没把字节码关掉，这里会在 harness 树里看到 `__pycache__`。
+    assert _pycache_dirs(tmp_path) == [], (
+        f"⛔ 预检**通过**这条路上落了字节码: {_pycache_dirs(tmp_path)}\n"
+        f"   ⇒ 「纯读零写」的声称不成立（这一格一路走到 import validator，最容易暴露）。"
+    )
+
+
+# ══════════════════════════════════════════════════════════════════════════
+# ④ 结构门：Step 2.9 的位置与块序（(e)⑤）
+# ══════════════════════════════════════════════════════════════════════════
+def test_g33r2_step29_precedes_step3():
+    """⛔ `## Step 2.9` 必须排在 `## Step 3` **之前** —— 否则「先拒后写」就是空话。
+
+    本门钉的是**顺序**这个性质本身：预检块写得再对，排在写分之后也救不了半态白板。
+    """
+    _lines = _SKILL_TEXT.splitlines()
+    _s29 = [i for i, ln in enumerate(_lines, 1) if ln.startswith("## Step 2.9")]
+    _s3 = [i for i, ln in enumerate(_lines, 1) if ln.startswith("## Step 3 ·")]
+    assert len(_s29) == 1, f"⛔ SKILL.md 应恰有 1 个 `## Step 2.9` 标题, 实见 {len(_s29)} —— 改前红在这里属预期"
+    assert len(_s3) == 1, f"⛔ SKILL.md 应恰有 1 个 `## Step 3 ·` 标题, 实见 {len(_s3)}"
+    assert _s29[0] < _s3[0], f"⛔ Step 2.9 在 :{_s29[0]}、Step 3 在 :{_s3[0]} —— 预检排在写分之后 = 半态照旧"
+
+
+def test_g33r2_preflight_block_precedes_step3():
+    """⛔ **可执行的那个块本身**必须排在 Step 3 的写分指令之前 —— 不是只有标题。
+
+    round-5 复核在这里抓到一个**门未覆盖的路径**：把预检的 fenced block 单独挪到 Step 3
+    指令之后（`## Step 2.9` 标题留在原地），当时的两道结构门**都 PASS** ——
+      · `..._step29_precedes_step3` 测的是「`## Step 2.9` **标题**的行号」；
+      · `..._preflight_is_the_second_pyeof_block_…` 测的是「在 PYEOF 序列里的**序号**」。
+    标题在前、块在后，「先拒后写」当场失效，而两道门都看不见。⇒ 缺的是**块自己的位置**。
+
+    本门把三样东西钉在一条线上：`## Step 2.9` 标题 < 预检 fence < `## Step 3 ·` 标题。
+    中间那一条是新的；两头那两条顺带保证标题没有脱离它描述的块。
+    """
+    _text = _SKILL_TEXT
+    _i_title = _text.index("## Step 2.9")
+    _i_step3 = _text.index("## Step 3 · ")
+    _fence = "```bash\nQUIZ_ANSWER_NODE='节点/<concept>.md' python3 - <<'PYEOF'\n"
+    assert _text.count(_fence) == 1, f"⛔ 预检 fence 应恰 1 处, 实见 {_text.count(_fence)}"
+    _i_block = _text.index(_fence)
+
+    def _line(_o):
+        return _text[:_o].count("\n") + 1
+
+    assert _i_title < _i_block, (
+        f"⛔ `## Step 2.9` 标题（行 {_line(_i_title)}）排在预检块（行 {_line(_i_block)}）之后 —— 标题脱离了它描述的块。"
+    )
+    assert _i_block < _i_step3, (
+        f"⛔ **预检块本身**在行 {_line(_i_block)}，而 `## Step 3 ·` 在行 {_line(_i_step3)} ——"
+        f" 块排在写分指令之后，「先拒后写」失效。\n"
+        f"   ⚠️ 只看标题位置的门看不见这个：标题可以留在原地而块被挪走"
+        f"（round-5 复核实测两道旧门在这种形态下都 PASS）。"
+    )
+    #: 顺带钉住块**确实是预检块**——否则上面三条比的可能是另一个 fence。
+    assert "quiz-answer/preflight" in _text[_i_block : _i_block + 4000], (
+        "⛔ 那个 fence 之后的内容里没有 `quiz-answer/preflight` 标记 —— 比错块了"
+    )
+
+
+def test_g33r2_preflight_is_the_second_pyeof_block_and_main_stays_single():
+    """⛔ 预检块是文件第 2 个 PYEOF 块，且主写点块仍**恰 1** 个。
+
+    `_MAIN_BLOCKS` 的过滤器（`P = "/tmp/quiz-answer-payload.json"`）是 test_g3_2 的
+    夹具基石：预检块若含那个字面量，那边 collect 当场 ERROR。本门在这一侧钉住它。
+
+    ⛔ 同理，预检块不得含 `def _harness_tree(` 字面量 —— 它自己要按这个串去定位
+    主块，写成字面量的话「含该锚的块恰 1」当场自指失效（块序判据变成恒真）。
+    """
+    assert len(_MAIN_BLOCKS) == 1, f"⛔ 主写点块应恰 1, 实见 {len(_MAIN_BLOCKS)}"
+    assert len(_ALL_BLOCKS) == 3, (
+        f"⛔ SKILL.md 应有 3 个 PYEOF 块(A3 增量 / Step 2.9 预检 / 主写点), 实见 {len(_ALL_BLOCKS)}"
+    )
+
+    _pf = _preflight_block()
+    assert _ALL_BLOCKS[1] is _pf, "⛔ 预检块应是文件第 2 个 PYEOF 块(A3 增量第 1、主写点第 3)"
+    assert 'P = "/tmp/quiz-answer-payload.json"' not in _pf, (
+        "⛔ 预检块含主块过滤字面量 ⇒ test_g3_2 夹具 collect 会 ERROR"
+    )
+    assert "/tmp" not in _pf, "⛔ 预检块不得出现 `/tmp` —— 会动 lint 的 `tmp_all` 基线与块指纹集合"
+    assert "def _harness_tree(" not in _pf, "⛔ 预检块含定位锚字面量 ⇒ 它自己也会命中, 自指失效"
+    assert "fsrs_bridge" not in _pf, "⛔ 预检块不得 import `fsrs_bridge`(零写者 vault 脚本, 与选树无关)"
+
+    _anchored = [b for b in _ALL_BLOCKS if "def _harness_tree(" in b]
+    assert len(_anchored) == 1, f"⛔ 含 `def _harness_tree(` 的块应恰 1(预检块靠它定位), 实见 {len(_anchored)}"
+
+
+# ══════════════════════════════════════════════════════════════════════════
+# ⑤ 门未覆盖的路径（2026-09-19 变异探针实测补齐）
+# ══════════════════════════════════════════════════════════════════════════
+#: 手法：把生产里每一条判据的条件逐个换成 `if False:`（= 让它永不拒绝，语法与函数体
+#: 一字不动），看 349 格里有没有任何一格会红。红 ⇒ 有门看着；全绿 ⇒ 这条判据现在
+#: 删掉也没人知道。存档 `evidence-harness-tree-r2/probe-uncovered-judges-20260919T043826.txt`
+#: （同目录 …T043255.txt 是**作废**的第一版，头部写了它为什么假绿）。
+#:
+#: ⚠️ 该手法对**控制流型**判据（决定要不要执行某段）不适用：换成 `False` 会抽掉后续
+#: 代码的前提，红成一片（`tree-cf-is-none` 35 格、`tree-not-tree` 121 格），
+#: 那种红不构成「有门看着这条判据」，只证明代码崩了。下面两格补的是**校验/补全型**
+#: 的两条真缺口。
+
+
+def _needs_trailing_newline_yaml():
+    """要求文档以换行结尾的坏解析器 —— 没有结尾换行就给 `None`。
+
+    ⛔ 它是**坏环境本身的形态**，不是对被测代码的 mock：流式读取器把最后一行没有换行的
+    内容当作不完整记录丢掉，是真实存在的事故形态。
+
+    关键在于它**只**在第一道探针上出错：
+      · 第一道探针的输入是 `"a: 1"` —— **没有**结尾换行 ⇒ 它给 `None`；
+      · 键级探针的输入 `_KPROBE_DOC` 以换行结尾 ⇒ 它老实回答。
+    """
+    import yaml as _real_yaml
+
+    _m = types.ModuleType("yaml")
+
+    def _safe_load(_stream, *_a, **_kw):
+        _s = str(_stream)
+        if not _s.endswith("\n"):
+            return None
+        return _real_yaml.safe_load(_s)
+
+    _m.safe_load = _safe_load
+    return _m
+
+
+def test_g33r2_first_probe_catches_what_the_key_probe_cannot(tmp_path, monkeypatch):
+    """⛔ 第一道通用探针有一个**未被键级探针接替**的观测点，本格是它唯一的门。
+
+    实测（2026-09-19）：把第一道探针的 `_probe.get("a") == 1` 判据换成 `if False:`，
+    349 格**一格不红**。当时第一反应是「它冗余了 —— 键级探针的文档含 `a: 1` 且校验
+    `a == 1`，把它的活全接了」。**那只对了一半**：键级探针的文档是三行、**以换行结尾**的，
+    它验不到「解析器对一份**没有结尾换行的单行文档**怎么处理」。
+
+    ⇒ 覆盖归属必须逐条列**未被接替的观测点**，不能只说「归到哪」——
+      「A 的职责被 B 接了」这句话，要能撑住得先证明 A 的每个观测点 B 都看得到。
+    """
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _usable_tree(tmp_path)  # 父树可用 ⇒ 一旦静默回退就会「成功」地绑错树
+    _target = _usable_tree(tmp_path / "target-tree")
+    (_vd / ".canvas-config.yaml").write_text(f"harness_tree: {_target}\n", encoding="utf-8")
+
+    _bad = _needs_trailing_newline_yaml()
+
+    #: 前提自证（三条，缺一这格就不是在测它声称的东西）
+    assert _bad.safe_load("a: 1") is None, "⛔ 前提没成立: 它对第一道探针的输入并没有出错"
+    assert _bad.safe_load(_KEY_PROBE_DOC) == {
+        "a": 1,
+        "b": 2,
+        "harness_tree": "__quiz_answer_key_probe__",
+    }, "⛔ 前提没成立: 它对键级探针答错了 ⇒ 这格测的就不是「第一道探针独有」那个观测点了"
+    assert _KEY_PROBE_DOC.endswith("\n"), "⛔ 前提没成立: 键级探针文档不以换行结尾 ⇒ 两道探针在这一点上没差别, 本格空转"
+
+    monkeypatch.setitem(sys.modules, "yaml", _bad)
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+
+    assert _got[0] == "exit", (
+        f"⛔ 第一道探针没拦住它 —— 而键级探针也拦不住(前提已证它答得对) ⇒ 会径直走到读 config。\n"
+        f"   实得 {_got!r}(父树 = {tmp_path}, config 指着 {_target})"
+    )
+    assert "PyYAML 不可用" in _got[1], f"⛔ 该落在「拿不到 PyYAML」那一层: {_got[1]!r}"
+    assert "对 'a: 1' 给出的是" in _got[1], f"⛔ 拒因必须点名**第一道探针**, 否则别的层红了这格也算过: {_got[1]!r}"
+
+
+def test_g33r2_relative_harness_tree_is_resolved_against_the_vault(tmp_path):
+    """⛔ config 写**相对路径**时必须相对 vault 目录补全，本格是这条判据唯一的门。
+
+    实测（2026-09-19）：把 `if not os.path.isabs(_given):` 换成 `if False:` 后
+    349 格一格不红 —— 补全这一步当时完全没有门看着。
+
+    ⚠️ 删掉它的后果**不是报错**，是解析基准悄悄从 vault 目录换成**进程 CWD**：
+    同一份 config 在不同工作目录下指向不同的树。而 `quiz-answer` 是被别处调起来的，
+    CWD 不由用户控制 —— 这正是本卡反复在防的那类「静默绑错树」。
+    """
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _usable_tree(tmp_path)  # 父树可用 ⇒ 回退也会「成功」
+    _alt = _usable_tree(_vd / "alt-tree")  # 相对 vault 的目标树
+    (_vd / ".canvas-config.yaml").write_text("harness_tree: alt-tree\n", encoding="utf-8")
+
+    #: 前提自证：这个相对路径**不能**恰好在 CWD 下也解析得通，否则两种基准给同一答案
+    assert not os.path.isdir(os.path.join(os.getcwd(), "alt-tree", "backend", "scripts")), (
+        f"⛔ 前提没成立: CWD({os.getcwd()}) 下也有一棵 alt-tree ⇒ 两种基准同答案, 本格证不到东西"
+    )
+
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+
+    assert _got[0] == "ok", f"⛔ 相对路径应被补全后接受, 实得: {_got!r}"
+    assert _got[1] == os.path.realpath(_alt), (
+        f"⛔ 补全基准错了 —— 期望相对 vault 目录({_vd})解析到 {os.path.realpath(_alt)}, 实得 {_got[1]!r}"
+    )
+
+
+def test_g33r2_lexical_veto_does_not_over_match_a_similar_key(tmp_path):
+    """⛔ 词法否决**不得过宽**：`harness_tree_backup:` 不是 `harness_tree:`。
+
+    这一格钉的是生产正则**末尾那个冒号**。把 `^harness_tree[ \t]*:` 写成 `^harness_tree`
+    （少一个字符，而且是「简化正则」这类清理里最常见的一种）之后：
+    一份完全合法、真 PyYAML 解析正确、顶层**只有** `harness_tree_backup` 的 config
+    会命中词法正则 ⇒ 而解析结果里确实没有 `harness_tree` 键 ⇒ **误拒**。
+
+    ⚠️ 本格与 `..._lexical_veto_false_refusal_cost_is_accepted` 三格的区别：
+    那三格钉的是**已接受的**误拒（那串字确实以顶格形式出现在文件里）；
+    这一格钉的是**不该有的**误拒（文件里根本没有那个键，只有一个名字以它开头的**别的键**）。
+    两者都期望某个结局，但含义相反 —— 所以不能合并。
+
+    ⚠️ 为什么 2026-09-19 的覆盖实测没抓到这一向：那次把 15 条 `if` 判据换 `if False:`，
+    而 `_lex = re.search(...)` 是**赋值语句**，判据内容在赋值右侧，那套枚举够不着。
+    """
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _parent = _usable_tree(tmp_path)  # 没有 harness_tree 键 ⇒ 正确行为是回退到它
+    _raw = 'vault_id: "v"\nharness_tree_backup: /nowhere/at/all\n'
+    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+    #: 前提自证（两条）：① 真 PyYAML 解析成功且顶层**没有** harness_tree；
+    #: ② 但它确实有一个**名字以它开头**的别的键 —— 否则这一格测不到「过宽」。
+    import yaml as _real_yaml
+
+    _truth = _real_yaml.safe_load(_raw)
+    assert isinstance(_truth, dict) and "harness_tree" not in _truth, (
+        f"⛔ 前提没成立: 真 PyYAML 给出 {_truth!r} —— 这份 config 顶层不该有 harness_tree"
+    )
+    assert any(k.startswith("harness_tree") for k in _truth), (
+        f"⛔ 前提没成立: 没有以 harness_tree 开头的别的键 ⇒ 本格测不到「否决过宽」: {_truth!r}"
+    )
+
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+
+    assert _got[0] == "ok", (
+        "⛔ 词法否决**过宽**了：文件里根本没有 harness_tree 键，只有一个名字以它开头的\n"
+        f"   别的键（harness_tree_backup），却被当成「解析结果与文件内容不符」拒掉。\n"
+        f"   实得 {_got!r}\n"
+        "   ⇒ 多半是生产正则末尾的 `:` 被去掉了（`^harness_tree[ \\t]*:` → `^harness_tree`）。"
+    )
+    assert _got[1] == os.path.realpath(_parent), (
+        f"⛔ 没有 harness_tree 键时应回退父目录 {os.path.realpath(_parent)}, 实得 {_got[1]!r}"
+    )
+
+
+#: 词法正则 `^harness_tree[ \t]*:` 的**第三个**承重 token：行首锚 `^`。
+#: 这三份 config 都含 `harness_tree:` 字样，但**都不在行首**，真 PyYAML 顶层也都没有该键
+#: ⇒ 正确行为是**回退父树**（`ok`），不是拒。
+#: ⛔ 第一种正是本写点 docstring **明文承诺**的那一句：「注释掉的 `# harness_tree:` 不顶格
+#: ⇒ 正则不命中, 也照旧回退」—— 在本格之前，那是一条**零门的行为契约**。
+_NON_ANCHORED_FORMS = {
+    "commented_out": '# harness_tree: /old/tree\nvault_id: "v"\n',
+    "inline_comment": 'vault_id: "v"   # 想换树就改 harness_tree: 这一项\n',
+    "indented_nested": 'nested:\n  harness_tree: /a/b\nvault_id: "v"\n',
+}
+
+
+@pytest.mark.parametrize("_form", sorted(_NON_ANCHORED_FORMS))
+def test_g33r2_lexical_veto_requires_the_line_start_anchor(tmp_path, _form):
+    """⛔ 词法否决只认**顶格**：那串字出现在注释里/缩进里，不构成「文件明文写着这个键」。
+
+    人审替代轮 v3 的发现：生产正则三个承重 token（`^` / `[ \t]*` / 末尾 `:`）里，
+    前一轮给后两个各补了一格，**`^` 一个门都没有** —— 删掉它 358 个 nodeid 一格不红。
+
+    ⚠️ 与 `..._lexical_veto_false_refusal_cost_is_accepted` 三格的区别（不能合并）：
+    那三格里那串字**确实以顶格形式**出现在文件中，被拒是**已接受的代价**；
+    这三格里它**不在行首**，被拒就是**不该有的**误拒。两边都断言某个结局，含义相反。
+
+    ⚠️ 与 `..._does_not_over_match_a_similar_key` 的区别：那格钉**末尾冒号**
+    （`harness_tree_backup:` 不是 `harness_tree:`），这格钉**行首锚**。
+
+    ⛔ 定级如实：删掉 `^` 的后果是否决**多发**（可见的误拒），不是**漏发**（静默绑错树）——
+    `re.search` 去掉 `^` 是匹配集的严格超集，而 `_lex` 只进
+    `if _lex and (key not in _doc): raise`，所以 r10 H1 的复活路径结构上到不了这里。
+    这与 `[ \t]*` 那一向**不对称**：那个删掉是收窄 ⇒ 漏发 ⇒ 静默绑错树。
+    ⇒ 「这条判据没有门」不足以定级，要问**它坏掉时系统往哪个方向坏**。
+    """
+    _vd = tmp_path / "canvas-vault"
+    _vd.mkdir()
+    _parent = _usable_tree(tmp_path)  # 没有顶层 harness_tree 键 ⇒ 正确行为是回退到它
+    _raw = _NON_ANCHORED_FORMS[_form]
+    (_vd / ".canvas-config.yaml").write_text(_raw, encoding="utf-8")
+
+    #: 前提自证（三条）：① 真 PyYAML 解析成功且顶层**没有** harness_tree；
+    #: ② 文本里**确实含**那串字（否则本格与 `^` 无关，测的是别的东西）；
+    #: ③ 但它**不在任何一行的行首**（否则它属于「已接受的误拒面」，期望应当相反）。
+    import yaml as _real_yaml
+
+    _truth = _real_yaml.safe_load(_raw)
+    assert isinstance(_truth, dict) and "harness_tree" not in _truth, (
+        f"⛔ 前提没成立({_form}): 真 PyYAML 给出 {_truth!r} —— 顶层不该有 harness_tree"
+    )
+    assert "harness_tree:" in _raw, f"⛔ 前提没成立({_form}): 文本里没有那串字 ⇒ 本格与行首锚无关"
+    assert re.search(r"^harness_tree[ \t]*:", _raw, re.M) is None, (
+        f"⛔ 前提没成立({_form}): 它顶格命中了 ⇒ 属「已接受的误拒面」, 本格的期望应当相反"
+    )
+
+    (_harness_tree,) = _extract("_harness_tree")
+    _got = _outcome(_harness_tree, str(_vd))
+
+    assert _got[0] == "ok", (
+        f"⛔ 词法否决把**非顶格**出现的那串字当成了「文件明文写着这个键」({_form})。\n"
+        f"   文件: {_raw!r}\n   实得 {_got!r}\n"
+        "   ⇒ 多半是生产正则的行首锚 `^` 被删了（`^harness_tree[ \\t]*:` → `harness_tree[ \\t]*:`）。"
+    )
+    assert _got[1] == os.path.realpath(_parent), (
+        f"⛔ 顶层没有该键时应回退父目录 {os.path.realpath(_parent)}, 实得 {_got[1]!r}({_form})"
+    )
diff --git a/canvas-vault/.claude/skills/quiz-answer/SKILL.md b/canvas-vault/.claude/skills/quiz-answer/SKILL.md
index cefecb72..598b3bb2 100644
--- a/canvas-vault/.claude/skills/quiz-answer/SKILL.md
+++ b/canvas-vault/.claude/skills/quiz-answer/SKILL.md
@@ -186,6 +186,82 @@ PYEOF
   - 1 = 空泛/错误；2 = 部分正确但有实质缺口；3 = 正确且基本完整；4 = 正确完整且能自发联系/举例（流利）。
 - `grade` = 4 维均值（1–4）；`grade_norm = (grade - 1) / 3`。⛔ 分数先不显示。
 
+## Step 2.9 · harness 预检（写分之前先证树在、库在、契约对）
+
+⛔ **先拒后写**：Step 3 会用 `Edit` 往检验白板写分并置 `scored_pending_node_update`，而
+真正需要 harness 树的是 Step 4 的主写点。两者之间任何一次拒写，都会把白板留在
+「**已记分、节点没更新**」这个半态上——用户看到的是一块记了分的白板加一段看不懂的报错，
+而真正的原因（装错了解释器 / config 指错了树 / 那棵树不是本写点认识的那一套）早已滚出屏幕。
+
+所以把「这次到底能不能写成」挪到写分**之前**问一遍。本块**纯读零写**：不建锁、不读 payload、
+不落任何文件，它只回答一个问题——待会儿 Step 4 要用的那棵树，现在找得到、库在、契约对不对。
+
+- **预检 rc ≠ 0 ⇒ 停在 Step 2，不进 Step 3，不写分**，把拒因**原样**回给用户（别改写、别摘要）。
+- 既有的半态白板**不回滚**：分数保留，拒因里已经点明「装好 PyYAML / 修好 config 后重跑
+  `/quiz-answer` 从 Step 0 续写」——Step 0 的 `scored_pending_node_update` 续跑态会接上。
+- `<concept>` 换成本次的节点名；路径经**环境变量**传入，**不拼进代码**。
+
+```bash
+QUIZ_ANSWER_NODE='节点/<concept>.md' python3 - <<'PYEOF'
+import sys
+
+#: ⛔ **先关字节码, 再 import 别的**(round-3 复核 MEDIUM): 这一行原先排在
+#: `import ast, os, re, sys` **之后** —— 冷缓存环境下那一行自己就可能触发标准库的
+#: `__pycache__` 写入。`sys` 在解释器启动时已经载入, 单独 import 它不新增落盘面。
+sys.dont_write_bytecode = True
+
+import ast, os, re  # noqa: E402  —— 必须排在上面那一行之后, 顺序本身就是判据
+
+#: ⛔ 预检声称**纯读零写**, 那就得自己把字节码关掉(round-2 复核 MEDIUM, 已实测):
+#: 下面 `_harness_contract` 会 `import validate_learning_events`, 而真实用户跑
+#: `/quiz-answer` 时环境里**没有** `PYTHONDONTWRITEBYTECODE` —— Python 会往选中的那棵
+#: harness 树的 `backend/scripts/` 落 `__pycache__`。零写的那道门恰好设了那个环境变量,
+#: 所以这条路径在门下看不见(A/B 对照实测: 不设 ⇒ 落 1 个; 设了 ⇒ 0 个)。
+#: 写在这里而不是靠调用方传环境变量: 声称是这个块自己作出的, 保证也该由它自己给。
+
+#: ⛔ 用 `.get` 而不是下标: 环境变量没传进来时下标抛的是 KeyError, 用户看到的是一段
+#: traceback 而不是一句话 —— 预检的整个价值就在于「把拒绝说清楚」, 这里漏一句就少一半。
+NODE = os.environ.get("QUIZ_ANSWER_NODE", "")
+if not NODE:
+    raise SystemExit("[quiz-answer/preflight] 环境变量 QUIZ_ANSWER_NODE 没传进来(或是空串) — 预检不知道该查哪块白板所在的 vault, fail-closed 拒写 —— 停在 Step 2, 不写分")
+VAULT = os.path.dirname(os.path.dirname(os.path.abspath(NODE)))
+_SK = os.path.join(VAULT, ".claude", "skills", "quiz-answer", "SKILL.md")
+try:
+    with open(_SK, encoding="utf-8") as _f:
+        _TEXT = _f.read()
+except OSError as _e:
+    raise SystemExit(f"[quiz-answer/preflight] 读不到本写点自己 ({_SK}: {_e}) — vault 不是标准布局 (预期 <vault> 根下的 .claude 里有 skills 目录, 内含 quiz-answer/SKILL.md), 预检无从自证, fail-closed 拒写 —— 停在 Step 2, 不写分")
+#: ⛔ 两个定位锚都**拼出来**, 不写成字面量: 写成字面量的话本块自己就会命中自己,
+#: 「含该锚的块恰 1」当场自指失效, 判据变成恒真 —— 判据的输入面不能包含判据本身。
+_FENCE = "python3 - <<'" + "PYEOF" + "'"
+_ANCHOR = "def " + "_harness_tree" + "("
+_BLOCKS = [_b for _b in re.findall(_FENCE + r"\n(.*?)\n" + "PYEOF", _TEXT, re.S) if _ANCHOR in _b]
+if len(_BLOCKS) != 1:
+    raise SystemExit(f"[quiz-answer/preflight] 写点里带 harness 解析的块应恰 1 处, 实见 {len(_BLOCKS)} — 预检无从自证, fail-closed 拒写 —— 停在 Step 2, 不写分")
+_MOD = ast.parse(_BLOCKS[0])
+_WANT = ("_harness_tree", "_harness_contract")
+_FNS = [_n for _n in _MOD.body if isinstance(_n, ast.FunctionDef) and _n.name in _WANT]
+if len(_FNS) != len(_WANT):
+    raise SystemExit(f"[quiz-answer/preflight] 写点里 {_WANT} 应各恰 1 处, 实见 {[_n.name for _n in _FNS]} — 预检无从自证, fail-closed 拒写 —— 停在 Step 2, 不写分")
+#: ⛔ 与主写点**同一份实现**(AST 逐字抽取, 零第二份): 预检要是另抄一遍选树逻辑, 两份必然
+#: 漂移 —— 生产收紧了而预检还在按旧的判, 预检就会绿着骗人。
+#: ⛔ 命名空间只取**这两个函数之前**的顶层 import: 主块顶层还有 `from decay_beta import …`,
+#: 那是 vault 脚本, 得先插 sys.path 才导得进 —— 盲目全取会让预检自己装不起来, 而那个
+#: ImportError 长得就像「harness 有毛病」。这条口径与 test_g3_2 的 `_extract_harness_tree` 同。
+_CUT = min(_n.lineno for _n in _FNS)
+_NS = {}
+for _st in _MOD.body:
+    if isinstance(_st, (ast.Import, ast.ImportFrom)) and _st.lineno < _CUT:
+        exec(compile(ast.Module(body=[_st], type_ignores=[]), "<preflight-prelude>", "exec"), _NS)
+exec(compile(ast.Module(body=_FNS, type_ignores=[]), "<preflight-harness>", "exec"), _NS)
+#: 两个函数自己的拒因已经写全了(缺库 / 树不存在 / 解析不忠 / 契约不符), 原样传出去,
+#: 不在这里包一层 —— 包一层就把「哪一步不行」压成「预检没过」。
+_REPO = _NS["_harness_tree"](VAULT)
+_NS["_harness_contract"](_REPO)
+print(f"[quiz-answer/preflight] harness={_REPO} 契约 ok — 库在、树在、契约对, 可以进 Step 3 写分")
+PYEOF
+```
+
 ## Step 3 · 写分 + 置 scored_pending_node_update（两阶段第一步）
 
 `Edit` **检验白板 md** frontmatter：
@@ -416,8 +492,64 @@ def _harness_tree(vault_dir):
     不是合法 YAML ⇒ fail-closed 拒写。第一条与第二条混成一条, 「用户把这个键清
     掉了」就会变成砖化操作。⚠️ 这三条**全部以 PyYAML 可用为前提** —— 缺库时只有
     一种结局(拒写), 不要跨分支宣称。
+    ⛔ **威胁模型 —— 本层防什么、不防什么**(CARD-HARNESS-TREE-PARSE-R2, r10 H1 收口):
+    `:440` 那个行为探针只回答「它像不像一个解析器」。它回答不了「它对**这份文件**的解析
+    忠不忠于文件内容」—— 一个 `safe_load` 恒返 `{"a": 1}` 的模块**答得对探针**, 随后对写
+    着 `harness_tree: <目标树>` 的 config 也说「没有这个键」, 于是被读成用户的沉默, 静默
+    回退父树。补上的那一层是**词法否决**: 文件明文顶格有 `harness_tree:` 而解析结果里没
+    有这个键 ⇒ 解析器不可信 ⇒ 拒写。
+      · **防得住**(⚠️ 逐条限定, 别缩写成「防得住坏解析器」): 空的同名 `yaml.py`、半装的包、
+        C 扩展与纯 python 版本错配 —— 这些连第一道探针 `safe_load("a: 1")` 都过不去;
+        以及**丢掉文档一部分**的解析器(缓冲截断 / 流被提前关闭 / 只读前 N 行 / 只读最后
+        几行), **前提是它丢掉的那部分恰好落在那份 3 行探针里** —— 探针是
+        `a: 1 / b: 2 / harness_tree: <哨兵>`, 三行的值都校验, 所以丢头丢尾都显形。
+        ⚠️ **但一个只读前 5 行(或更宽)的解析器仍能答对这份 3 行探针** —— 阈值只是被推高,
+        没有关门。根本限制写在下面实现处: 探针永远是**另一份**文件。
+        ⚠️ **这条承诺一度被写强过两次**: round-1 为修误拒引入的「值内豁免」把它打穿
+        (round-2 复核抓到); round-3 之前探针是**单行**, 丢尾巴的解析器整类都能过
+        (round-3 复核抓到)。两次都已整改, 而**两次都是「写得比实际强」先于「实际变弱」**。
+        留这些记录是因为**规则与 docstring 会被后人照抄**: 写强了, 后人就以为这一层比
+        实际更管用。
+      · **代价**(与上一条同等重要, 别只抄上一条): 一批**合法**文档会被**误拒** ——
+        凡是「正则 `^harness_tree[ \t]*:` 顶格命中、而 PyYAML 解析出的顶层没有这个键」的
+        文档都在内。round-3 复核把这个集合列全了, 比本卡先前写的「跨行标量续行顶格」宽:
+          · 值里跨行、续行顶格: `note: "open<换行>harness_tree: /a/b"`(及其嵌套变体);
+          · 真正的**嵌套**键: `nested: {<换行>harness_tree: /a<换行>}`、`[{<换行>harness_tree: /a<换行>}]`;
+          · 它其实是**另一个键**: `harness_tree:other: /a`(键名是 `harness_tree:other`)、
+            `harness_tree:/a`(整串是键名, 没有值);
+          · `!!binary` 之类解析成非 `str` 标量的值里含那串字。
+        方向是安全的(可见的拒绝、拒因指明行号、改一下写法即可), 但它是**真代价**,
+        不是「保守拒无代价」—— 这句话在本卡历史上被证伪过一次, 别再写回去。
+      · **防不住**(明写, 别在别处宣称更强): 一个**敌意**的同名模块, 探针答对、且对真实
+        config 返回一棵**存在的别树**。词法这一层看得见「有人写过这个键」, 看不见「这个
+        键的值应该是什么」—— 要看见就得自己解析, 那就是逐行降级解析回潮, 那条路被四轮
+        同族缺陷打回过。这种形态与「在 `sys.path` 上放一个假 `validate_learning_events`」
+        同层: 能往解释器里塞模块的人本来就能做更多事。它由 `_harness_contract` 把面缩小
+        (选中的树得是本写点认识的那一套), 彻底收口要靠**树侧自报契约版本**(零写者文件,
+        已登记移交)。
+      · ⛔ **不采用「解析出的值必须逐字出现在原文」这类忠实性判据**: 转义引号、隐式类型
+        (日期/数字)、续行折叠之后, 合法文档的解析值本来就**不是**原文的子串 —— 那种判据
+        会把一批写对了的 config 打红。词法只做否决, 不做比对。
+      · ⚠️ **误拒面: 探测过一轮、漏了, 复核方补上了**(如实留档, 这条教训比结论值钱)。
+        本卡第一版在这里写过「探测 7 个候选形态, 零个落进误拒面」并据此说结构上不存在。
+        **那个结论是错的** —— 复核方当轮就给出了第 8 个: `note: "open<换行>harness_tree: /a/b"`。
+        值是一个**跨行的流式标量**, 它的续行可以顶格, 于是正则在第 2 行命中, 而 PyYAML 把
+        整段读成 `note` 的值, 解析完全正确。我那 7 个形态全都在问「顶层结构会不会冲突」,
+        **一个都没问「这行字会不会是别人的值」** —— 又是「缺的是一个维度, 不是一格」。
+        当时加了豁免去修它, 而那个豁免在 round-2 复核里被证明**打穿了本层**, 现已整段去掉
+        —— 这个误拒面因此成为本层**已知且接受的代价**(见下面实现处的三次尝试记录)。
+        教训: **「探测范围内的阴性」写成结论就会被当成证明**,
+        它顶多是「我没找到」, 而「我没找到」与「不存在」之间隔着别人的一次尝试。
+      · ⚠️ **词法这一层依赖书写形式, 所以它只是纵深, 不是主力**: `"harness_tree": v` 与
+        `{harness_tree: v}` 这两种本函数支持的合法写法, 行首都不是 `harness_tree`, 正则一条
+        都不命中。真正与书写形式无关的那道判据是上面的**键级探针**。
     """
     _cfg_p = os.path.join(vault_dir, ".canvas-config.yaml")
+    #: 本函数每一条拒因都带上这一句(CARD-HARNESS-TREE-PARSE-R2, 用户口径): 拒写发生在
+    #: Step 4 主写点, 而 Step 3 可能**已经写过分**了。不带这句时用户看到的是一块「记了分
+    #: 却没更新节点」的白板加一段看不懂的报错, 会以为分数也丢了 —— 分数没丢, 且本写点
+    #: **不回滚**它(回滚 Step 3 分数需用户另裁, 本卡不预设; 拒写态零写入)。
+    _HALFSTATE = "若检验白板已处于 scored_pending_node_update: 分数保留、不回滚; 装好 PyYAML / 修好 config 后重跑 /quiz-answer 从 Step 0 续写。"
     #: ⛔ **拿 PyYAML 与读 config 必须分成两个 try**(Codex round-7 HIGH, 已独立复现):
     #: 合在一个 try 里时, **导入过程自己抛的 OSError**(yaml 包源码/依赖不可读、权限错等)
     #: 会被下面那条 `except OSError` 当成「没有 config 文件」⇒ 静默回退父目录 ⇒ 绕过
@@ -442,6 +574,29 @@ def _harness_tree(vault_dir):
             raise ImportError(f"yaml.safe_load 在最简输入上就抛了 ({type(_pe).__name__}: {_pe}); 来自 {getattr(yaml, '__file__', '未知位置')}")
         if not (isinstance(_probe, dict) and _probe.get("a") == 1):
             raise ImportError(f"yaml.safe_load 对 'a: 1' 给出的是 {_probe!r} 而不是 {{'a': 1}} —— 它不是一个能用的 YAML 解析器 (来自 {getattr(yaml, '__file__', '未知位置')})")
+        #: ⛔ **键级探针**(CARD-HARNESS-TREE-PARSE-R2 round-1 整改, 两处未被拦下的输入):
+        #: 上面那条只问「它像不像解析器」, 下面这条问**本函数真正关心的那件事** ——
+        #: 「给它一份明确写着 harness_tree 的文档, 它给不给得出这个键」。
+        #: ⛔ 为什么非要单独一条: 收口的第一版只有下面的词法否决, 而词法问的是「文件里有没有
+        #: **顶格裸键**」—— 那依赖用户的**书写形式**。YAML 至少还有两种合法写法本函数是支持的:
+        #:   · `"harness_tree": /a/b`(带引号的键, 见 `..._noncanonical_key_form_is_honored`)
+        #:   · `{harness_tree: /a/b}`(整份 flow mapping, 见 `..._refuses_whole_flow_document`)
+        #: 两者行首都不是 `harness_tree`, 正则一条都不命中 ⇒ 恒返 `{"a": 1}` 的假模块在这两种
+        #: 写法下**照样静默回退父树**(2026-09-18 实测复现)。本探针**完全不看用户的文件**,
+        #: 所以它对任何合法写法都成立、零误拒, 且不挑书写形式。
+        #: ⛔ 探针文档是**多行的, 而且那个键在最后一行**(round-3 复核 HIGH, 已实测):
+        #: 原先是单行 `harness_tree: <哨兵>` —— 于是一整类**丢文件尾巴**的坏解析器
+        #: (缓冲截断 / 流被提前关闭 / 只读前 N 行)照样答得对, 因为单行文档没有尾巴可丢。
+        #: 它们过了这一层, 又因为词法否决只认**顶格裸键**(`"harness_tree": v` 与
+        #: `{harness_tree: v}` 行首都不是它), 于是两层一起落空 ⇒ 静默回退父树。
+        #: ⚠️ **如实**: 这只是把阈值从「1 行」推到「探针的行数」, **不是关门** ——
+        #: 一个只读前 5 行的解析器仍能答对这份 3 行探针。根本限制在于: 探针永远是**另一份**
+        #: 文件, 它测得到「这个解析器的一般能力」, 测不到「它对**用户那份 config** 忠不忠实」。
+        #: 要测后者就得自己解析用户的文件, 那就是逐行降级解析回潮(四轮同族缺陷打回过)。
+        _KPROBE_DOC = "a: 1\nb: 2\nharness_tree: __quiz_answer_key_probe__\n"
+        _kprobe = yaml.safe_load(_KPROBE_DOC)
+        if not (isinstance(_kprobe, dict) and _kprobe.get("harness_tree") == "__quiz_answer_key_probe__" and _kprobe.get("a") == 1 and _kprobe.get("b") == 2):
+            raise ImportError(f"yaml.safe_load 对一份三行、末行写着 harness_tree 的最简文档给出的是 {_kprobe!r} —— 它读不出本写点唯一关心的那个键(或者读丢了文档的尾巴), 选哪棵树不可证 (来自 {getattr(yaml, '__file__', '未知位置')})")
     except Exception as _ie:
         #: ⛔ 报错里必须带上**这个进程自己的解释器路径**与一条绑定它的安装命令
         #: (Codex round-6 LOW): 只说「请装 PyYAML」时, 用户照抄 `pip install pyyaml`
@@ -454,7 +609,7 @@ def _harness_tree(vault_dir):
         import shlex
 
         _exe_q = shlex.quote(sys.executable)
-        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree 指向哪棵树不可证, fail-closed 拒写 — 逐行扫描猜不出 YAML 的换行与语法上下文, 猜错的代价是把学习事件静静地绑到另一棵 harness 树上, 故本写点在拿不到 PyYAML 时一律不写。拿不到的原因: {type(_ie).__name__}: {_ie}。跑本写点的解释器是 {sys.executable} ; 请照抄这一条装(它绑定的正是上面那个解释器, 不要换成裸 pip): {_exe_q} -m pip install pyyaml")
+        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree 指向哪棵树不可证, fail-closed 拒写 — 逐行扫描猜不出 YAML 的换行与语法上下文, 猜错的代价是把学习事件静静地绑到另一棵 harness 树上, 故本写点在拿不到 PyYAML 时一律不写。拿不到的原因: {type(_ie).__name__}: {_ie}。跑本写点的解释器是 {sys.executable} ; 请照抄这一条装(它绑定的正是上面那个解释器, 不要换成裸 pip): {_exe_q} -m pip install pyyaml。{_HALFSTATE}")
     #: ⛔ **「打不开」与「打开了但读/解析出错」必须分成两个作用域**(Codex round-9 HIGH,
     #: 已独立复现)。原先两者共用一个 `except OSError` ⇒ 解析途中的 IO 错(读流时 EIO、
     #: safe_load 自己抛的 OSError)被当成「压根没有 config」⇒ 静默回退父目录, 而 config
@@ -463,21 +618,67 @@ def _harness_tree(vault_dir):
     #: 一个 except, 于是一个异常被当成了另一个异常的意思。修一处不等于这类错没了 ——
     #: 往后在本函数里新开 try 时, 先问「这个 except 会不会同时接住两种不同含义的失败」。
     _tree = ""
+    _raw = ""
     try:
         _cf = open(_cfg_p, encoding="utf-8")
     except OSError:
         _cf = None  # 压根没有 .canvas-config.yaml ⇒ 没写这个键 ⇒ 缺省回退
     if _cf is not None:
         try:
+            #: ⛔ **先读原文, 再解析这份原文**(CARD-HARNESS-TREE-PARSE-R2, r10 H1 收口):
+            #: 原先直接把**文件对象**递给 safe_load, 于是函数手里从头到尾没有文件明文,
+            #: 也就无从发现「解析器说没有这个键, 而文件里明明写着」。读流自身的 OSError
+            #: 仍落在同一个 try 里 ⇒ 仍然 fail-closed, round-9 那条分界一个字没动。
             with _cf:
-                _doc = yaml.safe_load(_cf)
-            #: `_doc` 非 dict (空文件 / 纯标量 / 列表)、键缺失、值为 null —— 三者一律
-            #: 视同「没写这个键」, 与「值是空串」同口径回退, 不是 fail-closed。
-            if isinstance(_doc, dict) and _doc.get("harness_tree") is not None:
-                _tree = str(_doc["harness_tree"])
+                _raw = _cf.read()
+            _doc = yaml.safe_load(_raw)
         except Exception as _ye:
             #: 这里**不再**豁免 OSError: 文件已经打开了, 之后任何失败都不是「没有 config」。
-            raise SystemExit(f"[quiz-answer] .canvas-config.yaml 打开后读取/解析失败 ({type(_ye).__name__}: {_ye}) — harness_tree 指向哪棵树不可证, fail-closed 拒写 — 请人工修复 {_cfg_p}")
+            raise SystemExit(f"[quiz-answer] .canvas-config.yaml 打开后读取/解析失败 ({type(_ye).__name__}: {_ye}) — harness_tree 指向哪棵树不可证, fail-closed 拒写 — 请人工修复 {_cfg_p}。{_HALFSTATE}")
+        #: ⛔ **词法否决: 只否决, 绝不采用**(CARD-HARNESS-TREE-PARSE-R2, r10 H1)。
+        #: `:440` 那个行为探针只证得到「它像个解析器」—— 证不到「它对这份文件的解析忠于
+        #: 文件内容」。一个 `safe_load` 恒返 `{"a": 1}` 的假模块**答得对探针**, 随后对
+        #: 写着 `harness_tree: <目标树>` 的 config 也返回 `{"a": 1}`, 于是下面那条「无键
+        #: ⇒ 视同没写」把它读成用户的沉默, 静默回退父树 —— config 明明指着另一棵。
+        #: 缺的维度不是「像不像解析器」, 是「解析结果忠不忠于文件」。这里补上: 文件明文
+        #: 里有这个键、解析结果却没有 ⇒ 解析器不可信 ⇒ 拒写。
+        #: ⛔ **只用来否决, 绝不拿 `_lex` 匹配到的值去当树**: 那是逐行降级解析回潮, 那条
+        #: 路被四轮同族缺陷打回过(见上面 docstring)。词法这一层不知道自己看的这一行处在
+        #: 什么语法上下文里 —— 它只够说「有人写过这个键」, 不够说「这个键的值是什么」。
+        #: ⛔ 键**在**、值是 null / 空串 ⇒ 不否决, 照旧回退(「用户把这个键清掉了」不是
+        #: 砖化操作); 注释掉的 `# harness_tree:` 不顶格 ⇒ 正则不命中, 也照旧回退。
+        _lex = re.search(r"^harness_tree[ \t]*:", _raw, re.M)
+        #: ⛔⛔ **这里没有「豁免」, 而且不能有 —— 三次尝试后的结论, 留档给后人**
+        #: (round-1 引入、round-2 复核打回、本轮去掉; 每一步都有实测):
+        #:   v1 豁免只看顶层 `values()`          → 嵌套一层的值仍被误拒;
+        #:   v2 改成遍历整棵结构 + 环防护         → 复核抓到: 它是**整份文档一个布尔**,
+        #:      只要已解析结果里**任意一个**字符串含那串字, 否决就对文件里**每一处**
+        #:      (含真正的顶层 `harness_tree` 键)一起失效。触发**不需要敌意模块**:
+        #:      一个**截断式解析器**(只读前 N 行 = 缓冲 / 流被提前关闭那一类事故; 两道探针
+        #:      都是单行文档, 所以它照样答对、活得过键级探针)配一份**普通的单行自文档
+        #:      config**(`note: "改这里的 harness_tree: 就能换树"`)就够 —— 实测静默回退父树;
+        #:   v3 改成按「处数」比(顶格 N 处 vs 值内 M 次) → 实测**修不了**: PyYAML 把双引号
+        #:      跨行标量的换行**折叠成空格**, 于是误拒形态(顶格 1 处 / 值内子串 1 次)与
+        #:      缺陷形态(顶格 1 处 / 值内子串 1 次)**完全同构**, 计数区分不了两者。
+        #: ⛔ **根本原因**: 豁免要拿**解析器的输出**去决定要不要相信解析器 —— 而解析器
+        #: 正是这一层唯一不可信的那一方。任何依赖不可信方输出的豁免, 说谎的那一方都能
+        #: 利用(换成 `yaml.compose()` 的位置跨度也一样: 它可以谎报跨度覆盖全文)。
+        #: ⚠️ **代价如实**: 一份值里跨行、续行恰好顶格写着 `harness_tree:` 的**合法**文档
+        #: 会被误拒(实测形态: `note: "open<换行>harness_tree: /a/b"`, 以及它的嵌套变体)。
+        #: 接受这个代价, 因为方向不同: 误拒是**可见的拒绝**, 拒因会指出是第几行、用户改一下
+        #: 写法就好; 而豁免带来的是**静默绑错树**, 用户无从察觉。本函数一以贯之的取向。
+        if _lex and (not isinstance(_doc, dict) or "harness_tree" not in _doc):
+            raise SystemExit(f"[quiz-answer] .canvas-config.yaml 解析结果与文件内容不符 (文件第 {_raw[: _lex.start()].count(chr(10)) + 1} 行明文写着 harness_tree 键, 解析器却没有给出它; 它给出的是 {type(_doc).__name__}) — 解析器不可信, harness_tree 指向哪棵树不可证, fail-closed 拒写 — 请核对跑本写点的解释器 ({sys.executable}) 里的 yaml 模块 (来自 {getattr(yaml, '__file__', '未知位置')})。{_HALFSTATE}")
+        #: `_doc` 非 dict (空文件 / 纯标量 / 列表)、键缺失、值为 null —— 三者一律
+        #: 视同「没写这个键」, 与「值是空串」同口径回退, 不是 fail-closed。
+        #: ⚠️ **别把这条读成「走到这里时文件里一定没写这个键」**(round-4 复核 LOW, 原文
+        #: 就是这么写的, 不成立): 上面那条否决只认**顶格裸键**, 所以
+        #: `"harness_tree": v`(带引号的键)与 `{harness_tree: v}`(flow mapping)这两种
+        #: **本函数支持的合法写法**在词法层不命中 —— 它们若被解析器谎报成「无键」,
+        #: 会径直走到这一行并回退。挡住那一类的是上面的**键级探针**, 不是这一条。
+        #: 这一条如实的说法是: 「解析器说没有这个键, 而词法也没在顶格看到它」⇒ 回退。
+        if isinstance(_doc, dict) and _doc.get("harness_tree") is not None:
+            _tree = str(_doc["harness_tree"])
     if not _tree:
         return os.path.dirname(vault_dir)
     _given = os.path.expanduser(_tree)
@@ -497,8 +698,109 @@ def _harness_tree(vault_dir):
         #: 拒因先报**配置里写的那条路径**(已展开 `~`、已补全相对路径), 解析结果不
         #: 同时再附上 —— 只报解析后的路径, 用户认不出自己写错的是哪一行。
         _also = "" if (not _real or _real == _given) else f" [逐段解析 symlink 后: {_real}]"
-        raise SystemExit(f"[quiz-answer] harness_tree 指向不存在的树 ({_given}){_also} — G3-2 依赖不可达, fail-closed 拒写 — 请修正 .canvas-config.yaml 或删掉该键回退到 vault 父目录")
+        raise SystemExit(f"[quiz-answer] harness_tree 指向不存在的树 ({_given}){_also} — G3-2 依赖不可达, fail-closed 拒写 — 请修正 .canvas-config.yaml 或删掉该键回退到 vault 父目录。{_HALFSTATE}")
     return _real
+
+
+def _harness_contract(repo_dir):
+    """从选中的那棵树导入写点要用的 7 个名字, **并证明它就是本写点认识的那一套**。
+
+    ⛔ 本函数是 CARD-HARNESS-TREE-PARSE-R2 补上的一层。在它之前, 写点对 `harness_tree`
+    选中的树只有一条判据 —— 「那 7 个名字能不能从它的 validator 里裸 import 进来」。
+    导得进就按它的语义写账本, 别的一概不问。于是:
+      · 本仓 `b85a168a` 那棵旧树(`_vault_id_of` 是另一套实现)被静默采用, 账本照写 ——
+        这是 T7-A 已经**实测到的**反例, 不是假想;
+      · 任意旧版 / 异版 / 第三方分发的 harness 都享受同样的待遇。
+    `harness_tree` 是**部署侧可写的运行期自由变量**, 选错树的代价是「分数记到别的本子
+    上」, 而用户看到的是一次成功的写入 —— 无从察觉。所以这里把「导得进」升级成一份
+    可检验的契约。
+
+    四层, 逐层回答一个不同的问题:
+      ① **影子门** —— 导进来的真是**这棵树里的**那一份吗? (`sys.modules` 先到先得:
+         任何早于本写点被 import 的同名模块都会让上面那次 `sys.path.insert` 完全失效,
+         而 7 个名字照样导得到。)
+      ② **版本** —— 它是 v1 语义吗? (写点按 v1 消费: 账本行 `event_version != 1` 直接
+         拒写。树侧换了语义而写点不知道 = 两边对同一个字段的理解分叉。)
+      ③ **形状** —— 7 个名字都在, 且 5 个可调用 / 2 个是编译好的正则吗?
+      ④ **纯函数行为探针** —— 它们在**已知输入**上的答案对吗? (名字对、类型对, 不代表
+         语义对。这四个探针零 IO、零写, 只问纯函数。)
+
+    ⚠️ **本层挡不住什么, 如实写在这里**: 一棵「同名、同形状、纯函数行为也一样, 只有
+    别处语义不同」的树通得过 —— `b85a168a` 恰好就是这样的树(它也有 `EVENT_VERSION = 1`
+    和全部 7 个名字)。要挡住它得让**树侧自报契约版本**, 那是 `validate_learning_events.py`
+    的改动, 不在本写点职责内(已登记移交)。本层把「任何导得进的东西都算数」缩成
+    「形状与纯函数语义都对得上的东西才算数」, 是缩面, 不是关门。
+
+    返回 7 个名字组成的元组, 顺序与 `_HARNESS_NAMES` 逐一对应。
+    """
+    _HALFSTATE = "若检验白板已处于 scored_pending_node_update: 分数保留、不回滚; 装好 PyYAML / 修好 config 后重跑 /quiz-answer 从 Step 0 续写。"
+    #: ⛔ 名单在这里和调用点的解包各一份 —— 数量对不上时解包当场 `ValueError`(响亮失败),
+    #: 不会静默少绑一个名字。两份都在同一屏内, 改一处忘另一处走不出这个文件。
+    _HARNESS_NAMES = ("classify_card_state", "_vault_id_of", "_WHOLE_SECOND_RE", "_looks_like_review_ext", "validate_record_full", "_golden_manifest", "_TS_RE")
+    _scripts = os.path.join(repo_dir, "backend", "scripts")
+    sys.path.insert(0, _scripts)
+    try:
+        import validate_learning_events as _vle
+    except Exception as _e:
+        raise SystemExit(f"[quiz-answer] G3-2 依赖不可达 (validate_learning_events/fsrs_bridge import 失败), fail-closed 拒写: {_e}")
+
+    def _refuse(_item, _actual):
+        raise SystemExit(f"[quiz-answer] harness 树契约不符 ({_item}: {_actual}) — 选中的树 {repo_dir} 不是本写点认识的 validate_learning_events, fail-closed 拒写。{_HALFSTATE}")
+
+    #: ① 影子门。⛔ 比 `abspath` 而**不是** `realpath`: 一键部署形态下 harness 树里的
+    #: validator 完全可以是一条指向别处的 symlink(测试夹具就是这么搭的), 那是合法布局。
+    #: 要判的是「Python 从**哪条 sys.path 条目**把它取进来的」, 不是「这个文件物理上躺
+    #: 在哪」—— 后者会把一棵合法的树判成影子。
+    _from = os.path.dirname(os.path.abspath(getattr(_vle, "__file__", "") or ""))
+    if _from != os.path.abspath(_scripts):
+        raise SystemExit(f"[quiz-answer] validate_learning_events 来自 {_from} 而不是选中的树 {repo_dir} — sys.modules 里先坐着一个同名模块(先到先得), 本写点这次 sys.path.insert 没有生效, 导进来的不是选中的树里那一份, harness 语义不可证, fail-closed 拒写。{_HALFSTATE}")
+
+    #: ② 版本。⛔ `bool` 要单独排除: `True == 1` 为真, 不排的话 `EVENT_VERSION = True`
+    #: 这种(配置注入 / 占位符没填)会被当成 v1 放行。
+    _ver = getattr(_vle, "EVENT_VERSION", None)
+    if isinstance(_ver, bool) or _ver != 1:
+        _refuse("EVENT_VERSION", f"{_ver!r} 非 1 — 本写点按 v1 语义消费(账本行 event_version != 1 直接拒写)")
+
+    #: ③ 形状。
+    for _n in _HARNESS_NAMES:
+        if not hasattr(_vle, _n):
+            _refuse("缺名字", f"{_n} 在这棵树的 validate_learning_events 里不存在")
+    for _n in ("classify_card_state", "_vault_id_of", "_looks_like_review_ext", "validate_record_full", "_golden_manifest"):
+        if not callable(getattr(_vle, _n)):
+            _refuse("不可调用", f"{_n} 是 {type(getattr(_vle, _n)).__name__}, 不是函数")
+    for _n in ("_TS_RE", "_WHOLE_SECOND_RE"):
+        if not isinstance(getattr(_vle, _n), re.Pattern):
+            _refuse("不是编译正则", f"{_n} 是 {type(getattr(_vle, _n)).__name__}")
+
+    #: ④ 纯函数行为探针(零 IO、零写)。
+    #: ⚠️ **覆盖如实**(round-2 复核 MEDIUM; 这里原本写「每条都两向」, 过强):
+    #:   · 两个正则(`_TS_RE` / `_WHOLE_SECOND_RE`)是**两向**的 —— 该认的认、该拒的拒;
+    #:   · `classify_card_state` / `validate_record_full` / `_looks_like_review_ext`
+    #:     各只测**一向**, 所以一个在别处语义不同、但这几点上恰好同答的占位实现能通过
+    #:     (复核方举的例子正是本卡测试自己的 `_VALIDATOR_STUB_OK`)。
+    #: 这一层是**缩面**不是关门: 把「任何导得进的东西都算数」缩成「形状与这几点语义对得上
+    #: 的才算数」。彻底收口要靠树侧自报契约版本(零写者文件, 已登记移交)。⛔ 不探 `_vault_id_of` / `_golden_manifest`: 它们要读
+    #: 文件, 而预检块必须是纯读零写的前置检查。
+    if not _vle._TS_RE.fullmatch("2026-08-01T10:00:00Z"):
+        _refuse("_TS_RE", "不认 '2026-08-01T10:00:00Z' 这样的事件时间戳")
+    if _vle._TS_RE.fullmatch("2026-08-01"):
+        _refuse("_TS_RE", "把光秃秃的 '2026-08-01' 也当成合法时间戳")
+    if not _vle._WHOLE_SECOND_RE.fullmatch("2026-08-01T10:00:00Z"):
+        _refuse("_WHOLE_SECOND_RE", "不认整秒时间戳 '2026-08-01T10:00:00Z'")
+    if _vle._WHOLE_SECOND_RE.fullmatch("2026-08-01T10:00Z"):
+        _refuse("_WHOLE_SECOND_RE", "把缺秒的 '2026-08-01T10:00Z' 也当成整秒")
+    _st = _vle.classify_card_state({})
+    if not (isinstance(_st, tuple) and len(_st) == 2 and _st[0] == "new"):
+        _refuse("classify_card_state", f"对空 frontmatter 给出 {_st!r}, 期望 ('new', <理由>) — 三态判别语义不同")
+    _vr = _vle.validate_record_full("x")
+    if not (isinstance(_vr, tuple) and len(_vr) == 2 and isinstance(_vr[0], list) and _vr[0]):
+        _refuse("validate_record_full", f"对一个非 JSON object 给出 {_vr!r}, 期望 (<非空错误列表>, <warnings>) — 它不会拒绝坏记录")
+    if _vle._looks_like_review_ext({}) is not False:
+        _refuse("_looks_like_review_ext", f"对空 dict 给出 {_vle._looks_like_review_ext({})!r}, 期望 False")
+
+    return tuple(getattr(_vle, _n) for _n in _HARNESS_NAMES)
+
+
 VAULT = os.path.dirname(os.path.dirname(os.path.abspath(NODE)))
 REPO = _harness_tree(VAULT)
 EV = os.path.join(VAULT, "learning_events.jsonl")
@@ -508,10 +810,14 @@ EV = os.path.join(VAULT, "learning_events.jsonl")
 sys.path.insert(0, os.path.join(VAULT, ".claude", "scripts"))
 try:
     from fsrs_bridge import rating_from_grade, fields_from_frontmatter, cas_token, cas_conflict
-    sys.path.insert(0, os.path.join(REPO, "backend", "scripts"))
-    from validate_learning_events import classify_card_state, _vault_id_of, _WHOLE_SECOND_RE, _looks_like_review_ext, validate_record_full, _golden_manifest, _TS_RE
 except Exception as _e:
     raise SystemExit(f"[quiz-answer] G3-2 依赖不可达 (validate_learning_events/fsrs_bridge import 失败), fail-closed 拒写: {_e}")
+#: ⛔ validator 那 7 个名字走 `_harness_contract` 而不是裸 import(CARD-HARNESS-TREE-PARSE-R2):
+#: 裸 import 只判「导得进」, 于是任意旧版 / 异版 harness 树都会被静默采用并按它的语义
+#: 写账本 —— T7-A 已实测到 `b85a168a` 那棵旧树就是这样被用上的。⛔ 解包成 7 个名字而
+#: 不是 `globals()[…] =` 反射写: 反射写既躲开了 lint 的写入面统计, 也让「这里到底绑了
+#: 哪些名字」只有运行时才知道。数量与函数里的 `_HARNESS_NAMES` 对不上时当场 ValueError。
+classify_card_state, _vault_id_of, _WHOLE_SECOND_RE, _looks_like_review_ext, validate_record_full, _golden_manifest, _TS_RE = _harness_contract(REPO)
 
 #: CARD-G3-3 (a) per-node CAS 令牌 —— 由**上面已经读进来的那份字节** `s` 构造,
 #: 不重读磁盘 (重读会在「令牌」与「真正拿去算的内容」之间再开一个可插队的窗口)。
````

# ② 作者自述 —— 请独立核对（不要采信，逐条验证）

1. **词法否决只否决不采用**：`^harness_tree[ \t]*:` 命中而解析结果没有该键 ⇒ 拒写；它没有拿匹配值当树用，**不是**降级解析回潮（`:650` 起注文）。
2. **`parse_returns_junk` 改真 PyYAML 后语义与既有 16 门同口径**：真解析器 + 文件本身是列表 ⇒ 回退父树（`:7970` / `:7989`）。
3. **契约门影子判据用 `abspath` 不用 `realpath`**：一键部署的 symlink 树是合法布局，比 `realpath` 会把合法树判成影子（`:754` 注文）。
4. **预检块与主块是同一份实现**：主块 AST 抽取，零第二份；预检块不含 `P = "/tmp/quiz-answer-payload.json"` 字面量（否则会命中 `_MAIN_BLOCKS` 过滤器）。
5. **既有半态不回滚是默认口径**，非遗漏：拒写态零写入；Step 3 已写的分数保留（`:552` / `:736` 的 `_HALFSTATE`）。

# ③ 请按重要性排序回答

⓪ 词法否决 `^harness_tree[ \t]*:` 是否有**误拒面**（整份文档为块标量 / 注释块 / 多文档）或**漏否决面**（键在但值被谎报 —— 已明写为威胁模型外，请核 docstring 是否如实）。
① `_harness_contract` 的探针能否被一棵「同名同形状但语义不同」的树通过（`b85a168a` 已知通过 —— 作者已登记为移交项；请找**别的**已知树或形态）。
② 预检块从 SKILL.md 自抽取：SKILL.md 路径由 `VAULT` 派生，vault 不在标准布局时预检失败的形态是「拒写」还是「跳过」（必须拒写）。
③ Step 2.9 与 Step 0 续跑态（`:166` 跳过 Step 1-3）的交互：续跑是否也应先预检。
④ `_mode="whole"` 新参数的有库控制半是否真钉住了 PyYAML 结局（前提断言是否会被 `pytest.skip` 吞成假绿）。
⑤ 负控各段（卡文 (k) 要求 ≥2；最终 13 段）是否各只拆一层、红在指定断言。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级；每条给 `file:line` + 一句话问题 + 一句话说明如何让它显形（用「**负控输入**」「**对照输入**」「**未被拦下的输入**」「**门未覆盖的路径**」这四种说法）。某一级没有条目请明确写「无」。

**若整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`**（这行会被用作轮次闭合依据）。

# ⑤ 边界

只读；不连任何库（7691 / 7687 不适用）；不评 `fsrs_bridge` / `validate_learning_events.py` 树侧改法、不评 P6-A 的 start-exam-board 改动、不评 G8-3；除上方点名的上下文文件外，`_bmad-output/` 下其余内容不在审查面内。

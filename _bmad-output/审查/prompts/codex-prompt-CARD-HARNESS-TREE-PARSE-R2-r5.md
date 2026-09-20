你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。

# ① 背景与最小读取面

本卡 `CARD-HARNESS-TREE-PARSE-R2`（BATCH-2026-09-18-第十五批）。**这是第 5 轮，也是本卡的
轮次上限**；若这一轮仍有 HIGH，按协议停下交主 session 人审。

被审改动面：`git --no-pager diff --no-color a05732c9 HEAD -- . ':(exclude)_bmad-output'`（4 个文件）

行号为改后现值（已 `grep -n` 实测）：

1. `canvas-vault/.claude/skills/quiz-answer/SKILL.md`
   - `:189-264` Step 2.9 全段（预检块 `:206-261`；`:211` `sys.dont_write_bytecode = True`，
     排在 `import ast, os, re` 之前）
   - `:446-702` `_harness_tree`（`:596` `_KPROBE_DOC` 三行探针；`:650` 词法否决，**无豁免**）
   - `:705-801` `_harness_contract`
2. `backend/tests/regression/test_g3_2_review_ledger.py`（探针文档从 CODE 抽取；60 条
   `_HEADED_LINES` 本卡逐字未动；13 条 `_WHOLE_DOCS`；两道门）
3. `backend/tests/skills/test_harness_tree_parse_r2.py` —— 新文件全文 **952 行，34 nodeid**
4. `backend/tests/skills/skill_portability_lint.py` —— 基线数值四处 + 交接注释

# ② 第 4 轮之后的整改 —— **不要重复报告，改为核对整改本身**

| 你上轮给的 | 处置 |
|---|---|
| **L3** 两处 docstring 仍承诺「任意 N 行截断 / 任何谎报无键」「回退只覆盖用户确实没写」，与新增限制矛盾 | **已改**：`:502` 起改成逐条限定（丢头丢尾都显形的**前提**是丢掉的部分恰好落在那份 3 行探针里；只读前 5 行或更宽的仍能答对）；`:674` 起改成「解析器说没有这个键，而词法也没在顶格看到它 ⇒ 回退」，并点明引号键 / flow mapping 在词法层不命中、挡它们的是键级探针 |
| **L1** 删掉探针对 `a`/`b` 的两项校验后 15 格仍全过 | **已补门** `..._tail_only_parser_is_refused`：只解析**最后一行**的解析器（丢头），对三行探针只读到 `harness_tree: <哨兵>` ⇒ 那个键的校验照样过，唯一拦得住它的是 a/b。前提自证四条 |
| **L2** 删掉形状层 `isinstance(..., re.Pattern)` 后六格契约负控仍全过 | **已补门** `..._harness_contract_refuses_a_non_pattern_wrapper`：把 `fullmatch` 委托给真正则的包装对象 |
| **M1** Python 启动阶段（未缓存的 `sitecustomize.py`）仍可能写字节码 | **登记不修**：那发生在本块第一行执行**之前**，块内无法控制 |
| **M2** 本机 zsh 下 heredoc 需要临时文件 | **登记不修**：heredoc 是这个写点三个块一贯的调用形态，改它会动 `_MAIN_BLOCKS` 的提取口径（`test_g3_2` 的夹具基石） |

**负控现已九段**（每段只拆一层、EXIT trap 还原、跑前/还原后 shasum 逐字同）：
① 词法否决 / ② 版本判据 / ③ Step 2.9 位置 / ④ 键级探针 / ⑤ 豁免回潮 /
⑥ 预检禁字节码 / ⑦ 探针改回单行 / ⑧ 探针的 a/b 校验 / ⑨ 形状层 isinstance。

**本卡明写为「已知且接受」的，请核边界而不是重报**：
1. 多行探针只是把阈值推高，**不是关门**（根本限制：探针永远是另一份文件）。
2. 词法否决**没有豁免**，代价是一批合法文档被误拒（集合见 `:509` 起）。
3. 「对两道探针都老实、只对用户这份 config 说谎」的模块 + 引号键 / flow 写法 ⇒ 两层都拦不住。

# ③ 请按重要性回答

⓪ 这一轮改的两处 docstring（`:502` 起、`:674` 起）现在**如实**吗？有没有仍然比实际强、
   或者反过来把实际有的能力说没了？
① 新补的两格门（`..._tail_only_parser_is_refused`、`..._refuses_a_non_pattern_wrapper`）
   真的锁住了它们声称的那条判据吗？有没有**即使删掉对应生产代码也照样绿**的可能？
② 九段负控合起来，还有哪些**生产判据没有专属负控**（删掉它没有任何一格会红）？
③ 34 个 nodeid 里，有没有哪一格的断言锚在了比它声称的更弱的东西上？
④ **回归面**：三条分界、缺库不变量、打不开 vs 打开后失败的分野，是否都还成立？
⑤ 有没有**本卡引入、前四轮都没覆盖到**的问题？

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么
让它显形（用「**负控输入**」「**对照输入**」「**未被拦下的输入**」「**门未覆盖的路径**」
这四种说法）。某一级没有条目请明确写「无」。

**如果整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`** —— 这一行会被
用作轮次闭合的依据。

# ⑤ 边界

只读；不评 `validate_learning_events.py` 树侧改法、不评 `fsrs_bridge.py` / `decay_beta.py`、
不评别卡改动；`_bmad-output/` 下的验收单与存档不在审查面内。

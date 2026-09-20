你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。

# ① 背景与最小读取面（请只读下面点名的这些，别扩散）

本卡 `CARD-HARNESS-TREE-PARSE-R2`（BATCH-2026-09-18-第十五批）收口的是上一张卡
`CARD-HARNESS-TREE-PARSE-REDO`（T7-A）第 10 轮复核留下的一个 HIGH，并并入同族的两件缺口。

**被审的改动面**（4 个文件，其余一概不在本卡范围）：

```
git --no-pager diff --no-color a05732c9 HEAD -- . ':(exclude)_bmad-output'
```

请逐一读这些位置（行号为改后现值，已用 `grep -n` 实测）：

1. `canvas-vault/.claude/skills/quiz-answer/SKILL.md`
   - `:189-245` —— 新增的 `## Step 2.9 · harness 预检` 全段（prose + 一个新的 PYEOF fence）
   - `:428-615` —— `_harness_tree(vault_dir)` 全函数（docstring 含新增的「威胁模型」段；
     函数体 `:534-585` 一段是本卡的主要改动：先读原文再解析 + 词法否决）
   - `:616-708` —— 新函数 `_harness_contract(repo_dir)`
   - `:710` `REPO = _harness_tree(VAULT)` 与 `:725` 的 7 名字解包行
2. `backend/tests/regression/test_g3_2_review_ledger.py`
   - `:7523-7565` —— `_extract_harness_tree()` / `_ht_outcome()`（**本卡未改**，作为口径参照）
   - `:7567-7665` —— `_HEADED_LINES`（既有 60 条，本卡逐字未动，只是从 parametrize 内联列表
     提成命名常量）
   - `:7666-7690` —— 新增的 `_WHOLE_DOCS`（13 条整份文档形态 + 每条写死的真 PyYAML 结局）
   - `:7691-7760` —— `..._never_returns_a_tree` 门（新增 `_mode` / `_truth` 两个参数与控制组前提）
   - `:7955-8010` —— `..._pyyaml_available_failures_are_not_missing_config` 门（`parse_returns_junk`
     参数改真 PyYAML 真列表文档；假模块的探针分辨从按类型改为按内容）
3. `backend/tests/skills/test_harness_tree_parse_r2.py` —— **新文件全文**（18 个 nodeid）
4. `backend/tests/skills/skill_portability_lint.py` —— 只有三处：quiz-answer 的块指纹四条
   （`:2154-2186`）、不透明记号基线一行（`:2126`）、整文件 digest 一行（`:3262`），以及交接注释

**契约探针的依据**（只读，本卡零改动）：
`backend/scripts/validate_learning_events.py` 的 `:71`（`EVENT_VERSION = 1`）、`:132`（`_TS_RE`）、
`:137`（`_WHOLE_SECOND_RE`）、`:239-252`（`classify_card_state`）、`:1282-1290`
（`_looks_like_review_ext`）、`:1737-1750`（`validate_record_full`）。

**缺陷的来源**：
- 复核裁定书 `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md:190`
- 上一卡第 10 轮存档 `_bmad-output/审查/codex-review-CARD-HARNESS-TREE-PARSE-REDO-r10.md:18-31`
- 上一卡验收单 `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:872-941`（四个候选口径，用户选了「丙」）

**缺陷本身**：`_harness_tree` 在 `:440` 用一个行为探针（`yaml.safe_load("a: 1")` 是否给出
`{"a": 1}`）确认 PyYAML 可用。这个探针只回答「它像不像一个解析器」，回答不了「它对**这份
文件**的解析忠不忠于文件内容」。一个 `safe_load` 恒返 `{"a": 1}` 的假 `yaml` 模块答得对探针，
随后对写着 `harness_tree: <目标树>` 的 config 也返回 `{"a": 1}`，于是被当成「用户没写这个键」
而静默回退父树 —— 学习事件被记到另一棵 harness 树的账本上，而用户看到的是一次成功的写入。

# ② 作者自述（请独立核对，不要采信）

1. **词法否决只否决、绝不采用**：新增的 `_lex = re.search(r"^harness_tree[ \t]*:", _raw, re.M)`
   只用来判「文件明文里有没有人写过这个键」，匹配到的内容**不被当作树的值使用**。作者认为
   这与被删除的「逐行降级解析」有本质区别（后者会采用词法解析出的值）。请核这个区别在代码
   里是否真的成立。
2. **`parse_returns_junk` 门的口径更正**：原门用一个说谎的假模块制造「非 dict」，再断言
   「回退父树是对的」；作者认为那把错误结果固化成了期望，已改为**真 PyYAML + config 文件
   本身就是 `- a\n- b`**。请核改后的语义与既有 16 门是否同口径。
3. **契约门的影子判据用 `abspath` 而不是 `realpath`**：因为一键部署形态下 harness 树里的
   validator 可以合法地是一条指向别处的 symlink（测试夹具 `_real_harness` 就是这样）。
   请核这个选择是否让影子门本身失效。
4. **预检块与主写点是同一份实现**：Step 2.9 的块用 AST 从 SKILL.md 主写点逐字抽取
   `_harness_tree` / `_harness_contract`，没有第二份拷贝。请核这个抽取在什么情况下会取到
   与主写点不同的东西。
5. **既有半态白板不回滚是默认口径，不是遗漏**：用户裁定缺 PyYAML 半态白板的处置是「改顺序
   先拒后写 + 既有半态分数保留」。回滚 Step 3 分数需用户另裁，本卡不预设。

# ③ 请按重要性回答这些问题

⓪ 词法否决 `^harness_tree[ \t]*:` 有没有**误拒面**（一份 PyYAML 能成功解析、且解析结果里
   没有这个键、但文件明文顶格写着它的**合法**文档）？作者探测了 7 个候选形态（顶层块标量
   顶格内容 / `...` 之后再写 / 多文档 `---` / 顶层序列后顶格该键 / 值是未定义锚点 / 注释掉的键 /
   正常有键），零个落进这个组合，并把这个结论写进了 docstring。请核这个陈述是否如实，
   以及有没有作者没想到的形态。反方向也请核：**漏否决面**（键在、但值被谎报成另一棵存在
   的别树）已被明写为威胁模型之外 —— 请核 docstring 里那段声明与代码的实际能力是否一致，
   有没有把防不住的说成防得住。

① `_harness_contract` 的四层探针（影子 / 版本 / 形状 / 纯函数行为），能不能被一棵「同名、
   同形状、纯函数行为也一样，只有别处语义不同」的树通过？作者已登记一个已知的这样的树
   （本仓 `b85a168a` 的旧 validator，它也有 `EVENT_VERSION = 1` 和全部 7 个名字）。
   请找**别的**已知树或形态，或者指出这四层里哪一层的判据比它自称的更弱。

② 预检块从 SKILL.md 自抽取：`SKILL.md` 的路径由 `VAULT` 派生（`VAULT` 又由
   `QUIZ_ANSWER_NODE` 派生）。vault 不在标准布局时，预检的结局必须是**拒写**而不是跳过。
   请核所有派生失败的分支是否都落在拒写上，包括 `os.environ["QUIZ_ANSWER_NODE"]` 本身缺失。

③ Step 2.9 与 Step 0 续跑态（`SKILL.md:166`，`scored_pending_node_update` 时「跳过 Step 1-3」）
   的交互：续跑路径**不经过** Step 2.9。作者把这一条登记为「未证明」。请判断续跑是否也应该
   先预检，以及不预检的实际后果是什么。

④ `_mode="whole"` 那 13 条新参数的**有库控制半**：门里用真 PyYAML 先跑同一份文本，把结局
   与表里写死的 `_truth` 比对。请核这个前提断言会不会被 `pytest.skip` 之类吞成假绿，以及
   `_truth` 的四个取值（`dict_with_key` / `dict_no_key` / `not_a_dict` / `raises:<类名>`）是否
   足以区分「PyYAML 真的拒了这份文档」与「PyYAML 收下了但没有这个键」。

⑤ 负控三段（临时删掉词法否决分支 / 把版本判据从 `== 1` 放宽成 `in (1, 2)` / 把 Step 2.9 整段
   挪到 Step 3 之后）是否各只拆一层，且红点落在指定的那条断言上、而不是落在夹具或收集期。

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出：
- `file:line`
- 一句话说明这是什么问题
- 一句话说明怎么让它显形：请用「**负控输入**」「**对照输入**」「**未被拦下的输入**」
  「**门未覆盖的路径**」这四种说法来描述，不要写成攻击步骤。

如果某一级没有条目，请明确写「无」。

# ⑤ 边界

- 只读。不要修改文件，不要运行会写盘的命令，不要连接 7691 / 7687 / 7692 任何端口。
- 不要评 `backend/scripts/validate_learning_events.py` 的树侧改法（它是本批零写者文件，
  「让树自报契约版本」已登记为移交事项）。
- 不要评 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（零写者）。
- 不要评同车道上一张卡 `CARD-SEB-WRITER-SUBSTRING-TMP` 对 `start-exam-board/SKILL.md` 的改动。
- 不要评 `CARD-G8-3` / `CARD-G8-10`（本车道后续两张卡，尚未开工）。
- `_bmad-output/` 下的验收单与存档不在审查面内。

你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。

# ① 背景与最小读取面

本卡 `CARD-HARNESS-TREE-PARSE-R2`（BATCH-2026-09-18-第十五批）。**这是第 3 轮**。

被审改动面（4 个文件）：`git --no-pager diff --no-color a05732c9 HEAD -- . ':(exclude)_bmad-output'`

行号为改后现值（已 `grep -n` 实测）：

1. `canvas-vault/.claude/skills/quiz-answer/SKILL.md`
   - `:189-258` `## Step 2.9 · harness 预检` 全段（预检 PYEOF 块 `:206-255`；`:214`
     `sys.dont_write_bytecode = True`）
   - `:440-671` `_harness_tree`（`:570` 键级探针；`:623` 词法否决正则，**其后已无豁免**）
   - `:674-770` `_harness_contract`
2. `backend/tests/regression/test_g3_2_review_ledger.py` —— `:7354` `_KEY_PROBE_DOC` + 防漂移
   assert；`:7572-7670` `_HEADED_LINES`（本卡逐字未动）；`:7671-7695` `_WHOLE_DOCS`；
   `:7696-7770` / `:7969-8035` 两道门
3. `backend/tests/skills/test_harness_tree_parse_r2.py` —— 新文件全文 797 行（26 nodeid）
4. `backend/tests/skills/skill_portability_lint.py` —— 基线数值四处 + 交接注释

契约依据（只读，零改动）：`backend/scripts/validate_learning_events.py` 的
`:71`/`:132`/`:137`/`:239-252`/`:1282-1290`/`:1737-1750`。

# ② 第 2 轮之后发生了什么 —— **请不要重复报告这些，改为核对整改本身**

你上一轮给出 4 MEDIUM + 3 LOW，并在 ⓪/①(c) 里指出「旁观值也能触发豁免」。车道的处置：

| 项 | 处置 |
|---|---|
| ⓪/①(c) 的豁免问题 | **升级为 HIGH 并整改**：独立复核用一个**截断式解析器**（非敌意，只读前 N 行）+ 一份普通单行自文档 config 实测到**静默回退父树**，说明它落在威胁模型**之内**，不是你判的「已排除」。⇒ **豁免整段去掉**（`:623` 之后已无豁免） |
| M4 预检落字节码 | **已修**：`:214` `sys.dont_write_bytecode = True`；测试 `_run_preflight` 改成**显式删掉** `PYTHONDONTWRITEBYTECODE`（按真实用户环境跑），四格加 `_pycache_dirs(...) == []` 断言 |
| M3「每条探针都两向」措辞过强 | **已改**：docstring 如实写明只有两个正则是两向的，其余三个各只测一向；并写明这一层是缩面不是关门 |
| M2 影子门 `abspath` | **登记，但附实证反驳**：你注明「本轮未建立实体 symlink」。车道用三种**实体** symlink 布局（validator 是 symlink / 树目录是 symlink / `backend/scripts` 那段是 symlink）实测，影子门**全部返回 7 元组、无误判**。请复核这一反驳是否站得住，或给出实体可验的反例 |
| M1 `!!binary` ⇒ bytes 误拒 | **登记不修**：豁免已整段去掉，误拒面现已是本层**已知且接受的代价**（docstring 与门里都写明了取舍理由） |
| L1 / L2 / L3 | 登记不阻断 |

**豁免为什么不是「换个写法」能修的**（三次尝试，全部实测，写在 `:624-644` 与门的 docstring）：
v1 只看顶层 `values()` → 嵌套值仍误拒；v2 遍历整棵结构 → 就是那个 HIGH；
v3 按「处数」比 → **修不了**，因为 PyYAML 把双引号跨行标量的换行**折叠成空格**，
误拒形态（顶格 1 处 / 值内子串 1 次）与缺陷形态（同样 1/1）**完全同构**。
根本原因：豁免要拿**解析器的输出**去决定要不要相信解析器。

# ③ 请按重要性回答

⓪ **去掉豁免这个决定本身**：`:623` 现在是「顶格命中 ∧ 解析结果无该键 ⇒ 拒」，没有任何例外。
   (a) 这条规则有没有**未被拦下的输入**（谎报无键却不被拒）？
   (b) 它的**误拒面**有多大？docstring `:509-517` 与门
       `..._lexical_veto_false_refusal_cost_is_accepted` 把它写成「已知且接受的代价」——
       请核这个代价的边界写得对不对、有没有比声称的更宽。
⓪' **键级探针**（`:570`）仍是挡住引号键 / flow mapping 写法的唯一一层。有没有新的未被拦下的输入？
① **预检禁字节码**（`:214`）：这一行放在预检块自己而不是靠调用方传环境变量。
   (a) 它真的覆盖了这条路径上**所有**的落盘吗？（`ast.parse` / `exec` / `import` / 别的？）
   (b) 测试改成真实用户环境后，还有没有**门未覆盖的路径**？
② **`_harness_contract`**：措辞改如实之后，这四层的**实际**保障面是什么？有没有比新措辞
   仍然更弱的地方？
③ **测试有效性（找假绿）**：26 个 nodeid 里，有没有哪一格即使把它声称守护的那行生产代码
   删掉也照样绿？特别请核新增的三格：`..._truncating_parser_cannot_disarm_the_veto`、
   它的 `..._control_group`、以及三格 `..._false_refusal_cost_is_accepted`。
④ **回归面**：三条分界（无键 / null / 空串 ⇒ 回退）、缺库不变量、打不开 vs 打开后失败的
   分野，在去掉豁免之后是否都还成立？
⑤ 有没有**本卡引入、上面各问都没覆盖到**的问题？

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么
让它显形（用「**负控输入**」「**对照输入**」「**未被拦下的输入**」「**门未覆盖的路径**」
这四种说法，不要写成攻击步骤）。某一级没有条目请明确写「无」。

**如果整轮没有 BLOCKER 与 HIGH，请在开头写一行 `BLOCKER: 无 / HIGH: 无`** —— 这一行会被
用作轮次闭合的依据。

# ⑤ 边界

只读；不评 `validate_learning_events.py` 的树侧改法、不评 `fsrs_bridge.py` / `decay_beta.py`、
不评别卡改动；`_bmad-output/` 下的验收单与存档不在审查面内。

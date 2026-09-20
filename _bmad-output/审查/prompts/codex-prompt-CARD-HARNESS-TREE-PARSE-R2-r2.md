你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。

# ① 背景与最小读取面（只读下面点名的这些，别扩散）

本卡 `CARD-HARNESS-TREE-PARSE-R2`（BATCH-2026-09-18-第十五批）。**这是第 2 轮**：第 1 轮你
给出过三条发现，作者全部独立复现并整改，本轮审的是**整改后的最终状态**。

**被审的改动面**（4 个文件，其余一概不在本卡范围）：

```
git --no-pager diff --no-color a05732c9 HEAD -- . ':(exclude)_bmad-output'
```

行号为**改后现值**（已用 `grep -n` 实测）：

1. `canvas-vault/.claude/skills/quiz-answer/SKILL.md`
   - `:189-250` —— `## Step 2.9 · harness 预检` 全段（prose + 预检 PYEOF 块在 `:206-247`）
   - `:432-662` —— `_harness_tree(vault_dir)` 全函数。其中：
     - `:552` 键级探针 `_kprobe = yaml.safe_load("harness_tree: __quiz_answer_key_probe__")`
     - `:605` 词法否决的正则 `_lex = re.search(r"^harness_tree[ \t]*:", _raw, re.M)`
     - `:617` 起 `_in_value` 的全结构遍历（带自引用环防护）
   - `:665-755` —— `_harness_contract(repo_dir)` 全函数
   - `:759` `REPO = _harness_tree(VAULT)`、`:774` 7 名字解包行
2. `backend/tests/regression/test_g3_2_review_ledger.py`
   - `:7354` `_KEY_PROBE_DOC` 常量与它下面那条防手抄漂移的 `assert`
   - `:7528-7570` `_extract_harness_tree()` / `_ht_outcome()`（**本卡未改**，口径参照）
   - `:7572-7670` `_HEADED_LINES`（既有 60 条，**本卡逐字未动**，仅从 parametrize 内联列表
     提成命名常量；作者已用逐元素 AST dump 比对 + 验伪锚证明这一点）
   - `:7671-7695` 新增的 `_WHOLE_DOCS`（13 条整份文档形态 + 每条写死的真 PyYAML 结局）
   - `:7696-7770` `..._never_returns_a_tree` 门（新增 `_mode` / `_truth` 与控制组前提）
   - `:7969-8035` `..._pyyaml_available_failures_are_not_missing_config` 门
3. `backend/tests/skills/test_harness_tree_parse_r2.py` —— **新文件全文 710 行**（25 个 nodeid）
4. `backend/tests/skills/skill_portability_lint.py` —— 只有基线数值三处 + 交接注释

**契约探针的依据**（只读，本卡零改动）：
`backend/scripts/validate_learning_events.py` 的 `:71`（`EVENT_VERSION = 1`）、`:132`（`_TS_RE`）、
`:137`（`_WHOLE_SECOND_RE`）、`:239-252`（`classify_card_state`）、`:1282-1290`
（`_looks_like_review_ext`）、`:1737-1750`（`validate_record_full`）。

# ② 第 1 轮的三条发现 —— 已全部整改，**请不要重复报告，改为核对整改本身**

| # | 你当时给出的形态 | 作者的整改 |
|---|---|---|
| 1 | `"harness_tree": v`（带引号的键）+ 恒返 `{"a":1}` 的假 yaml ⇒ 静默回退父树 | 加**键级探针**（`:552`）：要求解析器在一份只写着 `harness_tree` 的最简文档上给出该键。**不看用户的文件**，故与书写形式无关 |
| 2 | `{harness_tree: v}`（整份 flow mapping）+ 同上 ⇒ 静默回退父树 | 同上 |
| 3 | `note: "open<换行>harness_tree: /a/b"` + 真 PyYAML ⇒ 误拒一份合法文档 | 词法否决补**值内文本豁免**（`:617` 起）：命中串若落在任何已解析值内则不否决。作者随后自查发现第一版豁免只看顶层 `values()`，嵌套一层的值仍误拒，已改成遍历整棵结构 + 自引用环防护 |

请核对：**这三处整改是否真的成立、有没有引入新的问题**，以及下面 §③ 的问题。

# ③ 请按重要性回答这些问题

⓪ **键级探针**（`:552`）：它是本卡挡住形态 1/2 的唯一一层。请核
   (a) 它自己有没有**未被拦下的输入**——什么样的 yaml 模块能答对
       `safe_load("harness_tree: __quiz_answer_key_probe__")` 却仍对用户的 config 说谎？
       （作者已明写「对两道探针都老实、只对这份 config 说谎」的模块属**威胁模型之外**，
       并且指出这种模块在**引号键 / flow mapping** 写法下两层都拦不住 —— 请核这个自述是否
       如实、边界画得对不对）；
   (b) 它有没有**误拒面**——什么样的**合法**环境会让这条探针失败？

① **词法否决的值内豁免**（`:617` 起的遍历）：
   (a) 遍历面是 `dict` 的 keys+values、`list/tuple/set` 的元素、`str` 的子串命中。
       有没有**已解析结构里能藏字符串、而这个遍历走不到**的容器形态？
   (b) 环防护用 `id()` 集合。`id()` 在 CPython 上会被回收复用 —— 在这段代码的生命周期内
       有没有可能产生**误判**（把没访问过的节点当成访问过，从而漏掉一个本该豁免的值）？
   (c) 豁免判据是「命中串出现在某个值内」。这条件会不会**反向被利用**：一份文档顶层真的
       写了 `harness_tree`、解析器谎报无键、而文档里恰好另有一个值含 `harness_tree:` 子串
       ⇒ 豁免生效 ⇒ 不否决？若成立，这是一条未被拦下的输入。

② **`_harness_contract` 的四层**：能不能被一棵「同名、同形状、纯函数行为也一样」的树通过？
   作者已登记一个已知的这样的树（本仓 `b85a168a` 的旧 validator）。请找**别的**已知树或
   形态，或指出这四层里哪一层的判据比它自称的更弱。特别请核：
   (a) 影子门比 `abspath` 不比 `realpath` —— 这个选择是否让影子门在**某些布局**下失效？
   (b) 纯函数探针的具体取值（`2026-08-01T10:00:00Z` 等）是否**跟着 validator 漂**？

③ **Step 2.9 预检块**（`:206-247`）：
   (a) 它从 SKILL.md 自抽取实现。所有派生失败的分支（`QUIZ_ANSWER_NODE` 缺失 / SKILL.md
       读不到 / 块数不对 / 函数数不对）是否**都落在拒写**上，而不是跳过或静默继续？
   (b) 它声称**纯读零写**。`exec` 抽取出来的函数、`ast.parse`、`import validate_learning_events`
       —— 这条路径上有没有**会落盘**的东西（`__pycache__`、锁、临时文件）？
   (c) 它与 Step 0 续跑态（`SKILL.md:166`，`scored_pending_node_update` 时跳过 Step 1-3）
       的交互：续跑**不经过** Step 2.9。这个缺口的实际后果是什么？
   (d) 两个定位锚都是分段拼出来的（`"def " + "_harness_tree" + "("`）以免命中自己。这个写法
       有没有**漏掉的自指面**？

④ **测试的有效性（找假绿）**：
   (a) `_WHOLE_DOCS` 13 格的「有库控制半」把真 PyYAML 结局写死在表里并断言进前提。
       这个前提断言会不会被吞成绿色？`_truth` 的四个取值够不够区分「PyYAML 真的拒了」
       与「PyYAML 收下了但没有这个键」？
   (b) 新文件里 `_fake_yaml(_honest_probes=True)` 这一档的存在理由是「让负控输入能通过
       第一层，否则词法否决就是**门未覆盖的路径**」。请核这个推理，以及**还有没有别的
       层被同样的机制遮住了**。
   (c) `..._preflight_refuses_before_step3` 的零写断言用 `(相对路径, size, mtime_ns)` 集合
       比对。这个写入面判据有没有**测不到的写**？
   (d) 有没有哪一格测试，即使把它声称守护的那行生产代码删掉，也**照样绿**？

⑤ **回归面**：这些改动有没有**打破既有语义**？特别是：
   (a) 「无键 / 值为 null / 值为空串 ⇒ 回退父树」这三条分界（既有 16 门钉着）；
   (b) 缺 PyYAML 时「对任何 config 都不返回任何树」这条不变量；
   (c) 「打不开 config ⇒ 回退」与「打开了但读/解析失败 ⇒ 拒写」的分野（round-9 的 HIGH）。

⑥ 有没有**本卡引入、而上面各问都没覆盖到**的问题？（编码、并发、路径、异常传播、
   拒因文案与实际行为不符、docstring 的声明与代码能力不符，等等。）

# ④ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出：
- `file:line`
- 一句话说明这是什么问题
- 一句话说明怎么让它显形：请用「**负控输入**」「**对照输入**」「**未被拦下的输入**」
  「**门未覆盖的路径**」这四种说法来描述，不要写成攻击步骤。

**如果某一级没有条目，请明确写「无」。** 如果整轮没有 BLOCKER 与 HIGH，请在开头明确写一行
`BLOCKER: 无 / HIGH: 无`，这一行会被用作轮次闭合的依据。

# ⑤ 边界

- 只读。不要修改文件，不要运行会写盘的命令，不要连接 7691 / 7687 / 7692 任何端口。
- 不要评 `backend/scripts/validate_learning_events.py` 的树侧改法（本批零写者文件，
  「让树自报契约版本」已登记为移交事项）。
- 不要评 `canvas-vault/.claude/scripts/fsrs_bridge.py` / `decay_beta.py`（零写者）。
- 不要评同车道上一张卡对 `start-exam-board/SKILL.md` 的改动，不要评 `CARD-G8-3` / `CARD-G8-10`。
- `_bmad-output/` 下的验收单与存档不在审查面内。

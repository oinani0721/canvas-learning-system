# UAT 验收单 — CARD-G4-4b 邻居扩展按 subject 过滤

> 批次: `BATCH-2026-09-04-第十批` · 车道 X3-② · 分支 `card/x3-vaultscope`
> 卡文: `第十批-goals/X3-2.md` · 工时预算 5h
> 基线: `138d2a94`（= 本车道 4a + OBS 收官态）

---

## ⛔ 先读：两条显著声明

1. **卡文的开工前提没满足，本卡换了基线**。卡文写「前提：CARD-G4-4a 已 squash
   合入主干；本卡从**含 4a 的新主干**切」。实测 feature 主干仍在 `67abca34`
   （= `1f249b33` + 2 个第十批文档 commit），**4a 尚未合入**。
   本卡因此**不 merge 主干**，直接在 X3 车道 HEAD `138d2a94` 上继续 ——
   该 commit 已包含 4a + OBS 的全部内容，与「含 4a 的新主干」在**代码上等价**。
   影响：本卡与 4a 在同一分支上串成一条链，主 session squash 时会**一起**合入。
   如果你希望 4b 独立成一次合并，需要先把 4a 合进主干、再从新主干切 4b 重做。
2. **这是真修复，不是登记**。4a 用 `xfail(strict=True)` 锁住的那个跨学科泄漏，
   本卡把它修掉了，用例转为常绿门。`strict=True` 在本卡实测中**真的起了作用**：
   缺陷一修好，它立刻以 `XPASS(strict)` 报红提醒转正（§4-A.2）。

---

## 1. 🎯 一句话目标

同一个笔记库里，A 学科的笔记链接到 B 学科的板子时，检索的「邻居扩展」这一步
会把 B 学科的内容也带回来。本卡给这一步加上学科过滤，把它堵住。

## 2. 📖 你的视角

4a 堵住的是**库与库之间**串台；本卡堵的是**同一个库内部、不同科目之间**串台。

**这句话的适用范围要说清**（Codex round-5 HIGH-3 指初稿「边界才算完整」
是无条件闭合，过宽）：本卡的收口成立于「**请求带了非空学科** 且
**没走跨学科检索**」这两个前提下。两个例外：
- 请求**不带学科**（`subject` 为 `None` 或空串）→ 按设计**不过滤**
  （与主检索同口径），邻居仍可跨科目；
- **跨学科检索**（`cross_subject=True`，含 CRAG 低质量回退自动触发）→
  邻居只按**主**学科过滤，反而比预期**更窄**（见 §未证明 #4）。

## 3. 🖥️ 交互流程（你的屏幕变化）

问同一个问题（**且问的时候指明了科目**），回答里**不会再混进别的科目的内容**。
其余无变化。没指明科目时行为不变（不过滤）——这与「先选库才能查」的
4a 不同：4a 是**必填**，本卡的学科是**可选**，卡文没有要求把它也做成必填。

## 4-A. 🤖 Claude 已代验（全部代跑，✅ = 有证据）

| # | 判据 | 结果 | 证据 |
|---|---|---|---|
| 1 | **(a) 先红** | ✅ `AssertionError: math 请求的邻居扩展带入了 physics 板内容` / `'PHYSICS_SECRET' is contained here: A 库版本内容 \| PHYSICS_SECRET 物理学机密内容` | `--runxfail` 单跑目标用例，`1 failed` |
| 2 | **裁判 1** 两单测文件 | ✅ **35 passed + 3 failed**（3 红 = 主干既有，同名） | 见 §4-A.1 |
| 3 | **裁判 2** 目标用例改前/改后 | ✅ 改前 `1 xfailed` → 改后 **`1 passed`** | 单 nodeid 跑 |
| 4 | **(e)** xfail/skip 零残留 | ✅ 全文件无 `@pytest.mark.xfail` / `skip` | `grep` |
| 5 | **(f)** `test_agentic_rag_vault_scope.py` 0 xfailed；isolation 不回退 | ✅ 23 passed / 0 xfailed（原 17=16+1x，本卡 +6 新用例）；isolation 12 passed + 3 既有红，**与 4a 基线逐条同名** | 见 §4-A.1 |
| 6 | **(g)** 变异 3 条串行 | ✅ **3/3 杀死指定门**，且**记录了失败身份** | `evidence-g44b/mutation-run.txt` |
| 7 | 变异还原三重外部锚点 | ✅ ① 两文件 sha256 一致 ② `git status` 仅本卡改动 ③ `grep MUTANT` rc=1 | 判据不依赖脚本自检 |
| 8 | **裁判 3** 禁改门（`rag.py` / `agents.py` / `exam_service` / `verification_service`） | ✅ 空 | `git log --format= --name-only 138d2a94..HEAD -- <4 文件>` |
| 9 | 4a 面无回归 | ✅ `test_rag_vault_scope_api` + `test_rag_four_state_api` + `test_nothrow_logging_api` **69 passed** | — |
| 9b | **间接回归面**（全仓触及 `retrieve_lancedb` / `expand_neighbors` 的其余测试文件） | ✅ `test_state_graph_l1_routing.py` + `test_four_state_injection.py` **49 passed** | `grep -rln` 枚举出这三个文件，另一个即本卡主战场 |
| 10 | `ruff check` 三个改动文件 + 变异脚本 | ✅ All checks passed | — |
| 11 | live LanceDB / vault 零写 | ✅ 全部测试用 `tmp_path` 建库；未连现网 | fixture 均取 `tmp_path` |

### 4-A.1 基线 → 终态

| 文件 | 基线 `138d2a94` | 本卡终态 |
|---|---|---|
| `test_agentic_rag_vault_scope.py` | 17 = **16 passed + 1 xfailed(strict)** | **23 passed / 0 xfailed**（转正 1 条 + 新增 6 条） |
| `test_lancedb_vault_isolation.py` | 15 = 12 passed + **3 failed** | 15 = 12 passed + 3 failed（**同名三条，未回退未新增**） |
| 合跑 | 3 failed + 28 passed + 1 xfailed | **3 failed + 35 passed + 0 xfailed** |

> 卡文 (f) 写的是「17 passed / 0 xfailed」，那是**转正前的条数**。
> 本卡为 (c) 的注入判据新增了 6 条用例，故实际是 23 passed / 0 xfailed。
> 「0 xfailed」与「isolation 不回退」两条硬指标均达成。

### 4-A.2 `strict=True` 在本卡真的起了作用（值得记一笔）

4a 留下的 `xfail(strict=True)` 不是装饰。本卡修好 `expand_neighbors` 之后，
**还没来得及删标记**时跑了一次，pytest 直接报：

```
[XPASS(strict)] 归 CARD-G4-4b: expand_neighbors 无 subject 过滤。…
                strict=True: 意外修复 (XPASS) 视为失败, 提醒转正。
======================== 1 failed …
```

即：缺陷一旦被修好，`strict=True` **立刻把「你忘了转正」变成红**。
如果当初写的是 `strict=False`，修好之后它会安静地继续显示 `xfailed`，
一条本该转正的门就此长期挂在「已知缺陷」名下 —— 这正是 4a 收紧它的理由。

### 4-A.3 改动面（生产代码只有 4 行功能改动）

| 文件 | 改动 |
|---|---|
| `lancedb_client.py` | ① `expand_neighbors` 签名加 `subject: Optional[str] = None`；② where 后加 `if subject: where_clause += f" AND subject = '{self._escape_sql(subject)}'"` |
| `nodes.py` | ③ 调用点加 `subject=state.get("subject")` |
| `test_agentic_rag_vault_scope.py` | 删 xfail 标记 + 更新过时断言消息 + 新增 `TestExpandNeighborsSubjectFilter`（6 条） |

其余全部是注释/docstring。写法**照抄同文件既有惯用法**
（`_build_where_clause:3211` 的 `subject = '{self._escape_sql(subject)}'`），
没有发明新范式。

### 4-A.4 (g) 变异 —— 3/3 杀门，**且记录了失败身份**

| 变异 | 指定门 | exit | 失败身份（脚本记录，非事后补写） |
|---|---|---|---|
| **M1** 去掉 where 的 subject 子句 | `test_subject_math_drops_physics_neighbor` | 1 | `跨 subject 邻居未被丢弃: 起点 [[共享板]] \| MATH_ONLY 数学内容 \| PHYS_ONLY 物理内容` |
| **M2** 去掉 `_escape_sql` | `test_single_quote_injection_does_not_break_where` | 1 | `注入撑开了 where: … \| MATH_ONLY … \| PHYS_ONLY …` |
| **M3** `nodes.py` 调用点不透传 | `test_neighbor_expansion_respects_subject_boundary` | 1 | `math 请求的邻居扩展带入了 physics 板内容 —— 同 vault 跨 subject 泄漏回归了` |

**M2 能回答什么、不能回答什么**（Codex round-5 HIGH-2 指出初稿归因过宽，
此处收窄）：

注入断言是「一条邻居都不带回」。它在两种情况下都成立 ——
(甲) 转义生效、字面量匹配不到任何行；(乙) where 语法炸了、整段被 `except` 吞掉。

- **M2 证明的是**：把转义**去掉**后，`MATH_ONLY` 与 `PHYS_ONLY` **双双回来**
  （`subject = 'x' OR '1'='1'` 是合法且恒真的条件）。即「未转义会撑开 where」
  —— 转义**在承重**。这是**必要性**。
- **M2 证明不了的是**：保留转义时那条查询**没有抛异常**。
  M2 只观察了「去掉转义」那一侧；(乙) 的可能性它排除不掉。
  初稿把「不是 (乙)」也算到 M2 头上，**过宽**。

**排除 (乙) 的证据在 §4-A.4b**（转义充分性探针）：8 类载荷逐个直接打
LanceDB filter，全部**零命中且不抛异常**，对照值正常命中自己 ——
「不抛异常」这一半才是排除 (乙) 的那条证据。
Codex 独立复跑同一批载荷得到相同结果，判定「是证据归因问题，不是实际注入漏洞」。

另配一条 `test_escape_sql_doubles_single_quote` 直接钉 `_escape_sql` 的行为，
与注入用例互为验伪。

### 4-A.4b 转义充分性 —— 8 类载荷直接打 LanceDB filter（不是推理）

`_escape_sql` 只做一件事：`value.replace("'", "''")`。**它对 LanceDB/DataFusion
的 filter 语法够不够？** 这个问题不能靠「SQL 标准里加倍就是对的」来回答 ——
不同引擎对反斜杠、Unicode 引号的处理不一样。本卡直接把载荷打进 tmp 库实测：

| 载荷 | 转义后 where | 结果 |
|---|---|---|
| `math`（**对照**） | `subject = 'math'` | **命中自己** |
| `x' OR '1'='1` | `subject = 'x'' OR ''1''=''1'` | 零命中，**无异常** |
| `math' OR subject LIKE '%` | `subject = 'math'' OR subject LIKE ''%'` | 零命中，无异常 |
| `math' --` | `subject = 'math'' --'` | 零命中，无异常 |
| `x\' OR '1'='1`（反斜杠转义尝试） | `subject = 'x\'' OR ''1''=''1'` | 零命中，无异常 |
| `x\\' OR '1'='1`（双反斜杠） | `subject = 'x\\'' OR ''1''=''1'` | 零命中，无异常 |
| `x’ OR ’1’=’1`（Unicode 右单引号） | `subject = 'x’ OR ’1’=’1'` | 零命中，无异常 |
| `math'\n OR '1'='1`（含换行） | 跨行 where | 零命中，无异常 |
| `x'' OR ''1''=''1`（已加倍，测二次转义） | `subject = 'x'''' OR ''''1''''=''''1'` | 零命中，无异常 |

**两个判据缺一不可**：

1. **对照命中自己** —— 证明查询机制是活的，「零命中」不是因为整个查询坏了；
2. **注入载荷零命中且不抛异常** —— 「不抛异常」这一半才是关键：
   它把「转义生效、字面量不匹配」与「where 语法炸了、被 `except` 吞掉」
   分开了。若是后者，这些行会以异常形式出现，而不是安静地返回空。

反斜杠那两条是特意测的：DataFusion **不**把 `\'` 当作转义序列
（它是「字面反斜杠 + 加倍的引号」），所以没有逃逸面。这是**实测**结论，
不是从「SQL 标准」推出来的。

> 与 M2 变异互补：M2 证明「**去掉**转义会撑开 where」（转义在承重），
> 本探针证明「**加上**转义后各类载荷都关不出去」（转义够用）。
> 一个证必要性，一个证充分性。
>
> ⚠️ **这条实证是版本域内的结论，不是永久不变量**：探针跑在
> `lancedb 0.30.2` / `pyarrow 23.0.1` 上，而 `requirements.txt:76` 钉的是
> **`lancedb>=0.14.0`（上界开放）**。「反斜杠不构成转义序列」是 DataFusion
> **当前**的 filter 解析行为；将来若上游改了字符串字面量的转义规则，
> 这一条需要重跑。`_escape_sql` 的「单引号加倍」本身是 SQL 标准做法、
> 也是同文件其它 8 处过滤共用的写法，所以**代码不会因此变错**，
> 只是**这份实测证据**要跟着版本走。

### 4-A.5 本卡的变异脚本修了 4a 脚本被点名的三处

`evidence-g44b/g44b_mutations.py` 相对 4a 的 `g44_mutations.py`：

| 4a 的问题 | 4b 的做法 |
|---|---|
| Codex round-4 HIGH-3：kill 时丢弃 pytest tail / 断言 / nodeid，归档只能证「exit=1」 | **记录失败身份**：`--tb=line -rf` + 保存 `^E ` 行与 nodeid（上表即其输出） |
| 无 `__main__` 守卫 —— `import` 即对生产源码施加变异 | 加 `if __name__ == "__main__": sys.exit(main())`，顶层零副作用 |
| `try/finally` 不接信号，SIGTERM 下变异体留在工作树 | `signal.signal(SIGTERM/SIGINT)` 转成异常，让 `finally` 跑到 |

还原判据同样收紧：对**全部**被变异文件逐个复核 sha（不是只盯一个），
`exit==1` 才算杀，其余非零一律硬失败。

## 4-B. 👤 你来验（产品体验，2 分钟）

在一个**同时放了多个科目**的笔记库里，问一个某科目的问题。

- 预期：回答里引用的笔记**全部来自这个科目**。
- 以前会出现的情况：某条笔记链接到了别科目的板子，那个板子的内容就被一并捞出来。

**这张卡给你的实际好处**：同一个库里不同科目的笔记不会再混进检索结果。

## 5. 🚦 验收结果

Claude 侧全部代验完成：指定裁判全绿（`23 passed / 0 xfailed`；isolation
`12 passed + 3` 条主干既有红）；目标用例改前 `xfailed` → 改后 `passed`；
变异 3/3 杀门并记录失败身份；4a 面 69 passed + 间接回归面 49 passed 无回归；
live vault / LanceDB / 只读车道全程零写；**Codex round-5 末行 `阻断级 = 0`**。

按本批合并门（阻断级 = 数据丢失 / live 写入 / 安全 / 指定裁判红 / 负控假绿）：
**本卡阻断级 = 0，可合**。Codex 的 3 HIGH + 1 MEDIUM 全为**声明过宽**类，
已逐条撤回/收窄（§6.6），无一要求改功能代码。

**留给你的三件**：D4（基线换成车道 HEAD，因 4a 未先合入主干）、
台账 R1（`course_id` 分支的 schema 依赖）、台账 R2（`cross_subject` 收窄，
CRAG 回退路径自动可达）。

- [ ] 通过
- [ ] 有问题（写在 §6 批注区）

## 6. 📝 批注区（默认裁决 D1-D3，卡文 §六）

| 编号 | 事项 | Claude 默认取值 | 你的裁决 |
|---|---|---|---|
| **D1** | subject 不匹配的邻居**丢弃**（而非「保留但不加分」） | 按卡文默认执行。理由：邻居是被**当作检索结果返回**的，留下来就是泄漏，「不加分」挡不住它进上下文 | |
| **D2** | `subject` 默认 `None`，向后兼容 | 按卡文默认执行。`None` 时 where 与本卡之前逐字相同，另有专门用例钉住 | |
| **D3** | 不扩到 `search()` 主检索（主检索已各自传 subject） | 按卡文默认执行，本卡零改动 `search` / `search_multiple_tables` | |
| **D4**（本卡新增） | 基线换成车道 HEAD 而非「含 4a 的新主干」（4a 尚未合入） | 见「先读 #1」。若你要 4b 独立合并，需先合 4a 再重切 | |

## 6.6 Codex 定向复审（G4-4 族第 5 轮，本卡唯一一轮）—— **阻断级 = 0**

提示词 `_bmad-output/审查/prompts/codex-prompt-CARD-G4-4b.md`（6709 字节），
输出 `codex-review-CARD-G4-4b.md`（7008 字节，`rc=0`，一次成功，无需重发）。
绑定 `3a938e28`。

**一句话结论**：*「核心修复有效，未发现阻断级问题；但有 3 条声明过宽的 HIGH，
以及 1 条非阻断的 `cross_subject` 召回问题。」* **末行 `阻断级 = 0`。**

### PASS 的 5 项（它独立复核，不采信我的说法）

向后兼容（新形参在签名末尾、`None` 跳过分支、仓内单一生产调用点）／
空串未引入链内分叉／D1 丢弃语义成立／**变异门**（它在**隔离的临时 HEAD 副本**里
重放 M1/M2/M3，3/3 以指定断言 `exit=1` 被杀，并复核我的工作树两份生产文件
SHA 前后相同、零 `MUTANT` 残留）／指定裁判（`23 passed / 0 xfailed`、
`12 passed + 3` 基线红、4a 三端点文件 `69 passed`、ruff 通过、未连 live）。

### 3 HIGH + 1 MEDIUM 与本卡处置

| # | Codex 的发现 | 本卡处置 |
|---|---|---|
| **HIGH-1** | 「缺 `subject` 列没有新增 schema 风险」**论证不成立** —— `course_id` 分支主检索查的是 `vault_notes`（`nodes.py:386`），邻居却恒查 `canvas_nodes`（`:432`），「同一张表」的前提只在默认分支成立 | ✅ **已撤回并限缩**。复核属实。§未证明 #2 改为分支表：默认分支仍成立、`course_id` 分支**确实新增**了依赖且失败静默。定性：召回损失，非数据丢失/泄漏 |
| **HIGH-2** | M2 变异**不能**排除「转义后语法错被吞空」—— 它只观察了「去掉转义」那一侧 | ✅ **已收窄归因**。M2 证**必要性**；排除 (乙) 的证据是 §4-A.4b 的 8 载荷探针（零命中**且不抛异常**）。Codex 独立复跑同批载荷，判「归因问题，非实际漏洞」 |
| **HIGH-3** | `nodes.py` 新注释称「同源 + 分裂会告警」过宽 —— `subject_id=""` 时 VaultScope 改走 canvas 二级、state 留空串，而哨兵在 `if not subject: return`（`:81`）**早退不告警**；验收单的「边界完整／其余无变化／功能面收口」也无条件 | ✅ **代码注释与三处闭合措辞均已收窄**到「非空 subject + `cross_subject=False`」，并把空串反例写进注释 |
| **MEDIUM-4** | `cross_subject=True` 确实过度收窄，但**卡文没有该完成条件，登记后卡足够**；不过闭合文案必须收窄 | ✅ 代码不改（与卡文 (b) 单值形参一致）；登记升级为「CRAG 回退路径**自动可达**」+ 三选项权衡表；闭合措辞已收窄 |

### 本卡对这一轮的自评

Codex 的 HIGH-1 是**我论证里的真洞**：我验证了「主检索也依赖同一列」，
却没有检查「主检索是不是总查同一张表」—— `course_id` 分支正好不是。
这与本卡另外两处自查失误同形（`dredd` 高估影响、`cross_subject` 低估可达性）：
**影响面判断的两头都要追，只追一头就是盲区**。

HIGH-2 则是「证据归因」而非「证据缺失」—— 排除 (乙) 的探针我**做了**，
只是在 M2 那一段把功劳记错了地方。

## 7. 🔗 技术 spec 引用

- 卡文：`第十批-goals/X3-2.md`
- 4a 验收单：`UAT-CARD-G4-4a-显式VaultScope-2026-09-04.md`（本卡的直接前身）
- 既有惯用法参照：`lancedb_client.py::_build_where_clause:3211`

## ⛔ 本卡未证明什么（必填段）

1. **没有连真库验证过**。全部测试跑在 `tmp_path` 上的临时 LanceDB。
   证明的是**过滤逻辑**，不是现网数据的实际隔离状态。
2. **没有覆盖 `subject` 为 NULL 的历史行**（缺**列**的情况已查证不构成新风险，
   见下）。本卡 fixture 每行都带 `subject`；若现网某行该列为**空值**，
   `AND subject = 'math'` 会把它从邻居结果里丢掉。这是行为变化，本卡没有测。

   > **查证记录（初稿把这条写得比事实惊悚，此处收窄）**：初稿担心的是
   > 「表**缺 subject 列**会让查询抛 `LanceError(Schema)`、被
   > `except Exception: continue` 静默吞掉、该链接的邻居全丢」。
   > 该失败模式**真实存在**（`search()` 在 `:3312-3318` 有专门注释说明缺列会让
   > "entire branch fail silently"，并为此建了 schema guard），
   > 但**本卡没有引入它**：
   > - `expand_neighbors` 生产上**只有一个**调用方（`nodes.py:430`），
   >   传的是 `resolve_table_name("canvas_nodes")`；
   > - **同一张表**上，主检索链 `search_multiple_tables` → `search` 早已
   >   通过 `_build_where_filters` 建 `subject = '<escaped>'` 子句；
   > - 而 `search()` 的 schema guard 缺列清单是
   >   `("doc_type", "course", "tags_str")`，**不含 `subject`** ——
   >   即代码库本就把 `subject` 当作「必然存在」的列。
   >
   > ### ⛔ 这个结论**被 Codex round-5 HIGH-1 推翻了一半，此处撤回并限缩**
   >
   > 我原本写：「若 `subject` 列缺失，**主检索早就已经坏了**，本卡没有新增
   > schema 依赖面」。**论证有洞** —— 它假定「主检索与邻居扩展查同一张表」，
   > 而这个前提**只在一条分支上成立**：
   >
   > | 分支 | 主检索查的表 | 邻居扩展查的表 | 「同表」是否成立 |
   > |---|---|---|---|
   > | 无 `course_id`（默认） | `search_multiple_tables` → `DEFAULT_TABLES=["canvas_nodes"]` | `resolve_table_name("canvas_nodes")` | ✅ 成立 |
   > | **有 `course_id`** | `progressive_scope_search(table_name="vault_notes")`（`nodes.py:386`） | 仍是 `canvas_nodes`（`nodes.py:432`） | ❌ **不成立** |
   >
   > 也就是说：走 `course_id` 分支时，主检索压根不碰 `canvas_nodes`，
   > 所以「`canvas_nodes` 上的 `subject` 依赖早就存在」这句话**推不出来**。
   > 若该表恰好缺 `subject` 列，**只有邻居这一路会坏，而且是静默地坏**
   > （`lancedb_client.py` 的 `except Exception: continue` 吞掉 schema 错）。
   > Codex 用临时真库复现了这个形态；本卡自己的缺列探针也是同一结果
   > （`subject=None` 带回邻居 / `subject='math'` 零邻居）。
   >
   > **限缩后的正确表述**：
   > - **默认分支**（无 `course_id`，即绝大多数流量）：主检索与邻居扩展查
   >   **同一张表**、依赖**同一个列**，本卡未新增 schema 依赖面 —— 这一半仍成立；
   > - **`course_id` 分支**：co-dependency **不成立**，本卡确实**新增**了一个
   >   「`canvas_nodes` 必须有 `subject` 列」的依赖，且失败是静默的召回损失。
   >
   > 定性：**召回损失，不是持久数据丢失、不是安全泄漏**（Codex 同判），
   > 故非阻断。但「没有新增依赖面」这句**无条件**的说法已撤回。
   > 已并入台账移交 R1（给 `expand_neighbors` 补 `search()` 那道 schema guard）。
   >
   > **仍然留下的不对称（登记级，非本卡引入）**：`search()` 有 schema guard +
   > 分支异常累积（全分支失败会 raise）；`expand_neighbors` 两者都没有，
   > 它的 `except Exception: continue` 会把任何查询异常静默吞成「零邻居」。
   > 建议后续卡给 `expand_neighbors` 补同款 schema guard。
3. **没有证明 `state["subject"]` 与请求作用域二级永远一致**。4a 的
   `_warn_subject_scope_mismatch` 是**哨兵**（只告警不抛错），不是门。
   两者分裂时，本卡的过滤会按 `state["subject"]` 走。
4. **⚠️ `cross_subject=True` 下本卡引入了一处行为收窄**（定性从初稿的
   「未测」上调 —— 它不只是没测，是**可以从代码结构直接读出来的行为变化**）。

   机制（`nodes.py`，行号为本卡终态）：
   - `:341` `subjects_to_search = [subject] if subject else [None]`；
     `cross_subject=True` 时 `:350` 用 `expand_search_subjects` 把它**扩成多值**；
   - `:380` `for search_subject in subjects_to_search:` —— 主检索**逐个学科**查，
     结果合并进 `lancedb_results`；
   - 而**邻居扩展在这个循环之外**（`:430`），只调用**一次**，
     传的是 `subject=state.get("subject")` —— **原始单值**，不是扩展后的列表。

   后果：`cross_subject=True` 时，主检索会带回桥接学科（如 physics）的行，
   但这些行的**邻居**会被按主学科（math）过滤掉。
   **改前**这些邻居会回来，**改后**不会 —— 这是本卡引入的**收窄**（非泄漏）。

   **可达性（初稿写「opt-in 默认关」是低估了，此处更正）**：
   `cross_subject` 的 API 字段确实默认 `False`（`rag.py:80-81`），插件也不传
   （插件根本不调 `/rag/query`）。**但它还有一条自动路径**：
   `deep_research.py` 在**三处**（`:226` / `:242` / `:303`）主动返回
   `"cross_subject": True`，而 `state_graph.py:692-698` 明写
   *「deep_research_fallback **reruns retrieval once** via the same
   fan_out_retrieval conditional edge」* —— 即 CRAG 低质量回退时
   （`route_after_quality_check` 的第三个出口，`:366`），
   系统会**自己**把 `cross_subject` 打开并**重跑一次检索**。

   所以这条收窄**在生产上可达**，触发条件是「检索质量低 + safe_degradation」，
   不需要任何人手动开开关。而 `deep_research.py:205` 的注释写的正是
   *「sets cross_subject=True (**widens** local recall)」* ——
   本卡的过滤在这条**专门用来放宽召回**的路径上起了反作用。

   仍然缓解的部分：它是**召回减少**，不是泄漏，也不是数据丢失；
   主检索的扩展不受影响（只有邻居那一层被按主学科收窄）。

   **三个选项与本卡的取舍**（把权衡摆出来，不藏在「超出范围」后面）：

   | 选项 | 行为 | 代价 |
   |---|---|---|
   | **A（本卡采用）** | 邻居恒按 `state["subject"]` 过滤 | 泄漏堵住；`cross_subject` 路径召回收窄 |
   | B | `subject=None if cross_subject else …` | 无收窄；但那条路径上**泄漏原样留着** |
   | **C（正解）** | 把 `subjects_to_search` 传进去，where 用 `subject IN (...)` | 两头都对；但要改形参形状（单值 → 序列）+ 新门 |

   选 A 的理由：本卡的**任务就是堵泄漏**，卡文 D1 明写「不匹配的邻居丢弃」；
   B 会在一条可达路径上把缺陷原样留下，与卡文相悖。A 是**安全但偏窄**，
   B 是**宽但不安全** —— 在两者之间，本卡选安全。
   C 才是正解，但它改的是卡文 (b) 钉死的**单值** `subject` 形参形状，
   还要配新的 `IN (...)` 转义门与变异，超出本卡 5h 范围。**已列进台账移交（R2）**，
   并把可达性写清楚，好让排期时能正确定优先级。
5. **`subject` 的真值语义已查证与主检索一致，但没有为它单独立门**。
   本卡用 `if subject:`（Python 真值判断），空串 `""` 会**不加子句**。
   查证链（三跳，都可复核）：
   - `rag.py` 的 `subject_id: Optional[str]` 无 `min_length`，客户端可传 `""`；
   - `rag_service.py:295` `effective_subject = subject_id` 直通，
     `:302` 写进 `state["subject"]`；
   - **主检索用的是同一个惯用法** —— `nodes.py:341`
     `subjects_to_search = [subject] if subject else [None]`，
     空串同样落到「不按 subject 过滤」。

   即：空串在**整条链上**都等于「没指定学科」，本卡没有引入语义分叉。
   `_build_where_clause:3211` 的 `if subject:` 也是同一口径。
   **但这条一致性是查证出来的，不是门** —— 没有用例钉住「空串不过滤」。
   非 `str | None` 的 falsy 值（`0` / `[]`）在生产上不可达（类型是 `Optional[str]`），
   同样没有门。
6. **4a 面的 69 passed 只覆盖三个端点测试文件**，不是全量回归。

## 🔍 追到一半、结论是「无法确定」的一项（如实记录，不臆断）

审查过程中冒出一个问题：**现网的 `canvas_nodes` 表里，`subject` 列会不会为空？**
（若为空，本卡的 `AND subject = 'x'` 会把这些行从邻居里丢掉。）

追查链与它停在哪里：

1. **写侧确实存在两种形态** —— `lancedb_client.py` 里既有
   `"subject": subject or ""`（`:1622` / `:1886` / `:2169`，None 时落**空串**），
   也有 `"subject": subject`（`:1350` / `:1363` / `:1860` / `:2145`，可落 **NULL**）。
   两者在 `subject = 'math'` 下**都不匹配**，都会被丢弃。
2. **同文件有「不让旧行消失」的先例** —— `doc_type` 用
   `(doc_type IN (...) OR doc_type IS NULL)`（`:3247`），
   注释（`:3241-3243`）明写这是为了让 legacy 行「degrade 而不是 disappear」。
   即这个仓**认可**「旧行缺值不该消失」这个原则。
3. **想去现网数据上验一把，但验不了** —— 宿主上的
   `data/lancedb` 与 `backend/data/lancedb` **只有** `vault_notes` /
   `file_fingerprints` / `test_table`，**没有 `canvas_nodes`**；
   但 `docker-compose.yml:161` 用的是**命名卷** `canvas-lancedb:/app/data/lancedb`，
   宿主目录**不是**运行时库。而 `docker ps` 当前**无容器在跑**，
   在不启动服务、不碰 live 基础设施的前提下**看不到卷里的内容**。

**结论：无法确定**。所以本卡既不宣称「现网没有空 subject 行、所以无影响」，
也不宣称「现网有、所以有缺陷」。留给主 session 一条**可执行的核对**：
容器起来后 `docker run --rm -v canvas-lancedb:/d alpine ls /d` 看表清单，
若有 `*_canvas_nodes`，再抽样看 `subject` 列的空值占比。

> 顺带记一个**属于 4a 而非本卡**的观察：4a 把邻居扩展的表从裸 `vault_notes`
> 改成了 `resolve_table_name("canvas_nodes")`。若运行时库里没有 `canvas_nodes`
> 系的表，`open_table` 会抛错、被 `expand_neighbors` 外层的
> `except Exception: pass` 吞掉 —— 邻居扩展会**静默变成 no-op**（不报错、
> 不影响主检索结果）。同样因为看不到卷内容，**本卡无法判定这是否已经发生**。
> 这条不影响 4b 的正确性（4b 的过滤逻辑在表存在时才执行），但值得主 session 核。

## 📋 台账待登记条目（由主 session 单点写入）

> 本车道**未改**台账（卡文 §五 硬边界）。

1. **§一 G4-4 行**：subject 面（CARD-G4-4b）已落地，4a 留下的
   `xfail(strict=True)` 已转正为常绿门。
   ⚠️ 措辞按 Codex round-5 HIGH-3 收窄：**不写「功能面收口完毕」** ——
   收口成立于「非空 subject + `cross_subject=False`」；
   `cross_subject=True` 的过度收窄（R2）与 `course_id` 分支的 schema
   依赖（R1）都还挂着。准确说法是「**vault 面与 subject 面的主路径已收口**」。
2. **合并形态提醒**：4b 与 4a 在**同一分支** `card/x3-vaultscope` 上串成一条链
   （因 4a 未先合入主干）。squash 时会一起进；若需分开，见「先读 #1」。
3. **新增移交项 G4-4b-R1（优先级建议：中）**：给 `expand_neighbors` 补
   `search()` 那道 schema guard（`lancedb_client.py:3312-3335`）。
   ⚠️ 定性按 Codex round-5 HIGH-1 更正：这**不完全是**「非本卡引入」——
   在 **`course_id` 分支**上，主检索查 `vault_notes`（`nodes.py:386`）而邻居查
   `canvas_nodes`（`:432`），两者**不同表**，所以「`canvas_nodes` 的 subject
   依赖早已存在」推不出来；该分支上本卡**确实新增**了一个 schema 依赖，
   且失败被 `except Exception: continue` 静默吞成「零邻居」。
   默认分支（无 `course_id`）则同表同列，未新增。
   另：现网若有 `subject` **为空值**的历史行，本卡的等值过滤会丢弃它们。
4. **新增移交项 G4-4b-R2（优先级建议：中，因为可达）**：
   `cross_subject=True` 时邻居扩展在 `for search_subject` 循环**之外**
   只调一次、传原始单值 subject，桥接学科结果行的邻居会被按主学科过滤掉
   —— **本卡引入的召回收窄**。⚠️ 它**不是**「手动 opt-in 才会碰到」：
   `deep_research.py:226/:242/:303` 会自动置 `cross_subject=True`，
   `state_graph.py:692-698` 随即**重跑一次检索** —— 即 CRAG 低质量回退
   路径上自动可达。修法（选项 C）：把 `subjects_to_search` 传进去、
   where 用 `subject IN (...)`。详见「未证明」#4 的三选项表。
5. **新增移交项 G4-4b-R3（需现网核对）**：容器起来后核
   `canvas-lancedb` 卷里是否有 `*_canvas_nodes` 表、其 `subject` 列空值占比。
   两件事都悬在这上面：本卡过滤会不会误伤空 subject 旧行，
   以及 4a 的表名切换有没有让邻居扩展静默变成 no-op。见「追到一半」节。
6. **变异脚本范式已升级**：`evidence-g44b/g44b_mutations.py` 修了 4a 脚本被
   Codex round-4 点名的三处（失败身份留存 / `__main__` 守卫 / 信号处理），
   建议后续卡以它为模板，并回头补 `g44_mutations.py`（4a 的 R5 移交项）。

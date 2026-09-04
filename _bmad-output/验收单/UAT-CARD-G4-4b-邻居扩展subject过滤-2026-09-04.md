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
两者合起来，检索结果的边界才算完整。

## 3. 🖥️ 交互流程（你的屏幕变化）

问同一个问题，回答里**不会再混进别的科目的内容**。其余无变化。

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

**M2 的失败身份回答了「注入用例是不是假绿」这个问题**：
注入断言是「一条邻居都不带回」。这在两种情况下都成立 ——
(甲) 转义生效、字面量匹配不到任何行；(乙) where 语法炸了、整段被 `except` 吞掉。
只跑正向测试分不出这两者。M2 把转义去掉后，**`MATH_ONLY` 与 `PHYS_ONLY` 双双回来**
（`subject = 'x' OR '1'='1'` 恒真），说明未转义时 where 是**合法且恒真**的，
即转义**确实在承重**，不是 (乙) 那种「碰巧空」。

另配一条 `test_escape_sql_doubles_single_quote` 直接钉 `_escape_sql` 的行为，
与注入用例互为验伪。

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

Claude 侧全部代验完成，指定裁判全绿，变异 3/3 杀门并记录失败身份，
4a 面 69 passed 无回归，live 零写。

- [ ] 通过
- [ ] 有问题（写在 §6 批注区）

## 6. 📝 批注区（默认裁决 D1-D3，卡文 §六）

| 编号 | 事项 | Claude 默认取值 | 你的裁决 |
|---|---|---|---|
| **D1** | subject 不匹配的邻居**丢弃**（而非「保留但不加分」） | 按卡文默认执行。理由：邻居是被**当作检索结果返回**的，留下来就是泄漏，「不加分」挡不住它进上下文 | |
| **D2** | `subject` 默认 `None`，向后兼容 | 按卡文默认执行。`None` 时 where 与本卡之前逐字相同，另有专门用例钉住 | |
| **D3** | 不扩到 `search()` 主检索（主检索已各自传 subject） | 按卡文默认执行，本卡零改动 `search` / `search_multiple_tables` | |
| **D4**（本卡新增） | 基线换成车道 HEAD 而非「含 4a 的新主干」（4a 尚未合入） | 见「先读 #1」。若你要 4b 独立合并，需先合 4a 再重切 | |

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
   > 结论：若 `subject` 列真的缺失，**主检索早就已经坏了**，不是本卡引入的。
   > 本卡的 where 与主检索依赖**同一个列**，没有新增 schema 依赖面。
   >
   > **仍然留下的不对称（登记级，非本卡引入）**：`search()` 有 schema guard +
   > 分支异常累积（全分支失败会 raise）；`expand_neighbors` 两者都没有，
   > 它的 `except Exception: continue` 会把任何查询异常静默吞成「零邻居」。
   > 建议后续卡给 `expand_neighbors` 补同款 schema guard。
3. **没有证明 `state["subject"]` 与请求作用域二级永远一致**。4a 的
   `_warn_subject_scope_mismatch` 是**哨兵**（只告警不抛错），不是门。
   两者分裂时，本卡的过滤会按 `state["subject"]` 走。
4. **没有覆盖 `cross_subject=True` 的跨学科检索场景**。该开关下主检索会
   扩展到相似学科，而本卡的邻居过滤仍只按 `state["subject"]` 单值过滤 ——
   跨学科模式下邻居可能被过度收窄。本卡**没有测**这条路径。
5. **没有测 `subject` 为空字符串以外的 falsy 值**（如 `0`、`[]`）。
   `if subject:` 对它们都不加子句；生产上 `state["subject"]` 只可能是
   `str | None`，但这是**推断**不是门。
6. **4a 面的 69 passed 只覆盖三个端点测试文件**，不是全量回归。

## 📋 台账待登记条目（由主 session 单点写入）

> 本车道**未改**台账（卡文 §五 硬边界）。

1. **§一 G4-4 行**：subject 面（CARD-G4-4b）已落地，4a 留下的
   `xfail(strict=True)` 已转正为常绿门；G4-4 卡族至此**功能面收口完毕**。
2. **合并形态提醒**：4b 与 4a 在**同一分支** `card/x3-vaultscope` 上串成一条链
   （因 4a 未先合入主干）。squash 时会一起进；若需分开，见「先读 #1」。
3. **新增移交项 G4-4b-R1（登记级）**：`expand_neighbors` 缺 `search()` 那道
   schema guard（`lancedb_client.py:3312-3335`）与分支异常累积，
   其 `except Exception: continue` 会把任何查询异常静默吞成「零邻居」。
   **非本卡引入**（bare except 一直如此，且本卡的 `subject` 列依赖与主检索同源，
   已查证不新增 schema 面，见「未证明」#2）。建议后续卡补齐。
   另：现网若有 `subject` **为空值**的历史行，本卡的等值过滤会丢弃它们。
4. **新增移交项 G4-4b-R2**：`cross_subject=True` 场景下邻居过滤仍是单 subject
   等值，可能过度收窄（见「未证明」#4）。
5. **变异脚本范式已升级**：`evidence-g44b/g44b_mutations.py` 修了 4a 脚本被
   Codex round-4 点名的三处（失败身份留存 / `__main__` 守卫 / 信号处理），
   建议后续卡以它为模板，并回头补 `g44_mutations.py`（4a 的 R5 移交项）。

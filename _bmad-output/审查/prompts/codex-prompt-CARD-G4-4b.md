# CARD-G4-4b 定向复审请求（G4-4 族第 5 轮，本卡唯一一轮）

你是对抗性代码审查员。审查对象：worktree
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope`
（分支 `card/x3-vaultscope`，HEAD `3a938e28`，基线 `138d2a94`）上
`BATCH-2026-09-04-第十批 / CARD-G4-4b` 的实现。

## 这张卡做了什么

4a 用 `xfail(strict=True)` 锁住的那个**同 vault 跨 subject 泄漏**，本卡修掉了。

`expand_neighbors` 的 where 此前只有 `canvas_file LIKE '%<link>%'`，匹配的是
**整张 vault 表**。于是一条 subject=math 的笔记只要写了 `[[物理板]]`，
subject=physics 的行就会被当作「邻居」带回 math 请求的检索结果。

改法（生产代码只有 4 行，其余是注释）：
1. `expand_neighbors` 签名加 `subject: Optional[str] = None`；
2. 非空时 `where_clause += f" AND subject = '{self._escape_sql(subject)}'"`；
3. `nodes.py` 调用点透传 `state.get("subject")`；
4. 测试侧删 xfail、用例转正，并新增 6 条用例。

## 只审这个 diff

```
git diff 138d2a94..HEAD -- \
  backend/lib/agentic_rag/clients/lancedb_client.py \
  backend/lib/agentic_rag/nodes.py
```

（测试文件 `backend/tests/unit/test_agentic_rag_vault_scope.py` 的 diff
可以读作参考，但卡文限定审查面是上面两个生产文件。）

验收单：`_bmad-output/验收单/UAT-CARD-G4-4b-邻居扩展subject过滤-2026-09-04.md`。
变异证据：`_bmad-output/审查/evidence-g44b/`（脚本 + 运行记录）。

## ⛔ 已裁决清单（不要重开，除非能证明裁决前提已失效）

| # | 事项 | 裁决 |
|---|---|---|
| D1 | subject 不匹配的邻居**丢弃**，而不是「保留但不加分」 | 卡文默认裁决。理由：邻居是被当作检索结果返回的 |
| D2 | `subject` 默认 `None` 向后兼容；`None` 时 where 与改前逐字相同 | 卡文默认裁决 |
| D3 | 不扩到 `search()` / `search_multiple_tables`（它们已各自传 subject） | 卡文默认裁决，本卡零改动 |
| D4 | 基线是车道 HEAD `138d2a94` 而非「含 4a 的新主干」——因为 4a 尚未 squash 合入主干（主干仍 `67abca34`）。两者代码等价 | 本卡声明，已写进验收单「先读 #1」 |
| — | 3 条 `test_lancedb_vault_isolation.py` 的红 | 主干既有，基线登记，非本卡 |

## 重点复核项

1. **向后兼容是否真的逐字一致**：`subject=None`（默认）时，where 与改前是否
   完全相同？有没有哪条既有调用路径会因为这个新形参而行为改变？
2. **转义是否承重**：`_escape_sql` 只做 `value.replace("'", "''")`。
   在 LanceDB 的 filter 语法下，这对单引号注入是否**充分**？
   有没有本卡没想到的载荷形态（反斜杠转义、Unicode 引号、注释符）能撑开 where？
3. **丢弃语义的边界**：`if subject:` 用的是 Python 真值判断。
   `state["subject"]` 若是空字符串会**不加子句**（= 不过滤）。
   这是本卡的选择（与 `_build_where_clause:3211` 同惯用法），
   但请核：有没有路径会让 `state["subject"]` 变成空串而调用方本意是「过滤」？
4. **schema 依赖**：本卡在 `expand_neighbors` 的 where 里引用了 `subject` 列。
   本卡的论证是「同一张表上主检索链早已依赖该列，且 `search()` 的 schema guard
   缺列清单 `("doc_type","course","tags_str")` 不含 `subject`，
   所以没有新增 schema 依赖面」。**请独立复核这个论证**。
   特别是：`expand_neighbors` 的 `except Exception: continue` 会把查询异常
   静默吞成「零邻居」，本卡把这条不对称登记为「非本卡引入」——是否成立？
5. **变异证据是否够**：3 条变异（去 subject 子句 / 去转义 / 调用点不透传）
   各自杀了指定门，且脚本**记录了失败身份**（`^E ` 行）。
   本卡用 M2 的失败身份论证「注入用例不是假绿」——
   去转义后 `MATH_ONLY` 与 `PHYS_ONLY` 双双回来，说明未转义时 where 恒真、
   转义在承重，不是「where 语法炸了所以碰巧空」。**请复核这个推理**。
6. **cross_subject 场景**：`state["cross_subject"]=True` 时主检索会扩展到
   相似学科（`subjects_to_search` 多值），而邻居过滤仍是**单** `state["subject"]`
   等值。本卡把它登记为未证明项 #4。请判断这个登记是否足够，
   还是应当在本卡内收口。

## 证据锚点（可直接复核）

- **(a) 先红**：`--runxfail` 单跑目标用例 → `1 failed`，
  `AssertionError: math 请求的邻居扩展带入了 physics 板内容`，
  `'PHYSICS_SECRET' is contained here: A 库版本内容 | PHYSICS_SECRET 物理学机密内容`。
- **改后**：同用例 `1 passed`；未删标记时先报 `XPASS(strict)` → `1 failed`
  （`strict=True` 的设计意图达成）。
- **裁判**：`test_agentic_rag_vault_scope.py` **23 passed / 0 xfailed**
  （基线 17 = 16 passed + 1 xfailed）；`test_lancedb_vault_isolation.py`
  12 passed + 3 主干既有红（同名）；4a 端点面
  （`test_rag_vault_scope_api` + `test_rag_four_state_api` + `test_nothrow_logging_api`）
  **69 passed**。
- **禁改门**：`git log --format= --name-only 138d2a94..HEAD --
  rag.py agents.py exam_service.py verification_service.py` → 空。
- **变异**：`evidence-g44b/mutation-run.txt`，3/3 `exit=1` 且附失败身份；
  外部锚点三条（两文件 sha256 前后一致 / `git status` 无残留 / `grep MUTANT` 零命中）。
- 全部测试用 `tmp_path` 临时 LanceDB，未连现网。

## 已知并如实声明的未证明项（验收单，6 条）

未连真库／`subject` 为空值的历史行会被丢弃（缺**列**的情况已查证不构成新风险）／
`state["subject"]` 与请求作用域二级一致性只有哨兵不是门／`cross_subject=True`
路径未测／`subject` 非 `str|None` 的 falsy 值未测／4a 面 69 passed 不是全量回归。

如果你认为其中任何一条**应该**在本卡范围内证明，请明确说是哪一条、依据卡文哪一段。

## 输出要求

逐条给 verdict：BLOCKER / HIGH / MEDIUM / LOW / PASS，每条附 `file:line` 证据。
不要复述代码。发现「声明比证据宽」（验收单/注释/commit message 声称了它没证明
的东西）按 HIGH 起。

**本批合并门只看一件事**：是否存在**阻断级**问题 —— 定义为：数据丢失 /
向 live vault 或 Neo4j 7691 写入 / 安全 / 指定裁判红 / 负控假绿。
请在输出**最后一行**明确给出：`阻断级 = 0` 或 `阻断级 = N（逐条列出）`。
其余等级一律登记不阻断。

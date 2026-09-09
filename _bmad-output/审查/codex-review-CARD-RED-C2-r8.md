> 批次: BATCH-2026-09-07-第十三批 · 车道 U11-B · 卡 CARD-RED-C2 round-8
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-C2-r8.md)"`
> 审查绑定: `37b7c7b8`（送审时 HEAD，代码面工作树干净）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

> ⚠️ 协议 D-15 上限之外的第三个破例轮（r6/r7/r8 均由用户显式授权）。
> ⚠️ **本轮 stdout 有内容**（4675 字节）——前七轮 stdout 均为 0 字节、内容走 stderr。
> 同一版本 codex 在本机两种行为都出现过，故「0 字节」不能当作「无产出」的判据。

---

核验 SHA：`37b7c7b854ce800129e63875b392ee5cf29dcf81`。结果为 **HIGH 2 / MEDIUM 2 / LOW 1**。以下反例已用抽取的断言离线复现；物理化值以等值符号 E 保持约束，未导入项目、连接数据库或修改文件。

**BLOCKER：无。**

- **HIGH | [test_story_30_24_boundary.py:302](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:302) | S1 的“构造用户字符串必须加引号”前提不成立。 | 将用户条件改成 `e.userId = head(keys({test_:0})) + head(keys({user:0}))`，删除该调用的 `userId` kwarg，随后加一次完整正常调用，全部 A/B 判据仍 PASS。**

  两个 map 键经 `keys()` 转为字符串，拼出 `test_user`；query 既没有引号，也没有完整输入值。这个反例只用原生 Cypher，无需 APOC。[官方 keys 文档](https://neo4j.com/docs/cypher-manual/5/functions/list/#functions-keys)

- **HIGH | [test_story_30_24_boundary.py:317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:317) | S2 未识别子查询结束及外层 UNWIND，外层参数可以替内层常量分页通过检查。 | 保持完整四参数，使用以下单行查询，全部 A/B 判据 PASS。**

  ```cypher
  CALL { MATCH (e:Entity) WHERE e.userId = $userId AND (e.group_id = $group_id OR e.group_id STARTS WITH $group_prefix) RETURN e LIMIT 5 } UNWIND [$limit] AS page RETURN e, page
  ```

  实际 `_expr` 是 ` 5 } UNWIND [$limit] AS page `；`$limit` 明明在子查询外，却被算进内层分页表达式。`page` 确实返回，故不是重复报告已登记的“无用表达式占位”。[CALL 语法](https://neo4j.com/docs/cypher-manual/current/subqueries/call-subquery/)、[UNWIND 语法](https://neo4j.com/docs/cypher-manual/current/clauses/unwind/)

- **MEDIUM | [test_story_30_24_boundary.py:322](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:322) | 首个换行截断会误伤合法参数化分页。 | 将基线 `LIMIT $limit` 排版成 `LIMIT` 后真实换行再写 `$limit`，`_expr` 变成空串并 FAIL；`SKIP` 同样如此。**

  Cypher 将换行视为空白，不改变这里的语义。[官方空白规则](https://neo4j.com/docs/cypher-manual/current/syntax/parsing/#supported-whitespace)

- **MEDIUM | [test_story_30_24_boundary.py:318](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:318) | 扫描器会把反引号属性名误认成分页子句。 | 将基线返回部分改为 ``RETURN e.`limit` AS page LIMIT $limit``，属性名触发额外匹配，表达式被取成 `` ` AS page ``，导致 FAIL。**

  反引号内的关键字属于标识符。[官方关键字规则](https://neo4j.com/docs/cypher-manual/25/syntax/keywords/)

- **LOW | [negctl-security-r8pre-committed-20260909T174405.txt:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/_bmad-output/审查/evidence-red-c2/negctl-security-r8pre-committed-20260909T174405.txt:15) | 摘要不足以独立确认变异生效及逐条失败归因。 | 对⑬保留 `limit` kwarg，会首先失败于旧占位符断言；删除它才首先失败于 S2，两者都能产生日志中的同一个 FAIL。**

  两种归因已分别离线复现。现有文件只能证明它**报告了 5 PASS / 12 FAIL**；缺少实际 query、kwargs 和首失败断言，不能据此认定原变异错误，也不能认定归因已经核验。

**其余问题的核对结果：**

- **B 子集变更没有发现独立的新漏洞。** 上述反例在原“恰好四参数”的 B 下也通过；掩护路径仍来自 A 层漏检。
- **五个正控不足**，至少遗漏了上述合法换行与反引号标识符。
- `WITH 5 AS n … LIMIT n` 不能算有效绕过：官方规定 LIMIT 表达式不能包含变量。[LIMIT 规则](https://neo4j.com/docs/cypher-manual/current/clauses/limit/)
- 已接受的无害字符串常量拒绝、占位符语义与注释启发式边界，不重复评级。生产模板的可见部分确实没有字符串字面量或 SKIP；动态插入的 `read_group_filter()` 未展开，运行态“计数为零”未在本轮独立实测。

**这处判据是否可以合入**

**目前不能合入。** 两条 HIGH 直接否定本轮的结构性保证，两条 MEDIUM 则误拒合法查询，都应在测试判据范围内继续整改；LOW 可登记并补充证据，前轮明确接受的边界无需重开。

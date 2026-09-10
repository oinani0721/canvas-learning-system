# CARD-RED-C2 独立复核请求（round-7 · 只审一处：内联判据的「地基」）

## 一 背景 + 最小读取面（写死，请只读这些）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`
分支 `card/u11-red-c`。**本轮审查 SHA = `d0272927`**（工作树干净）。

**轮次说明**：协议 D-15 上限 5 轮。round-5 仍有 HIGH，车道已按 D-15 停下交主 session；
用户随后**两次显式授权破例加跑**（round-6、本轮 round-7），每次只审上一轮那处整改本身。

**本轮只审一件事**：round-6 的 HIGH 整改是否真的换掉了地基、还能不能被绕。

### 这处判据被连着打回的历史（三轮同一个根因）

| 轮 | 当时的修法 | 下一轮结果 |
|---|---|---|
| r2 | 钉死「期望参数集」`{userId, limit, group_id, group_prefix}` | r5：一次合法调用可**掩护**同序列里的坏调用 |
| r5 | 拆 A/B 两层，并给 `limit` 单写一条「有 `LIMIT` 就必须绑 `$limit`」 | r6：把 `$userId` 换成字面量并删掉该 kwarg，同样漏过 |
| r6 | **换地基**：判据不再看 kwargs（攻击者能自己缩小的集合），改看**本用例自己喂进去的输入值** | ← 本轮要审的就是这个 |

**round-6 整改后的形态**（`test_story_30_24_boundary.py`，A 层对**每次** `run_query` 调用生效）：

1. 无 `groupId` 旧参数名；
2. 恶意原串不得出现在 query 文本（`:191-194` 的安全内核，六轮未动过）；
3. 仍留在 kwargs 里的字符串值不得出现在 query 文本；
4. **新地基**：本用例喂进去的四个值——`user_id="test_user"`、`group_id` 原始恶意串、
   其物理化结果、物理化结果 + `"__"`——**无论 kwargs 怎么变**，都不得出现在任何 query 文本里；
5. 每个仍在 kwargs 里的参数都要有 `$name` 占位符（剥掉 `//` 行注释与 `/* */` 块注释后查）；
6. 每次调用必须带 `group_id` + `group_prefix`，且值等于物理化期望；
7. 出现 `\bLIMIT\s+\d`（`LIMIT` 后**直接跟数字**）时，必须绑 `$limit`。
B 层：至少一次调用带齐四参数。

**最小读取面**（不要读其它文件）：

1. 本轮整改 diff：`git diff --no-color b5047b1d d0272927 -- . ':(exclude)_bmad-output'`
   （应只有 `backend/tests/unit/test_story_30_24_boundary.py`）
2. `backend/tests/unit/test_story_30_24_boundary.py:160-300`（判据全文）
3. `_bmad-output/审查/evidence-red-c2/negctl-security-r6-20260909T161650.txt`（10 输入负控）
4. `_bmad-output/审查/evidence-red-c2/c2-verdicts.md` 的 **§十一**（round-6 处置记录）
5. `backend/app/clients/neo4j_client.py:1105-1130`（现行生产查询，**只读不评**）

## 二 本轮自述，请独立核对（不要采信）

1. 「按输入值查内联」不依赖 kwargs，因此 r6 那种「内联 + 删参数」对 `user_id` /
   `group_id` / 物理化值 / prefix **四个值都不再有效**。
2. `\bLIMIT\s+\d` 既挡住「整数被内联」，又不再误伤 `AS unlimited_count` /
   `'LIMIT' AS marker` / `LIMIT $limit` / `LIMIT toInteger($limit)`。
3. 负控 10 输入：③④ 是 round-6 的两个误报正控（必须 PASS），⑧ 是 round-6 的 HIGH 序列
   （必须 FAIL），⑨ 已重做成**隔离**形态（只可能死在安全内核那一条上）。

## 三 请回答的问题（按重要性排序）

1. **「按输入值查内联」这个地基还能不能被绕**？例如：把值**变形**后拼进文本
   （大小写、转义、Unicode 等价、拼接、参数化片段拼装、编码后再解码），
   使字面量比对查不到、但注入面仍在。
2. 判据 6（每次调用必须带 `group_id` + `group_prefix` 且值正确）与判据 7，
   有没有**合法**查询会被误伤？
3. 还有没有**新的**「一次合法调用掩护坏调用」的路径（B 层「至少一次」是否仍可被满足）？
4. 负控 10 输入是否可信：变异是否真生效、每条的失败理由是否**就是**它声称在测的那条判据、
   ⑨ 的隔离是否成立？
5. §十一 的记述有没有比证据宽的地方？
6. **收官判断**：这处判据现在是否可以合入；若还有残留面，哪些属于「登记即可」、
   哪些属于「必须再改」？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
`<级别> | <file:line> | <一句问题> | <一句复现思路>`。
没有问题的级别请显式写「无」。不要给补丁。
最后另起一节「**这处判据是否可以合入**」，两三句给结论。

## 五 边界

- 只读，不要改任何文件；不要连数据库（7687 / 7691 是现网端口，测试进程不得连接）。
- **本轮只审这一处判据**，不重审前六轮已处置并记录在 §六～§十一 的条目。
- 不评另一张卡（`CARD-RED-R`）的 4 条外来红；不评 reranker 权重表。
- 不要提出「改 `backend/app/**`」的建议——本卡硬边界是零生产改动。

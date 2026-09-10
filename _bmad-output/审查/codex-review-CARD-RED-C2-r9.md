> 批次: BATCH-2026-09-07-第十三批 · 车道 U11-B · 卡 CARD-RED-C2 round-9
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-C2-r9.md)"`
> 审查绑定: `7edbc0c1`（送审时 HEAD，代码面工作树干净）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

> ⭐ **本轮是本卡第一轮 BLOCKER 0 且 HIGH 0** —— D-15 的成功判据（绑最终 HEAD 的一轮
> BLOCKER/HIGH 同时为 0）在此达成。协议 D-15 上限为 5 轮，r6/r7/r8/r9 四轮均由用户显式授权。
>
> ⭐ 本轮 prompt 与前八轮不同：除验收整改外，明确请复核方就**「判据天花板在哪、
> 剩余缺口该留本卡还是拆卡」**给判断（§三.5-6）。其结论见正文末两节。

---

**三处定点整改成立；发现两项 S2 新回归和两项收尾问题。解析器无需成为本卡的合入前置条件，但当前 SHA 尚不宜原样收口。**

已核对判据片段与 `7edbc0c1` 一致。以下结果来自抽取的逐调用 A 层断言的新旧差分，未运行完整 pytest 或执行 Cypher，未改文件、未连接数据库。

| 定点案例 | r8 | r9 |
|---|---|---|
| `LIMIT` 后换行再写 `$limit` | FAIL | PASS |
| 反引号属性名 ``e.`limit` `` | FAIL | PASS |
| `CALL { … LIMIT 5 } UNWIND [$limit]` | PASS | FAIL |
| 已登记的 `keys()` 拼串 | PASS | PASS |

BLOCKER：无。

HIGH：无。以下按本轮明确的“单元测试启发式探针”定位分级。

- MEDIUM | [test_story_30_24_boundary.py:323](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:323) | 删除换行截断后，未识别的 `FOREACH` 边界重新允许外部参数掩护内联分页。 | 保留作用域及四个 kwargs，使用尾部 `WITH e LIMIT 5\nFOREACH (v IN [$limit] | SET e.seen = v) RETURN e`（`\n` 为真实换行），旧版 FAIL、新版 PASS，后者把 `FOREACH` 中的 `$limit` 算进分页片段；该子句形态符合 [Neo4j FOREACH 语法](https://neo4j.com/docs/cypher-manual/5/clauses/foreach/)。

- MEDIUM | [test_story_30_24_boundary.py:326](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:326) | 新增的 `}` 边界不区分 map 与子查询，产生合法参数化分页误报。 | 将查询尾部改成 `LIMIT size(keys({})) + $limit`，旧版 PASS、新版 FAIL，实际分页值仍为 `$limit`，扫描却在空 map 处截成 ` size(keys({`；该表达式符合 [LIMIT 的表达式要求](https://neo4j.com/docs/cypher-manual/5/clauses/limit/)。

- LOW | [test_story_30_24_boundary.py:282](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:282) | 降级文案仍不一致，自述③不完全成立。 | 对照 282、285、288 行保留的“结构性判据”“两条改为结构性”和“字符串必须加引号”，与 296–301 行的新声明直接冲突；329 行“说明分页值被内联”也被上述 map 误报反证。

- LOW | [negctl-security-r9-20260909T175828.txt:12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/_bmad-output/审查/evidence-red-c2/negctl-security-r9-20260909T175828.txt:12) | 逐条归因仍未充分展示变异：query 被截断，kwargs 仅列键名，失败消息也有截断。 | 比较第 8、12、16 行，基线与两个修复正控只显示相同查询前缀，看不到换行分页或反引号属性，因此不能单凭日志认定变异生效。

**反引号挖空本身未发现确定的新漏过面**；含转义反引号的标识符样本也能通过。负控证据并非全部不足：33–36 行展示内层 `LIMIT 5` 和首失败 `expr=' 5 '`，支持该项 S2 归因；45–57 行支持两种引号拼接的 S1 归因；80–84 行明确保留了 `keys()` 漏过事实。

除 `keys()` 外，建议登记以下无引号字符串来源，无需继续逐项补规则：

| 原生形态 | 示例与边界 |
|---|---|
| 标量转字符串后拆字拼接 | `toString(123)`；`substring(toString(true),2,1)+substring(toString(false),3,1)+right(toString(false),1)+substring(toString(true),1,1)` 按函数语义得到 `user`，但字符来源受限。[字符串函数](https://neo4j.com/docs/cypher-manual/5/functions/string/) |
| 类型名称转字符串 | `toLower(valueType(0))` 后继续截取、拼接；依赖固定类型名称字符域，`valueType()` 要求 Neo4j 5.13+。[标量函数](https://neo4j.com/docs/cypher-manual/5/functions/scalar/) |
| 图中名称恢复 | `labels(n)`、`type(r)` 后索引或拼接；依赖已有标签、关系类型及对这些名称的控制。[列表函数](https://neo4j.com/docs/cypher-manual/5/functions/list/)、[标量函数](https://neo4j.com/docs/cypher-manual/5/functions/scalar/) |

这些是缺口家族登记，不代表每一种都能编码任意用户串，也未逐项证明绕过当前完整测试。

**这处判据是否可以合入**

可以作为明确限定能力的单元测试探针合入，**不必等待 Cypher 解析器**。但当前 `7edbc0c1` 还需统一旧文案、补齐关键负控证据，并把本轮 S2 的漏过与误报纳入明确的限制声明；只降级 S1 尚不足以原样收口。完成这些有限收尾后，我支持合入，不要求继续枚举绕法。

**剩余缺口该留还是该拆卡**

推荐 **（c）拆独立卡，本卡保留缺口登记后收口**，无需沿当前正则继续磨无引号拼串。独立卡应覆盖“Cypher 解析＋参数绑定和来源判定”：解析器能识别结构，但解析成功本身不证明全参数化。

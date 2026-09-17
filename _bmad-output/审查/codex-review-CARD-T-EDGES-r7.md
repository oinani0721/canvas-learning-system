## 终审结论

绑定 **`a6f682410482a25a8aea3b052b1d36e59789e6b9`**：

**BLOCKER 0 / HIGH 1（卡外既有）/ MEDIUM 0 / LOW 4。**

本轮未发现功能回归；仍有措辞和重复断言需要收尾，尚不能称“全部干净”。全程只读，未运行测试、未连接数据库。

## BLOCKER

无。

## HIGH

**H1 — 缺陷成立，但超出本卡改动面；建议维持 HIGH。**

- **位置：** [neo4j_client.py:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/clients/neo4j_client.py:411)，同文件 `:416`、`:553`、`:669`。
- **问题：** 初始化阶段的凭据、配置异常仍会被转成 JSON fallback，端点失去以 500 暴露部署错误的信号。
- **显现条件：** 首次初始化失败、fallback 初始化成功，随后查询返回空行；另一侧报告成功时，端点返回 207。

**接受本卡“限定措辞＋client 侧移交”的处置，但不等于 H1 已修复。** 为避免把“初始化之后”误读成充分保证，建议说明改为：

> `run_query` 原样抛出且不被本元组捕获的异常才会上抛成 500；初始化阶段被 client 吞掉的异常不受该保证覆盖。

## MEDIUM

无。原 M1 的响应语义已修正；剩余文字问题降为 LOW。

## LOW

### R7-L1：M1 仍有“未确认＝未落盘”的残留表述

- **位置：** [edges.py:222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:222)、[测试文件:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:76)，测试文件 `:643`、`:656`。
- **问题：** 这些位置仍将空行或写确认描述成“图库里没有”“有没有落盘”，与已经修正的响应语义冲突。
- **显现条件：** Neo4j 已提交、确认丢失，重试耗尽后 fallback 返回 `[]`。

可直接统一为：

> 返回空行表示未取得写入确认，提交结果未知；不能据此断言没有落盘。

### R7-L2：L1 的绝对根因分类仍留在测试说明

- **位置：** [测试文件:279](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:279)，同文件 `:69–70`、`:561–565`。
- **问题：** 仍写着“连接池耗尽＝我方 session 泄漏”“它们不是对端的错”，与生产说明中的“处置策略”限定不一致。
- **显现条件：** 正常慢查询占满连接池、触发连接获取超时时，这种根因归类失实。

可直接改为：

> 这些类型按当前处置策略保留 500；异常类型本身不唯一确定根因。

### R7-L3：新增门的覆盖说明仍超过实际检测范围

- **位置：** [测试文件:595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:595)、同文件 `:491`。
- **问题：** 1d2 被描述成锁住“try 只包一行”，RETURN 锚则被描述成补上“没有别的门会发现”的缺口，两处均过强。
- **显现条件：** getter 留在外面、仅将参数构造包进 try 时，1d2 仍绿；7692 真库门执行时，删除 RETURN 原本就会让其失败，NC-G 也记录了这一点。

分别改为：

> 1d2 验证 getter 阶段的 AttributeError 不被降级，防止 try 扩大覆盖 getter。

> 当真库门被 skip 时，原有零数据库门无法发现 RETURN 被删除。

### R7-L4：真库门仍保留一条条件恒真断言

- **位置：** [测试文件:839](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:839)。
- **问题：** 再次检查 URI 白名单没有独立检测力，因为前面的探针已放行，`:835` 又确认 URI 等于同一个输入字符串。
- **显现条件：** 前置检查通过后，同一纯函数对同一字符串再次求值，此断言必然为真。

删除 `:839`，保留 URI 相等断言即可。**这是单条冗余断言，不代表真库门整体不可证伪。**

## 对六个问题的直接回答

| 项目 | 裁定 |
|---|---|
| M1 | 响应和核心说明已修；文字残留未关闭，见 R7-L1。 |
| M2 | **可关闭。** sentinel-only 加类型名前缀断言有效。 |
| M3 | **原来缺少 getter 边界门的问题可关闭。** 精确覆盖范围需按 R7-L3 改写。 |
| L1 | 未完全关闭，见 R7-L2。 |
| L2 | **可关闭。** 独立预期表与继承捕获关系的主要说明已经准确。 |
| H1 处置 | 本卡范围内可接受，保留卡外 HIGH。 |

**新门均可证伪：** NC-F 对应 getter 被捕获的回归；NC-G 对应实际发送的 query 丢失 RETURN 片段。RETURN 文本锚只证明片段存在，不能单独证明它是有效、未被注释的 Cypher 子句；真库门提供执行语义验证。

**17 格仍有上述 `:839` 条件恒真断言；其余核心行为断言未发现同类恒真／恒假问题。**

**回归判断：** 本轮生产可执行差异只调整未确认状态的日志和错误文案，异常元组、查询、参数和控制流未变；未发现功能回归。R7-L3 包含本轮新增的说明错误。

证据核验结果：

- 生产源码的提交内哈希、工作区哈希与负控前后哈希一致；存档记录 NC-E/F/G 分别 **5／1／2 格失败**，还原后 **17 passed，`rc=0`**。
- 单元测试存档实际为 **35 failed、29 errors、5079 passed，`rc=1`**；两个 nodeids 文件逐字节相同，且与存档的 64 条失败／错误记录一致。这支持“失败清单未增加”，不能表述为单元测试全绿或已证明全项目零回归。

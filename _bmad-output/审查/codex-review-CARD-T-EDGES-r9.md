**绑定 `134cf5a458dc7a9ec6e9f739d50b0bcbb0b0e973`：三条 r8 LOW 均可关闭；另发现 1 条此前遗漏的本卡 LOW，非本轮新增。未发现本轮功能回归。**

| 计数范围 | BLOCKER | HIGH | MEDIUM | LOW |
|---|---:|---:|---:|---:|
| 本卡 | 0 | 0 | 0 | 1 |
| 连同已登记的两条卡外缺陷 | 0 | 2 | 0 | 1 |

## BLOCKER

无。

## HIGH

**本卡：无。** 以下两条沿用已登记结论，本轮仅核对指定读取面中的缺陷说明：

- **卡外，建议 HIGH — `_write_lancedb` 未实际执行异步写入。** 登记依据：[test_edges_dual_write_neo4j_t5b.py:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:84)。调用异步 `add_documents` 经 `to_thread` 返回协程而未等待时，会报告成功但未执行写入。
- **卡外，建议 HIGH — 初始化吞异常使 500 策略失效。** 登记依据：[edges.py:72](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:72)。首次初始化遇到认证／配置异常并转入 JSON fallback 时，异常到不了端点捕获边界，最终可能返回“写未确认”的 207。

## MEDIUM

无。

## LOW

**LOW-1：其他失败消息仍把可能原因写成确定结论；本卡既有，非 r9 新增。**

位置：[test_edges_dual_write_neo4j_t5b.py:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:445)，同文件 `:467`、`:853`。

- **问题：** 身份检查失败被解释为继续“会真连／会真往 7691 写节点”，任意 500 被解释为 `AttributeError` 仍在穿透，均超出判据所能确定的范围。
- **显现条件：** getter 被另一测试替身覆盖、真实连接／认证失败，或请求因其他异常返回 500 时，诊断消息会误指原因。
- **收口：** 分别改为“可能连接／写入”和“可能仍在穿透，需核对异常来源”。

## 五项回答

1. **三条旧 LOW 均关闭。** 1d 两条消息已改为处置策略；清理消息已改为结果未知；指定漂移引用已替换。保留跨文件 `neo4j_client.py:536` 本身不构成缺陷，本轮未扩读核验该行。

2. **新增回执断言恰当，非恒真。** 我在内存中求值了实际表达式：零／正数通过，负数／两行回执失败。允许零删除正确。它检查单行与 `deleted >= 0`，**不独立证明目标 group 已清空，也未检查整数类型**；`0.5`、`True` 同样通过，正常整数性来自 `count(er)` 的查询契约。

3. **未发现核心行为门不可证伪。** 真库查询已经按 `record_id`／`group_id` 过滤，随后同值断言属于冗余；联合 `len(rows) == 1` 仍能发现这些字段写错。覆盖／失败消息的剩余问题见上述 LOW-1。

4. **未发现本轮功能回归。** 差异仅在测试文件，`edges.py` 跨轮 diff 为空；新增检查接受合法零删除。

5. **终审计数如上：本卡 `0 / 0 / 0 / 1`；连同两条已登记卡外 HIGH 为 `0 / 2 / 0 / 1`。**

### 存档证据边界

- r9 存档确有 **17 passed、rc=0**，但没有 HEAD／内容哈希，不能由日志自身独立绑定本次 SHA。
- NC-H 的跑前／还原后哈希与 `34935f62` 的测试文件一致；记录了变异失败、还原通过及当时 7692 残留为零。
- unit 存档为 **35 failed + 29 errors = 64，rc=1**；未包含 SHA 或基线 diff 输出，因此“绑定 r8、与基线 diff 空”不能仅凭该文件独立确认。

全程只读、未连接数据库、未重跑 pytest。

**绑定 `34935f62a361265112e3db71a92a7803636ae865`：R7-L1／L3／L4 可关闭，L2 尚有失败消息残留；H1 限定措辞达标。未发现本轮运行逻辑回归。**

计数：**本卡 BLOCKER 0／HIGH 0／MEDIUM 0／LOW 3**；若连同已登记的独立卡外缺陷列示，则 **HIGH 2**，均非本轮新增。

## BLOCKER

无。

## HIGH

以下两项均**超出本卡改动面，建议维持 HIGH**；依据已有登记及指定存档列示，本轮未扩大读取面重新检查其实现。

1. **H1：初始化吞异常，部署错误可能表现为 207。** 卡内记录位置：[edges.py:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:75)。当初始化把认证或配置异常转为 JSON fallback，后续返回空行时，端点只能给出写未确认，无法保留原始 500 信号。

2. **H2：LanceDB 异步方法被 `to_thread` 调用后，返回的协程未被执行。** 卡内记录位置：[test_edges_dual_write_neo4j_t5b.py:86](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:86)。当走到该 `add_documents` 分支且此前没有失败时，可能返回成功状态而未完成写入；指定探针支持这一机制，但没有直接实跑 `_write_lancedb`。

这里把两项独立根因分开计数，不把“已移交”视为缺陷关闭。

## MEDIUM

无。

## LOW

1. **R7-L2 未完全关闭：失败消息仍把处置策略写成根因结论。** [test_edges_dual_write_neo4j_t5b.py:591](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:591) 仍写“`{type_name} 是本进程/部署缺陷”，`:584` 也有同义表述。当异常元组或响应行为回归导致门报红时，输出仍把 `ConnectionPoolError` 一概归因为本进程／部署缺陷，正常慢查询占满连接池就是反例。  
   **建议表述：**“`{type_name} 按当前处置策略应保留 500；异常类型本身不唯一确定根因`。”

2. **本轮新增：清理失败消息超出回执断言的证明范围。** [test_edges_dual_write_neo4j_t5b.py:907](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:907) 写“清理是空转”，但无回执不能证明 DELETE 未执行。当仅删除 RETURN，或删除提交后确认丢失时，该消息仍会出现。  
   **建议表述：**“清理未取得确认，提交结果未知；verifier 可能已转入 JSON fallback，目标 group 的节点可能滞留在共享 7692。”

3. **既有：复核用行号引用已漂移。** [test_edges_dual_write_neo4j_t5b.py:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:57)、`:62` 分别引用旧的 `edges.py:63`、`:66-70`，实际对应当前 `:119`、`:121-126`；`:841` 的“`:435` 的 skip”也已失效。当按文中行号跳转复核时会定位错误，运行行为不受影响。  
   **建议：**改用函数名及条件表达式定位，与文件已有约定一致。

## 六项问题的结论

| 项目 | 裁定 |
|---|---|
| R7-L1 | **关闭**。既有四处已改为“未取得确认、提交结果未知”。 |
| R7-L2 | **暂不关闭**。主体说明达标，剩上述失败消息。 |
| R7-L3 | **关闭**。getter 门及 RETURN 文本锚均已明确限制覆盖范围。 |
| R7-L4 | **关闭**。冗余断言已删除。 |
| H1 限定措辞 | **达标**。`:72-79` 已明确要求异常从 `run_query` 原样抛出且不被元组捕获，并排除初始化吞异常路径。 |
| 清理回执断言 | **可证伪且符合“必须取得非空回执”的主张**；失败消息需要上述修正。 |

**清理门的证明边界：**NC-H 后一份存档确实显示删除 RETURN 后该断言报红，还原后 17 格通过。它没有证明 verifier 实际经历过中途 fallback，也没有证明删除数量或删后零残留。可选增强是检查“单行回执、`deleted` 为非负整数”；**不要无条件要求 `deleted == 1`**，因为 `finally` 也覆盖尚未成功写入等合法零删除路径。

**17 格其余断言：**未发现其他需要报告的恒真／恒假断言；覆盖说明超出的明确问题是上述清理失败消息。行号漂移属于文档定位问题。

**diff 与证据：**

- 生产文件只有注释变化；测试行为变化是清理添加 RETURN 和回执断言，以及删除 R7-L4 冗余断言。因此“清理之外全是文字”严格说还需加上后一个例外。
- 当前两文件与目标提交一致，SHA-256 也与负控跑前、还原后的记录一致。
- 存档支持 17／268／66 passed；较早负控文件中的首次 NC-H 因 `count=0` 未成功变异，不能采用那段全绿作为负控证明，后面的独立 NC-H 存档有效。
- 指定存档未直接打印删除回执 `{'deleted': 1}`；全库零残留仅代表存档检查当时。

本轮仅做只读复核，未修改文件、未运行测试、未连接数据库。

## 终审结论

绑定 **`65a5e6423dc7d24fdef68775e97d58a4f92bcf1b`**：

| 统计范围 | BLOCKER | HIGH | MEDIUM | LOW |
|---|---:|---:|---:|---:|
| 本卡 | 0 | 0 | 0 | 1 |
| 连同两条已登记卡外缺陷 | 0 | 2 | 0 | 1 |

**r9 指定的三处失败消息可以关闭；全文仍有一项同类措辞残留。未发现本轮行为回归。**

## 分级发现

### BLOCKER

无。

### HIGH

**本卡：无。** 以下两条沿用已登记卡外缺陷，建议级别均为 **HIGH**；本轮未扩读其实现，不声称重新验证或讨论修法。

- **`_write_lancedb` 未执行实际异步写入**：[测试文件:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:84)。触发条件：将异步 `add_documents` 交给 `asyncio.to_thread`，只取得协程对象便报告成功。
- **初始化异常被 fallback 吞掉，部署错误失去预期的 500 信号**：[edges.py:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:75)。触发条件：首次初始化发生认证或配置错误，转入 fallback 后查询返回空行，端点按写未确认处理。

### MEDIUM

无。

### LOW

**LOW-1：部分注释及失败消息仍把有限证据解释为确定结论。** 同类问题合并计一条，均非本轮 diff 新增：

- [测试文件:839](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:839)：仍写“并真往现网写节点”，与下方已改成“可能”的失败消息不一致。**显现条件：**注入失效，但连接、认证或写入失败，实际没有完成写入。
- [测试文件:477](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:477)：sentinel 缺失不能推出“不是 stub 的 AttributeError 被 except 收下换来的”。**显现条件：**生产仍捕获该异常并返回 207，但错误文本被脱敏或仅保留类型名；断言应失败，当前失败归因却不成立。

收口分别改为“可能写入”和“缺少预期 sentinel，无法确认来源，错误文本也可能被改写”即可。[测试文件:441](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:441) 的邻近确定性说明也宜同步。

## 对六个问题的回答

1. **r9-LOW-1：按原指定三处，可以关闭。** 新文本已区分可能原因和确定结果；上述 LOW 是其他位置的残留。

2. **回执断言恰当，没有引入恒真。** [测试文件:920](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:920) 的组合允许 `0`、正整数，拒绝 `True`、`False`、小数、负数及多行回执；空回执由前一断言拒绝。保留合法零删除符合 `finally` 覆盖写入未成功路径的事实。

3. **17 格未发现应新增计数的承重恒真断言；措辞问题见 LOW-1。** getter 门能检出“把 getter 纳入现有 try”的回归，但 HTTP 500 本身不能独立证明异常身份或所有控制路径。另有一处轻微枚举笔误：[测试文件:614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:614) 列出的 `1c/1d/1e/1f` 合计 **13 格**，包含门 1 才是 14 格；不另增缺陷计数。

4. **本轮 diff 未发现回归。** `edges.py` 无改动；三处消息只调整描述，清理断言收紧了合法回执类型。

5. **自绑存档满足本轮 SHA 绑定要求，无必补项。** 我独立核实：当前完整 HEAD、非 `_bmad-output` 工作树零改动，以及两文件“工作树 SHA256＝提交 SHA256”，均与[存档头部](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-t-edges/allgates-selfbound-20260916T010656.txt:2)一致。日志记录 **17 passed、pytest_rc=0**，以及 pyright **0 errors、81 warnings**。它未记录 pyright 调用范围，因此不扩称“全仓检查通过”。

6. **终审计数：本卡 `0 / 0 / 0 / 1`；连同指定的两条已登记卡外缺陷 `0 / 2 / 0 / 1`。**

本轮仅做只读复核及哈希重算，未修改任何文件、未运行测试、未连接数据库。

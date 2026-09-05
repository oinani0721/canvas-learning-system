# 独立复审 — X4（`CARD-TEST-isolate-lifespan-R1`）这套门，在 BLOCKER 修复之后

你是独立审查者。工作树只读：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z3-w4`

## 〇 这一轮要回答的那一个问题

第十批把 X4 **人判合入**了（commit `32c8e325`），当时两轮独立终审给出相同的
`1 BLOCKER / 8 HIGH`。那条 BLOCKER 现已由本车道修掉（见 §二）。

**请你在修复后的代码上，独立判一次：这套门现在能不能承重？**
结论会交给用户，用来对「当初人判合入」这个决定做二次确认，所以请给明确裁定，
不要只列现象。

## 一、最小读取面（**写死，请只读这些**）

```
backend/tests/support/live_port_guard.py            ← 全文（约 900 行，门的本体）
backend/tests/support/lifespan.py                   ← 全文（隔离夹具）
backend/tests/support/guard_plugin.py               ← 全文（import 期装门）
backend/tests/regression/conftest.py                ← 全文
backend/tests/conftest.py                           ← 只看装门与 session 预检那几段
backend/tests/unit/test_live_port_guard_contract.py ← 全文（契约测试）
```

⛔ **显式排除**（不要读、不要评）：
`backend/scripts/lifespan_isolation_negative_control.py`、
`backend/scripts/lifespan_isolation_guard_probes.py`、
`backend/scripts/lifespan_isolation_runtime_sha.sh`、
`backend/scripts/lifespan_isolation_*` 其余文件 —— 合计约 3744 行，属于另外两张卡的面，
读它们会把这一轮的注意力吃掉。本轮只审**门本体与它的接线**。

## 二、已裁决、不必再提的事项

以下四项已有归属，**不要再作为本轮发现列出**（除非你发现它们的定性本身是错的）：

1. **`NEO4J_TEST_URI` 端口 0 那条 BLOCKER —— 已由本车道 `CARD-W4-3a` 修**：
   判据从黑名单改成正面白名单 `ALLOWED_TEST_PORTS={7692}`，端口按 neo4j 驱动
   自己的解析链（`urlparse` → `netloc` → `Address.parse(default_port=7687)`）复算。
2. **AST 门的 5 条 HIGH（B 类）** —— 另立卡。那道门在 `scripts/` 下，已排除在读取面外。
3. **`runtime_sha.sh` 的 `BASH_ENV` 一节（C 类）** —— 另立卡，同样已排除。
4. **`live_port_guard.py` 的最终结算原子性（W4-④）** —— `os._exit(3)` 前的
   `repr`/`print`/IO 可能抛、`_FINALIZING` 检查与 `STATE.record()` 与 ledger 快照
   三者未同锁线性化。**已另立卡**，不必重复列，但如果你认为它的**定级**不对
   （例如实际上是 BLOCKER 而不是 HIGH），请说明。

## 三、请聚焦的四个问题

1. **门在哪些情形下会失效？** 在读取面之内，有没有一条路径能让 pytest 进程真的连上
   7691 / 7687 而门不抛、或抛了但进程仍以 0 退出？
   （audit hook 的四条 socket 路径、端口提取、`_FINALIZING` 之后的窗口、
   子进程、`socket` 之外的连接方式……）
2. **`is_exempt()` 的 advisory 路径**：`tests/integration` / `tests/e2e` 下的用例
   「只记不拦」，是**有意的设计**。在 BLOCKER 修复之后，这条旁路还剩多大风险面？
   具体说：现在还有什么配置或写法，能让一个 advisory 用例连上现网库？
3. **解析完备性**：门只按端口判定。`extract_port` / `port_is_trustworthy` /
   `canonical_target_port` 三者合起来，有没有哪类地址或 URI 会被判成安全而实际不是？
4. **装门时机**：门必须早于任何业务 import 生效。`guard_plugin.py` 的 import 期装门 +
   `conftest.py` 的接线，这个时序真的成立吗？有没有窗口能在装门前发起连接？

## 四、输出格式

先给**整体裁定**一句话：这套门当前的阻断级问题数量，以及你认为它能不能承重。
然后按级别（BLOCKER / HIGH / MEDIUM / LOW）列发现，每条给：位置（`文件:行`）、
一句话结论、**你据以判断的具体代码**、建议修法。
无法在只读环境下判定的，明说「未验证」并写清需要什么才能判定 —— 不要把推测写成结论。

最后请单独回答一句：**如果当初这套门没有合入主干，今天的代码值不值得合入？**
（这是给用户做二次确认用的，请直接表态。）

## 五、边界

- 只读，不修改任何文件，不运行会写盘的命令。
- 不连接 7691 / 7687 / 7692 任何数据库端口。

终审绑定 **`caf8180ebd22c75dc5087621f0a0cd64309303cd`**：**BLOCKER 0 / HIGH 1 / MEDIUM 0 / LOW 1**。三条 LOW 中，**L1、L2 可以关闭，L3 尚不能关闭**。

- **BLOCKER：无。**

- **HIGH：1 条，H1〔缺陷成立但超出本卡改动面〕。**  
  [edges.py:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/edges.py:161)：真实驱动异常仍不在本函数捕获范围内，半成功返回路径存在缺口。**当权限／约束类 `ClientError` 等穿透客户端内部处理时，即使 LanceDB 已成功，异常仍会上抛并导致 500。**  
  当前披露**达到最低要求**：明确了“不被捕获”的条件边界，也明确写出既存缺口在接通 `run_query` 后变得可达；继续保留移交，由主 session 按 D-15 裁定，不记为关闭。

- **MEDIUM：无。**

- **LOW：1 条，L3〔整改未完整〕。**  
  [test_edges_dual_write_neo4j_t5b.py:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/integration/test_edges_dual_write_neo4j_t5b.py:65) 把 advisory 推成“连接必然建立并真写”，且同文件 **`:157` 仍称 socket 门为“第二道防线”**，与新说明矛盾。**当注入失效但连接、认证或写入失败时，“必然真写”不成立；默认豁免模式下，`:157` 所称的拦截保障也不成立。**

L3 应统一为：“**默认豁免模式下，W4 只记录、不阻止连接尝试；注入失效可能导致真实客户端连接并写入 7691。**”另有两点需要限定：

- 前置身份检查负责阻止误用客户端；请求后的 `stub.calls`、sentinel 是事后证明。
- 零账表示**账本计入的受覆盖连接尝试为零**；W4 自证探针明确跳过记账，不能包括在“一次尝试都没有”里。`W4_GUARD_NO_EXEMPT=1` 时也不适用默认 advisory 结论。

**L1、L2 的关闭依据**：`edges.py:122` 与测试文件 `:47` 已撤回“未捕获 ⇒ 必然 500”的直接推论；测试文件 `:163`、`:171` 已正确区分 `urlsplit()` 失败和读取 `.port` 失败。

**关于本轮变更性质：确认是。** 排除 `_bmad-output` 后，`c2e3d533..caf8180e` 仅两份文件的注释／docstring 改动；`edges.py` 去注释 token 完全一致，两份文件去 docstring 后 AST 完全一致，未发现运行逻辑变动。

存档核对支持三门 **3 passed、真实 `rc=0`**、Pyright 新增诊断 **0**、两项负控变红；unit 全套仍为 **35 failed / 29 errors、rc=1**，但前后 64 项失败清单一致。Pyright 存档摘要匹配 `c2e3d533`；测试日志未直接记录最终 SHA，因此不宣称本轮重新实跑。MRO 存档中旧的“必然 500”推论不作为证据采用。

本轮未修改文件、未运行 pytest、未连接数据库。



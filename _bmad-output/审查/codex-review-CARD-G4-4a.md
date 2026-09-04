审查锚定 `card/x3-vaultscope@cb671e26be4312a66589efc764c2143c00398506`。结论：代码移植等价，四处补口行为正确，指定裁判和负控均无新增红；发现 5 个文证类 HIGH、1 个 LOW，按本批定义均不阻断。

## 非 PASS 项

1. **HIGH — merge-tree 冲突归因不可复现。**  
   [4a UAT:79-94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4a-显式VaultScope-2026-09-04.md:79) 声称七次均 rc=1 且冲突全在 DEBT-8 面。逐 pick 重放时，第二次还冲突 `agents.py/rag.py`，第四次冲突 `evidence-g44/rag.py/test_agentic...`；固定用 `1f249b33` 重放则 rc 为 `1,1,1,0,0,0,1`。不存在同时支持“七次全 rc=1”与“全是 DEBT-8”的常规命令序列。  
   “整树 merge-tree 不等于单提交 cherry-pick”这个判断本身正确，不影响代码等价性。当前未提交 UAT 的 `:112-128` 又同时声称“每条同底稿”及承认 `aaecf696` 两侧父提交不同，也应收窄。

2. **HIGH — OBS 注释把现有测试能力说宽了。**  
   [rag.py:327-330](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/api/v1/endpoints/rag.py:327) 点名 `test_nothrow_logging_api` 能验证 scope 包装器；实际 info 注入只覆盖 weak-concepts，[`/rag/query` 用例](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/api/v1/endpoints/test_nothrow_logging_api.py:261) 注入的是 error。四态门 [test_rag_four_state_api.py:197-217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:197) 同时命中入口与 scope，不能单独锁定 scope。  
   删除调用点 `try/except` 仍然正确；准确措辞应是“统一单层保护，并避免未来 scope 专门负控被调用点兜底掩盖”。

3. **HIGH — `mutation-run.txt` 单独不足以证明“8 条门仍活”。**  
   UAT [4-A.3:155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4a-显式VaultScope-2026-09-04.md:155) 的“证明”过宽：归档仅保存八个 `exit=1` 与结论性外部锚点，[mutation-run.txt:18-32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/审查/evidence-g44/mutation-run.txt:18)；脚本在成功 kill 时丢弃 pytest tail、失败断言及 nodeid，[g44_mutations.py:26-35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/审查/evidence-g44/g44_mutations.py:26)、[145-157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/审查/evidence-g44/g44_mutations.py:145)。  
   我们在隔离的 HEAD 归档中复跑仍为 8/8、脚本 exit=0、三文件 SHA 前后一致；M6 失败身份也单独验证，所以这是留存粒度问题，不是负控假绿。

4. **HIGH — `/rag/query` 调用方文证两端都写宽。**  
   源 UAT [24-30](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:24) 把插件零调用方扩大为“本仓库零调用方”，但仓内确有 Dredd POST hook：[dredd-hooks.js:38-40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/scripts/spec-tools/dredd-hooks.js:38)、[152-157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/scripts/spec-tools/dredd-hooks.js:152)。  
   反过来，当前未提交 UAT [307-343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4a-显式VaultScope-2026-09-04.md:307) 又称它是活 CI 消费方；唯一工作流实际带 `--method GET --names`，[api-spec-sync.yml:344-353](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/.github/workflows/api-spec-sync.yml:344)。官方说明 `--method GET` 只选 GET，`--names` 不发送请求，因此没有证明 POST hook 会执行。[Dredd CLI 文档](https://dredd.org/en/latest/usage-cli.html)  
   准确结论仍是用户已裁决的：插件零调用方成立，其他活调用方未穷举；D2 不重开。

5. **HIGH — V5 状态注释已失效。**  
   [nodes.py:417-418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:417) 仍称 B0.7 回退存在且“V5 未合”；当前 V5 已删除回退，[lancedb_client.py:765-792](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/clients/lancedb_client.py:765)。按“注释声明比事实宽”的规则定 HIGH；仅影响说明，不影响运行时。

6. **LOW — HEAD UAT 的日志计数陈旧。**  
   `HEAD:_bmad-output/验收单/UAT-CARD-G4-4a-显式VaultScope-2026-09-04.md:56` 写 `rag.py 7→7`，实际 OBS 终态为 `7→0`。判据仍通过；当前未提交草稿已修正。

## 逐项 verdict

- **PASS — 移植等价。** 七个目标提交均有正确 `-x` trailer。相对 `6a732e1b`，指定六文件中四个 blob 完全相同；仅 [rag.py:325-336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/api/v1/endpoints/rag.py:325) 与 [test_agentic_rag_vault_scope.py:536-547](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/unit/test_agentic_rag_vault_scope.py:536) 各一个授权补口。

- **PASS — 台账未被移植污染。** `git diff 1f249b33..HEAD -- <台账>` 为空，两端 blob 相同；见 [未合卡追踪台账.md:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:1)。

- **PASS — 主干前提未失效。** `resolve_vault_scope`、`current_vault_id`、配置契约均未变，[vault_scope.py:137-209](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/core/vault_scope.py:137)、[294-318](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/core/vault_scope.py:294)。`DEFAULT_TABLES` 仍是 `["canvas_nodes"]`，[lancedb_client.py:611-614](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/clients/lancedb_client.py:611)。唯一相关变化是 V5 删除 B0.7，且与当前显式解析兼容。

- **PASS — (g) xfail 声明诚实。** 唯一标记为 `xfail(strict=True)`，无 `skip`，[test_agentic_rag_vault_scope.py:536-547](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/unit/test_agentic_rag_vault_scope.py:536)。reason 只描述同 vault 跨 subject 缺口，与 [expand_neighbors:2277-2343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/clients/lancedb_client.py:2277) 相符。

- **PASS — (m) M6 不是假杀。** fixture 明建含 `b_secret` 的裸 `vault_notes`，[test_agentic_rag_vault_scope.py:356-393](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/unit/test_agentic_rag_vault_scope.py:356)；生产路径传已解析表名，[nodes.py:409-424](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/nodes.py:409)；扩展内部直接 `open_table(table_name)`，[lancedb_client.py:2314-2343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/lib/agentic_rag/clients/lancedb_client.py:2314)。等价 M6 探针实际返回 `lancedb_b_secret / B 库绝密… / neighbor_expansion`，由跨库内容断言击杀。

- **PASS — (k) OBS 运行时归一。** 模块 logger 在 [rag.py:32-35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/api/v1/endpoints/rag.py:32) 包装；scope 日志直调位于 [331-336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/api/v1/endpoints/rag.py:331)；两层故障均在 [nothrow_logging.py:124-136](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/app/core/nothrow_logging.py:124) 内捕获。scope-only sink 注入实测 HTTP 200、业务 service 已 await、fallback warning 一次。

- **PASS — stacklevel。** 既有断言 [test_nothrow_logging_api.py:443-462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/api/v1/endpoints/test_nothrow_logging_api.py:443) 通过；独立 `/rag/query` 捕获的入口与 scope 两条记录也均为 `filename="rag.py"`、`funcName="rag_query"`。

- **PASS — 证据剔除本身可复核。** 移植注 [源 UAT:3-11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/_bmad-output/验收单/UAT-CARD-G4-4-full-RAG-显式VaultScope-2026-09-01.md:3) 给出了精确源 commit；五份 judge 和三份 stderr 均能从 `6a732e1b` 读取，原数字也核对一致。缺口仅是上文 mutation 摘要粒度，不是文件剔除导致原件消失。

- **PASS — 指定裁判。** 当前复跑：裁判 1 `107 passed`，OBS `21 passed`，合跑 `128 passed`；裁判 2 `28 passed + 1 xfailed + 3 failed`，三红与 `1f249b33` 同名。隔离基线重跑为 `89 collected = 88 passed + 1` 条已登记红。测试使用局部 FastAPI 与临时 LanceDB，[API fixture:75-84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/api/v1/endpoints/test_rag_vault_scope_api.py:75)、[LanceDB fixture:303-405](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x3-vaultscope/backend/tests/unit/test_agentic_rag_vault_scope.py:303)，未启动 lifespan、未连 7691 或 live vault。

- **PASS — 七条“未证明项”边界成立。** 无一条需要在 4a 内扩面证明；subject、真库、外部调用方、非预期异常、dedup、`lancedb_client.py` 修复及三条基线红均按卡文留待相应裁决/后续卡。

状态说明：指定六个代码/测试文件相对 HEAD staged/unstaged 均干净；全工作树当前有三份未提交文档修改及两个未跟踪审查工件，因此历史 `git status 空` 不能当作当前状态。审查全程只读。方法上采用了 Canvas adversarial-audit 的 final-SHA 绑定、并行证据轨和真实入口负控准则。

阻断级 = 0



> 批次: BATCH-2026-09-11-第十四批 · 车道 T2 · 卡 CARD-G2-8 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-8.md)"`
> 审查绑定: `bb070e6f`（该轮 HEAD；本轮后有 r1 整改 commit `53eca445`，故本档**不绑**最终 HEAD）
> 会话头自证（抄 .stderr，行号如实标；.stderr 本身不入库）:
> `.stderr:2` `OpenAI Codex v0.153.3` / `.stderr:5` `model: gpt-6-astra` / `.stderr:9` `reasoning effort: ultra`

---

已绑定 `bb070e6f` 复核。**发现 2 项 HIGH、4 项 MEDIUM、1 项 LOW；未发现 BLOCKER。** 本轮未修改文件、未运行测试或连接服务，不评价真 Docker 行为。

1. **HIGH — [scripts/deploy-vault.sh:1402](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1402)**：curl 返回零，但响应为含 `"status":"ready"` 的截断 JSON，或顶层状态失败、嵌套状态就绪时，全文正则仍会记 `result=ready`，现有三类失败样本未覆盖这些输入。
2. **HIGH — [scripts/deploy-vault.sh:431](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:431)**：日志路径在初次检查后改变指向的负控路径未被覆盖，新增追加点没有紧邻复查或固定文件描述符，现有门只核检查语句存在及目标变量名。
3. **MEDIUM — [scripts/deploy-vault.sh:1332](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1332)**：健康失败或 up 失败后，`run_step` 立即退出，回滚阶段不会进入步 6 evidence，而失败门仅拼接全部 `.txt` 查找阶段行，未断言 `deploy-*.txt` 存在。
4. **MEDIUM — [scripts/deploy-vault.sh:1377](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1377)**：合法输入 `CLS_DEPLOY_LANCE_READY_TIMEOUT=1` 配合超过一秒才返回的响应，仍受固定十秒 curl 超时控制，且 ready 分支先于期限检查退出，现有门未验证耗时上限。
5. **MEDIUM — [scripts/deploy-vault.sh:1462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1462)**：CRLF／CR `.env` 中追加缺失名字会触发全文换行归一，改变 `ACTIVE_VAULT` 行的原始字节，而测试的 `read_text()` 加 `splitlines()` 比较无法识别该变化。
6. **MEDIUM — [scripts/deploy-vault.sh:432](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:432)**：阶段日志追加失败、后续 evidence 仍可写的负控路径只增加一条不含 `rc=` 的失败标记，`act_stage` 仍返回零，整轮仍可报告成功。
7. **LOW — [backend/tests/unit/test_deploy_vault_sh.py:3416](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3416)**：去重门覆盖缺键及逗号清单中的已有名字，未覆盖逗号／空格混合分隔、键存在但为空这两类输入。

作者七项自述的核对结果：

| 项目 | 结论 |
|---|---|
| 1．只拆本实例 | **健康失败分支核对通过**：兄弟 curl 确实依赖同一运行项目清单，并核验前后存活；up 非零／部分启动分支缺少同等对照。 |
| 2．Graphiti 三失败面 | **现有样本及两侧断言核对通过**：既要求 skipped，也禁止 ready，另有 ready 正控；不能覆盖第 1 条发现。 |
| 3．`--also-push` | **追加去重逻辑、写入硬化、四项计数 2→3 核对通过**；混合分隔和空值按代码可处理，但门未覆盖；逐字节不变不成立。 |
| 4．未授权 SKIP | **核对通过**：闸门在 up 前返回 SKIP，evidence 标明未进入真 activate；整轮 `rc=0` 没有改写阶段的 SKIP 状态。 |
| 5．步 1～4 未改 | **核对通过**：两 SHA 对应函数区间逐字节一致；连字符拒绝、下划线放行分别有真 harness 对照。 |
| 6．写面 | **静态记账落点核对通过**；`.env` 自带禁写判据和硬化写入，足以保护该次写入，但不等同于部署开始前整体拒绝；新增日志追加另见第 2 条。 |
| 7．Lance 取值 | **非空数值校验核对通过**：ASCII、长度及范围检查未见可造成数值溢出或无限循环的取值；空值取默认 120，实际期限执行存在第 4 条问题。 |

index journal 使用 harness 真模块计算两条路径、Lance 记录耗时与 `table_count`、新增 evidence 目录纳入凭据及 stderr 门，均**核对通过**。

存档核对：先红为 **14 failed、4 passed**；最新文件级结果为 **166 passed、9 skipped**；四段负控均记录指定断言变红，恢复后的脚本哈希与当前审查对象一致。这些是存档结果，本轮未重跑。



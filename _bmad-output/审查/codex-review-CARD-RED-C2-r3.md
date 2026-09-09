> 批次: BATCH-2026-09-07-第十三批 · 车道 U11-B · 卡 CARD-RED-C2 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-C2-r3.md)"`
> 审查绑定: `0909e935`（送审时 HEAD；本轮整改后 HEAD 已前进，见 round-4 存档）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

> ⚠️ 同前两轮：stdout 落盘 0 字节、内容走 stderr。`0 字节 ≠ 无产出` ⇒
> 从会话流取最后一个 `codex` 标记行与 `tokens used` 之间的整段逐字入库，未改一字。

---

复核 `0909e935`：**BLOCKER 无 / HIGH 1 / MEDIUM 1 / LOW 4**。复现均在内存执行，未修改文件、未连接数据库。

下表中 `M` 指完整豁免串 `/Users/Heishing/Desktop/canvas/canvas-learning-system/docker/neo4j/data:/data`。

| 级别 | file:line | 一句问题 | 一句复现思路 |
|---|---|---|---|
| HIGH | [test_story_1_7_env_config.py:120](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_1_7_env_config.py:120) | 只检查 `path[:3]`，会豁免 `volumes[0].source` 等后代字段，使获准短格式串变成新的主机路径。 | 在 `neo4j.volumes` 使用长格式 `type: bind`、`source: >-`，下一行放 `M`，再设 `target: /other`，测试本体 **PASS**；此时源路径包含末尾 `:/data`，不同于原获准源路径。 |
| MEDIUM | [test_story_1_7_env_config.py:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_1_7_env_config.py:100) | `safe_load` 的合并覆盖会消去原文路径，使位置和数量检查漏检。 | 在 `services.other` 的 `<<:` 默认映射里放 `volumes: [M]`，显式设置 `volumes: []`，按块式换行书写后实测 **PASS**；同理可使原文重复两次、计数只剩一次。 |
| LOW | [test_story_30_24_boundary.py:242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:242) | 去掉 `//` 后查子串仍不能证明参数实际参与查询，第 230 行“内联立即红”仍过宽。 | 保留四个 kwargs，将查询改成 `LIMIT 5 /* $limit */`，或把 `$limit` 放进字符串／无用表达式，全部安全断言仍 **PASS**。 |
| LOW | [test_story_30_24_boundary.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/backend/tests/unit/test_story_30_24_boundary.py:184) | 只审最后一次 `run_query` 调用，无法证明此前调用安全，这是本轮新发现的既有盲区。 | 先调用含恶意原串的查询，再调用完整参数化查询，实测调用次数为 2，而全部断言 **PASS**。 |
| LOW | [negctl-compose-exemption-r2-20260909T141039.txt:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/_bmad-output/审查/evidence-red-c2/negctl-compose-exemption-r2-20260909T141039.txt:13) | ④⑤声称移到另一 service，实际失败位置却是顶层 `volumes.other.volumes`，末尾仅更正②仍不充分。 | 对照第 12–15 行标题与异常路径，可见没有落在 `services.other.volumes`；我另行构造真实兄弟 service，确认确实会红。 |
| LOW | [c2-verdicts.md:219](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c/_bmad-output/审查/evidence-red-c2/c2-verdicts.md:219) | 存档没有给出所声称的空 diff 证明，三份证据实际标记 `4449e292`。 | 对照 gates 第 5–15 行，展示的是 `cfd299f3 → 4449e292` 非空 diff；本次独立核实 `4449e292 → 0909e935` 排除证据目录后确实为空，故实际绑定已闭合，仅保留文档问题。 |

其余问题的核对结果：

- **两轴确实存在同时放行的输入**：HIGH 项会改变实际挂载源；MEDIUM 项仅漏检被覆盖的原文路径，没有新增生效挂载。
- 已测普通 anchor/alias 跨 service、合并继承跨 service、列表 alias 重复均被拦截；多文档抛 `ComposerError`，不会放行。流式映射及 `>-` 可以通过；普通双引号包裹豁免串会被内容轴拒绝。
- **新增绑定参数会红是固定四参数契约的预期行为**，但这种红不能直接解释为安全回归。
- 两份负控包含预期断言的失败信息，没有发现“无关异常被当作成功负控”的证据。安全负控记录了恢复身份为 `True`，但缺少运行脚本，无法独立确认 `finally` 和完整还原过程，也没有依据认定存在残留。
- §七对调用发起顺序、替身参数边界及 SHA 计数的收窄措辞足够；对应依据表不在许可读取面，未确认其同步情况。
- Git 树元数据确认：`5139428d → 0909e935` 排除证据目录后仅改 **23 个测试文件，`backend/app/**` 零改动**。本轮增量未修改 skip、未删除用例；**全卡累计 skip 状态及 U11-A／R 族逐用例归属，当前读取面不足以独立确认**。

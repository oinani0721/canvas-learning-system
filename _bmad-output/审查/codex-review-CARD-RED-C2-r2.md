> 批次: BATCH-2026-09-07-第十三批 · 车道 U11-B · 卡 CARD-RED-C2 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-C2-r2.md)"`
> 审查绑定: `cfd299f3`（送审时 HEAD；本轮整改后 HEAD 已前进，见 round-3 存档）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

> ⚠️ 同 round-1：本机 `codex-cli 0.153.3` 本次调用 **stdout 落盘 0 字节**，全部内容走 stderr。
> `0 字节 ≠ 无产出` ⇒ 按实情从会话流取出最终答复段逐字入库（取最后一个 `codex` 标记行
> 与 `tokens used` 之间的整段），未改一字。

---

整改**部分成立**：compose 的 HIGH 尚未关闭，收工证据仍未绑定 `cfd299f3`。

BLOCKER：无。

| 级别 | file:line | 问题 | 复现思路 |
|---|---|---|---|
| HIGH | `backend/tests/unit/test_story_1_7_env_config.py:77` | service 解析遇到合法的注释或引号写法时不更新归属，会沿用前一个 `neo4j`。 | 将获准挂载从 `neo4j` 移到随后 `other: # comment` 或 `"other":` 的 `volumes`，保持只出现一次，三段判据仍 PASS。 |
| MEDIUM | `backend/tests/unit/test_story_1_7_env_config.py:88` | 没有验证豁免行位于 `services.neo4j.volumes`，豁免范围超出了三条 bind-mount 的依据。 | 将获准行移入 `neo4j.command` 列表，三个断言仍 PASS。 |
| MEDIUM | `_bmad-output/审查/evidence-red-c2/unit-after-20260909T135407.txt:1` | SHA 绑定整改未闭合：三份证据全部写的是 `c6278d6e`。 | 对照 `files-23-20260909T135910.txt:1`、`gates-20260909T135944.txt:2`；许可材料未提供与 `cfd299f3` 的代码树等价证明。 |
| LOW | `backend/tests/unit/test_story_30_24_boundary.py:228` | 占位符子串检查不能证明实际参数化，且删除 kwarg 会缩小检查集合。 | `LIMIT 5 // $limit` 保留 kwargs，或 `LIMIT 5` 同时删除 `limit` kwarg，两种输入均通过；§四“任何值不得内联”的声明仍过宽。 |
| LOW | `backend/tests/unit/test_story_38_1_review_fixes.py:103` | `mock_calls` 证明协程调用顺序，不能证明初始化先完成等待。 | `pending = client.initialize(); await client.index_canvas(); await pending`：次数与顺序断言全部通过，实际执行却是索引→初始化。 |
| LOW | `_bmad-output/审查/evidence-red-c2/c2-verdicts.md:66` | “生产增加必传形参即红”仍过宽；替身只能发现调用点传入其不接受的参数。 | 只给真实 `call_agent` 增加必传形参、保持调用点不变；真实函数被替换后，该签名变化不会被这些断言发现。 |
| LOW | `_bmad-output/审查/evidence-red-c2/c2-verdicts.md:202` | “全文 SHA 去重 27 个减 2”的复核方法已过期，虽然依据 SHA 确实仍是 25 个。 | 当前全文去重为 30 个，新增了三个审查/证据 SHA；应区分全文计数与依据栏计数。 |
| LOW | `backend/tests/unit/test_story_30_24_boundary.py:199` | 注释仍反称“硬编码会在物理化规则变化时静默通过”，与已登记的同源盲区相矛盾。 | 让 helper 返回不同结果：独立字面量期望会红，同 helper 求出的期望才会同步变化。 |

确认成立的部分：

- **第 4 条反向锚有效**：指定校验器片段改成只看 DEBUG 后不再抛错，新增 `pytest.raises` 会红。
- **`none_score` 整串相等有效**：期望与生产拼装一致；仅返回 `"N/A"`、遗漏标题或改变空格都会红，没有同源求值自证。
- 两条初始化次数锚有效；三类新增断言均非恒真，但顺序与参数化检查仍有上述漏过面。
- 同源盲区已在依据表 #43 和 §六充分登记，属于**已接受、未修的 MEDIUM**，不能视为风险消除。

完整指定 diff 仅涉及 **23 个测试文件**；`backend/app/**`、`_archive/**` 零改动，未新增或删改 skip，新增 xfail 均为 `strict=True`，未删用例，两条重命名已有登记。已知四条外来红的测试体未改；许可材料不足以独立确认 U11-A 全部用例的归属与零触碰。

复核仅使用指定读取面及纯内存探针，未修改文件、未启动项目测试或连接数据库。

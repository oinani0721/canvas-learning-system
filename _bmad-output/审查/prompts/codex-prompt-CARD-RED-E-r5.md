你是独立代码审查者。请对以下这一张卡的改动做对抗性审查。仓库根目录 = `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`（只读）。

# 一 背景

本卡 `CARD-RED-E`（批次 BATCH-2026-09-07-第十三批）修的是一条已存在 7 个月的生产静默降级。

事实链（作者已实测，请独立核对）：

- `.claude/agents/` 目录里只剩 11 份 agent 模板，而 `backend/tests/unit/test_agent_templates_smoke.py` 的 `EXPECTED_AGENT_TEMPLATES` 期望 18 份。
- 缺的 7 份分两类：6 份在 commit `f425d7b7`（2026-03-30，message "ralph-loop: iteration 0"）被删；第 7 份 `hint-generation.md` 在**仓库全部历史里从未存在过**（`git log --all --diff-filter=A` 空、四棵候选树 `ls-tree` 全 0 命中）。
- 生产影响：`backend/app/services/verification_service.py:3032` 调 `call_agent(AgentType.HINT_GENERATION, ...)`；模板不存在 → `gemini_client.load_prompt_template` 抛 `FileNotFoundError` → `agent_service.py:2816-2833` 把它转成 `AgentResult(success=False)` → `verification_service.py:3035` 条件为假 → `:3060-3067` 落到写死的兜底提示。也就是说「AI 分级提示」这个功能自 2026-02-07 调用点上线以来一直没有真正跑过，只是每次都返回同一句静态文案，且不抛错。

用户裁定 D-19「恢复 + 门」、D-22 门形态取纯 pytest 分支（本树的 `.claude/hooks/pretool-guard.js` 虽然存在，但 `.claude/settings.json` 的 `hooks` 是空对象、未注册任何 PreToolUse，等价于未接线，所以本卡不动 hook）。

本卡改动面只有三处：`.claude/agents/**`（7 份新增文件）、`backend/app/services/agent_service.py`（只加一行）、`backend/tests/unit/test_agent_templates_smoke.py`。

两张「期望表」的关系是本卡的核心概念，请务必先理解：

- **smoke 表** = `EXPECTED_AGENT_TEMPLATES`，18 项，管的是「目录里必须有这些文件」，作用是防止再次被批量删除。
- **health 表** = `agent_service.py:5711-5725` 的 `expected_templates`，本卡由 12 项改为 13 项，管的是 `/agents/health` 端点报不报 degraded，只应盯 `AgentType` 里真会被 `call_agent` 加载的模板。
- 两表相差 5 项（`graphiti-memory-agent` / `iteration-validator` / `parallel-dev-orchestrator` / `planning-orchestrator` / `review-board-agent-selector`），原因是这 5 份不是 `AgentType` 成员，生产从不加载它们，但它们仍须留在目录里作为删除告警面。

# 一-bis round-5 说明：round-4 之后改了什么（本轮预期是末轮）

round-4（绑 `798b39b1`）判 BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 1。作者已处置，产生新 commit `2b9d44d8`。本轮请绑 **当前 HEAD** 重审。

**本轮改动是纯文档，逻辑零改动，且有严格证明**：剥去全部 docstring 后，工作树与 `798b39b1` 的 `ast.dump` 逐字节相同（存档 `evidence-red-e/r4fix-docstring-only-20260910T010000.txt`，输出 `True`）。请优先用 `git diff 798b39b1 HEAD -- backend/` 确认这一点。

round-4 LOW-1 的三条说明性问题及处置：

1. **因果搭错（已改写）**：原 docstring 写「hint-generation 从未存在，所以 probe *could never be clean*」。实况是旧 health 表 12 项里**没有** hint-generation，它的缺失对旧 probe 不可见；probe 恒 `degraded` 的真实原因是表里的 `canvas-orchestrator` 不在盘。且 `:5771-5774` 优先判 `unhealthy`。现改写为区分两类失败，并点明「表里看不见」才是它能长期存在的原因。
2. **过宽（已改写）**：原写覆盖失效会造成「空集比较、断言 vacuous」。实况是 `probe_names == names` 比的是完整列表，`[] != 13 项` 仍会红；前置断言改善的是**错误定位**。现改写为 "for diagnosis, not for correctness"。
3. **自查推断错误（已在验收单更正，存档不改）**：原自查称「probe 改为路径不存在时提前 return 会被抓住」——`tmp_path` 是**已存在**的空目录，该分支不触发。

round-4 另指出的两条覆盖边界，作者接受、未改代码、已记入验收单「本卡未证明什么」：门绑定的是 probe **报告的成员名**而非**每个成员对应的文件路径**；`monkeypatch` 未发现实际隔离缺陷但不等于任意并发环境无冲突。

请复核：
(a) `git diff 798b39b1 HEAD` 是否确实只含 docstring 与 `_bmad-output`，有无夹带逻辑改动；
(b) 改写后的三处说明是否**这次准确了**，有没有引入新的失实或新的过宽；
(c) 站在本卡整体（四个 commit：`eed7a44c` / `f7729fdb` / `49994317` / `798b39b1` / `2b9d44d8`）上，是否还有**尚未被指出过**的 BLOCKER 或 HIGH；
(d) 作者在验收单里的能力声明是否已经收窄到与证据相符 —— 这是本卡连续四轮的复发问题，请直接判定「已收窄 / 仍偏宽」。

# 二 作者自述，请独立核对

1. **6 份恢复逐字节等于 `f425d7b7^`**：作者用 `git show f425d7b7^:.claude/agents/<n>.md > <同路径>` 逐份写盘，并对每份做了 `shasum -a 256` 双侧比对与 `wc -c` 与勘探字节数（104719 / 5584 / 13690 / 13392 / 16492 / 7579）核对，声称 6 份全部 OK、内容一字未改（其中 3 份没有 YAML frontmatter，作者故意保持原样未补）。存档：`_bmad-output/审查/evidence-red-e/restore-sha-20260909T000001.txt`。
2. **`hint-generation.md` 是新作，不是恢复**；其契约取自两处生产代码：消费方 `verification_service.py:3036` 读 `result.data["hint_text"]`、`:3040` 读 `result.data["hint_level"]`；解析器 `gemini_client.py:147-206`。作者声称新模板能被生产解析器 `GeminiClient.load_prompt_template("hint-generation")` 解析出 `name == "hint-generation"`，且 `output_format` 非空、能 `json.loads`、同时含 `hint_text` 与 `hint_level` 两键。存档：`evidence-red-e/template-parse-20260909T000001.txt`。
3. **假绿修**：`test_agent_template_not_empty` 原本是 `if filepath.exists():` 包住断言，文件不存在时零断言通过——开工基线里 7 个不存在的模板在这条测试上全部报 PASSED，而同一批文件在 `test_agent_template_exists` 上报 FAILED。作者改成先无条件 `assert filepath.exists()` 再断非空。存档：`evidence-red-e/smoke-open-20260909T000001.txt`。
4. **阈值与两表对齐**：`test_minimum_template_count` 的阈值由 `>= 17` 改为 `>= 18`；health 表由 12 项改为 13 项（新增 `"hint-generation"`）。作者另加了两条测试把「两表为什么不相等」写成可执行断言：`test_health_expected_templates_equals_loadable_agent_types`（用 `ast` 从 `agent_service.__file__` 里取出 `expected_templates` 字面量，与 `AgentType` 去掉两个别名后的值集比较）、`test_smoke_table_minus_health_table_is_the_tripwire_only_set`（断言两表差集恰是上述 5 项，且反向差集为空）。
5. **两个对照输入各自让「指定的那条」用例变红**（判据是指定用例必红，不是「只有它红」）：对照输入 A 把 `graphiti-memory-agent.md` 清空 → **恰 1 条红**且正是 `test_agent_template_not_empty[graphiti-memory-agent.md]`；对照输入 B 把 `parallel-dev-orchestrator.md` 移到树外 → **4 条红**（存在性 / 非空 / 缺失汇总 / 数量），其中承重的 `test_minimum_template_count` 红且消息含 `found 17`，另 3 条是同一次删除的必然连带。两次还原后 sha 与还原前一致。⚠️ 前几轮 prompt 此处写成「各自只让指定用例变红」，与存档不符，已更正。存档：`evidence-red-e/negctl-a-*.txt`、`negctl-b-*.txt`。
6. **入库**：仓根 `.gitignore:44` 有 `.claude/*`，所以 7 份新文件必须 `git add -f` 才能进版本控制；作者用 `git ls-files .claude/agents | wc -l == 18` 作为判据（而不是 `git check-ignore`）。
7. **未改的东西**：`agent_service.py` 只加了一行；该文件的 8 条既有 pyright 报错作者一条未修（属另一张卡）；`backend/tests/api/v1/endpoints/test_agents_health.py` 未改（其 mock 内硬编码的 12 项期望表与本卡改成 13 的生产表已经脱节，但因为是 mock 所以测试照绿——作者把这条列为移交项而非本卡修复项）。

# 三 请按重要性回答的问题

1. 新模板的 `## Output Format` 段，是否真的会被生产解析器读成一个含 `hint_text` 与 `hint_level` 的结构？有没有可能解析"成功"但字段名或层级与 `verification_service.py:3036/:3040` 实际读取的路径不一致？注意消费方读的是 `result.data`，而 `result` 是 `agent_service.py:2449-2470` 把模型返回的 JSON 串解析后 `update` 进去的——请检查模板里对输出格式的要求与这条链路是否真的对得上。
2. 阈值改成 `>= 18` 之后，是否仍存在"删掉一份模板但测试还是绿"的余量？请特别考虑：`test_minimum_template_count` 数的是 `_AGENTS_DIR.glob("*.md")`（目录里所有 .md，不是期望名单），如果有人删掉一份期望模板同时新增一份无关 .md 会怎样。
3. 那两条新增的两表差集断言，在 `AgentType` 未来增删成员时会给出有帮助的失败信息，还是会给出误导性的信息？用 `ast` 抓 `expected_templates` 这个变量名是否可靠——变量改名、被移到别处、或同名变量在文件里出现第二次时，这两条断言会红还是会静默失效？
4. 除了 `git add -f`，还有什么路径会让这 7 份文件重新掉出版本控制或被误删？`.gitignore:44` 的规则对已跟踪文件的实际效力是什么？
5. 只在 health 表加一项 `"hint-generation"`，是否可能改变 `/agents/health` 端点的既有语义（例如让一个原本 healthy 的部署变成 degraded，或反之）？请看 `agent_service.py:5726-5735` 的分桶与 `:5768-5776` 的状态判定。

# 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 四档分级，每条给出：

- 一句话结论
- `file:line` 定位
- 你据以判断的依据（引用你实际读到的代码或存档内容，不要凭印象）

若某一档没有条目，明确写「该档 0 条」。最后给一段总评，说明本卡的门是否真的锁住了它声称锁住的东西。

# 五 边界

- 不评 `backend/tests/unit/conftest.py` 的改动（属同车道上一张卡 `CARD-HYGIENE-conftest`，已单独审过）。
- 不评 `backend/tests/conftest.py` / `tests/support/**` 的 Neo4j 端口门（属另一条车道）。
- 不评 `agent_service.py` 的 8 条既有 pyright 报错（属另一张卡，本卡按纪律不得顺手修）。
- 不评 `_archive/` 下的任何内容。
- 不评 `backend/tests/api/v1/endpoints/test_agents_health.py` 该不该在本卡里改——它不在本卡地盘，作者已列为移交项；但如果你认为「不改它」会导致本卡的某条结论不成立，请指出。

# 六 最小读取面（请只读这些）

- 本卡改动全文：在仓库根执行 `git diff 0465a35c HEAD -- . ':(exclude)_bmad-output'`（五个 commit：`eed7a44c` 主体 + `f7729fdb` r1 + `49994317` r2 + `798b39b1` r3 + `2b9d44d8` r4；`git diff 798b39b1 HEAD` 可单看本轮整改）
- `.claude/agents/hint-generation.md` 全文
- `backend/tests/unit/test_agent_templates_smoke.py` 全文
- `backend/app/services/agent_service.py` 的 `:2440-2480`、`:2500-2520`、`:2810-2835`、`:5705-5780`
- `backend/app/services/verification_service.py` 的 `:3000-3070`
- `backend/app/clients/gemini_client.py` 的 `:147-236`
- `_bmad-output/审查/evidence-red-e/` 下的 `.txt` 存档

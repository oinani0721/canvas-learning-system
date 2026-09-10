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

# 一-bis round-2 说明：round-1 之后改了什么

round-1（绑 `eed7a44c`）判 BLOCKER 0 / HIGH 0，MEDIUM 1 条 + LOW 2 条。作者已全部处置，产生新 commit `f7729fdb`。本轮请绑 **当前 HEAD**（`git rev-parse HEAD`）重审。

round-1 提出并已整改的四点：

1. **MEDIUM-1（门缺口）**：`_health_expected_templates` 原先只扫 `expected_templates = [...]` 这种 list 字面量赋值，因此追加一句 `expected_templates = expected_templates[:-1]` 时，health 真正迭代的表变成 12 项缺 `hint-generation`，而提取器仍返回原 13 项，两条集合断言照绿。
   现改为**两段检查**：先用 `ast.Store` 统计该名字的**全部绑定**（覆盖 Assign / AugAssign / AnnAssign / for-target / with-as / walrus），数量 `!= 1` 即失败并报出所有绑定行号；再取唯一的 list 字面量，取不到也失败。
   作者补做了对照输入 C 实证：注入那一行后得 `2 failed`，消息为 `` `expected_templates` is bound 2 time(s) … at line(s) [5711, 5726] ``；还原后 `agent_service.py` 与 HEAD 逐字节相同、48 passed、ruff format/check 全绿。存档 `evidence-red-e/negctl-c-*.txt`。
2. **LOW-1a**：差集失败消息原用对称差 `^`，会把「已正式加入 AgentType 因而不再 smoke-only」的模板误称为 `unexpected smoke-only`。现改为分方向报「newly smoke-only」与「no longer smoke-only」。
3. **LOW-1b**：0 绑定与 2+ 绑定现在分开解释，不再一律说成 "renamed or removed"。
4. **LOW-2**：作者更正了「两个对照输入各只让指定用例变红」这一过宽表述（B 实际 4 failed），判据本身不变。

round-1 另有两条被作者接受并补记入验收单「本卡未证明什么」，未改代码：`git rm --cached` 之类只动 index 的路径不受 pytest 门保护；`exists()` 分桶不识别「非空但不可解析」的模板。

请特别复核：**上述整改本身是否引入新的缺口**，尤其是 (a) `ast.Store` 计数是否真能覆盖它声称覆盖的全部绑定形式，(b) 「恰好 1 次绑定」这个约束会不会在合理的生产重构下变成噪声红，(c) 分方向的失败消息是否在两个方向上都说得准。

# 二 作者自述，请独立核对

1. **6 份恢复逐字节等于 `f425d7b7^`**：作者用 `git show f425d7b7^:.claude/agents/<n>.md > <同路径>` 逐份写盘，并对每份做了 `shasum -a 256` 双侧比对与 `wc -c` 与勘探字节数（104719 / 5584 / 13690 / 13392 / 16492 / 7579）核对，声称 6 份全部 OK、内容一字未改（其中 3 份没有 YAML frontmatter，作者故意保持原样未补）。存档：`_bmad-output/审查/evidence-red-e/restore-sha-20260909T000001.txt`。
2. **`hint-generation.md` 是新作，不是恢复**；其契约取自两处生产代码：消费方 `verification_service.py:3036` 读 `result.data["hint_text"]`、`:3040` 读 `result.data["hint_level"]`；解析器 `gemini_client.py:147-206`。作者声称新模板能被生产解析器 `GeminiClient.load_prompt_template("hint-generation")` 解析出 `name == "hint-generation"`，且 `output_format` 非空、能 `json.loads`、同时含 `hint_text` 与 `hint_level` 两键。存档：`evidence-red-e/template-parse-20260909T000001.txt`。
3. **假绿修**：`test_agent_template_not_empty` 原本是 `if filepath.exists():` 包住断言，文件不存在时零断言通过——开工基线里 7 个不存在的模板在这条测试上全部报 PASSED，而同一批文件在 `test_agent_template_exists` 上报 FAILED。作者改成先无条件 `assert filepath.exists()` 再断非空。存档：`evidence-red-e/smoke-open-20260909T000001.txt`。
4. **阈值与两表对齐**：`test_minimum_template_count` 的阈值由 `>= 17` 改为 `>= 18`；health 表由 12 项改为 13 项（新增 `"hint-generation"`）。作者另加了两条测试把「两表为什么不相等」写成可执行断言：`test_health_expected_templates_equals_loadable_agent_types`（用 `ast` 从 `agent_service.__file__` 里取出 `expected_templates` 字面量，与 `AgentType` 去掉两个别名后的值集比较）、`test_smoke_table_minus_health_table_is_the_tripwire_only_set`（断言两表差集恰是上述 5 项，且反向差集为空）。
5. **两个对照输入各自只让指定用例变红**：对照输入 A 把 `graphiti-memory-agent.md` 清空 → 恰 1 条红且正是 `test_agent_template_not_empty[graphiti-memory-agent.md]`；对照输入 B 把 `parallel-dev-orchestrator.md` 移到树外 → `test_minimum_template_count` 红且消息含 `found 17`。两次还原后 sha 与还原前一致。存档：`evidence-red-e/negctl-a-*.txt`、`negctl-b-*.txt`。
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

- 本卡改动全文：在仓库根执行 `git diff 0465a35c HEAD -- . ':(exclude)_bmad-output'`（两个 commit：`eed7a44c` 主体 + `f7729fdb` round-1 整改；`git diff eed7a44c HEAD` 可单看整改部分）
- `.claude/agents/hint-generation.md` 全文
- `backend/tests/unit/test_agent_templates_smoke.py` 全文
- `backend/app/services/agent_service.py` 的 `:2440-2480`、`:2500-2520`、`:2810-2835`、`:5705-5780`
- `backend/app/services/verification_service.py` 的 `:3000-3070`
- `backend/app/clients/gemini_client.py` 的 `:147-236`
- `_bmad-output/审查/evidence-red-e/` 下的 `.txt` 存档

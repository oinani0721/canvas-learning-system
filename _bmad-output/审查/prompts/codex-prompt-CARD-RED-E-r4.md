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

# 一-bis round-4 说明：round-3 之后改了什么

round-3（绑 `49994317`）判 BLOCKER 0 / HIGH 0 / LOW 0，MEDIUM 1 条。作者已处置，产生新 commit `798b39b1`。本轮请绑 **当前 HEAD** 重审。

**round-3 M-1 与整改**：round-2 的运行期用例三条断言全是**数量**（`total == len(names)` / `missing == []` / `available == len(names)`）。在表定义后注入 `expected_templates[-1] = "graphiti-memory-agent"` 时，静态名单仍是 13 项含 `hint-generation`，运行期也是 13 项但已不含它，三条断言全绿。作者注释里那句 "any such edit changes the length" 范围过宽。

整改按 round-3 给出的方向做：把 `settings.AGENT_PROMPT_PATH` 用 `monkeypatch` 临时指向 pytest 的空 `tmp_path`，于是每一项都落进 `missing`，probe 把自己的**完整名单按顺序**原样返回。新增 `test_health_probe_watches_exactly_the_names_this_gate_reads`：逐项比对静态名单、查重、断言 `available == 0`，并在 probe 运行**之前**断言覆盖已生效（防这条用例自己退化成读真实目录后的空集比较）。原用例保留并改名 `test_health_probe_reports_no_missing_template`，守生产面。

作者补做对照输入 D/E/F 共五组，全部实证只让该用例变红：`remove(...)`、`[:] = ...`、`[-1] = "graphiti-memory-agent"`、`[-1] = "scoring-agent"`、以及让 `AGENT_PROMPT_PATH` 覆盖失效。

**作者主动上报的两起自身事故**（细节在验收单，本轮请只判它们是否影响你对代码的判断）：
1. round-1 存档曾被一条 BSD sed 不兼容的命令清空正文，随后自 codex session 记录还原，并做了字节账与特征串双重核对。该存档非原始落盘产物，首部已标注。
2. round-3 的对照输入 F 变异的是测试文件本身，而当轮改动尚未提交，还原源却用了 `git show HEAD:`，把整轮改动清掉；随后重写并以**行为等价**（五组注入全部复跑）而非 sha 作为判据。同窗口的一次后台 `tests/unit` 全跑测的是损坏中间态，已改名 `VOID-` 并附作废声明。

请特别复核：
(a) 新的身份绑定用例是否真的把「probe 实际迭代的成员」绑住了，还剩哪些改动能同时骗过它与静态断言；
(b) 用 `monkeypatch` 改写全局 `settings` 属性来做这件事，是否引入测试隔离、顺序依赖或与其他读该设置的测试冲突的风险；
(c) 「空目录 ⇒ `missing` 即完整名单」这个推断依赖 probe 的哪些实现细节，这些细节若变化，用例会红（好）还是会静默失效（坏）；
(d) 作者在验收单里对这道门的能力声明是否仍比证据宽 —— 这是本卡连续三轮的复发问题；
(e) 事故 2 的重写是否可能遗漏了丢失前存在的内容（作者只以行为等价复核，未保留丢失前副本）。

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

- 本卡改动全文：在仓库根执行 `git diff 0465a35c HEAD -- . ':(exclude)_bmad-output'`（四个 commit：`eed7a44c` 主体 + `f7729fdb` r1 整改 + `49994317` r2 整改 + `798b39b1` r3 整改；`git diff 49994317 HEAD` 可单看本轮整改）
- `.claude/agents/hint-generation.md` 全文
- `backend/tests/unit/test_agent_templates_smoke.py` 全文
- `backend/app/services/agent_service.py` 的 `:2440-2480`、`:2500-2520`、`:2810-2835`、`:5705-5780`
- `backend/app/services/verification_service.py` 的 `:3000-3070`
- `backend/app/clients/gemini_client.py` 的 `:147-236`
- `_bmad-output/审查/evidence-red-e/` 下的 `.txt` 存档

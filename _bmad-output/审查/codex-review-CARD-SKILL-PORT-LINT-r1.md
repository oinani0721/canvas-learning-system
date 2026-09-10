> 批次: BATCH-2026-09-07-第十三批 · 车道 U4 · 卡 CARD-SKILL-PORT-LINT round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT.md)"`
> 审查绑定: `9303201a..ae6a68f3`（审时 HEAD = `ae6a68f3`；本轮后已按 HIGH/MEDIUM 整改，round-2 另绑新 HEAD）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: …/worktrees/card-u4-hosts` / `model: gpt-6-astra` · `reasoning effort: ultra` · `sandbox: read-only`

---

复核绑定 `9303201a → ae6a68f34be769155a5d26e09b9036e6ca0cad0b`，确认范围内仅一个提交。**建议修改后复核：发现 1 项 HIGH、1 项 MEDIUM 缺陷，另有一项计数覆盖限制。**

- **BLOCKER：未发现。**
- **HIGH — [test_skill_portability_lint.py:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:269)**：新增 `/tmp/cls-exam/../x` 时，两个子串各计一次，`bare_tmp=0`，尽管路径已越出命名空间，层 2 仍绿。当前是**固定子串放行**，没有检查后续路径段；现有负控只覆盖进入命名空间前的 `..`。应补充此反例及路径段检查。
- **MEDIUM — [test_skill_portability_lint.py:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:419)**：U6 新增脚本并按注释登记进 `U6_SCRIPTS_BASELINE`，即使三项全为零，仍被“键集必须恰好两份”拦住。已在内存复现。可改为“原两份必须存在＋新增条目属于 U6 规定目录”，保留层 3 的文件集合精确相等；未登记的新脚本仍立即红。
- **MEDIUM，覆盖限制 — [test_skill_portability_lint.py:348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:348)、[:375](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:375)**：同文件同指标减少一个旧命中、增加一个新命中时，总数相等而保持绿。例如将旧裸路径整改为命名空间路径，同时新增另一个裸路径。实现符合“精确计数基线”，但不能保证逐个命中的“新增即红”；若要求后者，需要登记命中的稳定上下文或另加差异检查。
- **LOW：未发现独立缺陷。**

你列出的形态，直接执行本文件计数函数得到：

| 输入 | 对应裸值增量 | 结果 |
|---|---:|---|
| `${X:-8011}` | 1 | 红 |
| `/tmp/cls-exam` | 1 | 红 |
| `/tmp/a/../cls-exam/` | 1 | 红 |
| `/tmp/cls-exam/../x` | **0** | **漏拦** |
| `/tmp/cls-exam/x.json` | 0 | 放行 |

反向也存在合理形态被拒：`${CLS_BACKEND_URL:-http://127.0.0.1:8011}` 仍有环境变量覆盖能力，但被计入裸值；`mkdir -p /tmp/cls-exam` 也会红。这符合作者选定的严格字面规则，不能据此宣称这些形态不可移植。

另外，`${X:-http://localhost:8011}` 同样放行；甚至普通字符串中的 `:-http://localhost:8011` 也放行。当前没有验证变量名或 shell 参数展开结构。

其余问题逐项结论如下：

1. **档 B 退回：未发现应立即改写的依据。**  
   `python3 scripts/x.py` 的相对文件参数按执行进程的 cwd 解析；SKILL.md 所在目录本身不会改变这个规则。但限定材料无法确认 Claude Code 是否主动切换目录或改写命令，因此也不能断言它必在 vault 根执行。解锁证据应来自真实 skill 调用：记录宿主版本、调用方式、同一次 Bash 中的 `pwd`、实际命令及脚本解析后的绝对路径，并至少比较从 vault 根与子目录启动的情况。单次 `pwd` 只证明一次运行。frontmatter、工具名等行为面暂缓修改也合理。

2. **旧事件路径保留：未发现遗漏的独立硬编码钉点。**  
   backend 字面量搜索除作者列出的四处，还命中 `test_learning_events_schema_contract.py:1014` 的匹配数量断言、`:1016` 的测试临时文件名，以及新 lint 的说明文字；前两处属于同一测试链，没有发现另一个独立 `/tmp/…` 替换点。注意 `test_g3_3_cas.py:49` 命中行本身是筛选条件，单凭这些匹配行不能核实相邻断言的模块级位置。  
   `/tmp/exam-candidates.json` 的“测试零引用”若指文本已不准确：新测试 `:179` 的注释引用了它；限定扫描中**未发现其它测试执行引用或生产、hooks、scripts 消费者**。字面量搜索不能穷尽动态拼接出的文件名。

3. **U5-B：并非 rebase 必红。**  
   只有计数或其它受检结构变化才红，修改正文但指标不变可以继续绿。单列常量有助于审阅，足够表达维护入口；它不能替代对基线增减原因的复核。后续应在包含本卡的候选提交上重跑门，并逐项解释基线变化。

4. **U6：零基线本身未发现问题，现有交接不够。**  
   现有两份脚本可以修改功能并继续保持三项零命中。注释和手册不能解决上述 `:419` 的确定冲突。修正那条额外集合断言后，保留“文件集合精确相等＋零计数”即可，无须给予计数余量。

5. **负控归因：未发现被其它层误打红的情况。**  
   三层确实使用精确相等；收工证据的 **9×7＝63 项**与正文基线常量一致。新增脚本负控实际执行两次：未登记时验证文件集合红，登记零基线后验证计数红，职责隔离成立；并非一次调用同时返回两条。当前缺少“减少”方向负控，但比较运算本身确实会拦减少。

6. **`mkdir` 偏离：成立，数字自洽。**  
   [SKILL.md:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/canvas-vault/.claude/skills/start-exam-board/SKILL.md:188) 在 Write 前建目录；`:198–199` 是读取，`:236` 删除。把建目录放到读侧无法保障此前的 Write。新计数为 `:188` 两次、`:198` 一次、`:577` 一次命名空间，加上 `:430/:435` 两次旧路径，即 **6−4＝2**；多出的两次分别来自 mkdir 和变更记录。

本次未修改文件、未联网或连接数据库，也未运行会复制并读取禁止正文的 pytest。三份指定未改文件在提交区间内 diff 为空；两份 collect 摘要均为 **226 collected**，只支持收集数一致，不能证明测试执行通过。



> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t7-skills · 卡 CARD-AILINKED-4TH-WRITER round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-AILINKED-4TH-WRITER-r3.md)"`
> 审查绑定: `12f85104`（该轮送审时的 HEAD；round-4 绑最终 HEAD）
> 会话头自证（抄 .stderr 对应行，stderr 本身不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: gpt-6-astra` / `L9: reasoning effort: ultra`

---

本轮结论：**B0 / H0 / M0 / L0，round-2 的 UTF-8 问题已闭合。** 审查绑定 `12f851043287139ca1ab30f170b4de02ec4e51a7`；结束时 HEAD 未变，五个受审文件均与该提交逐字节一致。

- **BLOCKER：无**
- **HIGH：无**
- **MEDIUM：无**
- **LOW：无**

逐项复核如下：

| 复核项 | 结论与定位 |
|---|---|
| UTF-8 坏行隔离 | **通过。** [SKILL.md:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:310) 按物理 LF 切 bytes，严格解码和解析均在行级 `try` 内；坏行后面的合法记录仍能参与查重。 |
| 空白行、空账本 | **通过。** `bytes.strip()` 跳过的纯 ASCII 空白不可能构成字典查重证据；其他空白在解析失败后逐行跳过。空 `raw` 产生的空项被跳过，`:339` 的条件不会补 LF。 |
| ⓪ parsed-field 相等 | **通过。** [SKILL.md:332](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:332) 只比较顶层 `event_id`，其他字段值恰等于 evid 不会误判。 |
| ① fd 生命周期、② LF 守卫 | **通过。** [SKILL.md:278](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:278) 仅打开一次账本；读、补 LF、追加使用同一 fd，直到 `:351` 的 `close` 才释放锁，无隐式重开路径。 |
| ③ 形态门 | **通过。** [SKILL.md:235](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/ai-linked-doc/SKILL.md:235) 禁止码点集与校验器完全一致；首尾空白拒绝而不修改身份。门④三类反例在 `derive:` 前缀下均可达。 |
| ④ 外形与提取 | **通过。** 门⑪仍恰为四份；唯一写点块正文无行首 `PYEOF`，两处占位各保留一次；[producer 文件:991](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_learning_events_schema_contract.py:991) 仅 ai-linked-doc 对应函数发生变化。 |
| ⑤ backend 行为不变 | **通过。** [learning_event_log.py:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/app/services/learning_event_log.py:14) 的修改限于注释/docstring；去除 docstring 后 AST 与 `d5ad6fca` 相同。 |

独立执行的 **14 组纯内存解析检查全部通过**，覆盖非法 UTF-8、坏行后合法重复、深嵌套、超长整数、非字典 JSON、空白和尾 LF 等边界。未发现这些输入让坏行影响后续查重的路径；但整本读入仍不能提供资源耗尽情况下的无条件隔离保证。

**两项时序限制仅登记、不引入 trace 握手，取舍合适。** [测试文件:309](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/skills/test_ai_linked_doc_writer.py:309) 的计时余量不能覆盖任意暂停，`:339` 起的固定 backlog 也不能保证跨机器负控必红。因此这些门应作为本机压力回归证据，并结合静态锁生命周期复核；源码中的“必然／必红”不能按无条件保证理解。本卡无需强制改成 `sys.settrace`。

字符核对需要区分范围：

- **SKILL.md 全文裸 U+2028、U+2029 均为 0**，未发现其他异常控制符或格式字符。`:136` 原有 `⚠️` 包含一个 U+FE0F，是正常 emoji 呈现选择符。
- [测试文件:460](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/skills/test_ai_linked_doc_writer.py:460) 注释仍有一个裸 U+2028，`:462` 反例字符串另有一个。后者用于测试；前者与“转义写”的注释不一致，但不影响功能，作为清洁附注，不另计缺陷。

验证边界：`ruff check --no-cache`、`ruff format --check --no-cache` 均通过。**pyright 未复证**，实际仍因缺少 `libllhttp.9.3.dylib` 启动失败。为遵守“不修改任何文件”，未运行会创建文件的完整写点、并发及 pytest 套件；作者报告的整套计数和历史进程退出码未独立重跑。全程未修改文件、未连接数据库。



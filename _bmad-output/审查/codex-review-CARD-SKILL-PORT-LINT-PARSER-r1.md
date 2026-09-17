> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 · 卡 CARD-SKILL-PORT-LINT-PARSER round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-SKILL-PORT-LINT-PARSER.md)"`
> 审查绑定: `1eab9358df306838c897163142647b1ea5424e27`（= 本卡代码 commit；基线 `17c14d2705e519d44cb7c4988c81a920b175d03f` = 前卡 T7-B tip）
> 会话头自证（抄 .stderr 的 L2 / L5 / L9，stderr 本身不入库；codex 0.153.3 把 model 排在第 5 行，字面抄前三行会漏字段）:
> `OpenAI Codex v0.153.3` (L2) / `model: gpt-6-astra` (L5) / `reasoning effort: ultra` (L9)

---

**结论：指定审 SHA `1eab9358df306838c897163142647b1ea5424e27` 的搬迁行为可接受。BLOCKER 0 / HIGH 0 / MEDIUM 0；发现 1 项 LOW 文档歧义。**

- **LOW — [skill_portability_lint.py:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/skills/skill_portability_lint.py:22)**：读者顺接前文理解“这两处都在模块级”时，会把 `_exam_board_code()` **函数内**的 `.replace()` 也误归为导入期执行；collect-time ERROR 的归因应限定于模块级筛选及其断言。登记中的两类失败阶段已作区分，但这句指代仍有歧义。

按六个问题逐项回答：

1. **零漂移：通过。** 独立重算得到 `237 = 85 + 152`，无重名、遗漏或新增；全部同名节点的 AST **及源码片段字节**一致，77 个测试完整保留。两段原文连注释均原样搬迁，中间隔着的 31 个测试声明没有装饰器或默认参数求值，不会执行判据或改变常量。  
   [模块:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/skills/skill_portability_lint.py:59) 的 `parents[3]` 实测仍指向当前 worktree 根；两个缓存包装器被 test 直接引用，`cache_clear()` 仍清理判据实际使用的缓存。独立导入未加载 pytest。这里确认的是现有判据和测试行为；函数 `__module__`、traceback 文件位置会随抽模块改变。

2. **真实模块依赖：通过。** [test:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/skills/test_skill_portability_lint.py:175) 的 51 个导入对象全部满足 `test.name is module.name`，12 个判据的 `__globals__` 均指向新模块。  
   本轮另在**内存中**令两条判据返回非空列表，实际触发：
   - `正文指标基线漂移:\nforced-drift-check_body`
   - `受管文件基线漂移:\nforced-drift-check_managed_files`

   没有落到 import 或夹具错误；恢复后对象绑定一致，磁盘字节未变。原存档 PRE/POST 摘要也与审 SHA 模块一致。仅凭“555 全绿＋无旧定义＋无重名”尚不是完整证明；加上此次对象身份、全局绑定和 AST 核验，足以支持其余 10 条的**搬迁连线正确**，不等于完成全部判据的语义变异覆盖。

3. **显式 import：通过。** 递归符号表检查未发现“引用搬出符号却未导入”的名字。本轮用真实文件路径进行 ruff stdin 检查，两文件原文均 `rc=0`，注入未定义名均明确报 **F821、rc=1**。  
   F821 不能普遍覆盖字符串反射、动态命名空间查找；但本 test 未发现此类取用搬出符号的路径。普通延迟执行的函数体全局引用仍受静态检查，因此没有实际漏名证据。F401 未启用，不能承担该证明。

4. **负控保持有效：通过。** 独立核对为 **25 个函数、46 个参数化用例**；函数、装饰器及断言与基线一致。  
   [test:2020](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/skills/test_skill_portability_lint.py:2020) 的裸 `/tmp/x.json` 输入仍调用新模块 `check_body`，并要求非空结果及 `exam-quick`、`tmp_all`、`期望=0 实测=1`，没有改走残留副本或弱化断言。

5. **复用限制：成立，属既有限制登记。** [模块:60](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/skills/skill_portability_lint.py:60) 的 `DEFAULT_ROOT` 固定为当前仓的 `canvas-vault/.claude`；其他静态面若直接使用它和现成基线，会检查本仓部署面。即便传入其他 root，`check_frontmatter` 的固定 `EXPECTED_SKILLS` 等约束仍在，不是通用静态检查接口。

6. **三处更正：结果可采信，但不能声称所有同型命令缺陷已穷尽排除。**
   - **(a)** 本轮直接读取子进程返回码，缺失符号确为 `ImportError / rc=1`，不经过过滤管道。
   - **(b)** 已独立复现真实文件路径下的 F821 注入红测；旧项目外探针的 `rc=0` 不再作为有效证据。
   - **(c)** 用明确文件名独立对照，before/after 唯一差异确为耗时行；after-final 去掉摘要头和返回码后，也仅耗时不同。

   存档仍有可复核性限制：[module-verifier:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/审查/evidence-skill-port-lint-parser/module-verifier-20260916T204822.txt:35) 只保存断言身份计数，未保留原始 traceback，完整 shell 命令也未入档。因此，**关键结论已由本轮独立复现补强；历史命令实现是否全部消除同型缺陷，现有存档不足以证明。**

三跑 `555 passed`、负控 `46 passed` 均已核对存档；最终存档的两份源码摘要与审 SHA、当前文件逐字节一致。SKILL.md 和两个 regression 文件在指定提交差异中均未改；SKILL 的摘要及 `6−4=2` 数字来自指定存档，未扩读实体。此次未重跑完整测试套件、未连接数据库、未修改文件。



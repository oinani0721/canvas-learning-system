## 结论

审查不通过。禁改面通过，freshness 真 oracle 也通过；但零写铁律已被实际破坏，且 orphan、退出码和变异门存在多处可复现的 fail-open。

## BLOCKER

1. **级别：BLOCKER**

   **位置：** [vault_lint.py:39-40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:39)、[vault_lint.py:69-73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:69)、[probe-BF-workflow:117-126](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/probe-BF-workflow-全量输出.json:117)、[UAT:10-14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:10)

   **问题陈述：** “全程零写（含 `__pycache__`）”已经被实际违反，而且正常 CLI 仍依赖调用者自觉设置环境变量。无 `PYTHONDONTWRITEBYTECODE` 时，仅执行 `--help` 就会因顶层 import 写入 `check_vault_doc_roles.pyc`。

   **依据：**

   - 隔离复制到 `/tmp` 后执行  
     `env -u PYTHONDONTWRITEBYTECODE -u PYTHONPYCACHEPREFIX backend/.venv/bin/python <tmp>/vault_lint.py --help`  
     得到 `rc=0`，同时生成 `<tmp>/__pycache__/check_vault_doc_roles.cpython-314.pyc`。
   - 卡内证据自身明确记录：probe-B 故意漏掉环境变量后，在车道 `backend/app`、`app/core`、`app/utils` 写入了 8 个 `.pyc`，随后才 `mv` 隔离恢复，并承认“中途确实产生过一次 LANE 内写入”。恢复不等于从未写。
   - [test_vault_lint.py:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:4) 声称“禁用 conftest”，实际 pytest 仍自动加载父级 conftest；存档测试输出中的 graphiti/jieba 等 warnings 证明真实裁判进程并非只有 filespec 直载链。
   - UAT 仍在结论区写“全部达成”“只看不动”，未登记上述已发生违例。

## HIGH

1. **级别：HIGH**

   **位置：** [vault_lint.py:299-303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:299)、[vault_lint.py:330-356](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:330)、[vault_lint.py:427-463](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:427)

   **问题陈述：** 文件 symlink 会被 `is_file()` 接纳并跟随到 vault 外读取；越界内容还能让检查整体绿灯。

   **依据：**

   - `/tmp/vault/原白板/external.md -> /tmp/outside.md`，外部内容为 `[[x]]`；节点 `x.md` 无 `source_board`。实际结果：`status=ok, findings=[], inbound_targets=1`，真实孤儿被外部文件隐藏。
   - `outputs/回顾-outside.md` 链到 vault 外、且外部文件带 `type: recap` 时，G8-1 虽登记 G11，独立 recap 扫描仍再次读取外部文件，最终 `rc=0/status=ok/findings=[]/blind_spots=1`。
   - UAT 只披露“目录 symlink 后代不递归”，未披露文件 symlink 外逃。

2. **级别：HIGH**

   **位置：** [vault_lint.py:330-343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:330)、[sync_board_concepts.py:192](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/canvas-vault/.claude/scripts/sync_board_concepts.py:192)、[sync_board_concepts.py:463](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/canvas-vault/.claude/scripts/sync_board_concepts.py:463)

   **问题陈述：** AUTO-GENERATED 成员块被当作普通入链。陈旧自动块中的 `[[节点/x]]` 可让无真实来源、无 `source_board` 的节点判为正常。

   **依据：**

   - `/tmp` fixture 中，节点 `x` 无 `source_board`，唯一链接位于 AUTO 哨兵块，结果 `status=ok, findings=[]`。
   - live 只读复算：14 个节点全部同时有 `source_board` 和 AUTO 成员链接；去掉 AUTO 后有 3 个节点没有其他入链。
   - 这意味着 live orphan 门的两个“独立”条件实际上同源、自确认。UAT 未登记这一实现选择及陈旧块假阴后果。

3. **级别：HIGH**

   **位置：** [vault_lint.py:326-381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:326)、[vault_lint.py:576-580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:576)

   **问题陈述：** 扫描面缺失或节点不可读时 fail-open。

   **依据：**

   - 任意存在的空目录执行 `--only orphan_nodes`：`节点/` 不存在，但返回 `status=ok`、CLI `rc=0`；note 同时承认“无对象可查，不是零孤儿”。
   - 唯一节点为非法 UTF-8 的 `节点/bad.md`：实际返回 `ok / 1个节点, 0个孤儿 / findings=[]`，不可读文件甚至被重复记为两个盲区。
   - 因而“没有发现孤儿”和“检查根本没覆盖对象”在退出信号上不可区分。

4. **级别：HIGH**

   **位置：** [vault_lint.py:108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:108)、[vault_lint.py:292-295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:292)、[UAT:93-102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:93)

   **问题陈述：** 非语义 wikilink 被计为入链：fenced code、行内 code、HTML 注释以及跨行 `[[\nx\n]]` 都可隐藏真孤儿。

   **依据：** 四组独立 `/tmp` fixture 中，节点 `x` 无来源，白板分别只含上述一种伪链接；四组均返回 `status=ok, findings=[]`。正则允许跨行且没有 code/comment 剥离。UAT 只披露 code/行内/template，未披露 HTML、跨行和 AUTO。

5. **级别：HIGH（声明比证据宽）**

   **位置：** [test_vault_lint.py:271-328](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:271)、[UAT:37-40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:37)

   **问题陈述：** frontmatter 排除门不具判别力，却被写成“已证明”。

   **依据：**

   - 用例只在 A 自己的 frontmatter 放 `[[某板]]`、`[[B]]`，没有构造“另一文件 frontmatter 指向 A”。
   - 将 `_split_frontmatter` 在内存中变异为把完整文本都当正文后，该测试仍然得到 `["节点/A.md"]`；真正的 `B.frontmatter: up:[[A]]` 才能杀死此变异。
   - 也没有“节点 B 正文 → A”的正向 fixture；删除节点正文作为入链源仍可躲过现有 orphan 门。
   - UAT 声称测试覆盖空 `[[]]`，实际参数是空字符串 `""`，不是 `[[]]`。

6. **级别：HIGH**

   **位置：** [vault_lint.py:624-633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:624)、[vault_lint.py:639-662](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:639)、[test_vault_lint.py:543-545](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:543)

   **问题陈述：** “2=有 warn”不是全入口真相；参数/调用错误也返回 2，和正常治理告警冲突。

   **依据：**

   - 无参数启动：`rc=2`。
   - `--only no_such_check`：`rc=2`。
   - 两者均在 `parse_args()` 阶段退出，绕过配置错误 `rc=3` 的 catch。
   - 正确部分：显式传入不存在的 vault、非法 `--now`、台账 `ConfigError` 会返回 3。但测试反而把缺 `--vault` 的 rc2 固化为预期。

7. **级别：HIGH（声明比证据宽）**

   **位置：** [g82_mutation_negative_controls.sh:37-52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/g82_mutation_negative_controls.sh:37)、[UAT:66-70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:66)

   **问题陈述：** 变异脚本把几乎所有 pytest 非零都记为 KILLED。收集/导入/usage/internal error 即使指定门一条都没执行，也可得到 `ALL-KILLED`。

   **依据：** 判定仅排除 rc0 和 rc5；pytest rc2/3/4 均进入 `KILLED`，没有核对失败节点名或断言。脚本的串行执行、替换锚唯一和逐轮 `cmp` 恢复是正确的，但 evidence 目录中没有 `MUTANT … KILLED` 或 `ALL-KILLED` 运行 transcript；`rg` 排除脚本自身后无命中。UAT 的“6/6 指定门逐个变红”目前只是自报。

## MEDIUM

1. **级别：MEDIUM**

   **位置：** [vault_lint.py:244-257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:244)、[vault_lint.py:292-295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:292)、[vault_lint.py:339-342](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:339)

   **问题陈述：** 三个未登记的 orphan 边界：

   - 节点 `x.md`、白板 `[[X.MD]]` → `.MD` 未被去除，误报孤儿。
   - `source_board: null`、无入链 → `"null"` 被当真值，真实孤儿返回 ok。
   - `节点/d1/A.md` 正文显式链接 `[[d2/a]]`，另有 `节点/d2/a.md` → casefold/basename 后被误判为自链并丢弃，两个节点均被误报孤儿。

2. **级别：MEDIUM（当前代码正确，但门未证明默认路径）**

   **位置：** [vault_lint.py:597-605](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/scripts/vault_lint.py:597)、[test_vault_lint.py:413-420](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/backend/tests/unit/test_vault_lint.py:413)

   **问题陈述：** `resolve_today(None)` 当前正确使用上海日，但名为“不是 host local”的测试只传显式字符串，从未调用默认分支。把默认实现变异回 `date.today()`，该门仍会全绿。

   **依据：** 独立运行 freshness 门为 `18 passed`；17 组真实 oracle 状态为 `ok=4, stale=12, corrupt=1`，确认不是全 corrupt 假绿。缺口仅是默认时钟路径未锁。

3. **级别：MEDIUM（声明比证据宽）**

   **位置：** [UAT:12、53-56、76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:12)、[live-sha-command.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/live-sha-command.txt:1)

   **问题陈述：** UAT 写“live 全树 sha”“全部笔记一个字没改”，实际命令排除了 `今日复习.*`。UAT 后文 107-108 虽如实承认排除，但与结论区直接矛盾。

4. **级别：MEDIUM（声明比证据宽）**

   **位置：** [UAT:64-65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/验收单/UAT-CARD-G8-2-统一lint骨架与三检查.md:64)、[help-head20.txt:14-20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint/_bmad-output/审查/evidence-g82/help-head20.txt:14)

   **问题陈述：** UAT 称存档的 `help-head20.txt` 包含 0/2/1/3，实际第 20 行只到 `0 全部检查 ok`。当前完整 `--help` 确实包含四个码，但没有写清 orphan/raw finding 只到 warn，以及 freshness 的 stale/no_projection=warn、corrupt=fail；这些规则只存在源码/UAT，未出现在 CLI 帮助或报告契约说明中。

## 已核实通过

- 禁改面：用户给定 `git log` 命令的文件名 stdout 为空；仅有 Git 的 `confstr()` 环境 warning。额外补查遗漏的 `.gitignore`，对六个禁改文件执行 `git diff --exit-code -- ...` 得到 rc0。
- freshness：测试确实 filespec 直载并调用真实 `_vault_entry`，不是自制 oracle；17 组有效 v3 fixture 确实进入 `ok/stale` 分支。
- 标准 orphan 形态 `[[x]]`、alias、子路径、embed、heading/block、 lowercase `.md`、NFC/NFD、普通大小写差异均有有效用例。
- `with_probe=False` 已固定；未 import live vault 的 sync 脚本；生产 lint 路径没有启动 FastAPI lifespan 或连接 Neo4j。
- JSON 与文本都由同一 `LintReport` 渲染；有效 `--only` 的聚合/skipped 语义正确。
- recap 子检查在 live 恒绿这一限制，UAT 已如实披露，且 fixture 有真实反例。
- 本轮只读审查未修改工作树；所有对抗 fixture 均位于 `/tmp` 并禁用 bytecode/cache。

BLOCKER/HIGH 清零：否



# 复核任务（round-2, prompt-2）：CARD-HARNESS-TREE-PARSE-REDO（`_harness_tree` 解析整体重做）

你是独立复核者，在做一次普通的代码评审：判断一段读配置文件的解析代码在换成 YAML 解析器
之后是否还有行为不一致。只读，不要修改任何文件，不要连接任何数据库或网络服务。
（round-2 的第一次提问因措辞被判为安全风险而中断；本版把问题改成按类别核对覆盖面，
不索取具体输入文本。）
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
审查绑定：`08100483..4d21bc9b`（本卡全部代码改动；`f7f10be4` 是 round-1 审过的中间态，
`4d21bc9b` 是按 round-1 结论整改后的最终 HEAD）。

## 一 背景与最小读取面（请只读下列内容，不要扩面）

被改的是 `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 里的 `_harness_tree`。它解析
vault 的 `.canvas-config.yaml` 中的 `harness_tree` 键，决定 `REPO` —— 那棵装着
`backend/scripts/validate_learning_events.py` 的代码树。选错树 = 事件被写去绑定到另一棵
harness，用户看不见。原实现是逐行正则，历史上有四轮同族缺陷，本卡整体换成 PyYAML。

round-1 判定：BLOCKER 无、HIGH 无、MEDIUM 一条、LOW 两条。整改已全部落在 `4d21bc9b`。

请读：
1. `git diff 08100483 4d21bc9b -- . ':(exclude)_bmad-output'`（本卡全部代码改动）
2. `git diff f7f10be4 4d21bc9b -- . ':(exclude)_bmad-output'`（本轮整改的增量，最该细看）
3. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `:370-500`（改后的 `_harness_tree`
   与其唯一调用点；含嵌套的 `_degraded_scan`）
4. 同文件 `:1200-1235` 一带（F1 判定段，本卡声称与它同构的参照实现；请用
   `grep -n "换 PyYAML 一次解决整类问题"` 重新定位，行号会漂）
5. `backend/tests/regression/test_g3_2_review_ledger.py`：`:40-56`（提取被测代码的机制）、
   `:218-266`（子进程执行写点）、`:6859-7112`（既有 8 个 harness_tree 门 = 16 nodeid）、
   `:7113-7600`（本卡新增的全部门，含 round-2 新增的不变量门）
6. `_bmad-output/审查/codex-review-CARD-HARNESS-TREE-PARSE-REDO-r1.md`（round-1 结论原文）
7. `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md`（作者自述与证据路径）

## 二 round-1 结论的整改自述（请独立核对，不要采信）

1. **MEDIUM（降级扫描接受面越过 PyYAML）**：`_degraded_scan` 重写。分隔符只认 SP；值内
   禁 TAB 与冒号；含 `harness_tree` 的行若带 YAML 当换行的字符（U+0085 / U+2028 / U+2029 /
   VT / FF / FS / GS / RS）一律拒；规范行后跟续行一律拒；任何含 `harness_tree` 而不是那一种
   写法的行（含流式映射 `{harness_tree: /B}`）一律拒。
2. **LOW（非严格 realpath）**：改 `os.path.realpath(..., strict=True)`，`OSError` 落到既有的
   「树不存在」拒因。
3. **LOW（降级门控制组对绑定树失明）**：控制组补「先弄坏缺省回退目标 + 断言账本恰 1 行」。
4. **Q2 措辞**：docstring 明确「三条分界只对 PyYAML 在的那条分支成立」，降级分支只有
   「无键 ⇒ 回退 / 其余 ⇒ fail-closed」两态。
5. **Q5**：探针的 `finally` 改为用哨兵记住原模块对象后按原样放回，不再只 `del`。
6. **新门** `test_g33r2_harness_tree_degraded_never_diverges_from_yaml`（40 参数）：用 AST 从
   写点里逐字抽出 `_harness_tree`，对同一份 config 分别以 yaml 可用 / 屏蔽各跑一次，断言
   两次结局要么完全相同、要么降级侧是一个点名 PyYAML 的拒绝。
7. 作者自跑：74（harness_tree 子集）/ 223（整文件）/ 546（tests/skills）全通过；把 SKILL.md
   还原到 `f7f10be4` 后该新门红 11 条。

## 三 请按重要性回答的问题

0. **整改的覆盖是否完整（按来源分类核对，不必给出具体输入）**：`_degraded_scan` 现在由四
   件事合起来保证「接受面 ⊆ PyYAML 且同值」——① `_canon` 的形状（分隔符、值内禁用字符）、
   ② `_breaks` 的换行类字符判据、③ 续行判据、④「这一行提到了这个键就必须是那一种写法」的
   宽判据。请按**来源分类**核对它们合起来是否覆盖了「同一行文本在逐行扫描与 YAML 解析下
   取值不同」的各类成因：换行类字符 / 空白与分隔符差异 / YAML 指示符（冒号、井号、引号、
   流式括号）/ 多行折叠与块标量 / 文档分隔与锚点别名 / 编码层（BOM、CRLF）。若某一类没有被
   上述四条覆盖，请指出是**哪一类**以及应由四条中的哪一条负责，不需要给出具体配置文本。
1. **新门本身有没有假绿面**：AST 抽取 + `sys.modules["yaml"] = None` 的做法，会不会在
   某些输入上让两条分支都走进同一个早退路径，从而「相同」得没有意义？40 条参数里有
   没有哪几条其实测不到东西？
2. **`strict=True` 有没有引入回归**：原先能用的合法配置（符号链接链、相对路径、`~` 展开）
   会不会因为 strict 而被误拒；既有 16 个门的期望是否仍然成立。
3. **降级分支新增的拒绝是否过宽到有害**：`"harness_tree" in line` 这条宽判据会让
   「某个无关键的值里恰好含有 harness_tree 这个词」的配置也被拒。这个取舍在本函数的
   语境里是否可接受，有没有更窄又不漏的写法。
4. **既有 16 个门是否仍逐条行为不变**（尤其 TAB / U+3000 / NBSP 三态与值首 Unicode 空白）。
5. **降级 fail-closed 门新增的三条结构参数**（U+0085 / 续行 / 流式映射）的控制组是否成立：
   它们在 PyYAML 可用时确实解析到 alt 树并写入，而不是走了别的路径。
6. 有没有哪一条新增门的断言宽到「只要退出码为 0 就算过」，从而对「绑到了哪一棵树」失明。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：
- 一句话结论
- `file:line`
- 一句话说明在什么输入下会出现该结果
没有问题的分级请显式写「无」。

## 五 边界

- 只读。不要修改文件，不要运行会写盘的命令，不要连接 7691 / 7687 / 任何数据库。
- 不评 `backend/app/services/learning_event_log.py`（属另一张卡的面）。
- 不评 `test_g3_2_review_ledger.py` 里 harness_tree 区以外那 150 个测试的设计。
- 不评 `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `decay_beta.py`（本卡零改动）。

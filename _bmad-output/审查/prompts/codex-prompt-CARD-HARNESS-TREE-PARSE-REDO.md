# 复核任务：CARD-HARNESS-TREE-PARSE-REDO（`_harness_tree` 解析整体重做）

你是独立复核者。只读，不要修改任何文件，不要连接任何数据库或网络服务。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
审查绑定：`08100483..f7f10be4`（本卡唯一代码 commit）。

## 一 背景与最小读取面（请只读下列内容，不要扩面）

被改的是 `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 里的一个函数 `_harness_tree`。
它解析 vault 的 `.canvas-config.yaml` 中的 `harness_tree` 键，决定 `REPO`——那棵装着
`backend/scripts/validate_learning_events.py` 的代码树。选错树 = 事件被写去绑定到另一棵
harness，用户看不见。原实现是逐行正则，历史上有四轮同族缺陷（尾注释被截断 / `#` 当分隔符 /
正则空白类吃掉值首全角空格 / 转义引号截短 / 非列首键写法不识别），本卡整体换成 PyYAML。

请读：
1. `git diff 08100483 f7f10be4 -- . ':(exclude)_bmad-output'`（本卡全部代码改动）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `:370-461`（改后的 `_harness_tree` 与其唯一调用点）
3. 同文件 `:1176-1205`（F1 判定段——本卡声称与它同构的那个参照实现）
4. `backend/tests/regression/test_g3_2_review_ledger.py` 的 `:40-53`（测试如何从 SKILL.md 逐字
   提取被测代码）、`:216-264`（子进程执行写点的方式）、`:6857-7110`（既有 8 个 harness_tree
   门，参数化展开 16 个 nodeid）、`:7111-7447`（本卡新增的全部门）
5. `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md`（作者自述与证据路径）

## 二 作者自述（请独立核对，不要采信）

1. yaml-first 分支与 F1 判定同构：`try: import yaml` → `safe_load` → `except ImportError`
   打印降级告警后走正则 → `except Exception` 抛 SystemExit（fail-closed）。
2. 降级分支只接受 `harness_tree: <绝对路径>` 一种写法，其余（引号 / `#` / 相对路径 /
   Unicode 空白 / 非列首键）一律 fail-closed，不静默回退。
3. M-a 用 `os.path.realpath` 逐段解析 symlink，取代原 `os.path.normpath` 的字符串消 `..`。
4. 既有 16 个 harness_tree 门语义不变、全部保持通过。
5. 新增 15 个 nodeid；改代码前先跑，其中 6 个（M-a/M-b/M-c）如期失败在各自的判据断言。
6. 负控：把 `_harness_tree` 还原成正则版后，那 6 个门重新全部失败；给 SKILL.md 追加一行注释
   后，受管文件摘要门失败。两段跑完后 SKILL.md 的 sha256 与跑前逐字相同。
7. SKILL-PORT-LINT 的三处基线随卡更新（文件摘要 / `/tmp` 块指纹 / body 计数注释行号）。

## 三 请按重要性回答的问题

0. **降级分支的收口是否真的严**：缺 PyYAML 时那条正则 `^harness_tree:[ \t]+(/\S[^#]*?)[ \t]*$`
   加上"看起来像这个键就拒"的宽判据，是否存在某种**合法 YAML 写法**被降级正则**取到一个与
   PyYAML 不同的值**却照样放行？若有，请给出那一行配置文本和两边各自会得到的值。
1. **M-a 的 realpath 是否覆盖"链在中间段 + `..` 混用"的全部形态**，与 `normpath` 是否还有
   残余分叉（例如链指向相对目标、多重链、`.` 与 `..` 混排）。
2. **回退与拒写的分界是否被改动**：`_doc` 非 dict / 键缺失 / 值为 `None` / 值为空串这四种，
   是否都仍然回退 `dirname(VAULT)`（与既有门 `:7089` 同口径），有没有哪一种被误判成拒写
   （那会把"用户清空这个键"变成不可用）。
3. **config 整体不是合法 YAML 时**（例如行内有 TAB）是否 fail-closed 且拒因点名 `harness_tree`，
   有没有被吃成回退。另请判断：把"整份 config 解析失败"报成 harness_tree 的问题，措辞是否会
   误导用户去改错地方。
4. **既有 16 个门在 yaml-first 下是否真的行为不变**，特别是 `:6975`（空 / SP / TAB / U+3000 /
   NBSP 五参数）与 `:7025`（值首 U+3000 / NBSP）的期望是否仍与实现一致；`:6975` 的 TAB 参数
   拒绝层次变了（从下游 config 读取层上移到本函数），作者改了该门的 docstring 措辞但没改断言，
   这样处理是否恰当。
5. **注入 ImportError 的降级门是否真的进入了 `except ImportError` 分支**（见
   `_run_writer_no_yaml_at_harness_tree`，做法是把写点里 `REPO = _harness_tree(VAULT)` 这一行
   包进 `sys.modules['yaml'] = None` / `finally: del`）。这个探针有没有可能在不进入该分支的
   情况下也让门通过；以及它对写点其余部分的 yaml 使用有没有副作用。
6. 新增门里有没有哪一条的断言宽到"只要退出码为 0 就算过"，从而对"绑到了哪一棵树"失明。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：
- 一句话结论
- `file:line`
- 一句话说明在什么输入下会出现该结果
没有问题的分级请显式写"无"。

## 五 边界

- 只读。不要修改文件，不要运行会写盘的命令，不要连接 7691 / 7687 / 任何数据库。
- 不评 `backend/app/services/learning_event_log.py`（属另一张卡的面）。
- 不评 `test_g3_2_review_ledger.py` 里 harness_tree 区以外那 150 个测试的设计。
- 不评 `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `decay_beta.py`（本卡零改动）。

绑定 **`08100483..4c722826`**；结束时 HEAD 和被审文件未漂移。

**结论：BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 2。**  
H1 的异常串入回退路径已修复；“PyYAML 不可用时绝不返回树”和“P2 被构造性消除”仍不能成立。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

### M1：成功导入同名模块，不等于取得可用的 PyYAML

**位置：** [SKILL.md:429](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:429)，后续 `:440–451`。

**触发输入：** PyYAML 不可用，但同名空 `yaml.py` 成功导入，同时 config 不存在、父目录是可用树。

此时尚未调用 `yaml.safe_load`，读取 config 的 `FileNotFoundError` 已触发回退，函数返回父树。因此，**导入失败已全部拦住，但“拿不到 PyYAML 绝不返回树”的全称断言仍有反例。**

只读复现使用真实 `SourceFileLoader` 从 `/dev/null` 加载空源码，没有替换 `__import__`：

```text
default_yaml_spec None
loader SourceFileLoader
has_safe_load False
returns_parent True
```

24 格都制造“导入抛异常”，没有覆盖“导入成功但缺少解析入口”。应在导入门内取得实际使用的解析入口。

**影响限度：** 当前树的下游仍会因 config 缺失拒写；未证明账本写入。此处是 PyYAML 能力检查，区别于另立卡的 harness 版本契约。

### M2：P2 只是旧锚失配，换写法后仍能通过全部 24 格

**位置：** [变异脚本:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/审查/evidence-harness-tree/verify-new-gates-kill-mutants-20260915.py:175)、[测试:7743](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7743)；错误结论见 [UAT:673](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:673)。

**触发输入：** PyYAML **可用**、config 不存在、父目录是可用树。

保留当前 `except Exception`，仅在同一 `try` 内把一次 `open(...).read()` 放到 `import yaml` 前：

- 现有矩阵：**24/24 绿**。
- 补上述输入：生产返回父树；变体将 `FileNotFoundError` 报成“PyYAML 不可用”并拒绝。

既有 `absent_falls_back_to_parent:6866` 测的是 **config 存在但无键**，补不上这一格。

所以 **INVALID 仅证明旧文本锚不能用了**。如果再加入 `except OSError: return parent`，现有矩阵能够抓住；但这不证明整个前置读取缺陷类别已消失。

### M3：仍漏掉“无 config 时才采用环境变量／缓存”的组合

**位置：** [测试:7798](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7798)，以及 `:7803`。

**触发输入：** 缺 PyYAML、config 不存在，同时环境变量指向可用树。

在缺库处理内加入“**仅 config 不存在时**，采用有效的 `QUIZ_ANSWER_HARNESS_TREE`”这一错误回退，逐字执行现有矩阵仍 **24/24 绿**；补齐组合后，变体返回该树。

原因是无 config 的两种形状不设变量，而 `env_override_set` 必写 config。`sidecar_present` 同样必写 config，因此“仅无 config 时采用缓存”也存在相同覆盖缺口。

**这是测试缺口；当前生产没有上述回退。**

## LOW

### L1：安装命令的引号仍不能保留所有合法路径

**位置：** [SKILL.md:436](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:436)。

**触发输入：** 解释器路径包含 `$VAR`、`$(...)`、反引号，或反斜杠紧接双引号。

当前只转义双引号；shell 在双引号内仍会展开变量和命令替换。只读 zsh 验证中，`/opt/$(printf wrong)/bin/python` 变为 `/opt/wrong/bin/python`；反斜杠紧邻引号的样例出现引号不配对。应使用可靠的 shell 参数引用，例如 `shlex.quote`。

### L2：六处措辞仅修了五处，仍有直接矛盾

**位置：** [UAT:533](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:533)。

**触发条件：** 阅读负控⑥汇总时，仍看到“新不变量门 **12 条红**”，与本轮 `:495–496` 明确更正的 **10 unit + 2 端到端**矛盾；这正是 r7 点名的那一行。

其他残留：

- UAT `:766` 仍建议引用“不会损失一次原本能完成的写入／实际代价只是错误信息”，与 `:756` 的作废声明冲突。
- 测试 `:7711` 仍称“两种方式”，现在有三探针。
- 测试 `:7284–7285`、`:7345` 仍描述已删除的正则降级和降级告警。

## 其余逐项核对

### 24 格没有恒真断言，但并不穷尽错误实现

每格都要求 `exit` 且包含完整缺库拒因，返回树会使对应格失败。下表每行覆盖该形状的**全部三个探针**：

| 形状 | 三格仍可共同漏过的错误实现示例 |
|---|---|
| `no_config_file` | 仅父树可用时回退；此格父树不可用 |
| `no_config_and_parent_is_tree` | 仅无 config 且有环境变量时采用树 |
| `target_tree_really_exists` | 只降级解析无注释、无引号的极简配置 |
| `parent_is_a_usable_tree` | 仅 config 不存在时回退 |
| `minimal_unquoted_config` | 只降级读取 JSON |
| `pure_json_config` | 只用行首正则读取普通键值行 |
| `env_override_set` | 仅 config 不存在时采用变量 |
| `sidecar_present` | 仅 config 不存在时采用缓存 |

此外，三探针均属于 `(ImportError, OSError)`，不能证明其他异常类别的诊断覆盖完整。

### H1 的异常处理与第三探针

独立执行生产函数确认：`ModuleNotFoundError`、普通 `ImportError`、`PermissionError`、`RuntimeError`、`SyntaxError` 均转为缺库拒绝，**config 读取次数为零**。

`KeyboardInterrupt`、`SystemExit` 属于 `BaseException`，不会被 `except Exception` 吞掉；它们原样传播，也不返回树。

`import_raises_oserror` 名称准确，但它只验证导入调用边界的异常分派。直接替换 `__import__` 绕过了模块缓存、finder、loader 和 `.pyc`；真实源码不可读时，已有缓存或可用字节码仍可能让导入成功。不能把该探针等同于真实权限环境的集成验证。

### 异常文本是否泄漏

`:437` 确实会原样展示包路径和异常文本。但目前输出给同一用户，且本来就要求展示解释器路径；未发现跨权限接收者或真实敏感内容，**不另列安全缺陷**。这不代表任意异常文本天然安全。

### 既有门与复现脚本

AST 对比和控制流核对未发现 **16 个既有门、6 个 M 门及 flow／采用门**因本轮新增失效或恒真。flow／采用门仍关闭父树，并要求目标树路径下成功写入一行，区分能力保留。

三向脚本固定了 `4eeaeaa6` 写点；自动断言仍只覆盖 rc 和账本行数，未断言 mastery、`find_spec` 或 B 格具体拒因。

本次未修改文件、未连接网络或数据库；动态验证限于内存执行及只读命令，**未重跑会写盘的 pytest 或三向脚本，不独立背书 `112 / 261 / 546` 整套运行计数**。



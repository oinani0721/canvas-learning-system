> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 · 卡 CARD-HARNESS-TREE-PARSE-REDO round-6（用户裁定后的新增范围，第 1 轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-REDO-r6.md)"`
> 审查绑定: `08100483..faaeb005`（该轮 HEAD；其 M1/M2 与 L1-L4 **六条全部整改** ⇒ HEAD 已前进到 `8d973a29`，故本轮**不绑最终 HEAD**，见 r7）
> 会话头自证（抄 .stderr 前 12 行中的三条，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

复核绑定：`08100483..faaeb005`，实际 HEAD 为 `faaeb005ad168cfae2ad1c40e5a004bd60ba3050`。

**未发现本轮生产解析逻辑回归；发现 2 项 MEDIUM、4 项 LOW。** 验收单有未提交更新，下文涉及其新增内容时均指工作树版。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

### M1．原 9 参数并非无损折叠：合法的整文档流式映射覆盖丢失

位置：[test_g3_2_review_ledger.py:7476](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7476)、同文件 `:7559`。

**触发输入：** 整份配置写成 `{vault_id: ..., subject: ..., harness_tree: /有效树}`。

旧门以 `whole` 模式写入合法文档，并验证有库时实际采用目标树；现在的 `{harness_tree: /a/b}` 被接到固定 block mapping 配置头之后，独立调用真 PyYAML 得到 **ScannerError**，已经不是原形态。

原 9 项逐条映射如下：

| 原形态 | 当前行号 | 结果 |
|---|---:|---|
| 键后空格 | 7486 | 保留 |
| 双引号键 | 7487 | 保留 |
| 单引号键 | 7488 | 保留 |
| 双引号值 | 7485 | 保留 |
| 值后注释 | 7482 | 保留 |
| 相对路径 | 7489 | 字符串形态保留 |
| 值尾 U+0085 | 7471 | 字符串形态保留 |
| 续行折叠 | 7474 | 字符串形态保留 |
| 整文档流式映射 | 7476、7559 | **未等价保留** |

此外，60 参数门已删除有库侧调用，因此相对路径、U+0085、续行的**成功采用目标树**控制也随旧门删除。当前实现仍正确，但这些回归现在缺少原来的检测。

### M2．复现脚本未绑定历史写点，在最终 HEAD 无法重现承重反例

位置：[repro-counterexample-20260914.py:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/审查/evidence-harness-tree/repro-counterexample-20260914.py:43)。

**触发输入：** 在 `faaeb005` 上按脚本说明运行 A/B/C。

脚本从活动工作树提取当前写点。A、B 都会提前收到新的 PyYAML 拒绝，A 无法到达旧校验器，因而不能重现历史的 `rc=0／账本1行／mastery=0.57`。应固定删除降级前的写点版本。

这不否定用户提供的历史实测，只说明**入库脚本目前不能重现它**。

## LOW

### L1．测试说明和验收单仍保留已证伪的“拒写无代价”依据

位置：[test_g3_2_review_ledger.py:7298](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7298)。

**触发输入：** 真缺库，目标 harness 使用不依赖 yaml 的旧 `_vault_id_of`。

这里仍称成功写入“不可达”、降级“改变不了写不写得成”，与本轮反例直接矛盾。`:7283–7285`、`:7336`、`:7450`、`:7477` 也仍描述旧降级分支或旧不变量。

[验收单:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:13)及 `:22` 仍把降级作为现状；工作树版 `:581/:591` 仍推荐无代价论据，`:630` 仍称 r5 后控制流零变化。追加新节没有消除这些冲突。

### L2．“无键老布局从成功变拒绝”的代价范围写大了

位置：[test_g3_2_review_ledger.py:7391](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7391)。

**触发输入：** 无 `harness_tree`、回退当前 harness、真实缺库。

三向实验 B 表明该场景原本就拒写；只有下游无需 yaml 的 harness 才可能损失原本成功的写入。该门的“有库成功／局部屏蔽后拒绝”不能证明所有老布局此前都能成功。工作树验收单 `:505–507` 同样扩大了范围。

### L3．错误点明了缺什么，但不足以让非技术用户可靠修复

位置：[SKILL.md:435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:435)。

**触发输入：** `pip` 与运行 quiz-answer 的 Python 属于不同环境。

照抄 `pip install pyyaml` 可能安装成功却继续拒写。消息虽说“那个解释器”，却没有显示实际路径或绑定该解释器的安装命令。

**不会被下游归属错误覆盖：** 此处在确定 `REPO` 时已抛 `SystemExit`，尚未导入校验器，更未进入“vault 归属无法绑定”判据。

### L4．“恢复降级后 60 条一起红”与负控结果不符

位置：[test_g3_2_review_ledger.py:7548](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7548)。

**触发输入：** 恢复 `4eeaeaa6` 的 `_harness_tree`。

存档汇总是 **12 failed + 50 passed，共 62 项**；结合源码判据可核得 **10 个 unit 失败 + 2 个端到端失败**，不是 12 个 unit，更不是全部 60 个 unit。

## 其余问题的核对结论

### PyYAML 可用时：确认零行为变化

16 个既有用例及 6 个 M 用例的参数、函数体和断言与 `4eeaeaa6` 相同，逐项期望如下：

| 用例组 | 数量 | 期望 |
|---|---:|---|
| 无键、显式目标树、引号值带尾注释、空值带注释 | 4 | 正确回退或采用并写入 |
| `#` 前分隔符 | 5 | SP 成功；TAB 拒绝；无分隔/U+3000/NBSP 保留完整路径并拒绝 |
| 值首 Unicode 空白 | 2 | 不吞字符，拒绝且节点、账本不变 |
| 坏绝对路径、`~`、引号路径、相对路径 | 4 | 拒绝，不回退 |
| 清空值 | 1 | 回退并写入 |
| M-a／M-b／M-c | 1／2／3 | OS 解析 symlink／完整转义引号值／识别三种合法键写法 |

生产函数去除 docstring、已删降级代码及有意修改的 `ImportError` handler 后，AST 相同：读取 `OSError`、非映射/无键/null/空串的回退；`expanduser`；相对路径基准；严格 `realpath`；采用出口；YAML 错误和路径不可达拒因均未变。**唯一有意改变的是缺库出口。**

### 三个新门：均非恒真，但各有覆盖边界

| 门 | 能抓住什么 | 单独仍可能放过什么 |
|---|---|---|
| 60 参数 unit | 任何返回，包括 `None`；拒因未点名 PyYAML | “有库也恒抛 PyYAML”的错误实现；由端到端有库控制补住 |
| canonical 端到端 | 误回退、缺库仍写入、节点或账本变化 | 只对无键/其他形态错误放行 |
| 无键端到端 | 缺库继续采用默认树并写入 | 只在显式配置上发生的错误 |

三门共同仍未覆盖一个具体回归：若把 `import yaml` 移到打开配置文件之后，缺库且配置文件不存在时可能先被 `OSError` 分支回退；现有 60+2 项都先创建配置文件，仍可全绿。**当前代码导入在前，行为正确。**

### 代价与删除依赖

- 主函数 docstring 的历史数字与用户给定实测一致，正确承认存在写入损失；两个新端到端门验证的是局部屏蔽依赖后的拒写，不能替代历史三向实验。
- `_degraded_scan` 及其状态量均为局部实现，唯一调用同步删除；未发现仍依赖它们的可执行引用或共享辅助功能被误删。

## 验证范围

全程只读、离线，未运行会写盘的 pytest 或完整复现脚本。独立用真实 `Python 3.14.4 -B -S` 确认 `find_spec("yaml") is None` 时函数提前拒绝；两个 ruff 检查均使用 `--no-cache`，结果为 0；排除 `_bmad-output` 后确实仅三文件变更。

84/233 有本轮测试存档；找到的 546 存档早于此次提交，不能据此独立确认最终 HEAD 的 546 全绿。

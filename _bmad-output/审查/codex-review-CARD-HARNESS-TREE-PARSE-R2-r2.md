> 批次: BATCH-2026-09-18-第十五批 · 车道 P6 · 卡 CARD-HARNESS-TREE-PARSE-R2 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-R2-r2.md)"`
> 审查绑定: `23c6aaf0`（送审时 HEAD；**收工复核实测 `git diff --stat 23c6aaf0 HEAD -- . ':(exclude)_bmad-output'` = 0 行 ⇒ 本轮绑最终 HEAD**）
> 会话头自证（抄 `.stderr` 中的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 4 行） / `model: gpt-6-astra`（第 7 行） / `reasoning effort: ultra`（第 11 行）
>
> 分级实数（车道复核）: 正文 `**BLOCKER**` 小节 0 个、`**HIGH**` 小节 0 个；
> 开头由模型自己写下 `BLOCKER: 无 / HIGH: 无`。MEDIUM 4 条、LOW 3 条 —— 按协议 §1
> **登记不阻断**。⇒ **D-15 闭合条件满足**（绑最终 HEAD 的一轮 BLOCKER = 0、HIGH = 0）。

---

BLOCKER: 无 / HIGH: 无

审查绑定 `HEAD 23c6aaf08c04fd1db76bf0281168d67c166b169d`，四个文件工作区与 HEAD 一致。第 1 轮三项整改在原来的负控／对照形态上均成立；本轮发现 **4 项 MEDIUM、3 项 LOW**。

**MEDIUM**

1. **值内豁免仍会误拒真 PyYAML 接受的无键文档。**  
   [SKILL.md:625](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/quiz-answer/SKILL.md:625)、`:634`：`!!binary` 解析后成为 `bytes`，原文中的词法命中无法获得豁免，破坏“无键回退”的分界。  
   **负控输入**：`note: !!binary "open\nharness_tree: /a/b=="`，其中 `\n` 表示真实换行；真 PyYAML 6.0.3 返回仅含 `note: bytes` 的字典，生产函数却报“解析结果与文件内容不符”；**对照输入**去掉 `!!binary` 后正常回退。

2. **影子门会把不同物理来源消成同一路径。**  
   [SKILL.md:714](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/quiz-answer/SKILL.md:714)：`abspath` 按字符串消除 `symlink/..`，不能证明缓存模块来自选中的树。  
   **未被拦下的输入**：缓存模块源路径为 `/home/app/link/../chosen/backend/scripts/validate_learning_events.py`，`link → /else/leaf`，选树为 `/home/app/chosen`；比较结果相等，实际来源却是 `/else/chosen`，内存验证契约门返回七元组。CPython 会保留这种源路径；本轮未建立实体 symlink。比较目录的 `realpath`，与先解析文件 symlink 再取目录不同，前者不会误拒作者允许的单文件 symlink 布局。

3. **“每条探针都两向”不成立，纯函数语义不同的占位树也能通过。**  
   [SKILL.md:735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/quiz-answer/SKILL.md:735)、`:746–753`：分类、记录校验、扩展识别各只测一个方向，实际保障弱于声明。  
   **未被拦下的输入**：新测试自己的 `_VALIDATOR_STUB_OK`——分类恒返 `new`、扩展识别恒返 `False`、所有字典记录均通过——原样契约函数仍返回七元组；这是不同于已登记旧树的形态，并非“纯函数行为也一样”。

4. **生产预检可能落字节码，零写测试掩盖了这条路径。**  
   [SKILL.md:205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/quiz-answer/SKILL.md:205)、`:703`；[test_harness_tree_parse_r2.py:543](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/backend/tests/skills/test_harness_tree_parse_r2.py:543)：生产没有禁用字节码，测试却强加 `PYTHONDONTWRITEBYTECODE=1`，而快照只检查 vault。  
   **对照输入**：普通 Python、可写且没有有效缓存的 harness；导入可生成 `__pycache__/*.pyc`，外部 harness 又属于快照的**门未覆盖的路径**。已在内存截获加载器的缓存写入意图，没有实际落盘。

**LOW**

1. **部分契约判据删除后，现有契约负控仍全部通过。**  
   [test_harness_tree_parse_r2.py:434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/backend/tests/skills/test_harness_tree_parse_r2.py:434)：表中缺少 `_TS_RE` 负向判据的专属负控；内存删除生产 `:740–741` 后，五格负控结局及底本控制结局全部不变。  
   **负控输入** `_TS_RE = re.compile(".*")` 能区分原版与删除版，但当前表没有它；整秒正则两向、分类与扩展识别的行为检查也有同类**门未覆盖的路径**。

2. **键级探针“零误拒”的声明需要限定为默认加载语义。**  
   [SKILL.md:551](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/quiz-answer/SKILL.md:551)：公开 API 扩展过的真 PyYAML，也可能正确解析配置却被哨兵的字符串等值判断拒绝。  
   **对照输入**：SafeLoader 的路径 resolver 将 `harness_tree` 值构造成 `pathlib.Path`；真实配置原本可经后续 `str()` 使用，探针却得到 `Path("__quiz_answer_key_probe__")`，被误报为“PyYAML 不可用”。默认、未扩展的 PyYAML 未发现这项误拒。

3. **契约探针自身抛异常时，绕过统一拒因与半态说明。**  
   [SKILL.md:746](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w/canvas-vault/.claude/skills/quiz-answer/SKILL.md:746)、`:749`：行为调用位于异常包装之外，仍会拒绝执行，但只留下 traceback。  
   **负控输入**：形状检查通过、调用时抛 `ValueError` 的分类函数；实测传播原始异常，没有“契约不符／分数保留”的说明。

其余指定问题核对如下：

- **⓪、①(c)：探针边界确实存在。** 两探针答对、配置返回无键字典的模块，在引号键／flow mapping 下仍会回退；裸键配置另含 `note: "harness_tree:"` 时，旁观值也能触发豁免。该条件只证明“某处存在相同文本”，没有证明它对应命中的原文位置。按你明确排除的威胁模型，本轮不将其另报 HIGH；但源码 `:487–489` 的“任何谎报无键都防得住”仍强于实际能力。只解析首行的损坏包装器就能产生后一形态，无需专门识别探针。
- **①(a)(b)：默认 SafeLoader 的字符串容器遍历未发现遗漏。** `dict/list/tuple/set` 覆盖其相关结构；上述 `bytes` 问题属于标量转换。遍历期间 `_doc` 持有整棵对象图，正常结构中的节点不会释放，未发现 `id()` 回收复用导致的误判。
- **②(b)：探针取值没有跟随 validator 动态漂移。** 时间戳输入写死，当前指定正则符合预期；问题是覆盖有限，而非期望与实现共同变化。
- **③：指定派生失败均不会静默继续。** 环境变量、读取、块数、函数数异常会非零退出；解码或 AST 错误即使未经包装也会失败。当前分段锚未发现自指遗漏。续跑绕过 Step 2.9，但 `:759/:774` 仍执行最终检查，只失去提前拒绝的机会。
- **④(a)(b)：控制前提有效。** `_truth` 断言在异常捕获之外，不会被吞；四类结局足够区分拒绝／有键／无键／非字典，13 格已全部核对一致。`_honest_probes=True` 确实必要，拒因断言也能证明到达词法层。
- **④(c)：快照不能证明没有发生过写入。** 临时写后删除、等长改写并恢复 mtime、权限或一般目录变化都可能不可见，亦非“逐字节不变”验证。
- **⑤：普通无键／null／空串控制均回退；缺库仍在读取配置前拒绝；打不开回退、打开后读取失败拒绝的分野保持。** 但 MEDIUM-1 是新增的无键误拒例外。

本轮仅做源码审查与禁止字节码落盘的内存验证；未运行 pytest，未修改文件，未连接数据库或网络服务。



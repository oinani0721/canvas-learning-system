> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-RV-G2-6 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-G2-6-r2.md)"`
> 审查绑定: `6bdb0fab`（送审时 HEAD）。⚠️ **本轮之后代码又改了**（1 HIGH + 3 MEDIUM + 3 LOW 整改），故本存档**不绑合并态**；round-3 绑最终 HEAD。
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

本轮**未确认整改新引入的运行时缺陷**，但有一项 HIGH 尚未修完整，新增测试中也有三处防退化缺口。汇总：**0 BLOCKER / 1 HIGH / 4 MEDIUM / 5 LOW**。下文明确区分整改遗漏、遗留问题和测试缺口。

严格使用了指定五处材料；未修改文件、运行安装脚本或读取 live vault。实际执行的是内存检查；涉及权限、文件名和链接的文件系统案例仅作代码推演，未创建夹具或复跑完整 pytest。

**BLOCKER：0**

核对结果：无问题——本轮整改没有新增写被审树的调用，报告写入函数及落点保护未被改动。此结论限于代码审查。

**HIGH：1**

1. **整改遗漏：exclude 的元数据访问失败仍可能被当成“不存在”，绕过新增 unreadable 收集，最终返回 0。**  
   位置：[verify_vault_install.py:492](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:492)，精确 exclude 同类出口在 `:558`。本机 Python 3.14.4 的存在性谓词会吞掉 `OSError`；此处提前返回，根本没有进入 `_walk()` 的错误透传链。  
   复现思路：最小合法清单仅声明 exclude `locked/cache/**`，让实际存在的 `cache` 因祖先目录缺搜索权限而无法 stat；不提供 `--source/--report`，检查是否得到空 unreadable 和 rc=0。

**MEDIUM：4**

1. **遗留问题：两侧均不可读、摘要标记相等时，同一 copy 项仍会计入 match。**  
   位置：[verify_vault_install.py:843](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:843)，最终追加 match 在 `:867`。登记 unreadable 后，只要两个摘要相等就继续记 match；虽然 rc=2，但仍把未证明一致的项计成一致。  
   复现思路：源、目标同名普通文件均设为不可读，使两侧摘要都是 `U:unreadable`，观察 unreadable 与 match 同时增加。

2. **遗留问题：`_printable()` 挡不住到达 render 之前的摘要编码异常，CLI 仍可能错误退出为 1。**  
   位置：[verify_vault_install.py:636](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:636)，同类在 `:582/:631`。文件名和软链目标文本仍直接严格编码 UTF-8，`UnicodeEncodeError` 不属于已捕获的 `OSError`。  
   复现思路：在 `--source` 比较的 copy 子树中放入产生 surrogateescape 字符的文件名或链接文本；本轮已在内存中验证，这些字符串代入三个编码表达式均抛异常。

3. **遗留问题：路径展开失败仍绕过用法错误档，退出码契约尚未覆盖全部出口。**  
   位置：[verify_vault_install.py:1102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1102)，另见 `:1195/:1202`。`expanduser()` 抛出的 `RuntimeError` 未捕获，独立 CLI 会以 1 结束。  
   复现思路：传入带引号的 `--vault '~不存在的账户名'`；内存调用已实测抛异常，应归用法错误 3。

4. **整改不完整：支持三种引号没有消除“部分命令解析失败”的假拦下。**  
   位置：[verify_vault_install.py:981](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:981)，误报发生在 `:995`；复审表 `:88` 的“消除假拦下”表述过宽。  
   复现思路：产物注册 `"canvas:\u0061"` 和普通字面量 `"canvas:b"`，快捷键绑定 `canvas:a`；正则只提取 b，因集合非空而绕过零命令分支，将真实的 a 报成 orphan。此提取结果已在内存验证。

**LOW：5**

1. **新增测试缺口：SKILL.md 目录负控没有单独承重。**  
   位置：[test_vault_install_manifest.py:1467](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1467)。样例只有六个合格文件，错误计入那个同名目录后也仅七个，仍低于阈值八。  
   复现思路：让 find 同时统计普通文件和同名目录，并保留静态断言要求的字符串；正控九个通过、负控七个失败，测试仍绿。目录负控应使用“七个合格文件＋一个目录入口”。

2. **新增测试缺口：“声明路径单一真相源”门没有检验加载侧。**  
   位置：[test_vault_install_manifest.py:1605](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1605)。它比较 helper 与直接调用 helper 的 property，未证明加载侧也遵守同一规则。  
   复现思路：仅让加载侧 `:349` 的独立推导漏掉 generate；本门仍绿，而 `extra_allow=[".canvas-config.yaml"]` 会被错误接受。

3. **新增测试缺口：exclude unreadable 门没有锁住跨项去重。**  
   位置：[test_vault_install_manifest.py:1508](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1508)。单个 outputs 样例及 `any()/next()` 断言允许重复登记，也没有触发两个 exclude 共用失败位置。  
   复现思路：把同一 outputs finding 登记两次，测试仍通过；这条门证明了根目录错误透传，没有证明去重。

4. **文档旧口径仍与当前状态冲突。**  
   位置：[review-c4e6b165.md:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md:67) 仍写 #25“登记，不修”，`:107–108` 却称已经更新；[verify_vault_install.py:109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:109) 等注释仍称配置、报告错误返回 2。  
   复现思路：分别对照表 `:86` 的新处置及代码 `:1207/:1216` 的实际返回 3。

5. **复审表仍把字面量搜索当成了过强的读取范围证据。**  
   位置：[review-c4e6b165.md:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md:20)。`grep 'canvas-vault'` 零命中只能证明没有该字面量，不能“自证”仅访问临时夹具。  
   复现思路：路径来自变量时无需出现该字面量；应将这项证据限定为辅助检查。本轮没有读取其引用脚本或原始日志。

其余核对结果：

- **源端缺项整改：无问题。** 新分支登记 unreadable 后立即继续，不再落入 match；生产代码没有依赖 match 数量决定退出码或其他分类。
- **新出参调用链：无问题。** `_iter_relative → hits_for → verify` 无遗漏；已进入 `_walk()` 的失败能透传，跨 exclude 的相同相对路径会去重。上述 HIGH 位于进入这条链之前。
- **四档桶优先级：无问题。** 实际枚举 **128 种组合全部通过**；缺陷在未捕获异常出口。
- **`_Parser.error()`：无问题。** 缺参数、缺参数值、未知选项和未知位置参数均实测 `SystemExit(3)`；`--help` 保持 0。当前没有子命令，上层没有吞掉 `SystemExit`。
- **render 正文转义：无问题。** 孤立代理 hotkey 实测保留为可见转义，正文可编码 UTF-8，仍为 rc=2。但 CLI 独立提示不经过 `_printable()`，摘要阶段也在其保护范围之外。
- **零命令处理：无问题。** 有绑定而提取零 id 时仍以 unreadable 阻断为 2，没有把真问题放绿；损失的是逐项 orphan 定位，属于已声明取舍。注释、普通字符串或未执行代码中的同形 id 仍可假放行，属于已登记的文本识别限制。
- **收紧后的主要门：无问题。** 反向覆盖参数、hotkeys 行专属断言，以及 orphan／非法 JSON 排除其他阻断桶，均能针对相应退化承重。
- **复审表两项更正：无问题。** 开工快照绑定和 R3-2“预置文件保留不等于发生独占冲突”的限定准确；历史 diff 确有固定随机名的碰撞门。新增测试数量也可从 diff 独立核为 **12 个函数、17 个参数展开用例**。

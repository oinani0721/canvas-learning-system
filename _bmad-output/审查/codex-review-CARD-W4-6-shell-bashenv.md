> 批次: BATCH-2026-09-05-第十二批 · 车道 Y7-B · 卡 CARD-W4-6-shell-bashenv round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-6-shell-bashenv.md)"`
> 审查绑定: `4d56beb0`（HEAD 当时 = 4d56beb0；⚠️ 审后按本轮意见整改，代码树已变 ⇒ **失绑，整改未复审**，见验收单 §九.1）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `provider: openai`

---

只读复核结论：**0 BLOCKER / 0 HIGH / 3 MEDIUM / 3 LOW**。第一层对现有 `printf`、`dirname` 注入样例已经承重，但“全部摘净”“多摘无害”和部分探针归因仍说得过宽。

未修改文件，未运行门或测试。仅重新计算了文件摘要，当前门的 SHA-256 与 after 存档的 `d033b19f…5277` 一致。

1. **MEDIUM — 按行解析环境有歧义，普通多行变量就能导致正常调用假红。**

   **依据：**[门脚本:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:203) 按行生成删除名单；[门脚本:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:229) 又用同样规则判断残留。两处都无法区分环境条目边界与值里的换行。

   **输入形态：**一个普通导出变量，其值包含换行，某个续行以 `BASH_FUNC_` 开头。第一遍只会尝试删除续行代表的名字，携带这段文字的普通变量仍保留；第二遍再次命中，于是 `GATE-BROKEN`、rc=1。**不需要真正的导出函数或主动注入。**

   另外，真实环境变量的**名字本身含 LF** 时，第一遍只能取到名字的第一段，无法准确删除原条目。第二遍通常仍会发现此前缀并拒绝，所以这证明的是“全部摘掉”不成立，**不是已证明整门假绿**。本机 Bash 是否会把这样的名字成功导入为函数，材料不足。

   对其他形态，应分别判断：`-`、`.`、空格、反斜线、通配符不会被这里的 `IFS= read -r` 和带引号数组拆散或展开；函数体续行若误命中，在所属函数条目正确删除后也会消失。普通变量的续行则不会消失。因此，“额外一个不存在名字的 `-u` 无副作用”不能推出整套处理无害。

   **建议处置：**两次读取都使用能准确区分环境条目的方式；补普通多行值与名字含 LF 的边界样例，并修正“多摘安全”的注释。

2. **MEDIUM — 最后一条伪票探针没有钉住导出函数的环境检查，其他拒绝原因也能满足它。**

   **依据：**[探针:903](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_guard_probes.py:903) 保留非空 `BASH_ENV`；票据匹配时，门在 [门脚本:221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:221) 就会拒绝，根本到不了后面的 `BASH_FUNC_*` 扫描。其判据只要求 rc=1 和通用 `GATE-BROKEN`，**票据实际不匹配也能报绿**。

   **输入形态：**匹配当前 PID 的票据，`BASH_ENV`、`ENV` 均为空，仅存在导出函数环境。这才是目前缺少的分支样例。现有用例即使删除函数环境扫描，也仍可能全绿。

   **建议处置：**分别覆盖票据失配、匹配票据加非空 `BASH_ENV`／`ENV`、匹配票据加仅导出函数；断言具体拒绝文案。再以仅删除对应检查的门副本证明各分支承重。

3. **MEDIUM — 两条票据探针的 before 红是协议差异，不能算旧清洗缺陷显形。**

   **依据：**[before 存档:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/_bmad-output/审查/evidence-w4-6/e-before-final-20260906T030829.txt:22) 和 [before 存档:26](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/_bmad-output/审查/evidence-w4-6/e-before-final-20260906T030829.txt:26) 都明确记录 rc=2、用法错误；旧门已经拒绝，没有放行污染或无限重入。

   **输入形态：**向旧门传它不认识的 `--w4-reexec`。新断言要求 rc=1，单凭新增参数协议就足以产生红绿差异。

   **建议处置：**保留为新协议回归测试，但报告区分：前三条证明拆层后的行为差异，第四条证明旧哨兵问题，最后两条验证新协议。后两条的承重证据应来自 after 基线上针对验票、验环境分别做的窄变体。[harness:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/_bmad-output/审查/evidence-w4-6/before-after-harness.py:19) 的说法也应改为“差异来自门版本”，不能直接等同于“旧缺陷被复现”。

4. **LOW — 环境枚举失败没有被识别，空输出会被当作没有残留。**

   **依据：**[门脚本:207](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:207)、[门脚本:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:233) 都通过进程替换读取 `/usr/bin/env`，没有取得生产者退出状态；`pipefail` 不覆盖这个状态。

   **输入形态：**资源或进程故障使枚举无法启动、输出不完整或失败退出。第一遍可能漏摘；第二遍若空输出，`__w4_stale` 仍为空，自洽检查就通过。

   **建议处置：**明确取得枚举成功状态，将失败与“零个匹配条目”区分。第二层仍会清函数并复核，所以这里只能确认第一层检查不完整，不能据此断言整门假绿；具体故障可达性材料不足。

5. **LOW — `builtin`／`file` 补强堵住了当前样例的纯空输出，但全 stdout 子串不是可靠的命令输出证明。**

   **依据：**[探针:845](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_guard_probes.py:845) 搜索整个 stdout；门还会打印完整监视路径，见 [门脚本:501](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:501)。

   **输入形态：**临时目录路径含 `function`，正常类型输出也会被误拒；路径同时含 `builtin` 和 `file`，阳性词就可能来自路径，无法独立证明子命令产生过类型输出。

   **建议处置：**界定被包裹命令的输出区域，逐项精确核对 `printf=builtin`、`dirname=file`，并分别检查两次查询成功。当前存档路径和固定命令没有上述干扰，**此项不推翻当前 PASS**。

6. **LOW — 票据和前言仍有超出实现的保证，应收窄文案。**

   **依据与输入形态：**

   - [门脚本:146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:146) 称“一次性票据”，实际只是公开 PID 字符串等值，没有消费状态。PID 猜中、复用，或进程创建后再构造 argv，都不符合“必须预知尚未创建 PID”的描述。
   - [门脚本:156](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:156) 称同时注入必然拒绝，但检查只观察当前环境。启动代码自行清掉 `BASH_ENV`／`ENV`、留下非导出函数或其他 shell 状态时，环境检查可以通过；第二层仍可能清掉它们。这属于已接受的前置代码执行边界，**无需本卡扩大防御**。
   - [门脚本:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:66) 把“不立即 exit 的那一半”概括为全部关闭，与后文明确排除 `builtin` 劫持不一致。“没有 readonly 变量”也应改为“不继承调用者设置的 readonly 属性”。

   **建议处置：**称为“PID 一致性标记”，明确它不证明发生过清洗；环境检查只保证检查成功时未观察到指定残留；前言只声明已覆盖的注入形态。数字方面，现在列出的 11 个名字内部一致，但函数实际有 12 条 shell 探针；若表示总数，应补列遗漏的 `shell-reexec-sentinel-forged`。

另外，两点可以明确肯定：

- **拆第二层的对照有效，限于当前输入。**[探针:778](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_guard_probes.py:778) 精确删除清函数循环；剩下的函数表复核只能拒绝，无法满足 rc=0、真实路径、`unchanged`。before 存档确实由残留函数检查拒绝，after 成功，支持第一层清掉这些样例，不能推广为所有名字均覆盖。
- **票据失配没有无界重入路径。**只有未声明前哨的分支执行 `exec`；失配在 [门脚本:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y7-w4-settle/backend/scripts/lifespan_isolation_runtime_sha.sh:217) 直接退出。未发现既定范围内仅凭普通伪造参数即可令整门假绿的路径。

**材料不足：**获准读取面不含 `_fake_backend`、`_sh`、`_sh_direct` 的实现，故未独立核验副本构造、完整启动环境及 timeout 配置；也没有跨 Bash 版本、含 LF 名称实际导入为函数的证据。需要对应 helper 全文和绑定解释器的原始输出才能补足。

**作者哪些自述核对后不成立：**“多摘只是无害的空名删除”“完整摘掉全部此前缀变量”“PID 票据是一次性的”“伪票同时注入必然被环境检查拒绝”，以及末条探针足以证明整个环境自洽检查承重，都过宽。“六条 before 红、after 绿”的存档记录成立，但后两条红不能解释为旧缺陷显形；当前样例的第一层承重结论成立。



> 批次: BATCH-2026-09-11-第十四批 · 车道 T8-F · 卡 CARD-PYRIGHT-TAIL round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-TAIL.md)"`
> 审查绑定: `bcd487db`（= 本卡最终 HEAD；`BASE_F` = `f493a4e1`）。绑定核见验收单 §七。
> 会话头自证（抄自 `.stderr`，⚠️ 非前三行——本机 codex 0.153.3 把 model 排在第 5 行、reasoning effort 在第 9 行；`.stderr` 本身不入库，已被 `.gitignore:264` 覆盖）:
> L2 `OpenAI Codex v0.153.3` / L5 `model: gpt-6-astra` / L9 `reasoning effort: ultra`

---

**计数：BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 1。**

绑定 `bcd487db75e697c3cbf6f9c46f80f07a3b74771b`。全程只读，未运行 pyright／pytest／ruff，未连接数据库。

**BLOCKER：无。HIGH：无。**

1. **MEDIUM — [census.md:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md:53)**  
   **问题：**「生产调用方」混用了实际调用数、import／注释命中数和裸名命中数，部分记录只有“有／混合／活”或缺少两列，因此“每条都有实测数字”不成立，无法据此统一判定活／死路径。  
   **独立确认：** 对照第 15–17 行的定义与第 53、55、57、62 行，再检查第三、五、六节的表头；表内实际上没有一条明确列出两个数字 **0** 的“双零”记录。

2. **MEDIUM — [exam_service.py:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/app/services/exam_service.py:84)、[canvas_service.py:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/app/services/canvas_service.py:341)**  
   **问题：** 新注释仍有超出证据的结论：“文件内无读 logging”不能推出“无业务回归”；“生产不可达”也未限定为注释所述的上游 guard 调用链，动态入口仍未获证明。  
   **独立确认：** 阅读限定 diff 的这两处新增文字，分别核对是否排除了模块外属性消费者、绕过所述上游入口的调用；提供的材料没有这类证明，但这也不代表已发现真实动态调用或回归。

3. **MEDIUM — [census.md:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md:27)**  
   **问题：** `git ls-files src = 0` 只能证明没有受跟踪文件，不能独证实际分析文件集不变；第 53 行据此进一步断言运行期“恒 ImportError”也超出了该证据范围。  
   **独立确认：** 绑定提交的 `git ls-tree` 与当前 `git ls-files` 均为空，但不覆盖未跟踪／忽略文件或运行环境中的包，所给 pyright 日志也没有完整分析文件清单；**未发现实际文件集变化，只是“不变”的证明不足。**

4. **LOW — [census.md:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md:34)**  
   **问题：** 全部 diff 中非注释增删行实际为 **3 行**，不是 2 行：除参数行的一删一增，还包括删除配置中的 `"src",`。  
   **独立确认：** 对指定 SHA 范围运行 `git diff -U0`，排除 diff 元数据及纯注释后计数；这是自证表述错误，删除配置本身属于已说明的范围。

其余问题的裁定：

- **⓪ 活路径延期：** 未发现足以认定“本批必须修却漏修”的证据。T-new-7 已明确登记活调用链、失效后果和最高优先级；其延期依据是行为变化需要裁定，并非误判为死路径。两列零计数本身也不能排除别名、回调、反射或路由注入。
- **① ignore 与门覆盖：** 留存日志逐条比对后，除正常行号移动外，唯一消失的诊断就是目标冗余 ignore；确为 **0 errors／81 warnings → 0 errors／80 warnings**。但两套 tests 未重测，测试自身的调用／导入错误及不同分析入口下的诊断差异仍未覆盖；不能据此宣称 tests 增量为零，也不能反向断言删除局部 ignore 已引入新 error。
- **④ T-new-9／10：** 按 census 引述的行级授权，登记不改理由成立；原卡 §〇／§三不在允许读取面内，因此授权条款本身未获独立确认，不能给出完整一致性通过结论。
- **⑤ 等量替换：** 属实。`canvas_service.py` 为 **1／1**，`review_service.py` 为 **3／3**，且各个差异块分别等量，确实没有移动这两个文件其余内容的行号。

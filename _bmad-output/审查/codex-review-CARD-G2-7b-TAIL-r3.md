> 批次: BATCH-2026-09-11-第十四批 · 车道 T2（card-t2-deploy） · 卡 CARD-G2-7b-TAIL round-3 prompt-r3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-TAIL-r3.md)"`
> 审查绑定: `ff9f580c`（Codex 正文首行自行核实为 `ff9f580cbfb7f4e15e2b8da2735cf0ee37d1eb82`，与该轮 HEAD 相同）
> 本轮结论: **BLOCKER 0 / HIGH 0**（D-15 的达标条件在这一轮已成立）；MEDIUM 4 / LOW 1，其中
> MEDIUM-1/2/3 与 LOW-1 由 r4 整改，MEDIUM-4（夹具 lstat→unlink 竞争）如实登记不修。
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

复核绑定 **`ff9f580cbfb7f4e15e2b8da2735cf0ee37d1eb82`**。结论：**整改尚未完全闭合，4 项 MEDIUM、1 项 LOW。**

本次仅做源码核对和纯内存负控；未修改文件，未运行 pytest、hook、部署入口或连接数据库及网络。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：**

1. **残件更正器仍可能把部分追加失败报告为成功。**  
   [scripts/deploy-vault.sh:3374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:3374) 的四条 `printf` 只回传最后一条的状态。核验路径：纯内存负控令前三条失败、末条成功，函数仍返回 `0`；3489／3508 的调用方随后宣称“已标注未发布”，但残件缺少对第六行及 `rc=` 的否定。`set -e` 在这里的条件调用上下文中不能补救。

2. **换行门会误拒归一化后可完整表示的源路径。**  
   [scripts/deploy-vault.sh:2957](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2957) 在 `realpath` 之前检查原始字符串。核验路径：普通目录 `ok<LF>` 存在时，使用 `TMPDIR=/tmp/ok<LF>/..` 和非 8011 端口；报告源路径与应有基准归一化后相等且不含换行，实际回执代码仍返回 `4`，部署映射为 `74`。纯内存对照已确认。

3. **CR 路径仍被截断，并误报为基准不一致。**  
   [scripts/deploy-vault.sh:2945](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2945) 使用通用换行读取，2957 却只检查 LF。核验路径：源基准为 `/tmp/cr<CR>dir/cls-srcmirror-ABC`，回执记录相同路径；实际解析得到 `/tmp/cr`，返回 `1`，未进入字符不可表示的 `4` 分支。前置检查未覆盖这类 `TMPDIR` 输入。

4. **夹具核对 inode 后，仍可能删除别人随后发布的产物。**  
   [backend/tests/unit/test_deploy_vault_sh.py:5827](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5827) 的 `lstat` 与 5832 的 `unlink` 不是同一操作。核验路径：取回自有 inode → 并行构建替换 `main.js` → 执行删除；抽取真实夹具的纯内存调度确认删除的是替换后的 inode。新增源码门仍全部满足，未覆盖这条路径。

**LOW：**

1. **key 临时件删除失败时，消息仍声称“已丢弃”。**  
   [scripts/deploy-vault.sh:2791](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2791) 吞掉 `rm` 的失败。核验路径：key 回读失败，再令删除返回非零，随机临时件仍存在，2792 的消息却断言已丢弃，也未报告残件路径。

其余重点核对结果：

- `_want_src` 未复用 `$src`。8011 下源、目标相同会被回执自身放行，但当前真实入口存在更早的拒绝，不能列为可达的自比漏洞。
- 五处发布均接收 `os.rename` 的失败码；末段目录软链问题已闭合，EXDEV 会失败。中间段软链仍属已声明边界。撤掉旧 `.tmp` 登记未削弱实际终文件的硬链接检查。
- 成功发布时，三类第六行结果与终端一致；sha 失败及“只列已跑步骤”的判断保持成立。
- 链接数三态、A3 引号处理及 ROLE 收窄未发现新增放行输入。祖先门的对照能排除规则 1–4，但只能支持已列样本，不能推出普遍覆盖。



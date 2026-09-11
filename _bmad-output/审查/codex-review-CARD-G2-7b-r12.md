> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7b round-12
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-r12.md)"`
> 审查绑定: `afd7e5fc`（= 最终 HEAD 的代码面；其后的 commit 只动 `_bmad-output`）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`（另 `sandbox: read-only`）

> ⭐ 裁定: **0 BLOCKER / 0 HIGH / 0 MEDIUM / 3 LOW**，明确「**本卡可收敛**」。
> 这是 12 轮以来第一次同时满足 D-15 的两个条件：**绑最终 HEAD** 且 **B/H = 0**。
> 三条 LOW 均判「不阻断收敛」；其中 LOW-3（变异脚本缺绿基线自检）本车道**已修**。

---

核对的四份代码与 `afd7e5fc` 一致。本次未运行部署或 pytest；补证仅使用只读源码检查和内存探针。

**BLOCKER：未发现。**

**HIGH：未发现。**

**MEDIUM：未发现。**

**LOW：3 条，均不阻断本卡收敛。**

1. **非 ASCII 空白兼容性回归** — [scripts/deploy-vault.sh:282](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:282)：在本机 Bash 3.2.57、`en_US.UTF-8`／`zh_CN.UTF-8` 下，U+00A0 或全角空格包围的 `claude`，旧 `tr` 会删除空白并接受，新表达式保留空白、随后 rc 64。ASCII 空白修复成立，但与旧版的 locale 语义并不完全等价。

2. **清理门在空 TMPDIR 下看错目录** — [backend/tests/unit/test_deploy_vault_sh.py:2212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:2212)：继承 `TMPDIR=""` 时，两次快照扫描当前目录，脚本却在 `/tmp` 创建镜像；若清理退化为空操作，镜像残留仍可能绿。测试应采用与 `${TMPDIR:-/tmp}` 相同的空值回退。

3. **变异运行器仍能重现 §二.4 的错误归因** — [mutate_r6.py:319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-g27b/mutate_r6.py:319)、[同文件:347](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-g27b/mutate_r6.py:347)：未变异时已有相同断言失败，仍可能计为 KILLED；探针遇到任何非零退出，甚至没有 FAILED nodeid，也会宣称承重。应先确认绿基线，再核失败归因；本次最终全绿探针没有走这个误判分支。

其余重点的裁定：

- **HARNESS 下游语义：未发现新增问题。** [绝对化:353](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:353)只加 `$PWD/`，保留软链拼写；installer 实参、`CLS_REPO`、`--source`、`--harness-tree`、verify 和 compose `-f`／project directory 均使用同一基准。普通软链目录没有新增偏移；带 `link/..` 的逻辑／物理解析差异是既有边界。
- **两份清单覆盖：未发现因分家漏项。** [调用点:442](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:442)把两数组同时交给判据，只有 `PENDING_WRITES` 再接受叶子规则。此结论不扩大为“全部外部程序写入面已证明”。
- **其它过时源码门仍绿：未发现新增实例。** 重点检查的 `open_pinned`、`fchmod`、`nlink`、祖先／叶子 `O_NOFOLLOW` 锚点都匹配真实语句；内存删改会触发对应断言。上面的清理门属于取样覆盖缺口。
- **§二.6 转卡项：未发现必须升级的依据。** 26 条变异及探针、9 条负控的摘要数量吻合；`173+29=202`、passed 增量 `3` 可复算，红集逐 nodeid 相等仍不能凭限定摘要独立证明。允许材料中未发现疑似真实明文密钥。

**结论：本轮 BLOCKER 0 条、HIGH 0 条；本卡可收敛。**



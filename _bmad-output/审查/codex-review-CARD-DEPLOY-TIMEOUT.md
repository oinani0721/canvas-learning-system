> 批次: BATCH-2026-09-11-第十四批 · 车道 T2-A · 卡 CARD-DEPLOY-TIMEOUT round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEPLOY-TIMEOUT.md)"`
> 审查绑定: `7413283a`（该轮送审时的 HEAD；此后本卡按 D-15 继续整改 ⇒ 最终 HEAD 不同，末轮绑定见 r3 存档）
> 会话头自证（抄 `.stderr` 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；`.stderr` 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

复核结论：**FAIL，1 HIGH / 2 MEDIUM / 3 LOW**。已绑定 `7413283a`，两个源码文件的哈希与负控记录一致。未修改文件、未重跑 pytest；以下复现使用无写盘的独立语义探针。

**BLOCKER：无。**

**HIGH-1：合法通过校验的取值会静默取消墙钟上限。**  
位置：[scripts/deploy-vault.sh:563](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:563)，执行点 `:582`。

**未被拦下的输入**：`CLS_NPM_BUILD_TIMEOUT=0`、`000` 或 `4294967296`，配合永久挂起的 build。本机 `/usr/bin/perl 5.34.1` 实测三者均没有活动闹钟；`4294967297` 则截断为 **1 秒**。`set -euo pipefail` 不会拦截这些正常返回的调用。

**对照输入**：空串经 `:87` 回退到 `300`；`005`、`08` 分别是十进制 5、8 秒，没有八进制问题。[Perl 明确定义 `alarm 0` 为取消闹钟](https://perldoc.perl.org/functions/alarm)。本卡未声明允许关闭保护，因此这不符合其墙钟保证，应校验**有界正整数**。测试侧 600 秒只终止直接子进程，也不能补证 npm 后代已清理。

**MEDIUM-1：同组后台进程能被终止，脱组后代仍可继续运行。**  
位置：[scripts/deploy-vault.sh:580](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:580)、`:581`；测试覆盖点 `test_deploy_vault_sh.py:2698`。

`kill(-15,$pid)`／`kill(-9,$pid)` 的负信号语义**正确，确实向进程组发信号**。[Perl 官方说明](https://perldoc.perl.org/functions/kill)。

**对照输入**：同组孙进程，cap=1，约 3 秒后被清理。**门未覆盖的路径**：孙进程先 `setsid()`；独立探针中 wrapper 仍返回 124，但孙进程在第 4 秒打印存活标记。Node 的 `detached:true` 也可创建新进程组和 session。[Node 官方说明](https://nodejs.org/api/child_process.html#optionsdetached)。这证明能力边界，不能据此断言真实 npm 当前一定脱组。

另一个启动窗口位于 **`fork → setpgrp`**：若子进程建组前被暂停超过 cap+2 秒，两次组信号可能落空，而返回值未检查。此窗口未做严格调度复现；普通 `exec` 本身不会导致脱组。

**MEDIUM-2：立即 rc=124 的普通失败会被误报为超时。**  
位置：[scripts/deploy-vault.sh:588](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:588)，退出码透传点 `:586`。

**未被拦下的输入**：假 npm 立即 `exit 124`。原样 Perl wrapper 在 cap=5 下约 **0.007 秒**返回 124，随后命中“超时、已杀整个进程组”。**对照输入** `exit 1` 正常报失败。因此负控第三段只能区分挂起与 rc=1，不能证明“任意 build 失败”均可区分；需要独立的超时标记。

**LOW-1：离线开关注入正确，但“整个 build 不等网”的说明过强。**  
位置：[scripts/deploy-vault.sh:71](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:71)，注入点 `:574`。

**对照输入**：npm 自身缓存取包路径缺失缓存时，offline 不回退网络请求。**门未覆盖的路径**：`prebuild/build/postbuild` 直接执行 `curl`、Node `fetch` 等；这些仍可能等待网络，截止依赖 alarm。npm 配置不构成包脚本的网络隔离。[npm offline 配置](https://docs.npmjs.com/cli/v11/using-npm/config/#offline)、[npm run 执行语义](https://docs.npmjs.com/cli/v11/commands/npm-run/)。

三条假 npm 用例也未读取或断言该环境变量；删除 `:574` 后，它们仍可通过。

**LOW-2：300∶600 不能保证脚本超时“必定”先于测试超时。**  
位置：[scripts/deploy-vault.sh:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:68)；常量 `test_deploy_vault_sh.py:67`。

**门未覆盖的路径**：build 前已耗时较长，或用户将 build cap 调到超过 600；测试计时覆盖整次调用，alarm 仅覆盖 build，另有 2 秒清理宽限。

对④：`bash -n`、`git log/show`、`docker ps` 的 600 秒偏宽，可缩短反馈，但**没有现有证据要求某一处必须换成特定数值**。daemon 永不响应应报查询超时；完整 `--apply` 的最坏耗时仍未证明。Python timeout 只清理直接 child，不能等同于进程树清场。[Python subprocess 文档](https://docs.python.org/3/library/subprocess.html#subprocess.run)。

**LOW-3：目录级 diff 的负控返回码不符合其验收条件。**  
位置：[unit-diff-20260914T201203.txt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-deploy-timeout/unit-diff-20260914T201203.txt:10)。

**负控输入**：人为少一条 nodeid；记录确实打印了差异，却报告 `probe_diff_rc=0`，预期是 1。这段不足以证明退出码判据能拒绝差异，需要修正取码并补证；本轮未读取其引用的范围外原始日志。

其余核对结果：

- **②未发现真实 build 误触。** [测试 helper:2663](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:2663) 固定创建 tmp harness，假 npm 位于 PATH 首位；脚本的 main.js 检查、构建 cwd、复制目的均取 `$HARNESS`。真实树有无 `main.js` 不改变这三条用例。`FORBID_PY` 来自真实脚本目录，本身不能推出越界写入；其依赖附带写入属于**本门未证明的路径**，两个源码 shasum 也不能证明 tmp 外零写入。
- 差异确认 **16 处新增 `timeout=_SUBPROCESS_TIMEOUT`，既有 4 处未改**；AST 记录与此一致。
- 独立重算 `step2_install` 至 EOF：**33631 bytes，SHA256 `96d10556a71e71c3702fd20ae4cb31f4a1c6acab3cc2b3317e8d40abe5789819`**，基线与审查提交完全相同。步 5／6／主流程零改动属实。
- `139 passed / 9 skipped`、行为先红后绿和 ruff 通过均是已读取的存档结果；本轮没有将其当作重新执行的结果。



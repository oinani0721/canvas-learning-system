**本卡仍不可收敛。**发现一条 HIGH 修复遗漏、一条 MEDIUM 新回归，以及一条 LOW 兼容遗漏。

- **BLOCKER：未发现。**

- **HIGH-1｜默认目录仍绕过绝对化。** [deploy-vault.sh:354](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:354)：输入 `--harness . --apply`、省略 `--evidence-dir` 且需要构建 `main.js` 时，默认值在绝对化**之后**才填入，因此仍为相对路径；`:536` 的创建与 `:538–543` 的 npm 使用分别基于调用目录和插件目录。若插件目录内预置 `_bmad-output -> $HOME/.codex`，npm 会使用未受检的保护区路径，**无需竞争窗口**。这是原 HIGH-1 后半尚未闭合，属于 npm 配置层，必须本卡处理。

- **MEDIUM-1｜合法 TMPDIR 目录软链被新增规则误拒。** [deploy-vault.sh:428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:428)：`TMPDIR=/tmp`，或未设／为空而回退 `/tmp` 时，macOS 的 `/tmp -> /private/tmp` 会被 `:445` 的统一 `-L` 检查拒成 rc 71，dry-run 同样受影响。`:204` 的 `assert_writable_now` 还会再次拒绝，**只改外层检查不够**。这是本轮把目录套入文件叶子规则造成的正常输入回归，应本卡修复。

- **LOW-1｜循环收敛，但没有恢复旧空白删除语义。** [deploy-vault.sh:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:281)：`$'\vclaude\f'`、`$'\rclaude\r'`、`$'cl au\tde'` 经旧 `tr -d '[:space:]'` 可得到 `claude`，当前保留相应字符而 rc 64；非 ASCII 空白还取决于旧命令的 locale，不能宣称等价。这是 r9 遗留、r10 仍未完整修复的兼容差异。

其余指定维度：

- **目录检查旁路：未发现。** `:432–439` 已先执行完整路径判据，`:209` 的 `[ -d ] && return 0` 只跳过目录的文件硬链接计数检查；`--outputs` 仅豁免 env 叶子名称规则，保护根、`.git` 和沿链检查仍执行。
- **合法 `$PWD` 软链导致 Shell／Python 判据分裂：未发现。** 已绝对化的原始路径仍保留软链和 `..`，双方按解链后的路径解释；上面的 HIGH 是**默认值遗漏**。这不等于已证明 npm 内部全部路径规范化行为。
- **空白循环不收敛：未发现。** 每次命中分支至少删除一个字符，有限输入必然结束。
- **preflight 前的 heredoc／进程替换写入：未发现。** 四处 heredoc 执行点为 `:186、807、853、1086`，均在禁写门之后；提前定义函数不会执行其重定向。未见进程替换，普通 `$(...)` 的大输出也不会自动溢写临时文件。有效、稳定的 TMPDIR 下，本脚本已见 heredoc 的执行顺序得到覆盖；无效 TMPDIR 的 Bash 回退及外部程序完整写入集合，在准读面内仍未证明。
- **疑似明文密钥：未发现。**

回归门需要随上述问题补齐：[test_deploy_vault_sh.py:1838](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1838) 只检查标签和源码片段存在，`:1852` 也未实际输入混合空白；它们没有锁住默认值赋值顺序、合法目录软链和完整空白行为。本轮证据还明确记录 **未触发 build 分支**，所以现有正负控不能证明 HIGH-1 已闭合。

§二.6 其余已裁定转卡项，本轮未发现必须升级留卡的新依据；上述 HIGH 不能并入“npm 配置层之外未证明”。`write_all` 的零进度不终止担忧可以关闭：`:226–227` 已对 `n <= 0` 抛错。证据摘要的算术一致，但完整 nodeid 集不在准读面内，M-5 仍应保留。

**结论：本轮 0 BLOCKER / 1 HIGH；本卡尚不可收敛。**



# CARD-DEBT-15 · Codex round-2 复核报告（原文存档）

> **批次**: BATCH-2026-08-29-第六批 / CARD-DEBT-15
> **日期**: 2026-08-30
> **审查命题**: round-1 的 5 BLOCKER + 2 HIGH 是否真的关闭？是否引入新逃逸面？
> **形式**: codex exec --sandbox read-only，自建沙箱注入变异实测
> **裁定**: **仍判 FAIL**——新增 B-05/B-06 两条 BLOCKER + H-01/H-02 + M-01/M-02
> **处置**: 见台账 §3.6「round-2 处置与宣称降级」

---

# BLOCKER

### B-01：ACK 是整来源后门，作者自陈风险已被实际利用

证据：[assert-hook-write-safety.sh:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:107) 将 ACK 锁定为 `<source>::UNANALYZABLE`；[assert-hook-write-safety.sh:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:212) 在核查 evidence 前按该粗键去重。台账也在 [DEBT-15 台账:242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:242) 明确认领此缺口。

可逃逸场景：

```yaml
run: git push "$REMOTE" HEAD
```

收集器实际产生两行同键：

```text
wt-lefthook::UNANALYZABLE  lefthook.yml:32 git add "$schema"
wt-lefthook::UNANALYZABLE  lefthook.yml:257 git push "$REMOTE" HEAD
```

生产断言只显示原 ACK，新增动态 push 被同一 ACK 覆盖：**exit 0，FAIL=0**。

同理，向主 lefthook 添加有效 `extends` 后，本机 `lefthook dump` 确认外部 rogue push 已合并，断言仍 **exit 0**。

修复建议：ACK 必须绑定 `realpath + 文件 SHA-256 + occurrence ordinal/字节区间 + 规范化命令 SHA`；按多重集合核对，禁止在核查前去重。任何新增或变化的不可解析 occurrence 必须成为新键并 FAIL。

### B-02：普通 KEEP/REMOVE 仍不是 occurrence 登记

证据：[scan_git_occurrences.py:228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:228) 把所有具体 pathspec 合并为 `add:path`；[scan_git_occurrences.py:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:244) 的 push 只保留 remote；登记表在 [assert-hook-write-safety.sh:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:91) 直接放行这些粗类。

可逃逸场景，均 **exit 0**：

```sh
git add secret.env
git add -- ':/'
git push origin HEAD:refs/heads/rogue
```

`:/` 已用真实临时仓库验证，会 stage 仓库根与嵌套目录全部文件，却被分类成已 KEEP 的 `add:path`。

修复建议：登记必须包含精确 pathspec、cwd、remote/URL、refspec、force/no-verify 等影响语义的参数，并绑定具体文件 occurrence 和允许数量。不能保留泛化的 `add:path` 或 `push:origin` 通配许可。

### B-03：手写 Shell 状态机对未识别语法静默返回“无写”

证据：[scan_git_occurrences.py:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:125) 只拆 `&& || ; |`；[scan_git_occurrences.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:184) 只认可首部白名单；[scan_git_occurrences.py:280](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:280) 明确忽略 `-c/-e` 内联代码。

以下全部注入真实挂载脚本后 **exit 0，FAIL=0**：

```sh
$(git push rogue-subst HEAD)
true & git push rogue-bg HEAD
printf x | xargs git push rogue-xargs HEAD
sh -c 'git push rogue-shc HEAD'
eval 'git push rogue-eval HEAD'
shopt -s expand_aliases; alias g=git
g push rogue-alias HEAD
git -c alias.p=push p rogue-gitalias HEAD
git -p push rogue-paginate HEAD
(git push rogue-group HEAD)
g\
it push rogue-cont HEAD
```

修复建议：不要继续补字符串特例。使用 Shell AST，并对 command substitution、后台执行、eval、`*-c`、未知 wrapper、动态 executable、别名/函数等不支持节点统一 fail-closed。更稳妥的最小方案是冻结人工核查过的精确脚本字节，文件变化即重新审查。

### B-04：Python/JS 的 EXEC_API 行级白名单既漏报又无法证明执行语义

证据：[scan_git_occurrences.py:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:59) 的 EXEC_API 是关键词正则；[scan_git_occurrences.py:338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:338) 要求 `git` 与执行 API 在同一物理行；[scan_git_occurrences.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:291) 仅删除括号/逗号。

可逃逸场景：

```python
subprocess.run([
    "git",
    "push",
    "rogue-py-multiline",
    "HEAD",
])
os.system("git push rogue-os-system HEAD")
from subprocess import run
run(["git", "push", "rogue-import-run", "HEAD"])
```

以及多行 `spawnSync(...)`、`execSync("git push ...")`：全部 **exit 0**。

修复建议：Python 用 AST、JS/TS 用对应语法树，追踪导入别名和字符串/数组调用；动态拼接或不能证明为非执行的调用必须 FAIL。若不愿实现跨语言数据流分析，就改成精确文件哈希准入。

### B-05：递归闭包存在多个静默终止点

证据：

- [collect_hook_signatures.py:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:77)：`depth > 6` 直接 return；
- [scan_git_occurrences.py:270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:270)：仅认可少数解释器；
- [collect_hook_signatures.py:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:161)：settings 再用扩展名正则提脚本；
- [collect_hook_signatures.py:178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:178)：`parse_inline` 丢弃 scanner 返回的 refs；
- [collect_hook_signatures.py:92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:92)：二进制静默跳过。

实测：

- 深度 7 的 writer：**exit 0**
- 直接执行 `rogue-helper.sh`：**exit 0**
- settings 挂载 `bash rogue.txt`：**exit 0**
- settings exec-form `sh -c ...`：**exit 0**
- 编译的 Mach-O `.git/hooks/pre-commit` 内 `execlp("git",...push...)`：**exit 0**
- 符号链接直接指向文本 writer：**exit 1**，此项未逃逸

修复建议：深度溢出必须发唯一 UNANALYZABLE；保留 inline refs；按 shebang/可读文本而非扩展名发现脚本；直接 executable、未知 wrapper、二进制都必须 fail-closed 或精确哈希准入。visited set/realpath 本身有效，不是当前主要问题。

### B-06：扫描的不是完整有效运行时配置

证据：[collect_hook_signatures.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:291) 只调用固定十类来源；台账先在 [DEBT-15 台账:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:297) 声称全覆盖，随后又在 [DEBT-15 台账:358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:358) 承认 CLI、managed、skill/agent 未解决。

当前 Claude Code 官方文档确认 managed settings、`--settings`、skill/agent frontmatter 都能提供 hooks；本机 `claude --help` 也显示 `--settings`，并实存 5 个带 hooks 的用户 skill 文件。[Claude Hooks reference](https://code.claude.com/docs/en/hooks)，[Claude settings](https://code.claude.com/docs/en/settings)。

实测：

- managed-settings fixture：**exit 0**
- CLI `--settings` fixture：**exit 0**
- skill frontmatter hook：**exit 0**
- plugin `.cmd`：**exit 1**，该子项已修
- 主仓自定义 `core.hooksPath`：**exit 1**，当前拓扑子项已修

Lefthook 还支持多种主/local 配置格式、`extends`、`remotes` 和 `LEFTHOOK_CONFIG`；当前实现只处理 `lefthook.yml` 和 `lefthook-local.yml`。[Lefthook configuration](https://lefthook.dev/configuration/)，[extends](https://lefthook.dev/configuration/extends/)。

本机 `lefthook dump` 已证明以下 rogue push 是有效合并结果，但断言均 **exit 0**：

- `lefthook-local.yaml`
- `lefthook-local.yml -> extends -> rogue-extend.yml`
- 主 `lefthook.yml -> extends -> rogue-main-extend.yml`（被 ACK 放行）

LaunchAgent 的 argv 也未按整体命令解析：[collect_hook_signatures.py:260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:260) 只逐个扫描绝对路径参数。

```text
ProgramArguments = ["/usr/bin/git","push","rogue-launch-git","HEAD"]
ProgramArguments = ["/bin/sh","-c","git push rogue-launch-shc HEAD"]
```

两者均 **exit 0**。binary plist 指向文本脚本则 **exit 1**，说明 plistlib 本身修复有效，但 argv 语义未修。

修复建议：以有效运行时清单为输入：Claude `/hooks`/setting sources 导出、managed/MDM/server 状态、CLI flags、skill/agent、启用插件；主仓和 worktree 分别解析 hooksPath；lefthook 使用 `dump` 的合并结果并覆盖全部格式/环境覆盖；LaunchAgent 按 `Program + ProgramArguments` 完整 argv 分析。无法取得运行时来源时必须输出 UNVERIFIED/FAIL。

# HIGH

### H-01：新解析器引入明显误报

证据：[scan_git_occurrences.py:352](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:352) 在 Python/JS 中只要同一行出现 EXEC_API 词和独立 `git` token 就向后搜；[collect_hook_signatures.py:235](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:235) 扫描 hooks 目录所有普通文件，不校验可执行位或合法 Git hook 名。

可逃逸/误报场景：

```python
payload = ["subprocess", "git", "push", "rogue-data"]
```

纯数据却 **exit 1**。

```sh
cat <<'DOC'
git push rogue-heredoc-doc HEAD
DOC
```

只是 heredoc 文本，却 **exit 1**。

非可执行、非 Git hook 名的 `.git/hooks/NOT-A-GIT-HOOK` 也被判 **exit 1**。

修复建议：语法树判执行节点；区分 heredoc consumer；Git hooks 只纳入 Git 支持的 hook 名及可执行文件，同时对异常二进制走 fail-closed/hash 准入。

### H-02：N0–N16 不能支撑总体结论

证据：

- [verify-hook-write-safety-negative.sh:41](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:41) 的 N0 创建空 LaunchAgents/plugins，而非复制真实有效来源；
- [verify-hook-write-safety-negative.sh:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:95) 的 N0 原则正确，但只是缩减沙箱基线；
- [verify-hook-write-safety-negative.sh:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:193) 的 N6 不检查 assertion exit code，且 grep 的还是旧签名形状；
- [verify-hook-write-safety-negative.sh:340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:340) 的 N12 只检查 commit，未断言“两条 occurrence 都出现”；
- 各负例主要检查“非零 RC + marker 在输出任意位置”，没有要求对应 marker 本身是 `[FAIL]`。

另外，“17 个负例”计数不准确：N0 是正基线，N6 是反向误报控制。

修复建议：表驱动单变异测试；每例要求精确 `[FAIL] <occurrence fingerprint>`、预期 FAIL 数和无额外 FAIL；N0 使用完整有效来源快照。补入本轮全部 exit-0 样例和三类误报控制。

# MEDIUM

### M-01：`exit 0 / 全门通过` 混淆“登记吻合”与“安全”

[assert-hook-write-safety.sh:216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:216) 对 REMOVE 只 WARN；[assert-hook-write-safety.sh:289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:289) 在四条危险 auto-sync 仍存在时打印“全门通过”。

实测生产状态：`WARN=4` 但 **exit 0**。

修复建议：至少分成 `INVENTORY_MATCH`、`KNOWN_UNSAFE`、`SAFE` 三种状态；不能把有 REMOVE 写链的状态称为安全 PASS。

### M-02：ACK 依据表述与实况矛盾

台账 [DEBT-15 台账:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:244) 称每条 ACK 对应文件写计数为 0；但 `main-lefthook` 明确有 add/push，`wt-lefthook` 有 add，`daily-brief` 有 add/commit。当前实际是 17 个边界 occurrence、12 个唯一粗键、15 个登记 ACK，并非 15 条逐 occurrence 证据。

修复建议：逐 ACK 绑定具体 occurrence 和人工核查摘要，删除未触发历史 ACK；禁止用“该文件无 git 写”作为整源授权理由。

# LOW / INFO

- **INFO**：生产断言最终复跑仍为 `PASS=29 WARN=4 FAIL=0 / exit 0`；官方 N0–N16 runner 为 `exit 0`，其精确 round-1 字符串回归确实有效。
- **INFO**：真实 macOS file-based managed settings 当前不存在；server-managed/MDM 是否生效本轮无法从静态脚本确认，应标 `UNVERIFIED`，不能据此当作无 hook。
- **INFO**：符号链接到文本 writer 被正确追踪并 `exit 1`；visited set 未发现独立逃逸。
- **INFO**：所有对抗变异均位于自动清理的临时目录；未执行任何真实 hook、stage、commit 或 push。

## 最小成立修复集合

不是再补几条正则，而是以下四项缺一不可：

1. **精确身份登记**：KEEP/REMOVE/ACK 都绑定来源 realpath、文件 SHA、occurrence 字节/AST 指纹、完整参数和 occurrence 数量；新增或变化即 FAIL。
2. **有效运行时清单**：覆盖 managed/CLI/skill/agent/启用插件、main+WT hooksPath、lefthook dump 全合并结果、LaunchAgent 完整 argv；取不到有效清单就 FAIL/UNVERIFIED。
3. **解析边界真正 fail-closed**：深度溢出、动态命令、`eval`/`sh -c`/命令替换、未知 wrapper/扩展、二进制、跨语言动态调用不能静默忽略。若无法可靠分析，采用精确字节准入。
4. **补强证明集**：加入本轮所有 exit-0 逃逸和误报控制，并精确断言违规 fingerprint 自身导致 FAIL。

在这四项完成前，正确结论仍是：

> 该脚本只能证明“被当前扫描器识别、且没有命中粗登记/整源 ACK 的签名会 FAIL”；不能证明“未登记的自动 stage/commit/push 都会被看见并 FAIL”。DEBT-15 应继续判 **FAIL**。


tokens used
363,402
结论：**FAIL。DEBT-15 仍不足以支撑“未登记的 auto stage/commit/push 都会被看见并 FAIL”。**

当前生产断言确实是 `PASS=29 WARN=4 FAIL=0 / exit 0`；官方负验证也确实是 `N0–N16 17/17 / runner exit 0`。但新增对抗样例中存在大量稳定 `exit 0` 假绿，尤其是 ACK 整源放行、粗签名复用、Shell/Python/JS 解析逃逸、运行时来源缺失。

审查绑定：`card/t3-hooks @ e31b6dea`；四个脚本与 HEAD 一致。审查期间台账有外部未提交修改，我未改动或清理它。

## Round-1 七项复核

| Round-1 项 | 状态 | 实跑结果 |
|---|---|---|
| B1 签名粒度 | **PARTIALLY-CLOSED** | 原例 `git add -A`：N11 断言 `exit 1`。但 `git add secret.env`、全仓 pathspec `git add -- ':/'` 均 `exit 0`；后者在真实临时 Git 仓库把根目录和嵌套文件全部 stage。 |
| B2 一行多命令 | **PARTIALLY-CLOSED** | `commit && push`：N12 `exit 1`；`rogue # origin`：`exit 1`。但 `true & git push rogue-bg HEAD` 为 `exit 0`。 |
| B3 链/引号/全局选项 | **PARTIALLY-CLOSED** | `echo && git`：N13 `exit 1`；`"git"`、`git -C`：N14 `exit 1`。但 `$()`、子 shell、`git -p`、换行拼接均 `exit 0`。 |
| B4 闭包/exec-form | **PARTIALLY-CLOSED** | 一级 `bash child.sh`：N15 `exit 1`；直接 `command=git,args=...`：N16 `exit 1`。深度 7、直接执行脚本、未知扩展名、`sh -c` args 均 `exit 0`。 |
| B5 覆盖面 | **PARTIALLY-CLOSED** | 插件内联与 `.cmd` 均 `exit 1`。managed settings、CLI `--settings`、skill frontmatter 分别 `exit 0`。 |
| H6 运行时语义 | **PARTIALLY-CLOSED** | 自定义主仓 hooksPath、binary plist 指向文本脚本均 `exit 1`。LaunchAgent exec-form、有效 lefthook local/extends 均 `exit 0`。 |
| H7 负例证明力 | **STILL-OPEN** | 官方 runner 是 `exit 0`，但未覆盖下面的假绿矩阵，不能推出总体结论。 |

没有一项在其完整安全主张上达到 CLOSED；只是 round-1 的若干精确字符串已被回归锁住。

# BLOCKER

### B-01：ACK 是整来源后门，作者自陈风险已被实际利用

证据：[assert-hook-write-safety.sh:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:107) 将 ACK 锁定为 `<source>::UNANALYZABLE`；[assert-hook-write-safety.sh:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:212) 在核查 evidence 前按该粗键去重。台账也在 [DEBT-15 台账:242](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:242) 明确认领此缺口。

可逃逸场景：

```yaml
run: git push "$REMOTE" HEAD
```

收集器实际产生两行同键：

```text
wt-lefthook::UNANALYZABLE  lefthook.yml:32 git add "$schema"
wt-lefthook::UNANALYZABLE  lefthook.yml:257 git push "$REMOTE" HEAD
```

生产断言只显示原 ACK，新增动态 push 被同一 ACK 覆盖：**exit 0，FAIL=0**。

同理，向主 lefthook 添加有效 `extends` 后，本机 `lefthook dump` 确认外部 rogue push 已合并，断言仍 **exit 0**。

修复建议：ACK 必须绑定 `realpath + 文件 SHA-256 + occurrence ordinal/字节区间 + 规范化命令 SHA`；按多重集合核对，禁止在核查前去重。任何新增或变化的不可解析 occurrence 必须成为新键并 FAIL。

### B-02：普通 KEEP/REMOVE 仍不是 occurrence 登记

证据：[scan_git_occurrences.py:228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:228) 把所有具体 pathspec 合并为 `add:path`；[scan_git_occurrences.py:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:244) 的 push 只保留 remote；登记表在 [assert-hook-write-safety.sh:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:91) 直接放行这些粗类。

可逃逸场景，均 **exit 0**：

```sh
git add secret.env
git add -- ':/'
git push origin HEAD:refs/heads/rogue
```

`:/` 已用真实临时仓库验证，会 stage 仓库根与嵌套目录全部文件，却被分类成已 KEEP 的 `add:path`。

修复建议：登记必须包含精确 pathspec、cwd、remote/URL、refspec、force/no-verify 等影响语义的参数，并绑定具体文件 occurrence 和允许数量。不能保留泛化的 `add:path` 或 `push:origin` 通配许可。

### B-03：手写 Shell 状态机对未识别语法静默返回“无写”

证据：[scan_git_occurrences.py:125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:125) 只拆 `&& || ; |`；[scan_git_occurrences.py:184](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:184) 只认可首部白名单；[scan_git_occurrences.py:280](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:280) 明确忽略 `-c/-e` 内联代码。

以下全部注入真实挂载脚本后 **exit 0，FAIL=0**：

```sh
$(git push rogue-subst HEAD)
true & git push rogue-bg HEAD
printf x | xargs git push rogue-xargs HEAD
sh -c 'git push rogue-shc HEAD'
eval 'git push rogue-eval HEAD'
shopt -s expand_aliases; alias g=git
g push rogue-alias HEAD
git -c alias.p=push p rogue-gitalias HEAD
git -p push rogue-paginate HEAD
(git push rogue-group HEAD)
g\
it push rogue-cont HEAD
```

修复建议：不要继续补字符串特例。使用 Shell AST，并对 command substitution、后台执行、eval、`*-c`、未知 wrapper、动态 executable、别名/函数等不支持节点统一 fail-closed。更稳妥的最小方案是冻结人工核查过的精确脚本字节，文件变化即重新审查。

### B-04：Python/JS 的 EXEC_API 行级白名单既漏报又无法证明执行语义

证据：[scan_git_occurrences.py:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:59) 的 EXEC_API 是关键词正则；[scan_git_occurrences.py:338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:338) 要求 `git` 与执行 API 在同一物理行；[scan_git_occurrences.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:291) 仅删除括号/逗号。

可逃逸场景：

```python
subprocess.run([
    "git",
    "push",
    "rogue-py-multiline",
    "HEAD",
])
os.system("git push rogue-os-system HEAD")
from subprocess import run
run(["git", "push", "rogue-import-run", "HEAD"])
```

以及多行 `spawnSync(...)`、`execSync("git push ...")`：全部 **exit 0**。

修复建议：Python 用 AST、JS/TS 用对应语法树，追踪导入别名和字符串/数组调用；动态拼接或不能证明为非执行的调用必须 FAIL。若不愿实现跨语言数据流分析，就改成精确文件哈希准入。

### B-05：递归闭包存在多个静默终止点

证据：

- [collect_hook_signatures.py:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:77)：`depth > 6` 直接 return；
- [scan_git_occurrences.py:270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:270)：仅认可少数解释器；
- [collect_hook_signatures.py:161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:161)：settings 再用扩展名正则提脚本；
- [collect_hook_signatures.py:178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:178)：`parse_inline` 丢弃 scanner 返回的 refs；
- [collect_hook_signatures.py:92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:92)：二进制静默跳过。

实测：

- 深度 7 的 writer：**exit 0**
- 直接执行 `rogue-helper.sh`：**exit 0**
- settings 挂载 `bash rogue.txt`：**exit 0**
- settings exec-form `sh -c ...`：**exit 0**
- 编译的 Mach-O `.git/hooks/pre-commit` 内 `execlp("git",...push...)`：**exit 0**
- 符号链接直接指向文本 writer：**exit 1**，此项未逃逸

修复建议：深度溢出必须发唯一 UNANALYZABLE；保留 inline refs；按 shebang/可读文本而非扩展名发现脚本；直接 executable、未知 wrapper、二进制都必须 fail-closed 或精确哈希准入。visited set/realpath 本身有效，不是当前主要问题。

### B-06：扫描的不是完整有效运行时配置

证据：[collect_hook_signatures.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:291) 只调用固定十类来源；台账先在 [DEBT-15 台账:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:297) 声称全覆盖，随后又在 [DEBT-15 台账:358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:358) 承认 CLI、managed、skill/agent 未解决。

当前 Claude Code 官方文档确认 managed settings、`--settings`、skill/agent frontmatter 都能提供 hooks；本机 `claude --help` 也显示 `--settings`，并实存 5 个带 hooks 的用户 skill 文件。[Claude Hooks reference](https://code.claude.com/docs/en/hooks)，[Claude settings](https://code.claude.com/docs/en/settings)。

实测：

- managed-settings fixture：**exit 0**
- CLI `--settings` fixture：**exit 0**
- skill frontmatter hook：**exit 0**
- plugin `.cmd`：**exit 1**，该子项已修
- 主仓自定义 `core.hooksPath`：**exit 1**，当前拓扑子项已修

Lefthook 还支持多种主/local 配置格式、`extends`、`remotes` 和 `LEFTHOOK_CONFIG`；当前实现只处理 `lefthook.yml` 和 `lefthook-local.yml`。[Lefthook configuration](https://lefthook.dev/configuration/)，[extends](https://lefthook.dev/configuration/extends/)。

本机 `lefthook dump` 已证明以下 rogue push 是有效合并结果，但断言均 **exit 0**：

- `lefthook-local.yaml`
- `lefthook-local.yml -> extends -> rogue-extend.yml`
- 主 `lefthook.yml -> extends -> rogue-main-extend.yml`（被 ACK 放行）

LaunchAgent 的 argv 也未按整体命令解析：[collect_hook_signatures.py:260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:260) 只逐个扫描绝对路径参数。

```text
ProgramArguments = ["/usr/bin/git","push","rogue-launch-git","HEAD"]
ProgramArguments = ["/bin/sh","-c","git push rogue-launch-shc HEAD"]
```

两者均 **exit 0**。binary plist 指向文本脚本则 **exit 1**，说明 plistlib 本身修复有效，但 argv 语义未修。

修复建议：以有效运行时清单为输入：Claude `/hooks`/setting sources 导出、managed/MDM/server 状态、CLI flags、skill/agent、启用插件；主仓和 worktree 分别解析 hooksPath；lefthook 使用 `dump` 的合并结果并覆盖全部格式/环境覆盖；LaunchAgent 按 `Program + ProgramArguments` 完整 argv 分析。无法取得运行时来源时必须输出 UNVERIFIED/FAIL。

# HIGH

### H-01：新解析器引入明显误报

证据：[scan_git_occurrences.py:352](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/scan_git_occurrences.py:352) 在 Python/JS 中只要同一行出现 EXEC_API 词和独立 `git` token 就向后搜；[collect_hook_signatures.py:235](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/lib/collect_hook_signatures.py:235) 扫描 hooks 目录所有普通文件，不校验可执行位或合法 Git hook 名。

可逃逸/误报场景：

```python
payload = ["subprocess", "git", "push", "rogue-data"]
```

纯数据却 **exit 1**。

```sh
cat <<'DOC'
git push rogue-heredoc-doc HEAD
DOC
```

只是 heredoc 文本，却 **exit 1**。

非可执行、非 Git hook 名的 `.git/hooks/NOT-A-GIT-HOOK` 也被判 **exit 1**。

修复建议：语法树判执行节点；区分 heredoc consumer；Git hooks 只纳入 Git 支持的 hook 名及可执行文件，同时对异常二进制走 fail-closed/hash 准入。

### H-02：N0–N16 不能支撑总体结论

证据：

- [verify-hook-write-safety-negative.sh:41](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:41) 的 N0 创建空 LaunchAgents/plugins，而非复制真实有效来源；
- [verify-hook-write-safety-negative.sh:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:95) 的 N0 原则正确，但只是缩减沙箱基线；
- [verify-hook-write-safety-negative.sh:193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:193) 的 N6 不检查 assertion exit code，且 grep 的还是旧签名形状；
- [verify-hook-write-safety-negative.sh:340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:340) 的 N12 只检查 commit，未断言“两条 occurrence 都出现”；
- 各负例主要检查“非零 RC + marker 在输出任意位置”，没有要求对应 marker 本身是 `[FAIL]`。

另外，“17 个负例”计数不准确：N0 是正基线，N6 是反向误报控制。

修复建议：表驱动单变异测试；每例要求精确 `[FAIL] <occurrence fingerprint>`、预期 FAIL 数和无额外 FAIL；N0 使用完整有效来源快照。补入本轮全部 exit-0 样例和三类误报控制。

# MEDIUM

### M-01：`exit 0 / 全门通过` 混淆“登记吻合”与“安全”

[assert-hook-write-safety.sh:216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:216) 对 REMOVE 只 WARN；[assert-hook-write-safety.sh:289](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:289) 在四条危险 auto-sync 仍存在时打印“全门通过”。

实测生产状态：`WARN=4` 但 **exit 0**。

修复建议：至少分成 `INVENTORY_MATCH`、`KNOWN_UNSAFE`、`SAFE` 三种状态；不能把有 REMOVE 写链的状态称为安全 PASS。

### M-02：ACK 依据表述与实况矛盾

台账 [DEBT-15 台账:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:244) 称每条 ACK 对应文件写计数为 0；但 `main-lefthook` 明确有 add/push，`wt-lefthook` 有 add，`daily-brief` 有 add/commit。当前实际是 17 个边界 occurrence、12 个唯一粗键、15 个登记 ACK，并非 15 条逐 occurrence 证据。

修复建议：逐 ACK 绑定具体 occurrence 和人工核查摘要，删除未触发历史 ACK；禁止用“该文件无 git 写”作为整源授权理由。

# LOW / INFO

- **INFO**：生产断言最终复跑仍为 `PASS=29 WARN=4 FAIL=0 / exit 0`；官方 N0–N16 runner 为 `exit 0`，其精确 round-1 字符串回归确实有效。
- **INFO**：真实 macOS file-based managed settings 当前不存在；server-managed/MDM 是否生效本轮无法从静态脚本确认，应标 `UNVERIFIED`，不能据此当作无 hook。
- **INFO**：符号链接到文本 writer 被正确追踪并 `exit 1`；visited set 未发现独立逃逸。
- **INFO**：所有对抗变异均位于自动清理的临时目录；未执行任何真实 hook、stage、commit 或 push。

## 最小成立修复集合

不是再补几条正则，而是以下四项缺一不可：

1. **精确身份登记**：KEEP/REMOVE/ACK 都绑定来源 realpath、文件 SHA、occurrence 字节/AST 指纹、完整参数和 occurrence 数量；新增或变化即 FAIL。
2. **有效运行时清单**：覆盖 managed/CLI/skill/agent/启用插件、main+WT hooksPath、lefthook dump 全合并结果、LaunchAgent 完整 argv；取不到有效清单就 FAIL/UNVERIFIED。
3. **解析边界真正 fail-closed**：深度溢出、动态命令、`eval`/`sh -c`/命令替换、未知 wrapper/扩展、二进制、跨语言动态调用不能静默忽略。若无法可靠分析，采用精确字节准入。
4. **补强证明集**：加入本轮所有 exit-0 逃逸和误报控制，并精确断言违规 fingerprint 自身导致 FAIL。

在这四项完成前，正确结论仍是：

> 该脚本只能证明“被当前扫描器识别、且没有命中粗登记/整源 ACK 的签名会 FAIL”；不能证明“未登记的自动 stage/commit/push 都会被看见并 FAIL”。DEBT-15 应继续判 **FAIL**。



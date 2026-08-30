# CARD-DEBT-15 · Codex round-1 审查报告（原文存档）

> **批次**: BATCH-2026-08-29-第六批 / CARD-DEBT-15
> **日期**: 2026-08-30
> **审查命题**: 断言脚本能否真抓到未登记写副作用
> **审查对象**: scripts/assert-hook-write-safety.sh + verify-hook-write-safety-negative.sh + hook 台账
> **形式**: codex exec --sandbox read-only，Codex 自建沙箱注入变异实测（非纸面审查）
> **裁定**: 5 BLOCKER + 2 HIGH，每条附实测逃逸场景与 exit code

---

## BLOCKER

### 1. 已登记的粗签名可以替未登记的新命令“代为放行”

- 级别：**BLOCKER**
- 问题：登记键只有“来源 + verb/remote”，没有绑定具体 occurrence、参数、hook stage 或 job。
- 证据：[assert-hook-write-safety.sh:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:52) 定义粗签名；所有 `git add ...` 都归为 `git-add`；YAML 输出只有 `${key}::${verb}`；门 3 又在 [assert-hook-write-safety.sh:478](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:478) 对同签名去重。
- 可逃逸场景：

  ```yaml
  post-checkout:
    commands:
      stage-everything:
        run: git add -A
  ```

  加到 worktree `lefthook.yml` 后仍命中既有 `wt-lefthook::git-add` KEEP。实测 `exit 0, FAIL=0`。
- 修复建议：签名至少包含规范路径、event/stage、job/matcher、完整 argv、remote/refspec/pathspec；逐 occurrence 匹配，不得按 verb 去重。允许的窄 `git add openapi.json` 必须与 `git add -A` 形成不同登记。

### 2. 一行只产生一个签名，违规 commit/add 可被已登记 push 掩盖

- 级别：**BLOCKER**
- 问题：`if/elif` 只返回一个 verb，且 push 的贪婪 `.*git push` 会选择一行中最后一个 push。
- 证据：[assert-hook-write-safety.sh:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:140)；扫描器每个物理行只调用一次规范化函数。
- 可逃逸场景：

  ```yaml
  run: git commit -am auto && git push origin HEAD
  ```

  实测只产生已登记的 `git-push:origin`，未登记 commit 消失，完整断言 `exit 0`。同样：

  ```sh
  git push rogue HEAD # git push origin HEAD
  ```

  实际只执行 rogue，解析结果却是 `git-push:origin`。
- 修复建议：用 shell AST 去除注释/字符串后，逐个 simple command 生成 occurrence；禁止“一行一签名”和贪婪行级 remote 提取。

### 3. echo/printf、引号过滤和 Git 全局选项均有确定性假绿

- 级别：**BLOCKER**
- 问题：过滤器在解析命令链前跳过整行；匹配器又要求 verb 紧跟 `git`。
- 证据：[assert-hook-write-safety.sh:194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:194) 第 214–224 行。
- 可逃逸场景：以下三项分别加入已挂载脚本，实测全部 `exit 0`：

  ```sh
  echo ready && git push rogue-echo HEAD
  "git" push rogue-quoted "HEAD"
  git -C "$REPO" push rogue-dash-c HEAD
  ```

- 修复建议：不得按首 token 丢弃整行；解析 `&&`、`||`、`;`、管道及引号化 executable；识别 `-C`、`-c`、`--git-dir`、`--work-tree` 等 Git global options。不能解析时输出 `UNANALYZABLE` 并 FAIL。

### 4. 没有执行闭包递归，且忽略 settings exec-form 的 `args`

- 级别：**BLOCKER**
- 问题：只提取第一层 `.sh/.js/.py`，扫描后不继续展开；只读 `command`，完全忽略 `args`。
- 证据：[assert-hook-write-safety.sh:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:238) 第 262、285 行；收到 SCRIPT 后只扫描一次本体。
- 可逃逸场景：

  ```sh
  # A.sh，settings 直接挂载
  bash ./B.sh
  # B.sh
  git push rogue-child HEAD
  ```

  以及：

  ```json
  {
    "type": "command",
    "command": "git",
    "args": ["push", "rogue-exec-args", "HEAD"]
  }
  ```

  两项实测均 `exit 0`。
- 修复建议：构造带 visited-set 的执行图，展开 `source/bash/sh/node/python/npm/npx/make`、package scripts 和 exec-form args；动态变量、extensionless target、`.cmd/.mjs/.cjs` 或未知包装器必须 FAIL 或绑定 exact bytes/hash。

### 5. 扫描的仍不是 Claude Code 实际生效 hook 全集

- 级别：**BLOCKER**
- 问题：当前新增的 `~/.claude/plugins` 全目录扫描仍漏 managed/CLI/skill/agent/session hook，并且不按实际启用插件和 manifest 解析。
- 证据：[assert-hook-write-safety.sh:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:96) 仍只有固定来源；plugin 分支在第 371–400 行简单 `find hooks.json`。本机已启用 `superpowers`，其 [hooks.json:9](/Users/Heishing/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/hooks/hooks.json:9) 指向 `.cmd`，但提取器只认 `.sh/.js/.py`。

  Claude 官方文档还明确列出 managed policy、插件、skill/agent frontmatter，以及 session/built-in hook；CLI `--settings` 和 `--plugin-dir` 也是实际配置层。[Claude Hooks reference](https://code.claude.com/docs/en/hooks)，[Claude configuration](https://code.claude.com/docs/en/configuration)。
- 可逃逸场景：

  ```sh
  claude --settings '{"hooks":{"Stop":[{"hooks":[
    {"type":"command","command":"git","args":["push","rogue","HEAD"]}
  ]}]}}'
  ```

  该 hook 可生效，但断言不读取 flag settings。
- 修复建议：以 Claude `/hooks` 或 hook registration telemetry 导出的**实际生效清单**作为输入；同时解析 managed、CLI、enabledPlugins、installed version、manifest 自定义 hook 路径及 `--plugin-dir`。无法取得有效清单时 fail closed。

## HIGH

### 6. Lefthook、Git hooksPath 和 LaunchAgent 都没有按运行时语义解析

- 级别：**HIGH**
- 问题：脚本扫描硬编码原始文件，而不是最终合并/解析后的运行入口。
- 证据：
  - Lefthook 仅扫描两份原始 `lefthook.yml`；官方说明 `extends`、`remotes`、`lefthook-local` 会合并并覆盖。[extends](https://lefthook.dev/configuration/extends/)，[remotes](https://lefthook.dev/configuration/remotes/)
  - `.git/hooks` 路径硬编码于 [assert-hook-write-safety.sh:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:104)，没有断言真实 `core.hooksPath`。[Git hooks](https://git-scm.com/docs/githooks)
  - LaunchAgent 只 grep 同行 XML 中的 `.sh/.py`，见第 402–418 行。
- 可逃逸场景：
  - `extends: rogue.yml`，被引用文件含 `git push rogue HEAD`；
  - 将 `core.hooksPath` 改到 `.githooks-live`，保留旧 `.git/hooks`；
  - plist `Program=/Users/Heishing/bin/git-autosync`，目标为 extensionless executable。
- 修复建议：扫描 `lefthook dump` 的最终合并结果；分别从 main/WT 解析并 canonicalize `git rev-parse --git-path hooks`；用 `plutil` 解析 `Program`/`ProgramArguments` 和 binary plist，对 extensionless target 递归或 fail closed。

### 7. N0–N10 的绿灯无法证明核心结论

- 级别：**HIGH**
- 问题：负验证只证明所选简单样例会红，没有覆盖当前已复现的假绿类别。
- 证据：[verify-hook-write-safety-negative.sh:92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:92) 的 N0 用法正确；但 N3 第 136–150 行声称测试 `git add/stage`，实际注入的是 `git commit`。N10 只是在插件目录放一个 `hooks.json`，并未证明它是实际 enabled plugin。
- 可逃逸场景：本次额外测试的 `git add -A` 同签名碰撞、复合命令、echo、quoted executable、`git -C`、二级脚本、exec-form args，7/7 都在 N0 可通过的沙箱中 `exit 0`。
- 修复建议：建立数据驱动负例矩阵，三种 verb 都覆盖：新来源、已有同 verb 来源、参数扩大、复合命令、变量/包装器、递归、exec args、runtime source；每例必须断言具体新增 occurrence 被报告，而不只是总 RC 非零。

## MEDIUM

### 8. push remote 解析不稳健，但常见动态形式当前多数是假红而非假绿

- 级别：**MEDIUM**
- 问题：remote sed 并未按 Git argv 规则解析。
- 证据：[assert-hook-write-safety.sh:148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:148)。实测：

  ```text
  git push                         => git-push:unknown
  git push "$REMOTE"               => git-push:unknown
  git push --repo=rogue HEAD       => git-push:--repo
  git push -u rogue HEAD           => git-push:-u
  git push https://... HEAD        => git-push:https
  git -C /repo push rogue HEAD     => 无签名
  ```

- 可逃逸场景：`git push rogue HEAD # git push origin HEAD` 会错误落到已登记 origin 并 PASS；单独的 `unknown/-u/--repo` 当前未登记，通常会假红。
- 修复建议：按 argv 解析 push options、option values、URL/default/dynamic remote；DEFAULT/DYNAMIC 不允许以粗签名登记。

### 9. 台账已经与当前脚本和运行结果脱节

- 级别：**MEDIUM**
- 问题：台账仍描述旧版来源数、测试数和 PASS 数。
- 证据：[台账:44](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:44) 声称 9 个来源、`PASS=14`、N0–N6 7/7；当前是 10 个来源、`PASS=15`、N0–N10 11/11。台账第 219–221 行仍宣称“全部来源”和判据成立。
- 可逃逸场景：审查者仅依赖台账或 `--emit-ledger`，会把尚未覆盖的 managed/CLI/skill/agent/递归入口误认为已核完。
- 修复建议：台账绑定三文件 SHA-256、生成时间和 effective hook inventory digest；任何脚本变化都令台账 STALE 并 FAIL，禁止手写绿灯继续沿用。

## 明确确认未发现问题的部分

- 当前直接可见的 Git 写：`--list` 为 10 个 occurrence、8 个唯一签名；与台账 §4 的 4 个 auto-sync、3 个 main lefthook、1 个 WT lefthook一致。
- 当前 main/WT `lefthook dump` 未发现额外 `extends/remotes/local` 写操作。
- 当前真实 `core.hooksPath` 恰好与硬编码路径一致；五个非 sample hook 都是 Lefthook shim，无额外直接 Git 写。
- 当前五个 `com.canvas.*` plist 均为 XML、直达 `.sh`；手工追到 daily-review 二/三层后未发现 Git 写。
- 标准 YAML `run: "git push rogue HEAD"` 能被检测。
- 无参数和变量 remote 当前落 `unknown` 且未登记，会 FAIL。
- 无效 settings JSON 已在当前版修成 `UNPARSEABLE`，实测 `exit 1`。
- N0 的基线使用方式正确；问题在于负例覆盖不足。
- 当前未发现 file-based managed settings；server/MDM/session hook 未能从静态文件确认，标为 **UNVERIFIED**。
- 全程只读项目；变异仅发生在 `mktemp` 临时副本。Sequential Thinking、Graphiti、LSP 当前未提供可调用工具；LSP亦因无编辑不适用。

最终结论：**该断言当前只能证明“若扫描器恰好看见一个未登记的粗签名，就会 FAIL”；不能证明“未登记的自动 stage/commit/push 都会被看见并 FAIL”。DEBT-15 规范结论应为 FAIL，不能据此关闭。**


tokens used
352,086
总体判断：**FAIL / BLOCKED**。当前断言脚本不足以支撑“未登记的 auto stage/commit/push 必然 FAIL”。在最终稳定快照上，我复现了 **7 类未登记写副作用均 `exit 0`**。

审查锚点：

- WT：`card/t3-hooks`
- HEAD：`cbb20afb572a7b8ce9ebc205082e4be6de076fb8`
- 断言脚本 SHA-256：`0bcc2e275d788b6cbf16f2387e98550f8a4d5e93a42476268498fc9ee301bb2e`
- 负验证 SHA-256：`eff04fbe02366b32d66f91db57e452f8cecbaf3ebec0a11206effe839f0f552b`
- 当前基线：`PASS=15 WARN=4 FAIL=0`
- 自带负验证：N0–N10，`抓到=11 逃逸=0`
- 额外对抗负例：7/7 假绿，均 `PASS=15 WARN=4 FAIL=0`

## BLOCKER

### 1. 已登记的粗签名可以替未登记的新命令“代为放行”

- 级别：**BLOCKER**
- 问题：登记键只有“来源 + verb/remote”，没有绑定具体 occurrence、参数、hook stage 或 job。
- 证据：[assert-hook-write-safety.sh:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:52) 定义粗签名；所有 `git add ...` 都归为 `git-add`；YAML 输出只有 `${key}::${verb}`；门 3 又在 [assert-hook-write-safety.sh:478](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:478) 对同签名去重。
- 可逃逸场景：

  ```yaml
  post-checkout:
    commands:
      stage-everything:
        run: git add -A
  ```

  加到 worktree `lefthook.yml` 后仍命中既有 `wt-lefthook::git-add` KEEP。实测 `exit 0, FAIL=0`。
- 修复建议：签名至少包含规范路径、event/stage、job/matcher、完整 argv、remote/refspec/pathspec；逐 occurrence 匹配，不得按 verb 去重。允许的窄 `git add openapi.json` 必须与 `git add -A` 形成不同登记。

### 2. 一行只产生一个签名，违规 commit/add 可被已登记 push 掩盖

- 级别：**BLOCKER**
- 问题：`if/elif` 只返回一个 verb，且 push 的贪婪 `.*git push` 会选择一行中最后一个 push。
- 证据：[assert-hook-write-safety.sh:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:140)；扫描器每个物理行只调用一次规范化函数。
- 可逃逸场景：

  ```yaml
  run: git commit -am auto && git push origin HEAD
  ```

  实测只产生已登记的 `git-push:origin`，未登记 commit 消失，完整断言 `exit 0`。同样：

  ```sh
  git push rogue HEAD # git push origin HEAD
  ```

  实际只执行 rogue，解析结果却是 `git-push:origin`。
- 修复建议：用 shell AST 去除注释/字符串后，逐个 simple command 生成 occurrence；禁止“一行一签名”和贪婪行级 remote 提取。

### 3. echo/printf、引号过滤和 Git 全局选项均有确定性假绿

- 级别：**BLOCKER**
- 问题：过滤器在解析命令链前跳过整行；匹配器又要求 verb 紧跟 `git`。
- 证据：[assert-hook-write-safety.sh:194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:194) 第 214–224 行。
- 可逃逸场景：以下三项分别加入已挂载脚本，实测全部 `exit 0`：

  ```sh
  echo ready && git push rogue-echo HEAD
  "git" push rogue-quoted "HEAD"
  git -C "$REPO" push rogue-dash-c HEAD
  ```

- 修复建议：不得按首 token 丢弃整行；解析 `&&`、`||`、`;`、管道及引号化 executable；识别 `-C`、`-c`、`--git-dir`、`--work-tree` 等 Git global options。不能解析时输出 `UNANALYZABLE` 并 FAIL。

### 4. 没有执行闭包递归，且忽略 settings exec-form 的 `args`

- 级别：**BLOCKER**
- 问题：只提取第一层 `.sh/.js/.py`，扫描后不继续展开；只读 `command`，完全忽略 `args`。
- 证据：[assert-hook-write-safety.sh:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:238) 第 262、285 行；收到 SCRIPT 后只扫描一次本体。
- 可逃逸场景：

  ```sh
  # A.sh，settings 直接挂载
  bash ./B.sh
  # B.sh
  git push rogue-child HEAD
  ```

  以及：

  ```json
  {
    "type": "command",
    "command": "git",
    "args": ["push", "rogue-exec-args", "HEAD"]
  }
  ```

  两项实测均 `exit 0`。
- 修复建议：构造带 visited-set 的执行图，展开 `source/bash/sh/node/python/npm/npx/make`、package scripts 和 exec-form args；动态变量、extensionless target、`.cmd/.mjs/.cjs` 或未知包装器必须 FAIL 或绑定 exact bytes/hash。

### 5. 扫描的仍不是 Claude Code 实际生效 hook 全集

- 级别：**BLOCKER**
- 问题：当前新增的 `~/.claude/plugins` 全目录扫描仍漏 managed/CLI/skill/agent/session hook，并且不按实际启用插件和 manifest 解析。
- 证据：[assert-hook-write-safety.sh:96](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:96) 仍只有固定来源；plugin 分支在第 371–400 行简单 `find hooks.json`。本机已启用 `superpowers`，其 [hooks.json:9](/Users/Heishing/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/hooks/hooks.json:9) 指向 `.cmd`，但提取器只认 `.sh/.js/.py`。

  Claude 官方文档还明确列出 managed policy、插件、skill/agent frontmatter，以及 session/built-in hook；CLI `--settings` 和 `--plugin-dir` 也是实际配置层。[Claude Hooks reference](https://code.claude.com/docs/en/hooks)，[Claude configuration](https://code.claude.com/docs/en/configuration)。
- 可逃逸场景：

  ```sh
  claude --settings '{"hooks":{"Stop":[{"hooks":[
    {"type":"command","command":"git","args":["push","rogue","HEAD"]}
  ]}]}}'
  ```

  该 hook 可生效，但断言不读取 flag settings。
- 修复建议：以 Claude `/hooks` 或 hook registration telemetry 导出的**实际生效清单**作为输入；同时解析 managed、CLI、enabledPlugins、installed version、manifest 自定义 hook 路径及 `--plugin-dir`。无法取得有效清单时 fail closed。

## HIGH

### 6. Lefthook、Git hooksPath 和 LaunchAgent 都没有按运行时语义解析

- 级别：**HIGH**
- 问题：脚本扫描硬编码原始文件，而不是最终合并/解析后的运行入口。
- 证据：
  - Lefthook 仅扫描两份原始 `lefthook.yml`；官方说明 `extends`、`remotes`、`lefthook-local` 会合并并覆盖。[extends](https://lefthook.dev/configuration/extends/)，[remotes](https://lefthook.dev/configuration/remotes/)
  - `.git/hooks` 路径硬编码于 [assert-hook-write-safety.sh:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:104)，没有断言真实 `core.hooksPath`。[Git hooks](https://git-scm.com/docs/githooks)
  - LaunchAgent 只 grep 同行 XML 中的 `.sh/.py`，见第 402–418 行。
- 可逃逸场景：
  - `extends: rogue.yml`，被引用文件含 `git push rogue HEAD`；
  - 将 `core.hooksPath` 改到 `.githooks-live`，保留旧 `.git/hooks`；
  - plist `Program=/Users/Heishing/bin/git-autosync`，目标为 extensionless executable。
- 修复建议：扫描 `lefthook dump` 的最终合并结果；分别从 main/WT 解析并 canonicalize `git rev-parse --git-path hooks`；用 `plutil` 解析 `Program`/`ProgramArguments` 和 binary plist，对 extensionless target 递归或 fail closed。

### 7. N0–N10 的绿灯无法证明核心结论

- 级别：**HIGH**
- 问题：负验证只证明所选简单样例会红，没有覆盖当前已复现的假绿类别。
- 证据：[verify-hook-write-safety-negative.sh:92](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/verify-hook-write-safety-negative.sh:92) 的 N0 用法正确；但 N3 第 136–150 行声称测试 `git add/stage`，实际注入的是 `git commit`。N10 只是在插件目录放一个 `hooks.json`，并未证明它是实际 enabled plugin。
- 可逃逸场景：本次额外测试的 `git add -A` 同签名碰撞、复合命令、echo、quoted executable、`git -C`、二级脚本、exec-form args，7/7 都在 N0 可通过的沙箱中 `exit 0`。
- 修复建议：建立数据驱动负例矩阵，三种 verb 都覆盖：新来源、已有同 verb 来源、参数扩大、复合命令、变量/包装器、递归、exec args、runtime source；每例必须断言具体新增 occurrence 被报告，而不只是总 RC 非零。

## MEDIUM

### 8. push remote 解析不稳健，但常见动态形式当前多数是假红而非假绿

- 级别：**MEDIUM**
- 问题：remote sed 并未按 Git argv 规则解析。
- 证据：[assert-hook-write-safety.sh:148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/scripts/assert-hook-write-safety.sh:148)。实测：

  ```text
  git push                         => git-push:unknown
  git push "$REMOTE"               => git-push:unknown
  git push --repo=rogue HEAD       => git-push:--repo
  git push -u rogue HEAD           => git-push:-u
  git push https://... HEAD        => git-push:https
  git -C /repo push rogue HEAD     => 无签名
  ```

- 可逃逸场景：`git push rogue HEAD # git push origin HEAD` 会错误落到已登记 origin 并 PASS；单独的 `unknown/-u/--repo` 当前未登记，通常会假红。
- 修复建议：按 argv 解析 push options、option values、URL/default/dynamic remote；DEFAULT/DYNAMIC 不允许以粗签名登记。

### 9. 台账已经与当前脚本和运行结果脱节

- 级别：**MEDIUM**
- 问题：台账仍描述旧版来源数、测试数和 PASS 数。
- 证据：[台账:44](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-hooks/_bmad-output/审查/DEBT-15-hook写副作用台账-2026-08-30.md:44) 声称 9 个来源、`PASS=14`、N0–N6 7/7；当前是 10 个来源、`PASS=15`、N0–N10 11/11。台账第 219–221 行仍宣称“全部来源”和判据成立。
- 可逃逸场景：审查者仅依赖台账或 `--emit-ledger`，会把尚未覆盖的 managed/CLI/skill/agent/递归入口误认为已核完。
- 修复建议：台账绑定三文件 SHA-256、生成时间和 effective hook inventory digest；任何脚本变化都令台账 STALE 并 FAIL，禁止手写绿灯继续沿用。

## 明确确认未发现问题的部分

- 当前直接可见的 Git 写：`--list` 为 10 个 occurrence、8 个唯一签名；与台账 §4 的 4 个 auto-sync、3 个 main lefthook、1 个 WT lefthook一致。
- 当前 main/WT `lefthook dump` 未发现额外 `extends/remotes/local` 写操作。
- 当前真实 `core.hooksPath` 恰好与硬编码路径一致；五个非 sample hook 都是 Lefthook shim，无额外直接 Git 写。
- 当前五个 `com.canvas.*` plist 均为 XML、直达 `.sh`；手工追到 daily-review 二/三层后未发现 Git 写。
- 标准 YAML `run: "git push rogue HEAD"` 能被检测。
- 无参数和变量 remote 当前落 `unknown` 且未登记，会 FAIL。
- 无效 settings JSON 已在当前版修成 `UNPARSEABLE`，实测 `exit 1`。
- N0 的基线使用方式正确；问题在于负例覆盖不足。
- 当前未发现 file-based managed settings；server/MDM/session hook 未能从静态文件确认，标为 **UNVERIFIED**。
- 全程只读项目；变异仅发生在 `mktemp` 临时副本。Sequential Thinking、Graphiti、LSP 当前未提供可调用工具；LSP亦因无编辑不适用。

最终结论：**该断言当前只能证明“若扫描器恰好看见一个未登记的粗签名，就会 FAIL”；不能证明“未登记的自动 stage/commit/push 都会被看见并 FAIL”。DEBT-15 规范结论应为 FAIL，不能据此关闭。**



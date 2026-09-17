# CARD-DEPLOY-TIMEOUT 独立复核（round 2）

## 一 背景与最小读取面

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy`
（分支 `card/t2-deploy`，基线 `08100483`，**本轮审查 SHA `71a85acf`**；round 1 审的是 `7413283a`）。

round 1 结论是 BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 3。本轮请复核 round 1 的整改是否真的成立、
以及整改本身有没有引入新问题。

**只读这些**（不要扩展到别处）：

1. `git diff 7413283a 71a85acf -- . ':(exclude)_bmad-output'` —— **本轮整改**（两文件）。
2. `git diff 08100483 71a85acf -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动。
3. `scripts/deploy-vault.sh` `:55-100`（头注 环境开关 + 缺省赋值，头注 `CLS_NPM_BUILD_TIMEOUT` 起于 `:63`）、
   `:414-651`（步 1 `step1_preflight` 全文；本卡改动集中在 `:569-638` 的 build 段，perl 在 `:603`）。
4. `scripts/deploy-vault.sh` `:1144-1240`（步 5 `step5_activate`）—— 只核「本卡一字未动」是否属实。
5. `backend/tests/unit/test_deploy_vault_sh.py` `:57-67`（`_SUBPROCESS_TIMEOUT`）、
   `:2634-2876`（假 harness / 假 npm 辅助 + 六条用例，文件共 2876 行）。
6. 本轮证据（`_bmad-output/审查/evidence-deploy-timeout/`）：
   `negctl2-20260914T202240.txt`（**本轮重点**：三处整改逐个变异回旧行为的杀伤力实验 + 跑前跑后 shasum）、
   `r1fix-targeted-20260914T202156.txt`（9 条定向用例）、
   `deploy-file-r1fix-20260914T202625.txt`（文件级 145 passed / 9 skipped）、
   `unit-close-r1fix-20260914T202713.txt`（tests/unit 全量）、
   `gates-r1fix-20260914T203249.txt`（静态门重跑）、
   `unit-diff-falsifier-20260914T201210.txt`（**round 1 LOW-3 所指那条锚的重测**）。

## 二 本轮整改自述（请独立核对，不要采信本节）

1. **HIGH-1（取值边界）**：`:580-591` 现在先判数字、再剥前导零、再按「长度 ≤5 且 1..86400」
   收口。理由：`[ -gt ]` 比一个 30 位数字会 rc=2 而 `if` 判假 = 反而放行，所以先按长度拦。
   `0` / `000` / `4294967296` / `abc` 四个取值各有一条参数化用例钉住「拒在调 npm 之前」；
   `005` 有一条控制组用例钉住「合法的 5 秒不能被误拒」。
2. **MEDIUM-2（退出码碰撞）**：超时信号改走**带外标记** —— shell 生成 `CLS-NPM-BUILD-TIMEDOUT-$$-$TS`
   作为参数传给 perl（单一来源），perl 的子进程在 `exec` 前把自己的 stdout/stderr 改到
   `/dev/null`，父进程只在闹钟触发时 `print "$mark\n"`；bash 侧改用 `case "$_build_out" in *"$_mark"*)`
   判定，不再看退出码。新增 `rc124` 假 npm 形态（立刻 `exit 124`）作为回归门。
3. **LOW-1（离线开关）**：① 头注收回「不等网」的过强说法，改成「只约束 npm 自己的取包路径；
   package.json 脚本自己发的请求不受它约束，兜底的是墙钟上限」；② 假 npm 现在把收到的
   `npm_config_offline` 落盘，`..._cap_does_not_kill_a_fast_build` 断言它是 `true` ——
   证据 `negctl2` 第三段：删掉脚本那一行，该用例确实变红。
4. **MEDIUM-1（脱组后代）**：认同「能力边界」结论，**不声称能杀干净进程树**。代码侧只做了
   一件事：`kill(-15,$pid) or kill(15,$pid)`（KILL 同形），补上 `fork → setpgrp` 之间那个窗口；
   文档侧在头注写明「后代自己 `setsid()` 会脱离被杀的进程组，本上限保证的是**本步骤按时返回**」。
5. **LOW-2（300:600 顺序）**：认同不能说「必定」，头注改为「通常」并写明三个例外
   （步 1 前段另计时 / 2s 清理宽限 / 用户把上限调到 >600）。
6. **LOW-3（负控 rc）**：该锚的 rc 当时被 `head` 吃掉（取到的是 `head` 的 rc）。当场已重测：
   `unit-diff-falsifier-20260914T201210.txt` 里锚 `rc=1`、真判据 `rc=0`。本轮请核这份文件。
7. 步 5/6 与主流程仍为**逐字节未动**：`step2_install` 到 EOF 的 sha256 在基线与本轮相同
   （`96d10556…`，33631 bytes，见 `gates-r1fix-…`）。

## 三 请按重要性排序回答的问题

- ⓪ HIGH-1 的新校验是否仍有**未被拦下的输入**能让上限静默失效或被显著缩短？
  （前导零 + 长度 + 范围三段的组合、`+5` / 空白 / 全角数字 / 极长零串 `000…0`、
  `_cap` 被剥零后用于 `alarm` 与用于文案的是否一致。）
- ① 带外标记是否真的不可能被 npm 侧伪造或吞掉？子进程 `exec` 前改 stdout 到 `/dev/null` 之后，
  命令替换捕获的还有没有别的来源；`$$` 在命令替换 / 子 shell 里取的是哪个 pid，标记会不会
  因此在两次运行里相同或为空；`case` 的模式匹配对含 `*`/`[` 的标记串是否仍安全。
- ② `kill(-15,$pid) or kill(15,$pid)` 的**短路语义**是否如作者所想：`kill` 返回成功计数，
  组信号在「组已存在但成员都已退出」时返回什么？会不会出现「组信号返回 0 ⇒ 又给单进程发一次」
  的多余信号，或反过来「组信号成功但实际没人收到」而漏杀？
- ③ 六条新用例是否存在**顺序/端口/残留**耦合：同一 `tmp_path` 下的 `bin` 与 `npm-pids`、
  参数化用例各自占的端口（8251-8259）、`_reap` 按 pid 文件杀进程在 pid 复用时的风险、
  以及非法取值那条用例「假 npm 不应被调到」的断言是否可能因上一条用例的残留文件而假绿。
- ④ 头注（= `--help` 输出）新增的十余行是否与脚本实际行为逐条相符？有没有仍然过强的说法？
- ⑤ 本卡是否有任何一处仍在「用一条恒真的判据证明自己」（假绿）？`negctl2` 的三段变异是否
  足以支撑「这三道门有牙齿」，还是其中某段的红其实来自别的原因？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给：
`<级别> <一句话结论>` + `file:line` + 一句话说明**在什么输入或环境下会发生**。
用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这套措辞描述触发条件。
没有问题的级别请明确写「无」。若 round 1 的某条结论在本轮被推翻，请直接说明。

## 五 边界

- 只读审查：不要修改任何文件，不要执行会写盘的命令。
- 不连任何数据库（7691 / 7687 / 7692），不跑真实 `docker compose up -d`，不跑真实 `npm run build`。
- 不评步 5 / 步 6 的语义设计与 `scripts/cls_forbidden_paths.py` 的禁写面设计 —— 本卡对它们零改动。
- 不评本仓 ruff 规则集只有 `E9/F63/F7/F82` 这一既有决策（`backend/ruff.toml`，非本卡引入）。

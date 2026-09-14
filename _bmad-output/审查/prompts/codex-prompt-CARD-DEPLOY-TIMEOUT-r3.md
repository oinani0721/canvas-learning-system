# CARD-DEPLOY-TIMEOUT 独立复核（round 3）

## 一 背景与最小读取面

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy`
（分支 `card/t2-deploy`，基线 `08100483`，**本轮审查 SHA `25f56065`**；r1 审 `7413283a`、r2 审 `71a85acf`）。

r2 结论 BLOCKER 0 / HIGH 1 / MEDIUM 0 / LOW 3。本轮请复核 r2 整改是否成立、以及整改本身是否引入新问题。

**只读这些**：

1. `git diff 71a85acf 25f56065 -- . ':(exclude)_bmad-output'` —— **本轮整改**（两文件）。
2. `git diff 08100483 25f56065 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动。
3. `scripts/deploy-vault.sh` `:55-106`（头注 环境开关 + 缺省赋值）、`:421-679`（步 1 全文；
   本卡改动集中在 `:576-666` 的 build 段，取值校验在 `:591-620`，perl 在 `:631`）。
4. `scripts/deploy-vault.sh` `:1172-1268`（步 5）—— 只核「本卡一字未动」是否属实。
5. `backend/tests/unit/test_deploy_vault_sh.py` `:57-67`（`_SUBPROCESS_TIMEOUT`）、
   `:2634-2914`（假 harness / 假 npm 辅助 + 八条用例，文件共 2914 行）。
6. 本轮证据（`_bmad-output/审查/evidence-deploy-timeout/`）：
   `negctl3-20260914T205017.txt`（**本轮重点**：四处修复的变异杀伤力，驱动已按 r2 LOW-2 重写 ——
   红绿由 pytest 汇总行判定、预期值参与比对打印 MATCH/MISMATCH、每例留全量日志）、
   七份逐例全量日志 `negctl3-n1-locale-205017.txt` / `negctl3-n1-ctrl-legal-205117.txt` /
   `negctl3-m1-range-205135.txt` / `negctl3-m1-ctrl-hang-205406.txt` / `negctl3-m2-rc124-205427.txt` /
   `negctl3-m3-offline-205444.txt` / `negctl3-restore-all-205500.txt`（含失败断言正文）、
   `r2fix-targeted-20260914T204347.txt`（11 条定向）、
   `deploy-file-r2fix-20260914T205549.txt`（文件级 147 passed / 9 skipped）、
   `unit-close-r2fix-20260914T205645.txt` + `unit-nodeids-r2fix-20260914T205645.txt`
   （**两个比较集合本身已落盘**，回应 r2「无法独立重算」那条）、
   `gates-r2fix-20260914T210350.txt`（静态门全套）。

## 二 本轮整改自述（请独立核对，不要采信本节）

1. **r2 HIGH-1（locale 依赖）**：`:591-620`。字符集改成**逐字符枚举** `[!0123456789]`（两处：
   剥零前、剥零后），并把数值比较挪到「已确认 1-5 位纯 ASCII 数字」**之后** —— 比较一旦出错
   就是 rc=2 → `if` 判假 → 放行，这类 fail-open 是原缺陷的根源。另加「原串 >20 位直接拒」，
   规避十万个零的剥零耗时（r2 ⓪ 实测约 14s，发生在闹钟装上之前）。
   本机四条前提已复测：`ar_EG.UTF-8` 存在；旧写法对 `٠٥` **通过**（被骗）、新写法**拒绝**；
   `[ '٠٥' -lt 1 ]` 报 integer expression expected；`perl -e 'alarm "٠٥"'` 剩余 **0**。
2. **r2 LOW-3（头注过强）**三处已收回：① perl 走 PATH（不再写「固定 /usr/bin/perl」）；
   ② 超 uint32 是**截断**（4294967296→0、4294967297→1s），不是一律取消；
   ③ 上限保证的是「这条 build 不会无限等下去」，不是「步 1 整体按时返回」——
   build 之后的 `mkdir`/`cp` 卡住时闹钟已取消，这一句写进了头注。
3. **r2 LOW-1（`_reap` PID 复用）**：收窄为「先看进程还在不在、不在就不发信号；发就直接 KILL
   一次，不再 TERM→等→KILL」，并在 docstring 如实写明**窗口不为零**。未做进程身份校验。
4. **r2 LOW-2（负控驱动）**：重写。红绿由 pytest 汇总行判定（不看 `tail` 的 rc）；预期值真的
   参与比对并打印 MATCH/MISMATCH；失败断言正文进日志（用来排除「红于别的原因」）；
   每例全量日志单独落盘；末行打印 `MISMATCH 总数`（本轮 = 0）。
   顺带：上一版驱动末行自己踩了 `$VAR` 紧跟全角括号的坑（被吃进变量名 → unbound variable），
   已改 `${VAR}`，那一版存档**未入库**。
5. **新增 2 条 locale 回归门**：`test_preflight_rejects_non_ascii_digits_in_any_locale[ar_EG.UTF-8]`
   与 `[C]`（两个 locale 都跑，避免「碰巧这台机器的 locale 不认」）。
6. 步 5/6 与主流程仍**逐字节未动**：`step2_install` 到 EOF 的 sha256 = `96d10556…`，33631 bytes。

## 三 请按重要性排序回答的问题

- ⓪ 新的取值校验是否还有**未被拦下的输入**能让上限静默失效、被显著缩短、或让步 1 卡住？
  （两次字符集判断之间的剥零表达式 `${_cap#"${_cap%%[!0]*}"}` 本身是否 locale 安全；
  `20`/`5` 两个长度阈值与 `86400` 的关系；`_cap` 传给 perl 时是否可能再被 shell 重新解释。）
- ① 本卡是否还有**别的 fail-open**：`if` 条件里的命令出错（rc≥2）被当成「条件不成立」而放行，
  或 `case` 没有兜底分支导致落空。请在步 1 本卡改动面内逐条看。
- ② 八条新用例是否存在顺序 / 端口 / 残留耦合导致的假绿？特别是：`_npm_was_invoked` 依赖
  `npm-env.txt` 是否存在，而它由假 npm 第一行写 —— 若假 npm 被调到但写文件失败，
  断言会怎么错？`[C]` locale 那条是否只是「本来就拒」而不构成回归门？
- ③ `negctl3` 的七例是否足以支撑「这四道门有牙齿」？有没有哪一例的红其实来自变异之外的原因
  （日志里已保留失败断言正文，请据此判断）；`m1-range` 那例 `3 failed / 1 passed` 里
  `abc` 仍绿是否与作者解释（该变异只撤范围、不撤字符集）一致。
- ④ 头注（= `--help` 输出）现在是否还有超出实现的承诺？
- ⑤ `unit-nodeids-r2fix-…txt` 里的两个集合是否真能独立重算出「逐条一致」？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给：
`<级别> <一句话结论>` + `file:line` + 一句话说明**在什么输入或环境下会发生**。
用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这套措辞描述触发条件。
没有问题的级别请明确写「无」。若前两轮的某条结论在本轮被推翻，请直接说明。

## 五 边界

- 只读审查：不要修改任何文件，不要执行会写盘的命令。
- 不连任何数据库（7691 / 7687 / 7692），不跑真实 `docker compose up -d`，不跑真实 `npm run build`。
- 不评步 5 / 步 6 的语义设计与 `scripts/cls_forbidden_paths.py` 的禁写面设计 —— 本卡对它们零改动。
- 不评本仓 ruff 规则集只有 `E9/F63/F7/F82` 这一既有决策（`backend/ruff.toml`，非本卡引入）。
- `tests/unit` 的 35 failed / 29 errors 是**主干既有的 64 条红基线**，本卡的主张是「对基线逐条
  一致」，不是「全绿」—— 请按这个口径核。

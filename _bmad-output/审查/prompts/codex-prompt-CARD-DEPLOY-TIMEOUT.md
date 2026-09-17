# CARD-DEPLOY-TIMEOUT 独立复核（round 1）

## 一 背景与最小读取面

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy`
（分支 `card/t2-deploy`，基线 `08100483`，审查 SHA `7413283a`）。

本卡承接集成期裁定 R-15：候选树跑 `backend/tests/unit` 时，`test_deploy_vault_sh.py` 里真跑
`scripts/deploy-vault.sh` 的用例**逐个无限挂起**。挂点是步 1 `step1_preflight` 在缺少
gitignored `main.js` 时触发的 `npm run build` —— 它原先没有任何墙钟上限。本卡做两件事：
① 给该 build 加墙钟上限 + 离线标志；② 给测试文件 16 处裸 `subprocess.run` 加统一 `timeout=`。

**只读这些**（不要扩展到别处）：

1. `git diff 08100483 7413283a -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动（两文件）。
2. `scripts/deploy-vault.sh` `:55-75`（头注 环境开关，= `--help` 输出）、`:84-90`（缺省赋值）、
   `:402-610`（步 1 `step1_preflight` 改后全文，build 段在 `:552-596`）。
3. `scripts/deploy-vault.sh` `:1103-1200`（步 5 `step5_activate`）—— **只看「本卡一字未动」是否属实**，
   不评其语义（那是下一张卡 T2-B 的面）。
4. `backend/tests/unit/test_deploy_vault_sh.py` `:57-67`（`_SUBPROCESS_TIMEOUT` 常量与依据）、
   `:2626-2822`（本卡新增的假 harness / 假 npm 辅助与三条新用例）。
5. 本卡证据（全部在 `_bmad-output/审查/evidence-deploy-timeout/`）：
   `ast-open-20260914T194902.txt` / `ast-close-20260914T195612.txt`（AST 先红后绿）、
   `script-open-20260914T195329.txt` / `script-close-20260914T195516.txt`（行为先红后绿与耗时）、
   `negctl-20260914T195738.txt`（负控三段 + 跑前跑后 shasum）、
   `scope-gate-20260914T195832.txt`（步 2-6 逐字节对照）、
   `deploy-file-20260914T195639.txt`（文件级 139 passed / 9 skipped）、
   `unit-diff-20260914T201203.txt`（tests/unit 对 64 条基线 diff）、
   `ruff-20260914T195908.txt`、`ruff-live-20260914T195843.txt`。

## 二 作者自述（请独立核对，不要采信本节）

1. 16 处裸 `subprocess.run` 已全部加 `timeout=_SUBPROCESS_TIMEOUT`（AST 判据 `WITHOUT` 16 → 0，
   `with` 20）；既有 4 处（`:89` helper 转发 / `:474` 120 / `:1894` 600 / `:2466` 120）一字未动。
2. 步 1 的墙钟上限用 `/usr/bin/perl` 的 `alarm`：`fork` 出一个 `setpgrp(0,0)` 自成进程组的子进程
   `exec npm`，到点对**整个进程组**发 TERM、隔 2s 再 KILL，以 rc 124 回报。本机 `timeout(1)` 与
   `gtimeout` 都缺席（`command -v` 实测 ABSENT），故不用该命令。
3. 离线标志 `npm_config_offline="$CLS_NPM_BUILD_OFFLINE"`（缺省 true）写在真正的 env 段里
   （与既有 `npm_config_cache` / `npm_config_logs_dir` 同段），不是写在注释里。
4. 先红后绿全部用假 npm + 自洽的假 harness：不跑真 build、不联网、不依赖本机树上是否有
   `main.js`（假 harness 里恒无 `main.js`，恒走 build 分支）。
5. 步 5 / 步 6 与主流程一字未动：`step2_install` 到文件尾的文本在基线与改后 sha256 相同
   （`96d10556…`，33631 bytes）。
6. 上限缺省 300s、测试侧兜底 600s，比例 1:2 是刻意的：让脚本自己的超时文案先于裁判超时出现。

## 三 请按重要性排序回答的问题

- ⓪ 墙钟上限是否**真的**能终止后台子进程：`perl` 里 `kill(-15, $pid)` / `kill(-9, $pid)` 的语义
  （Perl 的负信号 = 发给进程组）是否与作者的意图一致？子进程 `setpgrp(0,0)` 与 `exec` 之间是否
  存在窗口，使得 npm 自己再改进程组、或其孙子进程脱离该组而在上限到点后继续运行？
- ① `npm_config_offline=true` 在本地缓存缺失时的实际语义边界：是快速失败，还是仍可能等待网络？
  这个开关是否足以覆盖「build 等网」这条挂起路径，还是只覆盖了其中一部分？
- ② 新增三条用例在「树上**有** `main.js`」的机器（如主干树 / 候选树）上会不会误触真实 build 或
  写到 tmp 之外？假 harness 的 `--harness` 指向 tmp，但 `FORBID_PY` 取自脚本自身所在目录 ——
  这条不对称是否留下了未被覆盖的写入路径？
- ③ 超时专属文案与「任意 build 失败」是否真的可分辨？负控第三段（`CLS_NPM_BUILD_TIMEOUT=1` 的挂起
  假 npm vs 立刻 rc=1 的假 npm）是否足以支撑这个主张，还是存在两者都命中同一条文案的输入？
- ④ 给 16 处统一 `timeout=600` 是否对某些本就很快的跑（`bash -n` / `git log` / `git show`）过松、
  或对某些跑（`docker ps -a` 在 daemon 无响应时、`--apply` 全流程）过紧？有没有哪一处需要不同上限？
- ⑤ `CLS_NPM_BUILD_TIMEOUT` 的取值校验（`case … *[!0-9]* …`）在 `set -euo pipefail` 下是否有遗漏的
  取值（空串、前导零、超大整数、`0`）会让上限静默失效？`alarm 0` 在 Perl 里是「取消闹钟」——
  `CLS_NPM_BUILD_TIMEOUT=0` 时会发生什么，这是否是可接受的语义？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给：
`<级别> <一句话结论>` + `file:line` + 一句话说明**在什么输入或环境下会发生**。
用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这套措辞描述问题的触发条件。
没有问题的级别请明确写「无」。

## 五 边界

- 只读审查：不要修改任何文件，不要执行会写盘的命令。
- 不连任何数据库（7691 / 7687 / 7692），不跑真实 `docker compose up -d`，不跑真实 `npm run build`。
- 不评步 5 / 步 6 的语义设计与 `scripts/cls_forbidden_paths.py` 的禁写面设计 —— 它们不是本卡的面，
  本卡对它们零改动；只在「本卡是否真的没碰它们」这一点上核对。
- 不评本仓 ruff 规则集只有 `E9/F63/F7/F82` 这一既有决策（`backend/ruff.toml`，非本卡引入）。

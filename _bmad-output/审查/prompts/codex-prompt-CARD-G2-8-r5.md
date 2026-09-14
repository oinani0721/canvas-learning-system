# 代码复核请求 — CARD-G2-8（部署激活事务化）

请用中文输出。只读审查，不要修改任何文件。

## 一 背景

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy`（分支 `card/t2-deploy`）。

本卡 G2-8 包裹 `scripts/deploy-vault.sh` 的步 5/6：

1. **真 activate 事务化**：闸门 `CLS_DEPLOY_ALLOW_DOCKER_UP=1` 之后那段改为分阶段事务 ——
   起/重建**本 vault 自己的** compose 项目 `cls-<vault>` → 健康断言 → 失败只拆本实例。
   每阶段一行 `stage=… rc=` 落进 `compose-config-<ts>.txt` 与步 6 evidence 的「激活分阶段」段。
   语义按决策页 §一 改写过：`/vault/switch` 已 410，运行时切换不存在 ⇒ 激活 = 起本 vault 自己的实例、
   不顶别的 vault；回滚 = 只拆这一个 compose 项目，**不是**「恢复旧 `ACTIVE_VAULT`」。
2. **三段新增**（改前脚本里 grep 0 命中）：
   - index journal 隔离：用 harness 的 `app.core.vault_state_paths` 真算两条 pending journal 路径
   - Lance 首索引单独计时：阶段耗时 + `table_count` 进度
   - Graphiti 回填 readiness：不可达 / 解析不出 / 明确未就绪三面一律 `skipped-with-reason`，禁假成功
3. **实现 `--also-push`**：把本次 vault 名追加进 harness 自己的 `.env` 的 `DAILY_REVIEW_VAULTS`
   （逗号分隔、去重），**不动 `ACTIVE_VAULT`**；harness 守卫（限 `FEATURE_TREE`）保留不动。
4. **canvas-vault 名口径**：加门钉住「连字符名被步 1 不动点 preflight 拒 / 下划线名放行」的现状。
   步 1~4 逻辑本卡一行未改。

**真 `docker compose up -d` 未执行**（用户未授权）⇒ 全部验证走 PATH 注入的桩 `docker` / 桩 `curl`。

## 二 最小读取面（写死，不必读别处）

- `git diff 677fa112 4309757b -- . ':(exclude)_bmad-output'`（`677fa112` = 前一卡 T2-A 的 tip，
  `4309757b` = 本卡审查 SHA = 当前 HEAD，含 r1~r4 四轮整改）
- `scripts/deploy-vault.sh` 的 `act_stage()` / `step5_activate()` / `also_push_daily_review()` /
  `step6_evidence()` 四段全文，以及头注的 `--also-push`、`[5/6]`/`[6/6]`、环境开关三处说明
- `backend/tests/unit/test_deploy_vault_sh.py` 中 `CARD-G2-8` 那一节全文（`_tx_harness` 及其后），
  外加被本卡改动的 `test_every_bash_write_site_has_a_prewrite_recheck`、
  `test_no_plaintext_credentials_in_committed_evidence`、`test_evidence_dir_has_no_stderr_archives`
- `_bmad-output/审查/evidence-g2-8/` 下的存档（先红 / 文件级单跑 / 负控四段）

## 三 作者自述，请独立核对

1. **失败回滚只拆 `cls-<vault>`**：桩态证据是否真的覆盖「另一实例存活」这一断言？
   桩 `curl` 对兄弟端口的 200 是否真的**取决于**桩 `docker` 那份「在跑项目」清单
   （即：它是不是一个有对照对象的判据，而不是恒 200）？
2. **Graphiti readiness 是否恒落 `skipped-with-reason`**：有没有某条路径在探测其实失败时仍报
   `result=ready`？三种失败面（curl 非零 / 响应里没有 `status` 字段 / `status` 非就绪值）是否都被覆盖？
   门的断言是否两侧都核（既核 `skipped-with-reason=` 出现，也核 `result=ready` 不出现）？
3. **`--also-push`**：去重是否真去重（逗号/空格混合分隔、键缺失、键存在但值为空三种输入）？
   `ACTIVE_VAULT` 是否逐字节不变？写入路径（`open_pinned` + `write_all`）是否与脚本别处同级硬化？
   把既有门的四个计数从 2 改到 3 是否是「跟着新增写入点走」而不是放宽？
4. **真 activate 未授权走 SKIP 时是否被如实标记**，SKIP 有没有在任何一处被当成成功？
5. **步 1~4 是否一行未改**：名口径收口是否误动了 preflight 逻辑？
6. **写面是否扩张**：步 5/6 的新增记账是否落在步 1 `PENDING_WRITES` 已申报过的对象上？
   `also_push_daily_review` 写 harness `.env` 这一处不在 `PENDING_WRITES` 里 ——
   它自带 `check_forbidden_paths --outputs` + `assert_writable_now`，这样够不够？
7. **Lance 轮询**：`CLS_DEPLOY_LANCE_READY_TIMEOUT` 的取值校验是否 fail-closed？
   有没有某个取值会让循环不终止或让上限静默失效？

## 四 输出

按重要性排序（BLOCKER / HIGH / MEDIUM / LOW），每条给出 `file:line` 与一句说明。
说明只描述**负控输入 / 对照输入 / 门未覆盖的路径**，不要给出任何攻击步骤。
若某项自述成立，请明确说「核对通过」，不要默认沉默。

## 五 边界

- 只读。不要连 docker daemon、不要连 Neo4j 7691/7687、不要写任何文件。
- 不评真态（真 `docker compose up -d` 未授权未跑，本轮不评真 docker 行为）。
- 不评步 1~4 的既有逻辑，不评前一卡 T2-A 的超时改动。
- 不评 `_bmad-output/` 下的文档措辞。

## 六 本轮（r5，按卡文是轮次上限）另需核对：r4 两条的处置

1. **HIGH（复查通过之后、`exec 9>>` 之前的窗口）** → `act_journal_open` 现在：
   ① `assert_writable_now`；② 用 `python3` 记下**复查当时**该路径对象的 `dev:ino:nlink`；
   ③ `exec 9>>`；④ 用 `python3` 对 **fd 9** 做 `os.fstat`，与 ② 的三元组逐字比较，
   对不上或问不出来就 `act_journal_close` 并拒（fail-closed）。
   理由：掉包之后再 stat 一次**路径**是没用的（路径与 fd 指向同一个新对象，两边一致，
   而那个对象没验过），只有问 **fd** 才能知道自己连到了哪个 inode。
   请核：这个推理是否成立？③④ 之间是否又引入了新的窗口（在 fd 已经握在手里之后，
   还有什么能让写落到别的对象上）？`python3` 子进程能拿到 fd 9 这一点是否可靠
   （本卡实测可继承，但请独立判断有没有环境会不成立，以及不成立时是否 fail-closed）？
   `nlink` 放进比较三元组是否有意义？
2. **LOW（`up -d` 失败那条回滚分支没有兄弟对照）** → 补了 `CLS_FAKE_UP_RC=1` 的门。

另：负控这一轮发现 `assert_writable_now` 那一层原本的段**打不响** —— 掉包会被新加的
身份核对接住，两层都覆盖。于是改用**硬链接**注入来钉这一层（身份核对对硬链接是瞎的：
`want` 与 `got` 是同一个 inode、`nlink` 也相同）。请核这个判断是否成立，以及
`negctl-final-r4-17seg-*.txt`（17 段全 KILLED）是否每段都只拆一层。

⚠️ **本轮是卡文允许的最后一轮。** 若仍有 BLOCKER/HIGH，请明确说出它**必须**在本卡修、
还是可以作为移交项登记 —— 并说明理由。

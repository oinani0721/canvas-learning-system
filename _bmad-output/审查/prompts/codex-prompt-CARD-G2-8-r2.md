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

- `git diff 677fa112 53eca445 -- . ':(exclude)_bmad-output'`（`677fa112` = 前一卡 T2-A 的 tip，
  `bb070e6f` = 本卡审查 SHA = 当前 HEAD）
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

## 六 本轮（r2）另需核对：r1 七条的整改是否真的成立

r1 给出 2 HIGH / 4 MEDIUM / 1 LOW，作者全部接受并整改，请独立核对每条：

1. **HIGH-1（readiness 全文正则）** → 改为 `json_top_field()`：`json.loads` 后只看顶层键，
   rc 三态（0 取到 / 3 解析不出或非对象 / 4 顶层无此键）分别映射到不同 `skipped-with-reason`。
   Lance 的 `status` 与 `table_count` 同改。请核：还有没有输入能让顶层失败被读成 `ready`？
   `json_top_field` 自身的 rc 语义在「值为 null」「值为 false」「值是嵌套对象」时是否仍正确？
2. **HIGH-2（阶段账追加点缺紧邻复查）** → `act_stage` 每次追加前 `assert_writable_now "$ACT_JOURNAL"`。
   请核：这道复查与随后的 `>>` 之间仍有残留窗口吗？失败时是否既记账又置 `ACT_JOURNAL_ERR`？
3. **MEDIUM-3** → 失败路径的判据面收窄到 `compose-config-<ts>.txt`，并断言步 5 FAIL 时
   `deploy-*.txt` 不存在。请核这个断言是否与 `run_step` 的实际行为一致。
4. **MEDIUM-4** → Lance 单次探测的 `-m` 取「剩余预算与 10 的较小者」。
   请核：循环的终止条件在 `lcap` 取边界值（1 / 86400）时是否仍成立？有没有不终止的取值？
5. **MEDIUM-5** → `--also-push` 改为 `splitlines(keepends=True)` 的**字节**口径，
   只改/只加目标行，保留各行原本行尾。请核：文件以 CR 结尾、最后一行无行尾、
   文件为空、目标键出现多次这四种输入下的结果是否都正确且不动其他字节。
6. **MEDIUM-6** → 阶段账写不进去时置 `ACT_JOURNAL_ERR`，由步 6 以 76 失败，
   证据的 rc 行同步标 76。请核：这条路径与 `--also-push` 失败路径同时发生时，
   报告与退出码是否仍自洽（不会出现「报告说 0、进程退 76」）。
7. **LOW-7** → 补了混合分隔与空值两类去重输入的门。

另请核对：为整改新增的 8 条门里，有没有**恒绿**（对被测行为不敏感）的？
负控现为 7 段（存档 `evidence-g2-8/negctl-r1fix-7seg-*.txt`），每段是否真的只拆一层防线？

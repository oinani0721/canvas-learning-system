你是独立审查者。审查对象是一张卡的**唯一代码文件**：`scripts/j01_e2e.sh`（新增）。
仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy`
分支 `card/p3-deploy`，基线 `9c4e7e82`，审查绑定 SHA = `986a22bdf8e607e4c3dd3809524932166be4d907`（分支 tip）。

---

## §一 背景与**最小读取面**（只读这些，不要扩散到别处）

本卡 = CARD-G2-11 [BATCH-2026-09-18-第十五批]。目标：为 J01「新 vault bootstrap」这条
用户旅程写一个**黑盒 E2E harness**。它自己不实现任何部署逻辑，只做两件事：
(1) 用一次性 throwaway vault 驱动既有的 `scripts/deploy-vault.sh` 六步；
(2) 对结果打 13 条机器可判的断言并落证据。

`deploy-vault.sh` / `install-vault.sh` / `verify_vault_install.py` / `docker-compose.yml` /
`backend/tests/unit/test_deploy_vault_sh.py` 本批**零写者**，本卡对它们**一行未改**。

**读取面**（请按此清单读，不要读别的）：

1. 本卡全部代码改动：
   `git --no-pager diff --no-color 9c4e7e82 986a22bd -- . ':(exclude)_bmad-output'`
   （= `scripts/j01_e2e.sh` 全文，约 1000 行）
2. `scripts/deploy-vault.sh` 的这几段（被调方契约）：
   - `:1-52`（六步说明 / 参数表 / rc 表）
   - `:972-1075`（`.env.<vault>` 白名单派生与固定六键）
   - `:3006-3070`（`docker compose config` 断言 + `CLS_DEPLOY_ALLOW_DOCKER_UP` 开关，
     未设即 `return 2` SKIP，不执行 `up -d`）
   - `:3120-3165`（`up -d backend` / 失败 `down`（带 `-p`）/ 健康断言）
   - `:3205-3272`（index-journal-isolation / lance-first-index / graphiti-readiness）
   - `:815-830`（`--port` 黑名单与 lsof 三态）
   - `:170-178`（`redact_secrets` 按键名脱敏的正则）
3. `docker-compose.yml`：`:18-56`、`:140-161`、`:205-240`、`:281-297`
4. `backend/app/api/v1/endpoints/index.py:81-121`（`/index/stats`、`DELETE /index/{vault_id}` 契约）
5. `backend/app/mcp/server.py:207-232`（`search_notes` 入参形态）
6. `backend/lib/agentic_rag/clients/lancedb_client.py:1294-1323`（`get_all_vault_stats` 分桶口径）
7. `backend/app/security.py:44-56`（鉴权头名 `X-CLS-Internal-Key`）
8. 本卡证据（`_bmad-output/审查/evidence-g211-j01/`）：
   - `isolation-values-pre-20260918T165258.txt`（改前隔离六值）
   - `run-20260918T175151-fixture/j01-20260918T175152.txt`（fixture 半边真跑, 13 条 assert, rc=0）
   - `run-20260918T175235-livepre/j01-20260918T175235.txt`（live 半边预检真跑, rc=1）
   - `negctl-scan-and-regression-20260918T175256.txt`（负控①② + 回归守卫共 24 个子例）
   - `negctl-3-statediff-20260918T175256.txt`（负控③ 代码变异, VERDICT=KILLED）
   - `struct-post-20260918T175358.txt`（结构判据 + 验伪锚）
   - `isolation-anchor-20260918T175358.txt`（隔离预检验伪锚 + 逐条敏感度矩阵）
   - `base.nodeids` / `close.nodeids`（目录级红基线 nodeid 集合对比）

---

## §一.5 round-1 整改说明（本轮请**重点复核这些改动本身是否引入新问题**）

上一轮（绑 `104c3e2d`）你给出 BLOCKER=0 HIGH=4 MEDIUM=8。**12 条全部整改**，摘要：

| 上轮编号 | 整改 |
|---|---|
| HIGH :552 | docker 查询失败不再等同零容器：`docker ps` 的 rc 单独接住，非 0 即拒删（teardown 与 rollback 两处同型一并修） |
| HIGH :540 | 判定抽成 `throwaway_guard_verdict`，**删除前重判一次**物理路径（TOCTOU），不复用 `THROWAWAY_OK` 旧结论 |
| HIGH :816 | 证据明文扫描对**敏感键名**的值不设长度下限（9 位密码不再被长度过滤跳过）；同时把非敏感键的兜底收窄为「高熵令牌形态」——路径/名字（`VAULTS_ROOT`/`ACTIVE_VAULT`）本来就该出现在部署证据里，按「出现即红」会让该判据恒红 |
| HIGH :930 | `stats_key_of` 先看 HTTP 状态码，非 200 一律回 `<unreadable:http=N>`；调用方哨兵改前缀匹配 |
| MED :265 | 新增 `dequote` / `env_kv_of`：值去成对引号后的等价形式一并参与 sha 比对 |
| MED :316a | `find` 枚举的 rc 全部接住（env / 软链 / 普通文件三处），失败即计入 unreadable 并判红 |
| MED :316b | env 枚举收进 `-type l`；`.env*` 是软链一律判红（不跟随） |
| MED :914 | `docker_project_set` 先捕获再判，保证**单 token**（原先失败时会输出两行哨兵） |
| MED :1002 | 授权态第二趟 deploy 的退出码进 `backend-ready` 判定 |
| MED :594 | `state-diff` 对 deploy 缺省证据目录改为**逐文件 sha**，不再只数个数 |
| MED :638 | compose **短格式** ports/volumes 解析（`"127.0.0.1:7478:7474"` / `"/path:/data"`），且输入面计数数的是**解析出来的**条目 |
| MED :1037 | `search-hit` 轮询的 curl `--max-time` 与 `sleep` 都夹在剩余时间内 |

新增 5 条定向回归守卫（负控文件里 `M1/M2/M3/M7 回归` 行），负控总数 24 → **29，全 MATCH**。

⚠️ 请特别核：**整改本身有没有引入新缺陷**（尤其 `throwaway_guard_verdict` 的重构、
`env_kv_of` 的双份输出、`looks_like_secret` 的收窄是否放过了真密钥、compose 短格式解析
的边界）。

---

## §二 作者自述（请**独立核对**，不要采信）

作者声称以下几点成立，请逐条自己去代码里核：

1. **fixture 半边跑的是真东西不是桩**：`run --mode fixture` 真调 `deploy-vault.sh --apply`
   （真 preflight / 真 `install-vault.sh` / 真密钥重生 / 真 `verify_vault_install.py`），
   模板源是 harness 树自己的 `canvas-vault/`，零 docker 容器。
2. **throwaway 路径保护（作者已自认其中两条是恒真的复述，请核这个自认本身对不对）**：
   ①「realpath(ROOT) 在 `$TMPDIR` 之内」与 ②「basename 是 `j01-*`」对本脚本自己
   用 `$TMPDIR` + `j01-XXXXXX` 模板 mktemp 出来的 ROOT **恒真**，代码里已标注它们只是
   兜底、不计作独立判据；③ 真正在挡事的是黑名单（ROOT **与 TMPDIR 都**不得落在
   harness 树 / **主仓根**（用 `--git-common-dir` 推，不是 `--show-toplevel` —— worktree
   里后者回的是 worktree 自己）/ 主仓 `canvas-vault` / `$HOME/Library` / `$HOME/.claude`
   / `$HOME/.codex` 之内），黑名单一条都解析不出来时 fail-closed；④ `deploy-vault.sh`
   自带的禁写面在它那一侧再判一次。`assert=throwaway-outside-protected` 未绿时
   `teardown_root` 自己再判一次并拒删；live 授权态下若仍有 `cls-<vault>-*` 容器存活也
   拒删（不抽走运行中容器的挂载源）。
3. **隔离预检的五条断言与 compose 事实逐条对应**，且五条**各自独立求值不短路**；
   `isolation-check` 子命令存在的唯一理由是给这道门做验伪锚
   （在「已隔离」的配置上必须变绿，否则它就是一道恒红的假门）。
4. **live 半边在预检红时结构上到不了 `up`**：harness 自身可执行代码里没有任何
   `docker compose up`；`up` 只可能由 `deploy-vault.sh` 执行，而它被调用两次 ——
   第一趟一律 `env -u CLS_DEPLOY_ALLOW_DOCKER_UP`（结构上不可能 up），
   第二趟带 `CLS_DEPLOY_ALLOW_DOCKER_UP=1` 前缀且位于
   `isolation-preflight rc=0 ∧ --allow-up ∧ 进程启动时 env 已为 1` 三者皆真的分支内。
   进程开头还 `unset` 了继承来的该变量，只留只读副本。
5. **`no-abs-path` 的「继承自模板源」分类不是白名单式放行**：判定依据是**整文件
   sha256** 与 `<harness>/canvas-vault/<相对路径>` 相同；继承项逐条列出并计数，
   任何一处被改动过 sha 即变 ⇒ 立刻归「新引入」判红。
6. **`table-diff` 只看本 vault 的 stats 键是产品口径而非偷懒**：`canvas-lancedb` 是
   `external: true` 的共享命名卷（裁定未落），全库表集合不归单个 vault 管。
7. **拆除只删自己 mktemp 出来的根**，全脚本只有一处递归删除语句（在 `teardown_root`
   里），主流程与 EXIT trap 都按函数名调它。
8. **所有「数命中数、0 命中即绿」的判据都先断言输入面非空**（`no-old-secret` 的参照
   env 集合与 env 文件数、`no-abs-path` 的文件数、`evidence-redacted` 的复查文件数、
   隔离预检的 `surface.*` 六项），空输入面一律 fail-closed 而不是放行。
   请独立核：还有没有**门未覆盖的路径**上残留同一形态（「没跑成」与「真为零」同值）。
9. **`evidence-redacted` 不只复述生产者的口径**：除键名形态外，还按参照 env 的**真实值**
   逐条 `grep -F`（与键名无关，YAML 块标量也逃不掉），值只在内存里比、只以 sha 进日志。
10. **`deploy-rc` 已归一到三态**：`deploy-vault.sh` 的原始退出码（0/64/71..76）进
    `reason=deploy-vault-exit=<n>`，assert 的 rc 只有 0/1/2 三种。

---

## §三 请按重要性排序回答的问题

0. 有没有**任何一条路径**能让本 harness 在「未授权」或「隔离预检红」的情况下仍然
   执行 `docker compose up`（含容器被间接拉起）？特别请核：
   `CLS_DEPLOY_ALLOW_DOCKER_UP` 是否可能被无条件 export 或从父进程泄入第一趟调用；
   `compose-config` 文件缺失 / 为空 / 解析失败时预检的取值；
   以及 `set -e` 提前退出是否可能跳过预检而直接落到别的分支。
1. `assert=no-old-secret` 有没有任何路径会把**密钥明文**写进日志或入库证据（sha 之外）？
   参照 env 集合为空时它是否真的 fail-closed（而不是空洞通过）？
   sha 比较有没有换行/空白处理上的缺口，使它**永远匹配不上**从而恒绿？
2. `assert=no-abs-path` 的文件名白名单是否**恰好只放行** `.canvas-config.yaml` 一个？
   软链与二进制文件分别怎么处理，有没有**门未覆盖的路径**（例如被跳过却没计数）？
3. `assert=state-diff` 的 S0/S1 快照有没有漏掉可能变化的面 —— 特别是 deploy 的
   **缺省**证据目录（`<harness>/_bmad-output/审查/evidence-deploy-<vault>`）被误用，
   以及 harness 的 `.env` 家族被追加 `DAILY_REVIEW_VAULTS` 的可能？
4. 拆除阶段 `rm -rf` 之前的物理路径保护是否真的按 realpath 判（中间段软链、
   macOS 大小写不敏感文件系统、前缀比较是否带分隔符）？realpath 解不出来时是否 fail-closed？
   EXIT trap 是否可能在保护断言尚未跑过时就触发拆除？
5. live 半边 `search-hit` 的轮询上限与 `refresh-changed` 的语义是否匹配？
   `DELETE /index/{vault}` 返回 404 时会不会被误记成通过？
   `/index/stats` 的分桶口径（按首个 `_` 切）与本卡 vault 名形态是否相容？
6. bash 3.2 兼容性与 `set -euo pipefail` 下的 rc 传递：有没有哪个计数器落在**管道产生的
   子 shell** 里导致自增丢失？有没有哪个失败被吞掉而报成绿？有没有 `set -u` 下的未定义变量？
   非 ASCII 路径（vault 里有中文目录名 `节点`）与含空格路径下的词分割问题？
7. 13 条断言的**完整性自检**（`verify_assert_completeness`）能否被**未被拦下的输入**
   绕开 —— 例如某条断言在某分支下根本没 emit 而进程仍以 rc=0 退出？

---

## §四 输出格式

逐条给出：

```
[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> <一句话结论>
  何以成立：<一句复现思路 —— 用「负控输入」「对照输入」「未被拦下的输入」「门未覆盖的路径」这类措辞>
```

没有该等级的发现就写「本级无」。最后给一行 `BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

---

## §五 边界

- 只读审查。不要修改任何文件，不要起容器，不要连数据库（本机 Neo4j 在 7691，**不要连**）。
- 不评 `scripts/verify_vault_install.py` / `scripts/vault-install-manifest.json`
  （那是同车道下一张卡 P3-B 的面）。
- 不评 compose 的隔离方案本身应该怎么改 —— **compose 四项共享面是本卡登记的事实，
  不是本卡的缺陷**；改法等用户裁定后另立卡。
- 不要求本卡新增 pytest 文件（本卡地盘无测试文件，判据在 harness 自身与证据里）。
- `deploy-vault.sh` 等既有脚本的缺陷请**登记**（标注即可），不要求本卡就地修。

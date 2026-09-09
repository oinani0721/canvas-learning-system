# 一 背景与最小读取面

你在只读沙箱里审查一个新增的部署脚本与一处 compose 参数化。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff 0ee633ea a6978b58 -- . ':(exclude)_bmad-output'` —— 本卡代码面全量改动
2. `scripts/deploy-vault.sh` 全文（本卡新增）
3. `docker-compose.yml` 全文（本卡只改 5 处 `container_name`）
4. `scripts/install-vault.sh`（本卡只改头注 2 行 + activate 分支加 1 行警告）
5. `backend/tests/unit/test_deploy_vault_sh.py` 全文（本卡新增的门）
6. `_bmad-output/审查/evidence-g27b/` 下：`dryrun-*.txt`、`apply-*.txt`、`neg-*.txt`、
   `mutation-*.txt`、`compose-gate-*.txt`、`step3-phaseAB-*.txt`

**不要读**：任何 `.env*` 文件的内容、任何密钥件、live vault（
`/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault`）下的文件。
证据文件里密钥只以 sha256 出现，如果你看到疑似明文密钥，请直接指出这是缺陷。

## 这个脚本做什么

`scripts/deploy-vault.sh` 把「新建一个课程学习库」做成六步，缺省 dry-run（不传 `--apply` 零写）：

```
[1/6] preflight   harness 树完整性 / 禁写面 / vault 名命名不动点 / 端口 / skills 数 / main.js
[2/6] install     调 install-vault.sh（不加 --activate）
[3/6] postprocess 按实例重生鉴权 key（0600）同步三处 / .env.<vault> / 端口模板化 / 在位判
[4/6] verify      调 verify_vault_install.py，rc 必须 0
[5/6] activate    只 docker compose config 断言；up -d 需用户授权
[6/6] evidence    落 deploy-<ts>.txt（密钥只 sha）
```

rc：0 成功 / 64 用法错 / 7N 第 N 步失败。

# 二 作者自述，请独立核对（不要采信，去代码里验）

1. 六步各有一条负控输入，实测 rc 与消息片段都对上（存档 `neg-*.txt`）。
2. 禁写面判据对 `--vault` / `--evidence-dir` / `--env-dir` **三个**路径参数使用同一份
   `realpath` 判据；对尚不存在的路径取最近存在祖先的物理路径再拼回剩余段。
3. compose 5 处 `container_name` 参数化后，不传任何变量时 `docker compose config` 渲染与
   参数化前**逐字节相同**；单独覆盖任一变量只改它自己那一行。门带 `--profile test/windows/dev`
   ——因为缺省只渲染 2 个服务，另 3 处会落在门外。
4. 密钥三处同值（key 文件 0600 / `.env.<vault>` / 插件 `data.json`），且「已存在则不重生」。
5. 步 3 拆成 Phase A（全部只读校验）与 Phase B（写），key 文件最后写。
6. 步 5 只 `docker compose config`（`CLS_DEPLOY_NO_DOCKER_UP=1` 时断言后 SKIP），本卡未真起容器。
7. 步 4 在 `--port != 8011` 时用「同端口口径的源镜像」当 `--source`，以保留 content-drift 轴。
8. 幂等：第二次 `--apply` 被 install 的防覆盖闸门拦成 rc 72，目标零字节变化。

# 三 请按重要性排序回答这些问题

1. **禁写面判据的覆盖完整性**：`is_forbidden()` / `resolve_abs()` 对下列路径别名形态，
   判据是判成命中还是不命中——软链、大小写差异（APFS 默认大小写不敏感）、`..` 片段、
   相对路径、`~` 未展开、路径中含空格或换行、多重软链、指向父目录的软链。
   每种形态请给出一条输入与你预期的 rc。哪些形态会让本该受保护的目录被判成不命中？
2. **`set -euo pipefail` 与三态返回码**：每个 `stepN` 在 `|| rc=$?` 条件上下文里调用，
   函数体内 set -e 被抑制。哪一步的哪一条命令失败后，函数会继续往下走并最终 `return 0`
   或 `return 2`，从而让「没做成」被打印成 `OK` 或 `SKIP`？rc 表（70+N）与六行输出是否
   在所有路径上一致？
3. **密钥三处同步的中间失败态**：Phase B 的 B2/B3/B4/B5 任一失败时，key 文件 / `.env` /
   `data.json` 各处于什么状态？重跑能否收敛？「key 已存在则不重生」在什么情况下会让
   一个**旧** key 被保留下来而其余两处指向新值？
4. **compose 参数化的现网影响**：不传变量时现网 `docker compose up -d backend` 会不会
   重建容器？缺省值是否逐字等于原常量？`config` 等价这条门是否真的覆盖了这一点，
   还是只覆盖了它的一部分？
5. **`--harness` 缺省推断**：`docker compose ls --format json` 在 0 个 / 2 个 / 项目
   Status 非 "running" 前缀 / `ConfigFiles` 含多个逗号分隔路径时，推断分支的行为分别是什么？
6. **新增的门本身**：`test_deploy_vault_sh.py` 里哪些断言是「看起来在测但实际恒真」的？
   特别是 `test_no_var_ref_followed_by_non_ascii`、`test_port_templated_files_is_single_source...`、
   `test_step4_uses_mirrored_source_when_port_differs` 这三条源码级门——什么样的实现改动会让它们不再报红？

# 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条：

```
[级别] 一句话结论
  file:line
  为什么成立：<一句>
  怎么看到：<一句思路，不需要写出可运行的东西>
```

没有该级别就写「无」。

# 五 边界

- 只读。不要修改任何文件。
- 不连数据库（Neo4j 7691/7687）、不起容器、不跑 `docker compose up/down`。
- 不评 `scripts/verify_vault_install.py` 与 `scripts/vault-install-manifest.json` 的本体
  （它们由 CARD-RV-G2-6 / CARD-G2-7a 定稿，本卡只调用）。
- 不评二线宿主（codex / opencode / dsh）支持——本版明确不实现。
- 不评 `install-vault.sh` 的复制/生成逻辑本体（本卡只改头注与 activate 警告）。

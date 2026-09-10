# 一 背景与最小读取面

你在只读沙箱里审查一个新增的部署脚本与一处 compose 参数化。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff 560bf59f 8f525887 -- . ':(exclude)_bmad-output'` —— 本卡代码面全量改动
2. `scripts/deploy-vault.sh` 全文 + **`scripts/cls_forbidden_paths.py` 全文（本轮新增：禁写面判据本体）**
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




# 二''' round-3 的处置（请独立核对）

你 r3 的 4 BLOCKER / 4 HIGH / 5 MEDIUM / 1 LOW **全部认下**，无一驳回。**含你标为
「登记不阻断」的 MEDIUM-4/5 也一并修了**，没留给下一卡。

- **B-1（我三轮都没想到的那一层）**：`mkdir -p` 的写入面不是**一个** inode 而是**一串**。
  r2 我用 realpath 修好了「算错落点」，但「落点」本身不是全部写入面。新增
  `mkdir_p_segments()` 逐段累积、每段单独过判据（`..` 不折叠 —— 它前面的段已落地）。
  另一半：`.git → 外部目录` 时 realpath 后 `.git` 段消失 ⇒ 该规则**同时**在原始路径上查。
- **B-2**：五个 evidence 报告路径（含 tmp）进判据；`: > "$ilog"` **之前再查一次 `-L`**。
- **B-3**：所有 tmp 进 `-L` 列表。
- **B-4**：`$(dirname)`/`$(basename)` 换 `${VAULT%/*}`/`${VAULT##*/}`，不经命令替换。
- **H-1**：HOME 枚举失败改 **fail-closed**（报 HIT）；`.claude` 前缀匹配改大小写不敏感。
- **H-2**：`unicodedata.normalize("NFC")` 后再 lower（**如实声明**仍不等于 APFS 完整规范化）。
- **H-3**：两处 python 写入改 `with` + `flush` + `os.fsync`。
- **H-4**：A3 补读取 rc、**缺键也拒**、比较范围加 `VAULTS_ROOT`。
- **M-1（我上一轮引入的回归）**：`{ printf … || exit 1; }` 的大括号在当前 shell 执行，
  `exit 1` 绕过 `run_step` 的 7N 映射 ⇒ 改逐条判 rc 后 `return 1`。
- **M-2**：`shasum` 判 rc（非空≠成功）；失败时写 `rc=76` 而非先写 `rc=0`。
- **M-3**：`find | wc | tr` 用 pipefail 子 shell 取 find 的 rc。
- **M-4**：剥离门改成**真的走 `_run`**（加 `script=`）+ **反向锚**（不经 `_run` 时宿主值必须可见）。
- **M-5**：产出对象门连**实际路径表达式**一起钉；补 `.claude*` 两条规则的定向门
  （尚不存在的必拦 / HOME 不可枚举必 fail-closed，真造 `--x--x--x` 的假 HOME）。
- 一并补上 r2 遗留：头注同步为 python 判据实现；M14 的 `lsof` 三态门 + 控制组。

⚠️ **整改自身第三次同型回归**：新加的逐段判先 `expanduser`，把「字面 `~`」那条规则吃掉了
（新加一层让原有一条失效，与你 r2 BLOCKER-3「收紧丢掉一轴」同型）。已把规则 6 前置。
**登记不阻断、未整改**：内容比较门不能排除「目标与自身比较」（缺一条目标漂移负控）；
`ancestor_symlink_hits` 被逐段判涵盖后没有独立门（如实标为防御深度）；
`<<<` here-string / python 字节码缓存的隐式写入面；步 5 的 75 与步 6 的 76 缺入口级负控；
「六行状态」落盘只有前五行；`assert yaml is not None` 恒真；通配符门只验输出行数。

# 三''' 本轮请重点回答

1. **逐段判是否正确且完整**：`mkdir_p_segments` 对 `..` 不折叠、对 `.` 跳过；中间段按
   outputs 口径判、只有最后一段按调用方口径。这个划分有没有让某类对象该拦没拦？
   `mkdir -p` 的真实行为（POSIX / macOS）与这个模型有哪些偏差？
2. **B-2/B-3 的「再查一次 `-L`」是否够**：从 preflight 到实际写入之间还有哪些窗口？
   哪些写入点仍然没有「写之前最后一道」检查？
3. **H-1 的 fail-closed 会不会太宽**：HOME 正常可枚举时不受影响，但有没有场景会让它
   在合法情况下持续报 HIT（判据退化成永远拦）？
4. **整改自身有没有第四次同型回归**：我三轮各一次（修 A 破坏 B）。这一轮还有吗？
5. **新门是否承重**：M-4 的反向锚、M-5 的路径表达式断言、`.claude*` 两条定向门、
   `lsof` 三态门 + 控制组 —— 哪些仍是「看起来在测但实际恒真」的？

# 二'' round-2 的处置（请独立核对）

你 r2 的 4 BLOCKER / 2 HIGH / 4 MEDIUM / 2 LOW 我**全部认下**，无一驳回。

- **B-1（根因）**：你指出的不是细节漏了，而是**层次错了** —— 三种解释全是词法/逻辑层面的。
  判据整体搬到新文件 `scripts/cls_forbidden_paths.py`，用 `os.path.realpath`（先解链再折叠）。
  bash 侧的 `norm_path` / `lower` / `build_forbidden` / `_hits_one` 全删。
- **B-2**：`.git` 与 `.env` 名的比较全部移到归一后的 key 上。
- **B-3**：`.claude*` 改成**两条并存** —— 已存在条目的解析结果（覆盖软链目标）+ HOME 下词法前缀
  （覆盖尚不存在的）。
- **B-4**：判据现在还收 `.env.<vault>` 与它的 `.tmp`、key 文件与 `.tmp`、插件 `data.json`、
  preflight build 的两个落点；已存在对象若本身是软链直接拒。
  ⚠️ 由此引入了**两类对象**：`--strict`（三个路径参数，含 env 文件名规则）与 `--outputs`
  （脚本自己的产出，跳过 env 文件名规则 —— 否则 `.env.<vault>` 会被自己的规则永远拦下，
  本卡实测过：整改后所有正控一度 rc 71）。
- **H-1**：`_STRIP_ENV` 剥掉宿主的 `CLS_DEPLOY_ALLOW_DOCKER_UP` + 专门的剥离门。
- **H-2**：`grep` / `lsof` 全改**三态**（rc 2 或异常 = 读不动/问不出来，不是「没有」）；
  seed 白名单逐项判 rc + 写后回读六键；`shasum` 失败留痕并让步 6 FAIL；步 5 `mkdir` 判 rc。
- **MEDIUM**：B5 回读补判 `cat` 的 rc；**并按你的意见更正了一处失实注释** ——
  原写「重跑会重生并覆盖两处 ⇒ 自愈」，实际整脚本重跑先被 install 拦成 72，**不会自动收敛**。
- **MEDIUM（门不承重）**：把源码门换成**行为门** ——
  `test_step4_actually_evaluates_content_drift_when_port_differs` 看 verify 报告里
  `content-drift == 0` 且 `match > 0`。新增 24 条判据本体门（喂输入看判定），**两个方向都测**。
- 已 KILLED 的变异（点名的门都红了）：M9 把 `src` 改回源树（**你说源码门杀不死的那条**）、
  M10 `.git` 去归一、M11 `realpath`→`abspath`、M12 outputs 不跳过 env 名、M13 判据不收产出对象。
  M14（`lsof` 三态退回两态）**如实标 NOGATE：这条退化当前没有门能抓**。
- **登记不阻断**（未整改）：`<<<` here-string 在 Bash 3.2 用临时文件 / python 未禁字节码缓存
  （「preflight 前零写」的隐式写入面）；步 5 的 75 与步 6 的 76 缺入口级负控；
  「六行状态」落盘只有前五行；`assert yaml is not None` 恒真。

# 三'' 本轮请重点回答

1. **新判据 `cls_forbidden_paths.py` 本身**：还有哪些形态能让本该受保护的对象被判 OK？
   请特别看：`realpath` 对**循环软链**、对**权限不可读的中间段**、对 `//` 与尾部 `/`、
   对 NFC/NFD 不同规范化形式的中文路径；`ancestor_symlink_hits` 的 64 步上限；
   `build_targets` 里 `os.listdir(home)` 失败时静默 `pass` 的后果。
2. **两类对象（strict / outputs）的划分是否正确**：有没有哪个对象被划错组，
   从而要么被误拦、要么该拦没拦？`--outputs` 只跳过 env 文件名规则，这个「只」成立吗？
3. **H-2 之后失败传播还有缺口吗**：请按步骤列。特别是我这轮新加的
   `: > "$ilog"`、seed 的回读循环、步 6 的 `_sha_fail`。
4. **整改自身有没有引入新缺陷**：r1 和 r2 我各引入过一次回归（r1 打断步 2、r2 一度让
   所有正控 rc 71）。这一轮还有吗？
5. **新门是否承重**：24 条判据本体门 + 那条行为门，哪些是「看起来在测但实际恒真」的？
   什么样的实现改动会让它们不再报红？

# 二' round-1 的处置（请独立核对，不要采信）

你 r1 的 2 BLOCKER / 4 HIGH / 3 MEDIUM / 2 LOW 我**全部认下**，无一驳回。整改要点：

- **BLOCKER-1**：判据改成三种解释**并列**判定，任一命中即拦 —— `resolve_abs`（解软链）、
  `norm_path`（纯字符串折叠 `.`/`..`）、`lower()`（大小写归一后比较）；`$HOME/.claude*`
  从 glob 枚举改为 `FORBIDDEN_PREFIX` 前缀规则。方向刻意选**多拦**。
- **BLOCKER-2**：删掉主流程顶层的 `mkdir -p "$EVIDENCE_DIR"`，改由通过了 preflight 的
  步骤自建。⚠️ 这个修复自己打断了步 2（install 输出重定向依赖那个目录），已在步 2 补建
  并把「重定向失败」与「install 非零」分成两条消息。
- **HIGH-1**：步 4 在 `APPLY != 1` 时一律 SKIP。
- **HIGH-2**：闸门反转成 opt-in `CLS_DEPLOY_ALLOW_DOCKER_UP`（缺省 0 = 不 up）。
- **HIGH-3**：补了 14 处显式失败判定；evidence 与 key 文件改 tmp+mv 原子落盘（key 还加了
  写后回读比对）；`down` 失败不再声称「已回滚」；`curl` 单独判 rc。
- **HIGH-4**：`cat` 读 key 判 rc + 校验 64 位小写 hex + 回读比对。
- MEDIUM-2：Status 前缀匹配改大小写不敏感；`ConfigFiles` 含多份时**拒绝推断**。
- LOW-1：非 ASCII 门改按**逻辑行**扫（`_logical_lines` 折叠 bash 续行），验伪锚加续行样本；
  `docker ps` 改三态（rc≠0 = 问不出来，不是「没有」）。
- LOW-2：`_compose_config` 先 pop 掉 5 个 `CLS_*_CONTAINER`。
- MEDIUM-1 / MEDIUM-3 **登记不阻断**（协议 §1），未整改。

# 三' 本轮请重点回答

1. **BLOCKER-1 的修复是否完整**：三种解释并列之后，还有哪些别名形态能让本该受保护的目录
   被判成不命中？特别是：`norm_path` 折叠 `..` 时不解软链，`link/..` 的两种语义我都查了，
   但这个「都查」本身有没有反过来造成**误拦合法路径**的情况（控制组我只测了一条）？
   `lower()` 用 `tr` 对非 ASCII 路径段会怎样？
2. **BLOCKER-2 的修复是否留下别的早写点**：除了 evidence 目录，preflight **之前**还有
   哪些语句会写文件或创建目录？（含参数解析阶段、`--harness` 推断阶段）
3. **HIGH-3 的 14 处是否覆盖完整**：还有哪些动作命令的失败会被吞掉？请按步骤列。
4. **HIGH-4 的原子性是否真的成立**：`tmp + 回读 + mv` 这套在 B3/B4/B5 之间任一失败时，
   三处状态分别是什么？重跑能否收敛？（我已如实声明「重跑会先 rc 72，adopt 归下一卡」）
5. **整改自身有没有引入新缺陷**：r1 我已经因为一个修复打断了另一步。这一轮还有类似的吗？
6. **新加的门是否承重**：`_logical_lines`、三种解释并列、`docker ps` 三态 —— 哪些是
   「看起来在测但实际恒真」的？什么样的实现改动会让它们不再报红？

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

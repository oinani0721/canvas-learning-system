# 一 背景与最小读取面

你在只读沙箱里审查一个部署脚本与它的禁写面判据。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff e5ab1af0 fd2972e6 -- . ':(exclude)_bmad-output'` —— **本轮（r6 整改）改了什么**
   本卡代码面**全量**（若要从头核）：`git diff 0ee633ea fd2972e6 -- . ':(exclude)_bmad-output'`
2. `scripts/cls_forbidden_paths.py` 全文（禁写面判据本体，本轮改动最集中）
3. `scripts/deploy-vault.sh` 全文
4. `docker-compose.yml` 全文（本卡只改 5 处 `container_name`，本轮未动）
5. `backend/tests/unit/test_deploy_vault_sh.py` 全文（本卡的门）
6. `_bmad-output/审查/evidence-g27b/` 下：`mutation-r6-postfmt-*.txt`（10 条变异 + 1 探针）、
   `mutate_r6.py`（变异脚本本体）、`positive-r6fix-*.txt`（正控 + H-3 端到端）、
   `judges-r6fix-*.txt`（负控 8 条）、`dir-red-diff-r6fix.txt`、`close-recon-r6fix-*.txt`

**不要读**：任何 `.env*` 文件的内容、任何密钥件、live vault
（`/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault`）下的文件。
证据里密钥只以 sha256 出现；若你看到疑似明文密钥，请直接指出这是缺陷。

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

⚠️ 轮次说明：r5 是 D-15 的 5 轮上限，**用户随后显式授权继续**，故有 r6 / r7。

# 二 round-6 的处置（请独立核对，不要采信）

你上一轮给了 **2 BLOCKER / 1 HIGH / 5 MEDIUM / 0 LOW**。我**全部认下、无一驳回**。
其中**三条直指我 r5 的工作**，我认为那三条是本轮最该被你复核的部分。

## 二.1 HIGH-1 —— 我 r5 引入的越界写（你说得对，旧版反而没有）

r5 我为消除「密钥落进宽权限文件」的窗口，在 bash 里加了写前 `chmod 600 "$ENV_FILE"`。
你指出：目标在 A3 校验后、B4 前被换成指向保护文件的软链/硬链接时，那次 chmod 会
**先改掉保护对象的权限**，之后才轮到 `O_NOFOLLOW` / nlink 拒写；而且它改的是**元数据**，
内容 sha 与 `find -newermt` 两道对账都看不见。

**修法不是调顺序而是换工具**：`os.fchmod(fd)` —— fd 由 `O_NOFOLLOW` 取得、且已过 nlink
检查，此时改权限只可能落在那个已确认安全的 inode 上。bash 侧写前/写后两次 chmod
**一并删除**，权限收紧只剩这一处。（自我总结的规则：凡「先检查再作用」，两者须同句柄。）

## 二.2 MEDIUM-2/3 —— 你拆穿了我的变异测试，「7/7 KILLED」不成立

- H-2 变异体产生 `*) : ;`（缺 `;;`）⇒ 红的是 rc 2 语法错，不是入口门；且 `relcourse`
  这种**单段**输入即使入口检查被删也会被 `case */*` 的不变量断言拦成 rc 64、消息同样含
  「绝对路径」—— 两条分支同结果，变异杀不掉。**多段** `parent/course` 才行。
- H-3 期望片段留空 ⇒ 脚本 `frag_ok` 恒真；实际红在 `.index()` 抛的 `ValueError`。

⇒ 新脚本 `mutate_r6.py` 堵两洞：**期望片段必填非空**（加载时 assert）+ 变异后**先做语法
检查**（`.sh` → `bash -n`，`.py` → `ast.parse`），不过判 SETUP-FAIL、**不计 KILLED**。

## 二.3 其余逐条

- **BLOCKER-1**：`chain_resolvable()` 用 `os.stat` 走**整条**链（r5 只验第一跳）。
  ⚠️ 顺带修了一个你没点、但查「`os.access` 为何冗余」时暴露的真缺陷：`k()` 里的
  `realpath(strict=False)` 对**所有**保护目标都吞 EACCES —— `~/.codex` 若是外部软链而
  HOME 不可搜索，它只会以**词法**路径入表。⇒ 整链检查**扩到全部目标**，不只 `.claude*`。
- **BLOCKER-2**：抽出 `under(key, tk)` **单一来源**（`tk == "/"` 返回 True）+ walker 登记根。
- **MEDIUM-1**：上限从「处理段数」改为**软链跳数**。两个方向各一条门：无软链的深段路径
  必须放行、软链环必须 fail-closed。
- **MEDIUM-4**：镜像门再钉**外层守卫**（内层形状对了，外层仍可被 `if false; then` 架空）。
- **MEDIUM-5**：不辩解，加**探针**实测 —— 停用 `ancestor_symlink_hits` 整份测试**全绿**
  ⇒ 该函数**零承重**。已在 docstring 如实改口：保留为纵深，**不再宣称是第二道防线**。

## 二.4 ⛔ 变异抓出我第 3 次「两层互相兜底」

首轮 9/11，两条 SURVIVED 都不是缺陷，是我修 A 时顺手加的 B 把 A 兜住了：

| 重叠对 | 出现在 |
|---|---|
| `ancestor_symlink_hits` ↔ `chain_hits` | r5 |
| `os.access` ↔ `chain_resolvable` | r6 |
| `under()` 根特例 ↔ walker 登记根 | r6 |

三次形状一样：单删任一门都不红 ⇒ 看着两道防线、实际只验过一道。
处置用了**拆职责**（`ancestor_symlink_hits` 不再转调 `chain_hits`）与**组合变异**
（根处理两处一起移除，证明这一**对**承重、同时承认单个不承重）两种；
没有用第三种「改门迁就变异」。最终 **10/10 KILLED**，还原逐字节回变异前 sha256。

## 二.5 实测数字

文件级 **316 passed**（r5 后 311，+5 与「新增 6 − 改名 1」及目录级 4963→4968 三处逐数吻合）；
负控 8 条 71/64/71/64/71/71/**64**(单段相对)/**64**(多段相对)；正控 dry-run + apply rc 0；
**H-3 端到端**：脚本外来源预置的 **0644** `.env.<vault>` → apply 后 **600** + 密钥写入 1 行；
目录级红集对 `da690bf8` 批级基线**逐 nodeid 相等**（202 == 202）。

⚠️ 如实记一次我自己造的并发风险：目录级 pytest 与变异脚本**读写面相交**（后者改写前者
读取的两个脚本）。时间线显示相关用例早于首次变异写入 35 秒且全绿，但余量不足以当证据
⇒ 无并发重跑一次为准；两次 nodeid 集实测相同，污染未发生。

## 二.6 仍未修 / 未证明（请核这份清单是否完整）

- **M-1(r5)** nlink 判据未查 python 的 rc、未覆盖 0 与 bash 整数溢出；
  **M-3(r5)** `tr -d` 删值内所有引号 ⇒ 含 `O'Brien` 的合法父路径在 A3 误拒；
  **M-5(r5)** 红集总量相同不证明事件来源相同 —— 三条**本轮仍未修**。
- **M-2(r5)** 的「ftruncate 前置」与「清单元素被替换」两处仍只有源码门。
- `ancestor_symlink_hits` 已实测零承重，但**未证明**它冗余（只证明现有用例测不到它）。
- `walk_visited` 与内核 namei 的完整等价**未证明**（`.`／末尾 `/`／挂载点／APFS 完整折叠）。
- H-3 **只验了顺序与终态**，没验「密钥落盘那一刻」的权限（无法从外部采样）。
- B-3 在 **root** 下未被验证（门用权限位造前提，root 下 skip）。

# 三 请按重要性排序回答这些问题

1. **`os.fchmod(fd)` 这条路真的关死了 HIGH-1 吗**？（最重要 —— 它是本轮唯一的安全面改动）
   `O_NOFOLLOW` 只挡末段，**祖先目录**在 open 时仍会被跟随：若 `.env.<vault>` 的父目录
   在 preflight 后被换成指向保护区的软链，`os.open` 会打开保护区里的同名文件，
   随后 `fchmod` + `ftruncate` + 写 —— 这算不算我把一个「权限越界」换成了「内容越界」？
   若算，正确形态是什么（`O_DIRECTORY` + `openat` 逐级？还是本卡该如实登记为未闭合）？
2. **`chain_resolvable` 扩到全部目标之后有没有引入新的误拦或性能面**？
   `os.stat` 对每个保护目标各一次；`~/Library` 这类大目录、目标是 FIFO/socket、
   目标在网络卷上不可达时的行为对吗？`FileNotFoundError` 放行、其余 OSError fail-closed
   这个二分，有没有该放行却被拦的常见情形？
3. **`under()` 与 walker 登记根这一对，除了 `tk == "/"` 还有别的退化目标吗**？
   （空串、`"."`、末尾带斜杠的目标、大小写归一后变成前缀关系的两个目标）
4. **上限改成数跳数之后，还有能让 `walk_visited` 不终止或指数膨胀的输入吗**？
   （相对目标反复把祖先段压回队列、目标含大量 `..`、跳数未超但队列持续增长）
5. **我在 §二.6 列的清单完整吗**？本轮改动有没有**新引入**、而我没意识到的未证明项？

# 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入或
什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

# 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务；不要启停容器；不要跑部署。
- 不评 U3-A / U3-B 已定稿的 `verify_vault_install.py` 与 `vault-install-manifest.json`。
- 不评二线宿主（codex / opencode / dsh）—— 本版刻意只 `--hosts claude`，是已裁事项。
- 不评 `_bmad-output/` 下的文档措辞。
- 步 5 的 `up -d` / `curl` / 回滚在车道**刻意未执行**（需用户授权），不要当缺陷提。

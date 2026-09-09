# 一 背景与最小读取面

你在只读沙箱里审查一个部署脚本与它的禁写面判据。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff __R5FIX_BASE__ __R6_SHA__ -- . ':(exclude)_bmad-output'` —— **本轮（r5 整改）改了什么**
   本卡代码面**全量**（若要从头核）：`git diff 0ee633ea __R6_SHA__ -- . ':(exclude)_bmad-output'`
2. `scripts/cls_forbidden_paths.py` 全文（禁写面判据本体，本轮改动最集中）
3. `scripts/deploy-vault.sh` 全文
4. `docker-compose.yml` 全文（本卡只改 5 处 `container_name`，本轮未动）
5. `backend/tests/unit/test_deploy_vault_sh.py` 全文（本卡的门）
6. `_bmad-output/审查/evidence-g27b/` 下：`mutation-r5-final-*.txt`（7 条变异逐条）、
   `mutate_r5.py`（变异脚本本体）、`neg-positive-r5fix-*.txt`（负控 9 条 + 正控 + 端到端）、
   `judges-r5fix-*.txt`、`round5-exposure-bounds-*.txt`

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

⚠️ 轮次说明：r5 是 D-15 的 5 轮上限且判 4B/3H，**用户随后显式授权继续**，故有本轮 r6。

# 二 round-5 的处置（请独立核对，不要采信）

你上一轮给了 **4 BLOCKER / 3 HIGH / 5 MEDIUM / 0 LOW**。我**全部认下、无一驳回**，
七条 B/H 已整改；五条 MEDIUM 只部分处置（见 §二.3）。

## 二.1 逐条修法与关键取舍

- **B-1（HOME 自身是软链 ⇒ 物理别名轴丢失）**：`.claude` 前缀现取**两条** ——
  词法 HOME 与 `os.path.realpath(HOME)` **各拼一次** `.claude`。
  两条需求是**正交**的，不是二选一：不 realpath `.claude` 那一段（否则 r4 的
  `claude-baseball` 误拦 + `.claude-new` 失保护会回来），但要 realpath **HOME 那一段**。
  r3 只留物理、r4 只留词法，所以来回摆。
- **B-2（`resolve_chain` 把路径当原子对象解）**：换成 `walk_visited()` —— 模拟内核 namei
  **逐段**解析：从根逐段拼、每段记录；遇软链读出目标并把目标的**段**压回队列（**不 normpath**，
  让 `..` 在解链之后才处理）；遇 `..` 先记录当前位置再上移；**超限 fail-closed**（原来静默 break）。
  ⚠️ 刻意**不**与 `phys()`/`k()` 合并：前者答「途中经过哪些对象」，后者答「最终落点」，
  合并 = 又一次「统一 helper 删掉一条规则」。
- **B-3（listdir 成功 ≠ 解链成功）**：`os.access(home, R_OK|X_OK)` **加上**对每个 `.claude*`
  软链条目**真的 `readlink` 一次**。两道都要：只问权限位在 root 下恒真（你 r4 LOW-1 同型），
  只 readlink 则在「还没走到条目就不可搜索」时 `islink` 静默 False。
- **B-4（镜像根合法 ≠ 镜像里的对象合法）**：镜像内**实际要写的每个文件**过同一份判据 +
  `assert_writable_now`，清单取自 `$PORT_TEMPLATED_FILES` 单一来源（与 sed 循环同源）。
  复用 `PENDING_WRITES` 的结构，不发明新形状。
- **H-1（`O_NOFOLLOW` 不能整体宣称原子）**：**代码不动，收窄声明** —— 承认它只原子拒绝
  **末段**软链、祖先段照跟，且 `fstat`↔`ftruncate` 之间仍有新增硬链接的窗口。
  验收单原先「两处 python 写入是真原子」的说法已按此改。
- **H-2（相对 `--vault` 让 VAULTS_ROOT 解析基准分裂）**：入口**强制绝对路径**（rc 64），
  与头注本来就写的「必填绝对路径」一致。顺带把因此变成不可达的 `VAULT_PARENT="."` 分支
  改成**显式不变量断言**，而不是留成死代码。
- **H-3（已有宽权限 `.env.<vault>` 时密钥先写后 chmod）**：写入**之前**若文件已存在则先
  `chmod 600`（写后那次保留，覆盖新建情形）；`seed_env_file` 的 tmp 改 `(umask 077 && : > …)`。
  条件执行是必须的 —— 文件不存在时 `chmod` 必失败。

## 二.2 ⛔ 变异测试抓出我两条过度声明（我认为这是本轮最该被你复核的部分）

7 条变异首轮 **5 KILLED / 2 SURVIVED**：

1. **B-2 的门不承重**：我在注释里写「删掉 `hits()` 里的直接 `chain_hits` 调用 = 两个拓扑
   重新放行」，变异证明**这是假的** —— `ancestor_symlink_hits` 内部也转调 `chain_hits`，
   把它兜住了。**两层互相兜底 = 谁都测不出承重**，正是你 r4 批过的「让人以为有两道防线」。
   → 修法是**拆开职责**：`chain_hits` 只在 `hits()` 里调（逐段轴），
   `ancestor_symlink_hits` 不再转调它（只保留 `k(cur)` 的整体 realpath 轴）。
2. **B-4 的源码门挡不住就地失效**：把调用改成 `false && check_forbidden_paths …` 门照样绿
   （你 r4 MEDIUM-4 的原话：「留在注释或不可达代码中仍能满足断言」）。
   → 门加强到钉住整条语句的**形状**（必须是 `if` 的直接条件）。

拆开职责 + 加强门后 **7/7 KILLED**，还原逐字节回变异前 sha256。
每条 KILLED 都验了**声称的那条断言**红了（抓失败正文里的消息片段），不是「某处失败了」。

## 二.3 未修的与如实声明

- **M-1**（nlink 判据未查 python 的 rc、未覆盖 0 与 bash 整数溢出）、**M-3**（`tr -d` 删值内
  所有引号 ⇒ 含 `O'Brien` 的合法父路径在 A3 误拒）、**M-5**（红集总量相同不证明来源相同）
  —— **本轮未修**，已登记转下一卡。
- **M-2** 只修了它点名的第三处（源码门形状）；**ftruncate 前置** 与 **清单元素被替换**
  两处仍只有源码门。
- **M-4** 部分回应：变异脚本落盘（`mutate_r5.py`）、每条绑 nodeid + 断言消息片段 +
  变异前 sha256 + 还原逐字节核对；**但仍没有逐条的变异 diff 全文**。
- **H-3 只验了顺序，没验窗口**：最终权限在整改前后都是 0600，post-hoc 观察不到差别；
  「密钥落盘那一刻文件是什么权限」无法从外部采样，故门钉的是源码顺序。
- **B-3 在 root 下未被验证**：门用权限位造前提，root 下不生效，该用例 `skip`（写明了理由）。
- **H-2 是行为收窄**：判定「无既有调用方受影响」的依据是「本脚本本卡新增、生产零调用方」，
  这是**推断不是全仓 grep 实证**。

## 二.4 实测数字（本轮）

文件级三文件 **311 passed**（r4 后 300）；变异 **7/7 KILLED**；
负控 9 条：71 / 64 / 71 / 64 / 71 / 71 / **64**（相对 vault，新）/ 73 / **74**（镜像软链，新）；
正控 dry-run + apply rc 0，key 0600、`.env` 0600、8011 残留 0、三处密钥同值；
幂等 rc 72 + `diff -r` 空 + `.env` sha 同（`install-vault.sh` 对已存在目标 `exit 66`，
是本卡 §3.3 已裁定的语义，不是回归）。

**B-4 有端到端负控**（不是源码门）：harness 副本的 `canvas-vault/.claude/hooks` 换成指向
保护目录的软链 → rc 74，消息点名 `mirror-.claude/hooks/session-end-archive.py` 与命中目标，
且保护目录 `find -newermt` 计数 **0**；同一副本还原为真目录 → rc 0（控制组）。

# 三 请按重要性排序回答这些问题

1. **`walk_visited()` 的逐段模型对不对**（这一问最重要 —— 它替换的是判据的**模型**，不是一个分支）：
   - 相对软链目标我以「链所在目录」为基准展开，绝对目标则从根重启并把段压回队列 —— 对吗？
   - `..` 我先记录当前位置再上移；`cur` 为根时 `dirname` 的处理有没有边界错？
   - 还有哪些形态会让「逐段」与内核实际 namei 不一致（`//`、末尾 `/`、`.`、
     大小写不敏感卷上的段比较、挂载点、`readlink` 返回空串）？
   - `limit=256` 与「超限 fail-closed」的组合，会不会让某类**合法**深路径被误拦？
2. **拆开 `chain_hits` 与 `ancestor_symlink_hits` 的职责之后，有没有哪一类命中被**两边都漏掉**？
   我用变异证明了两者各自承重，但那只说明「各有一条用例只有它能红」，
   不等于「并集覆盖了原来的并集」。请找反例。
3. **B-1 的两条前缀**会不会引入新的误拦？特别是：物理 HOME 与词法 HOME 互为前缀时、
   HOME 是多跳软链时、HOME 本身以 `.claude` 结尾这类退化输入。
4. **本轮整改有没有再次「修 A 破坏 B」**？前四轮每一轮都发生过。重点看：
   H-2 的绝对路径强制是否让某条既有路径不可达（我把 `VAULT_PARENT="."` 改成了 die64）；
   H-3 的写前 chmod 在「文件是软链 / 有硬链接 / 不可写」时的行为；
   B-4 的 `local -a MIRROR_WRITES=()` 在 bash 3.2 + `set -u` 下的展开。
5. **我在 §二.3 列的「未修与未证明」清单完整吗**？有没有我没意识到、但本轮改动**新引入**的
   未证明项？

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

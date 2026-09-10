# 一 背景与最小读取面

你在只读沙箱里审查一个部署脚本与它的禁写面判据。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff fd2972e6 e924db03 -- . ':(exclude)_bmad-output'` —— **本轮（r7 整改）改了什么**
   本卡代码面**全量**（若要从头核）：`git diff 0ee633ea e924db03 -- . ':(exclude)_bmad-output'`
2. `scripts/cls_forbidden_paths.py` 全文（禁写面判据本体，本轮改动最集中）
3. `scripts/deploy-vault.sh` 全文
4. `docker-compose.yml` 全文（本卡只改 5 处 `container_name`，本轮未动）
5. `backend/tests/unit/test_deploy_vault_sh.py` 全文（本卡的门）
6. `_bmad-output/审查/evidence-g27b/` 下：`mutation-r7-final2-*.txt`（14 条变异 + 1 探针）、
   `mutate_r6.py`（变异脚本本体）、`judges-r7fix-*.txt`（负控 8 条 + H-3 端到端）、
   `dir-red-close-r7fix.txt`（红集 + 收工对账）

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

⚠️ 轮次说明：r5 是 D-15 的 5 轮上限，**用户两次显式授权继续**，故有 r6 / r7 / r8。

# 二 round-7 的处置（请独立核对，不要采信）

你上一轮给了 **0 BLOCKER / 1 HIGH / 3 MEDIUM**。四条**全部认下、无一驳回**。

## 二.1 ⛔⛔ HIGH-1 —— 我的第一版修法被自己的三行冒烟当场证伪

你指出 `O_NOFOLLOW` 只挡末段、祖先照样被跟随，并给了方向（从可信目录 fd 起逐级
`O_DIRECTORY|O_NOFOLLOW`）。

**我的初版**：写入时 `realpath(父目录)` 后逐级 `O_NOFOLLOW`。论证是「合法软链
（macOS `/tmp -> /private/tmp`）已被解析掉所以不误拒」。冒烟三行直接打脸：

```
③ 祖先软链: FAIL —— 没拒
```

误拒确实没了，**但拦截也没了** —— 在**作用时刻**调 `realpath` 等于**替攻击者把那条链
走完**：它把要检测的软链解成了目标真路径，逐级遍历一路畅通。
与我 r5 的 `chmod` 是同一个错的第二次显形：**解析/检查发生在作用时刻而非可信时刻**。

**最终形态**（`cls_forbidden_paths.open_pinned()`，两步缺一不可）：
1. `realpath` 父目录后**立刻用本模块判据重新校验解析结果**（`hits()`）—— 管「链被换到哪」；
2. 再沿那个**已校验的物理串**逐级 `O_DIRECTORY|O_NOFOLLOW` + `openat` 叶子 ——
   管「校验之后到打开之间又被换」，由内核原子拒绝。

配套：`.env` 与 `data.json` 的**读与写绑到同一个 pinned fd**（你点的「783 行读取之后替换
会把安全文件旧内容写进保护文件」）；`:564` / `:841` 两处路径式 `chmod` → `chmod_pinned`；
脚本内**裸 `chmod` 归零**（门断言）。

⚠️ 放进判据模块是为**单一来源**（4 个调用点各抄一份遍历 = 必然漂移，本卡栽过一次），
模块因此从「禁写面判据」扩为「路径安全判据**与原语**」，DD-13 口径写进模块 docstring。

**如实声明的残留**：只关「祖先被换成指向**保护目标**的软链」。换成指向另一个**非保护**
目录、或祖先被**改名/替换成真目录**时本函数**不设防**（需目录 fd 稳定性前提或权限隔离）。

## 二.2 其余三条

- **M-1**：`fchmod` 从「钉在 `fstat` 之后」收紧到「钉在 **nlink 拒绝分支之后**」。
- **M-2**：`mkdir_p_segments("/")` 返回**空列表** ⇒ 逐段循环零次迭代直接 `OK`。
  空列表不代表「没有写入面」，而代表「写入面就是根本身」⇒ 补 `segs = [os.sep]`。
- **M-3**：你说得对，源码门证不了控制流可达。⇒ **换一层判据**：升级为**端到端 pytest 门**
  + 控制组（`canvas-vault` 仅 1.5M，副本 2 秒）。源码门保留但不再单独承担该主张。

## 二.3 变异：两次修正后 14/14 KILLED，首轮两条问题都在**我的门与变异体**

1. **SETUP-FAIL**：H-1(r6) 变异体锚点指向我已重写掉的 `.env` 块 —— r6 把「片段没找到」
   从静默跳过改成计入 `bad`，它才变成「变异集与代码脱节」的信号。
2. **SURVIVED**：门名叫「保护目标为根」，而 M-2 修的是「**输入路径**为根」——
   同一个「根」字让我以为覆盖到了。⇒ 补 `test_forbidden_judge_checks_root_path_input`。
   ⚠️ 这条我改了两次才对：首次改 nodeid 时锚点带了 `]`、字符串没匹配上、脚本静默什么
   都没改却仍打印 SURVIVED，我一度误判成代码问题 ⇒ 改用行号 + 内容断言。

## 二.4 实测

文件级 **134 passed**（本文件，含 3 条 r7 新门）；变异 **14/14 KILLED** + 探针
（`ancestor_symlink_hits` 仍实测零承重）；负控 8 条 71/64/71/64/71/71/64/64；
正控 apply rc 0；**H-3 端到端** 预置 0644 → apply 后 600 + 密钥写入 1 行；
目录级红集对 `da690bf8` 基线**逐 nodeid 相等**（202==202），
`passed` 4968→4973 与「新增 5 / 删除 0」逐数吻合。

## 二.5 仍未修 / 未证明（请核这份清单是否完整）

- **M-1(r5)** nlink 判据未查 python 的 rc、未覆盖 0 与 bash 整数溢出；
  **M-3(r5)** `tr -d` 删值内所有引号 ⇒ 含 `O'Brien` 的合法父路径在 A3 误拒；
  **M-5(r5)** 红集总量相同不证明事件来源相同 —— 三条**仍未修**。
- `ancestor_symlink_hits` 实测零承重，但**未证明**它冗余（只证明现有用例测不到它）。
- `walk_visited` 与内核 namei 的完整等价**未证明**（`.`／末尾 `/`／挂载点／APFS 折叠）。
- `open_pinned` 的残留面见 §二.1 末段（非保护目录、改名/替换成真目录）。
- 六处 **bash 重定向**写入点仍是路径式（`assert_writable_now` 紧邻复查，残留窗口不为零）。
- B-3 在 **root** 下未被验证（门用权限位造前提，root 下 skip）。

# 三 请按重要性排序回答这些问题

1. **`open_pinned` 的两步真的关住了你 r7 点的那条路径吗**？特别是：
   - ① 与 ② 之间仍有窗口（判据用的是路径、②用的是逐级 open）——这个窗口里能做什么？
   - `os.path.realpath` 对**不存在**的父目录返回未解析串，此时 ① 判什么、② 走到哪一级失败？
   - 叶子用 `O_CREAT|O_NOFOLLOW`：叶子**已存在且是软链**时 errno 是什么、外层区分得开吗？
2. **`chmod_pinned` 用 `O_RDONLY` 打开再 `fchmod`**：对**只写不可读**的既存文件（如 0200）
   会不会打不开从而拒绝合法操作？对目录、FIFO、socket 呢？
3. **把 `open_pinned` 放进判据模块**引入了循环依赖或行为耦合吗？
   （`open_pinned` 内部调 `build_targets`/`hits`，而 `build_targets` 会枚举 HOME、
   做 `os.stat` —— 每次写入都跑一遍，有没有性能或 fail-closed 面的新问题？）
4. **本轮整改有没有再次「修 A 破坏 B」**？重点：`.env` 读写合并到一个 fd 之后，
   原来「先读全量再决定写什么」的语义有没有变（空文件、无尾换行、非 UTF-8）？
5. **§二.5 的清单完整吗**？本轮**新引入**而我没意识到的未证明项有哪些？

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

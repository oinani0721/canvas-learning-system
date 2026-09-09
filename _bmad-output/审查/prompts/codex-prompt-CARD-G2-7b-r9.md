# 一 背景与最小读取面

你在只读沙箱里审查一个部署脚本与它的禁写面判据。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff e924db03 26003c23 -- . ':(exclude)_bmad-output'` —— **本轮（r8 整改）改了什么**
   本卡代码面**全量**（若要从头核）：`git diff 0ee633ea 26003c23 -- . ':(exclude)_bmad-output'`
2. `scripts/cls_forbidden_paths.py` 全文（禁写面判据本体，本轮改动最集中）
3. `scripts/deploy-vault.sh` 全文
4. `docker-compose.yml` 全文（本卡只改 5 处 `container_name`，本轮未动）
5. `backend/tests/unit/test_deploy_vault_sh.py` 全文（本卡的门）
6. `_bmad-output/审查/evidence-g27b/` 下：`mutation-r8-final3-*.txt`（18 条变异 + 1 探针）、
   `mutate_r6.py`（变异脚本本体）、`judges-r8fix-*.txt`（负控 8 条 + 正控 + H-3 端到端）、
   `dir-red-close-r8fix.txt`（红集 + 收工对账 + H-2 双向实测）

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

⚠️ 轮次说明：r5 是 D-15 的 5 轮上限，**用户两次显式授权继续**，故有 r6 / r7 / r8 / r9。

# 二 round-8 的处置（请独立核对，不要采信）

你上一轮给了 **0 BLOCKER / 4 HIGH（你判其中 3 条为本轮新增）/ 5 MEDIUM**。
**全部认下、无一驳回。**

## 二.0 ⛔⛔ 先说对我不利的账：r7 那个「架构改进」净产出为负

`open_pinned` 的初衷是收口 r7 HIGH-1。实际账：

| | |
|---|---|
| 收口 | 1 条旧洞（祖先软链指向保护目标） |
| **新引入** | **3 条 HIGH**（你点的 H-1 / H-2 / H-4） |
| 且 | 它自己新加的判据半边 `hits(parent)` **事后被变异证明冗余** |

恢复 `hits(path)` 之后，单独删掉 `hits(parent)` 那半，祖先软链门**仍绿**
（本卡**第 7 次**「两层互相兜底」）。真正还承重的只剩「逐级 `O_NOFOLLOW`」那一步 ——
由「叶子不强制 O_NOFOLLOW」变异 KILLED 证明。**这个账我原样记着，不摊薄。**

## 二.1 四条 HIGH（全部用**加法**修，不再动判据形状）

- **H-1**（我 r7 引入）：把判据对象从「原路径」换成「解析后的父目录」，
  **丢掉了 walker 的沿链 `.git` 保护**。修法 `hits(path) or hits(parent)` —— **只加不换**。
  这是「统一 helper 会删掉一条规则」的第 6 次显形，而我 r6 才刚把这条写进注释。
- **H-2**（我 r7 引入）：`import cls_forbidden_paths` 会写 `scripts/__pycache__/*.pyc`，
  且发生在 `open_pinned` 检查**之前**、不在待写清单里 ⇒ `export PYTHONDONTWRITEBYTECODE=1`。
- **H-4**（我 r7 引入）：裸 `os.write` 短写返回值被忽略 ⇒ `write_all()` 循环写。
- **H-3**（旧洞）：`chmod_pinned` 补 `fstat`/nlink 拒绝 + 限普通文件。

**共同根因**：三条全来自同一个动作 —— 搬进模块 + 换底层原语。
**「换成更底层的实现」总会丢掉高层替你做的事**：`open()` 处理短写与通用换行，
`os.write()` 不会；`import` 会缓存字节码，而那是一次写入。

## 二.2 五条 MEDIUM

M-1/M-2 原语兼容性（0200 文件 EACCES 退 `O_WRONLY`；`O_NONBLOCK` 防 FIFO 阻塞；
非普通文件拒绝）/ M-3 恢复通用换行（否则 `KEY=old\rEXTRA=keep` 被当**一行**整体替换、
连带删掉 `EXTRA`）/ M-4 去掉 `O_CREAT`（文件被移走时应 ENOENT 失败，而不是**造个空文件**
把「实例字段全丢」伪装成成功）/ M-5 两条端到端门补 `main.js` 前置 skip。

## 二.3 变异 18/18，但首轮三条问题**全在我的门与变异体**

1. SETUP-FAIL：锚点指向我已改写的行。
2. SURVIVED：H-4 变异指错了门（钉在 chmod 门上，而它不查 `write_all`）。
3. SUSPECT：门用 `src.index()`，缺失时抛 `ValueError` ⇒ 红的不是断言 ——
   **这正是你 r6 MEDIUM-3 指出过的形状，本卡第 3 次踩**。已全面改 `find` + `assert`。

⚠️ 我在锚点上**连续失败五次**（`]` 结尾 / ruff 折行 ×2 / 转义层 / 改名），
根因同一个：凭记忆手写锚点而文件已被 formatter 改过 ⇒ 最终改为
**让程序去源文件抓真实片段**。五次全部当场暴露，无一静默通过。

`_write_all` 我在**同一轮**里又抄了两份（刚在 `open_pinned` 上避开过），
门用 `count == 2` 撞实测 4（2 定义 + 2 调用）当场抓到，已搬进模块作单一来源。

## 二.4 实测

文件级 **136 passed**；变异 **18/18 KILLED** + 探针；负控 8 条 71/64/71/64/71/71/64/64；
正控 apply rc 0（key/env 均 600）；H-3 端到端 0644→600 + 密钥写入 1 行；
目录级红集对 `da690bf8` 基线**逐 nodeid 相等**（202==202），
`passed` 4973→4975 与「新增 2 / 删除 0」逐数吻合。

**H-2 双向实测**（比源码门强）：删掉 `.pyc` → 跑完整 `--apply`（rc 0，步 3 OK ⇒ 确实经过
import 路径）→ `.pyc` **不重现**；`unset` 该 env 后单独 import → **立刻重现**
⇒ 该 export **承重**，不是装饰。

禁写面：live / `.dsh` / opencode 全 0；裸 `chmod` 与裸 `os.write` 残留均 **0**；
`$WT/.env` sha 同基线。`LaunchAgents` 计 2 = **MLX 本地模型服务**自身 plist；
`scripts/__pycache__` 计 1 = **我自己的临时冒烟**（未带该 env）所写，非脚本。

## 二.5 仍未修 / 未证明（请核这份清单是否完整）

- **M-1(r5)** nlink 判据未查 python 的 rc、未覆盖 0 与 bash 整数溢出；
  **M-3(r5)** `tr -d` 删值内所有引号 ⇒ 含 `O'Brien` 的合法父路径在 A3 误拒；
  **M-5(r5)** 红集总量相同不证明事件来源相同 —— 三条**仍未修**。
- `ancestor_symlink_hits` 与 `hits(parent)` 两处**实测零承重**（探针 / 变异），
  保留为纵深但**不宣称**是第二道防线。
- `walk_visited` 与内核 namei 的完整等价**未证明**。
- `open_pinned` 只关「祖先被换成指向**保护目标**的软链」；换成非保护目录、
  或祖先被改名/替换成真目录时**不设防**（需目录 fd 稳定性前提）。
- 六处 **bash 重定向**写入点仍是路径式（`assert_writable_now` 紧邻复查，残留窗口不为零）。
- B-3 在 **root** 下未被验证（门用权限位造前提，root 下 skip）。
- 每次 `open_pinned` 都重跑一遍 `build_targets`（枚举 HOME + stat 全部目标），
  **无性能实测**，也未证明保护目标集合在一次部署内稳定。

# 三 请按重要性排序回答这些问题

1. **本轮四条修复有没有再次「修 A 破坏 B」**？这是最重要的一问 ——
   本卡已连续三轮出现「修复引入新 HIGH」。重点看：
   - `hits(path) or hits(parent)` 的短路：`hits(path)` 抛异常时会怎样？两者判据口径
     （`skip_env_name=True`）对**叶子本身是 `.env`** 的产出对不对？
   - `write_all` 在 `os.write` 抛 `EINTR`/`EAGAIN`（`O_NONBLOCK` 场景）时的行为；
   - 去掉 `O_CREAT` 后，**首次**部署（文件由 seed 刚建）与 data.json（由 installer 建）
     的时序还成立吗？有没有哪条路径现在必然 ENOENT？
   - `chmod_pinned` 的 `O_RDONLY → EACCES → O_WRONLY` 回退：`O_WRONLY` 打开会不会
     对某些文件产生副作用（截断？不会，但请核）；两次 `open_pinned` 意味着两次判据，
     中间窗口有没有新问题？
2. **`export PYTHONDONTWRITEBYTECODE=1` 够不够**？子进程（installer、verify、compose）
   会继承它；但 `python3 -c`/heredoc 之外，还有哪些路径可能写字节码或其它缓存？
3. **M-3 的通用换行还原**（`\r\n`/`\r` → `\n`）与旧文本模式**逐字节等价**吗？
   有没有输入让新旧两版产出不同的 `.env` 内容？
4. **§二.5 的清单完整吗**？本轮**新引入**而我没意识到的未证明项有哪些？
5. 若你认为本卡应当收敛了，请直说哪些属于「必须本卡修」、哪些可以「登记转下一卡」。

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

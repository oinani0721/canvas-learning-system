# 一 背景与最小读取面

你在只读沙箱里审查一个部署脚本与它的禁写面判据。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff 26003c23 111fb768 -- . ':(exclude)_bmad-output'` —— **本轮（r9 整改）改了什么**
   本卡代码面**全量**（若要从头核）：`git diff 0ee633ea 111fb768 -- . ':(exclude)_bmad-output'`
2. `scripts/cls_forbidden_paths.py` 全文（禁写面判据本体，本轮改动最集中）
3. `scripts/deploy-vault.sh` 全文
4. `docker-compose.yml` 全文（本卡只改 5 处 `container_name`，本轮未动）
5. `backend/tests/unit/test_deploy_vault_sh.py` 全文（本卡的门）
6. `_bmad-output/审查/evidence-g27b/` 下：`mutation-r9-final-*.txt`（21 条变异 + 1 探针）、
   `mutate_r6.py`（变异脚本本体）、`judges-r9fix-*.txt`（负控 8 条 + 正控 + H-3 端到端）、
   `dir-red-close-r9fix.txt`（红集 + 收工对账 + npm build 实测 + ~/.npm 口径更正）

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

⚠️ 轮次说明：r5 是 D-15 的 5 轮上限，**用户两次显式授权继续**，故有 r6 ~ r10。

# 二 round-9 的处置（请独立核对，不要采信）

你上一轮给了 **0 BLOCKER / 1 HIGH（你判为旧遗漏）/ 5 MEDIUM**，并明确
「**r8 新引入 HIGH 0 条**」—— 连续三轮「修复引入新 HIGH」的链条在 r8 断了。
r8 唯一的策略变化是：四条**全用加法**修，一处判据形状都没动。本轮继续照此办理。

我按你 §四十一行的收敛裁定，**只修你点名「必须本卡处理」的四条**，其余登记转下一卡。

## 二.1 H-1 —— preflight 之前的 here-string 临时写入

`IFS=',' read -r -a _hosts_arr <<< "$HOSTS"` 在 Bash 3.2 下会在 `$TMPDIR` **建临时文件**，
而这一行在 preflight **之前**、dry-run 也走到 ⇒ `TMPDIR` 指向保护目录就是一次先于任何
判据的写入，事后删除撤不回。步 4 的 TMPDIR 检查来得太晚且只覆盖非 8011 的镜像分支。

**改成纯参数展开切分**（零子进程、零临时文件）：`${_rest%%,*}` / `${_rest#*,}` 循环，
去空白也用 `${_h# }` / `${_h% }` 而不是 `tr`（那会 fork）。
实测：非注释行 `<<<` **归零**；`--hosts` 三种输入行为不变
（`claude`→0 / `' claude '`→0 / `claude,codex`→64）。

## 二.2 M-1 —— 我 r8 的 EACCES 回退**永远不可达**（你说得对）

`PermissionError` **就是** `OSError(EACCES/EPERM)` 的子类，所以
`except PermissionError: raise` 把**内核**对 0200 文件的 EACCES 也吞了，
下面的 `O_WRONLY` 回退到不了。

**修法不是调顺序，而是给判据自己的拒绝一个专属类型** `ForbiddenPath(PermissionError)`。
自我总结的规则：**按错误来源分流，就不能只按 errno 分，要按「谁抛的」分。**
双向实测：0200 文件 → 收紧到 600 ✅；禁写面拒绝仍是 `ForbiddenPath`、未被回退吞掉 ✅。

## 二.3 M-2 —— 字符串门抓不到「假推进」

你指出把推进改成 `view = view[len(view):]` 后短写会再被当成功、而门仍绿。
**换行为门**：注入每次只写 1 字节的 `os.write`，断言全量落盘 **且调用次数 == 字节数**
（后者专抓「一次跳完」）；控制组：`os.write` 恒返回 0 时必须抛「短写」，
而不是死循环或静默成功。

## 二.4 npm 写入面 —— 不只是改配置，**真跑了一次 build**

`npm_config_cache` / `npm_config_logs_dir` 钉到已过判据的 evidence 子目录，
并关掉 `update_notifier` / `fund` / `audit`。

**实测**（移走 gitignored `main.js` 逼 preflight 触发 E-4 build）：
- 产出落在 `<evidence>/npm-<ts>/{cache,logs}` ✅
- `find ~/.npm -newer <build 标记目录>` = **0** ✅
- `main.js` 重建 **130139 字节**，与移走前**同尺寸** —— 顺带排除「跑成功但产出残缺」

⚠️ 如实声明：这只约束了 npm **配置层**能约束的部分；npm 及其依赖是否还有别的写入路径，
本卡未读其实现，**完整写入集合仍未证明**（已登记）。

## 二.5 变异 21/21，两条 SUSPECT 的处置

首轮两条 SUSPECT —— 门确实红了，但红在**我声称的另一条断言**上。
我去看了**实际失败正文**再据实修正声称，而不是改门迁就猜测：
- M-2 实际命中更根本的那条：`b'0' != b'0123456789abcdef'`（「短写下没有写全」）；
- M-1 是在到达断言**之前**就抛 `PermissionError: [Errno 13]` —— 那正是该缺陷的表现形态。

## 二.6 ⚠️ 一处我自己的口径更正（先前那句话证明的范围比它听起来的小）

我先前写「`~/.npm` 新写入 = 0」，用的是 build 跑完后的 `-newermt '-2 minutes'` ——
只覆盖两分钟。用收工哨兵（跨 ~30 分钟）重算是 **19**。两个数字都对，**口径不同**。
以我的 build 标记目录为界的精确判据：
- `find ~/.npm -newer <build 目录>` = **0** ⇒ 我的 build 确实没写
- `find ~/.npm -newer <哨兵> ! -newer <build 目录>` = **19** ⇒ 全部早于我的 build，
  同期 `ps | grep -c 'npm\|node'` = 23（本批其它车道）
**相对时间窗口不能替代固定哨兵。**

## 二.7 实测数字

文件级 **327 passed**；变异 **21/21 KILLED** + 探针；负控 8 条 71/64/71/64/71/71/64/64；
正控 apply rc 0（key/env 均 600）；H-3 端到端 0644→600 + 密钥写入 1 行；
目录级红集对 `da690bf8` 基线**逐 nodeid 相等**（202==202），
`passed` 4975→4979 与「新增 4 / 删除 0」逐数吻合。
禁写面：live / `.dsh` / opencode 全 0；裸 `chmod` / 裸 `os.write` / 非注释 here-string **均 0**。

## 二.8 按你的裁定**登记转下一卡**（本轮未修）

- M-3(r5) nlink 判据的 rc / 0 值 / shell 整数溢出；M-4(r5) `tr -d` 删值内引号致 A3 误拒。
- 性能（每次 `open_pinned` 重跑 `build_targets`）、完整 namei 等价、APFS Unicode 折叠。
- 目录并发稳定性（祖先被改名/替换成真目录）、事务恢复（三文件不一致、adopt）。
- 六处 bash 重定向写入点仍是路径式（紧邻复查，残留窗口不为零）。
- `chmod_pinned` 的非普通文件限制不覆盖 B3/B4 内容写入（前置检查后换 FIFO 仍可能阻塞）。
- `ancestor_symlink_hits` 与 `hits(parent)` 两处**实测零承重**，保留为纵深、不宣称防线。
- B-3 在 root 下未被验证；证据摘要不足以独立重算红集与事件归属（你 r9 M-5）。

# 三 请按重要性排序回答这些问题

1. **本轮四条修复有没有引入新问题**？（连续两轮「新引入 = 0」是我想守住的）重点：
   - 纯参数展开的 `--hosts` 切分：`HOSTS` 含**连续逗号**、**仅空白**、**极长**、
     或含 `%`/`#`/`*` 等展开元字符时，与原 `read -a` 的行为差异在哪？
   - `ForbiddenPath` 分型后，还有哪些调用点在**按 `PermissionError` 捕获**从而语义变了？
   - `write_all` 的行为门用 `monkeypatch.setattr(cfp.os, "write", ...)`：
     它改的是模块级 `os` 引用，会不会影响同进程内其它测试（顺序依赖）？
2. **npm 那条我只约束了配置层**。在你能静态判断的范围内，还有哪些 npm/node 写入路径
   不受 `npm_config_*` 约束（postinstall、node 自身缓存、esbuild 的临时目录）？
3. **§二.8 的转卡清单**：有没有我列进去、但其实**本卡就该修**的？
   或者反过来，有没有我漏列的？
4. 若你认为本卡已可收敛，请直说；若仍有必须本卡处理的，请只列那几条。

# 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入或
什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条，以及本卡是否可收敛。

# 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务；不要启停容器；不要跑部署。
- 不评 U3-A / U3-B 已定稿的 `verify_vault_install.py` 与 `vault-install-manifest.json`。
- 不评二线宿主（codex / opencode / dsh）—— 本版刻意只 `--hosts claude`，是已裁事项。
- 不评 `_bmad-output/` 下的文档措辞。
- 步 5 的 `up -d` / `curl` / 回滚在车道**刻意未执行**（需用户授权），不要当缺陷提。

# 一 背景与最小读取面

你在只读沙箱里审查一个部署脚本与它的禁写面判据。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff 3504036c afd7e5fc -- . ':(exclude)_bmad-output'` —— **本轮（r11 整改）改了什么**
   本卡代码面**全量**（若要从头核）：`git diff 0ee633ea afd7e5fc -- . ':(exclude)_bmad-output'`
2. `scripts/cls_forbidden_paths.py` 全文（禁写面判据本体，本轮改动最集中）
3. `scripts/deploy-vault.sh` 全文
4. `docker-compose.yml` 全文（本卡只改 5 处 `container_name`，本轮未动）
5. `backend/tests/unit/test_deploy_vault_sh.py` 全文（本卡的门）
6. `_bmad-output/审查/evidence-g27b/` 下：`mutation-r11-final-*.txt`（**26** 条变异 + 1 探针）、
   `mutate_r6.py`（变异脚本本体）、`judges-r11fix-*.txt`（负控 9 条 + 正控 + H-3 + 三条回归面）、
   `dir-red-close-r11fix.txt`（红集 202==202 + 收工对账）

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

⚠️ 轮次说明：r5 是 D-15 的 5 轮上限，**用户两次显式授权继续**，故有 r6 ~ r12。

# 二 round-11 的处置（请独立核对，不要采信）

你上一轮给了 **0 BLOCKER / 1 HIGH / 1 MEDIUM / 1 LOW**，判「本卡尚不可收敛」。
**三条全部认下**，且三条都能追溯到我 r9/r10 修复的副作用。

## 二.1 HIGH-1 —— **顺序错**：绝对化写在了默认值赋值之前

我 r10 把词法绝对化放在默认值赋值**之前** ⇒ `--harness .` + 省略 `--evidence-dir` 时，
默认值 `$HARNESS/_bmad-output/…` 之后才填入，整条仍是相对串、绝对化白做。
**修法**：绝对化挪到两个默认值都赋好之后；`HARNESS` 本身也先绝对化。

## 二.2 MEDIUM-1 —— **分类错**（我 r10 引入的新回归）

我把 `tmpdir` 塞进 `PENDING_WRITES`，而那份清单的语义是「本脚本创建/截断的**叶子文件**」，
其消费方会做 `-L` 软链拒绝 ⇒ macOS 的 `/tmp -> /private/tmp`（`TMPDIR` 未设时的**默认
回退值**）当场 rc 71，dry-run 同样中招。
**修法**：新增 `DIR_WRITES`（「写入其中的目录」），**只过判据、不过叶子规则**。
**自我总结的规则**：**往现成清单里塞新东西之前，先问这份清单的语义是什么。**

## 二.3 LOW-1 —— 语义不等价，且修法越写越复杂说明模型选错了

旧 `tr -d '[:space:]'` 删的是**全部位置**的**所有** ASCII 空白（含 `\v` `\f` `\r` 与
**中间**空白，`cl au\tde` → `claude`）。我 r9 剥首尾、r10 改不动点循环仍只剥首尾。
**修法一行**：`${_h//[$' \t\n\r\v\f']/}` —— 恢复完整语义，顺带消掉 r10 LOW-2 的二次复杂度。

## 二.4 ⛔ 我本轮犯的流程错误（比上面三条更值得你看）

**我只跑 `-k` 过滤子集就以为绿了。** 两条钉源码文本的门早已因本轮改动失效
（`tmpdir` 移出 `PENDING_WRITES`、不动点循环被取代），全量一跑立刻现形。

**更险的是它制造了一个假信号**：变异脚本的探针因此报
「`ancestor_symlink_hits` 现在有 2 条变红 ⇒ 独立承重成立」—— 那 2 条与探针**毫无关系**，
是本来就红的。若采信，会**同时**得出一个假的「承重」判断、并继续错过 2 条失效门。
修好后探针恢复「全绿 ⇒ 仍零承重」，判断得到证实。
⇒ 两条门已同步到新实现（**主张不变、位置变了**）。**改完代码必须跑全量文件级。**

## 二.5 实测

文件级 **145 passed**；变异 **26/26 KILLED**（0 SURVIVED / 0 SUSPECT / 0 SETUP-FAIL）+ 探针，
还原逐字节；负控 **9/9**；正控 apply rc 0（key/env 均 600）；H-3 端到端 0644→600；
三条回归面双向实测（`TMPDIR=/tmp` 与空值放行、`~/.codex` 仍 71；相对 `--harness` 下默认
目录已绝对；中间空白与 `\v\f\r` 全部接受、`claude,codex` 仍 64）。
目录级红集对 `da690bf8` 基线**逐 nodeid 相等**（**202==202**），
`passed` 4981→4984 与「新增 3 / 删除 0」逐数吻合。

⚠️ 目录级跑了 4 次，前 3 次被本机 OOM 杀；其中一次报 `completed` 但**产物不存在** ——
「任务 completed」不等于「任务做完了」，判据必须落在**产物**上。

## 二.6 仍未修 / 未证明（按你 r9 的裁定登记转下一卡，未变）

M-3(r5) nlink 判据的 rc / 0 值 / 整数溢出；M-4(r5) `tr -d` 删值内引号致 A3 误拒；
性能（每次 `open_pinned` 重跑 `build_targets`）；完整 namei 等价 / APFS Unicode 折叠；
目录并发稳定性（祖先改名或替换成真目录）；事务恢复（三文件不一致、adopt）；
六处 bash 重定向仍是路径式；`chmod_pinned` 的非普通文件限制不覆盖 B3/B4 内容写入；
`ancestor_symlink_hits` 与 `hits(parent)` **实测零承重**（保留为纵深、不宣称防线）；
npm 配置层之外的写入路径（`prebuild/postbuild`、`NODE_V8_COVERAGE`、`NODE_COMPILE_CACHE`、
esbuild 临时目录）；B-3 在 root 下未验；证据摘要不足以独立重算红集与事件归属。

# 三 请按重要性排序回答这些问题

1. **本轮三条修复有没有引入新问题**？重点：
   - `HARNESS` 绝对化后，由它派生的**所有**下游路径（installer 参数、`--source`、
     `--harness-tree`、compose `-f`）语义有没有变？`--harness` 传软链目录时呢？
   - `DIR_WRITES` 与 `PENDING_WRITES` 分家后，两者**都**交给判据了吗？
     有没有哪个写入面因为分家而**从两份清单里同时漏掉**？
   - `${_h//[$' \t\n\r\v\f']/}` 在 Bash 3.2 下对**非 ASCII 空白**（U+00A0、全角空格）
     与旧 `tr -d '[:space:]'`（受 locale 影响）的差异，会不会让某个合法宿主名被拒？
2. **我在 §二.4 承认的流程错误**：除了那 2 条，现有门里还有**其它已失效但仍绿**的吗？
   （即：门断言的源码形态已被后续整改取代，但断言恰好仍能满足）
3. **§二.6 的转卡清单**有没有该升级为本卡必修的？
4. **本卡是否可收敛**？若可，请直说；若不可，请只列必须本卡处理的那几条。

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

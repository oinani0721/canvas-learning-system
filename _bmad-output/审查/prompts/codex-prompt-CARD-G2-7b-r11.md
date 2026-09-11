# 一 背景与最小读取面

你在只读沙箱里审查一个部署脚本与它的禁写面判据。仓库根是当前工作目录。

**只读这些，不要扩大读取面**：

1. `git diff 111fb768 3504036c -- . ':(exclude)_bmad-output'` —— **本轮（r10 整改）改了什么**
   本卡代码面**全量**（若要从头核）：`git diff 0ee633ea 3504036c -- . ':(exclude)_bmad-output'`
2. `scripts/cls_forbidden_paths.py` 全文（禁写面判据本体，本轮改动最集中）
3. `scripts/deploy-vault.sh` 全文
4. `docker-compose.yml` 全文（本卡只改 5 处 `container_name`，本轮未动）
5. `backend/tests/unit/test_deploy_vault_sh.py` 全文（本卡的门）
6. `_bmad-output/审查/evidence-g27b/` 下：`mutation-r10-*.txt`（23 条变异 + 1 探针）、
   `mutate_r6.py`（变异脚本本体）、`judges-r10fix-*.txt`（负控 **9** 条 + 正控 + H-3 端到端）、
   `dir-red-close-r10fix.txt`（红集 + 收工对账）

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

⚠️ 轮次说明：r5 是 D-15 的 5 轮上限，**用户两次显式授权继续**，故有 r6 ~ r11。

# 二 round-10 的处置（请独立核对，不要采信）

你上一轮给了 **0 BLOCKER / 2 HIGH（新增 1、旧遗漏 1）**，判「本卡尚不可收敛」。
**两条 HIGH 与一条 LOW 全部认下并整改。**

## 二.1 ⛔ HIGH-1（我 r9 引入）：为堵写入面而**新开的**写入面

我 r9 为「约束 npm 写入面」加的 `mkdir -p "$EVIDENCE_DIR/npm-$TS/{cache,logs}"`
**本身不在待写清单里** —— evidence 下预置 `npm-<TS> -> 保护目录` 时那个 mkdir 直接写进去，
**无需竞争窗口**。你还点出相对 `--evidence-dir` 下「创建」与「使用」的基准分裂
（先按调用 cwd 建，再 `cd` 进插件目录把**同一相对串**交给 npm）。

**修法**：
- npm 子路径 `ev-npm-cache` / `ev-npm-logs` 进 `PENDING_WRITES`（与其它产出同一份清单）；
- `--evidence-dir` / `--env-dir` 在解析期做**词法**绝对化（不 realpath，免得改变语义）。

**自我总结的规则**：**父目录过了判据 ≠ 新建子路径过了判据。**
每次新增写入动作，都要回到那份清单，而不是依赖「它在一个安全目录下面」。

## 二.2 ⛔ HIGH-2：我 r9 只修了一半（here-**string** vs here-**document**）

我删掉 `<<<` 时以为闭合了「preflight 前的临时写入」这一类，实际 Bash 3.2 对
here-**document**（`<< 'PY'`）同样在 `$TMPDIR` 建临时文件，而步 2 的 `pinned_chmod600`、
步 3 两处 python 块都会触发；原唯一的 TMPDIR 检查在步 4，**太晚**且缺省端口 8011 完全跳过。

**修法不是逐个消灭 heredoc，而是把 `TMPDIR` 本身放进 preflight 的待写清单** ——
判一次，覆盖所有后续 heredoc。（preflight 自身只用 `python3 -c` 与带 argv 的调用，无 heredoc。）

**自我总结的规则**：**我修的是这一「类」，还是只是这一个「实例」？**

## 二.3 LOW-1（也是我 r9 引入）：去空白没到不动点

我写成「空格轮 → tab 轮」四段串行，`$'\t claude \t'` 剥完 tab 后留下的空格不再处理
⇒ 旧版接受、新版拒绝。改成**不动点循环**（有任一前后缀是空白就再剥一轮）。

## 二.4 双向实测

| 项 | 结果 |
|---|---|
| TMPDIR 合法（`/var/folders/...`） | dry-run **rc 0** |
| `TMPDIR=$HOME/.codex` | **rc 71**，消息点名 `tmpdir`（负控增至 **9 条**） |
| 混合空白 `$'\t claude \t'` / `$' \tclaude'` / `$'\t \t'` | 全部**恢复接受**（rc 0） |
| `claude,codex` | 仍 **64** |
| 清单 | 含 `ev-npm-cache:` / `ev-npm-logs:` / `tmpdir:` |

## 二.5 裁判

文件级 **142 passed**；变异 **23/23 KILLED** + 探针，还原逐字节；负控 **9/9**；
正控 apply rc 0（key/env 均 600）；H-3 端到端 0644→600 + 密钥写入 1 行；
目录级红集对 `da690bf8` 基线**逐 nodeid 相等**（202==202），
`passed` 4979→4981 与「新增 2 / 删除 0」逐数吻合。
裸 `chmod` / 裸 `os.write` / 非注释 here-string **均 0**。

⚠️ 目录级本轮跑了两次：第一次在 85% 处被**本机 OOM** 杀，raw 无汇总行 ⇒ 被前置判据
直接拦下、**未参与对账**（若不看汇总行就数 nodeid 会得到「红集变少」的假绿）。
加内存守卫后重跑正常。被杀的是 **pytest 而非 codex** —— 我先前只给 codex 加守卫，
是把「表现」当成了「面」，与代码里「修实例还是修类」同错，只是发生在运维侧。

## 二.6 仍未修 / 未证明（按你 r9 的裁定登记转下一卡）

- M-3(r5) nlink 判据的 rc / 0 值 / shell 整数溢出；M-4(r5) `tr -d` 删值内引号致 A3 误拒。
- 性能：每次 `open_pinned` 重跑 `build_targets`；`--hosts` 去空白的二次复杂度
  （你 r10 LOW-2：10,000 前缀空格 0.007s → 2.64s；实际 `--hosts` 值极短，判为可接受）。
- 完整 namei 等价、APFS Unicode 折叠；目录并发稳定性（祖先改名/替换成真目录）；
  事务恢复（三文件不一致、adopt）。
- 六处 bash 重定向写入点仍是路径式；`chmod_pinned` 的非普通文件限制不覆盖 B3/B4 内容写入。
- `ancestor_symlink_hits` 与 `hits(parent)` 两处**实测零承重**，保留为纵深、不宣称防线。
- 你 r10 LOW-3：`write_all` 零进度门缺超时兜底（当前实现有 `n <= 0` 拒绝分支，故不死循环）。
- npm 配置层之外的写入路径（`prebuild/postbuild`、`NODE_V8_COVERAGE`、
  `NODE_COMPILE_CACHE`、esbuild 临时目录）——**完整写入集合仍未证明**。
- 证据摘要不足以独立重算失败正文、红集与事件归属（你 r9 M-5）。

# 三 请按重要性排序回答这些问题

1. **本轮三条修复有没有引入新问题**？重点：
   - `tmpdir:` 进 `PENDING_WRITES` 后，`assert_writable_now` 对一个**目录**做的检查
     （`[ -d ] && return 0`）是否让这条清单项形同虚设？判据侧 `--outputs` 口径对目录对吗？
   - `--evidence-dir` / `--env-dir` 的**词法**绝对化（`$PWD/...`）：`$PWD` 含软链时
     与 realpath 口径不一致，会不会让判据判的与实际写的分裂？
   - 不动点去空白循环：有没有输入让它**不收敛**或与旧 `tr -d '[:space:]'` 语义再次分叉
     （`\v`、`\f`、`\r`、非 ASCII 空白）？
2. **`tmpdir` 这一条真的覆盖了所有 heredoc 吗**？preflight **之前**是否还有别的
   隐式临时写入（进程替换 `<(...)`、`$(...)` 的大输出、bash 自身的 `/tmp` 使用）？
3. **§二.6 的转卡清单**：有没有我列进去、但其实本卡就该修的？有没有漏列的？
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

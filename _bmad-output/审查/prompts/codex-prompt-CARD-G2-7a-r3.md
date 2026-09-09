# CARD-G2-7a 独立复核请求（round-3）

## 一 背景与最小读取面

worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡最终 HEAD **`725bbd19`**。前两轮：round-1 绑 `7aa89c5b`（0B/2H/4M/2L）、
round-2 绑 `3c1e3c00`（0B/1H/3M/3L）。两轮的 HIGH 我都在本机独立复现后才动手。

round-2 的 HIGH 是 **round-1 修法自己开的洞**（先清生成位 + 裸 `cp -R` 保留目录软链 ⇒ 沿链改写模板源）。
所以**这一轮请重点看：round-2 的修法有没有同样开新洞，以及同一问题面还有没有没盖到的入口。**

**请只读以下五处（不要读别的、不要读 live vault、不要执行安装脚本）：**

1. round-2 之后的整改：`git diff 3c1e3c00 725bbd19 -- . ':(exclude)_bmad-output'`
2. 本卡全部改动：`git diff 086771d3 725bbd19 -- . ':(exclude)_bmad-output'`
3. 脚本与清单全文：`scripts/install-vault.sh`、`scripts/vault-install-manifest.json`
4. 校验器全文：`scripts/verify_vault_install.py`
5. 门文件：`backend/tests/unit/test_vault_install_manifest.py`

## 二 round-2 逐条处置

| 你给的级别 | 处置 |
|---|---|
| HIGH-1 目录软链写穿 | 两处递归复制改 `cp -R -H`。门两层：结构门（每条 `cp -R` 必带 `-H`，只看可执行行）+ 行为门（**插件目录自身**是软链时共享源字节不变） |
| MEDIUM-1 不可读 generate 记 match | 形态检查扩为形态+可读性（复用 `_leaf_digest` 的读探测 `probe_bad`），不可读进 unreadable |
| MEDIUM-2 key 自检把 cmp 读错误当通过 | 改四态：`! -e` 放行 / `-f && -r` 两侧都成立才比内容 / 否则显式 ❌ |
| MEDIUM-3 H2 门用不存在的 .env（恒真） | 改用有效且指向别处的 `.env`（`VAULTS_ROOT=other-root` + `ACTIVE_VAULT=other-vault`） |
| LOW-1 清理名单与 generate 无联动 | 已补覆盖一致性门，`OUTSOURCED` 记录两个例外（yaml 独立生成器、key 归 activate 步） |
| LOW-2 origin 错位 / 只验越界 | origin 47 条按当前脚本实测重写；两条钉行号字面量的门改为**内容锚**（`_sh_line`，唯一命中断言）；越界门加「数组区起始行必须真是数组定义行」 |
| LOW-3 文案未收窄 | manifest `description` 与校验器 docstring 两处改（copy 比内容 / generate 不比；缺省源=harness 树） |

自查中修了判据自身两处缺陷：`_extract_block` 的 end 取全局首次命中（会得到 end<start）；
H1 行为门首版夹具把**父目录**做成软链，`cp` 操作数因而是穿链后的真目录，变异去掉 `-H` 照样全绿。

## 三 请按重要性排序回答的问题

1. **`-H` 的语义边界**：它只跟随**操作数**软链。若模板源的插件目录**内部**含软链（文件或子目录），
   TARGET 里仍是链——此时生成段的清理与写入、以及校验器的摘要，各自会发生什么？
   有没有与 round-2 同类的写穿或误判残留？
2. **`probe_bad` 复用 `_leaf_digest`**：对 generate 项多做了一次完整读取（含读全文件字节）。
   有无副作用（大文件、FIFO、权限探测顺序），以及它与后面 `:1097` 记 match 的判定是否一致？
3. **origin 重写的正确性**：47 条改动里有没有指错？内容锚 `_sh_line` 的「唯一命中」在脚本再改时
   会不会变成脆弱点（例如注释里出现同样字样——本轮已发生过一次，我把注释里的行号引用删了）？
4. 三条新门的变异我跑了 3/3 KILLED，但变异体是我自己选的。**还有哪些拆法我没试过？**
5. `wiki/**` exclude 两条加入后，intentionally-excluded 报告面扩张——树自洽门不断言该桶，
   这一点我已登记为未证明。除此之外还有别的桶被静默改变吗？
6. 现在还有哪些声明比证据宽？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条：一句问题 + `file:line` + 一句复现思路。
无问题的项明说「核对结果：无问题」并说明核对程度。

## 五 边界

只读审查；不执行安装脚本；不连数据库；不评 U3-C/U5-B 的消费方。
不需要攻击性内容；关心**误伤与漏报**。

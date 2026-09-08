# CARD-G2-7a 独立复核请求（round-1）

## 一 背景与最小读取面

仓库 worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡 HEAD **`7aa89c5b`**，基线 = 前卡 U3-A 末 `086771d3`。

这张卡把 vault 部署清单升到 v2（E-4：模板源 = harness 树的 git 追踪系统件 + 脚本生成件），
并引入 manifest item 级 `optional` 语义（允许缺失、不计退出码、在位仍比内容）。

**请只读以下五处，不要读别的文件、不要读任何 live vault 路径下的内容、不要跑 install-vault.sh：**

1. 本卡全部改动：`git diff 086771d3 7aa89c5b -- . ':(exclude)_bmad-output'`
2. 逐项裁定表：`_bmad-output/审查/evidence-g27a/manifest-ruling.md`
3. 被改清单全文：`scripts/vault-install-manifest.json`
4. 被改脚本全文：`scripts/install-vault.sh`
5. 校验器全文：`scripts/verify_vault_install.py`（本卡在其上叠加 optional 与 digest 过滤）

被测链路：`install-vault.sh`（五数组 + 复制循环 + 生成件段 + 自检）从模板源部署一个新 vault；
`vault-install-manifest.json` 是部署边界的机器可读投影；`verify_vault_install.py` 只读校验一个
已存在 vault 是否符合清单（退出码 0 ok / 1 只缺 / 2 多出·漂移·读不动·快捷键孤儿 / 3 用法错）。

## 二 作者自述（请独立核对，不要采信）

1. **裁定表分母是现场重算的**（确定性集合运算：`git ls-files -z` ∪ live ls，三重覆盖判据），
   卡文原表不可信（它自己承认漏过 `themes/Underwater/**`）。重算后补了卡文没有的行：
   `.claudian/**`（8 个 git 追踪文件）、`.quarantine/**`、`.trash/**`（均 retire→exclude）、
   `wiki/concepts` + `wiki/canvases`（新增 skeleton——后端 `vault_init_service.VAULT_DIRECTORIES`
   建而脚本不建，两个真相源只在 `raw` 重合）。
2. **`outputs/exam_boards` 刻意不加**：与既有 `outputs/**` exclude 冲突（加进去 20 条既有门全红），
   两条出路都要动既有语义 ⇒ 登记转下一卡。
3. **`settings.local.json` 键名核到**（三源互证）⇒ generate+optional，生成最小件只含
   `{"enabledMcpjsonServers": ["canvas-learning-mcp"]}`；**绝不复制** live 的 5 服务器版本。
4. **校验器 optional**：非 bool 即 ManifestError；缺失进 optional-missing 不计 rc；
   **在位仍比 drift、仍在 declared 不报 extra**。generate 路径**不入父目录摘要**
   （嵌套在 copy 目录里的生成件曾被当 drift，真跑照出后修）。
5. **钉点迁移全带验伪**：MANIFEST_BLOCK (63,67)→(73,77)；数组 6/8/6/5/2→8/6/9/4/3（合计 27→30）；
   match 28→31；declared 28→35；origin 全量重测。
6. 实测：树自洽 rc=0 且 optional-missing 恰等于「declared 且树上 ABSENT」12 项；
   live 源真跑自检 10✅/0❌、校验 rc 0、hotkeys 3 绑定/10 命令/0 orphan；四重禁写证明全清。

## 三 请按重要性排序回答的问题

1. **裁定表还有漏吗？** 分母重算用的三重覆盖判据（manifest 条目含 glob / 脚本数组前缀展开 /
   裁定表已裁项含祖先包含）本身有没有盲区？`extra_scan` 三个覆盖面之外的结构性盲区里
   是否还藏着「漏了不会有门报警」的部署相关项？
2. **optional 语义有没有被滥用**：12 个 optional 项里有没有哪项其实不该 optional
   （缺了它新 vault 会坏）？optional 项在位时真的仍参与 drift/match 吗？
3. **generate 项不入父目录摘要**这个修法有没有引入新盲区（比如真差异藏在生成路径下被剔掉）？
   幂等的生成件段（`[ ! -e ]` 才写）有没有「目标已存在但内容是错的」这类洞？
4. **退役是否干净**：`.claude/mcp.json` / `claudian` / `cls-internal-key.txt` / `settings.local.json`
   退出复制后，还有没有代码或配置引用它们会被部署态破坏？自检反向判（key）的语义对吗？
5. 钉点迁移后的测试有没有弱化（断言从精确值变成恒真）？`(h)` 两跑的期望态本身有没有写错？
6. 裁定表 / UAT 里有没有说得比证据宽的地方？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条：一句问题陈述 + `file:line` + 一句复现思路。
若某项核对无问题，请明说「核对结果：无问题」并说明核对程度。

## 五 边界

- 只读审查；不跑安装脚本；不连数据库；不评 U3-C 的 deploy-vault.sh 与 U5-B 的消费方。
- 不需要攻击性内容；关心的是**误伤与漏报**。

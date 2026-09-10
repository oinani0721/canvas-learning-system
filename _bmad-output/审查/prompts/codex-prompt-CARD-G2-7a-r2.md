# CARD-G2-7a 独立复核请求（round-2）

## 一 背景与最小读取面

worktree：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy`
分支 `card/u3-deploy`，本卡最终 HEAD **`3c1e3c00`**，前轮送审态 `7aa89c5b`（0B/2H/4M/2L）。

round-1 的两条 HIGH 我都在本机独立复现后才动手（HIGH-1 的复现比你的描述更重：
`(h)②` 目标 data.json 里是 live 的真实 48 字符 key，且我此前的断言只查键集没查值）。
**这一轮的重点：整改本身有没有引入新缺陷、同一问题面还有没有没盖到的入口。**

**请只读以下五处（不要读别的、不要读 live vault、不要跑安装脚本）：**

1. round-1 之后的整改：`git diff 7aa89c5b 3c1e3c00 -- . ':(exclude)_bmad-output'`
2. 本卡全部改动：`git diff 086771d3 3c1e3c00 -- . ':(exclude)_bmad-output'`
3. 逐项裁定表：`_bmad-output/审查/evidence-g27a/manifest-ruling.md`
4. 清单 + 脚本全文：`scripts/vault-install-manifest.json`、`scripts/install-vault.sh`
5. 校验器全文：`scripts/verify_vault_install.py`

## 二 round-1 逐条处置（请核对到位与否、有无引入新问题）

| 你给的级别 | 问题 | 处置 |
|---|---|---|
| HIGH-1 | 整目录 cp -R 带出旧 data.json，生成被短路、摘要过滤看不见 | 生成段开头**先 rm 三个生成位**再生成；`[ ! -e ]` 守卫降级为防御式。重跑 (h)② 实证目标 data.json = 生成的干净值（key 空、backendUrl=生成值）。门：预置 STALE-KEY 的 data.json → 跑生成段 → 必须被清 |
| HIGH-2 | 缺省源仍从 .env ACTIVE_VAULT 解析 | 缺省 `SOURCE=$REPO/canvas-vault`，.env 解析块删除；注释写明理由。门：不传 --source 时块输出必须是 `$REPO/canvas-vault` |
| MEDIUM | generate 摘要过滤隐藏形态错误 | verify() 对 generate 项加「存在但不是普通文件 → unreadable、不记 match」。门：data.json 误建成目录 → unreadable + rc2 |
| MEDIUM | wiki 骨架漏内容排除 | manifest 补 `wiki/concepts/**` + `wiki/canvases/**`（exclude 15→17、items 52），skeleton-excludes 门期望扩为 4 条 |
| MEDIUM | key 自检 `! cmp -s` 把读错误当通过 | 三态：目标无 key ✅ / 两边可读且内容不同 ✅ / 否则（不可读）显式 ❌ 带提示。门：源 key chmod 000 → ❌+「不可读」 |
| MEDIUM | outputs/exam_boards 退让理由漏第三条路 | 裁定表补全三路盘点（含 skeleton+exclude 并存路及其自指噪声代价），维持不加、转卡 |
| LOW×2 | origin 不验内容/区间尾；allowed-extra 成员包含弱化 | origin 门加区间尾越界检查；note `:121`→`:183 附近`；断言恢复精确 `[probe]` |

顺带：H2 使数组区上移到 71-75，`MANIFEST_BLOCK` 同步；「12 项在位都比内容」收窄为
「8 个 copy 项比、4 个 generate 项不比」；UAT 补未证明 #9（optional 是否都被该允许）
与 #10（未裁=0 ⇏ 部署无遗漏）。

## 三 请按重要性排序回答的问题

1. **H1 的修法（先 rm 再生成）有没有新洞**：rm 发生在复制之后、生成之前——这个窗口
   里还有什么路径能把旧值带回来？rm 的三个路径与 manifest 的 generate 集合**恰好一致**吗
   （将来加第四个 generate 件时谁保证 rm 行跟着加）？
2. **H2 的缺省源迁移有没有破坏既有调用方**：哪些现有流程依赖「缺省=活 vault」的旧语义
   （如推送 VAULT-SYNC、既有文档/别名）？`CLS_REPO` 缺省值与本 worktree 的关系？
3. generate 项「不是普通文件 → unreadable」的判定本身用的 `is_file()`——它跟随软链且吞
   OSError，这与你 round-5(U3-A) 指出的谓词家族问题同形。这里是真漏还是可接受？
4. wiki exclude 两条加了之后，「树自洽」与「(h) 两跑」的期望面有没有被静默改变？
5. 钉点迁移（71-75、161 条测试）后还有没有弱化断言或恒真门？
6. 裁定表/UAT 现在还有说得比证据宽的地方吗？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条：一句问题 + `file:line` + 一句复现思路。
无问题的项明说「核对结果：无问题」并说明核对程度。

## 五 边界

只读审查；不跑安装脚本；不连数据库；不评 U3-C/U5-B 的消费方。
不需要攻击性内容；关心**误伤与漏报**。

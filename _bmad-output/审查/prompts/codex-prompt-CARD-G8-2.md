# CARD-G8-2 独立对抗审查（round-1）

你是独立审查者。审查对象是 CARD-G8-2「统一 /lint 骨架 + 首批三检查」在车道
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint` 上的落地。

工作目录 = 上述车道根。**只读审查，不要修改任何文件。**

## 一、被审对象

新增（本卡独占）：
- `backend/scripts/vault_lint.py` —— lint runner + 三检查
- `backend/tests/unit/test_vault_lint.py` —— 本卡门测试
- `_bmad-output/审查/evidence-g82/` —— live 只读取证
- `_bmad-output/验收单/UAT-CARD-G8-2-*.md` —— 验收单

**禁改面（本卡一个字节都不该动，请核实确实没动）**：
`backend/scripts/check_vault_doc_roles.py` / `backend/scripts/vault_doc_roles.yaml` /
`canvas-vault/.claude/scripts/sync_board_concepts.py` / `backend/app/api/v1/endpoints/review_overview.py` /
`backend/app/services/board_manifest_service.py` / `.gitignore`

核实命令：
```
git log --format= --name-only $(git merge-base HEAD worktree-feature-obsidian-hybrid-dev)..HEAD -- \
  backend/scripts/check_vault_doc_roles.py backend/scripts/vault_doc_roles.yaml \
  canvas-vault/.claude/scripts/sync_board_concepts.py \
  backend/app/api/v1/endpoints/review_overview.py backend/app/services/board_manifest_service.py | sort -u
```
期望空。非空即 BLOCKER。

## 二、审查重点（卡文指定，按此优先级）

### 1. orphan 检查的假阴 / 假阳面（最高优先级）

孤儿定义：`节点/` 下的 md **既无**来自 `原白板/` / `检验白板/` / `节点/` 任一正文的 wikilink 入链
（basename 命中），**又无** frontmatter `source_board`。

请对抗性地找出这个定义会**漏判**（假阴：真孤儿被判成有链）或**误判**（假阳：正常节点被判成孤儿）的场景：
- wikilink 的各种形态：`[[x]]` / `[[x|别名]]` / `[[节点/x]]`（子路径）/ `![[x]]`（embed）/
  `[[x#小节]]` / `[[x#^block]]` / `[[x.md]]` / 空 `[[]]` / 跨行
- Unicode：NFC vs NFD 归一（中文/带音标文件名在 macOS 上的实际存储形态）
- 大小写：APFS 大小写不敏感 vs 判定逻辑是否大小写敏感
- **`原白板/*.md` 里 sync_board_concepts.py 写入的 AUTO-GENERATED 哨兵块**——
  如果那段自动生成的成员列表被算作"入链"，检查会不会在真实 vault 上恒绿（= 死门）？
  实现选了哪一边？验收单有没有如实登记这个选择的后果？
- 代码块 / 行内 code / HTML 注释里的 wikilink 算不算
- frontmatter 里的 wikilink（如 `source_board: "[[原白板/X]]"`）算不算正文入链

⛔ 关键判据：**实现声称覆盖的形态，是否每一类都有对应的测试用例真的验证过？**
验收单的「不比什么」表里有没有把不判定的形态如实列出（而不是含糊带过）？
有没有出现「我做了 X」被写成「X 已被证明」的措辞？

### 2. freshness 同源锁是否**真的**绑定在 oracle 上

本卡的 freshness 口径是**复制**自 `backend/app/api/v1/endpoints/review_overview.py:845-860`
（`_vault_entry` 的内联 stale 判定；该文件被 W6 车道独占，不可 import 改造）。
同源锁 = 测试构造 vault fixture，**调用真实的 `_vault_entry`** 作为 oracle，
断言 vault_lint 的判定与它逐项相等。

请核实：
- 同源锁用例是不是**真的 import 并调用了** `_vault_entry`，而不是复刻了一份判定逻辑再跟自己比
  （拿自己的副本当 oracle = 测试自己的副本，什么都没证明）
- ⛔ **最关键**：那些 fixture 投影是否真的走到了 stale/ok 分支？
  `_vault_entry` 会先调 `_summarize()`（严格 v3 形状门禁），任何形状不符 → `status="corrupt"` ——
  **根本走不到 stale 判定**。如果 fixture 投影形状不合法，两边都返回 corrupt、测试全绿，
  而 stale 逻辑一行都没被验证。请**实际检查每组同源锁 fixture 的 `_vault_entry` 返回值**，
  确认其中确实有 status 为 `ok` 和 `stale` 的组，不是清一色 corrupt。
- 边界覆盖：无时区 / 纯日期 / Z 后缀 / 跨午夜（UTC 昨日 23:00 = 上海今日 07:00）/
  空值 / 非字符串 / astimezone 溢出极值 —— 是否 ≥6 组且互不重复
- 时区：判定用的是 Asia/Shanghai 还是进程本地时区？（MEMORY 有一条真实缺陷：容器 TZ 为空
  导致产出"昨天"的日期）`--now` 注入的语义是否与生产 today 口径一致？

### 3. 零写侧（本卡铁律）

卡文要求「全程只读零写（含 `__pycache__`）」，live vault 与 Neo4j 7691 只读。请核实：
- `vault_lint.py` 源码有无任何写原语（`.write_text` / `.write_bytes` / `.mkdir` / `.unlink` /
  `.touch` / `shutil.*` / `os.remove` / `os.rename` / `open(..., "w"/"a"/"x")`）
- import 链的写副作用：
  - 若 import 了 `check_vault_doc_roles` 并调 `scan(with_probe=True)`，会经 `app.services` 触发
    `jieba.initialize()` 写系统临时缓存 —— 实现是否默认走 `with_probe=False`？
    若走了 probe 档，「零写」声明是否过宽？
  - 若 import 了 live vault 内的 `canvas-vault/.claude/scripts/sync_board_concepts.py`，
    在没有 `PYTHONDONTWRITEBYTECODE=1` 时会往 **live vault 里**写 `__pycache__`。
    实现选了 import 还是复制？这个选择的风险在验收单里登记了吗？
- 有无连 Neo4j / 起 FastAPI lifespan 的 import 路径

### 4. 退出码语义不自相矛盾

卡文规定：`0 = 全 ok` / `2 = 有 warn 无 fail` / `1 = 有 fail`。请核实：
- 三个检查各自在什么情况判 ok / warn / fail —— 规则是否在 `--help` 和报告里写清楚？
- **卡文没覆盖的洞**：配置/环境错误（vault 路径不存在、台账 yaml SHA 不符、
  `check_vault_doc_roles` 抛 `ConfigError`）该退什么码？
  注意 `check_vault_doc_roles.py` 自己用 **2 = ConfigError**，与本卡的 **2 = warn** 直接冲突。
  实现怎么处理的？会不会让"台账坏了"和"有 warn"变得不可区分（那是把故障伪装成正常信号）？
  验收单有没有把这个洞显式登记为待裁决点？
- `--only <name>` 时的退出码语义是否一致（只跑一个检查时的聚合规则）
- `--json` 与文本输出是否**同源**（同一份数据结构渲染两次），还是两条各自遍历的逻辑
  （后者意味着「同源门」测不出分叉）

### 5. 门的强度（别信"全绿"）

- 每道门「证明什么、不证明什么」是否写清？有没有**恒真断言**
  （否定式断言在被测逻辑被删掉后仍然通过）？
- 变异测试（卡文要求 ≥4 个：去掉 source_board 豁免 / 放宽 stale 为恒 fresh /
  退出码恒 0 / JSON 与文本分叉）—— 每个变异是否**指定了它该杀死哪一道门**，
  且那道门确实变红（不是"某处有失败"）？变异脚本是否串行、还原后逐字节比对？
- 有没有哪个检查在真实 live vault 上**恒空 / 恒绿**（= 死门）而未被登记？
  特别是 `回顾-*.md 缺 type: recap` 这条子检查 —— live 上所有回顾文件可能都有 `type: recap`，
  那么它在 live 上恒绿，是否有 fixture 反例证明它不是死门？

## 三、输出格式

按严重度分级列出发现，每条给出：
- 级别：BLOCKER / HIGH / MEDIUM / LOW
- 位置：`file:line`
- 问题陈述：**具体的失败场景**（什么输入 → 什么错误输出），不要泛泛的"建议改进"
- 依据：你实际跑过的命令与输出，或确切的代码引用

如果你认为某条实现其实是对的、而验收单的**声明**过宽（说得比证明的多），
请单独指出——这类"声明比证据宽"是本项目反复出现的失败模式，与代码缺陷同等重要。

最后一行必须是：`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`。

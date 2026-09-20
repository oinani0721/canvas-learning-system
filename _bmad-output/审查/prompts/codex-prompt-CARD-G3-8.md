# CARD-G3-8 独立复核请求（BATCH-2026-09-18-第十五批 · 车道 card-p4-fsrs）

你是独立复核者。只读审查，不要修改任何文件，不要连接任何数据库或网络服务。

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs`

---

## ① 最小读取面（只读这些，不要泛读全仓）

1. 本卡改动全文（两个新文件）：
   `git --no-pager diff --no-color 49e426263caa0356e8c947c701e206efb11ae97f 71d6ad2747857e592cad127803ece7b972d88b3e -- . ':(exclude)_bmad-output'`
2. census 文档：`_bmad-output/审查/evidence-g38/next_review-census.md`
3. 闸的参照实现（只读，不要评价它们本身）：
   - `backend/scripts/migrate_fsrs_card_states_vault_key_g35.py` 第 50–160 行（路径面闸范式）
   - `backend/scripts/migrate_write_identity_g23.py` 第 52–118 行（端口解析闸 + store identity 指纹闸）
4. 目标侧写/读的生产代码（只读事实，不要评价它们的处置）：
   - `backend/app/clients/neo4j_client.py` 第 985–1040 行（`LEARNED` 的 MERGE 身份键与 `P1D` 写）
   - `backend/app/clients/neo4j_client.py` 第 716–746 行（JSON 镜像的行匹配键与写法）
   - `backend/app/clients/neo4j_client.py` 第 790–835 行（JSON 镜像读方与其时区比较）
5. 真相源与比较口径：
   - `backend/app/services/review_service.py` 第 160–170 行（整秒归一）与第 223–330 行（governed 四态、frontmatter 正则）
   - `docs/fsrs-truth-source-d0-revision.md` 第 10–49 行（T1/T5）

---

## ② 作者自述（请独立核对，不要默认接受）

我声称本卡的实现满足下列性质。请逐条独立验证，**不要以我的措辞为准**：

- **A1** 迁移器永不写 frontmatter，也永不写 `backend/data/fsrs_card_states.json`（后者只读、只报分歧计数）。
- **A2** 现网库闸按 `urlsplit` **解析后的整数端口**判定，不是字符串包含判定；`bolt://h:07691` 与 `bolt://h:7691` 结论相同；省略端口的 URI 被拒。
- **A3** `--apply` 第二次执行时 `set + backfill == 0`（幂等）。
- **A4** 身份映射失败在**两个方向**都显形为 `unmatched`（`no_target` / `no_frontmatter`），不静默跳过。
- **A5** `--dry-run` 除 `--out` 之外零写入（判据是跑前/跑后整棵 tmp 树的 sha256 映射逐键相等，不是文件计数）。
- **A6** 迁移器零 `app` 导入，纯标准库（`neo4j` 仅在给了 `--neo4j-uri` 时函数内延迟导入）。
- **A7** `ungoverned`（无 `fsrs_due`）的节点既不动目标，也不反向回填 frontmatter。
- **A8** JSON 目标的写入按**行位置**而非三元组键，因此重复的 `(user_id, concept_name, group_id)` 行被逐行处置。

---

## ③ 请按重要性排序回答的问题

- **Q0（最高）** 身份映射：`--vault-dir` 下的文件 stem ↔ `Concept.name` + `group_id`。在真实数据上，是否存在一条路径会把 A vault 的 `fsrs_due` 写到 B vault 的 `LEARNED` 边上？读侧与写侧的 Cypher 是否对 `c`、`r` 两个 alias 都做了 group 过滤（R1 全覆盖 / W5 scoped update）？`--group-id` 的形态校验是否是唯一防线，够不够？
- **Q1** 整秒归一比较：除了「同秒不同微秒」之外，它是否还会把**真分歧**吞成 `noop`？特别是时区处理——naive 输入、Neo4j 纳秒精度、`--json-naive-tz` 的两种口径、跨夏令时边界的 naive 本地值。
- **Q2** pre-image 落盘失败时，`--apply` 是否**真的不开写**？`--rollback` 是否做了读回校验？备份被改动过时的处置是否正确（rc 语义 1 与 3 是否分得开）？
- **Q3** 闸对下列输入分别给什么结论，是否都正确：`neo4j://host:7692`、`bolt+s://host:7692`、`bolt://host`（省略端口）、`bolt://host:07691`、`http://host:7692`、以及路径面的 live vault 子树 / 受保护 inode 的硬链接 / `st_nlink > 1` 的普通文件。
- **Q4** 7692 真库门的清理查询是否只删它自己的 `g38gate_` 前缀身份？有没有可能删到共享容器里别人的数据？（本次执行环境容器未启动，该门为 SKIPPED，请按代码判断。）
- **Q5** 负控输入（把闸改成恒放行 / 把 `noop` 比较改成恒假）是否真的会让**指定的那几条**用例变红，还是会红在门未覆盖的路径上？有没有哪条门实际上绿在了更早的一道判据上？

---

## ④ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级，每条给：

- 一句话结论
- `file:line`
- 一句复现思路（描述哪种输入会让它出问题即可）

措辞请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这组词，不要用其他等价说法。

---

## ⑤ 审查边界（请不要越过）

- 只读。不要修改文件，不要连接数据库、不要发起网络请求。
- **不要评价** `neo4j_client.py:1034` / `fallback_sync_service.py:774` 的 `P1D` 写方、以及 `learning_context_service.py:96-102` 派生式**该如何处置** —— 它们属别的车道地盘，本卡只做 census 登记，明确不改。
- **不要评价** 是否应该对现网执行 `--apply` —— live 执行需用户当次授权，本批只做 dry-run。
- **不要评价** `backend/app/**` 里任何一行的写法 —— 本卡对这 14 个文件零改动，只读它们做 census。
- census 文档 `next_review-census.md` 的事实陈述属审查面（请核对它与代码是否一致）；台账与验收单不属审查面。

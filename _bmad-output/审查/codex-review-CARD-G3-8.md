> 批次: BATCH-2026-09-18-第十五批 · 车道 P4 · 卡 CARD-G3-8 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-8.md)"`
> 审查绑定: `71d6ad2747857e592cad127803ece7b972d88b3e`（本卡第 1 个 commit；审后按本轮意见改代码，故已失绑，由 round-2 绑最终 HEAD）
> 会话头自证（抄 `.stderr` 的第 2 / 5 / 9 行；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

**结论：存在 BLOCKER，A1、A4 不能按作者的完整表述接受。** 复核绑定 `71d6ad2747857e592cad127803ece7b972d88b3e`；两个新增文件与该提交一致。仅进行了源码检查和纯函数内存验证，未修改文件、运行原测试或连接数据库、网络。

以下行号分别指 [迁移器](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/scripts/migrate_next_review_g38.py)、[测试文件](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/unit/test_migrate_next_review_g38.py) 和 [census](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/_bmad-output/审查/evidence-g38/next_review-census.md)。

1. **BLOCKER｜Q0：合法的错误 group 能把 A vault 的 due 写入 B，形态校验不足以证明来源归属。**  
   `migrate_next_review_g38.py:879、887、893、1315、1331`。读、写、清空查询确实同时过滤 `c`、`r`，但都信任调用方给出的同一个 group；`--from-report` 也只比 group。  
   **未被拦下的输入：** A 目录含 `shared.md`，参数给 `--group-id vault__B`，B 有同名关系；内存验证得到 B 的 `action=set`，值来自 A。这里证明可达路径，不代表已确认现网发生过。

2. **HIGH｜A1：输出口没有保护全部只读输入，能够覆盖 frontmatter。**  
   `migrate_next_review_g38.py:1356、790、977、984`。`--out` 只排除 JSON 目标和显式 card-states 输入，没有排除扫描的节点文件；备份写口也缺少这层检查。  
   **未被拦下的输入：** `--dry-run --out /tmp/vault-copy/节点/A.md` 会覆盖源节点；`mirror.json.bak` 若为指向源节点或 card-states 副本的符号链接，备份复制也会覆盖它。

3. **HIGH｜Q2：Neo4j 已写入后仍可返回 rc=1，并报告 `written=0`，没有恢复原值。**  
   `migrate_next_review_g38.py:1098、1108、1113、1170、1229、1258`。写入或回滚期间的异常也没有统一转换为 rc=3。  
   **门未覆盖的路径：** 第一条写成功，后续条目回执不符，会返回 1；JSON 回滚复制后 SHA 读取抛异常，或 Neo4j 恢复部分行后查询抛异常，也可能异常退出为 1。

4. **HIGH｜Q2：rollback 未绑定原目标，可以把 A 的备份恢复到 B 并通过校验。**  
   `migrate_next_review_g38.py:995、1078、1188、1224、1240`。记录的 `target_path`、`target_uri/database` 没有参与目标核验。  
   **未被拦下的输入：** A 的 pre-image 配同组的另一份 `--json-file B`，会用 A 的完整镜像覆盖 B；另一个非现网 Neo4j 库具有相同组和身份时同理。

5. **HIGH｜Q3：读取连接没有 store identity 闸，非现网端口不能证明不会连接现网库。**  
   `migrate_next_review_g38.py:890、893、1067、1350`。dry-run 只检查 URI；apply 也先 `_gather`，随后才检查数据库身份。  
   **未被拦下的输入：** `7692` 实际转发到已知现网库，或路由种子指向它；读取已经发生，apply 的身份拒绝在其后。

6. **HIGH｜Q3：真库测试自己的端口闸仍是字符串判定，能够先连接、写入，再被迁移器拒绝。**  
   `test_migrate_next_review_g38.py:770、781、812、836`。  
   **未被拦下的输入：** `NEO4J_TEST_URI=bolt://host:07691` 或 `bolt://host`，在可达且认证成功时先执行 `MERGE/SET`，之后才进入迁移器的正确闸。

7. **HIGH｜Q4：清理限制了节点前缀，却没有限制本次身份和 group，能删除共享数据。**  
   `test_migrate_next_review_g38.py:890、893`。`DETACH DELETE` 还会删除这些节点连接的全部关系。  
   **对照输入：** 另一组存在 `Concept {name:'g38gate_concept', group_id:'vault__other'}`，也会被删除；非前缀节点本身不会被删除，但其相关边可能被删除。

8. **MEDIUM｜Q1：夏令时重复的 naive 本地时间可能把真实一小时分歧判为 noop。**  
   `migrate_next_review_g38.py:475、477、657`。  
   **未被拦下的输入：** 洛杉矶时区下，目标 `2026-11-01T01:30:00`、真相源 `08:30:00Z` 得到 `noop`；若目标来自第二次 01:30，实际应为 `09:30Z`。春季不存在的本地时间也被自动归一，没有判为 ambiguous。

9. **MEDIUM｜Q3：pre-image 路径被拒绝之前，可能已经向 live vault 创建目录。**  
   `migrate_next_review_g38.py:945、949`。  
   **未被拦下的输入：** 有可写行，且 `--backup-dir` 指向 live vault 下尚不存在的子目录；先 `mkdir`，后检查路径。

10. **MEDIUM｜A4：malformed 或不可读的 governed 节点缺目标时，没有计入 unmatched。**  
    `migrate_next_review_g38.py:625、636、638`；`next_review-census.md:194`。  
    **对照输入：** `fsrs_due: invalid` 且目标为空，结果为 `malformed_fsrs_due=1、unmatched=0`。节点问题有显形，但身份缺失没有按 census 所述计数。

11. **MEDIUM｜Q5：硬链接用例不能独立证明普通多硬链接判据。**  
    `test_migrate_next_review_g38.py:497`；`migrate_next_review_g38.py:194、218`。当前用例先被受保护 inode 判据拦下。  
    **负控输入：** 分别移除 inode 判据或 `st_nlink > 1` 判据，该用例仍能通过；普通目录内、不属于受保护 inode 的多硬链接文件是门未覆盖的路径。

其余逐项核对结果：

| 项目 | 结论 |
|---|---|
| A1 | 不成立，见第 2 条。固定主仓 card-states 路径有保护，但全部只读输入没有获得同等保护。 |
| A2 | 成立：迁移器用 `urlsplit().port` 的整数值；测试自身另有第 6 条问题。 |
| A3 | 成功完成且输入不变时成立，第二次分类为 `set + backfill = 0`。本轮未执行写入测试。 |
| A4 | 部分成立：正常有效 due 的两个方向都有 unmatched；第 10 条有例外。 |
| A5 | 测试确实比较整棵 tmp 文件树的路径→SHA256 映射，非文件计数；本轮未运行该测试。 |
| A6 | 成立：无 `app` 导入，只有标准库及函数内延迟导入的 `neo4j`。 |
| A7 | 分类和业务写入路径成立：ungoverned 提前结束，不进入写入集合；输出别名问题仍见第 2 条。 |
| A8 | 成立：按 `target_index` 写入；重复三元组中的 set/noop 行有分别覆盖的用例。 |

Q1 的其他口径正常：aware 值按 UTC 整秒比较；纳秒同秒归 noop、跨秒归 set；Neo4j naive 判 ambiguous；JSON `utc` 与 `local` 开关生效，普通冬夏日期使用对应日期的本地偏移。**Neo4j 回滚校验也截整秒**（`:1133、1263`），因此它不能证明精确恢复 pre-image 的小数秒。

Q2 的常规 pre-image 落盘失败确实发生在目标写入之前并返回 1，但 JSON 备份已先生成。JSON rollback 会先核对备份 SHA：备份被改动时返回 1、保持目标现状；复制失败或读回 SHA 不同返回 3。这里“保持现状”不等于“已恢复迁移前状态”。

Q3 的迁移器第一道闸结果如下，不能将其等同于最终数据库身份确认：

| 输入 | 结果 |
|---|---|
| `neo4j://host:7692`、`bolt+s://host:7692` | 放行 URI 闸 |
| `bolt://host` | 拒绝：无显式端口 |
| `bolt://host:07691` | 拒绝：解析为 7691 |
| `http://host:7692` | 拒绝：scheme 不允许 |
| live vault 文件子树、受保护 inode 硬链接、普通 `st_nlink > 1` 文件 | 均拒绝 |

Q5 指定的两组负控确实对应预期判据：闸恒放行会使 live 子树、硬链接、URI 用例分别在测试 `:493、511、533` 变红；noop 恒假会使分类计数、行判定和幂等断言在 `:254、276、330` 变红。后者的分类变化已做纯内存验证；本轮没有运行 pytest，也没有运行真库门。

census 在允许核对的生产片段中，身份键、`P1D` 写入及 JSON 时区比较后果基本一致；其 unmatched 表述有第 10 条例外。**14 文件／63 行的全量统计及 live 数据陈述超出指定读取面，本轮未独立复验。**

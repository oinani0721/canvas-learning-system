> 批次: BATCH-2026-09-18-第十五批 · 车道 P4 · 卡 CARD-G3-8 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-8-r2.md)"`
> 审查绑定: `f9e8e3e89659f9f916ecc66a9d6e753f8d280e52`（本卡第 2 个 commit；审后按本轮意见改代码，故已失绑，由 round-3 绑最终 HEAD）
> 会话头自证（抄 `.stderr` 的第 2 / 5 / 9 行；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

本轮仍有 **BLOCKER / HIGH**，不能认定整改全部成立。审查绑定 `f9e8e3e8`；仅做静态审查及纯内存计算，未修改文件、运行测试、连接数据库或网络。以下跨 vault 输入证明代码存在路径，**不代表已确认真实库存在对应数据**。

1. **BLOCKER — vault 绑定仍允许把 A 的 due 写入另一个合法 vault。**  
   位置：[migrate_next_review_g38.py:352](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/scripts/migrate_next_review_g38.py:352)，关联 `:124`。  
   未被拦下的输入：A 自报 `vault_id=alpha`，B 自报 `vault_id=alpha__beta`，传入 A 的目录与 `--group-id vault__alpha__beta`；绑定闸将 B 根组当作 A 二级组放行，无需打开逃生门。

2. **HIGH — Neo4j 自动恢复取错旧值字段，会清空原值后返回 rc=1。**  
   位置：[migrate_next_review_g38.py:1325](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/scripts/migrate_next_review_g38.py:1325)，关联 `:698/:1245/:1252/:1315`。  
   对照输入：第一行原有日期且写成功，第二行失败；`written` 中保存的是 `target_next_review`，恢复函数却读取 `old_next_review`，于是执行 `REMOVE`，清空读回通过后仍称“迁移前可信状态”。

3. **HIGH — 已提交但回执失败的当前行不在恢复集合中，仍可能返回 rc=1。**  
   位置：[migrate_next_review_g38.py:1308](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/scripts/migrate_next_review_g38.py:1308)，关联 `:1312/:1315/:1325`。  
   对照输入：第一行已经提交，获取回执时连接中断；程序在 `written.append()` 前退出，对空集合恢复后返回 1，无法证明该行未改动。

4. **HIGH — `--out` 仍能覆盖 vault 通过软链读取的 frontmatter，A1 不成立。**  
   位置：[migrate_next_review_g38.py:1618](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/scripts/migrate_next_review_g38.py:1618)，关联 `:1098/:385/:921`。  
   未被拦下的输入：`vault/节点/A.md` 指向 vault 外的普通文件 `/tmp/A.md`，同时指定 `--out /tmp/A.md`；输出闸尚未纳入扫描到的节点身份，报告随后覆盖真相源。外部软链配置文件也有相同问题。

5. **HIGH — 真库测试仍先写库、后检查 store identity。**  
   位置：[test_migrate_next_review_g38.py:984](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/unit/test_migrate_next_review_g38.py:984)，关联 `:1016/:1040`。  
   未被拦下的输入：7692 转发到已知现网库；探针只验端口与可达性，测试先 `MERGE/SET`，直到调用迁移器才核身份，最后还执行清理。这仍是身份闸门未覆盖的路径。

6. **MEDIUM — 已存在的正常备份目录被拒，且幂等负控提前红在这里。**  
   位置：[migrate_next_review_g38.py:1114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/scripts/migrate_next_review_g38.py:1114)，关联 `:217`；[test_migrate_next_review_g38.py:345](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/unit/test_migrate_next_review_g38.py:345)。  
   对照输入：已有 `--backup-dir` 且存在可写行，目录被“不是普通文件”拒绝。`noop` 比较恒假的负控输入因此先使第二次调用的 `rc == 0` 断言变红，**没有抵达 `:347` 的幂等计数断言**。

7. **MEDIUM — 回滚的“精确时刻”比较仍吞掉纳秒差异。**  
   位置：[migrate_next_review_g38.py:1348](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/scripts/migrate_next_review_g38.py:1348)，关联 `:549`。  
   负控输入：原值 `.123456999Z`、读回 `.123456001Z`；二者先截至六位小数，纯内存验证 `_same_instant_exact()` 返回 `True`。

8. **MEDIUM — `--out` 可以覆盖本次时间戳备份，使自动 rollback 失去有效依据。**  
   位置：[migrate_next_review_g38.py:1407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/scripts/migrate_next_review_g38.py:1407)，关联 `:1142/:1148/:1617`。  
   未被拦下的输入：`--out=<target>.bak.<本次时间戳>`；apply 成功后报告覆盖 stamped 备份，rollback 随后因 SHA 不符拒绝。simple 备份仍在，但现有回滚路径不会选它。

9. **MEDIUM — 真库清理已收窄，但固定身份不能证明属于本次运行。**  
   位置：[test_migrate_next_review_g38.py:1005](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/unit/test_migrate_next_review_g38.py:1005)，关联 `:1097`。  
   对照输入：共享库已有同一 `g38gate_user / g38gate_concept / vault__g38gate`，或两次测试并行；测试复用并改写该边，最终删除它。其他组同名 Concept 和仍有关系的节点不会被这组清理删除。

10. **LOW — DST 对照用例依赖启动时区。**  
    位置：[test_migrate_next_review_g38.py:934](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs/backend/tests/unit/test_migrate_next_review_g38.py:934)，关联 `:151/:186/:940`。  
    对照输入：从 UTC 单独运行该用例；fixture 先按 UTC 生成 naive 值，随后切到洛杉矶时区，却仍要求原来的 `noop/set` 计数。

其余问题的核对结果：

- **Q0：** 读、写、清除 Cypher 均对 `c`、`r` 使用 `group_id = $gid`（脚本 `:641/:649/:656`）。形态校验已不是唯一防线，但新增绑定仍有第 1 条问题。两个逃生门默认关闭，未发现正常调用自动打开；显式开启也不会放过已知组名不匹配或已确认的现网身份。
- **Q1：** 明确时区的值先转 UTC 再截整秒，未发现额外吞掉跨秒分歧。Neo4j naive 判 `ambiguous`；JSON `utc` 赋 UTC，`local` 使用**迁移进程时区**，需以它与原写方时区一致为前提。新增 DST 判据能识别洛杉矶的重复／不存在时间；纳秒问题在回滚验收。
- **Q2：** pre-image 写入失败后，目标写入确实不会开始，但 JSON 双备份可能已经写入。显式 JSON rollback 会先核备份 SHA，再复制并读回核验；备份被改动返回 1、目标保持当前状态，复制或读回失败返回 3。Neo4j 的 rc=1 保证仍被第 2、3 条破坏。
- **Q5：** “闸恒放行”的九条指定用例按代码路径会红；新增普通多硬链接用例确实排除了更早的受保护 inode 判据，live `--backup-dir` 用例也确实抵达指定闸。按三元组写的负控输入会被重复行用例识别。**9／10／恰好 1 的实测数量未在本轮重跑确认。**

Q3 的实际判定如下；前两项只是端口闸放行，迁移器仍需检查 store identity：

| 输入 | 判定 |
|---|---|
| `neo4j://host:7692` | 放行端口闸 |
| `bolt+s://host:7692` | 放行端口闸 |
| `bolt://host` | 拒绝：无显式端口 |
| `bolt://host:07691` | 拒绝：整数端口为 7691 |
| `http://host:7692` | 拒绝：scheme |
| live vault 子树 | 拒绝 |
| 受保护 inode 硬链接 | 拒绝 |
| 普通 `st_nlink > 1` 文件 | 拒绝 |

A1–A8 的逐项结论：

| 声称 | 独立核对 |
|---|---|
| A1 | **不成立**：第 4 条可覆盖 frontmatter；card-states 统计函数本身只读 |
| A2 | 成立：使用解析后的整数端口 |
| A3 | 不变输入、首次成功后的正常路径成立；负控证据受第 6 条影响 |
| A4 | 按修订口径成立：有效 due 两向 `unmatched`；malformed 用 `target_missing` 另行显形 |
| A5 | 普通 fixture 的 SHA 映射判据正确；第 4 条软链输入仍可改变非 `--out` 名下的源文件 |
| A6 | 成立：零 `app` 导入，Neo4j 驱动函数内延迟导入 |
| A7 | 正常迁移分类成立：`ungoverned` 不进入写入集合 |
| A8 | 成立：JSON 按 `target_index` 写入并读回 |

census 在允许读取的片段中，身份键、固定一天写法及 naive/aware 后果基本吻合；`now`、`except` 的行锚分别应为 `794`、`834`。其“14 文件／63 行”、live 唯一节点及 vault 脚本零写者涉及读取面之外，未在本轮独立重查。

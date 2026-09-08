你是独立代码审查者，这是同一张卡的第四轮（预计最后一轮）。仓库根目录：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance
（只读；不要连数据库，不要执行测试。）

## 〇 沿用第三轮的 A/B 分类

- **A 类**：已登记移交给 `CARD-G2-9-F2` 的未闭合面本身（前缀重叠；以及本卡分页收口
  扩大了它的可达面）。请**不要**把「缺陷仍在」重复报为 HIGH——那是已知且故意保留的。
  请评估**处置质量**：锁够不够、声称有没有宽于证据、给裁定者的信息够不够。
- **B 类**：除此之外的一切。**结论必须单独给出一行：B 类 BLOCKER = N，B 类 HIGH = M。**

第三轮你给出「B 类 BLOCKER = 0，B 类 HIGH = 0」以及 A 类四条。本轮请核对那四条的处置，
并检查本轮改动有没有引入新的 B 类问题。

## 一 背景 + 最小读取面

本轮 HEAD `b80c5f25`；上一轮绑 `0ec1f0c3`。

**本轮改动（两个文件）**：
1. `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`
   - 门⑤ 族重构：`overlap_envs` 改为 **module-scope fixture**，前提门与缺陷锁共用同一实例
   - 缺陷锁拆成两条路径：`..._by_cache_tables`（启动自愈）与
     `..._by_drop_vault_tables`（`DELETE /index` → `drop_vault_tables`），各参数化两形态
   - xfail `reason` 改为显式列出 XPASS 的**两种**成因
2. `backend/lib/agentic_rag/clients/lancedb_client.py` — 本轮**无**代码改动
   （上一轮的 docstring 变更仍在）

**最小读取面**：
- `git diff 0ec1f0c3 b80c5f25 -- . ':(exclude)_bmad-output'`（本轮增量）
- `git diff da690bf8 b80c5f25 -- . ':(exclude)_bmad-output'`（整卡全量）
- `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` 全文
- `backend/lib/agentic_rag/clients/lancedb_client.py` 的 `:830-905`、`:1000-1060`、`:3700-3760`
- 前三轮存档 `codex-review-CARD-G2-9-F1-r1.md` / `-r2.md` / `-r3.md`
- `_bmad-output/审查/evidence-g29f1/` 下：
  `g29f1-r4final-negctl-*.txt`（**七段**负控，含变异体逐行 diff）、
  `a2-dropvault-path-*.txt`（A-2 的实测：用**健康**表）、
  `connect-tmp-only-ast-r4-*.txt`（路径溯源判据 v5 + 逐项承重验伪锚）、
  `forbidden-zones-check-*.txt`（禁改区 AST 逐字节比对）、
  `uat-citation-integrity-*.txt`（验收单引用完整性）
- `_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md` 全文
- `_bmad-output/审查/CARD-G2-9-F1-裁定请求.md`（给做合并裁定的人的一页版）

## 二 对第三轮四条的处置

| 你的条目 | 处置 |
|---|---|
| A-1 缺陷锁自己的建库失败仍被误认成「缺陷仍在」 | 改用 **module-scope fixture** 共用同一实例。⚠️ 先证伪了一个想当然的修法：把夹具搬进 fixture **并不能**让 setup 失败变成 ERROR（实测 xfail 照样吞）；真正起作用的是「不带 xfail 的前提门也用同一个 fixture」。缺陷锁内只剩「跑操作 + 用 fixture 句柄枚举 + 断言」，不再自己 connect |
| A-1b「XPASS 不能单独解释为 F2 已修好」 | xfail `reason` 现显式列出两种成因及辨别特征 |
| A-2 漏记显式删索引路径 | 复核成立（实测：用**健康**重叠表，改前 `list_vault_tables('a')`=10 不含它、改后=11 含它）。已补缺陷锁 `..._by_drop_vault_tables`，并把「触发条件」从一条四要素改为**两条路径表**（drop 路径不需要 schema 漂移）。选项 B 的代价同步扩大 |
| A-3 收窄未同步 | 修四处，含你指出的中文例子错误（`算法进阶` 连写不触发，要 `算法 进阶`） |
| A-4 证据范围过宽 | **负控 7** 在真实源码上模拟 F2 修好，实测 `8 failed, 4 passed`（4 前提门红 + 4 缺陷锁 XPASS） |
| B-LOW#7 计数承重声称 | 已改：明确写「④b 与 ⑤ 都不承重，真正承重的是 §2.5.6 的 AST 控制流判据」 |

## 三 请回答

1. **A 类**：四条缺陷锁 + 四条前提门 + module-scope fixture，合起来还有没有「夹具坏 / 缺陷仍在 /
   缺陷修好」三者中任意两者不可区分的残余路径？
2. **A 类**：`_OVERLAP_XFAIL_REASON` 里列的两种 XPASS 成因，与代码实际行为是否一致？
   有没有第三种成因？
3. **A 类**：两条路径表（cache / drop）的触发条件描述与代码是否一致？给裁定者的两个选项及
   代价是否完整、准确？
4. **B 类**：module-scope fixture 让四条缺陷锁**共享**同一批库。`_cache_tables` 与
   `drop_vault_tables` 会修改库 —— 用例间会不会互相污染而使某条门失效？
5. **B 类**：整卡（`da690bf8` → `b80c5f25`）范围内，前三轮都没提到的问题。
6. **B 类**：七段负控里，有没有哪段的变异 diff 与其声称拆的那一层不符？

## 四 输出格式

逐条：`[A|B] [BLOCKER|HIGH|MEDIUM|LOW]` + `file:line` + 一句话触发条件。
没有问题的维度明确写「未发现问题」。**最后单独一行：B 类 BLOCKER = N，B 类 HIGH = M。**

## 五 边界

- 只读。不要改文件、跑测试或连数据库、网络。
- 不评 `_check_and_fix_dimension_mismatch` 的 drop 条件设计、`list_vault_tables:845` 的裸表口径
  （均为既有裁定）、完整 canary 的端到端运行（已登记移交）、前缀重叠的修法设计（属下一张卡）。

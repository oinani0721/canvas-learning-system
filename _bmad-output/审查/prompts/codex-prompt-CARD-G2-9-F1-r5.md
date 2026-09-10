你是独立代码审查者。这是同一张卡的**第五轮，也是流程规定的最后一轮**
（规则：轮次上限 5；第 5 轮若仍有 B 类 HIGH，本卡停下交人工裁定）。
仓库根目录：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance
（只读；不要连数据库，不要执行测试。）

## 〇 沿用 A/B 分类

- **A 类**：已登记移交给 `CARD-G2-9-F2` 的未闭合面本身（前缀重叠；本卡分页收口扩大了它的
  可达面）。**不要**把「缺陷仍在」重复报为 HIGH；请评估**处置质量**。
- **B 类**：其余一切。**结论必须单独给出一行：B 类 BLOCKER = N，B 类 HIGH = M。**

## 一 背景 + 最小读取面

本轮 HEAD `0db66c20`；上一轮绑 `b80c5f25`。你在第三、四轮已连续给出 B 类 0/0。

**本轮改动（两个文件）**：
1. `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py`
   - **顺序依赖修复**（你的 B-6）：依赖库状态的前提全部搬进 `overlap_envs` fixture；
     前提门只剩「复述 fixture 自检结果 + 一次 `_owns_table`（纯函数）」
   - **每个 (形态 × 消费路径 × 表种) 一个独立库**（原先 drop 侧参数化表名却共用一个库，
     而 `drop_vault_tables` 有副作用 ⇒ 后跑的参数看到先跑的残局；负控 8 抓到）
   - **drop 锁按表种参数化**：补 `a_b_file_fingerprints`（`_cache_tables` 有 `endswith`
     豁免、`drop_vault_tables` 没有 ⇒ 会删掉那个 vault 的变更检测基线）
   - xfail `reason` 改为列出**三种** XPASS 成因（含你 A-2(a) 指出的「删除异常被吞」）
2. `backend/lib/agentic_rag/clients/lancedb_client.py` — 仅 `_owns_table` docstring
   （更新为新的门名，并写明 XPASS 另有两种成因）

**最小读取面**：
- `git diff b80c5f25 0db66c20 -- . ':(exclude)_bmad-output'`（本轮增量）
- `git diff da690bf8 0db66c20 -- . ':(exclude)_bmad-output'`（整卡全量）
- `backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py` 全文
- `backend/lib/agentic_rag/clients/lancedb_client.py` 的 `:830-910`、`:1000-1060`、`:3700-3760`
- 前四轮存档 `codex-review-CARD-G2-9-F1-r1.md` ~ `-r4.md`
- `_bmad-output/审查/evidence-g29f1/` 下：
  `g29f1-r5c-negctl-*.txt`（**八段**负控，含变异体逐行 diff）、
  `g29f1-r5final-negctl-8-*.txt`（负控 8 的 KILLED 记录：`2 failed, 2 xfailed`）、
  `order-dependency-of-shared-fixture-*.txt`（顺序依赖的实测复现）、
  `premise-gate-no-live-query-*.txt`（前提门无实时查询的结构判据）、
  `fingerprint-drift-gap-*.txt`（指纹表在两条路径上的豁免差别）、
  `vault-id-collision-separators-*.txt`（碰撞分隔符实测）、
  `doc-consistency-*.txt`（文档引用：存档 + nodeid + SHA 三项）
- `_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md` 全文
- `_bmad-output/审查/CARD-G2-9-F1-裁定请求.md`

## 二 对第四轮七条的处置

| 你的条目 | 处置 |
|---|---|
| A-1 缺陷锁体内读回失败仍被吞 | ⚠️ **承认不可完全消除**，已**收回声称**（不再说三态无条件可区分），列入「未证明」第 11 条 |
| A-2(a) 第三种 XPASS 成因 | 复核成立，`reason` 已列三种及各自辨别特征 |
| A-2(b) 我对负控 6 的引用过宽 | 复核成立，`reason` 已限定范围；**补负控 8** 覆盖 drop 侧的 `list_vault_tables` 回退 |
| A-3 选项表未同步 + cache 指纹豁免 | 已补：选项 B 加「必须同时覆盖 `list_vault_tables`」与「页外正常表也删不掉」 |
| A-4 旧 nodeid / 避名保证过宽 | 旧 nodeid 在**代码与文档**里清零（`grep -c` = 0）；避名保证改为**实测口径** |
| A-5 一页版页首旧 SHA / 旧数字 | 已同步 |
| B-6 顺序依赖 | 已修（见上）。⚠️ 你说「`-k` 只筛选不重排」是对的，我原先的触发描述过宽，已改 |
| B-7 「④b 承重」残留 | 已改为「④b 与 ⑤ **都不**承重，真正承重的是 AST 控制流判据」 |

## 三 请回答

1. **B 类**：顺序依赖是否**真的**消除了？前提门现在还有没有任何依赖「库当前状态」的读取？
2. **B 类**：每组合独立库之后，八条缺陷锁之间、以及缺陷锁与前提门之间，还有没有残余耦合？
3. **B 类**：drop 锁按表种参数化后，`a_b_file_fingerprints` 那两例的夹具与断言是否成立
   （它是**健康**表，靠的是归属误判而非漂移）？
4. **A 类**：`reason` 里的三种 XPASS 成因是否穷尽？验收单对「不可完全消除的残余」的描述
   是否与代码一致、有没有仍宽于证据之处？
5. **B 类**：整卡（`da690bf8` → `0db66c20`）范围内，前四轮都没提到的问题。
6. **B 类**：八段负控里，有没有哪段的变异 diff 与其声称拆的那一层不符？

## 四 输出格式

逐条：`[A|B] [BLOCKER|HIGH|MEDIUM|LOW]` + `file:line` + 一句话触发条件。
没有问题的维度明确写「未发现问题」。**最后单独一行：B 类 BLOCKER = N，B 类 HIGH = M。**

## 五 边界

- 只读。不要改文件、跑测试或连数据库、网络。
- 不评 `_check_and_fix_dimension_mismatch` 的 drop 条件设计、`list_vault_tables` 的裸表口径
  （均为既有裁定）、完整 canary 的端到端运行（已登记移交）、前缀重叠的修法设计（属下一张卡）。

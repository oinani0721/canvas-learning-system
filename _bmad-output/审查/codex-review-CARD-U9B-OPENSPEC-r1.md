审查绑定 `02f59e5f… → af4793bc…`。**发现 1 个 MEDIUM、2 个 LOW；问题④暂无法独立确认。** 全程只读，未运行测试或 archive，未连接数据库。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

1. **[openspec/specs/concept-identity/spec.md:40](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/openspec/specs/concept-identity/spec.md:40)**：「heals all previously failed writes at once」超出代码保证——成功确实清空标记，但作用域失败的数据没有进入内存，编码失败的数据还会被回滚，后续快照不会补写这些失败的新值。  
   **负控输入**：先提交有效 vault 下、包含 lone surrogate 的 A，触发编码失败并回滚，再成功保存 B；预期所有 dirty marker 清空，但 A 的失败新值仍未落盘，依据 `review_service.py:958–965、979、985–990`。

## LOW

1. **[docs/project-status/fr-exploration/A6-phase0-reference-card.md:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/docs/project-status/fr-exploration/A6-phase0-reference-card.md:107)**：新摘要把失败统称为「归一为 False 并回滚」，遗漏了 `OSError` 必须保留内存 mutation 的区别。  
   **负控输入**：合法 `pending` 在临时文件写入或替换时遇到 `OSError`，应断言 `False` 且新值仍在内存；摘要会引导相反的回滚断言，源码依据为 `review_service.py:993–999`。

2. **[openspec/specs/concept-identity/spec.md:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/openspec/specs/concept-identity/spec.md:20)**：「entire method body」字面不准确，`_missing = object()` 位于锁外；实际成立的是全部相关状态操作都在锁内，pending 的并发保证没有因此缺口。  
   **对照输入**：检查函数语法树，断言所有可执行语句均在 `async with` 内会被 `review_service.py:948` 的赋值打破；措辞应限定为状态读取、mutation、序列化及写盘操作。

## 其余问题核验

### ⓪ 逐项源码对照

以下行号均指 [review_service.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/app/services/review_service.py:920)。

| 契约内容 | 核对结果 |
|---|---|
| 全量快照、指定 JSON 参数 | 符合：`968–976` 整体序列化并替换文档。 |
| `_card_states_payload()` → `to_nested()` 两层嵌套 | 生产容器路径符合：`645–649、512–514`；普通 dict 的测试兼容分支原样返回。 |
| 临时文件、原子替换、目标路径不以写模式打开 | 符合：`974–976`；两步均经 `asyncio.to_thread`。 |
| pending mutation 在锁内 | 符合：`949–965`；“整个方法体”的字面问题见 LOW-2。 |
| 作用域失败在 `try` 前返回，连 `mkdir` 都不执行 | 符合：`958–967`。 |
| `TypeError/ValueError` 回滚，`OSError` 保留内存 | 符合：`981–999`；应按列举的异常类型理解，不能扩展为吞掉任意异常。 |
| 成功清空全部 dirty marker | 符合：`979–980`；不能据此推出补写全部历史失败数据。 |

### ① 调用点与方法的责任

没有把 GET 真相源门锁写成私有方法保证：spec 明确以 **Callers** 为主语；实际门锁在 `review_service.py:2760–2774`。

报告信号还须保留分层含义：评分 service 返回 `card_state_persisted`，`truth_source` 由 API 层提供；不能把这段 spec 解读为要求 service 新增同名返回字段，已有测试在 `test_g3_7_truth_source.py:571–596` 锁定其键集合。

### ② 关键不变式遗漏

未发现正文遗漏关键不变式。锁、`OSError` 保留内存和真相源信号没有各自独立的 Scenario，但正文已有明确要求。

### ③ 范围与 archive 证据

- 排除 `_bmad-output` 后，提交差异恰为指定三文件。
- `backend/app/**`、`openspec/changes/**` 两端 tree 相同；指定历史档案和退役防复活断言所在文件均未改。
- 三文件裸名字独立重算为 **3/1/1 → 0/0/0**；Purpose 字节未变；结构确为 **1 Requirement + 4 个四井号 Scenario**。
- 先红日志的主 spec SHA 前后不变，并记录中止但 `rc=0`；后绿输入 SHA 与 HEAD spec 匹配，归档后 SHA 改变。因此存档确实使用 SHA 判据。**本轮核验了存档与 Git 输入的绑定，没有独立重跑 archive。**

### ④ 第 14 行裁定主语替换

**无法独立确认。** 私有方法当前具有“投影/缓存”的注释，不足以证明历史 `decision.md` 的裁定④也以它为对象；公共方法退役也不等于私有方法继承同一裁定。原决策不在允许读取清单内，故此项既不判 PASS，也不据此认定 DD-13 违规。

### ⑤ 四个 Scenario 的可判定性

四条均能形成具体断言：

1. 两个 vault 加已有磁盘条目，检查完整快照、替换路径及目标写模式。
2. 作用域解析失败，检查 `False`、dirty key 和零文件操作。
3. 有效作用域下分别使用已有键、缺失键触发编码失败，检查恢复旧值或删除新键。
4. 预置非空 dirty 集合，成功保存后检查 `True` 和空集合。

**计数：BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2。**



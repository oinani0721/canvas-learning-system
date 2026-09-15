**结论：round-1 三条整改本身已闭合；本轮发现 2 项 MEDIUM、2 项 LOW。** 已核对目标提交 `1c8d315f`，全程只读、未连接数据库。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

- **M1 — [spec.md:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/openspec/specs/concept-identity/spec.md:34)**：「`try:` 内失败均归一为 `False`」超出代码保证，实际仅捕获 `TypeError`、`ValueError`、`OSError`；A6:108 同样概括过宽。  
  **负控输入**：合法字符串 pending，但事件循环默认 executor 已关闭，`review_service.py:975` 的 `asyncio.to_thread` 会抛出未被捕获的 `RuntimeError`；本轮已用纯 asyncio 复现该异常边界，应限定文档中的异常族。

- **M2 — [spec.md:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/openspec/specs/concept-identity/spec.md:28)**：规范要求记录脏标记，却遗漏“不同 vault 的同名 concept，其脏状态互不影响”，而代码 `review_service.py:903–914` 明确保证这一点。  
  **未被拦下的路径**：把脏标记退回裸 `concept_id`，vault A 的 `c` 写盘失败后，vault B 已持久化的同名 `c` 会被误报未持久化，但现有四个 Scenario 仍可满足。

## LOW

- **L1 — [test_g3_7_truth_source.py:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/regression/test_g3_7_truth_source.py:14)**：裁定④的主语替换不成立，`decision.md:84–90、102` 指向历史公共入口，并未将该裁定转授 `_save_card_states`。  
  **对照输入**：把该行与裁定④标题及 `review_service.py:1666、2774` 两个现存调用点配对，即显出“已退役公共入口”被错绑成“活跃共用落盘方法”；可改用“已退役的公共单卡保存入口”保持裸名字归零。

- **L2 — [A6-phase0-reference-card.md:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/docs/project-status/fr-exploration/A6-phase0-reference-card.md:97)**：「当前内容」仍列旧的第 4 个 Scenario 名，未同步主 spec 新增的“不恢复丢失值”表述。  
  **对照输入**：提取主 spec 四个 Scenario 标题，与 A6 四项逐项比较，只有第 4 项不一致。

## 其余核对结果

- **round-1 闭合**：无条件清的是标记；回滚值不会由后续快照自动恢复；A6 已区分回滚与保留内存；锁范围已避开锁外的 `_missing`。没有发现这些整改反向否定代码已有保证。
- **实现对应成立**：全量嵌套快照、临时文件加替换、目标不直接写入、锁内 mutation、作用域失败在 `mkdir` 前返回，均与代码一致。
- **调用点未混同**：spec 明写 `Callers MUST`，没有把 GET 真相源门锁写成私有方法内部保证。
- **四个 Scenario 均可写成可判定断言**；可判定不代表覆盖完整，缺口见 M2。
- **范围通过**：排除 `_bmad-output` 后恰好三文件；生产目录、`openspec/changes/`、历史档案及地盘外保留项未改；裸名字独立复算为 `3/1/1 → 0/0/0`，测试去掉模块 docstring 后 AST 一致。
- **archive 证据通过输入绑定核对**：先红 SHA 不变，r2 后绿 SHA 改变，后绿输入 SHA 与目标 spec 一致。本轮未重跑 archive，执行结果依据存档，未把 validate 或退出码当鉴别裁判。

**计数：BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 2。**

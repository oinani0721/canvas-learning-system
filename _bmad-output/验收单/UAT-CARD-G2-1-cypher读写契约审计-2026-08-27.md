---
type: uat
title: "UAT · CARD-G2-1 Cypher 读写契约审计（2026-08-27）"
date: 2026-08-27
status: awaiting_user
scope: "BATCH-2026-08-27-第四批 / CARD-G2-1 — 139 处裸 Cypher 审计 + R/W 契约规则 + 7692 真库门测试"
worktree: "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract"
---

# UAT · CARD-G2-1 Cypher 读写契约审计

> [!info]+ 你不需要碰命令行 — 全部技术验证我已代跑（结果见下）
> 这张卡是纯基建卡（审计文档 + 规则文档 + 测试），没有浏览器可见的产品面。
> 你只需要过目下面 **三个关键结论 + 一个待你批的移交事项**。

## 📌 你需要过目的三个结论

1. **防御规则形同虚设被实锤**：根 CLAUDE.md 强制的 `cypher_with_group_filter()` 生产调用 = **0**（全部引用是测试/lint 文案/显式拒用注释）。真库实测还抓到 helper 第二个硬伤：对 MERGE 开头的写查询注入产生**非法 Cypher**（SyntaxError）——写侧防御它从来帮不上忙。
2. **真实防御现状**：139 处裸 Cypher 逐一归类完毕（99 处精分类 + 40 处脚本粗分类）。经 Codex 三轮对抗审查累计压掉 12 处 false-green 后的诚实大盘：**54 合规 / 16 设计跨 vault / 16 条件性 / 6 违规 / 7 非调用**（条件性大户 = 只过滤节点不过滤关系/中间节点的"部分 alias"形态）；**真雷区集中在 `neo4j_client.py`（Memory 系统）**：19 条语句 17 条违规（写身份缺 group 复合键 5、无 scope 删除 2、无 group 读 9、无 scope 更新 1）→ 跨 vault 同名概念会互相劫持归属。读侧全覆盖正例（连关系都过滤）**全库仅 1 处**（`targeting_material_service.py:163`）。
3. **雷已圈住待拆**：两条 `xfail(strict)` 真库测试把写身份缺陷钉在测试里 —— G2-3 修完写路径它们会自动报警（XPASS），届时移除标记翻绿。**本卡按铁律未改任何业务代码**。

## ✍️ 待你批的移交事项

- [ ] **根 CLAUDE.md L40 的"必须用 cypher_with_group_filter()"过时条款**：矛盾已在两份规则文档如实记录，改 CLAUDE.md 本体 = 移交（不在本卡）。**批准后**由后续卡把该条款改为指向 `.claude/rules/cypher-read-contract.md` / `cypher-write-contract.md`。
- [ ] **G2-3 排卡确认**：修 neo4j_client.py 写身份 5 处 + 无 scope 删除 2 处（`fallback_sync_service.py:352/458` 同形同修），翻绿门测试。

## ✅ 技术验证（Claude 已代跑）

| 项 | 结果 | 证据 |
|---|---|---|
| 真库门测试（7692 测试容器，未碰 live 7691） | **16 passed + 2 xfailed** | `cd backend && .venv/bin/pytest tests/integration/test_cypher_contract_gate.py -q` |
| helper 单元回归 | **20 passed** | `tests/unit/test_cypher_helpers.py` |
| 审计覆盖对账 | 99/99 逐 (file,line) 匹配，零缺失/零重复 | 审计文档 §8 |
| 人工抽查 | 6/6 与分类一致（含违规与合规正例） | 审计文档 §8 |
| Codex 独立审查 round-1 | **FAIL**（1 BLOCKER + 2 HIGH + 3 MEDIUM + 2 LOW，全部核实属实） | `_bmad-output/审查/codex-review-CARD-G2-1.md` |
| Codex round-1 findings 整改 | 8/8 完成（5 处 false-green 降 CONDITIONAL、§5 汇总重算 17v/2c/0ok、R3/W2/W5 口径统一、xfail 加 raises 收窄、交接补 #16） | 审计文档 §9 |
| Codex 复审 round-2 | 4 PASS / 4 FAIL（再揪 5 处同型 false-green + edge_client:436 R3 冲突 + 2 MEDIUM + LOW） | `_bmad-output/审查/codex-review-CARD-G2-1-round2.md` |
| round-2 findings 整改 | 6/6 完成（5 处降 CONDITIONAL + edge_client:436 升 VIOLATION + 物理化列/advisory 措辞/标题/#15 论证修正；R1 正例换 targeting_material_service:163） | 审计文档 §9 round-2 记录 |
| Codex 复审 round-3 | 指定项全 PASS，扫尾再出 1 BLOCKER（exam_service_ext:148 边身份键缺 group）+1 MEDIUM+4 LOW | `_bmad-output/审查/codex-review-CARD-G2-1-round3.md` |
| round-3 findings 整改 | 6/6 完成（148 降 CONDITIONAL、交接链计数改 16 并注明三轮构成、4 条 note 修正；读侧全覆盖正例最终只剩 1 处） | 审计文档 §9 round-3 记录 |
| Codex 终审 round-4（收敛确认轮） | **可接收**——5/5 PASS，无新 BLOCKER/HIGH，仅 2 处标点 LOW（已清） | `_bmad-output/审查/codex-review-CARD-G2-1-round4.md` |

## 📄 交付物清单

- 审计清单：`_bmad-output/审查/G2-1-cypher-audit-2026-08-27.md`（§1 方法论 / §2 helper 枚举 / §3-§4 精分类 99 处 / §5 neo4j_client 19 条 / §6 scripts 粗分类 / §7 违规汇总与交接链 / §8 质量对账）
- 契约规则：`.claude/rules/cypher-read-contract.md`（R1-R5）/ `.claude/rules/cypher-write-contract.md`（W1-W5），`.gitignore` 已加 `!.claude/rules/` 豁免入库
- 真库门测试：`backend/tests/integration/test_cypher_contract_gate.py`（语法门 + 双 vault 读隔离门 + 写身份 xfail(strict)×2）

## 📝 批注区

**User：**

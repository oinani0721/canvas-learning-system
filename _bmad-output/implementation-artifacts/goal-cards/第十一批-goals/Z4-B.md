> ⚠️ 本文件是 CARD-REDBASE-R2 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z4-B 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-REDBASE-R2]`。车道：`card-z4-redbase`，**前提 Z4-A 已独立 commit**。微卡 1.5h，默认不送 Codex。X8 已合入主干（`7ba8fc07`），openapi 快照重生成流程可用。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-REDBASE-R2 — 清掉对外契约面残留的 D16 前 group_id 示例（OpenAPI example + docstring 六处）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 红⑥ 修完后测试绿了，但 OpenAPI schema 的 example 仍把已废的 `math54:离散数学` 发给插件/前端消费方——测试与契约说两套话 | — |
| 六处：`backend/app/models/metadata_models.py:52 / :62 / :177 / :292`、`backend/app/api/v1/endpoints/metadata.py:125`、`backend/app/services/subject_resolver.py:48`（开工用 `grep -rn 'math54:离散数学\|math54:线性代数' backend/app` 重取行号） | grep |
| X8 已落地 `scripts/spec-tools/check-openapi-drift.py --write`（唯一合法的快照写法；手改 `backend/openapi.json` 禁止）；lefthook 两条 spec-sync 命令也走 `--write` | X8 |

## 一 完成条件（AND）
- (a) 六处示例统一改为 D16 格式，示例值用中性 `vault:cs_61b:math54:线性代数`（不写本机 `canvas_vault`）。
- (b) 只改字符串字面量与 docstring，零逻辑改动：diff 里不得出现 `if` / `return` / 赋值行变更。
- (c) openapi 快照按 X8 流程 `cd backend && <venv>/python ../scripts/spec-tools/check-openapi-drift.py --write openapi.json` 重生成，且快照 diff 只含这六处 example/description 的文本变化；随后 `--snapshot` → `DRIFT: none`。
- (d) 全仓复扫无残留：裸格式示例归零（Z4-A 已改成 `vault:` 前缀的断言除外）。

## 二 裁判命令
1. `grep -rn 'math54:离散数学\|math54:线性代数' backend/app backend/tests` → 除 Z4-A 已改为 `vault:` 前缀的断言外空输出。
2. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/api/v1/endpoints/test_metadata_subject_mapping.py tests/unit/test_subject_resolver.py tests/contract/test_openapi_snapshot_drift.py` → 全绿（后者 23）。
3. `git diff <Z4-A commit> HEAD -- backend/app | grep -E '^\+' | grep -vE '^\+\+\+' | grep -vE '("|#|\*|例|e\.g)'` → 空（(b) 无非注释/非字面量新增行）。
4. `cd <树>/backend && <venv>/python ../scripts/spec-tools/check-openapi-drift.py --snapshot openapi.json` → `DRIFT: none`；`git diff --stat <Z4-A commit> HEAD -- backend/openapi.json` 只含 example/description 文本。

## 三 禁改与隔离
禁改任何解析/构造逻辑（`build_vault_group_id` / `_make_group_id` / 端点返回值）；禁手改 `backend/openapi.json`（只经 `--write`）；不碰 live vault 与 7691；不改台账；不 push。

## 四 验收单
`…/验收单/UAT-CARD-REDBASE-R2-<日期>.md`：DoD-3 双段；4-B「无变化（接口文档里的示例改成现在的写法）」；「本卡未证明什么」必填（未证明仓外消费方已适配）；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push；跑完说「复核第十一批 Z4」。

# 03 — 断点归属表（CARD-G8-7）

> 列：环节 / 现象 / 证据文件 / 归属切片·卡 / 是否阻断旅程
> 「已知前置断点」= 走查开始前已存在的状态（非本卡引入），登记不修（走查窗口冻结部署 / 别卡 owner）。

## A. 已知前置断点（走查前存在，非本卡引入）

| 环节 | 现象 | 证据文件 | 归属切片·卡 | 是否阻断旅程 |
|---|---|---|---|---|
| ② / ④ | live 缺 `board-recap/scripts/recap_exam_build.py`（第十批 `5322043f` 修过的加载点在 live 不可达） | `01-skill-versions.md` 第 4 行（DIFF, live MISSING） | G5 / 部署链（非本卡修） | 否（第二刀「阶段回顾→派生检验白板」在 live 不可达；本卡走单板 `/board-recap` + `/start-exam-board`，不经该脚本） |
| ② ③ ④ ⑤ | dev↔live skill 版本差异 **8 处**（`ai-linked-doc` / `board-recap` SKILL+recap_scan / `quiz-answer` / `start-exam-board` 等） | `01-skill-versions.md` 主表 | 部署冻结（非缺陷；总账 v2 :1007） | 否（旅程跑 live 副本；差异只双列登记，不「顺手同步」） |
| ① ② | live 未部署 `board-split` / `clear-inbox` 两目录（只有 `scripts/`，无 SKILL.md） | `01-skill-versions.md` 结论段 | G5-7 / G5-10 面（本批其它车道） | 否（本卡六环节不经该两 skill） |
| ③ | `search_notes` 延伸路径 `RAG_EXTENDED_MODE=1`（退役 LangGraph 多源管道）0/5 通道存活 | ⚠️ **读取面外主张，未纳入包内复核**（源自 `backend/app/mcp/tools/note_search_tools.py` 只读阅读；本卡不改该文件） | G4（RAG） | 否（默认 fast path LanceDB + BGE-M3 可用；本卡走默认） |

## B. 本卡运行期发现（新增）

| 环节 | 现象 | 证据文件 | 归属切片·卡 | 是否阻断旅程 |
|---|---|---|---|---|
| （证据包元级）manifest | 卡文 (c)④ / §二.5 要求 `validate_release_manifest.py _bmad-output/审查/evidence-g87-journey/manifest.json` → rc=0 且 `journey_id: "G8-7"`；**实测不可同时成立**：schema 的 `journey_id` 模式为 `^J(0[1-9]|10)$`（`"G8-7"` 被结构层直接拒），且语义规则 S6 要求 manifest 位于 `<rc>/journeys/<Jxx>/manifest.json`（证据目录根不满足） | `manifest-red-*.txt` / `manifest-green-*.txt` / `manifest-validator-conflict-*.txt` | **本卡（卡文缺陷）** —— 断点登记，主 session 裁定 | **是**（指定裁判红 = 阻断级，协议 §1） |
| （环境）test harness | `pytest tests/unit` 目录级开工基线 **32 红 ⊆ 33 基线**，唯一差 = 已知 flaky `test_candidate_service::test_accept_candidate_already_accepted_returns_422`（本批手册 §零.2 明示按噪声处理） | `unit-open-*.txt` / `open.nodeids` / `base.nodeids` | 非本卡（既有红基线） | 否 |

## C. 授权侧六环节（SKIP 登记）

> **用户 2026-09-19 当次裁定：不授权真实走查。** 按卡文 (d)「未授权即每环节 `not_run` + SKIP 登记」处理；不在本证据包中充当环节证据，不用 fixture / 旧存档（D5 / J06）顶替。

| 环节 | 状态 | 原因 | 归属 |
|---|---|---|---|
| ① vault 准备 | `not_run` | 未授权写 live vault | 授权侧（用户当次） |
| ② `/board-recap` | `not_run` | 同上 | 授权侧 |
| ③ `search_notes` | `not_run` | 同上 | 授权侧 |
| ④ `/start-exam-board` | `not_run` | 同上 | 授权侧 |
| ⑤ `/quiz-answer` | `not_run` | 同上 | 授权侧 |
| ⑥ 次日总览页 | `not_run` | 同上（只读 GET 可行，但因六环节链断，未单独跑） | 授权侧 |

- 未授权分支下已跑：`02-live-snapshot-before.txt` + `04-live-snapshot-after.txt`（只读），零静默改写门 `changed=0 outside=0`（`silent-rewrite-gate-*.txt`）。
- 六环节若后续授权走查，按 `00-README.md` 顺序执行并在本区逐条补登；届时若改动 evidence/manifest ⇒ 按卡文 §一(n) 再送 Codex 一轮绑新 HEAD。

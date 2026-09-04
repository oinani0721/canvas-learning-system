> ⚠️ 本文件是 CARD-TOOL-dredd-decide 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z7-C 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-TOOL-dredd-decide]`。车道：`card-z7-tool`，**前提 Z7-B 已 commit**。**用户裁决卡**：第一个 commit 只出裁决页；若手册 §三 Z7-C 块上方「用户裁决记录」已填则抄录直接进 (b)。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-TOOL-dredd-decide — Dredd 复活 / 退役裁决卡（默认退役，条件是 schemathesis 合约测试真接进 CI）

## 〇 事实
| 事实 | 位置 |
|---|---|
| X8（`7ba8fc07`）按用户 #2 裁定把 Dredd `contract-test` job 停用（`api-spec-sync.yml` `if: false`），并**如实声明覆盖缺口**：schemathesis `backend/tests/contract/test_openapi_contract.py` 未接入 `test.yml` 白名单（只在本机 `importorskip` 跑）→ CI 侧契约覆盖归零 | X8 验收单 / 台账 §一.b X8 行 ① |
| Dredd 现状：`scripts/spec-tools/dredd-hooks.js:34-41 / :148-156` 的 `rag/query` payload 缺 `vault_id`（G4-4a 后必 422，台账 4a-R2）；历史 24/24 全红且日志 410 不可考 | dredd-hooks.js |
| schemathesis 版本风险：`test_openapi_contract.py:26` 用 `schemathesis.openapi.from_asgi(...)`（4.x 形态），pin 是 `pyproject.toml:17 >=3.0` 与 `tests/contract/requirements.txt:16 >=3.19.0`；CI 解到 3.x 会 AttributeError；且 `importorskip` 让「装不上」变成静默 skip（负控假绿形态） | test_openapi_contract.py |
| `test.yml:78-107` 已定的扩面口径：显式 17 文件白名单 + `:111-121` env（DEBUG/CORS_ORIGINS/INTERNAL_API_KEY）+ `:124-141` flags（`-m 'not integration' --override-ini="addopts=" -p no:cacheprovider`）；`:95-99` 记载 xdist 收集不确定性 → 禁换成目录级/marker 级 | test.yml |
| schemathesis `from_asgi` 是进程内、不过真实网络栈、`max_examples=10`（`:39`）；Dredd 是真实 HTTP 栈按 example 回放 + hooks 流转/鉴权——**二者不等价**，禁写成「已完全覆盖」 | 事实 |
| CI/CD 变更（删 job / 改 test.yml）按全局 CLAUDE.md 判破坏性：车道落 commit **不 push**，合并前用户逐项批 | 纪律 |

## 一 完成条件（AND）
- (a) **裁决页**（第一个 commit 只含此页 + 验收单骨架）：三选一——甲 复活 Dredd（须先修 dredd-hooks.js payload 缺 vault_id，并解释 24/24 全红且日志不可考的前提下如何证明它能绿）/ **乙 正式退役**（删 contract-test job 与 dredd-hooks.js，或保留脚本标注退役）+ 把 schemathesis 接进 `test.yml` 白名单并配硬前置 / 丙 明确接受「契约测试只在本机跑」并在 README 如实声明。**默认乙**。用户批前不动 (b)。
- (b) 走乙：按 `test.yml:78-107` 口径把 `tests/contract/test_openapi_contract.py` 加进白名单，用与 `:111-121` **逐字相同**的 env 与 `:124-141` 相同 flags 做本地等价验证，给出可加性证明（现有 17 文件 + 本文件全绿，收集数如实记）。
- (c) 依赖声明同批落：schemathesis 版本口径统一到一处（backend/requirements 或 tests/contract/requirements.txt），**实机确认所装版本上 `schemathesis.openapi.from_asgi` 存在**；CI 里加一条 `python -c 'import schemathesis'` 硬前置，让「装不上」变红而不是 skip。
- (d) 负控两条：① 临时把某端点 `response_model` 改成与快照不符（不入 commit）→ schemathesis 门红；② 卸载/遮蔽 schemathesis → 硬前置红（而非静默 skip）。
- (e) 覆盖面如实声明：写清退役后**确实丢失**的是「真实 HTTP 栈按 example 回放 + hooks 流转与鉴权」，schemathesis 不等价。
- (f) README 若有「合约测试已覆盖」类文案，按 readme-claims-lint 口径核一遍并同步。
- (g) 两轮 Codex（gpt-6-astra ultra）：round-1 审裁决页与 (b)(c) diff；round-2 审负控与 workflow 变更（只审 `test.yml` / `api-spec-sync.yml` diff）。

## 二 裁判命令
1. `backend/.venv/bin/python -c "import schemathesis; print(schemathesis.__version__); print(hasattr(schemathesis,'openapi'))"`。
2. `cd backend && .venv/bin/python -m pytest tests/contract/test_openapi_contract.py -q --no-header -p no:cacheprovider --override-ini="addopts="`（env 用 `test.yml:111-121` 逐字）→ 绿。
3. `cd backend && .venv/bin/python -m pytest <test.yml:124-141 现有 17 文件> tests/contract/test_openapi_contract.py -q --no-header -m "not integration" -p no:cacheprovider --override-ini="addopts="` → 全绿，收集数如实记。
4. `cd backend && .venv/bin/python ../scripts/spec-tools/check-openapi-drift.py --snapshot openapi.json` → `DRIFT: none`（不得手改快照）。
5. `grep -cE '^\s*contract-test:' .github/workflows/api-spec-sync.yml` 与 `grep -n 'test_openapi_contract' .github/workflows/test.yml` → 与所选方案一致；YAML 可解析。

## 三 禁改与隔离
禁在裁决页被批之前删 contract-test job 或 dredd-hooks.js；禁 push（CI/CD 变更车道落 commit，合并前用户逐项批）；禁手改 `backend/openapi.json`；禁声称 schemathesis 与 Dredd 等价；禁把 `test.yml` 显式 17 文件白名单换成目录级/marker 级；禁改 lefthook.yml（Z7-A/B 面已落，不再动）；不改台账。

## 四 Codex / 验收单
命令同协议，两轮 `codex-prompt-CARD-TOOL-dredd-decide-r1.md` / `-r2.md`。验收单 `…/验收单/UAT-CARD-TOOL-dredd-decide-<日期>.md`：DoD-3 双段；4-B「无变化（决定一个坏了很久的自动检查是修还是换掉，并把换的那个真接上）」；「待你裁决」三选一（或抄录已裁）；「本卡未证明什么」必填：未经 GitHub 实跑、schemathesis ≠ Dredd；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push；跑完说「复核第十一批 Z7」。

> ⚠️ 本文件是 CARD-CX-G6-2b-R1 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z1-A 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-CX-G6-2b-R1]`。车道：复用 `card-x2-g62b`（主 session 已于 2026-09-05 预合主干 `304f03ca`，venv symlink 已建）。勘探 2026-09-05（6 只读 agent，主干 `f128a85e`；行号在 `304f03ca` 上未漂移，开工仍须 `sed -n` 实测）。
> 协议：`.claude/rules/card-batch-protocol.md`（合并门 / Codex 命令 gpt-6-astra ultra / 裁判最低覆盖 / 合并程序）。

# CARD-CX-G6-2b-R1 — X2 `92734207` 补审：代际因果锚 + AST 门根名/豁免判定（1 轮 Codex）

## 〇 事实
| 事实 | 位置 |
|---|---|
| `92734207` 代码面只有 2 文件：`backend/app/api/v1/endpoints/review_app.py`（27 行）与 `backend/tests/unit/test_review_app.py`（264 行）；其余 23 文件在 `_bmad-output/`。commit 自述「整改未经任何外部复审」——第十批唯一带阻断级历史却零外审的代码面 | `git show --stat 92734207` |
| 代际因果锚**唯一判据行** `review_app.py:402` `if (startGen !== undefined && n.gen !== undefined && startGen <= n.gen) continue;`（台账原写 `:397`，那是注释行——**行号必须重取**） | `sed -n '398,406p'` |
| 代际锚 5 个耦合点：state `:345-347`（pollGen: 0 / pendingSync）、settlePendingSync 签名 `:388`、判据 `:402`、poll 取 gen `:442` 与两处结算 `:462` / `:473`、POST 写 pending `:508` | `grep -n 'settlePendingSync\|pendingSync\|pollGen'` |
| AST 门整改在 `test_review_app.py` 连续区：`_OWN_MODULE_DEFINITIONS :277`、`_root_name :286-296`、Store/Del 根名判定 `:353`、模块级定义豁免 `:380-400`、装饰器穷举 `:440-456`、def/class 名豁免 `:458-463`、request 形参注解 `:483`、重复定义收口 `:503` | 同文件 |
| **已知洞 ①**：`_root_name` 对根不是 `ast.Name` 的写路径返回空串（`:295`）→ `get_mod().dumps = f` / `(a or b).dumps = f` 因根名 `""` 不在 `_BANNED_REBINDS` 而放行 | `:286-296` + `:353-359` |
| **已知洞 ②**：request 豁免判据 `_root_name(arg.annotation) == "Request"`（`:483`）对 `fastapi.Request` / `Annotated[Request, Depends()]` / 字符串注解三种合法写法判红——方向 fail-closed，但豁免面窄于合法集 | `:483` |
| 上一版实现 = `27e61454`（时间戳锚），可作真实负控体 | `git show 27e61454 -- backend/app/api/v1/endpoints/review_app.py` |

## 一 完成条件（AND）
- (a) 只读复核并在验收单落 file:line：代际判据 `:402` 的三个前提逐条证明——① `state.pollGen` 在 poll 入口 `:442` 严格递增且无其他写点；② POST 侧 `:508` 记的 `n.gen` 是「发 POST 那一刻已启动的最新 GET 代际」；③ `document.hidden` 分支不发 GET 时 pending 不会永久饿死（回前台 visibilitychange 的 poll 代际必然更大）。
- (b) 负控用**真实上一版**而非手工变异体：把 `27e61454` 的 review_app.py 换入 → 同毫秒门必红、既有 ①② 门必绿 → 还原后 `shasum -a 256` 逐字节相同；三段 sha 落 `_bmad-output/审查/evidence-g62b/`。
- (c) AST 门四条新补面逐条给探针（进 evidence-g62b/）：① 洞 ①（`get_mod().dumps = f` / `(a or b).dumps = f`）实测放行 → 二选一「登记为已知洞」或「收紧」并写理由；② `ast.MatchAs / MatchStar / MatchMapping.rest` 绑定名不产生 Store 位置的 Name，构造 match 语句重绑定实测；③ `global`/`nonlocal` 声明 + 赋值；④ 装饰器穷举 `:440-456` 漏 `ast.Attribute` 链式装饰器的实测。
- (d) 洞 ②（`:483`）适用面如实声明：三种合法写法各一探针，结论写进 `:483` 上方注释，**不改判据只改声明**。
- (e) 重复定义收口 `:503` 真承重：构造模块级两次 `def _js_json` 与两次 `_PAGE_TEMPLATE = "..."`，改前 PASS 改后 FAIL。
- (f) 一轮 Codex（gpt-6-astra ultra）：prompt 五分节（一 只读文件 + 精确 `git show 92734207 -- <2 文件>` / 二 这次改了什么 / 三 重点问题按重要度 / 四 已裁决不再计 / 五 输出格式，末行「BLOCKER/HIGH 清零：是/否」）；§四 写入 D-4/D-5 已按默认、洞 ①② 若选「登记」则列为已裁决。
- (g) Codex 每条**先实测再采信**，采信/驳回逐条写进验收单，不直接抄结论。
- (h) 本卡不改 `review_app.py` 的代际语义（只许收紧，不许改回时间戳或引入第二套锚）。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_review_app.py tests/unit/test_review_overview.py` → 143 passed 起（新增门只增不减）。
2. `… $PYTEST -q -p no:cacheprovider tests/unit/test_review_app.py::test_review_app_module_imports_are_closed tests/unit/test_review_app.py::test_js_stale_get_cannot_settle_rebuild tests/unit/test_review_app.py::test_js_causal_anchor_survives_same_millisecond` → 绿。
3. 负控：换入 `27e61454` 版 → 裁判 2 中同毫秒门红 → 还原 → `shasum -a 256 backend/app/api/v1/endpoints/review_app.py` 与换入前相同。
4. `grep -c 'with TestClient' backend/tests/unit/test_review_app.py backend/tests/unit/test_review_overview.py backend/app/api/v1/endpoints/review_app.py` → 三文件 0（不起 lifespan）。
5. 门下目录级：`… $PYTEST -q -p no:cacheprovider tests/api` → 与主干基线同（主干既有红 6 条登记不算；Z4 合入后为 0）。

## 三 禁改与隔离
禁改 `review_overview.py`、`app/main.py`、`backend/tests/fixtures/**`；禁放宽 `ALLOWED_IMPORTS / _ALLOWED_CALL_NAMES / _ALLOWED_CALL_ATTRS / _ALLOWED_RECEIVERS` 四张白名单；禁改代际语义；禁改台账（只写「台账待登记条目」）；live vault 只读、禁连 7691、禁真实出网。**本卡 commit 后同车道继续 Z1-B（G6-3 取证）**——Z1-B/C/D 会改 review_app.py，本卡的注释/探针须在其之前独立 commit。

## 四 Codex / 验收单
命令：`codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-CX-G6-2b-R1.md)" > <树>/_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1.md 2> <树>/_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1.stderr </dev/null`（1 轮；0 字节重发一次后主 session 人审）。验收单 `…/验收单/UAT-CARD-CX-G6-2b-R1-<日期>.md`：DoD-3 双段；4-B「无变化（只是把上次自己改的东西请第三方看了一遍）」零技术词；「本卡未证明什么」必填（洞 ①② 若登记则写明）；「台账待登记条目」必填（X2 行的锚点 `:397→:402` 更正）。commit header ≤100 含批次标记，body 行 ≤100；不 push。

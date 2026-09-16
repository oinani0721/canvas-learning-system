# 独立复核请求（round-2）— CARD-SEC-DANGLING（第十四批 T5-D）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`（分支 `card/t5-bugs`）。

round-1 结论是 BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 2。作者采纳了 MEDIUM-1、MEDIUM-2、LOW-1 与一处注释更正，改的**只有测试文件**；生产源 `backend/app/security.py` 与快照 `backend/openapi.json` 自 round-1 起**一字未动**。本轮请复核这次整改本身。

**请只读下面这些面，不要跑测试、不要跑 hook、不要连任何数据库：**

1. round-1 之后的全部改动：`git diff c5e30cfc5e6681076d9bac8cc37c8792545eb1c6 __REVIEW_SHA__ -- . ':(exclude)_bmad-output'`
2. 本卡自前提 commit 起的全部代码改动（累计面）：`git diff 2287e2583c54472d238e8b8eec87bb1e9e95c9e8 __REVIEW_SHA__ -- . ':(exclude)_bmad-output'`
3. `backend/tests/contract/test_openapi_contract.py` 末尾 `Security scheme 悬空引用门` 整段（注释块 + `_HTTP_METHODS` + `_load_drift_module_for_security` + `_iter_path_item_security_refs` + `_iter_security_refs` + `test_security_schemes_cover_all_security_refs`）
4. round-1 存档 `_bmad-output/审查/codex-review-CARD-SEC-DANGLING.md`（你上一轮的意见原文）
5. 本轮新增证据：`_bmad-output/审查/evidence-sec-dangling/enum-coverage-probe-final-20260916T201922.txt`、`r2-red-green-negctl-fixed-20260916T202118.txt`、`r2-ruff-pyright-20260916T202258.txt`、`contract-3files-close-r2-*.txt`、`unit-close-r2-*.txt`
6. 验收单 `_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md` 的 §七（round-1 逐条处置表）

## ② 作者自述（请独立核对，不要采信）

**针对 MEDIUM-1（枚举遗漏合法嵌套 operation）**：新增 `_iter_path_item_security_refs(path_item, location)`，遍历一个 Path Item 下所有 operation 的 `security` 并**递归其 `callbacks`**；`_iter_security_refs` 现在依次走：文档根 `security` → `paths` → `webhooks` → `components.pathItems` → `components.callbacks`。`$ref` 仍不解析，理由写在 docstring：被引用的 Path Item 若来自 `components.pathItems`，它本身已被独立遍历，覆盖面不缺口（代价是同一 operation 可能以两个位置串各记一次，对「是否悬空」的判定无影响）。递归无环的依据：`load_live_schema()` 走过 `json.dumps`/`json.loads` 往返，产出纯 JSON 树。

**针对 LOW-1（`x-*` 冒充 per-op）**：加 `_HTTP_METHODS` 白名单（OpenAPI 3.1 的 8 个方法），只有这些键被当 operation。取舍已写进注释：代价是**非标准**方法键携带真 `security` 会被漏掉。

**针对 MEDIUM-2（禁闭覆盖面主张过强）**：注释块改写为如实口径 —— 明确点出 `:18` 的模块级 `from app.main import app` 与 `:79` 的 `from_asgi(...)` 都在禁闭外、`_custom_openapi` 有缓存、禁闭只换 `socket.socket.connect` 一个入口；本门**不**主张「整条收集路径无网络行为」，只主张「断言本身不发 HTTP 请求」+「每次定向跑 W4 端口门记账为 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`」。

**针对「两条前置断言」的更正**：docstring 改为「三条」并写明各自守什么，同时补上本门**不**证明的两件事（不排除 securitySchemes 里的冗余/同义方案；不校验方案定义体的 `type`/`in`/`name`）。

**LOW-2（与模块级 `importorskip` 耦合）未修**：卡文把断言落点钉死在 `test_openapi_contract.py`，移到独立文件属越界。已记入验收单「本卡未证明什么」。

**整改后的裁判**：`enum-coverage-probe-final-…` 用合成 schema 喂 `_iter_security_refs`，8/8 通过（A 组五处嵌套位置都被看见；B 组 `x-*` 与固定字段不计；C 组真实快照仍是 32/31/0）。`r2-red-green-negctl-fixed-…` 三阶段：对照绿 / 先红 31 与 /system/\* 16 / 负控 2 failed，跑前跑后 `shasum -a 256` 逐字相同。pyright `app` = 0 errors / 81 warnings。

## ③ 请按重要性排序回答的问题

- **⓪** MEDIUM-1 是否真的关闭了？`_iter_security_refs` + `_iter_path_item_security_refs` 现在的枚举面，是否还剩**门未覆盖的路径** —— OpenAPI 3.1 里还有没有别的位置能合法承载 Security Requirement Object？
- **①** 整改本身有没有引入新缺陷：递归是否可能不终止或重复计数？`_HTTP_METHODS` 白名单在大小写、`$ref` 形态的 Path Item、或 `callbacks` 值不是 dict 时的行为是否稳妥？
- **②** `enum-coverage-probe-final-20260916T201922.txt` 这条验伪锚本身是否成立 —— 它的**对照输入**（B 组）是否真能证明「不该算的没算」，还是只证明了「某个方案名没出现」？8 条断言里有没有恒真的？
- **③** MEDIUM-2 的注释改写是否已把主张收到证据能支撑的范围内？现在的措辞有没有仍然过强的地方？
- **④** LOW-2 不修、只登记，理由是「卡文把落点钉死在该文件」。这个处置是否合理？如果不合理，有没有不越界的做法？
- **⑤** 本轮只改测试文件，作者据此主张 `backend/openapi.json` 与 `backend/app/security.py` 无需重新再生 / 重新验证。这个推断成立吗？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与一句**复核思路**（说明你会怎样独立确认这条，用中性说法）。没有问题的级别请显式写 0 条。

## ⑤ 边界

- 只读；不跑测试、不跑 lefthook、不连 7691/7687/7692、不写任何文件。
- 不评运行时 403/503 行为门（归本批 T10-E），不评 `system.py` 端点语义，不评 `main.py:386-404`（本批 T6-B 地盘）。
- round-1 已判定成立的项（`scheme_name` 语义、31→0 的事实、⑤ 取舍、⑦ glob）无需重复论证，除非本轮改动动摇了它们。

# 独立复核请求（round-2）— CARD-SEC-DANGLING（第十四批 T5-D）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`（分支 `card/t5-bugs`）。

round-1 结论是 BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 2。作者采纳了 MEDIUM-1、MEDIUM-2、LOW-1、一处注释更正，并在自查中**又补了一项加固**（详见 ②-③），改的**只有测试文件**；生产源 `backend/app/security.py` 与快照 `backend/openapi.json` 自 round-1 起**一字未动**。本轮请复核这次整改本身。

**请只读下面这些面，不要跑测试、不要跑 hook、不要连任何数据库：**

1. round-1 之后的全部改动：`git diff c5e30cfc5e6681076d9bac8cc37c8792545eb1c6 76a602c436e25e55c44c690098a4b55ed1f99cfd -- . ':(exclude)_bmad-output'`
2. 本卡自前提 commit 起的全部代码改动（累计面）：`git diff 2287e2583c54472d238e8b8eec87bb1e9e95c9e8 76a602c436e25e55c44c690098a4b55ed1f99cfd -- . ':(exclude)_bmad-output'`
3. `backend/tests/contract/test_openapi_contract.py` 末尾 `Security scheme 悬空引用门` 整段（注释块 + `_HTTP_METHODS` + `_load_drift_module_for_security` + `_iter_path_item_security_refs` + `_iter_security_refs` + `test_security_schemes_cover_all_security_refs`）
4. round-1 存档 `_bmad-output/审查/codex-review-CARD-SEC-DANGLING.md`（你上一轮的意见原文）
5. 本轮**承重**证据（只有这五份作数）：`_bmad-output/审查/evidence-sec-dangling/` 下的
   `enum-coverage-probe-r2c-20260916T202622.txt`（枚举面验伪锚 16/16）、
   `r2-final-red-green-negctl-20260916T203537.txt`（先红 / 对照绿 / 负控 + 前后 sha）、
   `r2-final-ruff-pyright-20260916T203640.txt`（ruff / F821 锚 / pyright / 收集面）、
   `contract-3files-close-r2-20260916T202245.txt`、`unit-close-r2-20260916T202245.txt`。
   同目录另有 7 份**已被取代**的中间档（文件名里带 `-20260916T2018` / `-2019` / `-2020` / `-2022` / `-2025` 的枚举探针与 negctl 早期版本），验收单 §七 round-2 有逐条取代原因表；它们留作过程留痕，**不作依据**，其中 `enum-coverage-probe-r2b-20260916T202522.txt` 是一条**有价值的红**（见 ③ 的加固项）
6. 验收单 `_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md` 的 §七（round-1 逐条处置表）

## ② 作者自述（请独立核对，不要采信）

**针对 MEDIUM-1（枚举遗漏合法嵌套 operation）**：新增 `_iter_path_item_security_refs(path_item, location)`，遍历一个 Path Item 下所有 operation 的 `security` 并**递归其 `callbacks`**；`_iter_security_refs` 现在依次走：文档根 `security` → `paths` → `webhooks` → `components.pathItems` → `components.callbacks`。`$ref` 仍不解析，理由写在 docstring：被引用的 Path Item 若来自 `components.pathItems`，它本身已被独立遍历，覆盖面不缺口（代价是同一 operation 可能以两个位置串各记一次，对「是否悬空」的判定无影响）。递归无环的依据：`load_live_schema()` 走过 `json.dumps`/`json.loads` 往返，产出纯 JSON 树。

**针对 LOW-1（`x-*` 冒充 per-op）**：加 `_HTTP_METHODS` 白名单（OpenAPI 3.1 的 8 个方法），只有这些键被当 operation。取舍已写进注释：代价是**非标准**方法键携带真 `security` 会被漏掉。

**针对 MEDIUM-2（禁闭覆盖面主张过强）**：注释块改写为如实口径 —— 明确点出 `:18` 的模块级 `from app.main import app` 与 `:79` 的 `from_asgi(...)` 都在禁闭外、`_custom_openapi` 有缓存、禁闭只换 `socket.socket.connect` 一个入口；本门**不**主张「整条收集路径无网络行为」，只主张「断言本身不发 HTTP 请求」+「每次定向跑 W4 端口门记账为 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`」。

**针对「两条前置断言」的更正**：docstring 改为「三条」并写明各自守什么，同时补上本门**不**证明的两件事（不排除 securitySchemes 里的冗余/同义方案；不校验方案定义体的 `type`/`in`/`name`）。

**LOW-2（与模块级 `importorskip` 耦合）未修**：卡文把断言落点钉死在 `test_openapi_contract.py`，移到独立文件属越界。已记入验收单「本卡未证明什么」。

**作者自查时又补的一项加固（不在 r1 意见里，请一并核）**：新增 `_as_dict(value)`，把 `paths` / `webhooks` / `components.pathItems` / `callbacks` 容器及其内层的**非 dict 值**一律降级成空 dict。起因是作者给探针加了 D 组畸形结构用例后实测 **D3 红**：`callbacks` **容器本身**若不是 dict（例如是 list），`(operation.get("callbacks") or {}).items()` 仍会抛 `AttributeError` —— 当时只守了内层、没守容器。该红档留在 `enum-coverage-probe-r2b-20260916T202522.txt`。取舍写在 `_iter_path_item_security_refs` 的 docstring：畸形结构静默跳过而非抛异常，理由是本门的主张是「引用都有定义」，对畸形结构报 `AttributeError` 会把契约问题伪装成门自己坏了。

**整改后的裁判（全部为加固后重取）**：`enum-coverage-probe-r2c-20260916T202622.txt` 用合成 schema 喂 `_iter_security_refs`，**16/16 通过**（A 组 5 条：五处嵌套位置都被看见；B 组 2 条：`x-*` 与固定字段不计；D 组 8 条：六类畸形结构不抛异常 + 大写方法键仍被当 operation；C 组 1 条：真实快照仍是 32/31/0）。`r2-final-red-green-negctl-20260916T203537.txt` 三阶段：对照绿 / 先红 31 与 /system/\* 16 / 负控 2 failed，跑前跑后三文件 `shasum -a 256` 逐字相同。`r2-final-ruff-pyright-20260916T203640.txt`：ruff `All checks passed!`、F821 锚 rc=1、pyright `app` = 0 errors / 81 warnings、`91 tests collected`。

**关于两条长跑的适用性（请判断这个推断）**：`contract-3files-close-r2-…` 与 `unit-close-r2-…` 跑在该测试文件的**上一版**（sha `9765a69a…`）上，之后才做了 `_as_dict` 加固（现 sha `7bbe7d73…`）。作者主张两者无需重跑，依据是命令面：contract 那条逐个点名了三个文件、其中不含 `test_openapi_contract.py`；`tests/unit` 只收集 `tests/unit` 目录。

## ③ 请按重要性排序回答的问题

- **⓪** MEDIUM-1 是否真的关闭了？`_iter_security_refs` + `_iter_path_item_security_refs` 现在的枚举面，是否还剩**门未覆盖的路径** —— OpenAPI 3.1 里还有没有别的位置能合法承载 Security Requirement Object？
- **①** 整改本身有没有引入新缺陷：递归是否可能不终止或重复计数？`_HTTP_METHODS` 白名单在大小写、`$ref` 形态的 Path Item、或 `callbacks` 值不是 dict 时的行为是否稳妥？
- **②** `enum-coverage-probe-r2c-20260916T202622.txt` 这条验伪锚本身是否成立 —— 它的**对照输入**（B 组）是否真能证明「不该算的没算」，还是只证明了「某个方案名没出现」？D 组的 `run_no_raise` 只断言「没抛异常」，这样的断言有没有恒真的？16 条里哪几条实际上什么都没测？
- **③** MEDIUM-2 的注释改写是否已把主张收到证据能支撑的范围内？现在的措辞有没有仍然过强的地方？
- **④** LOW-2 不修、只登记，理由是「卡文把落点钉死在该文件」。这个处置是否合理？如果不合理，有没有不越界的做法？
- **⑤** 本轮只改测试文件，作者据此主张 `backend/openapi.json` 与 `backend/app/security.py` 无需重新再生 / 重新验证。这个推断成立吗？
- **⑥** 上面 ② 末尾那条「两条长跑不必重跑」的推断是否成立？pytest 会不会以作者没想到的方式把 `tests/contract/test_openapi_contract.py` 带进那两次运行（例如 conftest、插件、`-p` 自动加载或缓存）？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与一句**复核思路**（说明你会怎样独立确认这条，用中性说法）。没有问题的级别请显式写 0 条。

## ⑤ 边界

- 只读；不跑测试、不跑 lefthook、不连 7691/7687/7692、不写任何文件。
- 不评运行时 403/503 行为门（归本批 T10-E），不评 `system.py` 端点语义，不评 `main.py:386-404`（本批 T6-B 地盘）。
- round-1 已判定成立的项（`scheme_name` 语义、31→0 的事实、⑤ 取舍、⑦ glob）无需重复论证，除非本轮改动动摇了它们。

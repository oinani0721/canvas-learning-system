# 独立复核请求（round-3）— CARD-SEC-DANGLING（第十四批 T5-D）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`（分支 `card/t5-bugs`）。

round-2 结论是 BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 4，**合并条件按批次规则在 r2 即已满足**。本轮是作者**主动**追加的质量整改：采纳了 r2 的 MEDIUM-1、MEDIUM-2、LOW-1、LOW-3、LOW-4 与两处措辞更正，LOW-2 采纳意见但维持不修、只更正理由。改的**只有测试文件与文档**；生产源 `backend/app/security.py` 与快照 `backend/openapi.json` 自 round-1 起**一字未动**（sha 全程 `925443dce1f90b35391898dc7cfa45c436107b7d015ed9f24e30c90e0e361904` / `9df9f7df7fdb9a8f4d5ae22aa0886fe8e36d0e66f4e106a1579801c9824bab79`）。

**请只读下面这些面，不要跑测试、不要跑 hook、不要连任何数据库：**

1. round-2 之后的全部改动：`git diff 76a602c436e25e55c44c690098a4b55ed1f99cfd __REVIEW_SHA__ -- . ':(exclude)_bmad-output'`
2. 本卡自前提 commit 起的全部代码改动（累计面）：`git diff 2287e2583c54472d238e8b8eec87bb1e9e95c9e8 __REVIEW_SHA__ -- . ':(exclude)_bmad-output'`
3. `backend/tests/contract/test_openapi_contract.py` 末尾 `Security scheme 悬空引用门` 整段（注释块 + `_HTTP_METHODS` + `_as_dict` + `_named_entries` + `_load_drift_module_for_security` + `_iter_path_item_security_refs` + `_iter_security_refs` + `test_security_schemes_cover_all_security_refs`）
4. round-2 存档 `_bmad-output/审查/codex-review-CARD-SEC-DANGLING-r2.md`（你上一轮的意见原文）
5. 本轮**承重**证据（`_bmad-output/审查/evidence-sec-dangling/` 下）：
   - `enum-coverage-probe-r3-20260916T232823.txt` —— 枚举面对抗输入台。**该档末尾逐字收录了探针脚本全文**，每条用例都打印了合成输入、实际完整产出、精确期望集合与「能否区分本卡加固」标注
   - `r3-red-green-negctl-20260916T232904.txt` —— 先红 / 对照绿 / 负控，**逐阶段**带 W4 端口门记账行 + 跑前跑后 sha
   - `ref-distribution-census-20260916T204712.txt` —— 本仓 `$ref` 分布实测
   - `contract-3files-close-r3-*.txt`、`unit-close-r3-*.txt` —— 在**最终 sha** 上重跑的两条长跑
   - `r3-ruff-pyright-20260916T233009.txt`
6. 验收单 `_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md` 的 §七（r1/r2 逐条处置表）与 §四（本卡未证明什么）

## ② 作者自述（请独立核对，不要采信）

**r2 MEDIUM-1（`$ref` ⇒ 「全部合法位置」过强）**：不补 `$ref` 解析，改为**收窄主张** —— docstring 现写「全部**内联**位置」，并把 `$ref` 不解析列为**已知边界**，写明引用目标可落在遍历清单之外。同时补一条实测依据（`ref-distribution-census-…`）：本仓快照全文 `$ref` 736 处（`components` 212 / `paths` 524），但 **Path Item 级 `$ref`（`$.paths.<path>.$ref`）= 0**，`paths` 下那 524 处全在更深层的请求/响应 schema 里；另实测无 `webhooks`、`components` 只有 `schemas`/`securitySchemes`、`callbacks` 子树无 `$ref`。结论限定为「对本仓不构成缺口；换生成器就是真缺口」。

**r2 MEDIUM-2（验伪锚无法独立复核）**：重写探针。现在每条用例打印合成输入（紧凑 JSON）、实际**完整**产出、**精确期望集合**，断言一律是**集合相等**而不是「某名字不在里面」；生成器用 `list()` 消费；每条标 `能区分加固 = True/False`（True = 加固前会 FAIL）；存档**逐字收录脚本全文**。计数由脚本自算并带自洽性断言（作者上一版把分类计数写死过，13+5≠20）。本轮 20/20，分类 15 能区分 / 4 覆盖性 / 1 回归锁。

**r2 LOW-1（`x-*` 只修了 Path Item 层）**：新增 `_named_entries()`，在 `paths` / `webhooks` / `components.pathItems` / `components.callbacks` / callback 名层 / callback 表达式层统一跳过 `x-*` 键。探针 B3–B6 四条专测这个。

**r2 LOW-3（长跑复用理由过强）**：不再论证「可复用」，直接在**最终 sha** 上重跑 `contract` 三文件与 `tests/unit` 目录级。

**r2 LOW-4（W4 零记账只在对照阶段有记录）**：红绿档现在**逐阶段**打印 W4 行。

**r2 LOW-2（与模块级 `importorskip` 耦合）**：采纳意见、维持不修，但**更正理由** —— 原写「技术上只能迁移文件」不成立；真实理由是范围（要动卡文禁改的既有模块级行 `:17`–`:19` / `:78`–`:85`）。已记入验收单「本卡未证明什么」并登记为移交项。

**另有一条本轮实测到的事实，已如实写进验收单**：探针的模块级 import（即 `test_openapi_contract.py:18` 那条 `from app.main import app`）触发了 LiteLLM 对 `raw.githubusercontent.com` 的真实外联并 SSL 握手超时。它不是 7691/7687（W4 逐次记账仍为 0），也非本卡引入，但它坐实了 r2 MEDIUM-2 要求收窄的那一点。

## ③ 请按重要性排序回答的问题

- **⓪** r2 的 MEDIUM-1 / MEDIUM-2 / LOW-1 / LOW-3 / LOW-4 是否真的关闭了？其中哪一条只是措辞变化而实质未变？
- **①** `_named_entries` 的 `x-*` 跳过规则是否正确且够用：它用 `name.startswith("x-")`，对非字符串键、大小写（`X-`）、以及 OpenAPI 3.1 里**合法但不以 `x-` 开头**的非 operation 键（例如 Paths Object 下不以 `/` 开头的键）分别会怎样？有没有因此**漏掉**真引用的**门未覆盖的路径**？
- **②** 收窄后的 docstring 与注释是否还有过强之处？特别是那条 `$ref` 实测结论（736 / 212 / 524 / Path Item 级 0）的表述，是否恰好等于证据能支撑的范围？
- **③** 新探针（脚本全文在 `enum-coverage-probe-r3-*.txt` 末尾）是否已能被独立复核？20 条里有没有**对照输入**其实是恒真的、或期望集合写错却仍 PASS 的？`能区分加固 = True` 的那 15 条，标注是否属实？
- **④** 本轮改动有没有引入新缺陷：递归、生成器语义、`_as_dict` 与 `_named_entries` 的组合，在畸形或对抗输入下是否仍然稳妥？
- **⑤** 「r1 起生产源与快照一字未动」这个主张，能否由你独立复算的文件 SHA 与提交 diff 确认？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与一句**复核思路**（说明你会怎样独立确认这条，用中性说法）。没有问题的级别请显式写 0 条。

## ⑤ 边界

- 只读；不跑测试、不跑 lefthook、不连 7691/7687/7692、不写任何文件。
- 不评运行时 403/503 行为门（归本批 T10-E），不评 `system.py` 端点语义，不评 `main.py:386-404`（本批 T6-B 地盘）。
- r1/r2 已判定成立的项（`scheme_name` 语义、31→0 的事实、schemathesis 取舍、lefthook glob、「本轮无需重新生成生产源或快照」）无需重复论证，除非本轮改动动摇了它们。

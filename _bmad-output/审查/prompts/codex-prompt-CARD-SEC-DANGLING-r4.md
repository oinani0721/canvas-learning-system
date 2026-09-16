# 独立复核请求（round-4）— CARD-SEC-DANGLING（第十四批 T5-D）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`（分支 `card/t5-bugs`）。

round-3 结论是 BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3，其中 **MEDIUM-1 指出了作者在 r3 自己引入的一条真回归**（`x-*` 跳过被推广到命名映射，导致名叫 `x-event` 的 webhook / callback / 组件条目被整个跳过 = 漏掉真引用；且探针 B4/B6 的期望集合跟着写错却仍 PASS）。本轮请复核这次修复。改的**只有测试文件与文档**；生产源 `backend/app/security.py` 与快照 `backend/openapi.json` 自 round-1 起**一字未动**（sha 全程 `925443dce1f90b35391898dc7cfa45c436107b7d015ed9f24e30c90e0e361904` / `9df9f7df7fdb9a8f4d5ae22aa0886fe8e36d0e66f4e106a1579801c9824bab79`，你在 r3 已独立复算确认过）。

**请只读下面这些面，不要跑测试、不要跑 hook、不要连任何数据库：**

1. round-3 之后的全部改动：`git diff 9861c59598ca350ca7df10921744292b0deffb41 __REVIEW_SHA__ -- . ':(exclude)_bmad-output'`
2. 本卡自前提 commit 起的全部代码改动（累计面）：`git diff 2287e2583c54472d238e8b8eec87bb1e9e95c9e8 __REVIEW_SHA__ -- . ':(exclude)_bmad-output'`
3. `backend/tests/contract/test_openapi_contract.py` 末尾 `Security scheme 悬空引用门` 整段（注释块 + `_HTTP_METHODS` + `_as_dict` + `_extensible_entries` + `_load_drift_module_for_security` + `_iter_path_item_security_refs` + `_iter_security_refs` + `test_security_schemes_cover_all_security_refs`）
4. round-3 存档 `_bmad-output/审查/codex-review-CARD-SEC-DANGLING-r3.md`（你上一轮的意见原文）
5. 本轮**承重**证据（`_bmad-output/审查/evidence-sec-dangling/` 下）：
   - `enum-coverage-probe-r4-20260917T021352.txt` —— 枚举面对抗输入台，**末尾逐字收录探针脚本全文**；每条用例打印合成输入 / 实际完整产出 / 精确期望集合 / `能区分加固` 标注
   - `r4-red-green-negctl-20260917T021426.txt` —— 先红 / 对照绿 / 负控，逐阶段带 W4 记账 + 跑前跑后 sha
   - `r4-ruff-pyright-20260917T021534.txt`
   - `ref-distribution-census-20260916T204712.txt` —— **末尾有本轮追加的更正段与逐路径细分**（收 r3 LOW-2）
   - `contract-3files-close-r4-*.txt`、`unit-close-r4-*.txt`
6. 验收单 `_bmad-output/验收单/UAT-CARD-SEC-DANGLING-2026-09-16.md` 的 §七 round-3 / round-4 两节

## ② 作者自述（请独立核对，不要采信）

**r3 MEDIUM-1（`x-*` 过滤推广到命名映射 ⇒ 漏检）**：按「可挂扩展的对象」与「命名映射」逐层区分，不再一刀切。函数由 `_named_entries` 改名为 `_extensible_entries`，docstring 写死适用面**只有两处**：Paths Object（键是 `/…` 路径）与 Callback Object 的**表达式**层（键是运行时表达式）。`webhooks` / `components.pathItems` / `components.callbacks` / operation 的 `callbacks` 四处改回 `_as_dict(...).items()`，一律不跳 `x-*`。docstring 里写明理由：「对象自身允许扩展」不蕴含「它的子映射里所有 `x-` 开头的名字都是扩展」。

**探针（同一根因导致的期望写错）**：B4/B6 的期望集合按新行为改正；新增 **B7** = 你给的静态反例逐字照搬（`webhooks["x-event"].post.security=[{"Missing":[]}]` + 一个正常 webhook，期望两条都枚举到）；新增 **B8** 钉死「表达式层仍跳」这个反方向，防止两层被一起改掉。本轮 22/22。

**r3 LOW-1（标注不实）**：B2 与 C4 的 `discriminates` 由 `True` 改 `False` 并写明理由（B2 从 r1 起就被 `isinstance(operation, dict)` 跳过；C4 旧 `continue` 与新空迭代都产出空集合）。E 组标题写明它**不是**完整集合比较，只核数量 / 声明集 / 悬空集。分类现为 15 能区分 / 6 覆盖性 / 1 回归锁 = 22。

**r3 LOW-2（`$ref` 分类超出证据 + 存档自相矛盾）**：普查档末尾追加更正段，承认第 2 行那句「只出现在 components.schemas 侧」是**测之前的猜测**、与同档 `paths: 524` 矛盾（原行保留不改，留痕）；并补逐路径细分实测：paths 侧 524 = `responses` 430 + `requestBody` 91 + `parameters` 3，无一停在 Path Item 层或 operation 层本身。

**r3 LOW-3（「最终 sha 上重跑」字面不准）**：验收单措辞改为「尾改前版本重跑，最终版本经文案等价关系绑定」，并记下你独立逆转 docstring 尾改后复算 SHA 精确相等这一事实。

**r3 LOW-2(r2 遗留，与 `importorskip` 的耦合)**：仍维持不修、已登记移交。

## ③ 请按重要性排序回答的问题

- **⓪** r3 的 MEDIUM-1 是否真的关闭了？新的「可挂扩展对象 vs 命名映射」二分，对照 OpenAPI 3.1 是否**逐层都分对了**？有没有哪一层我判反了、因而仍存在**门未覆盖的路径**或新的误计？
- **①** `_extensible_entries` 现在只用在两处。Paths Object 下既不以 `/` 也不以 `x-` 开头的键、Callback 表达式层的非表达式键、以及非字符串键，分别会怎样？这些处置是否可接受？
- **②** 探针的 B4 / B6 / B7 / B8 四条**对照输入**是否真能把 r3 与 r4 的行为区分开？期望集合这次写对了吗（上一轮正是这里「写错却仍 PASS」）？22 条里还有没有标注不实或缺乏鉴别力的？
- **③** 普查档末尾追加的逐路径细分，是否已把 r3 LOW-2 的两点（证据不足 + 自相矛盾）都收掉？细分口径（按 `$.paths.<path>.<method>` 之后的第一个结构段归类）本身可靠吗？
- **④** 本轮改动有没有引入新缺陷？特别是 `_as_dict` 与 `_extensible_entries` 现在混用于不同层，调用点是否有错配？
- **⑤** 「r1 起生产源与快照一字未动」在本轮之后是否仍成立？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与一句**复核思路**（说明你会怎样独立确认这条，用中性说法）。没有问题的级别请显式写 0 条。

## ⑤ 边界

- 只读；不跑测试、不跑 lefthook、不连 7691/7687/7692、不写任何文件。
- 不评运行时 403/503 行为门（归本批 T10-E），不评 `system.py` 端点语义，不评 `main.py:386-404`（本批 T6-B 地盘）。
- r1–r3 已判定成立的项（`scheme_name` 语义、31→0 的事实、schemathesis 取舍、lefthook glob、W4 逐阶段零记账、「本轮无需重新生成生产源或快照」）无需重复论证，除非本轮改动动摇了它们。

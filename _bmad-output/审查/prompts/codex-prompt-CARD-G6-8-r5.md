# CARD-G6-8 独立审查请求（round-5 · 上限轮）

## 〇 判定口径

D-15：直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0；**上限 5 轮，本轮即第 5 轮**。
按协议 §1，本轮若仍有 HIGH，车道停下交主 session 人审（不自判通过）。

地盘文件：

```
backend/scripts/g68_five_view_contract.py
backend/tests/regression/test_g68_five_view_contract.py
_bmad-output/审查/evidence-g68/scripts/g68_negctl.py
.github/workflows/test.yml（只允许 +1 行）
```

本卡**未改**任何生产代码。

### 最小读取面（写死，勿扩）

1. `git diff dfc1c7e565f28274465a31aac89f0bef1e67b43b 33ede99d -- . ':(exclude)_bmad-output'`
2. `backend/scripts/g68_five_view_contract.py` 全文
3. `backend/tests/regression/test_g68_five_view_contract.py` 全文
4. `_bmad-output/审查/evidence-g68/scripts/g68_negctl.py`
5. `review_app.py`（`_PAGE_TEMPLATE` 与导入段）、`daily_review_pick.py` 的
   `_title` / `build_payload`（只读对照）

## 一 你 r4 的九条，逐条处置

**修 9 条，0 条驳回。**

| 条目 | 修法 |
|---|---|
| **H1** 正则读取未被拦下 | 边界规则在 `r"\bfsrs_due\b"` 上必然失效 ⇒ 改成**裸包含 + 身份白名单**（`_ALLOWED_MARKER_STRINGS` 现只有 `__BUCKET_ORDER_JSON__`），并纳入 `bytes` 字面量。 |
| **H2** 模板豁免允许页面自判 due | **改判据的声称**：`_PAGE_TEMPLATE` 里本就有 `humanizeDue(n.fsrs_due, nowMs)`，同一标识符也能自造判定，区分靠语义而 JS 语义不在 Python AST 射程内。改为把模板里碰 due 的调用点**按身份冻结**（`_TEMPLATE_DUE_CALLSITES`，现状两处）：门**不声称**「JS 是纯消费方」，只声称「这些调用点没变过」。 |
| **M3** 节点锚同步缩减 | 对账 `<=` → **相等**，先显式排除 ineligible 节点（占位 / TestConcept）再比完整分区。 |
| **M4** 参数遮蔽 | `ast.arg` 纳入射程。 |
| **M5** snooze 前提未验证 | 改为**实跑对照**（`snoozed={}` 再跑一次 picker），参照不是被推迟的那块板即当场抛「fixture 前提已漂移」。 |
| **M6** 重复省略号 | 改用 `picker._title(recommended)` **重建后逐字相等**。 |
| **M7** 日志回流冒充失败原因 | 负控锚改绑**结构化判据码** `G68DIFF\|face=…\|field=…`（只有本判据产出）。 |
| **L8** 队列重复项 | 加唯一性检查。 |
| **L9** 函数 docstring 误红 | 豁免扩到**所有** docstring。 |

**你的五组对照输入已全部做成常驻负控段**，连同 r1~r3 的，**32 段 32 合判据、rc=0**。

**本轮整改自己抓出的**：判据消息一改（M6 重建法、M7 结构化码），**十一段绑人话锚的
负控当场变「红了但锚未命中」**——已逐段重锚。这类「红点迁移」在 r3 也发生过一次。

## 二 按重要性排序的问题

0. **矩阵是否仍有「某一面改了却不红」的门未覆盖的路径**？请给对照输入。
1. 身份白名单 `_ALLOWED_MARKER_STRINGS` 只有一条。它会不会**误红**生产文件里
   其它正常字符串？又有没有哪种常见读法的字段名**不以字符串形式**出现、也不是
   属性/裸名/形参/keyword/MatchClass？
2. `_TEMPLATE_DUE_CALLSITES` 按**整行 strip 后**的文本冻结。同一处改动若只动空白或
   把它拆成两行，会不会绕成「集合没变」或「误红」？这条冻结的粒度合适吗？
3. `check_bucket_node_identity` 与 `_EXCLUDED`（ineligible 排除集）都是手写。
   这两处是否可能同步漂移而两边都过？
4. M5 的实跑对照多跑了一次 `build_payload`。这会不会引入非确定性、或让
   「二跑逐字节相等」那条判据失去意义？
5. `picker._title()` 是**私有**函数。判据依赖它是否合适——若它改名/改签名，
   本门是会**误红**还是会**静默失效**？
6. 结构化码 `G68DIFF|face=…|field=…` 只出现在主断言消息里。其余测试（inbox 分叉、
   AST 门、队列检查）的负控仍绑人话锚——它们是否仍有「红在别的原因上」的缝？
7. 负控 runner 的六道自检（锚点预检 / 变异后语法 / 失败块切分 / 捕获段截断 /
   `E ` 行 / sha 对账）里，还有哪一道是一个写坏或写巧的变异段可以走过去的？

## 三 输出格式与边界

- BLOCKER / HIGH / MEDIUM / LOW + `file:line` + 一句复现思路
- 边界：只读、不连库、不跑完整复习链、不评 picker / display_tz 本体设计
- 措辞：一律用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」

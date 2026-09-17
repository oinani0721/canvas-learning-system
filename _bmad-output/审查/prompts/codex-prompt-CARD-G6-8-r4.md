# CARD-G6-8 独立审查请求（round-4）

## 〇 判定口径

D-15：有代码改动的卡多轮审查，直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0；上限 5 轮，
第 5 轮仍有 HIGH 则停下交主 session 人审。本轮是 **round-4**。

**不要用「既有 / BASE 已有」豁免任何问题**。地盘文件：

```
backend/scripts/g68_five_view_contract.py
backend/tests/regression/test_g68_five_view_contract.py
_bmad-output/审查/evidence-g68/scripts/g68_negctl.py
.github/workflows/test.yml（只允许 +1 行）
```

本卡**未改**任何生产代码。

### 最小读取面（写死，勿扩）

1. `git diff ca443a517cb9a2ab45f8a42752cdd5c75c9e01d8 dfc1c7e5 -- . ':(exclude)_bmad-output'`
2. `backend/scripts/g68_five_view_contract.py` 全文
3. `backend/tests/regression/test_g68_five_view_contract.py` 全文
4. `_bmad-output/审查/evidence-g68/scripts/g68_negctl.py`
5. `review_app.py`（`_PAGE_TEMPLATE` 与导入段）、`daily_review_pick.py:29-96,:971-1160`、
   `inbox_preview.py` 的 `main` / `render_md`（只读对照）

## 一 你 r3 的八条，逐条处置

**修 8 条，0 条驳回。**

| 条目 | 处置 | 修法 |
|---|---|---|
| **H1** 普通 due 读取仍未被拦下 | 修 | 字符串判据「相等」→「**词边界**匹配」（`re.search(rf"\b{marker}\b")`）；补 `MatchClass.kwd_attrs` 与 `ast.keyword.arg` 两处**裸 str**。JS 豁免从「长度 ≥400」改成**按身份**（模块 docstring + `_PAGE_TEMPLATE`），名单里的名字不在了门当场抛。⚠ 词边界同时放过 `__BUCKET_ORDER_JSON__`（共享桶序注入占位符，裸包含会把它误报）——该性质已钉成验伪锚。 |
| **H2** 板级锚未覆盖板内节点缺失 | 修 | 新增 `FIXTURE_BUCKET_NODES` + `check_bucket_node_identity`：每个产出 `bucket` 的面报出的 (板, 节点) 集合必须**恰好**等于 fixture 那一份。 |
| **M3** 清单对子集缩减不敏感 | 修 | `<=` → **相等**对账；节点级锚同样对账。 |
| **M4** 队列只剩让位板时退化 | 修 | `require_in_ranked` → `require_exact_boards`（集合相等），期望集合从 picker 的 `due_nodes` 权威明细导出。 |
| **M5** fixture 不能证明 snooze 被消费 | 修 | 推迟一块**本该排首位**的板（`FIXTURE_SNOOZED_BOARD`）+ 一条**独立期望**「它不该在 `ranked` 首位」。 |
| **M6** 任意短前缀被认作点名 | 修 | 未截断 ⇒ 相等；截断 ⇒ 前缀 **且** 标题长度恰好顶到 `picker.TITLE_LIMIT`。 |
| **M7** captured stdout 的 `E ` 行被认作失败原因 | 修 | 失败块先在 `----- Captured … -----` 处截断再找 `E ` 行。 |
| **L8** 正常 FAIL 的诊断在 pytest 层丢失 | 修 | `_run()` 返回 stderr 并贴进主断言失败消息。 |

**你的六组对照输入已全部做成常驻负控段**，连同 r1/r2 的十组，**27 段 27 合判据、rc=0**。

**本轮整改自己又抓出三条**（一并交你复核）：
1. `R3M6` 首跑 rc=0 —— 那条修复**根本没应用上**（`ruff format` 先重排过，字符串替换没匹配）。
2. `RO_BOARD_IDENTITY` / `R2H1_BOTH_MISSING` 的红点随节点身份锚上线而**迁移**，原锚不再命中；
   已改锚并**另加** `MISSING_PATH` 段专守 MISSING 路径。
3. `MISSING_PATH` 首跑 rc=4 —— 变异串把行尾逗号注释掉了。已在 runner 加
   「变异后必须仍是合法 Python」的护栏。

**你 r3 结语里的三点，处置如下**：
- `pytest.fail(..., pytrace=False)` / `--tb=line` 的输出形态：**如实登记为覆盖面上限**，
  本 runner 固定用默认 tb，不在这两种形态下跑。
- inbox 文本锚依赖渲染措辞 ⇒ 措辞一改会 `MISSING` 误红：**接受这个取向**（你也判「漏红风险更大」），
  登记在「本卡未证明什么」。
- 「二跑只约束报告 stdout，不能宣称所有产物确定」：**同意**，已在未证明清单里写明。

## 二 按重要性排序的问题

0. **矩阵是否仍有「某一面改了却不红」的门未覆盖的路径**？请给对照输入。
   本轮新增 词边界 AST / 身份式豁免 / 节点级锚 / 集合相等队列 / 截断形态 / 捕获段截断
   六处，重点看它们的交叉格与退化输入。
1. 节点级锚 `FIXTURE_BUCKET_NODES` 是手写清单 + 与 fixture 对账（`<=`）。
   这个方向够不够？（板级那条已改成相等，节点级这条仍是子集——是否也该相等？）
2. 词边界判据会不会**误红**生产文件里正常的写法？又会不会漏掉某些常见读法？
3. 身份式豁免（`_PAGE_TEMPLATE`）「把 due 读法搬进那个常量」是不是一条未被拦下的输入？
   该常量是页面模板，里面本来就有 JS——这条豁免的边界到底在哪里？
4. `FIXTURE_SNOOZED_BOARD` 那条独立期望依赖「它本该排首位」这个事实。
   若 fixture 的排序因别的改动而变，这条期望会不会静默失效（恒真）？
5. `require_exact_boards` 的期望集合来自 `payload["due_nodes"]` —— 它与 `ranked`
   是否**按实现必然相等**（那样这条判据就是恒真的）？
6. 负控 runner 现在有「锚点预检 / 变异后语法检查 / 失败块截断 / `E ` 行 / sha 对账」
   五道自检，还有哪一道是一个写坏或写巧的变异段可以走过去的？
7. 已登记豁免仍只有 inbox 一条。矩阵新增 `projection_day` 列之后，是否出现了本该登记
   却没登记的**已知**分歧？

## 三 输出格式与边界

- BLOCKER / HIGH / MEDIUM / LOW + `file:line` + 一句复现思路
- 边界：只读、不连库、不跑完整复习链、不评 picker / display_tz 本体设计
- 措辞：一律用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」

# CARD-G6-8 独立审查请求（round-3）

## 〇 判定口径

用户裁定 D-15：有代码改动的卡多轮审查，直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0；
上限 5 轮，第 5 轮仍有 HIGH 则停下交主 session 人审。本轮是 **round-3**。

**不要用「既有 / BASE 已有」豁免任何问题**——只要落在下列地盘文件内就照报：

```
backend/scripts/g68_five_view_contract.py
backend/tests/regression/test_g68_five_view_contract.py
_bmad-output/审查/evidence-g68/scripts/g68_negctl.py
.github/workflows/test.yml（只允许 +1 行）
```

本卡**未改**任何生产代码（review_overview / review_app / 两个 skill 脚本 /
daily_review_pick 全部零改动）。

### 最小读取面（写死，勿扩）

1. `git diff 6e2ee891a5e80d8742fda62cb6086a62af1ff2b4 ca443a51 -- . ':(exclude)_bmad-output'`
2. `backend/scripts/g68_five_view_contract.py` 全文
3. `backend/tests/regression/test_g68_five_view_contract.py` 全文
4. `_bmad-output/审查/evidence-g68/scripts/g68_negctl.py` —— 负控实跑的就是这一份
5. `review_overview.py` 的 `_collect` / `_summarize` / `_gate_buckets` / `_display_*`、
   `daily_review_pick.py:29-96,:971-1160`、`inbox_preview.py` 的 `main` / `render_md` /
   `parse_now` / `_TZ_SHANGHAI`（只读对照）

## 一 你 r2 的十条，逐条处置

**修 10 条，0 条驳回。** 你那句「原版 20/20；六组完整对照副本也各 20/20」再一次是起点。

| 条目 | 处置 | 复现结果与修法 |
|---|---|---|
| **H1** `MISSING` 仍能作为一致值、甚至多数票放行 | 修 | 成立。`MISSING` 现在**每个缺值单独判红**，不参与取值比较、不进多数派。⚠ **按你的措辞改完之后，负控 `R2H1_BOTH_MISSING` 仍然全绿**——因为矩阵的**行索引**本身也是从各面反推的（`set(picker) \| set(overview)`），一块板从所有面同时消失时整行都不存在。已加 `FIXTURE_BOARDS`（fixture 自报的板清单）作为**独立于被测面**的行索引锚，并与 fixture 对账防漂移。 |
| **H2** inbox 日期仍未绑定实际入口的产出 | 修 | 成立。改为跑**真实入口** `main()`（`--vault` 指向 tmp 空仓），从它落盘的 preview 里抠「基准时刻」那一行；`rc != 0` / 无产物 / 抠不到 ⇒ `MISSING`。 |
| **H3** AST 门仍放行普通间接字段读取 | 修（改判据形状） | 成立。⛔ 前两轮都在**按语法形态补特例**，那是开放式判据、永远收敛不了。本轮改判据的**形状**：due 字段名**作为字符串常量出现在 Python 代码的任何位置**即违约，仅放过长度 ≥ 400 的大字符串（页面 JS），并把放过的那几个长度打进返回值。**原理上限如实声明**：运行期拼出来的字段名任何静态判据都拦不住。 |
| **M4** 未钉住产出方身份 | 修 | 成立。改为逐列**写死产出方集合** + 去重后仍需 ≥2 + 必须是已知的面。 |
| **M5** 让位检查未验队列完整性 / fixture 未覆盖 snooze 的消费 | 修 | 成立，两半都成立。加「空队列当场抛」+ `require_in_ranked` 点名要求被推迟/已完成的板必须在队列里；fixture 改为推迟**有到期节点**的「板-脏日期」（原先推迟的「板-未来」确实不进 `ranked`）。 |
| **M6** 通知点名只检查宽松成员关系 | 修 | 成立。改为绑定 picker 自己的 `ranked[0]`，标题缺席也判错。 |
| **M7** 仍能把已通过断言的源码当成失败原因 | 修 | 成立。锚只在失败块里 pytest 的 **`E ` 错误输出行**中找。 |
| **M8** `failure_block()` 会误切同一异常栈 | 修 | 成立。边界改认**连续**下划线（`^_{3,}\s.*\s_{3,}$`）——同一测试内部的帧分隔线是 `_ _ _ _`。 |
| **M9** 恢复散列不一致没有影响退出码 | 修 | 成立。散列失配计入 `bad`。 |
| **L10** 正常 `FAIL` 会丢弃计算期 stdout 诊断 | 修 | 成立。判红时也把缓冲倒进 stderr。 |

**你的五组对照输入已全部做成常驻负控段**（`R2H1_BOTH_MISSING` / `R2H2_INBOX_ENTRY` /
`R2H3_INDIRECT_DUE_READ` / `R2M5_RANKED_EMPTY` / `R2M6_NOTI_WRONG_BOARD`），
连同 r1 的五组，**20 段 20 合判据、rc=0**。

## 二 按重要性排序的问题

0. **矩阵是否仍有「某一面改了却不红」的门未覆盖的路径**？请给对照输入。
   本轮新增了 `FIXTURE_BOARDS` 行索引锚 / inbox 真实入口 / 字符串常量式 AST 判据 /
   `require_in_ranked` 四处，重点看它们的交叉格与退化输入。
1. `FIXTURE_BOARDS` 是手写清单 + 与 fixture 对账（`FIXTURE_BOARDS <= declared`）。
   这个对账方向是否够？有没有一种改法能同时骗过清单与对账？
2. inbox 面现在依赖「preview 里那一行的文本形状」。这个锚是否过于依赖渲染细节
   （换个措辞就变 `MISSING`＝误红）？误红与漏红哪个风险更大？
3. AST 判据改成「字符串常量出现即违约 + 放过 ≥400 的大字符串」之后：
   这条长度豁免是不是一扇新的门（例如把 due 读法藏进一个 400 字符以上的常量）？
4. `check_ranked_yield_partition` 的 `require_in_ranked` 与退化条款组合后，
   是否仍存在让整条判定恒真的输入？
5. `error_lines()` 只认 `E ` 前缀：pytest 在哪些输出形态下真正的失败信息**不带**
   该前缀（从而误红），或者**带**该前缀却不是本次失败（从而漏红）？
6. 已登记豁免的谓词现在只认「固定 +08:00 的当日」。inbox 面改绑真实产物之后，
   这个谓词与产物之间是否出现了新的不一致可能？
7. 确定性：本轮 inbox 面多跑了一个真实入口（会落盘），是否引入了非确定性
   （文件名含时刻？产物残留？）——门里有「二跑逐字节相等」，请判断它是否够。

## 三 输出格式与边界

- BLOCKER / HIGH / MEDIUM / LOW + `file:line` + 一句复现思路
- 边界：只读、不连库、不跑完整复习链、不评 picker / display_tz 本体设计
- 措辞：一律用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」

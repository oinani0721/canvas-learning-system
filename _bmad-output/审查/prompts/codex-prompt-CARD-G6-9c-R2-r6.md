# CARD-G6-9c-R2 独立审查请求（round-6：验证 round-5 整改）

## 〇 为什么有第 6 轮（如实说明）

本批协议写「轮次上限 5」，同时写「审后再改代码 ⇒ 必再送一轮」。round-5 你给出
1 HIGH + 1 MEDIUM + 3 LOW，其中 **H1 是本卡引入的启动失败面**（`TZ` 含非法字节时
`display_tz()` 抛 `UnicodeEncodeError`，而 `review_overview` 的模块级启动校验就调它
⇒ 那类宿主上应用起不来；BASE 在同样输入下只是正常退 UTC）。

车道判断：留着一个会让应用起不来的**新**回归，比让修复多审一轮风险更大。所以修了，
于是「审后改代码必再送一轮」触发。两条规则冲突时按后者处理 —— 不送审等于让未审代码
进合并队列，而 D-15 的本意是「多轮**直到确认没有问题**」。轮次也确实在收敛：
HIGH 数 2 → 2 → 1 → 1 → 1，且**每轮的 HIGH 都是新发现的面**，不是同一条反复不修。

本轮的判定结果会如实登记，包括「超出协议上限」这件事本身，交主 session 裁定。

## 一 背景

D-18 把「今天」钉在机器本地时区；归日靠两份**逐字节同源**的纯 stdlib TZ 解析器
（`scripts/local_tz.py` / `backend/app/core/display_tz.py`，共享定义由
`test_g6_9c_single_tz_source.py` 的两条 `inspect.getsource` 对照门锁住）
+ 桶位门 `review_overview.py::_gate_buckets`。

### 最小读取面

1. `git diff ebe0db58 0e456454 -- . ':(exclude)_bmad-output'` —— **round-5 整改的全部改动**
   （3 个文件、102 插入 / 10 删除；这是本轮的主要审查对象）
2. `git diff 08100483 0e456454 -- . ':(exclude)_bmad-output'` —— 本卡累计改动
   （绑定：BASE `08100483` → r1 `130e2dd2` → r2 `25933d55` → r3 `5a9d835e`
    → r4 `75f5102b` → r5 `ebe0db58` → HEAD **`0e456454`**；最后两个 commit
    只改 `_bmad-output`，代码面等于 `a7e11469`）
3. `parse_posix_tz` 的省略规则分支 + `_PosixTZ._in_dst`（两份副本）
4. `test_g6_9c_single_tz_source.py` 的 `test_display_tz_survives_non_utf8_tz_bytes`（新门）、
   `test_candidate_year_guard_keeps_extreme_epochs_from_raising`（含新增南半球断言）、
   `_OMITTED_RULE_REJECT_CASES`（19 条）

## 二 round-5 各条的处置

| r5 条目 | 处置 |
|---|---|
| **H1** UTF-8 长度检查引入未捕获的编码异常 | **接受并修**：`encode("utf-8")` → `encode("utf-8", "surrogateescape")`。它把代理对编回原字节，数出来正是 C 库实际收到的字节数（实测 `b"<\xff>0BBB"` → 7 字节）。新增门 `test_display_tz_survives_non_utf8_tz_bytes`（两侧引用名各一，用 `os.environb` 设真实字节，`finally` 无条件还原）。负控 ⑱ 段：改回严格 encode ⇒ 该门必红。 |
| **M1** 省略规则分支接受引用名中的 NUL | **接受并修**：控制字符检查加 `or "\x00" in spec`。拒绝表补该用例（并写明它走的是 JSON 自报值那条路，不是环境变量）。负控 ⑲ 段。 |
| **L1** 候选年测试没守住南半球上界 | **接受并修**：原门唯一规格走北半球分支，把 `elif year < 9999` 改成 `else` 整条门仍通过。新增南半球规格 `AAA0BBB,M11.1.0,M3.2.0` + 前提断言（`s > e`）+ `9999-12-15` 时刻；实测该变异抛 `year must be in 1..9999, not 10000`。负控 ⑳ 段。 |
| **L2** 机制说明仍不准确 | **接受并修**，采用你给的表述：**南支终点取 `e(Y+1)`，该端点自己还能滚进 Y+2**，故覆盖 y 年初的季度可能来自名义年 y−2。三轮被证伪的说法（「start 滚年」r3 / 「跨几个年界」r4 / 「两段位移累加」r5）都留在注释里标明已证伪。 |
| **L3** 两处总括与行为不符 | **接受并修**：①「本门只保证不抛」改为「钉两件事：不抛 + 上界不被收得过紧」；② 十九拒例的总括删掉「与 C 库一致」，改为「其中若干串 C 库是**接受**的（`AAA12BBB-12` libc 给 +12h 而两边都退 UTC），那属**既有**支持缺口；本门守的是『本卡没有把它们从退 UTC 变成被接受』」。 |

### 本轮另行加固

负控扩到**二十段**。负控自身也踩到两类失效并已修：变异把 `# NEGCTL-MUTATED` 插进
表达式中间产生 `SyntaxError`（pytest 报 ERROR 而非 FAILED、判据为假）⇒ 改为整行替换；
docstring 里写转义序列的字面拼法会被 Python 展开成真实代理字符，pytest 的 assertion
rewrite 编码整份源码时抛 ⇒ 整个测试文件在**收集期** ERROR ⇒ 改为文字描述。

## 三 已确认为「既有 / 不计本卡新增」的清单（前五轮累计，请确认仍成立）

1. 同偏移换名 + 搬桶（你在 r3 已撤销计数）。
2. 显式规则路径的偏移越界（`AAA24BBB,M3.2.0,M11.1.0` 抛 ValueError）。
3. 真实墙钟越过 datetime 范围时的溢出（`AAA-1` 在公元 9999 年末的 OverflowError）。
4. C 库接受而本实现拒收的反向差异：`AAA0000BBB` / `<>0BBB` / `<A<B>0BBB` /
   256..511 字节的长串 / 引用名内部含换行的串 / 受 Python ±24h 限制而被拒的串。
5. `_POSIX_TZ_RE` 与 `_POSIX_DEFAULT_TRANSITION` 不在源同源门的 shared 名单内。
6. 南半球极值年份（公元 1 年初、9999 年末）的范围支持缺口 —— BASE 同点原本抛
   `year 0 / 10000`。

## 四 请回答的问题（按重要性）

1. **本卡累计 diff（`08100483 → 0e456454`）里还有没有「本卡新增」的错误接受面或异常面？**
   这是本轮唯一的关键问题。请与第三节清单对照，**只报新增的**；既有的请显式标「既有」。
2. r5 的五条整改是否各自真的解决了？特别是 H1 的 `surrogateescape`：
   还有没有别的输入让 `display_tz()` 抛异常（而 BASE 不抛）？
3. 新增的两个门（非 UTF-8 字节 / 南半球上界）是否真能守住对应的防线？
4. 生产代码与测试注释里还有没有与实测不符的断言？

## 五 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给出 `file:line` 与一句复现思路。
没有问题的级别请显式写"无"。**每条必须显式标注「本卡新增」或「既有」** ——
既有的面不计入本卡的 HIGH 计数。

## 六 边界

只读，不修改任何文件；不连接数据库或网络；不评完整归日链路端到端行为；
不评 `_gate_buckets` 中与 `ref_tz` 无关的其余判据；不评本卡地盘外的文件。

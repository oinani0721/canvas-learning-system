# CARD-G6-9c-R2 独立审查请求（round-7：验证 round-6 整改）

## 〇 为什么还有第 7 轮

round-6 你指出：我在 r5 用 `surrogateescape` 修掉的「启动失败」，其实只是把失败
**挪到了响应出口** —— `.key` 带着代理字符进 `JSONResponse` 时再炸一次。那是一条
**我自己引入的** HIGH，闭环必须验证，否则等于把一个已知的新回归留进合并队列。

本轮是第 7 轮，早已超出协议的 5 轮上限。这个事实会如实登记交主 session 裁定。
判定请照常严格 —— 不要因为轮次多了就放宽。

## 一 背景

D-18 把「今天」钉在机器本地时区；归日靠两份**逐字节同源**的纯 stdlib TZ 解析器
（`scripts/local_tz.py` / `backend/app/core/display_tz.py`）+ 桶位门
`review_overview.py::_gate_buckets`。

### 最小读取面

1. `git diff 0e456454 cb1d6e9f -- . ':(exclude)_bmad-output'` —— **round-6 整改的全部改动**
   （3 文件、61 插入 / 19 删除；本轮主要审查对象）
2. `git diff 08100483 cb1d6e9f -- . ':(exclude)_bmad-output'` —— 本卡累计改动
   （绑定链：`08100483` → `130e2dd2` → `25933d55` → `5a9d835e` → `75f5102b`
    → `ebe0db58` → `a7e11469` → HEAD **`cb1d6e9f`**）
3. `parse_posix_tz` 开头的编码/长度校验段（两份副本）
4. `test_g6_9c_single_tz_source.py::test_display_tz_survives_non_utf8_tz_bytes`

## 二 round-6 两条的处置

| r6 条目 | 处置 |
|---|---|
| **HIGH** 代理字符进响应、序列化失败 | **接受并修**。不再用 `surrogateescape` 放行，改为严格 `spec.encode("utf-8")` + `except UnicodeEncodeError: return None` —— 不可严格编码的规格串**整个不接受** ⇒ `display_tz()` 退 UTC ⇒ `.key` 恒可序列化，与 BASE 逐点同行为（实测 `b"<\xff>0BBB"` 与 `b"AAA0<\xff>"` 两种输入下 BASE/HEAD 的 key 都是 `'UTC'`，`json.dumps(...,ensure_ascii=False).encode("utf-8")` 与真实 `JSONResponse` 都成功）。三轮的修法演进都写进注释：r4 严格 encode 直接量长度⇒抛（启动失败）／r5 surrogateescape 放行⇒响应失败／现在不接受⇒两处都不炸。 |
| **LOW** parametrize 注释不实 | **接受并修**。实测确认你是对的：直接参数化两个非 UTF-8 bytes，Python 3.14.4 + pytest 9.0.2 下 `2 passed`、rc=0。注释改为「用标签只是为了 id 可读」，并写明真正让文件收集期 ERROR 的是 docstring 里的转义序列字面拼法（`compile()` 即可复现，不需要 pytest rewrite —— 这点也按你说的更正了）。 |

### 门同步加强到出口

原门只验「`display_tz()` 不抛」——**那正是 r5 满足了却仍有 HIGH 的那一条**。
现在它还钉返回值的 `.key` 必须过 `json.dumps(..., ensure_ascii=False).encode("utf-8")`。
⚠️ 判据特意打在**编码到字节**那一步：`json.dumps` 默认 `ensure_ascii=True` 会把代理
字符转义成 `\udcff` 而**不抛**，用它做判据是假绿。
负控 ⑳ 之外新增的 ⑱ 段绑该出口（把 except 分支换回 `surrogateescape` ⇒ 序列化断言必红）。

## 三 已确认为「既有 / 不计本卡新增」的清单（请确认仍成立）

1. 同偏移换名 + 搬桶（你在 r3 撤销计数）。
2. 显式规则路径的偏移越界。
3. 真实墙钟越过 datetime 范围时的溢出。
4. C 库接受而本实现拒收的反向差异（`AAA0000BBB` / `<>0BBB` / `<A<B>0BBB` /
   256..511 字节长串 / 引用名内部含换行 / 受 Python ±24h 限制而被拒的串 /
   **本轮新增的：含非法字节因而不可严格 UTF-8 编码的串** —— 后者 BASE 同样退 UTC）。
5. `_POSIX_TZ_RE` 与 `_POSIX_DEFAULT_TRANSITION` 不在源同源门的 shared 名单内。
6. 南半球极值年份的范围支持缺口。

## 四 请回答的问题

1. **r6 的两条是否真的解决了？** 特别是 HIGH：还有没有输入让 `display_tz()` 抛、
   或让它的返回值在**任何**出口（响应序列化、日志、`.isoformat()`、`str()`）失败，
   而 BASE 不失败？
2. **这次的修法有没有又把问题挪到别处？** 前两轮各挪了一次（抛→启动失败、
   放行→响应失败）。请专门找第三个落点。
3. 本卡累计 diff（`08100483 → cb1d6e9f`）里还有没有其它「本卡新增」的错误接受面
   或异常面？与第三节清单对照，只报新增的。
4. 加强后的门是否真能守住出口？判据打在 `.encode("utf-8")` 而不是 `json.dumps` 本身，
   这个选择对吗？
5. 生产代码与测试注释里还有没有与实测不符的断言？

## 五 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给出 `file:line` 与一句复现思路。
没有问题的级别请显式写"无"。**每条必须显式标注「本卡新增」或「既有」。**

## 六 边界

只读，不修改任何文件；不连接数据库或网络；不评完整归日链路端到端行为；
不评 `_gate_buckets` 中与 `ref_tz` 无关的其余判据；不评本卡地盘外的文件。

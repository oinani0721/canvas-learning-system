> 批次: BATCH-2026-09-11-第十四批 · 车道 T3 · 卡 CARD-G6-9c-R2 round-9
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R2-r9.md)"`
> 审查绑定: `08100483 → 58b0b635`（结束时该轮所审的五个文件仍逐字等于绑定末端）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**本轮未达到“完全无问题”：确认 7 项 MEDIUM、4 项 LOW。**

审查绑定 `58b0b635bc63d64eb97334a02259e904297ef618`，五个文件均与该提交一致。以下不豁免既有问题。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

以下 M1–M5 统一用 **`2026-07-01T23:30:00Z`** 复现。

### M1．控制字符校验上移，新增合法串误拒

位置：`scripts/local_tz.py:153`；`backend/app/core/display_tz.py:152`。

复现：`TZ='<A\nAA>-1'`，或 `AAA0<B\nBB>,M3.2.0,M11.1.0`。

**libc、r8 均给 `07-02 00:30 +01:00`；HEAD 退 UTC，归 `07-01`。** 引用名内部换行可以安全地经过 JSON 转义，不能与尾部换行、NUL 一并认定为必须拒绝。

### M2．255 字节整串限制上移，新增合法长名误拒

位置：`scripts/local_tz.py:182`；`backend/app/core/display_tz.py:181`。

复现：`TZ = "A"*254 + "-1"`，恰好 256 字节。

**libc、r8 均归 `07-02`；HEAD 退 UTC，归 `07-01`。** 该串可正常编码，也没有超过本机 libc 的名字容量。这是已登记差值限制之外的新增过度拒绝。

### M3．缺失标准偏移的显式规则分支仍然漏检

位置：`scripts/local_tz.py:210,259`；`backend/app/core/display_tz.py:209,258`。

复现：`<AAA><BBB>,M3.2.0,M11.1.0`。

libc 拒收退 UTC；HEAD 把缺失偏移当作 `0`，再应用 DST，归次日。`if not g["std_off"]` **仍只保护省略规则分支**。

### M4．无 DST 分支提前返回，忽略非法规则

位置：`scripts/local_tz.py:215–216`；`backend/app/core/display_tz.py:214–215`。

复现：`AAA-1,J0,J0`。

libc 拒收退 UTC；HEAD 在调用 `_parse_rule` 前便返回固定 `+01:00`，归次日。规则随串进入正则，却没有被验证。

### M5．切换规则的数字与时刻范围仍未校验完整

位置：`scripts/local_tz.py:88–104`；`backend/app/core/display_tz.py:87–103`。

复现任一：

```text
AAA0BBB,M3.2.0/2:60,M11.1.0
AAA0BBB,M3.2.0/168,M11.1.0
AAA0BBB,M３.2.0,M11.1.0
AAA0BBB,M3.2.0/２,M11.1.0
```

libc 均退 UTC；HEAD 均应用 `+01:00`，归次日。上移的 ASCII、字段范围检查只覆盖 **std/dst 偏移**，没有覆盖规则日期与切换时刻。

M3–M5 还通过原 `_gate_buckets` 函数进行了内存复现：使用这些自报时区时，门能够接受与 libc 归日不符的 `future` 行。

### M6．长度限制位于正则之后，长坏串触发二次耗时

位置：`scripts/local_tz.py:143`；`backend/app/core/display_tz.py:142`。

复现：调用 `parse_posix_tz("A"*n + "!")`。

本机实测：

| n | 耗时 |
|---:|---:|
| 1,000 | 0.028 秒 |
| 2,000 | 0.115 秒 |
| 4,000 | 0.475 秒 |
| 8,000 | 1.875 秒 |

这些输入最终都返回 `None`，但正则的回溯已经发生；后面的 255 字节限制没有保护这条路径。盘上 `producer_tz` 也能进入这里。

### M7．新增偏移门未覆盖其名称声称的全部分支

位置：`backend/tests/regression/test_g6_9c_single_tz_source.py:736–746`。

同时对两份副本进行内存变异后，**148 个原解析器参数格仍全部通过**：

- std 量级检查仅在“有 DST”时执行：`AAA24` 随后在 `isoformat()` 抛异常。
- dst／差值检查仅在“省略规则”时执行：`AAA23BBB24,M3.2.0,M11.1.0` 随后在 `isoformat()` 抛异常；`AAA12BBB-12,…` 夏季在 `dst()` 抛异常。

因此现有门尚不能防住“校验又被移回局部分支”。

## LOW

### L1．9999 年末的南半球 DST 季被整体跳过

位置：`scripts/local_tz.py:369`；`backend/app/core/display_tz.py:368`。

复现：`AAA0BBB,M10.1.0,M3.1.0`，时刻 `9999-12-01T23:30Z`。libc 给 `12-02 00:30 +01:00`；HEAD 给 `12-01 23:30 +00:00`。当前墙钟仍可表示，但 `year < 9999` 已把整段季度排除了。

### L2．两侧偏移相等时，冬季名称错误

位置：`scripts/local_tz.py:411`；`backend/app/core/display_tz.py:410`。

复现：`AAA0BBB0,M3.2.0,M11.1.0`，时刻 `2026-01-01T00:30Z`。libc 名称为 `AAA`，HEAD 的 `tzname()` 为 `BBB`。偏移相等不能用来判定 DST 身份；此项不影响归日。

### L3．多处注释和用例说明没有随实现更新

主要位置：

- `scripts/local_tz.py:151,245,257`，backend 对应减一：仍称偏移检查未上移、显式分支不动。
- `backend/tests/regression/test_g6_9c_single_tz_source.py:686–688,805–806`：仍称其他分支未修。
- 同测试文件 `:1177,1221–1222,1279`：仍要求退回 `generated_at` 固定偏移，实际使用自报完整规则。
- 同测试文件 `:739`：声明 `AAA0` 是正控，但它被参数过滤，也不在下方接受表中。
- `backend/app/api/v1/endpoints/review_overview.py:564`：仍把本实现接受的差值上界写成约 ±83 天，现行检查已限制为严格小于 24 小时。

复现思路：对照共用校验运行位置、实际参数展开及当前 `ref_tz` 构造即可证伪。

### L4．“libc 在 tzset 时拒绝 ±24h”的归因错误

位置：`scripts/local_tz.py:224–225`；`backend/app/core/display_tz.py:223–224`；回归测试 `:737`。

复现：设置 `TZ=AAA24BBB` 后，**`time.tzset()` 成功**；冬季 `time.localtime()` 正常返回 −86400 秒偏移。抛异常的是后续 Python `datetime.astimezone()` 的时区表示边界。

拒绝这些串可以解释为保证 Python 全年可表示，但不能说成 libc 同样拒收。`AAA0:60BBB` 退 UTC 的描述则已确认正确。

## 对其余问题的结论

**两项既有修复：**代理字符和偏移量级检查确实覆盖了原来的三条分支；本次没有复现同类异常被转移到其他出口。但 M1、M2 是校验上移带来的新行为退化。

**差值 ≥24h 的取舍：**作为避免运行时异常的降级有依据，但会损失正确归日，且不是唯一方案。可以对这一特殊族让 `dst()` 返回 `None`，保留真实 `utcoffset()` 和自定义 `fromutc()`。内存探针中，冬夏及切换点的偏移、UTC 往返、序列化均正常；代价是 DST 差值未知、`tm_isdst=-1`。采用前须核查调用方是否接受 `None`，这部分属于**地盘外·移交**，本轮未评。

**新增门是否独立：**现有样本确实承重。分别删除 std 量级、分钟检查，以及把严格编码改为 `surrogateescape`，都会红在对应断言；问题在覆盖不足，见 M7。

**r8 LOW-1 端点：准确。**2007–2037 共 186 个边界秒及逐小时复核支持：

- 普通年份：`[01-01T00:00Z, 01-07T22:00Z)`。
- 闰年后一年：`[01-01T00:00Z, 01-06T22:00Z)`。

右端前一秒红、端点本身绿；分别对应 166／142 小时。

**验证边界：**只读执行原解析器测试的 148 个参数格及独立探针；未运行完整 pytest、未连接数据库或网络、未评完整归日链路。未修改任何文件。



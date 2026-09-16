> 批次: BATCH-2026-09-11-第十四批 · 车道 T3 · 卡 CARD-G6-9c-R2 round-10
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R2-r10.md)"`
> 审查绑定: `08100483 → 630f784a`（结束时该轮所审的五个文件仍逐字等于绑定末端）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

## 结论

**本轮不能封卡：仍有 HIGH，以及接受域、测试门和注释问题。**

审查绑定 `630f784ac7b89d0c1487d1698adcfad15ff72832`；结束时五个文件仍逐字等于该提交。全程只读、无网络或数据库连接。

以下位置简写：

| 简写 | 文件 |
|---|---|
| S | [scripts/local_tz.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/scripts/local_tz.py) |
| B | [backend/app/core/display_tz.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/core/display_tz.py) |
| R | [backend/tests/regression/test_g6_9c_single_tz_source.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g6_9c_single_tz_source.py) |
| O | [backend/app/api/v1/endpoints/review_overview.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/app/api/v1/endpoints/review_overview.py) |

## BLOCKER

无。

## HIGH

### H1．没有 DST 名、但附有合法规则时，错误地返回固定偏移

**位置：S:233–234；B:232–233。**

`AAA-1,M3.2.0,M11.1.0` 两边都接受，但实现因为 `g["dst"] is None` 提前返回无 DST 的时区；macOS 实际会实行夏令时。

**复现：**在 `2026-07-01T22:30Z` 转换：

| 本实现 | macOS libc |
|---|---|
| `2026-07-01 23:30 +01:00` | `2026-07-02 00:30 +02:00` |

`J60,J300`、`60,300` 同样复现。遗漏维度是**无 DST 名 × 有合法规则**；现有“无 DST + 非法规则必须拒”没有覆盖这一侧。

## MEDIUM

| 编号 | 位置 | 问题与一句复现 |
|---|---|---|
| M1 | **S:49–56、158；B:48–55、157** | **名字词法窄于 libc，尾空白也被错误概括。** `A1`、`<>1`、`<A<B>1` 均 libc 收、实现拒；`AAA-1BBB\n` 也被 libc 接受，只有引用名闭合后或规则后的尾 LF 才拒，故“带 dst 名只要尾空白就退 UTC”不成立。 |
| M2 | **S:50–56；B:49–55** | **把数字位宽当成数值范围，漏掉前导零维度。** `AAA0001`、`AAA1:000`、`AAA1BBB,M3.02.0,M11.1.0`、`AAA1BBB,J0001,J0200` 均 libc 收、实现拒。 |
| M3 | **R:751、788–795** | **22 例接受域表已有错误答案，测试仍绿。** 原表、原测试函数在内存执行 **22/22 通过**；再查 libc，`AAA-1\n` 实际被接受，冬季 `+01:00`、夏季 `+02:00`，表中却写 `False`；测试没有调用 libc 核验。 |
| M4 | **S:439；B:438** | **`lstrip(":")` 误收多重冒号。** `TZ=::Asia/Shanghai` 在 libc 下为 UTC，实现却剥成上海并返回 `+08:00`。 |
| M5 | **S:439–447；B:438–446** | **合法系统 tzfile 路径被当成垃圾 TZ。** `TZ=/usr/share/zoneinfo/Asia/Shanghai` 及其前导冒号形式，libc 为 `+08:00`，实现退 UTC；`./Asia/Shanghai`、`Asia//Shanghai` 同形。 |
| M6 | **S:176–179；B:175–178** | **非 UTF-8 字节的主动收紧仍违反双向接受域口径。** `os.environb[b"TZ"]=b"AAA-1<\xff>"` 后，libc 夏季为 `+02:00`，实现退 UTC；例如 `2026-07-01T22:30Z` 两边归日不同。 |
| M7 | **S:225、241；B:224、240；R:847** | **偏移可表示性限制仍造成接受域差异。** `AAA12BBB-12,M3.2.0,M11.1.0` 被实现拒绝，但 libc 冬季正常给 `−12h`；另 `AAA24BBB,…` 的 `tzset()` 实际成功，R:847 所称“C 库直接报错”错误。 |
| M8 | **S:134–141、248–258、328–330；B 对应行减一** | **披露过的年份差异仍未满足本轮口径。** `CET-1CEST` 在 `2038-07-01T22:30Z`，实现归 **7 月 2 日**、libc 归 **7 月 1 日**；2006 年旧规则及 1970 年前显式规则也有实测差异。 |
| M9 | **R:116–124** | **同源门遗漏两个关键模块常量。** 只把 scripts 的 `_POSIX_TZ_RE` 中 `\d{1,3}` 改为 `\d{1,4}`，即可让 scripts 收 `AAA0001`、backend 拒；源码门仍通过，选定的 **199 个原测试参数格**也全通过。 |

M6、M7、M8 都是已知或主动选择的限制，**本轮仍照报，没有用 BASE 或既有状态豁免**。

M9 另有方向性证据：缺省切换常量变成 `7199` 秒时，上述 199 格全绿；变成 `7201` 秒时有 5 格红。现有整分钟探针漏掉了**提前一秒**这一侧。这里没有声称整份 pytest 全绿。

## LOW

| 编号 | 位置 | 问题与一句复现 |
|---|---|---|
| L1 | **S:213–214；B:212–213** | **“按字符算这两条都会判反”错误。** `AAA0<A×504中>` 按字节和为 512、按字符和为 510，两者都接受；只有 `中×170` 那条发生误收。 |
| L2 | **R:686–688、916、1169–1171** | **旧作用域声明没有更新。** 当前无 DST、显式规则两支的非 UTF-8 都已退 UTC；仍称“未修／不动显式规则”错误，而“绑定 POSIX、不跟 macOS 短名”也与本轮判据冲突。 |
| L3 | **R:1251、1296、1340–1341、1398** | **注释仍指导退回固定偏移。** 纽约春季 `generated_at=2026-03-08T00:30-05:00`、到期 `2026-03-09T04:30Z`，完整规则判 future，照注释固定 `−05:00` 会误判 due_today。 |
| L4 | **O:564；R:1521** | **接受域边界论证仍沿用约 ±83 天。** 当前 parser 在 DST 差恰好 24h 时已经拒绝；旧正则位宽给出的宽松上界已不能代表当前可达范围。 |
| L5 | **R:597、601–602** | **极值年份说明过时。** 当前南半球已经保留 9999 年季度；显式规则在 9999 年也能由 libc 实行 DST，不能概括为“区间外 C 库不套 POSIX 规则”。 |
| L6 | **S:397–406；B:396–405** | **`tzname()` 与 libc 的缩写清理行为不同。** `<A\nAA>-1` 返回原换行名，libc 返回 `A_AA`；`<中>-1` 返回 `中`，libc 返回 `___`；256 字节缩写在 libc 中还会截至 255 字节。 |
| L7 | **S:408–422；B:407–421** | **`fromutc()` 缺少 tzinfo 身份校验。** 给它传 naive datetime 或 `tzinfo=timezone.utc` 的 datetime，当前静默转换；本机 stdlib `tzinfo`／`ZoneInfo.fromutc()` 均按协议抛 `ValueError`。 |

## 对名字和式、③、①的直接回答

### 名字和式：当前非空名字子域正确，完整 libc 域仍有例外

`_strip_name` 剥掉外围尖括号，再按**原始 UTF-8 字节**计数，与当前非空名字域的 libc 边界一致。不能先按 libc 的缩写清理或截断结果计数。

但 **DST 名为空**时，不能再加第二个 NUL：

```python
"<" + "A" * 511 + ">-1<>,M3.2.0,M11.1.0"
```

libc 接受且实行 DST；机械套用 `511 + 0 + 2` 却会误拒。当前实现先由正则拒绝空名，因此尚未走到⑦。

独立子进程边界检查还确认：**同名、异名、共享后缀没有缓存复用例外**。这里真正遗漏的是空 DST 名。

### ③：最终结论成立

当前正则只有 `<[^<>]+>` 能吞 NUL；没有第三类词法位置。逐位置插入检查中，20 个成功匹配位置全部位于引用名内部；仅去掉③后全部被接受。

### ①：对当前实现确实只是性能防线

当前其余约束下，合法串最多 **570 字符**，小于 1024。删除①后，4000 字符坏串仍返回 `None`，本次约耗 **0.587 秒**。

但 libc 接受超过 1024 字符的合法前导零串。**修复 M2 后必须重新审计①**，不能把“当前不改变接受域”推广到修改后的语法。

## 地盘外·移交

**MEDIUM：本轮负控证据尚不能独立复验。**

- [最新日志:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g69cr2/g69cr2-negctl-20260916T001954.txt:22) 确有 **23 RED + 1 GREEN**，但没有逐段 nodeid、失败正文或 J60/J365 文本命中证据。
- [保存的 runner:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g69cr2/scripts/negctl.py:82) 仍是 **22 段旧版**；只读提取锚点后发现 **10 个“文件／锚点”对零命中**，按其预检会失败。
- 日志只保存三生产文件的 16 位 SHA 前缀，没有完整 HEAD、测试文件及实际 runner 的绑定。

**这证明证据不足，不证明“23 RED”虚假。**

本次未发现 `_gate_buckets` 的 `ref_tz` 逻辑或单位测试文件中的其他独立缺陷；桶位门仍会继承上述解析器偏差。未执行落盘 fixture、数据库测试或完整归日链路 E2E。

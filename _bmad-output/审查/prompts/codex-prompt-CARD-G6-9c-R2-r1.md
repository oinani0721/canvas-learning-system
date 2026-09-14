# CARD-G6-9c-R2 独立审查请求（round-1）

## 一 背景

用户裁定 D-18：复习系统里的「今天」= 用户当前所在地 = 机器本地时区，不写死 UTC。
归日依赖三处：

- 两份**逐字节同源**的纯 stdlib TZ 解析器：`scripts/local_tz.py`（launchd / CLI 侧，
  不能 import backend）与 `backend/app/core/display_tz.py`（backend 侧）。二者的共享定义
  由 `backend/tests/regression/test_g6_9c_single_tz_source.py` 的两条源码级对照门锁住
  （`test_two_copies_share_identical_function_body` / `..._localtz_class`，用
  `inspect.getsource` 逐行比对 `_PosixTZ` / `parse_posix_tz` / `_posix_offset_seconds` /
  `_parse_rule` / `_rule_epoch` / `_parse_hms` / `_strip_name` 七个定义）。
- 复习总览的桶位门 `backend/app/api/v1/endpoints/review_overview.py::_gate_buckets`
  （约 :424-700），它按投影自带的 `generated_at` 重算生产器的五桶判据。

上一轮（CARD-G6-9c round-5）留下 3 条未关闭 HIGH，本卡逐条收口：
HIGH-1 `_PosixTZ._in_dst` 的候选年窗口漏格；HIGH-new `dst` 有名但省略切换规则被整体
退回 UTC；HIGH-2 旧投影的固定偏移回退存在与误拒完全对称的**误放行**。

### 最小读取面（只读这些，不要扩散到别处）

1. `git diff 08100483 130e2dd2 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
   （审查绑定：BASE `08100483` → HEAD `130e2dd2`）
2. `scripts/local_tz.py` 与 `backend/app/core/display_tz.py` 的
   `parse_posix_tz` / `_PosixTZ` 类体 / `display_tz` 三段全文
3. `backend/app/api/v1/endpoints/review_overview.py` 的 `_gate_buckets` 全函数，
   以及模块级常量 `_FIXED_OFFSET_DST_SPAN`
4. `backend/tests/regression/test_g6_9c_single_tz_source.py` 里本卡新增/改动的段：
   `_POSIX_TZ_VALUES` / `_DST_PROBE_INSTANTS` / `_CROSS_YEAR_WINDOW_CASES` /
   `_OMITTED_RULE_CASES` / `_OMITTED_RULE_TRANSITION_SCANS` 五张表及其参数化测试，
   加上 `test_bucket_gate_rejects_wrong_bucket_and_forged_display_tz` 与
   `test_bucket_gate_rejects_wrong_buckets_even_when_display_tz_is_absent`

## 二 作者自述，请独立核对

1. **HIGH-1**：`_in_dst` 的候选名义年从 `(y-1, y, y+1)` 扩到 `(y-2, y-1, y, y+1)`。
   自述的界：`_rule_epoch` 相对该年元旦 ∈ [0, 406.7 天]，`|偏移| ≤ 41.7 天`（本文件正则
   对偏移与切换时刻都允许到 `999:99:99`），故能包住 ts 的名义年只可能落在 [y-2, y+1]。
   自述实测：4088 个规格 × 873 个探针时刻与 C 库逐点对照，`(y-1,y,y+1)` 有 17 个规格
   共 1274 点分歧，扩到 y-2 后分歧 0，再扩到 `(y-3 … y+2)` 零增量。
   自述滚年有三条独立来源（平年裸 `n=365` / `Jn`·裸 n 叠 `/N` / `Mm.w.d` 年末叠 `/N`），
   三条各有一条回归用例。
2. **HIGH-new**：`parse_posix_tz` 在「`dst` 有名但 `start`/`end` 整段缺席」时不再
   `return None`（那会让 `display_tz()` 整串退回 `ZoneInfo("UTC")`），改为按 C 库
   `tzset(3)` 的 `posixrules` 补默认规则：start 用 `M3.2.0` 的 POSIX 缺省时刻（当地
   标准时 02:00）；end **不写死** `M11.1.0` 的缺省 02:00，而是按
   `3600 + dst_off − std_off` 现算。自述理由：C 库把秋季回拨钉在当地**标准**时 01:00，
   而 POSIX 的 `/时刻` 语义指切换**前**生效的那一侧（end 之前生效的是夏令侧），两者只在
   夏令时差恰为 +1 小时时重合。自述实测：写死 02:00 时 `IST-1GMT0`(Δ=−1h) 3720 分钟、
   `ABC-1DEF-5`(Δ=+4h) 5580、`NZST-12NZDT-13:30`(Δ=+1.5h) 930、`AAA5BBB7`(Δ=−2h) 5580
   与 C 库不符（2007..2037 秋季回拨窗逐分钟，156 万点），现算后四者归零。
   自述的对齐作用域：**2007..2037**；≤2006 C 库用 `posixrules` 整张历史转换表、
   ≥2038 它的 32 位表不外推直接丢 DST，两段不作为对齐目标。
3. **HIGH-2**：`_gate_buckets` 的 `ref_tz is None` 回退仍取 `generated_at` 自带的固定
   偏移（参照日在那一刻是准的），但非到期两桶的归桶判据要在 `±_FIXED_OFFSET_DST_SPAN`
   （2 小时）内复算，桶名随之翻转即判该条目不可判、按 corrupt 降级。自述理由：误拒与
   误放行出自同一个偏差、只会一起落在带内；只探两个端点是因为 `_display_day` 的日期随
   偏移单调不减、`ref_day` 固定，故二元判定在区间内单调。
   自述**未采用**卡文预设的「缺 `display_tz` 一律判 corrupt」：因为 `display_tz: null`
   不是历史遗留，而是现役生产器 `daily_review_pick` 在**末档宿主**（`local_tz.display_tz()`
   落到无 `.key` 的固定偏移兜底）上的正常产出；一律判 corrupt 会让那类宿主的复习清单
   整页只剩错误码，且手动重建按钮恒 503，无法自愈。
4. **两份副本逐字节同源**：共享段（模块 docstring 之后的全部）sha256 一致。
5. **门⑦ 样本**：`_POSIX_TZ_VALUES` 11→14、`_DST_PROBE_INSTANTS` 8→11（新增 3 个
   非 2026 时刻），组合数 176→308。自述每个新样本都做过负控。
6. **负控七段**：每段只拆一层防线，EXIT trap 无条件还原，三个被改文件的
   `shasum -a 256` 跑前/跑后逐字相同；七段全部红在指定断言消息上；⑥⑦ 用区分性变异
   证明两个闰年时刻各自不可删（互斥判定）。
7. `pyright app` 保持 `0 errors`；`tests/unit` 目录级 nodeid 与既有 64 条红基线 diff 为空；
   5 个改动文件 `ruff check` 与 `ruff format --check` 均 rc=0。
8. 自述本卡已自查并更正过一处失实注释：初版写「裸 `n=365` 是 `_rule_epoch` 唯一会溢出
   名义年的写法」，实测 `Jn` 叠 `/N` 与纯 `Mm.w.d` 年末叠 `/N` 同样滚年，已改。

## 三 请按重要性排序回答的问题

1. HIGH-1 的新候选窗 `(y-2, y-1, y, y+1)` 是否仍漏某类跨年/极区时刻？自述的界推导
   （406.7 天 / 41.7 天）是否与本文件正则的实际取值域相符？有没有**未被拦下的输入**
   能在新窗口下仍然错日？
2. HIGH-new 的 `3600 + dst_off − std_off` 是否对所有夏令时差都正确？在非 macOS/glibc
   平台、或 `posixrules` 缺席的宿主上，这个分支会退化成什么？自述的 2007..2037 作用域
   声明是否诚实（区间外的行为有没有被写成"已对齐"）？`secs` 取负值时
   `_rule_epoch` 的算术是否仍然正确？
3. HIGH-2 的 ±2 小时敏感性复算是否把合法旧投影**过度**判 corrupt？带宽取 2 小时的依据
   （覆盖现实中全部 DST 跨度）是否站得住？只探两个端点的单调性论证是否成立 ——
   有没有**对照输入**能让桶名在区间内部翻转而两端同侧？
4. 源同源门是否真覆盖本卡改动的每个函数？本卡有没有引入落在那七个名字之外的模块级
   定义（那会成为门抓不到的漂移面）？
5. 门⑦ 的新样本是否只是装饰、压不到修复面？负控七段有没有哪一段的红其实来自别的原因
   （即"门未覆盖的路径"被误记成击杀）？新增的三个非 2026 样本，年份约束（必须落在
   2007..2037）在注释里写清楚了吗？
6. 生产代码与测试注释里还有没有**与实测不符**的断言（同第二节第 8 条那一类）？

## 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给出 `file:line` 与一句复现思路。
没有问题的级别请显式写"无"。

## 五 边界

只读，不修改任何文件；不连接数据库或网络；不评完整归日链路的端到端行为
（pick → runner → 总览 → 推送）；不评 `_gate_buckets` 中与固定偏移回退无关的其余判据；
不评本卡地盘外的文件（`review_app.py` / `daily_review_pick.py` / `test_vault_lint.py` 等）。

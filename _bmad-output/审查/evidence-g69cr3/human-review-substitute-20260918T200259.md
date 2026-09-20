# 主 session 人审替代（Codex 配额耗尽，协议 §2.1）@ 2026-09-18T20:02:59

> 绑定：审 SHA `967cf4cf`（代码定稿 `c6a7f446`；`git diff --stat c6a7f446 HEAD -- . ':(exclude)_bmad-output'` = 空）
> 依据：Codex r1 两次均 0 字节（存档 `codex-r1-quota-exhausted-*.txt`）⇒ 协议 §2.1「不等配额，人审替代」
> 口径：逐条回答 prompt §③ 的 8 个问题，**每条都跑判据**，不采信自述。

---

## ⓪ 解析器接受域是否仍与 libc 有可观测分歧？（重点：std_off 必填引入的新路径）

**问题实质**：原先「正则匹配成功 → 校验层 ⑥ 判空 std_off → return None」与现在「正则根本不匹配
→ `if not m: return None`」是两条不同的路，必须证明它们在**所有**输入上返回值相同。

**判据**：穷举「缺 std_off」的全部形态（名字 16 种 × dst 5 种 × 规则 4 种，去掉含 ASCII 数字的）
= **320 条**，逐条问 `parse_posix_tz`。

**结果**：被接受 **0 条**。两条路返回值一致，都是 `None`。

另有两份更宽的证据（本卡早前已落档）：
- `g69cr3-re-equiv-*.txt`：**314,702 条**样本上，新旧解析器的**返回语义**（None / key + 冬夏偏移 + tzname）分歧 **0**；
- 3.9.6 与 3.14.4 两解释器对 93,397 条样本的正则判定**指纹逐字节相同**。

**残留分歧**：`UTC0` / `<UTC>0` 这一族与「解析失败退 UTC」在观测上不可分（R2 已声明，§六.1）。

---

## ① 计时门是否真能抓回溯？卡文门限的更正是否成立？

**卡文原判据 `t(808)/t(202) ≤ 3` 对真正线性的实现也会红** —— 长度从 202 到 808 是 **4 倍**，
线性耗时本来就该 ≈4。本卡基线实测（min-of-5）**3.55**，落在门限外侧。

**本卡改用的三层判据**（全部实测，见 §五.3 表）：

| 判据 | 基线（线性） | `std_off` 改回可选（平方） | 能否区分 |
|---|---|---|---|
| `t(808)/t(202) ≤ 3`（卡文原文） | 3.55 ⛔ 误红 | 13.49 | ⛔ 门限比线性值还紧 |
| 相邻比 ≤ 3 | 1.75~1.92 ✓ | 3.46~3.97 ⛔ | ✓ 但平方侧余量仅 15% |
| **n=3232 ≤ 0.05 s** | 0.000094 s ✓ | 0.527 s ⛔ | ✓ **余量 530× / 超标 10×** |
| n=808 ≤ 0.05 s | 0.000028 s ✓ | 0.035 s ✓ | ⛔ 抓不住（平方态仍在门内） |

**「改回可选是否真红」实测**：negctl 段 `H3QUANT` 两副本都红，消息为
`[arabic] n=3232 耗时 0.530174s > 0.05s —— 分词不是线性`（backend）/ `0.536153s`（scripts）。

⇒ **更正成立**；计时门确实能抓回溯，且抓它的是 n=3232 那条绝对门，不是比值。

---

## ② negctl 的空操作预检能否被「只差注释」之外的写法骗过？

**判据**：构造 8 种变异写法，看「去 docstring 后的 `ast.dump`」能否正确分类。

| 写法 | AST 指纹 | 预检判定 | 正确？ |
|---|---|---|---|
| 只改注释 | 相同 | 空操作 → ERROR | ✓ |
| 只改 docstring | 相同 | 空操作 → ERROR | ✓ |
| 只改空白/缩进 | 相同 | 空操作 → ERROR | ✓ |
| 加空行 | 相同 | 空操作 → ERROR | ✓ |
| `>` 改 `>=` | 不同 | 真变异 → 放行 | ✓ |
| 删整条分支 | 不同 | 真变异 → 放行 | ✓ |
| 改常量值 | 不同 | 真变异 → 放行 | ✓ |

**⚠️ 找到一个真实盲区**：`include_attributes=False` 意味着**行号不进指纹**，所以
「把整段代码原样挪到别处」这种变异 AST 指纹会相同 ⇒ 被误判为空操作。
本卡 9 段变异都不是这种形态（全是替换/删除语句），但这是真盲区，已登记 §六。

---

## ③ negctl 主判据只验「抛了 AssertionError」，这个缺口实际可达吗？

**判据**：逐段施变异、抓 `AssertionError` 的消息首句，看是不是该段**设计要红**的那条。

**结果：18 个组合（9 段 × 2 副本）全部红在各自设计要红的断言上**：

| 段 | 红在哪条断言（消息首句） |
|---|---|
| COLONPOSIX | 前导冒号串 `':AAA-1'` 被当成 POSIX 规格串收下了 |
| H1BARE | `` `<AAA1><BBB2` `` 被接受了 —— libc 对它退 UTC |
| H2COLON | `'AAA1:'` 被接受了 —— 偏移没吃满三段时那个 `:` 还属于偏移 |
| H3QUANT | `[arabic] n=3232 耗时 0.53s > 0.05s —— 分词不是线性` |
| H4ZERO | 超长前导零串被拒了 —— libc **接受**它 |
| ASCII | 正则数字类放宽后，`/２` 里的非 ASCII 数字没有被 ⑤ 接住 |
| RULEA | 正则数字类放宽后，规则字段 `J３60` 里的非 ASCII 数字没有被接住 |
| KEYUTF8 | `'AAA\udcff1'` 让解析器抛了 `UnicodeEncodeError` |
| HMAX | `'AAA24'` 被接受，却在 `isoformat()` 上抛 `ValueError: offset must be…` |

⇒ **缺口不实际可达**。加固（`expect_msg` 关键词断言）**本轮不做** —— 判据显示当前 9 段没有
一段红错地方，加固只会让终审绑定再断一次。已在 §五.11 如实登记为已知弱点。

---

## ④ pick 改现取后，全部 11 处夹具是否仍真钉住？

| 判据 | 结果 |
|---|---|
| monkeypatch 钉法（6 处）有无 `raising=False` 旁路 | **0** ⇒ 默认 `raising=True`，属性不存在会抛 |
| 直接赋值钉法（5 组）的 `try/finally` 还原 | `picker._display_tz` 赋值共 **10** 次 = 施钉 5 + finalbody 还原 **5** ⇒ 一一对应 |
| 钉的名字在 pick 里存在 | `def _display_tz` = **1** ⇒ 不是给不存在的名字赋值 |
| AST 级全仓 `_DISPLAY_TZ` 代码引用 | **0**（验伪锚 `_display_tz` = 53） |

**关于两种加载路径共存**（prompt ④ 后半）：本卡第一版用 `spec_from_file_location` 重新 exec
造成过测试间污染（§五.12），已改成与其余 4 处同形的普通 `import`。
实测两种执行顺序（先现取门 / 先 bucket_gate）**都 2 passed**，且 `tests/regression` 目录级
**2165 passed / 0 failed** ⇒ 这一次执行顺序下对其余 64 个文件零副作用。
⚠️ 顺序扰动（`-k` / xdist 分片）未测，已登记 §六.8。

---

## ⑤ `.key` 的 UTF-8 严格性是否有旁路？

**判据**：给三档逐个喂含代理字符的输入。

| 档 | 输入 | 结果 |
|---|---|---|
| CANVAS_TZ | `Asia/\udcffShanghai` | `display_tz()` **抛 ValueError**（配置断裂要说话，D-18 语义） |
| CANVAS_TZ | `Asia/Tokyo`（对照） | `.key='Asia/Tokyo'`，encode OK |
| TZ（POSIX 串） | `AAA\udcff1` | 退 `.key='UTC'` ⇒ ④ 的 `spec.encode("utf-8")` 拦住了 |
| TZ（IANA 名） | `Asia/\udcffShanghai` | 退 `.key='UTC'` |
| /etc/localtime | 不设 TZ/CANVAS_TZ | `.key='Asia/Hong_Kong'`，encode OK |

⇒ **无旁路**。CANVAS_TZ 档走 `ZoneInfo(name)`，坏名字直接抛；`/etc/localtime` 档的 key 来自
文件系统路径解析，不经 `os.environ` 的 surrogateescape；只有 TZ 档的 POSIX 串会带代理字符，
而那一层由 ④ 拦住（negctl 段 `KEYUTF8` 锁住这一条）。

---

## ⑥ pyright `0 errors` 是否靠 `# pyright: ignore` 掩盖？

| 判据 | 结果 |
|---|---|
| `pyright app` 汇总行（结构锚 `^[0-9]+ errors?, `） | **`0 errors, 81 warnings`** |
| 本卡在 **`backend/app`**（= pyright 的取值面）新增 ignore | **0** |
| 验伪锚：`backend/app` 全树既有 ignore 行数 | **53**（证明 grep 能命中） |
| 本卡改的两个 app 文件 base vs head | `display_tz.py` 0/0、`review_overview.py` 1/1 |
| 零 `LEFTHOOK_EXCLUDE` | 7 个 commit 全部由 lefthook 完整放行 |

⚠️ warning **80 → 81**：新增那条来自**移植进来的** R2 `fromutc` 防御
（`display_tz.py:683` `reportUnnecessaryIsInstance`），保留不改，理由见 §五.10。

---

## ⑦ 「生产 ⑥ 删掉、测试 `_declared_narrowing` 同名检查保留」的辩解是否站得住？

**两边都不可达**（实测：3723 条匹配成功样本里 std_off 为空 **0** 条），但**理由不同**：

- 生产 ⑥：纯行为防线，不可达就该删——这是本文件 ③ 处 R2 自己立下的规矩
  （「留着一条永不执行的检查，比删掉它更坏，它会让后人以为防线在这一层」）；
- 测试 `_declared_narrowing`：职责换成了**类型收窄**——`groupdict()` 给 `str | None`，
  紧接着那行 `_posix_offset_seconds(g["std_off"])` 需要 `str`。删了会引入类型问题。

两处都在注释/docstring 里写明了各自的理由。**辩解成立**，但这是本卡自评——
如果后续 Codex 轮次不认，改法是给测试侧那行换成显式的 `assert g["std_off"] is not None`，
语义相同且不伪装成行为防线。

---

## 人审的边界（这份不能替代 Codex 的地方）

1. **我是作者**。这 8 个问题是我自己写进 prompt 的，意味着我**只核了我想到的面**。
   Codex 的价值恰恰在于问我没想到的问题——这一层本轮缺席。
2. 本轮未做**对抗性输入构造**（Codex 会自己造 libc 对拍组合）。我跑的对拍样本
   （31 万条 + 320 条）都来自我自己设计的网格，与 R2 的网格同源。
3. 已知弱点仍在：negctl 的 `expect_msg` 加固（§五.11）、AST 指纹的行号盲区（本文 ②）、
   顺序扰动未测（§六.8）。

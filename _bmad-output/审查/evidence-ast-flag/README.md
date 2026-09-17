# evidence-ast-flag — CARD-AST-FLAG-PATCH 证据索引

> 批次 `[BATCH-2026-09-11-第十四批 / CARD-AST-FLAG-PATCH]`。
> ⚠️ 本目录有**五代**存档（初版 `0842–0850` / format 后 `0900` / Codex r1 后 `0917` /
> r2 后 `0930–0933` / **r3 后 `0949–0950`**）。**只有 `0949–0950` 那一代是定稿的承重件**；
> 前四代保留作过程记录，**不得引为定稿依据**。

## 承重（定稿一代，按裁判编号）

| 裁判 | 文件 | 结论 |
|---|---|---|
| 1 第 0 分钟 | `minute0-20260917T084209.txt` | 分支/HEAD/status 空/基线 64/patch 缺席 0（验伪锚 3） |
| — 改前基线 | `baseline-48-27-20260917T084255.txt` | `PASS (48 / 27)` |
| 2 三盲区先红（各一份） | `red-lambda-20260917T084628.txt` / `red-setattr-20260917T084629.txt` / `red-branch-20260917T084629.txt` | 各只加一条条目 ⇒ 各**恰好一条** `*** MISSED ***` + `FAIL` + rc=1 |
| 3 后绿 | **`green-63-28-20260917T094933.txt`** | `PASS (63 / 28)`，CAUGHT=63 CLEAN=28 MISSED=0 FALSE-POSITIVE=0 |
| 3+ 定向负控（本卡自加，承重） | **`negctl-anchors-20260917T100737.txt`** + `negctl.py` | **9 处**修复逐个撤掉，**指定的那一条**（ID 精确匹配 + 唯一性断言）各自变红；控制组红项为空 |
| 4 消费面 / 全扫描面 | `consumers-before-20260917T084638.txt` + `fullscan-before-20260917T084647.txt` vs **`consumers-after-20260917T094946.txt`** | 两文件违规集与 401 文件全扫描面违规集**改前改后逐字相同**（都为空） |
| 5 fixpoint 红 / 绿 | **`fixpoint-red-20260917T094933.txt`** / **`fixpoint-green-20260917T094933.txt`** | 红正文含 `MISSED: 未收敛未被报出` ×2 且 `RUNTIME-FILES-SELFTEST: PASS`；绿 `FIXPOINT-SELFCHECK: PASS` |
| 6 地盘 | `territory-20260917T092132.txt` | 只 `backend/scripts/lifespan_isolation_negative_control.py`（验伪锚：去掉 exclude 多出 55 条 `_bmad-output/` 路径）。⚠️ 该件绑 `6564fc09`；定稿 SHA 的地盘回执见 `territory-FINAL.txt` |
| 7 ruff | **`ruff-r3fix-20260917T094946.txt`** | `check` / `format --check` 均 rc=0；F821 验伪锚 rc=1 |
| 8 tests/unit | **`unit-close-20260917T094921.txt`** + `base.nodeids` / `close.nodeids` | 与 64 基线 diff 空 |
| — pyright | `close-pyright-20260917T085652.txt` | `0 errors, 81 warnings`（本卡零触及 `backend/app`） |
| — Codex r1 复现 | `verify-r1-findings-20260917T091714.txt` + `verify_r1.py` | 四条 finding 整改前后的旧/新对照 |
| — Codex r2 复现 | `verify-r2-findings-20260917T093255.txt` + `verify_r2.py` | 七条 finding 三版对照 |
| — Codex r3 复现 | **`verify-r3-findings-20260917T094933.txt`** + `verify_r3.py` | 五条 finding 的 base / r1 / r2 / 现版**四版**对照 |
| — 车道自审 | **`selfaudit-r3-recheck-20260917T095015.txt`** + `probe_r3_selfaudit.py` | r3 报告返回**前**自查抓到一条（四-A.12），整改后复跑全过 |
| — 索引自检（引用的是**当次**回执） | **`readme-selfcheck-20260917T100808.txt`** + `readme_selfcheck.py` | 三条判据各带验伪锚，全 PASS |

## 纵深（非卡文要求，本卡自加）

- `probe-isolation-boundaries-20260917T094946.txt` —— (d) 的六条边界性质。
- `probe-lambda-scope-20260917T093307.txt` —— `_own_exprs` 旧/新绑定对照（r2 一代，结论未变）。
  ⚠️ **声称必须收窄**（Codex r3 指出）：不能说「根位置与 `B14_BASE` **普遍**等价」。
  反例 `lambda cb=lambda x=(a := 1): x: cb` 以整个 lambda 作根输入时，基线收 `[]`、现版收 `['a']`
  —— 那是符合「定义时求值」定义的**预期变化**，不是缺陷，但等价声明本身不成立。
  准确说法：**探针里那三条输入上**根位置行为与 `B14_BASE` 逐字同；根 lambda 的**体**不再被
  借道新增路径下潜（r2-HIGH1 的失效路径已修）。
- `probe-annotation-yield-by-version-20260917T093019.txt` —— ⛔ **逐版本**实测注解里的 `yield`：3.11.15 **合法**且外层真多一条 `YIELD_VALUE`；3.14.4 `SyntaxError`。CI matrix 是 `['3.11','3.12']`。
- `probe-walk-same-scope-delta-20260917T092246.txt` + `probe_walk_delta.py` —— 新旧 `_walk_same_scope` 在 401 文件上的差分（旧有而新没有 = 0）。
- `probe-setattr-shadow-rate-20260917T092145.txt` —— `_module_binds_name` 在真实面上的触发率（0/401，交集 0）。
- `fixpoint-rounds-instrument-20260917T085859.txt` + `rounds_instr.py` —— `_FIXPOINT_MAX_ROUNDS=8` 的取值依据。
- `probe_direction.py` / `probe-lambda-direction-20260917T091725.txt` —— 根位置 lambda 的方向核（本卡一度改过、经 r1 HIGH-1 已撤回）。

## 如实登记：四处判据 / 改动**自身**出过问题（保留记录）

1. **`ruff-20260917T085053.txt` 的验伪锚失败**（anchor rc=0 = 判据当时恒绿）。根因：锚文件放在仓外，ruff 按**文件路径**解析配置。已改 `--stdin-filename` 重做。**该件不得引为依据。**
   顺带实测：`backend/**` 只启用 14 条必错级规则（`E902` + F 系），**`F401` 不在其中**。
2. **`rounds2.py` / `rounds_real.py` / `fixpoint-rounds-instrument-20260917T085801.txt` 作废（VOID）**，文件内已就地写明。根因：硬编码行号 634 在改动后漂到 687，直方图退化成 `{0: N}` 的假数据。替代件 `rounds_instr.py` 把锚升成 `assert`。
3. **`probe-outer-evaluated-completeness-20260917T092116.txt` 的结论是错的**（⛔ **不得引用**）。它断言「注解里不能写 `yield`，故不是缺口」—— 那是**只在本机 3.14 上**测的，而 CI 跑 3.11/3.12。Codex r2 HIGH-3 指出后逐版本复测（见上方 `probe-annotation-yield-by-version-*`）：3.11 上完全合法。代码已按 3.11 口径补收注解。
4. ⛔ **`setattr` 遮蔽开关在 round-3 被整条撤回**（它为一条 MEDIUM 而生，先后长出 5 条缺陷，其中 3 条 fail-open）。与之绑定的 3 条 must-pass 锚（`验伪锚 R1-M3` / `R2-M5` / `R2-M5b`）随之删除。详见验收单 四-A.11。
5. **本卡 r1 的两处修复各自引入了新回归**，均由 Codex r2 抓出并已修：根 lambda 的递归下潜（HIGH-1）、`_walk_same_scope` 的 `stack.extend` 未再过 `push`（HIGH-2）。两者都已加回归锚（`R2-HIGH1-*` / `R2-HIGH2-*`）。
6. **`readme-selfcheck-20260917T095015.txt` 是一份 `FAIL` 回执**（保留作过程记录，⛔ 不得引为
   「索引已闭合」的依据）。它抓到的是我**第四次**手写时间戳出错 —— 前三次都是 Codex 抓的，
   这次被自检当场拦住。根因不是「写错了哪一个」，是**手写**这个动作本身；现在 README 的文件名
   一律从磁盘**派生**，不敲。当次有效回执见上表「索引自检」行。
7. **索引自检的提取器一度窄于它的主张**（Codex r4 LOW）：只认「反引号 + 受限字符集 + 小写
   扩展名」，于是目录前缀 / 空格 / 大写扩展名 / 裸写四种形态**静默漏过**（连「判缺失」的机会
   都没有）。更要命的是它的验伪锚**绕过提取器**直接查集合成员，所以提取器有多窄它一个都
   看不见。现在提取面扩开、按 basename 校验，**五个锚全部改走同一条提取器** —— 改完当场又
   抓出「反引号内尾部空格」这一种，已补。
8. **定向负控的变异锚会随生产代码漂移**：`ruff format` 把一行 `child_in_body = ...` 折行后，r2 那个锚一度命中 0 次。脚本对每个锚 `assert count == 1`，锚不命中直接抛 —— 不会静默少跑一个变异。

## 索引自检

本文件引用的每个具体文件名都必须真实存在。**Codex 连三轮抓到这一条**，三次形态各不相同：
r1 是我手写了错的时间戳；r2 是留了尖括号占位；r3 是把时间戳中段写成省略号 —— 那种写法既不是
占位符也不是真名，所以前两版自检都放行了。

⇒ 自检口径收紧为三条，缺一不可：**(1)** 反引号包裹、以 txt / py / nodeids / md 结尾的名字逐个
必须存在；**(2)** 尖括号占位计数为 0；**(3)** 省略号计数为 0（第三条是 r3 之后才加的，前两条
都漏了这一形态）。脚本 `readme_selfcheck.py`，三条各带一个验伪锚。

⛔ 脚本的说明文字**刻意不字面写出**那三种被禁形态 —— 第一版写了，结果自检被自己的文档绊倒
（判据的文档落进判据自己的命中面）。修法是改文字，不是给判据开豁免：一开豁免，真正的漏检
就会从豁免区溜回来。

## 格式漂移的归属（卡文 (k) 要求先判再处置）

`ruff format --check` 在本卡定稿上红，**是本卡引入**（同一配置面下对 `B14_BASE` 内容跑 `--check` rc=0，见 `ruff-format-20260917T090107.txt`），故**不**走协议 §2.3 过渡条款，直接 `ruff format`。format hunk 全部落在本卡新增行内。

## prefix.py

裁判 5 的「先红」副本 = `cp` **定稿**文件后 `sed` **仅**剔除「未收敛处置」那一处 2 行 hunk（保留 `--selfcheck-fixpoint` 子命令）。依 **R-B14-7** 不从 `B14_BASE` 取。实测确认它不在门的扫描面内（401 不变）。

# CARD-RED-HYGIENE 对 Codex r3 的逐条处置

> r3 存档：`codex-review-CARD-RED-HYGIENE-r3.md`（绑最终 HEAD `69c99d1a`，**代码面 diff 为空**）
> r3 计数：**BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 3**
> ⇒ D-15 的终审条件（绑最终 HEAD 的一轮 BLOCKER=0 且 HIGH=0）**在 r3 这一轮再次满足**
> （r2 已满足过一次，之后因整改失绑）。
> ⚠️ 本卡按 r3 的 MEDIUM-1 / LOW-1 又改了代码 ⇒ r3 据 D-15 失绑，另送 **r4**。

⚠️ **r3 自述的一个限制（必须转述，不能省）**：r3 **没有完成独立的目录级重跑** ——
指定命令在 pytest 收集前被只读环境的临时目录限制挡住
（`FileNotFoundError: No usable temporary directory found`，退出码 1，尚未收集测试）。
它对目录级的结论是**对已有存档的复核**，不是本轮独立运行。r3 自己明说
「不能据此宣称目录级通过」。

---

## HIGH-1 维持撤销 —— r3 复核了历史证据

r3 独立执行 `git show f294878b:…/unit-integ5-20260911T010612.txt`，
确认 597–606 行确有同一 `candidate422`、同一 `::1:7691 / MainThread` 指纹与 JSON 降级，
1143 行为 `blocked=1, advisory=0, unaccounted=0` ⇒ **该现象早于本卡**。

并再次强调依据的**是历史原始日志**，「不能仅凭五跑非确定性或协议的 `grep -c` 判据免责」。
车道认可这个口径，`FINAL-sentinel-5runs-*.txt` 与 `attribution-*.txt` 均已按此收窄/拆分。

---

## MEDIUM-1 guard 仍漏直接重绑定及其他直接写入 —— ✅ 已修（**换方法，不再枚举**）

r3 用内存探针实测出**第四类**漏面（前三类是 r2 报的、已修）：

| 输入 | 修前 | 运行时名单 |
|---|---|---|
| `expected_templates = other = ["x"]` | **PASS（漏）** | 仅 1 项 |
| `expected_templates, other = ["x"], []` | **PASS（漏）** | 仅 1 项 |
| `with nullcontext("x") as expected_templates[0]:` | 漏 | 改变 |
| `[None for expected_templates[0] in ["x"]]` | 漏 | 改变 |
| `def helper(unused=expected_templates.pop())` | 漏 | 改变（**定义默认参数时就改**，不用调用 helper） |

r3 给的根因判断准确：旧实现「跳过多 target 绑定、不认解包绑定」，
而「无条件略过裸 `Name`」又假定这些已被 FOUND-N 覆盖 —— 两边都没管。

### 处置：不再打补丁，改判定方式

前三轮（r1 / r2 / r3）每一轮都被找出**没列到的语句形态**：
下标 `AugAssign` → 多 target → 解包绑定 → `with as` 下标 → 推导式 target → 默认参数里的 `.pop()`。
**枚举语句类型这条路追不完**。

新实现改为**按 Python AST 自带的 `ctx` 判定**：每一个写目标都被标成
`ctx=Store` 或 `ctx=Del`，不管它出现在哪种语句里。于是：

* `_collect_writes()` 只做三件事 ——
  (1) `Name` 且 `ctx=Store` → 记为**绑定**；`ctx=Del` → 记为其它写入；
  (2) `Subscript` / `Attribute` 且 `ctx in (Store, Del)` 且根名匹配 → 其它写入；
  (3) 就地变更方法调用（`.append` 等八个）→ 其它写入。
* 断言：**绑定恰好 1 处**，且**其它写入为空**；那一处绑定必须来自
  `Assign`/`AnnAssign` 且右值是字面量 list。
* `_own_nodes()` 跳过嵌套 def / lambda / class 的**函数体**（独立作用域），
  但**仍下钻**它们的默认参数 / 装饰器 / 基类 —— 那些在外层作用域求值，
  正是 r3 那条 `def helper(unused=expected_templates.pop())` 的落点。

### 同时修掉 r3 LOW-1 报的误报

`expected_templates[:].reverse()` 改的是**切片副本**，不改本体，r3 实测新版误报为 RED。
新实现对就地变更方法**只认裸 `Name` 作接收者**：`x.append()` 算写入，
而 `x[:].reverse()` / `x[0].append()` 改的是副本 / 元素，不算。

### 复验

`FINAL-R4-guard-shapes-*.txt`：import 入库的真 helper，只在内存替换 `inspect.getsource` 输入，
**26 格逐格写死预期并由探针自己断言**，`预期不符 = 0`，探针退出码 0。覆盖：

* **应通过 5 格**：真实生产源码 / 带类型注解 / 嵌套函数同名局部变量 /
  `x[:].reverse()`（r3 LOW-1）/ `x[0].append()`；
* **应报红 21 格**：r1 的 `+=`、`[0]=`；r2 的 `[0]+=`、`del a[0],b[0]`、`a[0]=b[0]=`；
  **r3 的 `x=other=[..]`、`x,other=..`、`with as x[0]`、推导式 target、默认参数 `.pop()`**；
  车道另补的 lambda 默认参数、装饰器内 `.pop()`、元组解包写下标、`for` 重绑、walrus 重绑、
  `del x`、`.append`/`.remove`/`.sort`、常量 / 改名。

### r3 点名的那句话已撤回

r3 指出 `_production_expected_templates` 的 docstring **仍保留**「门通过时必然一致」，
与 `RESPONSE-r2:182` 自述矛盾。**已删**，改为逐条列出**看不见**的三类：
别名写入、传进函数由被调方改、`locals()`/`globals()`/`setattr`/`exec` 等动态手段，
并写明「真要钉运行时值，得改成运行时取真实名单（那是另一张卡的面）」。

---

## MEDIUM-2 自审汇总在 RH-1 改判后仍未重算 —— ✅ 已修（第三次）

r3 解析**被审 Git 对象**得 `main_upheld=19 / workflow_upheld_rows=2 / overturn_rows=16 /
fixed=15 / registered=3`，而文件里仍写 18 / 15。车道复跑同类解析，**逐项确认**，
并查清了自己与 r3 差 1 的地方：车道先前把 RG-3（工作流「未验证」）也算进了「翻转」，
而 r3 用的是严格口径（工作流**明写**「不成立」）—— **严格口径为 16，采纳 r3 的**。

r3 另指出第 38 行的「15 + 3 ≠ 18」是**错的表述**：那两个集合本就不是互斥划分，
不构成算术命题。**已删**。

**这次连计数规则一起写进去**：§一 汇总表加了「计数规则（可照此复算）」一列，
并留了「历次错值留档」小表，写明第二次之所以还错，是因为
「改完数字后又改判了 RH-1，却没有重算汇总 —— 派生数字与来源表脱钩」。

⚠️ r3 关于「把严重度混进成立性」的限制仍成立：缺 verifier 正文，该解释只能作为摘要，
不能独立确认 —— 已在 §四 如实写明，未改。

---

## LOW-1 切片副本误报 —— ✅ 已修（见 MEDIUM-1「同时修掉」段）

---

## LOW-2 归属更正把两份不同红集混写成同一个 34 条 —— ✅ 已修

r3 实数：`unit-integ5-20260911T010612.txt` = **65** 条（36 FAILED + 29 ERROR）；
`epw-unit-close7.nodeids` = **34** 条；本卡 34 条与 **EPW 的 34 条逐项相同**。
车道独立复算，**逐项一致**（本卡 vs EPW 差集 **0**，本卡 vs integ5 差集 **31**）。

**已修**：`attribution-*.txt` 与 `RESPONSE-codex-r2-*.md` 都加了更正段，按 r3 的建议拆开引用：
* **EPW（34 条）** 证「红集没变」⇒ 本卡净贡献 0；
* **integ5（65 条）** 证「哨兵现象早于本卡」（含 candidate422 + 唯一指纹 + `blocked=1`）。
`FINAL-sentinel-5runs` 里「非确定性即可排除本卡归因」的过强推论此前已收窄（r2 LOW-2 处置）。
⛔ **更正（Codex r4 LOW-2）**：本句原先写「`FINAL-R2-unit-comm` 与 …… 本轮再核确认到位」——
**不实**：`FINAL-R2-unit-comm` 当时**并没有**加撤回段，其第 35 行附近仍保留
「两环境、两 SHA 出现 ⇒ 与本卡引入回归不相容」。r4 实跑 `git show ef21be2c:<路径>` 核出。
已在该文件末尾补撤回段并指向 `$PREV` 的 integ5 原始证据。

---

## LOW-3 最终地盘证据仍未入被审 SHA —— ✅ 本轮入库

`FINAL-R3-territory-20260916T195658.txt` 写于 `69c99d1a` 之后、当时是未跟踪文件。
本轮随整改 commit 入库。r3 明说「地盘实质已由本轮独立重算通过，不是代码越界，
也不影响代码 SHA 绑定」——其重算结果：代码面 **6 文件**、OpenAPI 三方字节一致、
exclude 锚 **51/0**、本卡变更文件名含 stderr **0**，与车道自跑一致。

⚠️ 这类「证据写于 commit 之后 ⇒ 不在被审 SHA 里」的问题本卡已出现两次
（r1 LOW-4 / r3 LOW-3）。结构性原因：收工判据必然在最后一个 commit 之后才跑得出来。
**登记移交**：这属于流程口径问题（末次判据存档与被审 SHA 的先后关系），建议批级统一处置。

---

## 本文件未证明什么

1. **未证明新实现覆盖了所有会让「声明 ≠ 运行时」的路径**。
   ⛔ **本条原先写「按 `ctx` 判定在本作用域的语法层是穷尽的」—— 已被 Codex r4 证伪、撤回**：
   `match` 的 `case [*name]`（`MatchStar.name` 是字符串、不产生 `Name(ctx=Store)`）与
   **类体在定义时立即执行**（`class Helper: expected_templates.pop()`）两种形态都能改到名单
   而门不红；`import` / `def` / `except as` 的名字绑定同样不是靠 `ctx` 收全的。
   准确说法：**覆盖比逐条枚举宽得多，但不穷尽**。加上原本就看不见的别名写入 / 传出去改 /
   动态手段，覆盖边界已逐条写进 `_collect_writes` 的 docstring。
2. **未独立验证 r3 自述的目录级受阻** —— 车道没有去复现它那个只读临时目录限制；
   车道自己的目录级跑是另一套环境的结果。
3. **未证明「按 ctx 判定」不会有新的误报** —— 26 格里有 5 格是「应通过」，
   但未穷举所有「看起来像写、其实不改本体」的形态（例如 `x.copy().append()` 之类未测）。
4. **未闭合 LOW-3 的结构性问题** —— 本轮只是把那份存档补进 commit，
   「末次判据必然晚于被审 SHA」这件事本身没解决，已登记移交。

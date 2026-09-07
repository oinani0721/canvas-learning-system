# CARD-RV-W4-5 外审请求 — 复审一次「审后整改」是否闭合

## 一 背景与最小读取面

树根: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates`
分支 `card/u8-mutgates`，HEAD `da690bf8`。**本卡零代码**：commit 只含 `_bmad-output/`，代码树与 `da690bf8` 逐字节相同。

被复审的对象是一次**整改**，不是一次新实现：

- 上一轮外审绑定 `6d6e3e09`，出 8 条（4 HIGH 条目 / 2 MEDIUM / 2 LOW），结论行写「不建议通过本卡」。
- 随后 `07d59a52` 按其中 5 个 HIGH 子发现做了整改：`1 file changed, 337 insertions(+), 17 deletions(-)`。
- **那次整改至今没有第二轮外审。** 本卡就是补这一轮。

请只读以下内容，不要跑任何命令、测试或分析器，不要连任何端口：

1. `git diff 6d6e3e09 07d59a52 -- backend/scripts/lifespan_isolation_negative_control.py`（453 行，整改全貌）
2. HEAD 上 `backend/scripts/lifespan_isolation_negative_control.py` 的五段：
   `:600-680`、`:1120-1140`、`:1200-1260`、`:1940-1980`、`:3110-3160`
3. 同文件两张表全文：`_AST_MUST_FLAG`（`:1977` 起）与 `_AST_MUST_PASS`（`:2580` 起）
4. 上一轮外审存档 `_bmad-output/审查/codex-review-CARD-W4-5-ast-high6.md` 的第 1、3、5、7 条
5. 本卡的复审表 `_bmad-output/审查/evidence-rv-w45/triage-20260908T065615.md`

补充锚点（都已在本树实测，行号以 HEAD 为准；存档正文自述其行号比当时请求的锚点后移 4 行，
整改又插入 337 行，所以**存档里的 `L…` 与 HEAD 行号不可直接对应**）：

| 主题 | HEAD 行号 |
|---|---|
| 白名单 `_PROVEN_NOT_MAIN_INSTANCE` | 定义 `:439-452`，唯一读站点 `:1814` |
| 逐位表按 key 聚合 | 判据 `:1351-1354`，轮末发布 `:1275` + `:1277-1297` |
| `_walk_same_scope` | 定义 `:455-481`，唯一消费站点 `:1442`；`:1462` 一个合格候选即 return |
| FunctionDef 的装饰器/默认参数扫描 | `:691-692`；`_own_exprs` `:751-766`（`:762` 遇 `ast.Lambda` 停止下潜） |
| `_module_attr_write_paths` | 定义 `:484-516`，消费 `:975-982`，C4 唯一调用点 `:1756` |
| 顶层不动点 | `:634` `for _ in range(4):`，`:664` break，`:665` 轮外 `_rebuild` |

## 二 作者自述，请独立核对

以下都是本卡作者（我）的判断，请逐条独立核对，**不要默认它们成立**。

### 2.1 五条 HIGH 的判定

判定刻意分两列：**A 列**只问「上一轮外审原文点名的那个形态」闭合没有；**B 列**是同一机制的其他语法位置，属本卡新查，不计入对整改的评价。

| 条 | A：外审点名形态 | B：同机制其他语法位置 |
|---|---|---|
| R2-1 白名单 | 闭合 | 未发现 |
| R2-3 按 key 聚合 | 闭合 | 未发现 |
| R2-5a 同作用域遍历 | **部分闭合** | 见下 |
| R2-5b 装饰器与默认参数 | 闭合 | lambda 的默认参数未被拦下 |
| R2-7 模块属性写 | 闭合 | `setattr` 形式的写未被拦下 |

### 2.2 三个**未被拦下的输入**（本树实测，非推演）

每一条都与一条已在 `_AST_MUST_FLAG` 里的**对照输入**只差一处写法。实测脚本
`_bmad-output/审查/evidence-rv-w45/probe_residual_surfaces.py`，同一次运行里 3 条必红的对照输入全部判红、
2 条必绿的对照输入全部判绿（否则这三条的「零违规」既可解释成门未覆盖、也可解释成脚本空转）。

- **P1**（对应 R2-5a）：包装器里一条分支在隔离块内让出控制权、另一条分支在隔离块外让出。
  这一条是**上一轮外审第 5 条正文里明文点过的**（原话：「普通的『一条分支隔离内 yield，
  另一条分支隔离外 yield』也存在同类问题」），所以我把 R2-5a 判为部分闭合。
- **P2**（对应 R2-5b）：把外审反例里的嵌套 `def unused(x=(a := FastAPI()))` 换成
  `unused = lambda x=(a := FastAPI()): x`。lambda 的默认参数与 def 的默认参数一样在定义处求值，
  但 `_own_exprs`（`:751-766`）遇到 `ast.Lambda` 就停止下潜。
- **P3**（对应 R2-7）：把外审反例里的 `mod.client = TestClient(app)` 换成
  `setattr(mod, 'client', TestClient(app))`。

### 2.3 MEDIUM-6① 定性

`:634` 的四轮上限达到后**没有任何处置分支**：`:664` 的 break（已收敛）与循环自然耗尽（未收敛）
走同一条出口，随后同一句 `:665`。全文 `grep '未收敛|收敛|converge'` 仅 5 处命中，全是注释里
描述判据组成的用词。我定性为「未修，方向是误拒而非放行，且静默」，归属 U8-B 或第十四批。

### 2.4 两个独立计数

门自报 `48 / 27`；用 `ast.parse` 独立静态解析两张表也是 `48 / 27`。两者不同源。

### 2.5 探针计数三口径

`grep -c '^def probe_'` = 33；`main()` 里显式条目 = 35；门运行时报告 = 54/54。三者不可互推，
以门运行报告为准。

## 三 请回答的问题（按重要性排序）

1. R2-1 改成白名单之后，是否仍存在「来源标签是白名单里的某一项、但对象实际不是那一项所描述的东西」
   的路径？白名单十项里有没有哪一项的标签生成依据不足以支撑它被列入。
2. R2-3 的按 key 聚合，是否覆盖「同名工厂跨模块或跨作用域重定义」的情形？`_factory_key`
   对嵌套定义与模块级同名定义会不会给出相同的 key。
3. R2-5a / R2-5b 整改之后，隔离包装器资格判定还有哪些求值位置没有被扫到？除我列出的 P1、P2 之外。
4. R2-7 的 `module_attr_writes` 除 `setattr` 外还漏了哪些写入形式？作者自述「容器元素写
   `clients[0]`」是盲区——我核为**在 C4 这条路上到不了**（`with mod.clients[0]:` 的上下文表达式
   是 `Subscript` 而非 `Attribute`，`:1756` 的类型判断直接不成立）。这个核对成立吗。
5. MEDIUM-6① 的四轮上限，在现有 48 条反例 / 27 条正例里有没有已经踩到的用例（即某条正例其实
   依赖第五轮才成立、现在恰好因别的原因通过）。
6. 本卡复审表（§二）的判定，有没有哪一处与 HEAD 原文不符。

## 四 输出格式

每条一段：**级别**（BLOCKER / HIGH / MEDIUM / LOW）+ **文件:行** + **依据** + **建议**。
只读条件下无法判定的，请明确写「未验证」，不要写成成立或不成立。
若认为作者的某条判定过宽或过窄，请指出是哪一列（A 还是 B）以及应该改成什么。

## 五 边界

- 只读。不跑门、不跑测试、不起子进程、不连任何端口。
- 本卡是零代码复审卡，不改任何代码；所有修法都是交接给后续卡的建议，不需要给出补丁。
- 不在本卡范围、请不要评审的面：
  `backend/tests/support/live_port_guard.py`、`backend/tests/support/guard_plugin.py`、
  `backend/tests/conftest.py`、`backend/scripts/lifespan_isolation_guard_probes.py` 与相关契约（属 U7）；
  `backend/scripts/mutation_kill_identity.py` 与四套变异 harness（属 U8-B）；
  `lefthook.yml`（属 U8-C）；`backend/tests/unit/conftest.py`（属 U10-A）；`backend/app/**`（本卡不触及）。

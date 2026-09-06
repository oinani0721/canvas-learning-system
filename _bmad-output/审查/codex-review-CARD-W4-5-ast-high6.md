> 批次: BATCH-2026-09-05-第十二批 · 车道 Y8 · CARD-W4-5-ast-high6 round-1（⚠️ 车道未按协议 §2.1 写首部，主 session 于 2026-09-06 集成期补记；按协议本轮不计入卡族轮次配额，正文一字未改）
> 模型: `gpt-6-astra`（车道 stderr 实测） · reasoning_effort: `ultra`（车道 stderr 实测） · codex: `codex-cli 0.153.3`（车道 stderr 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`（手册规定形态；实参见车道 stderr）
> 审查绑定: `6d6e3e09`（存档正文与验收单 §八 自证；审后 07d59a52 整改 5 HIGH 未复审，车道已登记）
> 会话头自证（抄车道 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y8-w4-ast` / `model: gpt-6-astra`

---

**结论：不建议通过本卡。** 改后代码仍有 HIGH 级漏放路径；40/24 条输入也没有分别守住全部新增规则。

本次仅作静态读取和手工推演，没有运行命令、测试、分析器或连接。以下 `L…` 均指本轮读到的[该文件](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y8-w4-ast/backend/scripts/lifespan_isolation_negative_control.py)，部分行号比请求中的锚点后移 4 行。指定 diff 未取得，历史比较的核验限制见第 8 条。

1. **HIGH — 三分仍有静默放行：`localfunc:` 标签不保证对象真的是函数。**

   `_flag_instance_context` 的实际分流如下（L1619–1662）：

   | 表达式 | 路径及结果 |
   |---|---|
   | `NamedExpr` | 递归 `.value`，随后适用该值的判定；递归本身成立 |
   | `Name` | `resolve_name` → main 实例检查 → 非 unknown 标签直接返回 → 否则检查 C1–C4 |
   | `Attribute` | 主实例属性识别或 `_attribute_origin` → 同上；unknown 属性还可能被 C4 放行 |
   | `Call` | 已知 main 工厂或 `_value_origin`；unknown 调用通常被 C2 放行，partial-main 工厂除外 |
   | 其余类型 | `origin` 保持 `None`；同步上下文且模块有 TestClient 可达性时通常 fail-closed；C1、C3 仍可能豁免 |

   因而，下标、字面量、比较式、`await` 等**没有一个无条件返回分支**；但“不可证必拒”仍受豁免条件限制。直接位于 `with` 的 IfExp 会先由 L1720–1729 展开，这部分成立。

   真正击中 L1652–1653 的反例是：

   ```python
   from app.main import app
   from fastapi.testclient import TestClient

   def as_client(fn):
       return TestClient(app)

   @as_client
   def cm():
       pass

   with cm:
       pass
   ```

   Python 装饰后，`cm` 是生产 app 的 TestClient 实例；但 L589–597 忽略装饰器，将其绑定为 `localfunc:cm`。L1652 把这个非 unknown 字符串当作“可证不是 main 实例”，直接放行。

   **与自述不符：**“`origin is not None and origin != O_UNKNOWN` 就是可证不是”不成立。问题来自来源标签的生成依据，不是 `_InstanceMain` 与字符串发生相等混淆。

2. **MEDIUM — 15 条新增负控的当前判红路径基本对应，但“判红”与“独立守住该规则”必须分开。**

   | 输入及所在行 | 当前判红路径 | 能否独立证明所称规则 |
   |---|---|---|
   | `(a)-1`，L2134 | 提取 `cm` → 直接构造判定，L1774–1775、L1705 | 不能证明 `cm` 专用分支；具名 fallback 也能提取 |
   | `(a)-2`，L2143 | 无可提取参数 → L1765–1772 | 成立，守住取不到参数时拒绝 |
   | `(b)-1`，L2152 | 展开两支 → main 实例拒绝，L1642 | 展开删除后仍被 unknown 拒绝 |
   | `(b)-2`，L2161 | 展开危险分支 → 直接构造拒绝 | 同上 |
   | `(c)-1`，L2170 | 海象值递归 → main 实例拒绝 | 递归删除后仍被 unknown 拒绝；不证明海象入表 |
   | `(c)-2`，L2179 | 形参 unknown，四豁免不命中 → L1657 | 成立 |
   | `(c)-3`，L2187 | partial-main 集合 → 收回 C2 豁免 → L1657 | 成立，L1124–1133、L1582–1583 |
   | `(d)-1`，L2199 | 工厂逐位表 → `c` 为 main 实例 | 删除表登记后 `c` 变 unknown，仍会拒绝 |
   | `(d)-2`，L2211 | `del` 加 unknown 绑定 → 构造来源不可证 | 成立，L750–757、L1696 |
   | `(d)-3`，L2221 | MatchAs 捕获加 unknown → 构造来源不可证 | 成立，但只覆盖 MatchAs |
   | `(f)-1`，L2232 | 重绑定使包装器失格 → 无隔离覆盖 | 成立，L1294 |
   | `(f)-2`，L2247 | yield 名不符使包装器失格 | 成立，L1298 |
   | `(f)-3`，L2261 | 同 key 资格冲突 → 失格 | 成立，L1258–1262 |
   | `(c)-4`，L2278 | Subscript 保持 `origin=None` → L1657 | 成立 |
   | `(e)-2`，L2287 | `m.other` 与 `m.app` 路径不同 → 无隔离覆盖 | 成立，属于放宽后的配对反例 |

   对归因变异的两条自述，核对结果是：

   **IfExp、NamedExpr 的自述成立。** 关闭展开或值递归，相关负例仍被 unknown 拒绝；正锚 b、c1 则会误报。只关闭 unknown 拒绝，保留展开和递归，`(b)-1`、`(b)-2`、`(c)-1` 仍会被明确的 main 实例／构造判定拒绝。但这只能说明这些输入有冗余，不能概括为全部 `(b)`、`(c)` 判定都有两层。

   **`cm=` 的归因说明不准确。** 单删 L1467–1469，L1470–1472 仍会取到 `cm`，正锚 a 也不变。禁用全部关键字提取后，负例由 L1765–1772“取不到实参”直接拒绝，**没有进入 `(c)` 三分**。因此需要原始变异文本才能解释作者的说法。

   还有以下未被独立守住的面：

   - **海象入表：**全表仅有的两个 NamedExpr 输入都直接递归值，没有后续读取目标名。删除 `_record_walrus` 不会被它们发现。缺少“先 `(app := production_app)`，后 `TestClient(app)`”这种输入。
   - **MatchStar、MatchMapping.rest：**L639–646 实现了，但唯一 match 输入是 `case [app]`，只覆盖 MatchAs。
   - **工厂逐位表：**负例不足以证明登记机制，但正锚 4、5、d2/d3 承重，已有正向约束。
   - **实例载体的属性路径：**正锚 e 直接调用 `TestClient(m.app)`，没有经过 `_InstanceMain.app_ref`；缺少先构造 `client`、再用 `no_lifespan(m.app)` 包住 `with client` 的正例。
   - **C3 的 AST／文本区别：**正锚 C3 完全没有 TestClient 文本，不能防止判据退回文本搜索；缺少“仅 docstring 含 TestClient”的正例。

   此外，L2128–2131 的“这些都是会跑真实 lifespan 的源码”不准确：`(d)-2` 先发生 `UnboundLocalError`；`(f)-1` 的 `a = app` 仍是原来的被隔离对象；`(f)-2` 的 yield 值被调用方忽略，实际进入的 app 仍处于隔离中。它们可以是保守规则的拒绝锚，不能全部计为真实 lifespan 漏检。该注释还残留“13/12”，当前新增区已有 15 条。

3. **HIGH — 解包逐位表缺少同 key 聚合，可以绕过同名工厂失格判定。**

   `_mark_factory_return_elts` 对一个函数内部的多条 return 做了列合并，却在 L1192 对函数 key 直接覆盖。调用侧 L814–817、L825–827 也没有检查 `disqualified_factory_keys`。

   因而，同名定义可以产生以下覆盖：

   ```python
   from app.main import app as production
   from fastapi import FastAPI
   from fastapi.testclient import TestClient

   if True:
       def make():
           return production, 1
   else:
       def make():
           return FastAPI(), 1

   def t():
       a, n = make()
       with TestClient(a):
           pass
   ```

   建表遍历两分支；同 key 的后一个安全定义在 L1192 覆盖生产来源。解包直接采用这张表，即使另一张工厂资格表已经将该 key 判为失格，也无法保护这个入口。

   **与自述不符：**“每一条 return 都满足条件”实际只覆盖**单个 FunctionDef**，没有覆盖相同 key 的所有定义。包装器的⑥没有同步保护逐位返回表。

   对题目点名的正例，通路核对成立：

   | 正例 | 通过的配对路径 |
   |---|---|
   | 锚 4，L2326–2335 | 工厂字面 tuple 登记 → L815–817 |
   | 锚 5，L2435–2445 | 同类方法 key → 工厂 tuple 表 |
   | 锚 d，L2529–2535 | 直接 RHS tuple → L810–813 |
   | d2/d3，L2541–2566 | 内层取得表，外层下一轮读取 frozen |

   常见等价写法仍有差异：

   - `return [FastAPI(), 1]` 在 L1188–1189 不登记，调用方解包成为 unknown，随后 `TestClient(a)` 被误拒；直接 RHS list 却受 L810 支持。
   - 同一函数多条等宽 return，仅来源不同的**那一列**在 L1192 变 unknown，其他列保留。差异只在未使用的 `n` 列，不影响 app 列；app 列混有生产来源时拒绝是合理保守判断。
   - 转调链长度问题见第 6 条，不能由 d2/d3 推广为任意长度均支持。

4. **LOW — 结构化载体与字符串标签的相等关系成立；“全部站点同批改”尚不能完整确认。**

   L342、L366 定义 NamedTuple；L376–382 用字段和 `isinstance` 读取、判型。它与 `str` 不相等，`__str__`（L368–369）不会改变相等关系；即使哈希碰撞，set 也不会把二者合并。

   已读的隔离站点 L1487–1543 均使用 `_ref_path`，没有发现 main 实例来源的前缀判型、切片取值或格式化后反解析。仍使用 `O_LOCAL_FUNC_PREFIX` 属于另一类来源标签，不是旧实例字符串编码残留。

   **成立范围：**已读站点及载体类型性质成立。`resolve_name`、`_attribute_origin` 和 `_value_origin` 的完整本体不在给定区段内，未取得 diff 时，不能为“所有读站点均同批修改”背书。

5. **HIGH — ⑥聚合成立，但④和⑤仍能错误授予隔离包装器资格。**

   **⑥成立。** L1252–1262 中，`None` 是吸收态：

   | 定义裁定序列 | 最终结果 |
   |---|---|
   | `None → 0` | `None` |
   | `None → None` | `None` |
   | `0 → 0` | `0` |
   | `0 → 1` | `None`，后续不能恢复 |

   它等价于“全部合格，且参数下标一致”，比单纯 `all(ok)` 多一个下标一致性条件。

   **⑤不成立：它没有检查包装器每一条 yield。** L1280 只收某个候选 `with` 体内的 yield，而且没有过滤嵌套函数；L1300 找到一个合格候选就返回。例如，采用标准 imports 后：

   ```python
   @contextlib.contextmanager
   def isolated(a):
       with no_lifespan(a):
           def unused():
               yield a
       yield a

   with isolated(app), TestClient(app):
       pass
   ```

   `unused` 从未执行。真正向调用方让出控制权时，隔离已经退出；静态判定却把嵌套生成器的 yield 当成隔离覆盖证据。普通的“一条分支隔离内 yield，另一条分支隔离外 yield”也存在同类问题。

   **④也有漏绑路径：嵌套函数默认参数的海象。** L589–597 遇到 FunctionDef 直接返回，跳过 L605 的海象登记；默认参数却在外层作用域执行：

   ```python
   @contextlib.contextmanager
   def isolated(a):
       def unused(x=(a := FastAPI())):
           pass
       with no_lifespan(a):
           yield a

   with isolated(app), TestClient(app):
       pass
   ```

   实际隔离的是新建局部 app；静态 `a` 仍只有形参的 `(0, 0)` 绑定，L1294 不会使其失格。

   **与自述不符：**“每一条 yield 都必须……”和“形参在包装器体内被重绑定即失格”均比实际检查面更宽。

   “旧版⑥此前不存在”及嵌套函数 `_factory_key` 是否撞模块级同名 key，仍需旧 diff／该函数本体，不能用新版注释当独立证据。

6. **MEDIUM — M16 状态比较补齐成立，但四轮不保证收敛；存在能区分重建与 add-only 的输入。**

   L549–565 确实把两个新增状态纳入比较；L1112–1114 确实冻结逐位表并重建两个容器。这部分成立。

   **四轮上限不够覆盖任意转调链。** 对：

   ```python
   def f0(): return FastAPI(), 0
   def f1(): return f0()
   def f2(): return f1()
   def f3(): return f2()
   def f4(): return f3()
   ```

   L1182–1187 每次只读上一轮：

   | 轮末 | 有逐位表的工厂 |
   |---|---|
   | 1 | f0 |
   | 2 | f0、f1 |
   | 3 | f0、f1、f2 |
   | 4 | f0、f1、f2、f3 |

   `f4` 要第五轮才取得表。L537 达到上限后没有未收敛处理；L568 最终 `_rebuild` 使用第四轮知识，故 `a, n = f4(); with TestClient(a): ...` 误拒。纯 tuple 转调因读取 frozen，两种定义顺序会相同地耗尽轮数；这不是整个 M16 已获顺序无关性证明。

   **能区分重建与 add-only 的输入存在。** 以下仅作手工逐轮推导：

   ```python
   def q():
       return FastAPI(), 1

   def q():
       return later()

   def later():
       return FastAPI(), 1, 2

   def mix(flag):
       if flag:
           return q()
       return FastAPI(), 1
   ```

   | 轮末 | q 表宽度 | 每轮清空时的 mix | 删除 L1113 清空时的 mix |
   |---|---:|---|---|
   | 1 | 2 | 无 | 无 |
   | 2 | 3 | 2 列 | 2 列 |
   | 3 | 3 | 无 | 保留旧 2 列 |
   | 4 | 3 | 无 | 保留旧 2 列 |

   第一轮 q 的第二个定义因 frozen 无 later 而不登记，保留首定义的两列表；第二轮 mix 读旧 q 得两列表；第三轮 mix 两条 return 宽度变为 3 和 2，L1190–1191 不再登记。**不需要 frozen 条目消失，就会出现“上一轮登记、下一轮不登记”。**

   因而，`a, n = mix(False)` 在两种实现下得到不同来源，后续 `TestClient(a)` 得到不同判定。

   **与自述不符：**L1109–1110 的结构性解释不成立。但这个反例不否定作者“当时那 40/23 条输入结论不变”的历史实测；正确结论是：**现有表没守住重建，而不是无法构造承重输入。**

   冻结变异的证据也需收窄：把 frozen 改为恒空，同时禁用了所有转调知识，不能单独隔离“冻结”机制。若改为读取本轮可变表并保留清空，应是 outer 在前的 d2 失败、inner 在前的 d3 可以通过；L2538–2539 把这个方向写反了，L1103–1105 的方向才正确。

7. **HIGH — C4 的依据直接不成立；C1–C3 也应区分安全证明与射程豁免。**

   **C4 是明确的同模块漏放面。** L854–864 只证明 base 来自模块 import，没有证明属性未在本模块写入。L773–792 的绑定目标处理又忽略 Attribute：

   ```python
   import contextlib as mod
   from app.main import app
   from fastapi.testclient import TestClient

   mod.client = TestClient(app)
   with mod.client:
       pass
   ```

   这里实例明确由本模块构造并写入模块属性；未知属性却可在 L1594–1595 因模块 base 获得豁免。

   **与自述不符：**L857–859、L1592 的“模块对象的属性不由本模块构造”是错误前提。导入模块对象，并不会阻止本模块修改其属性。

   其余三条分别是：

   | 窄化 | 核对结论 |
   |---|---|
   | C1，L1567–1572 | 即便接受基础 TestClient 没有 `__aenter__`，也不能推出任意 unknown 异步对象不会通过本地子类／代理调用同步 `__enter__`。判据覆盖面更宽；而已知 main 实例又在 C1 前先被拒绝。 |
   | C2，L1573–1584 | 作为声明过的跨函数射程豁免可以成立；作为“已证安全”不成立。代码豁免的是所有未命中 partial 集合的 unknown Call，没有进一步证明调用确实超出本模块可分析范围。 |
   | C3，L425–443、L1585–1590 | 实现是 AST 词法命中检查，不是真正的可达性证明。例如 `from fastapi import testclient as tc` 后用 `getattr(tc, "TestClient")`，可以取得类却不命中该检查。无需要求本卡扩展动态分析，但不能把这一豁免描述成“本模块构造不出实例”。 |

   C1–C4 各自确有一个正向通路锚（L2455–2482），这部分成立；这些正例没有证明豁免边界安全，更没有守住 C4 的本模块属性写入情形。

8. **LOW — 表项数量可以核对；旧版差异和运行裁判数据不能在本次读取条件下独立确认。**

   当前表确有 **40 条 must-flag、24 条 must-pass**。但本次没有取得指定 diff，也没有运行或读取裁判输出，因此以下仍是作者报告：

   - 新增 15 条中 14 条改前漏检，及 e／d 两条既有误判；
   - ExceptHandler 改前已覆盖、包装器⑥改前不存在；
   - 12/12 归因变异、40/24 PASS、385 文件零违规、36/36 探针及 Ruff／Pyright 结果；
   - 排除面在 diff 中未变，以及当前文件与 `6d6e3e09` 逐字节一致。

   此外，`_factory_key`、`resolve_name` 和部分来源解析实现没有落在已提供的完整读取区段里。对嵌套 key 碰撞和全部来源消费站点，应保留“未核验”，不能写成成立。

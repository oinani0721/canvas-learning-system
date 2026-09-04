# CARD-G6-2b round-5 定向复审（交互复习壳 /overview/app）

你是本仓库的独立代码审查者。请只做**代码正确性与测试有效性**的判断，不写实现、不改文件。

## 仓库与范围

工作树（只读）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b`

审查范围 = 下面这条命令的输出（两个文件，其余一概不看）：

```
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b
git diff 7ca194ac..HEAD -- backend/app/api/v1/endpoints/review_app.py backend/tests/unit/test_review_app.py
```

需要读全文时：
- 产品代码 `backend/app/api/v1/endpoints/review_app.py`（538 行左右，单文件内联 HTML+JS 的只读页面）
- 测试 `backend/tests/unit/test_review_app.py`

## 这段范围为什么这么划

- 上一轮（round-4）审的是 `7ca194ac`。此后到 G6-2 车道收尾 `52b9aa9b` 之间还有一段**从未被复审过**的量：
  `review_app.py` 35 增 10 删、`test_review_app.py` 160 增 16 删（`git diff --numstat 7ca194ac..52b9aa9b` 实测）。
  该段已随 squash 进主干，且 `52b9aa9b` 与主干 `1f249b33` 的这两个文件**逐字节相同**。
- 本卡（G6-2b）在主干基线之上又做了三件事，也在范围内：
  1. `renderCards()` 现在把「失联通知」一起拼进卡片区，且 `poll()` 成功路径的最终帧改为调用 `renderCards()`（帧形态单一来源）；
  2. 测试里的 AST 静态检查门从测试函数体提取为模块级 `_assert_module_closed(src)`，并补齐 for / with…as / except…as / 海象 / 推导式目标 / `def`·`class` 名 / `match` 捕获 这些**绑定形态**，以及 Lambda 的 posonlyargs·kwonlyargs·vararg·kwarg 四类参数；
  3. 新增 17 条内存探针 + 一条验伪锚测试。

所以本轮要回答的是：**这一整段（round-4 未审量 + 本卡改动）合起来，有没有引入产品缺陷或让既有的门失效。**

## 已裁决清单（round-2 / round-3 已 VERIFIED，请勿再计为发现）

1. `Object.create(null)` 容器防御（`state.notes` / `inflight` / `pendingSync` / `freshNotes` 产物）——已裁决成立。
2. 状态元数据的 own-key 检查（`Object.prototype.hasOwnProperty.call(STATUS_META, …)`）——已裁决成立。
3. 自动轮询绝不发 POST，只有手动按钮发——已裁决成立。
4. `_extract_script` 的「脚本结束标签恰好一处」提取链（含大小写、solidus、带属性、`</scriptx` 前缀这些形态）——已裁决成立。

对这四条的重复指认不计入本轮结论。

## 请重点核的几件事

1. `renderCards()` 现在被四个地方调用（结算兜底、POST 反馈重绘两处、poll 最终帧）。这次把「失联通知」并进去之后，有没有哪条路径变成重复渲染、丢帧、或者拿到不该拿的 `state.lastData`？`poll()` 里把最终帧换成 `renderCards(nowMs)` 是否与原来的 `renderPage(data, …) + lostSyncNotesHtml(data, …)` 逐帧等价（注意上一行刚做过 `state.lastData = data`）？
2. 结算的因果锚（`settlePendingSync` 的 `startMs < n.atMs` 跳过）与代际守卫（`state.pollGen`）配合下，是否还存在「重建前的投影被当成重建后状态」或「反馈永远结算不掉」的时序？
3. 新的 AST 检查器：`in_function` 的构造改成了「作用域根自身不计入」，并把 `ClassDef` 也算作作用域根；模块级 `def _js_json` 靠一份 `_OWN_DEFINITIONS` 豁免。这套判定有没有反过来放过某种遮蔽，或者误伤某种合法写法？枚举的绑定形态还缺哪一类？
4. 三张调用白名单（`_ALLOWED_IMPORTS` / `_ALLOWED_CALL_NAMES` / `_ALLOWED_CALL_ATTRS` / `_ALLOWED_RECEIVERS`）的**取值**与基线相比是否被放宽（应当逐字未变，只是加了 `_` 前缀并移到模块级）。
5. 新增的 17 条探针：有没有哪一条其实是被「白名单外调用」之类的**别的**规则拒掉的（那样它就证明不了被测的那条规则）？验伪锚（未注入的真实源码必须放行）是否足以排除「门恒红」这种平凡满足？
6. round-4 未审量里那 160 行测试新增，有没有形态上就不承重的门（断言恒真、前提没被验证、桩把被测逻辑一起替换掉了）。

## 输出格式（严格）

只输出两类条目，按严重度排列：

- **阻断级**：会让用户看到错误内容 / 让某道门实际不承重 / 让白名单被架空的问题。每条给：文件:行、你的判断、以及能证伪它的最小场景。
- **登记级**：值得记账但不阻断合入的问题。

每条都要能被一条具体的代码路径或输入支撑；拿不准的写「不确定 + 需要什么才能确定」，不要为了凑数写泛泛的建议。

最后一行必须是这一行，二选一，不要加别的字：

```
BLOCKER/HIGH 清零：是
```
或
```
BLOCKER/HIGH 清零：否
```

---

绑定 SHA：`27e61454`（本卡最终 tip；此后若有 docs-only 提交，代码树不变）。

## 这是重发（第一次因传输层断连没产出正文）

第一次运行到最后被网络切断（`tls handshake eof` → 重连 5 次 → 回落 HTTPS 仍断 → rc=1），
正文 0 字节。但那次运行的 stderr 里留下了你自己构造并跑完的 11 条用例，已被逐字还原，
并据此对 AST 检查器做了整改。**整改内容也在本次审查范围内**（`git diff 7ca194ac..HEAD`），
请重点看这批新逻辑有没有引入新问题：

1. `_OWN_DEFINITIONS` 豁免收紧为三条：只在模块级 / 只对 `ast.FunctionDef`（不对 `ClassDef`）/
   每个受保护名至多一个定义点（新增 `definitions` 计数字典，函数末尾断言）。
2. `init` 豁免不再覆盖 `ast.AugAssign`。
3. `ImportFrom.level` 非零一律拒（禁相对导入）。
4. `decorator_list` 里的裸 `Name` / `Attribute` 装饰器纳入调用白名单检查。
5. 赋值目标是 `ast.Attribute` 一律拒；赋值右侧是受保护名的裸 `Name` 一律拒。
6. `ast.TypeAlias` 走绑定检查，`TypeVar`/`ParamSpec`/`TypeVarTuple` 走遮蔽检查
   （节点类用 `getattr(ast, …)` 取，低版本上是空元组）。
7. `_flag_targets` 只认 `ctx` 是 `ast.Store` 的 `Name`（修正「下标读取被当成重绑定」的误伤）。

具体要判断的是：
- 第 7 条只缩小误伤面、没有放松任何真绑定的检测吗？有没有哪种绑定形态的目标 `Name` 其 `ctx`
  不是 `Store`，因而被这一改放过去了？
- `definitions` 计数的口径对不对？它统计的是「享受了豁免的名字」，会不会漏计或多计？
- 第 5 条会不会误伤某种合法写法？
- 这批规则合起来，还有哪个**维度**没被覆盖（前七条是按你上次那 11 条用例补的，用例本身可能
  也不完备）。

另外，负向探针表现在断言的是**各自的拒因关键词**而不是笼统的「被拒了」，还新增了 4 条反向
探针（合法写法必须放行）。请判断这两张表合起来，是否足以支撑「门既够严又没坏」这个结论。

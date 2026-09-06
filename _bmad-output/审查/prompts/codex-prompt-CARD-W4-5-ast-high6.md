# 独立复核请求 — CARD-W4-5-ast-high6（W4-⑤ AST 门 6 条加固）

## 一 背景与最小读取面

`backend/scripts/lifespan_isolation_negative_control.py` 里有一道**静态 AST 门**。它扫描 `backend/tests/**`（除 `integration` / `e2e` 两个顶层目录）的源码，判定其中有没有「会让真实 FastAPI lifespan 跑起来」的 `TestClient` 用法——因为真实 lifespan 会去连生产 Neo4j。门只做静态分析，不跑测试、不连库。

上一轮外部审查列出 5 条 HIGH 加 1 条「不可证即放行」的分支，说这道门有六个**未覆盖的判定路径**。本卡按 (a)–(f) 六条逐一加固，并把 `_AST_MUST_FLAG`（负控输入表，每条都必须被判违规）从 25 条加到 40 条、`_AST_MUST_PASS`（对照输入表，每条都必须判合规）从 13 条加到 24 条。

**请只读以下内容，不要读工作区其它文件，不要运行任何命令、测试或端口连接：**

1. 本卡 diff：`git diff <本卡开工 SHA> HEAD -- backend/scripts/lifespan_isolation_negative_control.py`（+939 / −107）
2. 该文件（改后共 3152 行）的这几段：
   - `:312-470` — 常量与来源标签：`AST_EXCLUDED_TOP_DIRS` :312、`_ENTER_CONTEXT_CM_PARAM` :323、`_IFEXP_MAX_DEPTH` :325、`_InstanceMain` :342、`_instance_main` :372、`_ref_path` :385、`Origin` :406、`O_IMPORTED_MODULE` :415、`_MODULE_OBJECT_ORIGINS` :422、`_module_has_testclient` :425
   - `:510-583` — `_ModuleIndex.__init__` 与 M16 不动点循环（`for _ in range(4)` :537，迭代状态元组与收敛比较紧随其后）
   - `:585-870` — 作用域构建与绑定表：`_walk_stmt` :585、`_record_match_captures` :630、`_own_exprs` :648、`_record_walrus` :664、`_record_bindings` :688、`_bind_target` :773、`_unpack_element_origins` :794、`_callee_factory_key` :820、`factory_returns_any_main` :837、`attribute_base_is_module` :854
   - `:1071-1330` — `_mark_main_client_sources` :1071、`_mark_factory_return_elts` :1146、`_mark_isolation_wrappers` :1190、`_isolation_wrapper_index` :1260
   - `:1449-1782` — `_enter_context_arg` :1449、`_unprovable_context_exempt` :1556、`_flag_instance_context` :1595、`analyze_source` :1661（内含 `check_with_ctx`）、`ast_scope_files` :1777
   - `_AST_MUST_FLAG` :1811-2291 与 `_AST_MUST_PASS` :2293-2565 **全文**

## 二 作者自述（请独立核对，不要默认成立）

**(a) `enter_context` 关键字面**（`_enter_context_arg` :1449，调用点在 `analyze_source` 的面 3）。旧代码是 `if not node.args: continue` —— 只看位置参。新实现按「位置参 → `cm=` → 第一个具名关键字」取，取不到（例如只有 `**kwargs` 展开）时**判违规**而不是 continue。

**(b) 条件表达式面**（`check_with_ctx`，在 `analyze_source` :1661 内）。旧代码对 `with` 的 `context_expr` 只分「是不是 `ast.Call`」两支，`ast.IfExp` 落进 else 支后解析不出来源、被静默放行。新实现对 IfExp 的 body / orelse 各判一次（任一支判违规即记），嵌套递归，超过 `_IFEXP_MAX_DEPTH`=8 层时判违规。

**(c) 不可证即放行改三分**（`_flag_instance_context` :1595、`_unprovable_context_exempt` :1556）。旧代码 `if origin is None or not _is_instance_main(origin): return` 是一个静默放行分支。新实现分三态：可证是 `app.main` 的 TestClient 实例 ⇒ 违规；可证不是 ⇒ 放行；**不可证 ⇒ 违规并标 fail-closed**，除非命中四条窄化之一（C1 异步上下文协议 / C2 调用面归属跨函数盲区 / C3 模块内无 TestClient 可达性 / C4 import 来的模块的属性）。

自述的实测数据：不设任何窄化、一律 fail-closed 时，全仓 385 个文件里 196 个会被判违规（1453 条），其中 194 个文件的条目形态是 `with pytest.raises(...)` / `with open(...)` / `with patch(...)`。C3 的判据刻意用 AST 可达性而不是文本查找，理由是 `tests/support/live_port_guard.py` 里 `TestClient` 只出现在 docstring（该文件 :34 / :54），文本判据会把一个零 TestClient 节点的文件当成有可达性。**卡文的止损口径是「新增违规文件 > 12 个则拆卡」，实测触发结果为 0 个新增违规文件，止损未触发。**

**(d) 绑定表补四类 + 解包收窄**（:630 / :664 / :688 / :773 / :794）。补了海象 `:=`、`del`、match-case 的捕获名（`MatchAs` / `MatchStar` / `MatchMapping.rest`）；`ExceptHandler.name` 经核对**改前版本已覆盖**（旧文件 :499-503 那段 `getattr(sub, "name", None)`，改后在 :614-618），未重复实现；同一段对 `match_case` 恒取不到（`match_case` 没有 `.name` 属性），这才是 `MatchAs` 族此前整族漏绑的原因。解包从「整体来源原样传给每个元素」改成逐位配对：右侧是字面 tuple/list 且等长，或右侧是本模块工厂调用且 `factory_return_elts` 有等宽逐位表，才按位取；否则每个元素一律 unknown。带 `*` 的目标一律放弃配对。

**(e) provenance 换结构化载体**（:342 / :372 / :385 / :406）。`"testclient:instance(app.main):<name>"` 字符串编码换成 `NamedTuple`，消掉了取值用的切片与判型用的 `startswith`；`app_ref` 从「只认 `ast.Name`」扩到「来源可证的属性链」（`m.app`），隔离比对两侧都改用 `_ref_path`。所有读该来源的站点已同批改（`_instance_app_name` / `_is_instance_main` / `_item_isolates` / `_isolation_sibling_covers` / `_isolation_enclosing_covers` / `_isolation_enclosing_covers_name`）。

**(f) 包装器资格加三条**（`_mark_isolation_wrappers` :1190、`_isolation_wrapper_index` :1260）。原有三条之外加：④ 被隔离的形参在包装器体内被重绑定 ⇒ 失格；⑤ 每一条 `yield` 递出去的必须**就是**被隔离的那个名字（`yield from` 一律失格）；⑥ **同名多定义时任一定义不合格、或两个定义的形参下标不一致 ⇒ 整个 key 失格**，集合每轮重建。

作者对 ⑥ 的说明：卡文原文写的是「在『同名多定义任一不合格 ⇒ 整 key 失格』**之外**补两条」，即卡文假定包装器侧已有该口径；作者实测发现**此前并不存在**（旧实现是 `self.isolation_wrappers[key] = idx` 的 add-only 覆盖），因此把它作为 ⑥ 一并补上。请独立核对这个「此前不存在」的判断是否成立。

**(g) 两张表**：`_AST_MUST_FLAG` 25 → 40，`_AST_MUST_PASS` 13 → 24。作者实测（两个独立进程分别加载改前版本与改后版本，负控输入源码由 AST 从改后文件同一处提取，两侧同源）：新增 15 条 must-flag 里有 **14 条改前判 0 条违规、改后判违规**；剩下 1 条（`(e)-2`）改前改后都判违规，作者已在代码注释里标注它是 `验伪锚 e` 的配对项、不计入那 14 条。must-pass 侧另有 2 条改前判违规、改后判合规（`验伪锚 e` 与 `验伪锚 d`），作者称那是 (e)(d) 修掉的既有误判。

**(h) M16 不动点**（:537 起）。新增的 `factory_return_elts` 与 `partial_main_client_funcs` 两个迭代状态已写进 `before` 元组与收敛比较；两者都在 `_mark_main_client_sources` :1071 开头**每轮重建**，且逐位表的求值读的是**上一轮冻结副本**。

作者对证据强度的自述（请核对是否诚实）：`_mark_main_client_sources` 开头的注释把「冻结求值」标为**承重且有门**（变异实测：frozen 改成恒空 ⇒ 验伪锚 d2/d3 当场翻红），把「每轮重建」标为**防御性纪律、本卡没造出能看见它的输入**（变异实测：删掉那行清空退回 add-only ⇒ 40 条反例与 23 条正例全部不变）。请核对后一句是否属实——即是否存在某个输入能让 add-only 与每轮重建给出不同结论。

**裁判结果**：负控 `AST-NEGATIVE-CONTROL: PASS (40 / 24)`；全仓重扫 `0 violations in 385 files`；探针 `36/36`（该文件本卡零改动）；`AST_EXCLUDED_TOP_DIRS` 与 `ast_scope_files` 的排除面未动（diff 中无这两处）；`ruff format --check` 与 `ruff check` 通过；`pyright` 5 errors / 0 warnings（改前版本 6/0）——本卡新增 0 条、消除 1 条存量，且 5 个报错行与本卡 diff 新增行交集为空。

**(i) 归因变异（作者自加的一道裁判，请一并核对其结论是否可信）**。作者对每条新规则各做了一个「只关掉这一条」的变异体（写临时文件，不改生产文件；每个变异断言锚点 `count == 1`，变异后先 `ast.parse` 自检），看它点名的反例是否变成不被判违规。作者报告 **12/12 成立**，并附了两条自我更正：

* 「取 `cm=`」/ IfExp 展开 / NamedExpr 递归这三条，关掉后对应的**反例照样被判违规**——被 (c) 的三分兜住，只是理由从「它是 app.main 的 client」退化成「来源不可证」。作者据此声称这三条的承重在**正例**侧（`验伪锚 a` / `b` / `c1`），并为 NamedExpr 递归**新补**了 `验伪锚 c1`（此前三条里只有它没有承重锚）。
* 关掉 (c) 三分时，`(b)-1` `(b)-2` `(c)-1` 仍被判违规，作者据此声称 (b) 与 (c) **互为冗余**、各有两层。

请核对这两条自述是否属实，以及是否还有别的新规则同样属于「反例证明不了它、承重其实在正例侧」——那类规则如果没有对应正例，就是没有门。

## 三 请按重要性核对以下问题

1. **(c) 的三分里是否仍有静默放行的路径**。请沿 `_flag_instance_context` :1595 逐个分支走：`ast.NamedExpr` 递归、`ast.Name`、`ast.Attribute`、`ast.Call`、以及**四种都不是**的表达式（例如下标、字面量、`await`、比较式）各自会落到哪里，最终是判违规还是返回。特别请核对 `origin is not None and origin != O_UNKNOWN` 这一句：`Origin` 现在是 `str | _InstanceMain` 的联合类型，有没有哪个来源标签会让「可证不是」这一分支吞掉本该 fail-closed 的输入。
2. **新增的负控输入是否因作者声称之外的原因被判违规**。15 条新 must-flag 每条只需要「有违规」就算通过，但作者声称的是「因为 (a)–(f) 里那一条规则」。请核对每条负控输入触发的是不是它对应的那条规则——如果某条其实是被别的既有规则拦下的，那么它对应的新规则就没有真正被这张表守住。
3. **(d) 的解包收窄会不会误拒对照输入**。`_unpack_element_origins` :794 只在两种形态下配对，其余一律 unknown。请核对 `_AST_MUST_PASS` 里的「验伪锚 4」「验伪锚 5」「验伪锚 d」「验伪锚 d2/d3」是靠哪条配对通过的，以及现实里常见的等价写法（例如工厂 return 的是 list 而不是 tuple、转调链长度 ≥3、或者同一工厂有多条 return 且宽度相同但某一位来源不同）会不会变成误判。

   作者已自查出并修复了一处：`def outer(): return inner()` 且 `inner` 返回 tuple 时，只认字面 tuple 会让 `app, n = outer()` 误判违规（改前反而放行）。修法是在 `_mark_factory_return_elts` :1146 加转调支，读**上一轮冻结**的表（`frozen` 参数），并加了验伪锚 d2/d3 两个定义顺序。请核对转调链更长（三层以上）时 4 轮迭代够不够。
4. **(e) 的结构化载体，读该来源的站点是否真的全部同批改**。请在指定读取面内查找是否还有地方按字符串形状判断来源（前缀比较、切片、`in` 判断、格式化后再解析），以及 `Origin` 联合类型进 `set` 做「全部绑定必须同源」比较时（`resolve_name` 附近）有没有 `_InstanceMain` 与某个字符串常量相等的可能。
5. **(f) 的 ⑥ 是否真的补住了同名重定义**。请核对 `_mark_isolation_wrappers` :1190 的聚合逻辑：`if key in verdicts and verdicts[key] != idx` 这一句，在「第一个定义不合格（idx=None）、第二个定义合格（idx=0）」与「两个定义都不合格」这两种情形下分别得到什么结果；以及这与 `_mark_all_fastapi_returning` 那边 `verdicts[key] = verdicts.get(key, True) and ok` 的口径是否等价。另请核对 `_factory_key` 对**嵌套函数**给出的 key 会不会与模块级同名函数相撞。
6. **(h) M16 不动点是否仍收敛**。`factory_return_elts` 每轮重建、而 `_rebuild` 又在轮首用它建绑定表，两者互为输入。请核对 `for _ in range(4)` 这个上限内能否收敛，以及不收敛时最终 `self._rebuild(tree)` 用的是第几轮的知识、这是否会让同一段源码因函数定义顺序不同而得到不同结论（M16 原始缺陷的形态）。
7. **(c) 的四条窄化各自是否可证**。C1 依据「Starlette TestClient 没有 `__aenter__`」，C2 依据「跨函数传递是已声明盲区，但本模块内可证的部分由 `factory_returns_any_main` 收回」，C3 依据「模块 AST 内无 TestClient 节点则本模块造不出 TestClient 实例」，C4 依据「import 出来的是模块对象」。请指出其中哪一条的依据在本文件的实现下并不成立，或者哪一条的判据面比它的依据更宽。

## 四 输出格式

逐条编号，每条给：**严重度（BLOCKER / HIGH / MEDIUM / LOW）** + 一句话结论 + 支持它的**文件行号**（绑定本次读取面）+ 你认为作者自述里哪一句与代码不符。若某条问题核对下来作者自述成立，也请明确写「成立」并说明你核对的路径，不要略过。

## 五 边界

- 只读。不要修改任何文件、不要运行 pytest、不要连接任何端口或数据库。
- 以下文件**不在本卡范围**，即使你在读取面里看到对它们的引用也不必审：`backend/tests/support/live_port_guard.py`、`backend/tests/conftest.py`、`backend/tests/support/guard_plugin.py`、`backend/scripts/lifespan_isolation_runtime_sha.sh`、`backend/scripts/lifespan_isolation_guard_probes.py`（本卡对它零改动）。
- 门的射程与排除面（`AST_EXCLUDED_TOP_DIRS`、`ast_scope_files`）本卡不动，扩大射程不在本卡范围。
- 运行时是否真的没有连接，由另一套变异运行的裁判承担，不在本卡范围。

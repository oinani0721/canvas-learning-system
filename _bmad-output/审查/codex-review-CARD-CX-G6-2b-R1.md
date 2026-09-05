> 批次: BATCH-2026-09-05-第十一批 · Z1 · CARD-CX-G6-2b-R1 round-3（首部由主 session 2026-09-05 按协议 §2.1 补记，正文一字未改）
> 模型: `gpt-6-astra`（stderr 实测） · reasoning_effort: `ultra`（stderr 实测） · codex: 未自证（stderr 无版本行）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`（第十一批手册规定形态；实参见车道 stderr）
> 审查绑定: `92734207 → d9f7b544`（审后 3d30bde6 / 8e8fd737 共 +173 行零外审 → 第十二批 Y5-A 复审）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b` / `model: gpt-6-astra`

---

## 结论摘要

**不能清零：代际比较能解决所测的因果错位，但状态结算和 AST 检查器仍有可复现的漏网。** 当前相对 `HEAD` 的 backend 差异为空；相对 `92734207`，确为测试文件 **+34/-0**，生产文件完全相同。指定测试在使用现成可用的 Node v24.16.0 后得到 **146 passed**；拦截证据写出的重放也通过了 16 条新探针、5 组定向变异及两条代际实验。以下发现区分本次新增限制、既有检查器漏洞和证据推论边界，不重复列入已裁决事项。

## 逐条发现

### [HIGH] 上一次重建的 pending 会覆盖同库下一次刷新失败

- 位置: [review_app.py:403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_app.py:403)，另见同文件 :491、:501、:508、:517。
- 事实: `inflight` 在 POST 完成后即清除，补发 GET 可以仍在飞。内存执行真实 JS，复现“POST1 重建成功 → GET2 挂起 → POST2 返回 HTTP 503 → GET2 成功返回”：页面先显示第二次刷新失败，随后变成第一次重建的“数字已更新”，最终卡片也不再包含第二次错误。
- 影响: GET2 对旧 pending 的代际比较完全合法，却无权代表用户最新一次操作。这是遗漏的**反馈归属前提**，现有门没有覆盖。
- 建议: 新一次同库刷新开始时，使被取代的 pending 失去覆盖当前反馈的权利，并增加上述交错顺序的验收。无需改变代际锚或引入第二套时间锚。

### [HIGH] 间接取别名仍可改写受保护对象

- 位置: [test_review_app.py:390](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:390)，另见 :353、:366。
- 事实: 别名禁令只处理赋值右侧恰为 `ast.Name` 的情况。布尔表达式、元组解包、海象及循环取得 `json` 别名，再通过别名写 `dumps`，均被当前检查器放行。隔离进程实测别名与 `json` 是同一对象，写入后，原样提取的生产 `_js_json()` 返回了替换后的错误结果。
- 影响: “根名不受保护，所以是普通对象”并不成立。本次收紧堵住直接复合根，没有堵住先转存引用再写入。
- 建议: 对受保护对象的引用传播建立明确限制或别名追踪，并补相应反例；不能仅凭目标根名决定对象身份。无需放宽白名单。

### [HIGH] 链式装饰器漏检能够执行白名单外函数

- 位置: [test_review_app.py:454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:454)，尤其 :458。
- 事实: 独立探针通过 `review_app_router.routes[0].endpoint.__globals__` 取得普通类，再将其引用内建 `print` 的 `get` 属性作为装饰器，检查器放行。使用真实 `APIRouter` 的隔离运行实际打印了函数对象，装饰后的名字变成 `None`；直接 `@print` 原本会被拒。此路径不依赖上一条别名写入漏洞。
- 影响: 中间路径漏检已经形成实际隐式调用绕过，不能只登记为两处分支口径不同。
- 建议: 校验装饰器的完整接收者路径，拒绝未经允许的中间属性及下标穿透，并增加同一 Attribute 分支内的对照探针。

### [HIGH] `Request` 绑定可以被替换，注解豁免并未证明可信接收者

- 位置: [test_review_app.py:256](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:256)，另见 :494、:505。
- 事实: `Request` 不在受保护集合中。将其绑定到 `str` 后添加同形态端点，检查器仍放行；实际 FastAPI 将参数识别为字符串查询参数，`request_param_name=None`，调用处理函数时 `.url_for` 产生 `AttributeError`。此外，`Request.__class__`、`Request[0]` 注解也被放行，“只认裸 Name”的新增声明不准确。
- 影响: 检查器把名字拼写当成了类型身份。这是**漏网**，与已裁决的合法注解误拒是不同问题。
- 建议: 保护豁免所依赖的 `Request` 绑定，并准确约束接受的注解节点形态；既有误拒范围仍可按裁决留待后续处理。

### [MEDIUM] 新判据会拒绝正常的复合表达式写目标

- 位置: [test_review_app.py:361](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:361)，反向探针在 :620。
- 事实: 六条反向探针没有覆盖非 Name 根上的普通对象写入。实测：根据条件选择两个普通缓存之一，再向其中写入下标，不涉及保护名或新增调用，也被“根不可解析”拒绝。
- 影响: 正常重构可能撞门。真实源码放行只证明当前源码兼容，不能证明没有误拒。
- 建议: 将其明确登记为保守的语法限制；若以后允许此类正常演进，再建立可证明安全的接受条件及反向探针。本卡不必为消除误拒而仓促收宽。

### [MEDIUM] 变异后对照把检查器异常也算作正常拒绝

- 位置: [probe_r1.py:60](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/_bmad-output/审查/evidence-g62b/probe_r1.py:60)，另见 :329、:338。
- 事实: 判决包装捕获所有 `BaseException`；变异前检查拒因关键词，变异后对照只要求结果非空。因此只在对照路径出现的 `NameError`、`TypeError` 也能被记为“仍红”。
- 影响: 现有控组可以排除整门恒绿，不能一般性排除局部分支损坏。本次实际输出中的对照拒因正常，因此这一缺陷不直接推翻已重放的矩阵结果。
- 建议: 变异后对照也应验证异常类别和拒因身份；将“独家承重”限定到指定探针与指定变异。

### [MEDIUM] 通用 Node 裁判仍允许零测试收集假绿

- 位置: [test_review_app.py:818](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:818)，同毫秒门在 :1952 使用它。
- 事实: `_assert_node_green()` 仅检查退出码和非零 skip；退出码为零、输出为空或测试计数为零，均可满足判据。`probe_r1_gen.py` 自己增加的 `2/0/0` 校验没有覆盖这个公共入口。
- 影响: 测试意外未收集时，正式 JS 门可以报绿。
- 建议: 校验实际测试数量、通过数量及取消情况。历史负控含明确断言失败，不能据此反推它当时空跑。

### [LOW] 判别脚本即使失败仍会生成肯定的结论段

- 位置: [probe_r1_gen.py:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/_bmad-output/审查/evidence-g62b/probe_r1_gen.py:244)。
- 事实: “代码 B 说是对的”结论无条件加入报告，未受 `ok` 控制；上方结果和最终退出码另行判断失败。
- 影响: 退出码不会因此假绿，但单读报告结论可能得到与实验结果相反的判断。
- 建议: 根据实验成功、失败或无法执行分别生成结论。

## §三 六个问题的逐项答复

**1．部分成立。** 前提①在 JS 安全整数范围内成立：实际只有初始化与前缀自增两个写点，未见 state 别名；依据是写点检查，`const` 本身不能保证属性不变。前提②应精确为 **`await resp.json()` 完成后的同步续段读取代际**，不是 fetch 响应头返回瞬间；实验实际挂起的也是 `json()`。固定其余代码，比较“POST 发出前取值”和当前实现，实验确能区分，隐藏页面以阻止 gen3 干扰也设计正确；但仅凭黑盒结果还不能排除“隐藏时禁止结算”等其他实现，需要结合已读源码排除。前提③的绝对说法不成立：隐藏启动仍发首轮 GET，源码及现有测试明确保留该行为；回前台会启动更大代际，但活性还要求某个未过期 GET 最终完成，当前无请求超时且完成后才排下一轮。乱序 GET 的成功和失败均有过期守卫，不同 vault 独立比较各自 `n.gen`，可见性翻转不破坏这一安全性；同库真正并发 POST 被拦截，但跨 POST/GET 阶段的重叠存在第一条 HIGH。另一个遗漏前提是**服务端发布可见性**：POST 的 rebuilt 必须意味着发布完成，后启动 GET 必须看见该结果；正向对照仍返回 `PRE` 却结算成功，说明实验没有验证这一契约。

**2．部分成立。** 新判据对三类直接复合根的收紧有效，保留 `_root_name()` 的既有返回语义是合理的局部修改。但六条反向探针与真实源码锚不足以覆盖误拒，正常缓存选择写入已经构成反例；同时，间接别名反例表明它也没有完成对象写保护。应分别声明语法限制与仍存在的漏网。

**3．部分成立。** E-dupes、C1b 对各自指定探针的局部必要性成立；C2 成立的是三类检查的**组级承重**，没有证明每行分别不可替代；C4 的精确替换及实际输出足以支持接收者断言对 `@Foo.get` 承重，但控组均在 Attribute 分支之外，单靠控组不能排除整个 Attribute 分支被放空。精确单次替换、真实源码锚、目标红转绿及正常拒因共同支持本次结果；“对照仍红就证明检查器没有被弄坏”的一般推论不成立。

**4．成立，但须限域。** 文档中的当前版—真实旧版—还原版结果、同毫秒失败的具体断言，以及 `92734207` 中集中于因果锚的生产差异，能够支持：**相对该旧实现，在这三道点名门中，同毫秒门有额外检出力**。不能外推到整个测试集合中的唯一性，也不能证明所有时间戳实现都会失败或当前状态机全面正确。三阶段历史哈希是本次读到的记录，我未重新换盘见证。

**5．部分成立。** 装饰器分支差异登记的事实正确，但“仅登记”的定级不恰当，实际白名单外调用已经复现。合法 `request` 注解被误拒仍可遵循既有裁决，不要求本卡收宽；不过“只接受裸 Name”及“四种均为等价合法注入”不是已证事实：除上述宽于声明的接受形态外，本树 FastAPI 实测 `Annotated[Request, Depends()]` 被解析为普通依赖，普通 GET 得到 422，不能与直接 Request 注入等同。

**6．部分成立。** 还有几处应收窄表述：生产 `_js_json(1)` 返回字符串，给其返回值写 `.dumps` 不会修改受保护对象，因此三条新探针并非都证明真实对象改写；另外两条足以支撑修复动机。`probe-matrix.md` 比较的是 `1f249b33`，其中三条复合根在基线均被拒，不能用该“改前”列证明 `92734207` 下放行，正确证据是 C1b 重放。三个脚本会写证据或临时文件，且 `probe_matrix.py` 没有首尾哈希检查；“磁盘文件不碰”“三个脚本各自哈希自证”均过宽。首尾哈希相同也只能证明采样时字节一致，不能单独证明中途从未修改。

## 我没有验证的部分

- 未读取清单外的项目源码、历史审查或生产发布实现；测试运行自身的导入与 fixture 执行不等于人工审查这些文件。
- 未重跑 `probe_matrix.py` 的历史基线矩阵，未重新换入 `27e61454` 执行负控。
- 未验证真实浏览器调度、服务端投影发布及后续 GET 的可见性，也未穷举所有并发顺序。
- 两份证据脚本采用拦截证据写出的方式重放，并非原命令逐字执行；原证据与两份源码哈希保持不变。首次测试因默认 Node 缺动态库失败，使用已有 Node v24.16.0 后完整通过，未修环境或修改代码。

BLOCKER/HIGH 清零：否

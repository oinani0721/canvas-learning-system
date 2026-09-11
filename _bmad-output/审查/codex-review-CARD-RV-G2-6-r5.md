> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-RV-G2-6 round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-G2-6-r5.md)"`
> 审查绑定: `ee18eb44` = **本卡最终 HEAD**（`git diff --stat ee18eb44 HEAD -- . ':(exclude)_bmad-output'` 为空，本轮之后**未再改代码**）
> ⚠️ **本轮仍有 2 HIGH，卡族轮次已用满 5 轮 ⇒ 按协议 §1 停手，车道不自判通过，交主 session 人审。**
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**round-5 结果：0 BLOCKER / 2 HIGH / 6 MEDIUM / 2 LOW。仍不能自判通过，应按轮次上限交主 session 人审。**

项目证据限于指定五处。当前校验器的 Git blob 与 `ee18eb44` 中的版本一致。未修改工作树、运行安装脚本、连接数据库或访问 live vault；权限及设备节点案例仅作静态推导，未创建夹具。

下文行号缩写：[V＝scripts/verify_vault_install.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py)，[T＝测试文件](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py)，[R＝复审结论表](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md)。

**BLOCKER：0。**

未发现本轮新增的被审对象写入分支；报告创建、短写循环、替换及失败清理逻辑未被这轮改动破坏。这是源码核对结果，不代表已动态证明所有报告落点安全。

**HIGH：2。**

1. **`kind=file` 仍把软链目标查询失败当成“不匹配”，可以假绿。**  
   位置：`V:564、574、630–635`。`lstat` 成功后，`path.is_file()` 仍会跟随软链；目标查询失败时返回 False，根本没有产生 None。  
   复现思路：合法清单仅声明 `exclude x / kind=file`、`extra_scan=[]`，让 `x` 指向不可搜索目录里的普通文件；`hits_for()` 返回空且不登记 unreadable，其余检查无问题时可返回 **0**。  
   **归属：本卡范围内应修，属于本轮三态整改遗漏。** 两路独立静态复核确认了完整传播路径。

2. **同类型设备节点仍丢失设备号，不同对象可判 match。**  
   位置：`V:691`。摘要只保留 `S_IFMT(st_mode)`，没有保留字符／块设备的 `st_rdev`。  
   复现思路：两侧同路径放置设备号不同的字符设备，两者均得到 `?:020000`，没有 unreadable，后续可以判等。此结论来自源码，未创建设备或读取 `/dev`。  
   **归属：本卡特殊类型整改仍不完整。** 若主 session 决定将契约明确收窄为“特殊节点只比较类型”，才可作为已接受边界转卡；不能继续宣称摘要消除了所有有损处理。

**MEDIUM：6。**

1. **不存在的 extra 扫描根被误报 unreadable，只有 missing 时也会返回 2。**  
   位置：`V:547、1063、1075`。`_collect_extra()` 没接住 absent，随后 `_resolved_kind()` 把 ENOENT／ENOTDIR 都归 unreadable。  
   复现思路：让扫描根确实不存在，或中间路径是普通文件；本轮只读实测后者得到 `_entry_state=absent`、`_resolved_kind=unreadable`，汇总为 rc=2。**本轮新引入。** 这是向上误阻断，按此前 ENOTDIR 同类问题维持 MEDIUM。

2. **None 在 extra 最终消费端仍被丢弃，无法判定排除条件的条目仍会误报 extra。**  
   位置：`V:1057–1058、1108`。这里没有传入 unreadable 收集器，匹配器最终返回 False 后直接进入 extra。  
   复现思路：覆盖目录可以列名字，但不能查询其中条目类型，同时存在匹配的类型限定 exclude；条目仍进入 extra。**整改不完整。** `hits_for()` 通常已登记 unreadable，因此残余是误分类，较原问题降为 MEDIUM。

3. **目录无法列举时，只跳过目录 key，仍会将对侧子孙误报为内容差异。**  
   位置：`V:755、1004–1012`。  
   复现思路：两侧 `pkg/d/a` 内容相同，仅一侧 `pkg/d` 无法列举；skip 包含 `pkg/d`，对侧 `pkg/d/a` 却继续参与摘要。实际调用 `_fold()` 的内存对照结果为不相等。**本轮修复不完整。**

4. **skip 会连已经可证明的文件／目录类型差异一起剔除。**  
   位置：`V:683–687、755`。普通文件读取失败后只剩 U 标记，其已知类型丢失；对侧同位置的 D 标记也被删除。  
   复现思路：一侧 `pkg/x` 是不可读普通文件，另一侧是空目录；实际 `_fold()` 对照结果相等，漏掉类型 drift。**本轮新引入。** unreadable 仍在，退出码仍为 2。

5. **skeleton 的软链目标查不到时，仍被说成“存在但不是目录”。**  
   位置：`V:973–980`。  
   复现思路：骨架路径是软链，本体可查询、目标不可查询；仅此问题时进入 missing／rc=1，而非 unreadable／rc=2。**已登记遗留问题。** 可以交主 session 决定转卡，但它不属于报告禁写防线，不能用“同上理由”解释。

6. **结论表“已 fail-closed，查询失败最坏多拒一次”的判断比证据宽。**  
   位置：`R:193–196`；对应 `V:820–823、1371–1373`。目标类型查询失败可以只加入 roots，身份取不到也直接跳过，并不必然登记扫描失败。  
   复现思路：逐分支追踪这些失败是否进入 `scan_failures`，即可看到“必拒绝”没有成立。**未实证写穿，不能据此升级 BLOCKER；也不能反向证明必然安全。** 本卡应收窄表述，禁写链是否改动交人审。

**LOW：2。**

1. **十叶子性质门仍抓不到前轮点名的 `ignore`／`replace` 退化。**  
   位置：`T:1769、1785、1821`。  
   复现思路：仅改软链目标的编码错误策略；非法字节分别变为 `bad-target`／`bad?-target`，现有集合没有对应文字对照。我用现有十种摘要输入计算，两种策略都仍是 **10 个不同摘要**。因此“新的有损写法只要出现就会红”不成立。

2. **无缓冲 `--help` 断管仍返回 0，输出失败口径尚未统一。**  
   位置：`V:1313、1493–1512`。  
   复现思路：预先关闭 stdout 管道读端后运行 `python3 -B -u … --help`；本轮实测 rc=0，同形默认缓冲为 3。帮助输出内部吞掉错误，无缓冲时 flush 已无错误可捕获。它不声称检查过 vault，故列 LOW。

其余核对结果如下。

- **base key 与 exclude 对齐：核对结果：无问题。** 对支持的树内路径，`root_key + rel` 与原来的 `child.relative_to(base)` 等价；两侧同一 item 的 key 一致，没有重复拼接前缀。问题在 skip 的信息粒度，而非 base 改动。
- **已修编码及记录边界：核对结果：无问题。** `os.readlink()` 保留原文，`surrogatepass` 消除了已知转义碰撞；路径不能含 NUL，叶子标记不含换行，当前记录拼接未发现结构歧义。FIFO／socket 等不同类型已区分。**SHA-256 本身并非数学上的单射，十个样本也不能证明全域单射。**
- **三态接收：部分成立。** `matches_exact`、`is_under_exclusion`、`hits_for` 内部确实接收了已产生的 None；但 HIGH-1 根本没有产生 None，MEDIUM-2 又在最终调用端丢了失败收集。
- **退出码桶优先级：核对结果：无问题。** 独立运行七桶空／非空的 **128 种组合**全部符合 0／1／2 契约。上游分类和帮助输出仍有上述问题，所以不能说整个 CLI 契约完全自洽。目标 missing 时新增源端 unreadable 登记，源码传播正确。

剩余会吞查询错误的位置，按“是否仍可能漏掉未完成核查”区分：

| 真漏／仍需区分失败 | 换谓词不会增加阻断保障 |
|---|---|
| `V:574`：`kind=file` 跟随查询，见 HIGH-1 | `V:572、576`：dir／nondir 明确按非软链目录区分，静态路径下可确定 |
| `V:973`：skeleton，见 MEDIUM-5 | `V:524`：已有入口检查，且明确不遍历软链 |
| `V:820、1371、1383`：报告安全查询失败并非全部显式拒绝 | `V:720`：失败后仍进入会登记错误的 `_leaf_digest()` |
|  | `V:988`：源端 `exists()` 失败已归 unreadable，不会放绿，但“模板源没有”理由不准确 |
|  | `V:1337、1400`：根目录／报告父目录查询失败已经拒绝入口 |

**测试门不能整体认定“各自只拆一层、均已证明承重”。** 本轮没有逐门执行变异：

| 门 | 核对程度 |
|---|---|
| 逐条 `hits_for` 后验证去重 | **核对结果：无问题。** 补上了“少扫一路冒充去重”的漏洞 |
| `_kind_ok` 与 `hits_for` 三态门 | 分别检查自身，但缺软链跟随失败和 extra 最终分类 |
| 单侧叶子 unreadable／可读兄弟 drift | 各自约束目标后果；不能代替目录级、类型差异覆盖 |
| 源端查询失败登记门 | 当前断言能区别既有“源端没有”分支；绑定具体路径会更稳 |
| 输出流门 | 普通报告断管覆盖改善；缺无缓冲 help，且 `T:2004` 接受 0／1／2，放过扫描根回归 |
| 十叶子摘要门 | 历史碰撞覆盖有效，普遍性声明不成立 |

**结论表其他部分，核对结果：无问题。** 历史行号／旧 rc 的快照限定、R3-2 原样例未制造碰撞的承认、方括号门不可区分的解释，以及 **12 个新增函数展开为 17 条测试**，均与授权 diff 一致。JS 注释、转义、拼接的假放行／假拦下也已明确登记，转下一卡可接受。

表中引用的外部探针及执行日志不在读取面内，本轮不追认其运行事实。`R:182、184` 的“已修”范围应随上述三态、skip 剩余问题收窄；两条 HIGH 的处置均需主 session 裁定，轮次上限不能替代通过证据。



> 批次: BATCH-2026-09-05-第十二批 · 车道 Y5 · 卡 CARD-RV-B round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-B.md)"`
> 审查绑定: `2c53a881..004e08cc`（本树 HEAD `472cf806`，**不绑合并态**；`negative_control.py` 在 HEAD 与 `004e08cc` blob 相同 `93309e09`，`guard_probes.py` 不同，Codex 正文 :3 自述已用 `004e08cc` 版行号）
> 会话头自证（抄 .stderr 前三行，stderr 本身不入库；该文件前三行不含 model 行，`model: gpt-6-astra` 实测出现在 .stderr 第 4 行）:
> `Reading additional input from stdin...` / `2026-09-05T09:49:11.081634Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit` / `2026-09-05T09:49:11.084100Z ERROR codex_models_manager::manager: failed to refresh available models: timeout waiting for child process to exit`

---

**静态推演结论：①的输入会报 1 条违规；但“冻结、聚合、发布三条各自缺一不可”的自述不成立。**

本次只审 `2c53a881 → 004e08cc` 的指定两文件，确认 diff 为 **153 新增、51 删除**。未运行脚本、测试或变异对照，未修改文件，未读取 `live_port_guard.py`。以下行号均属于 `004e08cc`；`guard_probes.py` 的 HEAD blob 与该提交不同，已使用提交版本。

为便于引用，N 指 [lifespan_isolation_negative_control.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/scripts/lifespan_isolation_negative_control.py)，G 指 [lifespan_isolation_guard_probes.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/backend/scripts/lifespan_isolation_guard_probes.py)。

| 编号 | 上一轮结论 | 整改落点（文件:行号） | 你的裁定 | 依据 |
|---|---|---|---|---|
| H1 | HIGH：失格工厂的调用方仍获安全资格 | N:740–752、782–794、1567–1582 | **整改成立但自述宽于可证范围** | `make` 的同名定义合并为 False，扫描期间不发布暂态资格，`outer` 无法取得资格。但删除冻结拷贝两行不会改变行为。 |
| M2 | MEDIUM：两次自比不能证明排序 | N:229–246 | **整改成立** | 与独立列举的有序清单比较；原始枚举已有序时明确失败。能够识别上一轮的“稳定但错误顺序”。 |
| L3 | LOW：AST 写盘前置的依赖理由错误 | N:1968–1979、1995–2000 | **整改成立** | 已承认 AST 分支不调用快照，并明确综合自检意图及可写临时目录代价；行为保留可接受。 |
| L4 | LOW：shell 排序探针未验证乱序前提 | G:1057–1092 | **整改成立但自述宽于可证范围** | 新前提与原判据相与，没有放宽门；但独立采样与被测展开尚未严格绑定，失败原因的解释也过宽。 |

① **该输入不会继续被放行。** 按代码静态推演，初始可信集为空（N:405）。第一版 `make` 的 `return a` 得到合格裁定，第二版的 `return real_app` 得到不合格裁定（N:782–787）；两者有相同的 `<module>.make` key（N:926–937），由 **N:794 的 AND 合并为 False**。扫描只写 `_factory_verdicts`，因此第一版 `make` 暂时得到 True 时不会让调用方读到它（N:742–745、794）；轮末 N:750–752 又把 False 的 key 排除。因此每一轮 `outer` 检查 `make()` 时，都在 **N:639–640** 因可信集中没有 `<module>.make` 返回 False；其返回值随后落为 unknown（N:604–620），自身也在 N:784–787 被判不合格。最终重建绑定表（N:453）后，`app = outer()` 是 unknown，`with TestClient(app)` 经 **N:1178–1183** 添加一条“来源无法静态证明”的违规。

这里三步各有明确作用：

- **冻结**：使本轮判定只见上一轮发布的资格，不见安全版 `make` 的中间裁定。
- **按 key 聚合**：使两个 `make` 定义的 True、False 合成 False。
- **轮末整组重建**：不发布 False 的 `make`，也不保留 False 的 `outer`，下一轮仍无法传播资格。

“每条 return 都要合格”的判据**参与了**上述过程，具体执行在 N:782–787；本输入每个函数只有一条 return，因此并未单独考验多 return 情况。它负责**单个定义**的真假，N:794 负责**同名多个定义**的合并。

新增常设反例的实际源码在 **N:1569–1582**，覆盖同一组合形态，并由 N:1743–1748 检查必须产生违规。它与题中输入不逐字相同：去掉了空行，`test_case` 改为 `t`，`with TestClient(app)` 增加 `as c`。这些差异不改变工厂链、同名定义次序或传入的 app；`c` 也未被使用，因此不影响本项判定。

② **“少任意一步都会退回某个缺陷”超出了代码能证明的范围。** 冻结与延迟发布是同一数据流约束的读、写两面；AND 聚合另有独立作用。必须把所谓“去掉一步”落实为具体改动：

| 单独改动，均为静态推演 | 结果 |
|---|---|
| 删除 N:740–741 的 `frozen` 拷贝及回绑 | **行为不变。** N:794 仍只写独立裁定表，可信集仍到 N:750–752 才改变。不会因此漏掉①或既有反例。 |
| 将 N:794 改为 `_factory_verdicts[key] = ok`，取消 AND | ①及“安全先、不安全后”的 E 仍被挡；但 **N:1545–1557 的逆序 E** 会被最后的 True 覆盖，产生漏检。 |
| 仅删除 N:752 的差集 | **两个 E 和①都会漏检。** 因为 N:750 把全部 key，包括 False 的 `make`、`outer`，加入了可信集。故 N:747–748 的这条具体注释有依据。 |
| 删除整段 N:749–752 的发布 | 可信集一直为空，工厂正例被误拒；①不会重新放行。 |
| 仅把 N:750 的重建改为 `update(verdicts)`，保留 N:751–752 | ①仍被挡，因为每轮仍会剔除 `make` 和 `outer`。 |

因此，**差集在当前“先纳入全部 key”的写法下承重**，不能据此扩大为“三个独立开关均已证明必要”。恢复扫描期间直接写可信集，还会同时改变冻结语义，属于联动回退。

③ **G 的 30 行改动只调整探针，没有放宽被测门。** 本探针在 G:1050 没有传变异文本，副本由 G:897–898 原样复制。G:1064–1071 仍读取门的 before 输出，并保留退出码为零、顺序等于期望、排除 `GATE-BROKEN` 三项条件；G:1072 只是增加 `and premise_ok`。

`premise_ok=False` 时，该次探针必 FAIL。如果某环境始终自然有序，正确门与去排序门都会红，表示**该环境下拒绝认证排序承重**。它没有变成逻辑恒红：前提成立且结果正确时仍能通过；更没有变成恒绿。

`builtin compgen -G` 前提探测是有效的当次输出采样：G:1060 同时检查完整六个文件名及非期望顺序。但其可靠性有具体边界：

- G:1057 使用 `/bin/bash`，G:1063 使用 PATH 中的 `bash`，代码没有保证二者相同。
- `_sh` 在 G:505–509 继承环境并套一层 `bash -c`，没有保证环境影响被排除。
- 没有检查 `raw_proc.returncode`；原始命令失败、缺少成员也能使前提为假。因此 G:1076–1077 一律解释成“去掉 sort 也会通过”不成立，此时只能说**前提未验证**。
- 原始采样与门内展开是不同调用，不能把一次采样升级为已经完成去排序对照。

④ **MEDIUM 的新判据能识别原问题，但“任何环境删排序必翻转”仍不可无条件声称。** N:235 的期望来自明确创建的六个名字，加上 N:201 定义的 journal；它没有调用被测函数，也没有用 glob 输出推算成员。双方都调用 `sorted` 不构成自证，独立性在于期望成员来源。

若删除 N:169 的 `sorted()`，两次枚举维持同一乱序时，N:236–238 必失败；原始枚举已经有序时，N:242–246 明确失败。这堵住了上一轮指出的稳定错误序列。不过 N:232 与 N:236→168 是两次枚举，代码没有强制顺序一致；自然有序环境中正确版也失败，所以这仍不等于已经证明“正确版通过、变异版失败”的运行对照。

**LOW 的 `main()` 处置可接受。** 上一轮存档第 65 行已明确允许如实说明“所有入口综合自检”的意图，搬移分支是建议。N:1968–1973 现在准确说明选择与代价；N:1978–1979、1995–2000 确实在 N:2031 的快照前返回。写盘前置仍存在，但其理由已不再伪称 AST 的调用依赖，本卡没有依据强制采用原建议的行为改动。

BLOCKER/HIGH 清零：是

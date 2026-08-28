结论：**需整改，暂不可验收**。当前向量内容与真实库重放是正确的，`9 passed`、旧套件 `91 passed`、锁定文件零改动均成立；但发现 **1 个 BLOCKER、2 个 HIGH**：防漂移测试未接入 CI，且矩阵结构与关键 manifest 字段可被篡改后保持全绿。

HEAD：`37387a8662e9dd646fad5628841679d777cb7eae`

### 逐项裁定

| 项目 | 分级 | 裁定 |
|---|---|---|
| a) 确定性 | **PASS**，附 **LOW** | 固定 `T0/card_id/due`、关闭 fuzz、所有 review/retrievability 时刻显式 UTC；未触发 `now()`/随机。两次生成及磁盘产物 byte 相同。`rel=1e-9, abs=1e-12` 合理且足够严格。LOW：[`write_text()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/generate_fsrs_golden_vectors.py:195) 未固定 `newline="\n"`，Windows 可能产生 CRLF；跨 CPU/libm 的末位浮点 bytes 也未物理验证。 |
| b) 矩阵覆盖 | **HIGH / PARTIAL** | 当前 JSON 确实是 5 场景×4 ratings、20 个唯一 ID，前态分别为 `1/1/2/2/3`，3 个 retrievability 点也正确。新卡采用 `Learning step=0 + stability/difficulty=None`，符合 6.3.1 无 New(0) 的现实。但测试只检查数量与最终结果，未验证矩阵唯一性及 `state_before_final_review`。 |
| c) 五道门 | **BLOCKER / FAIL** | [CI 显式测试清单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/.github/workflows/test.yml:114) 未包含 golden 测试；root `requirements.txt` 单独变化也不在 workflow path trigger 内。因此自动控制面根本不执行五门。 |
| d) 真实库验收 | **PASS** | [`FSRS_AVAILABLE` 明确断言](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:84)；运行对象与 site-packages `fsrs 6.3.1` 的 `Card/Rating/Scheduler/State` 身份一致；无 mock、monkeypatch、FakeCard。缺库会失败而非 skip。 |
| e) 回归/锁定文件 | **PASS** | 新门 `9 passed, 10 warnings in 0.39s`；验收口径六文件旧套件 `91 passed, 528 warnings in 108.96s`。`fsrs_manager.py` 的 WT 与 HEAD blob 均为 `980b375…60`，`git diff` 为空。 |
| f) 重放独立性 | **PASS** | 测试不 import 生成器，只读取 manifest+vectors，并按绝对 ISO UTC 时刻重放。严格说是“两份 JSON 合起来自包含”，vectors 单文件不含初始 card/config。 |
| “公开 re-export”边界 | **MEDIUM / PARTIAL** | [`fsrs_manager.py`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/lib/memory/temporal/fsrs_manager.py:20) 只是普通顶层导入，无 `__all__` 或稳定 re-export 契约；测试实际直接驱动第三方 Scheduler。对“真实库 golden contract”这是合理做法，不违反不改调度逻辑的边界；但“只消费项目公开接口”的表述不成立。建议测试诚实地直接从 `fsrs` 导入，待 D4 解锁后再考虑正式适配层。 |

### 阻断性反例

[`test_fsrs_golden_vectors.py:142`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:142) 只断言 `len == 20`；`:146–176` 不读取 `scenario/id/state_before_final_review`，也不锁定 retrievability 点数。主审以内存反例复现：

- `state_before_final_review = 999`：全绿。
- 用第一条替换最后一条，造成重复且缺少一个场景×rating：全绿。
- `retrievability.at = []`：全绿。
- `algorithm="arbitrary"`、`timezone="Mars/Olympus"`：9 项仍全绿。

此外 [`FLOAT_REL/FLOAT_ABS`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:45) 直接信任 manifest，未锁定允许上限；放宽容差可静默削弱浮点门。

### 升级/参数漂移故障矩阵

| 漂移 | 手动执行目标测试 | 当前 CI |
|---|---|---|
| 装入 6.3.2，manifest/requirements 不动 | 安装版本门必红；requirements 门仍绿；默认参数/向量门条件性红 | **五门均不执行** |
| 同版本 DEFAULT_PARAMETERS 改变 | 默认参数门红 | 不执行 |
| 同版本内部算法改变、默认参数不变 | 仅当 20+3 覆盖到且超过容差时红 | 不执行 |
| scheduler_config 改、hash 不改 | params_hash 门红 | 不执行 |
| algorithm/timezone、矩阵结构、前态或点数漂移 | **零门红** | 不执行 |

当前两份 requirements 实体确实是唯一、无 marker 的 `fsrs==6.3.1`：[root](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/requirements.txt:68)、[backend](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/requirements.txt:131)。但正则 `^fsrs==6.3.1\b` 也接受 `6.3.1.*`、`6.3.1.post1` 和条件 marker，故该单门为 **MEDIUM / PARTIAL**。

### 负验证证据

[`g3-4-negative-verification.txt`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/g3-4-negative-verification.txt:1) 为 **MEDIUM / PARTIAL**：

- 无完整命令、exit code、失败清单及恢复前后 SHA。
- N3 称“只改 manifest version”得到 2 failures；按当前代码复算应为 **3 门红**：installed-version、requirements、manifest/GOLDEN library_version 脱钩。若同时改了 GOLDEN metadata 才是 2 门红，说明存档描述与实际操作至少一项不实。

最低整改：将测试加入 CI 并覆盖 root requirements 触发路径；锁死精确 5×4 集合、唯一 ID、重放前态、3 个曲线点、manifest version/algorithm/timezone/容差；严格解析 requirements；用完整命令、失败名、退出码和前后 SHA 重做负验证。整改后再复跑 `9 + 91`。

验证边界：`91 passed` 仅绑定既定六文件验收清单，不外推为全仓所有含 FSRS 名称的 API/e2e 测试；Graphiti MCP 本会话未暴露，无法记录本轮 `[Code-Review]`。审查方法沿用既有只读、并行、证据优先流程，但上述事实均已在当前 HEAD 重新验证。



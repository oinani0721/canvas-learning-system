结论先行：**CARD-G3-1 需再一轮；CARD-G3-4 仍保持可验收。**

HEAD 确认为 `9a71eb8cce02132909991317d74438351333bbd9`。审阅前后 tracked 状态不变，仅保留原有 0-byte untracked round21 审查稿；未修改工作树、现网账本或 backups。

## 1. 二十轮 3 MEDIUM + 2 LOW

### 路由双向行为：CONFIRMED-CLOSED

proof scanner 当前顺序正确：先判 `node_id` 可用性，再排除其他节点，最后判断版本，见 [validate_learning_events.py:529](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:529) 和 [validate_learning_events.py:724](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:724)。

以主体校验完全合规的 v1 为 L1，重放：

```json
{"event_id":"future:1","event_version":2,"payload_v2":{"concept_ref":"n"}}
```

结果：

```text
unroutable_lines=[2]
unknown_version_lines=[]
proof problems=["第 [2] 行缺少可用 node_id … 无法判定归属 … fail-closed"]
```

保留信封但属于别的节点：

```json
{"event_id":"future:2","event_version":2,"node_id":"other-node","payload_v2":{}}
```

得到两数组均空、proof `[]`，无误拒。

纯内存 mutation 结果：

- 删除 `unroutable_lines.append`：仅 `test_v2_without_node_id...` 红，`1 failed / 172 passed / 1 skipped`。
- 把版本判断移到节点过滤前：仅 `test_v2_of_another_node...` 红，同计数。

对应门见 [contract test:2275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2275)。

### 主体校验器：STILL-OPEN — MEDIUM

新 schema 要求三个信封键跨版本保留，[schema:13-16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:13) 的例外和优先级本身表述清楚；但主体 `validate_file()` 对所有整数未知版本仍整行跳过，只发 WARN，[validator:1586-1600](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1586)。

无落盘重放：

```json
{"event_id":"future:missing-node","event_version":2,"payload_v2":{}}
{"event_version":2,"node_id":"n","payload_v2":{}}
```

两者都得到：

```text
violations=[]
warnings=[event_version=2 ... 前向兼容跳过形状校验]
```

主入口因此返回 PASS，[validator:1640-1648](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1640)。更直接的是，旧测试仍明确要求缺 `node_id` 的 v2 exit 0，[contract test:219-230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:219)。

所以目前是“proof scanner 拒绝，但主体裁判接受”，跨版本信封尚未真正冻结。

### G/L：CONFIRMED-CLOSED；Q：STILL-OPEN — MEDIUM

- G 的完整括号参数 ID 已精确锚定，[脚本:190-193](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:190)。
- L 的两个参数实例 ID 均完整，两个实例分别变红，[脚本:224-228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:224)。
- Q 两步各恰命中一次，机械上确实把同一代码块原样搬到 `continue` 后，没有删除或改写，[脚本:259-266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:259)。

但 Q mutation 后仍不是错误放行，而是被另一门替代拒绝：

```text
vault_ids={'a'}
vault_id_lines={1}
review_ext_lines=[1,2]
problems=["仅 1/2 条 review/1 事件带 vault_id … fail-closed"]
```

原因是 `review_ext_lines` 仍在 `continue` 前，[validator:567](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:567)。测试先在 [contract test:2071](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2071) 因预期诊断消失而失败，脚本只看到测试 node ID 变红，不能证明目标安全门失效。因此“次序行为有测试覆盖”成立，“该门本身承重”的归因仍不成立。

## 2. 路由条款自洽性与当前形状

- **CONFIRMED-CLOSED**：schema 明写信封条款优先于“v2 可改名任一顶层字段”，无规范内部死结。
- “改名/删除 `node_id` 的合法 v2”只在旧规则下合法；当前 schema 和 [测试注释:2275](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2275)仍称其“合法 v2”，措辞已过期。
- 当前代码把任何字符串，包括 v1 合法的空字符串，视为可路由值，因此不会因本改动误拒该合法旧形状。
- live 账本 22/22 行都有 `event_id/event_version/node_id`，`node_id` 全为非空字符串，版本全为 1；没有当前数据误伤。

## 3. 新 survivor 与测试有效性

- **NEW-FINDING — LOW**：`test_routing_envelope_is_frozen_in_schema` 只检查“路由信封”后 400 字符出现三个键名，[contract test:2314-2319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:2314)。把正文反转成“可删除/改名”、删除 fail-closed 义务、删除优先级行，判据均仍通过。
- **NEW-FINDING — LOW**：当前实现正确拒绝 `node_id=null/42/[]/{}`；但把判定收窄成“仅缺键才不可路由”后完整契约仍 `173 passed + 1 skipped`。
- **NEW-FINDING — LOW**：把无证据诊断恢复为旧“适用事件均无 vault_id”后完整契约仍全绿。
- **STILL-OPEN — LOW**：新增路由门继续复用 `_event()`，[contract test:1558-1574](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:1558)。该 review/1 基线缺五个主体必填字段，违反 verifier 明示的“账本已先通过主体校验”前置。独立使用主体合规 v1 重放后，当前实现行为正确，但测试尚未锁住合法全链。
- 三个新增测试没有恒真 `if`，双向行为期望值也不是从被测分支动态生成；主要薄弱点是 schema 字符串门及合法输入前置。

## 4. 负验证与 `COLLECTED`

- **CONFIRMED-CLOSED**：A–V 共 22 变体、23 次替换操作，静态复算全部恰命中一处；未执行原地修改脚本。
- **CONFIRMED-CLOSED（当前数据）**：最后摘要算法消除了原 334 重复累加；当前筛选输出可正确算出 174。
- **NEW-FINDING — LOW（通用性）**：[脚本:82-85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-1-evidence/negverify_round14_proof_gates.sh:82)遗漏 `skipped/xfailed/xpassed/error`。例如 `173 passed, 1 skipped` 会算成 173，而不是 collected 174；折行摘要或摘要后插件输出也可能取错行。

## 5. 范围、验收文档与账本更正

- **CONFIRMED-CLOSED**：三处六条机械同文。独立抽取仅去载体前缀并合并物理折行，三份规范化 SHA 均为 `2faa3265…`：
  - [schema:207-213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:207)
  - [模块注释:335-347](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:335)
  - [docstring:1149-1160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:1149)
- **STILL-OPEN — LOW**：三处第⑤条共同遗漏 scanner 实际依赖的 `event_version`/不可路由行为；所以“同文”成立，“内容完整”不成立。
- **STILL-OPEN — LOW**：G3-1 UAT 顶部仍两次写当前 23 行，[UAT:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:8)、[UAT:36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:36)，而同文件后部写 22。`CURRENT_TASK.md:20` 写提交数 21，实跑 `git rev-list --count 37387a86..HEAD` 为 **22**；UAT 的“二十一轮整改后”也与“二十轮处置/待二十一轮复核”时态冲突。
- **CONFIRMED-CLOSED**：上一轮错报的实质更正诚实。live 22 行/7232 bytes，backup 23 行/7492 bytes；backup 前 7232 bytes SHA 与 live 完全相同，剩余恰一条合法记录。独立裁定明确记载用户授权、先备份再清理，[独立裁定:29-32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-29-第五批独立复核裁定.md:29)。
- **NEW-FINDING — LOW**：backup 目前仍是本机 untracked、非版本化文件；UAT/CURRENT 省略了这一持久性边界。准确结论是“当前本机可完整恢复”，不是持久恢复保证。

## 6. 回归、账本与 G3-4

指定解释器实跑：

- 契约：`173 passed, 1 skipped`
- 契约 + golden + 既有账本：`198 passed, 1 skipped`
- golden + `test_fsrs_manager.py`：`56 passed`，即 19 + 37
- UAT 锁定的 11 文件 FSRS 全族：`191 passed`；2771 个既有 warning，无 F/E
- live 主仓账本：校验器 exit 0；前后 SHA 均  
  `2a18023e71a046db8a8c52e098cd48bd0b9898596e4ea3024e18695827796cb6`

`59e56cd6..HEAD` 对 G3-4 三文件零改动：

- generator：`9d6ab4f63b326dc3f604cb794ce9fd9e42de792e`
- manifest：`b59f331d9a1f57e5778fd82399ef12b61eb0c967`
- vectors：`33c601995d5274f7702a4d0ce501d2b81311d688`

锁定 blob：

- `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
- `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`

以上是指定本地回归，不冒充整套 CI 状态。

## 残留清单

- BLOCKER：0
- HIGH：0
- MEDIUM：2
  - 主体校验器/旧测试仍接受违反跨版本三键信封的 v2。
  - Q 仍由替代覆盖率 fail-closed 变红，负验证安全归因未闭合。
- LOW：7 组
  - 三处范围声明共同遗漏版本/不可路由依赖。
  - 新路由测试仍使用主体不合规 v1 基线。
  - schema 字符串门无法证明义务与优先级。
  - 非字符串 `node_id` 与诊断措辞存在全绿 survivor。
  - `COLLECTED` 非通用准确计数器。
  - UAT/CURRENT 的 live 行数、提交数、轮次仍漂移。
  - backup 的 untracked/非持久存证边界未披露。

**最终裁定：CARD-G3-1 需再一轮。**  
**CARD-G3-4 仍保持可验收。**

Graphiti-canvas MCP 本会话未暴露；没有任何当前结论依赖历史 Graphiti 自报，全部来自 HEAD、当前 bytes、真实入口和本轮实跑。



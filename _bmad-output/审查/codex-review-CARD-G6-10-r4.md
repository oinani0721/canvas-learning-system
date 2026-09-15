> 批次: BATCH-2026-09-11-第十四批 · 车道 T4-B · 卡 CARD-G6-10 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-10-r4.md)"`
> 审查绑定: `ee80de0e9687001b59b5a8f4472226b923b416af`（该轮的 HEAD；其后有整改 commit）
> 会话头自证（抄 .stderr 含 model 行，stderr 本身不入库）:
> L2: `OpenAI Codex v0.153.3` / L5: `model: gpt-6-astra` / L9: `reasoning effort: ultra`

---

复核绑定 **`ee80de0e9687001b59b5a8f4472226b923b416af`**。未改文件、未连接数据库；验证仅使用源码及抽取后的纯内存断言。

**结论：`--share-state` 确实制造了生产 state 文件碰撞；但落盘保护仍有 HIGH 缺口。**

## BLOCKER

无。

## HIGH

### H1：临时目录整改仍未约束第三方 import 的回退路径

- **位置**：[g610_dual_vault_interaction_canary.py:324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:324)，另见 `:332、:611、:613`。
- **问题**：`_resolve_tmp_base()` 遇到首个存在的目录便返回，后续环境变量未经检查，而选出的目录仅约束自己的 `mkdtemp`，此前 `app.*` 导入仍可自行选择临时目录。
- **负控输入**：设置 `TMPDIR=/System`、`TEMP=<生产 BACKUPS>`；纯内存检查已确认前者被选中、后者未受检查，导入链若调用 `gettempdir()`，便可在前者不可写时回退到受保护位置。

本轮确认的是**危险输入被放行**，未执行第三方导入或实测写盘，不能把它表述为本轮已观察到污染。

## MEDIUM

### M1：生产读缺少“切回 A 看见本次复习”的正向对照

- **位置**：[test_g610_dual_vault_isolation.py:357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:357)，另见 `:429、:434、:454`。
- **问题**：生产读只检查非空及 B 前后相等，复习后 A 的 95 分只由手写查询验证，因此不能排除生产读始终串到 B。
- **负控输入**：生产 getter 忽略 group 参数，始终返回 B 的旧 40 分；实际断言函数接受这种输入，而 raw A 正常变成 95 后，现有门仍可通过。

### M2：文件自身没有落实“只跑 7692”的限制

- **位置**：[test_g610_dual_vault_isolation.py:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:98)，另见 `:104、:114、:204`。
- **问题**：这里只拒绝 7691、7687，并未限定目标必须是 7692，与文件开头“只跑容器（7692）”的声明不一致。
- **未被拦下的输入**：`NEO4J_TEST_URI=bolt://127.0.0.1:7693`；纯函数实测返回 `False`，若那里存在可用数据库，本文件会继续探测及测试写入。

这是**文件自身限制不足**，不是已证明绕过仓库 W4；本轮没有读取或执行 W4。

### M3：总账要求的偏离仍然存在

- **位置**：[g610_dual_vault_interaction_canary.py:344](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:344)、`:624`；[test_g610_dual_vault_isolation.py:23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:23)、`:154`。
- **问题**：canary 虽直接复用 G2-9 常量，仍自行创建 tmp fixture vault；门文件则另建字面量，尚未满足用户引用的“强制复用、禁止另建”原文。
- **对照输入**：普通 `--isolated` 路径就会进入 `_materialize_vault()` 创建两份新库，说明这不是异常分支，而是默认执行方式。

隔离清理命名空间的工程理由合理；但 G2-9 清理语句不在允许读取面内，无法独立确认互删前提，且合理理由不等于已经取得总账例外。

## LOW

### L1：Episode 正控证明了变化，仍未证明新增

- **位置**：[test_g610_dual_vault_isolation.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:307)，另见 `:324、:444`。
- **问题**：快照不包含 Episode 身份，“出现 95＋列表变化”只能证明内容变化，注释却宣称证明新增记录。
- **负控输入**：保持 Episode 身份和数量不变，把原有 40 分原地覆盖为 95；现有两条正控均通过，已用纯内存输入确认。

### L2：自证测试仍不是独立第三层

- **位置**：[test_g610_dual_vault_isolation.py:131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:131)，另见 `:389`。
- **问题**：自证测试仍继承模块级 `skipif`；整改后的说明诚实，但执行缺口仍在。
- **负控输入**：URI 指向 `:7691` 时，整文件连同自证测试一起跳过，其断言不会执行。

## 其余问题的核对结论

- **⓪ 碰撞可信。** B 仅替换 basename；生产 `_vault_key()` 取 `resolve().name`，`send_bark.vault_key()` 对相同名字产生相同 key，两者最终指向相同 `BACKUPS/state` 文件。没有替换 `_vault_key`，最终仍比较同一套 B 文件哈希。
- **① 显式 state／lock 写路径覆盖正确。** 补丁及模块对象身份检查覆盖所示生产辅助函数，锁的 `mkdir/O_CREAT` 也由补丁后的 `BACKUPS` 派生；但 `_state_tmp_path()` 定义不在允许片段内，不能独立确认临时件构造，更不能据此认可“全部落盘点都已覆盖”。
- **② 两条负控的异常区分成立。** `pytest.raises` 仅包隔离断言，写入、查询、fixture 均在外；类型加 marker 足以排除这些异常冒充负控通过。手写查询与生产读分开验证的边界也已声明，但生产读仍有 M1。
- **③ “skip ≠ pass”写得清楚。** 文件明确记为“本卡未证明”，fallback 也标注 `gate void`；不能仅凭 pytest 返回码判该维通过。
- **⑤ “两库都没写”已被排除。** canary 的 P1/P2 验证实际文件变化及目标值，P3 是辅助核对；门的 raw A 正控也排除了旧 95 原封不动冒充本次写，剩余问题是 L1 的“新增”措辞。
- **⑥ 真实 group 派生仍未获证。** `_group_dimension()` 直接把 `va.name/vb.name` 交给构造器，没有调用实际 vault 身份解析流程；它证明的是这个输入模型下的相等关系。docstring 限定了“无配置”的场景，但真实 `Settings.vault_id` 派生代码不在读取面内，不能独立确认与生产一致。
- **修改范围属实。** 指定基线差异只有两个新增文件，未修改 `backend/app/**` 或 `daily_review_run.py`。删除越界孤儿清理及调整清理顺序属实；“生产写绝不产生无 group、无边残渣”因实现不在读取面内，未验证。

**计数：BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 2。**



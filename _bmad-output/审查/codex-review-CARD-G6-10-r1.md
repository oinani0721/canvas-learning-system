**⓪ 结论：`--share-state` 确实把两个库指向同一个 state 文件，不是改断言制造红灯。** 两库 basename 相同，生产 `_vault_key` 只传入 `.resolve().name`，`send_bark.vault_key` 不包含父目录信息；最终比较的也是实际文件 SHA。

本次绑定 `80d2fbb… → 974058e…`，仅静态读取，未执行测试、修改文件或连接数据库。以下负控输入均未执行。

**BLOCKER：无。**

**HIGH：2 条**

1. [g610_dual_vault_interaction_canary.py:454](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:454)：`mkdtemp()` 接受环境指定的临时目录，而 `:295–308` 直接信任其返回根目录，因此不能保证写面避开真实 `backups/` 或 live vault。  
   **未被拦下的输入**：`TMPDIR=<既存且可写的真实 backups 或 live vault>`；fixture、state、锁均可写入其子目录，白名单仍通过，事后删除不能抵消已经发生的写入。

2. [test_g610_dual_vault_isolation.py:365](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:365)：读侧负控只取消手写 Concept 查询的过滤，生产 LEARNED/Episode 读仍带 group，并把正例的同名复习写换成新增独有概念，不能证明宣称的单变量复习读负控。  
   **对照输入**：保留 `group_filtered=False`，将 `:378–383` 换回正例的 `_review_write(A)`；Concept 名单不变、两条生产读仍限定 B，共同隔离断言不会红。

**MEDIUM：7 条**

1. [g610_dual_vault_interaction_canary.py:460](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:460)：tmp 断言执行前已经创建目录并写入两份白板，而且白名单没有检查最终 `vault_dir / SHARED_BOARD` 路径，“任何写之前检查、漏列即拒绝”不成立。  
   **负控输入**：让复用的白板路径成为 tmp 外的绝对路径，`:245` 会先向该目标写入，后续对白板所属 vault 目录的检查无法发现它。

2. [g610_dual_vault_interaction_canary.py:228](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:228)：自建 loader 没有生产 loader 中的字节码禁写保护，`REPO/BACKUPS/VAULT` 补丁也管不到源码旁的 `__pycache__`。  
   **门未覆盖的路径**：冷缓存且允许字节码缓存时，`exec_module` 可向真实仓库的 `scripts/__pycache__` 写入 `.pyc`；这些目标不在 tmp 白名单内。

3. [g610_dual_vault_interaction_canary.py:441](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:441)：只捕获两个自定义异常，其他异常造成的进程退出码也可能是 `1`，与“隔离被破坏”重合。  
   **负控输入**：让 `--share-state` 的生产写遭遇磁盘满或权限错误；仅核对 `rc=1` 会把执行崩溃误认成负控命中，必须另外核对完整正向对照及 `BREACHED` 判词。

4. [test_g610_dual_vault_isolation.py:265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:265)：按 concept 构造字典会覆盖同名重复行，可能把已经泄漏进 B 读取结果的 A 记录消掉。  
   **负控输入**：B 的读依次返回 A 同名 `95` 分记录、B 同名 `40` 分记录，A 自身读取正常；字典仅留下 B 的 `40`，其他读取仍正确限定 group 时，隔离断言漏报。

5. [test_g610_dual_vault_isolation.py:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:188)：seed 只检查写函数返回成功，没有回读确认 B 确有初始复习账，允许“空 B 始终为空”的假绿。  
   **负控输入**：所有 `40` 分种子写返回 `True` 但不落库，`95` 分写正常；正例 A 对照通过、B 空→空，两条负控仍可命中，整个门仍可能通过。

6. [test_g610_dual_vault_isolation.py:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:147)：先删除 Node，再沿其 `SCORED` 边寻找 Episode，使声明要清理的无 group Episode 失去定位依据。  
   **负控输入**：无 `group_id` 的 scoring Episode 指向 `g610gate` 前缀 Node；删除 Node 后关系消失，下一条查询找不到 Episode，而模板 `:109` 的孤儿收尾也未复用。

7. [g610_dual_vault_interaction_canary.py:265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:265)、[test_g610_dual_vault_isolation.py:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:127)：按题给总账原文，canary 新建 tmp fixture vault、门使用另一组字面量，属于尚未获准的执行偏离，import 常量与形状相同不能替代履约。  
   **对照输入**：修改 G2-9 的资产常量，canary 随动而门不随动；同时 canary 每次仍自行创建两座临时库。

**LOW：1 条**

1. [test_g610_dual_vault_isolation.py:299](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:299)：7691 自证测试本身受整模块 `skipif` 覆盖，不能算独立第三层断言证据。  
   **负控输入**：`NEO4J_TEST_URI=bolt://127.0.0.1:7691`；探针返回 False 后，该断言也被跳过，直接拒连分支仍然有效。

其余问题的明确结论：

- **①** 可见的 state、锁目录和锁 `O_CREAT` 都沿补丁后的 `BACKUPS`；模块对象身份检查也在生产写之前。`_state_tmp_path`、损坏隔离及合并函数体不在允许读取面内，不能独立认证其全部落盘分支。
- **②** 两个 `pytest.raises` 仅包裹共同断言，确实排除了外围 import、fixture、连接及取样异常；marker 能证明失败来自该函数，不能证明测到了宣称的生产读路径。
- **③** `:50–51` 的“skip 不是 pass／本卡未证明”文字清楚；只看 pytest 成功退出仍可能误读，不能把 skip 算作本维通过。
- **④** 独立命名空间避免并发清理碰撞的理由合理，但 G2-9 清理语句不在获准读取面内，未独立核实其实际范围；该理由本身不构成总账豁免。
- **⑤** canary 的 P1/P2 读取真实文件变化和具体值，能排除未写入；P3 单独属于自报路径对照。数据库 A 的 `95` 分回读也有效，但未补上 B 初始账存在性的缺口。
- **⑥** `:370–375` 只证明“以 basename 作为 vault_id 输入”的派生结果，没有核对生产配置最终选出的 vault_id；配置派生代码不在读取面内，因此 docstring 所称生产一致性仍未获证实。
- 给定 diff 确实只有两个新增文件，`backend/app/**`、`daily_review_run.py` 均未修改。

**计数：BLOCKER 0 / HIGH 2 / MEDIUM 7 / LOW 1。**



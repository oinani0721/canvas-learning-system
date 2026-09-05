# 独立复核：CARD-TEST-hygiene-vaultinit（第十二批 Y6-A）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y6-testhygiene`
分支 `card/y6-testhygiene`，基线 commit `03ac8bf8`。

这张卡处理的问题：**跑后端单元测试会把一整套 Obsidian vault 骨架
（`raw/`、`wiki/`、`outputs/`、`CLAUDE.md`）写进代码目录 `backend/` 里**。
另一个 worktree（`card-z4-redbase` @ `c8611a89`）里冻结着这个污染的现场。
项目台账把它归给了 `backend/tests/unit/test_vault_init_service.py`，
本卡第一步就是去验证这个归因，然后修守卫面并落一道回归门。

**请只读以下内容**（不需要读全仓）：

1. `git diff 03ac8bf8 HEAD -- backend/app/api/v1/system.py`
2. `git diff 03ac8bf8 HEAD -- backend/tests/unit/conftest.py`
3. `git diff 03ac8bf8 HEAD -- backend/tests/unit/test_startup_health_check.py`
4. `_bmad-output/审查/evidence-hygiene/` 下的全部 `*.txt` 与 `定位结论-a*.md`
5. 需要上下文时可读 `backend/app/services/vault_init_service.py`（本卡未改动它）

## 二 作者自述，请独立核对

以下是我（作者）的结论。请**独立验证**，不要默认它们成立。

### 2.1 定位结论

- **台账归因不成立**。`test_vault_init_service.py` 的 8 个用例全部经
  `vault_dir(tmp_path)`；`tests/unit` 目录级实跑后，`backend/` 内四条路径
  全部不存在、`git status --porcelain backend` 为空、两个已入库文件 sha 未变。
- `tests/unit` 目录级**确实**复现了另一种污染：`/tmp/test-vault` 与
  `/tmp/test-vault-wizard`。二分到 nodeid 级，
  `TestSetupWizard::test_endpoint_exists` → 只产生前者，
  `TestSetupWizard::test_returns_structured_report` → 只产生后者。
- **`backend/` 内骨架的真凶是 H2**：`tests/contract/test_openapi_contract.py::
  test_api_contract[POST /api/v1/system/setup-wizard]`。在改前代码上单跑该
  operation 即完整复现；污染文件树与冻结证据树逐条相同，`backend/CLAUDE.md`
  的 sha256 一致（`319599d2ca3c…`）。改后代码上跑同一条 → 四路径全 absent，
  而失败原因（`DeadlineExceeded`）两轮同型 ⇒ 我据此声称「消除污染且零回归」。
  - 全量 H2 按卡文原命令跑不完（206 operation，实测 15:29 只完成 4 个 ⇒ 约 13
    小时），我改用 `-k setup` 定向子集。**这个替换是否削弱了结论，请判断。**
  - 我的**第一次**定向尝试是假绿：用带方括号的完整 nodeid 传参 → `rc=4`
    usage error、0 个用例执行、三签名全空。我加了「log 里必须出现
    `1 (passed|failed|error)`」的硬前置断言后重跑才得上述结论。
  - 换版用 `git show HEAD:...` 覆盖生产文件 + `EXIT trap` 还原，收尾有
    `RESTORE-OK sha=…` 自证。**这个做法本身是否留下了风险，请判断。**
- **判据污染面（我自己发现并声明的）**：`/tmp` 是全机共享的，本仓有多个
  worktree 并行跑测试，别的车道跑 `tests/unit` 同样会产出这两个目录
  （实测 `card-y9-maingoal` 车道即如此）。我认为 nodeid 归因不受影响，
  理由是「并行车道的污染成对出现、我的单跑各自只产生一个且与源码字面量对应」。
  **这条推理请重点检查是否站得住。**

### 2.2 绝对路径校验与既有黑名单的叠加关系

`system.py::setup_wizard` 原有两道检查（本卡**未改动、未搬动**它们）：
`str(vault) in ("/", "/etc", "/usr", "/var", "/tmp", "/System")` 与
`".." in request.vault_path`。它们跑在 `Path(...).resolve()` **之后**。

我新增的是 pydantic 层 `field_validator`：`Path(v).is_absolute()` 为假即 422。
理由：`resolve()` 对相对路径和空串是**静默**拼 cwd 的，等到黑名单看到的时候
已经是一个合法绝对路径，所以补黑名单永远追不上。

顺带记录（未修，本卡边界外）：macOS 上 `/tmp` 是 `/private/tmp` 的软链，
`Path("/tmp").resolve()` → `/private/tmp`，所以黑名单里的 `/tmp` 那一项
实际上恒不命中。

### 2.3 不变量 fixture 的零副作用

`backend/tests/unit/conftest.py` 新增 session 级 autouse fixture。我声称它：
不写任何文件、不依赖 cwd（走 `Path(__file__).resolve().parents[2]`）、
不 import `app.*`、setup 与 teardown 复用同一个快照函数。

## 三 请按重要性排序回答的问题

1. **定位证据是否支持结论？** 有没有把「没跑到」当成「不存在」的地方？
   特别是：`tests/unit` 目录级跑完后 `backend/` 干净，是否足以否定台账归因？
   还是说存在我没覆盖到的触发路径（不同 cwd、不同起跑目录、xdist、
   其他测试目录）会让同一批用例写进 `backend/`？
   2.1 里那条「成对 vs 单个」的推理，是否构成对并行干扰的有效排除？

2. **校验器会不会误拒合法输入，或漏放非法输入？**
   macOS `tmp_path` 形态（`/private/var/folders/...`）必须放行；
   `""`、`"."`、`"./x"`、`"relative/x"`、`"   "`、`"~/vault"` 必须拒。
   还有没有别的输入形态会**通过** `Path(v).is_absolute()` 检查、但最终
   `resolve()` 落到仓库目录里？校验器与消费方（`system.py` 里的 `Path(...)`）
   是否真的同口径？

3. **session fixture 是否可靠？** 是否依赖 cwd、是否自身写盘、
   session teardown 里 `pytest.fail` 是否真的让 pytest 退出码非 0（而不是
   静默吞掉）？前后两次快照的口径是否真的一致（会不会因环境差异假红）？
   `/tmp` 那一段判据在并行环境下会不会产生假红，我的处置是否恰当？

4. **负控是否真的承重？** 我用「临时让一个用例写 `raw/_probe` → 门变红 →
   还原 → 门变绿」来证明这道门有效。请检查：变红是否**确实由这道门**产生
   （而不是由别的失败顺带产生）、还原后变绿是否可能是因为变异根本没生效。
   我给的四条判据是：① `backend/raw/_probe` 确实被造出来 ② 拒因文本含
   `CARD-TEST-hygiene-vaultinit 不变量门` ③ 消息指名 `backend/raw`
   ④ 被测用例本身 `passed`（红只来自门）。这四条够不够？

5. **这道门的覆盖面是否名实相符？** 它落在 `tests/unit/conftest.py`，
   只在 `tests/unit` 被收集时生效；而本卡查到的真凶在 `tests/contract`。
   也就是说**这道门挡不住今天找到的那条链**。我在验收单里如实写了这一点
   （放到 `tests/conftest.py` 才能全覆盖，但那个文件是别的卡的地盘，硬边界禁改）。
   请判断：这个取舍是否应该在代码注释里也写清楚，避免后人误以为它全覆盖？

6. **`(c)` 与 `(e)` 的冲突处置是否恰当？** `/tmp` 全机共享，多 worktree 并行时
   别的车道跑 `tests/unit` 会让这道门假红，而卡文 (e) 又要求基线 diff 零新增。
   我照卡文把 `/tmp` 纳入 fail，并在消息里写了归属分辨方法。是否有更好的解法？

## 四 输出格式

按严重度分级（BLOCKER / HIGH / MEDIUM / LOW），每条给出：
- 结论一句话
- 你据以判断的**具体文件与行**
- 如果是我判断错了，指出错在哪一步推理

最后给一段总评：这张卡声称的三件事（定位、守卫、回归门）分别成立到什么程度。

## 五 边界

- **不要**评价 `test_startup_health_check.py` 里那个裸 `TestClient(app)`
  的 fixture —— 那是另一张卡（RED-A1，第十三批）的地盘，本卡明确不动它。
- **不要**评价 `tests/contract/**` 的代码本身 —— 本卡对它只做取证与登记，
  不改一行。
- 本卡未修 `vault_init_service.py`、未修 `backend/tests/conftest.py`、
  未修 `config/subject_mapping.yaml`，这些是硬边界，不是疏漏。
- `test_startup_health_check.py` 里那 6 条既有失败是仓库基线（W4 端口门
  哨兵拦现网 Neo4j 7691 导致），不是本卡引入。

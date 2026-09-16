# 独立复核请求 — CARD-G2-7a-TAIL（round-2）

## 〇 判定口径

用户裁定 D-15：有代码改动的卡多轮审查，直到**绑最终 HEAD 的一轮** BLOCKER/HIGH = 0。
round-1 的结论是 `BLOCKER=0 HIGH=0 MEDIUM=1 LOW=0`（绑 `b3baf7d9`）。
那条 MEDIUM 我**接受并已修**，改了代码 ⇒ 按 D-15 必须重送一轮重绑。

**不要用「既有 / 上一轮已过」豁免任何问题** —— 只要落在下面两个地盘文件内就照报：

```
scripts/verify_vault_install.py
backend/tests/unit/test_vault_install_manifest.py
```

## 一 背景 + 最小读取面（请只读下面这些）

本轮审 SHA：`3735b565b2ada7606aa1294c2d82e0520d7b3a64`
round-1 审 SHA：`b3baf7d967692db0b172f5ebb4de9e4ae6357923`
前一卡末 commit（PREV）：`09567e35bf393c34d1ab185e89e6b9effede7141`

1. `git diff b3baf7d967692db0b172f5ebb4de9e4ae6357923 3735b565b2ada7606aa1294c2d82e0520d7b3a64 -- . ':(exclude)_bmad-output'`
   —— **本轮增量**（只有 `test_vault_install_manifest.py` 的 +22 行）。
2. `git diff 09567e35bf393c34d1ab185e89e6b9effede7141 3735b565b2ada7606aa1294c2d82e0520d7b3a64 -- . ':(exclude)_bmad-output'`
   —— 整张卡的代码改动面（两个文件）。
3. `backend/tests/unit/test_vault_install_manifest.py`
   - `:643-754` — 零写门 `test_verifier_write_calls_are_confined_to_write_report`（含 16 条验伪锚）
   - `:762-849` — `_OS_OPEN_READONLY_FLAGS` / `_is_os_open()` / `_os_open_flag_names()` / `_is_readonly_open()`
   - `:3195-3287` — FIFO 回归门与 `_report_section()`（本轮未改，供对照）
4. `scripts/verify_vault_install.py` `:1272-1417`（`_check_hotkeys`，本轮未改，供对照）

## 二 对 round-1 的逐条处置

| 条目 | 处置 | 说明 |
|---|---|---|
| **MEDIUM**：只读豁免会把展开后的写入旗标误判为只读 | **修，0 驳回** | 你给的输入 `os.open(*[p, os.O_WRONLY \| os.O_TRUNC], os.O_RDONLY)` 我独立复现了：修前 helper 返 `True`。你那句「旧分支会拒绝 `Starred`，因此属于本卡新增缺口」也复现了 —— 旧 helper 对同一输入返 `False`。修法见下。 |

**修法**：在 `_is_readonly_open` 的**所有分支之前**拒绝带 `*args` / `**kwargs` 的调用 ——
参数展开时**位置绑定静态不可知**，与原有的「算出来的模式证明不了只读」是同一主张。

**自查又补出同族第二例**（你没点到，我加进了锚）：`os.open(p, os.O_RDONLY, **kw)`
—— 修前放行、旧 helper 拒绝，同一根因。

**配套**：验伪锚 10 → 16 条；另落一份 17 例判定矩阵（4 正例 / 13 反例，0 例不符）。
用 AST 实测确认 `verify_vault_install.py` 里**零处**带展开的写名调用，故这次收紧是纯增强、不误伤。

**round-1 第 4 点（并发替换）**：你指出「普通文件通过形态检查后被换成无写端 FIFO 时，
`:719 read_bytes()` / `:756 open()` / `:1388 read_text()` 仍可能阻塞，且 `--source` 摘要在
新 hotkeys 门之前执行」。我**接受这个描述并已登记为既有缺口移交**，本卡不扩面处理
（本卡地盘只允许改上列两个文件，且卡文明确只修 hotkeys 侧那一处读点）。如果你认为
其中某一条其实**属于本卡新引入**而非既有，请明确指出并给对照输入。

## 三 请按重要性排序回答的问题

① 新加的「拒绝参数展开」是否**完整**？还有没有别的静态形态能让位置绑定不可知却仍被放行
   （例如 `functools.partial`、别名 `_open = os.open` 后调用、`getattr(os, "open")(...)`、
   在 `try/except` 里重新绑定 `os`）？请给具体的未被拦下的输入。

② 这次收紧是否**过头**，会不会把某些确实只读的写法误判成违规，从而让这道门在将来出现假红？
   如果会，请说明代价是否可接受（我的立场是：宁可假红也不放宽这道门的主张）。

③ 16 条验伪锚是否存在**互相蕴含**、实际只覆盖了少数几条独立性质的情况？
   有没有哪一条锚在**任何**实现下都会通过（即空判据）？

④ 零写门本体（`:643-754`）在加了这道前置拒绝之后，`offenders == []` 这条结论的**含义**
   有没有变化？也就是说，现在它证明的是什么、不证明什么？

⑤ 本轮增量有没有影响到 FIFO 回归门与 `_check_hotkeys` 的既有结论（round-1 已核对过的那些）？
   `verify_vault_install.py` 本轮一行未改，请确认这一点与 diff 一致。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：一句话结论 + `file:line` +
一句话说明「在什么输入下会看到这个问题」。没有问题的级别请明确写「无」。
结尾给一行 `BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## 五 边界

- **只读**：不要运行 hook、不要暂存或提交文件、不要连任何数据库或网络服务、不要改动工作树。
- 相关行为请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类说法来描述。
- 不需要评审 `_bmad-output/` 下的文档写作质量，只在它与代码事实矛盾时指出。

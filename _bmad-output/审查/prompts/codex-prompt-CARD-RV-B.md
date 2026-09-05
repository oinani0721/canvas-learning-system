# CARD-RV-B — 对一次「审后整改」的独立复审（只读，不运行）

## §一 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review`

上一张卡（CARD-W4-3b）交付了一套「测试进程不得连生产数据库 / 不得裸启生产 lifespan」的门。
它的独立复核给出 0 BLOCKER、1 HIGH、1 MEDIUM、2 LOW，判「当前不能判通过」。
作者随后提交了一次整改 commit `004e08cc`，**这次整改本身没有经过任何外部复核**。
本卡请你只复审那一次整改，判断它是否真的处理了那四条。

**审面写死**（请只看这个范围，不要用 `2c53a881..HEAD`——那会混进另一张卡后来加的 81 行）：

```
git diff 2c53a881 004e08cc -- \
  backend/scripts/lifespan_isolation_guard_probes.py \
  backend/scripts/lifespan_isolation_negative_control.py
```

实测 = `2 files changed, 153 insertions(+), 51 deletions(-)`（guard_probes 30 行 / negative_control 174 行）。

**建议读取面**（`004e08cc` 版 == 当前 HEAD 版，两者 blob 相同，`negative_control.py` 共 2320 行）：

- `backend/scripts/lifespan_isolation_negative_control.py`
  - `:283-355` —— AST 门总述
  - `:382-420` —— `_ModuleIndex` 的状态字段（含新增的 `_factory_verdicts`）
  - `:627-800` —— 工厂判定核心（`_is_local_app_factory_call` / `_mark_all_fastapi_returning` / `_mark_fastapi_returning`）
  - `:1273-1300` 与 `:1555-1600` —— 常设反例表 `_AST_MUST_FLAG` / 正例表 `_AST_MUST_PASS`
  - `:180-260` —— `run_runtime_files_selftest`（MEDIUM 那条的整改落点）
  - `:1960-1980` —— `main()` 开头（LOW 那条的整改落点）
- `backend/scripts/lifespan_isolation_guard_probes.py:1040-1095` —— `probe_runtime_glob_expansion_sorted`
- 上一轮复核存档全文：`_bmad-output/审查/codex-review-CARD-W4-3b.md`（本树实测 **102 行**）

**请不要读** `backend/tests/support/live_port_guard.py`：那个文件归另一张卡，不在本卡审面。

## §二 作者自述（请独立核对，不要采信）

以下是作者对自己整改的说法，原文摘录。**它们是待核对的断言，不是事实。**

1. `004e08cc` 的 commit message 自述：整改了 1H/1M/2L 四条；HIGH 那条的机制是
   「两个集合生命周期不一致造成暂态资格传播」；修法是「冻结知识 + 按 key 用 and 聚合
   + 整组通过才在轮末一起发布」；并新增该组合形态为常设反例。它还自述把内外循环
   上限加到 20/40 仍不生效，所以问题不在迭代次数。

2. `_mark_all_fastapi_returning` 的 docstring（`:693-739`）复述了同一套说法，其中
   `:722` 一句写着：**「现在的口径（三条一起才成立，少一条就退回上面某个缺陷）」**，
   然后列出上面那三条。

3. 同一方法 `:746-748` 的行内注释写着：**「下面这个差集承重：注释掉它，E 的两条反例
   当场 MISSED」**。

4. `main()` 的注释（`:1964-1976`）自述：把运行时自证放在两条 AST 短路之前是刻意选择，
   并承认上一版给出的理由（「那两条捷径也依赖 runtime_snapshot 的语义」）不成立。

## §三 请回答的问题（按重要性排序）

### ① 上一轮 HIGH 那条点名的输入，在 `004e08cc` 之后是否仍被放行？

上一轮存档给出下面这段 python，并指出它**未被当时那一版的 AST 门拦下**（当时判 0 violation，
而它的父版判 1）：

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app as real_app

def outer():
    return make()

def make():
    a = FastAPI()
    return a

def make():
    return real_app

def test_case():
    app = outer()
    with TestClient(app):
        pass
```

请判断：**把这段源码交给 `004e08cc` 版的 `analyze_source()`（`:1147`），它现在会不会报违规？**

要求：
- 结论必须落到 `negative_control.py` 的**具体行号**，说明是哪一行/哪几行让 `outer`
  拿不到 `make` 的资格；
- 请分别说明 `:740-752` 那个循环里的三步（冻结 / 按 key 聚合 / 轮末整组重建）各自
  在这段输入上起了什么作用；
- 请说明 `_mark_fastapi_returning`（`:754`）的「每一条可达 return 都要合格」判据是否参与；
- 请说明 `_AST_MUST_FLAG`（`:1559-1568` 那一条）是否钉住了同一形态，以及它与上面这段
  输入是否逐字相同（若不同，差在哪里、差异要不要紧）;
- **不接受「已修」「已整改」这类措辞**——请给出可在代码里指认的依据。

### ② 「三条一起才成立，少一条就退回上面某个缺陷」这句自述是否成立？

针对 §二 第 2 条那句话，请逐条判断：把三步中的**任意一步**单独去掉，是否真的会让
某条既有反例漏检，或让 ① 那段输入重新被放行？

请特别注意：这三步是三条独立的开关，还是同一个数据流改动的三种说法？如果是后者，
那句自述就比它能证明的范围宽。请给出你的判断和依据行号。

### ③ `guard_probes.py` 那 30 行改动，是否只改了探针、没有改被测对象？

`probe_runtime_glob_expansion_sorted`（`:1040-1095`）新增了一段「前提探测」。请判断：
- 它是否只读取被测门的输出、没有放宽被测门本身的判据；
- `premise_ok` 为假时判 FAIL 的处理，是否会把一个本来能发现问题的探针变成恒绿或恒红；
- 它调用 `builtin compgen -G` 拿未排序展开，这个前提探测本身是否可靠。

### ④ MEDIUM 与两条 LOW 的整改是否到位？

- MEDIUM（`run_runtime_files_selftest`，`:221-246`）：原判据是 `runtime_files(fake) != runtime_files(fake)`，
  新判据改成与独立列举的期望清单比对 + 验证乱序前提。请判断新判据是否真的能在
  「去掉 `sorted()`」时失败，以及 `expected` 那份期望清单是不是用被测对象自己算出来的。
- LOW（`main()` `:1964-1976`）：上一轮建议是把自证移到 AST 短路之后；作者选择保留行为、
  只更正说法并登记代价。请判断这个处置是否可接受，还是应当按原建议改行为。
- LOW（`guard_probes` 排序探针）：见 ③。

## §四 输出格式

1. 一张逐条表：`编号 | 上一轮结论 | 整改落点(文件:行号) | 你的裁定 | 依据`，
   裁定用「整改成立 / 整改不成立 / 整改成立但自述宽于可证范围 / 无法判定」。
2. ① ② 两问各给一段结论，行号必须具体。
3. **末行固定写**：`BLOCKER/HIGH 清零：是/否`。

## §五 边界

- **只读**。不要运行任何脚本、测试、容器或数据库；不要修改任何文件。
- 结论请以代码本身为依据；如需推演，请写明是推演并给出行号。
- 本卡不要求你评估这套门的整体设计是否合理，只看这一次整改。

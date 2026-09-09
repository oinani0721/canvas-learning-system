你是独立代码审查者。这是**第五轮，也是本卡的最后一轮**（round-5，轮次上限）。只读，不要修改任何文件。

# 〇 本轮定位

轮次记录（全部由你的前几轮给出，作者每轮全采纳）：
- r1: BLOCKER=0 HIGH=0 + 2 MEDIUM + 3 LOW
- r2（绑 `..faeda37f`）: BLOCKER=0 HIGH=0 + 2 MEDIUM + 2 LOW
- r3（绑 `..bcbe2741`）: BLOCKER=0 HIGH=0 MEDIUM=0 + 2 LOW
- r4（绑 `..1e326860`）: BLOCKER=0 HIGH=0 MEDIUM=0 + **1 LOW**

**本轮绑定最终 HEAD `385078b8`**，审查面 = `git diff 7004a365 385078b8`（四个 commit）。
第四个 commit 是纯文档：把台账里最后一处指向本卡文件的行号
（`test_sync_exception_classification.py:48-58 _dev_settings`）改为
`test_sync_exception_classification.py::_dev_settings`，因为 r3 已立下
「本卡位置一律用名称」的规则，留着它是自相矛盾。作者改后复查，指向本卡五个文件的
行号引用已清零。

# 本轮只需回答三件事

1. **是否还有 BLOCKER 或 HIGH。** 这是停轮的唯一硬条件。
2. **r4 那条 LOW 是否已落实**，以及这个改动有没有引入新问题。
3. **有没有任何一处声明比它的证据更宽** ——这是本卡四轮里反复出现的问题类型
   （r1 的「移交理由过强」、r2 的「全仓没有 409 覆盖」、r3 的「一直绿」、
   r4 的「一律用名称却漏一处」都属于此类）。请最后扫一遍：
   `backend/tests/support/authed_client.py`、三处 `client` fixture docstring、
   `test_sync_exception_classification.py::_dev_settings` docstring、
   `_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt`、
   `_bmad-output/验收单/UAT-CARD-RED-A1-auth-2026-09-09.md`
   里的每一句事实性声明，指出仍然过宽（或已变得过窄）的那些。

前四轮已核过且未被动摇的结论**一律不必重复论证**：覆盖不泄漏、实例头覆盖请求路径、
17 条 active-vault 桩合理、sync 两桩未替换异常分类路径、37=32+5 闭合、断言未变、
未改生产代码与两个 conftest、「另有 409 覆盖」与「同一组桩」属实、各处计数与外部
行号准确、四个 commit 之间可执行 AST 一致。

# 四 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级列出。每条给出：
- `file:line`
- 你的判断依据（引用具体代码或存档内容，不要只给结论）
- 建议的处置

若某一级没有问题，明确写「无」。最后给一段总评，说明这套改动是否达成了它声称的目标
（让 37 条业务断言真正跑到业务层），以及有没有把问题从一处挪到另一处。

# 五 边界（这些不在本次审查范围）

- 不评 W4 端口哨兵本身的设计（`backend/tests/support/live_port_guard.py` /
  `guard_plugin.py`）——它是别的卡的地盘。
- 不评 `backend/tests/unit/conftest.py` 的内容——那是同批另一张卡的地盘。
- 不评仓库既有的 pyright 存量问题。
- 不评 `_archive/` 下的任何内容。
- 不评那 5 条被判「移交」的用例应该怎么重写——只需判断「移交」这个决定本身是否成立。

# 六 最小读取面（请只读这些）

- 本卡改动全文：`git diff 7004a365 385078b8`（四个 commit，含新文件）
- 前四轮存档：`_bmad-output/审查/codex-review-CARD-RED-A1-auth-r{1,2,3,4}.md`
- 新文件全文：`backend/tests/support/authed_client.py`
- `backend/app/security.py` 第 88-166 行
- `backend/app/api/v1/endpoints/chat.py` 第 38-52 行、第 283-330 行
- `backend/app/api/v1/endpoints/sync.py` 第 100-140 行
- `backend/tests/conftest.py` 第 441-452 行、第 470-520 行
- `backend/tests/unit/conftest.py` 第 393-420 行
- `backend/tests/unit/test_sync_batch_auth.py` 第 55-125 行（本卡打桩的先例，只读不改）
- `backend/app/core/vault_scope.py` 第 100-185 行
- 证据目录：`_bmad-output/审查/evidence-red-a1-auth/*.txt`
  其中 `second-layer-*.txt` 是第二层红三分类表，
  `closure-37-*.txt` 是 37 条去向的闭合校验，
  `gate-fixture-constraints-*.txt` 与 `gate-bare-testclient-*.txt` 是两道结构判据，
  `ruff-format-drift-proof-*.txt` 是格式漂移归属的证明。

# Codex 复核 round-1 — CARD-TOOL-dredd-decide [BATCH-2026-09-05-第十一批]

你是一名严格的代码复核者。请只做**只读**审查，不要修改任何文件。

## 仓库与审查面

工作树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool`

审查面 = `git diff 46ed18f1 e6f9aebc`，两个 commit：
- `7b8383d2` 只含裁决页 `_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md`
- `e6f9aebc` 含该页的 §六 补记 + 三个文件的改动：
  `backend/tests/contract/test_openapi_contract.py`、`pyproject.toml`、
  `tests/contract/requirements.txt`

**本卡没有改任何 workflow**（`.github/workflows/test.yml` 与 `api-spec-sync.yml` 零字节改动），
这是用户在前提被推翻后重裁的结果，理由写在裁决页 §六。

## 背景

这是一张「Dredd 契约测试：复活还是退役」的裁决卡。原定方案（用户先前已裁）是
**乙 = 退役 Dredd + 把 schemathesis 那份合约测试真接进 CI 白名单 + 配 import 硬前置**。
车道在执行 (b) 之前做了可行性实测，结果推翻了乙案的前提，于是把改变后的前提重新提交
给用户，用户重裁为「只落不依赖该前提的部分、不退役」。

## 请逐条判断真伪（不要采信我的措辞）

1. **「那个替代品在任何 schemathesis 版本上都跑不通」**。我的依据：
   `backend/tests/contract/test_openapi_contract.py:26` 用 `schemathesis.openapi.from_asgi`
   （4.x 形态），而改前的 `:60-65` 用 `schemathesis.checks.status_code_conformance`
   这类模块属性（3.x 形态）；本机 4.14.3 下 `dir(schemathesis.checks)` 里那四个名字
   都不存在，且 `hasattr(schemathesis, "from_asgi")` 为 False。
   请判断：这个推理是否成立；「任何版本都跑不通」是否说得过宽（例如是否存在某个
   中间版本两者并存）。

2. **我的修法是否削弱了检查**。改后用
   `schemathesis.checks.load_all_checks()` + `CHECKS.get_by_names([...四个同名...])`。
   请判断：取到的是否确实是同名的那四个 check；语义是否与原意图一致；
   `load_all_checks()` 放在测试函数体内（而不是模块级）是否有副作用或性能问题。

3. **版本口径归一**。`pyproject.toml` 的 `schemathesis>=3.0` 改为 `>=4.0`；
   `tests/contract/requirements.txt` 原 `>=3.19.0` 改为不写版本并指回 pyproject。
   我另断言该 requirements 文件**全仓没有任何安装方**。
   请判断这些是否成立，以及「不写版本」这一形态是否会带来新的歧义。

4. **裁决页 §六 的三条实测结论是否过宽**：
   (a) `importorskip` 的假绿机制——我说「模块不存在 → 1 skipped / rc=5；放进 17 文件
       白名单后整步 rc=0 绿，skip 被无声吸收」；
   (b) 性能——我说 schemathesis `case.call()` 单次 20–50s，而 `httpx.ASGITransport`
       直调同端点 0.01s、`TestClient` 直调 0.00s，因此「慢的不是应用，是 schemathesis
       4.x 的 ASGI 传输层」；
   (c) 我排除了两个假设：本机服务全 closed（所以不是真在查库）、禁系统代理反而更慢
       （所以不是代理超时）。
   请判断每条的证据是否支撑其结论，尤其是 (b) 的归因是否过强（例如是否可能是
   hypothesis 的数据生成而非传输层）。

5. **「不退役」这个处置是否恰当**。我的论证是：乙案的退役是**有条件的**，条件是替代品
   真能接上；条件不成立时单做退役等于单向减少覆盖面。
   请判断这个论证是否成立，以及是否存在我没考虑到的第三条路。

## 我明确知道自己没有证明的事

- 没有在 GitHub 上实跑任何 workflow；所有结论都来自本机。
- schemathesis **不等价于** Dredd：Dredd 走真实 HTTP 栈按 example 回放并覆盖 hooks
  流转与鉴权，schemathesis 是进程内 `from_asgi` 按 schema 生成。本卡未声称二者等价。
- 20–50s 的方差很大（同一 operation 两次测得 22s 与 49s），我只做了少量样本，
  没有做统计意义上的测量，也没有深入定位 schemathesis 内部把时间花在哪一步。
- 没有证明修好 API 之后那 206 个用例**能通过**——它们现在的失败形态从
  `AttributeError` 变成了 `DeadlineExceeded`，我没有在放开 deadline 后跑完整套。

## 输出要求

结构化清单：每条写明 **严重度（BLOCKER / HIGH / MEDIUM / LOW）**、**位置（文件:行）**、
**问题**、**判断依据**、**建议处置**。无法从仓库现状直接判定的标注为「需要额外证据」
并写清需要什么证据。最后单独回答一句：这次改动里有没有**数据丢失 / 安全 / 越权写入**级别的问题。

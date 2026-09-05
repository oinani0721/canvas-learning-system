# Codex 复核 round-2 — CARD-TOOL-dredd-decide [BATCH-2026-09-05-第十一批]

你是一名严格的复核者。请只做**只读**审查，不要修改任何文件。

## 本轮的审查面（与卡文原定不同，原因如实说明）

工作树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool`

卡文原定 round-2 = 「只审负控与 `.github/workflows/test.yml` / `api-spec-sync.yml` 的 diff」。
**本卡没有改任何 workflow**（两个文件零字节改动），该审查面为空。
原因：卡文的方案乙（退役 Dredd + 把合约测试接进 CI）在执行前做了可行性实测，结果推翻了
乙案的前提，用户据此重裁为「只落不依赖该前提的部分、不退役」。

因此本轮如实改为审**「不落 (b) 的证据链是否成立」**——即那些实测与由它们推出的处置。
这是本卡唯一需要外部对抗的地方：**如果证据链不成立，那么"不接进 CI"这个结论就是错的，
本卡等于用一份不可靠的测量说服用户放弃了一件本该做的事。**

审查材料：
- 裁决页 `_bmad-output/审查/2026-09-05-Dredd-复活或退役-裁决页.md`（尤其 §六）
- 验收单 `_bmad-output/验收单/UAT-CARD-TOOL-dredd-decide-2026-09-05.md`（尤其 §三、§五、§九）
- 代码 diff `git diff 46ed18f1 HEAD`
- round-1 的报告 `_bmad-output/审查/codex-review-CARD-TOOL-dredd-decide-r1.md`
  与我对它的处置（见验收单 §十）

## 请重点判断这几件事

1. **性能测量是否足以支撑"不能进 CI"这个结论。**
   我测到 schemathesis 4.14.3 的 `case.call()` 单次 **20–50s**，而 `httpx.ASGITransport`
   直调同端点 **0.01s**、`TestClient` 直调 **0.00s**、`TestClient` 跑一次 lifespan 7.1s。
   由此推出 206 个 operation 即使只跑 1 个 example 也要 70 分钟以上。
   请判断：样本量（个位数）与方差（同一 operation 22s / 49s）是否足以支撑该结论；
   我把归因落在「schemathesis 4.x 的 ASGI 传输层」是否过强；
   有没有我没排除的解释（我排除了「真在查库」与「系统代理超时」两个）。

2. **那两个"对照"是否真的可比。** 我拿 `httpx.ASGITransport` / `TestClient` 直调
   与 schemathesis 的 `case.call()` 相比。请判断这个对照是否公平——
   schemathesis 可能在 `call()` 里做了别的必要工作（例如按 schema 生成请求体、
   处理 `Case` 序列化），如果是，那 20s 就未必全是"传输层开销"。

3. **`importorskip` 的假绿论证是否成立。** 我的演示是：模块不存在 → `1 skipped` 且
   **rc=5**；模块在但版本不对 → `1 failed` 且 rc=1。我据此说「放进 17 文件白名单后
   整步 rc=0 绿、skip 被无声吸收」。请判断这个推论是否成立（我**没有**真的把它放进
   白名单跑过，这一步是推理不是实测）。

4. **"不退役"这个处置。** 我的论证：乙案的退役是有条件的（条件=替代品能接上），
   条件不成立时单做退役是单向减少覆盖面。请判断该论证是否成立，是否存在更好的第三条路。

5. **自我更正是否彻底。** 我在本卡中途推翻了自己的一条断言（原写「该合约测试在任何
   schemathesis 版本上都跑不通 / 从未被真正执行过」，实测 3.25/3.30/3.39 上两套 API
   并存、能跑）。该错误断言**已经写进了 commit `e6f9aebc` 的 message**，我在裁决页与
   验收单里做了显式更正但**没有改写那条 commit message**。
   请判断：更正是否覆盖了所有仍在生效的地方；仓库里是否还留有其它基于该错误断言的表述。

6. **副作用对账是否可信。** 我在跑任何会在进程内起 app 的东西之前拍了 `data/` 快照，
   跑完对账两次（第二次在明确跑过一次 lifespan 之后），三次均 342 行逐行相同。
   请判断这个对账口径是否足以支撑「未污染」的结论。

## 我明确知道自己没有证明的事

- 没有在 GitHub 上实跑任何 workflow。
- 没有把合约测试真的放进 `test.yml` 白名单跑过（第 3 点的推论因此是推理）。
- 没有在放开 deadline 后跑完整套 206 个用例（需要小时级）。
- 没有定位 schemathesis 内部把 20–50s 花在哪一步。
- `openapi.from_asgi` 与 `checks.*_conformance` 的确切交叠版本区间未知
  （3.19–3.24 与 4.0–4.13 都没测）。

## 输出要求

结构化清单：每条写明 **严重度（BLOCKER / HIGH / MEDIUM / LOW）**、**位置**、**问题**、
**判断依据**、**建议处置**。无法从现状直接判定的标注「需要额外证据」并写清需要什么。
最后单独回答两句：
(1) 这次改动里有没有**数据丢失 / 安全 / 越权写入**级别的问题；
(2) 「不把合约测试接进 CI」这个结论，依你看是**证据充分**、**证据不足但方向对**，
    还是**结论错误**。

---

## round-1 之后发生了什么（本轮请在此基础上审）

round-1 报了 9 条（BLOCKER 0 / HIGH 2 / MEDIUM 5 / LOW 2），我逐条源码 + 实测复核后
**全部采信**，其中四条推翻了我自己的断言，已在 `4cf0a3ba` 撤回：

1. 「任何版本都跑不通 / 每个用例必 AttributeError」——撤回。一次性 venv 实测
   3.25/3.30/3.39 两套 API 并存；4.14.3 上插件在收集期 `load_all_checks()`。
   **端到端实测**：改前版本原样跑真 pytest 一个 operation，拒因是
   `hypothesis.errors.DeadlineExceeded: Test took 20857.69ms`，**不是 AttributeError**，
   且跑满 9 个 example。⇒ 改前代码在当前环境下并没有坏，本卡对该文件的改动
   **已降级为"防御性加固"**。
2. 「慢的不是应用，是传输层」——撤回，归因反了（`with asgi.get_client(app)` →
   `starlette_testclient.TestClient(app)` → 每次跑一遍 lifespan，本 app 单次 7.1s）。
3. 「payload 缺 vault_id ⇒ 必然 422」——撤回（实际命令 `--method GET --names || true`
   + job 级 `continue-on-error`，根本不发请求）。
4. 「单向覆盖面减法」——撤回（job 已 `if: false`，删它减的是恢复选项而非当前覆盖）。

另修两处我自己写错的文档虚称：`pyproject.toml` 曾称 CI 已配硬前置（从未加过）；
`tests/contract/requirements.txt` 曾改成裸包名靠注释指路（pip 读不到 pyproject 约束，
等于取消了原有下限），已改回自带 `>=4.0`。

**本轮请特别审这件事**：我在一张卡里连续三次用「受控条件与真实路径不同的探针」
去代表真实路径（一个版本→所有版本、裸 import→pytest 入口、复用客户端→每次新建）。
请判断：`4cf0a3ba` 之后，仓库里**是否还残留任何基于这三个错误前提的表述或代码**；
以及现在给出的新结论（尤其"单个 operation 209s / 206 个≈12 小时"与
"根因是每次调用跑一遍 lifespan"）是否又犯了同一类错误。

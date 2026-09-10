# CARD-RED-C2 独立复核请求（round-2 · 整改后复审）

## 一 背景 + 最小读取面（写死，请只读这些）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`
分支 `card/u11-red-c`。上一卡（U11-A）末 commit = `5139428d`。
**round-1 审查 SHA = `c0d61a12`；本轮（round-2）审查 SHA = `cfd299f3`。**

round-1 你给出的分级是 BLOCKER 0 / HIGH 1 / MEDIUM 6 / LOW 4，本车道**一条未驳回**：
4 条改了代码，6 条收窄了声明，1 条如实登记不修。本轮请复核整改是否成立、有没有引入新问题。

本卡任务与硬边界（同 round-1）：`backend/tests/unit` 的既有红里属「契约演进未跟测」的 66 条，
每条先取到一行「契约演进依据」（sha + 日期 + 一句）再改断言；取不到依据的移交另一张卡。
只改测试文件，`backend/app/**` 零改动；不放宽 `config.py` 安全校验器；不改 reranker 权重表；
不把归档脚本路径重指 `_archive/`；不新增 skip；不用 `xfail(strict=False)`；不删用例；不降低判据强度。

**最小读取面**（不要读其它文件）：

1. round-1 → round-2 的整改 diff：
   `git diff --no-color c0d61a12 cfd299f3 -- . ':(exclude)_bmad-output'`
2. 本卡完整代码 diff（可选，用于看整体）：
   `git diff --no-color 5139428d cfd299f3 -- . ':(exclude)_bmad-output'`
3. `_bmad-output/审查/evidence-red-c2/c2-verdicts.md`（66 行依据表；**§六 是本轮整改逐条记录**）
4. `_bmad-output/审查/evidence-red-c2/negctl-compose-exemption-20260909T134534.txt`（HIGH 的负控存档）
5. `backend/app/config.py:268-300`（安全校验器现状）
6. `backend/app/clients/neo4j_client.py:1105-1130`（读侧收口后的查询与绑定参数）
7. `backend/app/services/lancedb_index_service.py:444-462`（initialize 与文件检查的先后）
8. `backend/app/services/agent_service.py:2196-2250`（`_format_learning_memories` 拼装规则）
9. `_bmad-output/审查/evidence-red-c2/unit-after-20260909T135407.txt`（目录级收工输出，首行是 `HEAD=`）
10. `_bmad-output/审查/evidence-red-c2/files-23-20260909T135910.txt`（23 文件级收工输出，首行是 `HEAD=`）
11. `_bmad-output/审查/evidence-red-c2/gates-20260909T135944.txt`（强度门 / fixture 门 / 地盘门，含 HEAD）

## 二 本轮整改自述，请独立核对（不要采信）

1. **HIGH（compose 豁免）**：改为三段判据——① 行内容在豁免名单里；② 该行所属顶层 service 恰为
   `neo4j`；③ 每条豁免行至多出现一次。三段都用子集/上界而非相等。负控（第 4 项）把测试模块的
   `PROJECT_ROOT` 指到临时目录喂三种 compose，你 round-1 给的复现输入**由 PASS 变 FAIL**。
2. **反向锚补第 4 条**：`DEBUG=true` 但 `CORS_ORIGINS` 不含 localhost/127.0.0.1 时仍须抛，
   钉住 `is_local` 合取的 CORS 半边。
3. **安全锚补占位符判据**：每个 kwarg 都必须在查询文本里有对应 `$name` 占位符
   （对非字符串值直接查 `str(v) in query` 会误报，故用正面形式表达同一主张）。
4. **`none_score` 用例升级整串 `==`**，期望值按生产拼装规则逐段抄写、不 import 格式化器。
5. **`initialize` 两条各加次数锚 + 用 `mock_calls` 下标加顺序锚**（挪到索引之后即红）。
6. **六处声明收窄**（归档族仍起 node 子进程 / sha 扫描的覆盖面 / floor 摘掉未必七条全红 /
   签名替身只覆盖增参一面 / 格式化用例送审时只有一条升级 / 依据 sha 实际 25 个而非 21 个），
   全部写进 `c2-verdicts.md` §六。
7. **全部裁判已在 `cfd299f3` 上重跑**，证据文件首行写入 `HEAD=`（round-1 你指出的绑定问题）。

## 三 请回答的问题（按重要性排序）

1. **整改是否真的成立**：三段 compose 判据有没有新的漏过面（例如豁免行出现在 `neo4j` 的
   非 `volumes` 段、或 service 名被改写、或 YAML 缩进变化导致 service 归属解析错）？
2. **有没有因整改引入新的自证或强度下降**：新增的 `$name` 占位符断言、顺序断言、整串相等断言，
   分别在什么输入下会红？有没有哪条其实恒真？
3. **第 4 条反向锚**是否真能在 `is_local` 被简化成「只看 DEBUG」时翻红？
4. **§六 的六处「收窄声明」是否收得够**——还有没有别的地方我把话说得比证据宽？
5. **round-1 未修的那条同源盲区**（物理化期望与生产同一 helper）登记得是否充分？
6. **越界复查**：`backend/app/**` 是否仍零改动？有没有碰到上一卡已处置的用例、
   另一张卡的 R 族用例、或既有 skip 标记？
7. 还有没有**新的**「判据看着绿、其实没证明」的地方？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
`<级别> | <file:line> | <一句问题> | <一句复现思路>`。
没有问题的级别请显式写「无」。不要给补丁。

## 五 边界

- 只读，不要改任何文件；不要连数据库（7687 / 7691 是现网端口，测试进程不得连接）。
- 不要评价另一张卡（`CARD-RED-R`）对那 4 条外来红的定性。
- 不要评价 reranker 权重表本身该不该翻转（属另一张后续卡）。
- 不要提出「改 `backend/app/**`」的建议——本卡硬边界是零生产改动。

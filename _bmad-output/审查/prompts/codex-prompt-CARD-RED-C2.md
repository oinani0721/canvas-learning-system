# CARD-RED-C2 独立复核请求（round-1）

## 一 背景 + 最小读取面（写死，请只读这些）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`
分支 `card/u11-red-c`。上一卡（U11-A）末 commit = `5139428d`，本卡审查 SHA = `c0d61a12`。

本卡任务：`backend/tests/unit` 的既有红里，属「契约演进未跟测」的 66 条 nodeid，
每条先取到一行「契约演进依据」（commit sha + 日期 + 一句），再改断言；
取不到依据的只能移交另一张卡（`CARD-RED-R`），不得为了让测试变绿而硬改。
硬边界：只改测试文件，`backend/app/**` 零改动；不得放宽 `config.py` 的安全校验器；
不得改 reranker 权重表；不得把归档脚本路径重指 `_archive/`；不得新增 skip；
不得用 `xfail(strict=False)`；不得删用例；不得降低判据强度。

**最小读取面**（不要读其它文件）：

1. 本卡代码 diff：
   `git diff --no-color 5139428d c0d61a12 -- . ':(exclude)_bmad-output'`
2. `_bmad-output/审查/evidence-red-c2/c2-verdicts.md`（66 行依据表，本卡主产出）
3. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/red-align-da690bf8.md` 的 `:131-200`（本卡 66 条 nodeid 的唯一来源，nodeid 在 `:134-199`）
4. `backend/app/config.py:268-300`（安全校验器现状）
5. `backend/app/services/supplementary_reranker.py:55-75` 与 `:190-205`（权重表与生产自述注释）
6. `backend/app/clients/neo4j_client.py:1069-1130`（读侧收口后的 get_review_suggestions）
7. `backend/app/core/vault_scope.py:596-621`（read_scope_params 返回键）
8. `_bmad-output/审查/evidence-red-c2/red-diff-20260909T132109.txt`（目录级收工 diff）
9. `_bmad-output/审查/evidence-red-c2/files-23-20260909T132712.txt`（23 文件级收工输出）
10. `_bmad-output/审查/evidence-red-c2/gates-20260909T132820.txt`（强度门 / fixture 门 / 地盘门）
11. `_bmad-output/审查/evidence-red-c2/sha-proof-sweep-20260909T132543.txt`（依据 sha 机器复核）

## 二 作者自述，请独立核对（不要采信，请自己验）

1. 66 条**每条都取到了依据 sha**，且不是「一个 sha 抄 66 遍」：实际用到 21 个不同 sha，
   `sha-proof-sweep` 逐行验了「该 sha 的 diff 里确有本条断言所指的那处改动」，不合格行数 = 0。
2. 处置计数：改断言/改测试替身 54、`xfail(strict=True)` 交接 12、移交 `CARD-RED-R` 0。
3. 锚①（`test_config_neo4j` 9 条）：只在测试侧加 `_LOCAL_DEV_ENV = {"DEBUG": "true"}` 让
   Settings 过校验，未改校验器；并新增 3 条 fail-closed 反向锚。
4. 锚②（`test_supplementary_reranker` 9 条）：只改测试，未动权重表与 floor 逻辑。
5. 锚③（归档路径 5 条）：`xfail(strict=True)` + 交接卡名，未把路径重指 `_archive/`，
   未在单元测试里起子进程。
6. 锚④（安全面 1 条）：`:191-194`「原始恶意串不得出现在 query 文本」的断言原样保留，
   只改了参数名/值形态断言，并加了一条更宽的「任何 kwarg 值都不得出现在 query 文本」。
7. 目录级 diff 的 `>` 行为零；`<` 行按 `comm` 拆分后本卡贡献恰为 66 条。
8. 23 文件级 failed 集合逐条等于预声明的 4 条外来红（属另一张卡，本卡禁碰），`XPASS` = 0。
9. fixture 门：无 `autouse=True` 新增，未读 `.env`、未读 `ACTIVE_VAULT`。
10. 作者已自行声明两件对自己不利的事，请一并核对是否**声明得足够、有没有漏**：
    - `c2-verdicts.md` §5.1：有 2 条 nodeid 是**改了测试函数名**才离开红集合，不是「转绿」；
    - `c2-verdicts.md` §5.2：有 1 条判据在特定输入上**确实变弱**（compose 硬编码路径豁免名单）。

## 三 请回答的问题（按重要性排序）

1. **有没有哪一条把断言改成了自证**——锁测试内自定义常量、锁 mock 自己的返回值、
   或判据强度低于原断言？请逐条问「这条新断言在什么输入下会红」，
   并指出 `c2-verdicts.md` 最后一列里哪些回答站不住。
2. **安全面（锚④）**：`:191-194` 的断言是否真的原样保留、没有被削弱？
   新的参数形态断言是否仍能发现「参数值被拼进查询文本」这一失效？
3. **锚①**：让 9 条变绿的改法有没有把 fail-closed 契约的覆盖一并弄没？
   新增的反向锚是否真的存在、当前是否 PASSED、是否真能在校验器被放宽时翻红？
4. **锚③与其它 xfail**：12 条 `xfail(strict=True)` 的 reason 是否都写明了归哪张卡？
   有没有哪一条实际 XPASS（strict 下 XPASS 即失败）？有没有哪一条其实应该改断言而不是交接？
5. **锚②**：重造数据后测的是否仍是 floor 机制本身，而不是变成在测权重值？
6. **越界**：有没有顺手改到上一卡（U11-A）已处置的用例、另一张卡的 R 族用例、
   或任何既有 `skip` 标记？`backend/app/**` 是否真的零改动？
7. 作者在 §5.1 / §5.2 的两处自认之外，**还有没有别的「判据看着绿、其实没证明」的地方**？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
`<级别> | <file:line> | <一句问题> | <一句复现思路>`。
没有问题的级别请显式写「无」。不要给补丁。

## 五 边界

- 只读，不要改任何文件；不要连数据库（7687 / 7691 是现网端口，测试进程不得连接）。
- 不要评价另一张卡（`CARD-RED-R`）对那 4 条外来红的定性。
- 不要评价 reranker 权重表本身该不该翻转（那属于另一张后续卡的范围）。
- 不要提出「改 `backend/app/**`」的建议——本卡硬边界是零生产改动。

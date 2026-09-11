# CARD-RED-C2 独立复核请求（round-4 · 第三次整改后复审）

## 一 背景 + 最小读取面（写死，请只读这些）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`
分支 `card/u11-red-c`。上一卡（U11-A）末 commit = `5139428d`。
**round-1 `c0d61a12` → round-2 `cfd299f3` → round-3 `0909e935` → 本轮（round-4）审查 SHA = `5e3c7998`。**

round-3 你给出 BLOCKER 0 / HIGH 1 / MEDIUM 1 / LOW 4，本车道**一条未驳回**：
4 条改了代码，1 条重做了负控，1 条补了实证输出。三轮累计 24 条意见，无一驳回。

本卡任务与硬边界（同前三轮）：只改测试文件，`backend/app/**` 零改动；不放宽 `config.py`
安全校验器；不改 reranker 权重表；不把归档脚本路径重指 `_archive/`；不新增 skip；
不用 `xfail(strict=False)`；不删用例；不降低判据强度。

**最小读取面**（不要读其它文件）：

1. round-3 → round-4 的整改 diff：
   `git diff --no-color 0909e935 5e3c7998 -- . ':(exclude)_bmad-output'`
2. `backend/tests/unit/test_story_1_7_env_config.py`（compose 判据全文）
3. `backend/tests/unit/test_story_30_24_boundary.py:160-260`（安全面判据）
4. `docker-compose.yml`（被判据读取的对象）
5. `_bmad-output/审查/evidence-red-c2/negctl-compose-exemption-r3-20260909T143735.txt`（9 输入负控）
6. `_bmad-output/审查/evidence-red-c2/negctl-security-r3-20260909T143823.txt`（安全面负控）
7. `_bmad-output/审查/evidence-red-c2/c2-verdicts.md` 的 **§六 / §七 / §八**（三轮处置记录）
8. `_bmad-output/审查/evidence-red-c2/unit-after-20260909T143922.txt`（目录级，首行 `HEAD=`）
9. `_bmad-output/审查/evidence-red-c2/files-23-20260909T144643.txt`（23 文件级，首行 `HEAD=`）
10. `_bmad-output/审查/evidence-red-c2/gates-20260909T144721.txt`（门 + §〇 SHA 绑定实证）

## 二 本轮整改自述，请独立核对（不要采信）

1. **HIGH（后代字段被豁免）**：位置判据由 `path[:3]` 改为**深度精确等于 4**
   （`services / neo4j / volumes / <序号>`）。长格式挂载的 `source` 落在深度 5，会红。
2. **MEDIUM（合并键消去原文）**：数量判据从「数 YAML 解析值」改为**数原始文本行**——
   每条豁免值在全文至多出现一次。`<<:` + 覆盖导致的「原文两次、解析一次」会红。
3. **LOW（只审最后一次调用）**：改为逐条审 `run_query.call_args_list` 的**全部**调用。
4. **LOW（只剥行注释）**：块注释 `/* */` 也剥。**并如实声明**：剥注释只堵「占位符藏在
   注释里」这一面，仍不能证明该参数真的参与查询语义。
5. **LOW（负控标注不实）**：重做负控，新片段插在 `services:` 行正下方；②④⑤ 附
   `yaml.safe_load` 结构自证。旧负控保留，并在新负控首部写明它错在哪。
6. **LOW（缺空 diff 实证）**：`gates-*` §〇 给出实际输出——既有本轮的非空 diff，
   也有「`4449e292` → `0909e935` 排除证据目录后为空」的空 diff。

## 三 请回答的问题（按重要性排序）

1. **深度精确等于 4 之后**，还有没有让硬编码路径生效却两轴都放行的写法？
   （例如 volumes 短格式里用 YAML 标签、非字符串标量、或把路径拆成拼接片段。）
2. **文本层数量判据**有没有新的漏过面或**误报**面？例如同一行里出现两次、
   跨行折叠（`>-` / `|`）把一条路径拆成多行、或注释行与真实行内容完全相同。
3. **逐条审全部 `run_query` 调用**之后，安全断言会不会对**合法**的多次调用产生误报？
4. 两份负控是否可信：有没有「变异没生效却报 FAIL」「还原没做干净」「标注仍与实际不符」？
5. **§六 / §七 / §八 的收窄声明是否收得够**——还有没有别的地方我把话说得比证据宽？
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

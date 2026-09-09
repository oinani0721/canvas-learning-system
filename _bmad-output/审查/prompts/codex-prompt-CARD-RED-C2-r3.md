# CARD-RED-C2 独立复核请求（round-3 · 第二次整改后复审）

## 一 背景 + 最小读取面（写死，请只读这些）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u11-red-c`
分支 `card/u11-red-c`。上一卡（U11-A）末 commit = `5139428d`。
**round-1 审查 SHA `c0d61a12` → round-2 审查 SHA `cfd299f3` → 本轮（round-3）审查 SHA = `0909e935`。**

round-2 你给出 BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 5，本车道**一条未驳回**：
4 条改了代码（HIGH + 1 MEDIUM 用同一处重写关掉、1 LOW 改判据、1 LOW 改注释），
1 条 MEDIUM 用「重跑 + 代码树等价证明」关掉，3 条 LOW 收窄声明。

本卡任务与硬边界（同前两轮）：只改测试文件，`backend/app/**` 零改动；不放宽 `config.py`
安全校验器；不改 reranker 权重表；不把归档脚本路径重指 `_archive/`；不新增 skip；
不用 `xfail(strict=False)`；不删用例；不降低判据强度。

**最小读取面**（不要读其它文件）：

1. round-2 → round-3 的整改 diff：
   `git diff --no-color cfd299f3 0909e935 -- . ':(exclude)_bmad-output'`
2. `backend/tests/unit/test_story_1_7_env_config.py`（compose 判据重写后的全文）
3. `backend/tests/unit/test_story_30_24_boundary.py:160-240`（安全面判据）
4. `docker-compose.yml`（被判据读取的对象）
5. `_bmad-output/审查/evidence-red-c2/negctl-compose-exemption-r2-20260909T141039.txt`（7 个输入的负控）
6. `_bmad-output/审查/evidence-red-c2/negctl-security-placeholders-20260909T141210.txt`（运行期变异负控）
7. `_bmad-output/审查/evidence-red-c2/c2-verdicts.md` 的 **§六 与 §七**（两轮逐条处置记录）
8. `_bmad-output/审查/evidence-red-c2/unit-after-20260909T141449.txt`（目录级收工输出，首行 `HEAD=`）
9. `_bmad-output/审查/evidence-red-c2/files-23-20260909T142327.txt`（23 文件级收工输出，首行 `HEAD=`）
10. `_bmad-output/审查/evidence-red-c2/gates-20260909T142452.txt`（门 + **代码树等价证明**，首行 `HEAD=`）

## 二 本轮整改自述，请独立核对（不要采信）

1. **HIGH + MEDIUM（compose）**：判据改成两轴。
   轴一（内容）保持**逐行原始文本**扫描——不换成只看 YAML 值，因为 YAML 解析丢注释，
   写在注释里的硬编码路径会漏过（原断言的正则是对全文跑的）。
   轴二（位置）改用 `yaml.safe_load` 递归走值，要求任何含硬编码用户路径的值，
   其结构路径**恰为** `services → neo4j → volumes → <序号>`，且每条至多出现一次。
   负控（第 5 项）7 个输入：你 round-1 与 round-2 给的三个漏过输入（复制到另一 service /
   `other: # comment` / `"other":` / 挪进 `neo4j.command`）**全部由 PASS 变 FAIL**。
2. **LOW（占位符）**：先钉死期望参数集 `{userId, limit, group_id, group_prefix}`（不随实现缩小），
   再在**去掉 `//` 行注释**的查询文本里查 `$name`。负控（第 6 项）用**运行期**替换生产方法为
   两个变异体（纯内存、`finally` 无条件还原、末尾断言已还原），你给的两个输入均由 PASS 变 FAIL。
3. **MEDIUM（SHA 绑定）**：全部裁判在 `0909e935` 的代码树上重跑，证据首行写 `HEAD=`；
   并给出 `git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空的**代码树等价证明**。
4. **三处只收窄声明未改代码**：`mock_calls` 只证明调用发起顺序 / 替身只能发现「调用点传入
   替身不接受的参数」/ 依据 sha 计法改为只数依据栏（25 个）。

## 三 请回答的问题（按重要性排序）

1. **compose 两轴判据还有没有漏过面**？例如：YAML 锚点与别名（`&x` / `*x`）、
   合并键 `<<:`、多文档（`---`）、`services` 被写成流式映射、值用引号/块标量表达同一路径、
   或结构路径正确但**数量**判据被绕开的写法。
2. **轴一与轴二会不会互相抵消**——有没有某个输入两轴都放行、但确实引入了新的硬编码路径？
3. **占位符判据**：钉死期望参数集之后，若生产**新增**一个绑定参数，本条会红——这是想要的吗？
   还有没有「值被内联但两条断言都过」的写法？
4. 两份负控本身是否可信：有没有「变异没生效却报了 FAIL」或「还原没做干净」的可能？
5. **§六 / §七 的收窄声明是否收得够**——还有没有别的地方我把话说得比证据宽？
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

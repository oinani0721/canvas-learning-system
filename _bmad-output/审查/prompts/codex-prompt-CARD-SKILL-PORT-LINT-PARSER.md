# 独立复核请求 — CARD-SKILL-PORT-LINT-PARSER（lint 解析器从巨测文件抽成可导入模块）

## 一 背景与最小读取面

本卡在 git worktree `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
（分支 `card/t7-skills`）。被审的是一次**纯搬迁重构**：把 6294→6323 行巨测文件
`backend/tests/skills/test_skill_portability_lint.py` 里的 lint 解析器/判据区
（12 个 `check_*` + 正则与解析 helper + 全部基线常量）抽成可导入模块
`backend/tests/skills/skill_portability_lint.py`，test 文件改为 import。
声称**行为零漂移**。

**最小读取面（请只读这些，不要扩散到全仓）**：

1. `git diff 17c14d2705e519d44cb7c4988c81a920b175d03f 1eab9358df306838c897163142647b1ea5424e27 -- . ':(exclude)_bmad-output'` —— 本卡全部代码改动
   （审 SHA = `1eab9358df306838c897163142647b1ea5424e27`；基线 `17c14d2705e519d44cb7c4988c81a920b175d03f` = 同车道前卡 T7-B 末 commit）。
2. 新模块 `backend/tests/skills/skill_portability_lint.py` 全文（含文件头 docstring 的交接登记）。
3. `backend/tests/skills/test_skill_portability_lint.py` 的 import 段（文件头到 import 块结束）。
4. `_bmad-output/审查/evidence-skill-port-lint-parser/` 下的存档：
   - `skills-before-*.txt` / `skills-after-*.txt` / `skills-after-final-*.txt` —— tests/skills 三跑
   - `passed-compare-*.txt` —— before/after 逐行对照
   - `ast-equivalence-*.txt` —— AST 逐节点等价证明
   - `module-verifier-*.txt` —— 模块依赖验伪锚（变异→红→还原→绿）
   - `negative-controls-*.txt` / `import-independence-*.txt` / `ruff-*.txt` / `scope-*.txt`
   - `skills-before-after-compare-20260916T232902.txt` —— **一轮作废判据的自陈**（见问题⑥）

## 二 作者自述，请独立核对

① **纯搬迁、行为零漂移**：12 个 `check_*`、正则/解析 helper、全部基线常量（`BASELINE`、
   `SCRIPTS_BASELINE`、`U6_SCRIPTS_BASELINE`、`TMP_BLOCK_BASELINE`、`MANAGED_FILE_DIGESTS`
   等）**值逐字节未变**。AST 判据：HEAD 版顶层符号 237 = 新 test 85 + 新模块 152，
   零丢失零新增、两侧重名 0，每个同名节点 `ast.dump()` 逐字符相同，77 个 test 函数一个不少。
   tests/skills 改前 555 passed / 改后 555 passed，两存档 `diff` 唯一差异是耗时行。
② **in-file 旧副本删尽**：`grep -cE '^def check_'` 在 test 文件 = 0、模块 = 12。
   test 文件改为**显式 import 51 个名字**（非 `import *`）。
③ **模块不依赖 pytest、可独立导入**：模块内 `^import pytest` = 0；`python -c` 导入模块后
   `'pytest' in sys.modules` 为 `False`；12 个 `check_*` 全部可从模块导入。
   `REPO_ROOT = Path(__file__).resolve().parents[3]` 在模块与 test **同目录**下解析到同一路径
   （已实测打印两侧值相同）。
④ **SKILL.md 未改**：`canvas-vault/.claude/skills/start-exam-board/SKILL.md` 的
   diff 为空、sha256 仍 `0f2c085a1bae12446dd74ab89cc1e6aa5c8bc34901dd3be7ac5d8521310d0dce`，
   `/tmp/` 出现 6 次、`/tmp/cls-exam/` 出现 4 次 ⇒ 裸 `/tmp/` 仍为 2。
⑤ **`:430/:435` 的 4 处 regression 钉点已登记、本卡未改 regression**：登记写在模块头
   docstring，含「`test_g3_3_cas.py` 侧的 `_SEB_BLOCKS` 与其 `assert len(...)==1` 在**模块级**
   ⇒ 改字面量是 collect-time ERROR、整文件不可收集」与「`test_learning_events_schema_contract.py`
   侧的 `matches` 在 `test_real_producer_start_exam_board_writer` **函数体内** ⇒ 是该条单测
   运行期断言红」这一**区分**。两文件本卡无写权，真解耦跨地盘、交主 session 裁。

## 三 请按重要性排序回答的问题

① **抽出是否真零漂移**：有没有某条正则/helper 在搬家时因**模块级求值顺序**、`__file__` 基准、
   `functools.lru_cache` 的缓存归属、或 import 副作用而语义改变？特别核 `REPO_ROOT` 的
   `parents[3]` 在新文件位置是否仍指同一 repo 根；以及模块内先后依赖的常量/正则求值顺序
   是否与原文件一致（原文件里解析器区是**两段不连续**的行区间 `:175-3299` 与 `:4363-4488`，
   搬到模块后被拼成**连续**的，中间原本隔着 test 函数——这一拼接是否改变了任何模块级求值顺序）。
② **test 是否真的依赖模块而非旧副本**：模块依赖验伪锚是否成立——变异方向是「让判据返回
   **非空** problems」（两条正控的断言都是 `assert not problems`，恒返 `[]` 是假绿），
   红是否落在 `正文指标基线漂移` / `受管文件基线漂移` 两条**断言身份**上而非 import/夹具错，
   还原后 sha 是否逐字节相同。若你认为这个锚点覆盖不足（只变异了 12 条里的 2 条），
   请说明剩余 10 条由「555 全绿 + in-file `^def check_` = 0 + 两侧重名 0」间接覆盖是否够。
③ **显式 import 名单是否漏名**：test 只导入了模块 152 个顶层绑定里的 51 个。作者主张漏名会被
   ruff 的 `F821 undefined-name` 抓出（该规则在 backend 面**已启用**，已打印 enabled 列表；
   `F401` 未启用故不能作锚），并做了 stdin 注入验伪锚证明这条判据对该文件会变红。
   这个论证链是否成立？有没有 F821 抓不到的漏名形态（例如只在字符串/`getattr`/延迟求值中引用的名字）？
④ **负控在抽出后是否仍能对坏输入变红**：25 条 `test_negative_control_*`（参数化展开 46）全绿，
   主锚 `test_negative_control_new_bare_tmp_reddens_layer2` 喂入「exam-quick 副本加一行裸
   `/tmp/x.json`」后 `check_body` 仍报红。搬家有没有让任何一条负控变成「门未覆盖的路径」
   （例如负控实际调的是 test 侧残留的什么东西、或断言被弱化）？
⑤ **模块的复用面限制**：`DEFAULT_ROOT` 写死 `canvas-vault/.claude`，其他静态面复用时是否受限？
   （登记项，不在本卡改，请只指出不提改法。）
⑥ **作者自曝的三处判据缺陷，请核对更正是否彻底**：
   (a) `( cmd | tail -N ); echo rc=$pipestatus[1]` 读到的是 `tail` 的 rc —— 曾让「缺失符号必
       rc≠0」的验伪锚假绿读成 0；已改为管道内不插过滤器后重跑（rc=1）。
   (b) ruff 验伪锚最初把探针文件放在项目外的临时目录且不带 `--select`，rc=0（未套用 backend
       配置）；已改为对**真实地盘文件**用**正跑那条命令**做 stdin 注入。
   (c) before/after 对照判据用 glob `skills-before-*.txt`，把 `tee` 正在写的
       `skills-before-after-compare-*.txt` 也匹配进来（diff 收 3 参数 rc=2、grep 加文件名前缀
       导致取数为空）；已改为显式文件名重跑，该轮存档被覆写为作废自陈。
   请判断这三处的更正是否**彻底**（有没有同型缺陷残留在别的判据里），以及作者据此得出的结论是否可采信。

## 四 输出格式

BLOCKER / HIGH / MEDIUM / LOW 分级 + `file:line` + 每条一句**触发路径说明**
（哪种输入会走到这条路径、会看到什么现象）。

## 五 边界

只读；不连任何数据库；不跑 `tests/regression` 目录级（pact/真服务会挂）；
不评 `SKILL.md :430/:435` 的真解耦方案设计（跨地盘，交主 session）；
不评第十三批已定版的 12 个判据**语义本身**（本卡只搬家，不重评语义）。

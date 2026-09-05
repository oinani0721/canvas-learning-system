# 复核任务：CARD-TOOL-typecheck-glob（lefthook `python-typecheck` glob 收窄）

你是独立复核者。审查对象是一个**已提交**的 git commit，只改了一个 YAML 配置文件里的一行
glob 与其上方的注释。请只做**只读审查**：读文件、比对数字、判断措辞是否与证据相符。
不需要运行任何命令，也不要提出任何改动建议之外的操作。

## 树与绑定

- 工作树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z7-tool`
- 审查绑定：`4cc4824c..64498c26`（`64498c26` 是本卡唯一的代码提交）

## 读取面（只读这些，不要读其它文件）

1. 本卡改动本身：
   `git -C <树根> diff 4cc4824c 64498c26 -- lefthook.yml`
2. 同一文件里已有的 glob 引擎实测矩阵（历史卡留下的注释）：
   `sed -n '40,48p' <树根>/lefthook.yml`
3. 改后的目标块（注释 + glob + run 脚本）：
   `sed -n '132,215p' <树根>/lefthook.yml`
4. 五份探针记录 + 一份新旧对照记录，目录：
   `<树根>/_bmad-output/审查/evidence-typecheck-glob/`
   - `probe-HIT-backend_app_main.py.txt`
   - `probe-HIT-backend_app_mcp_server.py.txt`
   - `probe-HIT-backend_app_api_v1_endpoints_health.py.txt`
   - `probe-NEG-backend_mutmut_config.py.txt`
   - `probe-NEG-backend_tests_conftest.py.txt`
   - `probe-OLDGLOB-flip.txt`（含一段作者自查勘误）
   - `judge1-counts-*.txt`（`git ls-files` 计数原始输出）
5. 未被本卡改动、但被注释引用的配置：`<树根>/pyrightconfig.json`

## 背景（供你判断措辞是否越界，不必复述）

- 该 hook 的 run 脚本把暂存文件列表作为**位置实参**传给 pyright；位置实参会取代
  `pyrightconfig.json` 的 `include` 列表，而不是与它取交集。
- 因此改动前该 hook 的实际作用面是 `backend/` 下全部 `.py`（包含测试目录），
  远大于配置里声明的面；测试目录的存量类型错误使该 hook 长期对无关提交报错。
- 本卡的处置是把 glob 收窄到 `backend/app/*.py`，并在注释里写清口径与实数。
- 本卡**不**安装 pyright、**不**修改 `pyrightconfig.json`。

## 请按重要性回答下列四问，每问都要给出你依据的具体行/文件

1. **glob 语义是否被探针证实。** 单个 `*` 在本机 lefthook 2.1.6 下是否确实跨任意目录
   层级？三份 `probe-HIT-*` 是否分别覆盖了根级、1 级、3 级三种深度，并且都出现了
   pyright 真正开始运行的字面输出？两份 `probe-NEG-*` 是否确实显示该命令被跳过？
   `probe-OLDGLOB-flip.txt` 是否构成一个有效的新旧对照（同一个文件在旧 glob 下进入了
   检查、在新 glob 下未进入）？其中作者自己标注的勘误是否正确、是否已把错误结论纠正？

2. **注释里的实数是否与证据一致。** 注释中的 263 / 0 / 41 / 304 / 846 / 493 各自是否
   与 `judge1-counts-*.txt` 的原始输出对应？注释里对 592 这个数字的归属说明
   （称它属于整个 include 面而非某个子目录）与 `pyrightconfig.json` 中的原始记载是否一致？
   有没有任何数字缺乏出处，或把某个数字用在了它不成立的范围上？

3. **措辞是否越界。** 注释与提交说明里有没有任何地方在暗示"类型已经检查过了/已通过"？
   注释是否如实说明了：主仓的虚拟环境中没有 pyright，因此在主仓上这个 hook 仍然走
   跳过分支、收窄 glob 不会让它开始运行；而只有软链到含 pyright 的共享虚拟环境的
   工作树才会真正运行？两种情形是否被分开陈述而不是合并成一句？

4. **改动面是否被限制住。** 该 commit 是否只改了 `lefthook.yml`？命令名的集合与它们在
   文件中的出现顺序是否与改动前完全一致？有没有新增 `priority` 键？
   `pyrightconfig.json` 是否确实一字未改？被注释登记为"有意不收"的两条
   （`src/` 与 `backend/` 一级的两个 `.py`）陈述是否属实？

## 输出格式

对每一问给出：**结论**（成立 / 不成立 / 部分成立）+ **依据**（文件与行号或原文片段）+
若不成立，指出具体是哪一句与哪一条证据冲突。最后给一段总评，指出你认为最需要修正的
一处（若有）。

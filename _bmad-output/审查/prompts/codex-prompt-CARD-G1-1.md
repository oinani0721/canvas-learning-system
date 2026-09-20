# CARD-G1-1 独立复核请求（BATCH-2026-09-18-第十五批 · 车道 card/p8-backend · round-1）

## ① 背景与最小读取面（只读这些，不要漫游仓库）

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend`
分支 `card/p8-backend`，审查绑定 SHA = `4a6524aa12f4c247245afda099bfa19d60dc510c`，
本卡代码面 = `git --no-pager diff --stat --no-color 86dc726c9eda76b11792e6793d401bf2dea04294 4a6524aa12f4c247245afda099bfa19d60dc510c -- . ':(exclude)_bmad-output'`
= 恰两个新文件、零修改既有文件。

请读取（全部相对上面的树根）：

1. `scripts/annotation_search.py` —— 新增的只读批注检索脚本，全文。
2. `backend/tests/unit/test_annotation_search.py` —— 其单测，全文（33 用例 / 0 skip）。
3. `_bmad-output/审查/evidence-g11/protocol-s5-annotation-search.patch` —— 协议条款 patch，全文。
4. `_bmad-output/审查/phase0a-annotation-truth/A01-source-boundary-draft.json` 第 42-108 行 —— 八条 source_roots 声明。
5. `_bmad-output/审查/phase0a-annotation-truth/2026-08-20-Phase0A-A01-A02-批注真相层实施契约.md`
   第 126-144 行（§4 Parser 契约：三层召回 / 至少覆盖清单 / 解析不变量）与第 82 行（repo-wide 容器面）。
6. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md`
   第 91-97 行 —— 协议 §5 排批章，patch 的落点。
7. `_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md` 第 232-236 行
   —— G1-1 的原始判据方向。
8. `_bmad-output/审查/evidence-g11/` 下这几份裁判存档（**只看文件名带 close / final 的那几份**，
   它们绑最终 HEAD；同名的更早时间戳是中间态快照，各自在首部自证了当时的 sha）：
   `close-judges-*.txt`（零写 AST 门 / 只读 hash / ruff / 地盘门 一次跑齐）、
   `negctl-1-*.txt` ~ `negctl-4-*.txt`（四段负控，每段带跑前跑后 sha 与变异 diff）、
   `gate-mutation-survey-*.txt`（门的变异存活面：七个变异体原本存活）、
   `gate-mutation-kill-*.txt`（补门后逐个复放，七杀七；其中 G 走了三跑，过程如实记录）、
   `annotation-search-final-*.txt`（真数据小抄）、`clause-dogfood-*.txt`（协议新条款按字面自跑两条路径）、
   `private-root-adversarial-*.txt`（私人面对抗输入六段含正控）、
   `patch-apply-check-final-*.txt`、`unit-close-*.txt`（tests/unit 目录级）、
   `internal-review-*.txt`（本车道自跑的内部对抗复核落盘——⚠️ 它在被审文件改动期间进行，
   **不作为验收依据**，只供你复查我当时看到了什么）。

### 本卡自己已经找到并修掉的缺陷（请独立复核这些修法本身是否站得住，以及有没有修出新问题）

送审前本车道自跑了一轮内部对抗复核 + 门的变异测试，抓到并修掉了下面这些。它们都**已在**
你要读的代码里，列在这里是为了让你把力气花在别处，也为了让你能挑战这些修法：

1. `os.path.realpath` 不归一大小写，而本机 macOS APFS 大小写不敏感 ⇒ `Canvas-Vault/` 下的
   私人批注曾被原样返回。修法 = `fold_path()`（NFC + casefold）统一比较口径。
2. `excluded_private_roots` 曾把 A01 算出的 6 个私人 root 全列上，读起来像 6 个都拦住了，
   而仓内只有 2 个有落地路径。修法 = 只报真有路径可拦的，其余另起一行如实说明。
3. `privacy_ceiling` 曾是精确字面量匹配 ⇒ 大小写 / 空白 / 未知更高级别静默当成非私人。
   修法 = strip+casefold 归一，且**认不出的级别按私人处理**。
4. git 子进程曾原样继承调用方环境（`GIT_DIR` 会让它回答另一个仓库，`GIT_TRACE*` 会让它
   自己往文件里写，零写 AST 门看不见子进程）。修法 = `git_env()` 剃掉全部 `GIT_*`。
5. `os.walk` 无 `onerror` ⇒ 列不动的目录整棵静默消失。修法 = `unwalkable` 桶 + 汇总行报数。
6. 引用块里的「空行」是一个光秃秃的 `>`，`str.strip()` 判不出来 ⇒ `> **User：**` 的块会
   一路吃到 `> **Claude（日期）：**`。修法 = `stops_block()`。
7. frontmatter 扫描无下界 + `DATE_RE` 无边界无有效性 ⇒ 会报出 `1234-56-78` 这种假日期，
   还把真实的 git 档挡掉。修法 = 要求 frontmatter 闭合 + `datetime.date()` 校验日历有效性。
8. 门的变异测试报出七个变异体存活（`gate-mutation-survey-*.txt`），已逐条补门并复放验证
   （`gate-mutation-kill-*.txt`）。其中确定性那条：同进程内比两次证明不了跨进程确定性，
   已改为起两个子进程 + 不同 `PYTHONHASHSEED`。

这个脚本要解决的问题：294 条 `**User：` 与 348 条 `[!question]+` 形态的用户批注散在两千多个 Markdown
文件里，此前没有任何检索工具，开卡时靠人翻文件。脚本按关键词 / Story ID 把批注连同 `file:line`、
来源类别、日期（带 `date_source`）一起列出来。

## ② 作者自述——请独立核对，不要采信

1. **零写**：除 stdout / stderr 外零写调用。唯一子进程是 `subprocess.run(["git","log","-1","--format=%cs","--",path], ...)`。
   自证方式是一道 AST 门（数 `open(mode含 w/a/x/+)`、`os.remove/unlink/rename/replace/makedirs/mkdir/rmdir`、
   `shutil.*`、`Path.write_*` 等，以及 argv[0:2] 不是 `["git","log"]` 的 subprocess 调用），
   被测文件计数 0、探针文件计数 2。
2. **不 import 目标目录内任何模块**；stdlib-only（argparse / json / os / re / subprocess / sys / unicodedata / pathlib）。
3. **私人 root 名单不写死**：从 A01 的 `privacy_ceiling ∈ {P3-high-sensitive, P4-secret}` 与
   `proposed_action` 含 `private-locator` 算出（本 A01 实测 6 条）；root_id → 路径的映射由脚本自带
   （A01 无 path 字段），判定用 `os.path.realpath` 后前缀比较，另有 `canvas-vault` 组件名与 PRD basename 两条安全网。
4. **A01 缺失 / 顶层无 source_roots / 某条缺 privacy_ceiling ⇒ 退出码 2**（fail-closed），不降级。
5. **真数据锚必命中**：`--keyword codex` 命中 `_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:494`；
   `--keyword anki` 命中 `_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md:163`。
6. **目标目录前后逐字同**：对 `_bmad-output` 逐文件 sha256 再总 sha（排除本卡落档目录 `审查/evidence-g11/` 与
   `__pycache__`），跑前跑后相同；同口径对一个两文件小目录改一字节会变，证明该摘要对内容敏感。
7. **协议本体零改动**：条款只以 patch 形式交付，`git -C <主干树> apply --check` rc=0，且主干树协议文件
   sha256 在 `--check` 前后均为 `accbe747c0a963823cb28b3ce7578fb232be396201e4f15115b765b77c22baf1`。

## ③ 请优先回答的问题（按重要性排序）

0. **只读是不是真只读**：AST 门只看语法形态，请找**门未覆盖的路径**——有没有执行路径会落盘、改 mtime、
   留缓存？`git log` 子进程会不会在带自定义 filter / hook 的仓库里产生副作用，或因 cwd 取自被扫文件所在
   目录而在某些输入下出问题？`--root` 指向软链、`..` 路径、hardlink、大小写不敏感文件系统上的
   `Canvas-Vault`、NFD 形态目录名——realpath 之外还有没有**未被拦下的输入**能落进私人 root？
   反方向也要看：把「每个扫描根的各级祖先」当基点来推导私人路径，会不会把**不该私有**的目录误判为私有？
1. **空槽与不可读文件是否被静默当 0**（契约 `:142` 明确要求 NUL / 非法编码不能静默当 0）。
2. **关键词只匹配 marker 行还是整块**：多行续写的批注，正文含关键词而首行不含时会不会漏？
   反过来，块提取会不会越界把不属于该批注的后续内容也算进命中面？
3. **`date_source` 会不会把 git 提交日期冒充成批注写下的时刻而不标明**；frontmatter 解析（不引 PyYAML）
   在 `---` 出现在正文、key 重复、值带引号时的行为。
4. **输出排序在中文路径 / NFC-NFD 差异下是否仍确定**；同参数两次运行是否逐字同。
5. **测试是否真读真 `_bmad-output`（DD-03 禁 mock）**，以及真数据用例断言行号（:494 / :163）在主干文件
   变动后的脆弱性——这是设计选择还是隐患，若行号漂移应如何登记？另请点名：有没有哪条测试在被测代码
   删掉整段逻辑后仍然全绿（即那道门其实锁不住它声称锁住的东西）。
6. **patch 是否只加一条、只加在 §5、§1-§4 一字未改**；新条款措辞是否与协议既有条款冲突或无法执行。

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- `file:line`
- 一句能让人自己验证的思路：具体的**负控输入**或**对照输入** → 观察到的错误输出。
- 若属于「**门未覆盖的路径**」或「**未被拦下的输入**」，请明确说是哪道门、哪类输入。

宁可少报也不要报推测：不确定的降级为 LOW 或不报，并说明不确定在哪里。

## ⑤ 边界

- 只读复核，不要修改任何文件，不要连任何数据库（本卡不连库）。
- 不评契约 `:132` 的 T3 broad discovery（`user`/`USer` 异常大小写、role 字段、转述、无冒号编号）——
  该层须人工分类，明确不在本卡范围。
- 不评契约 `:82` 的非 Markdown 容器（Canvas JSON / JSONL / YAML / 对话导出）——明确不在本卡范围。
- 不评修正链去重 / atomization、A02 ledger、G1-2 开卡小抄工作流、G1-3 能力证据台账——都是另卡。
- 不要求对 live vault 或锚定 PRD 实跑 `--include-private`；那两处本卡默认连读都排除。

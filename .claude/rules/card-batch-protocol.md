# 卡批次协议（排批 / 车道 / 复核 / 合并）

> **来源**：第八～十批实战沉淀（`_bmad-output/审查/2026-09-04-第八九批合并僵局诊断与开发清单.md` v2、`2026-09-05-第十批复核裁定与待裁决登记.md`）。台账 `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md` §三 是本文的执行侧。
> **执行级别**：主 session 排批与复核时逐条对照；车道 goal/卡文引用本文而不是重抄。

## 1. 合并门（唯一口径）

- **阻断级 = 0 即可合**：数据丢失 / live vault 或 Neo4j 7691 写入 / 安全 / 指定裁判红 / 负控假绿（窄口径：负控本身谎报 PASS）。其余 BLOCKER/HIGH/MEDIUM/LOW **登记不阻断**。
- Codex 的 PASS/FAIL 字样**不进门**，但台账 §二 必须如实抄录（含模型名）。
- 终审绑定看**代码树**：`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空即仍绑定；纯注释尾巴由主 session 逐行核后可判等价（写明）。⚠️ 写法必须是 `':(exclude)…'`——`':!…'` 在 zsh 下被吃掉、在本机 git 2.50 下报 `Unimplemented pathspec magic`，rc=128 且 stdout 空，「为空即绑定」会把没跑成读成绿（第十一批复核实测）。
- **串行车道的绑定口径**：一条车道串多张卡时，前面的卡在后面的卡改代码后必然「失绑」——按**本卡 diff 面**判：`git diff --stat <审SHA> <本卡末commit> -- <本卡改过的代码文件>` 为空即仍绑定；跨卡后续 commit 不算破坏。但**同一卡内**审后再改（如「按 Codex 意见整改」那次 commit）就是真失绑，须登记「整改未复审」。
- 轮次按**卡族**累计 ≤3；改卡号不重置。0 字节存档重发一次，再 0 字节 → 主 session 人审替代，不等配额。
- 主 session **人判合入**（终审「FAIL」但阻断级 0）必写：依据逐条对门、revert 点（单 squash SHA）、下批必排的修复卡。

## 2. Codex 复核命令（2026-09-05 起）

```bash
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-<CARD>.md)" \
  > <树>/_bmad-output/审查/codex-review-<CARD>.md 2> <树>/_bmad-output/审查/codex-review-<CARD>.stderr </dev/null
```

- 模型固定 `gpt-6-astra` + `ultra`（用户 2026-09-05 裁定）；新卡文/手册 `grep -c 'gpt-5.6'` 必须为 0。
- prompt 里禁止出现「构造 / 可复现片段 / 打穿 / 绕过」类请求（cyber 拦截在任务边界，不在措辞）。
- `*.stderr*` **永不入库**（`.gitignore` 已覆盖）；squash 时以 `ls-tree` 实数剔除。

### 2.1 存档首部模板（2026-09-05 起硬规则；第十二批 RV-F 落地）

每份 `_bmad-output/审查/codex-review-<CARD>[-rN][-pM].md` **首部**必须是下面的 blockquote（车道直接复制改字段），随后一行 `---`，再接 Codex 正文：

```
> 批次: BATCH-<日期>-第N批 · 车道 <Yx> · 卡 <CARD-ID> round-<N>[ prompt-<M>]
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `<codex --version 实测值，如 codex-cli 0.153.3>`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt 路径>)"`
> 审查绑定: `<审SHA 或 A..B>`（HEAD 若不同须如实写「不绑合并态 / 审工作区」）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `<line1>` / `<line2>` / `<line3>`
```

- **牙齿**：首部缺 `模型` / `reasoning_effort` / `codex` 任一字段，该轮**不计入**卡族轮次配额（等于没审），主 session 复核时按此判。
- 第十一批 9 份存档由主 session 于 2026-09-05 补首部（只加 blockquote + `---`，正文一字不改）；能从 `.stderr` 自证的字段填实测值，不能自证的写「未自证」，不追认。

### 2.2 裁判输出落盘（长跑卡 / 变异卡 / 复审卡）

- 所有承重裁判的 stdout+stderr 一律 `2>&1 | tee _bmad-output/审查/evidence-<卡短名>/<name>-$(date +%Y%m%dT%H%M%S).txt`，**末行写 `rc=$?`**。⚠️ 后缀用 `.txt` 不用 `.log`：仓根 `.gitignore` 有全局 `*.log`，`.log` 存档会被静默忽略、commit 里没有（第十二批排批实测 `git check-ignore`）（`tee` 会吞退出码：用 `set -o pipefail` 或 `${PIPESTATUS[0]}` / zsh `$pipestatus[1]` 取被测命令的 rc）。
- 验收单只**引用**路径与末行，不自述数字（Z6-B 教训：run-r2/r3 存档逐字节相同、无时间戳无 rc，不可区分轮次）。
- 变异 / 换文件类裁判须同时落**跑前 / 跑后**全文件 `shasum -a 256`（不是 grep 变异标记字面量——变异体文本可不含该字样；且本文件不在 `mutant-residue-scan` 允许名单，写字面量会被门拦）。

### 2.3 批级环境变更通告

- 任何改**共享运行环境**的动作（往 `card-v5-lance/backend/.venv` 装工具 / 升 codex / 升 lefthook / 改全局 hook）= 批级事件：动手前在手册 §零 追加一行「<时刻> <动作> <影响面>」并通知全部在跑车道；事后写进复核报告 §五。
- 反例：第十一批 Z7-B 07:42 往共享 venv 装 pyright，5 张卡随即用 `LEFTHOOK_EXCLUDE=python-typecheck` 绕过提交且无存档。凡用 `LEFTHOOK_EXCLUDE` 提交，验收单必须贴被跳过 hook 的原始输出与「报错不在本卡改动行」的证明；改 `backend/app/**` 的卡不得绕过 `python-typecheck`。

## 3. 车道裁判的最低覆盖

- 卡自己点名的裁判（显式文件）之外，**改了什么面就必须跑那个面的目录级套件**：改 `canvas-vault/.claude/skills/**` 脚本 → `tests/skills` 目录级；改 `backend/app/**` → 对应 `tests/api` / `tests/unit` 子集；改 `tests/support` / conftest → 全部门下目录级。
  - 教训：第十批 X6 改 `recap_scan.py` 加了模块级 dataclass，生产加载点 `recap_exam_build.py` 崩，`tests/skills` 117 红，卡裁判与两轮 Codex 都没跑到（`5322043f` 集成修复）。
- 动态加载（`importlib.util.spec_from_file_location` + `exec_module`）的目标含 `@dataclass` → **必须先 `sys.modules[name] = mod`**（Python 3.14 dataclass 自省取 `sys.modules[cls.__module__].__dict__`）。修坑时 grep 全部加载站点，不只修自己的测试。
- 无 W4 门的树上**禁目录级 pytest**（`test_vault_scope_409.py` 等 25 个 real-app 文件在收集/执行期起 lifespan 连 7691）；主干已含门（第十批起）可跑，但 `tests/integration` / `tests/e2e` 走 advisory 仍会真连。
- **改 `canvas-vault/.claude/scripts/{fsrs_bridge,decay_beta}.py` 的卡 = 合入当天必须部署 live**：`daily-review-wrapper.sh` 对这两份文件做开发树↔live 逐字节 `cmp`，不一致 → exit 78，整条复习链停摆（2026-09-05 09:05/10:05 已发生）。部署由主 session 在用户**当次显式授权**后执行：先备份 live 旧副本到 `canvas-vault/backups/` 记 sha → cp → `cmp` → 等下一个 :05 档核 `launchctl list` 归 0 → 证据落 `_bmad-output/审查/evidence-deploy/`。只部署 wrapper 门覆盖的文件，**不顺手部署 SKILL.md**。squash 与部署须在同一 session 内连做（中间每一档都在停摆）。
- 新车道 `backend/.venv` 缺席时建目录级 symlink 指向 `card-v5-lance/backend/.venv`（`.gitignore` 覆盖），否则 lefthook `python-lint` rc=127 阻断 commit。

## 4. 合并程序（主 session）

1. 集成候选树从主干 HEAD 切（scratch worktree），按手册队列 **逐卡 squash**（单卡多 commit 用 `cherry-pick --no-commit <range>`；整枝用 `merge --squash`），每步剔 `*.stderr*` + 断言干净。**禁止用「主干→车道全树 diff 套用」实现 squash**（会删掉车道没有的主干新文件、回滚台账）。
2. 树等价：每车道改过的每个代码文件在候选树上与车道 tip 逐字节相同；跨车道代码文件交集须为空或已声明。
3. 候选树补 gitignored `backend/.env` 后**重跑全部卡裁判 + 门下目录级**；红分三类：主干既有（在主干 HEAD 复现）/ 门抓到的既有偷连 / 本批引入（阻断）。
4. 集成期修复走**独立 commit**（不揉进卡的 squash），台账 §二 写「+ 集成修复 `<sha>`」，§一.b 写根因与卡方声明不实之处。
5. 主干 `--ff-only` 到候选尾；原分支 tag `merged-squash/<branch>`（部分抽取 `-<卡号>-only`）；台账 §一/§一.b/§二 更新；推送 origin 与 backup（**tag 逐个推**，zsh 不分词）。
6. guard hook 对 force-push 的正则会跨整条命令匹配 ` -f `：含推送的那条命令里不得再写 `[ -f x ]` 之类，改用 `test -e`。

## 5. 排批（主 session）

- `/goal` 正文硬限 4000 字符 → 短 goal（≤3800，长度门脚本必跑）+ 卡文（无限制，车道必读）分层。
- 卡文事实必须在**当前主干**实测；主干前进后复用旧卡文前重验（第十批 X8：7 条事实在新主干上失效）。
- 台账是全部卡的共同写入面 → **只有主 session 改**；卡在验收单写「台账待登记条目」。
- **tests/unit 既有红基线**：主 session 每批开跑前落一份 nodeid 口径的基线（`_bmad-output/审查/evidence-b<N>/unit-red-baseline-<主干SHA>.txt`），车道开工/收工各跑一次目录级并 `diff`，差集才算本卡引入或修复；「298/289」这类含日志噪音的行数不得作分母。
- 每张卡的完成条件含「本卡未证明什么」必填；数字与命令输出一致（`wc -m` 计字符非字节）。

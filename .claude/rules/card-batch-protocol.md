# 卡批次协议（排批 / 车道 / 复核 / 合并）

> **来源**：第八～十批实战沉淀（`_bmad-output/审查/2026-09-04-第八九批合并僵局诊断与开发清单.md` v2、`2026-09-05-第十批复核裁定与待裁决登记.md`）。台账 `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md` §三 是本文的执行侧。
> **执行级别**：主 session 排批与复核时逐条对照；车道 goal/卡文引用本文而不是重抄。

## 1. 合并门（唯一口径）

- **阻断级 = 0 即可合**：数据丢失 / live vault 或 Neo4j 7691 写入 / 安全 / 指定裁判红 / 负控假绿（窄口径：负控本身谎报 PASS）。其余 BLOCKER/HIGH/MEDIUM/LOW **登记不阻断**。
- Codex 的 PASS/FAIL 字样**不进门**，但台账 §二 必须如实抄录（含模型名）。
- 终审绑定看**代码树**：`git diff --stat <审SHA> HEAD -- . ':!_bmad-output'` 为空即仍绑定；纯注释尾巴由主 session 逐行核后可判等价（写明）。
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

## 3. 车道裁判的最低覆盖

- 卡自己点名的裁判（显式文件）之外，**改了什么面就必须跑那个面的目录级套件**：改 `canvas-vault/.claude/skills/**` 脚本 → `tests/skills` 目录级；改 `backend/app/**` → 对应 `tests/api` / `tests/unit` 子集；改 `tests/support` / conftest → 全部门下目录级。
  - 教训：第十批 X6 改 `recap_scan.py` 加了模块级 dataclass，生产加载点 `recap_exam_build.py` 崩，`tests/skills` 117 红，卡裁判与两轮 Codex 都没跑到（`5322043f` 集成修复）。
- 动态加载（`importlib.util.spec_from_file_location` + `exec_module`）的目标含 `@dataclass` → **必须先 `sys.modules[name] = mod`**（Python 3.14 dataclass 自省取 `sys.modules[cls.__module__].__dict__`）。修坑时 grep 全部加载站点，不只修自己的测试。
- 无 W4 门的树上**禁目录级 pytest**（`test_vault_scope_409.py` 等 25 个 real-app 文件在收集/执行期起 lifespan 连 7691）；主干已含门（第十批起）可跑，但 `tests/integration` / `tests/e2e` 走 advisory 仍会真连。
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
- 每张卡的完成条件含「本卡未证明什么」必填；数字与命令输出一致（`wc -m` 计字符非字节）。

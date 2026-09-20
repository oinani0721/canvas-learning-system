# CARD-R-RC 独立复核请求（round-3）

## ① 背景与最小读取面（写死，请只读这些）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs`
**审查绑定：`ef8ace4a73b346790672a61e5308458fbfbcec4f..5abcff162de43153d71c2dde84a0226a040918e2`**（后者 = 当前 HEAD 的代码提交）

本卡给 `docs/release-evidence/` 补**生成端**：一个 clean RC 冻结脚本 + 它的裁判 + README 两段。
r1（1H/4M/1L）与 r2（1H/7M/5L）的结论已全部处置，另有一轮内部 8 维对抗复核（119 agent）。
**请独立复核整改后的状态，不要把前两轮的结论当既定事实。**

**最小读取面**：
1. `git --no-pager diff --no-color ef8ace4a73b346790672a61e5308458fbfbcec4f 5abcff162de43153d71c2dde84a0226a040918e2 -- . ':(exclude)_bmad-output'`（恰三文件）
2. `backend/scripts/validate_release_manifest.py` 的 `:57-80` / `:800-867` / `:883-987`
3. `docs/release-evidence/manifest.schema.json` 的 `:119-149` / `:200-212`
4. `docs/release-evidence/README.md` 本卡新增两节 + 既有 `:56` / `:164`
5. 证据（`_bmad-output/审查/evidence-rrc/`，全文件名）：
   `freeze-real-5abcff16-20260919T005336.txt`、`check-real-5abcff16-20260919T005336.txt`、`freeze-dirty-real-5abcff16-20260919T005336.txt`、`freeze-dup-refused-5abcff16.txt`、`rc-manifest-5abcff16-rc-20260919-5abcff16.json`、
   `negctl-battery-c6d5e3a5-20260919T004740.txt`（16 段负控）、`negctl-supplement-5abcff16-20260919T005209.txt`（3 段补跑）、`negctl-N13-rewrite-5abcff16-20260919T005303.txt`（N13 精确重写）、`struct-5abcff16-20260919T005351.txt`、`ruff-5abcff16-20260919T005351.txt`

## ② r2 的处置（请独立核对，不要采信）

| r2 结论 | 处置 |
|---|---|
| HIGH 软链竞态：包含性检查在校验器 subprocess 之前，那几秒里 rc_dir 可被做成指向外部的软链 | 改用 `os.mkdir` 的原子语义（已存在的任何东西含软链都抛 FileExistsError）+ 建成后复核落点仍在 out-root 下 + `out_root.mkdir` 与它相邻 |
| 锁摘要与末次复核不同窗 | `_collect_locks` 拆成 `_assert_locks_present`（早拒）与 `_hash_locks`（挪到末次 HEAD/status 复核之后） |
| 判重对不可读旧件 `continue` = fail-open | 改 fail-closed：读不出来 / 顶层非对象 / candidate 非对象一律拒 |
| `.rc` 让 cwd 压过 out-root | freeze 侧禁前导点；且与包含性判据**合并成一道门**（分开写时包含性那半没有独占输入，变异掉不会让任何裁判红 = 无人看管的门） |
| check 侧非 dict candidate / 非法 UTF-8 | 都接住（`ValueError` 覆盖 `UnicodeDecodeError`） |
| `core.fileMode` 等 config 漏报 | 补 caveat（不可一般性修，如实声明） |
| 读锁 / 读 schema / 浅路径 validator 的失败落错档 | 一律归 `_Env`（rc=2 + `⛔ [env]` 标记） |
| validator 替身属 mock，违反禁 mock | **判定接受**。改成真校验器实现 + 合成证据树：缺 schema 让它自己退 2，畸形 manifest 让它自己退 1 |
| LOW：第四处「取名面小于主张」（补的 J02 的成功行满足了缺失清单断言） | 缺失清单只在「尚缺」那一行里判 |
| LOW：自陈测试只认两个词 / 缺锁只测一份 / N5 不覆盖特殊拓扑 / vault 比对不含 git 元数据 | 分别：锁住三项；参数化两份锁；新增 separate-git-dir 拓扑用例；全局 git 调用加 `--no-optional-locks` |

⚠️ **新增 main_root 重做（r2 的 LOW 促成、一覆盖就抓到真错）**：实测本机 git 2.50.1 在
`--separate-git-dir` 仓里把**git 目录**报成 worktree 路径（`worktree <…>/sepgit`），
于是「worktree-list 首条」与「common-dir 的父目录」两种推算法**都错**。现改判结构事实
`--git-dir == --git-common-dir` ⟺ 主工作树；主树直接用 `--show-toplevel`；linked 才问
worktree list 且校验其答案；都不成立记 `null` + `main_root_source: "unresolved"`。

## ③ 请按重要性排序回答的问题

- **⓪ 这一轮整改有没有引入新缺陷**，特别是新的执行顺序（锁摘要挪到复核之后、`os.mkdir` 原子建目录、
  `out_root.mkdir` 与它相邻）是否破坏了「所有拒绝路径零写入」。
- **① 三段 SURVIVED 的负控**我给出的验伪对不对：
  （a）N16 原子 mkdir 无用例覆盖——竞态不可确定性复现，是否同意如实登记而非补一道假门；
  （b）N2b 合并门只红一条（`.` 与 `..` 被下游的 exists 检查 / 原子 mkdir 接住）——这是纵深防御还是判据缺口；
  （c）判重扫描对**并发**两个进程同时扫同一 out-root 仍无排他——是否该上文件锁，还是如实登记。
- **② 39 个测试函数（40 nodeid）里还有没有「取名面小于主张」的判据。** 本卡已栽五次（文本判据被诚实声明打红 ×2、
  单名判据被同族别名越过、裸词判据被自己的说明文字满足、修复自造的缺失清单假绿）。请找第六处。
- **③ `main_root` 新口径**在哪些拓扑下仍会错？`unresolved` 分支什么时候会走到，走到时下游怎么办？
- **④ 真校验器 + 合成证据树**是否已满足禁 mock；这两条用例证明的到底是什么、不是什么。
- **⑤ README 三处新增**是否与代码一致、是否仍有夸大。
- **⑥ 「禁 mock」的机械判据**：我用 AST 证明了 0 个 mock import / 0 个 monkeypatch 参数 / 0 个 autouse
  （文本 grep 会被第 15 行那句「全文件 0 处 monkeypatch」的声明命中，是本卡第五次同型翻车）。
  这个 AST 判据的取名面是否等于它的主张？

## ④ 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给 `file:line` 与一句复现思路。
措辞请用：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**。

## ⑤ 边界

只读，不改任何文件；不连数据库或网络；不评 SLO 阈值与能力台账；不评校验器既有规则（本卡零改动）；
不评其他车道的证据内容。

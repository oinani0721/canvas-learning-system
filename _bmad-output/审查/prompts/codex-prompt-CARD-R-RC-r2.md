# CARD-R-RC 独立复核请求（round-2）

## ① 背景与最小读取面（写死，请只读这些）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs`
**审查绑定：`ef8ace4a73b346790672a61e5308458fbfbcec4f..920ae5b7b12c02691ccaed3c6897149795553e76`**
（后者 = 当前 HEAD 的代码提交；其后只有一个只含 `_bmad-output/**` 的证据提交）

本卡给 `docs/release-evidence/` 这套发布证据规范补**生成端**：一个 clean RC 冻结脚本。
校验器（`validate_release_manifest.py`，本卡零改动）把 `candidate.sha` 必须完整 40 位、
`candidate.dirty` 必须为 `false` 定成硬门，却只验格式不验来源——这两个字段一直靠人手填。

**round-1 已做过一轮**（绑定 `…5cd1cae1`，作者自己发现 prompt 里的绑定 SHA 写成了 amend 前的值，
该轮按协议不计入配额）。r1 的 1 HIGH + 4 MEDIUM + 1 LOW 已全部处置，另有一轮内部多维对抗复核
（119 个 agent，37 条原始发现经 3 视角反驳后存活 19 条）的结论也已处置。**本轮请独立复核整改后的状态，
不要把 r1 的结论当既定事实。**

**最小读取面**（其余文件请勿纳入判断）：

1. 本卡全部代码改动（恰三个文件）：
   `git --no-pager diff --no-color ef8ace4a73b346790672a61e5308458fbfbcec4f 920ae5b7b12c02691ccaed3c6897149795553e76 -- . ':(exclude)_bmad-output'`
   - 新增 `backend/scripts/freeze_release_candidate.py`
   - 新增 `backend/tests/unit/test_freeze_release_candidate.py`（32 条）
   - 追加 `docs/release-evidence/README.md`（只追加，`^-[^-]` 计数 0）
2. `backend/scripts/validate_release_manifest.py` 的 `:57-80` / `:800-867` / `:883-987`
3. `docs/release-evidence/manifest.schema.json` 的 `:119-149` / `:200-212`
4. `docs/release-evidence/README.md` 本卡新增的两节与既有 `:56` / `:164`
5. `backend/tests/unit/test_validate_release_manifest.py` 的 `:1-60` / `:1174-1180`
6. 本卡证据（`_bmad-output/审查/evidence-rrc/`，全文件名）：
   `freeze-real-920ae5b7-20260919T003240.txt`、`check-real-920ae5b7-20260919T003241.txt`、
   `freeze-dirty-real-920ae5b7-20260919T003213.txt`、`freeze-dup-refused-920ae5b7.txt`、
   `rc-manifest-920ae5b7-rc-20260919-920ae5b7.json`、
   `negctl-battery-8fe7f228-20260919T002007.txt`（12 段负控）、
   `negctl-N10-recheck-920ae5b7b12c02691ccaed3c6897149795553e76-20260919T002859.txt`、
   `struct-920ae5b7-20260919T003303.txt`、`ruff-920ae5b7-20260919T003303.txt`

## ② round-1 与内部复核的处置清单（请独立核对每条是否真的修好，而不是采信）

| 原发现 | 处置 | 请核对 |
|---|---|---|
| `--index-sha ""` 与理由同时给却通过 XOR 门，写出违反 schema `minLength:1` 的空串 | 新增 `_reject_blank_args`（对五个字符串参数拒空白）+ XOR 改判 `is not None` | 还有没有别的取值能同时满足两侧、或让 `index_sha` 写出非法值 |
| 子模块忽略配置让仓内改动对 status 隐形 | porcelain 加 `--ignore-submodules=none` | 这个 flag 够不够；还有没有别的 `git config` 能让 status 漏报 |
| `rc` 名 `.`/`..` 能 fullmatch 共享正则，`--out-root` 尚不存在时退 0 且把骨架写到 out-root **之外** | 保留共享正则（契约要求），另加包含性判据：`rc_dir.resolve().parent == out_root.resolve()` | 还有没有别的 rc 名能逃出 out-root（symlink？大小写不敏感文件系统？） |
| 「一个 SHA 一个 rc」只按目录名判，换个 `--rc-name` 就能重冻 | 新增 `_existing_rc_for_sha`：扫 out-root 下全部 `*/rc-manifest.json` 按 `candidate.sha` 判重 | 这道门能被什么输入绕开（读不出来的旧件被 `continue` 跳过，算不算洞） |
| SHA / dirty / 锁不是同一时刻的快照 | 校验器 subprocess 之后、首次 mkdir 之前复核 HEAD 与 porcelain，变了即拒，并记 `rechecked_before_write` | 剩余时间窗有多大；这个恒 `true` 的字段作为观测点够不够 |
| `main_root` 用 `git_common_dir.parent` 推，在 separate-git-dir / submodule / bare 下给出错值 | 改用 `git worktree list --porcelain` 首条，并把来源记进 `main_root_source` | 新实现在哪些拓扑下仍会错；fallback 分支什么时候会走到 |
| 首次 mkdir 的 `OSError` 以裸 traceback + rc=1 逃出，冒充「内容不合格」档 | mkdir 与写 manifest 都裹进 `try/except OSError` → `_Env`（rc=2 带 `⛔ [env]` 标记） | 还有哪些环境级失败会落错档 |
| journey 的 `candidate` 是非 dict 真值时 `check` 抛 `AttributeError` 崩掉 | 加 `isinstance` 判定，记一条问题后 `continue` | 还有哪些畸形输入能让 `check` 以未捕获异常收场 |
| `check` 先试 cwd 相对路径，cwd 同名目录会静默压过显式 `--out-root` | 名字与路径分流：不含 `/`、不以 `.`/`~` 开头且匹配 rc 正则的一律按名字在 `--out-root` 下解析，绝不回落 cwd | 分流规则有没有留下歧义输入 |
| `check` 成功不说明它没验什么 | 通过时打印一行自陈（未验 schema / symlink / RC 完整性） | 这句话是否与实际职责范围一致 |
| 裁判 `test_no_dirty_bypass_switch` 只排除字面量 `allow-dirty`（变异实测：加一个叫 `--force` 的旁路可让 22 条全绿而脏树冻出 `dirty=false`） | 改锚在 **freeze 子命令的选项名全集**上（封闭集合 + 验伪锚） | 这道门现在能不能被绕开（比如环境变量旁路、或在 `check` 侧加旁路） |
| `test_check_detects_journey_sha_mismatch` 只放一份 journey，「逐份」与「至少一份」不可区分 | 补第二份一致的 journey | 够不够 |
| `test_rerun_same_rc_refused` 在守卫被删后仍绿（`FileExistsError` 同样退 1） | 补 `_REJECT_MARK` 与「落点已存在」文案断言 | 够不够 |
| 两条 dirty 用例用裸 `"dirty" in output` 作锚，被脚本自己打印的 caveat 文字满足 | 改锚 `"dirty tree"`（只有主门会说）+ 断言列出脏条目 | 还有哪些判据锚在太宽的词上 |

## ③ 请按重要性排序回答的问题

- **⓪ 整改本身有没有引入新缺陷。** 这一轮改了十处代码。哪一处的修复扩大了别的攻击面、
  或让某条既有性质不再成立？特别看：新增的 TOCTOU 复核与 dirty 主门之间的关系
  （复核会不会在主门失效时掩盖问题，让判据测不到主门）。
- **① 拒绝路径零写入是否仍然成立。** 新增了两道拒绝门（包含性、同 SHA），它们的位置相对
  第一次 mkdir 是否正确？`_existing_rc_for_sha` 会读 out-root 下的文件，这算写入吗？
- **② `check` 的职责边界**在代码与那行自陈之间是否一致；`_resolve_rc_dir` 的名字/路径分流
  有没有未被拦下的输入。
- **③ 32 条裁判里还有没有「取名面小于主张」的判据。** 本卡已经栽了三次（文本判据被诚实声明打红、
  单名判据被同族别名的变异越过、裸词判据被自己的说明文字满足）。请找第四处。
- **④ 负控战役（12 段，`negctl-battery-8fe7f228-*.txt`）**：每段是否只拆了一层、红是否恰好落在
  它声称的那条测试上？有没有哪段的「1 failed」其实是另一条路径红的？
  注意 N10 那段在加固前只红一半，加固后由 `negctl-N10-recheck-*.txt` 复测——这两份合起来是否成立。
- **⑤ README 新增三处**（证据追加期间如何保持执行树干净 / 硬规则 3 改为按 SHA 机械判 /
  `candidate.worktree` 须填旅程实际执行的树）是否与代码一致、是否仍有夸大。
- **⑥ 测试是否真依赖真 git**；新增的 `_write_validator_stub`（写一个真的退 1 / 退 2 的校验器脚本，
  经脚本自带的 `--validator` 传入）算不算违反「禁 mock」——请给出你的判断与依据。

## ④ 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给 `file:line` 与一句复现思路。
描述问题时请用这几种措辞：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**。

## ⑤ 边界

只读，不要修改任何文件；不连任何数据库或网络服务；不评 SLO 阈值与能力台账内容（另卡）；
不评校验器既有规则本身（本卡对它零改动）；不评其他车道的证据内容。

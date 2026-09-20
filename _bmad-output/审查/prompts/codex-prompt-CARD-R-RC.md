# CARD-R-RC 独立复核请求（round-1）

## ① 背景与最小读取面（写死，请只读这些）

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs`
审查绑定：`ef8ace4a73b346790672a61e5308458fbfbcec4f..5cd1cae1e749411197148bfc4319fa9e24685f3f`（后者 = 当前 HEAD）

本卡给 `docs/release-evidence/` 这套「发布证据 manifest」规范补上**生成端**。此前只有校验器
（`validate_release_manifest.py`，已合入，本卡零改动），它把 `candidate.sha` 必须完整 40 位、
`candidate.dirty` 必须为 `false` 定成硬门，但只验格式不验来源——这两个字段一直靠人手填。
本卡新增一个冻结脚本，让它们在冻结当刻由机器取。

**最小读取面**（其余文件请勿纳入判断）：

1. 本卡全部改动（恰三个文件）：
   `git --no-pager diff --no-color ef8ace4a73b346790672a61e5308458fbfbcec4f 5cd1cae1e749411197148bfc4319fa9e24685f3f -- . ':(exclude)_bmad-output'`
   - 新增 `backend/scripts/freeze_release_candidate.py`
   - 新增 `backend/tests/unit/test_freeze_release_candidate.py`
   - 追加 `docs/release-evidence/README.md`（只追加，无删改）
2. `backend/scripts/validate_release_manifest.py` 的 `:57-80`（常量与证据根钉死）、
   `:800-867`（`discover_manifests` / `check_rc_completeness`）、`:883-987`（CLI 与退出码）
3. `docs/release-evidence/manifest.schema.json` 的 `:119-149`（`candidate`）、`:200-212`（`index_sha`）
4. `docs/release-evidence/README.md` 本卡新增的两节（「RC 冻结与重跑规则」「双树声明」）
   与既有的 `:56`（candidate.sha 填写警告）、`:164`（只验格式不验存在）
5. `backend/tests/unit/test_validate_release_manifest.py` 的 `:1-60`（自足声明与基底诚实声明）、
   `:1174-1180`（`_cli` 形态）
6. 本卡证据：`_bmad-output/审查/evidence-rrc/` 下的
   `freeze-real-*.txt`、`freeze-dirty-real-*.txt`、`check-real-*.txt`、
   `rc-manifest-real-rc-20260918-5cd1cae1.json`、`negctl-dirty-*.txt`、`negctl-checksha-*.txt`、
   `negctl-locksha-*.txt`、`struct-*.txt`、`ruff-*.txt`

## ② 作者自述（请独立核对，不要采信）

1. dirty 门是硬门：`git status --porcelain --untracked-files=all -z` 非空即退 1，且**拒绝路径零写入**
   ——`<out-root>/` 本身都不会被建出来。没有任何跳过该门的开关。
2. `candidate.sha` 来自 `git rev-parse HEAD`，正则与 schema 的 `candidate.sha` 同形（完整 40 位、
   拒绝全零）。因此「归档 `<rc>/` 的提交」必然晚于它。
3. 双树消歧字段（`worktree_rel_to_main` / `git_common_dir` / `is_linked_worktree`）在 linked worktree
   与主仓两态都正确；`--git-common-dir` 在主仓返回相对值 `.git`，脚本对它做了绝对化。
4. 依赖锁恰两项（`backend/requirements.txt` + `frontend/obsidian-plugin/package-lock.json`），
   缺任一即退 1，不写 `null` 冒充「本项目无锁」。
5. 索引 SHA：`--index-sha` 与 `--index-sha-null-reason` 二选一必给，都给或都不给均退 1
   （镜像 schema「禁止省略字段冒充无关」）。
6. 校验器走 subprocess 真调，脚本零 import 它；`--all` 非 0 即整体拒绝（rc=2 时原样透传 2）。
7. `check` 逐份 journey 比对 `candidate.sha`，不做「至少一份一致」；缺失的 J 只打印不判红。
8. 本卡在 `docs/release-evidence/` 下零新增目录（不提交任何真 `<rc>/`）。
9. README 只追加，`^-[^-]` 计数为 0。
10. 测试用 `tmp_path` 里 `git init` 出的真 git 仓跑真脚本，零 mock、零 monkeypatch、零 autouse。

## ③ 请按重要性排序回答的问题

- **⓪ dirty 门有没有门未覆盖的路径。** `--untracked-files=all` 是否足够？`.gitignore` 忽略面、
  submodule / gitlink、`assume-unchanged` 与 `skip-worktree`、`-z` 输出的解析（rename 占两段）
  各自会让哪些未被拦下的输入通过这道门？脚本把这些写进了 `candidate.dirty_scope_caveats`，
  这份声明是否与代码实际行为一致，有没有漏掉的一类。
- **① 两条重跑规则是否自洽。** 「同 SHA 重冻结被拒」与「文档改动也算新 SHA」合起来，会不会让
  R-J* 在 14 天 dogfood 期间无法给同一 rc 追加证据（校验器 S11 要求换 SHA 须重开窗口）？
  README 把这个代价写清楚了吗，还是留下了一个执行时才会撞上的矛盾。
- **② `--out-root` 在证据树外时不跑 `--require-complete`**，`rc-manifest` 记的是
  `require_complete: null` + 一段 skip 理由。这与「跑了并得到 `exit_code=1, missing=[10 项]`」
  在语义上差在哪？「冻结当刻缺 J01–J10」这条事实有没有因此在回执里丢失？
- **③ `check` 只读 `candidate.sha` 不跑 schema**，会不会把一份结构非法的 journey manifest 判成
  「一致」？是否该让 `check` 顺带调一次校验器？给出对照输入说明。
- **④ 依赖锁只 hash 两个文件**，而 venv 实装版本可能与 `requirements.txt` 不一致
  （README 自述 `jsonschema` 不在 requirements.txt、现为传递依赖，即一例）。这份「锁」
  证明了什么、没证明什么？
- **⑤ README 的双树声明**（`/app` 来自 worktree `backend/`、`/vaults` 来自主仓根、索引在 named
  volume `canvas-lancedb-data` 内无宿主 bind 路径）是否被写成了 R-J* 能照着填的规则，
  还是只是叙述？三条填写规则有没有留下歧义。
- **⑥ 测试是否真依赖真 git**（有无任何打桩 subprocess 的痕迹）；三段负控（dirty 判定恒干净 /
  `check` 的 sha 比对失效 / 锁 sha256 变常量）是否各自只拆了一层，红是否恰好落在它们声称的断言上。

## ④ 输出格式

按 BLOCKER / HIGH / MEDIUM / LOW 分级，每条给 `file:line` 与一句复现思路。
描述问题时请用这几种措辞：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**。

## ⑤ 边界

只读，不要修改任何文件；不连任何数据库或网络服务；不评 SLO 阈值与能力台账内容（另卡）；
不评校验器既有规则本身（本卡对它零改动）；不评其他车道的证据内容。

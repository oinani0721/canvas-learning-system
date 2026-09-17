# 独立复核请求 — CARD-G2-7b-TAIL（deploy-vault.sh G2-7b 尾巴 5 项）

## ① 背景

仓库：Canvas Learning System（Tauri + React + FastAPI）。本卡是部署卡链的最后一张，
收口 `scripts/deploy-vault.sh` 在上一张卡（CARD-G2-7b）已登记「转下一卡」的 5 项残留。
`deploy-vault.sh` 是「一键部署一个 vault + 它绑定的后端实例」的六步脚本，rc 表：
0 成功 / 64 用法错 / 71..76 对应步 1..6 失败。

审查绑定 SHA：`be2a799d`（= 当前 HEAD, round-2）。上一张卡的末 commit：`37b89ce0`。

本卡改动只在三个文件内：`scripts/deploy-vault.sh`、
`backend/tests/unit/test_deploy_vault_sh.py`、（本次实际未改）`scripts/cls_forbidden_paths.py`。

## ② 作者自述（请独立核对，不要采信）

1. **步 4 基准回执核对**：把 `src="$SRC_MIRROR"`（deploy-vault.sh:2871 附近）换成
   `src="$VAULT"` 时，校验器拿目标 vault 跟它自己比，`content-drift` 恒 0、`match` 非零、
   步 4 消息里的「基准=源镜像」文案也不变 ⇒ 既有三条断言全绿。作者称已在步 4 末尾
   （`deploy-vault.sh:2864` 起）加了「读校验器报告的 `# source` 回执 + 与独立算出的
   应有基准比对」，并称期望值是**独立算的**（`_want_src`），不是复用 `$src`。
   请核对：这条核对能否被本卡自己的写法绕过（例如期望值实际仍来自同一个变量）；
   以及它在 `--port 8011`（不建源镜像）那一支是否仍成立。

2. **五处 bash 写点改同目录 `mktemp` → 写 → `mv`**：`mk_tmp_beside()`
   （deploy-vault.sh:340）。作者称原问题是「终路径名字可预先算出」，预置一条软链/硬链接
   会让部署每次都停在写入前复查上（拒绝服务），而不是内容越界。随之把三条
   `<终路径>.tmp` 的固定名从 preflight 待写清单（`PENDING_WRITES`，:655）里撤掉，
   换成它们所在的**目录**。请核对：撤掉那三条登记是否**减弱**了 preflight 的覆盖面
   （尤其硬链接一轴）；`mv` 到终路径这一步是否仍有未被拦下的输入；失败路径上
   mktemp 出来的临时件是否都被清掉。

3. **rc 75 / 76 入口负控 + 六行状态**：作者称新增了从部署入口真跑出 rc 75 / 76 的
   负控（PATH 前置一个恒失败的 `docker` / `shasum`），并把 `step6_evidence`
   （:3311）落盘的「## 六行状态」从五行补成六行 —— 第 6 行由本步在**落盘之前**合成。
   为此把 sha 计算提到了写盘之前。请核对：第 6 行与 `run_step` 事后 emit 的那一行
   在**各条失败路径**上是否仍逐字一致；把 sha 计算移出 `{ … } > 文件` 之后，
   `_sha_fail` 的判定与报告末尾 `rc=` 行是否仍不可能自相矛盾；
   以及「失败入口只列已跑步骤」这条性质有没有被改坏。

4. **`ancestor_symlink_hits` 纵深门**：作者称 96 种拓扑实测造不出「只有它命中、
   逐段 walker 命不中」的样本，故未造独立门，改为「中和 walker 后它必须顶上、
   两条都中和必须全漏」的两跑对照（测试文件 `_e_topology` 附近）。
   请核对该结论的论证是否过强，以及那组样本是否真的绕开了 `hits()` 的规则 1-4。

5. **M-1 / M-2 / M-3**：`assert_writable_now`（:265）的链接数三态补全
   （补 `0`、补位数上限、显式判探针 rc、字符集改逐字符枚举）；两条源码门从
   `count()` 收窄为顺序门 / 引号门；A3 取值（:2503 附近）从 `tr -d` 无差别删引号
   改为只剥配对的首尾引号。请核对各自是否留下新的未被拦下的输入。

## ③ 按重要性排序的问题

1. 步 4 回执核对（`deploy-vault.sh:2864-2905`）：`_want_src` 的取值路径上是否存在
   「实际仍等于被改的那个 `$src`」的输入？`--port 8011` 时 `_mirror_at` 为空，
   期望值退回 `$HARNESS/canvas-vault` —— 若调用方把 `--vault` 指到 harness 自己的
   canvas-vault，这条核对会怎样？
2. `mk_tmp_beside`（:340-364）：`dirname` 结果为软链目录、`mktemp` 返回值含空白、
   `$TMPDIR` 无关（它写的是目标同目录）等情形；以及 `printf '%s'` 回显路径的方式
   在路径含换行时的行为。
3. `PENDING_WRITES`（:655-700）：撤掉 `env-file-tmp` / `key-file-tmp` /
   `ev-deploy-report-tmp` 之后，preflight 对「目录本身是软链」与「终路径是硬链接」
   两轴的覆盖是否各自还在？
4. `step6_evidence`（:3311-3460）：第 6 行合成与末尾 `rc=` 行的一致性；
   `mv` 失败时残留的 mktemp 文件与 `STEP_MSG` 的说法是否相符。
5. `_seed_env_file_body` / `seed_env_file` 包装（:944-1020）：拆成两层之后
   `SEED_ERR` / `SEED_TMP` 的生命周期；`set -euo pipefail` 下 `return "$rc"` 的行为。
6. `assert_writable_now`（:265-338）：三态判定的顺序；位数上限 10 的取值依据；
   `nrc` 捕获是否真的能拿到命令替换的退出码。
7. A3 取值（:2503-2516）：`case` 的两条引号模式在单字符值、只有一侧引号、
   值内含 `$'\r'` 等输入下的行为。
8. 测试侧（`backend/tests/unit/test_deploy_vault_sh.py:5759-6555`）：
   `harness_main_js` 夹具会在仓内写一个 gitignored 的 `main.js` 桩并还原 ——
   它对同时跑的别的用例有没有副作用？各条负控的期望值是否真的钉住了它声称的那件事？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出 `file:line` 与一句核验路径。
无问题的分级请显式写「无」。请不要复述作者自述，只写你自己核对出的结论。

## ⑤ 边界

- **只读**：不要修改任何文件，不要 `git` 写操作。
- 不要执行仓库的 hook（lefthook）、不要跑 `pytest`、不要连任何数据库或网络端口。
- 不要评价 `scripts/verify_vault_install.py` 的 content-drift 语义 —— 那是另一张卡
  （T7）的地盘，本卡对它只读、未改。
- 最小读取面：
  `git diff 37b89ce0 be2a799d -- . ':(exclude)_bmad-output'`；
  `scripts/deploy-vault.sh` 的 `:260-370` / `:620-700` / `:940-1080` / `:2490-2520` /
  `:2792-2910` / `:3311-3464`；
  `scripts/cls_forbidden_paths.py` 的 `:420-560`；
  `backend/tests/unit/test_deploy_vault_sh.py` 的 `:5759-6555`。
- 措辞：请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类说法描述问题。

## ⑥ round-2 补充：上一轮意见的整改点（请重点核这些，不要复述）

上一轮（绑定 `70b9203a`）给出 BLOCKER 1 / MEDIUM 4 / LOW 3，本轮全部整改，逐条如下。
请核对每一条**是否真的闭合**，以及整改本身有没有引入新的未被拦下的输入：

1. **BLOCKER（父目录取法）**：`mk_tmp_beside`（`scripts/deploy-vault.sh:340` 一带）
   从 `$(dirname "$dst")` 改为 `${dst%/*}` 参数展开，并对「取不出父目录」的输入显式拒绝。
   请核对：末尾换行之外的其它字节（多重斜杠、尾斜杠、单段路径、根目录）在新写法下的落点；
   以及五个调用方传入的路径是否都保证含 `/`。
2. **MEDIUM-1（终路径是目录）**：`mk_tmp_beside` 新增「`[ -d "$dst" ]` 即拒」。
   请核对：这条检查与随后 `mv` 之间的窗口；以及它是否误拒了任何合法输入。
3. **MEDIUM-2（值内回车）**：A3（`:2520` 一带）新增「值内含 CR 即拒」。
   请核对：该判据用 `*"$(printf '\r')"*` 匹配，在 `set -euo pipefail` 下的行为，
   以及它与紧邻的引号剥离、尾随 CR 剥离三者的先后是否自洽。
4. **MEDIUM-3（残件说法过时）**：新增 `mark_unpublished`，五条发布失败分支各追加一条更正；
   并撤回了上一版「失败即删除残件」的三处。请核对：`mark_unpublished` 自身失败时的行为；
   五条分支是否**确实**都覆盖到；以及残件与终路径同目录堆积是否带来新问题。
5. **MEDIUM-4（测试夹具）**：`harness_main_js`（测试文件内）删除前先比对内容身份，
   并在 docstring 里声明不支持并行。请核对这条身份比对是否仍有把别人产物删掉的路径。
6. **LOW-1（全 0 链接数）**：`assert_writable_now` 改按「全是 0」判（`case` + `*[!0]*`）。
7. **LOW-2（helper 错因）**：删掉了恒空的 `MK_TMP_ERR` 全局，细因改走 stderr。
8. **LOW-3（顺序门分辨力）**：按上一轮结论登记不改，限制已写进判据 docstring。

最小读取面在 ⑤ 的基础上增加：`scripts/deploy-vault.sh` 的 `:324-380`、`:2505-2535`、
`:3300-3320`（`mark_unpublished`）。

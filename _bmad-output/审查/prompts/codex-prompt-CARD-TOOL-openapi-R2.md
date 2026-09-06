你是独立复核者。请对下面这一份改动做一轮审查。树根为
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review`
（分支 `card/y5-review`，本卡 commit `f0b1e282`，其父为 `36871263`）。全部路径都相对该树根。

## §一 最小读取面（只读这些，不要扩散到其它目录）

1. `git diff 36871263 f0b1e282 -- scripts/spec-tools/check-openapi-drift.py backend/tests/contract/test_openapi_snapshot_drift.py`
2. `scripts/spec-tools/check-openapi-drift.py` 的 :60-160（常量区 + `_tag_leaf` / `_normalize` / `canonicalize`）
   与 :240-270（本卡改动所在的 `check_drift` 尾段）
3. `backend/tests/contract/test_openapi_snapshot_drift.py` 的 :30-60（模块加载与常量）
   与 :251-315（本卡新增的三门）
4. 参照口径：`lefthook.yml` 的 :50-70（spec-sync 的解析器选择）与 :146-171（python-typecheck）
5. 已落盘的裁判证据：`_bmad-output/审查/evidence-openapi-r2/`（目录内 txt，尤其
   `oldstring-control-*.txt`、`judge45-fix-verbatim-*.txt`、`negctl-three-archetype-locks-*.txt`）

## §二 作者自述（**请独立核对，不要采信**）

作者声称：

- **改动 A**：`check-openapi-drift.py` 原本在判出漂移时向 stderr 打一行 FIX 提示，内容是
  `python scripts/spec-tools/check-openapi-drift.py --write backend/openapi.json`。作者称这行有
  两个缺陷：解析器是裸 `python`（本机与 CI 都不是本仓 venv），路径是相对路径（在 `backend/`
  子目录下两个路径都不存在）。改法是：venv 解析器存在则用、否则回落 `python3`（对齐
  `lefthook.yml:54`），脚本与快照都改成绝对路径，并给三个路径加双引号。
- **改动 A 的实测**：作者称旧串在仓库根 rc=1（ModuleNotFoundError: structlog）、在 `backend/`
  下 rc=2（can't open file）；新串从实际 stderr 逐字复制后，在仓库根与 `backend/` 各执行一次
  都 rc=0 并打印 `WROTE: ... (paths=193 schemas=353)`。
- **改动 B**：测试文件新增三门（23 → 26），分别覆盖 `x-*` 扩展内的字面 `required`、Link Object
  的字面 `requestBody`、名叫 `enum` / `value` 的合法属性名。作者称这三门是
  **「防止重新引入 required 排序启发式」的回归锁**，在当前实现（`_normalize` 对一切数组保序）
  下**本来就绿**，不改变也不检验任何历史行为；依据是 `check-openapi-drift.py:121-129` 记录的
  三轮终局结论。
- **改动 B 的承重负控**：作者称把 `_normalize` 临时换成四种排序启发式（朴素键名 / 形状守卫 /
  语境切分 / 语境切分且把 `value` 也划为数据）后跑真 pytest，前三种下三门均转为失败；第四种
  下第三门保持通过而其余三门仍失败。作者还称第三门在「语境切分」下失败在**细节断言**那一条
  （`>properties>value>required`），若该门只写 `assert not clean` 则会在那种启发式下假通过。
- **改动 C**：作者称 `_normalize` / `canonicalize` / `_tag_leaf` / `VOLATILE_INFO_KEYS` /
  `X_GENERATOR_NAME` / `_load_drift_module` 六处零改动，脚本 diff 只有一个 hunk。
- **改动 D**：作者称 `backend/openapi.json` 在两次 `--write` 后只有 `x-generated-at` 一行变化，
  随后已还原到 HEAD 版本，本卡 commit 不含该文件。

## §三 请按下列重要性顺序回答

1. **FIX 串的可用性**：新的 FIX 提示行在两种环境下是否都能被开发者原样粘贴执行 ——
   (a) 本机（仓内有 `backend/.venv`）；(b) CI（仓内没有 `backend/.venv`，回落 `python3`）。
   请特别检查：回落分支产出的串是否仍是可执行的；路径里若含空格是否仍成立；
   `--write` 目标恒为仓内正式快照、与 `--snapshot` 的入参无关，这一点是否与改动前语义一致。
   CI 那条作者未实跑，请只做静态判断并明确标注这是未实测项。
2. **三门是否真有牙齿**：如果将来有人在 `_normalize` 里重新加入 required 排序，这三门是否
   会转为失败？请指出在 `_normalize` 的**哪一处、改成什么语义**会让它们分别转为失败
   （只描述位置与语义，不要提交任何改动）。并请独立判断作者关于第四种启发式下第三门
   保持通过的说法是否成立、以及三门加上既有 `test_required_order_is_drift` 是否构成组合覆盖。
   若你认为某一门在任何合理的排序实现下都不会转为失败（即它是死门），请直接点名。
3. **措辞是否夸大**：三门的 docstring、模块内注释与 commit message 有没有把这三门说成
   「修复」了什么、或暗示历史上存在过未被发现的行为？作者的定位是「回归锁、当前本来就绿」，
   请核对文字与事实是否一致。
4. **零行为改动**：`_normalize` / `canonicalize` / `_tag_leaf` / `VOLATILE_INFO_KEYS` /
   `X_GENERATOR_NAME` / `_load_drift_module` 六处是否确实一字未动；脚本 diff 是否只有一个
   hunk；新增的四个局部变量是否与 `check_drift` 内既有变量重名或产生遮蔽。

## §四 输出格式

按下列分节输出，每条问题写明：等级（BLOCKER / HIGH / MEDIUM / LOW）、文件与行号、
事实依据（引用你实际读到的内容）、你建议的处置。若某一节没有问题，明确写「无」。

- 一、FIX 串可用性
- 二、三门的有效性
- 三、措辞与事实一致性
- 四、零行为改动
- 五、其它

最后**单独一行**输出：`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`。

## §五 边界

- 只读审查，不要修改任何文件、不要运行会写盘的命令。
- 不要连接 Neo4j（7691 / 7687）、不要跑 `tests/contract` 目录级执行
  （同目录 `test_openapi_contract.py` 是 schemathesis，单个 operation 就要三分钟以上）。
- 只跑 `tests/contract/test_openapi_snapshot_drift.py` 这一个文件是允许的：
  `cd backend && ./.venv/bin/pytest -q -p no:cacheprovider tests/contract/test_openapi_snapshot_drift.py`
- 本卡不负责 `backend/app/**` 的 OpenAPI 形状、不负责 CI workflow、不负责 `lefthook.yml`
  （分属别的卡），这些面上的问题请只登记、不要求本卡处置。

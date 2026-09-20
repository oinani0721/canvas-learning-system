> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-4
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10-r4.md)" > _bmad-output/审查/codex-review-CARD-G5-10-r4.md 2> _bmad-output/审查/codex-review-CARD-G5-10-r4.stderr </dev/null`
> 审查绑定: `f42ff845`（不绑最终 HEAD——其后代码已按本轮意见整改, 移交 round-5）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

# CARD-G5-10 round-4 独立复核（绑 `f42ff8457ed428917f91c14153fb7b6726f3bda3`）

## 绑定与读取面核对

- 当前 HEAD 确认为 `f42ff8457ed428917f91c14153fb7b6726f3bda3`。
- tracked 工作树干净；只有 `_bmad-output/审查/...` 等未跟踪审查材料。
- `a357194b..f42ff845` 排除 `_bmad-output` 后确实只有两份新增文件：
  - `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`
  - `backend/tests/skills/test_g5_10_split_apply.py`
- `d5a06d33..f42ff845` 排除 `_bmad-output` 后也只改这两份文件。
- 静态统计测试函数为 25 个。按边界未运行 pytest / apply / undo / ruff，未连数据库或网络；因此“25/25 绿、ruff rc=0、AST 门、外部负控”仍是作者声明，本轮是静态独立验伪。

## r3 五条整改声明核对

| 命题 | 结论 |
|---|---|
| r3-HIGH-1 fresh 行号传导 | **主路径成立，但嵌套候选仍有残留缺口。** `_check_fresh()` 返回 fresh 坐标，dry-run、`run_create()`、`run_callout_insert()` 都使用它；㉕也能钉住“先插甲 callout 再建乙”的兄弟小节场景。但正文重建只剔除当前候选自己的 callout 行，父候选重建时会把子候选 callout 留进父节点，见 HIGH-2。 |
| r3-HIGH-2 undo 目标链 | **代码命题静态成立。** create/modify 两个分支都在删/还原前调用 `_undo_target_chain_ok()`；`assert_symlink_free()` 会拒绝 symlink 目录链，realpath 包含判定兜底物理越界。末段是 hardlink 时检查会通过，但 create undo 只移除 vault 内目录项、modify undo 用原子替换只改 vault 内目录项，未发现把写入扩散到外部链接的行为。普通文件位于 symlink 目录中会被拒绝。 |
| r3-MEDIUM-1 按批前池重放 | **同基错误后缀命题成立，但“产物改名后残留”能骗过减法。** 重放逐字比对 `resolved_name`，`claimed` 顺序与 preview 引擎的候选顺序一致；不过 `ours` 只检查“候选账上名字”的路径，不扫描其他文件名下同 `split_stable_id` 的残留节点，见 HIGH-1。 |
| r3-LOW-1 ㉒ 三变体 | **声明的三变体存在。** batch/workroot/journal 各自点名 `symlink`，且外部 journal 行数不变。若实现缩窄为只看 journal 末段，batch/workroot 会因外部账本被追加而红，journal 则直接红。但 `outputs/` 本身换成 symlink 的变体仍未入持久测试，见 LOW-1。 |
| r3-LOW-2 ㉓/㉕ | **成立。** U+2028 拒绝臂、CRLF/LF 混合局部 terminator、以及“先甲 callout 后乙创建/插入”的 ㉕ 都存在；㉕对乙正文与 callout 位置的钉住有效。 |

其余静态命题未发现反向证据：真 `scan_vault` 成员/derived/非孤儿断言仍在；callout 默认关与非 TTY 未确认不插仍成立；默认 apply 路径的物理删除原语仍只出现在 undo 分支；本卡仍不加 `SKILL.md`。

---

# BLOCKER

无。

---

# HIGH

## HIGH-1：批前池减法识别不了“已改名但保留同 stable_id”的自家产物，会用旧 preview 再建一份重复 provenance

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:294-318`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:200-216`

缺陷：`ours` 只在 `节点/<preview resolved_name>.md` 这一旧路径上检查 `split_stable_id`，不扫描其他文件名下同 id 的残留节点；改名残留不进入减法，旧名空位又被 `resolve_name()` 判为可用，最终 `_check_conflicts()` 也不会拦，形成两个文件携带同一 `split_stable_id`。

复现思路：未被拦下的输入——preview 候选 `甲` 生成 `节点/甲.md` 后，把该文件改名为 `节点/改名残留.md` 并保留 frontmatter；再用同一旧 preview 确认原候选。`pool={改名残留}`，但 `节点/甲.md` 不存在所以 `ours` 为空，`resolve_name("甲", pool, ...)` 仍返回 `甲`，于是新建第二份同 stable_id 的 `节点/甲.md`。对照输入——不改名时目标已有同 id，当前实现跳过；负控输入——按全节点池扫描 `split_stable_id` 时应拒绝并指出残留路径。

## HIGH-2：fresh 行号已传导，但正文重建只剔除“自己的 callout”，父候选会包含后插入的子候选 callout

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:272-291`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:321-378`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:500-509`
- `backend/tests/skills/test_g5_10_split_apply.py:887-928`

缺陷：门①允许把 fresh span 中全部派生 callout 剔除后映射回旧坐标，但 `run_create()` 按 fresh span 切片后只删除 `callout_line(c["resolved_name"])`，其他候选的嵌套 callout 仍留在父节点正文里，生成的字节也不再等于 preview 时的内容单元。

复现思路：门未覆盖的路径——preview 含父小节与嵌套子小节；先只确认子小节并插入 callout，再用同一 preview 确认父小节。父候选 fresh span 含子 callout，门①通过，但父节点正文包含 `> [!relation/related_to]+ 已派生为 [[节点/子小节]] …`。对照输入——父和子同一次 apply 中先创建两份节点、后插 callout，父节点正文干净；现有 ⑱ 只覆盖这种同命令重跑，㉕ 只覆盖兄弟小节，均不会红。

---

# MEDIUM

## MEDIUM-1：候选创建/认领失败后，callout 分支仍会因为目标路径存在而修改来源板

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:466-483`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:611-618`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:678-703`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:975-977`

缺陷：`run_create()` 已明确判定“同 id 但字节与账上 planned 不符，拒绝认领”并计失败后，`main()` 仍无条件调用 `run_callout_insert()`；该分支只检查目标 `.is_file()`，不检查本候选创建/认领是否成功，于是会在失败件上照常备份并插入 callout。

复现思路：对照输入——先 apply 生成节点但不插 callout，随后修改节点内容并删除 journal 中该 seq 的 done 行模拟中断；再同 preview 运行 `--apply --insert-callout --confirm-insert <id>`。`run_create()` 因当前 sha ≠ 账上 planned sha 报“拒绝认领”，但目标文件仍在，callout 分支仍修改来源板并落 `split_modify` 账。负控输入——callout 计划应只包含 create/done 成功或可安全认领的候选；目标不存在的失败路径目前已经会跳过。

---

# LOW

## LOW-1：㉒ 仍缺 `outputs/` 本身换成 symlink 的变体

- `backend/tests/skills/test_g5_10_split_apply.py:758-788`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:738-749`

缺陷：实现检查 `vault / outputs`，但持久测试只覆盖 batch、`outputs/board-split`、journal 三个位置，未覆盖 `outputs/` 目录本身。

复现思路：负控输入——把 `vault/outputs` 移到外部并替换为目录 symlink；当前实现会点名拒绝。若把实现中的检查列表缩窄为 `vault、workroot、batch、journal` 而漏掉 `outputs`，现有三变体仍可保持绿。

## LOW-2：持久测试没有钉住 r3-MEDIUM-1 的“同基错误后缀”专属形态

- `backend/tests/skills/test_g5_10_split_apply.py:726-752`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:294-318`

缺陷：㉑把手改目标写成完全不相关的“被改名的目标”，这会同时被 r3 旧兼容规则和当前重放规则拒绝；真正区分二者的是“期望 `甲_3` 被手改为空闲 `甲_9`”这一同基形态。

复现思路：负控输入——preview 时池中已有 `甲`、`甲_2`，期望名 `甲_3`；手改旧 JSON 为 `甲_9`。当前重放会拒绝；若恢复 r3 的同基后缀兼容判断则会被放行，而现有 ㉑ 仍绿。作者声明的外部负控未在本轮读取面内复核。

---

# 结论计数

`BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 2`

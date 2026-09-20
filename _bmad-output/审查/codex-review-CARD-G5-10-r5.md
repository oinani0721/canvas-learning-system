> 批次: BATCH-2026-09-18-第十五批 · 车道 P7 · 卡 CARD-G5-10 round-5
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source $HOME/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-10-r5.md)" > _bmad-output/审查/codex-review-CARD-G5-10-r5.md 2> _bmad-output/审查/codex-review-CARD-G5-10-r5.stderr </dev/null`
> 审查绑定: `80e4a319`（= 送审时 HEAD & 最终代码 SHA；**第 5 轮仍有 HIGH（D-15 上限已到）⇒ 按卡文停下交主 session**）
> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: glm-5.3` / `(L9) reasoning effort: max`

---

# CARD-G5-10 round-5 独立复核（绑定 `80e4a319`）

## 绑定与地盘核对

- 当前 HEAD 实测为 `80e4a3198a3484e965e8fc8a63eac2df4a188ff9`，与送审绑定一致。
- tracked 工作树干净；但存在未跟踪的 `_bmad-output/审查/...` 审查材料，这与送审说明“tracked 干净”一致。
- `a357194b..80e4a319` 排除 `_bmad-output` 后只有两份新增文件：
  - `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`
  - `backend/tests/skills/test_g5_10_split_apply.py`
- `f42ff845..80e4a319` 也只改上述两份文件；未改 `split_preview.py`、`board_manifest_service.py`、`undo_journal.py`，也未新增 board-split `SKILL.md`。
- 测试函数静态计数为 26 个。
- 静态删除调用只有 `split_apply.py:849` 的 `os.remove`，且仅在 undo 的 `OP_SPLIT_CREATE` / `STATE_DONE` / sha 相符分支；默认 apply 路径未发现物理删除调用。
- 遵守只读边界，本轮未运行 pytest、apply、undo 或任何写盘裁判；作者“26/26 绿”等运行结果仍按作者声明处理。

---

## r4 五条整改命题独立核验

| 命题 | 结论 |
|---|---|
| r4-HIGH-1 改名残留扫描 | **部分成立，未完全关闭**。普通文件改名且 `split_stable_id` 可读时会被拦；但 symlink 残留会被显式跳过，超过 200 行 frontmatter 的残留读不出 id，两条路径仍可形成同 id 双产物，见 HIGH-2。 |
| r4-HIGH-2 创建正文剔除全部派生 callout | **目标场景成立，但过度剔除**。对 preview 之后插入的子候选 callout有效；但 preview 当时已存在且进入内容指纹的真实 callout 行也会被剃掉，见 HIGH-3。 |
| r4-MEDIUM-1 `ok_ids` 传导 | **静态成立**。planned 恢复只有 planned sha 逐字节相符才入 `ok_ids`；EEXIST 竞态要求同 id + planned sha；创建失败不入集；callout 分支按 `ok_ids` 过滤。早批已落地且同 id 的候选会被视为 applied 并入集，不被过度跳过。dry-run 禁用 `--insert-callout`；undo 后重跑会按最新 journal 状态重新走 planned/done。 |
| r4-LOW-1 ㉒增加 `outputs/` symlink 变体 | **实现行为成立**：`_assert_batch_chain_symlink_free()` 检查 `vault → outputs → board-split → batch → journal`。但持久测试只断言泛化的 `"symlink"`，没有钉住 `outputs` 这一层本身，见 LOW-2。 |
| r4-LOW-2 ㉖同基错误后缀 | **成立**。池含 `甲小节` / `甲小节_2` 时期望 `_3`，手改成空闲 `_9` 会被批前池重放拒绝，并断言零产物。 |

---

# BLOCKER

无。

---

# HIGH

## HIGH-1：旧 preview 的 `content_fingerprint` 没有与 fresh 重算结果绑定，改名/改正文后同步改指纹即可让确认 id 落到新内容

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:220-247`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:333-383`

缺陷：`_check_fresh()` 虽然重算 fresh preview，但只对账安全标志、anchor、`suggested_name` 和行号；内容面只是把**旧 JSON 里可编辑的** `content_fingerprint` 拿去描述当前文件，没有确认“旧 preview 当时的指纹”与 fresh 候选的原始指纹一致。

复现思路：**未被拦下的输入**——先对 `甲小节` 生成 preview；保持标题和位置不变，把正文第二行从 `BODY2` 改成 `BODY_ALT`；再生成一份新 preview，只把新 `content_fingerprint` 复制进旧 JSON。由于 stable_id 不含内容、anchor 不变、候选集不变，`_span_drift_reason()` 会在当前正文上重算出被改过的指纹并放行，最终用户确认的旧 stable_id 会创建为改变后的正文。对照输入——不编辑旧 JSON 时同一正文修改会被“过期”拒绝；负控输入应把旧 `content_fingerprint` 与 fresh 候选指纹（或等价的剔除 callout 后指纹）对账。

---

## HIGH-2：改名残留扫描对“symlink 残留”和“id 位于 200 行之后”的残留 fail-open，r4-HIGH-1 仍未完全关闭

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:119-137`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:200-216`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:301-323`
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1734-1742`

缺陷：全池扫描确实覆盖普通改名文件，但 `existing_split_stable_id()` 最多只读前 200 行 frontmatter；扫描循环又显式 `continue` 掉 symlink 节点，两种“同 stable_id 残留”都读不出 id，随后旧名会被视为空闲并再建一份同 id provenance。

复现思路：**门未覆盖的路径 A**——先由候选 `甲` 创建 `节点/甲.md`，再把实际材料移走并在 `节点/改名.md` 放一条指向它的 symlink；扫描在 `is_symlink(p)` 处跳过，`甲` 成为空闲名，同一旧 preview 再建 `节点/甲.md`。**门未覆盖的路径 B**——把 `节点/甲.md` 改名为 `节点/改名.md`，并在 `split_stable_id:` 前加入超过 199 行合法 YAML frontmatter；循环在 200 行内找不到闭合 `---` 而返回 None，同样再建同 id 文件。负控输入应对任何无法安全读取/解析归属的池内残留 fail-closed，而不是从减法中消失。

---

## HIGH-3：`run_create()` 无条件剔除所有 callout 形态行，会把 preview 时已进入内容指纹的真实内容行从派生正文删掉

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:220-246`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:519-531`
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py:433-448`

缺陷：门①有两层判定——原字节指纹先精确匹配，只有不符时才用“剔除全部派生 callout 后匹配”解释插入漂移；但 `run_create()` 不区分这两层，即使原指纹已经精确证明 callout 行属于 preview 时内容单元，也把它从正文剔除。`split_preview` 的短语级正则本身是既有面、移交；本卡缺陷是执行侧在 exact fingerprint 已通过时仍删行。

复现思路：**未被拦下的输入**——生成 preview 前，来源小节正文里已有一行真实内容 `备注：已派生为 [[节点/某]]，必须保留`；该行不在 fence/HTML 注释中，会进入 preview 的 `content_fingerprint`。apply 时 `_span_drift_reason()` 的第一层 exact match 已通过，但 `run_create()` 因该行匹配 `_DERIVED_CALLOUT` 而剔除，派生节点少掉这行。**对照输入**——若这行是 preview 之后插入的，exact fingerprint 不符、剔除后相符，才是当前容差应接受的路径；因此修复应只在需要 callout-drift 解释时剔除。

---

# MEDIUM

无。

---

# LOW

## LOW-1：普通改名后的恢复提示不准确，“重跑 preview”并不能把已改名产物映射到新账上名

- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:303-314`
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py:815-829`

缺陷：普通改名残留会被 fail-closed 拦住，这是安全方向；但提示“恢复文件名或重跑 preview”中的后者无效，因为 preview 命名解析只看当前名字池，不会根据 frontmatter `split_stable_id` 把改名后的文件识别为同一候选产物。

复现思路：**对照输入**——创建 `节点/甲.md` 后改名为 `节点/新名.md`，再重新生成 preview；若默认未插 callout，候选仍会出现，`甲` 变回空闲名，新 preview 仍账上名 `甲`，改名残留扫描继续拒绝。行为不丢数据，但用户只能恢复旧文件名，没有受支持的改名后认领路径。

---

## LOW-2：㉒ 的 `outputs/` 变体没有钉住“outputs 这一层”本身

- `backend/tests/skills/test_g5_10_split_apply.py:758-793`
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py:768-779`

缺陷：实现确实先点名检查 `vault/outputs`，但测试只断言输出含泛化的 `"symlink"`；删除实现元组中的 `outputs` 项后，该输入仍会被 `workroot` 或 `batch` 的祖先链检查拦下，测试不会因这一层检查缺失而变红。

复现思路：**负控输入**——从 `_assert_batch_chain_symlink_free()` 的直接检查列表移除 `vault / outputs`，保留更内层 `assert_symlink_free()`；㉒ 的 outputs 变体仍会拒绝并保持绿，无法证明每一层都被分别点名。

---

# 其余静态命题

- 真 `scan_vault` 承接面有持久测试：`backend/tests/skills/test_g5_10_split_apply.py:178-197`，按 members / derived / orphans / parse_errors 断言。
- 歧义零持久化、过期零产物、undo 逐字节还原、CRLF 保真、默认 callout 关、`--confirm-insert` 前置拒绝等既有面未发现新的反向证据。
- `ok_ids` 修复本身未发现 r4 回退；部分失败时失败候选不会被插“已派生”。
- ㉖对 r4-LOW-2 的行为钉住程度足够。
- 本轮发现的 HIGH 均不需要覆盖既有文件或物理删除，因此未判 BLOCKER。

# 结论计数

`BLOCKER 0 / HIGH 3 / MEDIUM 0 / LOW 2`

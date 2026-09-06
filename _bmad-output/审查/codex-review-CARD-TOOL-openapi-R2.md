> 批次: BATCH-2026-09-05-第十二批 · 车道 Y5 · 卡 CARD-TOOL-openapi-R2 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-CARD-TOOL-openapi-R2.md)"`
> 审查绑定: `f0b1e282`（审时 HEAD）。审后 HEAD 前进一个整改 commit —— 按本轮 MEDIUM-1（部分采信）与 LOW-1（全采信）只改注释措辞，与审时版 **AST 逐节点相同**（证据 `evidence-openapi-r2/remediation-ast-equiv-*.txt`，含验伪锚）。按协议 §1 属「同一卡内审后再改」= 失绑，已在验收单登记「整改未复审」。
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review` / `model: gpt-6-astra` / `provider: openai` / `sandbox: read-only` / `reasoning effort: ultra` / `session id: 01a072fe-17f3-7582-965e-857640e07b73`

---

已确认当前分支为 `card/y5-review`，HEAD 为 `f0b1e282`，父提交为 `36871263`；所审两份源码及证据与该提交一致。未发现 BLOCKER/HIGH。

### 一、FIX 串可用性

**MEDIUM — 整行仍不能原样粘贴执行。**  
位置：[check-openapi-drift.py:262](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/scripts/spec-tools/check-openapi-drift.py:262)。

实际输出仍为 `FIX: "解释器" "脚本" --write "快照"  (禁手改快照)`。我对证据中的完整原行仅作 `bash -n` 语法检查，返回 **rc=2，错误位于 `(`**；`FIX:` 也不是命令的一部分。这是原有格式问题，但与新增注释“逐字复制”的承诺不一致。

建议：将可执行命令单独输出一行，把标签和说明放到另一行；或者明确只要求复制命令部分。

**去掉标签和说明后的命令部分，静态检查通过：**

- **本机**：`:257-260` 使用仓内 venv 解释器及两个绝对路径，切换 cwd 不影响路径定位。落盘 `judge45-fix-verbatim-…txt:29-30、58-59` 记录两处均 `WROTE`、rc=0；本轮未重新执行写入。
- **CI**：`"python3"` 仍会通过 PATH 查找程序，双引号不会使回落失效。需该解释器已安装项目依赖；**CI 未实测，不能据此确认导出成功**。
- **空格**：三个参数的双引号能保护路径中的空格；只读分词检查仍得到正确的四个参数。
- **写入目标**：恒为 `BACKEND_DIR / "openapi.json"`，不使用 `snapshot_path`。旧提示也固定写 `backend/openapi.json`，因此与原先预期语义一致；本卡修正了 cwd 对路径解析的影响。

### 二、三门的有效性

**无。三门都有牙齿，没有死门。**

触发位置是 [_normalize:130-133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/scripts/spec-tools/check-openapi-drift.py:130)：将 dict 分支改为“遇到 `required` 数组先排序”，或递归传递语境、对判定为 Schema 的 `required` 排序。

| 门 | 会使其失败的具体语义 |
|---|---|
| ① 扩展数据，测试 `:269-275` | 按键名排序；按 `type/properties` 形状排序；或错误地把 Schema 语境传入 `x-*`。唯一差异被吞，`:274` 失败。 |
| ② Link 字面值，测试 `:286-292` | 按键名/形状排序；或仅凭 `requestBody` 键进入 Schema 语境。唯一差异被吞，`:291` 失败。 |
| ③ 属性名，测试 `:303-314` | 两个属性下都排序时，`:312` 失败；只豁免 `enum`、仍排序 `value` 时，`:314` 的路径断言失败。 |

第三门的细节断言确实承重：仅保留 `enum` 差异时，`assert not clean` 仍通过，但没有 `>properties>value>required`。落盘[负控记录:45](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/_bmad-output/审查/evidence-openapi-r2/negctl-three-archetype-locks-20260906T030536.txt:45)与此一致。

第四种启发式同时把 `enum/value` 当数据，两条数组都保序，所以第三门**通过**成立；记录 `:47-57` 同时显示前两新门及既有 `test_required_order_is_drift` 失败。“其余三门”指这三者。

组合覆盖对所述四种回退成立；不代表每个新门都会击中每一种排序实现。建议保留第三门的两条细节断言。负控文件未附变异源码，本轮核验是静态推导与落盘结果互证，未复跑变异。

### 三、措辞与事实一致性

**三门的定位：无问题。**  
测试 `:251-258、264-267、281-284、298-301` 及 commit message 都明确写了“回归锁”“本来就绿”“不涉及历史行为变化”。提交标题中的“修复”指向 FIX 提示，没有把三门包装成新修复。

**LOW — FIX 注释对失败原因及 CI 状态写得过实。**  
位置：[check-openapi-drift.py:254](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y5-review/scripts/spec-tools/check-openapi-drift.py:254)。

注释写“本机/CI……缺 fastapi 即 ImportError”，但 `oldstring-control-…txt:10-12` 实际记录的是缺 **structlog**；限定证据也没有 CI 实跑。

建议改成“裸解释器可能缺少项目依赖；本机旧串实测缺 structlog”，避免把未验证的 CI 原因写成事实。

### 四、零行为改动

**六处文本及 hunk：无问题。**

完整提交 diff 确认 `_normalize`、`canonicalize`、`_tag_leaf`、`VOLATILE_INFO_KEYS`、`X_GENERATOR_NAME`、`_load_drift_module` 均未改动；脚本只有一个 hunk：`@@ -250,8 +250,16 @@`。归一化行为未变，FIX 输出行为发生了预期变化。

新增 `fix_python`、`fix_interpreter`、`fix_script`、`fix_snapshot` 在已读尾段没有重名。**但 `check_drift` 前半段不在指定读取区间内，全函数作用域的重名/遮蔽未完成独立核验，不能写成已确认无。**

### 五、其它

**无。**

提交文件清单不含 `backend/openapi.json`；`judge67-diff-and-drift-…txt:1-6` 记录写入后仅时间戳变化。其当前工作区内容不在授权读取面，本轮未独立核验恢复状态。

本轮未运行 pytest、`--write` 或连接 Neo4j；“26 passed”及两次写入成功均属于已落盘证据。

BLOCKER/HIGH 清零：是

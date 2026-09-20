> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7 round-3
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r3.md)"`
> 审查绑定: 审工作区 @ HEAD=9d4f7bf0（未提交；本卡零代码, 改动面全在 `_bmad-output/`）
> 会话头自证（抄 .stderr 三行, 行号括注）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: glm-5.3` / `L9: reasoning effort: max`
---

## 结论

**BLOCKER=0 / HIGH=0 / MEDIUM=1 / LOW=3。**

r2 三项的独立复核结果：

- **H-1：闭合。** 冻结 J06 对象存在、SHA 独立复算一致，isolation v2 的 header / restore / final 均绑定该 SHA。
- **M-1：主体闭合，但“逐段 rc”语义仍弱。** matcher、提取规则、负控输入与 `changed/outside` 明细可由脚本重建；问题是打印出的 rc 不是门判定状态。
- **M-2：闭合。** `notes → sidecar → frozen SHA` 形成非循环登记层，早期 isolation/red/green 对象也在 sidecar 中如实降级为历史记录。

本轮读取面内未见路径越界或点名证据哈希漂移。

---

## 分级发现

### BLOCKER

无。

### HIGH

无。

### MEDIUM

1. **逐段 rc 是末尾输出动作的状态，不是负控门判定状态。**  
   `_bmad-output/审查/evidence-g87-journey/scripts/negctl_strengthen.sh:38-43,52-72`  
   复现思路：`classify()` 最后一行是 `echo`，A/B/C 段随后的 `rc=$?` 因此恒为 `echo` 的返回值；D 段 `diff|grep -c` 也被包在上一行 `echo` 的命令替换里，故 `outside=0`、`outside>0` 或内部 `grep` 返回 1 时仍可能打印 `rc=0`。对应输出见 `_bmad-output/审查/evidence-g87-journey/negctl-strengthen-v2-20260919T212246.txt:11,18,27,34`。

### LOW

1. **sidecar 可定位最终对象，但自身没有包内完整性锚。**  
   `_bmad-output/审查/evidence-g87-journey/manifest.json:307`；`_bmad-output/审查/evidence-g87-journey/manifest-bindings.md:15-24`  
   复现思路：修改 sidecar 中非 `manifest.json` 引用的说明文字，manifest SHA 不变、validator 也不受影响；因此该层足以“按文件名定位”，不足以证明 sidecar 自身未被替换。

2. **r3 修正版 matcher 与卡文字面 matcher 不是同一实现，历史 count 文件无法区分二者。**  
   `_bmad-output/审查/evidence-g87-journey/silent-rewrite-gate-20260919T173124.txt:1`；`P3-C.md:50`；`_bmad-output/审查/evidence-g87-journey/scripts/negctl_strengthen.sh:14-22`  
   复现思路：把 B 段对照输入 `节点/lecture 2.md` 分别送入卡文字面 `^节点/` matcher 与脚本精确 matcher，前者会放行、后者报 `outside=1`；而未授权真实输入 diff 为空，两个 matcher 都会生成同样的 `changed=0 outside=0` 存档。

3. **isolation 重跑说明会临时改写 canonical J06 对象，缺中断恢复保护。**  
   `_bmad-output/审查/evidence-g87-journey/manifest-bindings.md:43-52`  
   复现思路：按第 47/50 行改 `$M` 后、第 49/52 行恢复前中断，冻结对象即停留在单变量改写状态；本轮已有 final SHA 证明过去一次完成还原，但重跑方法本身不是 fail-closed。

---

## 逐项核对

### ⓪ 自引用排除规则与非循环绑定

**判定：PASS，带 LOW-1 限制。**

登记 `manifest-isolation-v2-*.txt` 进同一 manifest 的 artifacts 会形成不稳定依赖：

```text
M 含 H(I)
I 内容含 H(M)
H(M) 又因 M 含 H(I) 而变化
```

因此排除是合理的。当前方案是：

- manifest `notes` 只按文件名引用 sidecar：`manifest.json:307`
- sidecar 记录根 manifest 与 J06 SHA：`manifest-bindings.md:19-24`
- sidecar 明确早期 isolation/red/green 属于旧对象，不绑定当前冻结件：`manifest-bindings.md:36-38`

reviewer 仅凭包内文件可以定位最终对象：manifest note → `manifest-bindings.md` → J06 path + SHA → 当前文件复算。限制是 sidecar 自身不进入 manifest hash 账本。

### ① 冻结 SHA 是否贯穿 isolation v2

**判定：PASS。**

独立复算：

```text
J06 manifest SHA-256 =
866983aadbf9b0e0e8a91d1f917358b0058e72d4b1524b351e20344d7be092cf
```

与 sidecar 登记一致。J06 实测 `execution.commands=9`、`artifacts=19`，也与 r3 声明一致。

isolation v2 中同一 SHA 出现在：

- header / frozen SHA：`manifest-isolation-v2-20260919T212305.txt:3`
- result 改 `pass` 后 restore：`:18`
- signoff 改 `approved` 后 restore：`:33`
- final：`:40`

说明：before 段没有单独打印 `before_sha`；但 header、两次 restore、final 与当前对象复算一致，本轮不据此降级。

### ② negctl 脚本可重建性

**判定：PARTIAL——实现可重建，rc 语义未闭合。**

可重建的部分：

- 精确 whitelist matcher：`scripts/negctl_strengthen.sh:14-18`
- 修正版路径提取规则：`:20-22`
- 负控输入构造逻辑：`:24-35`
- `changed/outside` 分类：`:38-43`
- A/B/C/D 段输出：`negctl-strengthen-v2-20260919T212246.txt:6-34`
- 输入面 before/after SHA：`:3-4`
- D 段完整原文行、第 64 位 `f`、diff=0：`:29-34`

A/B/C 三类未被拦下的输入在修正版门下均得到 `outside=1`；C 段同时证明卡文字面 `awk '$3'` 对含空格路径截断。D 段证明卡文 sed 因目标字符已是 `f` 而 no-op。

未闭合点是 MEDIUM-1：当前 `rc=0` 不能作为“负控输入被捕获”的机器判据，只能看 `changed/outside` 明细。

### ③ r2 已 PASS 项是否维持

**search_notes 身份绑定：PASS。**  
`00-README.md:14` 与 `manifest.json:123-127` 均要求完整 vault 相对路径 + 内容 SHA 前 16 位，并明确不接受仅同名命中；这强于卡文原始“返回含新材料”的表述。

**环节⑤ `mastery_*` / `fsrs_*` 区分：PASS。**  
`00-README.md:16` 与 `manifest.json:137-140` 均写明仅 `mastery_*` 变化不能证明 `fsrs_bridge`；`canvas-vault/.claude/skills/quiz-answer/SKILL.md:74` 也自述 v1 不调后端熟练度链，只写本地衰减 Beta 后验。

**断点归属：PASS。**  
`03-breakpoints.md:10-13` 将 live 缺脚本、8 处 skill 差异、未部署目录归属部署/G5 面，不误记为本卡代码缺陷；`:19` 将 manifest 卡文/schema 冲突归为本卡卡文缺陷；`:24-33` 明确六环节未授权全部 `not_run`。

**未授权路径独立价值：PASS。**  
证据包仍提供 live 输入面 before/after、skill 版本双列、零改写门、manifest validator 冲突与孤立对照、断点归属和 G1-8 备料索引；不是用旧旅程结果冒充执行证据。

### ④ 新证据一致性 / 路径面

- `manifest-isolation-v2` 未进 artifacts，符合自引用排除规则。
- `negctl-strengthen-v2` SHA `d057f3…` / 2107 bytes，与 manifest 登记一致。
- `scripts/negctl_strengthen.sh` SHA `be6aa6…` / 4306 bytes，与 manifest 登记一致。
- 根 manifest SHA `ce0528…` 与 sidecar 登记一致。
- J06 19 个 artifact path 均为 `repo://_bmad-output/审查/evidence-g87-journey/...` 形式，读取面内未见 `../`、绝对路径或越出 `_bmad-output` 的路径。
- 早前 `negctl2-signoff` 的原件 SHA 不等于当前对象，但 isolation v2 `[4]` 已在当前冻结 J06 上重现 signoff 负控且仅红 signoff，因此不构成新的未归属主判据。

## 地盘核对

- 用户给出的 `git status --porcelain --no-color` 在当前 Git 中是非法选项组合；我改用 `git --no-pager status --porcelain -- . ':(exclude)_bmad-output'`，结果为空。
- `git --no-pager diff --stat --no-color 9d4f7bf0 HEAD -- . ':(exclude)_bmad-output'` 为空。
- raw status 只显示 `_bmad-output/` 下的未跟踪审查/证据件，与“改动面全在 `_bmad-output`”一致。

未重跑 validator、未执行脚本、未连任何服务；服务健康状态仍按 manifest 自述处理。

> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 · 卡 CARD-HARNESS-TREE-PARSE-REDO round-7（裁定后新增范围第 2 轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HARNESS-TREE-PARSE-REDO-r7.md)"`
> 审查绑定: `08100483..8d973a29`（该轮 HEAD）。⛔ **本轮报 HIGH 1**（import 与读 config 共用一个 try ⇒ 导入抛 OSError 时静默回退父目录），四条全部整改 ⇒ HEAD 已前进到 `4c722826`，故本轮**不绑最终 HEAD**，见 r8。
> 会话头自证（抄 .stderr 前 12 行中的三条，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

绑定 `08100483..8d973a29`；结束时 HEAD 与审查文件均未漂移。

**结论：BLOCKER 0 / HIGH 1 / MEDIUM 1 / LOW 2。**  
**“KILLED 9/9、生产代码 14 格全绿”属实，但仍存在下面的生产缺陷和覆盖缺口。**

## BLOCKER

无。

## HIGH

### H1：真实 YAML 导入发生权限错误时，会静默返回父目录

**位置：** [SKILL.md:430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:430)，返回发生于 `:442`。

**触发输入：** config 明确指向另一棵树，但已安装的 `yaml` 包源码或必需依赖不可读，导入过程抛出 `PermissionError`。

`import yaml` 和读取 config 共用一个 `try`；因此导入阶段的 `OSError` 也被解释成“没有配置”，随后返回 `dirname(vault_dir)`，绕过“PyYAML 不可用即拒写”。

已独立复现：保留真实 `SourceFileLoader` 导入流程，仅让它读取 YAML 的 pyc、源码时抛权限错误；config 指向 `/…/real-harness`，生产函数却返回 `/…` 父目录。

**动态证据止于错误选树。** 父目录若是本卡三向反例所展示的不依赖 YAML 的旧 harness，下游拒绝不能兜底；本次没有执行账本写入实验。

## MEDIUM

### M1：14 格漏掉“配置不存在且父目录是可用树”的组合

**位置：** [test_g3_2_review_ledger.py:7772](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7772)。

**触发输入：** 无 `.canvas-config.yaml`，同时 vault 父目录具有 `backend/scripts`。

当前 `no_config_file` 不造可用父树；`parent_is_a_usable_tree` 又必定写配置。因此，在缺库分支加入下面这个错误回退，**逐字执行现有门仍然 14/14 绿**：

```python
parent = os.path.dirname(vault_dir)
if not os.path.exists(_cfg_p) and os.path.isdir(
    os.path.join(parent, "backend", "scripts")
):
    return parent
```

补上两条件同时成立的输入后，两种探针都得到返回父树。**这是测试覆盖缺口；当前生产没有这段回退。原 14 格也不能因此称为恒真。**

## LOW

### L1：安装命令没有引用解释器路径，“照抄”在含空格路径下失败

**位置：** [SKILL.md:438](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/canvas-vault/.claude/skills/quiz-answer/SKILL.md:438)。

**触发输入：** `sys.executable` 为 `/Users/A B/venv/bin/python`。

消息生成的命令会被 shell 拆成 `/Users/A`、`B/venv/bin/python` 等参数，无法运行指定解释器。路径需要按 shell 参数引用。

### L2：L1/L2/L4 的措辞整改仍有残留，部分就在新增更正旁边

**位置及触发条件：**

- [UAT:510](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:510) 仍称无键老布局从“照常写入”变拒写；缺库且回退当前树的 B 格并不支持这个结论。
- [UAT:676](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:676) 仍把“宽容换不来一次成功写入”列为结构事实；指向旧树的 A 格已经证伪。
- [UAT:528](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-REDO-2026-09-14.md:528) 仍称“不变量门 12 条红”；实际是 **10 unit + 2 端到端**。`:504` 也保留“9 参数形态全部覆盖”的旧声称。
- [测试文档:7660](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/regression/test_g3_2_review_ledger.py:7660) 仍写“60 条会一起红”，与紧随其后的更正矛盾；`:7306` 新增的“到达本函数之前就把下游打死”也颠倒了调用顺序。

## 逐项复核结果

### 0–1．变异结果属实；14 格均非恒真

用文件操作的**内存适配**执行原验证逻辑，并对照逐字提取的实际 regression 门：生产加九变异体共 **140 格结果完全一致**，没有靠 `NameError` 等夹具异常误杀。

下表每行包含两种探针：

| 形状 | 实际抓住的原变异体 | 仍能照样绿的错误实现示例 |
|---|---|---|
| 无配置 | `P2-open-before-import` | 仅在无配置且父树可用时回退 |
| 目标树存在 | `R3-try-then-refuse` | 只降级读取极简配置 |
| 父树可用 | `M1-parent-is-a-tree` | 只在配置缺失时回退 |
| 极简配置 | `R1-simple-config-only`、`R3` | 只降级读取 JSON |
| 整份 JSON | `R5-json-superset` | 只降级读取普通键值行 |
| 环境变量 | `R6-env-override` | 仅在显式配置目标时采用环境变量 |
| sidecar | `R4-sidecar-cache` | 仅在配置缺失时读缓存 |

另外：

- `WM-narrow-except`：被 **7 个普通 ImportError 格**抓住。
- `WM-merge-message`：被 **全部 14 格**抓住。
- 生产代码：**14/14 绿**。

### 2．round-6 M1 的采用控制确实补回

真实 PyYAML 与逐字生产函数对 relative、值尾 U+0085、续行折叠三形态均返回预期目标树。`_disable_tree(base)` 只改名 `base/backend`，目标树各自的 `backend/scripts` 保留；前提成立。整份 flow 文档也恢复了独立的有库控制组。

### 3．第二探针有效，但只证明异常分支

它确实能区分 `ImportError` 与 `ModuleNotFoundError`，抓住 except 收窄；它没有运行真实包的导入链。

真实 loader 的 `OSError` 是 H1 所示遗漏。另外，本机 PyYAML 会自行捕获 `.cyaml` 的 `ImportError` 并继续使用纯 Python；“C 扩展错配必然向外抛普通 ImportError”的说明过宽。

### 4．固定版本与三条期望有效，均非恒真

`PIN_REV=4eeaeaa6` 确实固定了含降级解析的写点。逐字判据的接受条件是：

- A、C：仅 `rc=0` 且账本一行。
- B：任意非零 rc 且账本零行。

**自证范围只到 rc 和行数。** B 的具体拒因、mastery、`find_spec` 输出没有被断言；例如 B 被信号终止且零行也满足其判据。不能据此宣称所有因果和数值都已自动认证。

### 5–6．提取辅助有明确限制；未发现既有 22 门因本轮失效

`_extract_harness_tree()` 只复制顶层直接 import。将 `sys` 改成 `if` 或 `try` 内条件导入，已实测在 `:7541` 明确断言失败，**会误报红，但不会静默假绿**；当前生产布局满足其前提。

AST 对比确认，16 个既有门与 6 个 M 门在本轮增量中未变；结合生产控制流核对，未发现本轮造成的新恒真或失效。

本次未修改文件、未连接网络或数据库；未重跑会写盘的 pytest 和三向端到端脚本，因此不独立背书 `102 / 251 / 546` 的整套运行结果。



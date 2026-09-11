> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7a round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a.md)"`
> 审查绑定: `7aa89c5b`（送审时 HEAD）。⚠️ 本轮之后代码又改了（2 HIGH + 4 MEDIUM + 2 LOW 整改），故本存档不绑合并态；round-2 绑最终 HEAD。
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**round-1 结论：不建议通过，发现 2 项 HIGH。** 本轮仅读取指定五处材料；三份源码的 Git blob 与指定 diff 新端一致。未运行安装脚本、测试或读取 live vault；以下复现均为静态推演。

- **HIGH — 插件 `data.json` 仍被复制，旧绑定值会绕过生成与校验。** [install-vault.sh:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/install-vault.sh:106) 整目录复制后，`:138/:152` 因目标文件已存在而跳过生成；[verify_vault_install.py:751](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:751) 又剔除这些路径，旧 `backendUrl/internalApiKey/activeVaultName` 和 Templater 配置可原样保留而不报 drift。**复现思路：**源插件已有两份 `data.json`，其中填写旧绑定值，顺序检查复制及生成分支即可；现有父摘要测试未覆盖这个来源状态。

- **HIGH — E-4 默认模板源迁移没有落实到执行逻辑。** [install-vault.sh:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/install-vault.sh:59) 仍从 `.env` 的 `ACTIVE_VAULT/VAULTS_ROOT` 解析源；`--harness-tree` 仅写 YAML，未决定复制源，与清单的 harness 模板声明不一致。**复现思路：**不传 `--source`、传入另一个 `--harness-tree`，追踪 `SOURCE`，它仍指向 `.env` 所选活 vault。

- **MEDIUM — generate 摘要过滤连文件类型错误和读取失败一起隐藏。** [verify_vault_install.py:751](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:751) 在处理 `unreadable` 前过滤生成路径及全部后代；生成项自身到 `:1082` 只凭存在就记 match。**复现思路：**将目标核心插件 `data.json` 误建成含文件的目录，或设为目录项可查询但内容不可读；其他项正常时仍可得到 `unreadable=0、rc=0`，旧父摘要原本能发现这类问题。

- **MEDIUM — 新增 wiki 骨架遗漏了“内容不部署”的报告语义，也暴露出祖先覆盖判据的盲区。** [vault-install-manifest.json:326](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/vault-install-manifest.json:326) 两项只有 skeleton，没有对应内容 exclude，也不在 `extra_scan` 内；祖先被裁定为 skeleton，只能证明建目录，不能代替子项裁定。**复现思路：**合规目标多出 `wiki/concepts/x.md`，不会出现 extra、drift 或 intentionally-excluded；这与 `raw/**`、`templates/**` 的既有报告行为不一致。

- **MEDIUM — key 反向自检把比较失败也当成通过。** [install-vault.sh:185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/install-vault.sh:185) 的 `! cmp -s` 同时接受“内容不同”和“读取出错”，因此不能证明 key 未从源复制。**复现思路：**目标 key 已存在，让源 key 无法读取，`cmp` 错误退出经取反仍显示 ✅；“目标缺失可通过”符合本卡生成阶段设计，但错误态需要另判。

- **MEDIUM — `outputs/exam_boards` 的退让理由说得比代码证据宽。** [manifest-ruling.md:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-g27a/manifest-ruling.md:89) 将新增 intentionally-excluded 导致测试变红，推成只有两条改变语义的出路；加载器实际上允许 skeleton 与 exclude 重叠，该报告桶本来不计退出码。**复现思路：**保留 `outputs/**`，同时增加脚本和清单 skeleton，并精确更新相关报告期望，是尚未讨论的第三条路；这不要求本轮扩大修复范围。

- **LOW — origin 门没有验证行内容，不能支撑“全量锚定正确”。** [test_vault_install_manifest.py:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:214) 只检查起始行未越界，也不检查范围尾；清单 `:168` 的 main.js 自检说明仍指 `:121`，实际在脚本 `:183`。**复现思路：**把 `.mcp.json` 的 origin 从 `:77` 改为 `:1`，该门仍通过。

- **LOW — 一条 allowed-extra 断言确有局部弱化。** [test_vault_install_manifest.py:1323](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1323) 从精确列表改为成员包含，会容忍处理组额外出现其他 allowed-extra。**复现思路：**处理组多出一个非预期条目，该断言仍成立；不过新增五项整体门保留精确集合，不能据此说整个测试面已退化。

其余问题的核对结论：

- **optional 分类机制：核对结果：无问题，限静态控制流。** 严格检查 bool，确定缺失才进 optional-missing，查询失败仍阻断，optional 仍留在 declared。**8 个 copy 项**在位且提供 `--source` 时仍比内容；**4 个 generate 项不比内容**，所以“12 项在位都比内容”的表述不成立。
- **12 项是否都适合 optional：未能全部确认。** `settings.local.json` 和核心插件 `data.json` 是安装脚本应产出的文件，“模板树没有”不足以证明“部署目标允许没有”；目前删除它们会被放行。第三方插件是否属于必需依赖，需要消费方证据，本轮不能断言缺失必坏。
- **计数迁移：核对结果：无问题。** 独立重算得到数组 `8/6/9/4/3＝30`、双向差集为空、declared＝35、optional＝12；match＝31 的夹具算式一致。extra 探针改名、skills 内容定位及父摘要测试均保留有效负控。
- **退出复制数组：核对结果：无问题。** 四个指定退役对象均已退出对应数组；但配置和代码引用闭包未获准读取，不能确认“退役后运行无影响”。脚本 `:68` 还会拒绝已有目标，因此 `:133` 的“同目标重跑幂等”不能作为整脚本行为成立。
- **分母与 UAT：未独立核验。** 裁定表没有展开可复算的完整候选集；浅层 live 列举、祖先包含及 git 文件分母不能覆盖全部嵌套项、生成件和依赖需求。“未裁＝0”不能推出“部署无遗漏”。UAT 原件不在五处读取面内，因此 `(h)` 两跑完整期望、10✅/0❌、快捷键现场数字及四重禁写证明均不能标为已复核。

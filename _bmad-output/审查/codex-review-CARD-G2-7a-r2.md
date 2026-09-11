> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7a round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-r2.md)"`
> 审查绑定: `3c1e3c00`（送审时 HEAD）。⚠️ 本轮后又整改（1 HIGH + 3 MEDIUM + 3 LOW），故本存档不绑合并态；round-3 绑最终 HEAD。
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：0 BLOCKER / 1 HIGH / 3 MEDIUM / 3 LOW。H1 的普通目录路径已修，但新增了父目录软链误伤路径，尚不能收口。**

审查绑定 `3c1e3c00`，以下均为静态复核；未执行安装脚本、脚本片段或测试，未访问 live vault。复现思路均指隔离夹具，**本轮未实跑**。

1. **HIGH-1：新清理操作可能沿插件目录软链删除并重写源配置。**  
   [install-vault.sh:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/install-vault.sh:104) 的 `-d` 接受目录软链，`cp -R` 保留链接；随后 `:137–138` 删除其子路径，`:144/:158` 写入生成值，实际可能修改共享源的真实 `data.json`，无需并发。  
   **复现思路：**源插件目录使用指向隔离共享目录的绝对软链，共享目录预置配置；部署后检查共享配置是否被重置。

2. **MEDIUM-1：generate 普通文件不可读时仍会被记为 match。**  
   [verify_vault_install.py:1030](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1030) 的 `is_file()` 只确认类型，权限 `000` 的普通文件仍可返回 True，随后 `:1097` 记 match；`:751` 的父目录摘要过滤又跳过它。  
   **复现思路：**干净夹具中将目标插件 `data.json` 设为不可读普通文件，以普通用户验证；该项仍进 match，其他条件正常时可得 rc0。

3. **MEDIUM-2：key 自检仍未真正区分内容不同与读取错误。**  
   [install-vault.sh:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/install-vault.sh:190) 在 `-r` 后仍使用 `! cmp -s`，返回码 2 仍会变成通过；首个 `! -f` 也把目录、悬空软链当作“没有 key”。  
   **复现思路：**源 key 路径误建成可读目录、目标为可读普通文件，两侧 `-r` 成立，但 `cmp` 读目录失败仍显示 ✅。这是自检入口缺陷，不表示正常安装会自行生成这种目标。

4. **MEDIUM-3：H2 新回归门无法拦住旧 `.env` 解析实现。**  
   [test_vault_install_manifest.py:2599](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2599) 使用不存在的 `no.env`；旧逻辑此时同样回退为 `${REPO}/canvas-vault`，满足 `:2604` 的断言。  
   **复现思路：**仅还原旧解析块，此门仍通过；需要有效且指向另一位置的 `VAULTS_ROOT/ACTIVE_VAULT` 才能区分新旧行为。

5. **LOW-1：清理名单没有与生成件建立联动门。**  
   [test_vault_install_manifest.py:2558](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2558) 的陈旧值门只验证核心插件；脚本三个清理路径仍靠手工维护。  
   **复现思路：**删除 templater 的清理行，核心插件这条门仍通过，而预置的 templater 旧配置会短路其生成；未来新增嵌套 generate 同样没有自动保障。

6. **LOW-2：MANIFEST_BLOCK 已迁移，origin 仍广泛错位，区间门没有检查实际内容。**  
   [vault-install-manifest.json:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/vault-install-manifest.json:32) 的 skeleton origin 指 `:73`，实际数组在 `:71`；`:265` 指向的脚本 `:84` 是空行，mkdir 在 `:82`；生成区间 `132–171` 也没有覆盖 settings 生成结束位置。  
   **复现思路：**逐条按 origin 定位即可看到错位，但测试 `:220` 的“不越界”断言全部允许这些值。

7. **LOW-3：来源和 optional 的文字口径尚未全部收窄。**  
   [vault-install-manifest.json:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/vault-install-manifest.json:4) 仍泛称 optional 在位时比内容；[verify_vault_install.py:29](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:29) 仍写“活 vault 即模板”。  
   **复现思路：**对照新默认源赋值和 generate 分支即可确认；12 个 optional 中，确实只有 8 个 copy 参与内容比较，4 个 generate 不参与。

其余重点核对如下：

- **H1 普通目录控制流：核对结果：无问题。**所有复制均在清理之前结束，清理后没有再复制旧值的语句；末端 `data.json` 自身为软链时，`rm` 删除的是链接。manifest 有 **5 个 generate，rm 有 3 个，并非集合相等**，但当前差异合理：yaml 不复制且无条件生成；key 不复制并留到后续步骤生成；settings 已退出复制数组；两个插件配置均已清理。

- **H2 默认赋值：核对结果：无问题；既有调用方兼容性未核验。**[脚本 :22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/install-vault.sh:22) 未设 `CLS_REPO` 时指固定主仓，因此默认源是**主仓的 `canvas-vault`**，并非本 worktree；默认 `harness_tree` 则指 `feature-obsidian-hybrid-dev`。`--harness-tree` 不改变 SOURCE；只将 `CLS_REPO` 设置成本 worktree，还会把默认 WT 拼成本 worktree 下的嵌套路径。授权读取面没有 VAULT-SYNC、别名和文档的实际调用点，不能确认哪些调用方受影响，也不能证明默认源磁盘目录只含 Git 追踪件。

- **`is_file()` 的 False 分支：核对结果：无问题。**吞掉 OSError 后返回 False，会进入 unreadable/rc2，并未形成此前那种假绿；确定遗漏在 True 不代表可读。它接受指向普通文件的软链，是否允许这种形态尚需明确契约，不能仅凭“跟随软链”单独定错。

- **wiki exclude：核对结果：无问题，报告面确有扩张。**`/**` 不命中 skeleton 根本身，因此没有自指噪声；后代内容会新增 intentionally-excluded，遍历失败会新增 unreadable。树自洽门没有断言 intentionally-excluded，故它通过不能证明该桶未变化，更不能证明 `(h)` 两跑报告完全相同。

- **其余钉点：核对结果：无问题。**`71–75`、五数组精确计数 `8/6/9/4/3`、双向差集、allowed-extra 精确 `[probe]`、skills 唯一定位均保持约束。独立计算得到 **52 项＝8 skeleton＋22 copy＋5 generate＋17 exclude**。

- **裁定表三路补齐：核对结果：无问题，限文档级。**[manifest-ruling.md:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-g27a/manifest-ruling.md:94) 已说明并存可行及其代价。**UAT #9/#10、161 条测试通过记录、两跑原始结果及“未裁＝0”的底层审计记录均不在允许读取面内，本轮不能独立确认。**



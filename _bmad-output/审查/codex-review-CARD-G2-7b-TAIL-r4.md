> 批次: BATCH-2026-09-11-第十四批 · 车道 T2（card-t2-deploy） · 卡 CARD-G2-7b-TAIL round-4 prompt-r4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-TAIL-r4.md)"`
> 审查绑定: `84336ace`（Codex 正文首行自行核实为 `84336ace6de4631b30a67419200214c8634e5846`）——
> **本轮为终审轮**：绑定即最终 HEAD 的代码树，`BLOCKER = 0 / HIGH = 0` ⇒ D-15 达标。
> 剩余 MEDIUM 2（其一为 r3 已裁定「无原子原语、登记不修」的夹具竞争）+ LOW 1，按协议 §1 登记不阻断；
> 车道选择**不再改代码**的理由写在验收单 §六（只剩一轮，改动会打破刚成立的终审绑定）。
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

绑定 **`84336ace6de4631b30a67419200214c8634e5846`**。结论：**BLOCKER 0 / HIGH 0 / MEDIUM 2（含已登记保留项）/ LOW 1**。

- **BLOCKER：无。**
- **HIGH：无。**

- **MEDIUM — 回执可表示性整改仍未闭合。**  
  [scripts/deploy-vault.sh:2955](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2955) 的 `.strip()` 会删除路径末尾的空格、Tab、NBSP 等有效字符，后面的 CR/LF 判据未覆盖这些输入。  
  **核验路径：**抽出原判据，通过 `/dev/fd/0` 输入报告；令 `got=vault="/safe/mirror "`、`want="/safe/mirror"`，实际返回 **0**，目标自己作为基准未被拦下；反之，`got=want="/safe/mirror "` 时返回 **1**，正确回执被误拒。8011 分支可通过源根或目标根的安全软链形成这类物理路径；此入口条件仅做静态核对，未执行部署。

- **MEDIUM — 原 MEDIUM-4 按约定保留，未闭合。**  
  [test_deploy_vault_sh.py:5827](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5827)。  
  **核验路径：**`lstat → 身份比较 → unlink` 仍为分离操作。未找到本机公开接口中按“预期 inode”条件删除的原子原语；`unlinkat` 固定父目录，不能消除末段替换窗口。不将此项计为本轮新增。

- **LOW — 新增更正器测试没有钉住失败返回码。**  
  [test_deploy_vault_sh.py:6953](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:6953) 只检查唯一 `printf` 和成功输出。  
  **核验路径：**在内存副本的函数末尾追加 `true`，现有相关断言仍成立；部分写入对照中，原函数写入 189 字节后返回 **1**，该负控同样只写入 189 字节却返回 **0**。当前实现正确，但门未覆盖这条回归路径。

本轮其余闭合情况：

- [回执六态门:6888](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:6888) 的六组输入，抽取判据实跑得到 **0/4/4/1/2/0**；[前移负控门:6916](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:6916) 对应输入由 **0→4**，确实钉住了归一化顺序。但六组输入不等于全部返回码覆盖，缺失回执的 **3** 未纳入该门。shell 对 **0/1/2/3/4** 的承接正确；不存在路径的 `realpath` 未使本轮正常分支落空。
- [mark_unpublished:3389](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:3389) 的当前修复闭合：单条 `printf` 不保证原子写入，但部分写入失败返回非零，两处调用方据此正确区分措辞。
- [key 删除处理:2793](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2793) 闭合原 LOW：删除失败会报告残件路径。

全程只读；未运行 pytest、hook、部署入口或连接端口，未修改任何文件。

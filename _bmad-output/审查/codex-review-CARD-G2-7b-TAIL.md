> 批次: BATCH-2026-09-11-第十四批 · 车道 T2（card-t2-deploy） · 卡 CARD-G2-7b-TAIL round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-TAIL.md)"`
> 审查绑定: `70b9203a`（跑完时 HEAD 已前进到 `b0819019`，但那一步只动 `_bmad-output`，代码树对 `70b9203a` 的 diff 为空 —— Codex 自己也在正文首行核了这一点）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（第 2 行） / `model: gpt-6-astra`（第 5 行） / `reasoning effort: ultra`（第 9 行）

---

审查绑定 `70b9203a`。收尾时 HEAD 已变为 `b0819019`，但三个审查文件的 Git blob 均与绑定版本一致。

**BLOCKER**

- **临时文件目录发生字节丢失，可越过禁写面。** [scripts/deploy-vault.sh:343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:343)  
  核验路径：负控 `--env-dir=$'/Users/Heishing/.codex\n'` 通过实际路径判据，但 `dir="$(dirname "$dst")"` 丢掉末尾 LF，随后在受保护的 `.codex` 内创建并写入临时文件。无需竞争窗口；只读探针已确认检查路径与实际目录字符串分裂。

**HIGH：无。**

**MEDIUM**

- **普通目录形式的日志终路径未被拦下。** [scripts/deploy-vault.sh:1069](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1069)  
  核验路径：预置 `install-$TS.txt` 为目录 → `assert_writable_now` 放行目录 → `mv` 将随机文件移入其内部并返回成功 → 步骤仍把目录路径报为日志。旧版重定向会在执行安装前失败，属于新增回归。

- **A3 新放行的内嵌 CR 会在后续写回中破坏字段。** [scripts/deploy-vault.sh:2511](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2511)  
  核验路径：父路径 `/tmp/course\rvaults` 在 A3 比较通过，但 `:2668` 将 CR 转成 LF，把 `VAULTS_ROOT` 拆成两行；旧逻辑会在 A3 拒绝。已验证局部转换，不声称完整部署最终返回 0。

- **步 6 发布失败留下状态文案过时的临时证据。** [scripts/deploy-vault.sh:3411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:3411)、`:3425`  
  核验路径：先触发 sha／收尾失败，再令 `mv` 失败，两分支均不清理 `$otmp`；残件第六行仍写“证据已标 rc=76”，最终 emit 则写“未能发布”。矛盾位于残件；未清理控制流原已存在，本卡新增了不一致的第六行。失败测试 `:6131` 未比较完整 stdout，也未覆盖发布失败。

- **`main.js` 夹具存在并发干扰及误删路径。** [backend/tests/unit/test_deploy_vault_sh.py:5778](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5778)  
  核验路径：A 创建共享文件 → B 看到存在后直接使用 → A teardown 删除 → B 失去依赖；期间真实构建替换该文件，也会被 `:5792` 无条件删除。没有锁或删除前身份核验。

**LOW**

- **零值门仍接受前导零表示。** [scripts/deploy-vault.sh:303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:303)  
  核验路径：探针输出 `00` 或 `0000000000`、退出 0，实际函数均放行。正常 CPython 不产生这种格式，因此这是异常探针输出门的残留，不能据此认定正常硬链接检查失效。

- **helper 的具体错误原因无法传回调用方。** [scripts/deploy-vault.sh:965](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:965)  
  核验路径：`$(mk_tmp_beside …)` 在子 shell 设置 `MK_TMP_ERR`，父 shell 保持空值；五处调用均会丢失失败目录及 mktemp rc。

- **顺序门没有绑定实际负责截断的 fd 检查。** [backend/tests/unit/test_deploy_vault_sh.py:6261](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:6261)  
  核验路径：在内存副本中把部署脚本 `:1664–1665` 的实际守卫移到截断之后，门仍通过，因为同块更早出现过其他 `st_nlink`。这是测试分辨力限制，当前守卫本身仍位于正确位置。

另已核实：

- **步 4：** `_want_src` 未复用 `$src`。8011 下源、目标同路径时，局部回执判定确实接受；但直接指定 harness 的 `canvas-vault` 会先被名字不动点检查拒绝，installer 也拒绝既存目标，不能算作当前入口可达漏检。
- **写入检查：** 撤掉固定 `.tmp` 登记没有撤掉终路径硬链接检查；新目录登记也经过软链检查。普通空格及内部换行保留，BLOCKER 出在 `dirname` 输出的末尾换行。
- **返回码：** `nrc`、sha 的非零退出捕获正确；seed 包装层保留错误与返回码。正常发布时第六行、末尾 rc 与 emit 一致；首个失败后仍立即退出，只列已跑步骤。
- **测试边界：** rc75／76 负控确实调用部署入口；祖先门四组对照确实排除了规则 1–4 的提前命中。正式枚举为 24 条，不能推出所有拓扑不存在独立样本；所述另外 96 条本次未核验。A3 单字符、单侧引号均保留；引号门能拒绝去引号负控。

全程只读，未运行部署入口、pytest、hook，也未连接数据库或网络端口。

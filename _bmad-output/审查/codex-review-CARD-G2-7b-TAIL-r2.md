绑定已核实：`be2a799d1bc5221c81851386a70b370fb3cc543c`。**BLOCKER：无；HIGH：1；MEDIUM：4；LOW：无。本轮整改尚未全部闭合。**

1. **HIGH — 发布时仍可能沿终路径的目录软链写入别处。**  
   [scripts/deploy-vault.sh:1090](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1090)：`:365` 的目录检查发生在创建临时件之前，而普通 `mv` 会跟随目标位置上的目录软链。  
   **核验路径：**检查通过 → installer 运行期间把 `$ilog` 换成指向保护目录的软链 → `mv` 将临时件搬入该目录并返回成功，`:1101` 仍宣称日志已发布。五处调用存在同型窗口；预置目录已拦，发布时的目录输入未覆盖。

2. **MEDIUM — 基准回执解析不保留完整路径。**  
   [scripts/deploy-vault.sh:2930](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:2930)：逐行读取再 `.strip()`，会截断路径中的换行。  
   **核验路径：**合法 `TMPDIR=$'/safe/base\nparent'`、非 8011 端口 → 实际源与 `_want_src` 均完整，但 `got` 只剩 `/safe/base`，正常部署被误判为 rc 74。另有回执未拦下的负控：8011 分支将 `src` 改为目标，目标经安全祖先软链解析成 `<harness>/canvas-vault<LF>/probe_x`，解析所得前缀恰等 `_want_src`；内存探针确认回执判据返回 0，未执行部署入口验证。

3. **MEDIUM — 发布失败后的残件仍保留成功状态及 `rc=0`。**  
   [scripts/deploy-vault.sh:3477](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:3477)：先写 `rc=0`，随后 `mv` 失败时只追加“报告落点不成立”，没有更正成功状态或返回码。  
   **核验路径：**SHA 等前置计算成功 → 写入第六行 `OK` 和 `rc=0` → `mv` 失败 → 入口返回 76；即使标注成功，残件也不满足第六行及 rc 与实际结果一致。

4. **MEDIUM — 更正失败仍被报告为“已标注”。**  
   [scripts/deploy-vault.sh:3343](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:3343)：`mark_unpublished` 吞掉追加错误，但 `:3458`、`:3473` 无条件声称标注已写入。  
   **核验路径：**正文写成后发生空间耗尽或残件不可追加 → 发布及更正失败 → 终端仍称“已在其尾部标注未发布”。五处分支确实都调用了 helper；测试只数调用次数，未覆盖更正失败。

5. **MEDIUM — 测试夹具仍未取得文件所有权。**  
   [backend/tests/unit/test_deploy_vault_sh.py:5801](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5801)：内容比较与删除分离，不能保证删除的还是读取过的对象。  
   **核验路径：**读取桩并得到相等 → 构建替换 `main.js` → `unlink` 删除新产物。另一个无需并发的负控是预置悬空软链：`:5786` 的 `exists()` 返回假，`:5796` 沿链写目标，收尾删除软链却留下外部文件。声明不支持并行没有闭合这些路径。

其余核对结论：

- round-2 的父目录参数展开、A3 内嵌 CR 拒绝、全零链接数、helper stderr 诊断均已闭合；顺序门按“登记限制、不增强”的要求完成。
- 五个临时件调用均传入含 `/` 的绝对路径；真实随机文件名使父目录中的空白、换行不会被命令替换截掉。
- 撤掉固定 `.tmp` 登记没有撤掉终路径硬链接检查。目录软链检查仍受尾斜杠影响：`-L /tmp` 与 `-L /tmp/` 不等价。
- `SEED_ERR`、`SEED_TMP` 生命周期及返回码传递正确；清理是尽力而为，不能保证所有失败残件都删除。
- `_want_src` 未复用 `$src`。8011 且目标就是源本体时，局部回执允许相等，但真实入口会更早因目标已存在而停止。
- 发布成功的各类步 6 失败分支，状态与 rc 一致；前五步失败仍只输出已跑步骤。
- ancestor 两跑样本确实绕开规则 1–4；结论只能覆盖已枚举样本，不能证明普遍覆盖关系。

全程未修改文件，未跑 pytest、hook、部署入口或连接服务；完成了静态复核、语法检查及零文件写入的语义探针。



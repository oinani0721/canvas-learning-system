# 独立复核请求 — CARD-G2-6（vault 部署清单 + 只读校验器）

## 一 背景与最小读取面

Canvas Learning System 用 `scripts/install-vault.sh` 从「当前活 vault」复制系统件到新
vault（脚本头注 `:2-6`：活 vault 即模板，不维护第二份模板）。部署边界原本只存在于该脚本
`:61-69` 的五个 shell 数组里，其他语言读不到、也无法拿它去检查一个已存在的 vault。

本卡把那份边界升格为带版本的 JSON 清单，并配一只**只读**校验器，另把脚本 `:16` 的硬编码
仓根改成可用环境变量覆盖（缺省值不变）。本卡**不**改部署行为本身。

请只读下列文件（绝对路径），不需要读别处：

1. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json`
2. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py`
3. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/unit/test_vault_install_manifest.py`
4. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/install-vault.sh`
   （只需 `:1-20`、`:61-69`、`:74-109` 三段）
5. `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/_bmad-output/审查/evidence-g26/live-diff.txt`
   （校验器对现网 vault 跑出的报告）

`.claude/skills/deploy-vault/SKILL.md` 本卡**未改动**（见问题 ④ 的说明），无需读取。

## 二 作者自述（请独立核对，不要采信）

- **覆盖等价**：manifest 里 `action ∈ {copy, skeleton}` 的 27 个 path，声称与 `:63-67`
  五个数组按各自前缀（`.claude/`、`.obsidian/`、`.obsidian/plugins/`、根级）展开后的并集
  逐项相等；另有 8 条 `exclude`、1 条 `generate`，共 36 项。
- **只读**：校验器声称对 `--vault` / `--source` 只做 stat / 列目录 / 读字节，唯一的写是把
  报告落到 `--report`，且 `--report` 落在这两棵树里时直接退出 2。
- **`:16` 缺省不变**：改成 `REPO="${CLS_REPO:-<原字面>}"` 后，不设该变量时求值结果与改动前
  逐字节相同（作者实测 IDENTICAL），且 diff 只有 `:16` 一行、MANIFEST 区行号未漂移。
- **live 结果**：对现网 vault 跑出 `match 28 / missing 0 / extra 5 / intentionally-excluded 8`，
  退出码 1。作者认为 `extra 5` 是预期（现网确有清单外的插件与缓存），不是缺陷。
- **退出码三档**：0 = 无 missing/extra/content-drift；1 = 有；2 = 用法或配置错。
  `intentionally-excluded` 只报告，不进退出码。

## 三 请回答的问题（按重要性排序）

① **manifest 与脚本是否逐项等价**：`:63-67` 五数组的 27 项是否全部、且只有这些进了
   `copy`/`skeleton`？`:84`（`find "$TARGET/.claude" -type d -name __pycache__` 剪除）与
   `:86`（`rm -f pending_archives*.jsonl`）这两条隐含的排除语义、以及 `:103-109` 生成
   `.canvas-config.yaml` 的语义，在 manifest 里是否被如实表达？特别请判断
   `.claude/**/__pycache__` 这个模式的作用面与脚本 `:84` 的实际作用面是否一致。
   另：`.canvas-config.yaml` 在 `:69` 被列为「不复制」、在 `:103-109` 又被生成，manifest 把它
   记成单独一条 `generate`（而非同时记一条 `exclude`），这样表达是否丢失了信息？

② **校验器是否真的没有写目标树的路径**：请通读 `verify_vault_install.py`，判断是否存在
   任何会修改 `--vault` 或 `--source` 的分支，包括间接的（报告落点、`__pycache__` 落盘、
   临时文件、目录创建）。测试用 AST 数写操作调用来把关这一点，请判断该判据是否有盲区。

③ **密钥件处置**：`.claude/settings.local.json` 与 `.obsidian/cls-internal-key.txt` 在
   manifest 里只应以路径 + `role: secret-or-local` + 说明出现，不得带任何内容或摘要。
   请核对是否如此。（这两个文件本身不在读取面内，也不需要读它们。）

④ **`:16` 改动的影响面**：不设 `CLS_REPO` 时缺省值是否逐字节不变？`:17-19` 由 `REPO` 派生的
   三个变量、以及 `:51-55` 那段从 `.env` 解析模板源的逻辑，是否受这次改动影响？
   本卡对 `SKILL.md:31`（里面写着一条绝对路径的脚本调用）选择**不改、只登记转交下一张卡**，
   理由是该 skill 只是薄壳、路径收敛应与下一卡的 CLI 化一并做。请评价这个取舍是否合理，
   以及不改是否会造成本卡内部的不一致。

⑤ **四类差异的反例是否各自独立承重**：测试对 missing / extra / content-drift /
   intentionally-excluded 各有反例，声称「一次只打一类」。作者另做了一轮验证：逐个把校验器里
   某一类的分类逻辑临时置为不生效，观察是否恰好是对应的那几条测试变红、其余保持绿
   （结果：5 个变异全部「恰好命中」，且每轮结束后文件摘要复原）。请判断：这些反例是否可能
   被别的分类逻辑兜住而并非真正由自己那段逻辑承重；测试里的期望集合是否写得过松或过紧。

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条写：**结论一句** + **依据（文件:行）** +
**若要修的话改哪里**。没有问题的分级请显式写「无」。最后给一段总评，说明你实际核对了哪些
断言、哪些因读取面限制未能核对。

## 五 边界

- 不评价下一张卡的范围：把五个部署动作做成 CLI（G2-7）、激活的事务与回滚（G2-8）。
- 不评价 `install-vault.sh` 现行会复制那两个密钥件这一行为本身——本卡只做登记，改动归 G2-7。
- 不需要运行 `install-vault.sh`（真跑会创建目录并可能改 `.env`）。
- 现网 vault 报告里的 5 个 `extra` 项应否补进 manifest，本卡未作裁定，不必替我们裁。

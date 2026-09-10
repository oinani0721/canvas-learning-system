> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-RV-G2-6 round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-G2-6-r6.md)"`
> 审查绑定: `8fb59bd2`（审查者注明实测工作区 HEAD 为 `7f98794c`，两者代码面 diff 为空——后者只多一个 prompt 文档 commit）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

> ⚠️ **本轮超协议轮次上限（第 6 轮）**，理由见验收单同名段：协议 §1 给的是流程出口，
> 卡文完成条件给的是验收标准（HIGH=0），停止条件复核指出后者未满足。轮次合规性不自行豁免。
> 结果 **0 BLOCKER / 1 HIGH / 5 MEDIUM / 2 LOW**：原 H1/H2 均确认已修，但旧 M2 升级为 HIGH。

---

**绑定 `8fb59bd2`：0 BLOCKER / 1 HIGH / 5 MEDIUM / 2 LOW。仍不满足 B/H=0。** 原 H1 的权限失败场景和原 H2 均已修；但旧 M2 的三态消费缺口，在一组加载器接受的配置下仍可返回 0，需升为 HIGH。

实测工作区当前 HEAD 是 `7f98794c`；以下结论只覆盖指定的 `8fb59bd2`。本轮为源码核对与纯内存计算，未执行安装、测试夹具或访问 live vault；未独立核验“2/2 KILLED”。

**BLOCKER**

核对结果：无问题。限定于指定读取面的审查，未发现阻断级缺陷。

**HIGH**

- **H1〔旧 M2 升级〕：extra 消费端丢失类型查询失败，可最终假绿。** [verify_vault_install.py:1173](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1173) 未传 `unreadable`，随后 `:1226` 可把条目放入白名单。
  
  复现思路：仅声明 `exclude="alias/*json", kind=file`、`extra_allow=["alias/f*"]`、扫描 `alias/*`；`alias` 是指向可读目录的软链，其中 `f.json` 又链接到不可搜索目录里的文件。exclude 遍历不跟随末级 `alias`，没有登记失败；extra 遍历跟随它，却丢掉 `_kind_ok=None`，最终得到 `allowed-extra`、阻断桶全空、rc=0。
  
  **这是静态可达推演，未运行夹具。** 纯内存核对确认上述 glob 组合能通过现有重叠判定。虽然利用了已登记的 glob 交叉边界，但单独补齐 extra 的失败传播即可阻断，因此不能仅按“误报 extra”保留 MEDIUM。

**MEDIUM**

- **M1〔本轮扩大〕：确实不存在的精确 `exclude + kind=file` 现在也被误阻断。** [verify_vault_install.py:658](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:658) 在 `state="absent"` 后仍查询类型，而 `_resolved_kind` 把 ENOENT/ENOTDIR 都归入 unreadable。复现思路：空目标目录，仅声明不存在的 `x` 为该类 exclude，`extra_scan=[]`；预期 rc=0，实际代码路径得到 unreadable、rc=2。

- **M3：目录不可列举时，仅跳过目录自身 key，对侧子孙仍参与摘要，误报 drift。** [verify_vault_install.py:838](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:838)。复现思路：两侧内容相同，仅一侧子目录不可列举；对侧子文件未被 skip，摘要不同。已做纯内存 `_fold` 对照确认。

- **M4：skip 同时抹掉已知类型差异，漏报 drift。** [verify_vault_install.py:1125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1125)。复现思路：同一路径一侧为不可读普通文件，另一侧为空目录；共同 skip 后摘要相等。纯内存对照成立，但仍有 unreadable、rc=2，且不会记 match。

- **M5：skeleton 的解引用失败仍被说成“不是目录”，降为 missing。** [verify_vault_install.py:1071](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1071)。复现思路：骨架路径链接到不可搜索目录内部的真实目录；`lstat` 成功，`is_dir()` 失败后进入 missing，可能只返回 1。

- **M6：“全链已 fail-closed，最坏多拒一次”仍超出证据。** [review-c4e6b165.md:274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md:274)。复现思路：追踪 `_fs_identity` 查询失败后的 `None` 被略过，以及 `target.is_dir()` 失败未登记 failures；只能证明**已登记的扫描失败会拒写**，不能证明所有失败都已登记。本轮未实证写穿。

**LOW**

- **L1：十叶子门仍不能证明“任何新的有损写法都会变红”。** [test_vault_install_manifest.py:1913](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1913)。复现思路：按现有样本纯内存替换编码策略，`ignore`、`replace` 均仍为 10/10 不同摘要；`backslashreplace` 才降为 9/10。

- **L2：无缓冲 `--help` 断管的退出码差异仍缺回归门。** [test_vault_install_manifest.py:2137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:2137)。复现思路：关闭 stdout 后比较默认缓冲与 `-u --help`；现有断管参数未覆盖 help。**保留 r5 登记，本轮未复跑该运行时现象。**

其余核对结果：

- **`dir/nondir`：核对结果：无问题，限稳定状态。** [verify_vault_install.py:593](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:593) 的内层“真目录”表达式对末级软链始终为 False，故 `dir=False`、`nondir=True`。你的论证在这个范围成立；但它仍先执行跟随查询，不能宣称已消除多次查询间状态变化或瞬时错误的边界。
- **主要 None 传播：核对结果：无问题，最终 extra 消费端除外。** `matches_exact`、`is_under_exclusion`、`hits_for` 通过失败列表传递信息，exclude 分类和摘要消费端会登记并阻断；它们本身返回 bool/list，并非返回三态。缺口就是上述 HIGH。
- **H2：核对结果：无问题。** [verify_vault_install.py:719](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:719) 同时覆盖字符、块设备的类型与 `st_rdev`。FIFO/socket 按类型比较符合部署结构口径；同类不同端点、同设备号不同节点仍可同摘要，不能据此宣称 inode、权限或运行状态一致。新增门只直接证明 `/dev/null` 与 `/dev/zero` 这一对字符设备的 helper 摘要不同。

优先顺序建议：**旧 M2 升级的 HIGH → M1 → M5 → M3/M4**；M6 的文字立即收窄，LOW 中先补摘要门。H1 新门的 `path=="x"` 断言确实针对原缺陷，但尚未证明缺失路径对照和 extra 完整传播；“两门通过”不能扩大成“整条三态链已闭合”。

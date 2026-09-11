> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-RV-G2-6 round-7
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RV-G2-6-r7.md)"`
> 审查绑定: `fd7e91f3`（审查者注明核对时分支 HEAD 已是 `461b559a`，但**校验器、门文件、定性表与 `fd7e91f3` 均无差异**——后者只多一个 prompt 文档 commit）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

> ✅ **D-15 终止条件满足**：**0 BLOCKER / 0 HIGH**（原文「未确认 BLOCKER / HIGH」「无确认遗留 HIGH」），
> H1（kind=file 三态）与 H2（st_rdev）均**确认已修**。7 MEDIUM / 3 LOW 按协议 §1 登记不阻断。
> ⚠️ 本卡共 7 轮，**超协议轮次上限 5**——理由与边界见验收单「round-6」段，轮次合规性不自行豁免。

---

本轮**未确认 BLOCKER / HIGH**，但不能宣称“三态已全链闭合”：仍有 **7 MEDIUM / 3 LOW**，其中两项仅达到内存故障注入证据级。

结论绑定 `fd7e91f3` 的指定材料。核对时分支 HEAD 已是 **`461b559a`**；校验器、门文件、定性表与 `fd7e91f3` 均无差异。未运行安装脚本、读取 live vault 或执行完整测试；你报告的 **3/3 KILLED 未独立重跑**。

以下 `V` 指 `scripts/verify_vault_install.py`，`T` 指门文件，`R` 指指定定性表。

**BLOCKER**

核对结果：无问题。程度限于指定材料的静态审查；未执行报告写入路径，不据此证明所有禁写边界。

**HIGH**

核对结果：**两条已知 HIGH 的原始形态已修补，无确认遗留 HIGH。**

- **H1：** `kind=file` 查询失败现在产生 `None`；精确 exclude 经 `hits_for → verify` 登记，末级 extra 经新增分支登记并跳过两个桶。已核对源码传播与关键函数内存行为，未重跑磁盘夹具。
- **H2：** [V:725](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:725) 纳入 `st_rdev`，消除了同类型、不同设备号的已知碰撞。FIFO/socket 只比类型，在当前“内容与形态”契约下**无问题**；它们的运行状态、端点身份不在比较范围内。同型 FIFO/socket、同设备号的不同设备节点仍可同摘要，不能宣称“不同对象均不碰撞”，也不应要求复制两端 inode 相同。

**MEDIUM**

1. **`absent` 修复仍不完整：悬空链目标和缺失扫描根继续被误报 unreadable。** [V:565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:565)、[V:1200](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1200)。复现：精确 `exclude + kind=file` 指向悬空链，链自身为 present，绕过新增短路；或令 `extra_scan.dir` 确定不存在，两者仍进入 unreadable、rc=2。旧 M1 的同根残留，ENOENT/ENOTDIR 都应区分。

2. **extra 只消费末级路径的错误，祖先错误仍会漏掉。** [V:647](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:647)、[V:1236](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1236)。复现：内存注入祖先 `a` 判型为 None，查询 `a/b` 实得 `excluded=False、unreadable=['a']`，随后 `"a/b" in kind_unreadable` 为 False。**已证传播缺口，未证明真实文件系统最终假绿，故不升 HIGH。**

3. **`dir/nondir` 仍有第二次查询吞错通道。** [V:594](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:594)、[V:609](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:609)，同形入口还有 V:543。复现：内存注入“lstat 成功取得真目录类型，随后 stat 抛 EIO”，得到 `dir=False、nondir=True`，没有产生 None。你的论证对**稳定的末级软链、谓词正常返回布尔值**成立；它不能证明额外查询无风险。此项同样尚未实证最终假绿。

4. **旧 M5：骨架链目标查不到，仍被说成“不是目录”。** [V:1077](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1077)。复现：仅声明 skeleton `x`，让其指向不可搜索目录中的目录，清空其他扫描面；进入 missing，得到 rc=1，而应登记 unreadable。

5. **旧 M3：不可列举目录只跳自身 key，对侧子孙仍参与摘要，误报 drift。** [V:844](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:844)。复现：两侧 `copy/d/f` 内容相同，一侧 `d` 不可列举，`skip={'copy/d'}`；实际 `_fold` 内存对照仍不等。

6. **旧 M4：skip 同时抹掉已经可确认的类型差异。** [V:1131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1131)。复现：`copy/d` 一侧为不可读普通文件，另一侧为空目录，双方跳过该 key 后摘要相等，漏报类型漂移；unreadable 仍阻断，未变成 rc=0。

7. **旧 M6：“禁写链已 fail-closed、最坏多拒一次”仍比证据宽。** [R:133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/_bmad-output/审查/evidence-rv-g26/review-c4e6b165.md:133)，同表 :275、:337。复现思路：沿 V:909 的类型查询、V:1499 的身份查询失败，检查是否都进入 V:1524 使用的 `scan_failures`；源码没有这个保证。**本轮未实证写穿，也不能反向证明只会多拒绝。**

**LOW**

1. **旧 L1：十叶子门仍抓不到 `ignore/replace` 退化。** [T:1913](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:1913)。复现：本轮按门内六个链接目标做内存编码比较，两种策略下仍各自互异，其余类型标签也不会补足碰撞；“新的有损写法只要出现就会红”仍不成立。

2. **旧 L2：`--help` 断管退出码仍随缓冲模式变化。** [V:1644](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/verify_vault_install.py:1644)。复现：预先关闭 stdout 管道读端，仅运行校验器 `--help`；本轮实测默认缓冲 **rc=3**，`-u` **rc=0**。

3. **新 extra 门未完整锁住“两桶都不进”的承诺。** [T:3208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_vault_install_manifest.py:3208)。复现思路：变异为“登记 unreadable，同时把 `alias/f.json` 放进 extra”，现有断言仍可通过；它也没锁 unreadable 的精确路径。

对问题 2 的直接回答是：**matcher 内部用列表承载 None，`hits_for → verify` 已到位，摘要侧也消费该列表；extra 末级到位、祖先未完整到位。**

遗留项优先级建议：**M6 先收窄声明并独立核验禁写边界；运行行为先 M5、M1，再一起处理 M3/M4；测试先 L1，L2 最后。** 旧 M2 的原始末级形态已修，祖先边界见上文。

其余声明也应限定：`st_rdev` 证明设备类型与设备号相同；三个指定变异被杀不能证明所有分类承诺；V:38 的“重叠即拒绝”还应保留 V:450 所述“仅字面近似、未计算 glob 交集”的限制。

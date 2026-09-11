> 批次: BATCH-2026-09-07-第十三批 · 车道 U10（card-u10-red-a） · 卡 CARD-RED-A1-auth round-5（末轮，轮次上限）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RED-A1-auth-r5.md)"`
> 审查绑定: `7004a365..385078b8`（最终 HEAD；本轮后仅有 `_bmad-output` 侧整改，协议 §1 的绑定判据排除该目录，绑定不失效）
> 会话头自证（抄 .stderr 的 workdir / model / provider / reasoning effort 行，stderr 本身不入库）:
> `provider: openai`
> `approval: on-request`
> `sandbox: read-only`
> `session id: 01a084e7-f54a-7f33-8ca6-92559677d5b9`

---

绑定 **`7004a365..385078b8`**，HEAD 已核实。全程只读，未重跑 pytest。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：无。**

**LOW：4 条，均为说明准确性问题。**

1. **目标总述仍超出实际完成范围。**  
   位置：[UAT:12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-auth-2026-09-09.md:12)、同文件 `:297`。

   “让检查真正查到它该查的地方”“本卡只把请求送进业务层”仍笼统涵盖全部 37 条。但 `second-layer:75–76` 明确五条仍停于 409，`:20–24` 另区分了输入校验和提前返回。“从来没进过屋”也超出了开工存档能够证明的历史范围。

   **建议：**统一为“开工时 37 条被鉴权阻挡；本卡解除该阻挡，32 条恢复预期校验或业务路径，五条仍因 active-vault 前提返回 409，按分工移交”。

2. **“15 条解开鉴权即绿”漏掉了同期加入的 sync 两桩。**  
   位置：[second-layer:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt:17)、[UAT:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-auth-2026-09-09.md:102)。

   `second-layer:8` 明写该阶段为“authed_client + sync 两桩后”；那 15 条包含 `:44–49` 的六条 sync。sync fixture 的 `:83–86` 又明确：不适配 active vault，六条都会停在 409。因此，存档支持的是组合改动后的结果，不能全部归因于鉴权解除。

   **建议：**改为“完成 authed_client 迁移及 sync 两桩后，15 条转绿”。

3. **Settings 的一致范围收窄过度。**  
   位置：[test_sync_exception_classification.py:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/test_sync_exception_classification.py:57)。

   “**只在鉴权相关字段上一致**”“等其余字段并不相同”不准确。本文件 `:63/:65/:67` 与 `authed_client.py:80/:82/:84` 的 `VERSION`、`LOG_LEVEL`、`CANVAS_BASE_PATH` 也分别相同。

   **建议：**改为“鉴权相关字段一致；PROJECT_NAME 与 CORS_ORIGINS 不同，因此整份 Settings 并不等价”。

4. **耗时归因强于证据，且部分与日志相反。**  
   位置：[second-layer:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/second-layer-20260909T134842.txt:124)、同文件 `:125`；相关 [UAT:308](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-auth-2026-09-09.md:308)。

   此处称 `1.07s→57s→96s`“反映了这条真连的超时等待”。但 [four-mid2:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-red-a1-auth/four-mid2-20260909T133815.txt:21) 至 `:30` 显示 MemoryService 初始化仅约 **2 ms**，`:35` 的整个请求仅 **128.12 ms**。这次被拦连接不能解释几十秒耗时。剩余时间“属 search_supplementary 既有慢，非本卡引入”的定论，也比 UAT 自承的“未证明全部来源、初判”更强。

   **建议：**删除连接超时归因；保留耗时观测，将剩余来源标为待确认。“非本卡引入”限定为“本卡未修改相关生产代码”。

**r4 LOW 已落实。** [UAT:325](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-RED-A1-auth-2026-09-09.md:325) 已改为 `test_sync_exception_classification.py::_dev_settings`，没有引入执行问题。整改历史中引用的旧行号，沿用 r4 的口径，不算当前定位漏改。

总评：**满足无 BLOCKER/HIGH 的停轮条件，本轮可以结束。** 解除 37 条鉴权阻挡、恢复其中 32 条预期执行的目标成立；“37 条业务断言全部跑到业务层”仍不成立。五条按分工移交的决定成立，未发现新增假绿或把失败转嫁给其他测试；耗时来源仍未闭合，不能据此宣称没有性能影响。



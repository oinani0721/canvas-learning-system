# UAT — CARD-DEBT-openapi-sync-R1「OpenAPI 漂移门重排」

> 批次 `[BATCH-2026-09-04-第十批 / CARD-DEBT-openapi-sync-R1]`
> 车道 `card/x8-openapi`（从主干 `bce2986a` 切）· 只读取证源 `card-w4-micro @f3333328`
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十批-goals/X8.md`（v2）
> 白名单移植面 = `git diff 2fb779b3^ f3333328` 的 15 文件 减 2 个 `*.stderr-redacted.txt` = **13 文件**

---

## 待你裁决（4 项，卡文 §一 (a)）

**裁决状态：未裁。** 开跑手册 §三 X8 块上方「用户裁决记录」为空
（`#0 ＿ / #1 ＿ / #2 ＿ / #3 ＿`，2026-09-05 实读）。

本车道**按卡文 §四 的默认裁决执行**，理由与代价见下表「若你推翻」列。
默认裁决不是「已获批准」——它只是让车道不空转；每项的回退成本都写在表里，
你事后推翻任何一项都不需要重跑这张卡。

| # | 决策 | 现状（为什么要裁） | 选项 | 默认 | 若你推翻 |
|---|---|---|---|---|---|
| **0** | 停轮状态下怎么合并 | round-3 终裁是 **FAIL**：2 BLOCKER + 1 HIGH + 1 MEDIUM。整改压在 `66017721`（把 `_normalize` 里的 required 排序**整个删掉**，-73 行），**没经过第四轮确认**。 | **甲** 接受现状认账「移除 required 排序」<br>**乙** 排第四轮 Codex 确认 2B+1H 清零<br>**丙** 降级只收路径修正 | **乙** | 选**甲**：删掉本卡产出的 round-4 Codex 两个文件即可，代码零改动（甲乙的落地产物**完全相同**）。<br>选**丙**：需 revert 打包 commit，重挑「只收路径修正」的子集——本卡是唯一需要重做的选项。 |
| **1** | 删 `api-spec-sync.yml` 的 `update-spec` job | 该 job 在 `push && main` 时自动 `git push \|\| true` 回写 spec。`\|\| true` 让它失败也不出声；且本仓从不直接 push main。**可证从未生效**。 | 删 / 留 | **批（删）** | 从本卡 commit 里 revert 该 hunk，job 原样回来。 |
| **2** | Dredd 契约测试改 `if: false` | Dredd job 需要 `npm install -g dredd` + 起服务，长期红。停用后 **CI 侧契约覆盖归零**（schemathesis 的 `test_openapi_contract.py` 没进 `test.yml` 白名单，只在本机 importorskip 跑）。 | 停用 / 留着红 | **批（停用）**<br>+ 同批登记「Dredd 复活/退役」独立候选卡 | 把 `if: false` 改回原样即可。⚠️ 无论你怎么裁，**契约覆盖归零这件事需要一张独立的卡**，本卡只负责登记它。 |
| **3** | lefthook `spec-sync` 出声化 | 现在这个 hook **死了 4 个月没人发现**：解析器是裸 `python`（不是本仓 venv）、`2>/dev/null` 吞掉全部失败、检查的 `openapi.json` 在**仓库根**（那个文件在本仓全部历史里都不存在）。三处任一都足以让它静默空转。 | 修 / 留 | **批（修）** | revert 本卡的 `lefthook.yml` hunk。 |

**#3 的已知代价（批了就会遇到，先说清楚）：**

1. 每次改 `backend/app/{api,models,schemas,mcp}/*.py` 或 `main.py`/`config.py` 的 commit，
   会多花约 **20 秒**导入 `app.main` 重生成快照。
2. 快照里有一个恒变的时间戳字段，所以 **`backend/openapi.json` 会必然出现在这类 commit 的 diff 里**。
3. 导出失败会 **阻断本地 commit**（这正是「出声」的含义——以前它失败和成功长得一模一样）。

---

> 以下章节在后续 commit 中补全（(b) 打包 → (i′) 快照重生成 → 裁判 1-7 → Codex round-4）。

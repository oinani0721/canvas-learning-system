# CARD-G5-9 round-3 发现处置表

> **上游**: `codex-review-CARD-G5-9-round3-T2车道.md`（BLOCKER 0 / HIGH 4 / MEDIUM 2 / LOW 2，裁决「仍有实现级缺陷」）
> **处置卡**: BATCH-2026-08-29-第六批 / CARD-收口A ③（卡文要求的「修复后再跑一轮」）
> **停轮规则**: BLOCKER 或 HIGH > 0 → 再一轮；MEDIUM / LOW → 登记结案。
> ⇒ HIGH 4 > 0，**已全部整改**（均落在 `recap_exam_build.py`，不涉及本批禁改的 `recap_scan.py` verifier）。

---

## 一、这 4 条 HIGH 的共同成因（值得先说）

round-3 确认前两段的**主路径修复全部到位**（4 项题定校验 PASS、承重 10/10、回归 160 passed）。
新发现的 4 条全部落在**失败路径与竞态窗口**上，原因是：

> **每加一道检查，就新增一条「它自己失败时」的路径。**

最典型的是 HIGH-2：我为了修「发布字节未校验」加了**发布后回读**，
却没想过**回读本身抛 EIO/EMFILE 时**会掉进统一错误分支——那里只删 tmp，
**把已经发布的 target 留在 vault 里**，回执却报「原子写失败」。
加固动作本身制造了新的不一致面。这是加固工作的固有代价，只能靠逐条审失败分支来收。

---

## 二、逐条处置

| # | 发现 | 整改 | 承重变体 |
|---|---|---|---|
| **HIGH-1** | `_open_exam_dirfd` 只在**打开那一刻**做一次 inode 快照。校验通过后若把 `检验白板/` rename 到 vault **外**（同一文件系统），dfd 仍指向已外移的 inode ⇒ 写入真的落在 vault 外，回执却按词法路径报 `created: true` | 新增 `_dirfd_still_in_vault()`：**写入完成后再核一次**「`vault/检验白板` 现在解析出的 inode 是否仍等于 dfd 的 inode」。检出则撤销已发布文件并 `exit 2`。⚠️ 这是**事后检测不是事前阻止**（POSIX 无「把 inode 钉在父目录里」的原语），docstring 已如实声明残留窗口 | **K** |
| **HIGH-2** | `os.link` 成功即已发布；此后回读抛 `EMFILE`/`EIO` 会掉进统一 except，那里**只删 tmp**、留下 target 却回报失败 | 引入显式 `published` 状态，失败路径据此**撤销自己的发布**；撤销失败并入错误消息（不吞） | **L** |
| **HIGH-3** | 回滚用的 `same_inode` 是**已过时的快照**——期间路径被换入他人文件时按 basename 删会**误删**；且 unlink 失败被静默吞掉 ⇒ 错误字节的 target 留存而回执只报失败 | 抽出 `_rollback_published()`：紧贴 unlink 前**再 lstat 一次**核 identity（可选再核内容 SHA），任一不符 **不删**；失败**如实回报**给调用方写进回执 | **M** |
| **HIGH-4** | `_fsync_dir` 吞掉 open/fsync 全部错误并返回 `None`，调用方无从分辨成败 ⇒ undo 会在**留痕目录项未持久化**时继续删源，崩溃模型下**两端皆失** | `_fsync_dir` 改为返回失败原因；undo 侧 **fail-closed**（拒绝回退、原文件原样保留）。⚠️ 诚实边界：部分 FS 对目录 fd 的 fsync 返回 `EINVAL/ENOTSUP`，那是「不支持」不是「失败」，已显式区分，避免在正常 FS 上误拒 | **N** |
| **MEDIUM-5** | `_atomic_write` 失败路径静默吞掉 tmp 清理错误 ⇒ 残留会阻断后续同 ts 的 `O_EXCL` 重试，而用户拿不到线索 | 并入错误消息如实回报（含「下次同 ts 会被拒，请手动删除」） | 随 L 覆盖 |
| **LOW-8** | `_atomic_write` 返回类型注解写 `str \| None`，实际返回二元组 | 改为 `tuple[str \| None, str \| None]` | — |

### 登记结案（按停轮规则不再开轮）

| # | 发现 | 结案理由 |
|---|---|---|
| MEDIUM-6 | undo 两处源回读的 `fstat/read` 抛 `OSError` 时直接外抛，不按 JSON 契约回报 | **源不会被删**（复核者已确认），只是回执形态不统一。属**契约一致性**而非数据风险；改它要动 undo 的整体异常包装，与本轮四条 HIGH 不同域 ⇒ 移交 |
| LOW-7 | `fdopen(closefd=False)` 而外围只捕 `OSError`，非 `OSError` 异常可能泄漏 tmp fd | 复核者明确「正常及常规 `OSError` 路径未见泄漏」。触发需非 OSError 异常（如 MemoryError），概率与影响均低 ⇒ 移交 |

---

## 三、判据

| 项 | 结果 |
|---|---:|
| `test_g5_9_recap_exam.py` | 55 → **62 passed**（三段 +7 门） |
| S6 完整裁判（`test_recap_scan_signals.py` + `test_g5_9_recap_exam.py`） | **167 passed**（裁定书基线 138 → 160 → 167） |
| 负验证（扩至 **14 变体**） | **14/14 如期变红**；还原后字节与备份逐字相同 |
| `ruff check` / `ruff format` | All checks passed |

### 累计三段的测试增长

| 阶段 | 测试数 | 负验证变体 |
|---|---:|---:|
| 整改前（`4717a2cd`） | 33 | 0 |
| 一段（首轮 4 HIGH） | 53 | 8 |
| 二段（并行复核 2 实证 HIGH） | 55 | 10 |
| **三段（round-3 4 HIGH）** | **62** | **14** |

---

## 四、HIGH-1 的诚实边界（不要外推）

`_dirfd_still_in_vault()` 保证的是**不会谎报成功**——目录被移走/替换时会被检出、
撤销已发布文件、并 `exit 2`。它**不**保证「目录不可能被移走」：

- 检出发生在**写入之后**，那一刻文件确实短暂存在于 vault 外的目录里；
- 与 `lstat → unlink` 那处同源，POSIX 没有能彻底消除该窗口的原语。

⇒ 文档/验收单请照此口径，不要写成「已彻底封死目录外移」。
同一条外推警告在 `_atomic_write` 的 docstring 里也有一份（针对 dirfd 锚定的作用域）。

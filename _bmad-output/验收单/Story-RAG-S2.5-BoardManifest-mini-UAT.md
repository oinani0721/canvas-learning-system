# Story RAG-S2.5 白板目录卡（Board Manifest）— mini-UAT 验收单

> PLAN-ID: `RAG-S2.5-2026-08-10` · 九阶段路线第 2.5 站（结构读模型）
> 验收通过后进入 2.6（`## Concepts` 写侧视图化 + 8 个 skill 接入 manifest）
>
> **这一站做了什么（一句话）**：以前 Claude 想知道「某块白板怎么拆的」要几十次
> Grep/Read 拼图；现在一次 API 调用完整返回成员+派生原因+掌握度+历史考察，
> 且出题用的 exam 视图从结构上就带不出答案。

## 你要做的事（3 条，每条 1 分钟内）

**① 问「特征值白板怎么拆的」——一次调用看全结构**

整行复制到终端：

```bash
curl -s -X POST http://127.0.0.1:8011/api/v1/boards/manifest -H "Content-Type: application/json" -H "X-CLS-Internal-Key: $(grep '^INTERNAL_API_KEY=' /Users/Heishing/Desktop/canvas/canvas-learning-system/.env | cut -d= -f2)" -d '{"vault_id":"canvas-vault","board_id":"特征值与特征向量","view":"study"}' | python3 -m json.tool | head -60
```

**预期看到**：3 个节点（Fundamentals / Characteristic-Equation / Eigenvalues-are-special）各自带掌握度和派生关系；`"source": "live"`。再把 board_id 换成 `"CS 61B"` 跑一次，**预期看到** `"frontmatter_only": ["csm-tutoring-unit-credit"]` ——这就是「白板目录漏记了一个成员」的告警（你签字收养的那个孤儿，板目录还没列它，系统主动告诉你）。

- [ ] 特征值板一次调用见 3 节点 + 派生原因 + 掌握度
- [ ] CS 61B 板的目录漏记告警亮了

**② 换 exam 视图——确认答案性内容带不出来**

把上面命令里 `"view":"study"` 改成 `"view":"exam"`，输出末尾加 ` | grep -c "反例 diag"`。

**预期看到**：输出 `0`（你节点里那条「反例 diag(-1,-1)…」纠错文本，在出题视图里全文搜索零命中——出题的 AI 拿不到答案，考察才是真考察）。

- [ ] exam 视图纠错文本 0 命中

**③ 后端读不到 vault 时——快照兜底 + 诚实标注**

```bash
mv /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/节点 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/节点-暂挪 && sleep 10
```

再跑一遍 ① 的命令。**预期看到**：`"source": "local_json"`、`"degraded": true`、节点列表**还在**（最后一次好数据兜底），并明说原因「live 扫描失败, 退快照」。然后改回：

```bash
mv /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/节点-暂挪 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/节点
```

再跑一遍，**预期看到** `"source": "live"` 恢复。

- [ ] 挪走节点目录后返回 local_json + degraded=true 且数据还在
- [ ] 改回后恢复 live

## Claude 已代跑的技术验证（你不用管，供留档）

| 项目 | 结果 |
|------|------|
| 金集硬禁通道（P=R=1.00 无容差） | **32/32 全绿**（宿主 + 容器双姿势），基线已封版留痕 |
| 独立对抗审查 | 3 HIGH / 3 MEDIUM / 5 LOW **全部处置后复验全绿**（信封字段泄漏通道封堵 / 脏标量不再 500 / digest 不吸入答案 callout / 金集恒真条件修复），审查确认投影穿透 E2E 失败、快照双黑名单成立 |
| 板成员矩阵 | CS188=8 / 特征值=3 / CS 61B=2 / 递归=1 / 空板×2，与 T0 迁移审计精确相等 |
| 孤儿 | 0（T0 迁移后清零，14/14 节点全员有 source_board） |
| exam 泄漏禁串扫描 | 纠错文本×2 / 正文段 / 占位模板 / 核心概念摘句 —— 全 0 命中 |
| exam 禁键（任意深度） | tips/errors/error_candidates/misconception/correction/raw_dialog_excerpt/ai_reason/calibration_log/title/aliases/source_note —— 结构性不存在 |
| 合成投毒攻击 | 批注塞 600 字定义进派生原因 → 只出现在白名单槽位且硬截断 500 字；塞进 tips → 0 命中 |
| 延迟 | 列板 104ms / exam 79ms / study 61ms（预算 <300ms） |
| pick_hint 数值 | 与 vault decay_beta.py 真相源 1e-9 等价（契约测试 + 金集双锁） |
| 契约测试 | 41 项全绿（成员/四 schema/差集/路径穿越/降级三态/禁键投毒/快照原子写） |
| MCP 工具 | `get_board_manifest` 第 6 个只读白名单工具；空 body 不 422；quarantine 测试同步 |
| 安全探测 | 无 key→403 / 路径穿越→422 / 未知板→404 / wildcard 误挂→404 |
| 快照隔离 | `.claude/cache/board-manifest/manifest-v1.json`（.claude 在索引黑名单 + .json 非 .md 双保险） |
| 实测抓到的 bug | YAML datetime 透传炸快照序列化（BUG-361BD6FC）→ 已修 + 回归锁 |
| 依赖洞 | python-frontmatter 此前从未进 requirements.txt（三个上线服务在裸奔传递依赖）→ T0.1 首 commit 修 + docker build 验证过 |

## 顺手发现（不阻塞验收，留给你知道）

- **8 个未剖析占位节点**：CS188 lecture 2 的 7 个派生节点 + 特征值板的 Eigenvalues-are-special 还是「你的 1-2 句精准定义」占位状态（manifest 的 `is_stub: true` 现在会如实标出，考察选点也会跳过它们）
- **doc_count 漂移 ×2**：CS 61B 板声明 doc_count=1 实际 2 个成员；递归板声明 0 实际 1 —— 板 frontmatter 的 doc_count 没人维护，2.6 写侧视图化时一并处理
- **Docker 文件缓存**：宿主改 vault 目录名后容器要 ~10 秒才看见（VirtioFS 缓存）——UAT ③ 里 sleep 10 就是这个原因

## 已知边界（2.5 不做，属后续阶段）

- 8 个 skill 还没接 manifest（还在 N 次 Grep 拼图）—— 2.6 接入
- `## Concepts` 目录漏记只告警不改写 —— 写侧视图化是 2.6
- node_id 仍是文件名（改名即变）—— 1.5 稳定 ID 升级，字段已标注 `id_stability: basename_v1_will_upgrade_in_1_5`
- Neo4j 投影残破不作数据源 —— 已记 backlog，manifest 留了数据源接口随时可切

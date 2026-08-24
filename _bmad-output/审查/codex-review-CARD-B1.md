结论：`PARTIAL`。`0 BLOCKER / 0 HIGH / 2 MEDIUM`。审查基线为 `card/b1-ci-e0@848469ca`，全程只读。

### Findings

1. **MEDIUM — moviepy 删除只对新建/重建环境成立，原地升级迁移未闭环**

   [backend/requirements.txt:157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-b1-ci-e0/backend/requirements.txt:157) 和 [known-gotchas.md:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-b1-ci-e0/docs/known-gotchas.md:121) 无条件声称 `MOVIEPY_AVAILABLE=False`。

   反例：

   - 旧 venv 含 MoviePy 2.2.1，其元数据要求 `pillow<12.0`。
   - 对新 requirements 执行 `pip install --dry-run` 只计划安装 Pillow 12.3.0，不会卸载已不再声明的 MoviePy。
   - 将旧 MoviePy 与 Pillow 12.3.0 组合后，真实导入 [video_processor.py:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-b1-ci-e0/backend/lib/agentic_rag/processors/video_processor.py:25) 得到 `MOVIEPY_AVAILABLE=True`，直接反证文档的一般化陈述。
   - [video_processor.py:230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-b1-ci-e0/backend/lib/agentic_rag/processors/video_processor.py:230) 仍提示直接 `pip install moviepy`，也与 gotcha 的有条件复活规则冲突。

   建议明确“仅 fresh/rebuilt 环境”，并为长期 venv 提供重建或精确卸载 MoviePy 的迁移步骤；安装后验证 MoviePy 不存在及 `pip check` 通过。

2. **MEDIUM — 5 个新 CVE 与 13 个旧豁免的历史因果链丢失**

   原 [CARD-B1:94](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md:94>) 明确：本轮由另外 5 个未豁免 CVE 触发，它们不在旧 13 条豁免中。

   现在 [test.yml:162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-b1-ci-e0/.github/workflows/test.yml:162) 只讲 13 个旧 CVE；requirements 和 gotcha 只讲 5 个，未说明两组不重合。未来审计者会看到冲突数字，无法还原“为何此时升级”。建议补一句：“另有 5 个未豁免 CVE 触发本轮修复，均 Fix=12.3.0”。

### 已通过项

- MoviePy 活跃代码调用面为零：唯一 import 在 `video_processor.py`，`processors/__init__.py` 仅 re-export；未发现动态 import、插件、subprocess 或其它调用方。无 MoviePy 环境下包导入成功。
- Pillow 生产调用面兼容 12.3.0：无 `Image.ANTIALIAS` 等已移除 API；`Image.LANCZOS` 与 `Image.Resampling.LANCZOS` 均有效。官方也确认 `Image.LANCZOS` 保留。[Pillow 弃用清单](https://pillow.readthedocs.io/en/stable/deprecations.html)
- YAML 解析、shell `bash -n`、pip-audit `-r/--desc` 语法均通过；13 条实际参数已全部删除。
- 零豁免实跑：`No known vulnerabilities found`，exit 0。
- 白名单 14 文件加 `test_multimodal_fixes.py`：`305 passed, 13 skipped`。
- 当前重建 venv：Pillow 12.3.0、MoviePy 未安装、`pip check` 无断裂。
- known-gotchas 分类及总数复算正确：`38 = 33 + 4 + 1`。

限制：未提交改动尚无对应 GitHub Actions run，因此不能宣称四个远端 job 已绿；本地运行环境为 Python 3.14，不是 CI 的 3.11/3.12。根 manifest 的 `Pillow>=10` 及 Python 3.9 声明属于既存 SoT 漂移，不是 CARD-B1 新回归；Pillow 12 本身仅支持 Python ≥3.10。[Pillow Python 支持矩阵](https://pillow.readthedocs.io/en/stable/installation/python-support.html)



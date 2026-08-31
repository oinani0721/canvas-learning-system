#!/usr/bin/env python3
"""工作树资产分类台账 — 只读盘点器（CARD-DEBT-13）。

对指定的若干 git 工作树，把 ``git status --porcelain -uall -z`` 的**每一条**记录
逐条归入四类（用户资产 / 审查产物 / 应提交代码 / 临时物），产出人读 md 台账
与机读 json 台账。

设计约束（卡文硬边界）：

1. **只读（及其边界，如实说清）**：本脚本对被盘点仓库只执行读命令（``status`` /
   ``rev-parse`` / ``ls-tree`` / ``cat-file`` / ``hash-object`` / ``log`` /
   ``check-ignore`` / ``config``），全部带 ``--no-optional-locks``。

   但 ``--no-optional-locks`` **不是只读沙箱**——它只禁用需要可选锁的操作。
   自定义 ``filter.<name>.clean`` / ``.process`` 驱动是任意命令，会在
   ``hash-object`` 取证时被 git 执行，可在被盘点工作树里留下副作用；副作用若
   恰好被 gitignore 覆盖，前后 porcelain sha256 还会照常相等——只读取证就给出
   假绿。因此"目标仓无自定义 filter 驱动"是一条**独立硬断言**（检出即 exit 2，
   ``--allow-filter-drivers`` 可明示接受）。

   同理，两次 porcelain sha256 相等只证明两个时点的 ``(XY, path[, orig])``
   字节相同；它不证明文件内容 / ignored 文件 / refs / object DB / git 配置未变，
   也不证明"写后又恢复"没发生，更不能把变化归因到本脚本还是并发进程。
2. **只登记，禁删除禁移动**：脚本对被盘点目标不含任何写/删/移的代码路径；
   产出只落 ``--out-dir``。若它落在某个被盘点目标的目录树内**且未被该目标
   gitignore 排除**，脚本在开始**盘点**之前就 exit 2（判定自身要调
   ``rev-parse --show-toplevel`` 与 ``check-ignore``，所以不是"任何 git 命令之前"）。
   被 gitignore 排除的嵌套情形放行，但在台账里**如实登记**——那种情况下产出确实
   写进了该目标的文件系统，只是 git 看不见，不能因此宣称"零交集"。
3. **零漏项，且要可证**——每道门各挡一类错误，缺一不可：
   - 独立计数：解析出的记录数 == 不带 ``-z`` 的 porcelain 行数。期望值取自
     **被验证对象之外**；若记录数从解析结果自己算，"解析器丢一条"会让期望值
     跟着变小、断言永远绿（变异 M1 实测如此）。
   - XY 序列：每条记录的两字符状态码序列 == 同一条独立命令的逐行行首。挡
     "字段分组错但字节序不变"——那种错误能同时骗过计数与字节往返。
   - 分类对账：分类条目数 == 记录数，挡"有记录没进分类"。
   - 字节往返：把解析结果重新序列化回 ``-z`` 字节流，必须与 git 的原始输出
     **逐字节相同**。挡"少解析一条 + 多分类一条"这类互相抵消的错误。
   - 无自定义 filter 驱动：见下条 1 的说明。
   任一断言不过 → exit 2。

判别口径（保守优先原则）：分类不确定时归入**更受保护**的类别。把用户数据错判
成"临时物"是不可逆的方向，把临时物错判成"用户资产"只是多留一份。

Usage::

    # 首跑
    python3 scripts/census_worktree_assets.py \\
        --pin-sha main=a55db2ab --pin-sha feature=7f5095fd

    # 复跑并与首跑 diff
    python3 scripts/census_worktree_assets.py \\
        --baseline _bmad-output/审查/2026-08-31-DEBT-13-工作树资产分类台账.json

Exit codes: 0 = 全部断言通过；2 = 断言失败（对账/往返/pin/只读取证）；
1 = 用法或环境错误。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import stat as stat_module
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

SCHEMA = "census_worktree_assets/v1"

# ---------------------------------------------------------------------------
# 盘点目标
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_TARGETS: List[Tuple[str, str, str]] = [
    (
        "main",
        "/Users/Heishing/Desktop/canvas/canvas-learning-system",
        "主仓（main 分支）——Stop hook 自动 stage+commit+push 的射程内",
    ),
    (
        "feature",
        "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev",
        "长期 feature worktree（worktree-feature-obsidian-hybrid-dev）",
    ),
]

# 主仓 untracked 若同路径也在此分支受控，需进一步比对 blob OID 判三态：
# same_blob（同内容副本）/ diverged（内容分歧，禁单向覆盖）/ 无法取证。
# ⛔ 不得笼统判"主仓落后"——两个 HEAD 互不为祖先，实测 75 条里 20 条内容不同。
FEATURE_BRANCH = "worktree-feature-obsidian-hybrid-dev"
FEATURE_WORKTREE_PATH = (
    "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/"
    "feature-obsidian-hybrid-dev"
)

# ---------------------------------------------------------------------------
# 四类
# ---------------------------------------------------------------------------

CAT_USER = "用户资产"
CAT_REVIEW = "审查产物"
CAT_CODE = "应提交代码"
CAT_EPHEMERAL = "临时物"

CATEGORIES = [CAT_USER, CAT_REVIEW, CAT_CODE, CAT_EPHEMERAL]

CATEGORY_DEFINITION = {
    CAT_USER: "用户手写或系统为用户产出、丢失即不可恢复或需人工重建的内容（vault 笔记与批注、数据库备份、live 管道产物快照）",
    CAT_REVIEW: "审查 / 研究 / 验收 / 计划过程文档（`_bmad-output/`、`.gdr/` 等），项目自身的工作记录",
    CAT_CODE: "源码、测试、配置、skill 定义、项目文档——本应受版本控制的仓库内容物",
    CAT_EPHEMERAL: "缓存、运行时日志、编辑器与工具状态、可由代码确定性重建的产物"
    "（注意：`logs/audit/` 下的审计事件与报告**不属此类**，它们不可确定性重建，归审查产物）",
}


@dataclass
class Rule:
    rule_id: str
    category: str
    why: str
    match: Callable[[str], bool]


def _seg(path: str, name: str) -> bool:
    """path 的任一目录段等于 name。"""
    return name in path.split("/")


def _under(path: str, prefix: str) -> bool:
    return path == prefix.rstrip("/") or path.startswith(prefix)


# 顺序敏感：首个命中的规则生效。越具体的越靠前。
RULES: List[Rule] = [
    # Codex round-3 B-1：U10 原来排在 E1-E3 之后，`hooks/__pycache__/dead.jsonl`
    # 这类路径会先被字节码缓存规则吃掉。用户的未送达学习会话优先级最高，前置。
    Rule(
        "U10",
        CAT_USER,
        "hooks 本地待发/死信队列（未送达的用户学习会话，禁丢禁提交）",
        lambda p: _under(p, "canvas-vault/.claude/hooks/") and p.endswith(".jsonl"),
    ),
    # --- 临时物：工具/缓存/编辑器状态 ---
    Rule(
        "E1",
        CAT_EPHEMERAL,
        "Python 字节码缓存",
        lambda p: _seg(p, "__pycache__") or p.endswith(".pyc"),
    ),
    Rule(
        "E2",
        CAT_EPHEMERAL,
        "虚拟环境 / 依赖树",
        # round-6 CLS-E2：`.venv-` 前缀原来匹配**任意路径段**，于是
        # `_bmad-output/审查/.venv-migration-notes.md` 这类审查文档被判成
        # 「临时物：可安全忽略」——正是台账自己声明的不可逆方向。
        # 收紧为：venv 备份目录只认「目录段本身」且必须落在已知的 venv 宿主目录下。
        lambda p: (
            any(s in ("node_modules", ".venv") for s in p.split("/"))
            or any(
                seg.startswith(".venv-") and i + 1 < len(p.split("/"))
                for i, seg in enumerate(p.split("/"))
                if i > 0 and p.split("/")[i - 1] in ("backend", "frontend", "scripts")
            )
        ),
    ),
    Rule(
        "E3",
        CAT_EPHEMERAL,
        "测试与 lint 缓存",
        lambda p: (
            _seg(p, ".pytest_cache") or _seg(p, ".ruff_cache") or _seg(p, ".mypy_cache")
        ),
    ),
    Rule(
        "E4",
        CAT_EPHEMERAL,
        "macOS Finder 元数据",
        lambda p: os.path.basename(p) == ".DS_Store",
    ),
    Rule(
        "E5",
        CAT_EPHEMERAL,
        "session 接管状态（进程级临时态）",
        lambda p: _under(p, ".session-takeover/"),
    ),
    # B-2 整改：`.obsidian/` 不是一棵同质的「工作区状态」——里面混着设备密钥、
    # .gitignore 明令保留受控的配置、以及真正的编辑器缓存。整棵判临时物会把设备
    # 密钥标成「可安全忽略」。按内容拆三档，顺序由具体到一般。
    # ⚠️ 顺序要紧：C11 的**精确文件名白名单**必须排在 U9 的**子串启发式**之前。
    # 实测踩过——`hotkeys.json` 的 basename 含子串 "key"，U9 在前就会把这份
    # .gitignore 明令保留受控的配置判成设备密钥。更具体的规则永远在前。
    # Codex round-2 B-2：`.obsidian/` 里还有两类被整棵兜底吃掉的东西——
    #   U11 插件的用户设置与迁移备份（breadcrumbs 的 backup_old_settings() 就往
    #       data-backup__*.json 写 this.settings），是用户数据不是确定性缓存；
    #   C12 `.obsidian/templates/` 被 .gitignore 明称项目代码。
    # 二者都比 C11/U9/E6 更具体，必须排在它们之前。
    Rule(
        "U11",
        CAT_USER,
        "插件的用户设置与迁移备份（data*.json / *backup*.json，丢失需重配）",
        lambda p: (
            _under(p, "canvas-vault/.obsidian/plugins/")
            and p.endswith(".json")
            and (
                os.path.basename(p).startswith("data")
                or "backup" in os.path.basename(p).lower()
            )
        ),
    ),
    Rule(
        "C12",
        CAT_CODE,
        "`.gitignore` 明称项目代码的 vault 模板目录",
        lambda p: _under(p, "canvas-vault/.obsidian/templates/"),
    ),
    Rule(
        "C11",
        CAT_CODE,
        "vault 级受控配置：hotkeys / community-plugins（`.gitignore` keep-track 明列）+ "
        "plugins·themes 的直属 manifest（同类元数据，本台账按同一口径归类——"
        "⚠️ `.gitignore` 的 keep-track 注释只点名了前两者，themes manifest 属本台账的判断）",
        # Codex round-2 B-2：原来只看 basename，任意深层 `cache/manifest.json` 都会误命中。
        # 限定为 vault 根级两份 + plugins/<id>/ 与 themes/<id>/ 的直属 manifest（路径段数 == 5）。
        # Codex round-4 B-2：还漏了根段约束——`.gitignore` 只把 canvas-vault 的
        # .obsidian 列为例外，别处的 `**/.obsidian/` 一律算个人配置。
        lambda p: (
            p
            in (
                "canvas-vault/.obsidian/hotkeys.json",
                "canvas-vault/.obsidian/community-plugins.json",
            )
            or (
                os.path.basename(p) == "manifest.json"
                and len(p.split("/")) == 5
                and p.split("/")[0] == "canvas-vault"
                and p.split("/")[1] == ".obsidian"
                and p.split("/")[2] in ("plugins", "themes")
            )
        ),
    ),
    Rule(
        "U9",
        CAT_USER,
        "设备级密钥/凭据（丢失需重新生成并同步配置，禁提交）",
        # Codex round-2 B-2：裸子串匹配会把 `keyboard-layout.json` 判成密钥。
        # 改为按词边界匹配——只在 basename 被非字母数字切开的片段里找关键词。
        lambda p: (
            _under(p, "canvas-vault/.obsidian/")
            and bool(
                {
                    "key",
                    "keys",
                    "secret",
                    "secrets",
                    "token",
                    "tokens",
                    "credential",
                    "credentials",
                    "password",
                    "oauth",
                }
                & set(re.split(r"[^a-z0-9]+", os.path.basename(p).lower()))
            )
        ),
    ),
    Rule(
        "E6",
        CAT_EPHEMERAL,
        "Obsidian 编辑器工作区状态与缓存（workspace/app/appearance/core-plugins 等）",
        lambda p: _under(p, "canvas-vault/.obsidian/"),
    ),
    Rule(
        "E7",
        CAT_EPHEMERAL,
        "fixture vault 的管道产物（可重跑重建）",
        lambda p: _under(p, "test-vault/outputs/"),
    ),
    # --- 用户资产：vault 内容与备份（先于下面的 code 规则） ---
    Rule(
        "U1",
        CAT_USER,
        "vault 回收站——用户删除但未清空的笔记",
        lambda p: _under(p, "canvas-vault/.trash/"),
    ),
    Rule(
        "U2",
        CAT_USER,
        "Claudian 插件的用户侧状态与产物",
        lambda p: _under(p, "canvas-vault/.claudian/"),
    ),
    Rule(
        "U8",
        CAT_USER,
        "skill 缓存区里的用户内容备份（*.bak / *backup* 目录，丢失不可重建）",
        lambda p: (
            _under(p, "canvas-vault/.claude/cache/")
            and ("backup" in p or p.endswith(".bak"))
        ),
    ),
    Rule(
        "E8",
        CAT_EPHEMERAL,
        "skill 缓存区（可由管道重建）",
        lambda p: _under(p, "canvas-vault/.claude/cache/"),
    ),
    Rule(
        "U3",
        CAT_CODE,
        "vault 内的 skill / 配置定义（受版本控制的代码面）",
        lambda p: _under(p, "canvas-vault/.claude/"),
    ),
    Rule(
        "U4",
        CAT_USER,
        "live 管道产物快照（含被维护卡 B 引为语料的真报告，非确定性可重建）",
        lambda p: _under(p, "canvas-vault/outputs/"),
    ),
    Rule(
        "U5",
        CAT_USER,
        "用户笔记正文（原白板/检验白板/节点/课程材料）",
        lambda p: _under(p, "canvas-vault/"),
    ),
    Rule(
        "U6",
        CAT_USER,
        "备份区（Neo4j dump、上线前快照、事件账备份）",
        lambda p: _under(p, "backups/") or _under(p, "backend/data/backups/"),
    ),
    Rule(
        "U7",
        CAT_USER,
        "用户手写批注与批注回复（丢失即不可重建）",
        lambda p: (
            _under(p, "_bmad-output/验收单/批注回复/")
            or _under(p, "_bmad-output/决策批注/")
        ),
    ),
    # --- 审查产物 ---
    Rule(
        "R1",
        CAT_REVIEW,
        "BMAD 过程文档（审查/研究/验收单/goal-cards/planning）",
        lambda p: _under(p, "_bmad-output/"),
    ),
    Rule(
        "R2", CAT_REVIEW, "deep-research 指令与素材清单", lambda p: _under(p, ".gdr/")
    ),
    # --- 应提交代码 ---
    Rule("C1", CAT_CODE, "后端源码 / 测试 / 脚本", lambda p: _under(p, "backend/")),
    Rule(
        "C2", CAT_CODE, "前端源码（含 Obsidian 插件）", lambda p: _under(p, "frontend/")
    ),
    Rule("C3", CAT_CODE, "仓库级脚本", lambda p: _under(p, "scripts/")),
    Rule(
        "C4",
        CAT_CODE,
        "项目文档（架构/gotchas/项目状态）",
        lambda p: _under(p, "docs/"),
    ),
    Rule("C5", CAT_CODE, "OpenSpec 规格", lambda p: _under(p, "openspec/")),
    Rule("C6", CAT_CODE, "CI 定义", lambda p: _under(p, ".github/")),
    Rule(
        "C7",
        CAT_CODE,
        "Claude Code 配置 / skill / rules",
        lambda p: _under(p, ".claude/"),
    ),
    Rule("C8", CAT_CODE, "决策记录", lambda p: _under(p, "_decisions/")),
    Rule(
        "C9",
        CAT_CODE,
        "fixture vault 骨架",
        lambda p: _under(p, "test-vault/") or _under(p, "backend/vault/"),
    ),
    Rule("C10", CAT_CODE, "仓库根级配置与说明文件", lambda p: "/" not in p),
    # Codex round-2 B-3 的第二档：仓里还有一批 tracked 目录既非源码也非 vault，
    # 逐个按实际内容定性（下列目录名与首层内容均已实查，非猜测）。
    Rule(
        "U12",
        CAT_USER,
        "运行时数据目录（LanceDB 表、调研产出等，丢失需重建索引）",
        lambda p: _under(p, "data/"),
    ),
    Rule(
        "E10",
        CAT_EPHEMERAL,
        "运行时生成的配图（`.gitignore` 的 `images/generated*`）",
        # Codex round-4 B-3：原来看最终 basename，与 gitignore 语义不等价——
        # `images/generated/chart.png` 该被判 runtime 却漏掉，
        # `images/sub/generated-icon.svg` 不该判却命中。gitignore 的 `images/generated*`
        # 匹配的是 `images/` 之下的**首段**。
        # Codex round-5 F7：两个目标都是 core.ignorecase=true，git 会把
        # `images/Generated/chart.png` 也判为命中 `images/generated*`。规则要跟上。
        # round-6 CLS-E10：F7 只折叠了第二段的大小写，第一段仍走大小写敏感的
        # `_under(p, "images/")`；core.ignorecase=true 下 git 也会匹配 `Images/`。
        lambda p: (
            len(p.split("/")) > 1
            and p.split("/")[0].lower() == "images"
            and p.split("/")[1].lower().startswith("generated")
        ),
    ),
    Rule(
        "R4",
        CAT_REVIEW,
        "审计事件与报告（`logs/audit/` 与 `logs/workflow-gate-audit*`，不可确定性重建）",
        lambda p: _under(p, "logs/audit/") or _under(p, "logs/workflow-gate-audit"),
    ),
    Rule(
        "E11",
        CAT_EPHEMERAL,
        "运行时日志（`.gitignore` 把 `logs/` 整体列为 runtime；生产代码会往这里写 alerts.log）",
        lambda p: _under(p, "logs/"),
    ),
    Rule(
        "E9",
        CAT_EPHEMERAL,
        "hypothesis / repomix 等工具缓存",
        lambda p: any(_under(p, root) for root in (".hypothesis/", ".repomix/")),
    ),
    Rule(
        "R3",
        CAT_REVIEW,
        "BMAD 与 PRD 过程文档树（_bmad / _bmad-archive / _archive / _prd-register / _plans / _reference / _verification）",
        lambda p: any(
            _under(p, root)
            for root in (
                "_bmad/",
                "_bmad-archive/",
                "_archive/",
                "_prd-register/",
                "_plans/",
                "_verification/",
                "_reference/",
            )
        ),
    ),
    Rule(
        "C14",
        CAT_CODE,
        "模板、文档配图与后台 shell 清单（`images/generated*` 除外，由 E10 接走）",
        # Codex round-3 B-3：`.gitignore` 明列 `images/generated*` 为 runtime 产物，
        # 由前置的 E10 接走，这里只收其余配图。
        lambda p: (
            any(_under(p, root) for root in ("_templates/", ".bg-shell/"))
            or (len(p.split("/")) > 1 and p.split("/")[0].lower() == "images")
        ),
    ),
    # Codex round-2 B-3：把全部 tracked 路径喂进 classify() 实测有 1832 条掉进 Z1；
    # Z1 现已归「用户资产」，那意味着真源码会被判成用户数据并失去 owner 追索。补齐代码根。
    Rule(
        "C13",
        CAT_CODE,
        "仓库级测试 / 配置 / 工具 / 规格 / 容器与部署定义",
        lambda p: any(
            _under(p, root)
            for root in (
                "tests/",
                "config/",
                "tools/",
                "specs/",
                ".devcontainer/",
                ".vscode/",
                "migrations/",
                "deploy/",
                "docker/",
                "src/",
                "lib/",
                "bin/",
                "e2e/",
                "infra/",
                "packages/",
                "apps/",
            )
        ),
    ),
    # --- 归档区：未决搬迁的目的地（类别一律由这三条路径规则判定，不继承来源） ---
    Rule(
        "A1",
        CAT_CODE,
        "旧 Tauri v0 源码归档（未受版本控制）",
        lambda p: _under(p, "archive/legacy-tauri-v0/"),
    ),
    Rule(
        "A2",
        CAT_CODE,
        "历史项目文档归档（原 docs/ 树的搬迁目的地）",
        lambda p: _under(p, "archive/legacy-docs/"),
    ),
    Rule(
        "A3",
        CAT_CODE,
        "归档区其余内容（本应受版本控制的仓库内容物）",
        lambda p: _under(p, "archive/"),
    ),
]

CATCHALL_RULE = "Z1"
# B-3 整改：原先 catch-all 归「应提交代码」，与声明的「保守优先」自相矛盾——
# 未知路径可能是私人资料，预设「应提交」把处置方向指向了"提交曝光"。
# 改归最受保护的「用户资产」（禁删禁移禁提交）+ 强制人审。
CATCHALL_CATEGORY = CAT_USER


def classify(path: str) -> Tuple[str, str, str]:
    """返回 (类别, 规则 id, 规则理由)。"""
    for rule in RULES:
        if rule.match(path):
            return rule.category, rule.rule_id, rule.why
    return (
        CATCHALL_CATEGORY,
        CATCHALL_RULE,
        "无规则命中——保守归入最受保护的用户资产并强制人工裁定",
    )


# ---------------------------------------------------------------------------
# git 只读封装
# ---------------------------------------------------------------------------


class GitError(RuntimeError):
    pass


# 所有 git 调用共用的只读加固前缀（Codex round-2 A-2）：
#   --no-lazy-fetch  partial clone 下 cat-file 可能向 promisor remote 懒取并写 object DB
#   core.fsmonitor=  关掉 fsmonitor（否则 status 可能起 daemon 或调 hook）
#   core.hooksPath   指向不存在目录，杜绝任何仓内钩子被顺手执行
GIT_READONLY_ARGS = [
    "--no-optional-locks",
    "--no-lazy-fetch",
    "-c",
    "core.quotepath=false",
    "-c",
    "core.fsmonitor=",
    "-c",
    "core.hooksPath=/nonexistent-census-readonly",
]


def git_raw(repo: str, args: Sequence[str], stdin: Optional[bytes] = None) -> bytes:
    cmd = ["git", "-C", repo, *GIT_READONLY_ARGS, *args]
    proc = subprocess.run(
        cmd, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        raise GitError(
            f"{' '.join(cmd)} → rc={proc.returncode}\n{proc.stderr.decode('utf-8', 'replace')}"
        )
    return proc.stdout


def git_text(repo: str, args: Sequence[str]) -> str:
    """只剥掉 git 输出末尾那一个换行，**不做 strip()**。

    Codex round-4 A-1：`.strip()` 会把路径末尾的空格 / NBSP 一并裁掉——
    `/tmp/repo` 与 `/tmp/repo<空格>` 是两个不同的仓，裁完就指向前者，
    于是「解析出的真实根」悄悄换了个仓，而所有断言照常全绿。
    解码也改 surrogateescape，非 UTF-8 路径不再被 replace 破坏。
    """
    raw = git_raw(repo, args)
    if raw.endswith(b"\n"):
        raw = raw[:-1]
    return raw.decode("utf-8", "surrogateescape")


def porcelain(repo: str) -> bytes:
    """卡文点名的规范命令。原始字节，不做任何加工。"""
    return git_raw(repo, ["status", "--porcelain", "-uall", "-z"])


def porcelain_xy_sequence(repo: str) -> List[str]:
    """XY 码序列的**独立来源**：不带 ``-z`` 的 porcelain 每条记录一行，行首两字符即 XY。

    这条门挡的是字节往返挡不住的一类错误：解析器把 NUL 字段**分组错**（例如把
    ``R`` 记录的来源字段当成下一条独立记录），字节序不变 → 重新序列化仍逐字节相同、
    记录数也可能仍然相等，但语义上真实的 rename 已经丢了。XY 序列来自另一条命令、
    与 ``-z`` 解析结果无共享代码路径，分组错会立刻在这里对不上。
    """
    raw = git_raw(repo, ["status", "--porcelain", "-uall"])
    return [
        line[:2].decode("utf-8", "surrogateescape") for line in raw.split(b"\n") if line
    ]


def porcelain_line_count(repo: str) -> int:
    """记录数的**独立来源**：不带 ``-z`` 的 porcelain 每条记录恰好一行
    （含控制字符的路径会被 git 加引号转义，不会跨行；rename 的两个路径也在同一行）。

    这条独立计数存在的理由：若记录数从解析结果自己算出来，"解析器丢了一条"这种
    错误会让期望值跟着一起变小，计数断言就永远绿——实测变异 M1 正是如此。
    期望值必须来自被验证对象之外。
    """
    raw = git_raw(repo, ["status", "--porcelain", "-uall"])
    return sum(1 for line in raw.split(b"\n") if line)


# ---------------------------------------------------------------------------
# porcelain -z 解析 + 字节往返
# ---------------------------------------------------------------------------


@dataclass
class Record:
    xy: str  # 两字符状态码，如 " D" / "?? " 里的 "??" / " M"
    path: str
    orig: Optional[str] = None  # 仅 R/C（rename/copy）有

    def serialize(self) -> bytes:
        out = (
            self.xy.encode("utf-8", "surrogateescape")
            + b" "
            + self.path.encode("utf-8", "surrogateescape")
            + b"\0"
        )
        if self.orig is not None:
            out += self.orig.encode("utf-8", "surrogateescape") + b"\0"
        return out


def parse_porcelain(raw: bytes) -> List[Record]:
    """按 porcelain v1 -z 规格解析。

    格式：``XY SP <path> NUL``；若 X 或 Y 是 R/C，则紧跟 ``<origPath> NUL``。
    """
    fields = raw.split(b"\0")
    # split 后末尾会多出一个空串（raw 以 NUL 结尾）；raw 为空时 fields == [b""]
    if fields and fields[-1] == b"":
        fields.pop()
    records: List[Record] = []
    i = 0
    while i < len(fields):
        entry = fields[i]
        if len(entry) < 4 or entry[2:3] != b" ":
            raise GitError(f"无法解析 porcelain 记录（第 {i} 个字段）: {entry!r}")
        xy = entry[:2].decode("utf-8", "surrogateescape")
        path = entry[3:].decode("utf-8", "surrogateescape")
        orig = None
        if xy[0] in "RC" or xy[1] in "RC":
            i += 1
            if i >= len(fields):
                raise GitError(f"rename/copy 记录缺少原路径: {entry!r}")
            orig = fields[i].decode("utf-8", "surrogateescape")
        records.append(Record(xy=xy, path=path, orig=orig))
        i += 1
    return records


def roundtrip(records: Sequence[Record]) -> bytes:
    return b"".join(r.serialize() for r in records)


# ---------------------------------------------------------------------------
# 搬迁取证（tracked 删除 ←→ untracked 归档副本）
# ---------------------------------------------------------------------------


# 内容匹配时纳入哈希的 untracked 文件大小上限（超过者只登记不哈希，避免为
# Neo4j dump 这类大文件做无意义的全量哈希）。
# C-1 整改：原 8MB 上限当场造出一条**假陈述**——`docs/architecture/backend-overview.png`
# (16,420,168 B) 与归档区同名文件 blob sha 同为 d7b8cb4d，实为位移，却因超限没进
# 内容索引，被 basename 兜底判成 "same_name_diff_content"。上限提到 128MB（覆盖本仓
# 最大未跟踪文件 16.4MB 与全部 Neo4j dump），并且超限一律走独立判定 `size_excluded`，
# **绝不再退回 same_name_diff_content 冒充内容结论**。
HASH_SIZE_CAP = 128 * 1024 * 1024

# C-2 整改：内容相等只证明「存在同一内容的副本」，不证明因果上的「此文件搬到了那里」。
# 低熵内容（`.gitkeep`、只含一行占位、固定存根）会让不相干的两棵树互相"配对"。
# 小于此阈值的 blob 一律标 low_entropy：仍登记为证据，但**不驱动类别继承**。
LOW_ENTROPY_MAX_BYTES = 64

# 空文件的 git blob sha 全仓恒等于此值。内容匹配必须把它排除：否则任意一个空的
# 被删文件会"匹配"上工作树里每一个空文件（实测本仓 docs/stories/4.5.story.md 是空的，
# 会一口气命中 16 个未跟踪空文件，其中含用户 vault 笔记）——那是假证据，不是位移。
EMPTY_BLOB_SHA_SHA1 = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


def empty_blob_oid(repo: str) -> str:
    """该仓的空 blob OID。硬编码 SHA-1 在 SHA-256 仓会失效（Codex round-2 LOW）。"""
    # 查询失败不得回退硬编码 SHA-1（Codex round-3）：在 SHA-256 仓那会把一个
    # 不相干的常量当成"空 blob"，重新打开空内容误配的口子。fail-closed。
    return (
        git_raw(repo, ["hash-object", "-t", "blob", "--stdin"], stdin=b"")
        .decode()
        .strip()
    )


@dataclass
class Relocation:
    verdict: str  # moved_identical / same_name_diff_content / no_candidate
    candidates: List[str]  # 内容或同名候选（可能多条）
    head_blob: Optional[str]
    match_kind: str  # content_sha / basename_only / none

    @property
    def candidate(self) -> Optional[str]:
        return self.candidates[0] if self.candidates else None


def batch_head_blobs(
    repo: str, paths: Sequence[str], skipped: Optional[List[str]] = None
) -> Dict[str, Optional[str]]:
    """一次 cat-file --batch-check 取出 HEAD 版本各路径的 blob sha。

    含换行的路径无法走 batch 协议（协议按行分隔）。这类路径**只降级取证、不降级覆盖**：
    从 batch 输入里剔除并登记到 ``skipped``，该条目仍会进分类与对账，只是没有内容取证。
    取证拿不到是可以接受的；整份台账因为一个文件名而不产出不可接受。
    """
    result: Dict[str, Optional[str]] = {p: None for p in paths}
    usable = [p for p in paths if "\n" not in p]
    if skipped is not None:
        skipped.extend(p for p in paths if "\n" in p)
    if not usable:
        return result
    stdin = "".join(f"HEAD:{p}\n" for p in usable).encode("utf-8", "surrogateescape")
    out = git_raw(repo, ["cat-file", "--batch-check"], stdin=stdin).decode(
        "utf-8", "replace"
    )
    lines = [ln for ln in out.split("\n") if ln != ""]
    if len(lines) != len(usable):
        raise GitError(
            f"cat-file --batch-check 行数 {len(lines)} != 输入路径数 {len(usable)}"
        )
    for path, line in zip(usable, lines):
        parts = line.split(" ")
        result[path] = parts[0] if len(parts) >= 3 and parts[1] == "blob" else None
    return result


def batch_worktree_blobs(
    repo: str, rel_paths: Sequence[str], skipped: Optional[List[str]] = None
) -> Dict[str, Optional[str]]:
    """一次 hash-object --stdin-paths 取出磁盘文件的 blob sha。"""
    if not rel_paths:
        return {}
    usable: List[str] = []
    for p in rel_paths:
        if "\n" in p:
            if skipped is not None:
                skipped.append(p)
            continue
        if (Path(repo) / p).is_file():
            usable.append(p)
    if not usable:
        return {p: None for p in rel_paths}
    stdin = "".join(f"{p}\n" for p in usable).encode("utf-8", "surrogateescape")
    out = git_raw(repo, ["hash-object", "--stdin-paths"], stdin=stdin).decode(
        "utf-8", "replace"
    )
    shas = [ln for ln in out.split("\n") if ln != ""]
    if len(shas) != len(usable):
        raise GitError(f"hash-object 输出行数 {len(shas)} != 输入路径数 {len(usable)}")
    result: Dict[str, Optional[str]] = {p: None for p in rel_paths}
    result.update(dict(zip(usable, shas)))
    return result


def head_blob_sizes(repo: str, paths: Sequence[str]) -> Dict[str, Optional[int]]:
    """批量取 HEAD 版本各路径 blob 的字节数（低熵判定用）。"""
    if not paths:
        return {}
    stdin = "".join(f"HEAD:{p}\n" for p in paths).encode("utf-8", "surrogateescape")
    out = git_raw(repo, ["cat-file", "--batch-check"], stdin=stdin).decode(
        "utf-8", "replace"
    )
    lines = [ln for ln in out.split("\n") if ln != ""]
    if len(lines) != len(paths):
        raise GitError(
            f"cat-file --batch-check 行数 {len(lines)} != 输入路径数 {len(paths)}"
        )
    result: Dict[str, Optional[int]] = {}
    for path, line in zip(paths, lines):
        parts = line.split(" ")
        result[path] = (
            int(parts[2])
            if len(parts) >= 3 and parts[1] == "blob" and parts[2].isdigit()
            else None
        )
    return result


def custom_filter_drivers(repo: str) -> List[str]:
    """列出该仓配置的自定义 ``filter.<name>.clean`` / ``.process`` 驱动。

    ``--no-optional-locks`` 只禁用需要可选锁的操作，**不是只读沙箱**：
    ``git hash-object --stdin-paths`` 会按路径套用 attributes，自定义 clean filter
    是任意命令，可以在被盘点工作树里产生副作用（且副作用若被 gitignore 覆盖，
    盘点前后的 porcelain sha256 还会照常相等——只读取证会给出假绿）。

    因此本脚本把「目标仓无自定义 filter 驱动」升为一条**显式断言**：检出即 exit 2，
    除非调用者用 ``--allow-filter-drivers`` 明示接受该风险。
    """
    proc = subprocess.run(
        [
            "git",
            "-C",
            repo,
            *GIT_READONLY_ARGS,
            "config",
            "--get-regexp",
            r"^filter\..*\.(clean|process)$",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # rc 语义要分清：1 = 没有匹配项（正常）；其余非零 = 读配置本身出错。
    # 原先把所有非零都当"无驱动"是 fail-open——读不到配置反而放行。
    if proc.returncode == 1:
        return []
    if proc.returncode != 0:
        raise GitError(
            f"git config --get-regexp 读取失败 rc={proc.returncode}: "
            f"{proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    return [
        ln for ln in proc.stdout.decode("utf-8", "replace").split("\n") if ln.strip()
    ]


def head_blob_index(repo: str) -> Dict[str, List[str]]:
    """HEAD 树里 blob sha → 路径列表。用于判「未跟踪文件其实是已受控内容的副本」。"""
    raw = git_raw(repo, ["ls-tree", "-r", "-z", "HEAD"])
    index: Dict[str, List[str]] = {}
    for rec in raw.split(b"\0"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        parts = meta.split(b" ")
        if len(parts) != 3 or parts[1] != b"blob":
            continue
        sha = parts[2].decode()
        if sha == EMPTY_BLOB_SHA_SHA1:
            continue
        index.setdefault(sha, []).append(path.decode("utf-8", "surrogateescape"))
    return index


def build_relocation_map(
    repo: str, records: Sequence[Record]
) -> Tuple[
    Dict[str, Relocation],
    Dict[str, List[str]],
    Dict[str, List[str]],
    List[str],
    Dict[str, str],
    Dict[str, Optional[str]],
]:
    """判定每条 tracked 删除是否只是「未提交的位移」。

    配对**以内容为准，不以文件名为准**：HEAD 侧 blob OID 由 ``git cat-file --batch-check``
    取得，工作树侧由 ``git hash-object --stdin-paths`` 取得，是同一套 git 内容身份，
    可直接相等比较。按 basename 配对会一对多（仓里有几十个 ``index.md``），
    配错就是假证据，所以 basename 只用来降级说明「同名但内容不同」。

    返回五元组：(被删路径 → Relocation, 位移目的地 → 位移来源列表,
    未跟踪路径 → HEAD 中同内容的受控路径列表, 因路径含换行而未能取证的路径列表,
    未能哈希的未跟踪路径 → 原因)。
    """
    deleted = [r.path for r in records if "D" in r.xy and r.xy != "??"]
    untracked = [r.path for r in records if r.xy == "??"]
    skipped: List[str] = []

    empty_oid = empty_blob_oid(repo)
    head_blobs = batch_head_blobs(repo, deleted, skipped) if deleted else {}

    # 只哈希大小在上限内的 untracked 普通文件；超限者单独记账，绝不静默混入结论
    hashable: List[str] = []
    size_excluded: List[str] = []
    # Codex round-2 C-1：原来只有「超限」被记账，symlink / 非普通文件 / stat 失败
    # / 含换行路径统统静默跳过，结果这些候选缺席时仍会给出 no_candidate 这种
    # **肯定性结论**。现在逐条记原因；池非空 ⇒ 不得宣称「没有内容同一副本」。
    unhashed: Dict[str, str] = {}
    for u in untracked:
        if "\n" in u:
            unhashed[u] = "path_contains_newline"
            continue
        fp = Path(repo) / u
        try:
            if fp.is_symlink():
                unhashed[u] = "symlink"
                continue
            if not fp.is_file():
                unhashed[u] = "not_regular_file"
                continue
            if fp.stat().st_size <= HASH_SIZE_CAP:
                hashable.append(u)
            else:
                size_excluded.append(u)
                unhashed[u] = "over_hash_size_cap"
        except OSError as exc:
            unhashed[u] = f"oserror:{type(exc).__name__}"
            continue
    unt_blobs = batch_worktree_blobs(repo, hashable, skipped)
    size_excluded_names = {os.path.basename(u) for u in size_excluded}

    # 未跟踪文件若与 HEAD 中某个受控路径的 git blob 身份相同（即 clean filter 之后的
    # 内容同一），它就是副本而不是「未入库的新内容」。
    tracked_index = head_blob_index(repo)
    duplicate_of_tracked: Dict[str, List[str]] = {}
    for u, sha in unt_blobs.items():
        if sha and sha != empty_oid and sha in tracked_index:
            duplicate_of_tracked[u] = sorted(tracked_index[sha])

    if not deleted:
        return {}, {}, duplicate_of_tracked, skipped, unhashed, unt_blobs

    by_content: Dict[str, List[str]] = {}
    for u, sha in unt_blobs.items():
        if sha and sha != empty_oid:
            by_content.setdefault(sha, []).append(u)
    by_basename: Dict[str, List[str]] = {}
    for u in untracked:
        by_basename.setdefault(os.path.basename(u), []).append(u)

    head_sizes = (
        head_blob_sizes(repo, [d for d in deleted if "\n" not in d]) if deleted else {}
    )

    out: Dict[str, Relocation] = {}
    dest_to_src: Dict[str, List[str]] = {}
    for d in deleted:
        hb = head_blobs.get(d)
        content_hits = sorted(by_content.get(hb, [])) if hb and hb != empty_oid else []
        if content_hits:
            low = (head_sizes.get(d) or 0) <= LOW_ENTROPY_MAX_BYTES
            # Codex round-3 C-2：低熵与多候选可以同时成立，原来 elif 会让
            # 「≤64 字节且多候选」的条目丢掉 low_entropy 标签，与文档口径不符。
            if len(content_hits) > 1 and low:
                kind = "content_sha_ambiguous_low_entropy"
            elif len(content_hits) > 1:
                kind = "content_sha_ambiguous"
            elif low:
                kind = "content_sha_low_entropy"
            else:
                kind = "content_sha"
            out[d] = Relocation("moved_identical", content_hits, hb, kind)
            for c in content_hits:
                dest_to_src.setdefault(c, []).append(d)
            continue
        name_hits = sorted(by_basename.get(os.path.basename(d), []))
        # C-1: 有超限同名候选时，结论只能是「因大小未取证」，不能冒充内容判定
        if os.path.basename(d) in size_excluded_names:
            out[d] = Relocation("evidence_skipped_size", name_hits, hb, "size_excluded")
            continue
        if hb == empty_oid:
            out[d] = Relocation(
                "evidence_skipped_empty_blob", name_hits, hb, "empty_blob_excluded"
            )
            continue
        # Codex round-3 C-1：HEAD 侧也可能取不到 blob——含换行的被删路径被 batch
        # 跳过（head_blob=None）、gitlink（mode 160000）不是 blob。这两种情况下
        # 「没有内容同一副本」同样无从谈起，必须走无结论，不能落 no_candidate。
        if hb is None:
            out[d] = Relocation(
                "evidence_incomplete_head", name_hits, hb, "head_blob_unavailable"
            )
            continue
        # Codex round-5 F6：HEAD twin 是**正证据**——「同内容 blob 就在 HEAD 的另一个
        # 受控路径上」这句话的成立与否，和未跟踪池完不完整毫无关系。它必须先于
        # 下面那道全局 unhashed 门，否则一个无关的未跟踪 symlink 就能把一条确凿的
        # 正证据压成「证据不全」。
        head_twins_early = sorted(x for x in tracked_index.get(hb, []) if x != d)
        if head_twins_early:
            out[d] = Relocation(
                "content_still_in_head",
                head_twins_early,
                hb,
                "same_blob_at_other_tracked_path",
            )
            continue
        # 未哈希池非空 ⇒ 「工作树里没有同内容副本」这句话无法成立，只能报「证据不全」。
        if unhashed:
            out[d] = Relocation(
                "evidence_incomplete_pool", name_hits, hb, "unhashed_candidates_exist"
            )
            continue
        # HEAD twin 已在上面（unhashed 门之前）判过，这里不再重复——
        # round-6 F6-DEAD：round-4 留下的第二段判定与上面逐字相同，是不可达死代码，已删。
        if name_hits:
            out[d] = Relocation(
                "same_name_diff_content", name_hits, hb, "basename_only"
            )
        else:
            out[d] = Relocation("no_candidate", [], hb, "none")
    return out, dest_to_src, duplicate_of_tracked, skipped, unhashed, unt_blobs


# ---------------------------------------------------------------------------
# owner 归属
# ---------------------------------------------------------------------------

OWNER_UNASSIGNED = "未分配·需裁定"

CARD_TAG_HINTS = ("CARD-", "BATCH-")


def owner_from_last_commit(repo: str, path: str) -> Optional[str]:
    """从最后一次触碰该路径的 commit subject 里抽 CARD/BATCH 标记。"""
    try:
        subj = git_text(repo, ["log", "-1", "--format=%h %s", "--", path])
    except GitError:
        return None
    if not subj:
        return None
    if any(tag in subj for tag in CARD_TAG_HINTS):
        return subj
    return f"{subj}（commit 无 CARD/BATCH 标记）"


def unhashed_ok_paths(
    repo: str, records: Sequence["Record"], unhashed: Dict[str, str]
) -> List[str]:
    """本应能被哈希的未跟踪普通文件（用于独立重算取证是否真的发生过）。"""
    out: List[str] = []
    for r in records:
        if r.xy != "??" or r.path in unhashed or "\n" in r.path:
            continue
        fp = Path(repo) / r.path
        try:
            if (
                fp.is_file()
                and not fp.is_symlink()
                and fp.stat().st_size <= HASH_SIZE_CAP
            ):
                out.append(r.path)
        except OSError:
            continue
    return out


def git_rev_parse_ok(repo: str, ref: str) -> bool:
    """该 ref 在此仓能否解析。round-6 F2-A：ref 缺失（分支被删/改名/浅克隆）时
    三态比对会整体静默缺席，必须显式记账而不是当成「不在 feature 分支上」。"""
    return (
        subprocess.run(
            [
                "git",
                "-C",
                repo,
                *GIT_READONLY_ARGS,
                "rev-parse",
                "--verify",
                "--quiet",
                ref,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def worktree_blob_oid(repo: str, path: str) -> Optional[str]:
    """磁盘上该路径的 blob OID（普通文件才有）；取不到返回 None。"""
    if "\n" in path:
        return None
    fp = Path(repo) / path
    try:
        if fp.is_symlink() or not fp.is_file():
            return None
    except OSError:
        return None
    proc = subprocess.run(
        ["git", "-C", repo, *GIT_READONLY_ARGS, "hash-object", "--", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    oid = proc.stdout.decode("utf-8", "replace").strip()
    return oid or None


def branch_blob_oid(repo: str, branch: str, path: str) -> Optional[str]:
    """该 ref 下此路径的 blob OID；不存在返回 None。

    Codex round-5 F2：原来只做 ``cat-file -e``（存在性），于是「同路径在 feature
    分支也有」被一律说成「主仓落后」。实测 75 条里 **20 条内容不同**，而且两个
    HEAD **互不为祖先**——「落后」这个说法在拓扑上根本不成立。必须拿到 OID
    才能区分「同内容」与「内容分歧」。
    """
    if "\n" in path:
        return None
    proc = subprocess.run(
        ["git", "-C", repo, *GIT_READONLY_ARGS, "rev-parse", f"{branch}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    oid = proc.stdout.decode("utf-8", "replace").strip()
    return oid or None


# ---------------------------------------------------------------------------
# 单仓盘点
# ---------------------------------------------------------------------------


@dataclass
class Entry:
    xy: str
    path: str
    orig: Optional[str]
    state: str  # tracked_modified / tracked_deleted / untracked / other
    category: str
    rule: str
    rule_why: str
    disposition: str
    owner: Optional[str] = None
    relocation: Optional[dict] = None
    duplicate_of_tracked: Optional[List[str]] = None
    feature_branch_state: Optional[str] = None
    needs_manual_review: bool = False

    def to_json(self) -> dict:
        d = {
            "xy": self.xy,
            "path": self.path,
            "state": self.state,
            "category": self.category,
            "rule": self.rule,
            "disposition": self.disposition,
        }
        if self.orig is not None:
            d["orig"] = self.orig
        if self.owner is not None:
            d["owner"] = self.owner
        if self.relocation is not None:
            d["relocation"] = self.relocation
        if self.duplicate_of_tracked:
            d["duplicate_of_tracked"] = self.duplicate_of_tracked
        if self.feature_branch_state:
            d["feature_branch_state"] = self.feature_branch_state
        if self.needs_manual_review:
            d["needs_manual_review"] = True
        return d


def state_of(xy: str) -> str:
    if xy == "??":
        return "untracked"
    if "D" in xy:
        return "tracked_deleted"
    if "M" in xy:
        return "tracked_modified"
    return "tracked_other"


@dataclass
class TargetReport:
    label: str
    path: str
    note: str
    head_sha: str = ""
    branch: str = ""
    porcelain_sha_before: str = ""
    porcelain_sha_after: str = ""
    record_count: int = 0
    entries: List[Entry] = field(default_factory=list)
    roundtrip_ok: bool = False
    evidence_skipped: List[str] = field(default_factory=list)
    filter_drivers: List[str] = field(default_factory=list)
    filter_drivers_accepted: bool = False
    feature_ref_resolvable: bool = False
    feature_ref_oid: Optional[str] = None
    unhashed_untracked: Dict[str, str] = field(default_factory=dict)
    rule_coverage: Optional[dict] = None
    assertions: Dict[str, bool] = field(default_factory=dict)

    @property
    def category_counts(self) -> Dict[str, int]:
        counts = {c: 0 for c in CATEGORIES}
        for e in self.entries:
            counts[e.category] += 1
        return counts

    @property
    def state_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.entries:
            counts[e.state] = counts.get(e.state, 0) + 1
        return counts

    def to_json(self, include_entries: bool = True) -> dict:
        return {
            "label": self.label,
            "path": self.path,
            "note": self.note,
            "head_sha": self.head_sha,
            "branch": self.branch,
            "porcelain_sha256_before": self.porcelain_sha_before,
            "porcelain_sha256_after": self.porcelain_sha_after,
            "readonly_proof_ok": self.porcelain_sha_before == self.porcelain_sha_after,
            "record_count": self.record_count,
            "classified_count": len(self.entries),
            "roundtrip_ok": self.roundtrip_ok,
            "evidence_skipped_newline_paths": self.evidence_skipped,
            "custom_filter_drivers": self.filter_drivers,
            "custom_filter_drivers_accepted_by_flag": self.filter_drivers_accepted,
            "feature_ref_resolvable": self.feature_ref_resolvable,
            "feature_ref_oid": self.feature_ref_oid,
            "rule_coverage_over_all_tracked": self.rule_coverage,
            "unhashed_untracked_with_reason": self.unhashed_untracked,
            "assertions": self.assertions,
            "category_counts": self.category_counts,
            "state_counts": self.state_counts,
            **(
                {"entries": [e.to_json() for e in self.entries]}
                if include_entries
                else {
                    "entries_omitted": "--brief：逐条数组见首跑台账 json，复跑证据只留 diff 与断言"
                }
            ),
        }


def disposition_for(
    entry_state: str,
    category: str,
    reloc: Optional[Relocation],
    on_feature: bool,
    relocation_sources: Optional[List[str]] = None,
    duplicate_of: Optional[List[str]] = None,
    feature_state: Optional[str] = None,
) -> Tuple[str, bool]:
    """返回 (处置建议, 是否需人工裁定)。台账只给建议，本卡不执行任何处置。"""
    if entry_state == "tracked_deleted":
        if reloc and reloc.verdict == "moved_identical":
            return (
                "未决搬迁：内容同一副本已落地未跟踪区，但搬迁未提交——禁删禁移，归 DEBT-14 合并策略裁定",
                True,
            )
        if reloc and reloc.verdict == "same_name_diff_content":
            return ("同名但内容不同：不能按搬迁处理，需逐文件人审后再裁定", True)
        if reloc and reloc.verdict == "evidence_skipped_size":
            return (
                f"⚠️ 未取证（同名候选超过 {HASH_SIZE_CAP // (1024 * 1024)}MB 哈希上限）："
                "本台账对该条**没有内容结论**，不得据此判搬迁或真删除，需人工比对",
                True,
            )
        if reloc and reloc.verdict == "evidence_incomplete_head":
            return (
                "⚠️ 未取证（HEAD 侧拿不到该路径的 blob——路径含换行走不了 batch 协议，"
                "或该条目是 gitlink/子模块而非普通文件）：本台账对它没有内容结论，需人工比对",
                True,
            )
        if reloc and reloc.verdict == "evidence_incomplete_pool":
            return (
                "⚠️ 未取证（工作树里存在未能哈希的未跟踪文件——超限/符号链接/非普通文件/"
                "路径含换行/stat 失败）：**不能**断言「没有内容同一副本」，需人工比对",
                True,
            )
        if reloc and reloc.verdict == "evidence_skipped_empty_blob":
            return (
                "⚠️ 未取证（HEAD 侧为空文件，空 blob sha 全仓恒等，内容匹配无鉴别力）："
                "本台账对该条没有内容结论，需人工比对",
                True,
            )
        if reloc and reloc.verdict == "content_still_in_head":
            twin = reloc.candidates[0] if reloc.candidates else "?"
            return (
                f"删除未提交，但同内容 blob 仍在 HEAD 的受控路径 `{twin}` 上——内容可还原，"
                "风险是「删除被提交」而非「内容丢失」；归 DEBT-14 裁定",
                True,
            )
        # ⚠️ 这里只说"本次盘点没找到"，不说"不可还原"——本台账只查了未跟踪池与本仓
        # HEAD 树，没做全 ref 可达性分析，证不出否定命题（Codex round-3/4）。
        # ⚠️ 证明域（Codex round-5 F5）：本次扫描的候选池 = **porcelain 可见且非 ignored**
        # 的未跟踪文件 + 本仓 HEAD 树的其他路径。被 gitignore 排除的子树（例如挂在
        # `.claude/worktrees/` 下的各 worktree）完全不在扫描范围内——实测本仓三条
        # no_candidate 在 ignored 子树里都能找到同内容物理副本。所以这里只能说
        # 「本次可见范围内没找到」，绝不能说「不可还原」。
        return (
            "在**本次可见候选池**（porcelain 可见且非 ignored 的未跟踪文件 + 本仓 HEAD 的其他路径）"
            "中未找到同内容副本：删除意图未提交，需用户显式裁定。"
            "⚠️ 这**不等于「不可还原」**——ignored 子树未扫描，也未做全 ref 可达性分析，"
            "同内容对象可能存在于别的分支或被忽略的目录里",
            True,
        )
    if entry_state == "tracked_modified":
        return ("已跟踪文件的未提交修改：由 owner 卡在其分支内提交，本卡只登记", False)
    # untracked
    if duplicate_of:
        head = duplicate_of[0]
        more = f"（另 {len(duplicate_of) - 1} 处）" if len(duplicate_of) > 1 else ""
        return (
            f"副本而非新内容：与 HEAD 中受控路径 `{head}`{more} 的 git blob 身份相同"
            "（即 clean filter 之后的内容同一）——"
            "不是「未入库的新代码」，处置等同于归档区其余条目，归 DEBT-14 裁定",
            True,
        )
    if relocation_sources:
        head = relocation_sources[0]
        more = (
            f"（另 {len(relocation_sources) - 1} 个同内容来源，方向未定）"
            if len(relocation_sources) > 1
            else ""
        )
        tail = "；⚠️ 位移方向未经独立证实，类别一律按本路径自身规则判定，不继承来源"
        return (
            f"未决搬迁的目的地：与 tracked 删除 `{head}`{more} 的 git blob 身份相同——"
            f"禁删禁移，与来源成对归 DEBT-14 裁定{tail}",
            True,
        )
    # ⛔ Codex round-5 F2：这里原来一律写「主仓落后」。实测 75 条里 20 条内容不同，
    # 且两个 HEAD 互不为祖先——「落后」既非事实也无拓扑依据，按它单向覆盖会丢改动。
    if feature_state == "same_blob":
        return (
            f"同路径已在 {FEATURE_BRANCH} 受控**且 git blob 身份相同**（即 clean filter 之后内容同一）"
            "——主仓这份是未纳管的同内容副本，"
            "归 DEBT-14 合并策略裁定，勿在主仓单独提交",
            True,
        )
    if feature_state == "diverged":
        return (
            f"⚠️ 同路径在 {FEATURE_BRANCH} 也受控，但**内容不同**，且两个 HEAD 互不为祖先——"
            "这不是「主仓落后」，是**双向分歧**：禁止单向覆盖（`-X ours/theirs` 一律不适用），"
            "须逐 hunk 人审，归 DEBT-14",
            True,
        )
    if feature_state == "unverifiable_path_contains_newline":
        return (
            f"⚠️ 路径含换行，与 {FEATURE_BRANCH} 的关系**未取证**（走不了参数化查询）——"
            "既不能说同内容也不能说不存在，需人工比对",
            True,
        )
    if on_feature:
        return (
            f"同路径在 {FEATURE_BRANCH} 存在，但本地内容无法取证（不可哈希）——关系未定，需人工比对",
            True,
        )
    if category == CAT_USER:
        return ("用户资产：保持原地，禁删除禁移动；若需纳管由用户显式裁定", False)
    if category == CAT_REVIEW:
        return ("审查产物：保持原地；是否入库由所属批次收尾时裁定", False)
    if category == CAT_EPHEMERAL:
        return ("临时物：可安全忽略；本卡不执行清理（只登记）", False)
    return ("应提交代码但未受控：需指认 owner 卡并由该卡提交", True)


def census_one(
    label: str,
    repo: str,
    note: str,
    pin: Optional[str],
    resolve_owner: bool,
    allow_filter_drivers: bool = False,
) -> TargetReport:
    rep = TargetReport(label=label, path=repo, note=note)

    if not (Path(repo) / ".git").exists():
        raise GitError(f"{repo} 不是 git 工作树（无 .git）")

    rep.head_sha = git_text(repo, ["rev-parse", "HEAD"])
    rep.branch = git_text(repo, ["rev-parse", "--abbrev-ref", "HEAD"])

    # A-2：--no-optional-locks 不是只读沙箱。自定义 clean/process filter 会在
    # hash-object 时被 git 执行，可在被盘点工作树里留下副作用；副作用若被 gitignore
    # 覆盖，前后 porcelain sha256 还会照常相等——只读取证会给出假绿。检出即拒。
    rep.filter_drivers = custom_filter_drivers(repo)
    if rep.filter_drivers and not allow_filter_drivers:
        raise AssertionError(
            f"[{label}] 检出自定义 git filter 驱动 {rep.filter_drivers}——"
            "内容取证会执行它们，只读保证不成立。确认可接受后加 --allow-filter-drivers 重跑。"
        )
    # --allow-filter-drivers 的语义是"已知情并接受"，那就必须真的放行；
    # 原先它跳过异常却仍把断言写 False，末尾照样 exit 2——既执行了风险又不产台账，
    # 两头落空（Codex round-2 A-2）。现在：接受即断言为真，风险如实记在报告里。
    rep.filter_drivers_accepted = bool(rep.filter_drivers) and allow_filter_drivers
    # Codex round-4 A-2：断言名叫 "no_custom_filter_drivers" 而在 allow 模式下
    # 仍写 True，等于把"风险被接受"说成"驱动不存在"。改名为如实描述的语义。
    rep.assertions["filter_drivers_absent_or_accepted"] = (
        not rep.filter_drivers or allow_filter_drivers
    )

    if pin:
        # 单向前缀断言，不留「反向也算过」的逃生口——那种写法会让 pin 门形同虚设。
        if not rep.head_sha.startswith(pin):
            raise AssertionError(
                f"[{label}] --pin-sha 基线校验失败：期望 HEAD 以 {pin} 开头，实际 {rep.head_sha}"
            )
        rep.assertions["pin_sha_ok"] = True

    raw_before = porcelain(repo)
    rep.porcelain_sha_before = hashlib.sha256(raw_before).hexdigest()

    records = parse_porcelain(raw_before)
    # 期望值来自独立命令，不从 records 自身推导
    rep.record_count = porcelain_line_count(repo)
    rep.assertions["parsed_count_matches_independent_count"] = (
        len(records) == rep.record_count
    )

    # 断言：orig 字段只能、且必须出现在 R/C 记录上——挡「XY 序列与字节往返都对，
    # 但 orig 挂错了记录」的分组错（Codex round-2 A-3 反例：
    # b"R  dest\0?? fake\0?? actual\0" 被错解成 R(dest) + ??(fake, orig=actual)，
    # 记录数、XY 序列、字节往返三者同时成立，真实的 actual 却被吞了）
    rep.assertions["orig_field_iff_rename_or_copy"] = all(
        (r.orig is not None) == ("R" in r.xy or "C" in r.xy) for r in records
    )

    # 断言：XY 序列与独立命令一致——挡「字段分组错但字节序不变」
    rep.assertions["xy_sequence_matches_independent_parse"] = [
        r.xy for r in records
    ] == porcelain_xy_sequence(repo)

    # 断言：字节往返
    rebuilt = roundtrip(records)
    rep.roundtrip_ok = rebuilt == raw_before
    rep.assertions["roundtrip_bytes_identical"] = rep.roundtrip_ok

    (
        reloc_map,
        dest_to_src,
        dup_map,
        evidence_skipped,
        unhashed,
        unt_blobs_used,
    ) = build_relocation_map(repo, records)
    rep.evidence_skipped = evidence_skipped
    rep.unhashed_untracked = unhashed

    # round-6 F2-A：原来用 `label == "main"` 当隐藏角色开关——改个 label 就让最重的
    # 20 条 diverged 静默消失。改为**按仓判定**：只要该仓能解析出 FEATURE_BRANCH，
    # 就对它做三态比对。ref 不可解析时显式记账，不静默跳过。
    feature_ref_ok = (
        git_rev_parse_ok(repo, FEATURE_BRANCH)
        if repo != FEATURE_WORKTREE_PATH
        else False
    )
    rep.feature_ref_resolvable = feature_ref_ok
    if feature_ref_ok:
        rep.feature_ref_oid = git_text(repo, ["rev-parse", FEATURE_BRANCH])
    # round-6 F2-A：这条断言的语义是「三态证据源的状态已被如实记账」——
    # 它对本仓自身（feature worktree）与 ref 缺失都为真，但**产物里必须留下痕迹**：
    # feature_ref_resolvable / feature_ref_oid 两个字段就是那道痕迹。
    # 缺了它们，20 条 diverged 的「禁止单向覆盖」警告会整节静默消失而无人知晓。
    rep.assertions["feature_ref_resolvable_or_declared"] = (
        rep.feature_ref_resolvable is not None
    )
    for r in records:
        st = state_of(r.xy)
        srcs = dest_to_src.get(r.path) if st == "untracked" else None
        src = srcs[0] if srcs else None
        # Codex round-2 C-2：类别继承（A-INHERIT）是循环论证——用内容相等反推
        # 位移来源，再用来源覆盖目的地的类别。三条件收窄仍挡不住反例（65 字节的
        # workspace.json 就能把归档区目的地继承成「临时物」）。**直接废除继承**：
        # 目的地一律用自身路径规则判别（archive/ 已有 A1/A2/A3 覆盖，实测 729 条
        # 继承项全是代码→代码，废除后类别零变化），位移证据只作 relocation 字段。
        category, rule_id, why = classify(r.path)
        reloc = reloc_map.get(r.path) if st == "tracked_deleted" else None
        # feature 侧同路径的三态：不在 / 同内容 / 内容分歧（Codex round-5 F2）
        feature_state = None
        if feature_ref_ok and st == "untracked" and not src:
            if "\n" in r.path:
                # round-6 F2-C：含换行的路径走不了 batch/参数化查询，「取不到」
                # 与「不在 feature 分支上」完全同形。显式记为未取证，不静默归零。
                feature_state = "unverifiable_path_contains_newline"
            else:
                fb = branch_blob_oid(repo, FEATURE_BRANCH, r.path)
                if fb is not None:
                    local = worktree_blob_oid(repo, r.path)
                    if local is None:
                        feature_state = "present_local_unhashable"
                    elif local == fb:
                        feature_state = "same_blob"
                    else:
                        feature_state = "diverged"
        on_feature = feature_state is not None
        dup = dup_map.get(r.path) if st == "untracked" and not src else None
        disp, manual = disposition_for(
            st, category, reloc, on_feature, srcs, dup, feature_state
        )
        # Codex round-3 B-3：Z1 的 manual 原来在 owner 计算之后才置位，
        # 于是 catch-all 条目拿到 needs_manual_review=true 却没有 owner。提前。
        if rule_id == CATCHALL_RULE:
            manual = True

        owner: Optional[str] = None
        if category == CAT_CODE or manual:
            if st == "tracked_deleted" or srcs:
                owner = "DEBT-14（分叉对账与合并策略裁定）· 未决"
            elif dup:
                owner = f"内容同一于受控路径 `{dup[0]}` → DEBT-14 归档策略"
            elif feature_state == "same_blob":
                owner = f"{FEATURE_BRANCH} 已受控且内容相同 → DEBT-14 合并策略"
            elif feature_state == "diverged":
                owner = f"⚠️ 与 {FEATURE_BRANCH} 同路径但内容分歧 → DEBT-14 逐 hunk 人审"
            elif on_feature:
                owner = f"{FEATURE_BRANCH} 同路径存在（关系未取证） → DEBT-14 合并策略"
            elif st in ("tracked_modified", "tracked_other") and resolve_owner:
                owner = owner_from_last_commit(repo, r.path) or OWNER_UNASSIGNED
            else:
                owner = OWNER_UNASSIGNED

        rel_json = None
        if reloc:
            rel_json = {
                "verdict": reloc.verdict,
                "match_kind": reloc.match_kind,
                "head_blob": reloc.head_blob,
                "candidates": reloc.candidates,
            }
        elif srcs:
            # C-3 整改：目的地侧原来只写标量 source，把「多个删除来源指向同一内容」
            # 静默压成第一个遍历到的来源——与台账「本卡不替它选」自相矛盾。改为全列。
            # Codex round-2 C-2 追加：目的地的 match_kind 原来只按来源数量生成，
            # 会把来源侧标了 low_entropy 的证据在目的地重新写成普通 content_sha。
            # 现在把来源侧的证据质量原样传播过来。
            src_kinds = {reloc_map[x].match_kind for x in srcs if x in reloc_map}
            # Codex round-4 C-2：目的地原来先判 len(srcs)>1，于是来源侧已标的
            # low_entropy 在目的地被丢掉。两个维度都要保留。
            multi = len(srcs) > 1
            low = any("low_entropy" in k for k in src_kinds)
            if multi and low:
                dest_kind = "content_sha_multi_source_low_entropy"
            elif multi:
                dest_kind = "content_sha_multi_source"
            elif low:
                dest_kind = "content_sha_low_entropy"
            else:
                dest_kind = "content_sha"
            rel_json = {
                "verdict": "relocation_destination",
                "match_kind": dest_kind,
                "sources": sorted(srcs),
                "category_inherited_from_source": False,
            }

        rep.entries.append(
            Entry(
                xy=r.xy,
                path=r.path,
                orig=r.orig,
                state=st,
                category=category,
                rule=rule_id,
                rule_why=why,
                disposition=disp,
                owner=owner,
                relocation=rel_json,
                duplicate_of_tracked=dup,
                feature_branch_state=feature_state,
                needs_manual_review=manual,
            )
        )

    # 断言：计数
    rep.assertions["count_equals_porcelain_records"] = (
        len(rep.entries) == rep.record_count
    )

    # round-6 A1：上面那条只绑「行数」。`path=(r.orig or r.path)` 这种**整列写错**
    # 能让台账把 rename 的目的地整条换掉，而计数、XY、往返、orig 四门全 PASS。
    # 这里把 records → entries 这一跳的三元组逐条钉死。
    rep.assertions["entries_preserve_record_identity"] = [
        (r.xy, r.path, r.orig) for r in records
    ] == [(e.xy, e.path, e.orig) for e in rep.entries]

    # round-6 A2：§四 的内容级取证此前**零门覆盖**——把 unt_blobs 整体置 None
    # 就能把 moved_identical 翻成 no_candidate，而所有门照样全 PASS。
    #
    # ⚠️ 第一版这道门只查「内部一致性」，实测**没抓住**该变异：取证瞎掉后的输出
    # 内部是自洽的（它只是说"没找到副本"，而这在没有独立信息源时无法证伪）。
    # 这与计数门上学过的是同一课——**期望值必须来自被验证对象之外**。
    # 所以这道门分两半：
    #   ①（独立重算）另起一次 git hash-object，重算若干应可哈希的未跟踪文件，
    #      验证它们的 OID 确实进了本次实际使用的内容索引；
    #   ②（内部一致性）判定与证据字段之间不得自相矛盾。
    _sample = [u for u in sorted(unhashed_ok_paths(repo, records, unhashed))][:32]
    _recomputed = batch_worktree_blobs(repo, _sample) if _sample else {}
    _evidence_live = all(
        _recomputed.get(u) is not None and unt_blobs_used.get(u) == _recomputed.get(u)
        for u in _sample
    )
    rep.assertions["content_evidence_independently_recomputable"] = _evidence_live
    _pos = {
        "moved_identical",
        "content_still_in_head",
        "same_name_diff_content",
        "no_candidate",
    }
    _inc = {"evidence_incomplete_pool", "evidence_incomplete_head"}
    _paths = {e.path for e in rep.entries}
    _ok = True
    for e in rep.entries:
        rj = e.relocation or {}
        v = rj.get("verdict")
        if v in _pos and v != "no_candidate" and not rj.get("head_blob"):
            _ok = False  # 有内容结论却没有 HEAD 侧 blob
        if v == "evidence_incomplete_pool" and not rep.unhashed_untracked:
            _ok = False  # 说池不完整，池却是空的
        if v == "relocation_destination":
            srcs = rj.get("sources") or []
            if not srcs or any(x not in _paths for x in srcs):
                _ok = False  # 位移目的地回指不到来源
    if rep.unhashed_untracked and any(
        (e.relocation or {}).get("verdict")
        in ("no_candidate", "same_name_diff_content")
        for e in rep.entries
    ):
        _ok = False  # 池不完整却仍给出「没找到」这种肯定结论
    rep.assertions["relocation_evidence_self_consistent"] = _ok

    raw_after = porcelain(repo)
    rep.porcelain_sha_after = hashlib.sha256(raw_after).hexdigest()
    rep.assertions["readonly_porcelain_unchanged"] = (
        rep.porcelain_sha_before == rep.porcelain_sha_after
    )

    return rep


# ---------------------------------------------------------------------------
# baseline diff
# ---------------------------------------------------------------------------


def diff_against_baseline(reports: Sequence[TargetReport], baseline_path: Path) -> dict:
    # Codex round-5 F4：只读一次原始字节，**同一份 bytes** 既算 digest 又做解析——
    # 分两次读会让"产物里记的 digest"和"实际用来 diff 的内容"可能不是同一份。
    baseline_bytes = baseline_path.read_bytes()
    baseline_digest = hashlib.sha256(baseline_bytes).hexdigest()
    baseline = json.loads(baseline_bytes.decode("utf-8"))
    base_by_label = {t["label"]: t for t in baseline.get("targets", [])}
    result: dict = {
        "baseline_file": str(baseline_path),
        "baseline_sha256": baseline_digest,
        "baseline_size_bytes": len(baseline_bytes),
        "baseline_generated_at_utc": baseline.get("generated_at_utc"),
        "targets": [],
    }
    for rep in reports:
        base = base_by_label.get(rep.label)
        if base is None:
            result["targets"].append(
                {"label": rep.label, "status": "新增目标（基线中不存在）"}
            )
            continue
        # round-6 F8-ORDER：三态校验原来放在 base_entries 构造之后，
        # 于是畸形形态（字符串 / 非空 dict）会先在这一行抛 TypeError，
        # 校验的错误信息永远到不了用户。校验必须在**使用之前**。
        raw_entries = base.get("entries")
        if isinstance(raw_entries, list):
            base_has_entries = True
        elif raw_entries is None and base.get("entries_omitted"):
            base_has_entries = False
        else:
            raise GitError(
                f"基线目标 `{base.get('label')}` 的 entries 字段形态非法（{type(raw_entries).__name__}）："
                "合法形态只有 list（完整）或 缺失+entries_omitted（brief）。"
            )
        base_entries = {e["path"]: e for e in (raw_entries or [])}
        now_entries = {e.path: e.to_json() for e in rep.entries}
        # Codex round-3：基线若是 --brief 生成（无 entries），按空集合算会把全部
        # 条目假报成 added（实测 main 假报 2027、feature 假报 106）。此时逐条 diff
        # 一律标不可用，不产生任何逐条集合。
        if not base_has_entries:
            added = removed = []
        else:
            added = sorted(set(now_entries) - set(base_entries))
            removed = sorted(set(base_entries) - set(now_entries))
        recategorized = (
            sorted(
                p
                for p in (set(now_entries) & set(base_entries))
                if now_entries[p].get("category") != base_entries[p].get("category")
            )
            if base_has_entries
            else []
        )
        # Codex round-2：原来只比 path 与 category，于是同一路径的 relocation.verdict
        # 从 no_candidate 变成 moved_identical 也照样显示「改类 0」。改为比较整条
        # 规范化 entry（xy/orig/state/rule/category/disposition/owner/relocation/
        # duplicate/manual），任何一维变化都能看见。
        DIFF_KEYS = (
            "xy",
            "orig",
            "state",
            "category",
            "rule",
            "disposition",
            "owner",
            "relocation",
            "duplicate_of_tracked",
            "feature_branch_state",
            "needs_manual_review",
        )

        def _norm(e: dict) -> dict:
            return {k: e.get(k) for k in DIFF_KEYS}

        changed = []
        for path in (
            sorted(set(now_entries) & set(base_entries)) if base_has_entries else []
        ):
            a, b = _norm(base_entries[path]), _norm(now_entries[path])
            if a != b:
                changed.append(
                    {
                        "path": path,
                        "fields": sorted(k for k in DIFF_KEYS if a.get(k) != b.get(k)),
                        "from": {k: a[k] for k in DIFF_KEYS if a.get(k) != b.get(k)},
                        "to": {k: b[k] for k in DIFF_KEYS if a.get(k) != b.get(k)},
                    }
                )
        result["targets"].append(
            {
                "label": rep.label,
                "head_sha_baseline": base.get("head_sha"),
                "head_sha_now": rep.head_sha,
                "head_moved": base.get("head_sha") != rep.head_sha,
                "porcelain_sha_baseline": base.get("porcelain_sha256_after"),
                "porcelain_sha_now": rep.porcelain_sha_after,
                "record_count_baseline": base.get("record_count"),
                "record_count_now": rep.record_count,
                "added": added,
                "removed": removed,
                "recategorized": [
                    {
                        "path": p,
                        "from": base_entries[p].get("category"),
                        "to": now_entries[p].get("category"),
                    }
                    for p in recategorized
                ],
                "entry_changed": changed,
                "baseline_had_entries": base_has_entries,
                "assertions_baseline": base.get("assertions"),
                "assertions_now": rep.assertions,
            }
        )
    return result


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------

SHANGHAI = _dt.timezone(_dt.timedelta(hours=8))


_MD_CTRL = {c: f"<U+{c:04X}>" for c in range(0x20)}
_MD_CTRL[0x7F] = "<U+007F>"


def _md_escape(text: str) -> str:
    """Markdown 表格单元格的安全化（Codex round-2 A-4）。

    原来只转义 ``|``。但合法路径可以含换行、反引号、控制字符与非 UTF-8 字节
    （经 surrogateescape 变成 U+DC80-DCFF 的孤立代理），任何一种都能把表格拆坏
    或让写盘抛异常。这里把它们全部替换成可见的占位记号——台账要的是「人能看清
    这条路径长什么样」，不是「原样粘回 shell」。
    """
    out = []
    for ch in text:
        cp = ord(ch)
        if cp in _MD_CTRL:
            out.append(_MD_CTRL[cp])
        elif 0xDC80 <= cp <= 0xDCFF:  # surrogateescape 还原出的原始字节
            out.append(f"<0x{cp - 0xDC00:02X}>")
        elif ch == "|":
            out.append("\\|")
        elif ch == "`":
            # 反斜杠在单反引号 code span 内不转义 delimiter（Codex round-4 A-4），
            # 只能换成可见记号。
            out.append("<0x60>")
        else:
            out.append(ch)
    return "".join(out)


def render_md(
    reports: Sequence[TargetReport],
    diff: Optional[dict],
    generated_utc: str,
    generated_sh: str,
    argv: str,
    brief: bool = False,
    nested_declared: Optional[List[Dict[str, str]]] = None,
) -> str:
    L: List[str] = []
    A = L.append

    A("# 工作树资产分类台账（DEBT-13）")
    A("")
    A(f"> **生成**: {generated_sh}（沪时） / {generated_utc}（UTC）")
    A(
        f"> **生成器**: `scripts/census_worktree_assets.py`（只读）· 调用 `{_md_escape(argv)}`"
    )
    A("> **卡**: CARD-DEBT-13 · **批次**: BATCH-2026-08-31-第七批")
    A("> **性质**: 只登记，不处置。本台账不授权任何删除 / 移动 / 提交动作。")
    A("")

    A("## ⛔ 台账使用前必读")
    A("")
    A(
        "1. **主仓的 tracked 删除是「未决搬迁」，不是「已决归档」。** 工作树里文件没了、"
        "index 里还在，说明搬迁动作从未被提交。台账为每条删除给出了内容级取证"
        "（HEAD 侧 blob OID 由 `git cat-file --batch-check` 批量取得，工作树侧由 "
        "`git hash-object --stdin-paths` 取得，两者是同一套 git 内容身份），"
        "但**「存在同内容副本」只证明位移可逆，既不证明位移的因果方向，也不证明用户已同意归档**。"
        "处置方向归 DEBT-14 裁定。"
    )
    A(
        "2. **禁清理 `~/.claude/auto-sync.lock.d`。** 依据来自第七批开跑手册与 CARD-DEBT-15 的"
        "hook 面核查：主仓 `.claude/settings.json` 仍注册着「自动 stage + commit + push 全工作树」"
        "的 Stop hook，而那个 2026-05-14 遗留的僵尸锁目录是目前挡住它的闸门。"
        "⚠️ **本卡按只读边界未读取用户 home 目录**，因此「它是唯一阻挡」这一点在本卡内属 "
        "**UNVERIFIABLE·转述**，不是本台账独立证实的事实（Codex round-2 指出）——"
        "但无论如何，本台账登记的条目都在该 hook 的射程内，禁清理这条纪律照常适用。"
    )
    A(
        "3. **可恢复性对 tracked 与 untracked 不同——处置前必须分清。** "
        "tracked 删除（` D`）的内容仍在 HEAD 里，可从 git 对象库原样取回，"
        "所以对它的风险是「删除被提交」而不是「内容已丢」。"
        "untracked（`??`）文件没有这层保障——它们不在 index 里。"
        "⚠️ 但**不能一概说「不在任何 git 对象里、没有任何还原路径」**（首版台账如此写，"
        "是不实陈述，Codex round-2 抓出）：本台账自己就证明了主仓的未跟踪条目里有相当一部分"
        "（位移目的地 + 已受控内容的副本，逐条见 §四）内容与本仓 HEAD 中某个 blob 完全相同。"
        "⚠️ 而且**「不在本仓 HEAD 里」也不等于不可还原**（Codex round-3 反例）——"
        "同内容的 blob 可能存在于**别的 ref**（如 feature 分支）里；本台账的 `duplicate_of_tracked` "
        "只查本仓 HEAD 树，未做全 ref 可达性分析。"
        "所以准确说法是：**本台账能证明「可还原」，不能证明「不可还原」**。"
        "「禁删除」对 tracked 与 untracked 都适用。"
    )
    A(
        "4. **本次盘点对被盘点仓的读写边界**：脚本除 `--out-dir` 下的产出文件外，"
        "不对被盘点仓做任何写/删/移。"
        + (
            "⚠️ **本次 `--out-dir` 正落在被盘点目标的目录树内**（见下方嵌套声明）——"
            "也就是说本次运行确实往该目标的**文件系统**里创建并写入了产出文件，"
            "只是这些路径被该目标的 gitignore 排除、git 看不见。"
            "「只读」在这里指的是「不改动盘点输入」，**不是**「没有向该目录树写过任何东西」。"
            if nested_declared
            else "本次 `--out-dir` 与所有被盘点目标零交集。"
        )
        + "取证方式：每个目标仓在盘点前后各取一次 "
        "`git status --porcelain -uall -z` 的 sha256，见下表；两值相等即为「盘点未改动被盘点工作树」的取证。"
    )
    A("")

    A("## ⛔ 威胁模型（本台账「只读」二字的确切含义）")
    A("")
    A(
        "本脚本的「只读」防的是**误伤**：脚本除 `--out-dir` 下的产出文件外，"
        "不含任何写/删/移被盘点仓的代码路径；所有 git 调用带只读加固参数；"
        "产出目录与最终两个产出文件都在写盘前对被盘点目标做过身份级检查；"
        "盘点前后 porcelain 的 sha256 相等。"
    )
    A("")
    A(
        "**它不防的是：与本脚本并发运行、且对产出目录有写权限的攻击者。** 具体地——"
        "在检查与写入之间替换产出文件的父目录、用 bind/nullfs 把被盘点子树挂到别处造成 inode 链断开、"
        "并发 unlink 产出文件，这三类交错本脚本挡不住。这是**声明的边界，不是已解决的问题**："
        "本卡的使用场景是用户在自己的机器上盘点自己的仓库，没有并发攻击者；"
        "若要在敌对环境使用，需要把 mkdir/open 全部绑定到已验证的目录句柄（`openat` 系）——"
        "那是另一张卡的工作量，不在本卡范围。"
    )
    A("")
    A(
        "**只读取证本身的证明力**也有限：两次 porcelain sha256 相等只证明两个时点的 "
        "`(XY, path[, orig])` 字节相同，不证明文件内容 / 被 gitignore 的文件 / refs / object DB / "
        "git 配置未变，也不能把变化归因到本脚本还是并发进程。"
    )
    A("")
    A("## 一、盘点总览与断言")
    A("")
    A(
        "| 目标 | 路径 | HEAD | 分支 | porcelain 记录数 | 分类条目数 | 前 sha256 | 后 sha256 |"
    )
    A("| --- | --- | --- | --- | ---: | ---: | --- | --- |")
    for r in reports:
        A(
            f"| `{_md_escape(r.label)}` | `{_md_escape(r.path)}` | `{r.head_sha[:8]}` | "
            f"`{_md_escape(r.branch)}` | {r.record_count} | "
            f"{len(r.entries)} | `{r.porcelain_sha_before[:16]}…` | `{r.porcelain_sha_after[:16]}…` |"
        )
    A("")
    A("### 断言矩阵（任一 FAIL → 脚本 exit 2，台账不产出）")
    A("")
    A(
        "| 目标 | pin 基线 | 独立计数 | orig⇔R/C | XY 序列 | 分类对账 | 字节往返 | filter 无或已接受 | 只读取证 |"
    )
    A("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in reports:

        def mark(k: str) -> str:
            v = r.assertions.get(k)
            return "PASS" if v else ("FAIL" if v is False else "n/a")

        A(
            f"| `{r.label}` | {mark('pin_sha_ok')} | {mark('parsed_count_matches_independent_count')} | "
            f"{mark('orig_field_iff_rename_or_copy')} | "
            f"{mark('xy_sequence_matches_independent_parse')} | "
            f"{mark('count_equals_porcelain_records')} | "
            f"{mark('roundtrip_bytes_identical')} | {mark('filter_drivers_absent_or_accepted')} | "
            f"{mark('readonly_porcelain_unchanged')} |"
        )
    A("")
    A("每道门各挡一类错误，缺一不可：")
    A("")
    A(
        "- **独立计数**：记录数取自不带 `-z` 的 `git status --porcelain -uall` 行数，"
        "**不从解析结果自己推导**。否则「解析器丢了一条」会让期望值跟着一起变小、断言永远绿。"
        "（实证是变异 **M6**＝M1+M5 叠加：单跑 M1 时本门变红 rc=2；只有把期望值也改成自推导之后，"
        "两条计数门才同时哑火。——原文把这条归给 M1 是错的，与变异表自相矛盾。）"
        "期望值必须来自被验证对象之外。"
    )
    A(
        "- **orig⇔R/C**（⚠️ 对**数据**恒真，只对**解析器代码**有鉴别力）：`orig` 字段当且仅当"
        "出现在 R/C 记录上。挡「XY 序列、字节往返、"
        '计数三门同时成立，但 `orig` 挂错了记录」——反例 `b"R  dest\\0?? fake\\0?? actual\\0"` '
        "若被错解成 `R(dest)` + `??(fake, orig=actual)`，三门全绿而真实的 `actual` 被吞掉。"
        "（Codex round-2 A-3 促成新增；变异 M11 证明只有这道门能抓住它。）"
    )
    A(
        "- **XY 序列**：把每条记录的两字符状态码序列，与同一条独立命令的逐行行首比对。"
        "挡的是字节往返挡不住的一类错误——解析器把 NUL 字段**分组错**（例如把 rename 记录的"
        "来源字段当成下一条独立记录），字节序不变则重新序列化仍逐字节相同、记录数也可能仍相等，"
        "但真实的 rename 已经丢了。（Codex round-1 A-3 促成新增。）"
    )
    A("- **分类对账**：分类条目数 == 记录数，挡「有记录没进分类」。")
    A(
        "- **字节往返**（⚠️ 同为对**数据**恒真的门）：把解析出的每条记录重新序列化回 `-z` 格式，"
        "与 git 原始输出逐字节比对。挡「少解析一条 + 多分出一条」这类互相抵消、计数看不出来的错误。"
    )
    A(
        "- **filter 无或已接受**：`--no-optional-locks` 只禁用需要可选锁的操作，**不是只读沙箱**。"
        "自定义 `filter.<name>.clean` / `.process` 驱动是任意命令，会在 `git hash-object` 取证时被执行，"
        "可在被盘点工作树里留下副作用；副作用若恰好被 gitignore 覆盖，前后 porcelain sha256 还会照常相等——"
        "只读取证就给出假绿。故「目标仓无自定义 filter 驱动」是独立硬断言，检出即 exit 2"
        "（`--allow-filter-drivers` 可明示接受）。"
        "⚠️ 这道门 PASS 有**两种**含义：目标仓确实没有自定义驱动，**或者**有驱动但调用者用 "
        "`--allow-filter-drivers` 明示接受了风险。后者下取证过程**确实执行过外部命令**，"
        "「只读」不再成立——具体是哪种，看各目标的 `custom_filter_drivers` 与 "
        "`custom_filter_drivers_accepted_by_flag` 字段（Codex round-1 A-2 促成，round-4/5 正名）。"
    )
    A("")
    A(
        "⚠️ **关于「对数据恒真」的两道门**（`orig⇔R/C` 与 `字节往返`）：任何能被本解析器成功解析的"
        "输入都必然让它们为真——20 万条对抗性 fuzz 输入里 8 万余条解析成功，两门零失败。"
        "所以它们的 PASS **不代表「这个目标的数据通过了检查」**，只代表「解析器代码这一版没被改坏」。"
        "它们的价值在变异测试里（M2/M8/M11 实证），不在逐目标的矩阵格子里。"
    )
    A("")
    A(
        "**只读取证能证明什么、不能证明什么**：两次 porcelain sha256 相等，只证明两个时点的 "
        "`(XY, path[, orig])` 字节相同。它**不能**证明文件内容、被 gitignore 的文件、refs/reflog/object DB、"
        "git 配置未变，也不能证明「写后又恢复」没有发生，更不能把变化归因到本脚本还是并发进程。"
        "真正的只读保证来自三处合力：脚本不含任何写/删/移代码路径 + 上面那条 filter 断言 + 下面的产出目录前置检查。"
    )
    A("")
    A(
        "**产出目录与产出文件的前置检查**：`--out-dir` 若落在某个被盘点目标的目录树内"
        "**且未被该目标的 gitignore 排除**，脚本**在开始盘点之前**就 exit 2——"
        "台账一写进去就会出现在该目标的 porcelain 里。"
        "（判定本身要调 `git rev-parse --show-toplevel` 与 `git check-ignore`，"
        "所以准确说法是「在任何**盘点**命令之前」而不是「在任何 git 命令之前」——"
        "首版如此写不准确，Codex round-2 抓出。）配套还有四道："
        "`--out-stem` 必须是纯文件名（挡绝对路径与 `..` 逃逸）；"
        "嵌套判定用 **st_dev/st_ino 身份**逐级上溯（`os.path.normcase` 在 macOS/Linux 是恒等函数，"
        "`/Users`↔`/users` 这类同卷别名骗得过字符串比较——Codex round-3 实测绕过）；"
        "目标根取 git 认定的 `--show-toplevel` 而非 CLI 路径（挡 `GIT_WORK_TREE` 指向别处）；"
        "**写盘前对最终的 `.md`/`.json` 两个 sink 再做一次身份复核**"
        "（`O_NOFOLLOW` 打开 → `fstat` 验 `S_ISREG` 且 `nlink==1` → 通过后才 `ftruncate`，"
        "顺序不能反：带 `O_TRUNC` 打开会在发现硬链接之前就把对方清空）。"
        "⚠️ 这只堵住**叶子**替换；父目录替换与 bind-mount 别名仍在声明的边界之外，见文首威胁模型。"
    )
    A("")
    if nested_declared:
        A("⚠️ **本次产出目录嵌套声明（如实登记，不宣称「零交集」）**：")
        for nd in nested_declared:
            A(
                f"- `--out-dir` 位于目标 `{_md_escape(str(nd['target']))}`"
                f"（`{_md_escape(str(nd['target_path']))}`）的目录树内，"
                "但被该目标的 gitignore 排除，因此不进其 porcelain。"
            )
        A("")
    A(
        "各门的承重性由变异测试实证（见验收单）：M1 截断解析结果 / M2 序列化漏结尾 NUL / "
        "M3 盘点后 porcelain 被改 / M4 分类循环漏一条，四者均 exit 2；M5 阴性对照保持绿。"
    )
    A("")

    A("## 二、四类判别口径")
    A("")
    A(
        "**保守优先原则**：判别不确定时归入更受保护的类别。把用户数据错判成「临时物」是不可逆方向；"
        "把临时物错判成「用户资产」只是多留一份。"
    )
    A("")
    A("| 类别 | 定义 |")
    A("| --- | --- |")
    for c in CATEGORIES:
        A(f"| **{c}** | {CATEGORY_DEFINITION[c]} |")
    A("")
    A("### 规则表（顺序敏感，首个命中生效；台账每条记录都标注命中的规则 id）")
    A("")
    A("| 规则 | 类别 | 判据 |")
    A("| --- | --- | --- |")
    for rule in RULES:
        A(f"| `{rule.rule_id}` | {rule.category} | {_md_escape(rule.why)} |")
    A(
        f"| `{CATCHALL_RULE}` | {CATCHALL_CATEGORY} | 无规则命中——保守归入最受保护的用户资产并强制人工裁定 |"
    )
    A("")

    A("## 三、分类计数")
    A("")
    A("| 目标 | " + " | ".join(CATEGORIES) + " | 合计 |")
    A("| --- | " + " | ".join(["---:"] * len(CATEGORIES)) + " | ---: |")
    for r in reports:
        cc = r.category_counts
        A(
            f"| `{r.label}` | "
            + " | ".join(str(cc[c]) for c in CATEGORIES)
            + f" | {len(r.entries)} |"
        )
    A("")
    A(
        "| 目标 | "
        + " | ".join(
            ["tracked_modified", "tracked_deleted", "untracked", "tracked_other"]
        )
        + " |"
    )
    A("| --- | ---: | ---: | ---: | ---: |")
    for r in reports:
        sc = r.state_counts
        A(
            f"| `{r.label}` | "
            + " | ".join(
                str(sc.get(k, 0))
                for k in [
                    "tracked_modified",
                    "tracked_deleted",
                    "untracked",
                    "tracked_other",
                ]
            )
            + " |"
        )
    A("")

    # 搬迁取证
    A("## 四、tracked 删除的搬迁取证")
    A("")
    A(
        "判据 **以内容为准，不以文件名为准**：HEAD 侧的 blob OID 由 "
        "`git cat-file --batch-check` 批量取得，工作树侧由 `git hash-object --stdin-paths` "
        "取得，两者是同一套 git 内容身份，可直接相等比较。"
        "按 basename 配对会一对多（仓里有几十个 `index.md`），配错就是假证据——"
        "所以 basename 只在内容匹配失败时用来降级说明「同名但内容不同」。"
    )
    A("")
    A(
        "⚠️ **相等的证明力有边界**：blob OID 相等只说明「工作树里存在与被删内容同一的副本」，"
        "**不证明位移的因果方向**（谁搬到了谁），也不证明这次搬迁是用户授意的。"
        "台账里所有「位移」措辞都应按这个口径读。"
    )
    A("")
    A(
        f"未跟踪文件哈希纳入上限：**{HASH_SIZE_CAP // (1024 * 1024)} MB**。超限文件不参与内容匹配；"
        "若某条删除的同名候选正好超限，该删除项判独立结论 **`evidence_skipped_size`**——"
        "意思是「本台账对它没有内容结论」，**不是**「内容不同」也**不是**「无候选」。"
    )
    A("")
    A(
        "> ⚠️ **这条上限曾造出一条假陈述（Codex round-1 C-1，已修）**：上限原为 8 MB，"
        "而 `docs/architecture/backend-overview.png` 是 16,420,168 字节，与归档区同名文件的 "
        "blob sha 同为 `d7b8cb4d`——**内容确实同一**，却因超限没进内容索引、被 basename "
        "兜底判成 `same_name_diff_content` 写进了台账。上限已提到 "
        f"{HASH_SIZE_CAP // (1024 * 1024)} MB，"
        "且超限一律走 `evidence_skipped_size`，**绝不再退回内容判定冒充结论**。"
        "（不在此落盘「当前最大未跟踪文件是多少 MB」——那是会过期的数值，"
        "本轮实测的 Neo4j dump 已比上一轮大了近 3 MB。真要核对请看各目标的 "
        "`unhashed_untracked_with_reason`：为空即表示没有任何条目触及上限。）"
    )
    A("")
    A(
        "**低熵内容不驱动分类（Codex round-1 C-2，已修）**：blob 内容相等只证明「存在同一内容的副本」，"
        f"不证明因果上的「此文件搬到了那里」。不超过 {LOW_ENTROPY_MAX_BYTES} 字节的 blob（`.gitkeep`、"
        "单行占位、固定存根）会让不相干的两棵树互相「配对」——`docs/.gitkeep` 与 `canvas-vault/.gitkeep` "
        "内容相同，就能把用户资产改判成应提交代码。现在：低熵匹配仍登记为证据"
        "（来源侧标 `content_sha_low_entropy`，与多候选并存时标 `content_sha_ambiguous_low_entropy`；"
        "目的地侧对应 `content_sha_low_entropy` / `content_sha_multi_source_low_entropy`——"
        "四种形态都会出现，逐条实际取值见 json 的 `relocation.match_kind`），"
        "并且**类别继承已整体废除**（Codex round-2 C-2）——"
        "「用内容相等反推来源、再用来源覆盖目的地类别」本身就是循环论证，收窄条件挡不住"
        "（65 字节的 `workspace.json` 就能把归档区目的地继承成「临时物」）。"
        "现在目的地一律用自身路径规则判别（归档区由 A1/A2/A3 覆盖），位移证据只作 `relocation` 字段。"
    )
    A("")
    for r in reports:
        if r.evidence_skipped:
            A(
                f"⚠️ **`{r.label}` 有 {len(r.evidence_skipped)} 条路径含换行符**，无法走 git 的按行 batch 协议，"
                "因此**只降级取证、不降级覆盖**：这些条目照常进分类与对账，但没有内容级搬迁/副本取证。"
                "逐条："
                + "、".join(f"`{_md_escape(x)}`" for x in r.evidence_skipped[:10])
            )
            A("")
    A(
        "**空文件必须排除**：空内容的 git blob sha 全仓恒等于 `e69de29…`。本仓 "
        "`docs/stories/4.5.story.md` 在 HEAD 里就是空文件——若不排除，它会一口气「匹配」工作树里"
        "全部 16 个空的未跟踪文件（含用户 vault 笔记 `canvas-vault/未命名 1.md` 等），"
        "把用户资产误标成「搬迁目的地」。这不是位移，是假证据。已在匹配前剔除，"
        "受影响的删除项判 `evidence_skipped_empty_blob`（同样是「没有内容结论」，不是「内容不同」）。"
    )
    A("")
    for r in reports:
        amb = [
            e
            for e in r.entries
            if e.relocation
            and str(e.relocation.get("match_kind", "")).startswith(
                "content_sha_ambiguous"
            )
        ]
        if amb:
            A(
                f"**`{r.label}` 内容命中多于一条的删除：{len(amb)} 条**——同内容文件在归档区有多份副本"
                "（如各 shard 下同样的 index.md 存根）。台账保留全部候选，位移方向由 DEBT-14 人审确定，"
                "本卡不替它选；这类来源**不驱动目的地的类别继承**。"
            )
            A("")
    A(
        "| 目标 | moved_identical | content_still_in_head | same_name_diff_content | no_candidate | evidence_skipped_size | evidence_skipped_empty_blob | evidence_incomplete_pool | evidence_incomplete_head | 位移目的地 |"
    )
    A("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in reports:
        v: Dict[str, int] = {}
        for e in r.entries:
            if e.relocation:
                v[e.relocation["verdict"]] = v.get(e.relocation["verdict"], 0) + 1
        A(
            f"| `{r.label}` | {v.get('moved_identical', 0)} | {v.get('content_still_in_head', 0)} | "
            f"{v.get('same_name_diff_content', 0)} | "
            f"{v.get('no_candidate', 0)} | {v.get('evidence_skipped_size', 0)} | "
            f"{v.get('evidence_skipped_empty_blob', 0)} | {v.get('evidence_incomplete_pool', 0)} | "
            f"{v.get('evidence_incomplete_head', 0)} | "
            f"{v.get('relocation_destination', 0)} |"
        )
    A("")
    A(
        "口径：前四列是**有内容结论**的判定（`content_still_in_head` = 同内容 blob 仍在 HEAD 的"
        "另一个受控路径上，即内容可还原）；`evidence_skipped_*` 与 `evidence_incomplete_*` "
        "四列是**明确的「无结论」**（未取证，需人工比对），不得读成任何一种内容判定。"
    )
    A("")
    A(
        "**「无结论」的四种来源**：① 候选超过哈希上限 (`evidence_skipped_size`)；"
        "② HEAD 侧是空文件、空 blob OID 全仓恒等因而无鉴别力 (`evidence_skipped_empty_blob`)；"
        "③ **HEAD 侧根本拿不到 blob** (`evidence_incomplete_head`) —— 路径含换行走不了 batch 协议、"
        "或该条目是 gitlink/子模块而非普通文件（Codex round-3 C-1 促成）；"
        "④ **工作树里存在任何未能哈希的未跟踪文件** (`evidence_incomplete_pool`) —— 包括超限、"
        "符号链接、非普通文件、路径含换行、`stat` 失败五种，逐条原因记在 json 的 "
        "`unhashed_untracked_with_reason`（Codex round-2 C-1 促成）。"
        "只要 ④ 的池非空，「没有内容同一副本」这句话就无法成立，因此 `no_candidate` 与 "
        "`same_name_diff_content` **一律降级为无结论**——首版会在池不完整时照样给出肯定结论。"
    )
    A("")
    for r in reports:
        if r.unhashed_untracked:
            A(
                f"⚠️ **`{r.label}` 未能哈希的未跟踪文件 {len(r.unhashed_untracked)} 条**，"
                "该目标的删除项一律判 `evidence_incomplete_pool`。逐条原因见 json。"
            )
        else:
            A(
                f"`{r.label}`：未能哈希的未跟踪文件 **0 条**——**本次可见候选池**"
                "（porcelain 可见且非 ignored）内无遗漏，因此本目标的 `no_candidate` / "
                "`same_name_diff_content` 在**该域内**是有效结论。"
                "⚠️ 仍不覆盖 ignored 子树与其他 ref——见上方证明域说明。"
            )
    A("")
    for r in reports:
        odd = [
            e
            for e in r.entries
            if e.relocation
            and e.relocation["verdict"]
            in (
                "same_name_diff_content",
                "no_candidate",
                "evidence_skipped_size",
                "evidence_skipped_empty_blob",
                "evidence_incomplete_pool",
                "evidence_incomplete_head",
                "content_still_in_head",
            )
        ]
        if odd:
            A(
                f"### `{r.label}`：⚠️ 非「内容同一位移」的删除（{len(odd)} 条，逐条需人审）"
            )
            A("")
            A("| 状态 | 路径 | 判定 | 同名候选 | 类别 |")
            A("| --- | --- | --- | --- | --- |")
            for e in odd:
                cands = e.relocation.get("candidates") or []
                shown = "、".join(f"`{_md_escape(c)}`" for c in cands[:3]) or "—"
                if len(cands) > 3:
                    shown += f"（另 {len(cands) - 3} 条）"
                A(
                    f"| `{e.xy}` | `{_md_escape(e.path)}` | {e.relocation['verdict']} | {shown} | {e.category} |"
                )
            A("")

    for r in reports:
        multi = [
            e
            for e in r.entries
            if e.relocation
            and str(e.relocation.get("match_kind", "")).startswith(
                "content_sha_multi_source"
            )
        ]
        if multi:
            A(f"### `{r.label}`：⚠️ 一个位移目的地对应多个同内容来源（{len(multi)} 条）")
            A("")
            A(
                "> Codex round-1 C-3 整改：目的地侧原来只写第一个遍历到的来源（标量 `source`），"
                "把「多个删除来源指向同一内容」静默压成唯一来源——与台账「本卡不替它选」自相矛盾。"
                "现在全列，并且这类条目**不继承任何来源的类别**。"
            )
            A("")
            A("| 未跟踪目的地 | 同内容的删除来源 |")
            A("| --- | --- |")
            for e in multi[:20]:
                srcs = e.relocation.get("sources") or []
                shown = "、".join(f"`{_md_escape(x)}`" for x in srcs[:3])
                if len(srcs) > 3:
                    shown += f"（另 {len(srcs) - 3} 条）"
                A(f"| `{_md_escape(e.path)}` | {shown} |")
            if len(multi) > 20:
                A(f"| …（另 {len(multi) - 20} 条见 json） | |")
            A("")

    for r in reports:
        fs = {}
        for e in r.entries:
            if e.feature_branch_state:
                fs[e.feature_branch_state] = fs.get(e.feature_branch_state, 0) + 1
        if not fs:
            continue
        A(
            f"### `{_md_escape(r.label)}`：同路径也在 `{FEATURE_BRANCH}` 受控的未跟踪文件"
        )
        A("")
        A(
            "> ⛔ **这一节原来一律写「主仓落后」，是错的**（Codex round-5 F2）。"
            "实测两个 HEAD **互不为祖先**，而且这批文件里有相当一部分**内容不同**——"
            "「落后」既无拓扑依据，也不是事实。按它单向覆盖会丢掉主仓侧的改动。"
        )
        A("")
        A("| 状态 | 条数 | 含义与处置 |")
        A("| --- | ---: | --- |")
        if fs.get("same_blob"):
            A(
                f"| `same_blob` | {fs['same_blob']} | 同路径同内容——主仓这份是未纳管的同内容副本，"
                "归 DEBT-14 合并策略 |"
            )
        if fs.get("diverged"):
            A(
                f"| `diverged` | {fs['diverged']} | ⚠️ **同路径内容分歧**——禁止单向覆盖"
                "（`-X ours/theirs` 一律不适用），须逐 hunk 人审 |"
            )
        if fs.get("present_local_unhashable"):
            A(
                f"| `present_local_unhashable` | {fs['present_local_unhashable']} | "
                "feature 侧有该路径，但本地内容无法取证，关系未定 |"
            )
        A("")
        div = [e for e in r.entries if e.feature_branch_state == "diverged"]
        if div:
            A(f"内容分歧的 {len(div)} 条逐条（这是本节最该被看到的部分）：")
            A("")
            A("| 路径 | 类别 |")
            A("| --- | --- |")
            for e in div[:40]:
                A(f"| `{_md_escape(e.path)}` | {e.category} |")
            if len(div) > 40:
                A(f"| …（另 {len(div) - 40} 条见 json 的 `feature_branch_state`） | |")
            A("")

    # 未跟踪副本取证
    A("### 未跟踪文件中「已受控内容的副本」")
    A("")
    A(
        "同一套 blob sha 判据反向用一次：未跟踪文件的内容若与 HEAD 树里某个**当前仍受控**的"
        "路径的 git blob 身份相同（即 clean filter 之后的内容同一），它就是副本，"
        "不是「未入库的新内容」。这条区分很要紧——"
        "把副本当新代码会得出「有大量代码没提交」的错误结论。"
    )
    A("")
    A("| 目标 | 未跟踪总数 | 其中是已受控内容的副本 | 占比 |")
    A("| --- | ---: | ---: | ---: |")
    for r in reports:
        unt = [e for e in r.entries if e.state == "untracked"]
        dup = [e for e in unt if e.duplicate_of_tracked]
        pct = f"{len(dup) * 100 // len(unt)}%" if unt else "—"
        A(f"| `{r.label}` | {len(unt)} | {len(dup)} | {pct} |")
    A("")
    for r in reports:
        dup = [e for e in r.entries if e.duplicate_of_tracked]
        if not dup:
            continue
        groups: Dict[str, List[Entry]] = {}
        for e in dup:
            groups.setdefault(e.path.split("/")[0] + "/", []).append(e)
        A(
            f"`{r.label}` 副本按顶层目录："
            + "、".join(
                f"`{k}` {len(v)} 条"
                for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1]))
            )
        )
        A("")
        sample = dup[:12]
        A("| 未跟踪路径 | 与之内容同一的受控路径 |")
        A("| --- | --- |")
        for e in sample:
            more = (
                f"（另 {len(e.duplicate_of_tracked) - 1} 处）"
                if len(e.duplicate_of_tracked) > 1
                else ""
            )
            A(
                f"| `{_md_escape(e.path)}` | `{_md_escape(e.duplicate_of_tracked[0])}`{more} |"
            )
        if len(dup) > len(sample):
            A(
                f"| …（另 {len(dup) - len(sample)} 条见 json 的 `duplicate_of_tracked` 字段） | |"
            )
        A("")

    # 需人工裁定
    A("## 五、需人工裁定项（`needs_manual_review`）")
    A("")
    for r in reports:
        manual = [e for e in r.entries if e.needs_manual_review]
        grouped: Dict[str, List[Entry]] = {}
        for e in manual:
            grouped.setdefault(e.disposition, []).append(e)
        A(f"### `{r.label}`：{len(manual)} 条")
        A("")
        A("| 处置建议 | 条数 |")
        A("| --- | ---: |")
        for disp, items in sorted(grouped.items(), key=lambda kv: -len(kv[1])):
            A(f"| {_md_escape(disp)} | {len(items)} |")
        A("")
        small = (
            [] if brief else [e for e in manual if len(grouped[e.disposition]) <= 40]
        )
        if small:
            A(f"逐条（仅列组内 ≤40 条的组，共 {len(small)} 条；全量见 json）：")
            A("")
            A("| 状态 | 路径 | 类别 | owner | 处置建议 |")
            A("| --- | --- | --- | --- | --- |")
            for e in small:
                A(
                    f"| `{e.xy}` | `{_md_escape(e.path)}` | {e.category} | "
                    f"{_md_escape(e.owner or OWNER_UNASSIGNED)} | {_md_escape(e.disposition)} |"
                )
            A("")

    # 应提交代码逐条 owner
    A("## 六、「应提交代码」逐条 owner 映射")
    A("")
    for r in reports:
        code = [e for e in r.entries if e.category == CAT_CODE]
        A(f"### `{r.label}`：{len(code)} 条")
        A("")
        if not code:
            A("（无）")
            A("")
            continue
        by_owner: Dict[str, List[Entry]] = {}
        for e in code:
            by_owner.setdefault(e.owner or OWNER_UNASSIGNED, []).append(e)
        A("| owner | 条数 |")
        A("| --- | ---: |")
        for owner, items in sorted(by_owner.items(), key=lambda kv: -len(kv[1])):
            A(f"| {_md_escape(owner)} | {len(items)} |")
        A("")
        listed = (
            []
            if brief
            else [e for e in code if len(by_owner[e.owner or OWNER_UNASSIGNED]) <= 60]
        )
        if listed:
            A(f"逐条（仅列组内 ≤60 条的 owner 组，共 {len(listed)} 条；全量见 json）：")
            A("")
            A("| 状态 | 路径 | 规则 | owner |")
            A("| --- | --- | --- | --- |")
            for e in listed:
                A(
                    f"| `{e.xy}` | `{_md_escape(e.path)}` | `{e.rule}` | {_md_escape(e.owner or OWNER_UNASSIGNED)} |"
                )
            A("")

    # 全量清单
    A("## 七、全量逐条清单")
    A("")
    if brief:
        A(
            "_本次以 `--brief` 生成：md 与 json 都省略了**各目标的逐条 `entries` 数组**_"
            "（json 里替换为 `entries_omitted` 说明）。"
            "注意 `baseline_diff` 下的 `added` / `removed` / `entry_changed` 数组**仍然完整保留**——"
            "省略的只是全量条目清单，不是 diff 结果。"
            "全量逐条数据只在**非 brief 生成的台账**里（本卡的首跑台账 "
            "`2026-08-31-DEBT-13-工作树资产分类台账.json`）。"
        )
        A("")
    else:
        A(
            "完整逐条数据在同名 `.json`（机读，含 blob OID 与规则 id）。此处按目标 + 类别给出"
            "路径清单，便于人工核对。"
        )
        A("")
    for r in [] if brief else reports:
        A(f"### `{r.label}`（{len(r.entries)} 条）")
        A("")
        for c in CATEGORIES:
            items = [e for e in r.entries if e.category == c]
            A(f"<details><summary><b>{c}</b>（{len(items)} 条）</summary>")
            A("")
            if items:
                A("| 状态 | 路径 | 规则 |")
                A("| --- | --- | --- |")
                for e in items:
                    A(f"| `{e.xy}` | `{_md_escape(e.path)}` | `{e.rule}` |")
            else:
                A("（无）")
            A("")
            A("</details>")
            A("")

    if diff is not None:
        A("## 八、与基线台账的 diff（复跑证据）")
        A("")
        A(
            f"基线文件：`{_md_escape(str(diff['baseline_file']))}`"
            f"（生成于 {_md_escape(str(diff.get('baseline_generated_at_utc')))}）"
        )
        A("")
        A(
            f"基线内容身份：sha256 `{diff.get('baseline_sha256', '?')}`，"
            f"{diff.get('baseline_size_bytes', '?')} 字节。"
            "**同一份读入的字节既用于计算该 digest、也用于本次 diff**——"
            "所以这个值能证明「生成时读的就是这些字节」（Codex round-5 F4 促成）。"
        )
        A("")
        for t in diff["targets"]:
            if t.get("status"):
                A(f"### `{t['label']}` — {t['status']}")
                A("")
                continue
            A(f"### `{t['label']}`")
            A("")
            A("| 维度 | 基线 | 本次 |")
            A("| --- | --- | --- |")
            A(
                f"| HEAD | `{(t['head_sha_baseline'] or '')[:8]}` | `{t['head_sha_now'][:8]}` |"
            )
            A(
                f"| porcelain sha256 | `{(t['porcelain_sha_baseline'] or '')[:16]}…` | `{t['porcelain_sha_now'][:16]}…` |"
            )
            A(f"| 记录数 | {t['record_count_baseline']} | {t['record_count_now']} |")
            A("")
            A(
                f"- 新增 {len(t['added'])} 条 · 消失 {len(t['removed'])} 条 · 改类 "
                f"{len(t['recategorized'])} 条 · **整条 entry 有任一字段变化 "
                f"{len(t.get('entry_changed', []))} 条**"
            )
            if not t.get("baseline_had_entries"):
                A("")
                A(
                    "> ⚠️ 基线 json 是用 `--brief` 生成的、不含逐条数组，因此本次只能比对目标级"
                    "汇总（HEAD / porcelain sha / 记录数），**逐条 diff 不可用**。"
                    "要做逐条比对请以非 brief 的首跑台账 json 作基线。"
                )
            if t.get("entry_changed"):
                A("")
                A("**逐条字段变化**（比 category 更细，任何一维变了都在这里）：")
                A("")
                A("| 路径 | 变化字段 |")
                A("| --- | --- |")
                for ch in t["entry_changed"][:50]:
                    A(f"| `{_md_escape(ch['path'])}` | {', '.join(ch['fields'])} |")
                if len(t["entry_changed"]) > 50:
                    A(f"| …（另 {len(t['entry_changed']) - 50} 条见 json） | |")
            for label, key in (("新增", "added"), ("消失", "removed")):
                if t[key]:
                    A("")
                    A(f"**{label}**：")
                    for p in t[key][:50]:
                        A(f"- `{_md_escape(p)}`")
                    if len(t[key]) > 50:
                        A(f"- …（另 {len(t[key]) - 50} 条见 json）")
            if t["recategorized"]:
                A("")
                A("**改类**：")
                for rc in t["recategorized"][:50]:
                    A(
                        f"- `{_md_escape(rc['path'])}`：{_md_escape(str(rc['from']))} → "
                        f"{_md_escape(str(rc['to']))}"
                    )
            A("")

    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="工作树资产分类台账（只读盘点）")
    ap.add_argument(
        "--target",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="盘点目标；可重复。缺省为主仓 + feature worktree。",
    )
    ap.add_argument(
        "--pin-sha",
        action="append",
        default=[],
        metavar="LABEL=SHA",
        help="基线校验：断言该目标 HEAD 以给定 sha 前缀开头，不符 exit 2。",
    )
    ap.add_argument(
        "--baseline", metavar="JSON", help="与既有台账 json 做 diff（复跑证据）。"
    )
    ap.add_argument(
        "--out-dir", default=str(REPO_ROOT / "_bmad-output" / "审查"), help="产出目录。"
    )
    ap.add_argument(
        "--out-stem", default=None, help="产出文件名主干（默认按日期生成）。"
    )
    ap.add_argument(
        "--no-owner-lookup",
        action="store_true",
        help="跳过 git log owner 解析（更快）。",
    )
    ap.add_argument(
        "--strict-rules",
        action="store_true",
        help="若有记录落到 catch-all 规则则 exit 2（含 --rule-coverage 的全量 tracked 面）。",
    )
    ap.add_argument(
        "--rule-coverage",
        action="store_true",
        help=(
            "额外把每个目标的**全部 tracked 路径**（git ls-files）喂进规则表，报告 catch-all 命中数。"
            "porcelain 只覆盖当前有变更的路径，这个模式才看得出规则表本身的盲区（Codex round-2 B-3）。"
        ),
    )
    ap.add_argument(
        "--allow-filter-drivers",
        action="store_true",
        help="目标仓配有自定义 git clean/process filter 时仍继续（默认 exit 2——取证会执行它们）。",
    )
    ap.add_argument(
        "--brief",
        action="store_true",
        help=(
            "md 与 json **都**省略逐条数组（json 的 entries 换成 entries_omitted 说明）。"
            "全量逐条数据只在非 brief 的台账里。"
        ),
    )
    ap.add_argument("--print-only", action="store_true", help="只打印摘要，不落盘。")
    args = ap.parse_args(argv)

    targets: List[Tuple[str, str, str]] = []
    if args.target:
        for spec in args.target:
            if "=" not in spec:
                print(f"ERROR: --target 需 LABEL=PATH，收到 {spec!r}", file=sys.stderr)
                return 1
            label, path = spec.split("=", 1)
            # Codex round-4 A-4：label 来自 CLI，含 `|` / 换行 / 反引号就能拆坏
            # Markdown 表格与标题。它散布在十几个插值点，与其逐点转义，
            # 不如在入口约束字符集——盘点目标的标签本就没有理由含这些字符。
            if not re.fullmatch(r"[A-Za-z0-9_.\-]{1,32}", label):
                print(
                    f"ASSERTION FAILED: --target 的 LABEL ({label!r}) 只允许 "
                    "字母/数字/下划线/点/连字符，长度 1-32。",
                    file=sys.stderr,
                )
                return 2
            if any(existing == label for existing, _, _ in targets):
                print(
                    f"ASSERTION FAILED: --target 的 LABEL ({label!r}) 重复——"
                    "label 是 pins / baseline / 报告分组的键，重复会静默折叠（Codex round-5 F9）。",
                    file=sys.stderr,
                )
                return 2
            targets.append((label, path, "命令行指定"))
    else:
        targets = list(DEFAULT_TARGETS)

    pins: Dict[str, str] = {}
    for spec in args.pin_sha:
        if "=" not in spec:
            print(f"ERROR: --pin-sha 需 LABEL=SHA，收到 {spec!r}", file=sys.stderr)
            return 1
        label, sha = spec.split("=", 1)
        pins[label] = sha

    unknown = set(pins) - {t[0] for t in targets}
    if unknown:
        print(f"ERROR: --pin-sha 指向未知目标 {sorted(unknown)}", file=sys.stderr)
        return 1

    # A-1 整改（BLOCKER）：原先 --out-dir 与 --target 无任何不相交检查，
    # `--target victim=/tmp/demo --out-dir /tmp/demo` 会在「只读取证」取完之后
    # 往被盘点工作树里写台账文件——取证窗口在写入之前就关闭了，PASS 是假绿。
    # 现在把不相交升为**开跑前的硬前置**：先拒，再谈只读。
    # out-stem 必须是纯 basename：`--out-dir /safe --out-stem /victim/X` 会让
    # `Path(out_dir) / "/victim/X"` 直接丢弃 out_dir，绝对路径与 `..` 都能逃逸
    # （Codex round-2 A-1）。
    if args.out_stem is not None:
        stem = args.out_stem
        if (
            os.path.isabs(stem)
            or "/" in stem
            or os.sep in stem
            or stem in ("", ".", "..")
            or stem.startswith("~")
        ):
            print(
                f"ASSERTION FAILED: --out-stem ({stem!r}) 必须是不含路径分隔符的纯文件名——"
                "绝对路径或 `..` 会让产出逃出 --out-dir。",
                file=sys.stderr,
            )
            return 2

    def _same_or_inside(inner: str, outer: str) -> bool:
        """inner 是否等于 outer 或位于 outer 之内。

        Codex round-3 A-1：`os.path.normcase` 在 macOS/Linux 上是恒等函数，
        所以 `/Users/x` 与 `/users/x`（同一卷的大小写别名）在字符串比较下被判成
        互不相干，别名 out-dir 就此绕过前置门。改为用 **st_dev/st_ino 身份**
        逐级上溯比较——这才是文件系统认定的"同一个目录"。
        inner 可能尚未创建，先退到它最近的已存在祖先再比。
        """
        try:
            outer_id = os.stat(outer)
        except OSError:
            return os.path.normcase(inner) == os.path.normcase(
                outer
            ) or os.path.normcase(inner).startswith(os.path.normcase(outer) + os.sep)
        cur = os.path.realpath(inner)
        while not os.path.exists(cur):
            parent = os.path.dirname(cur)
            if parent == cur:
                return False
            cur = parent
        seen = set()
        while True:
            try:
                st = os.stat(cur)
            except OSError:
                return False
            if (st.st_dev, st.st_ino) == (outer_id.st_dev, outer_id.st_ino):
                return True
            if (st.st_dev, st.st_ino) in seen:
                return False
            seen.add((st.st_dev, st.st_ino))
            parent = os.path.dirname(cur)
            if parent == cur:
                return False
            cur = parent

    out_dir_real = os.path.realpath(args.out_dir)
    nested_declared: List[Dict[str, str]] = []
    # Codex round-3 A-1：真实根原来只在预检里用一次，census_one 仍收到 CLI path，
    # 于是 git status 来自一个根、Python 的 stat 来自另一个根（GIT_WORK_TREE 分离）。
    # 这里把解析结果**替换回 targets**，让同一个根贯穿全部取证。
    resolved_targets: List[Tuple[str, str, str]] = []
    for label, path, _note in targets:
        # 用 git 认定的工作树根，而不是 CLI 传进来的路径——GIT_WORK_TREE 等环境
        # 变量可以让二者指向不同目录（Codex round-2 A-1）。
        try:
            repo_real = os.path.realpath(
                git_text(path, ["rev-parse", "--show-toplevel"])
            )
        except GitError:
            repo_real = os.path.realpath(path)
        resolved_targets.append((label, repo_real, _note))
        if _same_or_inside(repo_real, out_dir_real) and repo_real != out_dir_real:
            print(
                f"ASSERTION FAILED: 被盘点目标 `{label}` ({path}) 落在 --out-dir "
                f"({args.out_dir}) 之内——只读硬边界不成立，拒绝执行。",
                file=sys.stderr,
            )
            return 2
        if not _same_or_inside(out_dir_real, repo_real):
            continue
        # 落在目标目录树里 —— 判据不是「路径是否嵌套」，而是**产出会不会进该目标的
        # porcelain**。被该仓 gitignore 排除的嵌套目录（如挂在 .claude/worktrees/ 下的
        # 独立 worktree）不进 porcelain，只读取证仍然成立；未被排除的一律拒。
        ignored = (
            subprocess.run(
                [
                    "git",
                    "-C",
                    path,
                    *GIT_READONLY_ARGS,
                    "check-ignore",
                    "-q",
                    out_dir_real,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
        if not ignored:
            print(
                f"ASSERTION FAILED: --out-dir ({args.out_dir}) 落在被盘点目标 `{label}` "
                f"({path}) 之内**且未被其 gitignore 排除**——台账一写进去就会出现在该目标的 "
                "porcelain 里，只读取证给出的将是假绿。拒绝执行。",
                file=sys.stderr,
            )
            return 2
        nested_declared.append(
            {
                "target": label,
                "target_path": path,
                "target_toplevel": repo_real,
                "out_dir": out_dir_real,
            }
        )

    targets = resolved_targets
    reports: List[TargetReport] = []
    try:
        for label, path, note in targets:
            reports.append(
                census_one(
                    label,
                    path,
                    note,
                    pins.get(label),
                    resolve_owner=not args.no_owner_lookup,
                    allow_filter_drivers=args.allow_filter_drivers,
                )
            )
    except AssertionError as exc:
        print(f"ASSERTION FAILED: {exc}", file=sys.stderr)
        return 2
    except GitError as exc:
        print(f"GIT ERROR: {exc}", file=sys.stderr)
        return 1

    # round-6 A5：原来只遍历「已存在的 key」，于是把某条门的赋值整行删掉后
    # rc 仍是 0，md 矩阵那一格退化成 `n/a`，与「pin 未传」的合法 n/a 无法区分。
    # 断言清单必须是**必需项**：缺一条就是 FAIL。
    REQUIRED_ASSERTIONS = (
        "filter_drivers_absent_or_accepted",
        "parsed_count_matches_independent_count",
        "orig_field_iff_rename_or_copy",
        "xy_sequence_matches_independent_parse",
        "count_equals_porcelain_records",
        "entries_preserve_record_identity",
        "content_evidence_independently_recomputable",
        "relocation_evidence_self_consistent",
        "roundtrip_bytes_identical",
        "feature_ref_resolvable_or_declared",
        "readonly_porcelain_unchanged",
    )
    failed: List[str] = []
    for r in reports:
        for name in REQUIRED_ASSERTIONS:
            if name not in r.assertions:
                failed.append(f"[{r.label}] 缺失必需断言 {name}（门被删或未执行）")
        for name, ok in r.assertions.items():
            if not ok:
                failed.append(f"[{r.label}] {name}")
    if args.rule_coverage:
        for r in reports:
            raw = git_raw(r.path, ["ls-files", "-z"])
            tracked = [
                x.decode("utf-8", "surrogateescape") for x in raw.split(b"\0") if x
            ]
            miss = [t for t in tracked if classify(t)[1] == CATCHALL_RULE]
            r.rule_coverage = {
                "tracked_total": len(tracked),
                "catchall_hits": len(miss),
                "sample": sorted(miss)[:20],
            }
            print(
                f"[{r.label}] 规则覆盖自检：tracked {len(tracked)} 条，catch-all 命中 {len(miss)} 条"
                + (f"（样本 {sorted(miss)[:5]}）" if miss else "")
            )
            if args.strict_rules and miss:
                failed.append(
                    f"[{r.label}] strict_rules: 全量 tracked 面有 {len(miss)} 条落 catch-all"
                )

    if args.strict_rules:
        for r in reports:
            n = sum(1 for e in r.entries if e.rule == CATCHALL_RULE)
            if n:
                failed.append(f"[{r.label}] strict_rules: {n} 条落 catch-all 规则")

    generated = _dt.datetime.now(_dt.timezone.utc)
    generated_utc = generated.strftime("%Y-%m-%d %H:%M:%S UTC")
    generated_sh = generated.astimezone(SHANGHAI).strftime("%Y-%m-%d %H:%M:%S +08:00")

    diff = None
    if args.baseline:
        bp = Path(args.baseline)
        if not bp.is_file():
            print(f"ERROR: --baseline 文件不存在: {bp}", file=sys.stderr)
            return 1
        diff = diff_against_baseline(reports, bp)

    print(f"# census_worktree_assets — {generated_sh}")
    for r in reports:
        cc = r.category_counts
        print(
            f"[{r.label}] HEAD={r.head_sha[:8]} records={r.record_count} classified={len(r.entries)} "
            + " ".join(f"{c}={cc[c]}" for c in CATEGORIES)
        )
        print(
            f"[{r.label}] porcelain sha256 before={r.porcelain_sha_before[:16]} "
            f"after={r.porcelain_sha_after[:16]} "
            f"{'IDENTICAL(只读取证 PASS)' if r.porcelain_sha_before == r.porcelain_sha_after else 'DIFFER(FAIL)'}"
        )
        catchall = sum(1 for e in r.entries if e.rule == CATCHALL_RULE)
        print(
            f"[{r.label}] catch-all 规则命中 {catchall} 条 · needs_manual_review "
            f"{sum(1 for e in r.entries if e.needs_manual_review)} 条"
            + (
                f" · 含换行路径未取证 {len(r.evidence_skipped)} 条"
                if r.evidence_skipped
                else ""
            )
            + (
                f" · ⚠️ 自定义 filter 驱动 {len(r.filter_drivers)} 个"
                if r.filter_drivers
                else ""
            )
        )

    if failed:
        print("", file=sys.stderr)
        print("ASSERTION FAILED:", file=sys.stderr)
        for f in failed:
            print(f"  - {f}", file=sys.stderr)
        return 2

    if args.print_only:
        print("\n(--print-only：未落盘)")
        return 0

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = (
        args.out_stem
        or f"{generated.astimezone(SHANGHAI).strftime('%Y-%m-%d')}-DEBT-13-工作树资产分类台账"
    )
    md_path = out_dir / f"{stem}.md"
    json_path = out_dir / f"{stem}.json"

    # 写前对**最终两个 sink 本身**再做一次身份级复核（Codex round-2 A-1）：
    # 前置门检的是 --out-dir，但真正落盘的是这两个具体文件；预先摆好的叶子
    # symlink/hardlink 能把 write_text 导向别处，且前置检查与写入之间存在 TOCTOU 窗口。
    for sink in (md_path, json_path):
        # Codex round-5 F1：预检不拒 FIFO 时，第二个 sink 的阻塞式 open 会永久挂起
        # （第一个已经写完，于是留下半对）。非普通文件一律拒。
        if sink.exists() and not sink.is_symlink() and not sink.is_file():
            print(
                f"ASSERTION FAILED: 产出路径 {sink} 已存在且不是普通文件"
                "（FIFO / 设备 / 目录）——拒绝写入。",
                file=sys.stderr,
            )
            return 2
        if sink.is_symlink():
            print(
                f"ASSERTION FAILED: 产出路径 {sink} 是符号链接——拒绝写入（可能指向被盘点工作树）。",
                file=sys.stderr,
            )
            return 2
        try:
            if sink.exists() and sink.stat().st_nlink > 1:
                print(
                    f"ASSERTION FAILED: 产出路径 {sink} 存在多个硬链接——拒绝写入。",
                    file=sys.stderr,
                )
                return 2
        except OSError:
            pass
        sink_real = os.path.realpath(sink)
        for label, path, _n in targets:
            try:
                repo_real = os.path.realpath(
                    git_text(path, ["rev-parse", "--show-toplevel"])
                )
            except GitError:
                repo_real = os.path.realpath(path)
            if not _same_or_inside(sink_real, repo_real):
                continue
            ignored = (
                subprocess.run(
                    [
                        "git",
                        "-C",
                        path,
                        *GIT_READONLY_ARGS,
                        "check-ignore",
                        "-q",
                        sink_real,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ).returncode
                == 0
            )
            if not ignored:
                print(
                    f"ASSERTION FAILED: 产出文件 {sink} 落在被盘点目标 `{label}` 内且未被其 "
                    "gitignore 排除——拒绝写入。",
                    file=sys.stderr,
                )
                return 2

    payload = {
        "schema": SCHEMA,
        "out_dir_nested_in_target_but_gitignored": nested_declared,
        "card": "CARD-DEBT-13",
        "batch": "BATCH-2026-08-31-第七批",
        "generated_at_utc": generated_utc,
        "generated_at_shanghai": generated_sh,
        "generator": "scripts/census_worktree_assets.py",
        "argv": " ".join(sys.argv[1:]),
        # 不写 readonly:true 这种无条件断言（Codex round-2）：真实保证是分层的，
        # 逐条列出比一个布尔诚实。
        "readonly_guarantees": {
            # ⛔ 不写 script_has_no_mutating_code_path_into_targets:true（Codex round-5 F3）：
            # 产出目录若嵌在某目标的 ignored 子树内，脚本确实对该目标的**文件系统**
            # 执行了 mkdir/open/ftruncate/write。check-ignore 只证明这些写入 git 不可见，
            # 不等于"没写"。如实描述：
            # round-6 A4：allow 模式下 git 会执行自定义 clean filter（任意外部命令），
            # 实测能往被盘点树里写 10 次，此时"仅限 out-dir 产出"就是假话。
            "writes_into_targets": (
                "⚠️ 本次以 --allow-filter-drivers 运行且目标配有自定义 filter 驱动："
                "取证过程会让 git 执行这些外部命令，它们可以对被盘点树做任意写入——"
                "本次运行**不构成只读**"
                if any(r.filter_drivers for r in reports)
                else "仅限 --out-dir 下的产出文件；本次 out-dir 的嵌套情况见 "
                "out_dir_nested_in_target_but_gitignored（为空表示与所有目标零交集）"
            ),
            "porcelain_proof_scope": (
                "readonly_porcelain_unchanged 只比较 git 可见的 porcelain；"
                "被 gitignore 排除的子树写入天然不在其证明域内"
            ),
            "threat_model": (
                "防误伤，不防并发攻击者：父目录替换 / bind-mount 别名 / 并发 unlink "
                "三类交错在声明的边界之外，见 md 文首「威胁模型」节"
            ),
            "git_invocations_hardened": GIT_READONLY_ARGS,
            "custom_filter_drivers": (
                "asserted_absent"
                if not any(r.filter_drivers for r in reports)
                else "present_and_accepted_via_--allow-filter-drivers"
            ),
            "out_dir_and_final_sinks_checked_against_targets": True,
            "porcelain_sha256_equal_before_after": "见各 target 的 readonly_proof_ok",
            "does_not_prove": [
                "文件内容未变",
                "被 gitignore 的文件未变",
                "refs / reflog / object DB 未变",
                "git 配置未变",
                "写后又恢复没有发生",
                "变化可归因于本脚本而非并发进程",
            ],
        },
        "categories": CATEGORY_DEFINITION,
        "rules": [
            {"id": r.rule_id, "category": r.category, "why": r.why} for r in RULES
        ]
        + [
            {
                "id": CATCHALL_RULE,
                "category": CATCHALL_CATEGORY,
                "why": "无规则命中——保守归入最受保护的用户资产并强制人工裁定",
            }
        ],
        "targets": [r.to_json(include_entries=not args.brief) for r in reports],
    }
    if diff is not None:
        payload["baseline_diff"] = diff

    # ensure_ascii=True：非 UTF-8 路径经 surrogateescape 变成孤立代理，
    # ensure_ascii=False 会把它们原样留在 str 里，随后 strict UTF-8 写盘必抛异常。
    # 转成 \udcXX 转义后既纯 ASCII 又可逆（Codex round-2 A-4）。
    def _write_nofollow(path: Path, data: bytes) -> None:
        """O_NOFOLLOW 打开后 fstat 复核，堵住「检查完再把叶子换成 symlink」的竞态。

        Codex round-3 A-1：先 `is_symlink()` 检查、后 `write_text()` 之间存在窗口，
        期间把叶子替换成指向被盘点工作树的符号链接就能让写入越界。
        `O_NOFOLLOW` 让 open 本身在遇到符号链接时直接失败（ELOOP），
        再用 fstat 确认拿到的是普通文件且硬链接数为 1。
        """
        # Codex round-4 A-1：原来带 O_TRUNC 打开，于是「先截断、后 fstat」——
        # 若 sink 被换成受害文件的硬链接，等发现 nlink>1 时对方已经被清空了。
        # 现在不带 O_TRUNC 打开 → 先验身份 → 通过后才 ftruncate。
        # nlink 也改严格 ==1（原来只拒 >1，并发 unlink 后的 0 会被放行）。
        flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(str(path), flags, 0o644)
        try:
            st = os.fstat(fd)
            if not stat_module.S_ISREG(st.st_mode):
                raise OSError(f"产出 sink {path} 不是普通文件")
            if st.st_nlink != 1:
                raise OSError(
                    f"产出 sink {path} 的硬链接数为 {st.st_nlink}（要求恰好 1）"
                )
            os.ftruncate(fd, 0)
            written = 0
            while written < len(data):  # 短写必须补齐，不能假设一次写完
                n = os.write(fd, data[written:])
                if n <= 0:  # 返回 0 会让上面的循环空转（Codex round-5 F1）
                    raise OSError(f"写入 {path} 时 os.write 返回 {n}，无法推进")
                written += n
            os.fsync(fd)  # 先落稳再改名，避免"改名成功但内容还在缓存里"
        finally:
            os.close(fd)

    # 两份内容先全部渲染完成，再依次落盘——渲染中途抛异常时不会留下半套产物
    # （Codex round-4 A-1：原来 json 先写、md 后写，md 渲染失败就只剩半份）。
    # Codex round-5 F1：渲染**和编码**都必须发生在任何写盘之前——原来编码在
    # ftruncate 之后，于是「json 已更新 + md 编码抛异常」会留下半对。
    json_bytes = json.dumps(payload, ensure_ascii=True, indent=2).encode(
        "utf-8", "surrogateescape"
    )
    md_bytes = render_md(
        reports,
        diff,
        generated_utc,
        generated_sh,
        " ".join(sys.argv[1:]) or "(无参数)",
        brief=args.brief,
        nested_declared=nested_declared,
    ).encode("utf-8", "surrogateescape")
    # round-6 F1-R1：顺序直写两个 sink 时，第二个的 open/write 失败（EACCES/ENOSPC，
    # **不需要并发攻击者**）会留下「新 json + 旧 md」或「新 json + 被截断的半截 md」，
    # 而且截断后的 md 头部带着本次的新时间戳，让「两份 generated_at 一致」这条
    # 自然对账反而通过。实测复现：`chmod 444 <md>` 与 `ulimit -f 40`。
    # 正解：两份都先写进同目录的临时文件并 fsync，**全部成功后**才逐个 os.replace
    # 到最终名。os.replace 是同目录内的原子改名，中途失败最多留下 .tmp 残留，
    # 绝不会破坏已有的旧对。
    tmp_json = json_path.with_name(json_path.name + ".census-tmp")
    tmp_md = md_path.with_name(md_path.name + ".census-tmp")
    try:
        _write_nofollow(tmp_json, json_bytes)
        _write_nofollow(tmp_md, md_bytes)
    except BaseException:
        for t in (tmp_json, tmp_md):
            try:
                if t.exists():
                    t.unlink()
            except OSError:
                pass
        raise
    os.replace(str(tmp_json), str(json_path))
    os.replace(str(tmp_md), str(md_path))

    print("")
    print(f"台账（md）  : {md_path}")
    print(f"台账（json）: {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

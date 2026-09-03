"""后端本地状态文件的 vault 命名空间 — CARD-G2-5 (BATCH-2026-08-29-第七批).

问题 (计划书 L115 + 实证 ``vault_index_orchestrator.py`` / ``lancedb_index_service.py``):
两处 durable pending journal 都写在 ``backend/app/data/`` 的**固定文件名**上,
条目只有相对路径、**没有 vault 维度**。后果:

- vault A 运行期攒下若干 pending 意图 (含 delete) → 切到 vault B 重启 →
  ``recover()`` 把 A 的相对路径当成 B 的文件重放: 在 B 里索引一批**根本不存在**
  的路径, 或按 A 的删除意图去删 B 的索引行;
- 反过来, 切回 A 之后那批意图已经被 B 消费掉了, A 自己的意图反而丢了。

本模块给这类"进程本地、按 vault 分桶"的状态文件提供统一命名与隔离原语。

⛔ key 只取**部署期**值 (``settings.vault_id``), 不读 per-request ContextVar:
journal 是**进程级**资源, 在请求边界之外被 worker 循环读写。用 ContextVar 会让
同一个文件名随请求漂移 —— 那不是隔离, 是随机分桶。
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

#: 旧的"无 vault 维度"状态文件被隔离时追加的后缀。
LEGACY_QUARANTINE_SUFFIX = ".pre-g25.bak"

#: 命名空间分隔符 —— 双下划线, 与 vault_id 内部允许出现的单下划线区分
#: (``sanitize_vault_id`` 会把连续下划线折叠成一个, 所以 ``__`` 不会被 key 自身产生)。
NAMESPACE_SEP = "__"


def deployment_vault_key() -> str:
    """本进程的 vault key —— 恒取 ``settings.vault_id``。

    ``settings.vault_id`` 是部署期身份 (``.canvas-config.yaml`` 的 ``vault_id``,
    否则 ``sanitize_vault_id(ACTIVE_VAULT)``), 与 LanceDB 表前缀同源, 且已由
    ``sanitize_vault_id`` 保证只含 ``\\w`` 字符、长度 ≤200 —— 直接做文件名安全。

    ⛔ 不读 ``current_group_id()`` / subject ContextVar: 见模块 docstring。

    ⚠️ 已知边界 (如实): 两个不同的 vault 目录名可能 sanitize 成同一个 key
    (例如 ``CS 61B`` 与 ``cs-61b``), 那样它们会共用同一个 journal。这与
    LanceDB 表前缀、Neo4j group_id 的碰撞面**完全同源**, 不在本模块单独收敛。
    """
    from app.config import get_settings

    return get_settings().vault_id or "default"


#: 单段文件名的 UTF-8 字节预算。ext4 / overlayfs / APFS 的 ``NAME_MAX`` 都是
#: **255 字节**(不是 255 字符)。留 32 字节余量给最长的派生后缀 (``.jsonl.tmp``
#: 之外将来可能再加)。
_NAME_MAX_BYTES = 255
_NAME_BUDGET_BYTES = _NAME_MAX_BYTES - 32

#: key 被压缩时保留的可读前缀字符数 (够人认出是哪个 vault)。
_KEY_READABLE_CHARS = 24


def fs_safe_key(key: str, *, stem: str, suffix: str) -> str:
    """把 vault key 压到**文件名字节预算**之内, 保留可读前缀 + 稳定摘要。

    ⛔ Codex round-1 HIGH-3 实证: ``sanitize_vault_id`` 按**字符数**截到 200,
    而 CJK 一个字 3 字节 —— 200 个汉字的 key 会让
    ``vault_index_pending__<key>.jsonl.tmp`` 达到 **631 字节**, 超过 Linux
    ``NAME_MAX``(255)。后果不是报错退出, 而是 ``_persist_sync`` 里 ``open()``
    抛 ``ENAMETOOLONG`` 被 catch 成一行 error 日志, 而 ``enqueue()`` 照样返回
    "accepted" —— **durable 意图静默丢失**。macOS/APFS 本机能建, 所以这是只在
    Linux/Docker 生产上发作的条件性缺陷。

    压缩规则 (确定性、可复算): 前 24 字符 + ``-`` + key 的 sha256 前 12 位。
    摘要保证不同 key 不撞; 前缀保证人能认出来。
    """
    overhead = len(f"{stem}{NAMESPACE_SEP}{suffix}".encode("utf-8"))
    if overhead + len(key.encode("utf-8")) <= _NAME_BUDGET_BYTES:
        return key
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    prefix = key[:_KEY_READABLE_CHARS]
    # 前缀本身也可能超预算 (极端: 单字符占 4 字节的 emoji 已被 sanitize 剥掉,
    # 但 CJK 仍 3 字节) —— 逐字符退让直到装得下。
    while prefix and overhead + len(f"{prefix}-{digest}".encode("utf-8")) > _NAME_BUDGET_BYTES:
        prefix = prefix[:-1]
    return f"{prefix}-{digest}" if prefix else digest


def namespaced_state_path(
    data_dir: Path,
    stem: str,
    suffix: str = ".jsonl",
    *,
    vault_key: Optional[str] = None,
) -> Path:
    """``<data_dir>/<stem>__<vault_key><suffix>``, key 已过字节预算压缩。

    ⚠️ 预算按最长派生名 ``<stem>__<key>.jsonl.tmp`` 算 —— ``_persist_sync``
    用 ``with_suffix(".jsonl.tmp")`` 写临时文件, 主名塞得下而临时名塞不下的话,
    落盘照样失败。
    """
    key = vault_key if vault_key is not None else deployment_vault_key()
    safe = fs_safe_key(key, stem=stem, suffix=".jsonl.tmp")
    return Path(data_dir) / f"{stem}{NAMESPACE_SEP}{safe}{suffix}"


def legacy_state_path(data_dir: Path, stem: str, suffix: str = ".jsonl") -> Path:
    """G2-5 之前的无维度路径 ``<data_dir>/<stem><suffix>``。"""
    return Path(data_dir) / f"{stem}{suffix}"


def _reserve_unique(base: Path) -> Optional[Path]:
    """用 ``O_CREAT|O_EXCL`` **抢占**一个唯一目标名, 返回它; 抢不到返回 None。

    ⛔ Codex round-1 HIGH-1 实证: 旧实现只检查基础 ``.pre-g25.bak`` 是否存在,
    存在就换成秒级时间戳名 —— 但**不检查时间戳名是否也存在**, 然后直接
    ``Path.rename()``。同一秒内的第二次隔离 (或并发进程) 会把上一份隔离件
    **覆盖掉**, 里面的 delete 意图不可逆丢失。

    ``rename``/``replace`` 天然是覆盖语义, Python 没有可移植的
    ``RENAME_NOREPLACE``。所以先用 ``O_EXCL`` 创建一个空占位文件把名字**占住**
    (这一步是原子的, 并发下只有一个进程能成功), 再 ``os.replace`` 把源盖到自己
    刚占住的那个名字上 —— 被覆盖的只可能是自己的空占位。
    """
    candidates = [base] + [base.with_name(f"{base.name}.{i}") for i in range(1, 100)]
    for cand in candidates:
        try:
            fd = os.open(cand, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            continue
        except OSError:
            return None
        os.close(fd)
        return cand
    return None


def quarantine_legacy_state_file(
    legacy_path: Path, *, context: str, active_path: Optional[Path] = None
) -> Optional[Path]:
    """把无 vault 维度的旧状态文件**改名隔离**, 返回新路径; 不存在则 ``None``。

    为什么是隔离而不是加载或删除:

    - **不加载**: 旧文件里的条目无从判断属于哪个 vault。按当前 vault 重放
      就是本卡要消灭的那条串台路径; 猜一个归属等于把事故变成静默事故。
    - **不删除**: 里面是用户数据的**意图**记录 (尤其 delete 意图), 删掉就没有
      任何人能事后复盘。改名保留, 让 Ops 能看、能救。

    ⚠️ **语义损失的真实口径** (Codex round-1 HIGH-4 修正 —— 旧文案统一写
    "60 秒内必收敛", **不成立**):

    - ``vault_index_orchestrator`` 的 journal: 它确实有周期反熵
      (``reconcile()`` 的指纹 diff + orphan sweep, ``VAULT_INDEX_SCAN_INTERVAL_S``
      默认 60s, 且启动先跑一趟)。**但那趟扫描只覆盖当前部署的这个 vault**。
      所以准确说法是: **等那个 vault 自己再次运行且扫描健康之后**才收敛 ——
      如果隔离件属于一个你以后再没打开过的 vault, 它永远不会被补上。
    - ``lancedb_index_service`` 的 journal: **没有周期反熵**。它的条目只记
      ``canvas_name``, 靠 canvas 再次变更才会重新入队。隔离之后若该 canvas 不再
      改动, 就没有任何入口把它索引回去 —— 需要 Ops 判定归属或对该 vault 做一次
      全量重建。

    详见 CARD-G2-5 盘点文档 §二。
    """
    # ⛔ 绝不隔离**正在用的那份 journal**。
    # legacy 路径由 ``_pending_file.parent`` 派生 (HIGH-2 的修法), 若调用方把工作
    # journal 直接命名成无维度的老名字 (既有测试就是这么做的:
    # ``svc._pending_file = tmp/"lancedb_pending_index.jsonl"``), 两条路径会重合 ——
    # 那时"隔离旧件"就会把自己刚要读的文件改名走, recover 恒返回 0。
    # 生产不可能出现 (命名空间名恒带 ``__key``), 但这条守卫要在, 因为它保护的是
    # "别把自己正在读的文件搬走"这个更基本的性质。
    if active_path is not None:
        try:
            if legacy_path.resolve() == Path(active_path).resolve():
                logger.debug(
                    "[CARD-G2-5] %s: legacy 路径与当前 journal 重合 (%s), 跳过隔离",
                    context,
                    legacy_path,
                )
                return None
        except OSError:
            return None

    try:
        if not legacy_path.exists():
            return None
    except FileNotFoundError:
        return None
    except OSError as e:
        # Codex round-1 LOW-12: 只有"确实不存在"才静默; 其它 stat 失败要出声,
        # 否则一个权限问题会伪装成"没有旧文件, 一切正常"。
        logger.error("[CARD-G2-5] %s: 无法判断旧状态文件 %s 是否存在 (%s)", context, legacy_path, e)
        return None

    base = legacy_path.with_name(legacy_path.name + LEGACY_QUARANTINE_SUFFIX)
    target = _reserve_unique(base)
    if target is None:
        logger.error(
            "[CARD-G2-5] %s: 无法为 %s 抢占唯一隔离名 — **仍不会加载它**, 请 Ops 手工处理",
            context,
            legacy_path,
        )
        return None
    try:
        os.replace(legacy_path, target)
    except OSError as e:
        try:
            target.unlink()  # 清掉自己占的空位, 不留垃圾
        except OSError:
            pass
        logger.error(
            "[CARD-G2-5] %s: 旧的无 vault 维度状态文件 %s 隔离失败 (%s) — **仍不会加载它**, 但请 Ops 手工处理",
            context,
            legacy_path,
            e,
        )
        return None

    logger.warning(
        "[CARD-G2-5] %s: 发现旧的无 vault 维度状态文件, 已隔离为 %s 且**不加载**。"
        "它的条目无法判断属于哪个 vault, 按当前 vault 重放就是跨 vault 串台; "
        "其中若含 delete 意图: orchestrator 侧的反熵扫描只覆盖当前部署的这个 vault, "
        "lancedb_index_service 侧没有周期反熵 —— 收敛条件见本函数 docstring (不是无条件 60s)。",
        context,
        target.name,
    )
    return target

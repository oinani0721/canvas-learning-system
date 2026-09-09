#!/usr/bin/env python3
"""CARD-G3-5 — 把 FSRS 投影快照从扁平单键迁移到 vault 分桶嵌套形态.

[BATCH-2026-09-07-第十三批 / CARD-G3-5]

迁移对象是 **review 侧**的 ``backend/data/fsrs_card_states.json``:

    旧 (扁平, 无 vault 维度): {"<concept_id>": "<card json str>", ...}
    新 (vault 分桶):          {"<vault_id>": {"<concept_id>": "<card json str>"}}

两个 vault 的同名 concept 在旧形态下撞同一个 JSON 键、后写覆盖先写
(``review_service._card_states`` 的内存镜像同病, 已由本卡键化)。

**文件名 (DD-13 名实一致)**: 设计稿与任务书写的是 ``migrate_mastery_vault_key.py``,
但本迁移器的对象是 review 侧的 JSON 投影文件, **不是** mastery / Neo4j
(mastery 侧 ``MasteryStore`` 已含 group 维度, 且本卡禁连 7691)。沿用旧名会让
名字与行为不符, 故按 DD-13 改名, 理由记在验收单与台账。

用法::

    # 只读只报 (不改输入快照、不产生 .bak; 给了 --out 才写那一份报告)
    python scripts/migrate_fsrs_card_states_vault_key_g35.py \\
        --dry-run --file /tmp/copy.json --out /tmp/report.json

    # 实际迁移 (双备份 + 重读校验 + 失败还原)
    python scripts/migrate_fsrs_card_states_vault_key_g35.py \\
        --apply --vault-id canvas_vault --file /tmp/copy.json

设计参照 (DD-04): 备份/校验/还原形态抄 ``migrate_neo4j_data.py:175-201``;
互斥模式组抄 ``migrate_group_ids.py:58-68``; "证明目标不是现网才允许写"的
闸抄 ``migrate_write_identity_g23.py:105-167``。

**退出码约定**::

    0  成功 (含 "无可迁移条目" 的空输入路径)
    1  未写入或**已回滚到备份**——目标文件处于迁移前的可信状态
    2  参数/闸拒绝 (缺 --vault-id、目标是现网文件、--out 与 --file 同一文件、
       输入读不出或形态非法)
    3  **回滚也失败**——目标文件可能损坏/半写, 备份路径在 stderr 里, 需人工处置

1 与 3 必须分得开 (Codex r1 HIGH-3): 只看"非零"分不出"已安全回滚"与"文件还坏着"。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── 现网闸 ──────────────────────────────────────────────────────────────────
#: 主仓 (现网运行时读写的那一份)。--apply **绝不允许**落在它上面: 本卡硬边界
#: "禁改主仓 fsrs_card_states.json (迁移跑 tmp 副本)"。
LIVE_REPO_ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system")
LIVE_CARD_STATES = LIVE_REPO_ROOT / "backend" / "data" / "fsrs_card_states.json"
#: live vault — 任何落在它下面的写入都触发部署铁律, 迁移器一概拒绝。
LIVE_VAULT_DIR = LIVE_REPO_ROOT / "canvas-vault"

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "data" / "fsrs_card_states.json"

#: 隔离区保留键 —— 必须与 ``review_service._ORPHAN_LEGACY_KEY`` **逐字一致**。
#: 加载器把归不掉的 legacy 放在这个键下"等人用迁移器裁定归属"; 本脚本就是那个
#: "人裁定"的执行者。若它不认这个键 (原实现按 isinstance(dict) 当成一个 vault
#: 桶), 隔离区里的条目永远出不来, 整条链路是断的 (Codex r4 H3)。
_ORPHAN_LEGACY_KEY = "__g35_orphan_legacy__"


def _resolved(path: Path) -> Path:
    """真实路径 —— 消解符号链接、``..`` 回绕与相对路径。

    子串比对 (``"canvas-learning-system/backend/data" in str(p)``) 会被等价
    写法通过: 相对路径、``..`` 回绕、符号链接。

    ⚠️ **它只解析路径, 不是文件身份** (Codex r1 HIGH-4 整改): 同一份文件的
    **硬链接**有不同的 resolved 路径却是同一个 inode, 纯路径比对会放行它, 随后
    ``write_text()`` 截断的仍是那个受保护文件。文件身份判据见 :func:`_identity`。
    """
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _identity(path: Path) -> Optional[Tuple[int, int]]:
    """文件身份 = ``(st_dev, st_ino)`` —— 硬链接同身份, 路径不同也认得出。

    返回 None 表示文件不存在 (还没被创建的目标没有身份, 只能靠路径判据)。
    """
    try:
        st = path.stat()
    except OSError:
        return None
    return (st.st_dev, st.st_ino)


def _protected_identities() -> List[Tuple[int, int]]:
    """需要保护的现网文件身份集合 (存在的那些)。"""
    out: List[Tuple[int, int]] = []
    for p in (LIVE_CARD_STATES,):
        ident = _identity(p)
        if ident is not None:
            out.append(ident)
    return out


def assert_target_is_not_live(target: Path, *, what: str = "--apply 的目标") -> Optional[str]:
    """现网闸: 证明写入目标**不是**现网文件, 否则拒绝.

    两道判据, 缺一不可 (Codex r1 HIGH-4):
      1. **文件身份** ``(st_dev, st_ino)`` —— 认得出硬链接 (同 inode 不同路径);
      2. **路径包含** —— 覆盖尚不存在因而没有 inode 的目标 (如新建在 live vault
         里的文件), 以及 live vault 整个子树。

    Returns:
        None 表示放行; 非 None 为拒绝原因字符串。
    """
    resolved = _resolved(target)

    # ① 文件身份 (硬链接也拦得住)
    target_ident = _identity(target)
    if target_ident is not None and target_ident in _protected_identities():
        return (
            f"{what} {resolved} 与**主仓现网**投影文件是同一个文件 "
            f"(dev/inode {target_ident}, 硬链接或同路径) — 本卡硬边界禁改它。"
            "请 cp 到临时目录后指向副本。"
        )

    # ② 路径判据 (覆盖尚不存在的目标)
    if resolved == _resolved(LIVE_CARD_STATES):
        return f"{what} {resolved} 是**主仓现网**投影文件 — 本卡硬边界禁改它。请 cp 到临时目录后指向副本。"

    live_vault = _resolved(LIVE_VAULT_DIR)
    if resolved == live_vault or live_vault in resolved.parents:
        return f"{what} {resolved} 落在 live vault ({live_vault}) 内 — 写它会触发部署铁律, 拒绝执行。"

    if resolved.exists() and not resolved.is_file():
        return f"{what} {resolved} 不是普通文件, 拒绝执行。"

    # ③ 多名字判据 (Codex r3 H3): 受保护 inode 集只收得进**已知**的那一个文件;
    #    live vault 里成百上千个节点文件的 inode 不可能逐一枚举, 而它们中任何一个
    #    的硬链接都可以放在 /tmp 下、resolved 路径完全无辜。
    #    可证的收敛判据是: 已存在的写入目标若 st_nlink > 1, 它**还有别的名字**,
    #    而我们无法证明另一个名字不在受保护区 —— 拒绝, 而不是带着不确定去截断。
    #    (正常的临时副本 nlink == 1, 不受影响。)
    try:
        nlink = target.stat().st_nlink
    except OSError:
        nlink = 1
    if nlink > 1:
        return (
            f"{what} {resolved} 的硬链接数为 {nlink} — 它在文件系统里还有别的名字, "
            "无法证明另一个名字不在 live vault / 现网面内。请指向一个独占的普通文件。"
        )

    return None


def assert_out_is_safe(out: Optional[Path], data_file: Path) -> Optional[str]:
    """``--out`` 的写入闸 (Codex r1 HIGH-2 整改).

    ``--out`` 是**写入路径**, 此前完全不过闸, 于是:
      · ``--dry-run --file X --out X`` 会让报告 JSON 覆盖输入快照 —— "dry-run
        零写入"不成立, 且没有备份;
      · ``--apply`` 时同样的别名会在重读校验**通过之后**再覆盖刚迁好的文件 ——
        "校验成功后留下的是迁移结果"也不成立。

    故 ``--out`` 必须同时满足: 不是现网文件 (含硬链接), 且与 ``--file`` 不是
    同一个文件。
    """
    if out is None:
        return None

    refusal = assert_target_is_not_live(out, what="--out 的目标")
    if refusal is not None:
        return refusal

    out_ident = _identity(out)
    data_ident = _identity(data_file)
    if out_ident is not None and data_ident is not None and out_ident == data_ident:
        return (
            f"--out {_resolved(out)} 与 --file {_resolved(data_file)} 是同一个文件 "
            f"(dev/inode {out_ident}) — 报告会覆盖快照本身, 拒绝执行。"
        )
    if _resolved(out) == _resolved(data_file):
        return f"--out 与 --file 指向同一路径 {_resolved(out)} — 报告会覆盖快照本身, 拒绝执行。"

    # 备份路径也是本命令自己会写的产物 (Codex r3 M2): `--out <file>.json.bak`
    # 会在迁移成功并校验之后, 把简单备份覆盖成报告 —— "双备份"承诺随之落空,
    # 而退出码仍是 0。时间戳那条含运行时时刻, 这里按**同 stem 的 .json.bak 前缀**
    # 一并拒绝, 不依赖预知时间戳。
    simple_backup = data_file.with_suffix(".json.bak")
    out_resolved = _resolved(out)
    if out_resolved == _resolved(simple_backup):
        return f"--out {out_resolved} 就是本命令要写的简单备份路径 — 报告会把备份覆盖掉, 拒绝执行。"
    backup_ident = _identity(simple_backup)
    if out_ident is not None and backup_ident is not None and out_ident == backup_ident:
        return (
            f"--out {out_resolved} 与简单备份 {_resolved(simple_backup)} 是同一个文件 "
            f"(dev/inode {out_ident}) — 报告会把备份覆盖掉, 拒绝执行。"
        )
    if out_resolved.name.startswith(simple_backup.name + "."):
        return f"--out {out_resolved} 落在本命令的时间戳备份命名面 ({simple_backup.name}.<ts>) 上 — 拒绝执行。"
    return None


# ── 形态分类与迁移 ──────────────────────────────────────────────────────────


def classify(raw: Dict[str, Any]) -> Tuple[int, int, List[str], int]:
    """统计三个数: 裸键条数 n_old / 已带 vault 维度条数 n_new / 冲突 concept.

    判据:
      · value 是 ``dict``  → 该键是 **vault 桶**, 其中每条计入 ``n_new``;
      · value 不是 dict    → 该键是**裸 concept_id**, 计入 ``n_old``。

    冲突 = 同一个 ``concept_id`` 出现在**多个** vault 桶里。它不是错误 (正是
    键化要支持的形态), 但迁移时要让操作者看见: 把裸键并进某个已有桶可能与
    该桶里的同名条目撞上。
    """
    n_old = 0
    n_new = 0
    n_isolated = 0
    per_concept_vaults: Dict[str, List[str]] = {}

    for key, value in raw.items():
        if str(key) == _ORPHAN_LEGACY_KEY:
            # 隔离区**不是** vault 桶 (Codex r4 H3): 把它算进 n_new 会让
            # "还剩多少要迁"这个数从一开始就是假的, 也不参与跨 vault 冲突检测
            # (它不属于任何 vault)。值不是 dict 时按裸键处置, 与加载器同口径。
            if isinstance(value, dict):
                n_isolated += sum(len(v) if isinstance(v, list) else 1 for v in value.values())
            else:
                n_old += 1
            continue
        if isinstance(value, dict):
            n_new += len(value)
            for concept_id in value:
                per_concept_vaults.setdefault(str(concept_id), []).append(str(key))
        else:
            n_old += 1

    conflicts = sorted(concept_id for concept_id, vaults in per_concept_vaults.items() if len(vaults) > 1)
    return n_old, n_new, conflicts, n_isolated


def build_migrated(raw: Dict[str, Any], vault_id: str) -> Tuple[Dict[str, Any], List[str]]:
    """把裸键条目并进 ``vault_id`` 桶, 返回 (新快照, 被覆盖的 concept 列表).

    已是 vault 桶的部分**原样保留** —— 迁移器不重排已迁好的数据。
    """
    migrated: Dict[str, Any] = {
        str(k): dict(v) for k, v in raw.items() if isinstance(v, dict) and str(k) != _ORPHAN_LEGACY_KEY
    }
    bucket = migrated.setdefault(vault_id, {})
    clobbered: List[str] = []

    # ① 裸 concept_id 键
    for key, value in raw.items():
        if str(key) == _ORPHAN_LEGACY_KEY:
            continue
        if isinstance(value, dict):
            continue
        concept_id = str(key)
        if concept_id in bucket:
            clobbered.append(concept_id)
        bucket[concept_id] = value

    # ② 隔离区认领 —— 这就是"人工裁定归属"的落地动作 (Codex r4 H3)。
    #    加载器把归不掉的条目放进隔离区等这一步; 迁移器若不认领, 它们永远出不来。
    #    同一 concept 可能挂多份待裁定的卡 (值是列表): 取**第一份**并把其余逐条
    #    报出来 —— 脚本不替人选, 但也不静默丢: 未被选中的那些留在隔离区。
    isolated_raw = raw.get(_ORPHAN_LEGACY_KEY)
    leftover: Dict[str, Any] = {}
    if isinstance(isolated_raw, dict):
        for key, value in isolated_raw.items():
            concept_id = str(key)
            cards = value if isinstance(value, list) else [value]
            if not cards:
                continue
            if concept_id in bucket:
                clobbered.append(concept_id)
                leftover[concept_id] = cards
                continue
            bucket[concept_id] = cards[0]
            if len(cards) > 1:
                leftover[concept_id] = cards[1:]
    elif isolated_raw is not None:
        # 保留键的值不是 dict = 一个名字恰好等于保留键的 legacy 裸 concept
        concept_id = _ORPHAN_LEGACY_KEY
        if concept_id in bucket:
            clobbered.append(concept_id)
        else:
            bucket[concept_id] = isolated_raw

    if leftover:
        migrated[_ORPHAN_LEGACY_KEY] = leftover

    return migrated, clobbered


# ── 主流程 ──────────────────────────────────────────────────────────────────


def load_snapshot(path: Path) -> Dict[str, Any]:
    if not path.exists():
        print(f"ERROR: 文件不存在: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        print(f"ERROR: 读不出 {path}: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(raw, dict):
        print(
            f"ERROR: {path} 顶层不是 JSON object (实得 {type(raw).__name__}) — 拒绝迁移",
            file=sys.stderr,
        )
        sys.exit(2)
    return raw


def write_report(out: Optional[Path], payload: Dict[str, Any]) -> bool:
    """写证据报告; 返回是否写成功。

    ⚠️ **异常不得冒泡** (Codex r2 M2): 报告是**旁路产物**, 它写不出来不改变
    数据文件的状态。若让异常冒泡, 一个不可写的 --out 会让"迁移已成功且已校验"
    的运行以 rc=1 退出 —— 而 rc=1 按约定表示"未写入或已回滚到迁移前状态",
    与事实相反。故失败只告警, 由调用方决定怎么反映在退出码里。
    """
    if out is None:
        return True
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, TypeError) as e:
        print(
            f"WARNING: 报告写入失败 ({type(e).__name__}: {e}) — 数据文件本身不受影响。",
            file=sys.stderr,
        )
        return False
    print(f"报告已写: {out}")
    return True


def run_dry_run(path: Path, raw: Dict[str, Any], vault_id: Optional[str], out: Optional[Path]) -> int:
    n_old, n_new, conflicts, n_isolated = classify(raw)

    print("=" * 68)
    print("CARD-G3-5 FSRS 投影 vault 键化迁移 — DRY RUN (不改输入, 不产生备份)")
    print("=" * 68)
    print(f"目标文件 : {path}")
    print(f"顶层键数 : {len(raw)}")
    print(f"n_old    : {n_old}   (裸 concept_id 键, 待迁)")
    print(f"n_new    : {n_new}   (已在 vault 桶内的条目)")
    print(f"冲突     : {len(conflicts)}   (同一 concept 出现在多个 vault 桶)")
    print(f"隔离区   : {n_isolated}   (归不掉、等本命令裁定归属的条目)")
    if conflicts:
        for concept_id in conflicts[:10]:
            print(f"           · {concept_id}")
        if len(conflicts) > 10:
            print(f"           ... 另有 {len(conflicts) - 10} 条")

    print("-" * 68)
    if n_old == 0:
        print("计划     : 无可迁移条目 (n_old = 0) — --apply 将直接退出且不产生备份。")
    elif vault_id:
        _, clobbered = build_migrated(raw, vault_id)
        print(f"计划     : 把 {n_old} 条裸键并入 vault 桶 {vault_id!r}")
        if clobbered:
            print(f"⚠️ 警告   : 其中 {len(clobbered)} 条与该桶已有同名条目撞键, --apply 会用裸键那份覆盖:")
            for concept_id in clobbered[:10]:
                print(f"           · {concept_id}")
    else:
        print(f"计划     : 把 {n_old} 条裸键并入 --vault-id 指定的桶 (本次未给 --vault-id, 故只报数不排计划)")
    print("=" * 68)
    # L1 (Codex r2): 准确表述 —— 带 --out 时会创建目录并写报告,
    # 只有不给 --out 的 dry-run 才是零文件写入。
    print("[DRY RUN] 输入快照未被修改, 未产生任何 .bak 备份。")

    wrote = write_report(
        out,
        {
            "mode": "dry-run",
            "file": str(path),
            "vault_id": vault_id,
            "n_old": n_old,
            "n_new": n_new,
            "n_isolated": n_isolated,
            "conflicts": conflicts,
            "top_level_keys": len(raw),
        },
    )
    # 先写、成功了才宣称 (Codex r3 L2): 原实现在调用**之前**就打印"本次写了
    # 一份报告", 报告写失败时输出与事实相反。
    if out is not None and wrote:
        print(f"[DRY RUN] (报告已写: {out} — 这是本次唯一的文件写入)")
    return 0


def run_apply(path: Path, raw: Dict[str, Any], vault_id: str, out: Optional[Path]) -> int:
    n_old, n_new_before, conflicts, n_isolated = classify(raw)

    print("=" * 68)
    print("CARD-G3-5 FSRS 投影 vault 键化迁移 — APPLY")
    print("=" * 68)
    print(f"目标文件 : {path}")
    print(f"目标桶   : {vault_id}")
    print(f"n_old    : {n_old}")
    print(f"n_new    : {n_new_before} (迁移前已在桶内)")
    print(f"隔离区   : {n_isolated}   (本次 --vault-id 会认领它们)")

    # 「迁完」与「本来就空」必须分得开 —— 0 → 0 不算迁移成功。
    if n_old == 0 and n_isolated == 0:
        print("-" * 68)
        print("无可迁移条目 (裸键 0 条、隔离区 0 条) — 未做任何写入, 未产生备份。")
        print("=" * 68)
        wrote = write_report(
            out,
            {
                "mode": "apply",
                "file": str(path),
                "vault_id": vault_id,
                "n_old": 0,
                "n_new": n_new_before,
                "n_isolated": 0,
                "migrated": 0,
                "result": "nothing-to-migrate",
                "backups": [],
            },
        )
        if out is not None and wrote:
            print(f"报告已写: {out} (本次未改动数据文件, 这是唯一的文件写入)")
        return 0

    migrated, clobbered = build_migrated(raw, vault_id)
    _, n_new_after, _, n_isolated_after = classify(migrated)
    gained = n_new_after - n_new_before

    if clobbered:
        print(f"⚠️ {len(clobbered)} 条裸键与目标桶已有同名条目撞键, 用裸键那份覆盖: {clobbered[:10]}")

    # 数量判据: 迁进去的条数必须等于迁移前的裸键条数, 且 > 0。
    # 认领的隔离区条目也是"迁进去的" (Codex r4 H3), 数量判据必须含它们, 否则
    # 迁移隔离区会被判成"数量不符"而拒写。
    claimed_from_isolation = n_isolated - sum(
        len(v) if isinstance(v, list) else 1 for v in (migrated.get(_ORPHAN_LEGACY_KEY) or {}).values()
    )
    expected = n_old + claimed_from_isolation - len(clobbered)
    if gained != expected or n_new_after <= 0:
        print(
            f"ERROR: 数量判据不成立 — 迁移前裸键 {n_old} 条 (其中 {len(clobbered)} "
            f"条覆盖同名), 期望桶内净增 {expected}, 实得 {gained}; "
            f"迁移后总条目 {n_new_after}。未写任何文件。",
            file=sys.stderr,
        )
        return 1

    # ── 双备份 (抄 migrate_neo4j_data.py:175-183) ──────────────────────────
    # 备份自身失败 = 还没动源文件就停手: 没有有效备份就不该开始写。
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stamped_backup = path.with_suffix(f".json.bak.{timestamp}")
    simple_backup = path.with_suffix(".json.bak")
    # ⚠️ 备份路径也是**写入路径**, 必须过同一道闸 (Codex r2 H1): 输入可以是普通
    # 临时副本, 而 `<input>.json.bak` 本身已是现网投影的符号/硬链接 —— 只检查
    # --file / --out 时, 第二次 copy2 就把现网覆写了。
    for backup_path, label in ((stamped_backup, "时间戳备份"), (simple_backup, "简单备份")):
        refusal = assert_target_is_not_live(backup_path, what=f"{label} 的目标")
        if refusal is not None:
            print(f"ERROR: {refusal} 源文件未改动, 已中止。", file=sys.stderr)
            return 2
        # 时间戳路径要到这一刻才存在, 静态的命名前缀检查抓不到"它是一个指向
        # --out 的符号链接"这种反向别名 (Codex r4 M2)。这里按**解析后的真实
        # 路径 / inode** 再验一次。
        if out is not None:
            if _resolved(backup_path) == _resolved(out):
                print(
                    f"ERROR: {label} {_resolved(backup_path)} 与 --out 指向同一位置 — "
                    "报告会把备份覆盖掉, 源文件未改动, 已中止。",
                    file=sys.stderr,
                )
                return 2
            b_ident, o_ident = _identity(backup_path), _identity(out)
            if b_ident is not None and o_ident is not None and b_ident == o_ident:
                print(
                    f"ERROR: {label} 与 --out 是同一个文件 (dev/inode {b_ident}) — "
                    "报告会把备份覆盖掉, 源文件未改动, 已中止。",
                    file=sys.stderr,
                )
                return 2
    try:
        shutil.copy2(path, stamped_backup)
        shutil.copy2(path, simple_backup)
    except OSError as e:
        print(
            f"ERROR: 备份失败 ({type(e).__name__}: {e}) — 源文件未改动, 已中止。"
            f"可能残留不完整备份, 请手工检查 {stamped_backup} / {simple_backup}。",
            file=sys.stderr,
        )
        return 1
    # 备份可读性自检: copy2 成功不等于内容可用
    try:
        json.loads(stamped_backup.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        print(
            f"ERROR: 备份 {stamped_backup} 读回校验失败 ({type(e).__name__}: {e}) — "
            "源文件未改动, 已中止 (没有可用备份就不开始写)。",
            file=sys.stderr,
        )
        return 1
    print(f"备份     : {stamped_backup}")
    print(f"备份     : {simple_backup}")

    def _restore(reason: str) -> int:
        """从备份还原; **区分**「还原成功」(rc=1) 与「还原也失败」(rc=3)。

        Codex r1 HIGH-3: 原实现里 copy2 自身未捕获异常, 还原失败也大多以 1 退出,
        仅看退出码分不出"已回滚"与"文件仍处于坏状态"。
        """
        print(f"ERROR: {reason} — 从备份还原", file=sys.stderr)
        try:
            shutil.copy2(stamped_backup, path)
        except OSError as e:
            print(
                f"FATAL: 还原**也失败** ({type(e).__name__}: {e}) — "
                f"{path} 可能处于损坏/半写状态, 备份在 {stamped_backup}, 请人工处置。",
                file=sys.stderr,
            )
            return 3
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            print(
                f"FATAL: 还原后读回校验失败 ({type(e).__name__}: {e}) — "
                f"{path} 仍不可信, 备份在 {stamped_backup}, 请人工处置。",
                file=sys.stderr,
            )
            return 3
        print(f"已从备份还原: {stamped_backup} → {path}", file=sys.stderr)
        return 1

    # ── 写盘 ────────────────────────────────────────────────────────────────
    # write_text 必须在 try 内 (Codex r1 HIGH-3): 目标被截断后若磁盘满 / I/O
    # 出错, 原实现会直接异常退出, 到不了下面的还原分支, 留下空文件或半份 JSON。
    # ⚠️ except 必须含 ValueError (Codex r2 H2): lone surrogate 之类的键会让
    # `Path.write_text(..., encoding="utf-8")` 在**打开并截断目标之后**抛
    # UnicodeEncodeError —— 它属 ValueError 族而非 OSError, 只捕 OSError 会让它
    # 逃逸回滚, 目标已被截断成空文件却以 rc=1 退出, 直接推翻
    # 「rc=1 ⇒ 未写入或已安全回滚」的约定。本仓 _save_card_states 的 CARD-D3
    # Codex HIGH-3 早已踩过同一个坑, 那里的 except 就写着 (TypeError, ValueError)。
    try:
        payload_text = json.dumps(migrated, ensure_ascii=False, indent=2)
        path.write_text(payload_text, encoding="utf-8")
    except (OSError, ValueError, TypeError) as e:
        return _restore(f"写盘失败 ({type(e).__name__}: {e}), 目标可能已被截断")
    print(f"已写入   : {path}")

    # ── 重读校验 (抄 migrate_neo4j_data.py:190-201) ────────────────────────
    try:
        verify = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        return _restore(f"重读校验读不出文件 ({type(e).__name__}: {e})")

    if verify != migrated:
        return _restore("重读校验失败 — 落盘内容与预期不一致")

    _, n_new_verified, _, _ = classify(verify)
    if n_new_verified != n_new_after:
        return _restore(f"重读后条目数不符 (期望 {n_new_after}, 实得 {n_new_verified})")

    print("重读校验 : SUCCESS")
    print("-" * 68)
    print(f"迁移完成: 桶内条目 {n_new_before} → {n_new_verified} (净增 {gained})")
    print("=" * 68)

    write_report(
        out,
        {
            "mode": "apply",
            "file": str(path),
            "vault_id": vault_id,
            "n_old": n_old,
            "n_new_before": n_new_before,
            "n_new_after": n_new_verified,
            "migrated": gained,
            "clobbered": clobbered,
            "conflicts": conflicts,
            "result": "ok",
            "backups": [str(stamped_backup), str(simple_backup)],
        },
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="migrate_fsrs_card_states_vault_key_g35.py",
        description=(
            "CARD-G3-5: 把 fsrs_card_states.json 从扁平 {concept_id: card} "
            "迁移到 vault 分桶 {vault_id: {concept_id: card}}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    mode_group = p.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan + report only, do NOT modify the file",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="Actually migrate (double backup + verify-on-read + restore on failure)",
    )

    p.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_FILE,
        help=f"目标 JSON 快照 (default: {DEFAULT_FILE})",
    )
    p.add_argument(
        "--vault-id",
        default=None,
        help="裸键要并入的 vault 桶 id (--apply 必填; --dry-run 给了才排具体计划)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="把统计结果写成 JSON 证据文件",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    path: Path = args.file

    # --out 是写入路径, **两种模式都要过闸** (Codex r1 HIGH-2): dry-run 也会
    # 写报告, --file 与 --out 别名会让"零写入"不成立。
    out_refusal = assert_out_is_safe(args.out, path)
    if out_refusal is not None:
        print(f"ERROR: {out_refusal}", file=sys.stderr)
        return 2

    if args.apply:
        if not args.vault_id or not args.vault_id.strip():
            print(
                "ERROR: --apply 必须显式给 --vault-id — 归属由人裁定, "
                "不由脚本按进程 active vault 猜 (猜错就是把一个 vault 的卡"
                "写进另一个 vault 的桶)。",
                file=sys.stderr,
            )
            return 2
        # ⚠️ 桶键形态必须与消费端取键的口径一致 (Codex r2 M3): service 侧的
        # `_VaultScopedCardStates._resolve_vault` 取的是 D16 组的
        # `group_id.split(":")[1]`, 其结果**不可能含冒号**。迁移器若接受
        # `--vault-id 'vault_a:subject'`, 会写出一个语法合法、重读一致、但
        # service 永远选不中的桶 —— 「内容重读一致」不等于「结果可被消费」。
        if args.vault_id.strip() == _ORPHAN_LEGACY_KEY:
            # Codex r4 H1: 迁进这个名字的桶, 加载器会把整个桶当成隔离区。
            print(
                f"ERROR: --vault-id 不能是隔离区保留键 {_ORPHAN_LEGACY_KEY!r} — "
                "加载器会把该桶整个当成隔离区, 迁出来的数据不可消费。",
                file=sys.stderr,
            )
            return 2
        bad_chars = [c for c in (":", "/", "\\") if c in args.vault_id]
        if bad_chars:
            print(
                f"ERROR: --vault-id {args.vault_id!r} 含 {bad_chars} — 消费端按 "
                "group_id.split(':')[1] 取桶键, 该结果不可能含这些字符, 迁出来的桶"
                "永远读不到。请只给 vault 段本身 (如 canvas_vault)。",
                file=sys.stderr,
            )
            return 2
        refusal = assert_target_is_not_live(path)
        if refusal is not None:
            print(f"ERROR: {refusal}", file=sys.stderr)
            return 2

    raw = load_snapshot(path)

    if args.dry_run:
        return run_dry_run(path, raw, args.vault_id, args.out)
    return run_apply(path, raw, args.vault_id.strip(), args.out)


if __name__ == "__main__":
    sys.exit(main())

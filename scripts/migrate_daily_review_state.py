#!/usr/bin/env python3
"""旧全局 daily-review state → per-vault 命名空间迁移 (CARD-C1a)。

旧格式: backups/daily-review.state.json (全 vault 共用 — 多 vault 互踩根源)
新格式: backups/daily-review.<vault_key>.state.json (key 规则唯一定义点:
send_bark.vault_key, 与 runner state_path 恒等)

用法:
  python3 scripts/migrate_daily_review_state.py --vault canvas-vault --dry-run
  python3 scripts/migrate_daily_review_state.py --vault canvas-vault

--dry-run 只打印旧→新映射, 零写入; 实迁写新文件后把旧文件改名 .bak 保留
(不删除 — 回滚 = mv 回原名)。目标已存在时拒绝覆盖 (重复跑安全)。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Codex-C1a B3: --dry-run 承诺「零写入」是字面意义的 — import 也不许留
# __pycache__ 字节码
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import send_bark  # noqa: E402


def main() -> int:
    # allow_abbrev=False 与 runner/push.sh 同源 (Codex-C1a F1)
    ap = argparse.ArgumentParser(description="daily-review state per-vault 迁移", allow_abbrev=False)
    ap.add_argument("--vault", required=True, help="旧全局 state 归属的 vault (路径或目录名, 即当前 ACTIVE_VAULT)")
    ap.add_argument("--backups", help="backups 目录 (缺省 $CANVAS_REPO/backups)")
    ap.add_argument("--dry-run", action="store_true", help="只打印映射, 零写入")
    args = ap.parse_args()

    repo = Path(os.environ.get("CANVAS_REPO", "/Users/Heishing/Desktop/canvas/canvas-learning-system"))
    backups = Path(args.backups) if args.backups else repo / "backups"
    # 与 runner state_path 同一条名字规则: 存在的路径先 resolve (symlink /
    # 相对路径归一到真实目录名), 裸目录名保持字面 — 两侧 key 必须恒等,
    # 否则经 symlink 传参时迁移会落到 runner 永远不读的文件名
    vault_arg = Path(args.vault)
    name = vault_arg.resolve().name if vault_arg.exists() else vault_arg.name
    key = send_bark.vault_key(name)
    old = backups / "daily-review.state.json"
    new = backups / f"daily-review.{key}.state.json"
    bak = old.with_name(old.name + ".bak")

    print(f"映射: {old} → {new}")

    if args.dry_run:
        # dry-run 全程只读 (字面零写入承诺含锁目录), 不建锁 — 内部在
        # 触及任何写动作前就会以 DRY-RUN 出口返回
        return _migrate_locked(args, old, new, bak, backups)

    # 与 push.sh/runner 同一把 per-vault 锁 (Codex-C1a F3 round3): 生产链
    # (launchd→wrapper→push.sh) 的 runner 运行中不迁移, 迁移中 runner 也
    # 进不来 — mkdir 原子抢锁, 抢不到即退。(直接手跑 daily_review_run.py
    # 不经 push.sh 无锁, 属开发路径, 不在本防护范围。)
    lock_dir = backups / f".daily-review.{key}.lock"
    try:
        os.mkdir(lock_dir)
    except FileExistsError:
        print("per-vault 锁被占用 (runner 或另一迁移实例在跑), 请稍后重试", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"无法建立 per-vault 锁: {e}", file=sys.stderr)
        return 1
    try:
        # token 协议与 push.sh owner_token 逐字节一致: "pid + LC_ALL=C
        # TZ=UTC /bin/ps 启动时刻" (round4/5/6: 裸 pid 会被判协议外死锁;
        # TZ/locale/PATH 任一不钉死, 同一活进程 token 跨调用环境漂移会被
        # 误回收)。ps 失败 fail-closed 拒迁 — 残缺 token 写进锁只会污染
        # push.sh 的活性判定。
        try:
            ps = subprocess.run(
                ["/bin/ps", "-o", "lstart=", "-p", str(os.getpid())],
                capture_output=True,
                text=True,
                timeout=5,
                env={**os.environ, "TZ": "UTC", "LC_ALL": "C"},
            )
            lstart = ps.stdout.rstrip("\n")
            if ps.returncode != 0 or not lstart.strip():
                raise OSError(f"/bin/ps rc={ps.returncode}")
        except (OSError, subprocess.SubprocessError) as e:
            print(f"无法生成锁 ownership token, 拒绝迁移: {e}", file=sys.stderr)
            return 1
        (lock_dir / "pid").write_text(f"{os.getpid()} {lstart}", encoding="utf-8")
        return _migrate_locked(args, old, new, bak, backups)
    finally:
        try:
            (lock_dir / "pid").unlink(missing_ok=True)
            os.rmdir(lock_dir)
        except OSError:
            pass


def _migrate_locked(args, old: Path, new: Path, bak: Path, backups: Path) -> int:
    # 状态机 (Codex-C1a F3): 以 (old, new, .bak) 三元存在性判定, 每个中止/
    # 并发残局都有显式出口, 不留 "重跑说无需迁移但其实丢了账本" 的死角。
    if not old.exists():
        if bak.exists() and not new.exists():
            print(f"检测到中断的迁移: 仅剩 {bak.name} — 请先恢复 (mv {bak.name} {old.name}) 后重跑", file=sys.stderr)
            return 1
        if bak.exists() and new.exists():
            # 完成态判据 = 字节相等 (round3: 只验 "new 可解析" 会把内容
            # 不同的 new+bak 误判完成, 旧账本仅存于 .bak → 重复推送)
            try:
                if new.read_bytes() == bak.read_bytes():
                    print("迁移已完成 (新文件与 .bak 逐字节一致), 无需重复")
                    return 0
            except OSError:
                pass
            print(
                f"目标与备份不一致 (疑写入中断或非本工具产物): {new.name} vs {bak.name} — 请人工核对后删除损坏一方重迁",
                file=sys.stderr,
            )
            return 1
        print("旧全局 state 不存在, 无需迁移 (新装环境 runner 首跑自建)")
        return 0

    try:
        # 二进制读写 (round4: read_text 的换行规范化会把 CRLF state 洗成
        # LF, 让 new 与 .bak 首迁即字节不等, 完成态判据被自己击穿)
        content = old.read_bytes()
        parsed = json.loads(content)
        # Codex-C1a B3: 结构校验到 dict 级 — "[]" 也是合法 JSON; runner
        # load_state 自 D2b-M1 起对错型隔离重建 (不再当场炸), 但重建即丢
        # 账 — 迁移侧拒迁保数据仍是第一道防线; 关键嵌套字段同查
        if not isinstance(parsed, dict):
            raise ValueError(f"state 根节点应为 object, 实为 {type(parsed).__name__}")
        blr = parsed.get("board_last_recommended")
        if blr is not None and not isinstance(blr, dict):
            raise ValueError("board_last_recommended 应为 object")
    except (json.JSONDecodeError, ValueError, OSError) as e:
        print(f"旧 state 无法解析, 拒绝迁移 (交由 runner 损坏隔离逻辑处置): {e}", file=sys.stderr)
        return 1
    if new.exists():
        print(f"目标已存在, 拒绝覆盖: {new}", file=sys.stderr)
        return 1
    if bak.exists():
        # 已有 .bak (上次回滚副本或手工备份) 不许静默覆盖 — 人工处置后重跑
        print(f"回滚副本已存在, 拒绝覆盖: {bak} (请先人工移走再重跑)", file=sys.stderr)
        return 1
    if args.dry_run:
        print("DRY-RUN: 未写入任何文件")
        return 0

    # 原子决胜 (Codex-C1a F3): old→bak 的 rename 在并发双实例间只有一个
    # 赢家; 输家在此收到 ENOENT, 直接退出, 绝不再碰 new。
    try:
        os.replace(old, bak)
    except FileNotFoundError:
        print("旧文件在校验后消失 (并发迁移实例已接手), 本实例退出", file=sys.stderr)
        return 1
    # 发布 = mkstemp (随机名独占创建, 固定名 tmp 的 symlink 劫持不可行,
    # Codex-C1a F4) + rename 原子换名 (终点路径绝无半写可见窗口, round3 N1;
    # rename 只替换链接名本身, 预置悬空 symlink 也不会把内容写去别处)。
    fd, tmp_name = tempfile.mkstemp(dir=str(backups), prefix=".migrate-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        os.replace(tmp_name, new)
    except OSError as e:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        print(f"发布新文件失败: {e} — 旧账本在 {bak.name}, 可 mv 回原名回滚", file=sys.stderr)
        return 1
    print(f"已迁移; 旧文件保留为 {bak.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

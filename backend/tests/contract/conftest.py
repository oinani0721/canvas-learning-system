"""`tests/contract` 专用零写门 —— 合约测试不得把 vault 骨架写进 `backend/`。

CARD-HYGIENE-openapi [BATCH-2026-09-07-第十三批]

## 它挡的是什么

`POST /api/v1/system/setup-wizard` (`app/api/v1/system.py:456`) 会调
`VaultInitService.initialize_vault()` (`app/services/vault_init_service.py:18-23,:93-104`),
按请求体 `vault_path` 建整套 vault 骨架(`raw/` `wiki/` `outputs/` `CLAUDE.md`);
`tests/conftest.py` 又把 `CANVAS_BASE_PATH` 设成相对的 `"./test_canvas"`。
两者叠加, 从 `backend/` 起跑的合约测试会在代码目录里留下 vault 骨架 ——
已有一个冻结的污染现场: worktree `card-z4-redbase` @ c8611a89。

`test_openapi_contract.py` 已用 `.include(method_regex=r"^(GET|HEAD)$")` 把写端点排除出
生成面; 本门是**独立于那层过滤**的第二道防线: 过滤写错、被人改回、或某个 GET
handler 间接写盘时, 这里会把它变成一条红色断言, 而不是一次静默的目录污染。

## 边界(如实)

- 只看 `backend/` **顶层**的五项骨架名, 不做全树扫描 —— 端点若写到 `$TMPDIR` /
  `$HOME` / 任意其它绝对路径, 本门看不见。
- fixture 自身**零写**: 只 `Path.exists()` / `os.stat()`, 不 touch、不 mkdir。
- `_BACKEND_ROOT` 由 `Path(__file__).resolve().parents[2]` 推导, 与进程 cwd 无关 ——
  从仓根、从 `backend/`、从任意目录起跑都指向同一个 `backend/`。
"""

import os
from datetime import datetime
from pathlib import Path

import pytest

# backend/tests/contract/conftest.py → parents[0]=contract, [1]=tests, [2]=backend
_BACKEND_ROOT = Path(__file__).resolve().parents[2]

# `VAULT_DIRECTORIES` (vault_init_service.py:18-23) 的顶层项 + `CLAUDE.md` 骨架文件
# + `tests/conftest.py:487` 的相对 `CANVAS_BASE_PATH="./test_canvas"`
_SKELETON = ("CLAUDE.md", "raw", "wiki", "outputs", "test_canvas")


def _present(root: Path) -> list[str]:
    """返回 root 顶层实际存在的骨架项(只读, 不创建任何东西)。"""
    return [name for name in _SKELETON if (root / name).exists()]


def _describe(root: Path, names: list[str]) -> str:
    """为命中项列出 mtime, 便于判断是本次跑出来的还是历史遗留。"""
    lines = []
    for name in names:
        target = root / name
        try:
            mtime = datetime.fromtimestamp(os.stat(target).st_mtime).isoformat()
        except OSError as exc:  # 竞态删除 / 权限 —— 如实写出, 不吞
            mtime = f"<stat 失败: {exc!r}>"
        lines.append(f"  - {target} (mtime={mtime})")
    return "\n".join(lines)


@pytest.fixture(scope="module", autouse=True)
def _assert_backend_stays_clean():
    """跑前/跑后各查一次 `backend/` 顶层的 vault 骨架, 任一时刻命中即 fail。

    跑前命中 = 现场已经脏了, 此时再跑, 跑后那次断言分不清是谁写的 ⇒ 先 fail 要求清理。
    跑后命中 = 本次合约测试写的 ⇒ fail 并列出命中项与 mtime。
    """
    root = _BACKEND_ROOT

    before = _present(root)
    if before:
        pytest.fail(
            f"污染现场已存在: {before} 先清理再跑\n"
            f"(root={root}; 这些项在合约测试开始之前就在了, 跑后断言无法归因)\n"
            f"{_describe(root, before)}"
        )

    yield

    after = _present(root)
    if after:
        pytest.fail(
            f"本次合约测试把 vault 骨架写进了 backend/: {after}\n"
            f"(root={root}; 跑前这些项都不存在)\n"
            f"{_describe(root, after)}"
        )

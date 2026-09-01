#!/usr/bin/env python3
"""OpenAPI 快照漂移门 — CARD-DEBT-openapi-sync [BATCH-2026-09-01-第八批]

替代 export-openapi.py 成为 `backend/openapi.json` 的唯一合法写入口(禁手改)。

用法
  --snapshot <path>  只读比对: committed 快照 vs 当前 app.openapi()(两侧同规则归一化)。
                     无漂移 exit 0 打 `DRIFT: none (paths=N schemas=M)`;
                     有漂移 exit 1 打路径级差异摘要。不落盘。
  --write <path>     重生成快照并落盘。恒写(每次刷新 info.x-generated-at):
                     lefthook 判据依赖「即使 API 面没变也重生成并 stage」这一可证行为,
                     代价是触及 backend/app/{api,models,schemas} 的 commit 会带一行
                     时间戳 diff(噪音已知, 由比对侧归一化吸收, 不会让门误红)。

只 import 不起 lifespan(脚本内自证)
  - 本脚本从不构造 TestClient、从不进入 app.router.lifespan_context;
    生成 schema 只调 app.openapi()(纯内存, 不跑任何 ASGI 事件)。
  - `from app.main import app` 与 app.openapi() 全程处于 socket-connect 禁闭
    (socket.socket.connect 被换成抛错桩)。任何 lifespan 行为(连 Neo4j 7691/
    LanceDB/graphiti 探活)都会在这里立即炸出来, 而不是静默连库。
  - 禁闭本身不改变输出: 2026-08-31 本机实测「带禁闭」与「不带禁闭」两次导出
    去掉易变键后**逐字节相同**(sha256 前 16 位同为 919d6b41fb870217)。
    唯一被禁闭拦到的是 LiteLLM 拉远程 model cost map(它自带本地 fallback,
    不进 schema)。

归一化规则(--snapshot 对两侧同规则应用; --write 落盘的也是归一化结果 + 易变键,
所以「快照里看到的」与「门拿去比的」是同一个东西)
  1. 删除 info.x-generated-at / info.x-generator。只删 info 层这两个键——
     2026-08-31 全树扫描实测: 这两个键在 app.openapi() 原生输出中**不存在**,
     只由本脚本 --write 写入, 故不存在「删掉了生产真值」的可能。
  2. dict 按 key 排序(JSON 对象成员无序, 排序只消除表示差异)。
  3. 键名为 `required` 且值为**纯字符串数组**、且当前处于 **Schema 语境** →
     sorted()。JSON Schema 的 required 是集合语义, 而 pydantic 按字段声明序
     生成它——2026-08-31 实测 281 个 required 数组中 144 个(51.2%)非字典序,
     不排序会让一次无关的字段重排把半数 schema 报成漂移(误红的门必然被
     `|| true` 掉, 那正是本卡要修的病)。用 sorted 而非 set: 重复项与数量
     差异仍会暴露, 不吞真漂移。
     ⚠️ 语境切分(Codex round-1/2 两个 BLOCKER 的最终解): enum/const/default/
     example/examples/value 这些键的**值是实例数据**, 实例必须与之精确相等,
     其内部一切数组都是有序值 —— 进入这些键的子树后 required 一律保序。
     实例数据里不可能再嵌 Schema(JSON Schema 封闭世界), 因此这是完备判据,
     不依赖「宿主长什么样」的内容启发式(形状启发式已被
     {"enum":[{"type":"tag","required":[...]}]} 类反例两次打穿)。
     ⚠️ 同名 key 的另一种用法 `required: true`(Parameter Object, 实测 373 处)
     是布尔标量, 走原样分支, 不受此规则影响。
  4. 其余数组一律**保序**。enum 尤其不排序: 取值顺序有语义(文档展示序、
     客户端代码生成器的枚举序), 实测 51 个 enum 中 42 个非字典序, 排了就是真吞漂移。
     parameters / anyOf / tags / security 同理保序。
  5. 标量按 JSON 类型严格比对: bool 与数字**不**相等(JSON 里 true 和 1 序列化
     不同, 是真实契约变更; Python 的 True == 1 必须显式打破)。int 与 float
     **有意**归并为同一 number 类型(JSON 只有一个数字类型, 1 与 1.0 语义相同,
     吸收不算吞漂移)。字符串与 null 各自独立。

本门证明什么: 归一化后 committed 快照与 app.openapi() 逐键逐值相等。
本门不证明什么: 不验证 schema 语义正确性、不验证实现与 spec 一致(那是 schemathesis
  的 tests/contract/test_openapi_contract.py 在做)、不验证跨机器/跨 Python 版本的
  确定性(本机 3.14 三次连 key 序都逐字节相同, 但 CI 用 3.11, 未跨版本实测)。
  上述五条归一化之外的任何差异(path/schema 增删、enum 取值与顺序、required 集合
  内容、bool↔数字翻转、任意键值变化)都原样报为漂移。
"""

import argparse
import contextlib
import copy
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"

VOLATILE_INFO_KEYS = ("x-generated-at", "x-generator")
X_GENERATOR_NAME = "scripts/spec-tools/check-openapi-drift.py --write"
DETAIL_LINE_CAP = 50


@contextlib.contextmanager
def socket_connect_lockdown():
    """import app.main + app.openapi() 期间禁一切 socket connect(lifespan 自证)。"""
    real_connect = socket.socket.connect

    def _blocked_connect(self, address, *args, **kwargs):
        raise RuntimeError(
            f"socket connect blocked during OpenAPI export (target={address!r}) — "
            "check-openapi-drift.py 只允许 import, 不允许 lifespan/网络行为"
        )

    socket.socket.connect = _blocked_connect
    try:
        yield
    finally:
        socket.socket.connect = real_connect


def load_live_schema() -> dict:
    """import app.main(不起 lifespan)并取 app.openapi(), 全程 socket 禁闭。"""
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    with socket_connect_lockdown():
        from app.main import app  # noqa: PLC0415 — 延迟 import 是本脚本的自证边界

        schema = app.openapi()
    # json 往返: 把 FastAPI 返回的 python 对象钉成纯 JSON 类型, 与快照侧同构
    return json.loads(json.dumps(schema, ensure_ascii=False))


def _tag_leaf(value):
    """标量打 JSON 类型标签(归一化规则 5)。

    bool 必须先于 int 判(isinstance(bool, int) 为真); int/float 同归 "number"
    是**有意**的(JSON 单一数字类型), 除此之外不同标签永不相等。
    """
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, (int, float)):
        return ("number", value)
    if isinstance(value, str):
        return ("string", value)
    if value is None:
        return ("null", None)
    return ("raw", value)


VALUE_CONTEXT_KEYS = frozenset(
    {"enum", "const", "default", "example", "examples", "value"}
)
"""这些键的**值是实例数据**, 不是 Schema —— JSON Schema 的封闭世界性质。

enum/const 的成员、default/example 的值、Example Object 的 value, 实例都必须与
之**精确相等**, 其内部一切数组(含恰好叫 required 的)都是有序数据。实例数据里
不可能再嵌 Schema(JSON Schema 规定 instance 与 schema 是两个不相交的世界),
所以 value-context 一旦进入, 对整棵子树都成立, 不需要任何内容启发式。
(Codex round-2 BLOCKER: 宿主含 type/properties 的形状启发式会被
{"enum":[{"type":"tag","required":[...]}]} 这类把 type 当普通数据键的合法
enum 实例打穿 —— 内容模仿是无底洞, 语境切分才是封闭世界里的完备判据。)
"""


def _normalize(node, key_in_parent=None, container=None, value_context=False):
    """container = 拥有 key_in_parent 这个键的那个 dict(即 node 的宿主)。

    required 排序只发生在 **Schema 语境**(value_context=False)下: 此时 required
    是 JSON Schema 关键字, 集合语义(pydantic 按字段声明序生成, 实测 281 个中
    144 个非字典序, 不排序会把无关字段重排报成漂移)。进入实例数据键的子树后
    value_context 恒为 True, 一切数组保序 —— 顺序差异必须报为漂移。
    """
    if isinstance(node, dict):
        normalized = {}
        for key in sorted(node):
            normalized[key] = _normalize(
                node[key],
                key,
                node,
                value_context or key in VALUE_CONTEXT_KEYS,
            )
        return normalized
    if isinstance(node, list):
        if (
            key_in_parent == "required"
            and all(isinstance(item, str) for item in node)
            and not value_context
        ):
            return sorted(node)
        # value_context 必须穿透数组边界: enum 的成员列表本身是数组, 语境若在此
        # 断掉, 成员对象内的 required 又会被当 Schema 关键字排序(Codex round-2
        # 反例复现的根因就是这里)
        return [_normalize(item, None, None, value_context) for item in node]
        return [_normalize(item, None, None) for item in node]
    return _tag_leaf(node)


def canonicalize(spec: dict) -> dict:
    """按模块 docstring 的五条规则归一化。入参不被修改。"""
    spec = copy.deepcopy(spec)
    info = spec.get("info")
    if isinstance(info, dict):
        for key in VOLATILE_INFO_KEYS:
            info.pop(key, None)
    return _normalize(spec)


def _untag(node):
    """把归一化树的标签叶子剥回原始值(供 --write 序列化)。

    输入若来自 json.loads / load_live_schema, 树中的 tuple 只可能是本模块打的
    类型标签(JSON 不产生 tuple), 故剥标签无歧义。
    """
    if isinstance(node, dict):
        return {key: _untag(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_untag(value) for value in node]
    if isinstance(node, tuple) and len(node) == 2:
        return node[1]
    return node


def _display(value) -> str:
    """归一化后的值转回人话: 标签元组展示为 `值(类型)`, 容器展示 JSON 类型名。"""
    if isinstance(value, tuple) and len(value) == 2:
        return f"{value[1]!r}({value[0]})"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return repr(value)


def diff_nodes(snap, live, pointer, out):
    """收集归一化后两树的**全部**差异(不截断, 截断只发生在展示层); 子树整体
    缺失只报最高层, 不下钻刷屏。"""
    if type(snap) is not type(live):
        out.append(
            f"{pointer}: 类型不同 snapshot={_display(snap)} live={_display(live)}"
        )
        return
    if isinstance(snap, dict):
        for key in sorted(snap.keys() | live.keys()):
            child = f"{pointer}>{key}"
            if key not in live:
                out.append(f"{child}: 仅在 snapshot(已从 app 移除)")
            elif key not in snap:
                out.append(f"{child}: 仅在 app.openapi()(snapshot 缺失)")
            else:
                diff_nodes(snap[key], live[key], child, out)
        return
    if isinstance(snap, list):
        if len(snap) != len(live):
            out.append(f"{pointer}: 数组长度 snapshot={len(snap)} live={len(live)}")
        for index, (item_a, item_b) in enumerate(zip(snap, live)):
            diff_nodes(item_a, item_b, f"{pointer}[{index}]", out)
        return
    if snap != live:
        out.append(f"{pointer}: snapshot={_display(snap)} live={_display(live)}")


def _key_set(spec: dict, *path) -> set:
    node = spec
    for part in path:
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return set(node) if isinstance(node, dict) else set()


def compare(snapshot: dict, live: dict) -> tuple[bool, list[str]]:
    """归一化后比对。返回 (无漂移, 全部差异摘要行)。供本地门测试直接调用。"""
    snap_canon = canonicalize(snapshot)
    live_canon = canonicalize(live)
    if snap_canon == live_canon:
        return True, []
    details: list[str] = []
    diff_nodes(snap_canon, live_canon, "", details)
    return False, details


def check_drift(snapshot_path: Path) -> int:
    if not snapshot_path.is_file():
        print(f"ERROR: snapshot 不存在: {snapshot_path}", file=sys.stderr)
        return 2
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: snapshot 读取/解析失败: {exc}", file=sys.stderr)
        return 2

    live = load_live_schema()
    clean, details = compare(snapshot, live)

    if clean:
        paths = len(live.get("paths", {}))
        schemas = len(live.get("components", {}).get("schemas", {}))
        print(f"DRIFT: none (paths={paths} schemas={schemas})")
        return 0

    snap_canon, live_canon = canonicalize(snapshot), canonicalize(live)
    snap_paths, live_paths = (
        _key_set(snap_canon, "paths"),
        _key_set(live_canon, "paths"),
    )
    snap_schemas = _key_set(snap_canon, "components", "schemas")
    live_schemas = _key_set(live_canon, "components", "schemas")
    truncated = len(details) > DETAIL_LINE_CAP
    print(
        f"DRIFT: found (paths: +{len(live_paths - snap_paths)} -{len(snap_paths - live_paths)}, "
        f"schemas: +{len(live_schemas - snap_schemas)} -{len(snap_schemas - live_schemas)}, "
        f"diff lines: {len(details)}{'+' if truncated else ''})"
    )
    for line in details[:DETAIL_LINE_CAP]:
        print(f"  {line}")
    if truncated:
        print(
            f"  ... 以及更多差异(仅显示前 {DETAIL_LINE_CAP} 条, 共 {len(details)} 条)"
        )
    print(
        "FIX: python scripts/spec-tools/check-openapi-drift.py --write backend/openapi.json"
        "  (禁手改快照)",
        file=sys.stderr,
    )
    return 1


def write_snapshot(output_path: Path) -> int:
    """归一化 + 易变键后落盘。恒写(见模块 docstring --write 段)。

    原子落盘(每进程独立 tmp + os.replace): lefthook 的多条 spec-sync 命令可能
    并行命中同一 commit。tmp 文件名**必须含 pid** —— 共享 tmp 名时, 先完成者
    rename 走 tmp 后, 后完成者的 rename 目标已不存在(FileNotFoundError, 进程
    以非零退出, 误阻断 commit); Codex round-2 实测 8 进程受控碰撞 child_failures=8。
    独立 tmp 后并发退化为「最后 rename 者胜」, 内容各自完整。
    """
    schema = _untag(canonicalize(load_live_schema()))
    info = dict(schema.get("info", {}))
    info["x-generated-at"] = datetime.now(timezone.utc).isoformat()
    info["x-generator"] = X_GENERATOR_NAME
    schema["info"] = {key: info[key] for key in sorted(info)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_name(f"{output_path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    tmp_path.replace(output_path)
    paths = len(schema.get("paths", {}))
    schemas = len(schema.get("components", {}).get("schemas", {}))
    print(
        f"WROTE: {output_path} (paths={paths} schemas={schemas}, "
        f"x-generated-at={info['x-generated-at']})"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--snapshot", metavar="PATH", help="只读比对该快照与 app.openapi()"
    )
    mode.add_argument(
        "--write", metavar="PATH", help="重生成快照并写入该路径(唯一合法落盘口)"
    )
    args = parser.parse_args()

    if args.snapshot:
        return check_drift(Path(args.snapshot))
    return write_snapshot(Path(args.write))


if __name__ == "__main__":
    sys.exit(main())

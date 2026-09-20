"""CARD-DEADLETTER-PATH-ANCHOR — 死信默认路径必须是 backend 绝对锚，不随 cwd 漂移。

背景（缺陷）：``DeadLetterStore.__init__`` 与 ``GraphitiEpisodeWorker.__init__`` 的
默认参数曾是字面量 ``"data/dead_letter_episodes.jsonl"`` —— **相对 cwd** 解析。
生产单例 ``get_episode_worker()`` 无参构造，于是进程从哪个目录启动，死信就落到
哪个目录的 ``data/`` 下；而读侧 ``/traces`` 的 ``BACKLOG_FILES`` 用的是 backend
绝对锚，两边只有在 cwd=backend 时才偶然对得上 —— 其余情况下死信写了，追踪页
永远读不到（DD-13 名实不符）。

本文件的五条门（全部落 tmp_path，零 mock，不调 ``get_episode_worker()``）：
  1. 锚常量本身绝对且落在 backend/data
  2. 默认构造的 store 写到锚上、**且** 不在 cwd 下留 ``data/``（两半都断言 ——
     只测一半的话，改前也能绿）
  3. worker 默认值是运行时解析（``default is None``），不是 def 期绑定的字面量
  4. 读侧 traces 与写侧是**同一个对象**（``is``，不是 ``==``）
  5. episode_worker.py 里不再有任何以 ``data/`` 开头的 cwd 相对默认值（AST）

⚠️ 常量访问一律走 ``getattr(..., None)``：改代码**前**该常量并不存在，顶层
``from ... import DEAD_LETTER_EPISODES_PATH`` 会让先红档变成 collection error，
而 (b)② 要求的是「红在各自的路径断言」。
"""

import ast
import inspect
from pathlib import Path

from app.core import failure_counters
from app.services import episode_worker
from app.services.episode_worker import DeadLetterStore, EpisodeTask, GraphitiEpisodeWorker

_ANCHOR_NAME = "DEAD_LETTER_EPISODES_PATH"


def _anchor() -> Path | None:
    """写侧锚常量；改前不存在 ⇒ None（让断言而不是 import 来红）。"""
    return getattr(failure_counters, _ANCHOR_NAME, None)


def test_default_anchor_is_absolute_under_backend():
    """锚常量必须绝对且落在 backend/data —— 与 failure_counters 既有两条同形。"""
    anchor = _anchor()
    assert anchor is not None, f"app.core.failure_counters.{_ANCHOR_NAME} 不存在 —— 死信默认路径仍是 cwd 相对串"
    assert anchor.is_absolute(), f"锚不是绝对路径: {anchor}"
    assert anchor.parts[-3:] == ("backend", "data", "dead_letter_episodes.jsonl"), f"锚没落在 backend/data: {anchor}"
    # 默认构造的 store 必须就用这个锚（__init__ 只 mkdir 不建文件；backend/data 已存在 ⇒ 零写入）
    assert DeadLetterStore()._file_path == anchor, (
        f"DeadLetterStore() 默认落点 {DeadLetterStore()._file_path} != 锚 {anchor}"
    )


def test_default_store_writes_to_anchor_not_cwd(tmp_path, monkeypatch):
    """默认 store 把记录写到锚上，**且** cwd 下不出现 ``data/``。

    两半都要断言：只断言「锚文件存在」的话，把锚打桩到 tmp 里后改前也可能绿；
    只断言「cwd 下没有 data/」的话，一个什么都不写的实现也能绿。
    """
    anchor = tmp_path / "anchor" / "dead_letter_episodes.jsonl"
    monkeypatch.setattr(episode_worker, _ANCHOR_NAME, anchor, raising=False)

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    task = EpisodeTask(
        name="ep-anchor-probe",
        episode_body="学习记录正文",
        group_id="vault__probe",
        source_description="unit-test",
    )
    DeadLetterStore().store(task, RuntimeError("neo4j down"))

    assert anchor.exists(), f"死信没写到锚上；cwd={elsewhere} 下的落点才是真实去向"
    assert len(anchor.read_text(encoding="utf-8").strip().splitlines()) == 1
    assert not (elsewhere / "data").exists(), f"死信落到了 cwd 相对目录 {elsewhere / 'data'} —— 追踪页永远读不到这一份"


def test_worker_default_resolves_to_same_anchor(tmp_path, monkeypatch):
    """worker 的默认 dead_letter_path 必须**运行时**解析同一个锚。

    ``default is None`` 是承重的一半：若把常量直接当 def 期默认值，它会绑死在
    ``__defaults__`` 上，模块属性打桩就失效 —— 那样这条门只能对着真死信文件跑。
    不调 ``get_episode_worker()``（单例跨用例残留），也不 start。
    """
    default = inspect.signature(GraphitiEpisodeWorker.__init__).parameters["dead_letter_path"].default
    assert default is None, f"dead_letter_path 默认值在 def 期就绑定了: {default!r}"

    anchor = tmp_path / "anchor" / "dead_letter_episodes.jsonl"
    monkeypatch.setattr(episode_worker, _ANCHOR_NAME, anchor, raising=False)
    monkeypatch.chdir(tmp_path)

    assert GraphitiEpisodeWorker()._dead_letter._file_path == anchor


def test_traces_reads_exactly_where_worker_writes():
    """读侧两张表都必须是写侧那**同一个对象**（``is``）—— 两份手抄清单必然漂移。"""
    from app.api.v1.endpoints import traces

    anchor = _anchor()
    assert anchor is not None, f"写侧锚 {_ANCHOR_NAME} 不存在，读侧无从同源"
    assert traces.BACKLOG_FILES["dead_letter_episodes.jsonl"] is anchor, (
        "BACKLOG_FILES 仍在自己拼路径，不是 import 写侧常量"
    )
    assert traces.LOG_FILES["dead_letter_episodes"] is anchor, "LOG_FILES 仍在自己拼路径，不是 import 写侧常量"


def test_no_cwd_relative_default_left_in_episode_worker():
    """AST：episode_worker.py 的函数默认值里不得再有以 ``data/`` 开头的字符串常量。"""
    source = Path(episode_worker.__file__).read_text(encoding="utf-8")
    offenders = [
        (node.name, node.lineno, default.value)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for default in node.args.defaults + node.args.kw_defaults
        if isinstance(default, ast.Constant) and isinstance(default.value, str) and default.value.startswith("data/")
    ]
    assert offenders == [], f"仍有 cwd 相对默认值: {offenders}"

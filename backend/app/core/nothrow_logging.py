# CARD-OBS-nothrow-logging (BATCH-2026-09-01-第八批)
"""No-throw 日志适配器 — 端点层的日志调用不得成为业务失败源。

移交来源: CARD-G4-3 Codex round-4 HIGH-1 (`_bmad-output/审查/codex-review-CARD-G4-3-round4.md`)
—— `/weak-concepts` 入口的 ``logger.info`` 在业务 ``try`` **之外**, patch 它抛错
→ HTTP 500 且 ``rag_service.get_weak_concepts`` 的 ``await_count=0`` (请求根本
没被执行); 同端点 ``except`` 分支的 ``logger.error`` 抛错 → 本该是结构化 503
的响应变成裸 500 (状态码和 detail 双双失真)。

设计对照 (同仓先例): ``app/core/decision_tracker.py::log_retrieval_status_decision``
的两级 fail-open。本模块把同一语义收敛成可复用的包装器, 供端点模块整体替换
模块级 ``logger``, 而不必在每个调用点手写 ``try/except``。零依赖 structlog。

──────────────────────────────────────────────────────────────────────────
本模块承诺什么 (**唯一**承诺, 不多不少)
──────────────────────────────────────────────────────────────────────────
被包装的 ``logger.<level>(...)`` **这一次调用**若抛出异常, 不向调用方传播;
因此它不改变调用方所在请求的 HTTP 状态码与 detail。

本模块**不**承诺什么 (诚实边界; 验收单同款):
1. **不防 Handler 层**: stdlib 日志链里 ``Handler.emit`` / ``Formatter.format``
   内的异常 (含 structlog ``ProcessorFormatter``, ``app/core/logging.py``) 本来
   就由 ``logging.Handler.handleError`` 自吞、从不传播到调用点。那部分不是本
   模块守住的, 也不因本模块而改变。
2. **不防实参求值**: ``logger.error(f"...{expensive()}")`` 里 ``expensive()``
   在**进入本包装器之前**就已求值 (Python 调用语义), 它抛错本模块看不见。
   端点侧配套把 f-string 改写为惰性 ``%s`` 参数, 正是把消息构造从"实参求值"
   挪进 ``record.getMessage()`` / ``Formatter.format`` —— 前者在本模块守护区
   内, 后者由 ``handleError`` 自吞。**没有改写的调用点不享受这条**。
3. **不防绕过**: 任何直接 ``logging.getLogger(...)`` 或经 ``.inner`` 取回原始
   Logger 的调用点都在保护之外。本模块只保护"经由被包装对象发出的调用"。
4. **不是全仓保护**: 只有模块级 ``logger`` 被换成本包装器的文件才受保护。
   未包装模块的清单见 ``backend/scripts/nothrow_logging_inventory.py``。

已知代价与边界 (按 Codex round-1 HIGH-1 / round-2 MEDIUM-1 的实证修正):
- **包装器新增吞掉的面 (守护区 = 进入 ``_guarded`` 后至 inner 返回前)**:
  此窗口内同步冒出的一切 ``Exception`` 都降级为 fallback WARNING —— 包括
  (a) 调用方参数引发的错 (``stacklevel=None`` 的补偿 TypeError、
  ``logger.log("INFO", ...)`` 的 level 类型错、``wrapped.log()`` 缺 level 的
  绑定错不在此列 —— 那发生在**进入守护区之前**的 Python 参数绑定, 属于
  "签名不合法的调用", 不在本承诺内); (b) stdlib 本来会传播的错 (自定义
  Handler/filter 抛错、``extra`` 键冲突、``MemoryError``、``StreamHandler``
  ``handleError`` 重抛的 ``RecursionError`` —— 它虽然从 handler 链里逃出,
  但仍发生在 inner 调用窗口内, 一样被接住)。裸 Logger 会当场抛的, 包装后
  都变成一条 fallback WARNING (带 logger 名/方法名/异常 repr, 可定位但比
  "当场炸"容易被忽略)。这是"观测面不得成为业务失败源"的必然代价。
- **stdlib 本来就自吞、非本模块新增**: 常见 ``StreamHandler.emit`` 内部的
  格式化/写失败走 ``Handler.handleError`` 自吞 (消息占位符与实参不匹配属于
  这类)。注意这不是日志链的普遍性质: ``Handler.handle``/``Logger.callHandlers``
  并无统一 catch —— 那部分传播面已被本包装器接管 (见上)。
- **不接的**: ``except Exception`` 不接 ``KeyboardInterrupt``/``SystemExit``
  (BaseException 直通); 以及进入守护区**之前**的失败 —— 实参求值发生在
  调用点 (见上第 2 条) 方法调用的参数绑定错误 (如 ``wrapped.log()`` 少传
  level)。
"""

import logging
from typing import Any, Union

# 二级降级的落点。模块级缓存而非每次 ``logging.getLogger()`` 现取: 现取会去
# 抢 ``logging._lock``, 而本函数恰恰运行在"日志系统刚出过事"的路径上。
# 也是测试缝 —— 用例可 patch 本模块属性来单独验证二级路径确实被走到
# (见 tests/api/v1/endpoints/test_nothrow_logging_api.py 的分层断言)。
_FALLBACK_LOGGER = logging.getLogger("app.nothrow.fallback")

# 调用点帧补偿。stdlib ``Logger.findCaller`` 默认 ``stacklevel=1`` 会停在
# "调用 Logger 方法的那一帧" —— 包装后那是本模块的 ``_guarded``, 于是
# ``record.filename/lineno/funcName`` 会从 ``rag.py`` / 端点函数漂移成
# ``nothrow_logging.py`` / ``_guarded``。中间隔了 2 帧 (``_guarded`` 与
# ``info``/``error``/… 这层包装方法), 故 +2。
#
# ⚠️ 这个常量与 ``_guarded`` 的调用深度**强耦合**: 谁把 ``_guarded`` 内联掉
# 或再包一层, 它就错了。因此配了一道帧透明门 (测试
# ``test_wrapper_is_frame_transparent``) —— 改了深度不改这里, 那道门必红。
#
# 生产可见性如实声明: 当前 ``app/core/logging.py`` 的 structlog 链里**没有**
# ``CallsiteParameterAdder``, JSON 输出不含 filename/lineno/funcName, 所以这个
# 漂移在**现网日志里看不见**; 它在 ``caplog.records[*]`` 与任何将来加上调用点
# 字段的配置里看得见。补偿是为了"包装器对调用点透明"这条性质本身成立。
_STACKLEVEL_OFFSET = 2

_LEVEL_METHODS = ("debug", "info", "warning", "error", "exception", "critical", "log")


class NoThrowLogger:
    """包裹一个 stdlib ``Logger``, 让被包装的日志调用永不向调用方传播异常。

    两级降级 (与 ``decision_tracker`` 同构):

    1. 被包装方法抛错 → 用 ``_FALLBACK_LOGGER.warning`` 登记一条 (惰性参数;
       **刻意不重放原始消息** —— 原始消息本身可能正是失败源);
    2. 二级 ``warning`` 也抛错 → 静默。观测彻底失效仍不得波及业务响应, 这是
       本类唯一硬承诺。

    ``.inner`` 暴露原始 Logger, 供确需原生 API 的调用方使用 —— 这是**逃生舱,
    不是保护**: 经 ``.inner`` 发出的调用不受本类保护。

    刻意**不**实现 ``__getattr__`` 全量委托: 未包装的成员 (``handlers`` /
    ``setLevel`` / ``isEnabledFor`` …) 直接 ``AttributeError``, 比"静默返回一个
    不受保护的绑定方法"诚实 —— 后者会让人以为自己仍在保护之内。

    刻意**不**用 ``__slots__``: ``unittest.mock.patch("...rag.logger.info")``
    需要往**实例**上 setattr (写进实例 ``__dict__``), ``__slots__`` 会让它当场
    ``AttributeError`` —— 既有门 ``test_rag_four_state_api.py`` 的注入测试正是
    这种写法。每模块只有一个实例, 实例 ``__dict__`` 的内存代价无关紧要。
    """

    def __init__(self, inner: logging.Logger) -> None:
        self.inner = inner

    # ── 内部 ────────────────────────────────────────────────────────────
    def _guarded(self, method: str, *args: Any, **kwargs: Any) -> None:
        """转调 ``inner.<method>``, 吞掉它抛出的一切并降级登记。

        ``method`` 只来自本模块的 ``_LEVEL_METHODS`` 字面量, 不接受外部输入 ——
        ``getattr`` 本身不会失败, 除非 ``inner`` 根本不是 Logger (那属于调用方
        用错了本类, 会走进同一个 fallback 并留下 ``AttributeError`` 的 repr)。

        ⚠️ stacklevel 补偿**必须在 try 内**做 (Codex round-1 HIGH-1):
        ``kwargs.get("stacklevel")`` 之外的求值若放在 try 外 —— 例如调用方传
        ``stacklevel=None`` 时 ``1 + None`` 的 TypeError —— 会直接传播, 击穿
        本类唯一的 no-throw 承诺。参数归一化本身就是可能抛错的操作。
        """
        try:
            kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + _STACKLEVEL_OFFSET
            getattr(self.inner, method)(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — 观测面刻意兜底, 见模块 docstring
            try:
                _FALLBACK_LOGGER.warning(
                    "nothrow: logger %r method %r raised during logging: %r",
                    getattr(self.inner, "name", "<unknown>"),
                    method,
                    exc,
                )
            except Exception:  # noqa: BLE001 — 兜底的兜底: 日志后端整体坏死
                pass

    # ── stdlib Logger 的日志方法 ────────────────────────────────────────
    def debug(self, *args: Any, **kwargs: Any) -> None:
        self._guarded("debug", *args, **kwargs)

    def info(self, *args: Any, **kwargs: Any) -> None:
        self._guarded("info", *args, **kwargs)

    def warning(self, *args: Any, **kwargs: Any) -> None:
        self._guarded("warning", *args, **kwargs)

    def error(self, *args: Any, **kwargs: Any) -> None:
        self._guarded("error", *args, **kwargs)

    def exception(self, *args: Any, **kwargs: Any) -> None:
        self._guarded("exception", *args, **kwargs)

    def critical(self, *args: Any, **kwargs: Any) -> None:
        self._guarded("critical", *args, **kwargs)

    def log(self, level: int, *args: Any, **kwargs: Any) -> None:
        self._guarded("log", level, *args, **kwargs)


def nothrow(logger: Union[logging.Logger, NoThrowLogger]) -> NoThrowLogger:
    """把 stdlib ``Logger`` 包成 ``NoThrowLogger``; 已包装的原样返回 (幂等)。

    幂等是有意的: 重复包装会多一层帧, 让 ``_STACKLEVEL_OFFSET`` 失准。
    """
    if isinstance(logger, NoThrowLogger):
        return logger
    return NoThrowLogger(logger)

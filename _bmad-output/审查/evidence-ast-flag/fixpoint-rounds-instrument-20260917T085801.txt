⛔ 本件作废（VOID）—— 保留作记录，不得引为依据。

根因：这两个早期 instrument 脚本把「不动点 for 的行号」硬编码成 634（改前值），
而被测目标写死为工作树里的 backend/scripts/lifespan_isolation_negative_control.py。
本卡 (f) 改动后该 for 漂到 :687，计数器于是全程没被写过，直方图退化成 {0: N} 的
假数据。抓住它的是脚本自带的那句「须含 634」验伪锚。

有效替代：同目录 rounds_instr.py（被测文件与行号都从命令行传入，且把验伪锚升成
assert——锚不命中直接抛，不再可能产出全 0 的假直方图）。其两次实跑见
fixpoint-rounds-instrument-<ts>.txt。定稿文件的等价能力已内建为
--selfcheck-fixpoint 的 [rounds] / [headroom] 两行。

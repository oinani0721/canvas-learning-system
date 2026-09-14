#!/bin/bash
# CARD-W4-4b7-TAIL —— seam 门的负控跑器（薄壳；清单与实现在 negctl_w4_gates.sh）。
# 用法：./negctl_seam.sh [--phase before|after|clean|all] [--prereq <sha>]
# 未识别参数 ⇒ rc≠0 且打印 `unknown arg: <x>`（UAT-CARD-W4-7 LOW-3a）。
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/negctl_w4_gates.sh" --gate seam "$@"

# ② CI 本地等价验证 — 原始取证

跑法：完全复刻 .github/workflows/test.yml::Run tests 的 env / 选择集 / flags。
唯一偏差：--junitxml 落到 scratchpad（避免在被 Codex 审阅的工作树里新建未跟踪 backend/reports/）。
解释器：本地 backend/.venv = Python 3.14.4（CI 矩阵为 3.11/3.12，差异见验收单如实声明）。

```
########## A) 现行 CI 清单（15 文件）基线 ##########
====================== 303 passed, 661 warnings in 16.23s ======================
EXIT_A=0
########## B) 拟议 CI 清单（15+2 文件） ##########
================ 516 passed, 1 skipped, 661 warnings in 21.40s =================
EXIT_B=0
########## C) 仅两个新文件（隔离归因） ##########
================= 213 passed, 1 skipped, 10 warnings in 5.72s ==================
EXIT_C=0
```

## 加法自洽核对

    A(现行15文件) 303 + C(仅2新文件) 213 = 516 = B(15+2) ✅
    skipped: A 0 + C 1 = 1 = B 1 ✅

两段独立跑的通过数严格可加 ⇒ 新增文件与既有清单**无交叉污染**（无共享 fixture / ContextVar 泄漏）。

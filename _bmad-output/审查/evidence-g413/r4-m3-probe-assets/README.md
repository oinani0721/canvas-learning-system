# r4 M-3 变异探针资产（自包含）

- `run_memory_mut.py` / `run_vault_mut.py`：把各自 runner 的 **manifest 校验块挪到环境检查之后** 的变异体
  （`mutants.diff` 给出与真文件的差异）。
- `probe.py`：复跑脚本（导入真工具 + 变异体/真 runner，按 pin 同款条件跑，打印判定）。
- 用途：证明 r3/r4 新加的 M-3 顺序 pin 是**承重**的（变异体 → pin 红；无 pin + alive=True → 看不到差异）。

#!/usr/bin/env python3
"""
Profile canvas_utils import performance
测试各个导入步骤的耗时
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def time_import(module_name, statement):
    """计时导入语句"""
    start = time.time()
    try:
        exec(statement)
        elapsed = time.time() - start
        print(f"[OK] {module_name:40s} - {elapsed:6.2f}s")
        return elapsed, True
    except Exception as e:
        elapsed = time.time() - start
        print(f"[FAIL] {module_name:40s} - {elapsed:6.2f}s (Error: {e})")
        return elapsed, False

print("="*80)
print("Canvas Utils Import Performance Analysis")
print("="*80)
print()

total_start = time.time()

# Test individual heavy imports
print("[Step 1] Testing heavy scientific libraries...")
time_import("pandas", "import pandas as pd")
time_import("numpy", "import numpy as np")
time_import("matplotlib", "import matplotlib.pyplot as plt")
time_import("seaborn", "import seaborn as sns")
time_import("scipy.stats", "from scipy import stats")
time_import("sklearn.cluster", "from sklearn.cluster import KMeans")
time_import("sklearn.preprocessing", "from sklearn.preprocessing import StandardScaler")

print("\n[Step 2] Testing Graphiti and Neo4j...")
time_import("graphiti_core", "from graphiti_core import Graphiti")
time_import("neo4j", "from neo4j import GraphDatabase")

print("\n[Step 3] Testing concurrent processing...")
time_import("aiomultiprocess", "import aiomultiprocess")
time_import("concurrent.futures", "from concurrent.futures import ProcessPoolExecutor")

print("\n[Step 4] Testing Loguru...")
time_import("loguru", "from loguru import logger")

print("\n[Step 5] Testing Agent Pool...")
time_import("agent_instance_pool", "from agent_instance_pool import get_instance_pool")

print("\n[Step 6] Full canvas_utils import...")
import_start = time.time()
try:
    from canvas_utils import CanvasJSONOperator
    import_time = time.time() - import_start
    print(f"[OK] {'Full canvas_utils import':40s} - {import_time:6.2f}s")
except Exception as e:
    import_time = time.time() - import_start
    print(f"[FAIL] {'Full canvas_utils import':40s} - {import_time:6.2f}s")
    print(f"   Error: {e}")

total_time = time.time() - total_start

print("\n" + "="*80)
print(f"Total time: {total_time:.2f}s")
print("="*80)

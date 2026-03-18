"""
Agentic RAG Nodes Package.

Re-exports all node functions from the nodes module (../nodes.py)
to resolve the file vs directory import conflict.
"""
import importlib
import sys
from pathlib import Path

# Import from the actual nodes.py file (sibling to this package directory)
_nodes_file = Path(__file__).parent.parent / "nodes.py"
_spec = importlib.util.spec_from_file_location("agentic_rag._nodes_impl", str(_nodes_file))
_module = importlib.util.module_from_spec(_spec)
sys.modules["agentic_rag._nodes_impl"] = _module
_spec.loader.exec_module(_module)

# Re-export all public names
from agentic_rag._nodes_impl import *  # noqa: F401, F403, E402

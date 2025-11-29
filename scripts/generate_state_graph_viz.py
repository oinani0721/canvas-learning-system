"""
Generate Mermaid visualization for Canvas Agentic RAG StateGraph

Story 12.5: LangGraph StateGraph构建
Task: Generate Graph visualization (Mermaid)

This script generates a Mermaid diagram of the compiled StateGraph
and saves it to docs/architecture/state-graph.mmd
"""

import sys
from pathlib import Path

# Add src to path to import agentic_rag modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentic_rag.state_graph import canvas_agentic_rag


def main():
    """Generate and save Mermaid diagram"""
    print("Generating Mermaid visualization for Canvas Agentic RAG StateGraph...")

    # Get Mermaid diagram
    mermaid_str = canvas_agentic_rag.get_graph().draw_mermaid()

    # Determine output path
    output_path = Path(__file__).parent.parent / "docs" / "architecture" / "state-graph.mmd"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mermaid_str)

    print(f"[SUCCESS] Mermaid diagram saved to: {output_path}")
    print(f"[SUCCESS] Diagram size: {len(mermaid_str)} characters")

    # Also print to console for verification
    print("\n" + "="*80)
    print("MERMAID DIAGRAM:")
    print("="*80)
    print(mermaid_str)
    print("="*80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
